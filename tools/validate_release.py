"""Validate the finite public release, without private records or network calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from build_site import ROOT, SITE_FILES, safe_file

CONTENT_SHA256 = '76d943680f1008b283d31c3dbb5baa3ff8658c88ebe94619dc57a57395447360'
REFERENCE_HASHES = {
    'article_rounds.py': 'f81023876f936a1094a43b0189820146d01b3acc33c49033550fc990ed674f98',
    'catalogue.py': 'b8774a517ddd48bb0f33eeff38a2ab049bd6a338a70f2f40a0fc2b5361843264',
    'haunting_rounds.py': 'd92660951d7b3bfeeb53c577a1d5651a43dab4ce8b5a51826796d84b2599c9ac',
    'server.py': 'c022bef509659b9f86d38c6b8cdc05a6ce2fc05ffc2975f0eba6e1d46eb86c5b',
    'spooky_rounds.py': '6dff343213d953362bbaf035ffa935a0ace50671035ef2a7c9fc59001da7c1b4',
}
SOURCE_FILES = (
    '.gitignore', '.github/workflows/ci.yml', '.github/workflows/pages.yml', 'README.md', 'LICENSING.md',
    'THIRD_PARTY_NOTICES.md', 'package.json', 'render.yaml',
    *(f'demo/{name}' for name in SITE_FILES),
    'tools/build_site.py', 'tools/validate_release.py', 'tools/package_release.py',
    'tests/game.test.js', 'tests/client.test.js', 'tests/test_release.py',
    'docs/provenance.md', 'docs/submission-draft.md', 'docs/bonus-checklist.md',
    'docs/release-checklist.md', 'docs/narration-script.md',
    'reference/local-preparation/README.md',
    *(f'reference/local-preparation/{name}' for name in REFERENCE_HASHES),
)
# Root supplies actual app-only browser evidence. No wildcard media inclusion.
OPTIONAL_FILES = ('docs/browser-qa.md', 'docs/media/static-intro.jpg',
                  'docs/media/static-desktop-result.jpg', 'docs/media/static-mobile-reveal.jpg',
                  'docs/media/static-mobile-result.jpg')
IGNORED_DIRS = {'.git', 'site', 'dist', 'node_modules', '__pycache__'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_list(root=ROOT):
    root = Path(root)
    files = list(SOURCE_FILES)
    files.extend(name for name in OPTIONAL_FILES if (root / name).exists() or (root / name).is_symlink())
    for name in files:
        safe_file(root, name)
    return sorted(files)


def scan_text(name, raw):
    if name.endswith('.jpg'):
        if not raw.startswith(b'\xff\xd8\xff') or len(raw) > 2_000_000:
            raise ValueError(f'Invalid or oversized screenshot: {name}')
        return
    text = raw.decode('utf-8')
    patterns = {
        'private absolute path': r'/(?:home|Users|tmp)/[A-Za-z0-9_.-]+',
        'private Windows path': r'[A-Za-z]:\\(?:Users|Temp)\\',
        'credential token': r'(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})',
        'private key material': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'credential assignment': r'''(?i)(?:api[_-]?key|password|access[_-]?token)\s*[:=]\s*["'][A-Za-z0-9_+/=-]{20,}["']''',
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text):
            raise ValueError(f'{name}: prohibited {label}')  # Never print matched secret values.


def validate(root=ROOT):
    root = Path(root).absolute()
    files = file_list(root)
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in [*dirs, *names]:
            if (Path(directory) / name).is_symlink():
                raise ValueError('Symlink in release tree')
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in names:
            relative = (Path(directory) / name).relative_to(root).as_posix()
            if relative not in files:
                raise ValueError(f'Unexpected source file: {relative}')
    for name in files:
        scan_text(name, safe_file(root, name).read_bytes())
    raw = safe_file(root, 'demo/content.json').read_bytes()
    if len(raw) > 24000 or digest(raw) != CONTENT_SHA256:
        raise ValueError('Public content size/checksum mismatch')
    # The byte pin also rules out duplicate JSON keys; use the actual browser validator.
    result = subprocess.run(['node', '--input-type=module', '-e',
        "import fs from 'node:fs'; import {decodeContent} from './demo/game.js'; "
        "await decodeContent(fs.readFileSync('demo/content.json','utf8'));"],
        cwd=root, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise ValueError('Browser content validation failed')
    for name, expected in REFERENCE_HASHES.items():
        if digest(safe_file(root, f'reference/local-preparation/{name}').read_bytes()) != expected:
            raise ValueError(f'Historical reference changed: {name}')
    html = (root / 'demo/index.html').read_text()
    if not all(value in html for value in ('href="./styles.css"', 'src="./app.js" type="module"', 'href="./"', 'Answers are included', 'not connected to VerifyIt')):
        raise ValueError('Relative assets or static disclosure missing')
    for match in re.findall(r'(?:src|href)="([^"]+)"', html):
        if match.startswith(('/', '//')) or (not match.startswith('./') and not match.startswith('https://')):
            raise ValueError('Unsafe/non-relative page URL')
    for name in ('app.js', 'game.js', 'styles.css'):
        code = (root / 'demo' / name).read_text()
        if re.search(r'127\.0\.0\.1|localhost:\d|/api/|localStorage|sessionStorage|sendBeacon|https?://[^\s\'"`]+\.(?:js|css|woff)', code):
            raise ValueError(f'Unexpected live dependency in {name}')
    package = json.loads((root / 'package.json').read_text())
    if package.get('dependencies') or package.get('devDependencies') or package.get('license') or package.get('private') is not True:
        raise ValueError('Unexpected dependency/licensing/package-publication change')
    ci = (root / '.github/workflows/ci.yml').read_text()
    if 'pull_request_target' in ci or 'secrets.' in ci or 'contents: write' in ci:
        raise ValueError('Privileged CI configuration')
    pins = re.findall(r'uses: ([^\s]+)', ci)
    if len(pins) != 4 or not all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}', pin) for pin in pins):
        raise ValueError('Unpinned/unexpected action')
    if 'permissions:\n  contents: read' not in ci:
        raise ValueError('Read-only CI permissions missing')
    pages = (root / '.github/workflows/pages.yml').read_text()
    triggers = pages.split('on:\n', 1)[1].split('permissions:', 1)[0]
    if triggers.strip() != 'workflow_dispatch:':
        raise ValueError('Pages must remain manual-only')
    build_job, deploy_job = pages.split('  deploy:\n', 1)
    if 'pages: write' in build_job or 'id-token: write' in build_job or 'path: site/' not in build_job:
        raise ValueError('Pages build permissions/artifact boundary changed')
    if not all(value in deploy_job for value in ('needs: build', 'pages: write', 'id-token: write', 'name: github-pages')):
        raise ValueError('Pages deploy dependency/permissions/environment missing')
    if not all(re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}', pin) for pin in re.findall(r'uses: ([^\s]+)', pages)):
        raise ValueError('Unpinned Pages action')
    render = (root / 'render.yaml').read_text()
    if not all(line in render for line in ('runtime: static', 'staticPublishPath: ./site', "autoDeployTrigger: 'off'")) or 'envVars:' in render or 'startCommand:' in render:
        raise ValueError('Unexpected hosting configuration')
    return files


def validate_archive(archive, root=ROOT):
    expected = file_list(root)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.namelist() != [f'ghostproof/{name}' for name in expected]:
            raise ValueError('Archive allowlist/order mismatch')
        for info, name in zip(bundle.infolist(), expected):
            if info.file_size > 2_000_000 or info.external_attr >> 16 & 0o170000 == 0o120000:
                raise ValueError('Unsafe archive member')
            if bundle.read(info) != safe_file(root, name).read_bytes():
                raise ValueError(f'Archive bytes differ: {name}')
    return expected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    checked = validate()
    if args.archive:
        validate_archive(args.archive)
    print(f'Validated {len(checked)} allowlisted source files; content and reference hashes match.')

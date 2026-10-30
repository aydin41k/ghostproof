"""Create a deterministic allowlisted source ZIP, then optionally rehearse it."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

from build_site import ROOT, safe_file
from validate_release import digest, validate, validate_archive

NAME = 'ghostproof-1.0.0.zip'


def package(root=ROOT):
    root = Path(root).absolute()
    files = validate(root)
    output = root / 'dist'
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('Unsafe package directory')
    output.mkdir(exist_ok=True)
    targets = [output / NAME, output / (NAME + '.sha256'), output / 'source-manifest.sha256']
    for target in targets:
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValueError('Unsafe package output target')
    with zipfile.ZipFile(targets[0], 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name in files:
            info = zipfile.ZipInfo('ghostproof/' + name, date_time=(2026, 10, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, safe_file(root, name).read_bytes())
    validate_archive(targets[0], root)
    targets[1].write_text(f'{digest(targets[0].read_bytes())}  {NAME}\n')
    targets[2].write_text(''.join(f'{digest(safe_file(root, name).read_bytes())}  {name}\n' for name in files))
    return targets[0]


def smoke(archive, root=ROOT):
    validate_archive(archive, root)
    # A new allocation outside the checkout; only already-validated names can extract.
    with tempfile.TemporaryDirectory(prefix='ghostproof-package-smoke-') as scratch:
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(scratch)
        extracted = Path(scratch) / 'ghostproof'
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'GHOSTPROOF_EXTRACTED_SMOKE': '1'}
        commands = [
            ['python3', 'tools/validate_release.py'],
            ['node', '--check', 'demo/app.js'],
            ['node', '--check', 'demo/game.js'],
            ['node', '--test', 'tests/game.test.js', 'tests/client.test.js'],
            ['python3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test*.py', '-v'],
            ['python3', 'tools/build_site.py'],
            ['python3', 'tools/package_release.py'],
        ]
        for command in commands:
            subprocess.run(command, cwd=extracted, env=env, check=True, timeout=60)
        # Package bytes must be reproducible after a clean build/extraction.
        if digest((extracted / 'dist' / NAME).read_bytes()) != digest(Path(archive).read_bytes()):
            raise ValueError('Extracted package is not reproducible')
    print('Fresh extracted-package smoke PASS: actual game/client tests, full hunts/reset, build, deterministic repack.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    archive = package()
    print('Packaged:', archive)
    print('SHA-256:', digest(archive.read_bytes()))
    if args.smoke:
        smoke(archive)

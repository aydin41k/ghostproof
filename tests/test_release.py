"""Clean-package, publishing boundaries and local URL smoke coverage."""
import contextlib
import functools
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_site import build, safe_file, SITE_FILES
from package_release import package, smoke
from validate_release import validate, validate_archive, file_list, scan_text, CONTENT_SHA256


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='ghostproof-release-test-')
        self.root = Path(self.scratch.name) / 'source'
        self.root.mkdir()
        for name in file_list(ROOT):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def tearDown(self):
        self.scratch.cleanup()

    def test_clean_source_has_exact_contract(self):
        self.assertEqual(validate(self.root), file_list(ROOT))
        self.assertEqual(hashlib.sha256((self.root / 'demo/content.json').read_bytes()).hexdigest(), CONTENT_SHA256)
        self.assertNotIn('data', {p.name for p in self.root.iterdir()})

    def test_site_exact_allowlist_no_private_routes_at_root_and_subpath(self):
        site = build(self.root)
        self.assertEqual({p.name for p in site.iterdir()}, set(SITE_FILES))
        parent = Path(self.scratch.name) / 'host'
        parent.mkdir()
        subpath = parent / 'arbitrary-project'
        shutil.copytree(site, subpath)
        for served, prefix in [(site, ''), (parent, '/arbitrary-project')]:
            handler = functools.partial(QuietHandler, directory=str(served))
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f'http://127.0.0.1:{server.server_port}{prefix}/'
                for name in SITE_FILES:
                    with urlopen(base + name, timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.read(), (site / name).read_bytes())
                for path in ['data/sources.json', 'reference/local-preparation/server.py', '.env', 'api/start']:
                    with self.assertRaises(HTTPError) as failure:
                        urlopen(base + path, timeout=5)
                    self.assertEqual(failure.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_rebuild_refuses_unknown_output_and_symlink(self):
        site = build(self.root)
        extra = site / 'unrelated.txt'
        extra.write_text('do not delete')
        with self.assertRaises(ValueError):
            build(self.root)
        self.assertEqual(extra.read_text(), 'do not delete')
        extra.unlink()
        (site / 'index.html').unlink()
        (site / 'index.html').symlink_to(self.root / 'README.md')
        with self.assertRaises(ValueError):
            build(self.root)

    def test_path_escape_and_source_symlinks_rejected(self):
        for name in ['../README.md', '/etc/passwd']:
            with self.assertRaises(ValueError):
                safe_file(self.root, name)
        file = self.root / 'demo/content.json'
        file.unlink()
        file.symlink_to(ROOT / 'demo/content.json')
        with self.assertRaises(ValueError):
            validate(self.root)
        with self.assertRaises(ValueError):
            package(self.root)

    def test_symlinked_root_and_parent_rejected(self):
        alias = Path(self.scratch.name) / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            safe_file(alias, 'demo/index.html')
        with self.assertRaises(ValueError):
            safe_file(alias / 'demo', 'index.html')

    def test_credential_scan_reports_class_not_secret(self):
        sample = 'sk-' + 'A' * 30
        with self.assertRaises(ValueError) as failure:
            scan_text('demo/app.js', sample.encode())
        self.assertNotIn(sample, str(failure.exception))
        self.assertIn('credential token', str(failure.exception))
        for sample in ['/home/' + 'someone/project', '/tmp/' + 'private-run/log', '-----BEGIN ' + 'PRIVATE KEY-----']:
            with self.assertRaises(ValueError):
                scan_text('README.md', sample.encode())

    def test_forbidden_source_file_and_environment_file_rejected(self):
        for name in ['.env', 'raw-response.json', 'debug.log', 'data/sources.json']:
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_text('should never ship')
            with self.assertRaises(ValueError):
                validate(self.root)
            path.unlink()

    def test_missing_changed_content_and_reference_rejected(self):
        for name in ['demo/content.json', 'reference/local-preparation/spooky_rounds.py']:
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b'\n')
            with self.assertRaises(ValueError):
                validate(self.root)
            with self.assertRaises(ValueError):
                build(self.root)
            path.write_bytes(original)
        (self.root / 'demo/content.json').unlink()
        with self.assertRaises(ValueError):
            validate(self.root)

    def test_package_exact_allowlist_no_generated_recursion_and_reproducibility(self):
        build(self.root)
        archive = package(self.root)
        original = archive.read_bytes()
        self.assertEqual(validate_archive(archive, self.root), file_list(self.root))
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(bundle.namelist(), ['ghostproof/' + name for name in file_list(self.root)])
            self.assertFalse(any('/site/' in name or '/dist/' in name or '/data/' in name for name in bundle.namelist()))
        self.assertEqual(package(self.root).read_bytes(), original)
        checksum = (archive.parent / (archive.name + '.sha256')).read_text().split()[0]
        self.assertEqual(checksum, hashlib.sha256(original).hexdigest())
        self.assertEqual(len((archive.parent / 'source-manifest.sha256').read_text().splitlines()), len(file_list(self.root)))

    def test_archive_extra_traversal_duplicate_and_changed_member_fail_closed(self):
        archive = package(self.root)
        clean = archive.read_bytes()
        for name in ['ghostproof/../../escape', 'ghostproof/.env', 'ghostproof/demo/index.html']:
            archive.write_bytes(clean)
            with contextlib.redirect_stderr(None):
                with zipfile.ZipFile(archive, 'a') as bundle:
                    bundle.writestr(name, 'bad')
            with self.assertRaises(ValueError):
                validate_archive(archive, self.root)
        archive.write_bytes(clean)
        (self.root / 'README.md').write_text('different')
        with self.assertRaises(ValueError):
            validate_archive(archive, self.root)

    def test_archive_output_symlink_rejected(self):
        dist = self.root / 'dist'
        dist.mkdir()
        (dist / 'ghostproof-1.0.0.zip').symlink_to(self.root / 'README.md')
        with self.assertRaises(ValueError):
            package(self.root)

    def test_no_runtime_external_assets_or_absolute_game_routes(self):
        app = (self.root / 'demo/app.js').read_text()
        html = (self.root / 'demo/index.html').read_text()
        css = (self.root / 'demo/styles.css').read_text()
        self.assertNotIn('/api/', app)
        self.assertNotIn('href="/', html)
        self.assertNotIn('src="/', html)
        self.assertNotIn('@import', css)
        self.assertNotIn('url(', css)

    def test_ci_and_pages_permission_trigger_and_artifact_boundaries(self):
        validate(self.root)
        pages = self.root / '.github/workflows/pages.yml'
        original = pages.read_text()
        for changed in [original.replace('workflow_dispatch:', 'push:'),
                        original.replace('path: site/', 'path: ./'),
                        original.replace('needs: build', 'needs: other'),
                        original.replace('name: github-pages', 'name: other')]:
            pages.write_text(changed)
            with self.assertRaises(ValueError):
                validate(self.root)
        pages.write_text(original)
        ci = self.root / '.github/workflows/ci.yml'
        ci.write_text(ci.read_text().replace('contents: read', 'contents: write'))
        with self.assertRaises(ValueError):
            validate(self.root)

    @unittest.skipIf(os.environ.get('GHOSTPROOF_EXTRACTED_SMOKE') == '1', 'Avoid recursive extraction only; other boundary tests still run')
    def test_fresh_extraction_actual_game_render_tests_build_and_repack(self):
        smoke(package(self.root), self.root)


if __name__ == '__main__':
    unittest.main()

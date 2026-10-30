"""Build exactly five browser files; never serve the source repository."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE_FILES = ('index.html', 'styles.css', 'app.js', 'game.js', 'content.json')


def safe_file(root, relative):
    root = Path(root).absolute()
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Path escape rejected')
    target = root / relative
    for part in (root, *root.parents):
        if part.is_symlink():
            raise ValueError('Symlink ancestor rejected')
    for index in range(1, len(relative.parts) + 1):
        if root.joinpath(*relative.parts[:index]).is_symlink():
            raise ValueError('Symlink rejected')
    if not target.is_file():
        raise ValueError(f'Missing allowlisted file: {relative}')
    return target


def build(root=ROOT):
    root = Path(root).absolute()
    from validate_release import validate
    validate(root)
    sources = [(name, safe_file(root, 'demo/' + name)) for name in SITE_FILES]
    output = root / 'site'
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('Unsafe generated site target')
    if output.exists():
        actual = {p.name for p in output.iterdir()}
        if actual - set(SITE_FILES):
            raise ValueError('Unexpected files in generated site; refusing replacement')
        for path in output.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ValueError('Unsafe generated site member')
    output.mkdir(exist_ok=True)
    for name, source in sources:
        shutil.copyfile(source, output / name)
    return output


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print('Built narrow static site:', build())

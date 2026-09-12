#!/usr/bin/env python3
"""Publish classified office build-ups over the complete pinned facility."""
import argparse
import json
import shutil
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from usdaeco_buildup import register_plugins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    os.environ.setdefault('AECO_DATACENTRE_ROOT', str(ROOT.parent / 'usdaeco-datacentre'))
    os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')
    register_plugins()
    from usdaeco_buildup.datacentre import hook
    from usdaeco_check.example import run_example
    from usdaeco_render import render
    example = Path(__file__).resolve().parent
    manifest = run_example(example, hook, variant='clash', keywords=[], size=(960, 600), publish=args.publish)
    print('== stage: exploded WC section', flush=True)
    manifest['renders'] += render(example / 'out/exploded.usda', output=example / 'out/renders',
                                  size=(960, 600), views=['exploded'])
    (example / 'out/manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    if args.publish:
        shutil.copyfile(example / 'out/renders/exploded.png', example / 'renders/exploded.png')
        shutil.copyfile(example / 'out/manifest.json', example / 'manifest.json')



if __name__ == '__main__':
    main()

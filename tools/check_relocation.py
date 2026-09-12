#!/usr/bin/env python3
"""Prove committed results against fresh runs in two checkout layouts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
KIT = Path(os.environ.get('TOOLCHAIN_DIR', ROOT.parent / 'usdaeco-toolchain')).resolve()
sys.path[:0] = [str(ROOT / 'tools'), str(KIT / 'tools')]
from usdaeco_check import Report
from usdaeco_check.example import check_example
from usdaeco_buildup import core_root
from usdaeco_buildup.datacentre import published_source


def main():
    parser = __import__('argparse').ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-current-run', action='store_true',
                        help='Compare current out/ produced by the full gate instead of rerunning it')
    args = parser.parse_args()
    report = Report()
    os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')
    print('== stage: ResultStale current layout', flush=True)
    report.add(check_example(ROOT / 'examples/datacentre', execute=not args.reuse_current_run))
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                                    cwd=ROOT, text=True).split('\0')
    with tempfile.TemporaryDirectory(prefix='buildup-relocation-') as directory:
        temporary = Path(directory).resolve()
        checkout = temporary / 'review/nested/library'
        for name in sorted(set(paths)):
            path = ROOT / name
            if name and path.is_file() and not path.is_symlink():
                target = checkout / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        source, _ = published_source()
        data = temporary / 'releases/facility'
        (data / 'dist').mkdir(parents=True)
        shutil.copytree(source.parent, data / 'dist/clash')
        shutil.copyfile(source.parents[2] / 'library.json', data / 'library.json')
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'AECO_DATACENTRE_STAGE')}
        env.update(TOOLCHAIN_DIR=str(KIT), AECO_CORE_ROOT=str(core_root().resolve()),
                   CORE_PLUGIN_DIR=str(Path(os.environ.get('CORE_PLUGIN_DIR', core_root() / 'out/plugins/usdAeco/resources')).resolve()),
                   AECO_DATACENTRE_ROOT=str(data))
        print('== stage: ResultStale relocated checkout and source', flush=True)
        process = subprocess.run([sys.executable, '-c', '''
import sys
sys.path.insert(0, sys.argv[1])
from usdaeco_check.example import check_example
result = check_example(sys.argv[2])
print(result.name, 'PASS' if result.ok else 'FAIL', result.detail)
raise SystemExit(0 if result.ok else 1)
''', str(KIT / 'tools'), str(checkout / 'examples/datacentre')], env=env, cwd=checkout,
                                 capture_output=True, text=True, timeout=300)
        report.check('ResultStale relocated layout', process.returncode == 0, process.stdout.strip() or process.stderr[-1200:])
    return report.finish()


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations
import argparse
from pathlib import Path
import sys
from .matrix import run_matrix
from .report import summarize
from .runner import ROOT


def main() -> int:
    parser=argparse.ArgumentParser(description='Local formal-model experiments; no network/device targets')
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run');run.add_argument('matrix',type=Path);run.add_argument('--only');run.add_argument('--proverif')
    summary=sub.add_parser('summary');summary.add_argument('--raw',type=Path,default=ROOT/'experiments/raw')
    summary.add_argument('--output',type=Path,default=ROOT/'experiments/processed')
    args=parser.parse_args()
    try:
        if args.command=='summary': print(summarize(args.raw,args.output));return 0
        # This import is our read-only checker, never the historical module.
        sys.path.insert(0,str(ROOT/'scripts'))
        from check_environment import check
        environment=check(args.proverif)
        if not environment['ok']: raise RuntimeError(str(environment))
        paths=run_matrix(args.matrix,environment['proverif'],environment['proverif_version'],only=args.only)
        import json
        return 1 if any(json.loads((p/'metadata.json').read_text())['status']=='ERROR' for p in paths) else 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2

if __name__=='__main__': raise SystemExit(main())

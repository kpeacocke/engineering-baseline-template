from __future__ import annotations

import argparse
import subprocess
import sys

from .common import FactoryError, split_repo, validate_repo_name
from .local import slug_python
from .workflows import adopt_repo, apply_update_local, create, doctor, update


def self_test() -> int:
    assert validate_repo_name("my-project") == "my-project"
    try: validate_repo_name("bad/name")
    except FactoryError: pass
    else: raise AssertionError("invalid repository name accepted")
    assert split_repo("owner/repo") == ("owner", "repo")
    assert split_repo("repo", "owner") == ("owner", "repo")
    assert slug_python("my-api") == "my_api"
    print("SELF-TEST: PASS"); return 0


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description="Engineering baseline project factory: create, adopt, verify and update governed repositories")
    sub=p.add_subparsers(dest="command",required=True)
    n=sub.add_parser("new",help="create a new governed repository from the golden template"); n.add_argument("name"); n.add_argument("--profile",choices=["generic","python","ansible"],default="generic"); n.add_argument("--owner"); n.add_argument("--allow-other-owner",action="store_true")
    vis=n.add_mutually_exclusive_group(); vis.add_argument("--private",action="store_true"); vis.add_argument("--public",action="store_true")
    n.add_argument("--description"); n.add_argument("--directory"); n.add_argument("--template"); n.add_argument("--ansible-namespace"); n.add_argument("--ansible-collection"); n.add_argument("--no-wait",action="store_true"); n.add_argument("--timeout",type=int,default=900); n.set_defaults(func=create)
    a=sub.add_parser("adopt",help="adopt the baseline into an existing repository through a pull request"); a.add_argument("repo"); a.add_argument("--profile",choices=["generic","python","ansible"],required=True); a.add_argument("--directory"); a.add_argument("--template"); a.add_argument("--merge",action="store_true"); a.add_argument("--no-wait",action="store_true"); a.add_argument("--timeout",type=int,default=900); a.set_defaults(func=adopt_repo)
    d=sub.add_parser("doctor",help="verify baseline files, GitHub settings and update-source configuration"); d.add_argument("repo",nargs="?"); d.add_argument("--template"); d.set_defaults(func=doctor)
    u=sub.add_parser("update",help="open a pull request updating a governed repository to this baseline version"); u.add_argument("repo",nargs="?"); u.add_argument("--template"); u.add_argument("--merge",action="store_true"); u.add_argument("--no-wait",action="store_true"); u.add_argument("--timeout",type=int,default=900); u.set_defaults(func=update)
    l=sub.add_parser("local-doctor",help=argparse.SUPPRESS); l.set_defaults(func=lambda args: __import__("_project_factory.local",fromlist=["local_doctor"]).local_doctor(__import__("pathlib").Path.cwd()) or 0)
    au=sub.add_parser("apply-update",help=argparse.SUPPRESS); au.add_argument("--source",required=True); au.set_defaults(func=apply_update_local)
    s=sub.add_parser("self-test",help="run non-network project-factory contract checks"); s.set_defaults(func=lambda args:self_test())
    return p


def main() -> int:
    args=parser().parse_args(); return int(args.func(args))


def entrypoint() -> None:
    try: raise SystemExit(main())
    except subprocess.TimeoutExpired as exc: print(f"RESULT: FAIL — command timed out: {exc.cmd}",file=sys.stderr); raise SystemExit(1)
    except Exception as exc: print(f"RESULT: FAIL — {exc}",file=sys.stderr); raise SystemExit(1)

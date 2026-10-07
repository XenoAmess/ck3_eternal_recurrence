"""Reject newly introduced merge commits without rewriting published history."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


OID = re.compile(r'^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$')


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise ValueError('Git history could not be read; fetch and rebase first: ' + result.stderr.strip())
    return result.stdout.strip()


def commit(repo, oid):
    if not OID.fullmatch(oid) or set(oid) == {'0'}:
        raise ValueError('A nonzero actual commit OID is required.')
    return git(repo, 'rev-parse', '--verify', oid + '^{commit}')


def check_range(repo, base, head, label):
    base, head = commit(repo, base), commit(repo, head)
    merges = git(repo, 'rev-list', '--min-parents=2', head, '--not', base).splitlines()
    if merges:
        raise ValueError(label + ': new merge commits are forbidden: ' + ', '.join(merges)
                         + '. Preserve published history; fetch and rebase, then ordinary push.')
    print(label + ': no new merge commits (' + base + '..' + head + ')')


def pre_push(repo, lines):
    for line in lines:
        fields = line.split()
        if len(fields) != 4:
            raise ValueError('Malformed pre-push input; refusing the push.')
        local_ref, local_oid, remote_ref, remote_oid = fields
        if not OID.fullmatch(local_oid) or not OID.fullmatch(remote_oid):
            raise ValueError('Malformed pre-push OID; refusing the push.')
        if set(local_oid) == {'0'}:
            continue
        if set(remote_oid) == {'0'}:
            # A new ref has no remote old tip. Exclude the published master
            # baseline, never the local branch or --first-parent ancestry.
            base = git(repo, 'rev-parse', '--verify', 'refs/remotes/origin/master^{commit}')
        else:
            base = remote_oid
        check_range(repo, base, local_oid, local_ref + ' -> ' + remote_ref)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path.cwd())
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--range', nargs=2, metavar=('BASE', 'HEAD'))
    mode.add_argument('--event-file', type=Path)
    mode.add_argument('--pre-push', action='store_true')
    mode.add_argument('--pre-merge-commit', action='store_true')
    mode.add_argument('--pre-commit', action='store_true')
    args = ap.parse_args()
    try:
        if args.pre_merge_commit:
            raise ValueError('Merge commits are forbidden in this repository; fetch and rebase instead.')
        if args.pre_commit:
            merge_head = Path(git(args.repo, 'rev-parse', '--git-path', 'MERGE_HEAD'))
            if not merge_head.is_absolute():
                merge_head = args.repo / merge_head
            if merge_head.exists():
                raise ValueError('A pending merge commit is forbidden; preserve work and use rebase instead.')
        elif args.pre_push:
            pre_push(args.repo, sys.stdin)
        elif args.event_file:
            event = json.loads(args.event_file.read_text(encoding='utf-8'))
            if 'pull_request' in event:
                # Use real PR head, never the runner's synthetic merge SHA.
                base = event['pull_request']['base']['sha']
                head = event['pull_request']['head']['sha']
            else:
                base, head = event['before'], event['after']
            check_range(args.repo, base, head, 'GitHub actual event range')
        else:
            check_range(args.repo, *args.range, 'Requested range')
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

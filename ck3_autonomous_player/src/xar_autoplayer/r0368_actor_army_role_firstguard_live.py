"""Use the queued wake pair through the existing R0368 managed entry.

Every mode requires explicit new manifest hashes. The existing source, prepare,
read and cleanup code is reused within this process; historical providers are
restored on exit. No existing source file or historical manifest is rewritten.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import sys

from . import r0368_actor_army_role_live as original_entry
from . import r0368_actor_army_role_operator as original_role
from . import r0368_actor_army_role_outer_contract as original_outer
from .r0368_actor_army_role_firstguard_pair import verify_firstguard_source_pair


@contextmanager
def firstguard_pair_provider(*, expected_candidate_sha256: str,
                             expected_release_pair_sha256: str):
    """Select one explicitly pinned source provider for this CLI invocation."""
    def verified_source(**kwargs):
        return verify_firstguard_source_pair(
            **kwargs, expected_candidate_sha256=expected_candidate_sha256,
            expected_release_pair_sha256=expected_release_pair_sha256,
        )

    saved_role = original_role.verify_no_launch_source_pair
    saved_outer = original_outer.verify_no_launch_source_pair
    try:
        original_role.verify_no_launch_source_pair = verified_source
        original_outer.verify_no_launch_source_pair = verified_source
        yield
    finally:
        original_role.verify_no_launch_source_pair = saved_role
        original_outer.verify_no_launch_source_pair = saved_outer


def main(argv=None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--help" in arguments or "-h" in arguments:
        print("Queued wake pair: additionally required in every mode:\n"
              "  --expected-candidate-sha256 SHA256\n"
              "  --expected-release-pair-sha256 SHA256\n")
        return original_entry.main(["--help"])
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--expected-candidate-sha256", required=True)
    parser.add_argument("--expected-release-pair-sha256", required=True)
    pins, forwarded = parser.parse_known_args(arguments)
    with firstguard_pair_provider(
        expected_candidate_sha256=pins.expected_candidate_sha256,
        expected_release_pair_sha256=pins.expected_release_pair_sha256,
    ):
        return original_entry.main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())

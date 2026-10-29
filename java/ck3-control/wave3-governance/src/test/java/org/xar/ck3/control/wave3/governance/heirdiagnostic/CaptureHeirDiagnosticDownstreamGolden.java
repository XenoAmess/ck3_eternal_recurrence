package org.xar.ck3.control.wave3.governance.heirdiagnostic;

/** Existing capture definition, executed only inside Root's one source-qualified host/client CI session. */
public final class CaptureHeirDiagnosticDownstreamGolden {
    private CaptureHeirDiagnosticDownstreamGolden() { }

    /** No main, Java child, replacement transport or second Python bootstrap is permitted here. */
    public static String source() {
        return """
                def run_heir_consumer_projection_probe_v1(*, config:'JavaProjectionServiceV1', repository:'Path',
                        ranking_ref:'ExactRefV1', diagnostic_ref:'ExactRefV1', intake_ref:'ExactRefV1',
                        fixture_root:'Path')->dict[str,object]:
                    import sys
                    from pathlib import Path
                    if not isinstance(repository,Path):
                        raise ValueError('typed actual repository path required')
                    repository=repository.resolve()
                    for relative in ('ck3_autonomous_player/src','ck3_autonomous_player/tests/unit'):
                        sys.path.insert(0,str(repository/relative))
                    from test_family_marriage_formal_consumer import run_actual_heir_consumer_probe_v1
                    return run_actual_heir_consumer_probe_v1(config=config,repository=repository,
                        ranking_ref=ranking_ref,diagnostic_ref=diagnostic_ref,intake_ref=intake_ref,
                        fixture_root=fixture_root)
                """;
    }
}

package org.xar.ck3.control.application.action.council;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Model transport regression only; the separate writer integration tests must exercise the real ISSUED issuer. */
public final class NativeTransportCouncilFixture {
    private NativeTransportCouncilFixture() { }
    public static CouncilContinuationPermit issue(String actionId, String originalAttempt, String requestId,
            Stage stage, GuardEvidence guard, NativeRequest prepared, Runnable verifyIssued) {
        ExactRef original = guard.source().sourceRef();
        Request request = new Request(new Scope(actionId, "a".repeat(64), originalAttempt), requestId, stage,
                original, original, guard, Instant.now(), guard.validUntil(), 1, List.of(original));
        return new CouncilContinuationPermit(request, prepared, verifyIssued, Clock.systemUTC());
    }
}

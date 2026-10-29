package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.service.root.StatusCapabilityFailure;

/** Actual source-produced Status failure through each existing public consumer, with no second producer call. */
public final class PublicStatusCapabilityRpcAssertions {
    public static final String TOOL = "ck3_read_tactical_daily_sentinel_status_private_v1";
    private PublicStatusCapabilityRpcAssertions() { }

    public static void assertOriginal(PublicPlanningRpcAssertions.Consumer consumer,
            StatusCapabilityFailure original) throws Exception {
        Objects.requireNonNull(original);
        var result = PublicSourceFailureRpcAssertions.assertOriginal(consumer, TOOL, "{}", original,
                Optional.of(PublicServiceFailure.Kind.UNSUPPORTED_STEP));
        if (consumer == PublicPlanningRpcAssertions.Consumer.DIRECTORY) {
            var service = result.orElseThrow();
            assertEquals(Optional.of(original.originalHello()), service.originalCandidate());
            assertSame(original, service.getCause());
            assertSame(original, service.originalFailure().orElseThrow());
            assertTrue(service.nativeAttributes().isEmpty());
            assertTrue(service.preSubmissionDefaults().isEmpty());
        } else assertTrue(result.isEmpty(), "original RPC serializes the error message, not the Java cause");
    }
}

package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertFailureProducerFixture;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService;

/** Actual finite software Native/read/writer failure producer -> public mapper/Directory/both RPC.
 * The selected producer fixture remains the sole private QueryFailure issuer; this test creates no fault DTO or Root qualification. */
final class PublicFactionFailureBoundaryTest {
    @TempDir Path root;
    private static final String NAME="ck3_query_player_faction_alerts_v1";
    private static final String ARGUMENTS="{\"expected_revision\":1}";

    @Test void actualFailedReadProofKeepsNativeRejectionClassMessageAndOriginalCandidateAtEveryBoundary() throws Exception {
        for(var consumer:PublicPlanningRpcAssertions.Consumer.values()) {
            // Every consumer gets an independent real read/writer fixture; no mutation or UNKNOWN request is resent.
            var produced=FactionAlertFailureProducerFixture.actualNativeRejected(root.resolve(consumer.name()));
            assertEquals(1,produced.nativeReads());assertEquals(0,produced.nativeActions());
            var original=produced.failure();assertEquals(FactionAlertReadService.QueryFailureKind.NATIVE_COMMAND_REJECTED,original.kind());
            PublicSourceFailureRpcAssertions.assertOriginal(consumer,NAME,ARGUMENTS,original,
                    Optional.of(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED)).ifPresent(value->{
                assertSame(original.originalCandidate().orElseThrow(),value.originalCandidate().orElseThrow());
                assertSame(original,value.originalFailure().orElseThrow());assertSame(original,value.getCause());
                var retained=(FactionAlertReadService.QueryFailure)value.originalFailure().orElseThrow();
                assertEquals(original.preparedCandidate(),retained.preparedCandidate());
                assertEquals(original.actualRequestId(),retained.actualRequestId());
                assertTrue(value.nativeAttributes().isEmpty());assertTrue(value.preSubmissionDefaults().isEmpty());
            });
        }
    }

    @Test void actualRevisionPreflightKeepsOriginalBridgeClassAndNoInventedNativeReference() throws Exception {
        for(var consumer:PublicPlanningRpcAssertions.Consumer.values()) {
            var original=FactionAlertFailureProducerFixture.actualRevisionMismatch(root.resolve(consumer.name()));
            assertEquals(FactionAlertReadService.QueryFailureKind.BRIDGE_UNAVAILABLE,original.kind());
            assertTrue(original.originalCandidate().isEmpty());assertTrue(original.preparedCandidate().isEmpty());
            assertTrue(original.actualRequestId().isEmpty());
            PublicSourceFailureRpcAssertions.assertOriginal(consumer,NAME,ARGUMENTS,original,
                    Optional.of(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE)).ifPresent(value->{
                assertTrue(value.originalCandidate().isEmpty());assertSame(original,value.originalFailure().orElseThrow());
                assertTrue(value.preSubmissionDefaults().isEmpty(),"this original faction branch is BridgeUnavailable, not pre-submission mismatch");
            });
        }
    }
}

package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;

/** Exact public route/field guard only. Actual retired-UNKNOWN/private-material recovery is a
 * mandatory Core restore integration test; no Context or private attempt is fabricated here. */
final class RootPublicStepRetainedRestoreTest {
    private static PublicPlanningCodec.ExecuteRequest decode(String json) {
        return PublicPlanningCodec.decodeExecute(new PublicBindings.Value(new RawJson(json.getBytes(StandardCharsets.UTF_8))));
    }
    @Test void realPublicCodecRetainsMissingNullAndFullWidthRevisionForTheDedicatedRequest() {
        var missing=RootPublicStepExecution.retainedRestoreRequest(decode("{\"step\":\"restore-checkpoint\"}"));
        var nil=RootPublicStepExecution.retainedRestoreRequest(decode("{\"step\":\"restore-checkpoint\",\"expected_revision\":null}"));
        var wide=RootPublicStepExecution.retainedRestoreRequest(decode("{\"step\":\"restore-checkpoint\",\"expected_revision\":\"18446744073709551615\"}"));
        assertInstanceOf(RootCheckpointPublicCalls.MissingRevision.class,missing.expectedRevision());
        assertInstanceOf(RootCheckpointPublicCalls.NullRevision.class,nil.expectedRevision());
        assertEquals(new BigInteger("18446744073709551615"),assertInstanceOf(RootCheckpointPublicCalls.ExactRevision.class,wide.expectedRevision()).value());
    }
    @Test void noOtherLifecycleOrGameplayCallerCanBypassCurrentRootResolution() {
        for(String step:List.of("save-checkpoint","death-terminal","start-next-episode","continue-as-reconciled-successor","pause-map"))
            assertThrows(IllegalArgumentException.class,()->RootPublicStepExecution.retainedRestoreRequest(decode("{\"step\":\""+step+"\"}")));
        for(String invalid:List.of("true","1.0","18446744073709551615","\"018446744073709551615\""))
            assertThrows(IllegalArgumentException.class,()->decode("{\"step\":\"restore-checkpoint\",\"expected_revision\":"+invalid+"}"));
    }
}

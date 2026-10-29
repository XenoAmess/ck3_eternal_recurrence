package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;

/** Native-transport consumer of the application test artifact's actual Python vectors. No Root/Game authority. */
final class ArmyWarPublicResultServiceTest {
    @Test void actualServiceReplyAndEncoderConsumeCompleteOriginalPublicVectors()throws Exception {
        var vectors=ArmyWarPublicResultCodecTest.originalPublicVectors();assertEquals(4,vectors.size());
        for(var vector:vectors) {
            var scope=vector.scope();var context=scope.context();byte[] original=vector.receipt().original().originalFrame().bytes().clone();
            // Explicit typed software DATA. This is not a central acquired frame, scope, Native permit or submission.
            var frame=new Complete(context.before(),context.source(),context.sessionId(),BigInteger.ONE,scope.currentSnapshot(),
                    context.source().sourceRef(),Instant.parse(context.source().observedAtUtc()),"c".repeat(64));
            var selection=new ArmyWarReads.Selection(scope.call(),new ArmyRetreatFrames.Current(frame,context.deadline()),Optional.empty());
            var reply=new ArmyWarReadService.Reply(selection,new PlanningReadResult.Known<>(vector.observed(),vector.receipt(),context.source().sourceRef()));
            var encoded=ArmyWarReadService.encode(reply);var restored=ArmyPublicWire.decodeExactSourceBound(encoded,context);
            assertEquals(vector.expectedPublic(),restored);assertEquals(encoded,ArmyPublicWire.encodeExactSourceBound(restored,context));
            assertArrayEquals(original,vector.receipt().original().originalFrame().bytes());assertEquals(vector.observed(),ArmyWarReadCodec.decode(scope,vector.receipt()));
        }
    }
}

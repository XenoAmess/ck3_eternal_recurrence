package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Actual finite guarded writer/archive, with no active successor continuation. Private active-source tests are Life18.
 * Request construction must neither observe a Native frame nor imply action permission or a preclock original.
 */
final class AdvancePrimitiveSessionPreparationTest {
    @TempDir Path temporary;
    private static final AdvanceObservationPort NO_PREPARATION_OBSERVATION=new AdvanceObservationPort(){
        @Override public Frame current(ActionCommand command,Instant deadline){throw new AssertionError("preparation must not sample a replacement frame");}
        @Override public Frame next(ActionCommand command,ObservationIdentity after,Instant deadline){throw new AssertionError("preparation must not advance or poll");}
    };
    private static ActionCommand command(ActionCommand actual,String operation){
        var key=new OperationKey(operation);var args=new Obj(Map.of());
        return new ActionCommand(actual.actionId(),actual.before(),actual.source(),actual.sessionId(),key,args,
                AdvancePrimitives.expected(actual.before(),actual.source(),key,args),actual.claims(),actual.deadline());
    }
    private static ClockStatusRead status(ActionWriterIntegrationFixture actual){
        // This query is not installed or executed by these request-only tests; the registered object is DATA.
        return new ClockStatusRead(actual.reads,ClockStatusRead.registeredContract(actual.observationSource().sourceRef()),actual.archive);
    }
    @Test void originalOrdinaryConstructorPreparesRegisteredPrimitivesAndActualArchiveRetainsTheirExactWire()throws Exception{
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("ordinary-request"),false)){
            var original=actual.command("primitive-original");var primitive=new AdvancePrimitives(NO_PREPARATION_OBSERVATION,status(actual),Clock.systemUTC(),8);
            BigInteger start=original.before().frame().identity().dateRaw();
            var operations=List.of("pause-map","resume-map","set-speed-1",ClockStatusRead.CANCEL_PREFIX+"37",
                    ClockStatusRead.ARM_PREFIX+start+"-to-"+start.add(AdvancePlan.DAY)+"-speed-1-mode-terminal-a-0");
            int reads=actual.nativePacketReads(),writes=actual.nativeActionWrites();
            actual.writer.locked(same->{
                var archive=actual.archive.withSession(same);long before=same.head().state().sequence();
                for(String operation:operations){
                    var command=command(original,operation);var produced=primitive.prepare(same,command,RequestIds.forCommand(command));
                    var ref=archive.preserveRequest(produced);var loaded=archive.loadRequest(ref);
                    assertEquals(produced,loaded);assertEquals(ref,archive.requestReferenceOf(loaded));
                    assertEquals(operation,loaded.step());assertArrayEquals("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8),loaded.additionalFields().bytes());
                    assertTrue(loaded.preparationEvidence().isEmpty());
                    assertEquals(AdvancePrimitives.prepareRequest(command),loaded);
                }
                assertEquals(before,same.head().state().sequence());return null;
            });
            assertEquals(reads,actual.nativePacketReads());assertEquals(writes,actual.nativeActionWrites());
        }
    }
    @Test void inactiveSharedScopePreservesOrdinaryRequestAndNeverResolvesAPrivateSourceOrBorrowedSubstitute()throws Exception{
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("inactive-scope"),false)){
            var command=command(actual.command("ordinary-resume"),"resume-map");
            var scope=new PendingUiLifeAdvance.Scope(()->{throw new AssertionError("inactive ordinary preparation must not ask for a private session/source");});
            var primitive=new AdvancePrimitives(NO_PREPARATION_OBSERVATION,status(actual),Clock.systemUTC(),8,scope);
            var ordinary=primitive.prepare(command);assertFalse(scope.active());
            actual.writer.locked(same->{
                var canonical=primitive.prepare(same,command,RequestIds.forCommand(command));
                assertEquals(ordinary,canonical);assertTrue(canonical.preparationEvidence().isEmpty());
                var archive=actual.archive.withSession(same);assertEquals(canonical,archive.loadRequest(archive.preserveRequest(canonical)));
                return null;
            });
            assertThrows(NullPointerException.class,()->primitive.prepare(null,command,RequestIds.forCommand(command)));
            assertFalse(scope.active());
        }
    }
}

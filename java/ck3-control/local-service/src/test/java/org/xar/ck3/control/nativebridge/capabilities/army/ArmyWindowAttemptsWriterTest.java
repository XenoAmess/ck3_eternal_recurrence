package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;

/** Physical writer/archive and controlled transport packets. This grants no native build or Game qualification. */
final class ArmyWindowAttemptsWriterTest {
    @TempDir Path temporary;
    @Test void realReadPreparationAndActualOutcomesReachTheSameSourceWithoutRewritingObservedAsFailed()throws Exception{
        var store=new AtomicReference<ArmyWindowAttempts.Store>();var selected=new AtomicReference<Complete>();
        var installed=new AtomicReference<ReadContract<RawJson>>();var pending=new AtomicReference<ArmyWindowAttempts.Attempt>();
        var failDecode=new AtomicBoolean();var fixtureRef=new AtomicReference<ActionWriterIntegrationFixture>();
        var operation=new OperationKey("query-war-declared-overview-v1");String capability="game.command."+operation.value();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"fixture-window-attempt",source->{
            var contract=new ReadContract<RawJson>("actual-window-attempt-software-contract",operation,Optional.of(capability),capability,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->{
                        var original=new NativeRequest(operation.value(),Optional.of(capability),new RawJson(new byte[]{'{','}'}));
                        var frame=selected.get();var context=new ArmyTypes.Context(request.before(),request.source(),request.sessionId(),request.deadline());
                        store.get().prepared(installed.get(),ArmyWindowCodec.Kind.OVERVIEW,context,frame.connectionGeneration(),request,id,original);
                        try{pending.set(store.get().current(fixtureRef.get().journal.borrowedWriterSession(),frame).overview().orElseThrow());}
                        catch(IOException failure){throw new java.io.UncheckedIOException(failure);}return original;
                    },receipt->{
                        if(failDecode.get())throw new IllegalStateException("controlled strict decoder refusal with retained actual ACK");
                        store.get().observed(installed.get(),receipt);return receipt.original().originalResultToken().orElseThrow();
                    },receipt->receipt.original().originalResultToken().orElseThrow());
            installed.set(contract);return List.of(contract);
        },request->new RawJson("{\"actual_status\":\"retained\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("physical"),false,scenario)){
            fixtureRef.set(fixture);fixture.ready();
            var complete=RootGuardEvidence.loadFrame(fixture.lastNestedRead.get().before().binding(),fixture.archive,fixture.frameLoader());
            selected.set(complete);store.set(new ArmyWindowAttempts.Store(fixture.archive));
            var request=new PlanningReadRequest(complete.identity(),complete.source(),complete.sessionId(),operation,new Obj(Map.of()),Instant.now().plusSeconds(20));
            fixture.writer.locked(same->{
                assertTrue(store.get().current(same,complete).overview().isEmpty());
                var firstResult=fixture.reads.read(same,installed.get(),request);if(!(firstResult instanceof PlanningReadResult.Known<RawJson> known))throw new AssertionError(firstResult);
                var first=pending.get();assertEquals(ArmyWindowAttempts.Status.PENDING,first.status());assertTrue(first.originalOutcome().isEmpty());
                assertEquals(operation.value(),fixture.archive.loadRequest(first.preparedRequest()).step());
                var observed=store.get().current(same,complete).overview().orElseThrow();assertEquals(ArmyWindowAttempts.Status.OBSERVED,observed.status());
                assertEquals(known.receipt().original(),fixture.archive.load(observed.originalOutcome().orElseThrow()));
                assertEquals(observed.requestId(),known.receipt().requestId());assertEquals(2,observed.supportingEvidence().size());
                store.get().recordUnavailable(same,installed.get(),request,new PlanningReadResult.Unavailable<RawJson>("controlled later publication refusal",Optional.of(known.receipt().original())));
                assertEquals(ArmyWindowAttempts.Status.OBSERVED,store.get().current(same,complete).overview().orElseThrow().status());
                failDecode.set(true);
                var failedResult=fixture.reads.read(same,installed.get(),request);if(!(failedResult instanceof PlanningReadResult.Unavailable<RawJson> failed))throw new AssertionError(failedResult);
                assertTrue(failed.original().isPresent());store.get().recordUnavailable(same,installed.get(),request,failed);
                var actual=store.get().current(same,complete).overview().orElseThrow();assertEquals(ArmyWindowAttempts.Status.FAILED,actual.status());
                assertEquals(failed.original().orElseThrow(),fixture.archive.load(actual.originalOutcome().orElseThrow()));
                store.get().recordUnavailable(same,installed.get(),request,new PlanningReadResult.Unavailable<RawJson>("controlled later refusal before any new preparation",Optional.empty()));
                assertEquals(actual.originalOutcome(),store.get().current(same,complete).overview().orElseThrow().originalOutcome());
                assertEquals("failed",org.xar.ck3.control.planning.opportunity.OpportunityJson.text(actual.normalized().get("status"),"status"));
                var stale=new Complete(complete.identity(),complete.source(),complete.sessionId(),complete.connectionGeneration().add(BigInteger.ONE),complete.semantic(),complete.originalEvidence(),complete.observedAt(),complete.fullBindingSha256());
                assertTrue(store.get().current(same,stale).overview().isEmpty());
                fixture.reads.read(same,installed.get(),request);
                store.get().recordUnavailable(same,installed.get(),request,new PlanningReadResult.Unavailable<RawJson>("controlled missing original",Optional.empty()));
                assertThrows(IOException.class,()->store.get().current(same,complete));return null;
            });
        }
    }
}

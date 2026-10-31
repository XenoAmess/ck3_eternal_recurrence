package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing real software transport/collector/Root wrappers/Coordinator/archive; controlled READ only, not a Game. */
public final class FamilyOriginalReadScopeTest {
    @TempDir Path root;
    private static final String STEP="query-family-marriage-send-outgoing-v1-private";
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<ReadContract<RawJson>> selected) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("c".repeat(64),"family-original-source",source->{
            var contract=new ReadContract<RawJson>("family:marriage-send-outgoing:action_preparation/v2",new OperationKey(STEP),Optional.empty(),
                    "allow_private_family_marriage_send_outgoing_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                    ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(STEP,Optional.empty(),new RawJson("{}".getBytes(StandardCharsets.UTF_8))),
                    read->read.original().originalResultToken().orElseThrow(),read->read.original().originalResultToken().orElseThrow());
            selected.set(contract);return List.of(contract);
        },request->new RawJson("{}".getBytes(StandardCharsets.UTF_8)),Optional.of("1.20.0.2"),Set.of());
    }
    private static PlanningReadCoordinator.ReadGuardPort wrappers(ActionWriterIntegrationFixture.SoftwareReadGuardContext actual) {
        var deferred=new RootDeferredAuthorities.ReadGuard();deferred.bind(actual.guard());
        PlanningReadCoordinator.ReadGuardPort other=(head,request,contract)->{throw new AssertionError("software read cannot use another origin");};
        var origin=new RootApplicationAssembly.OriginReads(deferred,null,other,other,other);
        var board=new RootSessionSwitchboard(actual.writer());
        board.installInitial(new RootSessionSwitchboard.View(actual.identity(),(head,command)->{throw new AssertionError("no Game action");},origin,actual.originals()));
        return board;
    }
    @Test void negativeAckRetainsOriginalAfterGuardAndColdFailureRoundtrip()throws Exception { returned(false,false); }
    @Test void unknownRetainsOriginalAfterGuardWithoutSecondReadOrReplay()throws Exception { returned(true,false); }
    @Test void successfulReadDecodesAndPublishesOutsideEndedHeldSource()throws Exception { returned(false,true); }
    private void returned(boolean loseAck,boolean success)throws Exception {
        var selected=new AtomicReference<ReadContract<RawJson>>();
        try(var actual=new ActionWriterIntegrationFixture(root.resolve(success?"success":loseAck?"unknown":"negative"),false,scenario(selected),FamilyOriginalReadScopeTest::wrappers)) {
            if(!success) {if(loseAck)actual.loseReadAckOnce();else actual.rejectNextScenarioRead();}
            var contract=selected.get();var command=actual.command("family-software-read");
            var request=new PlanningReadRequest(command.origin(),command.source(),command.sessionId(),contract.operation(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(15));
            var received=new AtomicInteger();var atReceive=new AtomicInteger(-1);
            actual.writer.locked(same->{
                var result=actual.reads.read(same,contract,request,new PlanningReadCoordinator.ReadLifecycleObserver() {
                    @Override public void prepared(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,ReadContract<?> exact,PlanningReadRequest original,String id,NativeRequest prepared){ }
                    @Override public void received(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,ReadContract<?> exact,PlanningReadRequest original,String id,NativeActionPort.DispatchOutcome outcome)throws IOException {
                        assertSame(same,callback);assertSame(request,original);assertSame(contract,exact);
                        actual.collector.currentHeldOriginal(callback,original,lease->{assertEquals(request.before(),lease.frame().identity());return null;});
                        received.incrementAndGet();atReceive.set(actual.nativeReadWrites());
                    }
                    @Override public void known(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,ReadContract<?> exact,PlanningReadResult.Known<?> known){assertTrue(success);}
                    @Override public void failed(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,ReadContract<?> exact,PlanningReadRequest original,Optional<NativeActionPort.DispatchOutcome> outcome,String reason){assertFalse(success);}
                });
                if(success) {
                    var known=assertInstanceOf(PlanningReadResult.Known.class,result);assertNotNull(known.originalReceipt());
                } else {
                    if(!(result instanceof PlanningReadResult.Unavailable<RawJson> unavailable))
                        throw new AssertionError("technical native failure unexpectedly returned Known");
                    assertEquals("native query returned unavailable or an unbound ACK",unavailable.reason());
                    var failure=unavailable.observedFailure().orElseThrow();
                    assertEquals(failure.before().originalBindingSha256(),failure.after().originalBindingSha256());
                    if(loseAck)assertInstanceOf(NativeActionPort.Unknown.class,failure.original());
                    else assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,failure.original()).nativeOk());
                    var archive=actual.archive.withSession(same);
                    assertEquals(failure,PlanningReadFailureCodec.load(PlanningReadFailureCodec.preserve(failure,archive),archive));
                }
                assertEquals(atReceive.get(),actual.nativeReadWrites(),"after guard and archive replay must not perform another Native read");
                assertThrows(IllegalArgumentException.class,()->actual.collector.currentHeldOriginal(same,request,lease->null),"scope ends after the actual Coordinator wire/after callback");
                return null;
            });
            assertEquals(1,received.get());assertEquals(1,actual.scenarioReadWrites());assertEquals(0,actual.nativeActionWrites());assertEquals(0,actual.snapshot().ledgerSequence());
        }
    }
}

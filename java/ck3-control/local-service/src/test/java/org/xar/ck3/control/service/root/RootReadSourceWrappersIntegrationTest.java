package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.governance.PrivateCouncilReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real collector/guard/Coordinator/transport/archive with the production Root wrappers.
 * Only the existing software packet edge is controlled; this gives no Game/Main qualification. */
public final class RootReadSourceWrappersIntegrationTest {
    @TempDir Path root;

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(
            AtomicReference<ReadContract<CouncilPrivateCodec.Reply>> selected) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(
                "ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d",
                "root-read-source-wrappers",source->{
                    var reads=new PrivateCouncilReads(source);selected.set(reads.gates());return reads.registeredContracts();
                },request->new RawJson("{}".getBytes(StandardCharsets.UTF_8)),Optional.of("1.20.0.2"),Set.of());
    }

    private static PlanningReadCoordinator.ReadGuardPort wrappers(
            ActionWriterIntegrationFixture.SoftwareReadGuardContext actual,
            AtomicReference<RootSessionSwitchboard> retained) {
        var deferred=new RootDeferredAuthorities.ReadGuard();deferred.bind(actual.guard());
        // This test enters gameplay only; other origin-specific authorities are not installed by this fixture.
        PlanningReadCoordinator.ReadGuardPort otherOrigin=(head,request,contract)->{
            throw new AssertionError("gameplay read fixture cannot grant another origin");
        };
        var origin=new RootApplicationAssembly.OriginReads(deferred,null,otherOrigin,otherOrigin,otherOrigin);
        var board=new RootSessionSwitchboard(actual.writer());
        board.installInitial(new RootSessionSwitchboard.View(actual.identity(),
                (head,command)->{throw new AssertionError("read wrapper test cannot submit a Game action");},
                origin,actual.originals()));
        assertTrue(retained.compareAndSet(null,board));return board;
    }

    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual,ReadContract<?> contract)throws Exception {
        var command=actual.command("root-wrapper-original");
        return new PlanningReadRequest(command.origin(),command.source(),command.sessionId(),contract.operation(),
                new OpportunityJson.Obj(Map.of("position_key",new OpportunityJson.Text("councillor_steward"))),
                Instant.now().plusSeconds(15));
    }

    private void actualFailedRead(boolean loseResponse)throws Exception {
        var selected=new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        var board=new AtomicReference<RootSessionSwitchboard>();
        try(var actual=new ActionWriterIntegrationFixture(root.resolve(loseResponse?"unknown":"rejected"),false,
                scenario(selected),original->wrappers(original,board))) {
            if(loseResponse)actual.loseReadAckOnce();else actual.rejectNextScenarioRead();
            var contract=selected.get();var original=request(actual,contract);
            var received=new AtomicInteger();var readsAtReceive=new AtomicInteger(-1);
            var failed=actual.writer.locked(same->{
                var result=actual.reads.read(same,contract,original,new PlanningReadCoordinator.ReadLifecycleObserver() {
                    @Override public void prepared(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,
                            ReadContract<?> exact,PlanningReadRequest requested,String id,NativeRequest prepared) { }
                    @Override public void received(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,
                            ReadContract<?> exact,PlanningReadRequest requested,String id,NativeActionPort.DispatchOutcome outcome)throws IOException {
                        assertSame(same,callback);assertSame(original,requested);assertSame(contract,exact);
                        actual.collector.currentHeldOriginal(callback,requested,lease->{
                            assertEquals(requested.before(),lease.frame().identity());return null;
                        });
                        readsAtReceive.set(actual.nativeReadWrites());received.incrementAndGet();
                    }
                    @Override public void known(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,
                            ReadContract<?> exact,PlanningReadResult.Known<?> known) { fail("technical failure cannot become Known"); }
                    @Override public void failed(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session callback,
                            ReadContract<?> exact,PlanningReadRequest requested,
                            Optional<NativeActionPort.DispatchOutcome> outcome,String reason) { }
                });
                if(!(result instanceof PlanningReadResult.Unavailable<CouncilPrivateCodec.Reply> unavailable))
                    throw new AssertionError("technical native failure unexpectedly returned Known");
                var failure=unavailable.observedFailure().orElseThrow();
                assertNotSame(failure.before(),failure.after());
                assertEquals(failure.before().binding().origin(),failure.after().binding().origin());
                assertEquals(failure.before().originalBindingSha256(),failure.after().originalBindingSha256());
                var scoped=actual.archive.withSession(same);
                assertEquals(failure,PlanningReadFailureCodec.load(PlanningReadFailureCodec.preserve(failure,scoped),scoped));
                assertEquals(readsAtReceive.get(),actual.nativeReadWrites(),"wire and actual after share one physical source; no nested after READ");
                assertThrows(IllegalArgumentException.class,()->actual.collector.currentHeldOriginal(same,original,lease->null),
                        "the actual producer scope must end with the Coordinator callback");
                return failure;
            });
            if(loseResponse)assertInstanceOf(NativeActionPort.Unknown.class,failed.original());
            else assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,failed.original()).nativeOk());
            assertEquals(1,received.get());assertEquals(1,actual.scenarioReadWrites());
            assertEquals(0,actual.nativeActionWrites());assertEquals(0,actual.snapshot().ledgerSequence());
        }
    }

    @Test public void responseWaitUnknownKeepsWireAndAfterInsideAllThreeRootWrappers()throws Exception { actualFailedRead(true); }
    @Test public void negativeAckKeepsWireAndAfterInsideAllThreeRootWrappers()throws Exception { actualFailedRead(false); }

    @Test public void foreignSessionAndUnboundDeferredCannotEnterTheSourceCallback()throws Exception {
        var selected=new AtomicReference<ReadContract<CouncilPrivateCodec.Reply>>();
        var board=new AtomicReference<RootSessionSwitchboard>();
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("foreign"),false,scenario(selected),
                original->wrappers(original,board))) {
            var contract=selected.get();var current=request(actual,contract);
            var foreign=new PlanningReadRequest(current.origin(),current.source(),"retired-session",
                    current.operation(),current.arguments(),current.deadline());
            var entered=new AtomicInteger();int writes=actual.nativeReadWrites();
            actual.writer.locked(same->{
                assertThrows(IllegalArgumentException.class,()->board.get().withOriginalReadSource(same.head(),foreign,contract,entered::incrementAndGet));
                var absent=new RootDeferredAuthorities.ReadGuard();
                assertThrows(IllegalStateException.class,()->absent.withOriginalReadSource(same.head(),current,contract,entered::incrementAndGet));
                return null;
            });
            assertEquals(0,entered.get());assertEquals(writes,actual.nativeReadWrites());
        }
    }
}

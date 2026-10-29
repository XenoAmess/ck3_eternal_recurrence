package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Root link, coordinator, software transport and archive; no private failed proof is constructed. */
final class RootPlanningReadsFailureEvidenceTest {
    @TempDir Path root;
    private static final OperationKey OP=new OperationKey("query-root-failure-evidence-v1");
    private static final String CAP="game.query.root-failure-evidence";
    private static final RawJson JSON=new RawJson("{}".getBytes(StandardCharsets.UTF_8));
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<ReadContract<RawJson>> selected) {
        return new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"root-failure-evidence",source->{
            var contract=new ReadContract<RawJson>("root-failure-evidence/v1",OP,Optional.of(CAP),"root-failure-evidence",
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(request,id)->new NativeRequest(OP.value(),CAP,JSON),
                    receipt->receipt.original().originalResultToken().orElseThrow());
            selected.set(contract);return List.of(contract);
        },request->JSON);
    }
    private static PlanningReadRequest request(ActionWriterIntegrationFixture actual)throws Exception {
        var command=actual.command("root-failed-read");
        return new PlanningReadRequest(command.before(),command.source(),command.sessionId(),OP,
                new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(10));
    }
    @Test void bothFacadeOverloadsRetainTheActualNegativeAckAndPrivateOriginalCustody()throws Exception {
        for(boolean borrowed:List.of(false,true)) {
            var selected=new AtomicReference<ReadContract<RawJson>>();
            try(var actual=new ActionWriterIntegrationFixture(root.resolve("read-"+borrowed),false,scenario(selected))) {
                var facade=new RootPlanningReads(actual.archive.writer());facade.bind(assertInstanceOf(PlanningReadCoordinator.class,actual.reads));actual.rejectNextScenarioRead();
                var requested=request(actual);var captured=new AtomicReference<PlanningReadResult.Unavailable<?>>();var calls=new AtomicInteger();
                PlanningReadPort.FailureEvidenceObserver observer=(same,contract,current,exact,attempt,archive)->{
                    actual.writer.requireSession(same);assertSame(selected.get(),contract);assertSame(requested,current);
                    var proof=attempt.orElseThrow();proof.requireOriginal(same,contract,current,exact,archive);
                    assertFalse(assertInstanceOf(NativeActionPort.AckReceived.class,proof.original()).nativeOk());
                    assertEquals(proof.original(),archive.load(proof.originalRef()));captured.set(exact);calls.incrementAndGet();
                };
                var result=borrowed?actual.writer.locked(same->facade.readWithFailureEvidence(same,selected.get(),requested,observer))
                        :facade.readWithFailureEvidence(selected.get(),requested,observer);
                assertSame(captured.get(),result);assertEquals(1,calls.get());
                assertEquals(1,actual.nativeReadWrites());assertEquals(0,actual.nativeActionWrites());assertTrue(actual.sourceChecks.get()>0);
            }
        }
    }
}

package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Genuine software writer/receiver/guards; capture fails after the returned successful original ACK. */
final class ReadMaterialCaptureFailureTest {
    @TempDir Path directory;
    @Test void sourceCaptureFailureRetainsSuccessfulAckAndOriginalCauseWithoutDecodeRetryOrKnown() throws Exception {
        var operation=new OperationKey("query-current-first-heir-relationship-v1-private");
        var captures=new AtomicInteger();var decodes=new AtomicInteger();var knowns=new AtomicInteger();var failures=new AtomicInteger();
        var installed=new AtomicReference<ReadContract<RawJson>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"material-capture-failure",source->{
            var contract=new ReadContract<RawJson>("software-family-material/v1",operation,Optional.empty(),"software-family-material",
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(operation.value(),Optional.empty(),new RawJson(new byte[]{'{','}'})),
                    receipt->{decodes.incrementAndGet();return receipt.original().originalResultToken().orElseThrow();},
                    receipt->receipt.original().originalResultToken().orElseThrow()).withRetainedMaterialCapture(receipt->{
                        assertTrue(receipt.original().nativeOk());assertTrue(receipt.retainedMaterial().isEmpty());
                        assertEquals(receipt.before().originalBindingSha256(),receipt.after().originalBindingSha256());
                        captures.incrementAndGet();throw new IOException("controlled original export capture unavailable after successful ACK");
                    });
            installed.set(contract);return List.of(contract);
        },request->new RawJson("{\"software_value\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-writer"),false,scenario)) {
            fixture.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver(){
                @Override public void afterKnown(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadResult.Known<?> actual){
                    if(contract==installed.get())knowns.incrementAndGet();
                }
                @Override public void afterUnavailable(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> actual,Optional<PlanningReadCoordinator.FailedReadAttempt> attempt) {
                    if(contract!=installed.get())return;
                    failures.incrementAndGet();var original=attempt.orElseThrow();
                    try{original.requireOriginal(same,contract,request,actual,fixture.archive.withSession(same));}
                    catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                    assertTrue(assertInstanceOf(NativeActionPort.AckReceived.class,original.original()).nativeOk());
                    assertTrue(actual.decodeFailure().isEmpty(),"source export failure is not invented as decoder or post-Known failure");
                    assertEquals(original.originalRef(),actual.observedFailure().orElseThrow().originalRef());
                }
            });
            var ready=fixture.ready();
            fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(60),lease->{
                var request=new PlanningReadRequest(ready.request().before(),ready.request().source(),ready.request().sessionId(),operation,
                        new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(60));
                var actual=fixture.reads.read(same,installed.get(),request);
                if(!(actual instanceof PlanningReadResult.Unavailable<RawJson> unavailable))throw new AssertionError(actual);
                assertTrue(unavailable.reason().contains("controlled original export capture unavailable after successful ACK"));
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,unavailable.original().orElseThrow());
                assertTrue(ack.nativeOk());assertEquals(ack,fixture.archive.withSession(same).load(unavailable.observedFailure().orElseThrow().originalRef()));
                assertEquals(0,same.head().state().sequence());return null;
            }));
            assertEquals(1,captures.get());assertEquals(0,decodes.get());assertEquals(0,knowns.get());assertEquals(1,failures.get());
            assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }
}

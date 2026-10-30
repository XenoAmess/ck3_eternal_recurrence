package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software query/capture/archive/pureReplay boundary; no RootContext or Family business qualification. */
final class ReadMaterialPureReplayTest {
    @TempDir Path temporary;
    @Test void originalCaptureRunsOnceAndColdPureReplayNeverReopensDeletedSourceFolder() throws Exception {
        var operation=new OperationKey("query-current-first-heir-relationship-v1-private");
        var captures=new AtomicInteger();var decodes=new AtomicInteger();var replays=new AtomicInteger();
        var installed=new AtomicReference<ReadContract<RawJson>>();
        var originals=new AtomicReference<ActionPorts.OutcomeArchive>();
        Path folder=temporary.resolve("original-query-export"),export=folder.resolve("source.json");
        byte[] exported=" {\"schema\":\"software-query-export/v1\",\"wide\":18446744073709551615,\"optional\":null} \n".getBytes(StandardCharsets.UTF_8);
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"material-pure-replay",source->{
            var contract=new ReadContract<RawJson>("software-family-retained-material/v1",operation,Optional.empty(),"software-family-material",
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(operation.value(),Optional.empty(),new RawJson(new byte[]{'{','}'})),
                    receipt->{decodes.incrementAndGet();return originals.get().loadMaterial(receipt.retainedMaterial().orElseThrow().original());},
                    receipt->{replays.incrementAndGet();return originals.get().loadMaterial(receipt.retainedMaterial().orElseThrow().original());})
                    .withRetainedMaterialCapture(receipt->{
                        assertTrue(receipt.original().nativeOk());assertTrue(receipt.retainedMaterial().isEmpty());captures.incrementAndGet();
                        return new PlanningReadReceipt.RetainedMaterial(PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT,
                                originals.get().preserveMaterial(new RawJson(Files.readAllBytes(export))));
                    });
            installed.set(contract);return List.of(contract);
        },request->{
            try{Files.createDirectory(folder);Files.write(export,exported,StandardOpenOption.CREATE_NEW);}
            catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}
            return new RawJson("{\"software_export_written\":true}".getBytes(StandardCharsets.UTF_8));
        });
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-writer"),false,scenario)) {
            var ready=fixture.ready();var firstSession=new AtomicReference<ContinuityStorePort.Session>();
            PlanningReadResult.Known<RawJson> known=fixture.writer.locked(same->{
                firstSession.set(same);originals.set(fixture.archive.withSession(same));
                try{return fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(60),lease->{
                    var request=new PlanningReadRequest(ready.request().before(),ready.request().source(),ready.request().sessionId(),operation,
                            new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(60));
                    var result=fixture.reads.read(same,installed.get(),request);
                    if(!(result instanceof PlanningReadResult.Known<RawJson> actual))throw new AssertionError(result);
                    return actual;
                });}finally{originals.set(null);}
            });
            assertEquals(PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4,known.receipt().archiveVersion());
            assertEquals(1,captures.get());assertEquals(1,decodes.get());assertEquals(0,replays.get());assertArrayEquals(exported,known.value().bytes());
            Files.delete(export);Files.delete(folder);assertFalse(Files.exists(folder));
            var cold=NativeArchiveDataCodec.retainedFiles().readData(known.originalReceipt()).receipt();
            assertEquals(known.receipt(),cold);int reads=fixture.nativeReadWrites();byte[] ledger=fixture.ledgerBytes();
            fixture.writer.locked(same->{
                assertNotSame(firstSession.get(),same);originals.set(fixture.archive.withSession(same));
                try{assertArrayEquals(exported,installed.get().replay(cold).bytes());}
                finally{originals.set(null);}return null;
            });
            assertEquals(1,captures.get());assertEquals(1,decodes.get());assertEquals(1,replays.get());
            assertEquals(reads,fixture.nativeReadWrites());assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
            assertFalse(Files.exists(folder));assertArrayEquals(ledger,fixture.ledgerBytes());
        }
    }
}

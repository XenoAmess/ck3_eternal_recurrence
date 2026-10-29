package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.OfflineAnalysisFiles;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.service.OfflineAnalysisWorker;
import org.xar.ck3.control.service.OfflineEventAnalysisHost;
import org.xar.ck3.control.wave2.events.sourcecatalog.EvidenceGrantManifestPublisher;

/** Original captured stock/GUI bytes and real Java producers, with synthetic native frames.
 * Actual native file IO is exercised, but no Game installation/readiness/analysis execution claim is minted. */
final class OfflineAnalysisWorkerTest {
    @TempDir Path temporary;
    private record Fixture(ObjectValue corpus,ObjectValue row,Path root,EventSourceReadContext sources,Path incidents,
            Path scans,Path knowledge,Path manifest,NativeCheckpointFiles files,OfflineAnalysisFiles.Port io,
            AtomicInteger writes,OfflineAnalysisWorker.Binding binding) { }

    @Test void actualDurableWorkerAnalyzesOriginalDefinitionsPublishesFactsAndNextBatchRecognizesThem() throws Exception {
        Fixture f=fixture("actual");BatchRequest captured=batch(f,"first","a".repeat(32),o(f.row(),"plan"));
        try(var worker=worker(f,2)) {
            SessionPorts.OfflineAnalysisPort port=worker.bind(host(f),f.binding(),f.io());
            var ticket=port.enqueue(captured);
            assertEquals(captured.batchId(),ticket.batchId());
            assertEquals(1,requests(f));
            SessionPorts.AnalysisCompletion done=ticket.completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertFalse(done.persistedReviews().isEmpty());assertTrue(f.writes().get()>3,"actual scoped original producers must perform their writes");
            var published=OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(done.publishedKnowledge().path())));
            assertNotNull(published);
            for(ExactRef original:done.persistedReviews())assertEquals(original,f.files().observe(Path.of(original.path())).orElseThrow().reference());
            var trusted=TrustedEventSourceContext.open(f.sources());
            var known=SourceReviewedEventConsumer.continueWithExistingPlan(o(f.row(),"plan"),o(f.row(),"snapshot"),steps(f.row()),trusted);
            assertEquals(b(true),v(o(known.plan(),"unhandled_event_fallback"),"registry_known"));
            assertEquals(b(false),v(o(known.plan(),"unhandled_event_fallback"),"offline_followup_required"));
            var next=port.enqueue(batch(f,"next","b".repeat(32),known.plan())).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertEquals("next",next.batchId());
            var report=OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(next.persistedReviews().getFirst().path())));
            assertEquals(1,report.path("already_known").size());assertEquals(0,report.path("unresolved").size());
            assertEquals(done,port.enqueue(captured).completion().toCompletableFuture().get(1,TimeUnit.SECONDS));
        }
    }
    @Test void queueAckFollowsOriginalPublicationBoundedAdmissionDoesNotWaitForAnalysisAndCloseDoesNotFakeCompletion() throws Exception {
        Fixture f=fixture("bounded");CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
        var blocking=new OfflineEventAnalysisHost(Optional.of(f.sources()),settings(f)) {
            @Override public byte[] batch(BatchRequest request)throws IOException {
                assertFalse(Thread.currentThread().isDaemon(),"accepted real analysis must survive the host's finite shutdown wait");
                assertTrue(requests(f)>=1);entered.countDown();
                try {if(!release.await(30,TimeUnit.SECONDS))throw new IOException("test release missing");}
                catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                return super.batch(request);
            }
        };
        var worker=worker(f,1);
        try {
        assertThrows(java.nio.channels.OverlappingFileLockException.class,()->{
            try(var competing=worker(f,1)){fail("a second worker cannot own the same live fixed work root");}
        });
        var drain=worker.drainCompletion();AtomicInteger teardown=new AtomicInteger();
        var teardownDone=drain.whenComplete((ignored,failure)->{assertNull(failure);teardown.incrementAndGet();});
        var port=worker.bind(blocking,f.binding(),f.io());
        var first=port.enqueue(batch(f,"one","c".repeat(32),o(f.row(),"plan")));
        assertTrue(entered.await(10,TimeUnit.SECONDS));assertFalse(first.completion().toCompletableFuture().isDone());
        var second=port.enqueue(batch(f,"two","d".repeat(32),o(f.row(),"plan")));
        assertThrows(IOException.class,()->port.enqueue(batch(f,"three","e".repeat(32),o(f.row(),"plan"))));
        assertEquals(2,requests(f));worker.close();assertFalse(first.completion().toCompletableFuture().isDone());
        assertFalse(drain.toCompletableFuture().isDone());assertEquals(0,teardown.get());
        var callerCopy=drain.toCompletableFuture();callerCopy.complete(null);
        assertFalse(worker.drainCompletion().toCompletableFuture().isDone(),"a caller copy cannot forge actual accepted-work drain");
        release.countDown();first.completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
        second.completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
        drain.toCompletableFuture().get(10,TimeUnit.SECONDS);teardownDone.toCompletableFuture().get(10,TimeUnit.SECONDS);assertEquals(1,teardown.get());
        assertThrows(IOException.class,()->port.enqueue(batch(f,"four","f".repeat(32),o(f.row(),"plan"))));
        awaitClosed(worker);
        // Reopening the same real ownership file proves that the signal followed its FileLock closure.
        try(var replacement=worker(f,1)) { assertFalse(replacement.drainCompletion().toCompletableFuture().isDone()); }
        } finally { release.countDown();worker.close(); }
    }
    @Test void unresolvedDefinitionPersistsActualDiagnosisAndCannotProduceAnAnalysisCompletion() throws Exception {
        Fixture f=fixture("unresolved");ObjectValue plan=o(f.row(),"plan");
        ObjectValue capture=o(plan,"unhandled_event_fallback");
        ObjectValue changed=plan.with("unhandled_event_fallback",capture.with("event_definition_key",s("no_such_event.987654")));
        try(var worker=worker(f,2)) {
            var ticket=worker.bind(host(f),f.binding(),f.io()).enqueue(batch(f,"missing","1".repeat(32),changed));
            var failure=assertThrows(ExecutionException.class,()->ticket.completion().toCompletableFuture().get(30,TimeUnit.SECONDS));
            assertInstanceOf(OfflineAnalysisWorker.AnalysisIncomplete.class,failure.getCause());
            try(var files=Files.list(f.root().resolve("work"))) {
                Path terminal=files.filter(path->path.getFileName().toString().endsWith(".failure.json")).findFirst().orElseThrow();
                var raw=OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(terminal));assertNotNull(raw.get("result_ref"));
                assertFalse(raw.get("result_ref").isNull(),"actual analyzer output must persist before an unresolved failure");
            }
        }
    }
    @Test void requestWireAndImmutableSameIdBindingRejectWrongTypesChangesAndSourceDrift() throws Exception {
        Fixture f=fixture("integrity");BatchRequest original=batch(f,"same","2".repeat(32),o(f.row(),"plan"));
        assertEquals(original,OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(original)));
        var json=OfflineEventAnalysisWire.parseMetadataObject(OfflineEventAnalysisWire.encode(original));
        ((com.fasterxml.jackson.databind.node.ObjectNode)json.get("manifest_ref")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->OfflineEventAnalysisWire.decodeBatch(json.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        try(var worker=worker(f,2)) {
            var port=worker.bind(host(f),f.binding(),f.io());
            var done=port.enqueue(original).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertEquals("same",done.batchId());
            BatchRequest changed=new BatchRequest(original.batchId(),new ExactRef(original.manifestRef().path(),original.manifestRef().bytes(),"0".repeat(64)),original.capturedRefs());
            assertThrows(IOException.class,()->port.enqueue(changed));
            BatchRequest drift=batch(f,"drift","3".repeat(32),o(f.row(),"plan"));
            Files.writeString(Path.of(drift.capturedRefs().getFirst().path()),"changed original");
            assertThrows(IOException.class,()->port.enqueue(drift));assertEquals(1,requests(f));
        }
    }
    @Test void completedDurableOriginalRestoresWithoutRunningAnotherAnalyzerAndSourceTamperingCannotRestoreSuccess() throws Exception {
        Fixture f=fixture("restore");BatchRequest original=batch(f,"restore","4".repeat(32),o(f.row(),"plan"));
        var first=worker(f,2);var completed=first.bind(host(f),f.binding(),f.io()).enqueue(original).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
        first.close();awaitClosed(first);
        AtomicInteger dispatches=new AtomicInteger();var counting=new OfflineEventAnalysisHost(Optional.of(f.sources()),settings(f)) {
            @Override public byte[] batch(BatchRequest request)throws IOException {dispatches.incrementAndGet();return super.batch(request);}
        };
        try(var restored=worker(f,2)) {
            var actual=restored.bind(counting,f.binding(),f.io()).enqueue(original).completion().toCompletableFuture().get(10,TimeUnit.SECONDS);
            assertEquals(completed,actual);assertEquals(0,dispatches.get());
        }
        Files.writeString(Path.of(completed.persistedReviews().getFirst().path()),"changed real report");
        try(var rejected=worker(f,2)) {
            var ticket=rejected.bind(counting,f.binding(),f.io()).enqueue(original);
            assertThrows(ExecutionException.class,()->ticket.completion().toCompletableFuture().get(10,TimeUnit.SECONDS));assertEquals(0,dispatches.get());
        }
    }
    @Test void actualIoScopeIsThreadConfinedAndRestoresAfterAnAnalysisFailure() throws Exception {
        Fixture f=fixture("scope");assertTrue(OfflineAnalysisFiles.current().isEmpty());
        assertThrows(IOException.class,()->OfflineAnalysisFiles.with(f.io(),()->{
            assertSame(f.io(),OfflineAnalysisFiles.current().orElseThrow());
            assertTrue(java.util.concurrent.CompletableFuture.supplyAsync(()->OfflineAnalysisFiles.current().isEmpty()).orTimeout(5,TimeUnit.SECONDS).join());
            assertThrows(IOException.class,()->OfflineAnalysisFiles.with(f.io(),()->null));
            throw new IOException("actual failed analysis scope");
        }));
        assertTrue(OfflineAnalysisFiles.current().isEmpty());
    }
    @Test void originalDurableWorkAfterAPublicationCrashResumesTheRealIdempotentAnalyzerWithoutOverwritingEarlierResult()throws Exception {
        Fixture f=fixture("publication-cut");BatchRequest original=batch(f,"publication-cut","5".repeat(32),o(f.row(),"plan"));
        var first=worker(f,2);var completed=first.bind(host(f),f.binding(),f.io()).enqueue(original).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
        first.close();awaitClosed(first);
        // Test-only process cut: retain every original/request/result/knowledge file and remove only the last
        // completion publication, modeling a stop immediately before that final immutable publish.
        try(var entries=Files.list(f.root().resolve("work"))) {
            Path terminal=entries.filter(path->path.getFileName().toString().endsWith(".complete.json")).findFirst().orElseThrow();Files.delete(terminal);
        }
        AtomicInteger dispatches=new AtomicInteger();var actualHost=new OfflineEventAnalysisHost(Optional.of(f.sources()),settings(f)) {
            @Override public byte[] batch(BatchRequest request)throws IOException{dispatches.incrementAndGet();return super.batch(request);}
        };
        try(var resumed=worker(f,2)) {
            var actual=resumed.bind(actualHost,f.binding(),f.io()).enqueue(original).completion().toCompletableFuture().get(30,TimeUnit.SECONDS);
            assertEquals(completed,actual);assertEquals(1,dispatches.get());
            try(var entries=Files.list(f.root().resolve("work"))) {assertEquals(2,entries.filter(path->path.getFileName().toString().contains(".result-")).count());}
        }
    }
    private Fixture fixture(String name)throws IOException {
        Path root=Files.createDirectories(temporary.resolve(name));Map<String,Value> blobs=new HashMap<>();List<Value> rows=new ArrayList<>();ObjectValue first=null;
        for(String cohort:List.of("liberty","council","sway"))try(InputStream resource=getClass().getResourceAsStream("/offline-worker/source-review-"+cohort+"-golden-v1.json.gz")) {
            if(resource==null)throw new IOException("mandatory actual source-review cohort missing; NOT RUN: "+cohort);
            try(var gzip=new GZIPInputStream(resource)) {
                byte[] raw=gzip.readNBytes(1_048_577);if(raw.length>1_048_576)throw new IOException("actual cohort bound exceeded");
                ObjectValue corpus=RetainedJson.object(RetainedJson.parse(raw));if(first==null)first=corpus;
                blobs.putAll(o(corpus,"blobs").fields());rows.addAll(array(corpus,"cases"));
            }
        }
        ObjectValue corpus=first.with("blobs",new ObjectValue(blobs));
        ObjectValue row=rows.stream().map(RetainedJson::object).filter(value->eq(value,"name",s("faction_demand.0101-exact-stock"))).findFirst().orElseThrow();
        Path game=root.resolve("game");
        for(var source:ReviewedLetterSourceRebind.installedSourceHashes().entrySet()) {
            Path path=game.resolve(source.getKey());Files.createDirectories(path.getParent());Files.write(path,blob(corpus,source.getValue()));
        }
        Path state=Files.createDirectories(root.resolve("state")),incidents=Files.createDirectories(root.resolve("incidents")),scans=Files.createDirectories(root.resolve("scans"));
        Path knowledge=Files.createDirectories(root.resolve("knowledge"));Files.createDirectories(root.resolve("work"));Path manifest=knowledge.resolve("fixed-grants.json");
        EventSourceReadContext sources=new EventSourceReadContext("offline-worker-source-fixture",state,game);
        var files=new NativeCheckpointFiles();AtomicInteger writes=new AtomicInteger();
        OfflineAnalysisFiles.Port io=new OfflineAnalysisFiles.Port() {
            @Override public void directories(Path path)throws IOException {Files.createDirectories(path);}
            @Override public ExactRef createNew(Path path,byte[] raw)throws IOException {writes.incrementAndGet();return files.createNew(path,raw).reference();}
            @Override public ExactRef replace(Path path,byte[] raw)throws IOException {writes.incrementAndGet();return files.replace(path,raw).reference();}
            @Override public void beforeLock(Path path){writes.incrementAndGet();}
            @Override public void beforeLink(Path path,long bytes){assertTrue(bytes>0);writes.incrementAndGet();}
        };
        return new Fixture(corpus,row,root,sources,incidents,scans,knowledge,manifest,files,io,writes,
                new OfflineAnalysisWorker.Binding(sources.machineId(),state,game,incidents,scans,knowledge,manifest));
    }
    private static OfflineEventAnalysisHost.Settings settings(Fixture f) {return new OfflineEventAnalysisHost.Settings(true,false,Optional.of(f.manifest()),Optional.of(f.incidents()),Optional.of(f.knowledge()),Optional.of(f.scans()));}
    private static OfflineEventAnalysisHost host(Fixture f)throws IOException {
        return OfflineAnalysisFiles.with(f.io(),()->new OfflineEventAnalysisHost(Optional.of(f.sources()),settings(f)));
    }
    private static OfflineAnalysisWorker worker(Fixture f,int capacity)throws IOException {return new OfflineAnalysisWorker(new OfflineAnalysisWorker.Settings(f.root().resolve("work"),capacity,64),f.files(),f.io());}
    private static BatchRequest batch(Fixture f,String id,String incident,ObjectValue plan)throws IOException {
        ObjectValue binding=o(o(plan,"unhandled_event_fallback"),"binding");
        ObjectValue planned=obj(f("snapshot_id",v(binding,"snapshot_id")),f("revision",v(binding,"revision")),f("plan",plan));
        ObjectValue before=UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(Optional.of(planned),incident,"2026-10-22T00:00:00Z")).orElseThrow();
        Path beforePath=f.incidents().resolve(incident+".before.json");byte[] raw=RetainedJson.encode(before);Files.write(beforePath,raw);
        ExactRef beforeRef=new ExactRef(beforePath.toString(),raw.length,sha(raw));
        ObjectValue item=obj(f("incident_id",s(incident)),f("event_definition_key",v(before,"event_definition_key")),f("before",s(beforePath.toString())),f("before_sha256",s(beforeRef.sha256())));
        ObjectValue manifest=obj(f("completed_control_sequence",i(1)),f("new_incidents",new ArrayValue(List.of(item))));
        Path path=f.incidents().resolve(id+".json");byte[] bytes=RetainedJson.encode(manifest);Files.write(path,bytes);
        return new BatchRequest(id,new ExactRef(path.toString(),bytes.length,sha(bytes)),List.of(beforeRef));
    }
    private static long requests(Fixture f)throws IOException {try(var entries=Files.list(f.root().resolve("work"))){return entries.filter(path->path.getFileName().toString().endsWith(".request.json")).count();}}
    private static List<String> steps(ObjectValue row){return array(row,"action_steps").stream().map(value->((StringValue)value).value()).toList();}
    private static byte[] blob(ObjectValue corpus,String sha)throws IOException {
        try(var input=new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(o(corpus,"blobs"),sha))))) {
            byte[] raw=input.readNBytes(2_097_153);if(raw.length>2_097_152)throw new IOException("actual blob bound exceeded");assertEquals(sha,sha(raw));return raw;
        }
    }
    private static void awaitClosed(OfflineAnalysisWorker worker)throws InterruptedException {
        for(int attempt=0;attempt<100&&!worker.isTerminated();attempt++)Thread.sleep(20);
        assertTrue(worker.isTerminated(),"Core pool must finish graceful close without interruption or fake completion");
    }
}

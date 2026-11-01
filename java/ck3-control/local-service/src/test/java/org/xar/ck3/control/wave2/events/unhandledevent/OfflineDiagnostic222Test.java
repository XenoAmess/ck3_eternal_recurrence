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
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Set;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal.Kind;
import org.xar.ck3.control.application.planning.events.NativeWindowDiagnostic;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;


/** Original source/GUI bytes and real public diagnostic, journal, offline producers; software DATA only. */
final class OfflineDiagnostic222Test {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final int LARGE=5*1024*1024/2;
    private record Fixture(ObjectValue corpus,ObjectValue row,Path root,EventSourceReadContext sources,Path incidents,
            Path scans,Path knowledge,Path manifest,NativeCheckpointFiles files,OfflineAnalysisFiles.Port io,
            AtomicInteger writes,OfflineAnalysisWorker.Binding binding) { }
    private record Captured(Fixture f,PlanningRequest request,EpisodeIncidentJournal journal,
            EpisodeIncidentJournal.Ticket ticket,OpportunityJson.Obj plan,BatchRequest batch) { }
    private Captured capture(String name,Kind kind,int characters)throws Exception {
        Fixture f=fixture(name);
        Path sourceFile=f.root().resolve("software-source.json");Files.writeString(sourceFile,"{\"scope\":\"software-diagnostic-source\"}");
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before=new ObservationIdentity(f.sources().machineId(),game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(24000)),
                "snapshot-1",BigInteger.ONE,"episode-1"),1);
        OpportunityJson.Obj snapshot=snapshot();
        snapshot=switch(kind) {
            case EVENT -> snapshot.with("active_event",new OpportunityJson.Obj(Map.of("instance_id",integer(41))));
            case INTERACTION -> snapshot.with("pending_character_interaction",new OpportunityJson.Obj(Map.of("instance_id",integer(42))));
            case MANDATORY -> snapshot.with("top_exclusive_modal_choice_hint",new OpportunityJson.Obj(Map.of("status",new OpportunityJson.Text("present"))));
        };
        var source=new G2Source(before.machineId(),NOW.toString(),"SOFTWARE-DIAGNOSTIC-TEST",EpisodeIncidentJournal.measure(sourceFile));
        var observed=new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var request=new PlanningRequest(before,source,"session-1",NOW.plusSeconds(60),observed);
        var configured=new EpisodeIncidentJournal.Configuration(f.incidents(),f.scans(),Clock.fixed(NOW,ZoneOffset.UTC),pending->{
            if(pending<0||pending>(64L<<20)+4096)throw new IOException("finite software write cap");
        },Optional.empty());
        var journal=EpisodeIncidentJournal.initialize(configured,bind(request));
        var plan=NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(before,snapshot,
                List.of(new OpportunityJson.Text("A".repeat(characters))),Optional.empty(),Optional.empty(),"software-"+kind)).orElseThrow();
        Path frame=f.root().resolve("software-frame.json");Files.writeString(frame,"{\"scope\":\"software-frame\"}");
        var ticket=journal.captureBlocked(request,plan,EpisodeIncidentJournal.measure(frame));
        var batch=journal.scan(bind(request)).batch().orElseThrow();
        return new Captured(f,request,journal,ticket,plan,batch);
    }
    private static EpisodeIncidentJournal.Binding bind(PlanningRequest request) {
        return new EpisodeIncidentJournal.Binding(request.before(),request.source(),request.sessionId());
    }
    private static OpportunityJson.IntegerValue integer(long v){return new OpportunityJson.IntegerValue(BigInteger.valueOf(v));}
    private static OpportunityJson.Obj snapshot() {
        return new OpportunityJson.Obj(Map.ofEntries(
            Map.entry("paused",new OpportunityJson.Bool(true)),Map.entry("map_ready",new OpportunityJson.Bool(true)),
            Map.entry("revision",integer(1)),Map.entry("native_revision",integer(1)),Map.entry("date_raw",integer(24000)),
            Map.entry("snapshot_id",new OpportunityJson.Text("snapshot-1")),Map.entry("episode_run_id",new OpportunityJson.Text("episode-1")),
            Map.entry("played_character",new OpportunityJson.Obj(Map.of("character_id",integer(29829),"alive",new OpportunityJson.Bool(true)))),
            Map.entry("active_wars",new OpportunityJson.Arr(List.of())),Map.entry("player_armies",new OpportunityJson.Arr(List.of())),
            Map.entry("diagnostics",new OpportunityJson.Obj(Map.of("connection_generation",integer(1),"bridge_pid",integer(123))))));
    }
    private static OfflineScanSource.Loaded load(Captured c)throws IOException {
        return OfflineScanSource.load(c.f().incidents(),Optional.of(c.f().scans()),c.f().sources().machineId(),c.batch().manifestRef(),c.batch().capturedRefs());
    }
    private static OfflineEventBatchAnalyzer.Result analyze(Captured c)throws IOException {
        Fixture f=c.f();return OfflineAnalysisFiles.with(f.io(),()->OfflineEventBatchAnalyzer.run(
            new OfflineEventBatchAnalyzer.Configuration(f.sources(),f.incidents(),f.knowledge(),f.manifest(),Optional.of(f.scans())),
            new OfflineEventBatchAnalyzer.Request(c.batch().batchId(),c.batch().manifestRef(),c.batch().capturedRefs())));
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
    private static long requests(Fixture f)throws IOException {try(var entries=Files.list(f.root().resolve("work"))){return entries.filter(path->path.getFileName().toString().endsWith(".request.json")).count();}}
    private static byte[] blob(ObjectValue corpus,String sha)throws IOException {
        try(var input=new GZIPInputStream(new ByteArrayInputStream(Base64.getDecoder().decode(text(o(corpus,"blobs"),sha))))) {
            byte[] raw=input.readNBytes(2_097_153);if(raw.length>2_097_152)throw new IOException("actual blob bound exceeded");assertEquals(sha,sha(raw));return raw;
        }
    }
    private static void awaitClosed(OfflineAnalysisWorker worker)throws InterruptedException {
        for(int attempt=0;attempt<100&&!worker.isTerminated();attempt++)Thread.sleep(20);
        assertTrue(worker.isTerminated(),"Core pool must finish graceful close without interruption or fake completion");
    }
    @Test void actualDiagnosticsOfAllThreeKindsReachOfflineAnalyzerWithoutLosingHistory() throws Exception {
        for (int n=0;n<4;n++) {
            Kind kind=n==3?Kind.EVENT:Kind.values()[n];int size=n==3?16:LARGE;
            Captured c=capture("diagnostic-"+n,kind,size);
            var loaded=load(c);ExactRef before=c.ticket().before();
            assertTrue(loaded.diagnosticBeforeRefs().contains(before));
            assertEquals(OfflineScanSource.CAPTURED_DIAGNOSTIC_MAXIMUM,loaded.capturedMaximum(before));
            assertEquals(before,EpisodeIncidentJournal.measure(Path.of(before.path())));
            if(n<3)assertTrue(before.bytes()>2L*1024*1024);else assertTrue(before.bytes()<1024*1024);
            assertEquals(List.of(before),c.batch().capturedRefs());
            var body=FullJsonTree.parse(Files.readAllBytes(Path.of(before.path())),FullJsonTree.MAXIMUM_BYTES);
            var producer=DriverJson.toNode(c.plan().get("unhandled_native_window_diagnostic"));
            for(var field:producer.properties()) {
                if(field.getKey().equals("origin")) {
                    assertEquals(c.request().before(),org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.decodeObservation(body.get("origin")));
                } else assertEquals(field.getValue(),body.get(field.getKey()),"preserved producer field "+field.getKey());
            }
            assertEquals("A".repeat(size),body.path("retained_history").get(0).textValue());
            assertEquals("planning_diagnostic",body.path("stage").textValue());
            assertTrue(body.path("selection").isNull());assertFalse(body.path("dispatch_attempted").booleanValue());
            assertFalse(Files.exists(Path.of(before.path()).resolveSibling(c.ticket().incidentId()+".after.json")));
            var result=analyze(c);
            assertDiagnosticReport(OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(result.report().path()))),c);
            assertTrue(result.outputs().contains(result.report()));
            for(ExactRef output:result.outputs())assertEquals(output,EpisodeIncidentJournal.measure(Path.of(output.path())));
            assertEquals(before,EpisodeIncidentJournal.measure(Path.of(before.path())));
        }
    }

    @Test void wrongBindingRehashedMalformedRolesAndOriginalDriftRemainRejected() throws Exception {
        Captured machine=capture("wrong-machine",Kind.EVENT,16);
        var wrongMachine=assertThrows(IllegalArgumentException.class,()->OfflineScanSource.load(machine.f().incidents(),Optional.of(machine.f().scans()),
                "another-software-machine",machine.batch().manifestRef(),machine.batch().capturedRefs()));
        assertTrue(wrongMachine.getMessage().contains("another source machine"));assertNoKnowledge(machine);

        Captured kind=capture("wrong-index-kind",Kind.EVENT,16);
        Path indexPath=Path.of(kind.ticket().index().path());
        ObjectNode index=(ObjectNode)StrictJson.parse(Files.readAllBytes(indexPath),1<<20);
        index.put("kind","INTERACTION");Files.write(indexPath,StrictJson.canonical(index,1<<20));
        Captured rehashedKind=rescanned(kind);
        var wrongKind=assertThrows(IllegalArgumentException.class,()->load(rehashedKind));
        assertTrue(wrongKind.getMessage().contains("Native diagnostic crossed its original index binding"));assertNoKnowledge(kind);

        Captured legacy=capture("large-non-native",Kind.EVENT,LARGE);
        Path beforePath=Path.of(legacy.ticket().before().path());
        ObjectNode before=(ObjectNode)FullJsonTree.parse(Files.readAllBytes(beforePath),FullJsonTree.MAXIMUM_BYTES);
        before.put("schema","xar.software-malformed-legacy/v1");
        Files.write(beforePath,FullJsonTree.encode(before,FullJsonTree.MAXIMUM_BYTES));
        ExactRef malformedOriginal=EpisodeIncidentJournal.measure(beforePath);
        Path legacyIndex=Path.of(legacy.ticket().index().path());
        ObjectNode replacement=(ObjectNode)StrictJson.parse(Files.readAllBytes(legacyIndex),1<<20);
        replacement.set("before_ref",malformedOriginal.toJson());Files.write(legacyIndex,StrictJson.canonical(replacement,1<<20));
        Captured rehashedLegacy=rescanned(legacy);
        assertTrue(rehashedLegacy.batch().capturedRefs().contains(malformedOriginal));
        var refusedLegacy=assertThrows(IllegalArgumentException.class,()->load(rehashedLegacy));
        assertTrue(refusedLegacy.getMessage().contains("Legacy before body exceeds its unchanged role bound"));assertNoKnowledge(legacy);

        Captured drift=capture("original-sha-drift",Kind.EVENT,16);
        var loaded=load(drift);Path original=Path.of(drift.ticket().before().path());
        Files.writeString(original,Files.readString(original)+" ");
        var changed=assertThrows(IllegalArgumentException.class,()->OfflineScanSource.recheck(drift.f().incidents(),Optional.of(drift.f().scans()),drift.batch().manifestRef(),loaded));
        assertTrue(changed.getMessage().contains("Actual journal source bytes or SHA changed"));
        assertThrows(IllegalArgumentException.class,()->load(drift));
        assertNoKnowledge(drift);
    }

    @Test void publicWorkerAdmitsLargeQualifiedDiagnosticAndRetainsItsActualUnresolvedResult() throws Exception {
        Captured c=capture("durable-worker",Kind.EVENT,LARGE);
        assertTrue(c.ticket().before().bytes()>2L*1024*1024);
        var w=worker(c.f(),2);
        try(w) {
            var actualHost=OfflineAnalysisFiles.with(c.f().io(),()->new OfflineEventAnalysisHost(
                    Optional.of(c.f().sources()),settings(c.f()),Optional.of(c.journal()::acknowledge)));
            var ticket=w.bind(actualHost,c.f().binding(),c.f().io()).enqueue(c.batch());
            assertEquals(c.batch().batchId(),ticket.batchId());assertEquals(1,requests(c.f()));
            var failure=assertThrows(ExecutionException.class,()->ticket.completion().toCompletableFuture().get(30,TimeUnit.SECONDS));
            var incomplete=assertInstanceOf(OfflineAnalysisWorker.AnalysisIncomplete.class,failure.getCause());
            assertTrue(incomplete.getMessage().startsWith("UNRESOLVED_SOURCE_RESEARCH:"),incomplete.getMessage());
            ExactRef terminal=incomplete.evidence().orElseThrow();assertEquals(terminal,EpisodeIncidentJournal.measure(Path.of(terminal.path())));
            assertTrue(Path.of(terminal.path()).getFileName().toString().endsWith(".failure.json"));
            var terminalBody=OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(terminal.path())));
            assertEquals(c.batch().batchId(),terminalBody.path("batch_id").textValue());
            assertEquals(c.f().sources().machineId(),terminalBody.path("machine_id").textValue());
            ExactRef requestRef=ExactRef.fromJson(terminalBody.get("request_ref"));
            assertEquals(requestRef,EpisodeIncidentJournal.measure(Path.of(requestRef.path())));
            assertTrue(Path.of(requestRef.path()).getFileName().toString().endsWith(".request.json"));
            ExactRef result=ExactRef.fromJson(terminalBody.get("result_ref"));
            assertEquals(result,EpisodeIncidentJournal.measure(Path.of(result.path())));
            var resultBody=OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(result.path())));
            assertDiagnosticReport(resultBody.get("report"),c);
            ExactRef report=ExactRef.fromJson(resultBody.get("report_ref"));
            assertEquals(report,EpisodeIncidentJournal.measure(Path.of(report.path())));
            assertDiagnosticReport(OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(report.path()))),c);
            assertEquals(c.ticket().before(),EpisodeIncidentJournal.measure(Path.of(c.ticket().before().path())));
        } finally {awaitClosed(w);}
    }

    private static void assertDiagnosticReport(JsonNode report,Captured c) {
        assertEquals(0,report.path("entries").size());assertEquals(0,report.path("already_known").size());
        assertEquals(1,report.path("unresolved").size());JsonNode row=report.path("unresolved").get(0);
        JsonNode producer=DriverJson.toNode(c.plan().get("unhandled_native_window_diagnostic"));
        assertEquals("diagnostic_only",row.path("status").textValue());
        assertEquals(c.ticket().incidentId(),row.path("incident_id").textValue());
        assertEquals(producer.path("kind").textValue(),row.path("kind").textValue());
        assertEquals(producer.path("diagnostic_reason").textValue(),row.path("reason").textValue());
        assertEquals(c.batch().manifestRef(),ExactRef.fromJson(report.get("manifest")));
    }
    private static Captured rescanned(Captured c)throws IOException {
        var batch=c.journal().scan(bind(c.request())).batch().orElseThrow();
        return new Captured(c.f(),c.request(),c.journal(),c.ticket(),c.plan(),batch);
    }
    private static void assertNoKnowledge(Captured c)throws IOException {
        try(var files=Files.list(c.f().knowledge())){assertEquals(0,files.count());}
    }

}

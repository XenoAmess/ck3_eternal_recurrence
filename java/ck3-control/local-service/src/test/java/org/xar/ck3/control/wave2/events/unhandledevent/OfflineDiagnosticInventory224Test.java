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
final class OfflineDiagnosticInventory224Test {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final int LARGE=15*1024*1024;
    private record Fixture(ObjectValue corpus,ObjectValue row,Path root,EventSourceReadContext sources,Path incidents,
            Path scans,Path knowledge,Path manifest,NativeCheckpointFiles files,OfflineAnalysisFiles.Port io,
            AtomicInteger writes,OfflineAnalysisWorker.Binding binding) { }
    private record Captured(Fixture f,PlanningRequest request,EpisodeIncidentJournal journal,
            EpisodeIncidentJournal.Ticket ticket,OpportunityJson.Obj plan,BatchRequest batch) { }
    private Captured capture(String name,Kind kind,int characters)throws Exception {
        Fixture f=fixture(name);
        Path sourceFile=f.root().resolve("software-provenance.class");
        try(var code=OfflineDiagnosticInventory224Test.class.getResourceAsStream("OfflineDiagnosticInventory224Test.class")) {
            if(code==null)throw new IOException("own compiled class resource required");
            byte[] raw=code.readNBytes(1_048_577);if(raw.length>1_048_576)throw new IOException("finite own class source bound");
            Files.write(sourceFile,raw);
        }
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
    private static EpisodeIncidentJournal.Ticket append(Captured c,String reason,int characters)throws Exception {
        var plan=NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(c.request().before(),c.request().observations().snapshot(),
                List.of(new OpportunityJson.Text("A".repeat(characters))),Optional.empty(),Optional.empty(),reason)).orElseThrow();
        return c.journal().captureBlocked(c.request(),plan,EpisodeIncidentJournal.measure(c.f().root().resolve("software-frame.json")));
    }
    @Test void actualDouble15MiBDiagnosticAggregateAndProvenanceDrift() throws Exception {
        Captured c = capture("double-15mi", Kind.EVENT, LARGE);
        var second = append(c, "distinct-reason-2", LARGE);
        assertTrue(c.ticket().before().bytes() < 16L << 20);
        assertTrue(second.before().bytes() < 16L << 20);
        assertTrue(c.ticket().before().bytes() + second.before().bytes() > 16L << 20);

        var scan = c.journal().scan(bind(c.request()));
        var batch = scan.batch().orElseThrow(() -> new IOException("Actual scan batch missing"));
        var updated = new Captured(c.f(), c.request(), c.journal(), c.ticket(), c.plan(), batch);

        var loaded = OfflineScanSource.load(updated.f().incidents(), Optional.of(updated.f().scans()),
                updated.f().sources().machineId(), batch.manifestRef(), batch.capturedRefs());
        assertEquals(2, loaded.diagnosticBeforeRefs().size());
        assertTrue(loaded.diagnosticBeforeRefs().contains(c.ticket().before()));
        assertTrue(loaded.diagnosticBeforeRefs().contains(second.before()));
        for (ExactRef ref : loaded.diagnosticBeforeRefs()) {
            assertEquals(OfflineScanSource.CAPTURED_DIAGNOSTIC_MAXIMUM, loaded.capturedMaximum(ref));
        }

        Path provenance = Path.of(c.request().source().sourceRef().path());
        byte[] originalProvenance = Files.readAllBytes(provenance);
        Files.write(provenance, java.util.Arrays.copyOf(originalProvenance, originalProvenance.length + 1));

        var reloaded = OfflineScanSource.load(updated.f().incidents(), Optional.of(updated.f().scans()),
                updated.f().sources().machineId(), batch.manifestRef(), batch.capturedRefs());
        assertEquals(2, reloaded.diagnosticBeforeRefs().size());
        assertEquals(c.request().source().sourceRef(), assertInstanceOf(org.xar.ck3.control.contracts.offline.OfflineBatchBinding.ObservedScan.class,reloaded.binding()).source().sourceRef());
        OfflineScanSource.recheck(updated.f().incidents(), Optional.of(updated.f().scans()), batch.manifestRef(), reloaded);

        var result = analyze(updated);
        var report = OfflineEventAnalysisWire.parseMetadataObject(Files.readAllBytes(Path.of(result.report().path())));
        assertEquals(0, report.path("entries").size());
        assertEquals(0, report.path("already_known").size());
        assertEquals(2, report.path("unresolved").size());
        Map<String,String> reasons = new HashMap<>();
        for (JsonNode row : report.path("unresolved")) {
            assertEquals("diagnostic_only", row.path("status").textValue());
            assertNull(reasons.put(row.path("incident_id").textValue(), row.path("reason").textValue()));
        }
        assertEquals(Map.of(c.ticket().incidentId(),"software-EVENT",second.incidentId(),"distinct-reason-2"),reasons);
        for (ExactRef output : result.outputs()) {
            assertEquals(output, EpisodeIncidentJournal.measure(Path.of(output.path())));
        }
    }

    @Test void actualAggregate5x15MiBExceedsScanByteLimit() throws Exception {
        Captured c = capture("aggregate-5x15", Kind.EVENT, LARGE);
        append(c, "reason-2", LARGE);
        append(c, "reason-3", LARGE);
        append(c, "reason-4", LARGE);
        append(c, "reason-5", LARGE);

        var failure = assertThrows(IOException.class, () -> c.journal().scan(bind(c.request())));
        assertTrue(failure.getMessage().contains("Incident scan byte limit exceeded"));
    }

    @Test void actualExternalIntegrityProvenanceVsFrame() throws Exception {
        Captured c = capture("integrity-small", Kind.EVENT, 16);
        var loaded = OfflineScanSource.load(c.f().incidents(), Optional.of(c.f().scans()),
                c.f().sources().machineId(), c.batch().manifestRef(), c.batch().capturedRefs());

        Path provenance = Path.of(c.request().source().sourceRef().path());
        byte[] originalProvenance = Files.readAllBytes(provenance);
        Files.write(provenance, java.util.Arrays.copyOf(originalProvenance, originalProvenance.length + 1));

        var reloaded = OfflineScanSource.load(c.f().incidents(), Optional.of(c.f().scans()),
                c.f().sources().machineId(), c.batch().manifestRef(), c.batch().capturedRefs());
        assertEquals(loaded.diagnosticBeforeRefs(), reloaded.diagnosticBeforeRefs());
        assertEquals(c.request().source().sourceRef(),assertInstanceOf(org.xar.ck3.control.contracts.offline.OfflineBatchBinding.ObservedScan.class,reloaded.binding()).source().sourceRef());
        OfflineScanSource.recheck(c.f().incidents(),Optional.of(c.f().scans()),c.batch().manifestRef(),reloaded);

        Path frame = c.f().root().resolve("software-frame.json");
        Files.writeString(frame, "{}");

        var failure = assertThrows(IllegalArgumentException.class, () -> OfflineScanSource.load(c.f().incidents(), Optional.of(c.f().scans()),
                c.f().sources().machineId(), c.batch().manifestRef(), c.batch().capturedRefs()));
        assertTrue(failure.getMessage().contains("Actual external original changed identity, bytes or SHA"));
        var recheckFailure=assertThrows(IllegalArgumentException.class,()->OfflineScanSource.recheck(
                c.f().incidents(),Optional.of(c.f().scans()),c.batch().manifestRef(),reloaded));
        assertTrue(recheckFailure.getMessage().contains("Actual external original changed identity, bytes or SHA"));
    }
}

package org.xar.ck3.control.application.planning;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.offline.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.OfflineScanSource;
import static org.junit.jupiter.api.Assertions.*;

/** Actual capture/scan producer -> persisted manifest -> worker request decoder -> versioned report ACK.
 * Synthetic frame/evidence and reports test custody only, never analysis, Native or Game authority. */
final class EpisodeIncidentSignedScanTest {
    @TempDir Path temporary;
    private static final BigInteger NATIVE=new BigInteger("9007199254740993"),PUBLIC=new BigInteger("18446744073709551614");
    private record Fixture(PlanningRequest request,EpisodeIncidentJournal journal,EpisodeIncidentJournal.Ticket ticket){}
    private Fixture fixture(int actor)throws Exception {
        Path root=Files.createDirectory(temporary.resolve("actor-"+actor));Path sourceFile=root.resolve("original-software-frame.txt");Files.writeString(sourceFile,"signed actor scan software evidence");
        ObjectNode snapshot=(ObjectNode)StrictJson.parse(DriverJson.encode(PlanningFixtures.snapshot()));((ObjectNode)snapshot.get("played_character")).put("character_id",actor);snapshot.put("native_revision",NATIVE).put("revision",PUBLIC);
        var semantic=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(snapshot)),"actual software public frame");
        var base=PlanningFixtures.request(semantic,List.of(),Set.of(new OperationKey("select-event-option-1")));var old=base.before();var oldFrame=old.frame();
        var identity=new ObservationIdentity(old.machineId(),old.game(),new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),NATIVE,oldFrame.identity().dateRaw()),oldFrame.snapshotId(),PUBLIC,oldFrame.episodeRunId()),old.observationVersion());
        var source=new G2Source(identity.machineId(),PlanningFixtures.NOW.toString(),"SYNTHETIC-SIGNED-SCAN",EpisodeIncidentJournal.measure(sourceFile));
        var request=new PlanningRequest(identity,source,base.sessionId(),base.deadline(),base.observations());
        Path incidents=Files.createDirectory(root.resolve("incidents")),scans=Files.createDirectory(root.resolve("scans"));
        var journal=EpisodeIncidentJournal.initialize(new EpisodeIncidentJournal.Configuration(incidents,scans,Clock.fixed(PlanningFixtures.NOW,ZoneOffset.UTC),size->{if(size<0||size>(1<<20))throw new java.io.IOException("bounded software journal output");},Optional.empty()),binding(request));
        ObjectNode diagnostic=StrictJson.object().put("schema","xar.unhandled-native-window-diagnostic/v1").put("kind","unhandled_event").put("event_definition_key","SYNTHETIC.SIGNED_SCAN").put("current_event_instance_id",41).putNull("selection");diagnostic.set("origin",ProposalLifecycleCodec.observation(identity));
        ObjectNode plan=StrictJson.object().putNull("selected_step");plan.set("unhandled_native_window_diagnostic",diagnostic);
        var ticket=journal.captureBlocked(request,OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)),"actual diagnostic plan"),source.sourceRef());return new Fixture(request,journal,ticket);
    }
    private static EpisodeIncidentJournal.Binding binding(PlanningRequest request){return new EpisodeIncidentJournal.Binding(request.before(),request.source(),request.sessionId());}
    private static ObjectNode read(ExactRef source)throws Exception{return (ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(source.path())),1<<20);}
    private static ObjectNode report(OfflineBatchBinding.ObservedScan observed,OfflineEventAnalysisContract.BatchRequest batch,String incident){
        var report=StrictJson.object().put("machine_id",observed.observation().machineId());report.set("manifest",batch.manifestRef().toJson());OfflineBatchBinding.addReportBinding(report,observed);
        report.putArray("entries").addObject().put("incident_id",incident);report.putArray("already_known");report.putArray("unresolved");return report;
    }
    @Test void actualSignedScanAndWorkerInputPreserveNegativeZeroAndPositiveActors()throws Exception {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE}){
            var f=fixture(actor);var scan=f.journal().scan(binding(f.request()));var batch=scan.batch().orElseThrow();ObjectNode manifest=read(batch.manifestRef());
            assertEquals(OfflineBatchBinding.MANIFEST_V3,manifest.get("schema").textValue());assertTrue(manifest.at("/scan_observation/frame/played_character_id").isIntegralNumber());assertEquals(actor,manifest.at("/scan_observation/frame/played_character_id").intValue());assertEquals(NATIVE.toString(),manifest.at("/scan_observation/frame/native_revision").textValue());assertEquals(PUBLIC.toString(),manifest.at("/scan_observation/frame/revision").textValue());
            var loaded=OfflineScanSource.load(f.journal().configuration().incidentRoot(),Optional.of(f.journal().configuration().scanRoot()),f.request().before().machineId(),batch.manifestRef(),batch.capturedRefs());
            var observed=EpisodeIncidentJournal.requireBatchManifest(manifest);assertEquals(observed,loaded.binding());OfflineScanSource.recheck(f.journal().configuration().incidentRoot(),Optional.of(f.journal().configuration().scanRoot()),batch.manifestRef(),loaded);assertInstanceOf(OfflineBatchBinding.NativeObservedActor.class,observed.observation().frame().playedCharacterId());
            ObjectNode wire=StrictJson.object().put("schema",OfflineEventAnalysisContract.BATCH_REQUEST_SCHEMA).put("batch_id",batch.batchId());wire.set("manifest_ref",batch.manifestRef().toJson());var captures=wire.putArray("captured_refs");batch.capturedRefs().forEach(value->captures.add(value.toJson()));
            var workerInput=OfflineEventAnalysisWire.decodeBatch(StrictJson.canonical(wire));assertEquals(batch,workerInput);assertEquals(observed,EpisodeIncidentJournal.requireBatchManifest(read(workerInput.manifestRef())));
            ObjectNode response=report(observed,batch,f.ticket().incidentId());assertEquals(OfflineBatchBinding.REPORT_V3,response.get("schema").textValue());assertEquals(observed.observation(),OfflineBatchBinding.observationForReport(response));
            Path file=f.journal().configuration().scanRoot().resolve("software-report.json");Files.write(file,StrictJson.canonical(response));f.journal().acknowledge(batch,EpisodeIncidentJournal.measure(file));
            var reopened=EpisodeIncidentJournal.open(f.journal().configuration(),binding(f.request()),f.journal().episodeReference());assertTrue(reopened.scan(binding(f.request())).batch().isEmpty());assertEquals(1,reopened.scan(binding(f.request())).capturedIncidents());
        }
    }
    @Test void legacyV2ManifestAndReportRemainReadableWithoutRewritingTheirBytes()throws Exception {
        var f=fixture(73);var batch=f.journal().scan(binding(f.request())).batch().orElseThrow();byte[] original=Files.readAllBytes(Path.of(batch.manifestRef().path()));ObjectNode legacy=read(batch.manifestRef());legacy.put("schema",OfflineBatchBinding.MANIFEST_V2);((ObjectNode)legacy.at("/scan_observation/frame")).put("played_character_id","73");
        byte[] raw=StrictJson.canonical(legacy);String hash=java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));Path old=f.journal().configuration().scanRoot().resolve("incidents-"+hash+".batch.json");Files.write(old,raw);var request=new OfflineEventAnalysisContract.BatchRequest("incidents-"+hash,EpisodeIncidentJournal.measure(old),batch.capturedRefs());
        var loaded=OfflineScanSource.load(f.journal().configuration().incidentRoot(),Optional.of(f.journal().configuration().scanRoot()),f.request().before().machineId(),request.manifestRef(),request.capturedRefs());assertInstanceOf(OfflineBatchBinding.ObservedScan.class,loaded.binding());OfflineScanSource.recheck(f.journal().configuration().incidentRoot(),Optional.of(f.journal().configuration().scanRoot()),request.manifestRef(),loaded);
        var observed=EpisodeIncidentJournal.requireBatchManifest(legacy);assertInstanceOf(OfflineBatchBinding.LegacyUnsignedActor.class,observed.observation().frame().playedCharacterId());ObjectNode report=report(observed,request,f.ticket().incidentId());assertEquals(OfflineBatchBinding.REPORT_V2,report.get("schema").textValue());
        Path response=f.journal().configuration().scanRoot().resolve("legacy-source.report.json");Files.write(response,StrictJson.canonical(report));f.journal().acknowledge(request,EpisodeIncidentJournal.measure(response));assertTrue(f.journal().scan(binding(f.request())).batch().isEmpty());assertArrayEquals(raw,Files.readAllBytes(old));assertArrayEquals(original,Files.readAllBytes(Path.of(batch.manifestRef().path())));
    }
    @Test void malformedV3ActorAndCrossVersionReportNeverBecomeReviewedEvidence()throws Exception {
        var f=fixture(-2);var batch=f.journal().scan(binding(f.request())).batch().orElseThrow();ObjectNode original=read(batch.manifestRef());
        for(JsonNode wrong:List.of(com.fasterxml.jackson.databind.node.TextNode.valueOf("-2"),com.fasterxml.jackson.databind.node.BooleanNode.TRUE,com.fasterxml.jackson.databind.node.DoubleNode.valueOf(-2.0),com.fasterxml.jackson.databind.node.LongNode.valueOf(2147483648L))){ObjectNode changed=original.deepCopy();((ObjectNode)changed.at("/scan_observation/frame")).set("played_character_id",wrong);assertThrows(java.io.IOException.class,()->EpisodeIncidentJournal.requireBatchManifest(changed));}
        var observed=EpisodeIncidentJournal.requireBatchManifest(original);ObjectNode wrong=report(observed,batch,f.ticket().incidentId());wrong.put("schema",OfflineBatchBinding.REPORT_V2);Path file=f.journal().configuration().scanRoot().resolve("wrong-version.report.json");Files.write(file,StrictJson.canonical(wrong));assertThrows(java.io.IOException.class,()->f.journal().acknowledge(batch,EpisodeIncidentJournal.measure(file)));assertTrue(f.journal().scan(binding(f.request())).batch().isPresent());
    }
}

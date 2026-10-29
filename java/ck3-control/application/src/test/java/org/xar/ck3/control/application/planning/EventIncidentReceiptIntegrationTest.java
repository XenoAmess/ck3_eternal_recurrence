package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Python receipt fixture -> actual Journal before/after -> shared comparator -> original-index replay.
 * Typed before/after observations here are explicitly synthetic software evidence, never live Game credit.
 */
final class EventIncidentReceiptIntegrationTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temporary;
    private record Fixture(EpisodeIncidentJournal journal,EpisodeIncidentJournal.Configuration configuration,
        ActionCommand command,ActionState.Attempt attempt,NativeEffectSnapshots.Pair pair,NativeEffectRegistry.Projected projected) { }

    @Test void actualJournalConsumerVerifiesTheOriginalReceiptAndReplaysItsVersionedInput() throws Exception {
        Fixture f=fixture(false);var ticket=f.journal().before(f.command()).orElseThrow();
        f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        Path indexPath=f.configuration().incidentRoot().resolve(ticket.incidentId()+".after-index.json");
        JsonNode index=StrictJson.parse(Files.readAllBytes(indexPath),1<<20);
        assertEquals("xar.episode-incident-after-index/v2",index.get("schema").textValue());
        assertTrue(index.get("policy_receipt_input").isObject());
        assertArrayEquals(DriverJson.encode(f.command().arguments()),java.util.Base64.getDecoder().decode(index.path("policy_receipt_input").path("original_arguments_base64").textValue()),
            "canonical JSON persistence preserves the actual command encoding as well as its JSON-domain content");
        var reopened=EpisodeIncidentJournal.openOriginal(f.configuration(),f.journal().episodeReference());
        assertEquals(1,reopened.scan(new EpisodeIncidentJournal.Binding(f.command().before(),f.command().source(),f.command().sessionId())).capturedIncidents());
        f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        assertEquals(index,StrictJson.parse(Files.readAllBytes(indexPath),1<<20),"same original callback cannot replace the stored after input");
    }
    @Test void actualMismatchPreservesBothOriginalsBeforeRejectingWithoutASecondSubmission() throws Exception {
        Fixture f=fixture(true);var ticket=f.journal().before(f.command()).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected()));
        Path after=f.configuration().incidentRoot().resolve(ticket.incidentId()+".after.json");
        Path indexPath=f.configuration().incidentRoot().resolve(ticket.incidentId()+".after-index.json");
        assertTrue(Files.isRegularFile(Path.of(ticket.before().path())));assertTrue(Files.isRegularFile(after));assertTrue(Files.isRegularFile(indexPath));
        JsonNode input=StrictJson.parse(Files.readAllBytes(indexPath),1<<20).get("policy_receipt_input");
        assertEquals(2,input.path("legacy_input").path("body").path("result").path("option_index").intValue());
        assertFalse(input.path("legacy_input").path("body").path("unhandled_event_fallback_evidence").path("replay_allowed").booleanValue());
        var reopened=EpisodeIncidentJournal.openOriginal(f.configuration(),f.journal().episodeReference());
        assertThrows(IllegalArgumentException.class,()->reopened.scan(new EpisodeIncidentJournal.Binding(f.command().before(),f.command().source(),f.command().sessionId())));
        assertThrows(IllegalArgumentException.class,()->f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected()));
        assertEquals(input,StrictJson.parse(Files.readAllBytes(indexPath),1<<20).get("policy_receipt_input"));
    }
    @Test void originalCodecRoundTripRetainsReceiptScopeAndMissingAckGetsNoLegacyCredit() throws Exception {
        Fixture f=fixture(false);var ticket=f.journal().before(f.command()).orElseThrow();
        f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        ObjectNode index=(ObjectNode)StrictJson.parse(Files.readAllBytes(f.configuration().incidentRoot().resolve(ticket.incidentId()+".after-index.json")),1<<20);
        ExactRef after=ExactRef.fromJson(index.get("after_ref"));RawJson afterRaw=new RawJson(Files.readAllBytes(Path.of(after.path())));
        RawJson beforeRaw=new RawJson(Files.readAllBytes(Path.of(ticket.before().path())));
        RawJson input=new RawJson(StrictJson.canonical(index.get("policy_receipt_input"),1<<20));
        String argumentsHash=DriverJson.sha256(DriverJson.encode(f.command().arguments()));
        var credit=EventIncidentReceipt.verify(input,argumentsHash,ticket.before(),after,beforeRaw,afterRaw).orElseThrow();
        assertEquals(new org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.BooleanValue(false),credit.get("war_started_verified"));
        assertEquals(new org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.BooleanValue(false),credit.get("title_retention_verified"));
        assertEquals(new org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.BooleanValue(false),credit.get("replay_allowed"));
        ObjectNode changed=(ObjectNode)StrictJson.parse(input.bytes(),1<<20);((ObjectNode)changed.path("legacy_input").path("body").get("result")).remove("accepted");
        assertTrue(EventIncidentReceipt.verify(new RawJson(StrictJson.canonical(changed,1<<20)),argumentsHash,ticket.before(),after,beforeRaw,afterRaw).isEmpty());
        ((ObjectNode)changed.path("legacy_input").path("body").get("result")).put("accepted",false);
        assertThrows(IllegalArgumentException.class,()->EventIncidentReceipt.verify(new RawJson(StrictJson.canonical(changed,1<<20)),argumentsHash,ticket.before(),after,beforeRaw,afterRaw));
    }
    @Test void currentMissingFieldIsRejectedWhileLegacyIndexRetainsItsHistoricalScope() throws Exception {
        Fixture f=fixture(false);var ticket=f.journal().before(f.command()).orElseThrow();f.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        Path path=f.configuration().incidentRoot().resolve(ticket.incidentId()+".after-index.json");
        ObjectNode index=(ObjectNode)StrictJson.parse(Files.readAllBytes(path),1<<20);index.remove("policy_receipt_input");Files.write(path,StrictJson.canonical(index,1<<20));
        var binding=new EpisodeIncidentJournal.Binding(f.command().before(),f.command().source(),f.command().sessionId());
        assertThrows(IllegalArgumentException.class,()->f.journal().scan(binding));
        index.put("schema","xar.episode-incident-after-index/v1");Files.write(path,StrictJson.canonical(index,1<<20));
        assertDoesNotThrow(()->f.journal().scan(binding));
        index.putNull("policy_receipt_input");Files.write(path,StrictJson.canonical(index,1<<20));
        assertThrows(IllegalArgumentException.class,()->f.journal().scan(binding),"legacy data cannot claim a new comparison by adding null");
    }
    private Fixture fixture(boolean badIndex) throws Exception {
        ObjectNode body=originalBody(),plan=(ObjectNode)body.get("plan"),result=((ObjectNode)body.get("result")).deepCopy();
        if(badIndex)result.put("option_index",2);
        ObjectNode binding=(ObjectNode)plan.path("unhandled_event_fallback").get("binding");
        var game=new GameGeneration(binding.get("bridge_pid").intValue(),new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        BigInteger actor=binding.get("actor_character_id").bigIntegerValue(),date=binding.get("date_raw").bigIntegerValue();
        String episode=binding.get("episode_run_id").textValue();
        var before=new ObservationIdentity("synthetic-receipt-machine",game,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,
            binding.get("native_revision").bigIntegerValue(),date),binding.get("snapshot_id").textValue(),binding.get("revision").bigIntegerValue(),episode),1);
        JsonNode selected=result.get("event_selection");var after=new ObservationIdentity(before.machineId(),game,new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,
            before.frame().identity().nativeRevision().add(BigInteger.ONE),date),selected.get("ending_snapshot_id").textValue(),selected.get("ending_revision").bigIntegerValue(),episode),1);
        Path sourcePath=temporary.resolve("synthetic-source.json");Files.writeString(sourcePath,"{\"scope\":\"synthetic-original-receipt-test\"}");
        var source=new G2Source(before.machineId(),NOW.toString(),"1.20.0.4",EpisodeIncidentJournal.measure(sourcePath));String session="synthetic-populist-session";
        ExactRef beforeFrame=file("before-frame.json"),afterFrame=file("after-frame.json"),support=file("effect-basis.json");
        BigInteger connection=binding.get("connection_generation").bigIntegerValue();
        var initial=new Complete(before,source,session,connection,snapshot(before,connection,72),beforeFrame,NOW,"a".repeat(64));
        var changed=new Complete(after,source,session,connection,snapshot(after,connection,0),afterFrame,NOW.plusSeconds(1),"b".repeat(64));
        var expected=new ExpectedPostcondition(1,before,source,NativeEventPostconditionPort.EVENT_SCHEMA,List.of(
            new ExpectedInteger(new FieldKey("old_instance_id"),BigInteger.valueOf(72)),new ExpectedBoolean(new FieldKey("old_instance_advanced"),true),
            new ExpectedInteger(new FieldKey("actor_id"),actor),new ExpectedText(new FieldKey("connection_generation_decimal"),connection.toString())));
        var decodedPlan=object(plan);var keys=new java.util.ArrayList<>(decodedPlan.members().keySet());java.util.Collections.reverse(keys);
        var reversed=new java.util.LinkedHashMap<String,OpportunityJson.Value>();keys.forEach(key->reversed.put(key,decodedPlan.get(key)));
        var command=new ActionCommand("synthetic-populist-original-receipt",before,source,session,new OperationKey("select-event-option-4"),new OpportunityJson.Obj(reversed),expected,
            new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(60));
        var guard=new GuardEvidence(before,source,session,connection,command.operation(),beforeFrame,beforeFrame,"synthetic-original-guard",NOW,NOW.plusSeconds(60));
        var attempt=new ActionState.Attempt("synthetic-populist-request",NOW,guard,new NativeRequest(command.operation().value(),Optional.empty(),new RawJson(new byte[]{'{','}'})));
        var proof=new ActionState.EffectObservation(after,source,session,expected.observerSchema(),expected.values(),new ObservationProvenance.Push(after.frame().snapshotId(),after.frame().identity().nativeRevision(),afterFrame),
            NOW.plusSeconds(1),afterFrame,List.of(support));
        var projected=new NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(proof),Optional.of(new RawJson(StrictJson.canonical(result,1<<20))));
        Path incidents=Files.createDirectory(temporary.resolve("incidents")),scans=Files.createDirectory(temporary.resolve("scans"));
        var configuration=new EpisodeIncidentJournal.Configuration(incidents,scans,Clock.fixed(NOW,ZoneOffset.UTC),pending->{if(pending<0||pending>(1<<20))throw new java.io.IOException("finite synthetic test budget");},Optional.empty());
        var journal=EpisodeIncidentJournal.initialize(configuration,new EpisodeIncidentJournal.Binding(before,source,session));
        return new Fixture(journal,configuration,command,attempt,new NativeEffectSnapshots.Pair(initial,changed),projected);
    }
    private ExactRef file(String name) throws Exception {Path p=temporary.resolve(name);Files.writeString(p,"{\"synthetic\":\""+name+"\"}");return EpisodeIncidentJournal.measure(p);}
    private static OpportunityJson.Obj snapshot(ObservationIdentity identity,BigInteger connection,int event) {
        ObjectNode node=StrictJson.object().put("snapshot_id",identity.frame().snapshotId()).put("revision",identity.frame().revision()).put("native_revision",identity.frame().identity().nativeRevision())
            .put("date_raw",identity.frame().identity().dateRaw()).put("episode_run_id",identity.frame().episodeRunId()).put("paused",true).put("map_ready",true);
        node.putObject("played_character").put("character_id",identity.frame().identity().player()).put("alive",true);
        node.putObject("diagnostics").put("bridge_pid",identity.game().pid()).put("connection_generation",connection);
        if(event==0)node.putNull("active_event");else node.putObject("active_event").put("instance_id",event).put("option_count",4);
        return object(node);
    }
    private static OpportunityJson.Obj object(JsonNode node) {return DriverJson.object(StrictJson.canonical(node,1<<20),1<<20);}
    private static ObjectNode originalBody() throws Exception {
        try(InputStream raw=EventIncidentReceiptIntegrationTest.class.getResourceAsStream("/eventregistry/source-reviewed-populist-receipt-golden-v1.json.gz")) {
            assertNotNull(raw,"original Python producer fixture must be routed into this module by the source map");
            try(InputStream gzip=new GZIPInputStream(raw)) {byte[] bytes=gzip.readNBytes((1<<20)+1);assertTrue(bytes.length<=(1<<20));return ((ObjectNode)StrictJson.parse(bytes,1<<20).path("cases").get(0).get("body")).deepCopy();}
        }
    }
}

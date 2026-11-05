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
        assertArrayEquals(DriverJson.encode(ActionCodec.decodeCommand(ActionCodec.encodeCommand(f.command())).arguments()),java.util.Base64.getDecoder().decode(index.path("policy_receipt_input").path("original_arguments_base64").textValue()),
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
        String argumentsHash=DriverJson.sha256(DriverJson.encode(ActionCodec.decodeCommand(ActionCodec.encodeCommand(f.command())).arguments()));
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
    @Test void codecRoundtripKeepsOneCanonicalIncidentAndQualifiedPolicyReceipt() throws Exception {
        Fixture f=fixture(false);
        ActionCommand decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(f.command()));
        byte[] rawArguments=DriverJson.encode(f.command().arguments());
        byte[] canonicalArguments=DriverJson.encode(decoded.arguments());
        assertFalse(java.util.Arrays.equals(rawArguments,canonicalArguments));
        assertEquals(f.command().arguments(),decoded.arguments());
        assertEquals(ActionCodec.bodySha256(f.command()),ActionCodec.bodySha256(decoded));
        var ticket=f.journal().before(f.command()).orElseThrow();
        byte[] beforeBytes=Files.readAllBytes(Path.of(ticket.before().path()));
        byte[] indexBytes=Files.readAllBytes(Path.of(ticket.index().path()));
        String canonicalHash=DriverJson.sha256(canonicalArguments);
        assertEquals(authoredIncidentId(f.command(),canonicalHash),ticket.incidentId());
        ObjectNode index=(ObjectNode)StrictJson.parse(indexBytes,1<<20);
        assertEquals(canonicalHash,index.get("arguments_sha256").textValue());
        assertEquals(ticket.before(),ExactRef.fromJson(index.get("before_ref")));
        var reopened=EpisodeIncidentJournal.openOriginal(f.configuration(),f.journal().episodeReference());
        assertEquals(ticket,reopened.before(decoded).orElseThrow());
        assertEquals(1,incidentFileCount(f.journal(),".before-index.json"));
        assertEquals(1,incidentFileCount(f.journal(),".before.json"));
        assertArrayEquals(beforeBytes,Files.readAllBytes(Path.of(ticket.before().path())));
        assertArrayEquals(indexBytes,Files.readAllBytes(Path.of(ticket.index().path())));
        reopened.observedAfter(decoded,f.attempt(),f.pair(),f.projected());
        Path afterIndex=f.configuration().incidentRoot().resolve(ticket.incidentId()+".after-index.json");
        byte[] afterIndexBytes=Files.readAllBytes(afterIndex);
        ObjectNode after=(ObjectNode)StrictJson.parse(afterIndexBytes,1<<20);
        assertEquals("xar.episode-incident-after-index/v2",after.get("schema").textValue());
        assertTrue(after.get("policy_receipt_input").isObject());
        ExactRef afterRef=ExactRef.fromJson(after.get("after_ref"));
        byte[] afterBytes=Files.readAllBytes(Path.of(afterRef.path()));
        assertArrayEquals(canonicalArguments,java.util.Base64.getDecoder().decode(after.path("policy_receipt_input").path("original_arguments_base64").textValue()));
        assertEquals(originalExpectedCredit(),EventIncidentReceipt.verify(
            new RawJson(StrictJson.canonical(after.get("policy_receipt_input"),1<<20)),canonicalHash,
            ticket.before(),afterRef,new RawJson(beforeBytes),new RawJson(afterBytes)).orElseThrow());
        var cold=EpisodeIncidentJournal.openOriginal(f.configuration(),f.journal().episodeReference());
        var scan=cold.scan(new EpisodeIncidentJournal.Binding(decoded.before(),decoded.source(),decoded.sessionId()));
        assertEquals(1,scan.capturedIncidents());assertEquals(0,scan.incompleteAfter());
        assertTrue(scan.originals().containsAll(List.of(ticket.before(),ticket.index(),afterRef,EpisodeIncidentJournal.measure(afterIndex))));
        cold.observedAfter(decoded,f.attempt(),f.pair(),f.projected());
        assertEquals(ticket,cold.before(f.command()).orElseThrow());
        assertArrayEquals(beforeBytes,Files.readAllBytes(Path.of(ticket.before().path())));
        assertArrayEquals(indexBytes,Files.readAllBytes(Path.of(ticket.index().path())));
        assertArrayEquals(afterIndexBytes,Files.readAllBytes(afterIndex));
        assertArrayEquals(afterBytes,Files.readAllBytes(Path.of(afterRef.path())));
    }

    @Test void legacyRawIndexRemainsExactAndConflictingOrTamperedOriginalsReject() throws Exception {
        Fixture f=fixture(false);
        ActionCommand decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(f.command()));
        AuthoredLegacy legacy=authoredLegacy(f,"legacy-good");
        var journal=legacy.journal();var rawTicket=legacy.raw();
        byte[] beforeBytes=Files.readAllBytes(Path.of(rawTicket.before().path()));
        byte[] indexBytes=Files.readAllBytes(Path.of(rawTicket.index().path()));
        String rawHash=DriverJson.sha256(DriverJson.encode(f.command().arguments()));
        assertEquals(rawTicket,journal.before(f.command()).orElseThrow());
        assertEquals(rawHash,StrictJson.parse(indexBytes,1<<20).get("arguments_sha256").textValue());
        // A codec-decoded observer has no exact raw argument hash and may not create its own after.
        var missing=assertThrows(java.io.UncheckedIOException.class,()->journal.observedAfter(decoded,f.attempt(),f.pair(),f.projected()));
        assertInstanceOf(java.io.IOException.class,missing.getCause());
        assertNoIncidentAfter(journal);
        assertFalse(Files.exists(Path.of(legacy.seed().index().path())));
        journal.observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        Path afterIndex=journal.configuration().incidentRoot().resolve(rawTicket.incidentId()+".after-index.json");
        byte[] afterIndexBytes=Files.readAllBytes(afterIndex);
        ObjectNode after=(ObjectNode)StrictJson.parse(afterIndexBytes,1<<20);
        ExactRef afterRef=ExactRef.fromJson(after.get("after_ref"));
        byte[] afterBytes=Files.readAllBytes(Path.of(afterRef.path()));
        assertArrayEquals(DriverJson.encode(f.command().arguments()),java.util.Base64.getDecoder().decode(
            after.path("policy_receipt_input").path("original_arguments_base64").textValue()));
        assertEquals(originalExpectedCredit(),EventIncidentReceipt.verify(
            new RawJson(StrictJson.canonical(after.get("policy_receipt_input"),1<<20)),rawHash,
            rawTicket.before(),afterRef,new RawJson(beforeBytes),new RawJson(afterBytes)).orElseThrow());
        var cold=EpisodeIncidentJournal.openOriginal(journal.configuration(),journal.episodeReference());
        var scan=cold.scan(new EpisodeIncidentJournal.Binding(f.command().before(),f.command().source(),f.command().sessionId()));
        assertEquals(1,scan.capturedIncidents());assertEquals(0,scan.incompleteAfter());
        assertTrue(scan.originals().containsAll(List.of(rawTicket.before(),rawTicket.index(),afterRef)));
        cold.observedAfter(f.command(),f.attempt(),f.pair(),f.projected());
        assertEquals(rawTicket,cold.before(f.command()).orElseThrow());
        assertEquals(1,incidentFileCount(journal,".before-index.json"));assertEquals(1,incidentFileCount(journal,".before.json"));
        assertFalse(Files.exists(Path.of(legacy.seed().index().path())));
        assertArrayEquals(beforeBytes,Files.readAllBytes(Path.of(rawTicket.before().path())));
        assertArrayEquals(indexBytes,Files.readAllBytes(Path.of(rawTicket.index().path())));
        assertArrayEquals(afterIndexBytes,Files.readAllBytes(afterIndex));assertArrayEquals(afterBytes,Files.readAllBytes(Path.of(afterRef.path())));
        for(String corruption:List.of("hash","kind","source","before-bytes")) {
            AuthoredLegacy bad=authoredLegacy(f,"bad-"+corruption);
            var badJournal=bad.journal();var ticket=bad.raw();
            ObjectNode badIndex=(ObjectNode)StrictJson.parse(Files.readAllBytes(Path.of(ticket.index().path())),1<<20);
            if(corruption.equals("hash"))badIndex.put("arguments_sha256","0".repeat(64));
            else if(corruption.equals("kind"))badIndex.put("kind","INTERACTION");
            else if(corruption.equals("source"))((ObjectNode)badIndex.get("source")).put("observed_at_utc",NOW.plusSeconds(3).toString());
            else Files.writeString(Path.of(ticket.before().path()),"{\"tampered\":true}");
            byte[] corruptIndex=corruption.equals("before-bytes")?Files.readAllBytes(Path.of(ticket.index().path())):StrictJson.canonical(badIndex,1<<20);
            if(!corruption.equals("before-bytes"))Files.write(Path.of(ticket.index().path()),corruptIndex);
            assertNoIncidentAfter(badJournal);
            assertThrows(java.io.IOException.class,()->badJournal.before(f.command()),corruption);
            var failure=assertThrows(java.io.UncheckedIOException.class,()->badJournal.observedAfter(f.command(),f.attempt(),f.pair(),f.projected()),corruption);
            assertInstanceOf(java.io.IOException.class,failure.getCause());
            assertNoIncidentAfter(badJournal);
            assertArrayEquals(corruptIndex,Files.readAllBytes(Path.of(ticket.index().path())));
        }
        AuthoredLegacy conflict=authoredLegacy(f,"two-exact-originals");
        assertEquals(conflict.raw(),conflict.journal().before(f.command()).orElseThrow());
        // Both complete lanes were independently qualified by public before(); restore the exact seed pair.
        Files.write(Path.of(conflict.seed().before().path()),conflict.seedBefore());
        Files.write(Path.of(conflict.seed().index().path()),conflict.seedIndex());
        assertEquals(2,incidentFileCount(conflict.journal(),".before-index.json"));
        assertEquals(2,incidentFileCount(conflict.journal(),".before.json"));
        var ambiguity=assertThrows(java.io.IOException.class,()->conflict.journal().before(f.command()));
        assertEquals("Conflicting exact incident originals require reconciliation",ambiguity.getMessage());
        var ambiguityAfter=assertThrows(java.io.UncheckedIOException.class,()->conflict.journal().observedAfter(f.command(),f.attempt(),f.pair(),f.projected()));
        assertEquals(ambiguity.getMessage(),ambiguityAfter.getCause().getMessage());assertNoIncidentAfter(conflict.journal());
    }

    /** Authored schema DATA for exact legacy compatibility; never a historical producer/521 execution. */
    private record AuthoredLegacy(EpisodeIncidentJournal journal,EpisodeIncidentJournal.Ticket raw,
        EpisodeIncidentJournal.Ticket seed,byte[] seedBefore,byte[] seedIndex) { }
    private AuthoredLegacy authoredLegacy(Fixture f,String name) throws Exception {
        Path directory=Files.createDirectory(temporary.resolve(name));
        Path incidents=Files.createDirectory(directory.resolve("incidents"));Path scans=Files.createDirectory(directory.resolve("scans"));
        var configuration=new EpisodeIncidentJournal.Configuration(incidents,scans,f.configuration().clock(),f.configuration().io(),f.configuration().trustedInteractions());
        var journal=EpisodeIncidentJournal.initialize(configuration,new EpisodeIncidentJournal.Binding(f.command().before(),f.command().source(),f.command().sessionId()));
        var seed=journal.before(f.command()).orElseThrow();
        byte[] seedBefore=Files.readAllBytes(Path.of(seed.before().path()));byte[] seedIndex=Files.readAllBytes(Path.of(seed.index().path()));
        String rawHash=DriverJson.sha256(DriverJson.encode(f.command().arguments()));String rawId=authoredIncidentId(f.command(),rawHash);
        assertNotEquals(rawId,seed.incidentId(),"the fixture must exercise distinct complete raw and codec lanes");
        String seedText=new String(seedBefore,java.nio.charset.StandardCharsets.UTF_8);
        int at=seedText.indexOf(seed.incidentId());assertTrue(at>=0);assertEquals(at,seedText.lastIndexOf(seed.incidentId()));
        // Replace only generated ID bytes, retaining every original before-body numeric/string token.
        byte[] rawBefore=(seedText.substring(0,at)+rawId+seedText.substring(at+seed.incidentId().length())).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Path beforePath=incidents.resolve(rawId+".before.json");Files.write(beforePath,rawBefore);ExactRef beforeRef=EpisodeIncidentJournal.measure(beforePath);
        ObjectNode rawIndex=(ObjectNode)StrictJson.parse(seedIndex,1<<20);
        rawIndex.put("incident_id",rawId).put("arguments_sha256",rawHash);rawIndex.set("before_ref",beforeRef.toJson());
        Files.write(incidents.resolve(rawId+".before-index.json"),StrictJson.canonical(rawIndex,1<<20));
        // Remove only the two files this fixture's public seed call created; EPISODE/source/effect originals remain.
        Files.delete(Path.of(seed.index().path()));Files.delete(Path.of(seed.before().path()));
        var raw=journal.before(f.command()).orElseThrow();assertEquals(rawId,raw.incidentId());assertEquals(beforeRef,raw.before());
        assertEquals(rawId,StrictJson.parse(Files.readAllBytes(beforePath),1<<20).get("incident_id").textValue());
        assertEquals(1,incidentFileCount(journal,".before-index.json"));assertEquals(1,incidentFileCount(journal,".before.json"));
        return new AuthoredLegacy(journal,raw,seed,seedBefore,seedIndex);
    }
    private static String authoredIncidentId(ActionCommand command,String argumentsHash) {
        return DriverJson.sha256((command.actionId()+"|"+argumentsHash).getBytes(java.nio.charset.StandardCharsets.UTF_8)).substring(0,32);
    }
    private static long incidentFileCount(EpisodeIncidentJournal journal,String suffix) throws Exception {
        try(var files=Files.list(journal.configuration().incidentRoot())) {return files.filter(path->path.getFileName().toString().endsWith(suffix)).count();}
    }
    private static void assertNoIncidentAfter(EpisodeIncidentJournal journal) throws Exception {
        assertEquals(0,incidentFileCount(journal,".after.json"));assertEquals(0,incidentFileCount(journal,".after-index.json"));
        assertEquals(0,incidentFileCount(journal,".unsettled.json"));
    }
    private static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue originalExpectedCredit() throws Exception {
        try(InputStream raw=EventIncidentReceiptIntegrationTest.class.getResourceAsStream("/eventregistry/source-reviewed-populist-receipt-golden-v1.json.gz")) {
            assertNotNull(raw,"the unmodified original Python golden remains the independent expected credit");
            try(InputStream gzip=new GZIPInputStream(raw)) {
                byte[] bytes=gzip.readNBytes((1<<20)+1);assertTrue(bytes.length<=(1<<20));
                JsonNode expected=StrictJson.parse(bytes,1<<20).path("cases").get(0).get("expected");
                return org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.object(
                    org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.parse(StrictJson.canonical(expected,1<<20)));
            }
        }
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

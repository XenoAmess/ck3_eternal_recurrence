package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashSet;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

import java.util.ArrayList;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;

/** Actual Native planes reach ordinary consumers; no applied Start receipt is invented. */
final class SwaySignedNativeTerminalOrdinaryTest {
    private static final ExactRef SOURCE = new ExactRef("software:actual-native-terminal-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-30T00:00:00Z");
    private static final SwayObservationReads.Kind COMPLETION = SwayObservationReads.Kind.COMPLETION;
    private static final SwayObservationReads.Kind TERMINATION = SwayObservationReads.Kind.TERMINATION;

    @Test void actualPublicDecodedCompletionPlanesReachOrdinaryValidation() throws Exception {
        validateFamily(COMPLETION, 10);
    }
    @Test void actualPublicDecodedTerminationPlanesReachOrdinaryValidation() throws Exception {
        validateFamily(TERMINATION, 5);
    }
    private static void validateFamily(SwayObservationReads.Kind family, int expectedCount) throws Exception {
        List<String> failures = new ArrayList<>(); int count = 0;
        for (JsonNode packet : originals()) {
            if (kind(packet)!=family) continue;
            JsonNode raw = body(packet, family); var id = identity(subject(raw));
            var normalized = normalized(packet); var inputs = inputs(family, normalized);
            try { M6TerminalSourceComposition.validateInputs(inputs, id, binding(packet,raw).before()); }
            catch (IllegalArgumentException failure) { failures.add(requestId(packet)+" actor="+id.actorCharacterId()+" target="+id.targetCharacterId()+": "+failure.getMessage()); }
            count++;
        }
        assertEquals(expectedCount, count, "mandatory unchanged actual Native packets");
        assertEquals(List.of(), failures, "actual public normalized plane rejected at ordinary validation");
    }

    @Test void ordinaryLifecycleEntryRequiresItsRealStartRecordAfterPlaneValidation() throws Exception {
        List<String> failures = new ArrayList<>(); int count = 0;
        for (JsonNode packet : originals()) {
            var family = kind(packet); JsonNode raw = body(packet, family); var id = identity(subject(raw));
            var queried = binding(packet, raw).before(); var inputs = inputs(family, normalized(packet));
            // Empty copied original is deliberately an absence control, never an applied receipt.
            var episode = new Episode(id, Optional.empty(), Optional.empty(), Optional.empty(), ProjectionJson.object("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8), SwayNativeWire.MAX));
            var state = SwayLifecycle.empty(id, queried);
            var failure = assertThrows(IllegalArgumentException.class, () -> SwayLifecycle.observe(state, episode, inputs, queried));
            boolean missingOriginal = failure.getMessage().equals("JSON string required")
                    && java.util.Arrays.stream(failure.getStackTrace()).anyMatch(frame -> frame.getClassName().equals(M6TerminalSourceComposition.class.getName()) && frame.getMethodName().equals("original"));
            if (!missingOriginal) failures.add(requestId(packet)+": "+failure.getMessage());
            assertTrue(state.latest().isEmpty() && state.terminal().isEmpty()); count++;
        }
        assertEquals(15, count);
        assertEquals(List.of(), failures, "ordinary entry must pass native plane validation and stop at missing real Start status");
    }

    @Test void ordinaryCompletionStillRejectsSentinelUnsignedAliasCrossedPairAndFrame() throws Exception {
        JsonNode packet = originals().get(0); assertEquals(COMPLETION, kind(packet)); JsonNode raw = body(packet, COMPLETION);
        var id = identity(subject(raw)); var queried = binding(packet, raw).before();
        ObjectNode positive = (ObjectNode)StrictJson.parse(normalized(packet).bytes());
        for (String text : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "0.0", "\"0\"", "null")) {
            for (String field : List.of("actor_character_id", "target_character_id")) {
                ObjectNode bad = positive.deepCopy(); bad.set(field, StrictJson.parse(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateInputs(inputs(COMPLETION, projection(bad)), id, queried), field+":"+text);
            }
        }
        ObjectNode crossed = positive.deepCopy(); crossed.put("target_character_id", 1);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateInputs(inputs(COMPLETION, projection(crossed)), id, queried));
        ObjectNode wrongGeneration = positive.deepCopy(); wrongGeneration.put("scheme_instance_generation", id.schemeInstanceGeneration() ^ 1);
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateInputs(inputs(COMPLETION, projection(wrongGeneration)), id, queried));
        ObjectNode wrongRevision = positive.deepCopy(); wrongRevision.put("snapshot_revision", raw.get("snapshot_revision").bigIntegerValue().add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> M6TerminalSourceComposition.validateInputs(inputs(COMPLETION, projection(wrongRevision)), id, queried));
    }

    private static ProjectionJson normalized(JsonNode packet) {
        var family=kind(packet); JsonNode raw=body(packet,family); var subject=subject(raw);
        if (family==COMPLETION) {
            var query = SwayObservationReads.Query.current(family, identity(subject));
            var contract = SwayObservationReads.contract(SOURCE, query);
            return contract.decode(receipt(contract, request(contract, SwayObservationReads.arguments(query), packet, raw), packet)).normalized();
        }
        var query = new SwayObservationReads.JournalQuery(family, subject, raw.get("after_sequence").bigIntegerValue());
        var contract = SwayObservationReads.journalContract(SOURCE, query);
        return contract.decode(receipt(contract, request(contract, SwayObservationReads.arguments(query), packet, raw), packet)).normalized();
    }
    private static M6TerminalSourceComposition.Inputs inputs(SwayObservationReads.Kind kind, ProjectionJson value) {
        return new M6TerminalSourceComposition.Inputs(kind==COMPLETION?Optional.of(value):Optional.empty(), Optional.empty(), kind==TERMINATION?Optional.of(value):Optional.empty(), Optional.empty());
    }
    private static ProjectionJson projection(JsonNode value) { return ProjectionJson.object(StrictJson.canonical(value,SwayNativeWire.MAX),SwayNativeWire.MAX); }
    private static JsonNode originals() throws Exception {
        try (var stream = SwaySignedNativeTerminalOrdinaryTest.class.getResourceAsStream("/sway/m6-native-signed-terminal.json")) {
            assertNotNull(stream, "mandatory actual Native serializer packets, never cloud-authored positives");
            JsonNode rows = StrictJson.parse(stream.readAllBytes(), SwayNativeWire.MAX); assertTrue(rows.isArray() && rows.size() >= 4); return rows;
        }
    }
    private static SwayObservationReads.Kind kind(JsonNode packet) { return packet.path("result").has("sway_completion") ? COMPLETION : TERMINATION; }
    private static JsonNode body(JsonNode packet, SwayObservationReads.Kind kind) { return packet.path("result").get(kind == COMPLETION ? "sway_completion" : "sway_completion_termination"); }
    private static String requestId(JsonNode packet) { return packet.get("request_id").textValue(); }
    private static NativeSubject subject(JsonNode body) { long instance = body.get("scheme_instance_id").longValue(); return new NativeSubject(NativeCharacterId.fromJson(body.get("actor_character_id")).value(), NativeCharacterId.fromJson(body.get("target_character_id")).value(), instance, (int)(instance >>> 24)); }
    private static Identity identity(NativeSubject subject) { return new Identity("software-native-terminal-original", subject.actorCharacterId(), subject.targetCharacterId(), subject.schemeInstanceId(), subject.schemeInstanceGeneration()); }
    private static SwayNativeWire.Binding binding(JsonNode packet, JsonNode body) {
        JsonNode envelope = packet.get("result"); JsonNode revision = body.has("snapshot_revision") ? body.get("snapshot_revision") : envelope.get("snapshot_revision"); JsonNode date = body.has("date_raw") ? body.get("date_raw") : envelope.get("date_raw");
        var id = new JointBudgetSelector.Frame(BigInteger.valueOf(subject(body).actorCharacterId()), revision.bigIntegerValue(), date.bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(id, "software-native-terminal-snapshot", BigInteger.valueOf(9), "software-native-terminal-episode");
        var observed = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000074"))), frame, 1);
        return new SwayNativeWire.Binding(observed, "software-native-terminal-session", BigInteger.ONE, "software-native-terminal-authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    private static PlanningReadRequest request(ReadContract<?> contract, org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj args, JsonNode packet, JsonNode body) {
        var binding = binding(packet, body); return new PlanningReadRequest(binding.before(), new G2Source(binding.before().machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE), binding.sessionId(), contract.operation(), args, NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract, PlanningReadRequest request, JsonNode packet) {
        var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, contract.operation(), SOURCE, SOURCE, "software-native-terminal-authority", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64)); byte[] bytes = StrictJson.canonical(packet, SwayNativeWire.MAX);
        byte[] framed = ByteBuffer.allocate(bytes.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack = new NativeActionPort.AckReceived(requestId(packet), true, Optional.of(new RawJson(StrictJson.canonical(packet.get("result"), SwayNativeWire.MAX))), new RawJson(bytes), framed);
        return new PlanningReadReceipt(request, contract.contractId(), requestId(packet), guard, guard, ack);
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value, SwayNativeWire.MAX)); }
}

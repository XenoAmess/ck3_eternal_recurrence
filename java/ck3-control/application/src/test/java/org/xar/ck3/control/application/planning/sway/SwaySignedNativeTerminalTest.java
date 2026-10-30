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

/** Mandatory unedited packets from the isolated actual Native serializer; no Game or submitted-action credit. */
final class SwaySignedNativeTerminalTest {
    private static final ExactRef SOURCE = new ExactRef("software:actual-native-terminal-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-30T00:00:00Z");
    private static final SwayObservationReads.Kind COMPLETION = SwayObservationReads.Kind.COMPLETION;
    private static final SwayObservationReads.Kind TERMINATION = SwayObservationReads.Kind.TERMINATION;

    @Test void actualNativePacketsSurvivePublicTypedPrepareDecodeAndPublicOutput() throws Exception {
        var actors = new EnumMap<SwayObservationReads.Kind,Set<Long>>(SwayObservationReads.Kind.class);
        var targets = new EnumMap<SwayObservationReads.Kind,Set<Long>>(SwayObservationReads.Kind.class);
        Set<SwayObservationReads.Kind> kinds = new HashSet<>();
        int terminationRecords = 0;
        for (JsonNode packet : originals()) {
            var kind = kind(packet); var body = body(packet, kind); var nativeSubject = subject(body);
            actors.computeIfAbsent(kind, ignored -> new HashSet<>()).add(nativeSubject.actorCharacterId());
            targets.computeIfAbsent(kind, ignored -> new HashSet<>()).add(nativeSubject.targetCharacterId()); kinds.add(kind);
            assertTrue(body.get("available").booleanValue(), "positive Native packet must actually be available");
            ReadContract<?> contract; PlanningReadRequest request; Object plane;
            if (kind == COMPLETION) {
                var input = new SwayPublicCodec.DirectRequest(kind, binding(packet, body).before().frame().revision(), nativeSubject.targetCharacterId(), OptionalLong.of(nativeSubject.schemeInstanceId()));
                assertEquals(input, SwayPublicCodec.decodeDirect(kind, SwayPublicCodec.encodeDirectRequest(input)));
                var query = new SwayObservationReads.DirectQuery(kind, new SwayObservationReads.CompletionSubject(nativeSubject));
                var direct = SwayObservationReads.directContract(SOURCE, query); contract = direct;
                request = request(contract, SwayObservationReads.arguments(query), packet, body);
                plane = direct.decode(receipt(contract, request, packet));
                var ordinaryQuery = SwayObservationReads.Query.current(kind, identity(nativeSubject));
                var ordinary = SwayObservationReads.contract(SOURCE, ordinaryQuery);
                var ordinaryRequest = request(ordinary, SwayObservationReads.arguments(ordinaryQuery), packet, body);
                assertEquals(StrictJson.parse(contract.prepare(request, requestId(packet)).additionalFields().bytes()),
                        StrictJson.parse(ordinary.prepare(ordinaryRequest, requestId(packet)).additionalFields().bytes()));
                assertArrayEquals(((SwayObservationReads.DirectPlane)plane).normalized().bytes(), ordinary.decode(receipt(ordinary, ordinaryRequest, packet)).normalized().bytes());
            } else {
                BigInteger cursor = body.get("after_sequence").bigIntegerValue();
                var input = new SwayPublicCodec.JournalRequest(kind, binding(packet, body).before().frame().revision(), nativeSubject.targetCharacterId(), nativeSubject.schemeInstanceId(), cursor);
                assertEquals(input, SwayPublicCodec.decodeJournal(kind, SwayPublicCodec.encodeJournalRequest(input)));
                var query = new SwayObservationReads.JournalQuery(kind, nativeSubject, cursor);
                var journal = SwayObservationReads.journalContract(SOURCE, query); contract = journal;
                request = request(contract, SwayObservationReads.arguments(query), packet, body);
                plane = journal.decode(receipt(contract, request, packet));
            }
            JsonNode prepared = StrictJson.parse(contract.prepare(request, requestId(packet)).additionalFields().bytes());
            assertEquals(nativeSubject.actorCharacterId(), NativeCharacterId.fromJson(prepared.get("actor_character_id")).value());
            assertEquals(nativeSubject.targetCharacterId(), NativeCharacterId.fromJson(prepared.get("target_character_id")).value());
            assertEquals(nativeSubject.schemeInstanceId(), prepared.get("scheme_instance_id").longValue());
            JsonNode normalized; JsonNode result;
            if (plane instanceof SwayObservationReads.DirectPlane value) {
                normalized = StrictJson.parse(value.normalized().bytes());
                result = StrictJson.parse(SwayPublicCodec.publicNormalized(new SwayObservationReads.DirectBatch(value, Optional.empty())).bytes());
            } else if (plane instanceof SwayObservationReads.JournalPlane value) {
                normalized = StrictJson.parse(value.normalized().bytes());
                result = StrictJson.parse(SwayPublicCodec.publicNormalized(value).bytes());
            } else throw new AssertionError("unexpected typed terminal plane");
            for (var field : body.properties()) assertEquals(field.getValue(), normalized.get(field.getKey()), field.getKey());
            assertEquals(nativeSubject.actorCharacterId(), NativeCharacterId.fromJson(result.get("actor_character_id")).value());
            assertEquals(nativeSubject.targetCharacterId(), NativeCharacterId.fromJson(result.get("target_character_id")).value());
            assertFalse(result.has("action_id")); assertFalse(result.has("sway_terminal_sources_12004"));
            if (kind == COMPLETION) {
                assertEquals(body.get("native_owner_raw"), result.get("native_owner_raw"), "owner remains raw uint32");
                assertFalse(result.get("terminal_cause_observed").booleanValue());
            } else {
                assertEquals(body.get("after_sequence").bigIntegerValue().toString(), result.get("after_sequence").textValue());
                assertFalse(result.get("material_effect_observed").booleanValue());
                terminationRecords += body.get("records").size();
            }
        }
        assertEquals(Set.of(COMPLETION, TERMINATION), kinds, "mandatory actual serializer families");
        for (var kind : List.of(COMPLETION, TERMINATION)) {
            assertTrue(actors.get(kind).containsAll(Set.of((long)Integer.MIN_VALUE, -2L, 0L, (long)Integer.MAX_VALUE)), kind + " actual canonical signed actor coverage");
            assertTrue(targets.get(kind).containsAll(Set.of((long)Integer.MIN_VALUE, -2L, 0L, (long)Integer.MAX_VALUE)), kind + " actual canonical signed target coverage");
        }
        assertTrue(terminationRecords > 0, "mandatory actual Native recorder rows");
    }

    @Test void actualCompletionOwnerBitsRetainLiveAndClearedLifecycleStates() throws Exception {
        boolean liveNegative = false, cleared = false;
        for (JsonNode packet : originals()) {
            if (kind(packet) != COMPLETION) continue;
            JsonNode body = body(packet, COMPLETION); NativeSubject subject = subject(body);
            var observation = M6SourceProducer.fromRawCompletion(StrictJson.canonical(body, SwayNativeWire.MAX), identity(subject));
            long rawOwner = body.get("native_owner_raw").longValue(); int status = body.get("native_status_raw").intValue();
            if (status == 0 && rawOwner == Integer.toUnsignedLong(Math.toIntExact(subject.actorCharacterId()))) {
                assertEquals(M6SourceProducer.NativeState.CONTINUE, observation.nativeState(), "actual raw owner keeps the full signed actor bits");
                ObjectNode wrongGeneration = ((ObjectNode)body).deepCopy();
                wrongGeneration.put("native_owner_raw", rawOwner ^ 0x0100_0000L);
                assertEquals(M6SourceProducer.NativeState.UNOBSERVED,
                        M6SourceProducer.fromRawCompletion(StrictJson.canonical(wrongGeneration, SwayNativeWire.MAX), identity(subject)).nativeState(),
                        "software negative control: same slot with another full generation cannot match the actor");
                liveNegative |= subject.actorCharacterId() < 0;
            } else if (status == 1 && rawOwner == 0xffff_ffffL) {
                assertEquals(M6SourceProducer.NativeState.TERMINATED_UNATTRIBUTED, observation.nativeState()); cleared = true;
            }
        }
        assertTrue(liveNegative, "mandatory actual negative actor live-owner case");
        assertTrue(cleared, "mandatory actual cleared-owner terminal case");
    }

    @Test void malformedSentinelsUnsignedAliasesAndCrossedNativeIdentitiesStayRejected() throws Exception {
        for (var kind : List.of(COMPLETION, TERMINATION)) {
            JsonNode original = null;
            for (JsonNode packet : originals()) if (kind(packet) == kind) { original = packet; break; }
            assertNotNull(original, "mandatory actual Native family");
            final JsonNode positive = original; final JsonNode body = body(positive, kind); final NativeSubject subject = subject(body);
            for (String bad : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "0.0", "\"0\"", "null")) {
                JsonNode wrong = StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                ObjectNode publicArgs = StrictJson.object(); publicArgs.put("expected_revision", "9"); publicArgs.set("target_character_id", wrong); publicArgs.put("scheme_instance_id", subject.schemeInstanceId());
                if (kind == COMPLETION) assertThrows(IllegalArgumentException.class, () -> SwayPublicCodec.decodeDirect(kind, raw(publicArgs)), bad);
                else assertThrows(IllegalArgumentException.class, () -> SwayPublicCodec.decodeJournal(kind, raw(publicArgs)), bad);
                for (String field : List.of("actor_character_id", "target_character_id")) {
                    ObjectNode changed = ((ObjectNode)positive).deepCopy(); ((ObjectNode)body(changed, kind)).set(field, wrong);
                    assertThrows(IllegalArgumentException.class, () -> decode(kind, subject, positive, changed), field + ":" + bad);
                }
            }
            for (String field : List.of("actor_character_id", "target_character_id")) {
                ObjectNode changed = ((ObjectNode)positive).deepCopy(); ((ObjectNode)body(changed, kind)).put(field, field.startsWith("actor") ? subject.targetCharacterId() : subject.actorCharacterId());
                assertThrows(IllegalArgumentException.class, () -> decode(kind, subject, positive, changed), field);
            }
        }
    }

    @Test void unprovenExecutionAndStopDomainsStayUnchanged() {
        for (long value : new long[]{Integer.MIN_VALUE, -2, 0}) {
            assertThrows(IllegalArgumentException.class, () -> new SwayPublicCodec.JournalRequest(SwayObservationReads.Kind.EXECUTION, BigInteger.ONE, value, 1, BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.JournalQuery(SwayObservationReads.Kind.EXECUTION, new NativeSubject(value, 7, 1, 0), BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.currentCharacter(value));
        }
    }

    private static Object decode(SwayObservationReads.Kind kind, NativeSubject subject, JsonNode positive, JsonNode changed) {
        JsonNode body = body(positive, kind);
        if (kind == COMPLETION) {
            var query = new SwayObservationReads.DirectQuery(kind, new SwayObservationReads.CompletionSubject(subject)); var contract = SwayObservationReads.directContract(SOURCE, query);
            return contract.decode(receipt(contract, request(contract, SwayObservationReads.arguments(query), positive, body), changed));
        }
        var query = new SwayObservationReads.JournalQuery(kind, subject, body.get("after_sequence").bigIntegerValue()); var contract = SwayObservationReads.journalContract(SOURCE, query);
        return contract.decode(receipt(contract, request(contract, SwayObservationReads.arguments(query), positive, body), changed));
    }
    private static JsonNode originals() throws Exception {
        try (var stream = SwaySignedNativeTerminalTest.class.getResourceAsStream("/sway/m6-native-signed-terminal.json")) {
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

package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Retained JSON from the actual isolated Native producer; no live Game result. */
final class SwaySignedNativeOpinionTest {
    private static final ExactRef SOURCE = new ExactRef("software:isolated-native-opinion-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-30T00:00:00Z");
    private static final String REQUEST = "software-native-opinion-read";
    private static final SwayObservationReads.Kind OPINION = SwayObservationReads.Kind.OPINION;

    @Test void actualBodiesSurvivePublicRequestTypedPrepareDecodeAndPublicResult() throws Exception {
        Set<Long> actors = new HashSet<>(), targets = new HashSet<>();
        for (JsonNode body : originals()) {
            long actor = NativeCharacterId.fromJson(body.get("actor_character_id")).value();
            long target = NativeCharacterId.fromJson(body.get("target_character_id")).value();
            assertTrue(body.get("available").booleanValue(), "signed producer case must really be available");
            actors.add(actor); targets.add(target);
            var publicRequest = new SwayPublicCodec.DirectRequest(OPINION, binding(body).before().frame().revision(), target, OptionalLong.empty());
            var decodedPublic = SwayPublicCodec.decodeDirect(OPINION, SwayPublicCodec.encodeDirectRequest(publicRequest));
            assertEquals(publicRequest, decodedPublic);
            var query = new SwayObservationReads.DirectQuery(OPINION, new SwayObservationReads.OpinionSubject(new SwayObservationReads.Actors(actor, decodedPublic.targetCharacterId())));
            var contract = SwayObservationReads.directContract(SOURCE, query);
            var request = request(contract, query, body);
            JsonNode args = StrictJson.parse(contract.prepare(request, REQUEST).additionalFields().bytes());
            assertEquals(actor, NativeCharacterId.fromJson(args.get("actor_character_id")).value());
            assertEquals(target, NativeCharacterId.fromJson(args.get("target_character_id")).value());
            assertEquals(Set.of("actor_character_id", "target_character_id"), fieldNames(args));
            var plane = contract.decode(receipt(contract, request, body));
            // The ordinary wrapper carries an explicit software origin; the Native opinion body has no action/instance fields.
            var ordinaryQuery = SwayObservationReads.Query.current(OPINION, new Identity("software-signed-opinion-origin", actor, target, 0, 0));
            var ordinaryContract = SwayObservationReads.contract(SOURCE, ordinaryQuery);
            var ordinaryRequest = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), ordinaryContract.operation(), SwayObservationReads.arguments(ordinaryQuery), request.deadline());
            JsonNode ordinaryArgs = StrictJson.parse(ordinaryContract.prepare(ordinaryRequest, REQUEST).additionalFields().bytes());
            assertEquals(args, ordinaryArgs);
            var ordinary = ordinaryContract.decode(receipt(ordinaryContract, ordinaryRequest, body));
            assertArrayEquals(plane.normalized().bytes(), ordinary.normalized().bytes());
            JsonNode normalized = StrictJson.parse(plane.normalized().bytes());
            for (var field : body.properties()) assertEquals(field.getValue(), normalized.get(field.getKey()), field.getKey());
            JsonNode result = StrictJson.parse(SwayPublicCodec.publicNormalized(new SwayObservationReads.DirectBatch(plane, Optional.empty())).bytes());
            assertEquals(actor, NativeCharacterId.fromJson(result.get("actor_character_id")).value());
            assertEquals(target, NativeCharacterId.fromJson(result.get("target_character_id")).value());
            assertEquals(body.get("snapshot_revision").bigIntegerValue().toString(), result.get("snapshot_revision").textValue());
            for (String key : List.of("target_opinion_of_actor", "scheme_sway_opinion", "sway_blocker_opinion")) assertEquals(body.get(key), result.get(key));
            assertFalse(result.has("action_id")); assertFalse(result.has("scheme_instance_id"));
            assertFalse(result.get("instance_terminal_outcome_observed").booleanValue());
            assertFalse(result.get("cancel_outcome_observed").booleanValue());
        }
        assertTrue(actors.containsAll(Set.of((long)Integer.MIN_VALUE, -2L, 0L, (long)Integer.MAX_VALUE)), "actual signed actor coverage");
        assertTrue(targets.containsAll(Set.of((long)Integer.MIN_VALUE, -2L, 0L, (long)Integer.MAX_VALUE)), "actual signed target coverage");
    }

    @Test void sentinelsWrongTypesUnsignedAliasesAndCrossedIdentitiesAreRefused() throws Exception {
        JsonNode original = originals().get(0);
        long actor = NativeCharacterId.fromJson(original.get("actor_character_id")).value(), target = NativeCharacterId.fromJson(original.get("target_character_id")).value();
        var query = new SwayObservationReads.DirectQuery(OPINION, new SwayObservationReads.OpinionSubject(new SwayObservationReads.Actors(actor, target)));
        var contract = SwayObservationReads.directContract(SOURCE, query); var request = request(contract, query, original);
        for (String bad : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "0.0", "\"0\"", "null")) {
            var node = StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var publicArgs = StrictJson.object(); publicArgs.put("expected_revision", "7"); publicArgs.set("target_character_id", node);
            assertThrows(IllegalArgumentException.class, () -> SwayPublicCodec.decodeDirect(OPINION, new RawJson(StrictJson.canonical(publicArgs))), bad);
            for (String field : List.of("actor_character_id", "target_character_id")) {
                var changed = ((ObjectNode)original).deepCopy(); changed.set(field, node);
                assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, request, changed)), field + ":" + bad);
            }
        }
        for (String field : List.of("actor_character_id", "target_character_id")) {
            var changed = ((ObjectNode)original).deepCopy(); changed.put(field, field.startsWith("actor") ? target : actor);
            assertThrows(IllegalArgumentException.class, () -> contract.decode(receipt(contract, request, changed)), field);
        }
        assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.Actors(-1, 7));
        assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.Actors(7, -1));
    }

    @Test void opinionSupportDoesNotWidenCompletionJournalOrOldTargetAndStopRoutes() {
        for (long signed : new long[]{Integer.MIN_VALUE, -2, 0}) {
            assertThrows(IllegalArgumentException.class, () -> new SwayPublicCodec.DirectRequest(SwayObservationReads.Kind.COMPLETION, BigInteger.ONE, signed, OptionalLong.of(1)));
            assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.CompletionSubject(new NativeSubject(signed, 7, 1, 0)));
            assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.CompletionSubject(new NativeSubject(7, signed, 1, 0)));
            assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.JournalQuery(SwayObservationReads.Kind.EXECUTION, new NativeSubject(signed, 7, 1, 0), BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class, () -> new SwayObservationReads.InvalidationQuery(new NativeSubject(signed, 7, 1, 0), BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class, () -> SwayObservationReads.contract(SOURCE, SwayObservationReads.Query.current(SwayObservationReads.Kind.COMPLETION, new Identity("software-positive-only-completion", signed, 7, 1, 0))));
            assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.currentCharacter(signed));
        }
    }

    private static JsonNode originals() throws Exception {
        try (var stream = SwaySignedNativeOpinionTest.class.getResourceAsStream("/sway/m6-native-signed-opinion.json")) {
            assertNotNull(stream, "mandatory actual isolated Native serializer artifact");
            var rows = StrictJson.parse(stream.readAllBytes(), SwayNativeWire.MAX);
            assertTrue(rows.isArray() && rows.size() >= 4, "mandatory actual Native cases");
            return rows;
        }
    }
    private static Set<String> fieldNames(JsonNode node) {
        Set<String> result = new HashSet<>(); node.fieldNames().forEachRemaining(result::add); return Set.copyOf(result);
    }
    private static SwayNativeWire.Binding binding(JsonNode body) {
        long actor = NativeCharacterId.fromJson(body.get("actor_character_id")).value();
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(actor), body.get("snapshot_revision").bigIntegerValue(), body.get("date_raw").bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(identity, "software-native-opinion-snapshot", BigInteger.valueOf(9), "software-native-opinion-episode");
        var origin = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000074"))), frame, 1);
        return new SwayNativeWire.Binding(origin, "software-native-opinion-session", BigInteger.ONE, "software-native-opinion-authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    private static PlanningReadRequest request(ReadContract<?> contract, SwayObservationReads.DirectQuery query, JsonNode body) {
        var bound = binding(body);
        return new PlanningReadRequest(bound.before(), new G2Source(bound.before().machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE), bound.sessionId(), contract.operation(), SwayObservationReads.arguments(query), NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract, PlanningReadRequest request, JsonNode body) {
        var bound = new SwayNativeWire.Binding(request.before(), request.sessionId(), BigInteger.ONE, "software-native-opinion-authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
        var evidence = new GuardEvidence(request.before(), request.source(), bound.sessionId(), bound.connectionGeneration(), contract.operation(), SOURCE, SOURCE, bound.authorityId(), NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
        var packet = StrictJson.object(); packet.put("type", "command_result"); packet.put("protocol_version", 1); packet.put("request_id", REQUEST); packet.put("ok", true);
        var result = packet.putObject("result"); result.put("step", OPINION.step()); result.put("accepted", true); result.put("status", body.get("available").booleanValue() ? "available" : "unavailable"); result.put("private_build", true); result.put("read_only", true); result.put("advertised", false); result.put("backend_id", "native-headless"); result.set("sway_outcome_opinion", body);
        byte[] bytes = StrictJson.canonical(packet, SwayNativeWire.MAX); byte[] framed = ByteBuffer.allocate(bytes.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack = new NativeActionPort.AckReceived(REQUEST, true, Optional.of(new RawJson(StrictJson.canonical(result, SwayNativeWire.MAX))), new RawJson(bytes), framed);
        return new PlanningReadReceipt(request, contract.contractId(), REQUEST, guard, guard, ack);
    }
}

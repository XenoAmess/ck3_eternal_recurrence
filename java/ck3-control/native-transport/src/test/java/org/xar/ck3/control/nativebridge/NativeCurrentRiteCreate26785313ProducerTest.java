package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original18 are SHA-pinned C++ software resources. Mutations/exported packets are Java test DATA, never live Native authority. */
class NativeCurrentRiteCreate26785313ProducerTest {
    private record Artifact(String name, int bytes, String sha256) { }
    private static final List<Artifact> CPP = List.of(
        new Artifact("accept-dispatched.json", 1514, "fc81949adf4f15ae19b0054ed2979d7f2eebcde2ab82c53b4cf41c95ebcd69ee"),
        new Artifact("cleanup-unknown.json", 1258, "2305c10953250e68a6d6d74c8d5d241f224b0e33026b4b883c1fd4029a49a61a"),
        new Artifact("confirmation-native-can-false.json", 1496, "0513275d9073ad079783b687c9bfe4963285eac6c6b90b99764c495ee970d4ec"),
        new Artifact("confirmation-pending.json", 917, "d54454a7972374f611945c542dd109f8fb105f62d3781adb78f340906a8b9c51"),
        new Artifact("confirmation-ready.json", 1483, "630fc22b54d562b667481b9023b04b2591ab4c14e61af469075fea4019727111"),
        new Artifact("create-dispatched.json", 1619, "d2c8a422a440ac20d812021a2e3d64290d1d9f6f56d4181a192b59a242b7b411"),
        new Artifact("draft-actor-minus-two.json", 1591, "e940fc578f2ddf1f9f7e2ab78df8512578f1e4a3fe10d648f86522b32ea62f2e"),
        new Artifact("draft-actor-zero.json", 1583, "e8304597acdbe285740d6b933b299abb3f951b9696d05c884c23270910defd8b"),
        new Artifact("draft-is-creating-false.json", 1601, "8610318b17fa7c9b89df33e466eb75b9348f95aa6ecf29e4744b4c932bba813f"),
        new Artifact("draft-native-can-false.json", 1600, "141bdc85724b4bf98f4e6b91eabe8142680bdf0214fdfe0178c0770f74807c90"),
        new Artifact("draft-ready.json", 1587, "59011dedfe19cdf4426f900e8401c529e6103241a786dd9022b3a4e7d33c379c"),
        new Artifact("expired.json", 879, "80bbef36652015dc5a05eee6b2419ab2ac7421bcce2420b7b0fdf76c7c4f7a89"),
        new Artifact("request-accept_confirmation.json", 846, "fc277d001aa81006b1459db67ccb355d5d5bb9aab019519dad1ecf8c8e9ec728"),
        new Artifact("request-create.json", 820, "735b9df4a2bdd54dd57f29186a5c6f5cdc478b2bbee929b5dc3710b7745a37e5"),
        new Artifact("request-query.json", 780, "f4acc37f85cb401b8c97ddc4fef3a276770412b1013f52dc631c23ccc4de5f9d"),
        new Artifact("request-query_confirmation.json", 844, "dceb68b239b1e34e104c3d40e6b66173f49b732c99d4701ef4b148dd89376fa1"),
        new Artifact("stale-source.json", 889, "93130e24a13d31416177845ac7831fc6131afb4b6246fad1061d31865a425839"),
        new Artifact("unavailable.json", 848, "760965b90fbd8998913148e1840825eeb682705cf8929eb9a83b2675759f6fa6")
    );
    private static final BigInteger MAX_U64 = new BigInteger("18446744073709551615");
    private static final String DRAFT = "draft-ready.json";
    private static final String CONFIRMATION = "confirmation-ready.json";
    private static final List<String> RESPONSES = List.of("accept-dispatched.json", "cleanup-unknown.json",
            "confirmation-native-can-false.json", "confirmation-pending.json", CONFIRMATION, "create-dispatched.json",
            "draft-actor-minus-two.json", "draft-actor-zero.json", "draft-is-creating-false.json",
            "draft-native-can-false.json", DRAFT, "expired.json", "stale-source.json", "unavailable.json");

    private static byte[] raw(String name) throws Exception {
        var expected = CPP.stream().filter(a -> a.name().equals(name)).findFirst().orElseThrow();
        try (var in = NativeCurrentRiteCreate26785313ProducerTest.class.getResourceAsStream("/current267-rite-create-cpp-a01/" + name)) {
            if (in == null) throw new IOException("Original C++ Rite CREATE resource absent: " + name);
            byte[] bytes = in.readAllBytes(); assertEquals(expected.bytes(), bytes.length, name);
            assertEquals(expected.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception { return NativeWire.object(NativeWire.parse(raw(name))); }
    private static ObjectNode token(String name) throws Exception { return NativeWire.object(envelope(name).get("result")); }
    private static CurrentRiteCreateResult frame(String name) throws Exception {
        return CurrentRiteCreateResult.decode(new RawJson(NativeWire.token(raw(name), "result")));
    }
    private static CurrentRiteCreateResult changed(ObjectNode n) throws IOException {
        // Preserve integer versus floating JSON token kinds; canonicalization can normalize a1.0 DATA token.
        return CurrentRiteCreateResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode source(ObjectNode n) { return (ObjectNode) n.get("source"); }
    private static ObjectNode draft(ObjectNode n) { return (ObjectNode) source(n).get("draft"); }
    private static ObjectNode confirmation(ObjectNode n) { return (ObjectNode) source(n).get("confirmation"); }
    private static ObjectNode facts(ObjectNode n) { return (ObjectNode) n.get("facts_before"); }
    private static ObjectNode owner(ObjectNode n) { return (ObjectNode) n.get("owner"); }
    private static void reject(ObjectNode n) { assertThrows(IOException.class, () -> changed(n)); }
    private static CoreFrame.Partial core(int actor, int local, boolean paused, boolean alive) throws Exception {
        var p = frame(DRAFT).factsBefore().orElseThrow();
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(p.dateRaw(), p.speed(), paused, local, p.mapReady(), true, actor, alive));
    }
    private static CoreFrame.Partial originalRequestCore(ObjectNode n) throws IOException {
        var p = StrictJson.object(n.get("expected_core"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
                "has_played_character", "played_character_id", "played_character_alive"));
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(CurrentRiteCreate.i32(p.get("date_raw")), CurrentRiteCreate.i32(p.get("speed")),
                        CurrentRiteCreate.bool(p, "paused"), CurrentRiteCreate.i32(p.get("local_player_id")),
                        CurrentRiteCreate.bool(p, "map_ready"), CurrentRiteCreate.bool(p, "has_played_character"),
                        CurrentRiteCreate.i32(p.get("played_character_id")), CurrentRiteCreate.bool(p, "played_character_alive")));
    }

    private static void requestFactory(String name, CurrentRiteCreate.Action action) throws Exception {
        var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                "arguments", "rite_create", "core_control_deadline_unix_ms"));
        assertEquals("execute_step", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
        assertEquals(0, original.get("expected_revision").intValue()); assertEquals(MAX_U64, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        var claim = StrictJson.object(original.get("rite_create"), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "expected_core", "expected_source_rite_id", "provider_generation", "query_sequence"));
        assertEquals(action.wire(), claim.get("action").textValue());
        var request = CurrentRiteCreate.request(originalRequestCore(claim), action, CurrentRiteCreate.riteId(claim.get("expected_source_rite_id")),
                CurrentRiteCreate.decimal(claim, "provider_generation"), CurrentRiteCreate.decimal(claim, "query_sequence"));
        assertEquals(original.get("step").textValue(), request.step()); assertEquals(CurrentRiteCreate.STEP, request.step());
        assertEquals(CurrentRiteCreate.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "rite_create"));
        var generated = NativeWire.object(fields.get("rite_create")); assertEquals(10, generated.size());
        assertEquals(0, fields.get("arguments").size()); assertEquals(original.get("arguments"), fields.get("arguments"));
        assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),
                generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
        var comparable = generated.deepCopy(); comparable.set("executable_sha256", claim.get("executable_sha256")); assertEquals(claim, comparable);
        for (String key : List.of("request_id", "step", "core_control_deadline_unix_ms", "actor_id", "pointer", "key", "script", "ordinal"))
            assertFalse(generated.has(key), key);

        // Actual Java production packet encoder, original C++ requestID and deadline unchanged.
        fields.set("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms"));
        byte[] packet = NativeWire.execute(original.get("request_id").textValue(), request.step(), BigInteger.ZERO, StrictJson.canonical(fields));
        var decoded = NativeWire.decodeExecuteRequest(packet);
        assertEquals(original.get("request_id").textValue(), decoded.requestId()); assertEquals(request.step(), decoded.step());
        assertEquals(BigInteger.ZERO, decoded.expectedRevision().orElseThrow());
        int bytes = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt(); assertEquals(packet.length - 4, bytes);
        byte[] body = Arrays.copyOfRange(packet, 4, packet.length);
        var actualBody = StrictJson.object(NativeWire.parse(body), Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                "arguments", "rite_create", "core_control_deadline_unix_ms"));
        var expectedBody = original.deepCopy(); ((ObjectNode) expectedBody.get("rite_create")).set("executable_sha256", generated.get("executable_sha256"));
        assertEquals(expectedBody, actualBody); assertArrayEquals(packet, NativeWire.packet(body));
        String directory = System.getProperty("xar.rite.create.java.requests.output.directory");
        if (directory != null) {
            assertFalse(directory.isBlank(), "Explicit Java request output directory cannot be blank");
            Path output = Path.of(directory).toAbsolutePath(); Files.createDirectories(output);
            assertFalse(Files.isSymbolicLink(output), "Dedicated validation output directory required");
            Files.write(output.resolve("java-" + action.wire() + ".packet.bin"), packet, StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve("java-" + action.wire() + ".body.json"), body, StandardOpenOption.CREATE_NEW);
        }
    }

    @Test void fourteenActualCppResponsesRoundtripAndAllEighteenOriginalResourcesStayPinned() throws Exception {
        assertEquals(18, CPP.size()); int ok = 0, refused = 0;
        for (String name : RESPONSES) {
            var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            assertEquals("command_result", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
            var result = frame(name); assertEquals(result, CurrentRiteCreateResult.decode(result.encode()), name);
            assertEquals(original.get("ok").booleanValue(), result.successful(), name); assertEquals(24, NativeWire.parse(result.encode().bytes()).size());
            if (result.successful()) ok++; else refused++;
        }
        assertEquals(9, ok); assertEquals(5, refused);
        for (String name : List.of("request-query.json", "request-create.json", "request-query_confirmation.json", "request-accept_confirmation.json")) raw(name);
    }
    @Test void originalQueryRequestMatchesFactoryAndOptionalNativeValidationExport() throws Exception {
        requestFactory("request-query.json", CurrentRiteCreate.Action.QUERY);
    }
    @Test void originalCreateRequestMatchesFactoryAndOptionalNativeValidationExport() throws Exception {
        requestFactory("request-create.json", CurrentRiteCreate.Action.CREATE);
    }
    @Test void originalConfirmationQueryRequestMatchesFactoryAndOptionalNativeValidationExport() throws Exception {
        requestFactory("request-query_confirmation.json", CurrentRiteCreate.Action.QUERY_CONFIRMATION);
    }
    @Test void originalAcceptRequestMatchesFactoryAndOptionalNativeValidationExport() throws Exception {
        requestFactory("request-accept_confirmation.json", CurrentRiteCreate.Action.ACCEPT_CONFIRMATION);
    }

    @Test void falseNativeDataAndOneWayAdmissionAreRetainedWithoutInferringPermission() throws Exception {
        assertFalse(frame("draft-native-can-false.json").source().orElseThrow().draft().orElseThrow().nativeCanCreate());
        assertFalse(frame("draft-is-creating-false.json").source().orElseThrow().draft().orElseThrow().isCreating());
        assertFalse(frame("confirmation-native-can-false.json").source().orElseThrow().confirmation().orElseThrow().nativeCanAccept());
        for (String key : List.of("is_creating", "native_can_create", "known_dynastic", "selected_dynastic", "create_button_found",
                "create_button_visible", "create_button_enabled")) {
            var n = token(DRAFT); draft(n).put(key, false); draft(n).put("create_admissible", false);
            assertFalse(changed(n).source().orElseThrow().draft().orElseThrow().createAdmissible());
            draft(n).put("create_admissible", true); reject(n);
        }
        var blocked = token(DRAFT); draft(blocked).put("blocked_by_unrelated_modal", true); reject(blocked);
        var insufficient = token(DRAFT); draft(insufficient).put("piety_missing_raw", "1"); reject(insufficient);
        var nonAdmitted = token(DRAFT); draft(nonAdmitted).put("create_admissible", false);
        assertFalse(changed(nonAdmitted).source().orElseThrow().draft().orElseThrow().createAdmissible());
        var confirmationData = token(CONFIRMATION); confirmation(confirmationData).put("accept_admissible", false);
        assertFalse(changed(confirmationData).source().orElseThrow().confirmation().orElseThrow().acceptAdmissible());
        for (String key : List.of("native_can_accept", "accept_button_visible", "accept_button_enabled")) {
            var n = token(CONFIRMATION); confirmation(n).put(key, false); reject(n);
            confirmation(n).put("accept_admissible", false); assertTrue(changed(n).successful());
        }
    }

    @Test void sourceUnionSignedActorsAndUnsignedRiteIdsKeepExactActualIdentity() throws Exception {
        assertEquals(0, frame("draft-actor-zero.json").source().orElseThrow().actorId());
        assertEquals(0L, frame("draft-actor-zero.json").source().orElseThrow().sourceRiteId());
        assertEquals(-2, frame("draft-actor-minus-two.json").source().orElseThrow().actorId());
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var n = token(DRAFT); source(n).put("actor_id", actor); facts(n).put("played_character_id", actor);
            assertEquals(actor, changed(n).source().orElseThrow().actorId());
        }
        for (long id : new long[] {0, 0xffff_fffeL}) {
            var n = token(DRAFT); source(n).put("source_rite_id", id); assertEquals(id, changed(n).source().orElseThrow().sourceRiteId());
        }
        for (long id : new long[] {-1, 0xffff_ffffL, 0x1_0000_0000L}) {
            var n = token(DRAFT); source(n).put("source_rite_id", id); reject(n);
        }
        var wrongActor = token(DRAFT); source(wrongActor).put("actor_id", -1); reject(wrongActor);
        var drift = token(DRAFT); source(drift).put("actor_id", 0); reject(drift);
        var both = token(DRAFT); source(both).set("confirmation", source(token(CONFIRMATION)).get("confirmation")); reject(both);
        var neither = token(DRAFT); source(neither).putNull("draft"); reject(neither);
        var phase = token(DRAFT); source(phase).put("phase", "confirmation"); reject(phase);
        var missingModal = token(CONFIRMATION); confirmation(missingModal).put("modal_found", false); confirmation(missingModal).put("accept_admissible", false); reject(missingModal);
        var unbound = token(CONFIRMATION); confirmation(unbound).put("original_create_bound", false); confirmation(unbound).put("accept_admissible", false); reject(unbound);
    }

    @Test void voidDispatchesRetainTheirOwnImmutableBeforeSourceAndNeverClaimBusiness() throws Exception {
        for (String name : List.of("create-dispatched.json", "accept-dispatched.json")) {
            var result = frame(name); assertTrue(result.effectAttempted()); assertTrue(result.nativeReturned()); assertTrue(result.cleanupKnown());
            assertEquals(MAX_U64, result.providerGeneration()); assertEquals(MAX_U64, result.querySequence()); assertEquals(MAX_U64, result.claimSequence());
            assertFalse(result.nativeHandled()); assertFalse(result.riteCreated()); assertFalse(result.initialBindingConfirmed());
            assertFalse(result.newDateObserved()); assertFalse(result.physicalSaveConfirmed());
            for (String key : List.of("native_handled", "rite_created", "initial_binding_confirmed", "new_date_observed", "physical_save_confirmed")) {
                var n = token(name); n.put(key, true); reject(n);
            }
            var noSource = token(name); noSource.putNull("source"); noSource.put("source_available", false); reject(noSource);
            var noEntry = token(name); noEntry.put("effect_attempted", false); reject(noEntry);
            var unspent = token(name); unspent.put("claim_sequence", "0"); reject(unspent);
        }
        assertEquals(frame(DRAFT).source(), frame("create-dispatched.json").source());
        assertEquals(frame(CONFIRMATION).source(), frame("accept-dispatched.json").source());
        var wrongBefore = token("accept-dispatched.json"); wrongBefore.set("source", source(token(DRAFT))); reject(wrongBefore);
    }

    @Test void refusalPendingAndUnknownKeepOriginalLeaseClaimAndNullableSourceRoles() throws Exception {
        var pending = frame("confirmation-pending.json"); assertEquals(CurrentRiteCreateResult.Status.CONFIRMATION_PENDING, pending.status());
        assertEquals(MAX_U64, pending.providerGeneration()); assertEquals(MAX_U64, pending.querySequence());
        assertEquals(BigInteger.ZERO, pending.claimSequence()); assertTrue(pending.source().isEmpty()); assertFalse(pending.successful());
        var unknown = frame("cleanup-unknown.json"); assertEquals(CurrentRiteCreateResult.Status.INDETERMINATE, unknown.status());
        assertFalse(unknown.cleanupKnown()); assertTrue(unknown.effectAttempted()); assertTrue(unknown.nativeReturned());
        assertEquals(MAX_U64, unknown.claimSequence()); assertTrue(unknown.source().isEmpty());
        for (String name : List.of("unavailable.json", "expired.json", "stale-source.json", "confirmation-pending.json", "cleanup-unknown.json")) {
            var result = frame(name); assertFalse(result.successful()); assertFalse(result.unavailableReason().orElseThrow().isEmpty());
            var nullReason = token(name); nullReason.putNull("unavailable_reason"); reject(nullReason);
            var emptyReason = token(name); emptyReason.put("unavailable_reason", ""); reject(emptyReason);
        }
        var rewrittenUnknown = token("cleanup-unknown.json"); rewrittenUnknown.put("status", "expired"); reject(rewrittenUnknown);
        var leakedUnknown = token("cleanup-unknown.json"); leakedUnknown.set("source", source(token(DRAFT))); leakedUnknown.put("source_available", true); reject(leakedUnknown);
        var spentRefusal = token("expired.json"); spentRefusal.put("claim_sequence", MAX_U64.toString());
        assertEquals(MAX_U64, changed(spentRefusal).claimSequence()); // Explicit JavaDATA known zero-effect spentclaim is legal.
        var queryEffect = token(DRAFT); queryEffect.put("claim_sequence", "1"); reject(queryEffect);
    }

    @Test void resultSourceOwnerAndCoreRejectExtraMissingAndWrongNullableFields() throws Exception {
        var extra = token(DRAFT); extra.put("caller_scope", "actor"); reject(extra);
        var missing = token(DRAFT); missing.remove("native_handled"); reject(missing);
        var sourceExtra = token(DRAFT); source(sourceExtra).put("controller", "1"); reject(sourceExtra);
        var draftExtra = token(DRAFT); draft(draftExtra).put("formatted_piety", "123"); reject(draftExtra);
        var confirmExtra = token(CONFIRMATION); confirmation(confirmExtra).put("lease", "1"); reject(confirmExtra);
        var noFacts = token(DRAFT); noFacts.putNull("facts_before"); reject(noFacts);
        var noOwner = token(DRAFT); noOwner.putNull("owner"); reject(noOwner);
        var coreExtra = token(DRAFT); facts(coreExtra).put("Faith", 0); reject(coreExtra);
        var ownerExtra = token(DRAFT); owner(ownerExtra).put("pid", 1); reject(ownerExtra);
        var falseAvailability = token(DRAFT); falseAvailability.put("source_available", false); reject(falseAvailability);
        var reason = token(DRAFT); reason.put("unavailable_reason", "known-refusal"); reject(reason);
        for (String key : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action", "status")) {
            var n = token(DRAFT); n.put(key, "foreign"); reject(n);
        }
    }

    @Test void signedRawPietyAndAllUintWitnessesRejectCoercionAndPreservePrecision() throws Exception {
        for (long value : new long[] {Long.MIN_VALUE, -1, 0, Long.MAX_VALUE}) {
            var n = token(DRAFT); draft(n).put("create_admissible", false); draft(n).put("piety_cost_raw", Long.toString(value));
            draft(n).put("piety_missing_raw", Long.toString(value)); var d = changed(n).source().orElseThrow().draft().orElseThrow();
            assertEquals(value, d.pietyCostRaw()); assertEquals(value, d.pietyMissingRaw());
        }
        for (String field : List.of("piety_cost_raw", "piety_missing_raw")) {
            for (String value : List.of("-0", "+1", "01", "1.0", "9223372036854775808", "-9223372036854775809")) {
                var n = token(DRAFT); draft(n).put(field, value); reject(n);
            }
            var number = token(DRAFT); draft(number).put(field, 1); reject(number);
        }
        for (String field : List.of("provider_generation", "query_sequence", "claim_sequence")) {
            var overflow = token(DRAFT); overflow.put(field, "18446744073709551616"); reject(overflow);
            var leading = token(DRAFT); leading.put(field, "01"); reject(leading);
            var numeric = token(DRAFT); numeric.put(field, MAX_U64); reject(numeric);
        }
        for (String field : List.of("connection_generation", "ticket_sequence", "pump_epoch")) {
            var n = token(DRAFT); owner(n).put(field, "0"); reject(n);
        }
        var thread = token(DRAFT); owner(thread).put("thread_id", 0x1_0000_0000L); reject(thread);
        var floatingThread = token(DRAFT); owner(floatingThread).put("thread_id", 1.0); reject(floatingThread);
        var floatingActor = token(DRAFT); source(floatingActor).put("actor_id", 36423.0); reject(floatingActor);
        var floatingRite = token(DRAFT); source(floatingRite).put("source_rite_id", 47.0); reject(floatingRite);
    }

    @Test void requestRolesAndCoreConstructorsRejectInvalidInputsAtTheirActualBoundary() throws Exception {
        var actual = core(36423, 0, true, true);
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(actual, CurrentRiteCreate.Action.QUERY, 47, BigInteger.ONE, BigInteger.ONE));
        for (var action : List.of(CurrentRiteCreate.Action.CREATE, CurrentRiteCreate.Action.QUERY_CONFIRMATION, CurrentRiteCreate.Action.ACCEPT_CONFIRMATION)) {
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(actual, action, 47, BigInteger.ZERO, BigInteger.ZERO));
        }
        for (long id : new long[] {-1, 0xffff_ffffL, 0x1_0000_0000L})
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(actual, CurrentRiteCreate.Action.QUERY, id, BigInteger.ZERO, BigInteger.ZERO));
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE})
            assertEquals(CurrentRiteCreate.STEP, CurrentRiteCreate.request(core(actor, 0, true, true), CurrentRiteCreate.Action.QUERY, 0, BigInteger.ZERO, BigInteger.ZERO).step());
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(core(36423, -1, true, true), CurrentRiteCreate.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(core(36423, 0, false, true), CurrentRiteCreate.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreate.request(core(36423, 0, true, false), CurrentRiteCreate.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO));
        // Core Prefix itself rejects these values before a request/DTO can be invoked.
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 0, true, 0, true, true, 36423, true));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 2, true, 0, true, true, -1, true));
        assertThrows(IOException.class, () -> CurrentRiteCreate.Action.parse("confirm_edit"));
    }
}

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

/** Original C++ software DATA stays byteexact. All mutations below are explicitly Java DATA, never new Native frames. */
class NativeCurrentRiteCreationBlockers26785313ProducerTest {
    private record Artifact(String name, int bytes, String sha256) { }
    private static final List<Artifact> CPP = List.of(
        new Artifact("available-actor-negative-rite-max.json", 1358, "62a305b0df45a167c264de0b848dbbc80cc754c97a767a7c54cafb5242854477"),
        new Artifact("available-actor-zero-rite-zero.json", 1343, "dd6f46a11d13b0e8c052a94d66d4a9602a694764688a1d6fc4246b1bcbdea099"),
        new Artifact("available-false-can-empty.json", 1356, "119ee93242de31b5209ad0f6c7828d484342daca00ba57d40d174d3a32e63a86"),
        new Artifact("available-hidden-notcreating.json", 1351, "acac8724ff97346655a7fff7a7805b75a1ade73d6bdf8bdf0c10e4a1274c3383"),
        new Artifact("available-richtext-nul.json", 1387, "cb4a5af59580b8469fd26a96565dbd2d6ecc1d34473284ea5cbca74cfb765f19"),
        new Artifact("expired-before-source.json", 802, "6a0a6fca9dace98dfcf47539e69718ce1fe66e808b4f535ca4801df398062b92"),
        new Artifact("indeterminate-cleanup.json", 1109, "b2131f6f4ca442960e2404de475f394ae3617313578652f4e939ba9d07312883"),
        new Artifact("indeterminate-partial-samples.json", 1141, "e5aabdd211b819803e738fe7af8f98b97dd38a0bc0e7aedd75a0ebffd320b4a0"),
        new Artifact("request-query-blockers.json", 783, "7210a8fddcde66c1d3df92fdd1aa954336d420554b90f9b318a1fc6147cc1c23"),
        new Artifact("stale-core.json", 1109, "54c2e0b5913517e16ab326e6940f55a414ef54306bac1ae5b61ee3d2447741c5"),
        new Artifact("unavailable-definition.json", 1124, "b6b89b4ec8679ab8e5bca436c3c7cc4910d140f94db607a97c5c1ee87a9464f8")
    );
    private static final BigInteger MAX_U64 = new BigInteger("18446744073709551615");
    private static final String QUERY = "available-false-can-empty.json";
    private static final List<String> RESPONSES = List.of("available-actor-negative-rite-max.json", "available-actor-zero-rite-zero.json", "available-false-can-empty.json", "available-hidden-notcreating.json", "available-richtext-nul.json", "expired-before-source.json", "indeterminate-cleanup.json", "indeterminate-partial-samples.json", "stale-core.json", "unavailable-definition.json");
    private static byte[] raw(String name) throws Exception {
        var expected = CPP.stream().filter(a -> a.name().equals(name)).findFirst().orElseThrow();
        try (var in = NativeCurrentRiteCreationBlockers26785313ProducerTest.class.getResourceAsStream("/current267-rite-creation-blockers-cpp-a1021/" + name)) {
            if (in == null) throw new IOException("Original C++ blockers resource absent: " + name);
            byte[] bytes = in.readAllBytes(); assertEquals(expected.bytes(), bytes.length, name);
            assertEquals(expected.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name); return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception { return NativeWire.object(NativeWire.parse(raw(name))); }
    private static ObjectNode token(String name) throws Exception { return NativeWire.object(envelope(name).get("result")); }
    private static CurrentRiteCreationBlockersResult frame(String name) throws Exception {
        return CurrentRiteCreationBlockersResult.decode(new RawJson(NativeWire.token(raw(name), "result")));
    }
    private static CurrentRiteCreationBlockersResult changed(ObjectNode n) throws IOException {
        // Preserve integer versus floating JSON token kinds; canonicalization can normalize a1.0 DATA token.
        return CurrentRiteCreationBlockersResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode source(ObjectNode n) { return (ObjectNode) n.get("source"); }
    private static ObjectNode facts(ObjectNode n) { return (ObjectNode) n.get("facts_before"); }
    private static ObjectNode owner(ObjectNode n) { return (ObjectNode) n.get("owner"); }
    private static void reject(ObjectNode n) { assertThrows(IOException.class, () -> changed(n)); }
    private static CoreFrame.Partial core(int actor, int local, boolean paused, boolean alive) throws Exception {
        var p = frame(QUERY).factsBefore().orElseThrow();
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(p.dateRaw(), p.speed(), paused, local, p.mapReady(), true, actor, alive));
    }
    private static CoreFrame.Partial originalRequestCore(ObjectNode n) throws IOException {
        var p = StrictJson.object(n.get("expected_core"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready",
                "has_played_character", "played_character_id", "played_character_alive"));
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(CurrentRiteCreationBlockers.i32(p.get("date_raw")), CurrentRiteCreationBlockers.i32(p.get("speed")),
                        CurrentRiteCreationBlockers.bool(p, "paused"), CurrentRiteCreationBlockers.i32(p.get("local_player_id")),
                        CurrentRiteCreationBlockers.bool(p, "map_ready"), CurrentRiteCreationBlockers.bool(p, "has_played_character"),
                        CurrentRiteCreationBlockers.i32(p.get("played_character_id")), CurrentRiteCreationBlockers.bool(p, "played_character_alive")));
    }

    @Test void allTenActualCppResponsesRoundtripAndElevenOriginalResourcesStayPinned() throws Exception {
        assertEquals(11, CPP.size()); assertEquals(10, RESPONSES.size()); int available = 0;
        for (String name : RESPONSES) {
            var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            assertEquals("command_result", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
            var result = frame(name); assertEquals(result, CurrentRiteCreationBlockersResult.decode(result.encode()), name);
            assertEquals(original.get("ok").booleanValue(), result.successful(), name);
            assertEquals(22, NativeWire.parse(result.encode().bytes()).size());
            if (result.source().isPresent()) { available++; assertEquals(9, result.source().orElseThrow().encode().size()); }
        }
        assertEquals(5, available); raw("request-query-blockers.json");
    }

    @Test void originalFixedQueryFactoryMatchesOuter8Claim8AndExportsActualNativeWirePacketOptionally() throws Exception {
        var original = StrictJson.object(envelope("request-query-blockers.json"), Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                "arguments", "rite_creation_blockers", "core_control_deadline_unix_ms"));
        assertEquals("execute_step", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
        assertEquals(0, original.get("expected_revision").intValue()); assertEquals(MAX_U64, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        var claim = StrictJson.object(original.get("rite_creation_blockers"), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "expected_core", "expected_source_rite_id"));
        assertEquals("query_blockers", claim.get("action").textValue());
        var request = CurrentRiteCreationBlockers.request(originalRequestCore(claim), CurrentRiteCreationBlockers.riteId(claim.get("expected_source_rite_id")));
        assertEquals(CurrentRiteCreationBlockers.STEP, request.step()); assertEquals(original.get("step").textValue(), request.step());
        assertEquals(CurrentRiteCreationBlockers.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "rite_creation_blockers"));
        var generated = NativeWire.object(fields.get("rite_creation_blockers")); assertEquals(8, generated.size());
        assertEquals(0, fields.get("arguments").size()); assertEquals(original.get("arguments"), fields.get("arguments"));
        assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT), generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
        var comparable = generated.deepCopy(); comparable.set("executable_sha256", claim.get("executable_sha256")); assertEquals(claim, comparable);
        for (String key : List.of("request_id", "step", "core_control_deadline_unix_ms", "provider_generation", "query_sequence", "claim_sequence", "actor_id", "pointer", "text", "key", "script", "ordinal"))
            assertFalse(generated.has(key), key);
        fields.set("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms"));
        byte[] packet = NativeWire.execute(original.get("request_id").textValue(), request.step(), BigInteger.ZERO, StrictJson.canonical(fields));
        var decoded = NativeWire.decodeExecuteRequest(packet); assertEquals(original.get("request_id").textValue(), decoded.requestId());
        assertEquals(request.step(), decoded.step()); assertEquals(BigInteger.ZERO, decoded.expectedRevision().orElseThrow());
        int length = ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt(); assertEquals(packet.length - 4, length);
        byte[] body = Arrays.copyOfRange(packet, 4, packet.length); var expected = original.deepCopy();
        ((ObjectNode) expected.get("rite_creation_blockers")).set("executable_sha256", generated.get("executable_sha256"));
        assertEquals(expected, NativeWire.parse(body)); assertArrayEquals(packet, NativeWire.packet(body));
        String directory = System.getProperty("xar.rite.creation.blockers.java.requests.output.directory");
        if (directory != null) {
            assertFalse(directory.isBlank()); Path output = Path.of(directory).toAbsolutePath(); Files.createDirectories(output);
            assertFalse(Files.isSymbolicLink(output));
            Files.write(output.resolve("java-query.packet.bin"), packet, StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve("java-query.body.json"), body, StandardOpenOption.CREATE_NEW);
        }
    }

    @Test void allRepliesAreReadonlyAndInformationalSequencesCannotBecomeEffectClaims() throws Exception {
        for (String name : RESPONSES) {
            var actual = frame(name); assertEquals(BigInteger.ZERO, actual.claimSequence()); assertFalse(actual.effectAttempted());
            assertFalse(actual.nativeReturned()); assertFalse(actual.nativeHandled()); assertFalse(actual.newDateObserved()); assertFalse(actual.physicalSaveConfirmed());
            assertEquals(actual.sourceAvailable(), actual.successful());
            if (actual.sourceAvailable()) { assertEquals(MAX_U64, actual.providerGeneration()); assertEquals(MAX_U64, actual.querySequence()); }
            else { assertEquals(BigInteger.ZERO, actual.providerGeneration()); assertEquals(BigInteger.ZERO, actual.querySequence()); }
            for (String flag : List.of("effect_attempted", "native_returned", "native_handled", "new_date_observed", "physical_save_confirmed")) {
                var data = token(name); data.put(flag, true); reject(data);
            }
            var spent = token(name); spent.put("claim_sequence", "1"); reject(spent);
        }
        var madeLease = token("expired-before-source.json"); madeLease.put("provider_generation", "1"); reject(madeLease);
        var madeQuery = token("unavailable-definition.json"); madeQuery.put("query_sequence", "1"); reject(madeQuery);
    }

    @Test void falseCanEmptyReasonAndHiddenNotCreatingRemainCompleteActualData() throws Exception {
        var empty = frame(QUERY).source().orElseThrow(); assertFalse(empty.nativeCanCreate()); assertEquals("", empty.blockersText());
        var hidden = frame("available-hidden-notcreating.json").source().orElseThrow();
        assertFalse(hidden.isCreating()); assertFalse(hidden.windowVisible()); assertFalse(hidden.windowEnabled()); assertTrue(hidden.sampledTwice());
        for (String field : List.of("is_creating", "native_can_create", "window_visible", "window_enabled")) {
            var data = token(QUERY); source(data).put(field, false); assertTrue(changed(data).successful());
            source(data).put(field, true); assertTrue(changed(data).successful());
        }
        var partial = token(QUERY); source(partial).put("sampled_twice", false); reject(partial);
        var missing = token(QUERY); source(missing).remove("sampled_twice"); reject(missing);
        var noSource = token(QUERY); noSource.putNull("source"); noSource.put("source_available", false); reject(noSource);
    }

    @Test void sixteenKiBUtf8ReadBoundaryAndActualRichtextNulArePreservedWithoutTruncation() throws Exception {
        var original = frame("available-richtext-nul.json").source().orElseThrow();
        assertEquals(0, original.blockersText().charAt(1)); assertEquals(0x15, original.blockersText().charAt(3));
        assertTrue(original.blockersText().contains("#P detail#!\n\t"));
        assertEquals(original, CurrentRiteCreationBlockersSource.decode(original.encode()));
        String astral = new String(Character.toChars(0x1f600));
        for (String valid : List.of("", "a".repeat(16384), astral.repeat(4096), "\0\n\t" + String.valueOf((char) 0x7f))) {
            var data = token(QUERY); source(data).put("blockers_text", valid); var result = changed(data);
            assertEquals(valid, result.source().orElseThrow().blockersText()); assertEquals(result, CurrentRiteCreationBlockersResult.decode(result.encode()));
        }
        for (String invalid : List.of("a".repeat(16385), astral.repeat(4097))) {
            var data = token(QUERY); source(data).put("blockers_text", invalid); reject(data);
        }
        for (String invalid : List.of(String.valueOf((char) 0xd800), String.valueOf((char) 0xdc00)))
            assertThrows(IllegalArgumentException.class, () -> new CurrentRiteCreationBlockersSource(0, 0, false, false, invalid, false, false, true));
        var number = token(QUERY); source(number).put("blockers_text", 0); reject(number);
        var nullText = token(QUERY); source(nullText).putNull("blockers_text"); reject(nullText);
    }

    @Test void exactActorRiteAndCoreDomainsPreserveZeroAndNegativePackedActorButNotLocalPlayer() throws Exception {
        assertEquals(0, frame("available-actor-zero-rite-zero.json").source().orElseThrow().actorId());
        assertEquals(0L, frame("available-actor-zero-rite-zero.json").source().orElseThrow().sourceRiteId());
        assertEquals(-2, frame("available-actor-negative-rite-max.json").source().orElseThrow().actorId());
        assertEquals(0xffff_fffeL, frame("available-actor-negative-rite-max.json").source().orElseThrow().sourceRiteId());
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var data = token(QUERY); source(data).put("actor_id", actor); facts(data).put("played_character_id", actor);
            assertEquals(actor, changed(data).source().orElseThrow().actorId());
            assertEquals(CurrentRiteCreationBlockers.STEP, CurrentRiteCreationBlockers.request(core(actor, 0, true, true), 0).step());
        }
        for (long rite : new long[] {-1, 0xffff_ffffL, 0x1_0000_0000L}) {
            var data = token(QUERY); source(data).put("source_rite_id", rite); reject(data);
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreationBlockers.request(core(0, 0, true, true), rite));
        }
        var absent = token(QUERY); source(absent).put("actor_id", -1); reject(absent);
        var drift = token(QUERY); source(drift).put("actor_id", 0); reject(drift);
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreationBlockers.request(core(36423, -1, true, true), 47));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreationBlockers.request(core(36423, 0, false, true), 47));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteCreationBlockers.request(core(36423, 0, true, false), 47));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 0, true, 0, true, true, 36423, true));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 2, true, 0, true, true, -1, true));
    }

    @Test void nullableFactsOwnerAndExactResponseSourceShapeRejectInjectedAuthority() throws Exception {
        var noFacts = token(QUERY); noFacts.putNull("facts_before"); reject(noFacts);
        var noOwner = token(QUERY); noOwner.putNull("owner"); reject(noOwner);
        var zeroProvider = token(QUERY); zeroProvider.put("provider_generation", "0"); reject(zeroProvider);
        var zeroQuery = token(QUERY); zeroQuery.put("query_sequence", "0"); reject(zeroQuery);
        var sourceExtra = token(QUERY); source(sourceExtra).put("controller", "1"); reject(sourceExtra);
        var missing = token(QUERY); missing.remove("claim_sequence"); reject(missing);
        var capability = token(QUERY); capability.put("create_permission", true); reject(capability);
        var sourceAvailability = token(QUERY); sourceAvailability.put("source_available", false); reject(sourceAvailability);
        var wrongBool = token(QUERY); source(wrongBool).put("native_can_create", "false"); reject(wrongBool);
        var ownerExtra = token(QUERY); owner(ownerExtra).put("pid", 0); reject(ownerExtra);
        var coreExtra = token(QUERY); facts(coreExtra).put("faith_id", 0); reject(coreExtra);
        var leaked = token("expired-before-source.json"); leaked.set("source", source(token(QUERY))); leaked.put("source_available", true); reject(leaked);
    }

    @Test void allKnownRefusalsAndBothUnknownFormsRemainSourceNullWithOriginalNonemptyReason() throws Exception {
        for (String name : List.of("expired-before-source.json", "stale-core.json", "unavailable-definition.json", "indeterminate-cleanup.json", "indeterminate-partial-samples.json")) {
            var result = frame(name); assertFalse(result.successful()); assertTrue(result.source().isEmpty()); assertFalse(result.unavailableReason().orElseThrow().isEmpty());
            var missingReason = token(name); missingReason.putNull("unavailable_reason"); reject(missingReason);
            var emptyReason = token(name); emptyReason.put("unavailable_reason", ""); reject(emptyReason);
        }
        var cleanup = frame("indeterminate-cleanup.json"); assertEquals(CurrentRiteCreationBlockersResult.Status.INDETERMINATE, cleanup.status()); assertFalse(cleanup.cleanupKnown());
        var partial = frame("indeterminate-partial-samples.json"); assertEquals(CurrentRiteCreationBlockersResult.Status.INDETERMINATE, partial.status()); assertTrue(partial.cleanupKnown());
        var washed = token("indeterminate-cleanup.json"); washed.put("status", "expired"); reject(washed);
        var falseSuccessReason = token(QUERY); falseSuccessReason.put("unavailable_reason", "unknown"); reject(falseSuccessReason);
    }

    @Test void uint64InformationalSequencesAndWitnessesPreservePrecisionAndRejectNumericCoercion() throws Exception {
        assertEquals(MAX_U64, frame(QUERY).providerGeneration()); assertEquals(MAX_U64, frame(QUERY).querySequence());
        assertEquals(MAX_U64, frame(QUERY).owner().orElseThrow().connectionGeneration()); assertEquals(0xffff_ffffL, frame(QUERY).owner().orElseThrow().threadId());
        for (String field : List.of("provider_generation", "query_sequence", "claim_sequence")) {
            for (String invalid : List.of("18446744073709551616", "-1", "+1", "01", "1.0")) {
                var data = token(QUERY); data.put(field, invalid); reject(data);
            }
            var numeric = token(QUERY); numeric.put(field, MAX_U64); reject(numeric);
        }
        for (String field : List.of("connection_generation", "ticket_sequence", "pump_epoch")) {
            var zero = token(QUERY); owner(zero).put(field, "0"); reject(zero);
        }
        var overflow = token(QUERY); owner(overflow).put("thread_id", 0x1_0000_0000L); reject(overflow);
        var floatThread = token(QUERY); owner(floatThread).put("thread_id", 1.0); reject(floatThread);
        var floatActor = token(QUERY); source(floatActor).put("actor_id", 0.0); reject(floatActor);
        var floatRite = token(QUERY); source(floatRite).put("source_rite_id", 0.0); reject(floatRite);
    }

    @Test void fixedIdentityAndRawJsonDuplicateTrailingBoundariesFailBeforeAnyPermissionInference() throws Exception {
        for (String field : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action", "status")) {
            var foreign = token(QUERY); foreign.put(field, "foreign"); reject(foreign);
        }
        var addresses = token(QUERY); addresses.put("addresses_redacted", false); reject(addresses);
        var field = token(QUERY); field.put("native_returned", "false"); reject(field);
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{} {}".getBytes(StandardCharsets.UTF_8)));
    }
}

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

/** Exact original C++ software DATA. Mutations/exported requests never represent live effects or new C++ frames. */
class NativeCurrentRiteText26785313ProducerTest {
    private record Artifact(String name, int bytes, String sha256) { }
    private static final List<Artifact> CPP = List.of(
        new Artifact("claim-consumed.json", 856, "b386b5994f2d92e00f643c9e132ca9c30e58a2b7897bc1267617871905291dd8"),
        new Artifact("cleanup-unknown.json", 1218, "830ce10090ab961967649cbe1b7e09b91d387ea31f447395d72713cc016a6b8f"),
        new Artifact("description-dispatched.json", 1438, "2834efa0db962ca4a09d1763e1357be6c7ca635415123695c12f4471fff96360"),
        new Artifact("expired.json", 841, "01af65631bf12c3af0c1bfbcf4d3ebf397c6e3f387590d4553f404333b797562"),
        new Artifact("name-dispatched.json", 1424, "0823dc159697769e86aa6a9021502218146a22461757030049736d8a32c7faf9"),
        new Artifact("query-blocked.json", 1396, "c228335a99174ac185f21e0ed7cdeeebe9a466bd76cea5aaa58aac01a83c7446"),
        new Artifact("query-empty.json", 1361, "c051d5165ab234f760da3911927dc254c9406451b448130e6e811863ac6d0c3d"),
        new Artifact("query-not-creating.json", 1397, "2085e6d25c18476038d3c4cbac029a7a0f1c6c9f57120e77392307ac215dea1b"),
        new Artifact("query-read4096.json", 9556, "08958828d9e6100ab67da3aaa53da096b7a0be8ec574bad504386341ae14a3f4"),
        new Artifact("query-unicode.json", 1380, "3754859e9ccce4dc5f969d16230ab5de1ea1b1a7ad724ed9c975bb549013f627"),
        new Artifact("request-query.json", 780, "367af25791c1300a6de267363ef57c9a79f8672a93853eade80ee6e11ebf6bac"),
        new Artifact("request-set_description.json", 857, "754b842316eee66bcd175ed7492b0a9bbeabd8c17d621427a4ef1c5c4dbf2adb"),
        new Artifact("request-set_name.json", 831, "d4dd4357d24bd551dd9858c7a680232b70591f2d04a20dd20c4e2123758a1df9"),
        new Artifact("stale.json", 844, "e5ce5df12b47d8e96e1a68d433ceee755b252f8b76de35b5b57924cf21cd4a02"),
        new Artifact("unavailable.json", 849, "2c87a10af7c1565eda6a009b2cb279b459414d426c14d89f8fc7eb016f9a2b69")
    );
    private static final BigInteger MAX_U64 = new BigInteger("18446744073709551615");
    private static final String QUERY = "query-empty.json";
    private static final List<String> RESPONSES = List.of("claim-consumed.json", "cleanup-unknown.json", "description-dispatched.json", "expired.json", "name-dispatched.json", "query-blocked.json", "query-empty.json", "query-not-creating.json", "query-read4096.json", "query-unicode.json", "stale.json", "unavailable.json");
    private static byte[] raw(String name) throws Exception {
        var expected = CPP.stream().filter(a -> a.name().equals(name)).findFirst().orElseThrow();
        try (var in = NativeCurrentRiteText26785313ProducerTest.class.getResourceAsStream("/current267-rite-text-cpp-a01/" + name)) {
            if (in == null) throw new IOException("Original C++ Rite text resource absent: " + name);
            byte[] bytes = in.readAllBytes(); assertEquals(expected.bytes(), bytes.length, name);
            assertEquals(expected.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception { return NativeWire.object(NativeWire.parse(raw(name))); }
    private static ObjectNode token(String name) throws Exception { return NativeWire.object(envelope(name).get("result")); }
    private static CurrentRiteTextResult frame(String name) throws Exception {
        return CurrentRiteTextResult.decode(new RawJson(NativeWire.token(raw(name), "result")));
    }
    private static CurrentRiteTextResult changed(ObjectNode n) throws IOException {
        // Preserve integer versus floating JSON token kinds; canonicalization can normalize a1.0 DATA token.
        return CurrentRiteTextResult.decode(new RawJson(n.toString().getBytes(StandardCharsets.UTF_8)));
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
                new CoreFrame.Prefix(CurrentRiteText.i32(p.get("date_raw")), CurrentRiteText.i32(p.get("speed")),
                        CurrentRiteText.bool(p, "paused"), CurrentRiteText.i32(p.get("local_player_id")),
                        CurrentRiteText.bool(p, "map_ready"), CurrentRiteText.bool(p, "has_played_character"),
                        CurrentRiteText.i32(p.get("played_character_id")), CurrentRiteText.bool(p, "played_character_alive")));
    }

    private static void requestFactory(String name, CurrentRiteText.Action action) throws Exception {
        var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "step", "expected_revision",
                "arguments", "rite_text", "core_control_deadline_unix_ms"));
        assertEquals("execute_step", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
        assertEquals(0, original.get("expected_revision").intValue()); assertEquals(MAX_U64, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        var claim = StrictJson.object(original.get("rite_text"), Set.of("schema", "game_version", "executable_sha256", "adapter_id",
                "backend", "action", "expected_core", "expected_source_rite_id", "provider_generation", "query_sequence", "text"));
        assertEquals(action.wire(), claim.get("action").textValue());
        var request = CurrentRiteText.request(originalRequestCore(claim), action, CurrentRiteText.riteId(claim.get("expected_source_rite_id")),
                CurrentRiteText.decimal(claim, "provider_generation"), CurrentRiteText.decimal(claim, "query_sequence"), CurrentRiteText.actualText(claim.get("text")));
        assertEquals(original.get("step").textValue(), request.step()); assertEquals(CurrentRiteText.STEP, request.step());
        assertEquals(CurrentRiteText.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "rite_text"));
        var generated = NativeWire.object(fields.get("rite_text")); assertEquals(11, generated.size());
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
                "arguments", "rite_text", "core_control_deadline_unix_ms"));
        var expectedBody = original.deepCopy(); ((ObjectNode) expectedBody.get("rite_text")).set("executable_sha256", generated.get("executable_sha256"));
        assertEquals(expectedBody, actualBody); assertArrayEquals(packet, NativeWire.packet(body));
        String directory = System.getProperty("xar.rite.text.java.requests.output.directory");
        if (directory != null) {
            assertFalse(directory.isBlank(), "Explicit Java request output directory cannot be blank");
            Path output = Path.of(directory).toAbsolutePath(); Files.createDirectories(output);
            assertFalse(Files.isSymbolicLink(output), "Dedicated validation output directory required");
            Files.write(output.resolve("java-" + action.wire() + ".packet.bin"), packet, StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve("java-" + action.wire() + ".body.json"), body, StandardOpenOption.CREATE_NEW);
        }
    }

    @Test void allTwelveOriginalCppResponsesRoundtripAndAllFifteenResourcesStayPinned() throws Exception {
        assertEquals(15, CPP.size()); assertEquals(12, RESPONSES.size()); int ok = 0;
        for (String name : RESPONSES) {
            var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            assertEquals("command_result", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
            var result = frame(name); assertEquals(result, CurrentRiteTextResult.decode(result.encode()), name);
            assertEquals(original.get("ok").booleanValue(), result.successful(), name);
            assertEquals(23, NativeWire.parse(result.encode().bytes()).size());
            if (result.source().isPresent()) assertEquals(10, result.source().orElseThrow().encode().size());
            if (result.successful()) ok++;
        }
        assertEquals(7, ok);
        for (String name : List.of("request-query.json", "request-set_name.json", "request-set_description.json")) raw(name);
    }
    @Test void originalQueryMatchesTypedFactoryAndOptionalNativeRequestExport() throws Exception {
        requestFactory("request-query.json", CurrentRiteText.Action.QUERY);
    }
    @Test void originalNameMatchesTypedFactoryAndOptionalNativeRequestExport() throws Exception {
        requestFactory("request-set_name.json", CurrentRiteText.Action.SET_NAME);
    }
    @Test void originalDescriptionMatchesTypedFactoryAndOptionalNativeRequestExport() throws Exception {
        requestFactory("request-set_description.json", CurrentRiteText.Action.SET_DESCRIPTION);
    }

    @Test void writeLimitsCountUnicodeScalarsAndUtf8AndPermitActualEmptyClearOnly() throws Exception {
        var name = CurrentRiteText.Action.SET_NAME; var description = CurrentRiteText.Action.SET_DESCRIPTION;
        String astral = new String(Character.toChars(0x1f600));
        assertEquals(120, astral.repeat(30).getBytes(StandardCharsets.UTF_8).length);
        assertEquals(1600, astral.repeat(400).getBytes(StandardCharsets.UTF_8).length);
        assertDoesNotThrow(() -> CurrentRiteText.requireText(name, astral.repeat(30)));
        assertDoesNotThrow(() -> CurrentRiteText.requireText(description, astral.repeat(400)));
        assertDoesNotThrow(() -> CurrentRiteText.requireText(name, ""));
        assertDoesNotThrow(() -> CurrentRiteText.requireText(description, ""));
        for (String tooLong : List.of("a".repeat(31), astral.repeat(31)))
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(name, tooLong));
        for (String tooLong : List.of("a".repeat(401), astral.repeat(401)))
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(description, tooLong));
        for (int cp = 0; cp <= 0x1f; cp++) {
            String control = String.valueOf((char) cp);
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(name, "a" + control));
            if (cp == 9 || cp == 10) assertDoesNotThrow(() -> CurrentRiteText.requireText(description, "a" + control));
            else assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(description, "a" + control));
        }
        for (var action : List.of(name, description)) {
            for (String invalid : List.of(String.valueOf((char) 0x7f), String.valueOf((char) 0xd800), String.valueOf((char) 0xdc00)))
                assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(action, invalid));
        }
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(CurrentRiteText.Action.QUERY, "x"));
        var actual = core(36423, 0, true, true);
        for (var action : List.of(name, description)) {
            var empty = CurrentRiteText.request(actual, action, 47, MAX_U64, MAX_U64, "");
            assertEquals("", NativeWire.parse(empty.additionalFields().bytes()).get("rite_text").get("text").textValue());
        }
    }

    @Test void actualReadTextPreserves4096BytesRichtextControlsAndEmbeddedNulWithoutWriteLimits() throws Exception {
        var actual = frame("query-read4096.json").source().orElseThrow();
        assertEquals(4096, actual.name().getBytes(StandardCharsets.UTF_8).length);
        assertEquals(4096, actual.description().getBytes(StandardCharsets.UTF_8).length);
        String special = String.valueOf((char) 0x15) + "rich" + String.valueOf((char) 0) + "\n\t" + String.valueOf((char) 0x7f);
        var data = token(QUERY); source(data).put("name", special); source(data).put("description", special);
        var retained = changed(data); assertEquals(special, retained.source().orElseThrow().name());
        assertEquals(retained, CurrentRiteTextResult.decode(retained.encode()));
        for (String field : List.of("name", "description")) {
            var oversized = token(QUERY); source(oversized).put(field, "x".repeat(4097)); reject(oversized);
            var nullText = token(QUERY); source(nullText).putNull(field); reject(nullText);
            var numeric = token(QUERY); source(numeric).put(field, 0); reject(numeric);
        }
        for (String invalid : List.of(String.valueOf((char) 0xd800), String.valueOf((char) 0xdc00)))
            assertThrows(IllegalArgumentException.class, () -> new CurrentRiteTextSource(0, 0, true, invalid, "", true, true, false, true));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(CurrentRiteText.Action.SET_NAME, actual.name()));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.requireText(CurrentRiteText.Action.SET_DESCRIPTION, actual.description()));
    }

    @Test void falseCreatingHiddenDisabledAndBlockedAreActualDataNotDerivedWritePermission() throws Exception {
        assertFalse(frame("query-not-creating.json").source().orElseThrow().isCreating());
        assertEquals(-2, frame("query-not-creating.json").source().orElseThrow().actorId());
        assertTrue(frame("query-blocked.json").source().orElseThrow().blockedByUnrelatedModal());
        assertFalse(frame("query-blocked.json").source().orElseThrow().writeAdmissible());
        for (String gate : List.of("is_creating", "window_visible", "window_enabled")) {
            var value = token(QUERY); source(value).put(gate, false); source(value).put("write_admissible", false);
            assertTrue(changed(value).successful()); source(value).put("write_admissible", true); reject(value);
        }
        var blocked = token(QUERY); source(blocked).put("blocked_by_unrelated_modal", true); reject(blocked);
        var allowedButNotAdmitted = token(QUERY); source(allowedButNotAdmitted).put("write_admissible", false);
        assertFalse(changed(allowedButNotAdmitted).source().orElseThrow().writeAdmissible());
    }

    @Test void actorAndRiteZeroAndFullSignedActorDataNeverChangeLocalPlayerQualification() throws Exception {
        var zero = frame("query-unicode.json").source().orElseThrow(); assertEquals(0, zero.actorId()); assertEquals(0L, zero.sourceRiteId());
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var data = token(QUERY); source(data).put("actor_id", actor); facts(data).put("played_character_id", actor);
            assertEquals(actor, changed(data).source().orElseThrow().actorId());
            assertEquals(CurrentRiteText.STEP, CurrentRiteText.request(core(actor, 0, true, true), CurrentRiteText.Action.QUERY, 0,
                    BigInteger.ZERO, BigInteger.ZERO, "").step());
        }
        for (long rite : new long[] {0, 0xffff_fffeL}) {
            var data = token(QUERY); source(data).put("source_rite_id", rite); assertEquals(rite, changed(data).source().orElseThrow().sourceRiteId());
        }
        for (long rite : new long[] {-1, 0xffff_ffffL, 0x1_0000_0000L}) {
            var data = token(QUERY); source(data).put("source_rite_id", rite); reject(data);
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(core(0, 0, true, true), CurrentRiteText.Action.QUERY,
                    rite, BigInteger.ZERO, BigInteger.ZERO, ""));
        }
        var absent = token(QUERY); source(absent).put("actor_id", -1); reject(absent);
        var drift = token(QUERY); source(drift).put("actor_id", 0); reject(drift);
        var actual = core(36423, 0, true, true);
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(actual, CurrentRiteText.Action.QUERY, 47, BigInteger.ONE, BigInteger.ONE, ""));
        for (var action : List.of(CurrentRiteText.Action.SET_NAME, CurrentRiteText.Action.SET_DESCRIPTION))
            assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(actual, action, 47, BigInteger.ZERO, BigInteger.ZERO, ""));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(core(36423, -1, true, true), CurrentRiteText.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO, ""));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(core(36423, 0, false, true), CurrentRiteText.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO, ""));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(core(36423, 0, true, false), CurrentRiteText.Action.QUERY, 47, BigInteger.ZERO, BigInteger.ZERO, ""));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 0, true, 0, true, true, 36423, true));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 2, true, 0, true, true, -1, true));
    }

    @Test void voidWritesRetainImmutableBeforeSourceWithoutClaimingTextAppliedOrReadback() throws Exception {
        for (String name : List.of("name-dispatched.json", "description-dispatched.json")) {
            var r = frame(name); assertEquals(CurrentRiteTextResult.Status.TEXT_DISPATCHED, r.status());
            assertTrue(r.effectAttempted()); assertTrue(r.nativeReturned()); assertTrue(r.cleanupKnown());
            assertEquals(MAX_U64, r.providerGeneration()); assertEquals(MAX_U64, r.querySequence()); assertEquals(MAX_U64, r.claimSequence());
            assertEquals("Original name", r.source().orElseThrow().name()); assertEquals("Original description", r.source().orElseThrow().description());
            assertFalse(r.nativeHandled()); assertFalse(r.textApplied()); assertFalse(r.newDateObserved()); assertFalse(r.physicalSaveConfirmed());
            for (String field : List.of("native_handled", "text_applied", "new_date_observed", "physical_save_confirmed")) {
                var data = token(name); data.put(field, true); reject(data);
            }
            var noSource = token(name); noSource.putNull("source"); noSource.put("source_available", false); reject(noSource);
            var noEntry = token(name); noEntry.put("effect_attempted", false); reject(noEntry);
            var notReturned = token(name); notReturned.put("native_returned", false); reject(notReturned);
            var unspent = token(name); unspent.put("claim_sequence", "0"); reject(unspent);
            var nonAdmitted = token(name); source(nonAdmitted).put("write_admissible", false); reject(nonAdmitted);
            var queryAction = token(name); queryAction.put("action", "query"); reject(queryAction);
        }
        assertEquals(frame("name-dispatched.json").source(), frame("description-dispatched.json").source());
        assertNotEquals(envelope("request-set_name.json").get("rite_text").get("text").textValue(), frame("name-dispatched.json").source().orElseThrow().name());
    }

    @Test void refusalsAndUnknownKeepSpentClaimsNullableRolesAndStickyUnknown() throws Exception {
        var consumed = frame("claim-consumed.json"); assertEquals(BigInteger.valueOf(17), consumed.claimSequence());
        assertFalse(consumed.effectAttempted()); assertFalse(consumed.nativeReturned()); assertTrue(consumed.source().isEmpty());
        var unknown = frame("cleanup-unknown.json"); assertEquals(CurrentRiteTextResult.Status.INDETERMINATE, unknown.status());
        assertFalse(unknown.cleanupKnown()); assertTrue(unknown.effectAttempted()); assertTrue(unknown.nativeReturned());
        assertEquals(MAX_U64, unknown.claimSequence()); assertTrue(unknown.source().isEmpty());
        for (String name : List.of("unavailable.json", "expired.json", "stale.json", "claim-consumed.json", "cleanup-unknown.json")) {
            assertFalse(frame(name).successful()); assertFalse(frame(name).unavailableReason().orElseThrow().isEmpty());
            var nullReason = token(name); nullReason.putNull("unavailable_reason"); reject(nullReason);
            var emptyReason = token(name); emptyReason.put("unavailable_reason", ""); reject(emptyReason);
            var leaked = token(name); leaked.set("source", source(token(QUERY))); leaked.put("source_available", true); reject(leaked);
        }
        var rewrittenUnknown = token("cleanup-unknown.json"); rewrittenUnknown.put("status", "unavailable"); reject(rewrittenUnknown);
        var queryClaim = token(QUERY); queryClaim.put("claim_sequence", "1"); reject(queryClaim);
        var queryEntry = token(QUERY); queryEntry.put("effect_attempted", true); reject(queryEntry);
        assertTrue(frame("unavailable.json").factsBefore().isEmpty()); assertTrue(frame("unavailable.json").owner().isEmpty());
    }

    @Test void exactShapesIdentityAndActualRawJsonBoundaryRejectInjectedOrTrailingData() throws Exception {
        var extra = token(QUERY); extra.put("caller_key", "faith_name_edit"); reject(extra);
        var missing = token(QUERY); missing.remove("native_handled"); reject(missing);
        var sourceExtra = token(QUERY); source(sourceExtra).put("controller", "1"); reject(sourceExtra);
        var sourceMissing = token(QUERY); source(sourceMissing).remove("name"); reject(sourceMissing);
        var nullable = token(QUERY); nullable.putNull("source"); reject(nullable);
        var noFacts = token(QUERY); noFacts.putNull("facts_before"); reject(noFacts);
        var noOwner = token(QUERY); noOwner.putNull("owner"); reject(noOwner);
        var falseAvailability = token(QUERY); falseAvailability.put("source_available", false); reject(falseAvailability);
        var coreExtra = token(QUERY); facts(coreExtra).put("faith_id", 0); reject(coreExtra);
        var ownerExtra = token(QUERY); owner(ownerExtra).put("pid", 0); reject(ownerExtra);
        var successReason = token(QUERY); successReason.put("unavailable_reason", "failure"); reject(successReason);
        var stringBool = token(QUERY); source(stringBool).put("write_admissible", "true"); reject(stringBool);
        for (String field : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action", "status")) {
            var foreign = token(QUERY); foreign.put(field, "foreign"); reject(foreign);
        }
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IOException.class, () -> CurrentRiteText.Action.parse("set_adjective"));
    }

    @Test void uint64WitnessPrecisionAndIntegerKindsRejectCoercionAtActualBoundary() throws Exception {
        for (String field : List.of("provider_generation", "query_sequence", "claim_sequence")) {
            for (String bad : List.of("18446744073709551616", "-1", "+1", "01", "1.0")) {
                var data = token(QUERY); data.put(field, bad); reject(data);
            }
            var numeric = token(QUERY); numeric.put(field, MAX_U64); reject(numeric);
        }
        for (String field : List.of("connection_generation", "ticket_sequence", "pump_epoch")) {
            var zero = token(QUERY); owner(zero).put(field, "0"); reject(zero);
        }
        var threadOverflow = token(QUERY); owner(threadOverflow).put("thread_id", 0x1_0000_0000L); reject(threadOverflow);
        var floatThread = token(QUERY); owner(floatThread).put("thread_id", 1.0); reject(floatThread);
        var floatActor = token(QUERY); source(floatActor).put("actor_id", 0.0); reject(floatActor);
        var floatRite = token(QUERY); source(floatRite).put("source_rite_id", 0.0); reject(floatRite);
        var actual = core(36423, 0, true, true);
        var overflow = MAX_U64.add(BigInteger.ONE);
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(actual, CurrentRiteText.Action.SET_NAME, 47, overflow, MAX_U64, "x"));
        assertThrows(IllegalArgumentException.class, () -> CurrentRiteText.request(actual, CurrentRiteText.Action.SET_NAME, 47, MAX_U64, BigInteger.valueOf(-1), "x"));
        assertEquals(MAX_U64, frame(QUERY).owner().orElseThrow().connectionGeneration());
        assertEquals(0xffff_ffffL, frame(QUERY).owner().orElseThrow().threadId());
    }
}

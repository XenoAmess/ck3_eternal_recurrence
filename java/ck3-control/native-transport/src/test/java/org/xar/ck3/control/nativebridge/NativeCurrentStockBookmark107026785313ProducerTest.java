package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ArrayNode;
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
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Original C++ software DATA is byteexact; in-memory mutations are Java negative DATA, not new Native frames. */
class NativeCurrentStockBookmark107026785313ProducerTest {
    private record Artifact(String name, int bytes, String sha256) { }
    private static final List<Artifact> CPP = List.of(
        new Artifact("available-empty.json", 1347, "9da94f218f9ba2e348ca90d95e1e42d07494fb8fb431782938cbad93fd71be4a"),
        new Artifact("available-multiple.json", 2865, "34cab99f8e622ee1a2745875fabebb756ea81ec425d584a660619b8386c5b9b2"),
        new Artifact("available-native-can-false.json", 2106, "8d4f7d0825e9c83787aeb00978e42ea01482cd15c96909cd845dbafdb13c24c8"),
        new Artifact("available-original.json", 2109, "543b011d7c8558cecd702b262ecb365f0ad80e9d69eb7036a957ac6b77227cc0"),
        new Artifact("available-wrong-definition.json", 2109, "c69edf1eefebc93b6b695182eea9dbb7d5bdabf80faf025c575786e77eb5a653"),
        new Artifact("expired.json", 827, "b575a5d02fa5df3db14e9ad377e4f7a5a3304ffe9312bab7213d4c39f173e376"),
        new Artifact("indeterminate-cleanup.json", 1169, "3081cb9b2a2cbc209a40a0b9a5a5a5cb0d936816b39f0d71f19fa34d80cfc1b7"),
        new Artifact("indeterminate-incomplete.json", 1210, "5bdc480eec7a407f2bb547eca391ab4be4ffa808122cb5455160274e33ead4df"),
        new Artifact("request-query.json", 791, "cac49e175a56be12be8dcc2de8e8d1b003bf745c2a734176d3b8b2120aff4f09"),
        new Artifact("request-select-c.json", 833, "4d682671e2064f4da898b44500bef6eb3c0a2bf131e926b2c9ea6978619e7250"),
        new Artifact("selection-c-dispatched.json", 2119, "07849355223713b1f4c740b6d104053ecf5e20eb2e864cdfc1c8db95b75cbf61"),
        new Artifact("stale-with-original-source.json", 2121, "8f97561eead2b65209204d48d0d728d9a33b391c7d8995a8209a14677ff048a9")
    );
    private static final List<String> RESPONSES = List.of("available-empty.json", "available-multiple.json",
            "available-native-can-false.json", "available-original.json", "available-wrong-definition.json", "expired.json",
            "indeterminate-cleanup.json", "indeterminate-incomplete.json", "selection-c-dispatched.json", "stale-with-original-source.json");
    private static final BigInteger MAX = new BigInteger("18446744073709551615");
    private static final String QUERY = "available-original.json";
    private static byte[] raw(String name) throws Exception {
        var expected = CPP.stream().filter(a -> a.name().equals(name)).findFirst().orElseThrow();
        try (var in = NativeCurrentStockBookmark107026785313ProducerTest.class.getResourceAsStream("/current267-stock-bookmark1070-cpp-a1070/" + name)) {
            if (in == null) throw new IOException("Original C++ bookmark1070 resource absent: " + name);
            byte[] bytes = in.readAllBytes(); assertEquals(expected.bytes(), bytes.length, name);
            assertEquals(expected.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name); return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception { return NativeWire.object(NativeWire.parse(raw(name))); }
    private static ObjectNode token(String name) throws Exception { return NativeWire.object(envelope(name).get("result")); }
    private static CurrentStockBookmark1070Result frame(String name) throws Exception {
        return CurrentStockBookmark1070Result.decode(new RawJson(NativeWire.token(raw(name), "result")));
    }
    private static CurrentStockBookmark1070Result changed(ObjectNode data) throws IOException {
        // Preserve integer/float token kinds: canonical JSON could normalize the negative DATA token1.0.
        return CurrentStockBookmark1070Result.decode(new RawJson(data.toString().getBytes(StandardCharsets.UTF_8)));
    }
    private static ObjectNode source(ObjectNode n) { return (ObjectNode) n.get("source"); }
    private static ObjectNode census(ObjectNode n) { return (ObjectNode) source(n).get("event_census"); }
    private static ObjectNode row(ObjectNode n) { return (ObjectNode) census(n).get("events").get(0); }
    private static ArrayNode options(ObjectNode n) { return (ArrayNode) row(n).get("options"); }
    private static ObjectNode facts(ObjectNode n) { return (ObjectNode) n.get("facts_before"); }
    private static ObjectNode owner(ObjectNode n) { return (ObjectNode) n.get("owner"); }
    private static ObjectNode c(ObjectNode n) {
        for (var o : options(n)) if (o.get("authored_option_index").intValue() == 2) return (ObjectNode) o;
        throw new IllegalArgumentException("Test requires original authoredC DATA");
    }
    private static void reject(ObjectNode data) { assertThrows(IOException.class, () -> changed(data)); }
    private static CoreFrame.Partial core(int actor, int local, boolean paused, boolean alive) throws Exception {
        var p = frame(QUERY).factsBefore().orElseThrow();
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(p.dateRaw(), p.speed(), paused, local, p.mapReady(), true, actor, alive));
    }
    private static CoreFrame.Partial requestCore(ObjectNode claim) throws IOException {
        var p = StrictJson.object(claim.get("expected_core"), Set.of("date_raw", "speed", "paused", "local_player_id", "map_ready", "has_played_character", "played_character_id", "played_character_alive"));
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(CurrentStockBookmark1070.i32(p.get("date_raw")), CurrentStockBookmark1070.i32(p.get("speed")),
                        CurrentStockBookmark1070.bool(p, "paused"), CurrentStockBookmark1070.i32(p.get("local_player_id")), CurrentStockBookmark1070.bool(p, "map_ready"),
                        CurrentStockBookmark1070.bool(p, "has_played_character"), CurrentStockBookmark1070.i32(p.get("played_character_id")), CurrentStockBookmark1070.bool(p, "played_character_alive")));
    }

    @Test void allTwelveOriginalResourcesStayPinnedAndTenActualResponsesRoundtrip() throws Exception {
        assertEquals(12, CPP.size()); assertEquals(10, RESPONSES.size()); int sources = 0;
        for (var artifact : CPP) raw(artifact.name());
        for (String name : RESPONSES) {
            var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            assertEquals("command_result", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
            var actual = frame(name); assertEquals(actual, CurrentStockBookmark1070Result.decode(actual.encode()), name);
            assertEquals(original.get("ok").booleanValue(), actual.successful(), name); assertEquals(24, NativeWire.parse(actual.encode().bytes()).size());
            if (actual.source().isPresent()) {
                sources++; var s = actual.source().orElseThrow(); assertEquals(5, s.encode().size());
                assertEquals(s, CurrentStockBookmark1070Source.decode(s.encode()));
                assertEquals(3, s.encode().get("event_census").size());
                for (var e : s.encode().get("event_census").get("events")) { assertEquals(10, e.size()); for (var o : e.get("options")) assertEquals(6, o.size()); }
            }
        }
        assertEquals(7, sources);
    }

    private static void compareFactory(String name, CurrentStockBookmark1070.Action action, String outputStem) throws Exception {
        var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "step", "expected_revision", "arguments", "stock_bookmark1070", "core_control_deadline_unix_ms"));
        assertEquals("execute_step", original.get("type").textValue()); assertEquals(1, original.get("protocol_version").intValue());
        assertEquals(0, original.get("expected_revision").intValue()); assertEquals(MAX, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        var claim = StrictJson.object(original.get("stock_bookmark1070"), Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action", "expected_core", "provider_generation", "query_sequence", "instance_id"));
        assertEquals(action.wire(), claim.get("action").textValue());
        var instance = claim.get("instance_id").isNull() ? Optional.<Integer>empty() : Optional.of(CurrentStockBookmark1070.i32(claim.get("instance_id")));
        var request = CurrentStockBookmark1070.request(requestCore(claim), action, claim.get("provider_generation").bigIntegerValue(), claim.get("query_sequence").bigIntegerValue(), instance);
        assertEquals(action.step(), request.step()); assertEquals(original.get("step").textValue(), request.step()); assertEquals(action.capability(), request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "stock_bookmark1070"));
        var generated = NativeWire.object(fields.get("stock_bookmark1070")); assertEquals(10, generated.size());
        assertTrue(generated.get("provider_generation").isIntegralNumber()); assertTrue(generated.get("query_sequence").isIntegralNumber());
        assertEquals(0, fields.get("arguments").size()); assertEquals(original.get("arguments"), fields.get("arguments"));
        var comparable = generated.deepCopy();
        assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT), generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
        comparable.set("executable_sha256", claim.get("executable_sha256")); assertEquals(claim, comparable);
        for (String key : List.of("request_id", "step", "core_control_deadline_unix_ms", "event_key", "option_key", "option_index", "index", "native_can_select", "choice_token", "role", "pointer")) assertFalse(generated.has(key), key);
        fields.set("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms"));
        byte[] packet = NativeWire.execute(original.get("request_id").textValue(), request.step(), BigInteger.ZERO, StrictJson.canonical(fields));
        var decoded = NativeWire.decodeExecuteRequest(packet); assertEquals(original.get("request_id").textValue(), decoded.requestId());
        assertEquals(request.step(), decoded.step()); assertEquals(BigInteger.ZERO, decoded.expectedRevision().orElseThrow());
        assertEquals(packet.length - 4, ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        byte[] body = Arrays.copyOfRange(packet, 4, packet.length); var expected = original.deepCopy();
        ((ObjectNode) expected.get("stock_bookmark1070")).set("executable_sha256", generated.get("executable_sha256"));
        assertEquals(expected, NativeWire.parse(body)); assertArrayEquals(packet, NativeWire.packet(body));
        String directory = System.getProperty("xar.stock.bookmark1070.java.requests.output.directory");
        if (directory != null) {
            assertFalse(directory.isBlank()); Path output = Path.of(directory).toAbsolutePath(); Files.createDirectories(output); assertFalse(Files.isSymbolicLink(output));
            Files.write(output.resolve("java-" + outputStem + ".packet.bin"), packet, StandardOpenOption.CREATE_NEW);
            Files.write(output.resolve("java-" + outputStem + ".body.json"), body, StandardOpenOption.CREATE_NEW);
        }
    }
    @Test void originalQueryFactoryMatchesOuter8Claim10AndExportsActualPacket() throws Exception { compareFactory("request-query.json", CurrentStockBookmark1070.Action.QUERY, "query"); }
    @Test void originalSelectCFactoryMatchesOuter8Claim10AndExportsActualPacket() throws Exception { compareFactory("request-select-c.json", CurrentStockBookmark1070.Action.SELECT_C, "select-c"); }

    @Test void completeAbsentForeignMultipleAndFalseCanCensusesRemainQueryData() throws Exception {
        for (String name : List.of("available-empty.json", "available-multiple.json", "available-wrong-definition.json", "available-native-can-false.json")) {
            var result = frame(name); assertTrue(result.successful()); assertFalse(result.source().orElseThrow().selectCAdmissible());
            assertFalse(result.effectAttempted()); assertEquals(BigInteger.ZERO, result.claimSequence()); assertTrue(result.instanceId().isEmpty());
        }
        assertEquals(0, frame("available-empty.json").source().orElseThrow().eventCensus().events().size());
        assertEquals(2, frame("available-multiple.json").source().orElseThrow().eventCensus().events().size());
        assertEquals(Optional.of(1), frame("available-native-can-false.json").source().orElseThrow().fixedInstanceId());
        assertTrue(frame("available-wrong-definition.json").source().orElseThrow().fixedInstanceId().isEmpty());
        var negative = token(QUERY); source(negative).put("select_c_admissible", false); assertTrue(changed(negative).successful());
    }

    @Test void authoredCUsesItsRealIndexWithoutRequiringOtherOptionsCanTrue() throws Exception {
        var actual = frame(QUERY).source().orElseThrow(); assertEquals(2, actual.eventCensus().events().get(0).options().get(0).authoredOptionIndex());
        var othersDisabled = token(QUERY); for (var o : options(othersDisabled)) if (o.get("authored_option_index").intValue() != 2) ((ObjectNode) o).put("native_can_select", false);
        assertTrue(changed(othersDisabled).source().orElseThrow().selectCAdmissible());
        var cDisabled = token(QUERY); c(cDisabled).put("native_can_select", false); reject(cDisabled);
        source(cDisabled).put("select_c_admissible", false); assertTrue(changed(cDisabled).successful());
        var empty = token(QUERY); c(empty).put("text", ""); reject(empty);
        source(empty).put("select_c_admissible", false); assertEquals("", changed(empty).source().orElseThrow().eventCensus().events().get(0).options().get(0).text());
    }

    @Test void fixedInstanceCannotMaskPartialDuplicateForeignHiddenOrWrongRecipientRows() throws Exception {
        var partial = token(QUERY); source(partial).put("sampled_twice", false); reject(partial);
        var incomplete = token(QUERY); census(incomplete).put("census_complete", false); reject(incomplete);
        var count = token(QUERY); census(count).put("named_root_count", 2); reject(count);
        var duplicate = token(QUERY); ((ObjectNode) options(duplicate).get(1)).put("authored_option_index", 2); reject(duplicate);
        var missing = token(QUERY); options(missing).remove(1); reject(missing);
        var foreign = token(QUERY); row(foreign).put("definition_key", "other.event"); reject(foreign);
        var recipient = token(QUERY); row(recipient).put("recipient_character_id", 0); reject(recipient);
        var instance = token(QUERY); source(instance).put("fixed_instance_id", 2); reject(instance);
        var several = token("available-multiple.json"); source(several).put("fixed_instance_id", 1); reject(several);
        for (String key : List.of("named_root_bound", "window_visible", "window_enabled")) { var data = token(QUERY); row(data).put(key, false); reject(data); }
        var cleared = token(QUERY); source(cleared).putNull("fixed_instance_id"); source(cleared).put("select_c_admissible", false); assertTrue(changed(cleared).successful());
    }

    @Test void rawCachedRichtextControlsAndFullUtf8ArePreservedButNulAndMalformedUnicodeAreNot() throws Exception {
        String astral = new String(Character.toChars(0x1f600));
        for (String valid : List.of("", "#P original#!\n\t" + (char) 0x15, "x".repeat(16384), astral.repeat(4096))) {
            var data = token(QUERY); row(data).put("description", valid); var decoded = changed(data);
            assertEquals(valid, decoded.source().orElseThrow().eventCensus().events().get(0).description()); assertEquals(decoded, CurrentStockBookmark1070Result.decode(decoded.encode()));
        }
        for (String invalid : List.of("x".repeat(16385), astral.repeat(4097), "a\0b")) { var data = token(QUERY); row(data).put("description", invalid); reject(data); }
        var original = frame(QUERY).source().orElseThrow(); var e = original.eventCensus().events().get(0);
        for (String invalid : List.of(String.valueOf((char) 0xd800), String.valueOf((char) 0xdc00))) {
            var broken = new CurrentLydSource.EventRow(e.instanceId(), e.recipientCharacterId(), e.authoredOptionCount(), e.definitionKey(), invalid, e.description(), e.namedRootBound(), e.windowVisible(), e.windowEnabled(), e.options());
            var events = new CurrentLydSource.Events(true, 1, List.of(broken));
            assertThrows(IllegalArgumentException.class, () -> new CurrentStockBookmark1070Source(events, original.fixedInstanceId(), true, true));
        }
        var hyphen = token("available-wrong-definition.json"); row(hyphen).put("definition_key", "not-native-key"); reject(hyphen);
    }

    @Test void dispatchedVoidRetainsExactBeforeSourceAndCannotClaimClosureDateSaveOrHandled() throws Exception {
        var query = frame(QUERY); var sent = frame("selection-c-dispatched.json");
        assertEquals(query.source(), sent.source()); assertEquals(Optional.of(1), sent.instanceId()); assertEquals(BigInteger.valueOf(7), sent.claimSequence());
        assertTrue(sent.effectAttempted()); assertTrue(sent.nativeReturned()); assertTrue(sent.successful());
        for (String name : RESPONSES) {
            var result = frame(name); assertFalse(result.nativeHandled()); assertFalse(result.eventClosed()); assertFalse(result.newDateObserved()); assertFalse(result.physicalSaveConfirmed());
            for (String field : List.of("native_handled", "event_closed", "new_date_observed", "physical_save_confirmed")) { var data = token(name); data.put(field, true); reject(data); }
        }
        var noBefore = token("selection-c-dispatched.json"); noBefore.putNull("source"); noBefore.put("source_available", false); reject(noBefore);
        var wrong = token("selection-c-dispatched.json"); wrong.put("instance_id", 2); reject(wrong);
        var unspent = token("selection-c-dispatched.json"); unspent.put("claim_sequence", "0"); reject(unspent);
        var noReturn = token("selection-c-dispatched.json"); noReturn.put("native_returned", false); reject(noReturn);
    }

    @Test void knownStaleSourceAndBothUnknownFormsPreserveOriginalFactsInsteadOfPermission() throws Exception {
        var stale = frame("stale-with-original-source.json"); assertFalse(stale.successful()); assertTrue(stale.sourceAvailable()); assertFalse(stale.effectAttempted()); assertEquals(BigInteger.ZERO, stale.claimSequence());
        assertEquals(frame(QUERY).source(), stale.source());
        var unknown = frame("indeterminate-cleanup.json"); assertFalse(unknown.cleanupKnown()); assertTrue(unknown.effectAttempted()); assertFalse(unknown.nativeReturned());
        assertEquals(BigInteger.valueOf(7), unknown.claimSequence()); assertTrue(unknown.source().isEmpty()); assertEquals(Optional.of(1), unknown.instanceId());
        assertTrue(frame("indeterminate-incomplete.json").cleanupKnown()); assertTrue(frame("indeterminate-incomplete.json").source().isEmpty());
        for (String name : List.of("expired.json", "stale-with-original-source.json", "indeterminate-cleanup.json", "indeterminate-incomplete.json")) {
            var data = token(name); data.putNull("unavailable_reason"); reject(data); data.put("unavailable_reason", ""); reject(data);
        }
        var washed = token("indeterminate-cleanup.json"); washed.put("status", "stale_source"); reject(washed);
        var leaked = token("indeterminate-incomplete.json"); leaked.set("source", source(token(QUERY))); leaked.put("source_available", true); reject(leaked);
    }

    @Test void fullUint64WitnessesAndSignedPackedActorDomainDoNotLosePrecision() throws Exception {
        var original = frame(QUERY); assertEquals(MAX, original.providerGeneration()); assertEquals(MAX, original.querySequence());
        assertEquals(MAX, original.owner().orElseThrow().connectionGeneration()); assertEquals(0xffff_ffffL, original.owner().orElseThrow().threadId());
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var data = token(QUERY); facts(data).put("played_character_id", actor); row(data).put("recipient_character_id", actor);
            assertEquals(actor, changed(data).source().orElseThrow().eventCensus().events().get(0).recipientCharacterId());
            assertEquals(CurrentStockBookmark1070.Action.QUERY.step(), CurrentStockBookmark1070.request(core(actor, 0, true, true), CurrentStockBookmark1070.Action.QUERY, BigInteger.ZERO, BigInteger.ZERO, Optional.empty()).step());
        }
        for (String field : List.of("provider_generation", "query_sequence", "claim_sequence")) {
            for (String value : List.of("18446744073709551616", "-1", "+1", "01", "1.0")) { var data = token(QUERY); data.put(field, value); reject(data); }
            var number = token(QUERY); number.put(field, MAX); reject(number);
        }
        for (String field : List.of("connection_generation", "ticket_sequence", "pump_epoch")) { var data = token(QUERY); owner(data).put(field, "0"); reject(data); }
        var overflow = token(QUERY); owner(overflow).put("thread_id", 0x1_0000_0000L); reject(overflow);
        var decimal = token(QUERY); row(decimal).put("recipient_character_id", 0.0); reject(decimal);
        var fractional = token(QUERY); owner(fractional).put("thread_id", 1.0); reject(fractional);
    }

    @Test void exactUnionFieldsOwnerFactsAndStatusesRejectInventedSelectors() throws Exception {
        for (String key : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action", "status")) { var data = token(QUERY); data.put(key, "foreign"); reject(data); }
        var extra = token(QUERY); extra.put("option_index", 2); reject(extra);
        var extraSource = token(QUERY); source(extraSource).put("permission", true); reject(extraSource);
        var extraRow = token(QUERY); row(extraRow).put("pointer", "1"); reject(extraRow);
        var missing = token(QUERY); source(missing).remove("sampled_twice"); reject(missing);
        var falseAvailability = token(QUERY); falseAvailability.put("source_available", false); reject(falseAvailability);
        var noOwner = token(QUERY); noOwner.putNull("owner"); reject(noOwner);
        var noFacts = token(QUERY); noFacts.putNull("facts_before"); reject(noFacts);
        var zero = token(QUERY); zero.put("provider_generation", "0"); reject(zero);
        var queryInstance = token(QUERY); queryInstance.put("instance_id", 1); reject(queryInstance);
        var wrongBoolean = token(QUERY); source(wrongBoolean).put("sampled_twice", "true"); reject(wrongBoolean);
        var redaction = token(QUERY); redaction.put("addresses_redacted", false); reject(redaction);
    }

    @Test void requestFactoryAndStrictJsonRejectInvalidCoreOrCallerStyleAuthority() throws Exception {
        var query = CurrentStockBookmark1070.Action.QUERY; var choose = CurrentStockBookmark1070.Action.SELECT_C;
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, true), query, BigInteger.ONE, BigInteger.ZERO, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, true), query, BigInteger.ZERO, BigInteger.ZERO, Optional.of(1)));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, true), choose, MAX, MAX, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, true), choose, MAX, MAX, Optional.of(0)));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, -1, true, true), query, BigInteger.ZERO, BigInteger.ZERO, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, false, true), query, BigInteger.ZERO, BigInteger.ZERO, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, false), query, BigInteger.ZERO, BigInteger.ZERO, Optional.empty()));
        assertThrows(IllegalArgumentException.class, () -> CurrentStockBookmark1070.request(core(36423, 0, true, true), choose, MAX.add(BigInteger.ONE), MAX, Optional.of(1)));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 0, true, 0, true, true, 36423, true));
        assertThrows(IllegalArgumentException.class, () -> new CoreFrame.Prefix(53144328, 2, true, 0, true, true, -1, true));
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{\"x\":1,\"x\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{} {}".getBytes(StandardCharsets.UTF_8)));
    }
}

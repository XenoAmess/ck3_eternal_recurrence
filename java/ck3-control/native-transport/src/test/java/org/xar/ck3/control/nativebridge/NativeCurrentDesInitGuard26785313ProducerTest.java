package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Eleven SHA-pinned files are original C++ software bytes. Mutations are Java DATA, never Native observations. */
class NativeCurrentDesInitGuard26785313ProducerTest {
    private record Artifact(String name, int bytes, String sha256) { }
    private static final List<Artifact> CPP = List.of(
        new Artifact("available-actor-negative.json", 1443, "66b87b1da81e26e53f1a84303f7b9d04d653da85badc208b902c1a86e9428649"),
        new Artifact("available-actor-zero.json", 1437, "8eb34cfb294bd18ba8b24cdc61b8a79761681d72524d33f491600b42ae705909"),
        new Artifact("available-shown-false.json", 1449, "7a50f06819dd6787ce97f6147ba553cc2e02c88a20038c556463b80533382aa9"),
        new Artifact("available-shown-true.json", 1444, "42204ac51cea0d81e0656ba3522ffeeb96d1cd0831999cb6e0309876d64dee8e"),
        new Artifact("expired-before-source.json", 864, "c4756586a095adf14dbd7a87eaed29aa37b225b3dec820cfd9d82e3090612ddc"),
        new Artifact("indeterminate-cleanup-unknown.json", 1195, "75862e119c1b1a098343f9d4730d7a91f9661323423b54d37e49ecab0fe54987"),
        new Artifact("indeterminate-incomplete-samples.json", 1200, "7a96b0cb1599ee5263f9a8235d81be5b0f9c2ec324521b27df7144eb303c2a05"),
        new Artifact("request-query-guard.json", 742, "2caa1ec8f68ec784f7b764eac7d250164a68b7272ce66f86bf950623e9d4b367"),
        new Artifact("stale-source-actor-changed.json", 1187, "1ecb05e46ab2bf676e3841bba60560dfd5a0d213b1216a2f1b69978914e11727"),
        new Artifact("unavailable-missing-definition.json", 1202, "2475fc2975d09e09724d4dcda4fb81ac72d58302d7960f0656608cb570c728c3"),
        new Artifact("unavailable-no-facts.json", 880, "8119c0012be5879febe3e2cb02481b562869f0d476b9672d761b080afbd7315b")
    );
    private static final List<String> RESPONSE_NAMES = List.of(
            "available-shown-false.json", "available-shown-true.json", "available-actor-zero.json",
            "available-actor-negative.json", "unavailable-missing-definition.json", "stale-source-actor-changed.json",
            "indeterminate-cleanup-unknown.json", "expired-before-source.json", "unavailable-no-facts.json",
            "indeterminate-incomplete-samples.json");
    private static final String AVAILABLE = "available-shown-false.json";
    private static final BigInteger U64_MAX = new BigInteger("18446744073709551615");

    private static byte[] raw(String name) throws Exception {
        var expected = CPP.stream().filter(a -> a.name().equals(name)).findFirst()
                .orElseThrow(() -> new IOException("Unknown original C++ DES guard resource: " + name));
        try (var in = NativeCurrentDesInitGuard26785313ProducerTest.class
                .getResourceAsStream("/current267-des-init-guard-cpp-a891/" + name)) {
            if (in == null) throw new IOException("Original C++ DES guard resource absent: " + name);
            byte[] bytes = in.readAllBytes();
            assertEquals(expected.bytes(), bytes.length, name);
            assertEquals(expected.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), name);
            return bytes;
        }
    }
    private static ObjectNode envelope(String name) throws Exception {
        return NativeWire.object(NativeWire.parse(raw(name)));
    }
    private static ObjectNode token(String name) throws Exception {
        return NativeWire.object(envelope(name).get("result"));
    }
    private static ObjectNode source(ObjectNode result) { return (ObjectNode) result.get("source"); }
    private static ObjectNode facts(ObjectNode result) { return (ObjectNode) result.get("facts_before"); }
    private static ObjectNode owner(ObjectNode result) { return (ObjectNode) result.get("owner"); }
    private static CurrentDesInitGuardResult changed(ObjectNode result) throws IOException {
        return CurrentDesInitGuardResult.decode(new RawJson(StrictJson.canonical(result)));
    }
    private static CurrentDesInitGuardResult frame(String name) throws Exception { return changed(token(name)); }
    private static void reject(ObjectNode result) { assertThrows(IOException.class, () -> changed(result)); }
    private static CoreFrame.Partial core(CoreFrame.Prefix prefix) {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313, prefix);
    }
    private static CoreFrame.Prefix prefixWithActor(int actor, int local) throws Exception {
        var p = frame(AVAILABLE).factsBefore().orElseThrow();
        return new CoreFrame.Prefix(p.dateRaw(), p.speed(), p.paused(), local, p.mapReady(),
                p.hasPlayedCharacter(), actor, p.playedCharacterAlive());
    }

    @Test void allElevenOriginalFilesRemainPinnedAndTenResponsesRoundtripTyped() throws Exception {
        assertEquals(11, CPP.size());
        int available = 0, refused = 0;
        for (String name : RESPONSE_NAMES) {
            var original = StrictJson.object(envelope(name), Set.of("type", "protocol_version", "request_id", "ok", "result"));
            assertEquals("command_result", original.get("type").textValue());
            assertEquals(1, original.get("protocol_version").intValue());
            assertFalse(original.get("request_id").textValue().isEmpty());
            var result = changed(NativeWire.object(original.get("result")));
            assertEquals(result, CurrentDesInitGuardResult.decode(result.encode()), name);
            assertEquals(original.get("ok").booleanValue(), result.successful(), name);
            assertEquals(24, NativeWire.parse(result.encode().bytes()).size(), name);
            if (result.successful()) available++; else refused++;
        }
        assertEquals(4, available); assertEquals(6, refused);
        assertEquals("execute_step", envelope("request-query-guard.json").get("type").textValue());
    }

    @Test void actualShownFalseIsAvailableWithoutGrantingInitializationOrEffectCredit() throws Exception {
        var hidden = frame(AVAILABLE); var shown = frame("available-shown-true.json");
        assertTrue(hidden.successful()); assertTrue(shown.successful());
        assertFalse(hidden.source().orElseThrow().nativeShown()); assertTrue(shown.source().orElseThrow().nativeShown());
        for (var result : List.of(hidden, shown)) {
            var s = result.source().orElseThrow();
            assertEquals(9, s.encode().size());
            assertTrue(s.characterAlive()); assertTrue(s.nativeIsPlayer()); assertTrue(s.nativeDefinitionFound());
            assertTrue(s.scopeBound()); assertTrue(s.sampledTwice());
            assertEquals(U64_MAX, result.providerGeneration()); assertEquals(U64_MAX, result.querySequence());
            assertEquals(U64_MAX, result.owner().orElseThrow().connectionGeneration());
            assertEquals(U64_MAX, result.owner().orElseThrow().ticketSequence());
            assertEquals(U64_MAX, result.owner().orElseThrow().pumpEpoch());
            assertEquals(0xffff_ffffL, result.owner().orElseThrow().threadId());
            assertEquals(BigInteger.ZERO, result.claimSequence());
            assertFalse(result.effectAttempted()); assertFalse(result.nativeReturned()); assertFalse(result.nativeHandled());
            assertFalse(result.initializationExecuted()); assertFalse(result.migrationExecuted());
            assertFalse(result.newDateObserved()); assertFalse(result.physicalSaveConfirmed());
        }
    }

    @Test void originalRequestCommonEightAndNestedSevenMatchTheTypedFactory() throws Exception {
        var original = StrictJson.object(envelope("request-query-guard.json"), Set.of("type", "protocol_version", "request_id",
                "step", "expected_revision", "arguments", "des_init_guard", "core_control_deadline_unix_ms"));
        assertEquals(8, original.size()); assertEquals("execute_step", original.get("type").textValue());
        assertEquals(1, original.get("protocol_version").intValue()); assertEquals(0, original.get("expected_revision").intValue());
        assertEquals("des-guard-query-original-01", original.get("request_id").textValue());
        assertEquals(U64_MAX, original.get("core_control_deadline_unix_ms").bigIntegerValue());
        var claim = StrictJson.object(original.get("des_init_guard"), Set.of("schema", "game_version", "executable_sha256",
                "adapter_id", "backend", "action", "expected_core"));
        var request = CurrentDesInitGuard.request(core(frame(AVAILABLE).factsBefore().orElseThrow()));
        assertEquals(original.get("step").textValue(), request.step());
        assertEquals(CurrentDesInitGuard.STEP, request.step());
        assertEquals(CurrentDesInitGuard.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "des_init_guard"));
        assertEquals(original.get("arguments"), fields.get("arguments")); assertEquals(0, fields.get("arguments").size());
        var generated = NativeWire.object(fields.get("des_init_guard")); assertEquals(7, generated.size());
        // Original CPP bytes stay pinned. Only the parser's documented legal SHA case equivalence is normalized for comparison.
        assertEquals(claim.get("executable_sha256").textValue().toUpperCase(Locale.ROOT),
                generated.get("executable_sha256").textValue().toUpperCase(Locale.ROOT));
        var comparable = generated.deepCopy(); comparable.set("executable_sha256", claim.get("executable_sha256"));
        assertEquals(claim, comparable);
        String actualJavaRequestOutput = System.getProperty("xar.des.init.guard.java.request.output");
        if (actualJavaRequestOutput != null) {
            // Exact Java factory/encoder output for independent C++ parser qualification only.
            // No Native dispatch occurs, and all original C++ files remain unchanged.
            fields.put("core_control_deadline_unix_ms", original.get("core_control_deadline_unix_ms").bigIntegerValue());
            byte[] actualPacket = NativeWire.execute(original.get("request_id").textValue(), request.step(),
                    BigInteger.ZERO, StrictJson.canonical(fields));
            java.nio.file.Files.write(java.nio.file.Path.of(actualJavaRequestOutput), actualPacket,
                    java.nio.file.StandardOpenOption.CREATE_NEW);
        }
        for (String outer : List.of("request_id", "step", "core_control_deadline_unix_ms", "provider_generation", "query_sequence",
                "character_id", "guard_key", "lease", "scope")) assertFalse(generated.has(outer), outer);
    }

    @Test void signedPackedActorsUseOnlyMinusOneAsInvalidWhileLocalPlayerRemainsNonnegative() throws Exception {
        assertEquals(0, frame("available-actor-zero.json").source().orElseThrow().characterId());
        assertEquals(-2, frame("available-actor-negative.json").source().orElseThrow().characterId());
        // Explicit Java DATA boundaries; these are not additional C++ observations.
        for (int actor : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var n = token(AVAILABLE); source(n).put("character_id", actor); facts(n).put("played_character_id", actor);
            assertEquals(actor, changed(n).source().orElseThrow().characterId());
            assertEquals(CurrentDesInitGuard.STEP, CurrentDesInitGuard.request(core(prefixWithActor(actor, 0))).step());
        }
        var invalid = token(AVAILABLE); source(invalid).put("character_id", -1); facts(invalid).put("played_character_id", -1); reject(invalid);
        assertThrows(IllegalArgumentException.class, () -> CurrentDesInitGuard.request(core(prefixWithActor(-1, 0))));
        assertThrows(IllegalArgumentException.class, () -> CurrentDesInitGuard.request(core(prefixWithActor(0, -1))));
        var badLocal = token(AVAILABLE); facts(badLocal).put("local_player_id", -1); reject(badLocal);
        var mismatch = token(AVAILABLE); source(mismatch).put("character_id", 0); reject(mismatch);
        for (BigInteger actor : List.of(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))) {
            var outOfRange = token(AVAILABLE); source(outOfRange).put("character_id", actor); reject(outOfRange);
        }
    }

    @Test void incompleteOrMistypedSourceGuardsCannotBeEncodedAsAvailable() throws Exception {
        for (String key : List.of("character_alive", "native_is_player", "native_definition_found", "scope_bound", "sampled_twice")) {
            var n = token(AVAILABLE); source(n).put(key, false); reject(n);
        }
        for (String key : List.of("character_alive", "native_is_player", "native_definition_found", "native_shown", "scope_bound", "sampled_twice")) {
            var n = token(AVAILABLE); source(n).put(key, "true"); reject(n);
            n = token(AVAILABLE); source(n).putNull(key); reject(n);
        }
        var absent = token(AVAILABLE); absent.putNull("source"); reject(absent);
        var unavailable = token(AVAILABLE); unavailable.put("source_available", false); reject(unavailable);
        var falsePlayer = token(AVAILABLE); source(falsePlayer).put("native_is_player", false); reject(falsePlayer);
        // A NativeIsPlayer refusal is not converted into an AI finding or a false-shown source.
        assertTrue(frame("unavailable-missing-definition.json").source().isEmpty());
    }

    @Test void allRefusalsRetainSourceNullZeroIdentityAndOriginalReasonWithoutLaunderingUnknown() throws Exception {
        for (String name : RESPONSE_NAMES) {
            var result = frame(name); if (result.successful()) continue;
            assertTrue(result.source().isEmpty(), name); assertFalse(result.sourceAvailable(), name);
            assertEquals(BigInteger.ZERO, result.providerGeneration(), name);
            assertEquals(BigInteger.ZERO, result.querySequence(), name); assertEquals(BigInteger.ZERO, result.claimSequence(), name);
            assertFalse(result.unavailableReason().orElseThrow().isEmpty(), name);
            var nonzeroProvider = token(name); nonzeroProvider.put("provider_generation", "1"); reject(nonzeroProvider);
            var nonzeroQuery = token(name); nonzeroQuery.put("query_sequence", "1"); reject(nonzeroQuery);
            var missingReason = token(name); missingReason.putNull("unavailable_reason"); reject(missingReason);
            var emptyReason = token(name); emptyReason.put("unavailable_reason", ""); reject(emptyReason);
        }
        var unknown = frame("indeterminate-cleanup-unknown.json");
        assertEquals(CurrentDesInitGuardResult.Status.INDETERMINATE, unknown.status()); assertFalse(unknown.cleanupKnown());
        assertEquals(CurrentDesInitGuardResult.Status.INDETERMINATE, frame("indeterminate-incomplete-samples.json").status());
        assertTrue(frame("indeterminate-incomplete-samples.json").cleanupKnown());
        var erasedUnknown = token("indeterminate-cleanup-unknown.json"); erasedUnknown.put("status", "unavailable"); reject(erasedUnknown);
        var availableReason = token(AVAILABLE); availableReason.put("unavailable_reason", "not-really-available"); reject(availableReason);
        var availableEmpty = token(AVAILABLE); availableEmpty.put("unavailable_reason", ""); reject(availableEmpty);
    }

    @Test void readonlyQueryRejectsEveryEffectFlagClaimAndUnredactedAddressAssertion() throws Exception {
        for (String name : List.of(AVAILABLE, "unavailable-no-facts.json", "indeterminate-cleanup-unknown.json")) {
            for (String key : List.of("effect_attempted", "native_returned", "native_handled", "initialization_executed",
                    "migration_executed", "new_date_observed", "physical_save_confirmed")) {
                var n = token(name); n.put(key, true); reject(n);
            }
            var claim = token(name); claim.put("claim_sequence", "1"); reject(claim);
            var address = token(name); address.put("addresses_redacted", false); reject(address);
        }
    }

    @Test void exactKeysAndNullableFactsOwnerRolesRejectPartialOrForeignData() throws Exception {
        var extra = token(AVAILABLE); extra.put("lease", "caller"); reject(extra);
        var missing = token(AVAILABLE); missing.remove("source_available"); reject(missing);
        var extraSource = token(AVAILABLE); source(extraSource).put("is_ai", false); reject(extraSource);
        var missingSource = token(AVAILABLE); source(missingSource).remove("scope_bound"); reject(missingSource);
        var extraOwner = token(AVAILABLE); owner(extraOwner).put("connection_id", "1"); reject(extraOwner);
        var extraCore = token(AVAILABLE); facts(extraCore).put("treasury", 0); reject(extraCore);
        var missingFacts = token(AVAILABLE); missingFacts.putNull("facts_before"); reject(missingFacts);
        var missingOwner = token(AVAILABLE); missingOwner.putNull("owner"); reject(missingOwner);
        var noFacts = frame("unavailable-no-facts.json"); assertTrue(noFacts.factsBefore().isEmpty()); assertTrue(noFacts.owner().isEmpty());
        var split = token("unavailable-no-facts.json"); split.set("owner", token(AVAILABLE).get("owner")); reject(split);
        var reasonNumber = token("unavailable-no-facts.json"); reasonNumber.put("unavailable_reason", 0); reject(reasonNumber);
    }

    @Test void uint64AndOwnerThreadPrecisionStayStrictWithoutFloatingPointOrSignedCoercion() throws Exception {
        for (String field : List.of("provider_generation", "query_sequence", "claim_sequence")) {
            for (String invalid : List.of("-1", "01", "+1", "1.0", " 1", "18446744073709551616")) {
                var n = token(AVAILABLE); n.put(field, invalid); reject(n);
            }
            var number = token(AVAILABLE); number.put(field, BigInteger.ONE); reject(number);
            var zero = token(AVAILABLE); if (!field.equals("claim_sequence")) { zero.put(field, "0"); reject(zero); }
        }
        for (String field : List.of("connection_generation", "ticket_sequence", "pump_epoch")) {
            for (String invalid : List.of("0", "-1", "01", "18446744073709551616")) {
                var n = token(AVAILABLE); owner(n).put(field, invalid); reject(n);
            }
            var number = token(AVAILABLE); owner(number).put(field, U64_MAX); reject(number);
        }
        for (long invalid : new long[] {0, -1, 0x1_0000_0000L}) {
            var n = token(AVAILABLE); owner(n).put("thread_id", invalid); reject(n);
        }
        var floating = token(AVAILABLE); owner(floating).put("thread_id", 1.5);
        // Canonical JSON rejects a floating number before RawJson/DTO decoding.
        assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class, () -> StrictJson.canonical(floating));
        var stringThread = token(AVAILABLE); owner(stringThread).put("thread_id", "1"); reject(stringThread);
    }

    @Test void fixedIdentityAndStrictJsonCannotBeReboundToAnotherKeyActionOrStatus() throws Exception {
        for (String key : List.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "action")) {
            var n = token(AVAILABLE); n.put(key, "foreign"); reject(n);
        }
        var unknownStatus = token(AVAILABLE); unknownStatus.put("status", "ok"); reject(unknownStatus);
        var foreignGuard = token(AVAILABLE); source(foreignGuard).put("guard_key", "caller_selected_gui"); reject(foreignGuard);
        var sourceSchema = token(AVAILABLE); source(sourceSchema).put("schema", CurrentDesInitGuard.SCHEMA); reject(sourceSchema);
        String json = new String(StrictJson.canonical(token(AVAILABLE)), StandardCharsets.UTF_8);
        String duplicate = "{\"status\":\"available\"," + json.substring(1);
        // RawJson itself rejects malformed original-document DATA before DTO decoding.
        assertThrows(IllegalArgumentException.class, () -> new RawJson(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> new RawJson((json + "{}").getBytes(StandardCharsets.UTF_8)));
    }
}

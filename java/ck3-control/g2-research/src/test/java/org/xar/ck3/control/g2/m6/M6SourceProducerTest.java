package org.xar.ck3.control.g2.m6;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.g2.m6.G2M6Contracts.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Original bytes are actual historical closed responses. Mutations below are explicit negative fixtures. */
public final class M6SourceProducerTest {
    private static final String LEDGER_HASH = "edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580";
    private static final String AUTO_HASH = "44defd2b790131659d9dbd617b755b98d9d36820789bbc5e8248274152c93c24";
    private static final String AUTO_PATH = "D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime/p37-responses/0048-1-result.json";
    private static final String LEDGER_PATH = "Z:/ck3_mod_rewrite/docs/ck3-native-ai/evidence/m6-sway-closed-ledger-2026-10-20.json";

    @Test public void actualClosedLedgerKeepsBothRulersGenZeroAndRealGainWithoutTerminalCredit() throws IOException {
        byte[] raw = ledger(); assertEquals(LEDGER_HASH, sha(raw)); assertEquals(21864, raw.length);
        CampaignEvidence evidence = M6SourceProducer.fromClosedLedger(raw, source(raw, LEDGER_PATH));
        assertEquals(2, evidence.episodes().size()); assertArrayEquals(raw, evidence.originalLedger().bytes());
        Episode current = evidence.episodes().getFirst(), previous = evidence.episodes().get(1);
        assertEquals(40526, current.identity().actorCharacterId()); assertEquals(31254, previous.identity().actorCharacterId());
        assertEquals(2, previous.identity().schemeInstanceId()); assertEquals(0, previous.identity().schemeInstanceGeneration());
        assertEquals(StartOrigin.UNKNOWN, previous.start().orElseThrow().origin());
        assertEquals("25", current.firstNamedGain().orElseThrow().after().value().orElseThrow().toString());
        assertTrue(current.firstNamedGain().orElseThrow().consumption().consumedAfter(current.firstNamedGain().orElseThrow().observed()));
        assertFalse(current.terminal().orElseThrow().instanceTerminalOutcomeObserved());
        assertFalse(current.terminal().orElseThrow().consumption().consumedAfter(current.terminal().orElseThrow().observed()));
        assertFalse(new M6Research().evaluateCampaign(evidence).schemeComplete());
    }

    @Test public void actualOrdinaryStartResponsePromotesOnlyExactGenZeroArchivedEpisode() throws IOException {
        byte[] rawAuto = auto(); assertEquals(87990, rawAuto.length); assertEquals(AUTO_HASH, sha(rawAuto));
        byte[] packet = packet(ledger(), rawAuto, null);
        CampaignEvidence evidence = M6SourceProducer.fromEvidencePacket(packet, source(packet, "memory:packet-original"));
        assertEquals(StartOrigin.UNKNOWN, evidence.episodes().getFirst().start().orElseThrow().origin());
        assertEquals(StartOrigin.ORDINARY_FULL_PLANNER, evidence.episodes().get(1).start().orElseThrow().origin());
        var assessed = new M6Research().evaluateCampaign(evidence);
        assertTrue(assessed.episodes().get(1).satisfied().contains(Gate.ORDINARY_START));
        assertFalse(assessed.evidencePacketReady()); assertFalse(assessed.schemeComplete()); assertFalse(assessed.wholeM6Complete());
    }

    @Test public void actualCompletionRowsRemainUnknownOrContinueAndNeverOpinionOrCanContinueSuccess() throws IOException {
        CampaignEvidence campaign = M6SourceProducer.fromClosedLedger(ledger(), source(ledger(), LEDGER_PATH));
        JsonNode root = StrictJson.parse(ledger());
        JsonNode current = root.path("resolved").path("latest_instance_observation").path("native_observation");
        var state = M6SourceProducer.fromRawCompletion(bytes(current), campaign.episodes().getFirst().identity());
        assertEquals(M6SourceProducer.NativeState.UNOBSERVED, state.nativeState());
        ObjectNode can = current.deepCopy(); can.put("native_can_continue_observed", true); can.put("native_can_continue", true);
        assertEquals(M6SourceProducer.NativeState.UNOBSERVED,
                M6SourceProducer.fromRawCompletion(bytes(can), state.identity()).nativeState());
        JsonNode old = root.path("resolved").path("previous_interventions").get(0).path("latest_instance_observation").path("native_observation");
        assertEquals(M6SourceProducer.NativeState.CONTINUE,
                M6SourceProducer.fromRawCompletion(bytes(old), campaign.episodes().get(1).identity()).nativeState());
        assertTrue(StrictJson.parse(M6SourceProducer.composeCurrentObservation(bytes(current), state.identity()).bytes()).isNull());
    }

    @Test public void originalNumericUint64ContainerIdentityIsNeverRoundedOrConvertedThroughDouble() throws IOException {
        var evidence = M6SourceProducer.fromClosedLedger(ledger(), source(ledger(), LEDGER_PATH));
        JsonNode before = StrictJson.parse(evidence.episodes().getFirst().originalResolved().bytes());
        assertEquals("11680299756822511911", before.path("native_receipt").path("post_container_generation").bigIntegerValue().toString());
        assertEquals("17922751897147325986", StrictJson.parse(evidence.episodes().get(1).originalResolved().bytes())
                .path("native_receipt").path("post_container_generation").bigIntegerValue().toString());
    }

    @Test public void boolFloatStringAndMissingIdentityTokensAreRejectedPastFreshSourceHashes() throws IOException {
        for (String token : Set.of("true", "2.0", "\"2\"", "null")) {
            ObjectNode bad = (ObjectNode) StrictJson.parse(ledger());
            String marker = "__M6_EXACT_INVALID_ID_TOKEN__";
            ((ObjectNode) bad.path("resolved").path("previous_interventions").get(0).path("native_receipt"))
                    .put("scheme_instance_id", marker);
            String encoded = bad.toString(), quoted = "\"" + marker + "\"";
            assertTrue(encoded.contains(quoted), "raw-token fixture location exists");
            assertEquals(encoded.indexOf(quoted), encoded.lastIndexOf(quoted), "one explicit raw-token fixture location");
            byte[] raw = encoded.replace(quoted, token).getBytes(StandardCharsets.UTF_8);
            assertFalse(StrictJson.parse(raw).at("/resolved/previous_interventions/0/native_receipt/scheme_instance_id").isIntegralNumber(),
                    "fixture must preserve a non-integer JSON token: " + token);
            assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(raw, source(raw, "memory:invalid-identity")),
                    "original invalid JSON token must survive fixture serialization: " + token);
        }
        ObjectNode missing = (ObjectNode) StrictJson.parse(ledger());
        ((ObjectNode) missing.path("resolved").path("first_named_gain_intervention")).remove("action_id");
        byte[] raw = bytes(missing);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(raw, source(raw, "memory:missing-identity")));
    }

    @Test public void sourceDriftWrongAdmissionAndAckWithoutIndependentActiveCannotAcquireOrdinaryOrigin() throws IOException {
        byte[] original = ledger(); byte[] changed = original.clone(); changed[changed.length - 1] ^= 1;
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(changed, source(original, LEDGER_PATH)));
        ObjectNode wrongBinding = StrictJson.object(); wrongBinding.put("actor_character_id", 31254);
        wrongBinding.put("episode_run_id", "wrong-episode"); wrongBinding.put("game_pid", 214568);
        byte[] mismatch = packet(original, auto(), wrongBinding);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromEvidencePacket(mismatch, source(mismatch, "memory:wrong-admission")));
        ObjectNode ack = (ObjectNode) StrictJson.parse(auto(), M6SourceProducer.MAX_BYTES);
        ((ObjectNode) ack.at("/result/structured_content/result")).remove("applied_instance_observation");
        byte[] bad = packet(original, bytes(ack), null);
        assertThrows(RuntimeException.class, () -> M6SourceProducer.fromEvidencePacket(bad, source(bad, "memory:ack-only")));
    }

    @Test public void packetNestedHashAndUnknownKeysMissingVersusNullStayStrict() throws IOException {
        byte[] packet = packet(ledger(), auto(), null);
        ObjectNode root = (ObjectNode) StrictJson.parse(packet, M6SourceProducer.MAX_BYTES);
        ((ObjectNode) root.path("ledger").path("source_ref")).put("sha256", "0".repeat(64));
        byte[] drift = bytes(root);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromEvidencePacket(drift, source(drift, "memory:bad-nested-pin")));
        ObjectNode unknown = (ObjectNode) StrictJson.parse(packet, M6SourceProducer.MAX_BYTES); unknown.put("ordinary", true);
        byte[] extra = bytes(unknown);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromEvidencePacket(extra, source(extra, "memory:unknown-field")));
        ObjectNode wrong = (ObjectNode) StrictJson.parse(ledger()); wrong.putNull("resolved"); wrong.putNull("pending");
        byte[] empty = bytes(wrong);
        assertTrue(M6SourceProducer.fromClosedLedger(empty, source(empty, "memory:empty-resolved")).episodes().isEmpty());
        wrong.remove("resolved"); byte[] absent = bytes(wrong);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(absent, source(absent, "memory:missing-resolved")));
    }

    @Test public void nativeAndNormalizedSourceSchemasDoNotUseBuildFieldFallbacks() throws IOException {
        CampaignEvidence campaign = M6SourceProducer.fromClosedLedger(ledger(), source(ledger(), LEDGER_PATH));
        ObjectNode root = (ObjectNode) StrictJson.parse(ledger());
        ObjectNode raw = (ObjectNode) root.path("resolved").path("latest_instance_observation").path("native_observation");
        raw.remove("build_version"); byte[] wrongNative = bytes(raw);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromRawCompletion(wrongNative, campaign.episodes().getFirst().identity()));
        ObjectNode ledger = (ObjectNode) StrictJson.parse(ledger());
        ObjectNode receipt = (ObjectNode) ledger.path("resolved").path("native_receipt");
        receipt.set("build_version", receipt.remove("exact_ck3_build"));
        receipt.set("executable_sha256", receipt.remove("exe_sha256"));
        byte[] wrongNormalized = bytes(ledger);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(wrongNormalized, source(wrongNormalized, "memory:renamed-normalized-fields")));
        ObjectNode legacy = (ObjectNode) StrictJson.parse(ledger());
        for (JsonNode original : new JsonNode[]{legacy.path("resolved").path("native_receipt"),
                legacy.path("resolved").path("applied_instance_observation").path("source_read")}) {
            ((ObjectNode) original).put("exact_ck3_build", "1.20.0.3");
            ((ObjectNode) original).put("exe_sha256", "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        }
        byte[] oldIdentity = bytes(legacy);
        assertTrue(M6SourceProducer.fromClosedLedger(oldIdentity, source(oldIdentity, "memory:original-three-current-four"))
                .episodes().getFirst().start().isPresent());
        ((ObjectNode) legacy.path("resolved").path("native_receipt")).put("exe_sha256", M6SourceProducer.EXE);
        byte[] mismatch = bytes(legacy);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(mismatch, source(mismatch, "memory:wrong-original-version-pair")));
    }

    @Test public void matchingActiveRecoveryKeepsIdentityOnlyWithoutInventingOriginalStartProvenance() throws IOException {
        ObjectNode root = (ObjectNode) StrictJson.parse(ledger()); ObjectNode resolved = (ObjectNode) root.path("resolved");
        resolved.remove("native_receipt"); ObjectNode observed = (ObjectNode) resolved.remove("applied_instance_observation");
        observed.put("schema", "xar.ck3.sway-recovered-instance-observation.v1");
        observed.put("source_kind", "matching_active_readback_recovery"); observed.put("submission_receipt_available", false);
        resolved.set("recovered_instance_observation", observed); byte[] recovered = bytes(root);
        Episode episode = M6SourceProducer.fromClosedLedger(recovered, source(recovered, "memory:declared-recovery-fixture")).episodes().getFirst();
        assertEquals(StartOrigin.RECOVERED_IDENTITY_ONLY, episode.start().orElseThrow().origin());
        assertFalse(new M6Research().evaluateEpisode(episode).satisfied().contains(Gate.ORDINARY_START));
        ((ObjectNode) observed.path("source_read")).remove("queried_snapshot_id"); byte[] missing = bytes(root);
        assertThrows(IllegalArgumentException.class, () -> M6SourceProducer.fromClosedLedger(missing, source(missing, "memory:incomplete-recovery")));
    }

    @Test public void syntheticFullInstanceZeroRemainsValidUnderTheExistingProducerDomain() throws IOException {
        ObjectNode root = (ObjectNode) StrictJson.parse(ledger());
        ObjectNode retained = root.path("resolved").path("previous_interventions").get(0).deepCopy();
        assertEquals(2, retained.path("native_receipt").path("scheme_instance_id").longValue());
        assertEquals(0, retained.path("native_receipt").path("scheme_instance_generation").intValue());
        zeroSchemeInstance(retained);
        root.set("resolved", retained);
        byte[] synthetic = bytes(root);
        CampaignEvidence evidence = M6SourceProducer.fromClosedLedger(synthetic,
                source(synthetic, "memory:synthetic-full-instance-zero"));
        assertEquals(1, evidence.episodes().size());
        assertEquals(0, evidence.episodes().getFirst().identity().schemeInstanceId());
        assertEquals(0, evidence.episodes().getFirst().identity().schemeInstanceGeneration());
        assertFalse(new M6Research().evaluateCampaign(evidence).grantsSubmissionAuthority());
    }

    private static void zeroSchemeInstance(JsonNode value) {
        if (value.isObject()) {
            ObjectNode object = (ObjectNode) value;
            if (object.has("scheme_instance_generation")) assertEquals(0, object.get("scheme_instance_generation").intValue());
            var names = object.fieldNames();
            while (names.hasNext()) {
                String name = names.next();
                if (name.equals("scheme_instance_id")) object.put(name, 0);
                else zeroSchemeInstance(object.get(name));
            }
        } else if (value.isArray()) {
            for (JsonNode child : value) zeroSchemeInstance(child);
        }
    }

    public static byte[] packet(byte[] ledger, byte[] auto, ObjectNode bindingOverride) {
        byte[] encoded = M6SourceProducer.encodeEvidencePacket(ledger, ref(ledger, LEDGER_PATH), auto, ref(auto, AUTO_PATH),
                new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        if (bindingOverride == null) return encoded;
        ObjectNode root = (ObjectNode) StrictJson.parse(encoded, M6SourceProducer.MAX_BYTES);
        ((ObjectNode) root.path("ordinary_start_sources").get(0)).set("admitted_binding", bindingOverride);
        return bytes(root);
    }
    public static G2Source source(byte[] raw, String path) {
        return new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-20T00:47:10Z", M6SourceProducer.BUILD, ref(raw, path));
    }
    public static byte[] ledger() throws IOException { return resource("/closed-ledger-original.json"); }
    public static byte[] auto() throws IOException { return resource("/ordinary-start-auto48-original.json"); }
    private static byte[] resource(String name) throws IOException {
        try (var stream = M6SourceProducerTest.class.getResourceAsStream(name)) {
            if (stream == null) throw new IOException("required actual source resource missing: " + name);
            byte[] raw = stream.readNBytes(M6SourceProducer.MAX_BYTES + 1);
            if (raw.length > M6SourceProducer.MAX_BYTES) throw new IOException("source resource cap exceeded"); return raw;
        }
    }
    private static ExactRef ref(byte[] raw, String path) { return new ExactRef(path, raw.length, sha(raw)); }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static String sha(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}

package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Real shared native serializer vectors plus explicitly synthetic frame, recovery and malformed variants. No Game credit. */
public final class SwayNativeFormalTest {
    private static final long ACTOR = 50331649, TARGET = 50331650;
    private static final int DATE = 53220000;
    private static final ExactRef ORIGINAL = new ExactRef("fixture:synthetic-original-ledger", 1, "a".repeat(64));
    @Test void sharedProducerTargetPreservesFullNativeUint64GenerationThroughJsonRoundTrip() throws Exception {
        SwayNativeWire.TargetRead read = read();
        assertEquals(new BigInteger("16786632562036001389"), read.containerGeneration()); assertTrue(read.startable(true));
        assertEquals(read, SwayFormalCodec.target(SwayFormalCodec.target(read)));
        assertEquals(read.hashCode(), SwayFormalCodec.target(SwayFormalCodec.target(read)).hashCode());
    }
    @Test void exactWholeNativeEnvelopeRejectsWrongFieldsAndWrongScalarTypes() throws Exception {
        for (String defect : List.of("extra", "missing", "bool-revision", "float-revision", "wrong-request", "read-only", "null-list")) {
            ObjectNode packet = vector("query"); ObjectNode body = (ObjectNode)packet.at("/result/active_scheme_sway");
            switch (defect) {
                case "extra" -> body.put("coercion_alias", 1);
                case "missing" -> body.remove("active_scheme_count");
                case "bool-revision" -> body.put("snapshot_revision", true);
                case "float-revision" -> body.put("snapshot_revision", 7.0);
                case "wrong-request" -> packet.put("request_id", "different-original");
                case "read-only" -> ((ObjectNode)packet.get("result")).put("read_only", false);
                case "null-list" -> body.putNull("active_sway_instances");
                default -> throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.target(bytes(packet), "fixture-read", binding(73, 7, DATE), TARGET), defect);
        }
    }
    @Test void originalStartAckIsPendingAndOriginalReceiptStillRequiresIndependentActiveRead() throws Exception {
        var read = read(); var ack = SwayNativeWire.startAck(bytes(vector("submit")), "fixture-submit", "sway-fixture-start", read);
        assertFalse(ack.applied()); Ledger state = SwayFormalState.reduce(seed(), new StartIntent("sway-fixture-start", read, MandatoryContext.CLEAR));
        state = SwayFormalState.reduce(state, new StartAcknowledged(ack)); assertTrue(state.pending().isPresent()); assertTrue(state.resolved().isEmpty());
        var receipt = SwayNativeWire.receipt(bytes(vector("receipt")), "fixture-receipt", read.binding(), "sway-fixture-start", TARGET, read.captureEpoch());
        state = SwayFormalState.reduce(state, new ReceiptRetained(receipt)); assertTrue(state.pending().orElseThrow().receipt().isPresent()); assertTrue(state.resolved().isEmpty());
        Ledger resolved = SwayFormalState.reduce(state, new Recovered(active(binding(73, 7, DATE), 43, 1)));
        assertTrue(resolved.pending().isEmpty()); assertTrue(resolved.resolved().orElseThrow().nativeReceipt().isPresent());
        assertEquals(1, resolved.resolved().orElseThrow().identity().schemeInstanceId());
    }
    @Test void freshProcessRecoveryRetainsOriginalReceiptAndDoesNotCompareItsOldEpochToOne() throws Exception {
        Ledger state = withReceipt(); SwayNativeWire.AppliedReceipt retained = state.pending().orElseThrow().receipt().orElseThrow();
        Ledger recovered = SwayFormalState.reduce(state, new Recovered(active(binding(99, 1, DATE + 24), 1, 1)));
        Episode episode = recovered.resolved().orElseThrow(); assertTrue(episode.nativeReceipt().isEmpty()); assertEquals(Optional.of(retained), episode.retainedReceipt());
        assertEquals(BigInteger.ONE, episode.independentActive().captureEpoch()); assertEquals(DATE, retained.postDateRaw());
        assertEquals(DATE + 24, episode.independentActive().binding().date());
        assertArrayEquals(SwayFormalCodec.encode(recovered), SwayFormalCodec.encode(SwayFormalCodec.decode(SwayFormalCodec.encode(recovered))));
        JsonNode legacy = SwayFormalCodec.originalResolved(episode); assertTrue(legacy.get("native_receipt").isNull());
        assertEquals(DATE, legacy.at("/retained_native_applied_receipt/post_date_raw").intValue());
        assertEquals(DATE + 24, legacy.at("/recovered_instance_observation/source_read/date_raw").intValue());
    }
    @Test void recoveredZeroIsARealFullInstanceThroughIndependentReadback() throws Exception {
        Ledger pending = SwayFormalState.reduce(seed(), new StartIntent("sway-zero-recovery", read(), MandatoryContext.CLEAR));
        Episode recovered = SwayFormalState.reduce(pending, new Recovered(active(binding(99, 1, DATE + 24), 1, 0))).resolved().orElseThrow();
        assertEquals(0, recovered.identity().schemeInstanceId()); assertEquals(0, recovered.identity().schemeInstanceGeneration());
    }
    @Test void sameTargetDifferentFullIdentityCannotResolveOrAuthorizeAnotherStart() throws Exception {
        Ledger pending = withReceipt(); byte[] original = SwayFormalCodec.encode(pending);
        assertThrows(IllegalArgumentException.class, () -> SwayFormalState.reduce(pending, new Recovered(active(binding(99, 1, DATE + 24), 1, 2))));
        assertThrows(IllegalArgumentException.class, () -> SwayFormalState.reduce(pending, new StartIntent("sway-second", read(), MandatoryContext.CLEAR)));
        assertArrayEquals(original, SwayFormalCodec.encode(pending));
    }
    @Test void duplicateAndBoolGenerationRowsAreRejectedBeforeRecovery() throws Exception {
        for (String defect : List.of("duplicate", "bool", "generation")) {
            ObjectNode packet = activePacket(binding(99, 1, DATE + 24), 1, 1); ObjectNode body = (ObjectNode)packet.at("/result/active_scheme_sway"); var rows = (com.fasterxml.jackson.databind.node.ArrayNode)body.get("active_sway_instances");
            if (defect.equals("duplicate")) { rows.add(rows.get(0).deepCopy()); body.put("active_scheme_count", 2); }
            if (defect.equals("bool")) ((ObjectNode)rows.get(0)).put("scheme_instance_generation", false);
            if (defect.equals("generation")) ((ObjectNode)rows.get(0)).put("scheme_instance_generation", 1);
            assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.target(bytes(packet), "fixture-read", binding(99, 1, DATE + 24), TARGET), defect);
        }
    }
    @Test void sameSessionRequiresIndependentEpochAndDateAfterReceipt() throws Exception {
        Ledger pending = withReceipt(); assertThrows(IllegalArgumentException.class, () -> SwayFormalState.reduce(pending, new Recovered(active(binding(73, 7, DATE), 42, 1))));
    }
    @Test void mandatoryAndUnavailableContextsPreserveTheOriginalKnownClearLedger() throws Exception {
        Ledger state = seed(); byte[] original = SwayFormalCodec.encode(state);
        for (MandatoryContext context : List.of(MandatoryContext.MANDATORY, MandatoryContext.UNAVAILABLE)) assertThrows(IllegalArgumentException.class, () -> SwayFormalState.reduce(state, new StartIntent("sway-current", read(), context)));
        assertArrayEquals(original, SwayFormalCodec.encode(state));
    }
    @Test void strictPersistenceDistinguishesMissingNullAndUnsafeConnectionRepresentations() throws Exception {
        ObjectNode encoded = (ObjectNode)StrictJson.parse(SwayFormalCodec.encode(seed()), SwayFormalCodec.MAX); encoded.remove("pending");
        assertThrows(IllegalArgumentException.class, () -> SwayFormalCodec.decode(bytes(encoded)));
        ObjectNode binding = SwayNativeWire.bindingJson(binding(73, 7, DATE)); binding.put("connection_generation", 1);
        assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.binding(binding));
    }
    @Test void stopAckHasNoTerminalOrMaterialCreditAndRejectsFalsePostconditionPromotion() throws Exception {
        var binding = binding(73, 7, DATE); ObjectNode body = StrictJson.object(); body.put("schema", "xar.ck3.selected-sway-stop.v1"); body.put("action_id", "stop-sway-synthetic"); body.put("status", "submitted_verification_pending");
        body.put("actor_character_id", ACTOR); body.put("target_character_id", TARGET); body.put("scheme_instance_id", 1); body.put("scheme_instance_generation", 0); body.put("snapshot_revision", 7); body.put("date_raw", DATE);
        body.put("exact_ck3_build", SwayNativeWire.BUILD); body.put("exe_sha256", SwayNativeWire.EXE); body.put("submit_call_count", 1); body.put("postcondition_verified", false); body.put("terminal_observed", false); body.put("terminal_cause_observed", false); body.put("terminal_cause", "unknown");
        byte[] packet = SwayFormalCodec.payload(SwayNativeWire.STOP, "submitted_verification_pending", "sway_stop", body, false, true);
        assertFalse(SwayNativeWire.stopAck(packet, "persisted-payload", binding, "stop-sway-synthetic", TARGET, 1, 0).terminalObserved());
        body.put("postcondition_verified", true);
        assertThrows(IllegalArgumentException.class, () -> SwayNativeWire.stopAck(SwayFormalCodec.payload(SwayNativeWire.STOP, "submitted_verification_pending", "sway_stop", body, false, true), "persisted-payload", binding, "stop-sway-synthetic", TARGET, 1, 0));
    }
    private static Ledger withReceipt() throws Exception {
        Ledger pending = SwayFormalState.reduce(seed(), new StartIntent("sway-fixture-start", read(), MandatoryContext.CLEAR));
        return SwayFormalState.reduce(pending, new ReceiptRetained(SwayNativeWire.receipt(bytes(vector("receipt")), "fixture-receipt", read().binding(), "sway-fixture-start", TARGET, BigInteger.valueOf(40))));
    }
    private static Ledger seed() { return new Ledger("xenoamess-full-tower-eb9d2c1186", "episode:synthetic", Optional.empty(), Optional.empty(), List.of(), Optional.empty(), ORIGINAL); }
    private static SwayNativeWire.TargetRead read() throws Exception { return SwayNativeWire.target(bytes(vector("query")), "fixture-read", binding(73, 7, DATE), TARGET); }
    private static SwayNativeWire.TargetRead active(SwayNativeWire.Binding binding, int epoch, long id) throws Exception { return SwayNativeWire.target(bytes(activePacket(binding, epoch, id)), "fixture-read", binding, TARGET); }
    private static ObjectNode activePacket(SwayNativeWire.Binding binding, int epoch, long id) throws Exception {
        ObjectNode packet = vector("query"); ObjectNode body = (ObjectNode)packet.at("/result/active_scheme_sway"); body.put("snapshot_revision", binding.revision()); body.put("date_raw", binding.date()); body.put("capture_epoch", epoch); body.put("active_scheme_count", 1); body.put("matching_sway_active", true); body.put("native_complete_can_send", false); body.put("native_legal_now", false);
        body.putArray("active_sway_instances").addObject().put("scheme_instance_id", id).put("scheme_instance_generation", id >>> 24).put("target_character_id", TARGET).put("progress", 1).put("progress_goal", 355).put("is_exposed", false).put("is_frozen", false); return packet;
    }
    static SwayNativeWire.Binding binding(long pid, int revision, int date) {
        var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(ACTOR), BigInteger.valueOf(revision), BigInteger.valueOf(date));
        var frame = new JointBudgetSelector.ProposalFrame(identity, "synthetic:" + revision, BigInteger.valueOf(revision + 1L), "episode:synthetic");
        var origin = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(pid, new PythonOnlyUInt64(new BigInteger("134370000000000001").add(BigInteger.valueOf(pid)))), frame, 1);
        return new SwayNativeWire.Binding(origin, "synthetic:session:" + pid, BigInteger.ONE, "synthetic:authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    static ObjectNode vector(String role) throws Exception {
        String root = System.getProperty("xar.repository.root"); assertNotNull(root, "full CI must provide repository source; missing source is failure");
        Path source = Path.of(root).resolve("ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_sway_" + role + "_wire.json");
        byte[] original = Files.readAllBytes(source); String digest = switch (role) {
            case "query" -> "8051e4ed15f12f5ff1466187ae0c61f05fc91284c4f0821b8e30dea9a0098bed";
            case "submit" -> "0e906ab96b262a266d77677952327a28ce9107fa9069ab32fd8df724970ddefd";
            case "receipt" -> "9731c34de32b17abf59ce44549a10a73231cff199944571419e73dd9a8fa552f";
            default -> throw new AssertionError(role);
        };
        assertEquals(digest, ActionCodec.sha256(original), "original native serializer vector drift"); return (ObjectNode)StrictJson.parse(original, SwayFormalCodec.MAX);
    }
    static byte[] bytes(JsonNode row) { return StrictJson.canonical(row, SwayFormalCodec.MAX); }
}

package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayHistoricalImport;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Synthetic immutable historical input and real public decoders; no live restore authority or dispatch. */
public final class SwaySignedHistory214Test {
    private static final long FULL = 0x8100_0003L;
    private static final int DATE = 53280000;
    private static final BigInteger EPOCH = new BigInteger("9007199254740993");
    private static final BigInteger REV = EPOCH.add(BigInteger.valueOf(100));
    private static final String EPISODE = "software-history214";
    private static final long[][] PAIRS = {{-2, Integer.MIN_VALUE}, {Integer.MIN_VALUE, 0}, {0, Integer.MAX_VALUE}, {Integer.MAX_VALUE, -2}, {41, 73}};

    @Test void signedResolvedImportKeepsWholeOriginalAndExactCurrentIdentity() {
        for (long[] pair : PAIRS) {
            ObjectNode envelope = resolvedEnvelope(pair[0], pair[1]); byte[] original = bytes(envelope);
            var imported = SwayLegacyImport.parse(ref(original), original); var history = imported.resolved().orElseThrow();
            Identity expected = new Identity("sway-history214", pair[0], pair[1], FULL, 129);
            assertEquals(expected, history.identity()); assertArrayEquals(original, imported.original().bytes());
            var cold = SwayFormalCodec.imported(SwayFormalCodec.imported(imported));
            assertArrayEquals(original, cold.original().bytes()); assertEquals(expected, cold.resolved().orElseThrow().identity());
            var intent = SwayFormalCodec.intent(SwayFormalCodec.intent(imported.currentIntent()));
            intent.requireIdentity(expected); assertEquals(expected, intent.requireCurrent(current(pair[0], pair[1], FULL, EPISODE)));
            assertTrue(intent.historicalStartConsumed()); assertTrue(intent.historicalConsumed(SwayHistoricalImport.Plane.FIRST_GAIN));
            assertTrue(intent.historicalConsumed(SwayHistoricalImport.Plane.TERMINAL));
            assertEquals(SwayHistoricalImport.Flag.MISSING, ((SwayHistoricalImport.Retained) history.plane(SwayHistoricalImport.Plane.STOP)).consumption().flag());
            assertEquals(SwayHistoricalImport.Flag.FALSE, ((SwayHistoricalImport.Retained) history.plane(SwayHistoricalImport.Plane.MATERIAL)).consumption().flag());
            assertArrayEquals(imported.currentIntent().original().bytes(), intent.original().bytes());
        }
    }

    @Test void signedPendingStagesKeepOriginalReceiptEpochAndEpisodeBinding() {
        for (long[] pair : PAIRS) for (String stage : List.of("submission_unresolved", "receipt_pending", "postcondition_pending")) {
            ObjectNode envelope = pendingEnvelope(pair[0], pair[1], stage); byte[] original = bytes(envelope);
            var imported = SwayLegacyImport.parse(ref(original), original); var pending = imported.pending().orElseThrow();
            assertEquals(pair[0], pending.actor()); assertEquals(pair[1], pending.target()); assertEquals(EPOCH, pending.preEpoch());
            var cold = SwayFormalCodec.imported(SwayFormalCodec.imported(imported)); assertArrayEquals(original, cold.original().bytes());
            var intent = SwayFormalCodec.intent(SwayFormalCodec.intent(cold.currentIntent()));
            Identity expected = new Identity("sway-pending214", pair[0], pair[1], FULL, 129);
            intent.requireIdentity(expected); assertEquals(expected, intent.requireCurrent(current(pair[0], pair[1], FULL, EPISODE)));
            assertFalse(intent.historicalStartConsumed()); assertFalse(intent.historicalConsumed(SwayHistoricalImport.Plane.TERMINAL));
            assertArrayEquals(pending.original().bytes(), intent.original().bytes());
        }
    }

    @Test void malformedAliasesIdentityDriftAndOriginalSourceGuardsRemainRejected() {
        for (String token : List.of("-1", "4294967294", "2147483648", "-2147483649", "-2.0", "\"-2\"", "true", "null")) {
            for (boolean pending : new boolean[]{true, false}) {
                ObjectNode env = pending ? pendingEnvelope(-2, 0, "submission_unresolved") : resolvedEnvelope(-2, 0);
                node(env, pending ? "/pending" : "/resolved").put("actor_character_id", "history214-token");
                byte[] raw = new String(bytes(env), StandardCharsets.UTF_8).replace("\"history214-token\"", token).getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> SwayLegacyImport.parse(ref(raw), raw), token);
            }
        }
        for (String mutation : List.of("receipt-actor", "receipt-target", "receipt-epoch", "receipt-date", "receipt-build", "receipt-generation", "stage-receipt", "sidecar-actor", "sidecar-episode")) {
            ObjectNode env = pendingEnvelope(-2, 0, "postcondition_pending"), pending = node(env, "/pending"), receipt = node(pending, "/native_applied_receipt");
            switch (mutation) {
                case "receipt-actor" -> receipt.put("actor_character_id", 5);
                case "receipt-target" -> receipt.put("target_character_id", 5);
                case "receipt-epoch" -> receipt.put("post_capture_epoch", EPOCH);
                case "receipt-date" -> receipt.put("post_date_raw", DATE + 1);
                case "receipt-build" -> receipt.put("exact_ck3_build", "unknown");
                case "receipt-generation" -> receipt.put("scheme_instance_generation", 1);
                case "stage-receipt" -> pending.remove("native_applied_receipt");
                case "sidecar-actor" -> node(pending, "/native_receipt_source/before").put("actor_character_id", 5);
                case "sidecar-episode" -> node(pending, "/native_receipt_source/after").put("episode_run_id", "other");
                default -> throw new AssertionError(mutation);
            }
            if (mutation.startsWith("sidecar")) {
                var intent = imported(env).currentIntent();
                assertThrows(IllegalArgumentException.class, () -> intent.requireCurrent(current(-2, 0, FULL, EPISODE)), mutation);
            } else assertThrows(IllegalArgumentException.class, () -> imported(env), mutation);
        }
        ObjectNode stop = resolvedEnvelope(-2, 0); node(stop, "/resolved/stop_intervention").put("original_action_id", "sway-other");
        assertThrows(IllegalArgumentException.class, () -> imported(stop));
        ObjectNode plane = resolvedEnvelope(-2, 0); node(plane, "/resolved/material_intervention").put("target_character_id", 5);
        assertThrows(IllegalArgumentException.class, () -> imported(plane));
        var intent = imported(resolvedEnvelope(-2, 0)).currentIntent();
        assertThrows(IllegalArgumentException.class, () -> intent.requireCurrent(current(-2, 0, FULL + 1, EPISODE)));
        byte[] raw = bytes(resolvedEnvelope(-2, 0));
        assertThrows(IllegalArgumentException.class, () -> SwayLegacyImport.parse(new ExactRef("software:wrong-sha", raw.length, "a".repeat(64)), raw));
    }

    @Test void retainedHistoricalLabelsRemainOnlyHistoricalFacts() {
        for (long[] pair : PAIRS) {
            ObjectNode envelope = resolvedEnvelope(pair[0], pair[1]);
            byte[] original = bytes(envelope);
            var imported = imported(envelope);
            var history = imported.resolved().orElseThrow();
            var intent = imported.currentIntent();

            // Verify retained fields are merely Retained facts with original consumption flags
            var terminalField = history.plane(SwayHistoricalImport.Plane.TERMINAL);
            assertTrue(terminalField instanceof SwayHistoricalImport.Retained);
            assertTrue(((SwayHistoricalImport.Retained) terminalField).consumption().markedConsumed());

            var gainField = history.plane(SwayHistoricalImport.Plane.FIRST_GAIN);
            assertTrue(gainField instanceof SwayHistoricalImport.Retained);
            assertTrue(((SwayHistoricalImport.Retained) gainField).consumption().markedConsumed());

            var materialField = history.plane(SwayHistoricalImport.Plane.MATERIAL);
            assertTrue(materialField instanceof SwayHistoricalImport.Retained);
            assertFalse(((SwayHistoricalImport.Retained) materialField).consumption().markedConsumed());

            var stopField = history.plane(SwayHistoricalImport.Plane.STOP);
            assertTrue(stopField instanceof SwayHistoricalImport.Retained);
            assertFalse(((SwayHistoricalImport.Retained) stopField).consumption().markedConsumed());

            var phaseField = history.plane(SwayHistoricalImport.Plane.PHASE);
            assertTrue(phaseField instanceof SwayHistoricalImport.ExplicitNull);

            var instanceField = history.plane(SwayHistoricalImport.Plane.INSTANCE);
            assertTrue(instanceField instanceof SwayHistoricalImport.Missing);

            // Verify start consumption classification
            assertTrue(history.startConsumption().markedConsumed());
            assertTrue(intent.historicalStartConsumed());
            assertTrue(intent.historicalConsumed(SwayHistoricalImport.Plane.TERMINAL));
            assertTrue(intent.historicalConsumed(SwayHistoricalImport.Plane.FIRST_GAIN));
            assertFalse(intent.historicalConsumed(SwayHistoricalImport.Plane.MATERIAL));
            assertFalse(intent.historicalConsumed(SwayHistoricalImport.Plane.STOP));

            // identityOnlyEpisode must not create Start/gain/terminal
            var episode = SwayHistoricalImport.identityOnlyEpisode(history);
            assertTrue(episode.start().isEmpty());
            assertTrue(episode.firstNamedGain().isEmpty());
            assertTrue(episode.terminal().isEmpty());

            // compose with Inputs.unqueried must not create current/wrapper/common/cause/material or authority/ledger/retry
            var result = M6TerminalSourceComposition.compose(episode, M6TerminalSourceComposition.Inputs.unqueried());
            assertTrue(result.current().isEmpty());
            assertTrue(result.wrapperEnd().isEmpty());
            assertTrue(result.commonEnd().isEmpty());
            assertTrue(result.cause().isEmpty());
            assertTrue(result.material().isEmpty());
            assertFalse(result.requestRetried());
            assertFalse(result.actionAuthorized());
            assertFalse(result.ledgerCommitted());

            // Preserve original immutable whole bytes
            assertArrayEquals(original, imported.original().bytes());
        }
    }

    private static ObjectNode resolvedEnvelope(long actor, long target) {
        ObjectNode env = StrictJson.object().put("schema", "xar.ck3.active-scheme-sway-formal-private.v1").putNull("pending");
        ObjectNode root = tuple(actor, target).put("status", "applied").put("postcondition_verified", true).put("action_id", "sway-history214").put("next_turn_consumed", true);
        ObjectNode receipt = root.putObject("native_receipt").put("schema", "active-scheme-sway-formal-private-v1").put("stage", "applied")
                .put("action_id", "sway-history214").put("postcondition_verified", true).put("scheme_instance_id", FULL).put("scheme_instance_generation", 129)
                .put("exact_ck3_build", SwayNativeWire.BUILD).put("exe_sha256", SwayNativeWire.EXE);
        assertNotNull(receipt);
        ObjectNode terminal = tuple(actor, target).put("next_turn_consumed", true).put("instance_terminal_outcome_observed", true)
                .put("terminal_cause_observed", true).put("terminal_cause", "authored_sway_complete_100_source"); root.set("terminal_intervention", terminal);
        ObjectNode material = tuple(actor, target).put("next_turn_consumed", false).put("tracked_instance_active", true);
        material.putObject("scheme_sway_opinion").put("observed", true).put("present", true).put("value", 25); root.set("material_intervention", material);
        ObjectNode gain = material.deepCopy().put("next_turn_consumed", true).put("incremental_named_gain_observed", true);
        gain.putObject("previous_scheme_sway_opinion").put("observed", true).put("present", false).putNull("value"); root.set("first_named_gain_intervention", gain);
        root.set("stop_intervention", tuple(actor, target).put("action_id", "stop-sway-history214").put("original_action_id", "sway-history214").put("postcondition_verified", false));
        root.putNull("phase_intervention"); env.set("resolved", root); return env;
    }
    private static ObjectNode pendingEnvelope(long actor, long target, String stage) {
        ObjectNode env = StrictJson.object().put("schema", "xar.ck3.active-scheme-sway-formal-private.v1").putNull("resolved");
        ObjectNode p = env.putObject("pending").put("stage", stage).put("action_id", "sway-pending214").put("actor_character_id", actor).put("target_character_id", target)
                .put("pre_capture_epoch", EPOCH).put("pre_container_generation", EPOCH.add(BigInteger.ONE)).put("pre_date_raw", DATE).put("pre_native_revision", REV)
                .put("pre_target_opinion_of_actor", 20).put("episode_run_id", EPISODE);
        if (stage.equals("receipt_pending")) p.putObject("ack").put("opaque_historical_ACK", true);
        if (stage.equals("postcondition_pending")) {
            p.putObject("native_applied_receipt").put("schema", "active-scheme-sway-formal-private-v1").put("stage", "applied").put("action_id", "sway-pending214")
                    .put("actor_character_id", actor).put("target_character_id", target).put("postcondition_verified", true).put("post_capture_epoch", EPOCH.add(BigInteger.ONE))
                    .put("post_date_raw", DATE).put("scheme_instance_id", FULL).put("scheme_instance_generation", 129).put("exact_ck3_build", SwayNativeWire.BUILD).put("exe_sha256", SwayNativeWire.EXE);
        }
        ObjectNode side = p.putObject("native_receipt_source").put("schema", "xar.ck3.sway-receipt-source-frame.v1");
        for (String name : List.of("before", "after")) side.putObject(name).put("actor_character_id", actor).put("episode_run_id", EPISODE);
        return env;
    }
    private static SwayNativeWire.TargetRead current(long actor, long target, long full, String episode) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), REV, BigInteger.valueOf(DATE)), "software:214-frame", REV, episode);
        var observation = new ObservationIdentity("software-machine214", new GameGeneration(214, new PythonOnlyUInt64(new BigInteger("134372140000000000"))), frame, 1);
        var binding = new SwayNativeWire.Binding(observation, "software-session214", BigInteger.ONE, "software-authority-label-only", SwayNativeWire.BUILD, SwayNativeWire.EXE);
        ObjectNode body = StrictJson.object().put("schema", "active-scheme-sway-private-read-v1").put("snapshot_revision", REV).put("capture_epoch", EPOCH.add(BigInteger.TEN))
                .put("container_generation", EPOCH.add(BigInteger.ONE)).put("date_raw", DATE).put("actor_character_id", actor).put("target_character_id", target)
                .put("target_opinion_of_actor", 20).put("active_scheme_count", 1).put("matching_sway_active", true).put("native_complete_can_send", false)
                .put("native_legal_now", false).put("native_failure_classification", "");
        body.putArray("active_sway_instances").addObject().put("scheme_instance_id", full).put("scheme_instance_generation", full >>> 24).put("target_character_id", target)
                .put("progress", 0).put("progress_goal", 100).put("is_exposed", false).put("is_frozen", false);
        ObjectNode packet = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "software-read214").put("ok", true);
        packet.putObject("result").put("step", SwayNativeWire.TARGET + target).put("accepted", true).put("status", "available").put("private_build", true)
                .put("advertised", false).put("backend_id", "native-headless").put("read_only", true).set("active_scheme_sway", body);
        return SwayNativeWire.target(bytes(packet), "software-read214", binding, target);
    }
    private static ObjectNode tuple(long actor, long target) { return StrictJson.object().put("actor_character_id", actor).put("target_character_id", target).put("scheme_instance_id", FULL).put("scheme_instance_generation", 129); }
    private static ObjectNode node(JsonNode root, String pointer) { return (ObjectNode) root.at(pointer); }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static ExactRef ref(byte[] raw) { return new ExactRef("software:history214.json", raw.length, ActionCodec.sha256(raw)); }
    private static SwayLegacyImport.Imported imported(ObjectNode envelope) { byte[] raw = bytes(envelope); return SwayLegacyImport.parse(ref(raw), raw); }
}

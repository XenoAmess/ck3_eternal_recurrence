package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import org.xar.ck3.control.vanilla.schemesway.SwayScheduleWire;

/** Actual retained nonempty file -> historical parser -> durable codec -> ordinary stage and service consumer.
 * Current frames are explicitly synthetic. No test grants current Game/native/restore qualification. */
final class SwayLegacyActualImportTest {
    private static final String MACHINE = "xenoamess-full-tower-eb9d2c1186";
    private static final String ACTUAL_SHA = "6f1da9ee2c0e00839497a650cbcfaba527807342e85cce29d8a357344f55aad9";
    private static final String ACTUAL = "D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/native89-r0104/state/active-scheme-sway-formal-private-v1.json";
    @Test void fullActualFileSurvivesImportCodecAndOrdinaryConsumersWithoutManufacturingCurrentProof() throws Exception {
        byte[] original;
        try (var sourceFile = getClass().getResourceAsStream("/sway/actual-retained-nonempty-ledger.json")) {
            assertNotNull(sourceFile, "whole source graph must include the actual retained original; missing source is failure, never skipped"); original = sourceFile.readAllBytes();
        }
        assertEquals(7682, original.length); assertEquals(ACTUAL_SHA, ActionCodec.sha256(original));
        ExactRef source = new ExactRef(ACTUAL, original.length, ACTUAL_SHA); var imported = SwayLegacyImport.parse(source, original);
        assertTrue(imported.pending().isEmpty()); assertTrue(imported.resolved().isPresent()); var history = imported.resolved().orElseThrow();
        assertEquals(29829, history.identity().actorCharacterId()); assertEquals(34333, history.identity().targetCharacterId()); assertTrue(history.startConsumption().markedConsumed());
        assertEquals("1.20.0.3", StrictJson.parse(history.originalResolved().bytes()).at("/native_receipt/exact_ck3_build").textValue());
        Ledger state = new Ledger(MACHINE, "synthetic:historical-import", Optional.empty(), Optional.empty(), List.of(), Optional.empty(), source, Optional.of(imported));
        Ledger cold = SwayFormalCodec.decode(SwayFormalCodec.encode(state)); assertArrayEquals(original, cold.imported().orElseThrow().original().bytes());
        assertTrue(cold.resolved().isEmpty(), "old JSON cannot mint a current ObservationIdentity or native completion");
        ObservationIdentity before = before(29829, 53290296); var inputs = SwaySessionInputs.project(cold, before);
        assertEquals(history.identity(), inputs.ledger().resolved().orElseThrow().identity()); assertFalse(inputs.ledger().resolved().orElseThrow().terminalObserved());
        var frame = new OrdinarySwaySchedule.Frame(before.frame().snapshotId(), before.frame().revision(), before.frame().identity().nativeRevision(), before.frame().identity().dateRaw(), 29829, true, true, true, OrdinarySwaySchedule.Context.CLEAR);
        var captured = new OrdinarySwayService.Captured(new G2Source(MACHINE, "2026-10-23T19:25:00Z", "1.20.0.4", new ExactRef("synthetic:current-consumer.java", 1, "a".repeat(64))), new OrdinarySwayService.Wrapper(frame.snapshotId(), frame.publicRevision()), OrdinarySwaySchedule.Step.LIFE_ADVANCE, Optional.of(frame), Optional.empty(), new OrdinarySwayService.Capabilities(true, true, true));
        var staged = new OrdinarySwayService().stage(captured, () -> Optional.of(inputs)).staged().orElseThrow(); assertEquals(OrdinarySwaySchedule.Job.OBSERVE_APPLIED, staged.decision().job().orElseThrow());
        final int[] calls = new int[3]; final OrdinarySwaySchedule.State[] saved = new OrdinarySwaySchedule.State[1];
        var result = new OrdinarySwayService().execute(staged, new OrdinarySwayService.ExecutionPort() {
            @Override public Optional<OrdinarySwayService.Inputs> loadInputs() { return Optional.of(inputs); }
            @Override public OrdinarySwayService.FormalResult queryAndConsume(OrdinarySwaySchedule.Frame ignored, long target) { calls[0]++; throw new AssertionError("historical observation must not submit/replay original action"); }
            @Override public OrdinarySwayService.LifecycleResult observeLifecycle(OrdinarySwaySchedule.Frame ignored) { calls[1]++; return new OrdinarySwayService.LifecycleResult(OrdinarySwayService.LifecycleStatus.UNAVAILABLE, json("{\"status\":\"actual_restore_source_required\"}")); }
            @Override public Optional<String> saveScheduler(OrdinarySwaySchedule.State value) { saved[0] = value; return Optional.empty(); }
            @Override public OrdinarySwayService.OrdinaryContinuation executeFreshOrdinary() { calls[2]++; return new OrdinarySwayService.OrdinaryContinuation(json("{\"status\":\"synthetic_fresh_ordinary\"}"), json("{\"status\":\"synthetic_current_plan\"}")); }
        });
        assertInstanceOf(OrdinarySwayService.Continued.class, result); assertArrayEquals(new int[] {0, 1, 1}, calls);
        assertEquals(saved[0], SwayScheduleWire.decodeState(SwayScheduleWire.encodeState(saved[0]))); assertArrayEquals(original, cold.imported().orElseThrow().original().bytes());
    }
    @Test void unknownPendingRoundtripPreservesOriginalAndPreventsNewStart() throws Exception {
        byte[] raw = pending(); ExactRef ref = new ExactRef("synthetic:old-pending.json", raw.length, ActionCodec.sha256(raw)); var imported = SwayLegacyImport.parse(ref, raw);
        Ledger value = new Ledger(MACHINE, "episode:synthetic", Optional.empty(), Optional.empty(), List.of(), Optional.empty(), ref, Optional.of(imported));
        Ledger cold = SwayFormalCodec.decode(SwayFormalCodec.encode(value)); assertTrue(historicalPendingUnresolved(cold)); assertArrayEquals(raw, cold.imported().orElseThrow().original().bytes());
        var read = SwayNativeWire.target(SwayNativeFormalTest.bytes(SwayNativeFormalTest.vector("query")), "fixture-read", SwayNativeFormalTest.binding(73, 7, 53220000), 50331650);
        assertThrows(IllegalArgumentException.class, () -> SwayFormalState.reduce(cold, new StartIntent("sway-should-not-replay", read, MandatoryContext.CLEAR)));
    }
    @Test void pendingRejectsBooleanEpochMissingFieldAndReceiptStageWithoutOriginal() {
        ObjectNode pending = (ObjectNode)StrictJson.parse(pending()).get("pending"); pending.put("pre_capture_epoch", true);
        assertThrows(IllegalArgumentException.class, () -> SwayLegacyImport.pending(SwayLegacyImport.json(pending)));
        pending.put("pre_capture_epoch", 100); pending.remove("pre_container_generation"); assertThrows(IllegalArgumentException.class, () -> SwayLegacyImport.pending(SwayLegacyImport.json(pending)));
        pending.put("pre_container_generation", 900); pending.put("stage", "postcondition_pending"); assertThrows(IllegalArgumentException.class, () -> SwayLegacyImport.pending(SwayLegacyImport.json(pending)));
    }
    @Test void canonicalStoredBytesChunkLargeOriginalAndRejectAlternateChunking() {
        byte[] raw = new byte[18000]; Arrays.fill(raw, (byte)'a'); var chunks = SwayFormalCodec.chunks(raw); assertArrayEquals(raw, SwayFormalCodec.bytes(chunks));
        var changed = StrictJson.object().putArray("parts"); changed.add(chunks.get(0).textValue().substring(1)); changed.add(chunks.get(0).textValue().substring(0, 1)); assertThrows(IllegalArgumentException.class, () -> SwayFormalCodec.bytes(changed));
    }
    private static byte[] pending() { return ("{\"schema\":\"xar.ck3.active-scheme-sway-formal-private.v1\",\"pending\":{\"stage\":\"submission_unresolved\",\"action_id\":\"sway-old-unknown\",\"actor_character_id\":50331649,\"target_character_id\":50331650,\"pre_capture_epoch\":100,\"pre_container_generation\":17922751897147325986,\"pre_date_raw\":53220000,\"pre_native_revision\":7,\"pre_target_opinion_of_actor\":20},\"resolved\":null}").getBytes(StandardCharsets.UTF_8); }
    private static ProjectionJson json(String value) { return ProjectionJson.object(value.getBytes(StandardCharsets.UTF_8), 4096); }
    private static ObservationIdentity before(long actor, long date) { var identity = new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.valueOf(700), BigInteger.valueOf(date)); var frame = new JointBudgetSelector.ProposalFrame(identity, "synthetic:legacy-current", BigInteger.valueOf(701), "synthetic:historical-import"); return new ObservationIdentity(MACHINE, new GameGeneration(707, new PythonOnlyUInt64(new BigInteger("134370000000000707"))), frame, 1); }
}

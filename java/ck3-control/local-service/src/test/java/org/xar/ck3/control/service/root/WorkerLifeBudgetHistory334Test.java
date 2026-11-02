package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.OrdinarySessionResource;

/** Only controlled public report DATA and our own tiny log; no Root, file pair or action authority. */
public final class WorkerLifeBudgetHistory334Test {
    @TempDir Path temporary;
    private static final Instant AT = Instant.parse("2026-11-02T19:00:00Z");
    private static final GameGeneration GAME = new GameGeneration(4_000_000_000L,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "hint-334");
    private static final ExactRef REF = new ExactRef("D:/fixture/not-opened-334", 1, "a".repeat(64));

    @Test void exactLegacyDeferredReportMigratesOnlyItsQualifiedReserveFloor() {
        ObjectNode row = legacy();
        var decoded = StrictJson.parse(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(row, OWNER).orElseThrow().bytes());
        assertEquals("0", decoded.get("saved_life_tail_nanos").textValue());
        assertEquals("905000000000", decoded.get("reserve_floor_nanos").textValue());
        assertEquals(GAME, ProposalLifecycleCodec.decodeObservation(decoded.get("subject")).game());
        for (String field : List.of("dirty_since_save", "attempted_turns", "detail", "last_plan", "session_id")) {
            var changed = row.deepCopy();
            switch (field) {
                case "dirty_since_save" -> changed.put(field, true);
                case "attempted_turns" -> changed.put(field, 1);
                case "detail" -> changed.put(field, "ordinary WALL_TIMEOUT without the exact pre-INTENT marker");
                case "last_plan" -> ((ObjectNode) changed.get(field)).set("before", ProposalLifecycleCodec.observation(frame(12, "episode-1", 480)));
                default -> changed.put(field, "different-session");
            }
            assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(changed, OWNER).isEmpty(), field);
        }
        var notLife = row.deepCopy();
        ((ObjectNode) notLife.get("last_plan").get("final_plan").get("command")).put("operation", "fixture-not-life");
        assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(notLife, OWNER).isEmpty());
    }

    @Test void structuredRowsKeepCompleteOwnerAndHistoricalSubjectButNotAnExactOldPairDate() {
        var row = legacy();
        row.set("life_budget_hint", hint(frame(11, "episode-1", 456), "800000000000", "905000000000"));
        var accepted = RootOrdinaryWorkerMain.lifeBudgetHintFromReport(row, OWNER).orElseThrow();
        assertEquals("800000000000", StrictJson.parse(accepted.bytes()).get("saved_life_tail_nanos").textValue());
        for (ObservationIdentity subject : List.of(frame(12, "episode-1", 456), frame(11, "episode-2", 456), frame(11, "episode-1", 504))) {
            var changed = row.deepCopy(); changed.set("life_budget_hint", hint(subject, "800000000000", "905000000000"));
            assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(changed, OWNER).isEmpty());
        }
        var wrongBirth = row.deepCopy(); wrongBirth.put("game_creation_filetime", "134000000000000002");
        assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(wrongBirth, OWNER).isEmpty());
        var badMetric = row.deepCopy(); ((ObjectNode) badMetric.get("life_budget_hint")).put("saved_life_tail_nanos", "86400000000001");
        assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(badMetric, OWNER).isEmpty());
        var extra = row.deepCopy(); ((ObjectNode) extra.get("life_budget_hint")).put("grant", true);
        assertTrue(RootOrdinaryWorkerMain.lifeBudgetHintFromReport(extra, OWNER).isEmpty());
    }

    @Test void ownedLogTailUsesOnlyCompleteQualifiedRowsAndPreservesAbsence() throws Exception {
        Path log = temporary.resolve("worker-batches.jsonl");
        assertTrue(RootOrdinaryWorkerMain.readLifeBudgetHint(log, OWNER).isEmpty());
        var older = legacy(); older.set("life_budget_hint", hint(frame(11, "episode-1", 456), "700000000000", "0"));
        var latest = legacy(); latest.set("life_budget_hint", hint(frame(11, "episode-1", 480), "800000000000", "0"));
        String complete = new String(FullJsonTree.encode(older, 65_536), StandardCharsets.UTF_8) + "\n{bad-json}\n"
                + new String(FullJsonTree.encode(latest, 65_536), StandardCharsets.UTF_8) + "\n";
        Files.writeString(log, complete + "{\"incomplete_tail\":", StandardCharsets.UTF_8);
        var result = StrictJson.parse(RootOrdinaryWorkerMain.readLifeBudgetHint(log, OWNER).orElseThrow().bytes());
        assertEquals("800000000000", result.get("saved_life_tail_nanos").textValue());
        Files.writeString(log, new String(FullJsonTree.encode(latest, 65_536), StandardCharsets.UTF_8), StandardCharsets.UTF_8);
        assertTrue(RootOrdinaryWorkerMain.readLifeBudgetHint(log, OWNER).isEmpty(), "a record without its terminating newline is not committed telemetry");
        Files.writeString(log, "x".repeat(1_048_577) + "\n", StandardCharsets.UTF_8);
        assertTrue(RootOrdinaryWorkerMain.readLifeBudgetHint(log, OWNER).isEmpty(), "an oversized cut row cannot be pieced together");
    }

    private static ObservationIdentity frame(int actor, String episode, int date) {
        return new ObservationIdentity(OWNER.machineId(), GAME, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.ONE, BigInteger.valueOf(date)),
                "hint-frame-334", BigInteger.ONE, episode), 1);
    }
    private static ObjectNode hint(ObservationIdentity subject, String tail, String floor) {
        var row = StrictJson.object().put("schema", "xar.life-budget-hint/v1"); row.set("owner", OrdinaryCycleTransitions.sessionToJson(OWNER));
        row.set("subject", ProposalLifecycleCodec.observation(subject)); row.put("saved_life_tail_nanos", tail); row.put("reserve_floor_nanos", floor); return row;
    }
    private static ObjectNode legacy() {
        var before = frame(11, "episode-1", 480);
        var source = new G2Source(OWNER.machineId(), AT.toString(), "CONTROLLED-DATA-ONLY", REF);
        var command = new ActionCommand("unissued-hint-life-334", before, source, OWNER.sessionId(), new OperationKey("life-advance"),
                new OpportunityJson.Obj(Map.of()), new ExpectedPostcondition(1, before, source, "controlled-hint-only/v1",
                    List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), AT.plusSeconds(1200));
        var draft = new OrdinaryPolicy.Draft("controlled-policy", "selection", "unissued DATA", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var plan = new PlanTrace(before, List.of(), Optional.of(draft));
        var stat = new FileStatIdentity(BigInteger.ONE, "100", "134000000000000001");
        var pair = new CheckpointPair(new CheckpointPair.FileWitness(REF, stat),
                new CheckpointPair.FileWitness(new ExactRef("D:/fixture/not-opened-driver-334", 1, "b".repeat(64)), stat),
                before, "hint-lineage", 1, "hint-save-334", REF, AT);
        var tick = new SessionClock.Tick(0, AT);
        var report = new BatchReport(OWNER, "controlled-hint-334", BatchReport.Terminal.WALL_TIMEOUT,
                "PRE_INTENT_LIFE_BUDGET_DEFERRED: remaining_nanos=701000000000; reserve_nanos=905000000000; no action INTENT submitted; next batch must freshly observe and plan",
                tick, tick, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), Optional.of(plan), Optional.empty(), Optional.empty(),
                Optional.of(pair), Optional.empty(), 0, 0, false, List.of(), List.of(), List.of());
        return OrdinarySessionResource.report(report);
    }
}

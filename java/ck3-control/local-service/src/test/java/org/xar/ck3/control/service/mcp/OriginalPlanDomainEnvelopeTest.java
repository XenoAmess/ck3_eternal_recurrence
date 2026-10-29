package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.root.RootRuntimeDomainSettings.PlanFlags;

/** Original held software DATA -> shared request/trace -> actual envelope producer -> strict cold JSON.
 * No Core/private Stage or material-proof constructors are fabricated. */
final class OriginalPlanDomainEnvelopeTest {
    private static final PlanFlags OFF = new PlanFlags(false, false, false, false, false, false, false);
    private static final PlanFlags ON = new PlanFlags(true, true, true, true, true, true, false);
    private static Obj data(String json) {
        return DriverJson.object(json.getBytes(StandardCharsets.UTF_8), RawJson.MAXIMUM_BYTES);
    }
    private static PlanningRequest request(boolean opening, List<Obj> rows, String revision) {
        BigInteger rev = new BigInteger(revision);
        var game = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100)));
        var before = new ObservationIdentity("software-plan-envelope", game,
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), rev,
                BigInteger.valueOf(53217264)), "native:" + revision, rev, "native-29829-2bc2d599f7f9"), 1);
        var source = new G2Source(before.machineId(), "2026-10-24T00:00:00Z", "software-only",
            new ExactRef("software-source", 1, "a".repeat(64)));
        Obj snapshot = data("{\"snapshot_id\":\"native:" + revision + "\",\"revision\":" + revision
            + ",\"native_revision\":" + revision + ",\"date_raw\":53217264,\"episode_run_id\":\"native-29829-2bc2d599f7f9\","
            + "\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":29829},\"active_wars\":[{}],\"player_armies\":[]}");
        var observed = new PlanningObservation(snapshot, rows, Set.of(), Set.of(), Optional.empty(),
            List.of(), Optional.empty(), Optional.empty(), opening);
        return new PlanningRequest(before, source, "software-only-session",
            Instant.parse("2026-10-24T00:01:00Z"), observed);
    }

    private static PlanningResult result(PlanningRequest original, OrdinaryPolicy.Kind kind,
            String phase, PlanningStage... stages) {
        var visits = java.util.Arrays.stream(stages).map(stage -> new PlanTrace.StageVisit(stage,
            PlanTrace.Outcome.KEPT, "actual software source boundary", Optional.empty(), Optional.empty())).toList();
        var detail = data("{\"source_owned\":{\"cost\":-0.0,\"future\":null},\"phase\":\"" + phase + "\"}");
        var draft = new OrdinaryPolicy.Draft("original-source-parity", phase, "retain original envelope DATA",
            kind, Optional.empty(), OrdinaryPolicy.Purpose.READ_ONLY, Optional.empty(), detail);
        var trace = new PlanTrace(original.before(), visits, Optional.of(draft));
        return new PlanningResult.ReadOnlyWait(original.before(), draft.reason(), trace);
    }
    private static Obj root(String revision, String government) {
        return data("{\"command\":\"query-campaign-root-context-v1\",\"ok\":true,\"result\":{\"campaign_root_context\":{"
            + "\"status\":\"available\",\"snapshot_revision\":" + revision
            + ",\"date_raw\":53217264,\"player_character_id\":29829,\"government\":{\"key\":\"" + government
            + "\",\"flags\":[\"government_is_feudal\"]},\"council\":{\"status\":\"available\",\"positions\":[{"
            + "\"position_key\":\"councillor_steward\",\"incumbent_character_id\":200,\"task_key\":\"task_collect_taxes\",\"frozen\":false}]}}}}");
    }
    private static Obj pending(String status, String episode) {
        return data("{\"command\":\"private-select-player-lifestyle-stock-focus-v1\",\"ok\":false,\"result\":{"
            + "\"status\":\"" + status + "\",\"episode_run_id\":\"" + episode
            + "\",\"kind\":\"focus\",\"action_request_id\":\"life-focus-original\",\"unknown_extra\":{\"x\":1.2500e-7}}}");
    }
    @Test void disabledFlagsRetainExplicitNullUntilTheirActualConsumerPopsThem() {
        var request = request(false, List.of(), "1");
        var actual = result(request, OrdinaryPolicy.Kind.ORDINARY, "ordinary", PlanningStage.ORDINARY_CORE);
        var projected = OriginalPlanDomainEnvelope.project(request, actual, OFF);
        assertEquals(OriginalPlanDomainEnvelope.Branch.ORDINARY, projected.branch());
        assertEquals(13, projected.beforeConsumers().members().size());
        assertEquals(12, projected.survivingTopLevel().members().size());
        projected.survivingTopLevel().members().values().forEach(value -> assertEquals(Nil.INSTANCE, value));
        assertEquals(projected.survivingTopLevel(),
            DriverJson.object(OpportunityJson.encode(projected.survivingTopLevel()), RawJson.MAXIMUM_BYTES));
    }
    @Test void windowAndPendingEarlyReturnsDoNotPublishUnusedDomainSnapshots() {
        var request = request(false, List.of(), "1");
        var window = result(request, OrdinaryPolicy.Kind.FOREGROUND, "window",
            PlanningStage.TERMINAL_AND_FOREGROUND_WINDOWS);
        assertTrue(OriginalPlanDomainEnvelope.produce(request, window, ON).members().isEmpty());
        assertTrue(OriginalPlanDomainEnvelope.branch(request, window).commonAnnotations());
        var pending = result(request, OrdinaryPolicy.Kind.MATERIAL_RECEIPT, "pending_material_independent_receipt",
            PlanningStage.PENDING_MATERIAL_PUBLICATION);
        assertTrue(OriginalPlanDomainEnvelope.produce(request, pending, ON).members().isEmpty());
        assertFalse(OriginalPlanDomainEnvelope.branch(request, pending).commonAnnotations());
    }
    @Test void openingRetainsItsThreeExactInputsIncludingFalseFlagNulls() {
        var request = request(true, List.of(), "1");
        var actual = result(request, OrdinaryPolicy.Kind.OPENING_FOCUS, "initial_lifestyle_focus_already_present",
            PlanningStage.OPENING_LIFESTYLE_FOCUS);
        var flags = new PlanFlags(false, true, true, true, true, true, true);
        var projected = OriginalPlanDomainEnvelope.project(request, actual, flags);
        assertEquals(Set.of("_private_lifestyle_scope_v1", "_private_lifestyle_pending_v1",
            "_private_lifestyle_war_frame_v1"), projected.survivingTopLevel().members().keySet());
        projected.survivingTopLevel().members().values().forEach(value -> assertEquals(Nil.INSTANCE, value));
        // consumption-query phase alone did not call the helper which pops these three fields.
        var consumption = result(request, OrdinaryPolicy.Kind.OPENING_FOCUS, "initial_lifestyle_focus_consumption",
            PlanningStage.OPENING_LIFESTYLE_FOCUS);
        assertEquals(projected.survivingTopLevel(), OriginalPlanDomainEnvelope.produce(request, consumption, flags));
    }
    @Test void actualSameFrameSharedScopeAndUnknownPendingBodySurviveOpeningSerdeWithoutProofUpgrade() {
        String maximum = "18446744073709551615";
        String episode = "native-29829-2bc2d599f7f9";
        Obj originalPending = pending("action_state_unknown", episode);
        var request = request(true, List.of(root(maximum, "feudal_government"), originalPending), maximum);
        var actual = result(request, OrdinaryPolicy.Kind.OPENING_FOCUS, "initial_lifestyle_focus_observation_red",
            PlanningStage.OPENING_LIFESTYLE_FOCUS);
        var flags = new PlanFlags(true, false, false, false, false, false, true);
        var projected = OriginalPlanDomainEnvelope.project(request, actual, flags);
        Obj scope = (Obj) projected.survivingTopLevel().get("_private_lifestyle_scope_v1");
        assertEquals(new Text("admitted"), scope.get("status"));
        assertEquals(new IntegerValue(new BigInteger(maximum)), scope.get("snapshot_revision"));
        assertEquals(new Bool(true), scope.get("collect_taxes_active"));
        assertSame(originalPending.get("result"), projected.survivingTopLevel().get("_private_lifestyle_pending_v1"));
        assertEquals(Nil.INSTANCE, projected.survivingTopLevel().get("_private_lifestyle_war_frame_v1"));
        String wire = new String(OpportunityJson.encode(projected.survivingTopLevel()), StandardCharsets.UTF_8);
        assertTrue(wire.contains("1.2500e-7"));
        assertEquals(projected.survivingTopLevel(), DriverJson.object(wire.getBytes(StandardCharsets.UTF_8), RawJson.MAXIMUM_BYTES));
        assertEquals(originalPending.get("result"), projected.survivingTopLevel().get("_private_lifestyle_pending_v1"));
    }
    @Test void fullOrdinaryTracePopsAllPrivateInputsAndPreservesTheExactInnerPlan() {
        var request = request(false, List.of(root("1", "feudal_government")), "1");
        var actual = result(request, OrdinaryPolicy.Kind.ORDINARY, "ordinary",
            PlanningStage.ORDINARY_CORE, PlanningStage.M5_JOINT_PEACETIME, PlanningStage.LIFESTYLE,
            PlanningStage.FACTION_GIFT, PlanningStage.CONSTRUCTION, PlanningStage.FAMILY_AND_EDUCATION,
            PlanningStage.COUNCIL);
        Obj beforeDetail = actual.trace().finalPlan().orElseThrow().detail();
        var projected = OriginalPlanDomainEnvelope.project(request, actual, ON);
        assertSame(request.observations().snapshot(), projected.beforeConsumers().get("_private_m5_snapshot_v1"));
        assertEquals(request.observations().history(), ((Arr) projected.beforeConsumers().get("_private_council_history_v1")).items());
        assertTrue(projected.survivingTopLevel().members().isEmpty());
        assertSame(beforeDetail, actual.trace().finalPlan().orElseThrow().detail());
        assertEquals(data("{\"source_owned\":{\"cost\":-0.0,\"future\":null},\"phase\":\"ordinary\"}"), beforeDetail);
    }
    @Test void earlyM5BoundaryRetainsOnlyConsumersWhichActuallyHaveNotRun() {
        var request = request(false, List.of(), "1");
        var actual = result(request, OrdinaryPolicy.Kind.ORDINARY, "m5_early",
            PlanningStage.ORDINARY_CORE, PlanningStage.M5_JOINT_PEACETIME);
        var projected = OriginalPlanDomainEnvelope.project(request, actual, ON);
        assertFalse(projected.survivingTopLevel().members().containsKey("_private_m5_snapshot_v1"));
        assertTrue(projected.survivingTopLevel().get("_private_council_snapshot_v1") instanceof Obj);
        assertTrue(projected.survivingTopLevel().get("_private_lifestyle_war_frame_v1") instanceof Arr);
        assertTrue(projected.survivingTopLevel().get("_private_construction_history_v1") instanceof Arr);
    }
    @Test void reversePendingSelectionKeepsEpisodeAndAppliedReceiptSemanticsWithoutAuthority() {
        var request = request(true, List.of(pending("action_state_unknown", "foreign-episode")), "1");
        var flags = new PlanFlags(true, false, false, false, false, false, true);
        var actual = result(request, OrdinaryPolicy.Kind.OPENING_FOCUS, "opening", PlanningStage.OPENING_LIFESTYLE_FOCUS);
        assertEquals(Nil.INSTANCE, OriginalPlanDomainEnvelope.produce(request, actual, flags).get("_private_lifestyle_pending_v1"));
        String episode = request.before().frame().episodeRunId();
        Obj receipt = data("{\"command\":\"private-query-player-lifestyle-receipt-v1\",\"result\":{"
            + "\"episode_run_id\":\"" + episode + "\",\"status\":\"applied\"}}");
        var settled = request(true, List.of(pending("action_state_unknown", episode), receipt), "1");
        var after = result(settled, OrdinaryPolicy.Kind.OPENING_FOCUS, "opening", PlanningStage.OPENING_LIFESTYLE_FOCUS);
        assertEquals(Nil.INSTANCE, OriginalPlanDomainEnvelope.produce(settled, after, flags).get("_private_lifestyle_pending_v1"));
        // This deliberately matches the old selector's DATA view. No material receipt is issued.
    }
    @Test void foreignFrameAndWrongActualOpeningFlagFailBeforePublicProjection() {
        var request = request(false, List.of(), "1");
        var foreign = request(false, List.of(), "2");
        assertThrows(IllegalArgumentException.class, () -> OriginalPlanDomainEnvelope.produce(request,
            result(foreign, OrdinaryPolicy.Kind.ORDINARY, "ordinary", PlanningStage.ORDINARY_CORE), OFF));
        var opening = new PlanFlags(false, false, false, false, false, false, true);
        assertThrows(IllegalArgumentException.class, () -> OriginalPlanDomainEnvelope.produce(request,
            result(request, OrdinaryPolicy.Kind.ORDINARY, "ordinary", PlanningStage.ORDINARY_CORE), opening));
    }
}

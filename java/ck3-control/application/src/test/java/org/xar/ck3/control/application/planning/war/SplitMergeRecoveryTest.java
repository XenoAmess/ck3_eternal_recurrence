package org.xar.ck3.control.application.planning.war;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.Purpose;
import org.xar.ck3.control.application.planning.war.SplitMergeRecovery.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;

final class SplitMergeRecoveryTest {
  private static final RouteAuditPort CLEAR = (route, origin, target) ->
      MilitaryRouteGeometry.geometry(route, origin, target, List.of());
  private static final Set<String> STEPS = Set.of("merge-armies-0-with-7", "preview-move-army-0-to-77", "life-advance");

  @Test void actualSplitProducerFeedsBothDecisionSitesAndPreservesPublicZero() {
    for (int original : List.of(0, 7)) {
      int sibling = original == 0 ? 7 : 0;
      State state = collect(frame(army(original, 20, "[77]"), army(sibling, 20, "[77]")),
          List.of(split(original, "")));
      assertEquals(SplitStatus.READY_TO_MERGE, state.split().orElseThrow().status());
      assertInstanceOf(Keep.class, SplitMergeRecovery.beforeStrength(state));
      Select decision = assertInstanceOf(Select.class, late(state, Set.of(original, sibling), Set.of(),
          Set.of("merge-armies-" + original + "-with-" + sibling), CLEAR));
      assertEquals("native_war_merge_recovery", decision.phase());
      assertEquals("merge-armies-" + original + "-with-" + sibling, decision.selectedStep().value());
      assertEquals(Purpose.WORLD_ACTION, decision.purpose());
    }
  }

  @Test void splitIdentityUsesOneExactDeltaAndNeverRanksSoldiersOrIds() {
    State ambiguous = collect(frame(army(0, 20, "[]"), army(7, 20, "[]"), army(9, 20, "[]")),
        List.of(split(0, "")));
    assertEquals(SplitStatus.SPLIT_IDENTITY_PENDING, ambiguous.split().orElseThrow().status());
    Hold fence = assertInstanceOf(Hold.class, SplitMergeRecovery.beforeStrength(ambiguous));
    assertEquals("native_war_merge_recovery_blocked", fence.phase());
    State inconsistent = collect(frame(army(0, 20, "[]"), army(7, 20, "[]"), army(9, 20, "[]")),
        List.of(split(0, ",\"sibling_army_id\":7")));
    assertEquals(SplitStatus.SPLIT_ARMY_SET_INCONSISTENT, inconsistent.split().orElseThrow().status());
  }

  @Test void realBoundaryRejectsBoolFloatStringNegativeOverflowAndNoncanonicalCommands() {
    for (String token : List.of("true", "7.0", "\"7\"", "-1", "2147483648")) {
      Obj malformed = split(0, ",\"sibling_army_id\":" + token);
      assertTrue(collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(malformed)).split().isEmpty());
      Obj badBefore = obj("{\"command\":\"split-army-half-0\",\"ok\":true,\"result\":{\"war_action\":"
          + "{\"status\":\"split_submitted\",\"source_army_id\":0,\"player_army_ids_before\":[" + token + "]}}}");
      assertTrue(collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(badBefore)).split().isEmpty());
    }
    for (String command : List.of("split-army-half-00", "split-army-half-+0", "split-army-half-2147483648")) {
      assertTrue(collect(frame(army(0, 20, "[]"), army(7, 20, "[]")),
          List.of(split(0, "").with("command", new Text(command)))).split().isEmpty());
    }
  }

  @Test void pendingFailedAndContradictoryMergeNeverResubmitOrAdvance() {
    for (Obj merge : List.of(merge(true, "{\"status\":\"merge_submitted\"}"),
        merge(false, "{\"status\":\"merge_submitted\"}"),
        merge(true, "{\"status\":\"merge_applied\"}"))) {
      State state = collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(split(0, ""), merge));
      Hold decision = assertInstanceOf(Hold.class, SplitMergeRecovery.beforeStrength(state));
      assertEquals("native_war_merge_recovery_blocked", decision.phase());
      assertEquals("fresh-paused-merge-postcondition", decision.requiredStep().orElseThrow().value());
    }
  }

  @Test void separatedPairAndRetreatFlagKeepOriginalRendezvousPriority() {
    State separated = collect(frame(army(0, 20, "[]"), army(7, 31, "[]")), List.of(split(0, "")));
    assertEquals("native_war_merge_rendezvous_blocked",
        assertInstanceOf(Hold.class, late(separated, Set.of(9), Set.of(), STEPS, CLEAR)).phase());
    Obj retreat = army(7, 20, "[]").with("army_state", new Text("embarked")).with("retreating", new Bool(true));
    State waiting = collect(frame(army(0, 20, "[]"), retreat), List.of(split(0, "")));
    assertEquals(SplitStatus.MERGE_WAITING_FOR_IDLE, waiting.split().orElseThrow().status());
    assertInstanceOf(Hold.class, late(waiting, Set.of(), Set.of(), STEPS, CLEAR));
    assertInstanceOf(Keep.class, late(waiting, Set.of(9), Set.of(), STEPS, CLEAR));
  }

  @Test void unrelatedUnsafeArmyKeepsHigherPriorityAndAbsentMergeIsUnsupported() {
    State ready = collect(frame(army(0, 20, "[]"), army(7, 20, "[]"), army(9, 20, "[]")),
        List.of(obj("{\"command\":\"split-army-half-0\",\"ok\":true,\"result\":{\"war_action\":"
            + "{\"status\":\"split_submitted\",\"source_army_id\":0,\"player_army_ids_before\":[0,9]}}}")));
    assertInstanceOf(Keep.class, late(ready, Set.of(9), Set.of(), STEPS, CLEAR));
    assertEquals("native_war_merge_recovery_unsupported",
        assertInstanceOf(Hold.class, late(ready, Set.of(0), Set.of(7), Set.of("life-advance"), CLEAR)).phase());
    assertThrows(NullPointerException.class, () -> late(ready, null, Set.of(), STEPS, CLEAR));
  }

  @Test void mergeInvalidatesOldSameDatePreviewAndWrongLeaseCannotRepairIt() {
    Obj old = preview("[77]");
    State merged = collect(frame(army(0, 20, "[77]")), List.of(old, split(0, ""), merge(true, "{\"status\":\"merge_submitted\"}")));
    assertInstanceOf(Keep.class, SplitMergeRecovery.beforeStrength(merged));
    Select read = assertInstanceOf(Select.class, late(merged, Set.of(), Set.of(), STEPS, CLEAR));
    assertEquals("native_war_merge_route_preview", read.phase());
    assertEquals(Purpose.READ_ONLY, read.purpose());
    Obj stale = preview("[77]").with("result", result(preview("[77]")).with("queried_connection_generation", new IntegerValue(java.math.BigInteger.valueOf(8))));
    State wrongLease = collect(frame(army(0, 20, "[77]")), List.of(split(0, ""), merge(true, "{\"status\":\"merge_submitted\"}"), stale));
    assertEquals("native_war_merge_route_preview",
        assertInstanceOf(Select.class, late(wrongLease, Set.of(), Set.of(), STEPS, CLEAR)).phase());
  }

  @Test void exactPostMergeRouteUsesSharedGeometryBeforeOneBoundedAdvance() {
    List<Obj> history = List.of(split(0, ""), merge(true, "{\"status\":\"merge_submitted\"}"), preview("[20,77]"));
    State state = collect(frame(army(0, 20, "[20,77]")), history);
    Select progress = assertInstanceOf(Select.class, late(state, Set.of(), Set.of(), STEPS, CLEAR));
    assertEquals("native_war_merge_route_progress", progress.phase());
    assertEquals("life-advance", progress.selectedStep().value());
    assertEquals(Purpose.DATE_ADVANCE, progress.purpose());
    RouteAuditPort hostile = (route, origin, target) -> MilitaryRouteGeometry.geometry(route, origin, target,
        List.of(new Enemy(9, java.util.Optional.of(77), java.util.Optional.empty(), List.of(), TacticalState.OTHER)));
    assertEquals("native_war_merge_route_preview_unsafe",
        assertInstanceOf(Hold.class, late(state, Set.of(), Set.of(), STEPS, hostile)).phase());
    assertEquals("native_war_merge_route_progress_unsupported",
        assertInstanceOf(Hold.class, late(state, Set.of(), Set.of(), Set.of(), CLEAR)).phase());
  }

  @Test void mismatchedRetainedRouteCannotBecomeSameTargetMoveReplay() {
    State state = collect(frame(army(0, 20, "[77]")), List.of(split(0, ""),
        merge(true, "{\"status\":\"merge_submitted\"}"), preview("[31,77]")));
    Hold blocked = assertInstanceOf(Hold.class, late(state, Set.of(), Set.of(), STEPS, CLEAR));
    assertEquals("native_war_merge_route_refresh_blocked", blocked.phase());
    assertEquals("move-army-0-to-77", blocked.requiredStep().orElseThrow().value());
    State deferred = collect(frame(army(0, 20, "[77]")), List.of(split(0, ""),
        merge(true, "{\"status\":\"merge_submitted\"}"),
        preview("[77]").with("result", result(preview("[77]")).with("route_preview",
            OpportunityJson.object(result(preview("[77]")).get("route_preview"), "preview").with("status", new Text("deferred"))))));
    assertEquals("native_war_merge_route_preview_unsafe",
        assertInstanceOf(Hold.class, late(deferred, Set.of(), Set.of(), STEPS, CLEAR)).phase());
  }

  @Test void genericMergeRequiresPersistedIndependentPostconditionNotObservedRemoval() {
    Obj receipt = generic(false);
    State pending = collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(receipt));
    assertEquals(MergeStatus.PENDING_OBSERVED, pending.merge().orElseThrow().status());
    assertInstanceOf(Hold.class, SplitMergeRecovery.beforeStrength(pending));
    State removal = collect(frame(army(0, 20, "[]")), List.of(receipt));
    assertEquals(MergeStatus.POSTCONDITION_OBSERVED_UNCONSUMED, removal.merge().orElseThrow().status());
    assertInstanceOf(Hold.class, SplitMergeRecovery.beforeStrength(removal));
    State durable = collect(frame(army(0, 20, "[]")), List.of(generic(true)));
    assertEquals(MergeStatus.APPLIED, durable.merge().orElseThrow().status());
    assertInstanceOf(Keep.class, SplitMergeRecovery.beforeStrength(durable));
  }

  @Test void genericFailedDuplicatesStayAttachedAndDifferentPairFailureWins() {
    Obj failure = merge(false, "{}");
    State duplicate = collect(frame(army(0, 20, "[]")), List.of(generic(true), failure, failure));
    assertEquals(MergeStatus.APPLIED, duplicate.merge().orElseThrow().status());
    assertEquals(2, OpportunityJson.array(duplicate.merge().orElseThrow().detail().get("duplicate_attempts"), "duplicates").size());
    State different = collect(frame(army(0, 20, "[]")), List.of(generic(true),
        failure.with("command", new Text("merge-armies-0-with-9"))));
    assertEquals(MergeStatus.SUBMISSION_FAILED, different.merge().orElseThrow().status());
    assertInstanceOf(Hold.class, SplitMergeRecovery.beforeStrength(different));
  }

  @Test void actualAutoTurnRootResultWinsAndSuccessfulRestoreClosesOldLifecycle() {
    Obj wrapped = obj("{\"command\":\"auto-run 1\",\"ok\":true,\"result\":{\"turns\":["
        + "{\"command\":\"auto-turn\",\"ok\":true,\"result\":{\"war_action\":{\"status\":\"split_submitted\","
        + "\"source_army_id\":0,\"player_army_ids_before\":[0]},\"auto_turn\":{\"selected_step\":\"split-army-half-0\","
        + "\"result\":{\"war_action\":{\"status\":\"ignored-plan-payload\"}}}}}]}}");
    State state = collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(wrapped));
    assertEquals(SplitStatus.READY_TO_MERGE, state.split().orElseThrow().status());
    Obj restore = obj("{\"command\":\"restore-checkpoint\",\"ok\":true}");
    State restored = collect(frame(army(0, 20, "[]")), List.of(wrapped, restore));
    assertTrue(restored.split().isEmpty()); assertTrue(restored.merge().isEmpty());
    assertInstanceOf(Keep.class, SplitMergeRecovery.beforeStrength(restored));
    Obj failedRestore = restore.with("ok", new Bool(false));
    assertTrue(collect(frame(army(0, 20, "[]"), army(7, 20, "[]")), List.of(wrapped, failedRestore)).split().isPresent());
  }

  private static State collect(Obj snapshot, List<Obj> history) { return SplitMergeRecovery.collect(snapshot, history); }
  private static Resolution late(State state, Set<Integer> unsafe, Set<Integer> threatened, Set<String> steps, RouteAuditPort audit) {
    return SplitMergeRecovery.afterRetreat(state, unsafe, threatened, steps.stream().map(OperationKey::new).collect(java.util.stream.Collectors.toSet()), audit);
  }
  private static Obj obj(String json) { return OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)), "test"); }
  private static Obj result(Obj row) { return OpportunityJson.object(row.get("result"), "result"); }
  private static Obj frame(Obj... armies) {
    return obj("{\"snapshot_id\":\"s2\",\"revision\":12,\"native_revision\":22,\"episode_run_id\":\"ep\","
        + "\"date_raw\":24000,\"paused\":true,\"map_ready\":true,\"diagnostics\":{\"connection_generation\":7},"
        + "\"active_wars\":[{\"war_objective_province_ids\":[77]}]}")
        .with("player_armies", new Arr(List.of(armies)));
  }
  private static Obj army(int id, int province, String route) {
    return obj("{\"army_id\":" + id + ",\"controllable\":true,\"owner_character_id\":707,\"current_province_id\":"
        + province + ",\"move_target_province_id\":77,\"route_province_ids\":" + route + ",\"army_state\":\"moving\"}");
  }
  private static Obj split(int original, String extra) {
    return obj("{\"command\":\"split-army-half-" + original + "\",\"ok\":true,\"result\":{\"war_action\":"
        + "{\"status\":\"split_submitted\",\"source_army_id\":" + original + ",\"submitted_date_raw\":24000,"
        + "\"player_army_ids_before\":[" + original + "]" + extra + "}}}");
  }
  private static Obj merge(boolean ok, String action) {
    return obj("{\"command\":\"merge-armies-0-with-7\",\"ok\":" + ok + ",\"result\":{\"war_action\":" + action + "}}");
  }
  private static Obj preview(String route) {
    return obj("{\"command\":\"preview-move-army-0-to-77\",\"ok\":true,\"result\":{"
        + "\"queried_snapshot_id\":\"s2\",\"queried_revision\":12,\"queried_native_revision\":22,"
        + "\"queried_connection_generation\":7,\"queried_episode_run_id\":\"ep\",\"route_preview\":{"
        + "\"status\":\"available\",\"army_id\":0,\"origin_province_id\":20,\"target_province_id\":77,"
        + "\"previewed_date_raw\":24000,\"route_province_ids\":" + route + "}}}");
  }
  private static Obj generic(boolean applied) {
    return merge(true, "{\"status\":\"" + (applied ? "merge_applied" : "merge_submitted") + "\","
        + "\"destination_army_id\":0,\"source_army_id\":7,\"player_army_ids_before\":[0,7],\"submitted_date_raw\":24000,"
        + "\"submitted_snapshot_id\":\"s1\",\"submitted_public_revision\":10,\"submitted_native_revision\":20,"
        + "\"submitted_episode_run_id\":\"ep\",\"destination_owner_character_id\":707,\"destination_province_id\":20,"
        + "\"source_owner_character_id\":707,\"source_province_id\":20"
        + (applied ? ",\"postcondition_verified\":true,\"source_army_id_absent\":true,\"observed_snapshot_id\":\"s2\","
          + "\"observed_public_revision\":12,\"observed_native_revision\":22,\"observed_date_raw\":24000,"
          + "\"observed_episode_run_id\":\"ep\",\"player_army_ids_after\":[0]" : "") + "}");
  }
}

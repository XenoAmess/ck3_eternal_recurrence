package org.xar.ck3.control.application.planning.war;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Pattern;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy.Purpose;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.Audit;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.Status;

/**
* Actual ordinary-war split/merge collector and the two original decision sites.
* Source: strategy.py:10450-10498,11191-11368,20834-21151 and
* bridge/war_contract.py:3090-3394. This producer proposes no independent dispatch.
*/
public final class SplitMergeRecovery {
  private SplitMergeRecovery() { }
  private static final BigInteger MAX_UNIT = BigInteger.valueOf(Integer.MAX_VALUE);
  private static final Pattern SPLIT = Pattern.compile("split-army-half-(0|[1-9][0-9]*)");
  private static final Pattern MERGE = Pattern.compile("merge-armies-(0|[1-9][0-9]*)-with-(0|[1-9][0-9]*)");
  private static final Pattern PREVIEW = Pattern.compile("preview-move-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)");

  public enum SplitStatus {
    SPLIT_IDENTITY_PENDING, SPLIT_ARMY_SET_INCONSISTENT, MERGE_PENDING, MERGE_FAILED,
    MERGE_POSTCONDITION_INCONSISTENT, MERGE_COMPLETED, MERGE_REQUIRES_RENDEZVOUS,
    MERGE_WAITING_FOR_IDLE, READY_TO_MERGE;
    public String wire() { return name().toLowerCase(Locale.ROOT); }
  }
  public enum MergeStatus {
    SUBMISSION_FAILED, RECEIPT_INVALID, POSTCONDITION_UNAVAILABLE, POSTCONDITION_INCONSISTENT,
    POSTCONDITION_OBSERVED_UNCONSUMED, PENDING_OBSERVED, PENDING_SAME_FRAME,
    POSTCONDITION_UNBOUND, APPLIED;
    public String wire() { return name().toLowerCase(Locale.ROOT); }
  }
  public record Split(SplitStatus status, int originalArmyId, OptionalInt siblingArmyId,
            Optional<OperationKey> mergeStep, Obj detail) {
    public Split {
      Objects.requireNonNull(status); unit(originalArmyId); Objects.requireNonNull(siblingArmyId);
      siblingArmyId.ifPresent(SplitMergeRecovery::unit); Objects.requireNonNull(mergeStep);
      Objects.requireNonNull(detail);
      StrictJson.require(siblingArmyId.isEmpty() || siblingArmyId.getAsInt() != originalArmyId,
          "distinct exact split pair required");
    }
  }
  public record MergeLifecycle(MergeStatus status, OperationKey mergeStep, Obj detail) {
    public MergeLifecycle { Objects.requireNonNull(status); Objects.requireNonNull(mergeStep); Objects.requireNonNull(detail); }
  }
  private record Pair(int destination, int source) { }
  private record HistoryRow(String command, boolean ok, Optional<Obj> result, Obj raw) { }
  private record Army(int id, Obj raw) { }
  private record ArmySet(List<Army> armies, boolean identitiesValid) {
    private ArmySet { armies = List.copyOf(armies); }
  }
  /** Only collect can create this immutable same-snapshot history view. */
  public static final class State {
    private final Obj snapshot;
    private final List<HistoryRow> history;
    private final List<Army> armies;
    private final Optional<Split> split;
    private final Optional<MergeLifecycle> merge;
    private State(Obj snapshot, List<HistoryRow> history, List<Army> armies,
           Optional<Split> split, Optional<MergeLifecycle> merge) {
      this.snapshot = snapshot; this.history = List.copyOf(history); this.armies = List.copyOf(armies);
      this.split = split; this.merge = merge;
    }
    public Optional<Split> split() { return split; }
    public Optional<MergeLifecycle> merge() { return merge; }
  }
  public sealed interface Resolution permits Keep, Hold, Select { }
  public record Keep() implements Resolution { }
  public record Hold(String phase, Optional<OperationKey> requiredStep, String reason, Obj detail) implements Resolution {
    public Hold { StrictJson.text(phase); Objects.requireNonNull(requiredStep); StrictJson.text(reason); Objects.requireNonNull(detail); }
  }
  public record Select(String phase, OperationKey selectedStep, Purpose purpose, String reason, Obj detail) implements Resolution {
    public Select {
      StrictJson.text(phase); Objects.requireNonNull(selectedStep); Objects.requireNonNull(purpose);
      StrictJson.text(reason); Objects.requireNonNull(detail);
    }
  }
  /** WarCore captures its current complete hostile roster in the shared geometry producer. */
  @FunctionalInterface
  public interface RouteAuditPort { Audit audit(List<Integer> route, int originProvinceId, int targetProvinceId); }

  public static State collect(PlanningRequest request) {
    Objects.requireNonNull(request);
    return collect(request.observations().snapshot(), request.observations().history());
  }
  /** Existing immutable JSON is the sole dynamic boundary; no classified status is accepted from a caller. */
  public static State collect(Obj snapshot, List<Obj> rawHistory) {
    Objects.requireNonNull(snapshot); Objects.requireNonNull(rawHistory);
    DriverJson.object(DriverJson.encode(snapshot), DriverJson.MAX_NATIVE_BYTES);
    rawHistory.forEach(row -> DriverJson.object(DriverJson.encode(row), DriverJson.MAX_NATIVE_BYTES));
    List<HistoryRow> history = historyAfterRestore(rawHistory);
    ArmySet controlled = controlled(snapshot);
    Optional<Split> split = recover(history, controlled, objectives(snapshot));
    Optional<MergeLifecycle> merge = split.isPresent() ? Optional.empty() : latestMerge(history, snapshot);
    return new State(snapshot, history, controlled.armies(), split, merge);
  }

  /** strategy.py:10456, after global route completeness and before the strength query. */
  public static Resolution beforeStrength(State state) {
    Objects.requireNonNull(state);
    if (state.split.isPresent()) {
      Split split = state.split.orElseThrow();
      if (Set.of(SplitStatus.SPLIT_IDENTITY_PENDING, SplitStatus.SPLIT_ARMY_SET_INCONSISTENT,
          SplitStatus.MERGE_PENDING, SplitStatus.MERGE_FAILED,
          SplitStatus.MERGE_POSTCONDITION_INCONSISTENT).contains(split.status()))
        return hold("native_war_merge_recovery_blocked", "fresh-paused-merge-postcondition",
            "the latest exact split/merge lifecycle is pending, failed, or inconsistent; keep the map paused and do not resubmit or advance time",
            evidence("merge_recovery", split.detail()));
    } else if (state.merge.isPresent() && state.merge.orElseThrow().status() != MergeStatus.APPLIED) {
      return hold("native_war_merge_result_pending", "fresh-paused-merge-postcondition",
          "the latest merge receipt lacks an independently published exact source-removal postcondition; keep the map paused and do not resubmit or advance time",
          evidence("merge_result_lifecycle", state.merge.orElseThrow().detail()));
    }
    return new Keep();
  }

  /** strategy.py:11191, after higher-priority combat/retreat and before assault progress.
  * Both sets must be completed current WarCore audits. UNKNOWN is not an empty set.
  */
  public static Resolution afterRetreat(PlanningRequest request, State state,
      Set<Integer> unsafeArmyIds, Set<Integer> threatenedStationaryArmyIds, RouteAuditPort routeAudit) {
    Objects.requireNonNull(request);
    StrictJson.require(state.snapshot.equals(request.observations().snapshot()), "split state crossed planner frame");
    return afterRetreat(state, unsafeArmyIds, threatenedStationaryArmyIds, request.observations().actionSteps(), routeAudit);
  }

  /** The domain seam used by WarCore; admission of actual action commands remains at its single factory. */
  public static Resolution afterRetreat(State state, Set<Integer> unsafeArmyIds,
      Set<Integer> threatenedStationaryArmyIds, Set<OperationKey> availableSteps, RouteAuditPort routeAudit) {
    Objects.requireNonNull(state); Set<Integer> unsafe = Set.copyOf(unsafeArmyIds);
    Set<Integer> threatened = Set.copyOf(threatenedStationaryArmyIds);
    Set<String> steps = new HashSet<>(); Set.copyOf(availableSteps).forEach(step -> steps.add(step.value()));
    unsafe.forEach(SplitMergeRecovery::unit); threatened.forEach(SplitMergeRecovery::unit);
    Objects.requireNonNull(routeAudit);
    if (state.split.isEmpty()) return new Keep();
    Split split = state.split.orElseThrow(); Obj detail = evidence("merge_recovery", split.detail());
    boolean quiet = unsafe.isEmpty() && threatened.isEmpty();
    if (split.status() == SplitStatus.MERGE_REQUIRES_RENDEZVOUS
        || split.status() == SplitStatus.MERGE_WAITING_FOR_IDLE && quiet)
      return hold("native_war_merge_rendezvous_blocked", "safe-exact-rendezvous",
          "the exact split pair is separated or not merge-idle, and this first counter-policy stage has no proven safe rendezvous intent; keep both armies paused instead of issuing independent orders", detail);
    if (split.status() == SplitStatus.READY_TO_MERGE) {
      int sibling = split.siblingArmyId().orElseThrow();
      boolean otherUnsafe = unsafe.stream().anyMatch(id -> id != split.originalArmyId() && id != sibling);
      boolean otherThreatened = threatened.stream().anyMatch(id -> id != split.originalArmyId() && id != sibling);
      if (!otherUnsafe && !otherThreatened) {
        String step = split.mergeStep().orElseThrow().value();
        if (steps.contains(step))
          return select("native_war_merge_recovery", step, Purpose.WORLD_ACTION,
              "the exact latest split pair is still co-located, but no exact combat prediction proves both halves independently safe; merge the sibling back into the original army without advancing time", detail);
        return hold("native_war_merge_recovery_unsupported", step,
            "the exact co-located split pair requires recovery, but the generation-bound Merge action is not currently eligible; keep the map paused", detail);
      }
    }
    if (split.status() != SplitStatus.MERGE_COMPLETED || !quiet) return new Keep();
    Optional<Army> merged = state.armies.stream().filter(army -> army.id() == split.originalArmyId()).findFirst();
    if (merged.isEmpty()) return new Keep();
    Obj army = merged.orElseThrow().raw();
    OptionalInt target = province(army.get("move_target_province_id"));
    OptionalInt origin = province(army.get("current_province_id"));
    if (target.isEmpty() || origin.isEmpty()) return new Keep();
    int id = split.originalArmyId(), from = origin.getAsInt(), to = target.getAsInt();
    String previewStep = "preview-move-army-" + id + "-to-" + to;
    Optional<List<Integer>> preview = freshPreview(state, id, from, to);
    if (preview.isEmpty()) {
      if (steps.contains(previewStep))
        return select("native_war_merge_route_preview", previewStep, Purpose.READ_ONLY,
            "the confirmed Merge invalidated every older same-date move intent and preview; preview the destination army's current target again before advancing", detail);
      return hold("native_war_merge_route_preview_unsupported", previewStep,
          "the confirmed Merge invalidated the old route, but a fresh same-origin preview is not currently advertised; keep the map paused", detail);
    }
    Audit audit = Objects.requireNonNull(routeAudit.audit(preview.orElseThrow(), from, to));
    StrictJson.require(audit.targetProvinceId() == to, "route audit target differs");
    Obj audited = detail.with("route_audit", auditDetail(audit));
    if (audit.status() != Status.SAFE)
      return hold("native_war_merge_route_preview_unsafe", "safe-exact-war-route",
          "the first post-Merge preview is not safe against the current hostile route matrix; do not advance the retained pre-Merge route", audited);
    Optional<List<Integer>> observed = remainingRoute(army);
    if (observed.isEmpty() || !observed.orElseThrow().equals(audit.routeProvinceIds()))
      return hold("native_war_merge_route_refresh_blocked", "move-army-" + id + "-to-" + to,
          "the first safe post-Merge preview does not match the retained route; the current action surface intentionally does not resubmit a same-target move, so keep the map paused for a future exact replace-route primitive",
          audited.with("observed_route_province_ids", observed.<Value>map(SplitMergeRecovery::numbers).orElse(Nil.INSTANCE)));
    if (steps.contains("life-advance"))
      return select("native_war_merge_route_progress", "life-advance", Purpose.DATE_ADVANCE,
          "the first post-Merge preview is safe and exactly matches the observed remaining route; advance one bounded slice from this fresh intent epoch", audited);
    return hold("native_war_merge_route_progress_unsupported", "life-advance",
        "the post-Merge route is freshly revalidated but the backend cannot advance its bounded slice", audited);
  }

  private static Optional<Split> recover(List<HistoryRow> history, ArmySet controlled, Set<BigInteger> goals) {
    if (!controlled.identitiesValid()) return Optional.empty();
    Map<Integer, Army> current = new LinkedHashMap<>();
    controlled.armies().forEach(army -> current.put(army.id(), army));
    Set<Integer> currentIds = current.keySet();
    for (int position = history.size() - 1; position >= 0; position--) {
      HistoryRow row = history.get(position); OptionalInt parsed = parseSplit(row.command());
      if (parsed.isEmpty() || !row.ok()) continue;
      int original = parsed.getAsInt(); Optional<Obj> actionOpt = row.result().flatMap(value -> object(value.get("war_action")));
      if (actionOpt.isEmpty()) continue;
      Obj action = actionOpt.orElseThrow(); String actionStatus = text(action.get("status"));
      if (!"split_submitted".equals(actionStatus) && !"split_applied".equals(actionStatus)) continue;
      Value sourceRaw = action.get("source_army_id"); OptionalInt source = unit(sourceRaw);
      if (present(sourceRaw) && source.isEmpty() || source.isPresent() && source.getAsInt() != original) continue;
      Optional<List<Integer>> beforeOpt = ids(action.get("player_army_ids_before"));
      if (beforeOpt.isEmpty()) continue;
      List<Integer> before = beforeOpt.orElseThrow(); Set<Integer> beforeSet = new HashSet<>(before);
      if (beforeSet.size() != before.size() || !beforeSet.contains(original)) continue;
      TreeSet<Integer> candidates = new TreeSet<>();
      Value siblingRaw = action.get("sibling_army_id"); OptionalInt sibling = unit(siblingRaw);
      if (present(siblingRaw) && sibling.isEmpty()) continue;
      if (sibling.isPresent() && !beforeSet.contains(sibling.getAsInt())) candidates.add(sibling.getAsInt());
      Set<Integer> delta = new HashSet<>(currentIds); delta.removeAll(beforeSet);
      if (delta.size() == 1) candidates.addAll(delta);
      List<HistoryRow> merges = new ArrayList<>();
      for (int i = position + 1; i < history.size(); i++) {
        HistoryRow later = history.get(i); Optional<Pair> pair = parseMerge(later.command());
        if (pair.isPresent() && pair.orElseThrow().destination() == original
            && !beforeSet.contains(pair.orElseThrow().source())) {
          candidates.add(pair.orElseThrow().source()); merges.add(later);
        }
      }
      if (candidates.size() != 1)
        return Optional.of(split(SplitStatus.SPLIT_IDENTITY_PENDING, original, OptionalInt.empty(),
            empty().with("split_history_position", number(position))
              .with("reason", string("the exact split receipt and current army-set delta do not identify one sibling"))));
      int siblingId = candidates.first(); Set<Integer> expected = new HashSet<>(beforeSet); expected.add(siblingId);
      Obj pairDetail = empty().with("player_army_ids_before", numbers(beforeSet.stream().sorted().toList()))
          .with("current_player_army_ids", numbers(currentIds.stream().sorted().toList()));
      if (!currentIds.equals(beforeSet) && !currentIds.equals(expected))
        return Optional.of(split(SplitStatus.SPLIT_ARMY_SET_INCONSISTENT, original, OptionalInt.of(siblingId), pairDetail));
      if (!merges.isEmpty()) {
        HistoryRow latest = merges.getLast();
        Value mergeAction = latest.result().flatMap(value -> object(value.get("war_action"))).<Value>map(value -> value).orElse(Nil.INSTANCE);
        Obj mergeDetail = empty().with("war_action", mergeAction);
        if (!latest.ok()) return Optional.of(split(SplitStatus.MERGE_FAILED, original, OptionalInt.of(siblingId),
            mergeDetail.with("error", valueOrNil(latest.raw().get("error")))));
        if (currentIds.equals(beforeSet) && currentIds.contains(original))
          return Optional.of(split(SplitStatus.MERGE_COMPLETED, original, OptionalInt.of(siblingId), mergeDetail));
        if (mergeAction instanceof Obj receipt && "merge_applied".equals(text(receipt.get("status"))))
          return Optional.of(split(SplitStatus.MERGE_POSTCONDITION_INCONSISTENT, original, OptionalInt.of(siblingId),
              mergeDetail.with("current_player_army_ids", numbers(currentIds.stream().sorted().toList()))));
        return Optional.of(split(SplitStatus.MERGE_PENDING, original, OptionalInt.of(siblingId), mergeDetail));
      }
      if (currentIds.equals(beforeSet))
        return Optional.of(split(SplitStatus.SPLIT_IDENTITY_PENDING, original, OptionalInt.of(siblingId),
            empty().with("reason", string("the submitted split has no observable sibling yet"))));
      Army originalArmy = current.get(original), siblingArmy = current.get(siblingId);
      if (originalArmy == null || siblingArmy == null) return Optional.empty();
      OptionalInt province = province(originalArmy.raw().get("current_province_id"));
      if (province.isEmpty() || !province.equals(province(siblingArmy.raw().get("current_province_id"))))
        return Optional.of(split(SplitStatus.MERGE_REQUIRES_RENDEZVOUS, original, OptionalInt.of(siblingId), empty()));
      if (combatOrRetreat(originalArmy.raw()) || combatOrRetreat(siblingArmy.raw()))
        return Optional.of(split(SplitStatus.MERGE_WAITING_FOR_IDLE, original, OptionalInt.of(siblingId), empty()));
      List<Integer> durable = List.of(originalArmy, siblingArmy).stream()
          .filter(army -> integer(army.raw().get("move_target_province_id")).map(goals::contains).orElse(false))
          .map(Army::id).sorted().toList();
      Obj ready = empty().with("province_id", number(province.getAsInt())).with("durable_goal_army_ids", numbers(durable))
          .with("missing_proofs", new Arr(List.of(string("exact_combat_prediction_unavailable"))))
          .with("submitted_date_raw", integer(action.get("submitted_date_raw")).<Value>map(IntegerValue::new).orElse(Nil.INSTANCE))
          .with("player_army_ids_before", numbers(beforeSet.stream().sorted().toList()));
      return Optional.of(split(SplitStatus.READY_TO_MERGE, original, OptionalInt.of(siblingId), ready));
    }
    return Optional.empty();
  }

  private static Optional<MergeLifecycle> latestMerge(List<HistoryRow> history, Obj snapshot) {
    List<Obj> failures = new ArrayList<>();
    for (int i = history.size() - 1; i >= 0; i--) {
      HistoryRow row = history.get(i); Optional<Pair> parsed = parseMerge(row.command());
      if (parsed.isEmpty()) continue;
      Pair pair = parsed.orElseThrow();
      if (!row.ok()) {
        failures.add(empty().with("status", string(MergeStatus.SUBMISSION_FAILED.wire()))
            .with("destination_army_id", number(pair.destination())).with("source_army_id", number(pair.source()))
            .with("merge_step", string(row.command())).with("history_index", valueOrNil(row.raw().get("index")))
            .with("error", valueOrNil(row.raw().get("error"))));
        continue;
      }
      if (failures.stream().anyMatch(failure -> !row.command().equals(text(failure.get("merge_step")))))
        return Optional.of(failed(failures.getFirst()));
      MergeLifecycle lifecycle = observeMerge(row, pair, snapshot);
      if (!failures.isEmpty())
        lifecycle = new MergeLifecycle(lifecycle.status(), lifecycle.mergeStep(),
            lifecycle.detail().with("duplicate_attempt", failures.getFirst())
                .with("duplicate_attempts", new Arr(new ArrayList<Value>(failures))));
      return Optional.of(lifecycle);
    }
    return failures.isEmpty() ? Optional.empty() : Optional.of(failed(failures.getFirst()));
  }
  private static MergeLifecycle failed(Obj detail) {
    return new MergeLifecycle(MergeStatus.SUBMISSION_FAILED, new OperationKey(text(detail.get("merge_step"))), detail);
  }
  private static MergeLifecycle observeMerge(HistoryRow row, Pair pair, Obj snapshot) {
    Obj base = empty().with("merge_step", string(row.command())).with("history_index", valueOrNil(row.raw().get("index")))
        .with("destination_army_id", number(pair.destination())).with("source_army_id", number(pair.source()));
    Optional<Obj> actionOpt = row.result().flatMap(value -> object(value.get("war_action")));
    if (actionOpt.isEmpty()) return lifecycle(MergeStatus.RECEIPT_INVALID, row, base);
    Obj action = actionOpt.orElseThrow(); base = base.with("war_action", action);
    String receipt = text(action.get("status")); Optional<List<Integer>> beforeOpt = ids(action.get("player_army_ids_before"));
    if (!Set.of("merge_submitted", "merge_applied").contains(receipt == null ? "" : receipt)
        || !sameInteger(action.get("destination_army_id"), pair.destination())
        || !sameInteger(action.get("source_army_id"), pair.source()) || beforeOpt.isEmpty())
      return lifecycle(MergeStatus.RECEIPT_INVALID, row, base);
    List<Integer> before = beforeOpt.orElseThrow(); Set<Integer> beforeSet = new HashSet<>(before);
    if (beforeSet.size() != before.size() || !before.equals(before.stream().sorted().toList())
        || !beforeSet.contains(pair.destination()) || !beforeSet.contains(pair.source())
        || nonnegative(action.get("submitted_date_raw")).isEmpty())
      return lifecycle(MergeStatus.RECEIPT_INVALID, row, base);
    Set<Integer> afterSet = new HashSet<>(beforeSet); afterSet.remove(pair.source());
    String submittedSnapshot = text(action.get("submitted_snapshot_id")), submittedEpisode = text(action.get("submitted_episode_run_id"));
    boolean submitted = nonempty(submittedSnapshot) && nonempty(submittedEpisode)
        && nonnegative(action.get("submitted_public_revision")).isPresent()
        && nonnegative(action.get("submitted_native_revision")).isPresent();
    boolean durable = "merge_applied".equals(receipt) && truth(action.get("postcondition_verified"))
        && truth(action.get("source_army_id_absent")) && submitted
        && nonempty(text(action.get("observed_snapshot_id")))
        && !submittedSnapshot.equals(text(action.get("observed_snapshot_id")))
        && greater(action.get("observed_public_revision"), action.get("submitted_public_revision"))
        && greater(action.get("observed_native_revision"), action.get("submitted_native_revision"))
        && atLeast(action.get("observed_date_raw"), action.get("submitted_date_raw"))
        && submittedEpisode.equals(text(action.get("observed_episode_run_id")))
        && ids(action.get("player_army_ids_after")).map(afterSet.stream().sorted().toList()::equals).orElse(false);
    if (durable) return lifecycle(MergeStatus.APPLIED, row,
        base.with("receipt_bound", new Bool(true)).with("independently_published", new Bool(true))
          .with("postcondition_consumed", new Bool(true)));
    if (!(snapshot.get("player_armies") instanceof Arr))
      return lifecycle(MergeStatus.POSTCONDITION_UNAVAILABLE, row, base);
    ArmySet armies = controlled(snapshot); List<Integer> current = armies.armies().stream().map(Army::id).toList();
    if (!armies.identitiesValid() || new HashSet<>(current).size() != current.size())
      return lifecycle(MergeStatus.POSTCONDITION_INCONSISTENT, row, base);
    Optional<Army> destination = armies.armies().stream().filter(army -> army.id() == pair.destination()).findFirst();
    Optional<Army> source = armies.armies().stream().filter(army -> army.id() == pair.source()).findFirst();
    boolean bound = submitted && positive(action.get("destination_owner_character_id"))
        && positive(action.get("destination_province_id")) && positive(action.get("source_owner_character_id"))
        && positive(action.get("source_province_id"));
    boolean independent = bound && truth(snapshot.get("paused")) && truth(snapshot.get("map_ready"))
        && submittedEpisode.equals(text(snapshot.get("episode_run_id")))
        && greater(snapshot.get("revision"), action.get("submitted_public_revision"))
        && greater(snapshot.get("native_revision"), action.get("submitted_native_revision"))
        && !Objects.equals(snapshot.get("snapshot_id"), action.get("submitted_snapshot_id"))
        && atLeast(snapshot.get("date_raw"), action.get("submitted_date_raw"));
    base = base.with("receipt_status", string(receipt)).with("receipt_bound", new Bool(bound))
        .with("independently_published", new Bool(independent)).with("player_army_ids_before", numbers(before))
        .with("current_player_army_ids", numbers(current.stream().sorted().toList()));
    Set<Integer> currentSet = new HashSet<>(current);
    boolean sameDestination = sameArmy(destination, bound, action.get("destination_owner_character_id"), action.get("destination_province_id"));
    if (currentSet.equals(afterSet) && sameDestination && source.isEmpty())
      return lifecycle(MergeStatus.POSTCONDITION_OBSERVED_UNCONSUMED, row, base);
    if (currentSet.equals(beforeSet) && sameDestination
        && sameArmy(source, bound, action.get("source_owner_character_id"), action.get("source_province_id")))
      return lifecycle(independent ? MergeStatus.PENDING_OBSERVED : MergeStatus.PENDING_SAME_FRAME, row, base);
    if (!bound && "merge_submitted".equals(receipt)) return lifecycle(MergeStatus.POSTCONDITION_UNBOUND, row, base);
    return lifecycle(MergeStatus.POSTCONDITION_INCONSISTENT, row, base);
  }

  private static Optional<List<Integer>> freshPreview(State state, int armyId, int origin, int target) {
    Optional<BigInteger> date = integer(state.snapshot.get("date_raw"));
    if (date.isEmpty()) return Optional.empty();
    for (int i = state.history.size() - 1; i >= 0; i--) {
      HistoryRow row = state.history.get(i); Optional<Pair> merge = parseMerge(row.command());
      if (row.ok() && merge.isPresent() && (merge.orElseThrow().destination() == armyId || merge.orElseThrow().source() == armyId))
        return Optional.empty();
      var match = PREVIEW.matcher(row.command());
      if (!match.matches() || !match.group(1).equals(Integer.toString(armyId))
          || !match.group(2).equals(Integer.toString(target)) || !row.ok() || row.result().isEmpty()) continue;
      Obj result = row.result().orElseThrow();
      if (!sameFrameLease(result, state.snapshot)) continue;
      Optional<Obj> previewOpt = object(result.get("route_preview"));
      if (previewOpt.isEmpty()) continue;
      Obj preview = previewOpt.orElseThrow(); String status = text(preview.get("status"));
      if (!"available".equals(status) && !"deferred".equals(status)
          || !sameInteger(preview.get("army_id"), armyId)
          || !sameInteger(preview.get("origin_province_id"), origin)
          || !sameInteger(preview.get("target_province_id"), target)
          || !integer(preview.get("previewed_date_raw")).equals(date)) continue;
      if ("deferred".equals(status)) return Optional.of(List.of());
      Optional<List<Integer>> route = provinces(preview.get("route_province_ids"));
      if (route.isPresent()) return route;
    }
    return Optional.empty();
  }
  private static boolean sameFrameLease(Obj result, Obj snapshot) {
    Optional<Obj> diagnostics = object(snapshot.get("diagnostics"));
    if (diagnostics.isEmpty() || integer(diagnostics.orElseThrow().get("connection_generation")).isEmpty()
        || !nonempty(text(snapshot.get("episode_run_id")))) return false;
    return Objects.equals(result.get("queried_snapshot_id"), snapshot.get("snapshot_id"))
        && integer(result.get("queried_revision")).isPresent()
        && Objects.equals(result.get("queried_revision"), snapshot.get("revision"))
        && integer(result.get("queried_native_revision")).isPresent()
        && Objects.equals(result.get("queried_native_revision"), snapshot.get("native_revision"))
        && Objects.equals(result.get("queried_connection_generation"), diagnostics.orElseThrow().get("connection_generation"))
        && Objects.equals(result.get("queried_episode_run_id"), snapshot.get("episode_run_id"));
  }
  private static List<HistoryRow> historyAfterRestore(List<Obj> rawHistory) {
    List<Obj> expanded = new ArrayList<>();
    for (Obj row : rawHistory) {
      String command = text(row.get("command")); Optional<Obj> result = object(row.get("result"));
      boolean autoRun = "auto-run".equals(command) || command != null && command.matches("auto-run [0-9]+");
      if (autoRun && result.isPresent() && result.orElseThrow().get("turns") instanceof Arr turns) {
        for (Value value : turns.items()) if (value instanceof Obj turn)
          expanded.add(turn.with("index", number(expanded.size() + 1)));
      } else expanded.add(row.with("index", number(expanded.size() + 1)));
    }
    List<HistoryRow> rows = new ArrayList<>();
    for (Obj row : expanded) {
      String command = text(row.get("command")); Optional<Obj> result = object(row.get("result"));
      if ("auto-turn".equals(command)) {
        Optional<Obj> turn = result.flatMap(value -> object(value.get("auto_turn")));
        command = turn.map(value -> text(value.get("selected_step"))).orElse(null);
        if (result.isPresent()) {
          Obj rootResult = result.orElseThrow();
          boolean factual = List.of("assault_action", "route_preview", "war_action", "war_progress_before", "war_progress_after")
              .stream().anyMatch(key -> rootResult.get(key) instanceof Obj);
          Optional<Obj> nested = turn.flatMap(value -> object(value.get("result")));
          if (!factual && nested.isPresent()) result = nested;
        }
      }
      HistoryRow parsed = new HistoryRow(command == null ? "" : command, truth(row.get("ok")), result, row);
      if (parsed.ok() && "restore-checkpoint".equals(parsed.command())) rows.clear();
      else rows.add(parsed);
    }
    return List.copyOf(rows);
  }
  private static ArmySet controlled(Obj snapshot) {
    if (!(snapshot.get("player_armies") instanceof Arr rows)) return new ArmySet(List.of(), false);
    List<Army> result = new ArrayList<>(); boolean valid = true;
    for (Value value : rows.items()) if (value instanceof Obj army && truth(army.get("controllable"))) {
      OptionalInt id = unit(army.get("army_id"));
      if (id.isEmpty()) valid = false; else result.add(new Army(id.getAsInt(), army));
    }
    return new ArmySet(result, valid);
  }
  private static Set<BigInteger> objectives(Obj snapshot) {
    Set<BigInteger> goals = new HashSet<>();
    if (snapshot.get("active_wars") instanceof Arr wars)
      for (Value value : wars.items()) if (value instanceof Obj war && war.get("war_objective_province_ids") instanceof Arr ids)
        ids.items().forEach(id -> integer(id).ifPresent(goals::add));
    return Set.copyOf(goals);
  }
  private static boolean combatOrRetreat(Obj army) {
    if (truth(army.get("retreating")) || truth(army.get("in_combat"))) return true;
    String named = text(army.get("army_state"));
    if (named != null) return Set.of("combat", "retreating").contains(named.toLowerCase(Locale.ROOT));
    return integer(army.get("army_state_code")).map(value -> value.equals(BigInteger.TWO) || value.equals(BigInteger.valueOf(6))).orElse(false);
  }
  private static Optional<List<Integer>> remainingRoute(Obj army) {
    Optional<List<Integer>> route = provinces(army.get("route_province_ids"));
    if (route.isEmpty()) return route;
    List<Integer> values = route.orElseThrow(); OptionalInt current = province(army.get("current_province_id"));
    return Optional.of(!values.isEmpty() && current.isPresent() && values.getFirst() == current.getAsInt()
        ? List.copyOf(values.subList(1, values.size())) : values);
  }
  private static Split split(SplitStatus status, int original, OptionalInt sibling, Obj extra) {
    Obj detail = extra.with("status", string(status.wire())).with("original_army_id", number(original));
    Optional<OperationKey> step = Optional.empty();
    if (sibling.isPresent()) {
      detail = detail.with("sibling_army_id", number(sibling.getAsInt()));
      step = Optional.of(new OperationKey("merge-armies-" + original + "-with-" + sibling.getAsInt()));
      detail = detail.with("merge_step", string(step.orElseThrow().value()));
    }
    return new Split(status, original, sibling, step, detail);
  }
  private static MergeLifecycle lifecycle(MergeStatus status, HistoryRow row, Obj detail) {
    return new MergeLifecycle(status, new OperationKey(row.command()), detail.with("status", string(status.wire())));
  }
  private static Hold hold(String phase, String required, String reason, Obj detail) {
    return new Hold(phase, Optional.of(new OperationKey(required)), reason, detail);
  }
  private static Select select(String phase, String step, Purpose purpose, String reason, Obj detail) {
    return new Select(phase, new OperationKey(step), purpose, reason, detail);
  }
  private static Obj auditDetail(Audit audit) {
    return empty().with("status", string(audit.status().name().toLowerCase(Locale.ROOT)))
        .with("target_province_id", number(audit.targetProvinceId()))
        .with("route_province_ids", numbers(audit.routeProvinceIds()))
        .with("conflicts", new Arr(audit.conflicts().stream().<Value>map(conflict ->
            empty().with("kind", string(conflict.kind().name().toLowerCase(Locale.ROOT)))
              .with("enemy_army_id", conflict.enemyArmyId() == null ? Nil.INSTANCE : number(conflict.enemyArmyId()))
              .with("province_id", number(conflict.provinceId()))
              .with("to_province_id", conflict.toProvinceId().<Value>map(SplitMergeRecovery::number).orElse(Nil.INSTANCE))
              .with("player_hop", conflict.playerHop().<Value>map(SplitMergeRecovery::number).orElse(Nil.INSTANCE))
              .with("enemy_hop", conflict.enemyHop().<Value>map(SplitMergeRecovery::number).orElse(Nil.INSTANCE))).toList()));
  }
  private static boolean sameArmy(Optional<Army> army, boolean bound, Value owner, Value province) {
    return army.isPresent() && (!bound || Objects.equals(army.orElseThrow().raw().get("owner_character_id"), owner)
        && Objects.equals(army.orElseThrow().raw().get("current_province_id"), province));
  }
  private static OptionalInt parseSplit(String step) {
    var match = SPLIT.matcher(step); return match.matches() ? decimal(match.group(1)) : OptionalInt.empty();
  }
  private static Optional<Pair> parseMerge(String step) {
    var match = MERGE.matcher(step); if (!match.matches()) return Optional.empty();
    OptionalInt destination = decimal(match.group(1)), source = decimal(match.group(2));
    return destination.isPresent() && source.isPresent() && destination.getAsInt() != source.getAsInt()
        ? Optional.of(new Pair(destination.getAsInt(), source.getAsInt())) : Optional.empty();
  }
  private static OptionalInt decimal(String text) {
    if (text.length() > 10) return OptionalInt.empty();
    return unit(new IntegerValue(new BigInteger(text)));
  }
  private static Optional<List<Integer>> ids(Value value) {
    if (!(value instanceof Arr array)) return Optional.empty();
    List<Integer> result = new ArrayList<>();
    for (Value item : array.items()) { OptionalInt id = unit(item); if (id.isEmpty()) return Optional.empty(); result.add(id.getAsInt()); }
    return Optional.of(List.copyOf(result));
  }
  private static Optional<List<Integer>> provinces(Value value) {
    Optional<List<Integer>> result = ids(value);
    return result.filter(ids -> ids.stream().allMatch(id -> id > 0));
  }
  private static OptionalInt unit(Value value) {
    Optional<BigInteger> integer = integer(value);
    return integer.isPresent() && integer.orElseThrow().signum() >= 0 && integer.orElseThrow().compareTo(MAX_UNIT) <= 0
        ? OptionalInt.of(integer.orElseThrow().intValueExact()) : OptionalInt.empty();
  }
  private static OptionalInt province(Value value) {
    OptionalInt id = unit(value); return id.isPresent() && id.getAsInt() > 0 ? id : OptionalInt.empty();
  }
  private static void unit(int value) { StrictJson.require(value >= 0, "public CUnit ID must be nonnegative"); }
  private static Optional<BigInteger> integer(Value value) { return value instanceof IntegerValue number ? Optional.of(number.value()) : Optional.empty(); }
  private static Optional<BigInteger> nonnegative(Value value) { return integer(value).filter(number -> number.signum() >= 0); }
  private static boolean positive(Value value) { return integer(value).filter(number -> number.signum() > 0).isPresent(); }
  private static boolean sameInteger(Value value, int expected) { return integer(value).map(BigInteger.valueOf(expected)::equals).orElse(false); }
  private static boolean greater(Value after, Value before) { return integer(after).isPresent() && integer(before).isPresent() && integer(after).orElseThrow().compareTo(integer(before).orElseThrow()) > 0; }
  private static boolean atLeast(Value after, Value before) { return integer(after).isPresent() && integer(before).isPresent() && integer(after).orElseThrow().compareTo(integer(before).orElseThrow()) >= 0; }
  private static boolean truth(Value value) { return value instanceof Bool bool && bool.value(); }
  private static boolean present(Value value) { return value != null && value != Nil.INSTANCE; }
  private static Optional<Obj> object(Value value) { return value instanceof Obj obj ? Optional.of(obj) : Optional.empty(); }
  private static String text(Value value) { return value instanceof Text text ? text.value() : null; }
  private static boolean nonempty(String value) { return value != null && !value.isEmpty(); }
  private static Value valueOrNil(Value value) { return value == null ? Nil.INSTANCE : value; }
  private static Obj empty() { return new Obj(Map.of()); }
  private static Obj evidence(String field, Obj detail) { return empty().with(field, detail); }
  private static Text string(String value) { return new Text(value); }
  private static IntegerValue number(int value) { return new IntegerValue(BigInteger.valueOf(value)); }
  private static Arr numbers(List<Integer> values) { return new Arr(values.stream().<Value>map(SplitMergeRecovery::number).toList()); }
}

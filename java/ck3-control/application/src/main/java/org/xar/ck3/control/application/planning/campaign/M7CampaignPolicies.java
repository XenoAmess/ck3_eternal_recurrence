package org.xar.ck3.control.application.planning.campaign;

import java.math.BigInteger;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.m7.KernelCheckpointContinuity;
import org.xar.ck3.control.g2.m7.M7KernelPlanConsumer;
import org.xar.ck3.control.g2.m7.NativeCalendarObservation;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext;
import org.xar.ck3.control.wave2.military.routewindowstep.RouteWindowStep;
import org.xar.ck3.control.wave3.planning.datedsummary.DatedSummaryCodec;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmFeedbackApplication;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback;
import static org.xar.ck3.control.application.planning.OrdinaryPolicy.*;

/** Actual ordinary campaign normalization and private publication; never a query, submitter or ledger writer. */
public final class M7CampaignPolicies {
  private M7CampaignPolicies() { }
  public static final String FACTION_QUERY = "query-player-faction-alerts-v1";
  @FunctionalInterface public interface DeadlineSource {
    Optional<CampaignDeadline.Configuration> current(PlanningRequest request);
  }
  /** The unique life-advance factory rebuilds arguments AND expected postcondition.
  * For life-advance, the cap boundary is a maximum; its one-day lookup is not a selected horizon. */
  @FunctionalInterface public interface AdvanceRewrite {
    ActionCommand rewrite(PlanningRequest request, ActionCommand original,
        String effectiveStep, CampaignDeadline.Cap cap);
  }
  public record GoalInput(KernelCheckpointContinuity.Observation observation,
      Optional<GovernmentContext.Context> government) {
    public GoalInput { Objects.requireNonNull(observation); Objects.requireNonNull(government); }
  }
  /** Root supplies the real observation; G2 metadata or the portable goal alone cannot issue it. */
  @FunctionalInterface public interface GoalObservationSource {
    Optional<GoalInput> current(PlanningRequest request);
  }
  /**
   * Pure projection of the actual held full Native/Driver request. Root supplies its exact
   * executable and source epoch while retaining the original writer/observation lease.
   * Calling this method alone grants no episode, native-read or replay authority.
   */
  public static Optional<GoalInput> projectGoal(PlanningRequest request, String sourceEpoch,
      ExactRef exactExecutable, Optional<GovernmentContext.Context> government) {
    return projectGoal(request, Optional.of(sourceEpoch), Optional.of(exactExecutable), government);
  }

  public static Optional<GoalInput> projectGoal(PlanningRequest request, Optional<String> sourceEpoch,
      Optional<ExactRef> exactExecutable, Optional<GovernmentContext.Context> government) {
    Objects.requireNonNull(request); Objects.requireNonNull(sourceEpoch); Objects.requireNonNull(exactExecutable); Objects.requireNonNull(government);
    if (request.observations().campaignGoal().isEmpty()) return Optional.empty();
    if (exactExecutable.isPresent()) require(exactExecutable.get().bytes() > 0, "supplied executable evidence required for the kernel goal projection");
    NativeCalendarObservation.project(request.before(), request.source(), request.observations().snapshot());
    var before = request.before(); var frame = before.frame();
    return Optional.of(new GoalInput(new KernelCheckpointContinuity.Observation(before.machineId(), sourceEpoch,
        new org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity(before.game().pid(),
            before.game().creationFiletime().value().toString()), exactExecutable,
        frame.snapshotId(), frame.revision(), frame.identity().nativeRevision(),
        frame.episodeRunId(), frame.identity().player().longValueExact(), frame.identity().dateRaw().longValueExact(),
        request.observations().campaignGoal().orElseThrow(),
        government.map(GovernmentContext.Context::governmentKey).orElse(null),
        government.map(GovernmentContext.Context::adapterFamily).orElse(null)), government));
  }
  public static final class InputUnavailable extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public InputUnavailable(String reason) { super(reason); StrictJson.text(reason); }
  }

  public static final class CampaignAdvancePolicy implements OrdinaryPolicy {
    private final ExactRef source; private final DeadlineSource deadlines;
    private final AdvanceRewrite rewrite; private final GoalObservationSource goals;
    public CampaignAdvancePolicy(ExactRef source, DeadlineSource deadlines,
        AdvanceRewrite rewrite, GoalObservationSource goals) {
      this.source = source(source); this.deadlines = Objects.requireNonNull(deadlines);
      this.rewrite = Objects.requireNonNull(rewrite); this.goals = Objects.requireNonNull(goals);
    }
    @Override public PlanningStage stage() { return PlanningStage.CAMPAIGN_ADVANCE_CAP; }
    @Override public ExactRef implementationSource() { return source; }
    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
      Objects.requireNonNull(request); Objects.requireNonNull(previous);
      try {
        Draft result = previous;
        Optional<CampaignDeadline.Configuration> configuration = Objects.requireNonNull(deadlines.current(request));
        if (configuration.isPresent() && previous.command().isPresent()) {
          CampaignDeadline.Configuration config = configuration.orElseThrow();
          NativeCalendarObservation.project(request.before(), request.source(), request.observations().snapshot());
          require(config.equals(CampaignDeadline.configure(config.founding(),
              org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule::calendar, Optional.empty())), "actual founding calendar differs");
          // The fixed scoring clock and dynasty-continuity goal have independent producer IDs.
          ActionCommand command = previous.command().orElseThrow();
          BigInteger current = request.before().frame().identity().dateRaw();
          Optional<Step> shape = Step.parse(command.operation().value(), current);
          if (shape.isPresent() && !alreadyCapped(previous.detail(), config, current, command.operation().value())) {
            Step step = shape.orElseThrow();
            CampaignDeadline.Cap cap = CampaignDeadline.deadline(configuration, current, step.requested()).orElseThrow();
            String effective = cap.status() == CampaignDeadline.Status.ADVANCE
                ? step.effective(cap.targetDateRaw(), current) : null;
            OpportunityJson.Obj detail = previous.detail().with("campaign_deadline_v1", metadata(cap, step, effective));
            if (effective == null) {
              detail = detail.with("selected_step", OpportunityJson.Nil.INSTANCE);
              result = draft(previous, "campaign_score_endpoint_reached",
                  "the fixed campaign endpoint is already observed; no further clock advance", Optional.empty(), detail);
            } else {
              ActionCommand next = Objects.requireNonNull(rewrite.rewrite(request, command, effective, cap));
              require(next.operation().value().equals(effective) && next.before().equals(command.before())
                  && next.source().equals(command.source()) && next.sessionId().equals(command.sessionId())
                  && next.claims().equals(command.claims()) && next.deadline().equals(command.deadline()),
                  "advance factory crossed original frame/source/session/claims/deadline or selected step");
              detail = detail.with("selected_step", text(effective));
              if (!cap.targetDateRaw().equals(cap.requestedTargetDateRaw())) {
                for (String key : List.of("absolute_target_date_raw", "target_date_raw"))
                  if (detail.get(key) != null) detail = detail.with(key, number(cap.targetDateRaw()));
              }
              result = draft(previous, previous.phase(), previous.reason(), Optional.of(next), detail);
            }
          }
        }
        result = publishGoal(request, result, goals);
        return result.equals(previous) ? new Keep("campaign clock and full goal projection already current")
            : new Replace(result, "original campaign deadline and full goal projection consumed by the actual selected step");
      } catch (InputUnavailable unavailable) {
        return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, unavailable.getMessage());
      }
    }
  }

  private static Draft publishGoal(PlanningRequest request, Draft draft, GoalObservationSource supplier) {
    if (request.observations().campaignGoal().isEmpty()) return draft;
    var goal = request.observations().campaignGoal().orElseThrow();
    byte[] plan = GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(goal));
    OpportunityJson.Obj detail = draft.detail().with("campaign_goal_plan_used", json(plan));
    if (draft.command().isPresent()) {
      GoalInput input = supplier.current(request).orElseThrow(() -> new InputUnavailable("actual M7 observation supplier unavailable"));
      var observed = input.observation(); var frame = request.before().frame();
      require(observed.machineId().equals(request.before().machineId())
          && observed.game().pid() == request.before().game().pid()
          && observed.game().creationFiletime().equals(request.before().game().creationFiletime().value().toString())
          && observed.snapshotId().equals(frame.snapshotId()) && observed.revision().equals(frame.revision())
          && observed.nativeRevision().equals(frame.identity().nativeRevision())
          && observed.episodeRunId().equals(frame.episodeRunId())
          && BigInteger.valueOf(observed.dateRaw()).equals(frame.identity().dateRaw())
          && BigInteger.valueOf(observed.actorCharacterId()).equals(frame.identity().player()) && observed.goal().equals(goal),
          "actual M7 observation crossed full kernel birth/frame/actor/goal binding");
      var consumed = M7KernelPlanConsumer.consume(M7OrdinaryPlanConsumer.Publication.ORDINARY_PLAN,
          observed, draft.command().orElseThrow().operation().value(), input.government());
      require(java.util.Arrays.equals(plan, GoalCodec.encodePlan(consumed.campaignGoalPlanUsed())), "consumer changed full original goal policy");
      byte[] wire = M7KernelPlanConsumer.encode(consumed);
      require(M7KernelPlanConsumer.decode(wire).equals(consumed), "kernel ordinary consumer persistence drift");
      detail = detail.with("m7_kernel_plan_consumption", json(wire));
    }
    return draft(draft, draft.phase(), draft.reason(), draft.command(), detail);
  }

  /** Service-scoped, one pending query, no history lookup; Root planner/loop call the four lifecycle methods. */
  public static final class RealmLifecycle implements OrdinaryPolicy {
    private sealed interface ActiveScope permits Scope, PublicTerminalScope { }
    private final ExactRef source; private final ThreadLocal<ActiveScope> current = new ThreadLocal<>();
    private long epoch; private Pending pending; private RealmMembershipFeedback.VerifiedFeedback last;
    public RealmLifecycle(ExactRef source) { this.source = source(source); }
    public static final class Scope implements ActiveScope {
      private final RealmLifecycle owner; private final long epoch; private final PlanningRequest request;
      private final ActiveScope previous; private Draft staged; private boolean closed;
      private Scope(RealmLifecycle owner, long epoch, PlanningRequest request, ActiveScope previous) {
        this.owner = owner; this.epoch = epoch; this.request = request; this.previous = previous;
      }
    }
    /** Private custody of one actual raw DATA callback; it cannot stage or publish a faction query. */
    public static final class PublicTerminalScope implements ActiveScope {
      private final RealmLifecycle owner; private final long epoch;
      private final PublicTerminalDataContext actual; private final ContinuityStorePort.Session same;
      private final DriverObservationAssembler.FullSnapshot snapshot; private final Known driver;
      private final DriverStateSnapshot canonical; private final List<ActionReceipt> actions;
      private final Optional<ExactRef> sourceProof;
      private final ExactRef hello, heartbeat, originalDriver;
      private final Instant until; private final String head; private final long sequence;
      private final Thread thread; private final ActiveScope previous; private boolean closed;
      private PublicTerminalScope(RealmLifecycle owner, long epoch, PublicTerminalDataContext actual,
          ContinuityStorePort.Session same, ActiveScope previous) throws IOException {
        this.owner = owner; this.epoch = epoch; this.actual = actual; this.same = same; this.previous = previous;
        thread = Thread.currentThread();
        snapshot = Objects.requireNonNull(actual.snapshot()); driver = Objects.requireNonNull(actual.driver());
        canonical = Objects.requireNonNull(actual.canonicalDriver()); actions = List.copyOf(actual.actions());
        sourceProof = Objects.requireNonNull(actual.originalSourceProof()).map(M7CampaignPolicies::source); hello = source(actual.originalHello());
        heartbeat = source(actual.originalHeartbeat()); originalDriver = source(actual.originalDriver());
        until = Objects.requireNonNull(actual.validUntil());
        var captured = same.head(); head = captured.digest(); sequence = captured.state().sequence();
      }
    }
    private record Pending(long epoch, PlanningRequest request, ActionCommand command,
        OpportunityJson.Obj originalSnapshot, OpportunityJson.Obj sourceFrame) { }
    public synchronized Scope begin(PlanningRequest request) {
      require(!(current.get() instanceof PublicTerminalScope),
          "public terminal DATA cannot enter ordinary realm publication");
      Objects.requireNonNull(request); epoch = Math.incrementExact(epoch); pending = null;
      Scope scope = new Scope(this, epoch, request, current.get()); current.set(scope); return scope;
    }
    /** Authenticate before entering; a foreign or escaped DATA frame cannot clear another pending plan. */
    public synchronized PublicTerminalScope beginPublicTerminalData(PublicTerminalDataContext actual,
        ContinuityStorePort.Session same) throws IOException {
      Objects.requireNonNull(actual); Objects.requireNonNull(same); actual.assertCurrent(same);
      long next = Math.incrementExact(epoch);
      PublicTerminalScope scope = new PublicTerminalScope(this, next, actual, same, current.get());
      requirePublicCurrent(scope);
      epoch = next; pending = null; current.set(scope); return scope;
    }
    /** Only checks the terminal envelope; the original complete DATA producer/codec remains the Planner's. */
    public synchronized void finalizePublicTerminalData(PublicTerminalScope scope,
        OpportunityJson.Obj actualFinalPlan) throws IOException {
      owned(scope);
      try {
        requirePublicCurrent(scope); Objects.requireNonNull(actualFinalPlan);
        require(new OpportunityJson.Text("one-life-turn-v1").equals(actualFinalPlan.get("policy")),
            "public terminal DATA must retain the original plan policy");
        OpportunityJson.Value selected = actualFinalPlan.get("selected_step");
        require(selected == OpportunityJson.Nil.INSTANCE || selected instanceof OpportunityJson.Text text
            && List.of("death-terminal", "start-next-episode", "continue-as-reconciled-successor").contains(text.value()),
            "public terminal DATA cannot finalize an ordinary action or faction publication");
        requirePublicCurrent(scope);
      } finally { close(scope); }
    }
    /** Definite cleanup also runs when presentation or current-source validation failed. */
    public synchronized void cancelPublicTerminalData(PublicTerminalScope scope) {
      require(scope != null && scope.owner == this && scope.thread == Thread.currentThread(),
          "public terminal scope owner or thread differs");
      if (pending != null && pending.epoch() == scope.epoch) pending = null;
      if (!scope.closed) { owned(scope); close(scope); }
    }
    @Override public PlanningStage stage() { return PlanningStage.REALM_MEMBERSHIP_PUBLICATION; }
    @Override public ExactRef implementationSource() { return source; }
    @Override public synchronized Decision evaluate(PlanningRequest request, Draft previous) {
      Scope scope = active(); require(scope.request == request, "realm stage crossed original planning request");
      scope.staged = previous;
      return previous.command().filter(value -> value.operation().value().equals(FACTION_QUERY)).isPresent()
          ? new Keep("actual faction query staged for final private publication")
          : new NotApplicable("actual selected step is not a realm membership query");
    }
    public synchronized void finalizePlan(Scope scope, PlanningResult result) {
      owned(scope); Objects.requireNonNull(result);
      try {
        if (scope.epoch != epoch || !(result instanceof PlanningResult.ActionSelected selected)) return;
        Draft finalPlan = result.trace().finalPlan().orElseThrow(() -> new IllegalArgumentException("actual final draft required"));
        require(scope.staged == finalPlan && selected.command() == finalPlan.command().orElseThrow(),
            "realm publication must retain actual final draft/command references");
        if (!selected.command().operation().value().equals(FACTION_QUERY)) return;
        require(selected.command().before().equals(scope.request.before())
            && selected.command().source().equals(scope.request.source())
            && selected.command().sessionId().equals(scope.request.sessionId()), "realm final plan crossed source/frame/session");
        OpportunityJson.Obj sourceFrame = sourceFrame(scope.request);
        pending = new Pending(epoch, scope.request, selected.command(), scope.request.observations().snapshot(), sourceFrame);
      } finally { close(scope); }
    }
    public synchronized void cancel(Scope scope) {
      require(scope != null && scope.owner == this, "realm scope owner differs");
      if (pending != null && pending.epoch() == scope.epoch) pending = null;
      if (!scope.closed) { owned(scope); close(scope); }
    }
    /** Only the actual authoritative completion is accepted; ACK alone cannot qualify feedback. */
    public synchronized RealmCompletion afterExecution(ActionReceipt receipt) {
      Objects.requireNonNull(receipt);
      if (!receipt.command().operation().value().equals(FACTION_QUERY)) return new NoRealmQuery();
      Pending slot = pending;
      if (slot == null || !slot.command().actionId().equals(receipt.command().actionId()))
        return new RealmUnavailable("original_query_plan_slot_unavailable");
      pending = null; // one shot, including UNKNOWN, changed body and failed validation
      if (slot.epoch() != epoch || !slot.command().equals(receipt.command()))
        return new RealmUnavailable("original_query_plan_slot_unavailable");
      if (!(receipt.state() instanceof ActionState.Settled settled)
          || !(settled.settlement() instanceof ActionState.Applied applied)
          || !(settled.dispatch() instanceof NativeActionPort.AckReceived ack)
          || !ack.nativeOk() || ack.originalResultToken().isEmpty())
        return new RealmUnavailable("original_query_not_confirmed");
      var before = slot.request().before(); var after = applied.observation();
      if (!after.after().machineId().equals(before.machineId()) || !after.after().game().equals(before.game())
          || !after.after().frame().equals(before.frame()) || !after.source().equals(slot.request().source())
          || !after.sessionId().equals(slot.request().sessionId()))
        return new RealmUnavailable("original_query_frame_changed");
      byte[] faction = ack.originalResultToken().orElseThrow().bytes();
      if (faction.length > RealmMembershipFeedback.MAX_BYTES) return new RealmUnavailable("existing_faction_DTO_exceeds_feedback_budget");
      byte[] previous = last == null ? bytes("null") : StrictJson.parse(last.wireJson(), RealmMembershipFeedback.MAX_BYTES)
          .get("observation").toString().getBytes(StandardCharsets.UTF_8);
      byte[] request = join(bytes("{\"snapshot\":"), OpportunityJson.encode(slot.originalSnapshot()),
          bytes(",\"source_frame\":"), OpportunityJson.encode(slot.sourceFrame()),
          bytes(",\"faction_result\":"), faction, bytes(",\"previous\":"), previous, bytes("}"));
      if (request.length > RealmMembershipFeedback.MAX_BYTES) return new RealmUnavailable("existing_feedback_request_exceeds_budget");
      RealmMembershipFeedback.Result feedback = RealmFeedbackApplication.feedback(RealmMembershipFeedback.decodeRequest(request));
      if (feedback instanceof RealmMembershipFeedback.VerifiedFeedback verified) last = verified;
      return new RealmFeedback(feedback);
    }
    /** Original dated-summary reader: historical membership is never exposed as a current set. */
    public synchronized OpportunityJson.Obj summary(PlanningRequest request) {
      byte[] feedback = last == null ? bytes("null") : last.wireJson();
      byte[] input = join(bytes("{\"feedback\":"), feedback, bytes(",\"current_source_frame\":"), OpportunityJson.encode(sourceFrame(request)), bytes("}"));
      return json(DatedSummaryCodec.evaluate(input));
    }
    private Scope active() {
      if (!(current.get() instanceof Scope scope))
        throw new IllegalArgumentException("ordinary realm publication requires its original planning scope, not public terminal DATA");
      owned(scope); return scope;
    }
    private void owned(Scope scope) {
      require(scope != null && scope.owner == this && !scope.closed && current.get() == scope,
          "same-thread original realm scope required");
    }
    private void close(Scope scope) {
      scope.closed = true; if (scope.previous == null) current.remove(); else current.set(scope.previous);
    }
    private void owned(PublicTerminalScope scope) {
      require(scope != null && scope.owner == this && scope.thread == Thread.currentThread()
          && !scope.closed && current.get() == scope,
          "same-thread original public terminal scope required");
    }
    private void close(PublicTerminalScope scope) {
      scope.closed = true; if (scope.previous == null) current.remove(); else current.set(scope.previous);
    }
    private void requirePublicCurrent(PublicTerminalScope scope) throws IOException {
      scope.actual.assertCurrent(scope.same);
      require(scope.actual.snapshot() == scope.snapshot && scope.actual.driver() == scope.driver
          && scope.actual.canonicalDriver() == scope.canonical && scope.actual.actions().equals(scope.actions)
          && scope.actual.originalSourceProof().equals(scope.sourceProof) && scope.actual.originalHello().equals(scope.hello)
          && scope.actual.originalHeartbeat().equals(scope.heartbeat) && scope.actual.originalDriver().equals(scope.originalDriver)
          && scope.actual.validUntil().equals(scope.until), "public terminal DATA crossed its original frame/source/canonical evidence");
      var now = scope.same.head();
      require(scope.head.equals(now.digest()) && scope.sequence == now.state().sequence(),
          "public terminal DATA changed its actual original writer head");
      scope.actual.assertCurrent(scope.same);
    }
  }
  public sealed interface RealmCompletion permits NoRealmQuery, RealmUnavailable, RealmFeedback { }
  public record NoRealmQuery() implements RealmCompletion { }
  public record RealmUnavailable(String reason) implements RealmCompletion {
    public RealmUnavailable { StrictJson.text(reason); }
  }
  public record RealmFeedback(RealmMembershipFeedback.Result feedback) implements RealmCompletion {
    public RealmFeedback { Objects.requireNonNull(feedback); }
  }

  private static OpportunityJson.Obj sourceFrame(PlanningRequest request) {
    OpportunityJson.Obj snapshot = request.observations().snapshot();
    OpportunityJson.Obj player = OpportunityJson.object(snapshot.get("played_character"), "played_character");
    OpportunityJson.Obj diagnostics = OpportunityJson.object(snapshot.get("diagnostics"), "diagnostics");
    OpportunityJson.Obj source = new OpportunityJson.Obj(java.util.Map.of()).with("schema", text("xar.ck3.planning-source-frame/v1"))
        .with("status", text("complete"));
    for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id"))
      source = source.with(key, Objects.requireNonNull(snapshot.get(key)));
    source = source.with("actor_character_id", Objects.requireNonNull(player.get("character_id")));
    for (String key : List.of("bridge_pid", "connection_generation"))
      source = source.with(key, Objects.requireNonNull(diagnostics.get(key)));
    // Existing whole feedback reducer independently validates this exact snapshot/source pair.
    return source;
  }
  private static boolean alreadyCapped(OpportunityJson.Obj detail, CampaignDeadline.Configuration config,
      BigInteger current, String step) {
    if (!(detail.get("campaign_deadline_v1") instanceof OpportunityJson.Obj prior)) return false;
    return text(config.founding().campaignId()).equals(prior.get("campaign_id"))
        && number(current).equals(prior.get("starting_date_raw")) && text(step).equals(prior.get("effective_step"));
  }
  private static OpportunityJson.Obj metadata(CampaignDeadline.Cap cap, Step step, String effective) {
    OpportunityJson.Obj row = json(CampaignDeadlineCodec.encodeCap(cap));
    row = row.with("requested_step", text(step.original())).with("effective_step", effective == null ? OpportunityJson.Nil.INSTANCE : text(effective))
        .with("maximum_target_date_raw", number(cap.boundaryDateRaw()));
    if (step.original().equals("life-advance")) row = row.with("requested_target_date_raw", OpportunityJson.Nil.INSTANCE)
        .with("target_date_raw", OpportunityJson.Nil.INSTANCE);
    return row;
  }
  enum Shape { GENERIC, BATTLE, ROUTE, HOLD, WINDOW }
  record Step(String original, Shape shape, BigInteger requested, String prefix, String suffix,
      Optional<RouteWindowStep> window) {
    private static final Pattern BATTLE = Pattern.compile("battle-decision-epoch-advance-to-([1-9][0-9]*)");
    private static final Pattern ROUTE = Pattern.compile("committed-route-sentinel-advance-army-(0|[1-9][0-9]*)-to-([1-9][0-9]*)-until-([1-9][0-9]*)(-speed-[1245])?");
    private static final Pattern HOLD = Pattern.compile("war-objective-hold-sentinel-advance-war-([1-9][0-9]*)-army-(0|[1-9][0-9]*)-at-([1-9][0-9]*)-until-([1-9][0-9]*)(-speed-[1245])?");
    static Optional<Step> parse(String step, BigInteger current) {
      if (List.of("life-advance", "life-advance-one-day", "battle-decision-epoch-advance", "battle-terminal-cruise").contains(step)) {
        int days = step.startsWith("battle-") ? 45 : 1;
        return Optional.of(new Step(step, Shape.GENERIC, current.add(BigInteger.valueOf(days * 24L)), "", "", Optional.empty()));
      }
      Matcher battle = BATTLE.matcher(step);
      if (battle.matches() && positiveLong(battle.group(1)))
        return Optional.of(new Step(step, Shape.BATTLE, new BigInteger(battle.group(1)), "battle-decision-epoch-advance-to-", "", Optional.empty()));
      Matcher route = ROUTE.matcher(step);
      if (route.matches() && int32(route.group(1), true) && int32(route.group(2), false) && positiveLong(route.group(3))) {
        String prefix = "committed-route-sentinel-advance-army-" + route.group(1) + "-to-" + route.group(2) + "-until-";
        return Optional.of(new Step(step, Shape.ROUTE, new BigInteger(route.group(3)), prefix,
            route.group(4) == null ? "" : route.group(4), Optional.empty()));
      }
      Matcher hold = HOLD.matcher(step);
      if (hold.matches() && int32(hold.group(1), false) && int32(hold.group(2), true)
          && int32(hold.group(3), false) && positiveLong(hold.group(4))) {
        String prefix = "war-objective-hold-sentinel-advance-war-" + hold.group(1) + "-army-" + hold.group(2) + "-at-" + hold.group(3) + "-until-";
        return Optional.of(new Step(step, Shape.HOLD, new BigInteger(hold.group(4)), prefix,
            hold.group(5) == null ? "" : hold.group(5), Optional.empty()));
      }
      Optional<RouteWindowStep> window = RouteWindowStep.parse(step);
      return window.map(value -> new Step(step, Shape.WINDOW, current.add(BigInteger.valueOf(value.horizonDays() * 24L)), "", "", window));
    }
    String effective(BigInteger target, BigInteger current) {
      if (shape == Shape.GENERIC) return original;
      if (shape == Shape.WINDOW) {
        int days = target.subtract(current).divide(BigInteger.valueOf(24)).intValueExact();
        if (days == 1) return "life-advance-one-day";
        RouteWindowStep value = window.orElseThrow();
        return new RouteWindowStep(value.subjectArmyId(), value.targetProvinceId(), value.hostileArmyIds(), days).canonical();
      }
      return prefix + target + suffix;
    }
    private static boolean int32(String value, boolean zero) {
      BigInteger number = new BigInteger(value);
      return number.signum() >= (zero ? 0 : 1) && number.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0;
    }
    private static boolean positiveLong(String value) { return new BigInteger(value).compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0; }
  }
  private static Draft draft(Draft original, String phase, String reason, Optional<ActionCommand> command, OpportunityJson.Obj detail) {
    return new Draft(original.policy(), phase, reason, original.kind(), command, original.purpose(), original.domain(), detail);
  }
  private static ExactRef source(ExactRef source) { Objects.requireNonNull(source); require(source.bytes() > 0, "actual implementation source required"); return source; }
  private static OpportunityJson.Obj json(byte[] raw) { return OpportunityJson.object(OpportunityJson.parse(raw), "producer JSON object"); }
  private static OpportunityJson.Text text(String value) { return new OpportunityJson.Text(value); }
  private static OpportunityJson.IntegerValue number(BigInteger value) { return new OpportunityJson.IntegerValue(value); }
  private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
  private static byte[] join(byte[]... parts) {
    var result = new java.io.ByteArrayOutputStream();
    for (byte[] part : parts) result.writeBytes(part);
    return result.toByteArray();
  }
  private static void require(boolean condition, String message) { StrictJson.require(condition, message); }
}

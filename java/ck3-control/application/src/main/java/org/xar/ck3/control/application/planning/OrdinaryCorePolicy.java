package org.xar.ck3.control.application.planning;

import java.math.BigInteger;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.military.WarCorePlanner;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision.PreparedSelection;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/**
 * Original ordinary core dispatch, postwar cleanup/checkpoint and peaceful
 * current-life sequence. War, native ruler marriage, Council19 and war-entry
 * producers run at their actual original call sites, not as later analysis.
 */
public final class OrdinaryCorePolicy implements OrdinaryPolicy {
    @FunctionalInterface public interface CoreProducer { Decision evaluate(PlanningRequest request, Draft previous); }
    @FunctionalInterface public interface CommandBinding {
        Bound propose(PlanningRequest request, OperationKey operation, Obj arguments, Obj originalPlan, Purpose purpose, Optional<Domain> domain);
    }
    public sealed interface Bound permits Prepared, OwnerPrepared, MissingHandler { }
    /** An unchanged exact-argument command; this branch cannot carry an enriched family envelope. */
    public record Prepared(ActionCommand command) implements Bound { public Prepared { Objects.requireNonNull(command); } }
    /** Strict original-selection custody minted through the actual Army or Life owner decoder. */
    public record OwnerPrepared(PreparedSelection preparation) implements Bound {
        public OwnerPrepared { Objects.requireNonNull(preparation); }
    }
    public record MissingHandler(String reason) implements Bound { public MissingHandler { StrictJson.text(reason); } }

    @FunctionalInterface public interface WarCoreFactory {
        WarCorePlanner create(WarCorePlanner.CoreContinuation continuation);
    }
    /** The actual mutually linked core and military planner, constructed together exactly once. */
    public record Assembly(OrdinaryCorePolicy core, WarCorePlanner war) {
        public Assembly {
            Objects.requireNonNull(core); Objects.requireNonNull(war);
            StrictJson.require(core.war == war, "assembly must retain its actual military planner");
        }
    }

    /**
     * Close the recognized-transition continuation with this same core producer.
     * The private link cannot return an empty policy during construction or be rebound later.
     */
    public static Assembly assemble(ExactRef source, WarCoreFactory warFactory, CoreProducer registeredEvents,
            CoreProducer council, CoreProducer rulerMarriage, CoreProducer warEntry,
            CommandBinding binding, Predicate<String> isAdvance) {
        CoreLink link = new CoreLink();
        WarCorePlanner war = Objects.requireNonNull(Objects.requireNonNull(warFactory).create(link),
                "actual military planner required");
        OrdinaryCorePolicy core = new OrdinaryCorePolicy(source, war, registeredEvents, council,
                rulerMarriage, warEntry, binding, isAdvance);
        link.bind(core);
        return new Assembly(core, war);
    }

    private static final class CoreLink implements WarCorePlanner.CoreContinuation {
        private OrdinaryCorePolicy target;
        private synchronized void bind(OrdinaryCorePolicy actual) {
            StrictJson.require(target == null, "ordinary core continuation can only be bound once");
            target = Objects.requireNonNull(actual);
        }
        @Override public Decision plan(PlanningRequest request, Draft previous) {
            OrdinaryCorePolicy actual;
            synchronized (this) { actual = target; }
            StrictJson.require(actual != null, "ordinary core continuation is not available during assembly");
            return actual.evaluate(request, previous);
        }
    }

    private final ExactRef source;
    private final WarCorePlanner war;
    private final CoreProducer registeredEvents;
    private final CoreProducer council;
    private final CoreProducer rulerMarriage;
    private final CoreProducer warEntry;
    private final CommandBinding binding;
    private final Predicate<String> isAdvance;

    public OrdinaryCorePolicy(ExactRef source, WarCorePlanner war, CoreProducer registeredEvents,
            CoreProducer council, CoreProducer rulerMarriage,
            CoreProducer warEntry, CommandBinding binding, Predicate<String> isAdvance) {
        this.source = Objects.requireNonNull(source); this.war = Objects.requireNonNull(war);
        this.registeredEvents = Objects.requireNonNull(registeredEvents);
        this.council = Objects.requireNonNull(council); this.rulerMarriage = Objects.requireNonNull(rulerMarriage);
        this.warEntry = Objects.requireNonNull(warEntry); this.binding = Objects.requireNonNull(binding);
        this.isAdvance = Objects.requireNonNull(isAdvance);
        StrictJson.require(source.bytes() > 0, "actual core implementation source required");
    }
    @Override public PlanningStage stage() { return PlanningStage.ORDINARY_CORE; }
    @Override public ExactRef implementationSource() { return source; }

    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        Objects.requireNonNull(request); Objects.requireNonNull(previous);
        // strategy8420..9091: dedicated Raiktor and the complete known registry
        // classify the current event before war preludes and peaceful actions.
        Decision eventDecision = Objects.requireNonNull(registeredEvents.evaluate(request, previous));
        Draft eventDraft = previous;
        if (eventDecision instanceof Annotate annotation) {
            requireAnnotation(previous, annotation.retained()); eventDraft = annotation.retained();
        } else if (!(eventDecision instanceof Keep) && !(eventDecision instanceof NotApplicable)) return eventDecision;
        WarCorePlanner.PreludeResult prelude = war.prelude(request, eventDraft);
        if (prelude instanceof WarCorePlanner.PreludeChosen chosen) return chosen.decision();
        Draft current = ((WarCorePlanner.PreludeContinue) prelude).draft();
        if (request.observations().warInProgress()) return war.activeWar(request, current);

        OrdinaryHistory history = OrdinaryHistory.collect(request.observations().history());
        List<Obj> armies = OpportunityJson.array(request.observations().snapshot().get("player_armies"), "player_armies").stream()
                .map(value -> OpportunityJson.object(value, "player army")).toList();
        Optional<Obj> strongest = armies.stream().filter(army -> yes(army.get("controllable")))
                .filter(army -> publicUnit(army.get("army_id")))
                .max(Comparator.comparing(OrdinaryCorePolicy::soldiers).thenComparing(
                        army -> integer(army.get("army_id"), "army_id"), Comparator.reverseOrder()));
        if (strongest.isPresent()) {
            BigInteger id = integer(strongest.orElseThrow().get("army_id"), "army_id");
            return select(request, current, "native_postwar_disband", "disband-army-" + id,
                    "no active war remains; disband the strongest residual player army",
                    empty().with("army_id", new IntegerValue(id)), Optional.of(Domain.war));
        }

        String lastError = history.last().map(row -> textOrEmpty(row.get("error"))).orElse("");
        if (lastError.contains("one-life death terminal visible:")) return select(request, current,
                "terminal_visible", "death-terminal", "player death is visibly stable; settle and end this episode", empty(), Optional.empty());
        if (lastError.contains("ordinary event interrupted")) return select(request, current,
                "visible_interruption", "resolve-current-event", "the previous timeline step stopped on a visible CK3 event", empty(), Optional.empty());
        if (history.latest("death-terminal") > 0) return select(request, current, "terminal", "strategy-review",
                "player death already ended this one-life episode", empty(), Optional.empty());
        if (history.latest("save-checkpoint") == 0) return select(request, current, "baseline", "save-checkpoint",
                "create a native CK3 recovery point before strategic mutations", empty(), Optional.empty());

        int saved = history.latest("save-checkpoint"), disbanded = history.latestPrefix("disband-army-");
        if (disbanded > saved && armies.isEmpty()) return select(request, current, "native_postwar_checkpoint", "save-checkpoint",
                "persist verified peaceful postwar cleanup before long-term governance",
                empty().with("postwar_disband_history_index", new IntegerValue(BigInteger.valueOf(disbanded))), Optional.empty());

        Decision councilDecision = Objects.requireNonNull(council.evaluate(request, current));
        if (councilDecision instanceof Annotate annotation) { requireAnnotation(current, annotation.retained()); current = annotation.retained(); }
        else if (councilDecision instanceof Replace replacement && retainsChoice(current, replacement.draft())) current = replacement.draft();
        else if (!(councilDecision instanceof Keep) && !(councilDecision instanceof NotApplicable)) return councilDecision;

        if (focus(request).filter("succession"::equals).isPresent() && history.latest("succession-review") == 0
                && available(request, "succession-review")) return select(request, current, "cross_run_succession_first", "succession-review",
                "the previous episode promoted succession review to the first strategic action", empty(), Optional.empty());

        Decision marriageDecision = Objects.requireNonNull(rulerMarriage.evaluate(request, current));
        if (marriageDecision instanceof Annotate annotation) { requireAnnotation(current, annotation.retained()); current = annotation.retained(); }
        // A ruler-family Replace is an explicit selected action, even if its full choice equals an earlier pending choice.
        else if (!(marriageDecision instanceof Keep) && !(marriageDecision instanceof NotApplicable)) return marriageDecision;

        Decision entry = Objects.requireNonNull(warEntry.evaluate(request, current));
        if (entry instanceof Annotate annotation) { requireAnnotation(current, annotation.retained()); current = annotation.retained(); }
        else if (entry instanceof Replace replacement && retainsChoice(current, replacement.draft())) current = replacement.draft();
        else if (!(entry instanceof Keep) && !(entry instanceof NotApplicable)) return entry;

        // These are retained legacy backend branches. Their exact registered
        // handlers/capabilities are still required; no visual action is invented.
        if (history.latest("dynasty-review") == 0) return select(request, current, "current_life_family", "dynasty-review",
                "read the current ruler's spouse, children and available family", empty(), Optional.empty());
        if (history.latest("succession-review") == 0) return select(request, current, "current_life_domain", "succession-review",
                "measure title loss that matters while the current ruler is alive", empty(), Optional.empty());
        if (history.latest("marriage-confirm-response") == 0) {
            String step; String reason;
            if (history.latest("marriage-review") == 0) { step = "marriage-review"; reason = "compare current-life alliance candidates"; }
            else if (history.latest("marriage-alliance") == 0) { step = "marriage-alliance"; reason = "send the selected current-life alliance proposal"; }
            else {
                int confirmation = history.latest("marriage-confirm-response", false);
                int elapsed = Math.max(Math.max(history.latest("war-advance-week"), history.latest("resolve-current-event")),
                        Math.max(history.latestMatching(isAdvance, true), history.latest("economic-event-cycle")));
                if (confirmation == 0 || elapsed > confirmation) { step = "marriage-confirm-response"; reason = "check the pending visible betrothal response"; }
                else { step = "war-advance-week"; reason = "advance one bounded week so the pending proposal can resolve"; }
            }
            return select(request, current, "current_life_marriage", step, reason, empty(), Optional.of(Domain.marriage));
        }
        int victory = history.latest("war-enforce-demands");
        if (victory == 0) {
            if (history.latest("war-declare-palermo") == 0) {
                Obj evidence = empty().with("declaration", empty().with("source", new Text("legacy-visual-palermo")).with("step", new Text("war-declare-palermo")));
                return blocked(current, "native_war_entry_evidence_required",
                        "the legacy Palermo declaration lacks same-epoch power, combat, campaign-cost and exit observations", evidence);
            }
            String step; String reason;
            if (history.latest("war-raise-all") == 0) { step = "war-raise-all"; reason = "raise the army for the active Palermo war"; }
            else if (history.latest("war-siege-palermo") == 0) { step = "war-siege-palermo"; reason = "move to the visibly confirmed Palermo fort"; }
            else {
                int statusIndex = history.latest("war-status");
                int advanceIndex = Math.max(history.latest("war-advance-week"), history.latest("war-advance-month"));
                Optional<Obj> status = history.latestEffectiveResult("war-status");
                Optional<BigInteger> score = status.filter(value -> value.get("war_status") instanceof Obj)
                        .map(value -> (Obj) value.get("war_status")).filter(value -> value.get("war_score_percent") instanceof IntegerValue)
                        .map(value -> integer(value.get("war_score_percent"), "war_score_percent"));
                if (statusIndex <= advanceIndex) { step = "war-status"; reason = "re-read visible war score after the latest campaign advance"; }
                else if (score.filter(value -> value.compareTo(BigInteger.valueOf(100)) >= 0).isPresent()) { step = "war-enforce-demands"; reason = "visible war score reached 100 percent"; }
                else { step = "war-advance-week"; reason = "continue the active siege for one bounded week"; }
            }
            return select(request, current, "palermo_war", step, reason, empty(), Optional.of(Domain.war));
        }
        int legacyDisband = history.latest("war-disband-armies");
        if (legacyDisband == 0 || legacyDisband < victory) return select(request, current, "postwar", "war-disband-armies",
                "remove raised-army costs after confirmed victory", empty(), Optional.of(Domain.war));
        int strategicChange = Math.max(victory, Math.max(legacyDisband, history.latest("marriage-confirm-response")));
        if (saved < strategicChange) return select(request, current, "post_milestone_checkpoint", "save-checkpoint",
                "persist the completed war and alliance milestones in a native save", empty(), Optional.empty());
        long cycles = history.countSuccessfulAfter(saved, step -> isAdvance.test(step) || step.equals("economic-event-cycle"));
        return cycles >= 3 ? select(request, current, "periodic_checkpoint", "save-checkpoint",
                "three completed event cycles have elapsed since the last native save", empty(), Optional.empty())
                : select(request, current, "current_life_loop", "life-advance",
                "advance to the next visible event and reassess the realm", empty(), Optional.empty());
    }

    public static Optional<String> focus(PlanningRequest request) {
        if (request.observations().campaignGoal().isPresent()) return Optional.of(OrdinaryCampaignGoal.plan(request.observations().campaignGoal().orElseThrow()).focus());
        return CrossRunPlanning.focus(request.observations().crossRunPlan());
    }

    private Decision select(PlanningRequest request, Draft previous, String phase, String step, String reason, Obj payload, Optional<Domain> domain) {
        Obj plan = merge(previous.detail(), payload).with("policy", new Text("one-life-turn-v1")).with("phase", new Text(phase))
                .with("selected_step", new Text(step)).with("reason", new Text(reason));
        plan = OriginalPlanRouting.route(plan, request.observations().actionSteps());
        phase = ((Text) plan.get("phase")).value();
        reason = ((Text) plan.get("reason")).value();
        if (!(plan.get("selected_step") instanceof Text routed))
            return new Replace(new Draft("one-life-turn-v1", phase, reason, Kind.ORDINARY,
                    Optional.empty(), Purpose.READ_ONLY, domain, plan), reason);
        if (!routed.value().equals(step)) payload = empty();
        step = routed.value();
        Purpose purpose = isAdvance.test(step) ? Purpose.DATE_ADVANCE : Purpose.WORLD_ACTION;
        Bound result = Objects.requireNonNull(binding.propose(request, new OperationKey(step), payload, plan, purpose, domain));
        if (result instanceof MissingHandler missing) return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, missing.reason());
        ActionCommand command;
        if (result instanceof OwnerPrepared owner) {
            command = owner.preparation().requireOriginalChoice(request, new OperationKey(step), payload, plan);
        } else {
            command = ((Prepared) result).command();
            StrictJson.require(command.arguments().equals(payload),
                    "exact core action binding changed the original selected arguments");
        }
        StrictJson.require(command.before().equals(request.before()) && command.source().equals(request.source())
                && command.sessionId().equals(request.sessionId()) && command.operation().value().equals(step)
                && !command.deadline().isAfter(request.deadline()),
                "core action binding changed the original choice or its complete source/frame");
        return new Replace(new Draft("one-life-turn-v1", phase, reason, Kind.ORDINARY,
                Optional.of(command), purpose, domain, plan), reason);
    }
    private static Decision blocked(Draft previous, String phase, String reason, Obj evidence) {
        Obj plan = merge(previous.detail(), evidence).with("policy", new Text("one-life-turn-v1")).with("phase", new Text(phase))
                .with("selected_step", OpportunityJson.Nil.INSTANCE).with("reason", new Text(reason));
        return new Replace(new Draft("one-life-turn-v1", phase, reason, Kind.ORDINARY,
                Optional.empty(), Purpose.READ_ONLY, Optional.of(Domain.war), plan), reason);
    }
    private static BigInteger soldiers(Obj row) { return row.get("soldiers") instanceof IntegerValue number ? number.value() : BigInteger.valueOf(-1); }
    private static boolean publicUnit(OpportunityJson.Value raw) { return raw instanceof IntegerValue number && number.value().signum() >= 0 && number.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0; }
    private static BigInteger integer(OpportunityJson.Value value, String field) { return OpportunityJson.integer(value, field); }
    private static String textOrEmpty(OpportunityJson.Value value) { return value instanceof Text text ? text.value() : ""; }
    private static boolean yes(OpportunityJson.Value value) { return value instanceof Bool bool && bool.value(); }
    private static boolean available(PlanningRequest request, String operation) { return request.observations().actionSteps().contains(new OperationKey(operation)); }
    private static Obj empty() { return new Obj(java.util.Map.of()); }
    private static Obj merge(Obj previous, Obj next) {
        java.util.Map<String, OpportunityJson.Value> fields = new java.util.LinkedHashMap<>(previous.members());
        fields.putAll(next.members()); return new Obj(fields);
    }
    private static boolean retainsChoice(Draft before, Draft after) {
        return before.command().equals(after.command()) && before.policy().equals(after.policy()) && before.phase().equals(after.phase())
                && before.reason().equals(after.reason()) && before.kind() == after.kind() && before.purpose() == after.purpose()
                && before.domain().equals(after.domain());
    }
    private static void requireAnnotation(Draft before, Draft after) { StrictJson.require(retainsChoice(before, after), "core annotation changed the actual chosen action"); }
}

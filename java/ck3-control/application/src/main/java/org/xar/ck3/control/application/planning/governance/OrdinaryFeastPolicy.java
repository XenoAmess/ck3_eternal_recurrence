package org.xar.ck3.control.application.planning.governance;

import java.math.BigInteger;
import org.xar.ck3.control.governance.activity.ActivityPlannerDiagnostic;
import org.xar.ck3.control.governance.activity.ActivityConfigurationModels;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy;
import org.xar.ck3.control.finance.feastvalue.FeastValueCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.planning.optionalcadence.CadenceJson;
import org.xar.ck3.control.planning.optionalcadence.CadenceModels;
import org.xar.ck3.control.planning.optionalcadence.OptionalCheckCadence;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;
import static org.xar.ck3.control.application.planning.governance.FeastObservationSupplier.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;

/** Original ordinary Feast branch: reconcile, diagnose, configure or assess one actual Start. */
public final class OrdinaryFeastPolicy implements OrdinaryPolicy {
    public static final OperationKey CONFIGURE = new OperationKey("open-activity-feast-planner-v1-private");
    public static final OperationKey CONFIRM = new OperationKey("confirm-activity-feast-stage1-v1-private");
    public static final OperationKey DESTINATION = new OperationKey("select-activity-feast-stage2-destination-v1-private");
    public static final OperationKey START = new OperationKey("start-activity-feast-stage5-v1-private");
    public static final Set<OperationKey> OWNED = Set.of(CONFIGURE, CONFIRM, DESTINATION, START);
    @FunctionalInterface public interface Effects {
        Optional<ExpectedPostcondition> expected(OperationKey operation, PlanningRequest request, Obj arguments);
    }
    private final ExactRef source;
    private final FeastObservationSupplier supplier;
    private final Effects effects;

    public OrdinaryFeastPolicy(ExactRef source, FeastObservationSupplier supplier, Effects effects) {
        this.source = Objects.requireNonNull(source); this.supplier = Objects.requireNonNull(supplier);
        this.effects = Objects.requireNonNull(effects);
        StrictJson.require(source.bytes() > 0, "actual Java Feast producer source required");
    }
    @Override public PlanningStage stage() { return PlanningStage.FEAST; }
    @Override public ExactRef implementationSource() { return source; }

    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
        try {
            if (OWNED.stream().noneMatch(request.observations().actionSteps()::contains))
                return new NotApplicable("no original Feast action route is enabled");
            Read<State> read = supplier.state(request);
            if (read instanceof Unavailable<State> unavailable) return defer(unavailable.reason());
            State state = ((Known<State>) read).value(); state.bind(request);
            List<ActionReceipt> unresolved = state.actualReceipts().stream()
                    .filter(receipt -> OWNED.contains(receipt.command().operation()) && !receipt.settled()).toList();
            if (unresolved.size() > 1) return defer("multiple retained Feast commands require exact original reconciliation");
            if (unresolved.size() == 1) {
                ActionReceipt original = unresolved.getFirst();
                return new ReconcileExisting(original.command().actionId(), obj("original_command",
                        object(parse(ActionCodec.encodeCommand(original.command())), "original Feast command"),
                        "original_receipt_sequence", n(original.sequence()), "original_body_sha256", new Text(original.bodySha256())),
                        "observe the original Feast command; UNKNOWN is never another configuration or Start");
            }
            if (state.pending().isPresent()) return defer("legacy Feast pending intent has not been imported as its exact original command");
            if (!isAdvance(previous)) return new NotApplicable("Feast preserves the original earlier choice");
            var frame = cadenceFrame(request);
            if (OptionalCheckCadence.deferred(state.cadence(), CadenceModels.Domain.FEAST, frame).isPresent())
                return new Keep("the existing optional Feast review is not due");
            Read<Planner> plannerRead = supplier.planner(request);
            if (plannerRead instanceof Unavailable<Planner> unavailable) return defer(unavailable.reason());
            Planner planner = ((Known<Planner>) plannerRead).value();
            if (planner.needsConfiguration()) {
                Read<Hosted> hostedRead = supplier.hosted(request);
                if (hostedRead instanceof Unavailable<Hosted> unavailable) return defer(unavailable.reason());
                Hosted hosted = ((Known<Hosted>) hostedRead).value();
                StrictJson.require(hosted.actorId().equals(request.before().frame().identity().player()), "Feast hosted actor drift");
                if (hosted.unresolved(state.terminal())) return noAction(previous, request, state,
                        obj("status", new Text("current_feast_unresolved"), "hosted_observation", hosted.original()));
                Read<Obj> rootRead = supplier.root(request);
                if (rootRead instanceof Unavailable<Obj> unavailable) return defer(unavailable.reason());
                Obj root = ((Known<Obj>) rootRead).value();
                var capital = root.get("capital_province_id");
                if (!(capital instanceof IntegerValue integer) || integer.value().signum() <= 0
                        || integer.value().compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) > 0)
                    return noAction(previous, request, state, obj("status", new Text("current_capital_unavailable")));
                Configuration action = configuration(request, planner, hosted, root);
                if (action instanceof ConfigurationHeld held) return noAction(previous, request, state, held.evidence());
                ConfigurationReady ready = (ConfigurationReady) action;
                if (state.actualReceipts().stream().anyMatch(receipt -> receipt.command().operation().equals(ready.operation())
                        && receipt.command().before().equals(request.before())))
                    return noAction(previous, request, state, obj("status", new Text("primitive_already_attempted_this_frame"),
                            "operation", new Text(ready.operation().value())));
                return selected(request, previous, ready.operation(), ready.arguments(), "activity_feast_ordinary_configuration",
                        "perform one current native-legal Feast configuration primitive");
            }
            if (planner.kind() != ActivityPlannerDiagnostic.Kind.FEAST_STAGE_FIVE) return noAction(previous, request, state,
                    obj("status", new Text("configuration_not_stage1_or_stage5"), "planner_observation", planner.original()));
            Read<OrdinaryFinanceCollector.Spending> spendingRead = supplier.spending(request);
            if (spendingRead instanceof Unavailable<OrdinaryFinanceCollector.Spending> unavailable) return defer(unavailable.reason());
            Read<OrdinaryFinanceCollector.Feast> feastRead = supplier.feast(request,
                    ((Known<OrdinaryFinanceCollector.Spending>) spendingRead).value());
            if (feastRead instanceof Unavailable<OrdinaryFinanceCollector.Feast> unavailable) return defer(unavailable.reason());
            var feast = ((Known<OrdinaryFinanceCollector.Feast>) feastRead).value();
            if (feast.value().decision() != FeastStage5ValuePolicy.Decision.START)
                return noAction(previous, request, state, obj("inputs", feast.inputs(),
                        "decision", object(parse(FeastValueCodec.encodeAssessment(feast.value())), "actual Feast assessment")));
            return selected(request, previous, START, startArguments(request, feast), "activity_feast_ordinary_start",
                    "start the current native-legal Feast with qualified guest arrival and actual commitments");
        } catch (IllegalArgumentException invalid) {
            return defer("current Feast input rejected: " + invalid.getMessage());
        }
    }

    /** The coordinator invokes this inside its existing writer lock, before dispatching the original intent. */
    public void revalidate(ActionCommand command, PlanningRequest fresh) {
        StrictJson.require(OWNED.contains(command.operation()) && command.before().equals(fresh.before())
                && command.source().equals(fresh.source()) && command.sessionId().equals(fresh.sessionId()), "Feast submit source drift");
        Obj actual;
        if (!command.operation().equals(START)) {
            Planner planner = required(supplier.planner(fresh)); Hosted hosted = required(supplier.hosted(fresh));
            StrictJson.require(planner.needsConfiguration(), "Feast configuration stage drift");
            State state = required(supplier.state(fresh)); state.bind(fresh);
            StrictJson.require(!hosted.unresolved(state.terminal()), "a current Feast remains unresolved");
            Configuration next = configuration(fresh, planner, hosted, required(supplier.root(fresh)));
            StrictJson.require(next instanceof ConfigurationReady, "fresh Feast primitive is held by native legality");
            var ready = (ConfigurationReady) next;
            StrictJson.require(ready.operation().equals(command.operation()), "fresh Feast primitive stage drift");
            actual = ready.arguments();
        } else {
            var feast = required(supplier.feast(fresh, required(supplier.spending(fresh))));
            StrictJson.require(feast.value().decision() == FeastStage5ValuePolicy.Decision.START, "fresh Feast value/funding held Start");
            actual = startArguments(fresh, feast);
        }
        StrictJson.require(actual.equals(command.arguments()), "fresh Feast arguments/quote drift");
        StrictJson.require(effects.expected(command.operation(), fresh, actual).filter(command.expected()::equals).isPresent(),
                "actual independent Feast effect handler is absent or changed");
    }
    private Decision selected(PlanningRequest request, Draft previous, OperationKey operation, Obj args, String phase, String reason) {
        if (!request.observations().actionSteps().contains(operation)) return defer("actual Feast operation is not registered: " + operation.value());
        Optional<ExpectedPostcondition> expected = effects.expected(operation, request, args);
        if (expected.isEmpty()) return defer("actual independent Feast material handler is absent: " + operation.value());
        String actionId = ActionIds.forDecision(request.sessionId(), request.before(), operation.value() + ":" + ActionCodec.sha256(encode(args)));
        var claims = new Claims(Set.of(), Set.of(), Set.of(), Set.of("activity-feast:" + request.before().frame().identity().player()));
        ActionCommand command = new ActionCommand(actionId, request.before(), request.source(), request.sessionId(), operation,
                args, expected.orElseThrow(), claims, request.deadline());
        return new Replace(new Draft("ordinary-governance-java-v1", phase, reason, Kind.ORDINARY, Optional.of(command),
                Purpose.WORLD_ACTION, Optional.of(Domain.diplomacy), obj("activity_feast_opportunity", args,
                        "original_plan", previous.detail())), reason);
    }
    private sealed interface Configuration permits ConfigurationReady, ConfigurationHeld { }
    private record ConfigurationReady(OperationKey operation, Obj arguments) implements Configuration { }
    private record ConfigurationHeld(Obj evidence) implements Configuration { }
    private Configuration configuration(PlanningRequest request, Planner planner, Hosted hosted, Obj root) {
        BigInteger province = integer(root.get("capital_province_id"), "capital province");
        StrictJson.require(province.signum() > 0 && province.compareTo(BigInteger.valueOf(Integer.MAX_VALUE)) <= 0, "invalid Feast capital");
        Obj evidence = obj("planner_observation", planner.original(), "hosted_observation", hosted.original(),
                "campaign_root", root, "source_frame", OrdinaryFinanceCollector.sourceFrame(request));
        if (planner.kind() == ActivityPlannerDiagnostic.Kind.ABSENT)
            return new ConfigurationReady(CONFIGURE, evidence.with("activity_phase", new Text("open")).with("native_arguments", obj()));
        if (planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_ONE) {
            ActivityConfigurationModels.StageOne option = required(supplier.stageOne(request));
            bindConfiguration(request, option.frame());
            evidence = evidence.with("stage1_option", option.original());
            if (!option.ready()) return new ConfigurationHeld(evidence.with("status", new Text("generic_feast_confirm_held")));
            return new ConfigurationReady(CONFIRM, evidence.with("activity_phase", new Text("confirm"))
                    .with("native_arguments", FeastObservationCollector.stageArguments(request)));
        }
        StrictJson.require(planner.kind() == ActivityPlannerDiagnostic.Kind.FEAST_STAGE_TWO, "unknown Feast configuration stage");
        ActivityConfigurationModels.StageTwo option = required(supplier.stageTwo(request));
        ActivityConfigurationModels.Location location = required(supplier.location(request, province.intValueExact()));
        bindConfiguration(request, option.frame()); bindConfiguration(request, location.frame());
        evidence = evidence.with("stage2_option", option.original()).with("stage2_location", location.original());
        boolean destinationReady = option.genericFeastSelected() && location.singleLocation() && location.previousStage() == 1
                && location.activeRowIndex().equals(Optional.of(0)) && location.rows().size() == 2
                && location.rows().stream().allMatch(row -> row.provinceId() == 0) && !location.canProgress()
                && location.candidates().stream().anyMatch(candidate -> candidate.provinceId() == province.intValueExact() && candidate.canSelect());
        if (!destinationReady) return new ConfigurationHeld(evidence.with("status", new Text("native_capital_destination_held")));
        return new ConfigurationReady(DESTINATION, evidence.with("activity_phase", new Text("destination"))
                .with("native_arguments", FeastObservationCollector.stageArguments(request)
                .with("province_id", new IntegerValue(province))));
    }
    private static void bindConfiguration(PlanningRequest request, ActivityConfigurationModels.Frame observed) {
        var identity = request.before().frame().identity();
        StrictJson.require(observed.equals(new ActivityConfigurationModels.Frame(identity.nativeRevision(), identity.dateRaw(), identity.player())),
                "Feast configuration evidence crossed the current native actor/date/revision");
    }
    private static Obj startArguments(PlanningRequest request, OrdinaryFinanceCollector.Feast feast) {
        return obj("inputs", feast.inputs(), "assessment", object(parse(FeastValueCodec.encodeAssessment(feast.value())), "actual Feast value"),
                "source_frame", OrdinaryFinanceCollector.sourceFrame(request), "new_attempt", new Bool(true));
    }
    private static Decision noAction(Draft previous, PlanningRequest request, State state, Obj opportunity) {
        Obj detail = GovernanceCadencePublication.append(previous.detail().with("activity_feast_opportunity", opportunity),
                CadenceModels.Domain.FEAST, request, state.cadence());
        return new Annotate(new Draft(previous.policy(), previous.phase(), previous.reason(), previous.kind(), previous.command(),
                previous.purpose(), previous.domain(), detail), "complete native Feast read retained the original choice");
    }
    private static CadenceModels.Frame cadenceFrame(PlanningRequest request) {
        var frame = request.before().frame(); return new CadenceModels.Frame(frame.episodeRunId(), frame.identity().dateRaw(), frame.identity().nativeRevision());
    }
    private static boolean isAdvance(Draft previous) {
        return previous.kind() == Kind.ORDINARY && previous.command().filter(command -> command.operation().value().equals("life-advance")).isPresent();
    }
    private static Defer defer(String reason) { return new Defer(reason, obj("stage", new Text("feast"), "business_credit", new Bool(false))); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static <T> T required(Read<T> read) {
        if (read instanceof Unavailable<T> unavailable) throw new IllegalArgumentException(unavailable.reason());
        return ((Known<T>) read).value();
    }
}

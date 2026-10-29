package org.xar.ck3.control.nativebridge.capabilities.army;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectEvidence.FrameLoader;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeRegularMaaSubmission;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind;

/** Public and ordinary consumers of the same installed native producers, coordinator, effects and immutable archive. */
public final class ArmyOrdinaryActionService {
    @FunctionalInterface public interface Current { ArmyTypes.Context current(); }
    @FunctionalInterface public interface ActionIds { String next(ContinuityStorePort.Session original, ArmyTypes.Context source) throws IOException; }
    @FunctionalInterface public interface Expected {
        ExpectedPostcondition expected(ObservationIdentity before, G2Source source, OperationKey operation, RawJson originalArguments);
    }
    @FunctionalInterface public interface Replay {
        NativeRecordedEvidenceVerifier.Binding binding(OperationKey operation);
    }
    @FunctionalInterface public interface Commander {
        /** Delegate to the identical CommanderBindings.actionFamily used by ordinary planning. */
        ActionReceipt assign(ContinuityStorePort.Session same, ArmyCalls.AssignCommander input, ArmyTypes.Context source, String actionId);
    }
    @FunctionalInterface public interface Mercenary {
        /** Collect and qualify through the original FinanceRuntimeServices, retaining its full strategic quote and pending body. */
        ActionReceipt hire(ContinuityStorePort.Session same, ArmyCalls.Hire input, ArmyTypes.Context source, String actionId);
    }
    public record Sources(ExactRef producer, ExactRef decoder, ExactRef service) {
        public Sources { for (ExactRef ref : List.of(producer, decoder, service)) StrictJson.require(ref.bytes() > 0, "actual Army Java source required"); }
    }
    public record Effect(Kind kind, ExactRef source, NativeEffectRegistry.Observer observer, Expected expected, Replay replay) {
        public Effect {
            Objects.requireNonNull(kind); StrictJson.require(source != null && source.bytes() > 0, "actual independent Army verifier source required");
            Objects.requireNonNull(observer); Objects.requireNonNull(expected); Objects.requireNonNull(replay);
            StrictJson.require(kind != Kind.ASSIGN_ARMY_COMMANDER_V1 && kind != Kind.HIRE_MERCENARY_V1,
                    "Commander and mercenary hire have their unique existing installed families");
        }
    }
    public record Reply(ArmyCalls.Call input, ArmyTypes.Context context, ActionReceipt actual, OpportunityJson.Obj compatibleMaterial) {
        public Reply {
            Objects.requireNonNull(input); Objects.requireNonNull(context); Objects.requireNonNull(actual); Objects.requireNonNull(compatibleMaterial);
            StrictJson.require(actual.command().before().equals(context.before()) && actual.command().source().equals(context.source())
                    && actual.command().sessionId().equals(context.sessionId()), "Army public reply changed the original action source");
        }
    }
    private final ContinuityWriter writer;
    private final ActionCoordinatorPort actions;
    private final ActionPorts.OutcomeArchive archive;
    private final ArmyOrdinaryActionPreparation preparation;
    private final Supplier<RootExecutableBindings> catalog;
    private final Current current;
    private final ActionIds ids;
    private final Sources sources;
    private final Optional<Commander> commander;
    private final Optional<Mercenary> mercenary;
    private final Clock clock;
    private final Optional<FrameLoader> directFrames;
    private final EnumMap<Kind,Effect> effects = new EnumMap<>(Kind.class);
    private final EnumMap<Kind,RootExecutableBindings.Family<ArmyOrdinaryActionPreparation.Qualified>> families = new EnumMap<>(Kind.class);
    public ArmyOrdinaryActionService(ContinuityWriter originalWriter, ActionCoordinatorPort soleCoordinator, ActionPorts.OutcomeArchive sameArchive,
            ArmyOrdinaryActionPreparation actualPreparation, Supplier<RootExecutableBindings> identicalInstalledCatalog,
            Current actualCurrent, ActionIds actualRootIds, Sources actualSources, List<Effect> independentEffects,
            Optional<Commander> existingCommander, Optional<Mercenary> existingMercenary, Clock actualClock) {
        this(originalWriter, soleCoordinator, sameArchive, actualPreparation, identicalInstalledCatalog, actualCurrent, actualRootIds, actualSources, independentEffects, existingCommander, existingMercenary, actualClock, Optional.empty());
    }
    public ArmyOrdinaryActionService(ContinuityWriter originalWriter, ActionCoordinatorPort soleCoordinator, ActionPorts.OutcomeArchive sameArchive,
            ArmyOrdinaryActionPreparation actualPreparation, Supplier<RootExecutableBindings> identicalInstalledCatalog,
            Current actualCurrent, ActionIds actualRootIds, Sources actualSources, List<Effect> independentEffects,
            Optional<Commander> existingCommander, Optional<Mercenary> existingMercenary, Clock actualClock, FrameLoader actualOriginalFrames) {
        this(originalWriter, soleCoordinator, sameArchive, actualPreparation, identicalInstalledCatalog, actualCurrent, actualRootIds, actualSources, independentEffects, existingCommander, existingMercenary, actualClock, Optional.of(Objects.requireNonNull(actualOriginalFrames)));
    }
    private ArmyOrdinaryActionService(ContinuityWriter originalWriter, ActionCoordinatorPort soleCoordinator, ActionPorts.OutcomeArchive sameArchive,
            ArmyOrdinaryActionPreparation actualPreparation, Supplier<RootExecutableBindings> identicalInstalledCatalog,
            Current actualCurrent, ActionIds actualRootIds, Sources actualSources, List<Effect> independentEffects,
            Optional<Commander> existingCommander, Optional<Mercenary> existingMercenary, Clock actualClock, Optional<FrameLoader> actualDirectFrames) {
        writer = Objects.requireNonNull(originalWriter); actions = Objects.requireNonNull(soleCoordinator); archive = Objects.requireNonNull(sameArchive);
        preparation = Objects.requireNonNull(actualPreparation); catalog = Objects.requireNonNull(identicalInstalledCatalog);
        current = Objects.requireNonNull(actualCurrent); ids = Objects.requireNonNull(actualRootIds); sources = Objects.requireNonNull(actualSources); commander = Objects.requireNonNull(existingCommander);
        mercenary = Objects.requireNonNull(existingMercenary);
        clock = Objects.requireNonNull(actualClock); directFrames = Objects.requireNonNull(actualDirectFrames);
        for (Effect effect : List.copyOf(independentEffects)) {
            StrictJson.require(effects.putIfAbsent(effect.kind(), effect) == null, "two effects claim one Army action family");
            var family = new RootExecutableBindings.Family<>("army-ordinary-" + effect.kind().wire(), ArmyOrdinaryActionPreparation.Qualified.class,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, capability(effect.kind()), sources.producer(), sources.decoder(), effect.source(),
                    q -> { requireKind(q.call(), effect.kind()); return operationKey(q.request().step()); },
                    q -> new OperationKey(q.request().step()), q -> issue(effect, q));
            families.put(effect.kind(), family);
        }
    }
    /** The composition root must install these identical family objects before any public invocation. */
    public List<RootExecutableBindings.Family<?>> actionFamilies() { return new ArrayList<>(families.values()); }
    public Set<Kind> supported() {
        var selected = java.util.EnumSet.noneOf(Kind.class); selected.addAll(effects.keySet()); if (commander.isPresent()) selected.add(Kind.ASSIGN_ARMY_COMMANDER_V1);
        if (mercenary.isPresent()) selected.add(Kind.HIRE_MERCENARY_V1); return Set.copyOf(selected);
    }
    public Reply handle(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source, String actualRootActionId) {
        try {
            source = deadline(input, source);
            writer.requireSession(same); Kind kind = ArmyOrdinaryActionPreparation.kind(input); StrictJson.text(actualRootActionId);
            var bound = archive.withSession(same); var head = same.head();
            Optional<ActionReceipt> old = ContinuityActionJournal.lookup(head.state(), actualRootActionId, bound);
            if (old.isPresent()) {
                ActionReceipt original = old.orElseThrow();
                StrictJson.require(original.command().before().equals(source.before()) && original.command().source().equals(source.source())
                        && original.command().sessionId().equals(source.sessionId()), "existing Army action ID belongs to a different original caller source");
                if (kind != Kind.ASSIGN_ARMY_COMMANDER_V1 && kind != Kind.HIRE_MERCENARY_V1) {
                    var saved = ArmyOrdinaryActionArguments.decode(original.command().arguments());
                    StrictJson.require(saved.kind() == kind && ArmyCallCodec.decode(input.method(), saved.publicArguments()).equals(input), "existing Army action ID changed its public selection");
                } else requireDelegatedSelection(input, original);
                // Reconcile reads only the original request. It never starts another attempt.
                return finish(same, input, source, actions.reconcile(same, actualRootActionId));
            }
            StrictJson.require(supported().contains(kind), "Army action has no installed actual producer/effect/archive replay family");
            if (input instanceof ArmyCalls.Frame fixed && (fixed.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                    || fixed.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1)) preparation.currentDirectFixedWindow(fixed, source);
            else { input.revision().requireCurrent(source.before().frame().revision()); preparation.current(source); }
            rejectReplay(ContinuityActionJournal.receipts(head.state(), bound), input, source);
            if (input instanceof ArmyCalls.AssignCommander assignment) {
                ActionReceipt result = commander.orElseThrow().assign(same, assignment, source, actualRootActionId);
                return finish(same, input, source, result);
            }
            if (input instanceof ArmyCalls.Hire hire && kind == Kind.HIRE_MERCENARY_V1)
                return finish(same, input, source, mercenary.orElseThrow().hire(same, hire, source, actualRootActionId));
            ActionCommand command = input instanceof ArmyCalls.Frame fixed
                    && (fixed.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 || fixed.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1)
                    ? prepareDirectFixedWindowCommand(same, fixed, source, actualRootActionId)
                    : prepareCommand(same, input, source, actualRootActionId);
            ActionReceipt result = actions.execute(same, command); writer.requireSession(same);
            return finish(same, input, source, result);
        } catch (IOException failure) { throw new UncheckedIOException("same-writer Army action unavailable", failure); }
    }
    /** The specialized SDK producer retains its original explicit policy and never submits here. */
    public ActionCommand prepareCommand(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source, String actualRootActionId) {
        return prepareProfile(same, input, source, actualRootActionId, ArmyOrdinaryActionArguments.ExecutionProfile.SDK_ORDINARY);
    }
    /** Retains the original ordinary selection under the same writer before catalog issuance. No submission occurs here. */
    public ActionCommand preparePlannerCommand(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source,
            String actualRootActionId, ArmyOrdinaryPlannerSelection.Selection originalSelection) {
        Objects.requireNonNull(originalSelection);
        StrictJson.require(originalSelection.kind() == ArmyOrdinaryActionPreparation.kind(input)
                && DriverJson.object(originalSelection.publicArguments().bytes(), 65536).equals(
                        DriverJson.object(ArmyCallCodec.encode(input).bytes(), 65536)), "planner selection differs from the actual Army Call");
        var profile = input instanceof ArmyCalls.War war && war.method() == PublicMethod.SURRENDER_WAR
                ? ArmyOrdinaryActionArguments.ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER
                : ArmyOrdinaryActionArguments.ExecutionProfile.SDK_ORDINARY;
        return prepareProfile(same, input, source, actualRootActionId, profile, Optional.of(originalSelection));
    }
    /** Original generic execute_step policy. The Root owns INTENT, once fences and the single physical submission. */
    public ActionCommand prepareGenericAutomaticSurrenderCommand(ContinuityStorePort.Session same, ArmyCalls.War input,
            ArmyTypes.Context source, String actualRootActionId) {
        StrictJson.require(input.method() == PublicMethod.SURRENDER_WAR, "generic automatic preparation only accepts surrender");
        return prepareProfile(same, input, source, actualRootActionId, ArmyOrdinaryActionArguments.ExecutionProfile.GENERIC_AUTOMATIC_SURRENDER);
    }
    /** Original generic fixed-window close commands are frame-bound and do not issue a before query. */
    public ActionCommand prepareDirectFixedWindowCommand(ContinuityStorePort.Session same, ArmyCalls.Frame input,
            ArmyTypes.Context source, String actualRootActionId) {
        StrictJson.require(directFrames.isPresent(), "direct fixed-window original basis decoder is not installed for this actual service");
        StrictJson.require(input.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 || input.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1,
                "direct fixed-window preparation only accepts the two original close methods");
        return prepareProfile(same, input, source, actualRootActionId, ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW);
    }
    private ActionCommand prepareProfile(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source, String actualRootActionId,
            ArmyOrdinaryActionArguments.ExecutionProfile profile) {
        return prepareProfile(same, input, source, actualRootActionId, profile, Optional.empty());
    }
    private ActionCommand prepareProfile(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source, String actualRootActionId,
            ArmyOrdinaryActionArguments.ExecutionProfile profile, Optional<ArmyOrdinaryPlannerSelection.Selection> originalSelection) {
        Objects.requireNonNull(originalSelection);
        try {
            source = deadline(input, source); writer.requireSession(same); StrictJson.text(actualRootActionId);
            Kind kind = ArmyOrdinaryActionPreparation.kind(input);
            StrictJson.require(kind != Kind.ASSIGN_ARMY_COMMANDER_V1 && kind != Kind.HIRE_MERCENARY_V1,
                    "commander and mercenary command production belongs to its original domain family");
            StrictJson.require(supported().contains(kind), "Army command has no installed original observer/replay pair");
            var bound = archive.withSession(same);
            StrictJson.require(ContinuityActionJournal.lookup(same.head().state(), actualRootActionId, bound).isEmpty(),
                    "existing Army action identity must collect its original request without preparing again");
            Complete actualCurrent;
            if (profile == ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW)
                actualCurrent = preparation.currentDirectFixedWindow((ArmyCalls.Frame) input, source);
            else { input.revision().requireCurrent(source.before().frame().revision()); actualCurrent = preparation.current(source); }
            var previous = ContinuityActionJournal.receipts(same.head().state(), bound);
            rejectReplay(previous, input, source);
            if (input instanceof ArmyCalls.Frame fixed && (fixed.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                    || fixed.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1))
                rejectDirectWindowDeferred(previous, fixed, actualCurrent, bound, directFrames.orElseThrow(
                        () -> new IllegalStateException("fixed-window original retry basis decoder unavailable")));
            var selected = switch (profile) {
                case SDK_ORDINARY -> preparation.qualify(same, input, source);
                case GENERIC_AUTOMATIC_SURRENDER -> preparation.qualifyGenericAutomaticSurrender(same, (ArmyCalls.War) input, source);
                case DIRECT_FIXED_WINDOW -> preparation.qualifyDirectFixedWindow(same, (ArmyCalls.Frame) input, source);
            };
            if (originalSelection.isPresent()) {
                var retained = selected.arguments().withTerminalSelection(originalSelection.orElseThrow().terminalSelection());
                selected = new ArmyOrdinaryActionPreparation.Qualified(selected.call(), selected.context(), selected.actual(),
                        selected.reads(), retained, selected.request(), selected.claims());
            }
            Effect effect = effects.get(kind);
            RootExecutableBindings actualCatalog = Objects.requireNonNull(catalog.get(), "actual Army catalog has not been frozen");
            actualCatalog.issue(Objects.requireNonNull(families.get(kind)), selected);
            OperationKey operation = new OperationKey(selected.request().step());
            ExpectedPostcondition expected = Objects.requireNonNull(effect.expected().expected(source.before(), source.source(), operation, selected.arguments().raw()));
            var command = new ActionCommand(actualRootActionId, source.before(), source.source(), source.sessionId(), operation,
                    selected.arguments().encode(), expected, selected.claims(), source.deadline());
            writer.requireSession(same); return command;
        } catch (IOException failure) { throw new UncheckedIOException("same-writer Army command producer unavailable", failure); }
    }
    public Reply reconcile(ContinuityStorePort.Session same, String originalActionId) {
        try {
            writer.requireSession(same); var bound = archive.withSession(same);
            var old = ContinuityActionJournal.lookup(same.head().state(), originalActionId, bound)
                    .orElseThrow(() -> new IllegalArgumentException("original Army action does not exist in this writer"));
            ArmyCalls.Call call;
            if (old.command().operation().value().equals("hire-mercenary-v1")) {
                var id = OpportunityJson.integer(old.command().arguments().get("company_id"), "canonical finance company").longValueExact();
                call = new ArmyCalls.Hire(PublicMethod.HIRE_MERCENARY_V1, new ArmyCalls.Revision(new ArmyTypes.Present<>(old.command().before().frame().revision())), new ArmyTypes.HireId(id));
            } else if (old.command().operation().value().startsWith("assign-army-commander-v1-army-")) {
                var selected = org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition.arguments(old.command().arguments());
                call = new ArmyCalls.AssignCommander(new ArmyCalls.Revision(new ArmyTypes.Present<>(old.command().before().frame().revision())),
                        new ArmyTypes.PublicUnitId(selected.army().intValueExact()), new ArmyTypes.PublicUnitId(selected.character().intValueExact()));
            } else {
                var input = ArmyOrdinaryActionArguments.decode(old.command().arguments());
                call = ArmyCallCodec.decode(PublicMethod.valueOf(input.kind().name()), input.publicArguments());
            }
            var source = new ArmyTypes.Context(old.command().before(), old.command().source(), old.command().sessionId(), old.command().deadline());
            return finish(same, call, source, actions.reconcile(same, originalActionId));
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    private RootExecutableBindings.IssuedAction issue(Effect effect, ArmyOrdinaryActionPreparation.Qualified selected) {
        requireKind(selected.call(), effect.kind()); OperationKey operation = new OperationKey(selected.request().step());
        StrictJson.require(selected.request().requiredCapability().equals(capability(effect.kind())), "Army family capability drift");
        var nativeEffect = new NativeEffectRegistry.Binding(operation, sources.producer(), preparation, effect.observer());
        var replay = Objects.requireNonNull(effect.replay().binding(operation));
        StrictJson.require(replay.operation().equals(operation) && replay.definitionSource().equals(effect.source()), "Army live effect and archived replay pair changed");
        return new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(nativeEffect,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, capability(effect.kind()), sources.decoder()), replay);
    }
    private Reply finish(ContinuityStorePort.Session same, ArmyCalls.Call input, ArmyTypes.Context source, ActionReceipt result) throws IOException {
        writer.requireSession(same); var bound = archive.withSession(same);
        StrictJson.require(ContinuityActionJournal.lookup(same.head().state(), result.command().actionId(), bound).orElseThrow().equals(result),
                "Army public result is not the actual canonical writer receipt");
        RootExecutableBindings actualCatalog = Objects.requireNonNull(catalog.get());
        Optional<RawJson> material = ActionTransitions.attempt(result.state()).flatMap(attempt -> actualCatalog.effects().compatibleResult(result.command().actionId(), attempt.requestId()));
        var arguments = input instanceof ArmyCalls.Frame && (input.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                || input.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1) ? ArmyOrdinaryActionArguments.decode(result.command().arguments()) : null;
        if (arguments != null && arguments.executionProfile() == ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW) {
            var original = NativeDirectFixedWindowObservation.load(result, bound, directFrames.orElseThrow(
                    () -> new IllegalStateException("direct fixed-window original basis decoder unavailable")));
            return new Reply(input, source, result, DriverJson.object(original.normalized().bytes(), DriverJson.MAX_NATIVE_BYTES));
        }
        return new Reply(input,source,result,resultMaterial(input,result,material,bound));
    }
    /** Result representation and immutable material custody; finish first verifies the actual canonical writer result. */
    static OpportunityJson.Obj resultMaterial(ArmyCalls.Call input,ActionReceipt result,Optional<RawJson> material,ActionPorts.OutcomeArchive bound) {
        if(input instanceof ArmyCalls.CreateMaa)StrictJson.require(material.isEmpty()&&result.applied().isEmpty(),NativeRegularMaaSubmission.MATERIAL_GAP);
        var n = ArmyJson.empty().put("schema", "xar.ck3.army-ordinary-action-result/v1").put("step", result.command().operation().value())
                .put("action_id", result.command().actionId()).put("status", result.outcome().name().toLowerCase(java.util.Locale.ROOT))
                .put("settled", result.settled()).put("world_effect_verified", result.applied().isPresent())
                .put("gameplay_verified", result.visibleGameplay()).put("advance_eligible", result.eligibleAdvance())
                .put("automatic_retry", false).put("backend_id", "native-headless");
        n.set("original_request_id", ActionTransitions.attempt(result.state()).<com.fasterxml.jackson.databind.JsonNode>map(attempt -> n.textNode(attempt.requestId())).orElseGet(n::nullNode));
        if (material.isPresent()) {
            ExactRef ref = bound.preserveMaterial(material.orElseThrow()); StrictJson.require(bound.loadMaterial(ref).equals(material.orElseThrow()), "Army material archive readback differs");
            n.set("independent_material", ArmyJson.parse(material.orElseThrow().bytes())); n.set("independent_material_ref", ref.toJson());
        } else { n.putNull("independent_material"); n.putNull("independent_material_ref"); }
        if(input instanceof ArmyCalls.CreateMaa) {
            var attempt=ActionTransitions.attempt(result.state());var dispatch=ActionTransitions.dispatch(result.state());
            if(attempt.isPresent()&&dispatch.orElse(null) instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&ack.originalResultToken().isPresent()&&ack.outbound().isPresent()) {
                var original=NativeRegularMaaSubmission.original(result.command(),attempt.orElseThrow(),ack,bound);
                n.set("regular_maa_create",original.pythonProjection());n.set("regular_maa_original_dispatch",bound.referenceOf(ack).toJson());
            } else {
                n.putNull("regular_maa_create");
                if(dispatch.isPresent())n.set("regular_maa_original_dispatch",bound.referenceOf(dispatch.orElseThrow()).toJson());else n.putNull("regular_maa_original_dispatch");
            }
        }
        return DriverJson.object(ArmyJson.bytes(n), ActionCommand.MAX_ARGUMENT_BYTES);
    }
    private Reply invoke(ArmyCalls.Call input) {
        try { return writer.locked(same -> { ArmyTypes.Context source = Objects.requireNonNull(current.current()); return handle(same, input, source, ids.next(same, source)); }); }
        catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    public Reply submit_call_ally_to_war_private_v1(ArmyCalls.CallAlly input) { return invoke(input); }
    public Reply submit_regular_maa_create_private_v1(ArmyCalls.CreateMaa input) { return invoke(input); }
    public Reply close_war_declared_overview_v1(ArmyCalls.Frame input) { requireKind(input, Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1); return invoke(input); }
    public Reply close_war_results_window_v1(ArmyCalls.Frame input) { requireKind(input, Kind.CLOSE_WAR_RESULTS_WINDOW_V1); return invoke(input); }
    public Reply declare_war(ArmyCalls.Declaration input) { requireKind(input, Kind.DECLARE_WAR); return invoke(input); }
    public Reply raise_troops_default(ArmyCalls.Frame input) { requireKind(input, Kind.RAISE_TROOPS_DEFAULT); return invoke(input); }
    public Reply move_army(ArmyCalls.Move input) { return invoke(input); }
    public Reply start_assault(ArmyCalls.Siege input) { requireKind(input, Kind.START_ASSAULT); return invoke(input); }
    public Reply stop_assault(ArmyCalls.Siege input) { requireKind(input, Kind.STOP_ASSAULT); return invoke(input); }
    public Reply disband_army(ArmyCalls.Unit input) { requireKind(input, Kind.DISBAND_ARMY); return invoke(input); }
    public Reply enforce_demands(ArmyCalls.War input) { requireKind(input, Kind.ENFORCE_DEMANDS); return invoke(input); }
    public Reply surrender_war(ArmyCalls.War input) { requireKind(input, Kind.SURRENDER_WAR); return invoke(input); }
    public Reply offer_white_peace(ArmyCalls.War input) { requireKind(input, Kind.OFFER_WHITE_PEACE); return invoke(input); }
    public Reply hire_mercenary_v1(ArmyCalls.Hire input) { requireKind(input, Kind.HIRE_MERCENARY_V1); return invoke(input); }
    public Reply hire_holy_order_v1(ArmyCalls.Hire input) { requireKind(input, Kind.HIRE_HOLY_ORDER_V1); return invoke(input); }
    public Reply assign_army_commander_v1(ArmyCalls.AssignCommander input) { return invoke(input); }
    public Reply set_army_gathering_research_sampling_v1(ArmyCalls.Sampling input) { return invoke(input); }
    public List<PublicBindings.BoundBinding> install(PublicBindings publicBindings, ExactRef actualServiceSource) {
        StrictJson.require(sources.service().equals(actualServiceSource), "Army public installer source differs from the actual implementation");
        List<PublicBindings.BoundBinding> installed = new ArrayList<>();
        for (Kind kind : Kind.values()) if (supported().contains(kind)) {
            PublicMethod method = PublicMethod.valueOf(kind.name());
            switch (kind) {
                case RAISE_TROOPS_DEFAULT, CLOSE_WAR_DECLARED_OVERVIEW_V1, CLOSE_WAR_RESULTS_WINDOW_V1 -> installed.add(register(publicBindings, method, ArmyCalls.Frame.class, actualServiceSource));
                case ENFORCE_DEMANDS, SURRENDER_WAR, OFFER_WHITE_PEACE -> installed.add(register(publicBindings, method, ArmyCalls.War.class, actualServiceSource));
                case DECLARE_WAR -> installed.add(register(publicBindings, method, ArmyCalls.Declaration.class, actualServiceSource));
                case MOVE_ARMY -> installed.add(register(publicBindings, method, ArmyCalls.Move.class, actualServiceSource));
                case START_ASSAULT, STOP_ASSAULT -> installed.add(register(publicBindings, method, ArmyCalls.Siege.class, actualServiceSource));
                case DISBAND_ARMY -> installed.add(register(publicBindings, method, ArmyCalls.Unit.class, actualServiceSource));
                case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1 -> installed.add(register(publicBindings, method, ArmyCalls.CallAlly.class, actualServiceSource));
                case SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> installed.add(register(publicBindings, method, ArmyCalls.CreateMaa.class, actualServiceSource));
                case HIRE_MERCENARY_V1, HIRE_HOLY_ORDER_V1 -> installed.add(register(publicBindings, method, ArmyCalls.Hire.class, actualServiceSource));
                case ASSIGN_ARMY_COMMANDER_V1 -> installed.add(register(publicBindings, method, ArmyCalls.AssignCommander.class, actualServiceSource));
                case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> installed.add(register(publicBindings, method, ArmyCalls.Sampling.class, actualServiceSource));
            }
        }
        return List.copyOf(installed);
    }
    private <Q extends ArmyCalls.Call> PublicBindings.BoundBinding register(PublicBindings bindings, PublicMethod method, Class<Q> type, ExactRef source) {
        return bindings.register(method, type, Reply.class, input -> { StrictJson.require(input.method() == method, "Army public typed method drift"); return invoke(input); },
                arguments -> { if (!(arguments instanceof PublicBindings.Value value)) throw new IllegalArgumentException("Army action requires the exact named argument object"); return type.cast(ArmyCallCodec.decode(method, value.original())); },
                ArmyOrdinaryActionService::encode, new PublicRoutes.Target(ArmyOrdinaryActionService.class.getName(), method.pythonName(), source),
                PublicRoutes.Status.IMPLEMENTED, "same-writer typed preparation, sole ActionCoordinator, independent effect and original-evidence replay; UNKNOWN is retained without replay");
    }
    public static RawJson encode(Reply reply) {
        if (reply.input() instanceof ArmyCalls.Frame && (reply.input().method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                || reply.input().method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1)
                && ArmyOrdinaryActionArguments.decode(reply.actual().command().arguments()).executionProfile()
                    == ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW)
            return ArmyPublicWire.encodeExactSourceBound(reply.compatibleMaterial(), reply.context());
        return ArmyPublicWire.encode(reply.compatibleMaterial(), reply.context());
    }
    public static Optional<String> capability(Kind kind) {
        return switch (kind) {
            case SUBMIT_CALL_ALLY_TO_WAR_PRIVATE_V1, SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1 -> Optional.empty();
            case CLOSE_WAR_DECLARED_OVERVIEW_V1 -> Optional.of("game.command.close-war-declared-overview-v1");
            case CLOSE_WAR_RESULTS_WINDOW_V1 -> Optional.of("game.command.close-war-results-window-v1");
            case DECLARE_WAR -> Optional.of("game.command.declare-war-N");
            case RAISE_TROOPS_DEFAULT -> Optional.of("game.command.raise-troops-default");
            case MOVE_ARMY -> Optional.of("game.command.move-army-N-to-N");
            case START_ASSAULT -> Optional.of("game.command.start-assault-N");
            case STOP_ASSAULT -> Optional.of("game.command.stop-assault-N");
            case DISBAND_ARMY -> Optional.of("game.command.disband-army-N");
            case ENFORCE_DEMANDS -> Optional.of("game.command.enforce-demands-N");
            case SURRENDER_WAR -> Optional.of("game.command.surrender-war-N");
            case OFFER_WHITE_PEACE -> Optional.of("game.command.offer-white-peace-N");
            case HIRE_MERCENARY_V1 -> Optional.of("game.command.hire-mercenary-v1");
            case HIRE_HOLY_ORDER_V1 -> Optional.of("game.command.hire-holy-order-v1");
            case ASSIGN_ARMY_COMMANDER_V1 -> Optional.of("game.command.assign-army-commander-v1-army-N-to-character-N");
            case SET_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> Optional.of("game.command.query-army-strengths-v1");
        };
    }
    private static RawJson operationKey(String operation) { return new RawJson(StrictJson.canonical(StrictJson.object().put("operation", operation))); }
    private ArmyTypes.Context deadline(ArmyCalls.Call input, ArmyTypes.Context original) {
        if (!(input instanceof ArmyCalls.CreateMaa maa)) return original;
        java.math.BigDecimal seconds = maa.timeoutSeconds() instanceof ArmyTypes.Present<java.math.BigDecimal> present
                ? present.value() : java.math.BigDecimal.valueOf(30);
        var now = clock.instant(); StrictJson.require(original.deadline().isAfter(now), "original Army action deadline has expired");
        var remaining = java.time.Duration.between(now, original.deadline());
        java.math.BigDecimal available = java.math.BigDecimal.valueOf(remaining.getSeconds()).add(java.math.BigDecimal.valueOf(remaining.getNano(), 9));
        if (seconds.compareTo(available) >= 0) return original;
        long nanos = seconds.movePointRight(9).setScale(0, java.math.RoundingMode.CEILING).longValueExact();
        return new ArmyTypes.Context(original.before(), original.source(), original.sessionId(), now.plusNanos(nanos));
    }
    private static void requireKind(ArmyCalls.Call call, Kind expected) { StrictJson.require(ArmyOrdinaryActionPreparation.kind(call) == expected, "Army dynamic family changed its selected action kind"); }
    private static void requireDelegatedSelection(ArmyCalls.Call input, ActionReceipt original) {
        if (input instanceof ArmyCalls.AssignCommander assignment) {
            var old = org.xar.ck3.control.application.planning.military.CommanderAssignmentPostcondition.arguments(original.command().arguments());
            StrictJson.require(original.command().operation().value().equals(old.step()) && old.army().equals(BigInteger.valueOf(assignment.army().value()))
                    && old.character().equals(BigInteger.valueOf(assignment.character().value())), "existing commander action ID changed its selected army/character");
        } else if (input instanceof ArmyCalls.Hire hire && hire.method() == PublicMethod.HIRE_MERCENARY_V1) {
            StrictJson.require(original.command().operation().value().equals("hire-mercenary-v1")
                    && OpportunityJson.integer(original.command().arguments().get("company_id"), "canonical finance company").equals(BigInteger.valueOf(hire.id().value())),
                    "existing mercenary action ID changed its selected company");
        } else throw new IllegalArgumentException("unregistered Army delegated action shape");
    }
    /** Original late-owner-query latch; the flag is recomputed by the sole archived witness loader, never accepted from a caller. */
    public static void rejectDirectWindowDeferred(List<ActionReceipt> previous, ArmyCalls.Frame input,
            Complete actualCurrent, ActionPorts.OutcomeArchive bound, FrameLoader actualFrames) {
        Objects.requireNonNull(actualCurrent); Objects.requireNonNull(bound); Objects.requireNonNull(actualFrames);
        StrictJson.require(input.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 || input.method() == PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1,
                "fixed-window replay gate only accepts the two original close methods");
        StrictJson.require(input.revision().value() instanceof ArmyTypes.Present<BigInteger>, "fixed-window retry gate requires the original explicit public revision");
        input.revision().requireCurrent(actualCurrent.identity().frame().revision());
        String operation = (input.method() == PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 ? ArmyWindowCodec.Kind.OVERVIEW : ArmyWindowCodec.Kind.RESULTS)
                .step(ArmyWindowCodec.Operation.CLOSE);
        for (ActionReceipt old : List.copyOf(previous)) {
            if (!(old.command().origin() instanceof CommandOrigin.Gameplay) || !old.command().operation().value().equals(operation)
                    || !(old.state() instanceof ActionState.Settled settled)
                    || !(settled.settlement() instanceof ActionState.DirectFixedWindowCompleted)
                    || !old.command().before().frame().identity().player().equals(actualCurrent.identity().frame().identity().player())
                    || !Objects.equals(old.command().before().frame().episodeRunId(), actualCurrent.identity().frame().episodeRunId())) continue;
            var original = NativeDirectFixedWindowObservation.load(old, bound, actualFrames);
            var resolution = original.ownerResolution(); if (resolution.isEmpty() || !resolution.orElseThrow().retryDeferredForNativeFrame()) continue;
            Complete queryFrame = resolution.orElseThrow().current();
            if (queryFrame.identity().game().equals(actualCurrent.identity().game()) && queryFrame.source().equals(actualCurrent.source())
                    && queryFrame.sessionId().equals(actualCurrent.sessionId()) && nativeWindowGeneration(queryFrame).equals(nativeWindowGeneration(actualCurrent))
                    && queryFrame.identity().frame().identity().nativeRevision().equals(actualCurrent.identity().frame().identity().nativeRevision())
                    && queryFrame.identity().frame().identity().dateRaw().equals(actualCurrent.identity().frame().identity().dateRaw()))
                throw new IllegalArgumentException("fixed-window close retry deferred for this original Native frame after owner-query resolution");
        }
    }
    private static BigInteger nativeWindowGeneration(Complete frame) {
        var diagnostics = OpportunityJson.object(frame.semantic().get("diagnostics"), "original window diagnostics");
        var hello = OpportunityJson.object(diagnostics.get("hello"), "original window native hello");
        BigInteger generation = OpportunityJson.integer(hello.get("connection_generation"), "original window native generation");
        StrictJson.require(generation.signum() > 0 && generation.bitLength() <= 64, "positive original Native window generation required"); return generation;
    }
    static void rejectReplay(List<ActionReceipt> previous, ArmyCalls.Call input, ArmyTypes.Context source) {
        var claims = ArmyOrdinaryActionPreparation.claims(input, source); Kind kind = ArmyOrdinaryActionPreparation.kind(input);
        for (ActionReceipt old : previous) {
            if (!(old.command().origin() instanceof CommandOrigin.Gameplay)) continue;
            var before = old.command().before();
            if (!Objects.equals(before.frame().episodeRunId(), source.before().frame().episodeRunId()) || !before.frame().identity().player().equals(source.playerId())) continue;
            boolean overlaps = claims.overlaps(old.command().claims());
            StrictJson.require(old.settled() || !overlaps, "an original overlapping Army action remains unresolved; collect its original ID without resubmission");
            if (overlaps && ActionTransitions.attempt(old.state()).isPresent()) {
                // Shared player/resource claims serialize execution; only the complete WarID identifies a settled terminal action.
                boolean sameWar = input instanceof ArmyCalls.War war
                        && (old.command().operation().value().equals("enforce-demands-" + war.warId())
                        || old.command().operation().value().equals("surrender-war-" + war.warId())
                        || old.command().operation().value().equals("offer-white-peace-" + war.warId()));
                StrictJson.require((kind != Kind.SURRENDER_WAR || !sameWar) && kind != Kind.SUBMIT_REGULAR_MAA_CREATE_PRIVATE_V1,
                        "this explicit surrender/MAA action identity has already entered native execution; no second submission");
                if (sameWar && kind == Kind.OFFER_WHITE_PEACE && old.command().operation().value().startsWith("offer-white-peace-")) {
                    BigInteger elapsed = source.dateRaw().subtract(before.frame().identity().dateRaw());
                    StrictJson.require(elapsed.compareTo(BigInteger.valueOf(30L * 24L)) >= 0, "same-WarID white-peace proposal is inside the actual thirty-day cooldown");
                }
            }
        }
    }
}

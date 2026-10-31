package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.NativeStepDiscriminator.RiteCreation;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningGate;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyObserverSampling;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.Goal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Concrete current-Game planning input assembly; domain producers remain their single actual implementations. */
public final class RootPlanningInputsFactory {
    private RootPlanningInputsFactory() { }

    /** Installers register the actual domain for each exact callable; operation-name inference is forbidden. */
    @FunctionalInterface public interface DomainCatalog {
        Classification classify(ActionReceipt actual, Session same, ActionPorts.OutcomeArchive originals) throws IOException;
    }
    public sealed interface Classification permits BusinessDomain, SystemControl { }
    public record BusinessDomain(Domain domain) implements Classification {
        public BusinessDomain { Objects.requireNonNull(domain); }
    }
    public enum ControlKind { CHECKPOINT_SAVE, AUB_POLICY_CONTROL, RITE_CREATION_CONTROL, OBSERVER_SAMPLING_CONTROL, GUI_NAVIGATION_CONTROL, GUI_NAVIGATION_FINAL_PENDING, PILGRIMAGE_CONTROL, GUI_PHYSICAL_PRESENTATION, MILITARY_UI_CONTROL, PUBLIC_PAUSE_CONTROL, LIFE_ADVANCE, TIMELINE_PRIMITIVE }
    public record SystemControl(ControlKind kind) implements Classification {
        public SystemControl { Objects.requireNonNull(kind); }
    }
    @FunctionalInterface public interface OpeningInputs {
        OpeningObservation collect(Capture actual) throws IOException;
    }
    @FunctionalInterface public interface OfflineInputs {
        OfflineObservation collect(Capture actual, PlanningRequest complete) throws IOException;
    }
    public record Products(RootExecutableBindings bindings, CrossRunPlanningDomain crossRun,
            DomainCatalog domains, OpeningInputs opening, OfflineInputs offline) {
        public Products {
            Objects.requireNonNull(bindings); Objects.requireNonNull(crossRun); Objects.requireNonNull(domains);
            Objects.requireNonNull(opening); Objects.requireNonNull(offline);
        }
    }
    public record Capture(RootRuntimeContext context, Session session, Complete frame, Known driver,
            OpportunityJson.Obj receivedCapabilities, Instant deadline) {
        public Capture {
            Objects.requireNonNull(context); Objects.requireNonNull(session); Objects.requireNonNull(frame);
            Objects.requireNonNull(driver); Objects.requireNonNull(receivedCapabilities); Objects.requireNonNull(deadline);
        }
    }
    /** Empty-scan evidence and a missing body are distinct; even an empty scan has an original source. */
    public record FieldSource(ObservationIdentity before, G2Source source, String sessionId, List<ExactRef> evidence) {
        public FieldSource {
            Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId);
            evidence = List.copyOf(evidence);
            StrictJson.require(!evidence.isEmpty() && evidence.stream().allMatch(ref -> ref.bytes() > 0),
                    "actual field observation evidence required, including an empty incident scan");
        }
        public void require(Capture actual) {
            StrictJson.require(before.equals(actual.frame().identity()) && source.equals(actual.frame().source())
                    && sessionId.equals(actual.frame().sessionId()), "planning field crossed the current full source/frame/session");
        }
    }
    public record OpeningObservation(FieldSource binding, OpeningGate gate) {
        public OpeningObservation { Objects.requireNonNull(binding); Objects.requireNonNull(gate); }
    }
    public record OfflineObservation(FieldSource binding, Optional<BatchRequest> batch) {
        public OfflineObservation {
            Objects.requireNonNull(binding); Objects.requireNonNull(batch);
            batch.ifPresent(value -> StrictJson.require(binding.evidence().contains(value.manifestRef())
                    && binding.evidence().containsAll(value.capturedRefs()), "offline batch differs from its actual scanned originals"));
        }
    }

    public static NativeReadinessCollector.PublicPlanningInputsPort create(RootRuntimeContext context,
            DriverBootstrap.Adopted actualAdopted, DriverCapabilityRuntime actualCapabilities, Products products) {
        Objects.requireNonNull(context); Objects.requireNonNull(actualAdopted);
        Objects.requireNonNull(actualCapabilities); Objects.requireNonNull(products);
        actualCapabilities.requireOwner(actualAdopted.authority(), context.archive(), products.bindings());
        actualCapabilities.bindPublicPlanningRetry(ReadonlyPlanningRetry.sink());
        StrictJson.require(context.bindings() == products.bindings(), "planning inputs must use the actual installed runtime catalog");
        StrictJson.require(actualAdopted.source().equals(context.source())
                && actualAdopted.session().game().equals(context.game().generation())
                && actualAdopted.session().sessionId().equals(context.game().sessionId())
                && actualAdopted.session().machineId().equals(context.game().machineId()),
                "planning inputs cannot capture a predecessor or another physical Game");
        return new NativeReadinessCollector.PublicPlanningInputsPort() {
            @Override public NativeReadinessCollector.PlanningInputs collect(Session borrowed, Complete frame,
                    Known known, OpportunityJson.Obj received, Instant deadline) throws IOException {
                return collectActual(borrowed, frame, known, received, deadline, InputPurpose.ORDINARY_READY);
            }
            @Override public NativeReadinessCollector.PlanningInputs collectPublic(Session borrowed, Complete frame,
                    Known known, OpportunityJson.Obj received, Instant deadline) throws IOException {
                return collectActual(borrowed, frame, known, received, deadline, InputPurpose.PUBLIC_OBSERVED);
            }
            @Override public OriginalTerminalPlanning.Input collectPublicTerminal(Session same,
                    DriverObservationAssembler.FullSnapshot full, Known known, OpportunityJson.Obj received,
                    Instant deadline) throws IOException {
                context.requireCurrent(deadline); context.writer().requireSession(same);
                StrictJson.require(context.borrowedSession() == same && context.bindings() == products.bindings()
                        && full.facts().source().equals(context.source())
                        && full.actual().session().game().equals(context.game().generation())
                        && full.actual().session().sessionId().equals(context.game().sessionId())
                        && full.actual().session().machineId().equals(context.game().machineId())
                        && known.stamp().game().equals(context.game().generation()),
                        "public terminal inputs crossed the actual held Game/source/writer");
                String head = same.head().digest();
                var caps = actualCapabilities.collectPublicTerminalInputs(same, full, known, received, deadline);
                var crossRun = products.crossRun().read(same);
                if (!(crossRun instanceof CrossRunPlanningDomain.KnownState state))
                    throw new IOException("actual cross-run state body is unavailable for public terminal planning");
                List<OpportunityJson.Obj> history = known.driver().commandHistory().stream()
                        .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
                if (!full.semantic().members().containsKey("campaign_goal"))
                    throw new IOException("actual Driver campaign_goal is missing from the terminal snapshot");
                OpportunityJson.Value rawGoal = full.semantic().get("campaign_goal");
                Optional<Goal> goal = rawGoal == OpportunityJson.Nil.INSTANCE ? Optional.empty()
                        : Optional.of(GoalCodec.decodeGoal(DriverJson.encode(
                                OpportunityJson.object(rawGoal, "actual retained terminal campaign goal"))));
                var input = new OriginalTerminalPlanning.Input(full.semantic(), history, caps.actionSteps(),
                        caps.bridgeCapabilities(), goal, Optional.of(CrossRunPlanning.planJson(state.nextPlan())));
                context.requireCurrent(deadline); context.writer().requireSession(same);
                StrictJson.require(head.equals(same.head().digest()), "public terminal input reads changed the writer head");
                return input;
            }
            private NativeReadinessCollector.PlanningInputs collectActual(Session borrowed, Complete frame,
                    Known known, OpportunityJson.Obj received, Instant deadline, InputPurpose purpose) throws IOException {
            Capture capture = new Capture(context, borrowed, frame, known, received, deadline);
            requireCurrent(capture, actualAdopted, products);
            String head = borrowed.head().digest();
            var capabilities = purpose == InputPurpose.PUBLIC_OBSERVED
                    ? actualCapabilities.collectPublicPlanningInputs(borrowed, frame, known, received, deadline)
                    : actualCapabilities.collect(borrowed, frame, known, received, deadline);
            var coreInvalidation=actualCapabilities.armyCoreInvalidation(borrowed,frame,known);
            OpportunityJson.Obj planningSnapshot=coreInvalidation.map(value->value.planningSnapshot(frame,known)).orElse(frame.semantic());
            if(purpose==InputPurpose.ORDINARY_READY)StrictJson.require(planningSnapshot.equals(frame.semantic()),
                    "Core availability must refresh through the ordinary observation before Ready");
            List<ExternalFact> facts = actionFacts(capture, products.domains());
            Optional<Goal> goal = campaignGoal(frame);
            var crossRun = products.crossRun().read(borrowed);
            if (!(crossRun instanceof CrossRunPlanningDomain.KnownState state))
                throw new IOException("actual cross-run state body is unavailable; missing state is not an empty episode history");
            OpportunityJson.Obj next = CrossRunPlanning.planJson(state.nextPlan());
            OpeningObservation opening = Objects.requireNonNull(products.opening().collect(capture));
            opening.binding().require(capture);
            StrictJson.require(opening.gate().episodeRunId().equals(frame.identity().frame().episodeRunId())
                    && (opening.gate().stage() == OpeningStage.COMPLETE
                        || opening.gate().dateRaw().equals(frame.identity().frame().identity().dateRaw())),
                    "actual opening lifecycle belongs to another episode or its pending date changed");
            boolean required = opening.gate().stage() != OpeningStage.COMPLETE;
            List<OpportunityJson.Obj> history = known.driver().commandHistory().stream()
                    .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
            PlanningRequest complete = new PlanningRequest(frame.identity(), frame.source(), frame.sessionId(), deadline,
                    new PlanningObservation(planningSnapshot, history, capabilities.actionSteps(), capabilities.bridgeCapabilities(),
                            capabilities.battleSpeedReadiness(), facts, goal, Optional.of(next), required));
            OfflineObservation offline = Objects.requireNonNull(products.offline().collect(capture, complete));
            offline.binding().require(capture);
            requireCurrent(capture, actualAdopted, products);
            StrictJson.require(head.equals(borrowed.head().digest()), "planning input reads changed the authoritative writer head");
            return new NativeReadinessCollector.PlanningInputs(capabilities.actionSteps(), capabilities.bridgeCapabilities(),
                    capabilities.battleSpeedReadiness(), facts, goal, Optional.of(next), required, offline.batch(),coreInvalidation);
            }
        };
    }

    private enum InputPurpose { ORDINARY_READY, PUBLIC_OBSERVED }

    /**
     * Consume the actual public collector union. A same-actor Complete observation can be running,
     * terminal or blocked by a retained action; it is not a Ready publication or execution permission.
     * Partial player joins are retained by the public preflight owner and never receive an invented actor.
     */
    public static PlanningRequest publicRequest(NativeReadinessCollector.PublicPlanningObservation actual,
            Session same, Instant deadline) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(same); Objects.requireNonNull(deadline);
        actual.assertCurrent(same);
        if (actual instanceof NativeReadinessCollector.PublicReady ready) {
            PlanningRequest request = ready.ready().request();
            StrictJson.require(request.before().equals(ready.lease().frame().identity())
                    && request.source().equals(ready.lease().frame().source())
                    && request.sessionId().equals(ready.lease().frame().sessionId()),
                    "public Ready lost its actual original planning request");
            actual.assertCurrent(same);
            return request;
        }
        var held = actual.frame();
        if (!(held.joined() instanceof Complete complete))
            throw new IOException("public ordinary planning requires an actual complete player join: " + held.joined());
        StrictJson.require(complete.semantic().equals(held.snapshot().semantic())
                && complete.originalEvidence().equals(held.snapshot().originalEvidence())
                && complete.fullBindingSha256().equals(held.snapshot().fullBindingSha256()),
                "public planner Complete differs from the original held full snapshot");
        Instant effectiveDeadline = deadline.isBefore(held.validUntil()) ? deadline : held.validUntil();
        NativeReadinessCollector.PlanningInputs inputs = held.collectInputs(same, effectiveDeadline);
        List<OpportunityJson.Obj> history = held.driver().driver().commandHistory().stream()
                .map(row -> DriverJson.object(row.originalRow().json(), DriverJson.MAX_NATIVE_BYTES)).toList();
        PlanningRequest request = new PlanningRequest(complete.identity(), complete.source(), complete.sessionId(),
                effectiveDeadline, new PlanningObservation(inputs.planningSnapshot(complete,held.driver()), history, inputs.actionSteps(),
                        inputs.bridgeCapabilities(), inputs.battleSpeedReadiness(), inputs.actionFacts(),
                        inputs.campaignGoal(), inputs.crossRunPlan(), inputs.initialLifestyleFocusRequired()));
        actual.assertCurrent(same);
        return request;
    }

    /** Raw terminal DATA preserves the held full frame, including a genuinely absent or changed actor. */
    public static OriginalTerminalPlanning.Input publicTerminalInputs(
            NativeReadinessCollector.PublicPlanningObservation actual, Session same, Instant deadline) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(same); Objects.requireNonNull(deadline);
        actual.assertCurrent(same);
        if (actual instanceof NativeReadinessCollector.PublicReady)
            throw new IOException("public terminal DATA requires its actual observed terminal frame");
        var frame = actual.frame();
        StrictJson.require(OriginalTerminalPlanning.terminalFrame(frame.snapshot().semantic()),
                "public terminal input was requested for a nonterminal observation");
        Instant until = deadline.isBefore(frame.validUntil()) ? deadline : frame.validUntil();
        OriginalTerminalPlanning.Input input = frame.collectTerminalInputs(same, until);
        actual.assertCurrent(same);
        return input;
    }
    private static void requireCurrent(Capture actual, DriverBootstrap.Adopted adopted, Products products) throws IOException {
        RootRuntimeContext context = actual.context(); context.requireCurrent(actual.deadline());
        context.writer().requireSession(actual.session());
        StrictJson.require(context.borrowedSession() == actual.session(), "planning inputs require the exact borrowed writer session");
        StrictJson.require(context.bindings() == products.bindings() && actual.frame().source().equals(context.source())
                && actual.frame().sessionId().equals(context.game().sessionId())
                && actual.frame().identity().machineId().equals(context.game().machineId())
                && actual.frame().identity().game().equals(context.game().generation())
                && actual.driver().stamp().game().equals(context.game().generation())
                && actual.driver().stamp().episodeRunId().equals(actual.frame().identity().frame().episodeRunId()),
                "planning inputs crossed their actual current Game, source, Driver or episode");
        adopted.authority().withFrozenFacts(actual.session(), frozen -> {
            StrictJson.require(frozen.state() instanceof Known current && current.stamp().equals(actual.driver().stamp())
                    && DriverJson.sha256(DriverJson.encode(current.auxiliary())).equals(
                            DriverJson.sha256(DriverJson.encode(actual.driver().auxiliary()))),
                    "planning inputs no longer hold the actual frozen Driver state");
            return null;
        });
    }

    private static Optional<Goal> campaignGoal(Complete frame) throws IOException {
        if (!frame.semantic().members().containsKey("campaign_goal"))
            throw new IOException("actual Driver campaign_goal is missing; absence cannot initialize a new goal");
        OpportunityJson.Value raw = frame.semantic().get("campaign_goal");
        if (raw == OpportunityJson.Nil.INSTANCE) return Optional.empty();
        Goal goal = GoalCodec.decodeGoal(DriverJson.encode(OpportunityJson.object(raw, "actual retained campaign goal")));
        StrictJson.require(goal.currentCharacterId() == frame.identity().frame().identity().player().longValueExact(),
                "actual retained campaign goal belongs to a different current actor");
        return Optional.of(goal);
    }

    private static List<ExternalFact> actionFacts(Capture capture, DomainCatalog domains) throws IOException {
        var parent = ActionChildPlanningScope.current(capture.session(), capture.session().head());
        try {
            return capture.context().core().actions().withFrozen(capture.session(), lease -> {
                var originals = capture.context().archive().withSession(capture.session());
                List<ExternalFact> facts = new ArrayList<>();
                PhysicalActionRegistry.VerifiedPresentations presentation;
                try{presentation=capture.context().core().physicalActions().verified(capture.session(),lease.snapshot());}catch(IOException failure){throw new UncheckedIOException(failure);}
                for (ActionReceipt receipt : lease.snapshot().actions()) {
                    ActionCommand command = receipt.command();
                    if(presentation.contains(receipt))continue;
                    boolean current = command.origin() instanceof CommandOrigin.Gameplay
                            && command.before().machineId().equals(capture.frame().identity().machineId())
                            && command.before().game().equals(capture.frame().identity().game())
                            && command.before().frame().episodeRunId().equals(capture.frame().identity().frame().episodeRunId());
                    if (!current) {
                        StrictJson.require(receipt.settled(), "a prior Game/episode or frontend action is unresolved; sole authority must reconcile it");
                        continue;
                    }
                    if (parent.filter(actual -> actual.actionId().equals(command.actionId())
                            && actual.bodySha256().equals(receipt.bodySha256())).isPresent()) {
                        // The permit was privately minted by the actual Children callback and verified
                        // against this same canonical running parent. It never clears another UNKNOWN.
                        originals.receiptReferenceOf(receipt);
                        continue;
                    }
                    // Retain the real canonical original before classifying system controls.
                    // SAVE has its own exact verifier and never invents a business domain.
                    ExactRef original = originals.receiptReferenceOf(receipt);
                    Classification classification;
                    try { classification = Objects.requireNonNull(domains.classify(receipt,capture.session(),originals),
                            "actual installed action classification required"); }
                    catch (IOException failure) { throw new UncheckedIOException(failure); }
                    if (classification instanceof SystemControl control) {
                        requireSettledControl(control, receipt, lease.snapshot().actions());
                        continue;
                    }
                    if (!(classification instanceof BusinessDomain business))
                        throw new IllegalStateException("unrecognized installed action classification");
                    Domain domain = business.domain();
                    ExternalState state = externalState(receipt);
                    facts.add(new ExternalFact(command.actionId(), receipt.bodySha256(), command.before(), state,
                            UnknownScope.GLOBAL, domain, command.claims(), original));
                }
                lease.assertCurrent(); return List.copyOf(facts);
            });
        } catch (UncheckedIOException failure) { throw failure.getCause(); }
    }

    /** One typed receipt-to-fact mapping; a Family send remains distinct from an applied business effect. */
    static ExternalState externalState(ActionReceipt receipt) {
        Objects.requireNonNull(receipt);
        return switch (receipt.outcome()) {
            case APPLIED_CONFIRMED -> ExternalState.APPLIED_CONFIRMED;
            case SEND_CONFIRMED -> ExternalState.SEND_CONFIRMED;
            case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH -> ExternalState.REJECTED_CONFIRMED;
            case TERMINAL_WITHOUT_EFFECT -> ExternalState.TERMINAL_WITHOUT_EFFECT;
            case UNRESOLVED -> receipt.state() instanceof ActionState.AckReceived ? ExternalState.ACK_RECEIVED : ExternalState.UNKNOWN;
        };
    }
    /** This filters authenticated canonical controls; it neither verifies Native evidence nor grants SAVE/day credit. */
    static void requireSettledControl(SystemControl control, ActionReceipt receipt) {
        requireSettledControl(control, receipt, List.of());
    }
    static void requireSettledControl(SystemControl control, ActionReceipt receipt, List<ActionReceipt> canonicalActions) {
        Objects.requireNonNull(control);Objects.requireNonNull(receipt);Objects.requireNonNull(canonicalActions);
        StrictJson.require(receipt.settled(), "an unresolved system control blocks every ordinary action");
        switch (control.kind()) {
            case LIFE_ADVANCE -> {
                var command=receipt.command();
                StrictJson.require(org.xar.ck3.control.application.advance.LifeAdvanceComposite.accepts(command.operation().value())
                        &&command.expected().observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER),
                        "Life timeline control must retain its registered operation and observer");
                var plan=org.xar.ck3.control.application.advance.AdvancePlan.decode(command);
                StrictJson.require(command.expected().values().equals(plan.expected()),
                        "Life timeline control changed its exact typed plan expectation");
                if(receipt.state() instanceof ActionState.CompositeSettled settled) {
                    if(settled.settlement() instanceof ActionState.LifeControlPrefixInterrupted) {
                        var children=settled.execution().children().stream().map(child -> canonicalActions.stream()
                                .filter(value -> child.actionId().equals(value.command().actionId())).findFirst()
                                .orElseThrow(() -> new IllegalArgumentException("interrupted Life prefix child is absent from held canonical planning actions"))).toList();
                        ActionEffects.validateCompositeChildren(command,settled.execution(),settled.settlement(),children);
                        StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance()&&receipt.applied().isEmpty(),
                                "interrupted Life prefix cannot claim gameplay or day credit");
                    } else {
                        StrictJson.require(settled.settlement() instanceof ActionState.Applied
                                ||settled.settlement() instanceof ActionState.CompositeNoGameplayWrite
                                ||settled.settlement() instanceof ActionState.CompositeRejected,
                                "Life timeline control requires its actual semantic, no-write or rejected composite terminal");
                        ActionEffects.validateComposite(command,settled.execution(),settled.settlement());
                    }
                } else StrictJson.require(receipt.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,
                        "Life timeline control cannot borrow a primitive or Family-send settlement");
            }
            case TIMELINE_PRIMITIVE -> {
                var command=receipt.command();
                var expected=org.xar.ck3.control.application.advance.AdvancePrimitives.expected(
                        command.before(),command.source(),command.operation(),command.arguments());
                StrictJson.require(command.expected().equals(expected),
                        "timeline primitive changed its exact source-owned expectation");
                if(receipt.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH) {
                    StrictJson.require(receipt.state() instanceof ActionState.RejectedBeforeDispatch,
                            "timeline zero-dispatch control requires its actual rejection");
                    break;
                }
                StrictJson.require(receipt.state() instanceof ActionState.Settled,
                        "timeline control requires its original primitive settlement");
                var settled=(ActionState.Settled)receipt.state();
                if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
                    if(expected.observerSchema().equals(org.xar.ck3.control.application.advance.AdvancePrimitives.CLOCK_OBSERVER))
                        StrictJson.require(settled.settlement() instanceof ActionState.ControlApplied observed
                                &&observed.observerSchema().equals(expected.observerSchema())
                                &&!receipt.visibleGameplay(), "clock control requires its independent typed Status");
                    else if(command.operation().value().equals("pause-map"))
                        StrictJson.require(settled.settlement() instanceof ActionState.PauseConfirmed,
                                "pause control requires its independently confirmed pause");
                    else StrictJson.require(settled.settlement() instanceof ActionState.Applied observed
                                &&observed.observation().observerSchema().equals(expected.observerSchema()),
                                "speed/resume control requires its independent timeline observation");
                } else StrictJson.require(settled.settlement() instanceof ActionState.Rejected
                        ||settled.settlement() instanceof ActionState.NonAppliedTerminal,
                        "timeline control cannot borrow another terminal or Family-send outcome");
                ActionEffects.validate(command,settled.attempt(),settled.dispatch(),settled.settlement());
                StrictJson.require(!receipt.eligibleAdvance(), "a timeline primitive cannot grant an ordinary advance");
            }
            case PUBLIC_PAUSE_CONTROL -> RootPublicPauseArchiveClassifier.requireSettledReceipt(receipt);
            case CHECKPOINT_SAVE -> StrictJson.require(receipt.command().operation().equals(RootSaveRuntime.OPERATION),
                    "SAVE classification cannot be borrowed by another operation");
            case RITE_CREATION_CONTROL -> {
                OperationKey operation=receipt.command().operation();
                boolean exactAction=false;
                for(RiteCreation selector:RiteCreation.values())
                    if(selector!=RiteCreation.PREVIEW&&selector.operationKey().equals(operation))exactAction=true;
                StrictJson.require(exactAction&&receipt.command().expected().observerSchema().equals(RootRiteCreationRuntimeFactory.OBSERVER),
                        "Rite control must retain its exact finite action selector and independent observation contract");
                StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "Rite control cannot claim ordinary gameplay, religious business, saved-day or SAVE credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(!operation.equals(RiteCreation.CONFIRM_ONCE.operationKey())
                            &&receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(RootRiteCreationRuntimeFactory.OBSERVER),
                            "only independently observed Rite UI controls may settle; final confirmation cannot claim a control post");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException("Rite cannot use an unresolved or Family-send outcome");
                }
            }
            case OBSERVER_SAMPLING_CONTROL -> {
                String operation=receipt.command().operation().value();
                StrictJson.require((operation.equals(ArmyObserverSampling.ENABLE)||operation.equals(ArmyObserverSampling.DISABLE))
                        &&receipt.command().expected().observerSchema().equals(ArmyObserverSampling.OBSERVER),
                        "sampling control must retain its actual operation and independent result contract");
                StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "sampling control cannot claim ordinary gameplay, saved-day or SAVE credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(ArmyObserverSampling.OBSERVER),
                            "positive sampling control requires its independent actual ControlApplied settlement");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException(
                            "sampling cannot borrow an unresolved or Family-send outcome");
                }
            }
            case MILITARY_UI_CONTROL -> {
                StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "military UI controls cannot claim ordinary business, game-day or SAVE credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(receipt.command().expected().observerSchema()),
                            "positive military UI control requires its actual independently replayed ControlApplied");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException(
                            "military UI control cannot borrow an unresolved or Family-send outcome");
                }
            }
            case GUI_PHYSICAL_PRESENTATION -> StrictJson.require(
                    receipt.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT
                    &&receipt.state() instanceof PhysicalActionState actual&&actual.terminal()
                    &&actual.request().transportKind()==org.xar.ck3.control.contracts.presentation.TransportKind.PRESENTATION_MMAP
                    &&!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                    "physical GUI completion/not-posted is a separate zero-business terminal, never native Applied or SAVE/day credit");
            case PILGRIMAGE_CONTROL -> {
                StrictJson.require(receipt.command().expected().observerSchema().equals(RootReligionPilgrimage.OBSERVER)
                        &&!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "pilgrimage control must retain its actual result contract without ordinary, day or SAVE credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(RootReligionPilgrimage.OBSERVER),
                            "positive pilgrimage control requires its independent actual ControlApplied");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException(
                            "pilgrimage cannot borrow an unresolved or Family-send outcome");
                }
            }
            case GUI_NAVIGATION_CONTROL, GUI_NAVIGATION_FINAL_PENDING -> {
                StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "GUI navigation cannot claim ordinary gameplay, day or SAVE credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(control.kind()==ControlKind.GUI_NAVIGATION_CONTROL
                            &&receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(receipt.command().expected().observerSchema()),
                            "only an exact installed control selector with its independent ControlApplied may settle; final selectors remain pending");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException(
                            "GUI navigation cannot borrow an unresolved or Family-send outcome");
                }
            }
            case AUB_POLICY_CONTROL -> {
                String operation=receipt.command().operation().value();
                StrictJson.require((operation.equals(AubOperations.SELECT)||operation.equals(AubOperations.CONFIRM))
                        &&receipt.command().expected().observerSchema().equals(AubOperations.OBSERVER),
                        "AUB control must retain its exact original operation and independent observation contract");
                StrictJson.require(!receipt.visibleGameplay()&&!receipt.eligibleAdvance(),
                        "AUB control cannot claim ordinary gameplay or saved-day credit");
                switch(receipt.outcome()) {
                    case APPLIED_CONFIRMED -> StrictJson.require(receipt.state() instanceof ActionState.Settled actual
                            &&actual.settlement() instanceof ActionState.ControlApplied observed
                            &&observed.observerSchema().equals(AubOperations.OBSERVER),
                            "positive AUB control requires its separate original ControlApplied settlement");
                    case REJECTED_CONFIRMED, REJECTED_BEFORE_DISPATCH, TERMINAL_WITHOUT_EFFECT -> { }
                    case UNRESOLVED, SEND_CONFIRMED -> throw new IllegalArgumentException("AUB cannot use an unresolved or Family-send outcome");
                }
            }
        }
    }
}

package org.xar.ck3.control.application.planning.sway;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;
import static org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwaySchedule;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;

/** Ordinary service's real consumer. It uses the active parent's child custody and original writer only. */
public final class SwayOrdinaryExecutor {
    public record Fresh(PlanningRequest request, NativeEffectEvidence.FrameBasis originalFrame) { public Fresh { Objects.requireNonNull(request); Objects.requireNonNull(originalFrame); } }
    public record FinalRead(NativeEffectEvidence.FrameBasis originalFrame, ExactRef independentRootRead) { public FinalRead { Objects.requireNonNull(originalFrame); Objects.requireNonNull(independentRootRead); } }
    @FunctionalInterface public interface CurrentPlanning { Fresh current(ActionCommand parent); }
    @FunctionalInterface public interface IndependentFinal { FinalRead current(ActionCommand parent); }
    @FunctionalInterface public interface ActualRestoration { RestoreCheckpointService.RestoreBinding requireCurrent(Instant deadline) throws IOException, InterruptedException; }
    public record Execution(OrdinarySwayService.Execution result, ExactRef originalStage, Optional<ExactRef> originalRun,
            List<ExactRef> reads, List<ExactRef> children, Optional<SwaySchedulerCompletion> completion) {
        public Execution { Objects.requireNonNull(result); Objects.requireNonNull(originalStage); Objects.requireNonNull(originalRun); reads = List.copyOf(reads); children = List.copyOf(children); Objects.requireNonNull(completion); }
    }
    private final SwayCanonicalDomain domain;
    private final ActionPorts.OutcomeArchive archive;
    private final PlanningReadPort reads;
    private final SwaySharedRoot root;
    private final SwayActionLifecycle.RegisteredReads definitions;
    private final SwayRootActions actions;
    private final Supplier<RootExecutableBindings> inventory;
    private final Supplier<ContinuityStorePort.Session> sessions;
    private final CurrentPlanning fresh;
    private final IndependentFinal independentFinal;
    private final ActualRestoration restoration;
    private final Supplier<OrdinaryPlanner> planner;
    public SwayOrdinaryExecutor(SwayCanonicalDomain domain, ActionPorts.OutcomeArchive archive, PlanningReadPort reads,
            ReadContract<OpportunityJson.Obj> root, SwayActionLifecycle.RegisteredReads definitions, SwayRootActions actions,
            Supplier<RootExecutableBindings> inventory, Supplier<ContinuityStorePort.Session> sessions, CurrentPlanning fresh,
            IndependentFinal independentFinal, ActualRestoration restoration, Supplier<OrdinaryPlanner> planner) {
        this(domain,archive,reads,SwaySharedRoot.original(root),definitions,actions,inventory,sessions,fresh,independentFinal,restoration,planner);
    }
    public SwayOrdinaryExecutor(SwayCanonicalDomain domain,ActionPorts.OutcomeArchive archive,PlanningReadPort reads,
            SwaySharedRoot root,SwayActionLifecycle.RegisteredReads definitions,SwayRootActions actions,
            Supplier<RootExecutableBindings> inventory,Supplier<ContinuityStorePort.Session> sessions,CurrentPlanning fresh,
            IndependentFinal independentFinal,ActualRestoration restoration,Supplier<OrdinaryPlanner> planner) {
        this.domain = Objects.requireNonNull(domain); this.archive = Objects.requireNonNull(archive); this.reads = Objects.requireNonNull(reads); this.root = Objects.requireNonNull(root);
        this.definitions = Objects.requireNonNull(definitions); this.actions = Objects.requireNonNull(actions); this.inventory = Objects.requireNonNull(inventory); this.sessions = Objects.requireNonNull(sessions);
        this.fresh = Objects.requireNonNull(fresh); this.independentFinal = Objects.requireNonNull(independentFinal); this.restoration = Objects.requireNonNull(restoration); this.planner = Objects.requireNonNull(planner);
    }
    /** Cold reconciliation has no child custody or planning scope. It can only complete an actual published scheduler. */
    public Optional<SwaySchedulerCompletion> observe(ActionCommand parent, CompositeExecution retained) {
        try {
            var session = session(); var originals = archive.withSession(session); var saved = domain.savedScheduler(session, parent); if (saved.isEmpty()) return Optional.empty();
            var finalRead = independentFinal.current(parent); var refs = new ArrayList<ExactRef>();
            for (var child : retained.children()) { var actual = ContinuityActionJournal.lookup(session.head().state(), child.actionId(), originals).orElseThrow(() -> new IOException("retained original Start child unavailable")); require(actual.bodySha256().equals(child.bodySha256()) && actual.settled(), "retained original Start child remains unresolved"); refs.add(originals.receiptReferenceOf(actual)); }
            var proof = new SwaySchedulerCompletion(parent.actionId(), ActionCodec.bodySha256(parent), saved.orElseThrow().originalRun(), saved.orElseThrow().witness(), finalRead.originalFrame(), List.of(finalRead.independentRootRead()), refs, Optional.empty(), Optional.empty(), saved.orElseThrow().continuation(), business(session, originals, refs));
            domain.verifySchedulerCompleted(session, parent, retained, proof); return Optional.of(proof);
        } catch (IOException failure) { throw new Unavailable("actual retained scheduler observation unavailable: " + failure.getMessage()); }
    }
    /** Call only from the actually installed ordinary parent, never from a frontend or another submission authority. */
    public Execution execute(ActionCommand parent, CompositeActionPort.Children custody) {
        require(parent.operation().equals(OrdinarySwayPolicy.OPERATION), "foreign optional parent"); Objects.requireNonNull(custody);
        try {
            var session = session(); var originals = archive.withSession(session); var current = current(parent);
            require(current.before().equals(parent.before()), "optional stage frame changed before execution");
            var rootResult = rootRead(session,current);
            if (!(rootResult instanceof PlanningReadResult.Known<OpportunityJson.Obj> known)) throw new Unavailable("current original campaign-root read unavailable");
            var loaded = domain.load(session); ExactRef rootRef = originals.readReferenceOf(known.receipt());
            Optional<RestoreCheckpointService.RestoreBinding> restored = Optional.empty(); Optional<String> restoreFailure = Optional.empty();
            boolean historical = loaded.ledger().resolved().isEmpty() && loaded.ledger().imported().stream().anyMatch(value -> value.pending().isPresent() || value.resolved().isPresent());
            boolean pendingGame = loaded.ledger().pending().stream().anyMatch(value -> !value.original().binding().before().game().equals(current.before().game()));
            boolean resolvedGame = loaded.ledger().resolved().stream().anyMatch(value -> !value.lifecycle().origin().game().equals(current.before().game()));
            if (historical || pendingGame || resolvedGame) {
                // Real requireCurrent must precede our own stage commit, on this same held writer lease.
                try { restored = Optional.of(restoration.requireCurrent(parent.deadline())); }
                catch (IOException failure) { restoreFailure = Optional.of(failure.getMessage() == null ? "actual restoration revalidation unavailable" : failure.getMessage()); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); restoreFailure = Optional.of("actual restoration revalidation interrupted"); }
            }
            ExactRef stage = originals.preserveMaterial(new RawJson(SwaySchedulerReplay.encodeStage(new SwaySchedulerReplay.Stage(parent, loaded.original().reference().payload(), rootRef))));
            domain.commit(session, new StageRecorded(stage), new SwayTransitionCodec.Proofs(List.of(rootRef), Optional.empty(), Optional.empty(), List.of(stage)));
            Port port = new Port(parent, custody, session, originals, stage, restored, restoreFailure);
            var executed = new OrdinarySwayService().execute(OrdinarySwayPolicy.restoreStaged(parent), port);
            Optional<SwaySchedulerCompletion> completion = Optional.empty();
            if (port.publication.isPresent() && port.run.isPresent()) {
                if (port.finalSource.isEmpty()) port.captureFinal(fresh(parent));
                var business = business(session, originals, port.childRefs);
                var proof = new SwaySchedulerCompletion(parent.actionId(), ActionCodec.bodySha256(parent), port.run.orElseThrow(), port.publication.orElseThrow(), port.finalSource.orElseThrow().originalFrame(), port.finalReads, port.childRefs, port.selected, port.fullPlan, SwaySchedulerReplay.continuation(executed), business);
                domain.verifySchedulerCompleted(session, parent, retained(session, parent, originals), proof); completion = Optional.of(proof);
            }
            return new Execution(executed, stage, port.run, port.resultReads, port.childRefs, completion);
        } catch (IOException failure) { throw new Unavailable("actual original Sway execution unavailable: " + failure.getMessage()); }
    }
    private final class Port implements ExecutionPort {
        private final ActionCommand parent; private final CompositeActionPort.Children custody; private final ContinuityStorePort.Session session;
        private final ActionPorts.OutcomeArchive originals; private final ExactRef stage;
        private final List<ExactRef> resultReads = new ArrayList<>(), childRefs = new ArrayList<>();
        private CheckResult result; private Optional<ExactRef> run = Optional.empty(); private Optional<ExactRef> startChild = Optional.empty();
        private Optional<SwayCanonicalDomain.PublicationWitness> publication = Optional.empty();
        private Optional<Fresh> finalSource = Optional.empty(); private final List<ExactRef> finalReads = new ArrayList<>();
        private Optional<ActionCommand> selected = Optional.empty(); private Optional<SwaySchedulerCompletion.FullPlanOriginals> fullPlan = Optional.empty();
        private final Optional<RestoreCheckpointService.RestoreBinding> restored; private final Optional<String> restoreFailure;
        private Port(ActionCommand parent, CompositeActionPort.Children custody, ContinuityStorePort.Session session, ActionPorts.OutcomeArchive originals, ExactRef stage, Optional<RestoreCheckpointService.RestoreBinding> restored, Optional<String> restoreFailure) { this.parent = parent; this.custody = custody; this.session = session; this.originals = originals; this.stage = stage; this.restored = restored; this.restoreFailure = restoreFailure; }
        @Override public Optional<Inputs> loadInputs() {
            try { return Optional.of(SwaySessionInputs.project(domain.load(session).ledger(), parent.before())); }
            catch (IOException failure) { throw unavailable(failure); }
        }
        @Override public FormalResult queryAndConsume(OrdinarySwaySchedule.Frame expected, long target) {
            try {
                var request = current(parent); requireFrame(expected, request); Ledger ledger = domain.load(session).ledger();
                var known = target(request, target); SwayNativeWire.TargetRead read = known.value();
                if (ledger.pending().isPresent()) {
                    require(ledger.pending().orElseThrow().original().target() == target, "retained pending belongs to another selected target");
                    List<ExactRef> restoreSources = List.of();
                    if (!ledger.pending().orElseThrow().original().binding().before().game().equals(read.binding().before().game())) {
                        var actual = restored.orElseThrow(() -> new Unavailable(restoreFailure.orElse("actual cross-Game pending restore source unavailable"))); SwayRestorationProof.requireBinding(actual, session.head().state(), read, originals); restoreSources = List.of(SwayRestorationProof.material(session.head().state()));
                    }
                    ledger = domain.commit(session, new Recovered(read), new SwayTransitionCodec.Proofs(List.of(originals.readReferenceOf(known.receipt())), Optional.empty(), Optional.empty(), restoreSources));
                    return formal(FormalStatus.APPLIED, true, ledger.resolved().map(value -> value.identity().actionId()), Optional.empty(), SwayNativeWire.json(SwayFormalCodec.originalResolved(ledger.resolved().orElseThrow())));
                }
                if (ledger.resolved().isEmpty() && ledger.imported().stream().anyMatch(value -> value.pending().isPresent() || value.resolved().isPresent())) {
                    ledger = attach(known);
                    // Historical Start remains history; this is an independent restored observation.
                    return formal(FormalStatus.ALREADY_APPLIED, false, ledger.resolved().map(value -> value.identity().actionId()), Optional.of(Followup.OTHER), SwayNativeWire.json(SwayFormalCodec.originalResolved(ledger.resolved().orElseThrow())));
                }
                var decision = SwayFormalState.followup(ledger, read);
                if (decision != FollowupDecision.FIRST_SELECTED_RELATION && decision != FollowupDecision.RETARGET_SELECTED_RELATION && decision != FollowupDecision.REPEAT_SELECTED_TARGET)
                    return formal(FormalStatus.ALREADY_APPLIED, false, ledger.resolved().map(value -> value.identity().actionId()), Optional.of(SwaySchedulerReplay.followup(decision)), SwayNativeWire.json(SwayFormalCodec.originalResolved(ledger.resolved().orElseThrow())));
                if (!read.startable(true)) return formal(FormalStatus.NO_POSITIVE_OPPORTUNITY, false, Optional.empty(), Optional.empty(), read.body());
                actions.attach(inventory.get()); OperationKey operation = new OperationKey(SwayNativeWire.START + target); actions.issueStart(target);
                String actionId = custody.nextActionId(operation); SwayNativeWire.action(actionId, false);
                ObjectNode arguments = StrictJson.object(); arguments.put("schema", SwayNativeBindings.START_ARGUMENTS); arguments.put("target_character_id", target); arguments.set("original_target_read", originals.readReferenceOf(known.receipt()).toJson());
                var command = new ActionCommand(actionId, request.before(), request.source(), request.sessionId(), operation, arguments(arguments), expected(request, actionId, target), parent.claims(), parent.deadline());
                ActionReceipt child = custody.submit(command); ExactRef childRef = originals.receiptReferenceOf(child); childRefs.add(childRef); startChild = Optional.of(childRef);
                ledger = domain.load(session).ledger();
                if (NativeRecordedEvidenceVerifier.settlement(child.state()) instanceof ActionState.Applied && ledger.resolved().filter(value -> value.identity().actionId().equals(actionId)).isPresent())
                    return formal(FormalStatus.APPLIED, true, Optional.of(actionId), Optional.empty(), earlyBaseline(ledger.resolved().orElseThrow()));
                var pending = ledger.pending().orElseThrow(); return formal(switch(pending.stage()) { case SUBMISSION_UNRESOLVED -> FormalStatus.SUBMISSION_UNRESOLVED; case RECEIPT_PENDING -> FormalStatus.RECEIPT_PENDING; case POSTCONDITION_PENDING -> FormalStatus.POSTCONDITION_PENDING; }, false, Optional.of(actionId), Optional.empty(), pending.original().body());
            } catch (ReadPublicationRequiredException required) { throw required; }
            catch (IOException | IllegalArgumentException | IllegalStateException failure) { throw unavailable(failure); }
        }
        @Override public LifecycleResult observeLifecycle(OrdinarySwaySchedule.Frame expected) {
            try {
                PlanningRequest request = current(parent); requireFrame(expected, request); Ledger ledger = domain.load(session).ledger();
                if (ledger.resolved().isEmpty()) {
                    var historical = ledger.imported().flatMap(SwayLegacyImport.Imported::resolved).orElseThrow(() -> new Unavailable("historical lifecycle identity unavailable"));
                    ledger = attach(target(request, historical.identity().targetCharacterId()));
                }
                resultReads.clear();
                Episode episode = observePlanes(request, ledger.resolved().orElseThrow(), List.of(SwayObservationReads.Kind.COMPLETION, SwayObservationReads.Kind.OPINION, SwayObservationReads.Kind.TERMINATION, SwayObservationReads.Kind.EXECUTION));
                var row = StrictJson.object(); row.put("status", "observed"); row.put("original_action_id", episode.identity().actionId()); row.put("same_frame", true); result = new LifecycleResult(LifecycleStatus.OBSERVED, SwayNativeWire.json(row)); return (LifecycleResult)result;
            } catch (ReadPublicationRequiredException required) { throw required; }
            catch (IOException | IllegalArgumentException | IllegalStateException | Unavailable failure) { throw unavailable(failure); }
        }
        private Episode observePlanes(PlanningRequest request, Episode episode, List<SwayObservationReads.Kind> kinds) throws IOException {
            var planes = new java.util.EnumMap<SwayObservationReads.Kind, ProjectionJson>(SwayObservationReads.Kind.class); List<ExactRef> refs = new ArrayList<>();
            // Commit each validated prefix before an optional later reader can fail.
            // The same canonical writer replays every copied plane; a failed end/phase
            // reader still returns UNAVAILABLE and never erases named gain or terminal status.
            for (var kind : kinds) {
                var read = read(session, definitions.plane(kind, episode.identity()), request, SwayObservationReads.arguments(SwayObservationReads.Query.current(kind,episode.identity())));
                if (!(read instanceof PlanningReadResult.Known<SwayObservationReads.Plane> known)) throw new Unavailable("current " + kind + " source unavailable; retained original state preserved");
                refs.add(originals.readReferenceOf(known.receipt())); planes.put(kind, known.value().normalized());
                resultReads.add(refs.getLast());
                if (!episode.lifecycle().origin().game().equals(request.before().game())) {
                    var actual = restored.orElseThrow(() -> new Unavailable(restoreFailure.orElse("actual cross-Game lifecycle restore source unavailable")));
                    SwayRestorationProof.requireBinding(actual, session.head().state(), request.before(), request.sessionId(), originals); ExactRef material = SwayRestorationProof.material(session.head().state());
                    var ledger = domain.commit(session, new ScopeRebound(request.before(), material), new SwayTransitionCodec.Proofs(List.of(refs.getFirst()), Optional.empty(), Optional.empty(), List.of(material))); episode = ledger.resolved().orElseThrow();
                }
                SwayLifecycle.State observed = SwayLifecycle.observe(episode.lifecycle(), SwayFormalCodec.m6Episode(episode), new M6TerminalSourceComposition.Inputs(Optional.ofNullable(planes.get(SwayObservationReads.Kind.COMPLETION)), Optional.ofNullable(planes.get(SwayObservationReads.Kind.EXECUTION)), Optional.ofNullable(planes.get(SwayObservationReads.Kind.TERMINATION)), Optional.ofNullable(planes.get(SwayObservationReads.Kind.OPINION))), request.before());
                var ledger = domain.commit(session, episode.stop().isPresent() ? new StopObserved(observed, request.before()) : new LifecycleObserved(observed), proofs(refs));
                episode = ledger.resolved().orElseThrow();
            }
            return episode;
        }
        /** New Start is already confirmed by its original child; baseline failure cannot undo or replay it. */
        private ProjectionJson earlyBaseline(Episode applied) throws IOException {
            var diagnostic = StrictJson.object(); diagnostic.put("schedule_window", "after_completed_ordinary_sway_start");
            diagnostic.put("submit_attempted", false); diagnostic.put("new_game_days", 0);
            try {
                observePlanes(current(parent), applied, List.of(SwayObservationReads.Kind.COMPLETION, SwayObservationReads.Kind.OPINION));
                diagnostic.put("status", "observed");
            } catch (ReadPublicationRequiredException required) { throw required; }
            catch (IOException | IllegalArgumentException | IllegalStateException | Unavailable failure) {
                diagnostic.put("status", "query_failed"); diagnostic.put("error", failure.getMessage() == null ? failure.getClass().getSimpleName() : failure.getMessage());
            }
            var actual = domain.load(session).ledger().resolved().orElseThrow();
            require(actual.identity().equals(applied.identity()), "early baseline changed the confirmed original Start identity");
            var evidence = SwayFormalCodec.originalResolved(actual); evidence.set("ordinary_sway_post_start_observation", diagnostic);
            return SwayNativeWire.json(evidence);
        }
        @Override public Optional<String> saveScheduler(OrdinarySwaySchedule.State state) {
            try {
                if (result == null) result = new LocalResult(LocalStatus.KNOWN_EMPTY_RELATION_FRONTIER, Optional.empty());
                var original = new SwaySchedulerReplay.Run(stage, result, resultReads, startChild); ExactRef ref = originals.preserveMaterial(new RawJson(SwaySchedulerReplay.encodeRun(original)));
                List<ExactRef> materials = new ArrayList<>(List.of(stage, ref)); startChild.ifPresent(materials::add);
                var committed = domain.commitPublication(session, new SchedulerSaved(state, ref), new SwayTransitionCodec.Proofs(resultReads, Optional.empty(), Optional.empty(), materials)); publication = Optional.of(committed.witness()); run = Optional.of(ref); return Optional.empty();
            } catch (IOException failure) { return Optional.of("actual canonical Sway scheduler not committed: " + failure.getMessage()); }
        }
        @Override public OrdinaryContinuation executeFreshOrdinary() {
            Fresh source = fresh(parent); captureFinal(source); PlanningRequest request = source.request(); PlanningResult planned = Objects.requireNonNull(planner.get()).planAfterOptional(request, PlanningStage.ORDINARY_SWAY);
            fullPlan = Optional.of(new SwaySchedulerCompletion.FullPlanOriginals(originals.preserveMaterial(new RawJson(PlanningWire.encodeRequest(request))), originals.preserveMaterial(new RawJson(PlanningWire.encodeResult(planned)))));
            ObjectNode following = StrictJson.object(); following.put("planning_result", planned.getClass().getSimpleName()); ObjectNode outcome = StrictJson.object();
            if (planned instanceof PlanningResult.ActionSelected selection) {
                ActionCommand original = selection.command(); require(!original.operation().equals(OrdinarySwayPolicy.OPERATION), "fresh continuation reentered completed Sway stage");
                this.selected = Optional.of(original); outcome.put("status", "recorded_for_root_after_parent_settled"); outcome.put("exact_action_id", original.actionId()); outcome.put("exact_body_sha256", ActionCodec.bodySha256(original));
            } else if (planned instanceof PlanningResult.ExistingActionReconciliation) {
                outcome.put("status", "existing_action_requires_root_reconciliation");
            } else outcome.put("status", "no_action_selected");
            return new OrdinaryContinuation(SwayNativeWire.json(outcome), SwayNativeWire.json(following));
        }
        private void captureFinal(Fresh source) {
            var value = rootRead(session,source.request());
            if (!(value instanceof PlanningReadResult.Known<OpportunityJson.Obj> known)) throw new Unavailable("independent final root read unavailable; scheduler state remains committed without synthetic parent completion");
            finalSource = Optional.of(source); finalReads.clear(); finalReads.add(originals.readReferenceOf(known.receipt()));
        }
        private PlanningReadResult.Known<SwayNativeWire.TargetRead> target(PlanningRequest request, long target) {
            ObjectNode arguments = StrictJson.object(); arguments.put("target_character_id", target); var read = read(session, definitions.target(target), request, arguments(arguments));
            if (!(read instanceof PlanningReadResult.Known<SwayNativeWire.TargetRead> known)) throw new Unavailable("current selected Sway target read unavailable"); resultReads.clear(); resultReads.add(originals.readReferenceOf(known.receipt())); return known;
        }
        private Ledger attach(PlanningReadResult.Known<SwayNativeWire.TargetRead> known) throws IOException {
            RestoreCheckpointService.RestoreBinding actual = restored.orElseThrow(() -> new Unavailable(restoreFailure.orElse("actual source-bound restoration was not issued before this stage")));
            SwayRestorationProof.requireBinding(actual, session.head().state(), known.value(), originals); ExactRef material = SwayRestorationProof.material(session.head().state());
            return domain.commit(session, new HistoricalAttached(known.value(), material), new SwayTransitionCodec.Proofs(List.of(originals.readReferenceOf(known.receipt())), Optional.empty(), Optional.empty(), List.of(material)));
        }
        private FormalResult formal(FormalStatus status, boolean verified, Optional<String> action, Optional<Followup> followup, ProjectionJson evidence) { result = new FormalResult(status, verified, action, followup, evidence); return (FormalResult)result; }
        private Unavailable unavailable(Exception failure) { String error = failure.getMessage() == null ? failure.getClass().getSimpleName() : failure.getMessage(); result = new LocalResult(LocalStatus.UNAVAILABLE, Optional.of(error)); return new Unavailable(error); }
    }
    private ContinuityStorePort.Session session() { return Objects.requireNonNull(sessions.get(), "actual original Sway writer scope required"); }
    private Fresh fresh(ActionCommand parent) { Fresh value = Objects.requireNonNull(fresh.current(parent)); PlanningRequest request = value.request(); require(request.before().machineId().equals(parent.before().machineId()) && request.before().game().equals(parent.before().game()) && request.before().frame().episodeRunId().equals(parent.before().frame().episodeRunId()) && request.source().equals(parent.source()) && request.sessionId().equals(parent.sessionId()), "fresh ordinary source crossed original parent scope"); return value; }
    private PlanningRequest current(ActionCommand parent) { return fresh(parent).request(); }
    private static CompositeExecution retained(ContinuityStorePort.Session session, ActionCommand parent, ActionPorts.OutcomeArchive originals) throws IOException {
        var receipt = ContinuityActionJournal.lookup(session.head().state(), parent.actionId(), originals).orElseThrow(() -> new IOException("actual Sway parent custody unavailable"));
        return switch(receipt.state()) { case ActionState.CompositeRunning value -> value.execution(); case ActionState.CompositeUnknown value -> value.execution(); case ActionState.CompositeSettled value -> value.execution(); default -> throw new IllegalArgumentException("Sway parent is outside actual composite custody"); };
    }
    private static SwaySchedulerCompletion.Business business(ContinuityStorePort.Session session, ActionPorts.OutcomeArchive originals, List<ExactRef> childRefs) throws IOException {
        SwaySchedulerCompletion.Business business = new SwaySchedulerCompletion.NoNewBusiness();
        for (ExactRef ref : childRefs) { var child = originals.loadReceipt(ref); var actual = ContinuityActionJournal.lookup(session.head().state(), child.command().actionId(), originals).orElseThrow(() -> new IOException("actual Start child unavailable")); require(actual.bodySha256().equals(child.bodySha256()) && originals.receiptReferenceOf(actual).equals(ref), "child result differs from actual canonical receipt"); if (NativeRecordedEvidenceVerifier.settlement(actual.state()) instanceof ActionState.Applied) business = new SwaySchedulerCompletion.NewStartConfirmed(actual.command().actionId(), actual.bodySha256()); }
        return business;
    }
    private <T> PlanningReadResult<T> read(ContinuityStorePort.Session session, ReadContract<T> definition, PlanningRequest request, OpportunityJson.Obj arguments) { return reads.read(session, definition, new PlanningReadRequest(request.before(), request.source(), request.sessionId(), definition.operation(), arguments, request.deadline())); }
    private PlanningReadResult<OpportunityJson.Obj> rootRead(ContinuityStorePort.Session session,PlanningRequest request) {return root.read(reads,session,new PlanningReadRequest(request.before(),request.source(),request.sessionId(),root.operation(),root.arguments(),request.deadline()));}
    private static SwayTransitionCodec.Proofs proofs(List<ExactRef> refs) { return new SwayTransitionCodec.Proofs(refs, Optional.empty(), Optional.empty()); }
    private static OpportunityJson.Obj arguments(ObjectNode row) { return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)), "actual Sway arguments"); }
    private static void requireFrame(OrdinarySwaySchedule.Frame expected, PlanningRequest actual) { var frame = actual.before().frame(); require(expected.snapshotId().equals(frame.snapshotId()) && expected.publicRevision().equals(frame.revision()) && expected.nativeRevision().equals(frame.identity().nativeRevision()) && expected.dateRaw().equals(frame.identity().dateRaw()) && expected.actorCharacterId() == frame.identity().player().longValueExact(), "optional execution changed staged frame"); }
    private static ExpectedPostcondition expected(PlanningRequest request, String action, long target) { return new ExpectedPostcondition(1, request.before(), request.source(), SwayActionLifecycle.START_OBSERVER, List.of(new ExpectedBoolean(new FieldKey("sway.exact_active_observed"), true), new ExpectedText(new FieldKey("sway.action_id"), action), new ExpectedInteger(new FieldKey("sway.actor_character_id"), request.before().frame().identity().player()), new ExpectedInteger(new FieldKey("sway.target_character_id"), java.math.BigInteger.valueOf(target)))); }
}

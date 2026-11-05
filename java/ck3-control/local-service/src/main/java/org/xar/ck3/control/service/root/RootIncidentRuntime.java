package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadFailureCodec;
import org.xar.ck3.control.application.action.PlanningReadCoordinator;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal.Binding;
import org.xar.ck3.control.application.planning.events.EventIncidentCapturePort;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.application.planning.events.NativeWindowDiagnostic;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.offline.BatchReviewCompletionPort;
import org.xar.ck3.control.contracts.offline.RetainedIncidentBatchSource;
import org.xar.ck3.control.contracts.offline.IncidentJournalLayout;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Per-physical-Game production ports. Original journals survive Game retirement as source-review inputs only. */
public final class RootIncidentRuntime implements RootPlanningInputsFactory.OfflineInputs,
        ActionPorts.IntentPreparationPort, NativeEventEffects.ObservedAfter, EventIncidentCapturePort, RetainedIncidentBatchSource {
    private static final String BASIS_SCHEMA = "xar.java.incident-observation-original/v1";
    private static final int MAX_BASIS = 1 << 20;
    private static final int MAX_EPISODES = RetainedIncidentBatchSource.MAX_BATCHES;

    /** Fixed configured roles only: no previous ManagedGame, writer Session, journal or runtime closure. */
    public record Prepared(EpisodeIncidentJournal.Configuration baseConfiguration, ExactRef implementationSource) {
        public Prepared {
            Objects.requireNonNull(baseConfiguration); Objects.requireNonNull(implementationSource);
            StrictJson.require(baseConfiguration.trustedInteractions().isPresent(), "Actual trusted stock GUI/source context is required");
        }
        public RootIncidentRuntime install(RootRuntimeContext actualContext) throws IOException {
            Objects.requireNonNull(actualContext);
            plainDirectory(baseConfiguration.incidentRoot()); plainDirectory(baseConfiguration.scanRoot());
            baseConfiguration.trustedInteractions().orElseThrow().verifyCurrentRoots();
            StrictJson.require(baseConfiguration.trustedInteractions().orElseThrow().machineId().equals(actualContext.game().machineId()),
                    "Configured incident sources belong to another machine");
            verify(implementationSource, MAX_BASIS);
            return new RootIncidentRuntime(this, actualContext);
        }
    }

    /** Actual private preparation DATA only; archive and current-source validation occur at the capture boundary. */
    public record PendingBlocked(PendingUiEvent.Current current, PlanningReadReceipt receipt,
            ExactRef originalRead, OpportunityJson.Obj diagnosis) {
        public PendingBlocked {
            Objects.requireNonNull(current); Objects.requireNonNull(receipt);
            Objects.requireNonNull(originalRead); Objects.requireNonNull(diagnosis);
        }
    }

    /** Exact unavailable callback DATA, not a successful read receipt or a native action permit. */
    public record PendingReadFailure(PendingUiEvent.Current current, ReadContract<?> contract,
            PlanningReadRequest request, PlanningReadResult.Unavailable<?> unavailable,
            Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
        public PendingReadFailure {
            Objects.requireNonNull(current); Objects.requireNonNull(contract); Objects.requireNonNull(request);
            Objects.requireNonNull(unavailable); Objects.requireNonNull(attempted);
        }
    }

    /** Internal DATA source shared by the live private wrapper and original coordinator software regressions. */
    record ReadFailureOriginal(Complete frame, ReadContract<?> contract, PlanningReadRequest request,
            PlanningReadResult.Unavailable<?> unavailable, Optional<PlanningReadCoordinator.FailedReadAttempt> attempted,
            List<OpportunityJson.Obj> history, Optional<ActionCommand> parent, List<ExactRef> sourceOriginals) {
        ReadFailureOriginal {
            Objects.requireNonNull(frame); Objects.requireNonNull(contract); Objects.requireNonNull(request);
            Objects.requireNonNull(unavailable); Objects.requireNonNull(attempted);
            history = List.copyOf(Objects.requireNonNull(history)); Objects.requireNonNull(parent);
            sourceOriginals = List.copyOf(Objects.requireNonNull(sourceOriginals));
        }
    }

    private final Prepared prepared;
    private final RootRuntimeContext context;
    private EpisodeIncidentJournal current;
    private int batchCursor;
    private RootIncidentRuntime(Prepared prepared, RootRuntimeContext actualContext) { this.prepared = prepared; context = actualContext; }
    public RootPlanningInputsFactory.OfflineInputs offlineInputs() { return this; }
    public NativeEventEffects.ObservedAfter observedAfter() { return this; }
    public EventIncidentCapturePort capturePort() { return this; }
    void requireContext(RootRuntimeContext actual) {
        StrictJson.require(actual==context,"incident READ evidence must bind the identical physical Root");
    }
    @Override public <T> PlanningReadResult<T> read(PlanningReadPort actualReads, ReadContract<T> contract,
            PlanningReadRequest request, PlanningRequest planning) {
        Objects.requireNonNull(actualReads); Objects.requireNonNull(planning);
        boolean foreground=NativeWindowDiagnostic.foregroundKind(planning.observations().snapshot()).isPresent();
        if(!foreground)return actualReads.read(contract,request);
        try {
            Session original=context.borrowedSession();context.writer().requireSession(original);
            Complete frame=context.collector().currentPlanning(original,planning,planning.deadline(),(retained,lease)->lease.frame());
            requireOriginalSession(original,frame);
            var archive=context.archive().withSession(original);
            Complete rebuilt=context.frameLoader().load(NativeEffectEvidence.basis(frame),archive);requireSame(frame,rebuilt);
            return context.reads().readWithFailureEvidence(original,contract,request,(same,identical,requested,unavailable,attempted,originals)->{
                requireOriginalSession(same,rebuilt);String head=same.head().digest();
                StrictJson.require(context.readCatalog().containsIdentity(identical),"ordinary failed READ lost its identical installed contract");
                captureOrdinaryReadFailureOriginal(current(same,rebuilt),same,planning,rebuilt,identical,requested,unavailable,attempted,originals);
                unchanged(same,head);
            });
        } catch(IOException failure){throw new UncheckedIOException("actual ordinary READ incident source unavailable",failure);}
    }
    /** The same production ordinary seam is exercised with real coordinator/packet/archive failures. */
    static EpisodeIncidentJournal.Ticket captureOrdinaryReadFailureOriginal(EpisodeIncidentJournal journal, Session same,
            PlanningRequest planning, Complete frame, ReadContract<?> contract, PlanningReadRequest request,
            PlanningReadResult.Unavailable<?> unavailable, Optional<PlanningReadCoordinator.FailedReadAttempt> attempted,
            ActionPorts.OutcomeArchive originals) throws IOException {
        StrictJson.require(planning.before().equals(frame.identity())&&planning.source().equals(frame.source())
                &&planning.sessionId().equals(frame.sessionId())&&request.before().equals(planning.before())
                &&request.source().equals(planning.source())&&request.sessionId().equals(planning.sessionId())
                &&request.deadline().equals(planning.deadline()),"ordinary failed READ crossed its actual planning/frame/source/session/deadline");
        return captureReadFailureOriginal(journal,same,new ReadFailureOriginal(frame,contract,request,unavailable,attempted,
                planning.observations().history(),Optional.empty(),List.of(frame.originalEvidence(),NativeEffectEvidence.basis(frame).driverFacts())),originals);
    }
    public Path incidentBase() { return prepared.baseConfiguration().incidentRoot(); }
    public Path scanBase() { return prepared.baseConfiguration().scanRoot(); }
    public BatchReviewCompletionPort reviewCompletion() { return this::acknowledge; }
    public RootDomainIntentPreparation.Binding intentBinding() {
        return new RootDomainIntentPreparation.Binding("actual-uncovered-foreground-incident", prepared.implementationSource(), RootIncidentRuntime::supports, this);
    }

    /** Only the genuine committed fresh-entry proof can invoke this admission-specific initializer. */
    public void afterInitialEntry(Session original, RootInitialEpisodeProof actual) throws IOException {
        Objects.requireNonNull(actual).requireCurrent(original);
        requireOriginalSession(original, actual.frame());
        current(original, actual.frame());
    }

    public void afterInitialEntry(Session original,FreshCampaignContext actual)throws IOException {
        actual.requireCurrent(original);
        requireOriginalSession(original,actual.frame());
        current(original,actual.frame());
    }

    /** Retains only journal DATA from the installed private Source's actual callback.
     * It creates no ordinary Ready, planning request, private token or submission permission. */
    public void retainPendingUiFrame(Session same,PendingUiEvent.Current actual,Instant deadline)throws IOException {
        Objects.requireNonNull(actual);requireCurrent(same,actual.frame(),deadline);String head=same.head().digest();
        Complete original=replayPendingUiOriginal(actual,context.frameLoader(),context.archive().withSession(same));
        current(same,original);unchanged(same,head);
    }

    /** Captures a genuine rejected private selection without inventing an ordinary request, command or after. */
    public void retainPendingUiBlocked(Session same, PendingBlocked actual, Instant deadline) throws IOException {
        Objects.requireNonNull(actual); requireCurrent(same, actual.current().frame(), deadline); String head = same.head().digest();
        var archive = context.archive().withSession(same);
        Complete original = replayPendingUiOriginal(actual.current(), context.frameLoader(), archive);
        capturePendingUiBlockedOriginal(current(same, original), actual, original, archive, deadline);
        unchanged(same, head);
    }

    /** Invoked inside the genuine coordinator failure callback before its publication observer can move the head. */
    public void retainPendingUiReadFailure(Session same, PendingReadFailure actual,
            ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(actual); Objects.requireNonNull(originals);
        requireOriginalSession(same, actual.current().frame()); String head = same.head().digest();
        StrictJson.require(context.readCatalog().containsIdentity(actual.contract()), "Failed pending read lost its identical installed contract");
        if (actual.attempted().isPresent()) actual.attempted().orElseThrow().requireOriginal(same, actual.contract(),
                actual.request(), actual.unavailable(), originals);
        var archive = context.archive().withSession(same);
        Complete original = replayPendingUiOriginal(actual.current(), context.frameLoader(), archive);
        capturePendingUiReadFailureOriginal(current(same, original), same, actual, original, archive);
        unchanged(same, head);
    }

    /** Shared original-only failed-query producer. Missing attempt custody remains an unqualified diagnostic. */
    static EpisodeIncidentJournal.Ticket capturePendingUiReadFailureOriginal(EpisodeIncidentJournal journal, Session same,
            PendingReadFailure actual, Complete original, ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(journal); Objects.requireNonNull(same); Objects.requireNonNull(actual); Objects.requireNonNull(originals);
        requireSame(actual.current().frame(), Objects.requireNonNull(original));
        return captureReadFailureOriginal(journal, same, new ReadFailureOriginal(original, actual.contract(), actual.request(),
                actual.unavailable(), actual.attempted(), actual.current().history(), Optional.of(actual.current().originalParent()),
                actual.current().originals()), originals);
    }
    static EpisodeIncidentJournal.Ticket captureReadFailureOriginal(EpisodeIncidentJournal journal, Session same,
            ReadFailureOriginal actual, ActionPorts.OutcomeArchive originals) throws IOException {
        Objects.requireNonNull(journal); Objects.requireNonNull(same); Objects.requireNonNull(actual); Objects.requireNonNull(originals);
        var original = actual.frame(); var request = actual.request();
        StrictJson.require(request.before().equals(original.identity()) && request.source().equals(original.source())
                && request.sessionId().equals(original.sessionId()) && request.operation().equals(actual.contract().operation()),
                "Failed pending query crossed its original frame/source/session/contract");
        Optional<EpisodeIncidentJournal.FailedReadReferences> retained = Optional.empty();
        if (actual.attempted().isPresent()) {
            var proof = actual.attempted().orElseThrow();
            proof.requireOriginal(same, actual.contract(), request, actual.unavailable(), originals);
            Optional<ExactRef> observed = actual.unavailable().observedFailure().isPresent()
                    ? Optional.of(PlanningReadFailureCodec.preserve(actual.unavailable().observedFailure().orElseThrow(), originals)) : Optional.empty();
            var dependencies = originals.loadFailedReadOriginals(request, proof.requestId(), proof.before(), proof.prepared(),
                    proof.original(), observed).references();
            retained = Optional.of(new EpisodeIncidentJournal.FailedReadReferences(proof.originalRef(), proof.preparedRef(), observed, dependencies));
        }
        var raw = StrictJson.object().put("schema", "xar.pending-ui-read-failure/v1")
                .put("reason", actual.unavailable().reason()).put("operation", request.operation().value())
                .put("typed_decode_failure_present", actual.unavailable().decodeFailure().isPresent());
        if (actual.parent().isPresent()) {
            raw.put("original_parent_action_id", actual.parent().orElseThrow().actionId());
            raw.put("original_parent_body_sha256", org.xar.ck3.control.application.action.ActionCodec.bodySha256(actual.parent().orElseThrow()));
        } else { raw.putNull("original_parent_action_id"); raw.putNull("original_parent_body_sha256"); }
        raw.set("origin", ProposalLifecycleCodec.observation(original.identity()));
        var sources = raw.putArray("source_originals");
        actual.sourceOriginals().forEach(ref -> sources.add(ref.toJson()));
        if (retained.isPresent()) {
            raw.set("original_outcome_ref", retained.orElseThrow().originalOutcome().toJson());
            raw.set("prepared_request_ref", retained.orElseThrow().preparedRequest().toJson());
            if (retained.orElseThrow().observedFailure().isPresent()) raw.set("observed_failure_ref", retained.orElseThrow().observedFailure().orElseThrow().toJson());
            else raw.putNull("observed_failure_ref");
        } else { raw.putNull("original_outcome_ref"); raw.putNull("prepared_request_ref"); raw.putNull("observed_failure_ref"); }
        var failure = OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(raw)), "actual failed pending read DATA");
        var plan = NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(original.identity(), original.semantic(),
                new ArrayList<>(actual.history()), Optional.empty(), Optional.of(failure), actual.unavailable().reason()))
                .orElseThrow(() -> new IllegalArgumentException("failed pending read has no retained actual foreground"));
        var binding = new Binding(original.identity(), original.source(), original.sessionId());
        if (retained.isPresent()) return journal.captureFailedRead(binding, plan, original.originalEvidence(), retained.orElseThrow());
        return journal.captureBlocked(binding, plan, original.originalEvidence(), Optional.empty());
    }

    /** Same source DATA producer as the real private callback; callers cannot obtain native or action authority. */
    static EpisodeIncidentJournal.Ticket capturePendingUiBlockedOriginal(EpisodeIncidentJournal journal,
            PendingBlocked actual, Complete original, ActionPorts.OutcomeArchive archive, Instant deadline) throws IOException {
        Objects.requireNonNull(journal); Objects.requireNonNull(actual); Objects.requireNonNull(archive); Objects.requireNonNull(deadline);
        var current = actual.current(); requireSame(current.frame(), Objects.requireNonNull(original));
        var receipt = actual.receipt(); var request = receipt.request();
        StrictJson.require(archive.loadRead(actual.originalRead()).equals(receipt)
                && request.before().equals(original.identity()) && request.source().equals(original.source())
                && request.sessionId().equals(original.sessionId()) && request.deadline().equals(deadline)
                && receipt.original().nativeOk(), "Blocked pending capture lost its same-archive actual read/frame/source/session/deadline");
        var meta = OpportunityJson.object(actual.diagnosis().get("pending_ui_event_source"), "actual blocked pending source metadata");
        StrictJson.require(meta.members().keySet().equals(Set.of("schema", "original_parent_action_id", "original_parent_body_sha256", "original_read", "source_originals"))
                && new OpportunityJson.Text("xar.pending-ui-event-source/v1").equals(meta.get("schema"))
                && new OpportunityJson.Text(current.originalParent().actionId()).equals(meta.get("original_parent_action_id"))
                && new OpportunityJson.Text(org.xar.ck3.control.application.action.ActionCodec.bodySha256(current.originalParent())).equals(meta.get("original_parent_body_sha256"))
                && ExactRef.fromJson(DriverJson.toNode(meta.get("original_read"))).equals(actual.originalRead()),
                "Blocked pending diagnosis changed its actual parent or original read");
        if (!(meta.get("source_originals") instanceof OpportunityJson.Arr refs)) throw new IllegalArgumentException("blocked pending source originals must be an array");
        StrictJson.require(refs.items().stream().map(row -> ExactRef.fromJson(DriverJson.toNode(row))).toList().equals(current.originals()),
                "Blocked pending diagnosis changed its retained actual source originals");
        OpportunityJson.Obj plan = actual.diagnosis();
        boolean standard = plan.get("selected_step") == OpportunityJson.Nil.INSTANCE
                && (plan.get("unhandled_event_fallback") instanceof OpportunityJson.Obj
                    || plan.get("unhandled_interaction_fallback") instanceof OpportunityJson.Obj
                    || plan.get("unhandled_native_window_diagnostic") instanceof OpportunityJson.Obj);
        if (!standard) {
            RawJson token = receipt.original().originalResultToken().orElseThrow(() -> new IllegalArgumentException("actual blocked native read token required"));
            var raw = DriverJson.object(token.bytes(), RawJson.MAXIMUM_BYTES);
            String key = original.semantic().get("active_event") instanceof OpportunityJson.Obj
                    ? "current_event_window_context" : "pending_character_interaction_context";
            Optional<OpportunityJson.Value> context = raw.members().containsKey(key) ? Optional.of(raw.get(key)) : Optional.empty();
            String reason = plan.get("phase") instanceof OpportunityJson.Text phase ? phase.value() : "pending_ui_selection_rejected";
            plan = NativeWindowDiagnostic.plan(new NativeWindowDiagnostic.Source(original.identity(), original.semantic(),
                    new ArrayList<>(current.history()), context, Optional.of(actual.diagnosis()), reason))
                    .orElseThrow(() -> new IllegalArgumentException("blocked pending source has no actual foreground window"));
        }
        return journal.captureBlocked(new Binding(original.identity(), original.source(), original.sessionId()), plan,
                original.originalEvidence(), Optional.of(actual.originalRead()));
    }

    /** Original-only DATA replay shared by the actual initializer and its software boundary tests. */
    static Complete replayPendingUiOriginal(PendingUiEvent.Current actual,NativeEffectEvidence.FrameLoader frames,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(actual);Objects.requireNonNull(frames);Objects.requireNonNull(archive);
        RawJson driver=archive.loadMaterial(actual.originalDriver());
        StrictJson.require(archive.materialReferenceOf(driver).equals(actual.originalDriver())
                &&java.util.Arrays.equals(driver.bytes(),actual.known().driver().encode())
                &&java.util.Arrays.equals(driver.bytes(),actual.full().facts().driver().encode()),
                "Pending journal DATA changed its original full successor Driver");
        RawJson history=archive.loadMaterial(actual.originalHistoryBasis());
        StrictJson.require(archive.materialReferenceOf(history).equals(actual.originalHistoryBasis()),
                "Pending journal DATA lost its original full history basis");
        var basis=NativeEffectEvidence.basis(actual.frame());RawJson manifest=archive.loadMaterial(basis.driverFacts());
        StrictJson.require(DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest).equals(actual.originalDriver()),
                "Pending journal DATA changed the original Driver reference selected by its native-frame manifest");
        Complete rebuilt=frames.load(basis,archive);requireSame(actual.frame(),rebuilt);
        StrictJson.require(actual.full().fullBindingSha256().equals(rebuilt.fullBindingSha256()),
                "Pending journal DATA changed its actual full native/Driver binding");
        return rebuilt;
    }

    @Override public RootPlanningInputsFactory.OfflineObservation collect(RootPlanningInputsFactory.Capture actual, PlanningRequest complete) throws IOException {
        StrictJson.require(actual.context() == context && complete.before().equals(actual.frame().identity())
                && complete.source().equals(actual.frame().source()) && complete.sessionId().equals(actual.frame().sessionId()),
                "Incident inputs must consume the actual current complete request");
        requireCurrent(actual.session(), actual.frame(), actual.deadline()); String head = actual.session().head().digest();
        EpisodeIncidentJournal own = current(actual.session(), actual.frame());
        List<EpisodeIncidentJournal> journals = originals(actual.session());
        List<ExactRef> evidence = new ArrayList<>(); List<BatchRequest> candidates = new ArrayList<>();
        // Every configured episode is scanned. Old-source batches retain their old full binding;
        // no old Game is queried or admitted, and no pending source incident is silently dropped.
        // The ordinary scan carries the real later full-frame original for UI-recovery date-progress analysis.
        for (EpisodeIncidentJournal.Scan scan : scanOriginals(journals, journal -> journal.episodeReference().equals(own.episodeReference())
                ? new Binding(complete.before(), complete.source(), complete.sessionId()) : journal.origin(),
                journal -> journal.episodeReference().equals(own.episodeReference())
                        ? Optional.of(() -> context.archive().withSession(actual.session()).preserveMaterial(originalObservationBasis(actual.frame()))) : Optional.empty())) {
            evidence.addAll(scan.evidence()); scan.batch().ifPresent(candidates::add);
        }
        Optional<BatchRequest> batch;
        synchronized (this) {
            batch = candidates.isEmpty() ? Optional.empty() : Optional.of(candidates.get(Math.floorMod(batchCursor, candidates.size())));
            batchCursor = candidates.isEmpty() ? 0 : (Math.floorMod(batchCursor, candidates.size()) + 1) % candidates.size();
        }
        unchanged(actual.session(), head);
        return new RootPlanningInputsFactory.OfflineObservation(new RootPlanningInputsFactory.FieldSource(
                complete.before(), complete.source(), complete.sessionId(), List.copyOf(new LinkedHashSet<>(evidence))), batch);
    }

    /** Batch-end source DATA. It never requires or fabricates a current player/episode/Ready frame. */
    @Override public List<BatchRequest> scan() throws IOException {
        return context.withSession(same -> {
            context.writer().requireSession(same); String head = same.head().digest();
            // Every opened journal is revalidated against its fixed configured scope and archived originals.
            List<BatchRequest> batches = retainedOriginalBatches(originals(same));
            unchanged(same, head); return batches;
        });
    }

    /** The same actual journal producer serves Ready collection and retained-only batch boundaries. */
    static List<BatchRequest> retainedOriginalBatches(List<EpisodeIncidentJournal> journals) throws IOException {
        return scanOriginals(journals, EpisodeIncidentJournal::origin).stream()
                .flatMap(scan -> scan.batch().stream()).toList();
    }
    private static List<EpisodeIncidentJournal.Scan> scanOriginals(List<EpisodeIncidentJournal> supplied,
            java.util.function.Function<EpisodeIncidentJournal, Binding> binding) throws IOException {
        return scanOriginals(supplied, binding, journal -> Optional.empty());
    }
    private static List<EpisodeIncidentJournal.Scan> scanOriginals(List<EpisodeIncidentJournal> supplied,
            java.util.function.Function<EpisodeIncidentJournal, Binding> binding,
            java.util.function.Function<EpisodeIncidentJournal, Optional<EpisodeIncidentJournal.ProgressOriginal>> progress) throws IOException {
        List<EpisodeIncidentJournal> journals = List.copyOf(Objects.requireNonNull(supplied)); Objects.requireNonNull(binding); Objects.requireNonNull(progress);
        StrictJson.require(journals.size() <= MAX_EPISODES, "bounded retained original episode scan required");
        Set<String> paths = new java.util.HashSet<>();
        for (EpisodeIncidentJournal journal : journals) StrictJson.require(paths.add(journal.episodeReference().path()),
                "retained original episode scan contains a duplicate scope");
        List<EpisodeIncidentJournal.Scan> result = new ArrayList<>();
        for (EpisodeIncidentJournal journal : journals.stream().sorted(Comparator.comparing(j -> j.episodeReference().path())).toList()) {
            Binding actual = Objects.requireNonNull(binding.apply(journal));
            Optional<EpisodeIncidentJournal.ProgressOriginal> original = Objects.requireNonNull(progress.apply(journal));
            result.add(original.isPresent() ? journal.scanWithProgress(actual, original.orElseThrow()) : journal.scan(actual));
        }
        return List.copyOf(result);
    }

    @Override public void prepare(Session original, ActionCommand command) {
        if (!supports(command)) return;
        try {
            requireCommand(original, command); String head = original.head().digest();
            installed(command).before(command).orElseThrow(() -> new IOException("Actual fallback requires its original incident capture"));
            unchanged(original, head);
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    /** Same original-only seam used by ordinary blocked-modal capture; it grants no action or after. */
    static EpisodeIncidentJournal.Ticket captureBlockedOriginal(EpisodeIncidentJournal journal,PlanningRequest actual,OpportunityJson.Obj retainedPlan,
            Complete frame,ActionPorts.OutcomeArchive archive)throws IOException {
        StrictJson.require(actual.before().equals(frame.identity())&&actual.source().equals(frame.source())
                &&actual.sessionId().equals(frame.sessionId()),"blocked modal crossed its actual frame/source/session");
        Optional<ExactRef> read=Optional.empty();
        var diagnostic=retainedPlan.get("unhandled_native_window_diagnostic");
        if(diagnostic instanceof OpportunityJson.Obj body&&body.get("original_plan") instanceof OpportunityJson.Obj plan
                &&plan.get("mandatory_choice_original_read") instanceof OpportunityJson.Obj ref) {
            ExactRef candidate=ExactRef.fromJson(DriverJson.toNode(ref));
            var receipt=archive.loadRead(candidate);
            StrictJson.require(receipt.contractId().equals("native/mandatory-choice-v1")&&receipt.request().operation().value().equals(RootMandatoryChoiceRuntime.QUERY)
                    &&receipt.request().before().equals(actual.before())&&receipt.request().source().equals(actual.source())
                    &&receipt.request().sessionId().equals(actual.sessionId())&&receipt.request().deadline().equals(actual.deadline())
                    &&receipt.original().nativeOk(),"blocked modal lost its actual original query");
            read=Optional.of(candidate);
        }
        return journal.captureBlocked(new Binding(actual.before(),actual.source(),actual.sessionId()),retainedPlan,frame.originalEvidence(),read);
    }

    @Override public void captureBlocked(PlanningRequest actual, OpportunityJson.Obj retainedPlan) throws IOException {
        // Public evaluation may own a scope; ordinary AUTO can arrive after Ready returns.
        // Revalidate the original frame in the actual current readiness scope below.
        // No command ID, selected action, dispatch ACK or synthetic after is produced.
        Session original = context.borrowedSession(); context.writer().requireSession(original);
        context.requireCurrent(actual.deadline());
        context.readiness().current(original, actual.before(), actual.deadline(), lease -> {
            requireCurrent(original, lease.frame(), actual.deadline());
            StrictJson.require(actual.source().equals(lease.frame().source()) && actual.sessionId().equals(lease.frame().sessionId()),
                    "Blocked-window capture crossed its actual source/session");
            String head = original.head().digest();
            captureBlockedOriginal(current(original,lease.frame()),actual,retainedPlan,lease.frame(),context.archive().withSession(original));
            unchanged(original, head); return null;
        });
    }

    @Override public void record(ActionCommand command, ActionState.Attempt attempt, NativeEffectSnapshots.Pair pair, NativeEffectRegistry.Projected projected) {
        if (!supports(command)) return;
        try {
            Session original = context.borrowedSession(); requireCommandOrigin(original, command); String head = original.head().digest();
            EpisodeIncidentJournal journal=installedForObservation(original,command,attempt);
            if(journal.legacyLookupRequired(command)) {
                StrictJson.require(projected.result() instanceof ActionPorts.EffectObserved,"legacy after requires its real observed effect");
                var observed=((ActionPorts.EffectObserved)projected.result()).observation();
                StrictJson.require(observed.supportingEvidence().size()==1,"legacy first-rendered after requires its exact sole original effect basis");
                RawJson proof=journal.prepareLegacyBinding(command,attempt,pair.before(),legacyCanonicalEvidence(original,command,attempt,observed.supportingEvidence()));
                journal.observedAfterLegacy(command,attempt,pair,projected,proof);
            } else journal.observedAfter(command, attempt, pair, projected);
            unchanged(original, head);
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    /** Reuses only an immutable historical EVENT proof; the current physical scope is never relabelled as that old observation. */
    @Override public Optional<org.xar.ck3.control.application.effects.NativeEffectRegistry.Projected> replayExisting(ActionCommand command,ActionState.Attempt attempt,
            org.xar.ck3.control.application.action.NativeActionPort.DispatchOutcome dispatch) {
        if(!supports(command)||!command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}")
                ||!org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.EVENT_SCHEMA.equals(command.expected().observerSchema())
                ||!org.xar.ck3.control.application.action.ActionReconciliationScope.activeFor(command))return Optional.empty();
        try {
            Session same=context.borrowedSession();requireCommandOrigin(same,command);String head=same.head().digest();
            EpisodeIncidentJournal journal=installedForObservation(same,command,attempt);
            if(!journal.legacyLookupRequired(command))return Optional.empty();
            // This validates current canonical membership/ACK only. Its current guard is not substituted into the historical proof.
            legacyCanonicalEvidence(same,command,attempt,List.of());
            Optional<RawJson> existing=journal.existingLegacyAfter(command);
            if(existing.isEmpty()){unchanged(same,head);return Optional.empty();}
            ObjectNode envelope=StrictJson.object(StrictJson.parse(existing.orElseThrow().bytes(),MAX_BASIS),Set.of("schema","scan_ref","before_index","after_index","after"));
            StrictJson.require("xar.episode-incident-existing-after/v1".equals(StrictJson.text(envelope.get("schema"))),"unregistered existing event original envelope");
            ObjectNode index=read(ExactRef.fromJson(envelope.get("after_index")),MAX_BASIS);
            StrictJson.require(ExactRef.fromJson(index.get("after_ref")).equals(ExactRef.fromJson(envelope.get("after"))),"existing after body changed its owned pin");
            StrictJson.require(index.get("legacy_command_binding") instanceof ObjectNode,"existing after lost its original versioned proof");
            ObjectNode proof=(ObjectNode)index.get("legacy_command_binding");
            var bound=context.archive().withSession(same);var original=bound.loadReceipt(ExactRef.fromJson(proof.get("canonical_receipt_ref")));
            StrictJson.require(java.util.Arrays.equals(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(original.command()),org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command))
                    &&original.bodySha256().equals(org.xar.ck3.control.application.action.ActionCodec.bodySha256(command))
                    &&org.xar.ck3.control.application.action.ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent()
                    &&original.ack().filter(dispatch::equals).isPresent(),"existing after changed the complete current original command/Attempt/dispatch");
            var replayed=verifyLegacyBinding(new RawJson(StrictJson.canonical(proof,MAX_BASIS)));
            StrictJson.require(replayed.isPresent(),"existing after has no fully replayed original effect");
            StrictJson.require(journal.existingLegacyAfter(command).filter(existing.orElseThrow()::equals).isPresent(),"existing event originals changed during Root replay");
            unchanged(same,head);
            return replayed;
        } catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    @Override public void recordUnsettled(ActionCommand command,ActionState.Attempt attempt,NativeEventEffects.UnsettledObservation observed) {
        if(!supports(command))return;
        try {
            Session original=context.borrowedSession();requireCommandOrigin(original,command);String head=original.head().digest();
            // The sole coordinator archived this original ACK/UNKNOWN before invoking its observer.
            ExactRef dispatch=context.archive().withSession(original).referenceOf(observed.dispatch());
            EpisodeIncidentJournal journal=installedForObservation(original,command,attempt);
            if(journal.legacyLookupRequired(command)) {
                RawJson proof=journal.prepareLegacyBinding(command,attempt,observed.frames().before(),legacyCanonicalEvidence(original,command,attempt,List.of()));
                journal.observedUnsettledLegacy(command,attempt,observed,dispatch,proof);
            } else journal.observedUnsettled(command,attempt,observed,dispatch);
            unchanged(original,head);
        } catch(IOException failure){throw new UncheckedIOException(failure);}
    }

    /** Source-review completion may run after the originating Game retires; it grants no action/readiness authority. */
    private void acknowledge(BatchRequest original, ExactRef report) throws IOException {
        context.withSession(same -> {
            String head = same.head().digest(); ObjectNode manifest = read(original.manifestRef(), MAX_BASIS);
            var observed=EpisodeIncidentJournal.requireBatchManifest(manifest);
            ExactRef index = observed.indexRef();
            EpisodeIncidentJournal journal = originals(same).stream()
                    .filter(j -> Path.of(index.path()).getParent().equals(j.configuration().scanRoot())).findFirst()
                    .orElseThrow(() -> new IOException("Batch is absent from the actual configured original journals"));
            journal.acknowledge(original, report); unchanged(same, head); return null;
        });
    }

    private synchronized EpisodeIncidentJournal current(Session same, Complete frame) throws IOException {
        Binding binding = new Binding(frame.identity(), frame.source(), frame.sessionId());
        if (current != null && current.origin().before().frame().episodeRunId().equals(binding.before().frame().episodeRunId())) {
            current.origin().requireEpisode(binding); return current;
        }
        var scope = scope(binding); createScope(scope);
        var configured = configuration(scope); Path stamp = scope.incidentRoot().resolve("EPISODE.json");
        if (Files.exists(stamp, LinkOption.NOFOLLOW_LINKS)) {
            current = EpisodeIncidentJournal.open(configured, binding, EpisodeIncidentJournal.measure(stamp)); replay(same, current);
        } else {
            var actualBasis = NativeEffectEvidence.basis(frame); var archive = context.archive().withSession(same);
            // Rebuild before retaining even the initial empty scan. Archive/frame shape alone is insufficient.
            Complete rebuilt = context.frameLoader().load(actualBasis, archive); requireSame(frame, rebuilt);
            prepared.baseConfiguration().io().require(MAX_BASIS);
            ExactRef retained = archive.preserveMaterial(originalObservationBasis(frame));
            current = EpisodeIncidentJournal.initializeObserved(configured, binding, retained);
        }
        return current;
    }

    /** One unchanged incident-basis encoding for ordinary, initial-entry and private pending frames. */
    static RawJson originalObservationBasis(Complete frame) {
        var basis=NativeEffectEvidence.basis(Objects.requireNonNull(frame));
        ObjectNode row=StrictJson.object().put("schema",BASIS_SCHEMA).put("session_id",frame.sessionId());
        row.set("origin",ProposalLifecycleCodec.observation(frame.identity()));row.set("source",ProposalLifecycleCodec.source(frame.source()));
        row.set("native_frame",basis.nativeFrame().toJson());row.set("driver_facts",basis.driverFacts().toJson());
        return new RawJson(StrictJson.canonical(row));
    }

    private List<EpisodeIncidentJournal> originals(Session same) throws IOException {
        plainDirectory(incidentBase()); plainDirectory(scanBase()); List<Path> directories;
        try (var entries = Files.list(incidentBase())) { directories = entries.sorted().toList(); }
        StrictJson.require(directories.size() <= MAX_EPISODES, "Bounded configured episode inventory required");
        List<EpisodeIncidentJournal> journals = new ArrayList<>(); Set<Path> scanDirectories = new java.util.HashSet<>();
        for (Path directory : directories) {
            plainDirectory(directory); StrictJson.require(directory.getFileName().toString().matches("[0-9a-f]{64}"), "Unknown incident base entry requires reconciliation");
            var candidate = new IncidentJournalLayout.Scope(directory, scanBase().resolve(directory.getFileName()));
            plainDirectory(candidate.scanRoot());
            EpisodeIncidentJournal journal = EpisodeIncidentJournal.openOriginal(configuration(candidate), EpisodeIncidentJournal.measure(directory.resolve("EPISODE.json")));
            var expected = scope(journal.origin()); StrictJson.require(expected.equals(candidate), "Original journal is outside its recomputed configured scope");
            StrictJson.require(journal.origin().before().machineId().equals(context.game().machineId()), "Original incident belongs to another configured machine");
            replay(same, journal); journals.add(journal); scanDirectories.add(candidate.scanRoot());
        }
        try (var entries = Files.list(scanBase())) {
            for (Path directory : entries.toList()) { plainDirectory(directory); StrictJson.require(scanDirectories.contains(directory), "Orphan original scan scope requires reconciliation"); }
        }
        return journals;
    }

    private void replay(Session same, EpisodeIncidentJournal journal) throws IOException {
        ExactRef ref = journal.originalObservationBasis().orElseThrow(() -> new IOException("Legacy journal requires explicit original-frame import; it cannot be treated as scanned empty"));
        var archive = context.archive().withSession(same); var material = archive.loadMaterial(ref);
        StrictJson.require(archive.materialReferenceOf(material).equals(ref), "Original incident basis changed");
        ObjectNode row = StrictJson.object(StrictJson.parse(material.bytes(), MAX_BASIS), Set.of("schema", "session_id", "origin", "source", "native_frame", "driver_facts"));
        StrictJson.require(BASIS_SCHEMA.equals(StrictJson.text(row.get("schema"))), "Actual incident observation basis required");
        var basis = new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts")));
        Complete frame = context.frameLoader().load(basis, archive); Binding binding = journal.origin();
        StrictJson.require(frame.identity().equals(binding.before()) && frame.source().equals(binding.source()) && frame.sessionId().equals(binding.sessionId())
                && ProposalLifecycleCodec.decodeObservation(row.get("origin")).equals(frame.identity())
                && java.util.Arrays.equals(StrictJson.canonical(row.get("source"),MAX_BASIS),StrictJson.canonical(ProposalLifecycleCodec.source(frame.source()),MAX_BASIS))
                && frame.sessionId().equals(StrictJson.text(row.get("session_id"))), "Original full incident frame/source/session changed");
    }

    private EpisodeIncidentJournal installed(ActionCommand command) throws IOException {
        EpisodeIncidentJournal result;
        synchronized (this) { result = current; }
        if (result == null) throw new IOException("Actual current full-frame incident scan has not initialized this physical Game");
        result.origin().requireEpisode(new Binding(command.before(), command.source(), command.sessionId())); return result;
    }
    /** Opens only an existing same-episode original during the coordinator's issued read-only callback. */
    private EpisodeIncidentJournal installedForObservation(Session same,ActionCommand command,ActionState.Attempt attempt)throws IOException {
        synchronized(this){if(current!=null)return installed(command);}
        org.xar.ck3.control.application.action.ActionReconciliationScope.requireIdentity(command,attempt);
        requireCommandOrigin(same,command);var selected=scope(new Binding(command.before(),command.source(),command.sessionId()));
        plainDirectory(selected.incidentRoot());plainDirectory(selected.scanRoot());
        EpisodeIncidentJournal opened=EpisodeIncidentJournal.openOriginal(configuration(selected),EpisodeIncidentJournal.measure(selected.incidentRoot().resolve("EPISODE.json")));
        opened.origin().requireEpisode(new Binding(command.before(),command.source(),command.sessionId()));replay(same,opened);
        synchronized(this){if(current==null)current=opened;return installed(command);}
    }
    /** This JSON is DATA. Authority comes from the already active sole-coordinator reconciliation scope. */
    private RawJson legacyCanonicalEvidence(Session same,ActionCommand command,ActionState.Attempt attempt,List<ExactRef> supports)throws IOException {
        var identity=org.xar.ck3.control.application.action.ActionReconciliationScope.requireIdentity(command,attempt);
        var guard=org.xar.ck3.control.application.action.ActionReconciliationScope.requireObservationGuard(command,attempt);
        StrictJson.require(identity.driverRelation()==org.xar.ck3.control.application.action.ReconciliationIdentity.DriverRelation.EXACT,
                "legacy EVENT recovery does not authorize a Driver history append");
        var bound=context.archive().withSession(same);var original=bound.loadReceipt(identity.pending().originalReceipt());
        var record=org.xar.ck3.control.application.action.ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),original,bound);
        StrictJson.require(original.state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown
                &&java.util.Arrays.equals(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(original.command()),org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command))
                &&org.xar.ck3.control.application.action.ActionTransitions.attempt(original.state()).filter(attempt::equals).isPresent(),
                "legacy recovery requires its complete actual original UNKNOWN and Attempt");
        var ack=original.ack().filter(org.xar.ck3.control.application.action.NativeActionPort.AckReceived::nativeOk)
                .orElseThrow(()->new IOException("legacy EVENT recovery requires its retained actual accepted ACK"));
        StrictJson.require(ack.outbound().isPresent()&&ack.requestId().equals(attempt.requestId()),"legacy recovery lost original outbound/ACK custody");
        ack.custody().orElseThrow(()->new IOException("legacy recovery lacks actual ACK custody")).verify(ack,attempt.guard());
        byte[] commandBytes=org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command);
        var canonical=org.xar.ck3.control.application.action.ActionCodec.decodeCommand(commandBytes);
        ObjectNode row=StrictJson.object().put("schema",EpisodeIncidentJournal.LEGACY_BINDING_SCHEMA);
        row.set("canonical_receipt_ref",identity.pending().originalReceipt().toJson());row.set("canonical_record_ref",record.toJson());
        row.set("canonical_dispatch_ref",bound.referenceOf(ack).toJson());
        row.put("canonical_command_base64",java.util.Base64.getEncoder().encodeToString(commandBytes));
        row.put("canonical_command_sha256",original.bodySha256());row.put("canonical_arguments_sha256",DriverJson.sha256(DriverJson.encode(canonical.arguments())));
        row.set("reconciliation_guard",org.xar.ck3.control.application.action.CommandOriginCodec.guard(guard));
        StrictJson.require(supports.size()<=1,"legacy first-rendered observation has an unexpected material branch");
        var evidence=row.putArray("observation_supporting_refs");supports.forEach(ref->evidence.add(ref.toJson()));
        return new RawJson(StrictJson.canonical(row,MAX_BASIS));
    }
    /** Same verifier for live admission and cold side-evidence interpretation; the latter uses historical custody. */
    private Optional<org.xar.ck3.control.application.effects.NativeEffectRegistry.Projected> verifyLegacyBinding(RawJson serialized) {
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);String head=same.head().digest();
            ObjectNode row=(ObjectNode)StrictJson.parse(serialized.bytes(),MAX_BASIS);
            var bound=context.archive().withSession(same);ExactRef receiptRef=ExactRef.fromJson(row.get("canonical_receipt_ref"));
            var original=bound.loadReceipt(receiptRef);ActionCommand command=original.command();requireCommandOrigin(same,command);
            var record=org.xar.ck3.control.application.action.ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),original,bound);
            StrictJson.require(record.equals(ExactRef.fromJson(row.get("canonical_record_ref")))
                    &&original.state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown,
                    "legacy proof is not its exact historical canonical UNKNOWN record");
            var attempt=org.xar.ck3.control.application.action.ActionTransitions.attempt(original.state()).orElseThrow();
            var ack=original.ack().filter(org.xar.ck3.control.application.action.NativeActionPort.AckReceived::nativeOk)
                    .orElseThrow(()->new IOException("legacy proof lacks its actual accepted ACK"));
            StrictJson.require(ack.outbound().isPresent()&&ack.requestId().equals(attempt.requestId())
                    &&bound.referenceOf(ack).equals(ExactRef.fromJson(row.get("canonical_dispatch_ref"))),"legacy proof changed actual original dispatch/ACK");
            ack.custody().orElseThrow(()->new IOException("legacy proof lacks actual ACK custody")).verify(ack,attempt.guard());
            var guard=org.xar.ck3.control.application.action.CommandOriginCodec.guard(row.get("reconciliation_guard"));
            StrictJson.require(guard.origin() instanceof org.xar.ck3.control.application.action.CommandOrigin.Reconciliation,"actual reconciliation guard required");
            var identity=guard.origin().requireReconciliation();
            StrictJson.require(identity.driverRelation()==org.xar.ck3.control.application.action.ReconciliationIdentity.DriverRelation.EXACT
                    &&identity.pending().originalReceipt().equals(receiptRef)&&identity.pending().actionId().equals(command.actionId())
                    &&identity.pending().bodySha256().equals(original.bodySha256())&&identity.pending().requestId().equals(attempt.requestId()),
                    "legacy proof changed its actual original pending identity");
            // Live admission is checked by Journal.requireLegacyLive; stored proofs retain their own historical guard.
            var after=context.reconciliation().verifyArchived(guard,bound,same,context.originals());
            var before=org.xar.ck3.control.application.effects.RootGuardEvidence.loadFrame(attempt.guard(),bound,context.frameLoader());
            var selected=scope(new Binding(command.before(),command.source(),command.sessionId()));
            var journal=EpisodeIncidentJournal.openOriginal(configuration(selected),EpisodeIncidentJournal.measure(selected.incidentRoot().resolve("EPISODE.json")));
            journal.verifyLegacyBindingData(serialized,command,before);
            var replayed=verifyLegacyEffectBasis(row,original,attempt,guard,before,after,bound);
            StrictJson.require(after.identity().equals(identity.factual())&&after.source().equals(command.source())&&after.sessionId().equals(command.sessionId()),
                    "legacy proof changed its actual historical physical after");
            verifyLegacyProducer(command,before,row);
            unchanged(same,head);
            return replayed;
        } catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private Optional<org.xar.ck3.control.application.effects.NativeEffectRegistry.Projected> verifyLegacyEffectBasis(ObjectNode proof,org.xar.ck3.control.application.action.ActionReceipt original,ActionState.Attempt attempt,
            org.xar.ck3.control.application.action.GuardEvidence guard,Complete before,Complete after,ActionPorts.OutcomeArchive bound)throws IOException {
        JsonNode supports=proof.get("observation_supporting_refs");StrictJson.require(supports!=null&&supports.isArray()&&supports.size()<=1,"bounded explicit legacy observation supports required");
        if(supports.isEmpty())return Optional.empty();
        ExactRef reference=ExactRef.fromJson(supports.get(0));RawJson raw=bound.loadMaterial(reference);
        StrictJson.require(raw.bytes().length==reference.bytes()&&DriverJson.sha256(raw.bytes()).equals(reference.sha256()),"legacy effect basis original changed");
        ObjectNode basis=(ObjectNode)StrictJson.parse(raw.bytes(),MAX_BASIS);
        StrictJson.require((NativeEffectEvidence.RECONCILIATION_SCHEMA.equals(basis.path("schema").asText())
                ||NativeEffectEvidence.RECONCILED_EVENT_READ_SCHEMA.equals(basis.path("schema").asText()))
                &&original.bodySha256().equals(basis.path("command_body_sha256").asText())&&attempt.requestId().equals(basis.path("request_id").asText())
                &&org.xar.ck3.control.application.action.CommandOriginCodec.guard(basis.get("reconciliation_guard")).equals(guard),"legacy effect basis changed canonical command/request/guard");
        var initial=NativeEffectEvidence.basis(before);var ending=NativeEffectEvidence.basis(after);
        StrictJson.require(initial.nativeFrame().equals(ExactRef.fromJson(basis.path("before").get("native_frame")))
                &&initial.driverFacts().equals(ExactRef.fromJson(basis.path("before").get("driver_facts")))
                &&ending.nativeFrame().equals(ExactRef.fromJson(basis.path("after").get("native_frame")))
                &&ending.driverFacts().equals(ExactRef.fromJson(basis.path("after").get("driver_facts")))
                &&basis.path("independent_reads").isArray()&&basis.path("independent_reads").isEmpty()
                &&basis.path("supporting_materials").isArray()&&basis.path("supporting_materials").isEmpty(),"legacy first-rendered basis changed original frames or gained a material-query branch");
        ExactRef compatible=ExactRef.fromJson(basis.get("compatible_material"));RawJson retained=bound.loadMaterial(compatible);
        StrictJson.require(retained.bytes().length==compatible.bytes()&&DriverJson.sha256(retained.bytes()).equals(compatible.sha256()),"legacy original compatible result changed");
        // Verification-only proposal DATA. It is never appended, published, or treated as a canonical settlement.
        var command=original.command();
        var fresh=NativeEffectEvidence.reconciliationProvenance(raw);
        org.xar.ck3.control.application.action.ObservationProvenance provenance=fresh.<org.xar.ck3.control.application.action.ObservationProvenance>map(value->value)
                .orElseGet(()->new org.xar.ck3.control.application.action.ObservationProvenance.Push(after.identity().frame().snapshotId(),
                        after.identity().frame().identity().nativeRevision(),after.originalEvidence()));
        fresh.ifPresent(query->RootAdvanceInfrastructureFactory.verifyFreshSnapshotQuery(query,after,bound));
        var snapshot=new org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.BoundSnapshot(
                after.identity(),after.source(),after.sessionId(),after.semantic(),provenance,after.observedAt(),after.originalEvidence());
        var projected=fresh.isPresent()
                ?org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.projectReconciled(command,attempt,guard.origin().requireReconciliation(),snapshot)
                :org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort.project(command.before(),command.source(),command.sessionId(),command.expected(),command.arguments(),snapshot);
        var actual=projected.orElseThrow(()->new IOException("legacy actual after does not prove the original complete event postcondition"));
        var effect=new ActionState.EffectObservation(after.identity(),after.source(),after.sessionId(),command.expected().observerSchema(),actual,
                provenance,after.observedAt(),after.originalEvidence(),List.of(reference));
        var applied=new ActionState.Applied(effect);var ack=original.ack().orElseThrow();
        org.xar.ck3.control.application.action.ActionEffects.validate(command,attempt,ack,applied);
        var proposal=new org.xar.ck3.control.application.action.ActionReceipt(original.version(),original.sequence(),command,original.bodySha256(),
                new ActionState.Settled(attempt,ack,applied));
        var verifier=context.bindings().actualArchivedVerifier(command.operation())
                .orElseThrow(()->new IOException("legacy original event has no actual installed archive semantic verifier"));
        // This installed verifier replays NativeEventEffects, all actual scalar fields, and whole compatible bytes.
        verifier.verifier().verify(context.borrowedSession().head(),proposal,bound);
        var rebuilt=NativeEffectEvidence.load(proposal,bound,RootAdvanceInfrastructureFactory.freshFrameLoader(context.frameLoader()));
        StrictJson.require(rebuilt.compatibleResult().equals(retained),"legacy semantic replay changed the complete original compatible result");
        return Optional.of(new org.xar.ck3.control.application.effects.NativeEffectRegistry.Projected(new ActionPorts.EffectObserved(effect),Optional.of(retained)));
    }
    private void verifyLegacyProducer(ActionCommand command,Complete before,ObjectNode proof)throws IOException {
        ObjectNode captured=read(ExactRef.fromJson(proof.get("original_before")),MAX_BASIS);
        ObjectNode core=(ObjectNode)captured.get("original_registry_decision");
        StrictJson.require(core!=null&&core.isObject()&&core.get("active_event") instanceof ObjectNode,"legacy capture lost its complete original registry decision");
        ObjectNode snapshot=(ObjectNode)DriverJson.toNode(before.semantic());
        ObjectNode originalArguments=(ObjectNode)DriverJson.toNode(command.arguments());
        StrictJson.require(originalArguments.get("active_event") instanceof ObjectNode&&snapshot.get("active_event") instanceof ObjectNode,
                "legacy original normalized full frame lost its native event summary");
        ObjectNode summary=((ObjectNode)originalArguments.get("active_event")).deepCopy();
        summary.remove(List.of("selected_option_number","selected_native_option_index","selected_rendered_index","semantic_optimal","source_registry_known","source_knowledge_status"));
        StrictJson.require(summary.equals(snapshot.get("active_event")),"legacy original normalized native summary differs from its complete producer input");
        var frame=before.identity().frame();
        snapshot.put("snapshot_id",frame.snapshotId()).put("revision",frame.revision()).put("native_revision",frame.identity().nativeRevision())
                .put("date_raw",frame.identity().dateRaw()).put("episode_run_id",frame.episodeRunId());
        ObjectNode diagnostics=snapshot.get("diagnostics") instanceof ObjectNode node?node:snapshot.putObject("diagnostics");
        diagnostics.put("bridge_pid",before.identity().game().pid()).put("connection_generation",before.connectionGeneration());
        var observations=new org.xar.ck3.control.application.planning.PlanningObservation(
                OpportunityJson.object(DriverJson.fromNode(snapshot),"actual legacy original planning snapshot"),List.of(),
                Set.of(command.operation(),new org.xar.ck3.control.application.action.OperationKey(org.xar.ck3.control.application.planning.events.RegisteredEventCore.EVENT_QUERY)),
                Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var request=new org.xar.ck3.control.application.planning.PlanningRequest(command.before(),command.source(),command.sessionId(),command.deadline(),observations);
        var previous=new org.xar.ck3.control.application.planning.OrdinaryPolicy.Draft(core.path("policy").asText(),core.path("phase").asText(),core.path("reason").asText(),
                org.xar.ck3.control.application.planning.OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),org.xar.ck3.control.application.planning.OrdinaryPolicy.Purpose.READ_ONLY,
                Optional.empty(),OpportunityJson.object(DriverJson.fromNode(core),"original captured registry decision"));
        var validator=org.xar.ck3.control.nativebridge.capabilities.events.EventWindowService.validator(
                ignored->org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.Build.CROZIER4);
        ActionCommand produced;
        if("unknown".equals(captured.path("source_knowledge").path("status").asText())) {
            StrictJson.require("before_submission".equals(captured.path("stage").asText())
                    &&captured.path("dispatch_attempted").isBoolean()&&!captured.path("dispatch_attempted").booleanValue(),
                    "historical unknown producer requires its original unsubmitted before capture");
            // A public producer input copy only; never a frame, guard, Session or canonical output substitute.
            ObjectNode recorded=captured.deepCopy();
            recorded.remove(List.of("incident_id","stage","captured_at_utc","dispatch_attempted"));
            produced=org.xar.ck3.control.application.planning.events.EventPolicies.replayLegacyFirstDisplayed(request,previous,
                    prepared.baseConfiguration().trustedInteractions(),validator,command.expected(),
                    OpportunityJson.object(DriverJson.fromNode(recorded),"original pinned historical fallback"));
        } else {
            produced=org.xar.ck3.control.application.planning.events.EventPolicies.replayLegacyFirstDisplayed(request,previous,
                    prepared.baseConfiguration().trustedInteractions(),validator,command.expected());
        }
        StrictJson.require(produced.arguments().equals(command.arguments()),"legacy complete producer arguments differ from canonical original");
        var producedBody=DriverJson.object(org.xar.ck3.control.application.action.ActionCodec.encodeCommand(produced),org.xar.ck3.control.application.action.ActionCodec.MAX_COMMAND_BYTES)
                .with("action_id",new OpportunityJson.Text(command.actionId()));
        StrictJson.require(java.util.Arrays.equals(org.xar.ck3.control.application.driver.PublicDataJson.encodeTyped(producedBody).bytes(),
                org.xar.ck3.control.application.action.ActionCodec.encodeCommand(command)),"legacy complete producer command projection differs from canonical original");
    }
    private static boolean supports(ActionCommand command) {
        boolean event = command.arguments().get("unhandled_event_fallback") instanceof OpportunityJson.Obj;
        boolean interaction = command.arguments().get("unhandled_interaction_fallback") instanceof OpportunityJson.Obj;
        boolean mandatory = command.arguments().get("unknown_mandatory_choice_v1") instanceof OpportunityJson.Obj;
        if (mandatory) return !event && !interaction && command.operation().value().equals("select-mandatory-choice-v1");
        return event != interaction && (event ? command.operation().value().matches("select-event-option-[1-9][0-9]{0,8}")
                : Set.of("reject-pending-character-interaction", "acknowledge-pending-character-interaction").contains(command.operation().value()));
    }
    private void requireCommand(Session same, ActionCommand command) throws IOException {
        context.writer().requireSession(same); context.requireCurrent(command.deadline());
        requireCommandOrigin(same, command);
    }
    private void requireCommandOrigin(Session same, ActionCommand command) throws IOException {
        context.writer().requireSession(same);
        StrictJson.require(context.borrowedSession() == same && command.before().game().equals(context.game().generation())
                && command.before().machineId().equals(context.game().machineId()) && command.source().equals(context.source())
                && command.sessionId().equals(context.game().sessionId()), "Incident command crossed its current physical Game or original writer");
    }
    private void requireCurrent(Session same, Complete frame, Instant deadline) throws IOException {
        context.writer().requireSession(same); context.requireCurrent(deadline);
        StrictJson.require(context.borrowedSession() == same && frame.identity().game().equals(context.game().generation())
                && frame.identity().machineId().equals(context.game().machineId()) && frame.source().equals(context.source())
                && frame.sessionId().equals(context.game().sessionId()), "Incident capture crossed its actual full-frame Game or original writer");
    }
    /** The failed-query callback retains original DATA without renewing a native/action window. */
    private void requireOriginalSession(Session same, Complete frame) throws IOException {
        context.writer().requireSession(same);
        StrictJson.require(context.borrowedSession() == same && frame.identity().game().equals(context.game().generation())
                && frame.identity().machineId().equals(context.game().machineId()) && frame.source().equals(context.source())
                && frame.sessionId().equals(context.game().sessionId()), "Failed query DATA crossed its original full frame/source/writer");
    }
    private IncidentJournalLayout.Scope scope(Binding binding) {
        return IncidentJournalLayout.scope(incidentBase(), scanBase(), binding.before().machineId(), binding.before().game(),
                binding.sessionId(), binding.before().frame().episodeRunId(), binding.source().sourceRef());
    }
    private EpisodeIncidentJournal.Configuration configuration(IncidentJournalLayout.Scope scope) {
        return new EpisodeIncidentJournal.Configuration(scope.incidentRoot(), scope.scanRoot(), context.clock(),
                prepared.baseConfiguration().io(), prepared.baseConfiguration().trustedInteractions(), Optional.of(this::verifyLegacyBinding));
    }
    private void createScope(IncidentJournalLayout.Scope scope) throws IOException {
        for (Path path : List.of(scope.incidentRoot(), scope.scanRoot())) {
            if (Files.notExists(path, LinkOption.NOFOLLOW_LINKS)) { prepared.baseConfiguration().io().require(4096); Files.createDirectory(path); }
            plainDirectory(path);
        }
    }
    private static void requireSame(Complete expected, Complete rebuilt) {
        StrictJson.require(expected.identity().equals(rebuilt.identity()) && expected.source().equals(rebuilt.source()) && expected.sessionId().equals(rebuilt.sessionId())
                && expected.connectionGeneration().equals(rebuilt.connectionGeneration()) && expected.originalEvidence().equals(rebuilt.originalEvidence())
                && java.util.Arrays.equals(DriverJson.encode(expected.semantic()), DriverJson.encode(rebuilt.semantic())), "Actual incident full-frame replay differs");
    }
    private static void unchanged(Session same, String head) throws IOException { StrictJson.require(head.equals(same.head().digest()), "Incident side evidence changed the authoritative ledger head"); }
    private static ObjectNode read(ExactRef ref, int maximum) throws IOException { verify(ref, maximum); JsonNode node = StrictJson.parse(Files.readAllBytes(Path.of(ref.path())), maximum); StrictJson.require(node instanceof ObjectNode, "Original incident object required"); return (ObjectNode)node; }
    private static void verify(ExactRef ref, int maximum) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= maximum, "Bounded original incident metadata required");
        Path path = Path.of(ref.path()); plain(path);
        StrictJson.require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && EpisodeIncidentJournal.measure(path).equals(ref), "Original incident metadata changed");
    }
    private static void plainDirectory(Path path) throws IOException { plain(path); StrictJson.require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS), "Configured plain incident directory is unavailable"); }
    private static void plain(Path path) throws IOException {
        StrictJson.require(path.isAbsolute() && path.equals(path.normalize()), "Canonical absolute incident path required");
        for (Path cursor = path; cursor != null; cursor = cursor.getParent()) if (Files.exists(cursor, LinkOption.NOFOLLOW_LINKS))
            StrictJson.require(!Files.isSymbolicLink(cursor) && cursor.toRealPath().equals(cursor), "Incident path identity is not canonical/plain");
    }
}

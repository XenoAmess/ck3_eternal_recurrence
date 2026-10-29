package org.xar.ck3.control.wave2.finance.giftroute;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.Evaluated;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootProjection;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootSearch;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootStatus;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidatePolicy.RootView;
import org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ObjectEvidence;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingAction;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.ProcessIdentity;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFrameCodec;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Binding;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Snapshot;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashObserver;
import org.xar.ck3.control.wave2.runtime.creationtime.ProcessCreationTime;

/** Existing route orchestration as immutable plan patches. It has no submit/checkpoint/write method. */
public final class GiftRouteCoordinator {
    public static final String ROOT_STEP = "query-campaign-root-context-v1";
    public static final String RECEIPT_STEP = "private-query-faction-gift-receipt-v1";
    public static final String COLD_STEP = "private-query-faction-gift-cold-recovery-v1";
    public static final String SUBMIT_STEP = "private-submit-faction-gift-member-v1";
    public static final BigInteger MINIMUM_RESERVE_RAW = BigInteger.valueOf(10_000_000);
    private GiftRouteCoordinator() { }

    public enum PlanShape { NO_OBJECT, OBJECT }
    public record Context(PlanShape planShape, Read<String> selectedStep, BigInteger plannedRevision,
            Snapshot snapshot, Read<String> episodeRunId, RootSearch rootSearch, Set<String> availableSteps) {
        public Context {
            Objects.requireNonNull(planShape); Objects.requireNonNull(selectedStep); Objects.requireNonNull(plannedRevision);
            Objects.requireNonNull(snapshot); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(rootSearch);
            availableSteps = Set.copyOf(availableSteps);
        }
    }
    public sealed interface Directory permits NoManagedDirectory, ManagedDirectory { }
    public record NoManagedDirectory() implements Directory { }
    public record ManagedDirectory(Path path) implements Directory {
        public ManagedDirectory { Objects.requireNonNull(path); }
    }
    /** Actual raw identity evidence. The shared parser, rather than a caller success flag, decides compatibility. */
    public record ProcessObservation(ProcessIdentity current, ProcessIdentity source) {
        public ProcessObservation {
            Objects.requireNonNull(current); Objects.requireNonNull(source);
        }
        public boolean sameProcess(PendingAction pending) {
            if (!source.equals(pending.sourceProcess())) { throw new IllegalArgumentException("process observation source does not bind pending"); }
            if (invalidBirth(current.creationDate()) || invalidBirth(source.creationDate())) {
                throw new IllegalArgumentException("private faction process birth comparison is unknown");
            }
            if (current.pid().equals(source.pid()) && current.creationDate().equals(source.creationDate())) { return true; }
            ProcessCreationTime.Comparison comparison = ProcessCreationTime.compare(current.creationDate(), source.creationDate());
            if (comparison == ProcessCreationTime.Comparison.UNAVAILABLE) {
                throw new IllegalArgumentException("private faction process birth comparison is unknown");
            }
            return current.pid().equals(source.pid()) && comparison == ProcessCreationTime.Comparison.SAME;
        }
        private static boolean invalidBirth(String value) { return value.isEmpty() || value.equals("None") || value.equals("null"); }
    }
    public record CheckpointRead(String status, Read<String> sha256, Read<BigInteger> dateRaw,
            Read<String> episodeRunId, ObjectEvidence original) {
        public CheckpointRead {
            Objects.requireNonNull(status); Objects.requireNonNull(sha256); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(episodeRunId); Objects.requireNonNull(original);
        }
    }
    /** Qualifies only the original same-date/episode pre-submit reference, not a complete SAVE or recovery. */
    public record Checkpoint(String sha256, BigInteger dateRaw, String episodeRunId, ObjectEvidence original) {
        public Checkpoint {
            GiftPendingModel.digest(sha256); Objects.requireNonNull(dateRaw); Objects.requireNonNull(episodeRunId);
            Objects.requireNonNull(original);
        }
    }
    @FunctionalInterface public interface ExistingCheckpointPort {
        /** Read/deep-copy the original _last_checkpoint while holding its existing driver state lock. */
        Optional<CheckpointRead> readUnderOriginalDriverLock();
    }
    public record CashQuote(GiftWarCashModel.Snapshot snapshot,
            GiftWarCashModel.Read<GiftWarCashModel.Candidate> candidate, GiftWarCashModel.Read<GiftWarCashModel.Root> root) {
        public CashQuote { Objects.requireNonNull(snapshot); Objects.requireNonNull(candidate); Objects.requireNonNull(root); }
    }
    public interface ExistingPorts {
        Directory managedDirectory();
        Ledger readCurrentLedger(ManagedDirectory directory);
        ProcessObservation readProcessObservation(PendingAction pending);
        Optional<GiftPendingFramePolicy.ExistingSnapshotWaitPort> originalBoundedWait();
        Optional<GiftReadTransport.ExistingOwnedReadPort> originalCandidateRead();
        FactionThreatObserver.Request currentThreatInputs(FactionGiftChoice.Selected gift, Context context);
        FactionThreatObserver.ExistingAlertReader originalAlertReader();
        /** Project the already observed snapshot/candidate/root. Do not read optional spending ledgers here. */
        CashQuote currentCashQuote(FactionGiftChoice.Selected gift, RootProjection root, Context context);
        GiftWarCashObserver.CurrentInputsPort originalCashInputs();
        ExistingCheckpointPort originalCheckpointReader();
    }
    public sealed interface StepPatch permits KeepStep, ClearStep, SelectStep { }
    public record KeepStep() implements StepPatch { }
    public record ClearStep() implements StepPatch { }
    public record SelectStep(String step) implements StepPatch {
        public SelectStep { Objects.requireNonNull(step); if (step.isEmpty()) { throw new IllegalArgumentException("step required"); } }
    }
    public sealed interface CandidateTrace permits NoCandidateTrace, KnownEmptyTrace, CandidateReadTrace { }
    public record NoCandidateTrace() implements CandidateTrace { }
    public record KnownEmptyTrace() implements CandidateTrace { }
    public record CandidateReadTrace(GiftReadTransport.Result result) implements CandidateTrace {
        public CandidateReadTrace { Objects.requireNonNull(result); }
    }
    public record Patch(StepPatch step, Optional<String> phase, Optional<String> reason,
            Optional<PendingAction> pending, CandidateTrace candidate,
            Optional<FactionThreatObserver.Response> threat, Optional<GiftWarCashModel.Decision> cash,
            Optional<String> newSpendDeferredReason, Optional<Checkpoint> checkpoint, boolean attachGiftAction) {
        public Patch {
            Objects.requireNonNull(step); Objects.requireNonNull(phase); Objects.requireNonNull(reason);
            Objects.requireNonNull(pending); Objects.requireNonNull(candidate); Objects.requireNonNull(threat);
            Objects.requireNonNull(cash); Objects.requireNonNull(newSpendDeferredReason); Objects.requireNonNull(checkpoint);
            if (attachGiftAction && (checkpoint.isEmpty() || cash.isEmpty() || !cash.get().newGiftSpendingAllowed()
                    || !(threat.orElse(null) instanceof FactionThreatObserver.Observed observed) || !observed.dangerousResponseReady()
                    || !(candidate instanceof CandidateReadTrace trace) || selected(trace.result()).isEmpty()
                    || !(step instanceof SelectStep selectedStep) || !selectedStep.step().equals(SUBMIT_STEP))) {
                throw new IllegalArgumentException("typed submit plan lacks complete observations");
            }
            if (pending.isPresent() && attachGiftAction) { throw new IllegalArgumentException("pending request cannot become a new gift"); }
        }
        public static Patch keep() {
            return new Patch(new KeepStep(), Optional.empty(), Optional.empty(), Optional.empty(), new NoCandidateTrace(),
                    Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), false);
        }
    }
    public sealed interface Result permits PlanPatch, ReadOnlyReplan { }
    public record PlanPatch(Patch patch) implements Result { public PlanPatch { Objects.requireNonNull(patch); } }
    public record ReadOnlyReplan(GiftPendingFramePolicy.Proof proof) implements Result {
        public ReadOnlyReplan { Objects.requireNonNull(proof); }
    }

    public static Result plan(Context context, ExistingPorts ports) {
        Objects.requireNonNull(context); Objects.requireNonNull(ports);
        if (context.planShape() != PlanShape.OBJECT || !equal(context.selectedStep(), "life-advance")) {
            return new PlanPatch(Patch.keep());
        }
        Directory directory = Objects.requireNonNull(ports.managedDirectory());
        if (directory instanceof NoManagedDirectory) {
            return patch(new ClearStep(), null, "private faction route lacks managed state_dir", null,
                    new NoCandidateTrace(), null, null, null, null, false);
        }
        Ledger ledger = Objects.requireNonNull(ports.readCurrentLedger((ManagedDirectory) directory));
        if (ledger.pending().isPresent()) {
            PendingAction pending = ledger.pending().get();
            boolean sameProcess = Objects.requireNonNull(ports.readProcessObservation(pending)).sameProcess(pending);
            if (sameProcess && (!context.snapshot().binding().nativeRevision().known()
                    || context.snapshot().binding().nativeRevision().value().compareTo(pending.baseline().nativeSnapshotRevision()) <= 0)) {
                GiftPendingFramePolicy.ExistingSnapshotWaitPort wait = ports.originalBoundedWait()
                        .orElseThrow(() -> new IllegalStateException("private faction pending frame has no bounded native wait"));
                GiftPendingFramePolicy.Frame frame = GiftPendingFrameCodec.decodeSnapshot(context.snapshot().original().bytes());
                return new ReadOnlyReplan(GiftPendingFramePolicy.awaitFresh(pending, frame, wait));
            }
            return patch(new SelectStep(sameProcess ? RECEIPT_STEP : COLD_STEP), "faction_gift_pending_verification",
                    sameProcess ? "confirm gift on an independent paused frame" : "classify unresolved gift from independent cold-process facts",
                    pending, new NoCandidateTrace(), null, null, null, null, false);
        }
        RootView rootView = FactionCandidatePolicy.latestSameFrameRoot(context.rootSearch());
        if (rootView.status() == RootStatus.SAME_FRAME_ROOT_NOT_OBSERVED) {
            return context.availableSteps().contains(ROOT_STEP)
                    ? patch(new SelectStep(ROOT_STEP), "faction_gift_root_query", "refresh current feudal faction count before any private gift query",
                            null, new NoCandidateTrace(), null, null, null, null, false)
                    : patch(new ClearStep(), "faction_gift_root_query_unavailable", "private faction route lacks its same-frame public root query",
                            null, new NoCandidateTrace(), null, null, null, null, false);
        }
        if (rootView.status() == RootStatus.KNOWN_EMPTY) {
            return patch(new KeepStep(), null, null, null, new KnownEmptyTrace(), null, null, null, null, false);
        }
        if (rootView.status() != RootStatus.TARGETING_PRESENT) { return new PlanPatch(Patch.keep()); }
        Optional<GiftReadTransport.ExistingOwnedReadPort> reader = ports.originalCandidateRead();
        if (reader.isEmpty()) { return new PlanPatch(Patch.keep()); }
        RootProjection root = rootView.root().orElseThrow();
        GiftReadTransport.Result candidate = GiftReadTransport.query(new GiftReadTransport.Request(context.snapshot(), root,
                MINIMUM_RESERVE_RAW, new GiftReadTransport.Timeout(BigDecimal.valueOf(30))), reader.get());
        CandidateTrace trace = new CandidateReadTrace(candidate); Optional<FactionGiftChoice.Selected> selected = selected(candidate);
        if (selected.isEmpty()) { return patch(new KeepStep(), null, null, null, trace, null, null, null, null, false); }
        FactionGiftChoice.Selected gift = selected.get();
        FactionThreatObserver.Request threatInputs = Objects.requireNonNull(ports.currentThreatInputs(gift, context));
        requireThreatBinding(gift, context, threatInputs);
        FactionThreatObserver.Response threat = FactionThreatObserver.observe(threatInputs, ports.originalAlertReader());
        if (!(threat instanceof FactionThreatObserver.Observed observed) || !observed.dangerousResponseReady()) {
            return patch(new KeepStep(), null, null, null, trace, threat, null,
                    "selected_faction_not_observed_stock_dangerous", null, false);
        }
        CashQuote quote = Objects.requireNonNull(ports.currentCashQuote(gift, root, context));
        requireCashBinding(gift, context, quote);
        GiftWarCashModel.Decision cash = GiftWarCashObserver.observe(quote.snapshot(), quote.candidate(), quote.root(), ports.originalCashInputs());
        if (!cash.newGiftSpendingAllowed()) {
            return patch(new KeepStep(), null, null, null, trace, threat, cash, cash.reason().wire(), null, false);
        }
        Optional<Checkpoint> checkpoint = currentCheckpoint(context, ports.originalCheckpointReader());
        if (checkpoint.isEmpty()) {
            return context.availableSteps().contains("save-checkpoint")
                    ? patch(new SelectStep("save-checkpoint"), null, "freeze exact pre-submit faction gift checkpoint",
                            null, trace, threat, cash, null, null, false)
                    : patch(new ClearStep(), null, "faction gift requires an exact pre-submit checkpoint",
                            null, trace, threat, cash, null, null, false);
        }
        return patch(new SelectStep(SUBMIT_STEP), "faction_gift_typed_submit", "submit one native-legal budgeted faction mitigation gift",
                null, trace, threat, cash, null, checkpoint.get(), true);
    }

    public static Optional<Checkpoint> currentCheckpoint(Context context, ExistingCheckpointPort port) {
        return currentCheckpoint(context.snapshot(), context.episodeRunId(), port);
    }
    public static Optional<Checkpoint> currentCheckpoint(Snapshot snapshot, Read<String> episodeRunId, ExistingCheckpointPort port) {
        Objects.requireNonNull(snapshot); Objects.requireNonNull(episodeRunId); Objects.requireNonNull(port);
        Optional<CheckpointRead> read = Objects.requireNonNull(port.readUnderOriginalDriverLock());
        if (read.isEmpty()) { return Optional.empty(); } CheckpointRead checkpoint = read.get();
        if (!checkpoint.status().equals("saved") || !checkpoint.sha256().known()
                || !checkpoint.sha256().value().matches("[0-9a-f]{64}")
                || !same(checkpoint.dateRaw(), snapshot.binding().dateRaw())
                || !same(checkpoint.episodeRunId(), episodeRunId)) { return Optional.empty(); }
        return Optional.of(new Checkpoint(checkpoint.sha256().value(), checkpoint.dateRaw().value(), checkpoint.episodeRunId().value(), checkpoint.original()));
    }
    private static Optional<FactionGiftChoice.Selected> selected(GiftReadTransport.Result result) {
        return result instanceof GiftReadTransport.Candidate candidate && candidate.candidate() instanceof Evaluated evaluated
                && evaluated.choice() instanceof FactionGiftChoice.Selected selected ? Optional.of(selected) : Optional.empty();
    }
    private static void requireThreatBinding(FactionGiftChoice.Selected gift, Context context, FactionThreatObserver.Request request) {
        if (!(request instanceof FactionThreatObserver.SelectedGiftRequest selected)
                || !selected.gift().sourceFactionId().equals(gift.sourceFactionId())
                || !selected.gift().recipientCharacterId().equals(gift.recipientCharacterId())
                || !selected.frame().nativeRevision().equals(gift.snapshotRevision())
                || !BigInteger.valueOf(selected.frame().dateRaw()).equals(gift.dateRaw())
                || !selected.frame().playerCharacterId().equals(gift.playerCharacterId())
                || !selected.expectedRevision().equals(context.plannedRevision())) {
            throw new IllegalArgumentException("stock threat inputs do not bind actual selected candidate and frame");
        }
    }
    private static void requireCashBinding(FactionGiftChoice.Selected gift, Context context, CashQuote request) {
        Binding source = context.snapshot().binding(); GiftWarCashModel.SourceFrame frame = request.snapshot().frame();
        if (!equal(source.nativeRevision(), frame.nativeRevision()) || !equal(source.dateRaw(), frame.dateRaw())
                || !equal(source.actorId(), frame.playedCharacterId()) || !equal(source.snapshotId(), frame.snapshotId())
                || !equal(source.revision(), frame.revision()) || !equal(context.episodeRunId(), frame.episodeRunId())
                || !request.candidate().known() || !request.candidate().value().choice().known()) {
            throw new IllegalArgumentException("cash inputs do not bind actual source frame");
        }
        GiftWarCashModel.Choice choice = request.candidate().value().choice().value();
        if (!choice.giftCostRaw().known() || !choice.giftCostRaw().value().equals(gift.goldCostRaw())
                || !choice.playerCharacterId().known() || !choice.playerCharacterId().value().equals(gift.playerCharacterId())
                || !choice.nativeRevision().known() || !choice.nativeRevision().value().equals(gift.nativeSnapshotRevision())
                || !choice.dateRaw().known() || !choice.dateRaw().value().equals(gift.dateRaw())) {
            throw new IllegalArgumentException("cash quote does not bind actual selected gift");
        }
    }
    private static PlanPatch patch(StepPatch step, String phase, String reason, PendingAction pending,
            CandidateTrace candidate, FactionThreatObserver.Response threat, GiftWarCashModel.Decision cash,
            String deferred, Checkpoint checkpoint, boolean action) {
        return new PlanPatch(new Patch(step, Optional.ofNullable(phase), Optional.ofNullable(reason), Optional.ofNullable(pending),
                candidate, Optional.ofNullable(threat), Optional.ofNullable(cash), Optional.ofNullable(deferred), Optional.ofNullable(checkpoint), action));
    }
    private static <T> boolean equal(Read<T> value, T expected) { return value.known() && value.value().equals(expected); }
    private static <T> boolean same(Read<T> left, Read<T> right) { return left.known() && right.known() && left.value().equals(right.value()); }
}

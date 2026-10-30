package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.planning.ReadonlyPlanningRetry;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Reads and world actions share one writer and endpoint custody. */
public final class PlanningReadCoordinator implements PlanningReadPort {
    /** Original custody is immutable and non-serializable. The same ticket memoizes its first archived adoption. */
    public static final class OriginalRead<T> {
        private final PlanningReadCoordinator owner;
        private final ReadContract<T> contract;
        private final PlanningReadRequest request;
        private final ReadPermit permit;
        private final NativeActionPort.Unknown original;
        private final ExactRef unknownRef;
        private final ExactRef preparedRef;
        private final long headSequence;
        private final String headDigest;
        private final AtomicReference<PlanningReadResult.Known<T>> adopted = new AtomicReference<>();
        private final AtomicBoolean notified = new AtomicBoolean();
        private OriginalRead(PlanningReadCoordinator owner, ReadContract<T> contract, PlanningReadRequest request,
                ReadPermit permit, NativeActionPort.Unknown original, ExactRef unknownRef, ExactRef preparedRef,
                long headSequence, String headDigest) {
            this.owner = owner; this.contract = contract; this.request = request; this.permit = permit;
            this.original = original; this.unknownRef = unknownRef; this.preparedRef = preparedRef;
            this.headSequence = headSequence; this.headDigest = headDigest;
        }
        public PlanningReadRequest request() { return request; }
        public String requestId() { return original.requestId(); }
        public NativeActionPort.Unknown original() { return original; }
    }
    /** Opaque actual failed-attempt custody. Only the coordinator may attach an actual verified failed-read after observation; no submission authority exists here. */
    public static final class FailedReadAttempt {
        private final PlanningReadCoordinator owner;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final ReadPermit permit;
        private final NativeActionPort.DispatchOutcome original;
        private final PlanningReadResult.Unavailable<?> unavailable;
        private final Optional<PlanningReadFailure> observedFailure;
        private final ExactRef originalRef;
        private final ExactRef preparedRef;
        private final long headSequence;
        private final String headDigest;
        private FailedReadAttempt(PlanningReadCoordinator owner, ReadContract<?> contract, PlanningReadRequest request,
                ReadPermit permit, NativeActionPort.DispatchOutcome original, PlanningReadResult.Unavailable<?> unavailable,
                ExactRef originalRef, ExactRef preparedRef, long headSequence, String headDigest,
                Optional<PlanningReadFailure> observedFailure) {
            this.observedFailure=observedFailure;
            this.owner=owner; this.contract=contract; this.request=request; this.permit=permit; this.original=original;
            this.unavailable=unavailable; this.originalRef=originalRef; this.preparedRef=preparedRef;
            this.headSequence=headSequence; this.headDigest=headDigest;
        }
        public PlanningReadGuard before() { return permit.readGuard(); }
        public Optional<PlanningReadFailure> observedFailure() { return observedFailure; }
        public NativeRequest prepared() { return permit.preparedRequest(); }
        public String requestId() { return permit.requestId(); }
        public NativeActionPort.DispatchOutcome original() { return original; }
        public ExactRef originalRef() { return originalRef; }
        public ExactRef preparedRef() { return preparedRef; }
        public long headSequence() { return headSequence; }
        public String headDigest() { return headDigest; }
        /** Live callback custody only. Cold history must verify its actual committed source event and these originals separately. */
        public void requireOriginal(Session same, ReadContract<?> identical, PlanningReadRequest actualRequest,
                PlanningReadResult.Unavailable<?> exactUnavailable, ActionPorts.OutcomeArchive originals) throws IOException {
            Objects.requireNonNull(originals);
            owner.journal.locked(same, locked -> {
                StrictJson.require(contract==identical && request==actualRequest && unavailable==exactUnavailable
                        && observedFailure.equals(exactUnavailable.observedFailure())
                        && owner.catalog.containsIdentity(contract), "failed read lost identical installed contract/request/unavailable callback custody");
                StrictJson.require(permit.consumed() && permit.contract()==contract && original.requestId().equals(permit.requestId()) && permit.origin().equals(request.origin())
                        && permit.sessionId().equals(request.sessionId()), "failed read has no actual consumed original permit");
                StrictJson.require(locked.head().state().sequence()==headSequence && locked.head().digest().equals(headDigest),
                        "failed read callback crossed its original canonical writer head");
                var actual=owner.archive.withSession(locked.writerSession());
                StrictJson.require(originalRef.equals(actual.referenceOf(original)) && original.equals(actual.load(originalRef))
                        && preparedRef.equals(actual.requestReferenceOf(prepared())) && prepared().equals(actual.loadRequest(preparedRef))
                        && originalRef.equals(originals.referenceOf(original)) && original.equals(originals.load(originalRef))
                        && preparedRef.equals(originals.requestReferenceOf(prepared())) && prepared().equals(originals.loadRequest(preparedRef)),
                        "failed read original outcome/prepared artifact changed or is absent");
                StrictJson.require(exactUnavailable.original().filter(value -> value==original).isPresent(),
                        "failed read callback does not retain its exact actual outcome object");
                return null;
            });
        }
    }
    @FunctionalInterface public interface ReadGuardPort {
        PlanningReadGuard verify(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead, PlanningReadRequest request, ReadContract<?> contract);
        /** Actual source lifetime for one native READ and its real after guard; publication remains outside this scope. */
        default <T> T withOriginalReadSource(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead,
                PlanningReadRequest request, ReadContract<?> contract, java.util.function.Supplier<T> work) {
            return Objects.requireNonNull(work).get();
        }

        /** No fallback to a new physical capture/query or to the original expired lease. */
        default PlanningReadGuard verifyOriginalCurrent(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead,
                PlanningReadRequest request, ReadContract<?> contract) {
            throw new IllegalStateException("held original-read observation guard is not installed");
        }
        /** Same frontend guard is accepted only by its actual active source-bound whole-read scope. */
        default void verifyFrontendReadContinuation(org.xar.ck3.control.continuity.writer.WriterContracts.Head actualLockedHead,
                PlanningReadRequest request, ReadContract<?> contract, PlanningReadGuard before, PlanningReadGuard after) {
            throw new IllegalStateException("source-bound frontend read continuation is not installed");
        }
    }
    @FunctionalInterface public interface KnownReadObserver {
        void afterKnown(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session original,ReadContract<?> identicalInstalled,PlanningReadResult.Known<?> actual);
        default void afterUnavailable(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session original,ReadContract<?> identicalInstalled,
                PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual) { }
        default void afterUnavailable(Session original, ReadContract<?> identicalInstalled, PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> actual, Optional<FailedReadAttempt> attempted) {
            afterUnavailable(original, identicalInstalled, request, actual);
        }
    }
    /** Data recording only. It cannot create a guard, contract, request ID, native outcome or read permission. */
    public interface ReadLifecycleObserver {
        void prepared(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ReadContract<?> contract,
                PlanningReadRequest request, String actualRequestId, NativeRequest prepared) throws IOException;
        void received(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ReadContract<?> contract,
                PlanningReadRequest request, String actualRequestId, NativeActionPort.DispatchOutcome original) throws IOException;
        void known(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ReadContract<?> contract,
                PlanningReadResult.Known<?> actual) throws IOException;
        void failed(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ReadContract<?> contract,
                PlanningReadRequest request, Optional<NativeActionPort.DispatchOutcome> original, String reason) throws IOException;
    }
    /** Per-call adapter only; never another global publication observer. */
    private static final class FailureEvidenceLifecycle implements ReadLifecycleObserver {
        private final PlanningReadPort.FailureEvidenceObserver observer;
        private FailureEvidenceLifecycle(PlanningReadPort.FailureEvidenceObserver observer) {
            this.observer = Objects.requireNonNull(observer);
        }
        @Override public void prepared(Session same, ReadContract<?> contract, PlanningReadRequest request, String id, NativeRequest prepared) { }
        @Override public void received(Session same, ReadContract<?> contract, PlanningReadRequest request, String id, NativeActionPort.DispatchOutcome original) { }
        @Override public void known(Session same, ReadContract<?> contract, PlanningReadResult.Known<?> actual) { }
        @Override public void failed(Session same, ReadContract<?> contract, PlanningReadRequest request, Optional<NativeActionPort.DispatchOutcome> original, String reason) { }
    }
    private final RootReadContractCatalog catalog;
    private final ActionJournal journal;
    private final ReadGuardPort guard;
    private final NativePlanningReadPort nativePort;
    private final Clock clock;
    private final ActionPorts.OutcomeArchive archive;
    private final Optional<KnownReadObserver> knownReads;
    public PlanningReadCoordinator(List<ReadContract<?>> registered, ActionJournal journal, ReadGuardPort guard, NativePlanningReadPort nativePort, ActionPorts.OutcomeArchive archive, Clock clock) {
        this(RootReadContractCatalog.staticOnly(registered), journal, guard, nativePort, archive, clock);
    }
    public PlanningReadCoordinator(RootReadContractCatalog catalog, ActionJournal journal, ReadGuardPort guard, NativePlanningReadPort nativePort, ActionPorts.OutcomeArchive archive, Clock clock) {
        this(catalog,journal,guard,nativePort,archive,clock,Optional.empty());
    }
    public PlanningReadCoordinator(RootReadContractCatalog catalog, ActionJournal journal, ReadGuardPort guard, NativePlanningReadPort nativePort, ActionPorts.OutcomeArchive archive, Clock clock,KnownReadObserver actualCacheProducer) {
        this(catalog,journal,guard,nativePort,archive,clock,Optional.of(Objects.requireNonNull(actualCacheProducer)));
    }
    private PlanningReadCoordinator(RootReadContractCatalog catalog, ActionJournal journal, ReadGuardPort guard, NativePlanningReadPort nativePort, ActionPorts.OutcomeArchive archive, Clock clock,Optional<KnownReadObserver> knownReads) {
        this.catalog = Objects.requireNonNull(catalog); this.journal = Objects.requireNonNull(journal); this.guard = Objects.requireNonNull(guard);
        this.nativePort = Objects.requireNonNull(nativePort); this.clock = Objects.requireNonNull(clock);
        this.archive = Objects.requireNonNull(archive);
        this.knownReads=knownReads;
    }
    public RootReadContractCatalog catalog() { return catalog; }
    @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,
            PlanningReadRequest request, PlanningReadPort.FailureEvidenceObserver observer) {
        return read(contract, request, new FailureEvidenceLifecycle(observer));
    }
    @Override public <T> PlanningReadResult<T> readWithFailureEvidence(Session borrowed, ReadContract<T> contract,
            PlanningReadRequest request, PlanningReadPort.FailureEvidenceObserver observer) {
        return read(borrowed, contract, request, new FailureEvidenceLifecycle(observer));
    }

    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        return journal.locked(locked -> readLocked(locked, contract, request, Optional.empty()));
    }
    @Override public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        return journal.locked(borrowed, locked -> readLocked(locked, contract, request, Optional.empty()));
    }
    public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request, ReadLifecycleObserver observer) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        Objects.requireNonNull(observer);
        return journal.locked(locked -> readLocked(locked, contract, request, Optional.of(observer)));
    }
    public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed,
            ReadContract<T> contract, PlanningReadRequest request, ReadLifecycleObserver observer) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        Objects.requireNonNull(observer);
        return journal.locked(borrowed, locked -> readLocked(locked, contract, request, Optional.of(observer)));
    }
    private <T> PlanningReadResult<T> readLocked(ActionJournal.LockedJournal locked, ReadContract<T> contract, PlanningReadRequest request,
            Optional<ReadLifecycleObserver> observer) {
        return readAttemptLocked(locked, contract, request, observer, false).result();
    }
    @Override public <T> PlanningReadAttempt<T> readOriginal(ReadContract<T> contract, PlanningReadRequest request) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        return journal.locked(locked -> readAttemptLocked(locked, contract, request, Optional.empty(), true));
    }
    @Override public <T> PlanningReadAttempt<T> readOriginal(Session borrowed, ReadContract<T> contract, PlanningReadRequest request) {
        StrictJson.require(catalog.containsIdentity(contract), "query contract is not installed or minted by the one composition root");
        return journal.locked(borrowed, locked -> readAttemptLocked(locked, contract, request, Optional.empty(), true));
    }
    private <T> PlanningReadAttempt<T> readAttemptLocked(ActionJournal.LockedJournal locked, ReadContract<T> contract,
            PlanningReadRequest request, Optional<ReadLifecycleObserver> observer, boolean retainOriginal) {
        try { return runReadAttemptLocked(locked, contract, request, observer, retainOriginal); }
        catch (VerifiedReadRetry verified) { throw verified.original; }
        catch (VerifiedRootSourceFault verified) { throw verified.original; }
    }
    /** Only the actual failed-query callback can mint this internal exception boundary. */
    private static final class VerifiedReadRetry extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final RuntimeException original;
        private VerifiedReadRetry(ReadonlyPlanningRetry.QualifiedRejection original) {
            super(original); this.original = original;
        }
        private VerifiedReadRetry(ReadonlyPlanningRetry.QualifiedPreflightRejection original) {
            super(original); this.original = original;
        }
    }
    /** Only the actual first guard may retain an authenticated ROOT source fault without granting retry. */
    private static final class VerifiedRootSourceFault extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final org.xar.ck3.control.application.effects.RootPlanningReadGuard.RootRevisionPreconditionFailure original;
        private VerifiedRootSourceFault(ReadonlyPlanningRetry.QualifiedRootRevisionFailure actual) {
            super(actual);original=actual.originalFailure();
        }
    }
    private <T> PlanningReadAttempt<T> runReadAttemptLocked(ActionJournal.LockedJournal locked, ReadContract<T> contract,
            PlanningReadRequest request, Optional<ReadLifecycleObserver> observer, boolean retainOriginal) {
            NativeActionPort.DispatchOutcome original = null;
            Optional<PlanningReadGuard> observedAfter = Optional.empty();
            Optional<OriginalRead<T>> ticket = Optional.empty();
            ReadPermit attempted = null;
            try {
                PlanningReadGuard before;
                try { before = guard.verify(locked.head(), request, contract); }
                catch (ReadonlyPlanningRetry.QualifiedRootRevisionFailure actual) {
                    StrictJson.require(attempted==null && original==null,"original ROOT fault is not before the actual READ");
                    actual.requireGuardCallback(locked.writerSession(),contract,request);
                    throw new VerifiedRootSourceFault(actual);
                }
                catch (ReadonlyPlanningRetry.QualifiedPreflightRejection retry) {
                    // The source proof was minted inside its live guard lease. Only this first
                    // guard boundary can confirm that no prepare or native READ has occurred.
                    StrictJson.require(attempted == null && original == null,
                            "readonly preflight retry is not at the original before-read guard");
                    retry.requireGuardCallback(locked.writerSession(), contract, request);
                    throw new VerifiedReadRetry(retry);
                }
                verify(request, contract, before);
                String requestId = RequestIds.nextRead(); NativeRequest prepared = contract.prepare(request, requestId);
                if (observer.isPresent()) observer.orElseThrow().prepared(locked.writerSession(), contract, request, requestId, prepared);
                ReadPermit permit = new ReadPermit(contract, request, prepared, before, requestId); attempted = permit;
                var returned = new AtomicReference<NativeActionPort.DispatchOutcome>();
                var sampledAfter = new AtomicReference<PlanningReadGuard>();
                var retainedTicket = new AtomicReference<OriginalRead<T>>();
                try {
                    guard.withOriginalReadSource(locked.head(), request, contract, () -> {
                        NativeActionPort.DispatchOutcome received = readFromSource(permit, prepared, request.deadline());
                        returned.set(received);
                        if (retainOriginal && received instanceof NativeActionPort.Unknown unknown
                                && unknown.requestId().equals(requestId) && unknown.originalRequestPacket().length > 0
                                && contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP && permit.consumed()) {
                            var head = locked.head();
                            retainedTicket.set(new OriginalRead<>(this, contract, request, permit, unknown,
                                    archive.preserve(unknown), archive.preserveRequest(prepared), head.state().sequence(), head.digest()));
                        }
                        if (observer.isPresent()) {
                            try { observer.orElseThrow().received(locked.writerSession(), contract, request, requestId, received); }
                            catch (IOException failure) { throw new UncheckedIOException(failure); }
                        }
                        boolean successful = received instanceof NativeActionPort.AckReceived ack
                                && ack.nativeOk() && ack.requestId().equals(requestId);
                        boolean eligibleFailure = permit.consumed() && received.requestId().equals(requestId)
                                && request.origin() instanceof CommandOrigin.Gameplay && PlanningReadFailure.returnedRead(received);
                        if (!successful && !eligibleFailure) return null;
                        PlanningReadGuard after = successful
                                ? guard.verify(locked.head(), request, contract)
                                : guard.verifyOriginalCurrent(locked.head(), request, contract);
                        verify(request, contract, after);
                        StrictJson.require(before.binding().connectionGeneration().equals(after.binding().connectionGeneration()), "private query crossed the held connection generation");
                        if (before.binding().origin() instanceof CommandOrigin.Gameplay)
                            StrictJson.require(before.binding().origin().equals(after.binding().origin())
                                    && before.originalBindingSha256().equals(after.originalBindingSha256()), "private query crossed the original living paused frame/modal binding");
                        else if(before.binding().origin() instanceof CommandOrigin.LifecycleTerminal previous) {
                            StrictJson.require(after.binding().origin() instanceof CommandOrigin.LifecycleTerminal current
                                    &&previous.identity().sameGuardFrame(current.identity())
                                    &&before.originalBindingSha256().equals(after.originalBindingSha256())
                                    &&before.binding().authorityId().equals(after.binding().authorityId()),"terminal query crossed its qualified original lifecycle frame/source authority");
                        } else if(before.binding().origin() instanceof CommandOrigin.Reconciliation previous) {
                            StrictJson.require(after.binding().origin() instanceof CommandOrigin.Reconciliation current
                                    &&previous.identity().sameGuardFrame(current.identity())
                                    &&before.originalBindingSha256().equals(after.originalBindingSha256())
                                    &&before.binding().authorityId().equals(after.binding().authorityId()),
                                    "read-only reconciliation query crossed its original pending/native/source authority");
                        } else if (before.binding().origin() instanceof CommandOrigin.PhysicalStatusOnly previous) {
                            StrictJson.require(after.binding().origin() instanceof CommandOrigin.PhysicalStatusOnly current
                                    && previous.identity().sameGuardFrame(current.identity())
                                    && before.originalBindingSha256().equals(after.originalBindingSha256())
                                    && before.binding().authorityId().equals(after.binding().authorityId()),
                                    "physical status crossed its actual held transport/snapshot/HELLO/source epoch");
                        } else {
                            FrontendIdentity previous = before.binding().origin().requireFrontend(), current = after.binding().origin().requireFrontend();
                            StrictJson.require(previous.sameGuardFrame(current), "frontend query crossed its held origin frame");
                            boolean freshLater = current.frame().querySequence().compareTo(previous.frame().querySequence()) > 0
                                    && !current.nativeEvidence().equals(previous.nativeEvidence());
                            if (!freshLater) {
                                StrictJson.require(current.frame().querySequence().equals(previous.frame().querySequence())
                                        && current.nativeEvidence().equals(previous.nativeEvidence())
                                        && before.binding().equals(after.binding())
                                        && before.originalBindingSha256().equals(after.originalBindingSha256()),
                                        "frontend read is neither a fresh later frame nor the exact issued source-bound guard");
                                guard.verifyFrontendReadContinuation(locked.head(), request, contract, before, after);
                            }
                        }

                        sampledAfter.set(after);
                        return null;
                    });
                } catch (NativeReadInterrupted interrupted) { throw interrupted.original; }
                catch (UncheckedIOException failure) { throw failure.getCause(); }
                finally { original = returned.get(); ticket = Optional.ofNullable(retainedTicket.get()); }
                PlanningReadGuard after = sampledAfter.get();
                if (after != null && permit.consumed() && original.requestId().equals(requestId)
                        && request.origin() instanceof CommandOrigin.Gameplay && PlanningReadFailure.returnedRead(original))
                    observedAfter = Optional.of(after);
                if (!(original instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || !ack.requestId().equals(requestId))
                    return new PlanningReadAttempt<>(unavailable(locked,contract,request,"native query returned unavailable or an unbound ACK",
                            Optional.ofNullable(original),observer,attempted,Optional.empty(),observedAfter), ticket);
                StrictJson.require(after != null, "actual successful READ after guard is absent");
                PlanningReadReceipt receipt = contract.captureRetainedMaterial(
                        new PlanningReadReceipt(request, contract.contractId(), requestId, before, after, ack));
                T decoded;
                try { decoded = contract.decode(receipt); }
                catch (RuntimeException failure) {
                    if (!(failure instanceof OriginalReadDecodeFailure typed)) throw failure;
                    // Only the actual live decoder can supply this typed cause. Preparation,
                    // guard, archive and publication failures remain ordinary Unavailable.
                    typed.requireOriginal(contract, request, receipt);
                    String message = failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
                    return new PlanningReadAttempt<>(unavailable(locked, contract, request,
                            message.length() <= 2048 ? message : message.substring(0, 2048), Optional.of(original),
                            observer, attempted, Optional.of(typed), observedAfter), ticket);
                }
                PlanningReadResult.Known<T> known=new PlanningReadResult.Known<>(decoded, receipt, archive.preserveRead(receipt));
                attempted = null; // A produced Known whose publication callback fails is not a failed native-query origin.
                knownReads.ifPresent(cache -> cache.afterKnown(locked.writerSession(),contract,known));
                if (observer.isPresent()) observer.orElseThrow().known(locked.writerSession(), contract, known);
                return new PlanningReadAttempt<>(known, Optional.empty());
            } catch (IOException failure) {
                String message = "read lifecycle diagnostic unavailable:" + String.valueOf(failure.getMessage());
                return new PlanningReadAttempt<>(unavailable(locked,contract,request,message.length() <= 2048 ? message : message.substring(0, 2048),Optional.ofNullable(original),observer,attempted,Optional.empty(),observedAfter), ticket);
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); return new PlanningReadAttempt<>(unavailable(locked,contract,request,"native query interrupted",Optional.ofNullable(original),observer,attempted,Optional.empty(),observedAfter), ticket);
            } catch (RuntimeException failure) {
                if (failure instanceof VerifiedReadRetry verified) throw verified;
                if (failure instanceof VerifiedRootSourceFault verified) throw verified;
                String message = failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
                return new PlanningReadAttempt<>(unavailable(locked,contract,request,message.length() <= 2048 ? message : message.substring(0, 2048),Optional.ofNullable(original),observer,attempted,Optional.empty(),observedAfter), ticket);
            }
    }
    private static final class NativeReadInterrupted extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final InterruptedException original;
        private NativeReadInterrupted(InterruptedException original) { super(original); this.original = original; }
    }
    private NativeActionPort.DispatchOutcome readFromSource(ReadPermit permit, NativeRequest prepared, java.time.Instant deadline) {
        try { return Objects.requireNonNull(nativePort.read(permit, prepared, deadline)); }
        catch (InterruptedException interrupted) { throw new NativeReadInterrupted(interrupted); }
    }
    private <T> PlanningReadResult.Unavailable<T> unavailable(ActionJournal.LockedJournal locked,ReadContract<T> contract,
            PlanningReadRequest request,String reason,Optional<NativeActionPort.DispatchOutcome> original,Optional<ReadLifecycleObserver> observer,ReadPermit attempted) {
        return unavailable(locked, contract, request, reason, original, observer, attempted, Optional.empty(), Optional.empty());
    }
    private <T> PlanningReadResult.Unavailable<T> unavailable(ActionJournal.LockedJournal locked,ReadContract<T> contract,
            PlanningReadRequest request,String reason,Optional<NativeActionPort.DispatchOutcome> original,Optional<ReadLifecycleObserver> observer,
            ReadPermit attempted,Optional<OriginalReadDecodeFailure> decodeFailure, Optional<PlanningReadGuard> observedAfter) {
        Optional<PlanningReadFailure> afterFailure=Optional.empty();
        ExactRef outcomeRef=null, preparedRef=null; long sequence=0; String digest=null;
        String archiveDiagnostic=null; boolean archived=false;
        if (attempted!=null && attempted.consumed() && original.isPresent()) {
            try {
                var head=locked.head(); var outcome=original.orElseThrow();
                StrictJson.require(outcome.requestId().equals(attempted.requestId()), "failed-query outcome belongs to another request");
                if (outcome instanceof NativeActionPort.AckReceived received)
                    received.custody().orElseThrow().verify(received,attempted.guard());
                outcomeRef=archive.preserve(outcome); preparedRef=archive.preserveRequest(attempted.preparedRequest());
                sequence=head.state().sequence(); digest=head.digest();
                if (observedAfter.isPresent())
                    afterFailure=Optional.of(new PlanningReadFailure(request,contract.contractId(),attempted.requestId(),
                            attempted.readGuard(),observedAfter.orElseThrow(),attempted.preparedRequest(),outcome,
                            outcomeRef,preparedRef,sequence,digest));
                archived=true;
            } catch (RuntimeException missing) {
                archiveDiagnostic=reason+"; original failed-attempt archive unavailable: "+missing.getClass().getSimpleName();
                afterFailure=Optional.empty();
            }
        }
        var actual=new PlanningReadResult.Unavailable<T>(reason,original,decodeFailure,afterFailure);
        PlanningReadResult.Unavailable<T> result=actual;
        Optional<FailedReadAttempt> failureOrigin=archived
                ? Optional.of(new FailedReadAttempt(this,contract,request,attempted,original.orElseThrow(),actual,
                        outcomeRef,preparedRef,sequence,digest,afterFailure)) : Optional.empty();
        if (archiveDiagnostic!=null)
            result=new PlanningReadResult.Unavailable<>(archiveDiagnostic.length()<=2048?archiveDiagnostic:archiveDiagnostic.substring(0,2048),
                    original,decodeFailure,afterFailure);
        final Optional<FailedReadAttempt> origin=failureOrigin;
        if (observer.orElse(null) instanceof FailureEvidenceLifecycle evidence) {
            try {
                evidence.observer.failed(locked.writerSession(), contract, request, actual, origin,
                        archive.withSession(locked.writerSession()));
            } catch (IOException | RuntimeException failure) {
                String message = reason + "; original failed-read evidence observer unavailable:"
                        + failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
                result = new PlanningReadResult.Unavailable<>(message.length() <= 2048 ? message : message.substring(0, 2048),
                        original, decodeFailure, afterFailure);
            }
        }
        try { knownReads.ifPresent(cache -> cache.afterUnavailable(locked.writerSession(),contract,request,actual,origin)); }
        catch(RuntimeException failure) {
            if (failure instanceof ReadonlyPlanningRetry.QualifiedRejection retry) {
                boolean verified = false;
                try {
                    retry.requireOriginalCallback(locked.writerSession(), contract, request, actual, origin, archive);
                    verified = true;
                } catch (IOException | RuntimeException rejected) {
                    if (rejected != failure) failure.addSuppressed(rejected);
                }
                if (verified) throw new VerifiedReadRetry(retry);
            }
            String message=reason+"; actual failed-query publication unavailable: "+failure.getClass().getSimpleName()+":"+String.valueOf(failure.getMessage());
            result = new PlanningReadResult.Unavailable<>(message.length()<=2048?message:message.substring(0,2048),original,decodeFailure,afterFailure);
        }
        if (observer.isPresent()) {
            try { observer.orElseThrow().failed(locked.writerSession(), contract, request, result.original(), result.reason()); }
            catch (IOException | RuntimeException failure) {
                String message = result.reason() + "; read lifecycle failure diagnostic unavailable:" + failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
                return new PlanningReadResult.Unavailable<>(message.length()<=2048?message:message.substring(0,2048),original,decodeFailure,afterFailure);
            }
        }
        return result;
    }
    @Override public Optional<NativeActionPort.AckReceived> pollOriginal(OriginalRead<?> original) throws IOException {
        return lockedIo(null, locked -> pollLocked(locked, original));
    }
    @Override public Optional<NativeActionPort.AckReceived> pollOriginal(Session borrowed, OriginalRead<?> original) throws IOException {
        return lockedIo(Objects.requireNonNull(borrowed), locked -> pollLocked(locked, original));
    }
    private Optional<NativeActionPort.AckReceived> pollLocked(ActionJournal.LockedJournal locked, OriginalRead<?> original) {
        try {
            requireOriginal(locked, original);
            if (!(nativePort instanceof NativeActionPort actual)) throw new IOException("actual original outcome polling is unavailable on this read provider");
            // The sole transport constructs the retained exact-ID ACK before popping it. The domain
            // retains this returned ACK before any fallible decode/adoption; no post-pop I/O here.
            return actual.pollOriginalOutcome(original.requestId());
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Override public <T> PlanningReadResult<T> adoptOriginal(OriginalRead<T> original, NativeActionPort.AckReceived actual,
            PlanningReadRequest currentRequest, Obj currentSemantic) throws IOException {
        return lockedIo(null, locked -> adoptLocked(locked, original, actual, currentRequest, currentSemantic));
    }
    @Override public <T> PlanningReadResult<T> adoptOriginal(Session borrowed, OriginalRead<T> original,
            NativeActionPort.AckReceived actual, PlanningReadRequest currentRequest, Obj currentSemantic) throws IOException {
        return lockedIo(Objects.requireNonNull(borrowed), locked -> adoptLocked(locked, original, actual, currentRequest, currentSemantic));
    }
    private <T> PlanningReadResult<T> adoptLocked(ActionJournal.LockedJournal locked, OriginalRead<T> original,
            NativeActionPort.AckReceived actual, PlanningReadRequest currentRequest, Obj currentSemantic) {
        Objects.requireNonNull(original); Objects.requireNonNull(actual); Objects.requireNonNull(currentRequest); Objects.requireNonNull(currentSemantic);
        try {
            requireOriginal(locked, original);
            StrictJson.require(actual.nativeOk() && actual.requestId().equals(original.requestId()), "late adoption requires the successful original ACK");
            StrictJson.require(currentRequest.origin().equals(original.request.origin())
                    && currentRequest.source().equals(original.request.source()) && currentRequest.sessionId().equals(original.request.sessionId())
                    && currentRequest.operation().equals(original.request.operation()) && currentRequest.arguments().equals(original.request.arguments()),
                    "late adoption changed the original exact gameplay frame/source/session/query arguments");
            PlanningReadGuard after = guard.verifyOriginalCurrent(locked.head(), currentRequest, original.contract); verify(currentRequest, original.contract, after);
            PlanningReadResult.Known<T> retained = original.adopted.get();
            if (retained != null) {
                StrictJson.require(retained.receipt().original().equals(actual), "retry cannot replace the first actual adopted ACK");
                StrictJson.require(archive.loadRead(retained.originalReceipt()).equals(retained.receipt()), "first archived read adoption changed");
                requireSameOriginalFrame(original.permit.readGuard(), after);
                original.contract.requireCanonicalReuse(retained.receipt(), retained.value(), currentRequest, currentSemantic);
                notifyAdopted(locked, original, retained); return retained;
            }
            PlanningReadAdoption adoption = new PlanningReadAdoption(currentRequest, currentSemantic, original.original,
                    original.permit.preparedRequest(), original.headSequence, original.headDigest);
            PlanningReadReceipt receipt = new PlanningReadReceipt(original.request, original.contract.contractId(), original.requestId(),
                    original.permit.readGuard(), after, actual, Optional.of(adoption));
            adoption.requireReceipt(receipt);
            var chronology = actual.custody().orElseThrow(); chronology.verify(receipt);
            StrictJson.require(!chronology.responseReceived().observedAt().isAfter(clock.instant()), "late outcome cannot claim a future actual receive time");
            T value = original.contract.decode(receipt); // Includes the sole source-owned canonical reuse predicate.
            PlanningReadResult.Known<T> known = new PlanningReadResult.Known<>(value, receipt, archive.preserveRead(receipt));
            StrictJson.require(original.adopted.compareAndSet(null, known), "original read already has its one archived adoption");
            notifyAdopted(locked, original, known);
            return known;
        } catch (IOException | RuntimeException failure) {
            String message = "original read adoption unavailable:" + failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage());
            // The sole domain pending retains both ticket and actual ACK. Do not repoll, replace its
            // original request/deadline, invoke unavailable publication, or submit a fresh query here.
            return new PlanningReadResult.Unavailable<>(message.length() <= 2048 ? message : message.substring(0, 2048), Optional.of(actual));
        }
    }
    private <T> void notifyAdopted(ActionJournal.LockedJournal locked, OriginalRead<T> original, PlanningReadResult.Known<T> known) {
        if (original.notified.get()) return;
        knownReads.ifPresent(cache -> cache.afterKnown(locked.writerSession(), original.contract, known));
        original.notified.set(true);
    }
    private static void requireSameOriginalFrame(PlanningReadGuard before, PlanningReadGuard after) {
        StrictJson.require(after.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && after.paused() && after.mapReady() && after.playerAlive()
                && before.binding().origin().equals(after.binding().origin())
                && before.binding().source().equals(after.binding().source())
                && before.binding().sessionId().equals(after.binding().sessionId())
                && before.binding().connectionGeneration().equals(after.binding().connectionGeneration())
                && before.binding().authorityId().equals(after.binding().authorityId())
                && before.originalBindingSha256().equals(after.originalBindingSha256()),
                "late retry crossed its original exact living paused map/source/session/connection/authority");
    }
    private void requireOriginal(ActionJournal.LockedJournal locked, OriginalRead<?> original) throws IOException {
        Objects.requireNonNull(original);
        StrictJson.require(original.owner == this && catalog.containsIdentity(original.contract), "original read ticket belongs to another installed coordinator/catalog");
        StrictJson.require(original.permit.consumed() && original.permit.contract() == original.contract
                && original.permit.requestId().equals(original.requestId()) && original.permit.origin().equals(original.request.origin()),
                "original read ticket lost its one actual consumed permit");
        var same = locked.writerSession(); var head = locked.head();
        if (head.state().sequence() != original.headSequence || !head.digest().equals(original.headDigest))
            same.requireHistoricalState(original.headSequence, original.headDigest);
        StrictJson.require(original.original.equals(archive.load(original.unknownRef))
                && original.permit.preparedRequest().equals(archive.loadRequest(original.preparedRef)), "original read custody artifacts changed");
    }
    private <T> T lockedIo(Session borrowed, Function<ActionJournal.LockedJournal, T> work) throws IOException {
        try { return borrowed == null ? journal.locked(work) : journal.locked(borrowed, work); }
        catch (UncheckedIOException failure) { throw failure.getCause(); }
    }
    private void verify(PlanningReadRequest request, ReadContract<?> contract, PlanningReadGuard evidence) {
        GuardEvidence binding = evidence.binding(); var now = clock.instant();
        StrictJson.require(evidence.guardMode() == contract.guardMode(), "query readiness differs from registered origin mode");
        boolean statusOnly = request.origin() instanceof CommandOrigin.PhysicalStatusOnly;
        StrictJson.require(statusOnly == (contract.guardMode() == ReadContract.GuardMode.STATUS_ONLY),
                "physical status origin and its finite registered read mode must agree");
        if (statusOnly) {
            PhysicalStatusIdentity.requireProfile(contract);
            StrictJson.require(request.operation().equals(contract.operation()) && request.arguments().members().isEmpty(),
                    "physical status is only the exact installed original Sentinel query, never a generic planning read");
        }
        if (contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)
            StrictJson.require(evidence.paused() && evidence.mapReady() && evidence.playerAlive(), "read requires a living paused map player");
        StrictJson.require(request.origin().acceptsGuard(binding.origin()) && request.source().equals(binding.source())
                && request.sessionId().equals(binding.sessionId()) && request.operation().equals(binding.operation()), "read native Game/frame/source/session identity changed");
        StrictJson.require(now.isBefore(request.deadline()) && !now.isBefore(binding.observedAt()) && !now.isAfter(binding.validUntil()), "read native guard is stale");
    }
}

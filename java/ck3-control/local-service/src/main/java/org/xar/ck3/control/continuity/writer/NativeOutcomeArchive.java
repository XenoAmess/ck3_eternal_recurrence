package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionEffects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionRecord;
import org.xar.ck3.control.application.action.ActionRecordCodec;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.ActionTerminalObservation;
import org.xar.ck3.control.application.action.CommandOriginCodec;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.LifecycleIdentity;
import org.xar.ck3.control.application.action.LifecycleOriginFactory;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeFailureCauseCodec;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.NativeStepDiscriminator;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.application.action.FixtureBusinessObservation;
import org.xar.ck3.control.application.action.FixtureProofCodec;
import org.xar.ck3.control.application.action.FixtureStartObservation;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadFailure;
import org.xar.ck3.control.application.action.PlanningReadFailureCodec;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadAdoption;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PhysicalActionCodec;
import org.xar.ck3.control.application.action.PhysicalActionState;
import org.xar.ck3.control.application.action.PhysicalOutcome;
import org.xar.ck3.control.application.action.PreparedAction;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.ReconciliationIdentity;
import org.xar.ck3.control.application.action.ReconciliationPendingBinding;
import org.xar.ck3.control.application.action.RootExecutableBindings;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletion;
import org.xar.ck3.control.application.planning.sway.SwaySchedulerCompletionCodec;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.OriginalOutcome;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;
import org.xar.ck3.control.contracts.presentation.PresentationObservation;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.ArtifactRole;
import org.xar.ck3.control.contracts.presentation.PresentationOriginals.OriginalArtifact;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.service.root.RootOperatorGuardEvidence;
import org.xar.ck3.control.service.root.RootUnresolvedHistoryQualification;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.Pin;

/** One physical immutable archive, installed in the composition host, never a second ledger writer.
 * Native packets and JSON tokens are separate original-byte artifacts. Only small typed metadata is canonicalized.
 */
public final class NativeOutcomeArchive implements ActionPorts.OutcomeArchive {
    private static final int META_LIMIT = StrictJson.EXPLICIT_MAX_BYTES;
    private static final String DISPATCH_SCHEMA = "xar.native-dispatch-archive/v1";
    private static final String DISPATCH_WITH_OUTBOUND_SCHEMA = "xar.native-dispatch-archive/v2";
    private static final String DISPATCH_WITH_CUSTODY_SCHEMA = "xar.native-dispatch-archive/v3";
    private static final String DISPATCH_WITH_FAILURE_SCHEMA = "xar.native-dispatch-archive/v4";
    private static final String REQUEST_SCHEMA = "xar.native-request-archive/v1";
    private static final String REQUEST_WITH_PREPARATION_SCHEMA = "xar.native-request-archive/v2";
    private static final String READ_SCHEMA = "xar.planning-read-archive/v1";
    private static final String READ_WITH_ADOPTION_SCHEMA = "xar.planning-read-archive/v2";
    private static final String PHYSICAL_STATUS_READ_SCHEMA = "xar.planning-read-archive/v3";
    private static final String RETAINED_MATERIAL_READ_SCHEMA = "xar.planning-read-archive/v4";
    private final ImmutableArtifactStore artifacts;
    private final ContinuityWriter sameWriter;
    private final NativeOutcomeArchive owner;
    private final ContinuityStorePort.Session borrowed;
    private enum Publication { DURABLE, PLANNING_OBSERVATION }
    private final Publication publication;
    private final ThreadLocal<ContinuityStorePort.Session> current;
    private static final int MAX_READ_ORIGINALS = 256;
    private static final class ReadOriginalCapture {
        private final ContinuityStorePort.Session session;
        private final Set<Pin> installedSources;
        private final Map<ExactRef, Pin> pins = new LinkedHashMap<>();
        private final Set<ExactRef> verifiedSourceReferences = new LinkedHashSet<>();
        private ReadOriginalCapture(ContinuityStorePort.Session session, List<Pin> installedSources) {
            this.session = session; this.installedSources = Set.copyOf(installedSources);
        }
    }
    private final ThreadLocal<ReadOriginalCapture> readOriginalCapture;
    /** Finite collection budget only. Callers may omit an optional whole group for this
     * exception; missing, changed or invalid originals must continue to fail separately. */
    public static final class ReadOriginalsLimitExceeded extends IOException {
        private static final long serialVersionUID = 1L;
        private ReadOriginalsLimitExceeded() { super("bounded complete READ original collection exceeds 256 references"); }
    }
    private static final int MAX_HISTORY_EPOCHS = 64;
    private record HistoryEpoch(String machineId, GameGeneration game, String episodeRunId, long episodeEpoch) { }
    private record HistoryRegistration(HistoryEpoch epoch, ReconciliationPendingBinding binding) { }
    /** Explicit Root wiring only. Retain small keys and actual bindings for old cold reads;
     * never retain an EpochOwner ticket, borrowed Session or complete writer Head here. */
    private static final class HistoryBindings {
        private final Map<HistoryEpoch, HistoryRegistration> epochs = new LinkedHashMap<>();
        private final AtomicReference<HistoryRegistration> current = new AtomicReference<>();
    }
    private final HistoryBindings historyBindings;
    private record PhysicalStatusOriginals(RootExecutableBindings bindings, OriginalEvidencePort originals) { }
    private final Map<GameGeneration, PhysicalStatusOriginals> physicalStatusOriginals;
    @FunctionalInterface private interface IoWork<T> { T run() throws IOException; }

    public NativeOutcomeArchive(ImmutableArtifactStore artifacts, ContinuityWriter sameWriter) throws IOException {
        this.artifacts = Objects.requireNonNull(artifacts); this.sameWriter = Objects.requireNonNull(sameWriter);
        owner = this; borrowed = null; publication=Publication.DURABLE; current = new ThreadLocal<>(); historyBindings = new HistoryBindings();
        readOriginalCapture = new ThreadLocal<>();
        physicalStatusOriginals = new LinkedHashMap<>();
        if (!artifacts.originalWriterLock().equals(sameWriter.originalLockPath())
                || sameWriter.artifactStore().orElseThrow(() -> new IOException("writer has no immutable artifact store")) != artifacts)
            throw new IOException("archive must use this exact writer's installed immutable store");
        artifacts.identity();
    }
    private NativeOutcomeArchive(NativeOutcomeArchive original, ContinuityStorePort.Session borrowed) {
        this(original,borrowed,original.publication);
    }
    private NativeOutcomeArchive(NativeOutcomeArchive original, ContinuityStorePort.Session borrowed,Publication publication) {
        artifacts = original.artifacts; sameWriter = original.sameWriter; owner = original.owner;
        current = owner.current; historyBindings = owner.historyBindings; this.borrowed = Objects.requireNonNull(borrowed);
        this.publication=Objects.requireNonNull(publication);
        readOriginalCapture = owner.readOriginalCapture;
        physicalStatusOriginals = owner.physicalStatusOriginals;
    }
    public ImmutableArtifactStore artifactStore() { return artifacts; }
    public ContinuityWriter writer() { return sameWriter; }

    /** Root installs its identical per-Game catalog router and original-byte port under this writer.
     * This wiring creates no physical scope, authority, observation or read qualification. */
    public void bindPhysicalStatusOriginals(ContinuityStorePort.Session same, GameGeneration actualGame, RootExecutableBindings actualBindings,
            OriginalEvidencePort actualOriginals) throws IOException {
        requireSession(same); Objects.requireNonNull(actualGame); Objects.requireNonNull(actualBindings); Objects.requireNonNull(actualOriginals);
        synchronized (physicalStatusOriginals) {
            PhysicalStatusOriginals installed = physicalStatusOriginals.get(actualGame);
            if (installed != null) {
                if (installed.bindings() != actualBindings || installed.originals() != actualOriginals)
                    throw new IOException("physical Status archive must retain the identical per-Game catalog and original port");
                return;
            }
            if (physicalStatusOriginals.size() >= 64) throw new IOException("finite actual physical Status archive routes are exhausted");
            physicalStatusOriginals.put(actualGame, new PhysicalStatusOriginals(actualBindings, actualOriginals));
        }
    }

    /** Install one actual private provider per captured epoch under its original writer scope.
     * This wiring grants no history, Native, readiness or action qualification. */
    public void bindReconciliationHistory(ContinuityStorePort.Session same, ReconciliationPendingBinding binding,
            RootUnresolvedHistoryQualification.EpochOwner actualEpoch) throws IOException {
        requireSession(same); Objects.requireNonNull(binding); Objects.requireNonNull(actualEpoch);
        binding.requireOwner(sameWriter, owner); actualEpoch.requireOwner(sameWriter, owner);
        if (binding.historyQualification() != actualEpoch.qualification())
            throw new IOException("history binding differs from its actual private epoch provider");
        actualEpoch.requireCurrentEpoch(same);
        var stamp = actualEpoch.stamp();
        var key = new HistoryEpoch(actualEpoch.machineId(), stamp.game(), stamp.episodeRunId(), stamp.episodeEpoch());
        synchronized (historyBindings) {
            HistoryRegistration previous = historyBindings.current.get();
            HistoryRegistration installed = historyBindings.epochs.get(key);
            if (installed != null && installed.binding() != binding)
                throw new IOException("another history binding is already installed for this actual epoch");
            if (installed == null && historyBindings.epochs.size() >= MAX_HISTORY_EPOCHS)
                throw new IOException("finite actual history epoch registry is exhausted");
            actualEpoch.requireCurrentEpoch(same);
            HistoryRegistration next = installed == null ? new HistoryRegistration(key, binding) : installed;
            if (installed == null) historyBindings.epochs.put(key, next);
            if (!historyBindings.current.compareAndSet(previous, next)) {
                if (installed == null) historyBindings.epochs.remove(key, next);
                throw new IOException("actual history epoch changed while installing its private binding");
            }
        }
    }

    /** Exact installed instance for Root/Readiness assertions; never creates or qualifies a binding. */
    public ReconciliationPendingBinding reconciliationHistoryBinding(
            RootUnresolvedHistoryQualification.EpochOwner actualEpoch) throws IOException {
        Objects.requireNonNull(actualEpoch).requireOwner(sameWriter, owner);
        var stamp = actualEpoch.stamp();
        var key = new HistoryEpoch(actualEpoch.machineId(), stamp.game(), stamp.episodeRunId(), stamp.episodeEpoch());
        synchronized (historyBindings) {
            HistoryRegistration installed = historyBindings.epochs.get(key);
            if (installed == null || installed.binding().historyQualification() != actualEpoch.qualification())
                throw new IOException("actual private history binding is not installed for this epoch");
            return installed.binding();
        }
    }

    @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session session) {
        return unchecked(() -> { requireSession(session); return new NativeOutcomeArchive(owner, session); });
    }
    @Override public <T> T inSession(ContinuityStorePort.Session session, Function<ActionPorts.OutcomeArchive, T> operation) {
        Objects.requireNonNull(operation);
        return unchecked(() -> scoped(session, () -> operation.apply(new NativeOutcomeArchive(owner, session))));
    }
    private <T> T scoped(ContinuityStorePort.Session session, IoWork<T> operation) throws IOException {
        requireSession(session); ContinuityStorePort.Session before = current.get();
        current.set(session);
        try { return operation.run(); }
        finally { if (before == null) current.remove(); else current.set(before); }
    }
    private void requireSession(ContinuityStorePort.Session session) throws IOException {
        Objects.requireNonNull(session); sameWriter.requireSession(session); session.requireWriter(artifacts.originalWriterLock());
        if (borrowed != null && borrowed != session) throw new IOException("cannot rebind an archive borrowed from another writer session");
        ContinuityStorePort.Session active = current.get();
        if (active != null && active != session) throw new IOException("different writer sessions cannot share one archive scope");
        if (sameWriter.artifactStore().orElseThrow(() -> new IOException("writer store detached")) != artifacts)
            throw new IOException("writer's canonical artifact store changed");
    }
    private ContinuityStorePort.Session activeSession() throws IOException {
        ContinuityStorePort.Session result = borrowed != null ? borrowed : current.get();
        // Long-lived producer callbacks may run inside this exact writer's held scope. Borrow
        // only its live thread-local session; a foreign scope is an error, never an absent lock.
        if (result == null) result = sameWriter.activeSession().orElse(null);
        if (result != null) requireSession(result); return result;
    }
    private <T> T writing(IoWork<T> operation) throws IOException {
        if (activeSession() != null) return operation.run();
        return sameWriter.locked(session -> scoped(session, operation));
    }
    private static <T> T unchecked(IoWork<T> operation) {
        try { return operation.run(); } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }

    /** Shared actual-byte producer for readiness/Driver data; role contracts stay with their domain producer. */
    public ExactRef preserveArtifact(ContinuityStorePort.Session session, byte[] original, int maximumBytes) throws IOException {
        requireSession(session); Objects.requireNonNull(original);
        return (publication==Publication.PLANNING_OBSERVATION?artifacts.publishPlanningRead(original,maximumBytes):artifacts.publish(original,maximumBytes)).reference();
    }
    public byte[] readArtifact(ContinuityStorePort.Session session, ExactRef original, int maximumBytes) throws IOException {
        requireSession(session); Objects.requireNonNull(original);
        LedgerFiles.Document result = artifacts.readOriginal(original, maximumBytes);
        rememberReadOriginal(session, result.pin()); return result.bytes();
    }
    private void rememberReadOriginal(ContinuityStorePort.Session session, Pin pin) throws IOException {
        ReadOriginalCapture capture = readOriginalCapture.get();
        if (capture == null) return;
        if (capture.session != session) throw new IOException("READ originals crossed their identical writer session");
        // The holder already retains the complete canonical source lane independently.
        // Only exact native Pin membership may assign that role; an old-epoch external
        // source absent from it remains an explicit READ original, with its real locator.
        if (capture.installedSources.contains(pin)) return;
        Pin prior = capture.pins.putIfAbsent(pin.reference(), pin);
        if (prior != null && !prior.equals(pin)) throw new IOException("READ original native file identity changed during replay");
        if (capture.pins.size() > MAX_READ_ORIGINALS) throw new ReadOriginalsLimitExceeded();
    }
    private ExactRef publish(byte[] original, int maximumBytes) throws IOException {
        ContinuityStorePort.Session session = activeSession();
        if (session == null) throw new IOException("archive publication requires the same writer's live session");
        return preserveArtifact(session, original, maximumBytes);
    }
    private byte[] readBytes(ExactRef original, int maximumBytes) throws IOException {
        ContinuityStorePort.Session session = activeSession();
        return session == null ? artifacts.read(original, maximumBytes) : readArtifact(session, original, maximumBytes);
    }
    private ExactRef reference(byte[] original, int maximumBytes) throws IOException {
        activeSession();
        return artifacts.referenceOf(original, maximumBytes).reference();
    }
    /** The same physical store and writer session own presentation originals too. Fixed-size
     * regions are custody of bytes, including torn/partial diagnostics, never a native-pipe ACK. */
    @Override public ExactRef preservePresentationArtifact(OriginalArtifact original) {
        return unchecked(() -> writing(() -> publish(Objects.requireNonNull(original).bytes(), presentationLimit(original.role()))));
    }
    @Override public OriginalArtifact loadPresentationArtifact(ArtifactRole role, ExactRef original) {
        return unchecked(() -> writing(() -> presentationArtifact(role, original)));
    }
    @Override public ExactRef presentationArtifactReferenceOf(OriginalArtifact original) {
        return unchecked(() -> writing(() -> reference(Objects.requireNonNull(original).bytes(), presentationLimit(original.role()))));
    }
    private static int presentationLimit(ArtifactRole role) {
        Objects.requireNonNull(role);
        return role == ArtifactRole.POST_METADATA ? 16384 : role.fixedBytes();
    }
    private OriginalArtifact presentationArtifact(ArtifactRole role, ExactRef original) throws IOException {
        OriginalArtifact value = new OriginalArtifact(role, readBytes(Objects.requireNonNull(original), presentationLimit(role)));
        value.requireReference(original);
        if (!reference(value.bytes(), presentationLimit(role)).equals(original))
            throw new IOException("presentation original is not this writer's canonical retained locator");
        return value;
    }
    @Override public ExactRef preservePresentationOutcome(OriginalOutcome original) {
        return unchecked(() -> writing(() -> {
            verifyPresentationOutcome(Objects.requireNonNull(original));
            return publish(original.encode(), META_LIMIT);
        }));
    }
    @Override public OriginalOutcome loadPresentationOutcome(ExactRef original) {
        return unchecked(() -> writing(() -> {
            OriginalOutcome value = OriginalOutcome.decode(readBytes(Objects.requireNonNull(original), META_LIMIT));
            verifyPresentationOutcome(value);
            if (!reference(value.encode(), META_LIMIT).equals(original))
                throw new IOException("presentation outcome canonical locator differs");
            return value;
        }));
    }
    @Override public ExactRef presentationOutcomeReferenceOf(OriginalOutcome original) {
        return unchecked(() -> writing(() -> {
            verifyPresentationOutcome(Objects.requireNonNull(original));
            return reference(original.encode(), META_LIMIT);
        }));
    }
    @Override public ExactRef preservePresentationObservation(PresentationObservation original) {
        return unchecked(() -> writing(() -> {
            verifyPresentationObservation(Objects.requireNonNull(original));
            return publish(original.encode(), META_LIMIT);
        }));
    }
    @Override public PresentationObservation loadPresentationObservation(ExactRef original) {
        return unchecked(() -> writing(() -> {
            PresentationObservation value = PresentationObservation.decode(readBytes(Objects.requireNonNull(original), META_LIMIT));
            verifyPresentationObservation(value);
            if (!reference(value.encode(), META_LIMIT).equals(original))
                throw new IOException("presentation observation canonical locator differs");
            return value;
        }));
    }
    @Override public ExactRef presentationObservationReferenceOf(PresentationObservation original) {
        return unchecked(() -> writing(() -> {
            verifyPresentationObservation(Objects.requireNonNull(original));
            return reference(original.encode(), META_LIMIT);
        }));
    }
    private void presentationExisting(ExactRef original) throws IOException {
        if (original.bytes() < 1 || original.bytes() > WriterContracts.MAX_PIN_BYTES)
            throw new IOException("bounded nonempty existing presentation evidence required");
        int maximum = Math.toIntExact(original.bytes());
        byte[] actual = readBytes(original, maximum);
        if (!reference(actual, maximum).equals(original))
            throw new IOException("presentation evidence must retain its original owned locator");
    }
    private void verifyPresentationPreparation(PresentationRequest request) throws IOException {
        for (ExactRef original : request.preparationEvidence()) presentationExisting(original);
    }
    private void verifyPresentationOutcome(OriginalOutcome original) throws IOException {
        verifyPresentationPreparation(original.request());
        switch (original) {
            case OriginalOutcome.NotPosted value -> {
                for (ExactRef evidence : value.evidence()) presentationExisting(evidence);
            }
            case OriginalOutcome.Unknown value -> {
                for (ExactRef evidence : value.evidence()) presentationExisting(evidence);
            }
            case OriginalOutcome.Posted value -> {
                byte[] request = presentationArtifact(ArtifactRole.REQUEST, value.originalRequest()).bytes();
                Optional<byte[]> tracking = value.originalTrackingRequest().isEmpty() ? Optional.empty()
                        : Optional.of(presentationArtifact(ArtifactRole.TRACKING_REQUEST, value.originalTrackingRequest().orElseThrow()).bytes());
                byte[] metadata = presentationArtifact(ArtifactRole.POST_METADATA, value.originalPostEvidence()).bytes();
                OriginalOutcome.PostEvidence evidence = OriginalOutcome.PostEvidence.decode(metadata);
                byte[] before = presentationArtifact(ArtifactRole.HEADER, evidence.beforeHeader()).bytes();
                byte[] after = presentationArtifact(ArtifactRole.HEADER, evidence.afterHeader()).bytes();
                value.verifyOriginal(request, tracking, metadata, before, after);
            }
        }
    }
    private void verifyPresentationObservation(PresentationObservation original) throws IOException {
        verifyPresentationPreparation(original.request());
        switch (original) {
            case PresentationObservation.Pending value -> {
                PresentationObservation.Capture capture = value.capture();
                // A torn result remains raw custody; do not decode its status/geometry as an ACK.
                capture.verifyOriginal(presentationArtifact(ArtifactRole.HEADER, capture.originalHeader()).bytes(),
                        presentationArtifact(ArtifactRole.RESULT, capture.originalResult()).bytes(),
                        presentationArtifact(ArtifactRole.DIAGNOSTICS, capture.originalDiagnostics()).bytes());
            }
            case PresentationObservation.Acknowledged value -> {
                PresentationObservation.Capture capture = value.capture();
                value.verifyOriginal(presentationArtifact(ArtifactRole.HEADER, capture.originalHeader()).bytes(),
                        presentationArtifact(ArtifactRole.RESULT, capture.originalResult()).bytes(),
                        presentationArtifact(ArtifactRole.DIAGNOSTICS, capture.originalDiagnostics()).bytes());
            }
            case PresentationObservation.Unavailable value -> {
                for (ExactRef evidence : value.originals()) presentationExisting(evidence);
            }
        }
    }
    /** Distinct Win32 frontend DATA. Its original request and outcomes never use mmap binary
     * roles or a NativeWire decoder. Source admission and physical permission stay central. */
    @Override public ExactRef preserveFrontendWindowCaptureRequest(FrontendWindowCaptureRequest original) {
        return unchecked(() -> writing(() -> {
            verifyFrontendWindowRequest(Objects.requireNonNull(original));
            return publish(original.encode(), META_LIMIT);
        }));
    }
    @Override public FrontendWindowCaptureRequest loadFrontendWindowCaptureRequest(ExactRef original) {
        return unchecked(() -> writing(() -> frontendWindowRequest(Objects.requireNonNull(original))));
    }
    @Override public ExactRef frontendWindowCaptureRequestReferenceOf(FrontendWindowCaptureRequest original) {
        return unchecked(() -> writing(() -> {
            verifyFrontendWindowRequest(Objects.requireNonNull(original));
            return reference(original.encode(), META_LIMIT);
        }));
    }
    private FrontendWindowCaptureRequest frontendWindowRequest(ExactRef original) throws IOException {
        FrontendWindowCaptureRequest value = FrontendWindowCaptureRequest.decode(readBytes(original, META_LIMIT));
        verifyFrontendWindowRequest(value);
        if (!reference(value.encode(), META_LIMIT).equals(original))
            throw new IOException("Win32 frontend request canonical locator differs");
        return value;
    }
    private void verifyFrontendWindowRequest(FrontendWindowCaptureRequest original) throws IOException {
        presentationExisting(original.actualFrontendEvidence());
        for (ExactRef evidence : original.preparationEvidence()) presentationExisting(evidence);
        // Preserve the actual selected source locator. Use the existing writer's native pin
        // reader; copying source bytes to an artifact would change this provenance identity.
        ExactRef source = original.sourceRef();
        if (source.bytes() < 1 || source.bytes() > WriterContracts.MAX_PIN_BYTES)
            throw new IOException("bounded original Win32 frontend source required");
        ContinuityStorePort.Session session = activeSession();
        if (session == null) throw new IOException("Win32 frontend source needs its actual writer session");
        int maximum = Math.toIntExact(source.bytes());
        Pin pin = session.capturePin(source, maximum);
        byte[] actual = session.readPinned(pin, maximum);
        if (actual.length != source.bytes()) throw new IOException("Win32 frontend selected source length differs");
        session.verifyPin(pin);
    }
    @Override public ExactRef preserveFrontendWindowCaptureOutcome(FrontendWindowCaptureOutcome original) {
        return unchecked(() -> writing(() -> {
            verifyFrontendWindowOutcome(Objects.requireNonNull(original));
            return publish(original.encode(), META_LIMIT);
        }));
    }
    @Override public FrontendWindowCaptureOutcome loadFrontendWindowCaptureOutcome(ExactRef original) {
        return unchecked(() -> writing(() -> {
            FrontendWindowCaptureOutcome value = FrontendWindowCaptureOutcome.decode(readBytes(Objects.requireNonNull(original), META_LIMIT));
            verifyFrontendWindowOutcome(value);
            if (!reference(value.encode(), META_LIMIT).equals(original))
                throw new IOException("Win32 frontend outcome canonical locator differs");
            return value;
        }));
    }
    @Override public ExactRef frontendWindowCaptureOutcomeReferenceOf(FrontendWindowCaptureOutcome original) {
        return unchecked(() -> writing(() -> {
            verifyFrontendWindowOutcome(Objects.requireNonNull(original));
            return reference(original.encode(), META_LIMIT);
        }));
    }
    private void verifyFrontendWindowOutcome(FrontendWindowCaptureOutcome original) throws IOException {
        FrontendWindowCaptureRequest request = frontendWindowRequest(original.originalRequest());
        if (!request.equals(original.request())) throw new IOException("Win32 frontend original prepared request differs");
        original.verifyOriginalRequest(readBytes(original.originalRequest(), META_LIMIT));
        for (ExactRef evidence : original.originals()) presentationExisting(evidence);
    }
    private ExactRef token(RawJson original, boolean preserve) throws IOException {
        return preserve ? publish(original.bytes(), RawJson.MAXIMUM_BYTES) : reference(original.bytes(), RawJson.MAXIMUM_BYTES);
    }
    private ExactRef packet(byte[] original, boolean preserve) throws IOException {
        return preserve ? publish(original, WriterContracts.MAX_PIN_BYTES) : reference(original, WriterContracts.MAX_PIN_BYTES);
    }
    private RawJson token(ExactRef ref) throws IOException { return new RawJson(readBytes(ref, RawJson.MAXIMUM_BYTES)); }
    private ObjectNode metadata(ExactRef ref) throws IOException {
        JsonNode value = StrictJson.parse(readBytes(ref, META_LIMIT), META_LIMIT);
        StrictJson.require(value instanceof ObjectNode, "typed archive metadata object required"); return (ObjectNode) value;
    }
    private static byte[] encoded(ObjectNode row) { return StrictJson.canonical(row, META_LIMIT); }
    private static String text(ObjectNode row, String field) { return StrictJson.text(row.get(field)); }
    private static boolean bool(ObjectNode row, String field) {
        JsonNode node = row.get(field); StrictJson.require(node != null && node.isBoolean(), "exact archive boolean required: " + field); return node.booleanValue();
    }
    private static ExactRef ref(ObjectNode row, String field) { return ExactRef.fromJson(row.get(field)); }
    private static void fields(ObjectNode row, Set<String> required, String... optional) {
        Set<String> expected = new HashSet<>(required);
        for (String key : optional) if (row.has(key)) expected.add(key);
        StrictJson.object(row, Set.copyOf(expected));
    }
    private static void schema(ObjectNode row, String expected) { StrictJson.require(text(row, "schema").equals(expected), "exact archive schema required"); }

    @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) {
        return unchecked(() -> writing(() -> publish(dispatchBytes(Objects.requireNonNull(original), true), META_LIMIT)));
    }
    @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) {
        return unchecked(() -> reference(dispatchBytes(Objects.requireNonNull(original), false), META_LIMIT));
    }
    @Override public NativeActionPort.DispatchOutcome load(ExactRef original) {
        return unchecked(() -> new NativeArchiveDataCodec(this::readBytes).decodeDispatchData(original));
    }
    private byte[] dispatchBytes(NativeActionPort.DispatchOutcome original, boolean preserve) throws IOException {
        String dispatchSchema = DISPATCH_SCHEMA;
        if (original instanceof NativeActionPort.AckReceived ack) {
            if (ack.custody().isPresent()) dispatchSchema = DISPATCH_WITH_CUSTODY_SCHEMA;
            else if (ack.outbound().isPresent()) dispatchSchema = DISPATCH_WITH_OUTBOUND_SCHEMA;
        } else if (original instanceof NativeActionPort.Unknown unknown && unknown.failureCause().isPresent())
            dispatchSchema = DISPATCH_WITH_FAILURE_SCHEMA;
        ObjectNode row = StrictJson.object(); row.put("schema", dispatchSchema); row.put("request_id", original.requestId());
        if (original instanceof NativeActionPort.AckReceived ack) {
            verifyAck(ack); row.put("kind", "ACK"); row.put("native_ok", ack.nativeOk());
            row.set("frame_ref", token(ack.originalFrame(), preserve).toJson()); row.set("packet_ref", packet(ack.originalPacket(), preserve).toJson());
            if (ack.originalResultToken().isPresent()) row.set("result_ref", token(ack.originalResultToken().orElseThrow(), preserve).toJson());
            if (ack.outbound().isPresent()) row.set("outbound_packet_ref", packet(ack.outbound().orElseThrow().originalPacket(), preserve).toJson());
            if (ack.custody().isPresent()) row.set("custody", NativeRequestChronologyCodec.encode(ack.custody().orElseThrow()));
        } else if (original instanceof NativeActionPort.RejectedBeforeDispatch rejected) {
            row.put("kind", "REJECTED_BEFORE_DISPATCH"); var proof = rejected.proof();
            row.put("stage", proof.stage().name()); row.put("request_bytes_written", proof.requestBytesWritten()); row.put("reason", proof.reason());
            if (proof.diagnostic().isPresent()) row.set("diagnostic_ref", token(proof.diagnostic().orElseThrow(), preserve).toJson());
        } else {
            NativeActionPort.Unknown unknown = (NativeActionPort.Unknown) original; row.put("kind", "UNKNOWN"); row.put("reason", unknown.reason());
            row.set("request_packet_ref", packet(unknown.originalRequestPacket(), preserve).toJson());
            if (unknown.rawReturn().isPresent()) row.set("raw_return_ref", token(unknown.rawReturn().orElseThrow(), preserve).toJson());
            if (unknown.failureCause().isPresent()) row.set("failure_cause", NativeFailureCauseCodec.encodeValue(unknown.failureCause().orElseThrow()));
        }
        return encoded(row);
    }
    private static void verifyAck(NativeActionPort.AckReceived ack) throws IOException {
        NativeArchiveDataCodec.verifyAck(ack);
    }

    @Override public ExactRef preserveRequest(NativeRequest original) {
        return unchecked(() -> writing(() -> publish(requestBytes(Objects.requireNonNull(original), true), META_LIMIT)));
    }
    @Override public ExactRef requestReferenceOf(NativeRequest original) {
        return unchecked(() -> reference(requestBytes(Objects.requireNonNull(original), false), META_LIMIT));
    }
    private byte[] requestBytes(NativeRequest original, boolean preserve) throws IOException {
        verifyPreparationOriginals(original);
        ObjectNode row = StrictJson.object(); row.put("schema", original.preparationEvidence().isEmpty() ? REQUEST_SCHEMA : REQUEST_WITH_PREPARATION_SCHEMA); row.put("step", original.step());
        if (original.requiredCapability().isPresent()) row.put("required_capability", original.requiredCapability().orElseThrow());
        if (!original.preparationEvidence().isEmpty()) {
            var evidence = row.putArray("preparation_evidence"); original.preparationEvidence().forEach(ref -> evidence.add(ref.toJson()));
        }
        row.set("additional_fields_ref", token(original.additionalFields(), preserve).toJson()); return encoded(row);
    }
    @Override public NativeRequest loadRequest(ExactRef original) {
        return unchecked(() -> new NativeArchiveDataCodec(this::readBytes).decodePreparedRequestData(original));
    }
    private void verifyPreparationOriginals(NativeRequest original) throws IOException {
        // Exact originals are custody metadata. Their role/schema and transitive proof closure are
        // replayed by the installed preparation owner, never inferred from command arguments here.
        for (ExactRef retained : original.preparationEvidence()) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
    }

    /** Read-only DATA binding for an existing failed attempt. Historical canonical membership
     * and the actual installed contract's interpretation remain the history owner's responsibility. */
    @Override public void verifyReadAttemptOriginals(PlanningReadRequest request, String actualRequestId,
            PlanningReadGuard before, NativeRequest prepared, NativeActionPort.DispatchOutcome original) {
        unchecked(() -> writing(() -> {
            Objects.requireNonNull(request); StrictJson.text(actualRequestId); Objects.requireNonNull(before);
            Objects.requireNonNull(prepared); Objects.requireNonNull(original);
            GuardEvidence binding = before.binding();
            StrictJson.require(request.origin().acceptsGuard(binding.origin()) && request.source().equals(binding.source())
                    && request.sessionId().equals(binding.sessionId()) && request.operation().equals(binding.operation()),
                    "failed read request differs from its original complete before guard");
            if (before.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)
                StrictJson.require(before.paused() && before.mapReady() && before.playerAlive(),
                        "failed gameplay read lost its original living paused map guard");
            StrictJson.require(actualRequestId.equals(original.requestId()), "failed read changed its actual original request ID");
            NativeStepDiscriminator.requireRequest(request.operation(), ExecutableStepBindings.Kind.READ, prepared);
            verifyGuardOriginals(binding);
            ExactRef outcomeRef = referenceOf(original), preparedRef = requestReferenceOf(prepared);
            if (!original.equals(load(outcomeRef)) || !outcomeRef.equals(referenceOf(load(outcomeRef)))
                    || !prepared.equals(loadRequest(preparedRef)) || !preparedRef.equals(requestReferenceOf(loadRequest(preparedRef))))
                throw new IOException("failed read lost its existing actual outcome or complete prepared original");
            NativeWire.ExecuteRequest sent;
            if (original instanceof NativeActionPort.AckReceived ack) {
                NativeRequestChronology chronology = ack.custody().orElseThrow(
                        () -> new IllegalArgumentException("failed read ACK has no original held-transport chronology"));
                chronology.verify(ack, binding);
                StrictJson.require(chronology.writeEntered().observedAt().isBefore(request.deadline()),
                        "failed read actual write entered outside its original request deadline");
                // Failed/late DATA may arrive after the old deadline. It is not a successful
                // PlanningReadReceipt and cannot gain query freshness by changing that time.
                sent = verifyPreparedOutbound(ack, prepared, binding);
            } else if (original instanceof NativeActionPort.Unknown unknown) {
                StrictJson.require(unknown.originalRequestPacket().length > 0,
                        "failed UNKNOWN read has no complete original outgoing packet");
                sent = NativeWire.decodeExecuteRequest(unknown.originalRequestPacket());
                verifyPreparedOutbound(sent, prepared, binding);
            } else {
                NativeActionPort.RejectedBeforeDispatch rejected = (NativeActionPort.RejectedBeforeDispatch) original;
                StrictJson.require(rejected.proof().requestBytesWritten() == 0,
                        "failed pre-dispatch read must retain its existing exact zero-write proof");
                // No outgoing packet, received ACK, consumed permit or Known read is inferred.
                return null;
            }
            StrictJson.require(sent.requestId().equals(actualRequestId), "failed read actual outgoing request ID differs");
            NativeStepDiscriminator.requireWire(request.operation(), ExecutableStepBindings.Kind.READ,
                    sent.step(), new RawJson(sent.normalizedAdditionalFields().value()));
            return null;
        }));
    }

    /** Existing failed READ DATA only, under the identical writer and original head. The
     * source may be outside the immutable store; its actual file pin is never a MATERIAL alias.
     * Borrowed withSession/inSession views are this same class and execute this same override. */
    @Override public void verifyReadFailureOriginals(PlanningReadFailure original) {
        unchecked(() -> writing(() -> {
            Objects.requireNonNull(original);
            ContinuityStorePort.Session same = activeSession();
            if (same == null) throw new IOException("failed read requires its actual owning writer session");
            var head = same.head();
            if (head.state().sequence() != original.headSequence() || !head.digest().equals(original.headDigest()))
                same.requireHistoricalState(original.headSequence(), original.headDigest());
            // Replay the installed writer's source closure and this request's exact source
            // through the existing original-file reader, including native FileID checks.
            List<Pin> sources = same.captureSources();
            ReadOriginalCapture capture = readOriginalCapture.get();
            if (capture != null) for (Pin installedSource : sources)
                capture.verifiedSourceReferences.add(installedSource.reference());
            ExactRef source = original.request().source().sourceRef();
            if (source.bytes() < 1 || source.bytes() > WriterContracts.MAX_PIN_BYTES)
                throw new IOException("bounded failed-read source original required");
            int sourceMaximum = Math.toIntExact(source.bytes());
            Pin requestSource = same.capturePin(source, sourceMaximum);
            same.readPinned(requestSource, sourceMaximum);
            rememberReadOriginal(same, requestSource);
            verifyReadAttemptOriginals(original.request(), original.requestId(), original.before(),
                    original.prepared(), original.original());
            if (!original.originalRef().equals(referenceOf(original.original()))
                    || !original.preparedRef().equals(requestReferenceOf(original.prepared()))
                    || !original.original().equals(load(original.originalRef()))
                    || !original.prepared().equals(loadRequest(original.preparedRef())))
                throw new IOException("failed read changed its exact existing outcome or prepared locator");
            verifyGuardOriginals(original.after().binding());
            // Keep even an external request source pinned over the entire before/wire/after
            // replay. A fresh same-byte replacement cannot become the original native file.
            same.verifyPin(requestSource);
            for (Pin installedSource : sources) same.verifyPin(installedSource);
            var unchanged = same.head();
            if (head.state().sequence() != unchanged.state().sequence() || !head.digest().equals(unchanged.digest()))
                throw new IOException("canonical head changed during failed-read original verification");
            return null;
        }));
    }

    /** Trace only the existing failed-attempt readers under their same writer. With no
     * observed after proof, no after is constructed. Sources keep their actual locators;
     * this dependency list is DATA and grants no successful READ or live authority. */
    @Override public ActionPorts.FailedReadOriginals loadFailedReadOriginals(PlanningReadRequest request,
            String actualRequestId, PlanningReadGuard before, NativeRequest prepared,
            NativeActionPort.DispatchOutcome original, Optional<ExactRef> observedFailureReference) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(observedFailureReference);
            ContinuityStorePort.Session same = activeSession();
            if (readOriginalCapture.get() != null)
                throw new IOException("a READ original closure cannot recursively replace another capture");
            // The failed-read caller retains one flat closure, including consumed sources.
            ReadOriginalCapture capture = new ReadOriginalCapture(same, List.of());
            readOriginalCapture.set(capture);
            try {
                verifyReadAttemptOriginals(request, actualRequestId, before, prepared, original);
                observedFailureReference.ifPresent(reference -> PlanningReadFailureCodec.load(reference, this));
                Set<ExactRef> references = new LinkedHashSet<>(capture.pins.keySet());
                references.addAll(capture.verifiedSourceReferences);
                return new ActionPorts.FailedReadOriginals(List.copyOf(references));
            } finally { readOriginalCapture.remove(); }
        }));
    }

    @Override public ExactRef preservePlanningRead(PlanningReadReceipt original) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(original);
            // A private finite facade propagates publication through this receipt, request and actual returned outcome only.
            // It cannot escape as an ACTION archive or a later session default.
            return new NativeOutcomeArchive(owner,activeSession(),Publication.PLANNING_OBSERVATION).preserveRead(original);
        }));
    }
    @Override public ExactRef preserveRead(PlanningReadReceipt original) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(original);
            return switch (original.archiveVersion()) {
                case HISTORICAL_V1 -> reference(readBytes(original, false), META_LIMIT);
                case CURRENT_V2, PHYSICAL_STATUS_V3, RETAINED_MATERIAL_V4 -> publish(readBytes(original, true), META_LIMIT);
            };
        }));
    }
    @Override public ExactRef readReferenceOf(PlanningReadReceipt original) {
        return unchecked(() -> writing(() -> reference(readBytes(Objects.requireNonNull(original), false), META_LIMIT)));
    }
    private byte[] readBytes(PlanningReadReceipt original, boolean preserve) throws IOException {
        verifyReadOriginals(original);
        boolean historical = original.archiveVersion() == PlanningReadReceipt.ArchiveVersion.HISTORICAL_V1;
        if (historical && (preserve || original.adoption().isPresent()))
            throw new IOException("historical v1 reads cannot publish new originals or carry adoption");
        boolean physical = original.archiveVersion() == PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3;
        boolean material = original.archiveVersion() == PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4;
        ObjectNode row = StrictJson.object(); row.put("schema", historical ? READ_SCHEMA
                : physical ? PHYSICAL_STATUS_READ_SCHEMA : material ? RETAINED_MATERIAL_READ_SCHEMA : READ_WITH_ADOPTION_SCHEMA);
        row.put("contract_id", original.contractId()); row.put("request_id", original.requestId());
        row.set("request", planningRequest(original.request(), preserve));
        row.set("before", CommandOriginCodec.planningGuard(original.before())); row.set("after", CommandOriginCodec.planningGuard(original.after()));
        row.set("original_ref", (preserve ? preserve(original.original()) : referenceOf(original.original())).toJson());
        if (!historical && !physical) {
            if (original.adoption().isPresent()) row.set("adoption", adoption(original.adoption().orElseThrow(), preserve));
            else row.putNull("adoption");
        }
        if (material) {
            PlanningReadReceipt.RetainedMaterial retained = original.retainedMaterial().orElseThrow();
            ObjectNode attachment = StrictJson.object(); attachment.put("kind", retained.kind().name());
            attachment.set("original", retained.original().toJson()); row.set("retained_material", attachment);
        }
        return encoded(row);
    }
    private ObjectNode planningRequest(PlanningReadRequest request, boolean preserve) throws IOException {
        return CommandOriginCodec.planningRequest(request, token(new RawJson(OpportunityJson.encode(request.arguments())), preserve));
    }
    private ObjectNode adoption(PlanningReadAdoption original, boolean preserve) throws IOException {
        ObjectNode row = StrictJson.object(); row.set("current_request", planningRequest(original.currentRequest(), preserve));
        row.set("current_semantic_ref", token(new RawJson(DriverJson.encode(original.currentSemantic())), preserve).toJson());
        row.set("original_unknown_ref", referenceOf(original.originalUnknown()).toJson());
        row.set("prepared_request_ref", requestReferenceOf(original.preparedRequest()).toJson());
        row.put("original_head_sequence", original.originalHeadSequence()); row.put("original_head_digest", original.originalHeadDigest()); return row;
    }
    @Override public PlanningReadReceipt loadRead(ExactRef original) {
        return unchecked(() -> writing(() -> {
            PlanningReadReceipt result = new NativeArchiveDataCodec(this::readBytes).decodeRead(original);
            verifyReadOriginals(result); return result;
        }));
    }

    @Override public ExactRef preserveRecord(ActionRecord original) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(original); preserveReceipt(original.receipt()); original.previous().ifPresent(this::loadRecord);
            return publish(ActionRecordCodec.encode(original, this), META_LIMIT);
        }));
    }
    @Override public ActionRecord loadRecord(ExactRef original) { return unchecked(() -> ActionRecordCodec.decode(readBytes(original, META_LIMIT), this)); }
    @Override public ExactRef recordReferenceOf(ActionRecord original) { return unchecked(() -> reference(ActionRecordCodec.encode(Objects.requireNonNull(original), this), META_LIMIT)); }
    @Override public ExactRef preserveReceipt(ActionReceipt original) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(original);
            if (original.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.FixtureStarted started) {
                // This ACK is a separate actual Native READ, not the original Start ACK.
                // Validate its original parent/custody before first publishing that dependency;
                // the sole proof codec then references the retained original during verification.
                started.observation().validate(original.command(), settled.attempt(), settled.dispatch());
                preserve(started.observation().independentRead());
            }
            verifyReceiptOriginals(original);
            if (original.state() instanceof PhysicalActionState physical) PhysicalActionCodec.preserve(physical, this);
            ActionTransitions.attempt(original.state()).ifPresent(attempt -> preserveRequest(attempt.preparedRequest()));
            ActionTransitions.dispatch(original.state()).ifPresent(this::preserve);
            if (original.state() instanceof ActionState.Settled state) preserveSettlement(state.settlement());
            if (original.state() instanceof ActionState.CompositeSettled state) preserveSettlement(state.settlement());
            return publish(ActionReceiptCodec.encodeReceipt(original, this), ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        }));
    }
    private void preserveSettlement(ActionState.Settlement original) throws IOException {
        if (original instanceof ActionState.FixtureBusinessCompleted completed) {
            preserveReceipt(completed.observation().evidence().originalStart());
            preserveRead(completed.observation().evidence().campaignRootRead());
        }
        if (original instanceof ActionState.NormalExitPhaseConfirmed phase) {
            // Verification above already required these exact original read locators.
            preserveRead(phase.observation().beforeContext()); preserveRead(phase.observation().afterContext());
        }
        if (original instanceof ActionState.FamilySendConfirmed sent) {
            // The sole native producer already retained these exact queries before DATA exists.
            // Retain/read them again without manufacturing metadata for a missing original.
            preserveRead(sent.observation().beforeStorage()); preserveRead(sent.observation().afterStorage());
        }
        if (original instanceof ActionState.SwaySchedulerCompleted scheduler) {
            RawJson encoded = swayProof(scheduler.proof()); ExactRef ref = preserveMaterial(encoded);
            if (!encoded.equals(loadMaterial(ref))) throw new IOException("complete Sway scheduler sidecar readback changed");
        }
        if (original instanceof ActionState.ControlApplied control) { preserveRead(control.read()); control.supportingReads().forEach(this::preserveRead); }
        if (original instanceof ActionState.CompositeControlApplied control) {
            preserveRead(control.observation().terminalStatus()); control.observation().supportingReads().forEach(this::preserveRead);
        }
        if (original instanceof ActionState.GameplayEntered entered) preserveRead(entered.observation().campaignRootRead());
        if (original instanceof ActionState.NonAppliedTerminal terminal) {
            preserveRead(terminal.observation().selectedCollection()); preserveRead(terminal.observation().afterCollection());
        }
        if (original instanceof ActionState.LifecycleControlApplied control) {
            preserveRead(control.observation().beforeStatus()); preserveRead(control.observation().independentRead());
        }
        if (original instanceof ActionState.LifecycleApplied lifecycle) {
            RawJson encoded = lifecycleProof(lifecycle.proof()); ExactRef ref = preserveMaterial(encoded);
            if (!encoded.equals(loadMaterial(ref))) throw new IOException("complete lifecycle proof sidecar readback changed");
        }
    }
    @Override public ActionReceipt loadReceipt(ExactRef original) {
        return unchecked(() -> writing(() -> {
            ActionReceipt result = ActionReceiptCodec.decodeReceipt(readBytes(original, ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES), this);
            verifyReceiptOriginals(result); return result;
        }));
    }
    @Override public ExactRef receiptReferenceOf(ActionReceipt original) {
        return unchecked(() -> writing(() -> {
            verifyReceiptOriginals(Objects.requireNonNull(original));
            return reference(ActionReceiptCodec.encodeReceipt(original, this), ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        }));
    }

    /** Physical retention is distinct from domain acceptance. No observer, native query, dispatch or
     * ledger transition runs here. Historical empty-basis metadata remains data, without new authority.
     * Source-code references belong to the writer source guard and are never searched in this store.
     */
    private void verifyReceiptOriginals(ActionReceipt original) throws IOException {
        if (original.state() instanceof PhysicalActionState physical) verifyPhysicalOriginals(physical);
        if (original.command().expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind
                && ActionTransitions.composite(original.state()).isPresent())
            throw new IOException("operator request cannot borrow a composite or its ordinary guard");
        Optional<ActionState.Attempt> attempt = ActionTransitions.attempt(original.state());
        if (attempt.isPresent()) {
            NativeStepDiscriminator.requireRequest(original.command().operation(), ExecutableStepBindings.Kind.ACTION,
                    attempt.orElseThrow().preparedRequest());
            if (original.command().expectation() instanceof org.xar.ck3.control.application.action.CommandExpectation.OperatorRebind)
                verifyOperatorGuardOriginals(original.command(), attempt.orElseThrow().guard());
            else verifyGuardOriginals(attempt.orElseThrow().guard());
            var dispatch = ActionTransitions.dispatch(original.state());
            if (dispatch.isPresent() && dispatch.orElseThrow() instanceof NativeActionPort.AckReceived ack && ack.outbound().isPresent())
                verifyPreparedOutbound(ack, attempt.orElseThrow().preparedRequest(), attempt.orElseThrow().guard());
        }
        var composite = ActionTransitions.composite(original.state());
        if (composite.isPresent()) verifyGuardOriginals(composite.orElseThrow().guard());
        if (original.state() instanceof ActionState.Settled settled) {
            if (settled.settlement() instanceof ActionState.FixtureStarted started)
                started.observation().validate(original.command(), settled.attempt(), settled.dispatch());
            if (settled.settlement() instanceof ActionState.FixtureBusinessCompleted)
                throw new IOException("fixture business completion requires its actual original composite execution");
            if (settled.settlement() instanceof ActionState.DirectFixedWindowCompleted completed) {
                ActionEffects.validate(original.command(), settled.attempt(), settled.dispatch(), completed);
                completed.completion().validate(original.command(), settled.attempt(), settled.dispatch(), this);
                var ack = (NativeActionPort.AckReceived) settled.dispatch();
                verifyPreparedOutbound(ack, settled.attempt().preparedRequest(), settled.attempt().guard());
                ExactRef dispatch = referenceOf(ack), prepared = requestReferenceOf(settled.attempt().preparedRequest());
                if (!ack.equals(load(dispatch)) || !dispatch.equals(referenceOf(load(dispatch)))
                        || !settled.attempt().preparedRequest().equals(loadRequest(prepared)))
                    throw new IOException("direct fixed-window completion lost its existing ACK or complete preparation");
            }
            if (settled.settlement() instanceof ActionState.ControlSequenceCompleted)
                throw new IOException("control sequence requires its original composite execution and canonical child roster");
            if (settled.settlement() instanceof ActionState.PauseConfirmed pause) {
                ActionEffects.validate(original.command(), settled.attempt(), settled.dispatch(), pause);
                var ack = (NativeActionPort.AckReceived) settled.dispatch();
                // PauseConfirmation requires actual positive ACK/outbound/custody. This sole
                // protocol reader also binds the complete durable preparation and guarded revision.
                verifyPreparedOutbound(ack, settled.attempt().preparedRequest(), settled.attempt().guard());
                ExactRef dispatch = referenceOf(ack), prepared = requestReferenceOf(settled.attempt().preparedRequest());
                if (!ack.equals(load(dispatch)) || !dispatch.equals(referenceOf(load(dispatch)))
                        || !settled.attempt().preparedRequest().equals(loadRequest(prepared)))
                    throw new IOException("pause completion lost its existing original ACK or complete prepared request");
            }
            if (settled.settlement() instanceof ActionState.OperatorRebound rebound) {
                ActionEffects.validate(original.command(), settled.attempt(), settled.dispatch(), rebound);
                var ack = (NativeActionPort.AckReceived) settled.dispatch(); // The sole Completion validator requires this branch.
                NativeRequestChronology chronology = ack.custody().orElseThrow(
                        () -> new IllegalArgumentException("operator completion lacks its actual original ACK custody"));
                chronology.verify(ack, settled.attempt().guard());
                if (!chronology.session().equals(rebound.observation().transport()))
                    throw new IOException("operator completion changed the original held transport");
                verifyPreparedOutbound(ack, settled.attempt().preparedRequest(), settled.attempt().guard());
                ExactRef dispatch = referenceOf(ack), prepared = requestReferenceOf(settled.attempt().preparedRequest());
                if (!dispatch.equals(rebound.observation().originals().ack()) || !ack.equals(load(dispatch))
                        || !settled.attempt().preparedRequest().equals(loadRequest(prepared)))
                    throw new IOException("operator completion lost its existing canonical ACK or complete prepared original");
            }
            if (settled.settlement() instanceof ActionState.ControlApplied control && control.reconciledAck().isPresent()) {
                NativeActionPort.AckReceived candidate = ActionEffects.controlAcknowledgement(
                        original.command(), settled.attempt(), settled.dispatch(), control);
                // The observer already archived the actual received candidate. A late DATA
                // wrapper cannot manufacture it, replace the original UNKNOWN or change its bytes.
                ExactRef unknown = referenceOf(settled.dispatch());
                ExactRef prepared = requestReferenceOf(settled.attempt().preparedRequest());
                if (!settled.dispatch().equals(load(unknown))
                        || !settled.attempt().preparedRequest().equals(loadRequest(prepared)))
                    throw new IOException("reconciled control lost its existing original UNKNOWN or prepared request");
                verifyReconciledControlOriginal(control);
                verifyPreparedOutbound(candidate, settled.attempt().preparedRequest(), settled.attempt().guard());
                if (!control.read().equals(loadRead(readReferenceOf(control.read()))))
                    throw new IOException("reconciled control lost its original sampled read");
                NativeRequestChronology.requireSampledAfter(control.read(), settled.attempt(), candidate);
                for (PlanningReadReceipt read : control.supportingReads()) {
                    if (!read.equals(loadRead(readReferenceOf(read))))
                        throw new IOException("reconciled control lost its original supporting sampled read");
                    NativeRequestChronology.requireSampledAfter(read, settled.attempt(), candidate);
                }
            }
            if (settled.settlement() instanceof ActionState.NativeSourceCompleted source) {
                source.observation().validate(original.command(), settled.attempt(), settled.dispatch());
                ExactRef dispatch = referenceOf(settled.dispatch());
                if (!dispatch.equals(source.observation().originalDispatch()) || !settled.dispatch().equals(load(dispatch)))
                    throw new IOException("native source completion changed the original dispatch");
            }
            if (settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed phase)
                phase.observation().validate(original.command(), settled.attempt(), settled.dispatch(), this);
            if (settled.settlement() instanceof ActionState.FamilySendConfirmed sent)
                sent.observation().validate(original.command(), settled.attempt(), settled.dispatch(), this);
            if (settled.settlement() instanceof ActionState.LifecycleControlApplied control)
                control.observation().validate(original.command(), settled.attempt());
            if (settled.settlement() instanceof ActionState.NonAppliedTerminal terminal) {
                terminal.observation().validate(original.command(), settled.attempt());
                ExactRef submitted = referenceOf(settled.dispatch());
                if (!submitted.equals(terminal.observation().originalSubmission()) || !settled.dispatch().equals(load(submitted)))
                    throw new IOException("non-applied terminal changed its original archived dispatch");
            }
            if (settled.settlement() instanceof ActionState.CompositeRejected)
                throw new IOException("canonical composite rejection requires its original composite execution");
            if (settled.settlement() instanceof ActionState.CompositeNoGameplayWrite)
                throw new IOException("no-gameplay-write terminal requires its original composite execution");
            verifySettlementParent(settled.settlement(), original.command()); verifySettlementOriginals(settled.settlement());
        }
        if (original.state() instanceof ActionState.CompositeSettled settled) {
            if (settled.settlement() instanceof ActionState.CompositeNoGameplayWrite terminal) {
                terminal.observation().validate(original.command(), settled.execution());
                ActionEffects.validateComposite(original.command(), settled.execution(), terminal);
                ActionEffects.validateCompositeChildren(settled.execution(), terminal, List.of());
            }
            if (settled.settlement() instanceof ActionState.FixtureStarted)
                throw new IOException("fixture first-map completion requires its exact original primitive Start and ACK");
            if (settled.settlement() instanceof ActionState.FixtureBusinessCompleted completed)
                ActionEffects.validateComposite(original.command(), settled.execution(), completed);
            if (settled.settlement() instanceof ActionState.DirectFixedWindowCompleted)
                throw new IOException("direct fixed-window completion requires its exact original primitive ACK and preparation");
            if (settled.settlement() instanceof ActionState.PauseConfirmed)
                throw new IOException("pause confirmation requires its exact original primitive ACK and preparation");
            if (settled.settlement() instanceof ActionState.ControlSequenceCompleted sequence) {
                ActionEffects.validateComposite(original.command(), settled.execution(), sequence);
                var children = new java.util.ArrayList<ActionReceipt>();
                for (var child : sequence.observation().children()) {
                    ActionReceipt retained = loadReceipt(child.canonicalReceipt());
                    if (!child.canonicalReceipt().equals(receiptReferenceOf(retained)))
                        throw new IOException("control sequence child changed its existing canonical receipt locator");
                    children.add(retained);
                }
                sequence.observation().validateChildren(settled.execution(), List.copyOf(children));
                // Receipt custody and roster matching are DATA only. Actual canonical child
                // membership, proof roles and fresh-source retry authority stay with the same
                // installed archived domain verifier under this writer's historical head.
            }
            if (settled.settlement() instanceof ActionState.OperatorRebound)
                throw new IOException("operator completion requires its exact original primitive attempt and ACK");
            if (settled.settlement() instanceof ActionState.ControlApplied control && control.reconciledAck().isPresent())
                throw new IOException("reconciled control requires its original primitive UNKNOWN attempt");
            if (settled.settlement() instanceof ActionState.NativeSourceCompleted
                    || settled.settlement() instanceof ActionState.NormalExitPhaseConfirmed)
                throw new IOException("source/UI phase settlement requires its original primitive attempt and dispatch");
            if (settled.settlement() instanceof ActionState.FamilySendConfirmed)
                throw new IOException("family-send settlement requires its exact original primitive attempt and dispatch");
            if (settled.settlement() instanceof ActionState.CompositeRejected rejected && !settled.execution().children().equals(rejected.children()))
                throw new IOException("composite rejection changed its original recorded child identities");
            verifySettlementParent(settled.settlement(), original.command()); verifySettlementOriginals(settled.settlement());
        }
    }
    private void verifyReconciledControlOriginal(ActionState.ControlApplied control) throws IOException {
        if (control.reconciledAck().isEmpty()) return;
        var original = control.reconciledAck().orElseThrow();
        ExactRef reference = original.reference(this);
        NativeActionPort.DispatchOutcome retained = load(reference);
        if (!(retained instanceof NativeActionPort.AckReceived ack) || !ack.equals(original.ack())
                || !reference.equals(referenceOf(ack)))
            throw new IOException("reconciled control changed its actual retained ACK or locator");
    }
    /** v5 physical DATA must reopen existing originals before the explicit producer preserve
     * operation. Cold reads and reference calculation never manufacture a missing closure. */
    private void verifyPhysicalOriginals(PhysicalActionState original) throws IOException {
        verifyGuardOriginals(original.guard());
        byte[] request;
        if (original.request() instanceof PreparedAction.MmapRequest mmap) {
            verifyPresentationPreparation(mmap.value());
            RawJson encoded = new RawJson(mmap.value().encode());
            ExactRef retained = materialReferenceOf(encoded);
            if (!encoded.equals(loadMaterial(retained))) throw new IOException("original mmap prepared DATA changed");
            request = encoded.bytes();
        } else if (original.request() instanceof PreparedAction.WindowCaptureRequest window) {
            ExactRef retained = frontendWindowCaptureRequestReferenceOf(window.value());
            if (!window.value().equals(loadFrontendWindowCaptureRequest(retained)))
                throw new IOException("original Win32 prepared DATA changed");
            request = window.value().encode();
        } else throw new IOException("native pipe request cannot enter physical receipt custody");
        if (original.outcome().isPresent()) {
            PhysicalOutcome outcome = original.outcome().orElseThrow();
            byte[] actualRequest;
            if (outcome instanceof PhysicalOutcome.MmapOutcome mmap) {
                ExactRef retained = presentationOutcomeReferenceOf(mmap.value());
                if (!mmap.value().equals(loadPresentationOutcome(retained)))
                    throw new IOException("original mmap outcome DATA changed");
                actualRequest = mmap.value().request().encode();
            } else if (outcome instanceof PhysicalOutcome.WindowCaptureOutcome window) {
                ExactRef retained = frontendWindowCaptureOutcomeReferenceOf(window.value());
                if (!window.value().equals(loadFrontendWindowCaptureOutcome(retained)))
                    throw new IOException("original Win32 outcome DATA changed");
                actualRequest = window.value().request().encode();
            } else throw new IOException("native pipe outcome cannot enter physical receipt custody");
            if (!Arrays.equals(request, actualRequest)) throw new IOException("physical outcome changed complete prepared request");
        }
        // Sole readonly44 codec resolves existing references. No packet parser or material
        // assumption is applied to raw mmap regions or source-domain originals.
        for (ExactRef retained : PhysicalActionCodec.references(original, this)) presentationExisting(retained);
    }
    private byte[] verifyRetainedSourceOriginal(ExactRef original) throws IOException {
        if (original.bytes() < 1 || original.bytes() > WriterContracts.MAX_PIN_BYTES)
            throw new IOException("bounded retained source original required");
        ContinuityStorePort.Session session = activeSession();
        if (session == null) throw new IOException("source original requires its actual owning writer session");
        int maximum = Math.toIntExact(original.bytes());
        Pin pin = session.capturePin(original, maximum);
        byte[] bytes = session.readPinned(pin, maximum); session.verifyPin(pin);
        rememberReadOriginal(session, pin);
        return bytes;
    }
    private void verifyReadOriginals(PlanningReadReceipt original) throws IOException {
        // The actual live decoder preserved this source-owned material before publishing the
        // READ. Reopening follows that retained Ref; it never consults a current export path.
        if (original.retainedMaterial().isPresent()) loadMaterial(original.retainedMaterial().orElseThrow().original());
        if (original.adoption().isPresent()) {
            PlanningReadAdoption adopted = original.adoption().orElseThrow(); adopted.requireReceipt(original);
            ContinuityStorePort.Session same = activeSession();
            if (same == null) throw new IOException("late read requires its actual same-writer historical head scope");
            same.requireHistoricalState(adopted.originalHeadSequence(), adopted.originalHeadDigest());
            ExactRef unknown = referenceOf(adopted.originalUnknown());
            ExactRef prepared = requestReferenceOf(adopted.preparedRequest());
            if (!adopted.originalUnknown().equals(load(unknown)) || !adopted.preparedRequest().equals(loadRequest(prepared)))
                throw new IOException("late read changed its existing original UNKNOWN or prepared request");
            verifyPreparedOutbound(original.original(), adopted.preparedRequest(), original.before().binding());
        }
        original.original().custody().ifPresent(value -> value.verify(original));
        verifyGuardOriginals(original.before().binding()); verifyGuardOriginals(original.after().binding());
        if (original.original().outbound().isPresent()) {
            NativeWire.ExecuteRequest sent = NativeWire.decodeExecuteRequest(original.original().outbound().orElseThrow().originalPacket());
            if (!sent.requestId().equals(original.requestId()))
                throw new IOException("archived planning read differs from its actual outbound request ID");
            NativeStepDiscriminator.requireWire(original.request().operation(), ExecutableStepBindings.Kind.READ,
                    sent.step(), new RawJson(sent.normalizedAdditionalFields().value()));
            verifyOutboundRevision(sent, original.before().binding());
        }
    }
    private static NativeWire.ExecuteRequest verifyPreparedOutbound(NativeActionPort.AckReceived ack, NativeRequest prepared, GuardEvidence guard) throws IOException {
        ack.custody().ifPresent(value -> value.verify(ack, guard));
        NativeWire.ExecuteRequest sent = NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
        verifyPreparedOutbound(sent, prepared, guard);
        return sent;
    }
    private static void verifyPreparedOutbound(NativeWire.ExecuteRequest sent, NativeRequest prepared, GuardEvidence guard) throws IOException {
        JsonNode expectedAdditional = OpportunityJson.toNode(DriverJson.object(prepared.additionalFields().bytes(), RawJson.MAXIMUM_BYTES));
        StrictJson.require(expectedAdditional instanceof ObjectNode, "prepared outbound additions must remain an object");
        ObjectNode additions = (ObjectNode) expectedAdditional;
        if (additions.has("expected_snapshot_revision")) {
            JsonNode expectedSnapshot = additions.remove("expected_snapshot_revision");
            if (!expectedSnapshot.isIntegralNumber() || !expectedSnapshot.bigIntegerValue().equals(guard.origin().expectedRevision())
                    || sent.expectedSnapshotRevision().isEmpty())
                throw new IOException("prepared explicit snapshot revision differs from actual guarded outbound packet");
        }
        if (!sent.step().equals(prepared.step()) || !OpportunityJson.toNode(DriverJson.object(sent.normalizedAdditionalFields().value(), RawJson.MAXIMUM_BYTES))
                .equals(additions))
            throw new IOException("actual outbound execute fields differ from the durable prepared request");
        verifyOutboundRevision(sent, guard);
    }
    private static void verifyOutboundRevision(NativeWire.ExecuteRequest sent, GuardEvidence guard) throws IOException {
        var expected = guard.origin().expectedRevision();
        if (sent.expectedRevision().isPresent() && !sent.expectedRevision().orElseThrow().equals(expected)
                || sent.expectedSnapshotRevision().isPresent() && !sent.expectedSnapshotRevision().orElseThrow().equals(expected))
            throw new IOException("actual outbound revision differs from its original guarded frame");
    }
    private void verifyOperatorGuardOriginals(ActionCommand command, GuardEvidence original) throws IOException {
        ContinuityStorePort.Session same = activeSession();
        if (same == null) throw new IOException("operator guard requires its actual owning historical writer session");
        // The sole source-owned codec reopens the exact full before projection, HELLO/HB,
        // Driver/Aux/source roles and original head. This historical DATA check grants no
        // live operator authority, ordinary living readiness, current CAS or Window result.
        RootOperatorGuardEvidence.requireHistorical(same, command, original, this);
    }
    private void verifyGuardOriginals(GuardEvidence original) throws IOException {
        if (original.origin() instanceof CommandOrigin.PhysicalStatusOnly physical) {
            verifyPhysicalStatusOriginals(original, physical);
            return;
        }
        if (original.origin() instanceof CommandOrigin.Reconciliation reconciliation) {
            ReconciliationIdentity identity = reconciliation.identity(); verifyReconciliationOriginals(identity);
            var retainedRoles = new HashSet<>(identity.evidence().originals());
            retainedRoles.add(identity.pending().originalReceipt()); retainedRoles.add(identity.pending().originalBeforeDriver());
            // A guard basis is JSON material. A repeated identity role has already been read with
            // its explicit contract; notably, the heartbeat remains a complete framed packet.
            for (ExactRef locator : original.supportingEvidence()) if (!retainedRoles.contains(locator)) token(locator);
            return;
        }
        if (original.origin() instanceof CommandOrigin.LifecycleTerminal lifecycle) verifyLifecycleIdentityOriginals(lifecycle.identity());
        if (original.supportingEvidence().isEmpty()) return;
        // These are complete framed packets, not JSON material tokens.
        readBytes(original.nativeEvidence(), WriterContracts.MAX_PIN_BYTES);
        readBytes(original.capabilityEvidence(), WriterContracts.MAX_PIN_BYTES);
        for (ExactRef locator : original.supportingEvidence()) token(locator);
    }
    private void verifyPhysicalStatusOriginals(GuardEvidence original, CommandOrigin.PhysicalStatusOnly physical) throws IOException {
        ContinuityStorePort.Session same = activeSession();
        if (same == null) throw new IOException("physical Status originals require their actual owning writer session");
        var identity = physical.identity();
        PhysicalStatusOriginals installed;
        synchronized (physicalStatusOriginals) { installed = physicalStatusOriginals.get(identity.game()); }
        if (installed == null) throw new IOException("actual physical Status archive source router is unavailable");
        // Raw Native packets, source qualification and epoch metadata retain distinct roles.
        // The actual source-owned provider, rather than an ordinary Driver/living-map codec,
        // verifies their complete binding and historical source scope without new Native I/O.
        readOriginalPacket(identity.nativeEvidence()); readOriginalPacket(identity.helloEvidence());
        readOriginalPacket(identity.heartbeatEvidence());
        verifyRetainedSourceOriginal(identity.source().sourceRef());
        if(identity.sourceQualification().isPresent())verifyRetainedSourceOriginal(identity.sourceQualification().orElseThrow());
        if(identity.epochManifest().isPresent())verifyRetainedSourceOriginal(identity.epochManifest().orElseThrow());
        for (ExactRef retained : original.supportingEvidence()) verifyRetainedSourceOriginal(retained);
        var verified = installed.bindings().requirePhysicalStatusAuthority(identity)
                .verifyArchived(original, this, same, installed.originals());
        if (!identity.equals(verified)) throw new IOException("physical Status original verifier returned another complete identity");
    }
    private void verifyReconciliationOriginals(ReconciliationIdentity original) throws IOException {
        var evidence = original.evidence();
        byte[] originalNative = readBytes(evidence.actualNativePacket(), WriterContracts.MAX_PIN_BYTES);
        NativeWire.Frame nativeFrame = NativeWire.decode(originalNative);
        var factual = original.factual();
        if (!(nativeFrame instanceof NativeWire.Snapshot snapshot) || !snapshot.snapshotId().equals(factual.frame().snapshotId())
                || !snapshot.revision().equals(factual.frame().identity().nativeRevision()))
            throw new IOException("reconciliation factual identity differs from its actual original snapshot packet");
        NativeWire.Frame helloFrame = NativeWire.decode(readBytes(evidence.actualHello(), WriterContracts.MAX_PIN_BYTES));
        if (!(helloFrame instanceof NativeWire.Hello hello) || hello.pid() != factual.game().pid()
                || !hello.connectionGeneration().equals(original.connectionGeneration()))
            throw new IOException("reconciliation original hello differs from its held Game/connection");
        NativeWire.Frame heartbeat = NativeWire.decode(readBytes(evidence.originalHeartbeat(), WriterContracts.MAX_PIN_BYTES));
        if (!(heartbeat instanceof NativeWire.Notice notice) || notice.kind() != NativeWire.NoticeKind.HEARTBEAT)
            throw new IOException("reconciliation heartbeat must remain its original complete native packet");
        RawJson manifest = loadFullMaterial(evidence.observationManifest());
        RawJson currentDriver = loadFullMaterial(evidence.currentOriginalDriver());
        if(evidence.completeSourceQualification().isPresent())new RawJson(readBytes(evidence.completeSourceQualification().orElseThrow(), 16 << 20));
        new RawJson(readBytes(original.pending().originalReceipt(), ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES));
        RawJson beforeDriver = loadFullMaterial(original.pending().originalBeforeDriver());
        if (beforeDriver.equals(currentDriver)) {
            if (original.driverRelation() != ReconciliationIdentity.DriverRelation.EXACT || original.historyPoint().isPresent())
                throw new IOException("unchanged reconciliation Driver must retain its original exact relation");
        } else {
            if (original.driverRelation() != ReconciliationIdentity.DriverRelation.HISTORY_APPEND)
                throw new IOException("changed reconciliation Driver requires explicit history-append provenance");
            verifyReconciliationHistory(original, manifest, currentDriver, originalNative);
        }
        // Physical custody and packet roles only. The sole Root reconciliation verifier validates
        // actual manifest/source semantics, original canonical pending membership and writer point.
    }
    private void verifyReconciliationHistory(ReconciliationIdentity identity, RawJson manifest,
            RawJson currentDriver, byte[] originalNative) throws IOException {
        ContinuityStorePort.Session same = activeSession();
        if (same == null) throw new IOException("history reconciliation requires its actual writer Session");
        synchronized (historyBindings) {
            if (historyBindings.epochs.isEmpty())
                throw new IOException("actual private reconciliation history binding is unavailable");
        }
        var evidence = identity.evidence();
        if (!DriverObservationEvidenceReader.currentDriverReference(evidence.observationManifest(), manifest)
                .equals(evidence.currentOriginalDriver()))
            throw new IOException("reconciliation manifest selected another complete Driver original");
        var observed = DriverObservationEvidenceReader.nativeFrame(evidence.observationManifest(), manifest, originalNative);
        var facts = DriverObservationEvidenceReader.decode(evidence.observationManifest(), manifest, currentDriver, observed);
        if (!facts.transport().machineId().equals(identity.factual().machineId())
                || !facts.transport().game().equals(identity.factual().game())
                || !facts.transport().sessionId().equals(identity.sessionId())
                || !facts.transport().connectionGeneration().equals(identity.connectionGeneration())
                || !facts.driver().session().episodeRunId().equals(identity.factual().frame().episodeRunId())
                || !facts.source().equals(identity.source()))
            throw new IOException("reconciliation original manifest crossed its actual epoch owner");
        var key = new HistoryEpoch(facts.transport().machineId(), facts.transport().game(),
                facts.driver().session().episodeRunId(), facts.episodeEpoch());
        HistoryRegistration installed;
        synchronized (historyBindings) { installed = historyBindings.epochs.get(key); }
        if (installed == null) throw new IOException("actual private reconciliation history epoch is not installed");
        installed.binding().requireOwner(sameWriter, owner);
        // The sole binder authenticates the actual history target Head and original UNKNOWN
        // there, avoiding recursive traversal through a later settled reconciliation receipt.
        // The same private provider still replays every actual source/event/Driver proof.
        installed.binding().verifyHistorical(same, identity);
        synchronized (historyBindings) {
            if (historyBindings.epochs.get(key) != installed)
                throw new IOException("actual reconciliation history binding changed during cold verification");
        }
    }
    private void verifyEffectOriginals(ActionState.EffectObservation original) throws IOException {
        verifyProvenanceOriginal(original.provenance(), original.after(), original.originalEvidence());
        var reconciliation = NativeEffectEvidence.reconciliationGuard(original, this);
        if (reconciliation.isPresent()) verifyGuardOriginals(reconciliation.orElseThrow());
        if (!(original.provenance() instanceof ObservationProvenance.Push) && original.supportingEvidence().isEmpty()) return;
        if (!(original.provenance() instanceof ObservationProvenance.Push)) readBytes(original.originalEvidence(), WriterContracts.MAX_PIN_BYTES);
        for (ExactRef locator : original.supportingEvidence()) token(locator);
    }
    private void verifyProvenanceOriginal(ObservationProvenance provenance,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity after, ExactRef originalEvidence) throws IOException {
        if (provenance instanceof ObservationProvenance.Push push) {
            push.validate(after, originalEvidence);
            byte[] packet = readBytes(push.originalPacket(), WriterContracts.MAX_PIN_BYTES);
            NativeWire.Frame frame = NativeWire.decode(packet);
            if (!(frame instanceof NativeWire.Snapshot actual) || !actual.snapshotId().equals(push.snapshotId())
                    || !actual.revision().equals(push.nativeRevision()))
                throw new IOException("push provenance differs from its retained original native snapshot packet");
        }
    }
    private void verifyTerminalOriginals(ActionTerminalObservation original) throws IOException {
        verifyProvenanceOriginal(original.provenance(), original.after(), original.originalEvidence());
        readBytes(original.originalEvidence(), WriterContracts.MAX_PIN_BYTES); load(original.originalSubmission());
        verifyReadOriginals(original.selectedCollection()); verifyReadOriginals(original.afterCollection());
        for (ExactRef locator : original.supportingEvidence()) token(locator);
    }
    private void verifyLifecycleIdentityOriginals(LifecycleIdentity original) throws IOException {
        byte[] packet = readBytes(original.nativeEvidence(), WriterContracts.MAX_PIN_BYTES);
        NativeWire.Frame received = NativeWire.decode(packet);
        if (!(received instanceof NativeWire.Snapshot snapshot) || !snapshot.snapshotId().equals(original.frame().snapshotId())
                || !snapshot.revision().equals(original.frame().nativeRevision()))
            throw new IOException("lifecycle identity differs from its actual original native snapshot");
        var state = DriverJson.object(snapshot.state().value(), DriverJson.MAX_NATIVE_BYTES);
        var current = LifecycleOriginFactory.currentPlayer(state);
        if (!current.equals(original.currentPlayer()) || LifecycleOriginFactory.deriveReason(current, original.subject().characterId()) != original.terminalReason()
                || !OpportunityJson.integer(state.get("date_raw"), "date_raw").equals(original.frame().dateRaw())
                || OpportunityJson.bool(state.get("paused"), "paused") != original.frame().paused()
                || OpportunityJson.bool(state.get("map_ready"), "map_ready") != original.frame().mapReady())
            throw new IOException("lifecycle identity changed the original native current-player token, reason or frame state");
        readBytes(original.capabilityEvidence(), WriterContracts.MAX_PIN_BYTES);
        for (ExactRef retained : original.supportingEvidence()) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
    }
    private void verifySettlementOriginals(ActionState.Settlement original) throws IOException {
        switch (original) {
            case ActionState.CompositeNoGameplayWrite terminal -> {
                // Its exact original composite guard was already verified by verifyReceiptOriginals.
                // This terminal contains no fabricated after-state or additional Native originals.
                if (!terminal.observation().execution().children().isEmpty())
                    throw new IOException("no-gameplay-write terminal cannot contain any reserved child");
            }
            case ActionState.FixtureStarted started -> verifyFixtureStartOriginals(started.observation());
            case ActionState.FixtureBusinessCompleted completed -> verifyFixtureBusinessOriginals(completed.observation());
            case ActionState.DirectFixedWindowCompleted completed -> {
                var completion = completed.completion();
                // The sole proof owns the mixed ACK/preparation, Native packet, full Driver
                // and optional later-owner READ roles. Reopen exact bytes without recasting
                // every reference as MATERIAL or issuing a sampling query during cold read.
                for (ExactRef retained : completion.references()) verifyRetainedSourceOriginal(retained);
                var decoded = org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation.Completion
                        .decode(completion.encode(this), this);
                if (!completion.equals(decoded)) throw new IOException("direct fixed-window typed proof roundtrip changed");
                // Available/owner-query semantics and canonical provenance still require
                // the identical installed archived domain callback; custody grants no effect.
            }
            case ActionState.PauseConfirmed pause -> {
                // originalEvidence is a complete native Push packet. The only supporting
                // material is the sole AdvancePrimitiveEvidence sidecar; its inner native and
                // Driver roles are replayed by that existing codec and installed frame loader.
                if (pause.observation().supportingEvidence().size() != 1)
                    throw new IOException("pause needs its sole actual complete after-frame evidence sidecar");
                verifyEffectOriginals(pause.observation());
            }
            case ActionState.ControlSequenceCompleted sequence -> {
                var observation = sequence.observation(); byte[] bytes = observation.encode();
                var decoded = org.xar.ck3.control.application.effects.control.ControlSequenceObservation.decode(bytes);
                if (!Arrays.equals(bytes, decoded.encode()))
                    throw new IOException("control sequence changed its sole canonical DATA codec roundtrip");
                // The proof is MATERIAL, not a planning READ. Other references include native
                // packets, ACK metadata and complete source inputs; never reinterpret them all
                // as JSON or manufacture a missing original while reopening the cold closure.
                for (ExactRef retained : observation.references()) verifyRetainedSourceOriginal(retained);
                loadMaterial(observation.proof());
            }
            case ActionState.OperatorRebound rebound -> {
                var completion = rebound.observation();
                byte[] encoded = completion.encode();
                if (!Arrays.equals(encoded, OperatorPlayerSwitch.decodeCompletion(encoded).encode()))
                    throw new IOException("operator completion DATA changed its sole canonical codec roundtrip");
                // Mixed source originals include framed native bytes, external immutable Driver/Aux
                // and canonical commit/proof locators. Reopen every exact original with the existing
                // same-writer native pin reader; do not invent JSON roles or private proof schemas.
                for (ExactRef retained : completion.references()) verifyRetainedSourceOriginal(retained);
                if (!(NativeWire.decode(readOriginalPacket(completion.originals().hello())) instanceof NativeWire.Hello))
                    throw new IOException("operator HELLO role differs from its original framed packet");
                loadNativeFrame(completion.originals().beforeNative());
                loadNativeFrame(completion.originals().afterNative());
                // This is the actual post-publication FullSnapshot.semantic material. It
                // includes Driver episode/one-life fields and is not a framed native packet.
                RawJson reboundSemantic = loadFullMaterial(completion.originals().reboundNative());
                var reboundNode = OpportunityJson.toNode(DriverJson.object(reboundSemantic.bytes(), RawJson.MAXIMUM_BYTES));
                OperatorPlayerSwitch.requireAfter(completion.request(), reboundNode);
                OperatorPlayerSwitch.requireRebound(completion.request(), completion.episodeRunId(), reboundNode);
                // These four roles are exact immutable JSON objects. Their actual Driver/Aux
                // schemas and source/CAS relationships belong to the sole installed publisher.
                for (ExactRef retained : List.of(completion.originals().beforeDriver(), completion.originals().afterDriver(),
                        completion.originals().beforeAuxiliary(), completion.originals().afterAuxiliary()))
                    DriverJson.object(verifyRetainedSourceOriginal(retained), RawJson.MAXIMUM_BYTES);
                var ack = load(completion.originals().ack());
                if (!(ack instanceof NativeActionPort.AckReceived)
                        || !completion.originals().ack().equals(referenceOf(ack)))
                    throw new IOException("operator ACK locator is not its canonical typed archive original");
                // The installed Root callback must replay all eleven actual roles, source/CAS/Window
                // provenance and independent post-state. Byte custody alone never grants rebind.
            }
            case ActionState.NativeSourceCompleted source -> {
                var observation = source.observation();
                // This closure includes actual code, HELLO/native and qualification bytes.
                // Reopen every original through the existing writer pin reader, not a JSON cast.
                for (ExactRef retained : observation.references()) verifyRetainedSourceOriginal(retained);
                var dispatch = load(observation.originalDispatch());
                if (!referenceOf(dispatch).equals(observation.originalDispatch()))
                    throw new IOException("native source original dispatch locator changed");
                token(observation.independentClipboard()); token(observation.afterScope()); token(observation.compatibleResult());
                // Only the installed CoA domain verifier can replay source and clipboard meaning.
            }
            case ActionState.NormalExitPhaseConfirmed phase -> {
                var observation = phase.observation();
                verifyReadOriginals(observation.beforeContext()); verifyReadOriginals(observation.afterContext());
                for (ExactRef retained : observation.references()) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
                // The sole phase codec checks both canonical read, dispatch and prepared refs.
                org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation.decode(observation.encode(this), this);
                // Domain meaning still requires the installed four-argument phase replay verifier.
            }
            case ActionState.FamilySendConfirmed sent -> {
                var observation = sent.observation();
                verifyReadOriginals(observation.beforeStorage()); verifyReadOriginals(observation.afterStorage());
                // Reopen all exact originals with their real bytes/FileID pins, including frames,
                // Driver manifests, complete preparation and both reconciliation guard closures.
                // Arbitrary preparation objects retain their original role; binary packets are
                // never reinterpreted as JSON. The fixed domain verifier owns native send matching.
                for (ExactRef retained : observation.references(this)) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
            }
            case ActionState.SwaySchedulerCompleted scheduler -> {
                // External ledger events/domain payloads retain their exact original role. Only the
                // installed same-writer Sway verifier can establish canonical publication membership.
                swayProof(scheduler.proof());
            }
            case ActionState.Applied applied -> verifyEffectOriginals(applied.observation());
            case ActionState.LifecycleControlApplied control -> {
                var observation = control.observation(); verifyLifecycleIdentityOriginals(observation.after());
                verifyReadOriginals(observation.beforeStatus()); verifyReadOriginals(observation.independentRead());
                for (ExactRef locator : observation.supportingEvidence()) token(locator);
            }
            case ActionState.NonAppliedTerminal terminal -> verifyTerminalOriginals(terminal.observation());
            case ActionState.CompositeRejected rejected -> {
                if (rejected.children().size() > 1024 || rejected.children().stream().map(child -> child.actionId()).distinct().count() != rejected.children().size())
                    throw new IOException("bounded unique original composite rejection child identities required");
                // Failure reports are existing MATERIAL originals, not Native packets or
                // successful read receipts. Reopen exact bytes under this writer's pin/hash
                // contract before producer, reference lookup, cold reader or reducer can use
                // them. Missing/drift never becomes an empty-evidence legacy rejection.
                for (ExactRef retained : rejected.evidence()) token(retained);
                // Actual canonical Head child outcomes are revalidated by the sole composite authority.
            }
            case ActionState.FrontendApplied frontend -> {
                var effect = frontend.observation();
                if (!effect.supportingEvidence().isEmpty()) {
                    readBytes(effect.originalEvidence(), WriterContracts.MAX_PIN_BYTES);
                    readBytes(effect.after().capabilityEvidence(), WriterContracts.MAX_PIN_BYTES);
                    for (ExactRef locator : effect.supportingEvidence()) token(locator);
                }
            }
            case ActionState.GameplayEntered entered -> {
                var entry = entered.observation();
                for (ExactRef retained : entry.semanticEvidence().references()) readBytes(retained, WriterContracts.MAX_PIN_BYTES);
                for (ExactRef locator : entry.supportingEvidence()) token(locator);
                verifyReadOriginals(entry.campaignRootRead());
            }
            case ActionState.LifecycleApplied lifecycle -> {
                // Proof sidecar is strict recorded data. Its ordinary external originals remain under
                // LifecycleComposites.verifyRecorded with the actual writer Head, never a material fallback.
                lifecycleProof(lifecycle.proof());
            }
            case ActionState.ControlApplied control -> {
                verifyReconciledControlOriginal(control);
                verifyReadOriginals(control.read());
                for (PlanningReadReceipt read : control.supportingReads()) verifyReadOriginals(read);
            }
            case ActionState.CompositeControlApplied control -> {
                verifyReadOriginals(control.observation().terminalStatus());
                for (PlanningReadReceipt read : control.observation().supportingReads()) verifyReadOriginals(read);
                verifyEffectOriginals(control.observation().semantic());
            }
            case ActionState.Rejected rejected -> {
                // Domain originals may be framed packets or another exact binary role, never an assumed JSON token.
                readBytes(rejected.originalEvidence(), WriterContracts.MAX_PIN_BYTES);
                // Terminal rejection eligibility is still the installed domain verifier's responsibility.
            }
        }
    }
    private static void verifySettlementParent(ActionState.Settlement settlement, ActionCommand command) {
        if (settlement instanceof ActionState.FixtureBusinessCompleted completed) completed.observation().validateParent(command);
        if (settlement instanceof ActionState.LifecycleApplied lifecycle) lifecycle.proof().validateParent(command);
        if (settlement instanceof ActionState.SwaySchedulerCompleted scheduler) scheduler.proof().validateParent(command);
    }
    private void verifyFixtureStartOriginals(FixtureStartObservation original) throws IOException {
        // Mixed Native/SEM/Driver/policy/claim/source roles remain their exact originals.
        // Custody does not create first-map, paused-pump or source/Managed qualification.
        for (ExactRef retained : original.references()) verifyRetainedSourceOriginal(retained);
        loadNativeFrame(original.firstMap().originalNativePacket());
        if (!(NativeWire.decode(readOriginalPacket(original.originalHello())) instanceof NativeWire.Hello))
            throw new IOException("fixture first-map HELLO lost its exact original packet role");
        for (ExactRef heartbeat : List.of(original.firstHeartbeat(), original.lastHeartbeat())) {
            if (!(NativeWire.decode(readOriginalPacket(heartbeat)) instanceof NativeWire.Notice notice)
                    || notice.kind() != NativeWire.NoticeKind.HEARTBEAT)
                throw new IOException("fixture first-map heartbeat lost its exact original packet role");
        }
        ExactRef read = referenceOf(original.independentRead());
        if (!original.independentRead().equals(load(read)))
            throw new IOException("fixture independent READ changed its actual archived ACK");
        byte[] encoded = StrictJson.canonical(FixtureProofCodec.start(original, this), META_LIMIT);
        if (!original.equals(FixtureProofCodec.start(StrictJson.parse(encoded, META_LIMIT), this)))
            throw new IOException("fixture first-map proof changed its sole typed codec roundtrip");
    }
    private void verifyFixtureBusinessOriginals(FixtureBusinessObservation original) throws IOException {
        var evidence = original.evidence();
        // Entry Prepared/Receipt are external canonical writer originals; they are not
        // MATERIAL aliases or action receipts. Their sole Entry authority owns semantics.
        for (ExactRef retained : original.references()) verifyRetainedSourceOriginal(retained);
        loadNativeFrame(evidence.finalSemantic().originalNativePacket());
        ExactRef start = receiptReferenceOf(evidence.originalStart());
        if (!evidence.originalStart().equals(loadReceipt(start)))
            throw new IOException("fixture business evidence changed its actual original Start receipt");
        verifyReadOriginals(evidence.campaignRootRead());
        ExactRef root = readReferenceOf(evidence.campaignRootRead());
        if (!evidence.campaignRootRead().equals(loadRead(root)))
            throw new IOException("fixture business evidence changed its original campaign-root READ");
        byte[] encoded = StrictJson.canonical(FixtureProofCodec.business(original, this), META_LIMIT);
        if (!original.equals(FixtureProofCodec.business(StrictJson.parse(encoded, META_LIMIT), this)))
            throw new IOException("fixture business proof changed its sole typed codec roundtrip");
    }
    private static RawJson swayProof(SwaySchedulerCompletion proof) throws IOException {
        byte[] encoded = Objects.requireNonNull(proof).encode();
        byte[] decoded = SwaySchedulerCompletionCodec.decodeRecorded(encoded).encode();
        if (!Arrays.equals(encoded, decoded)) throw new IOException("Sway scheduler recorded proof canonical roundtrip changed");
        return new RawJson(encoded);
    }
    private static RawJson lifecycleProof(LifecycleTransitionProof proof) throws IOException {
        byte[] encoded = Objects.requireNonNull(proof).encode();
        byte[] decoded = LifecycleProofCodec.decodeRecorded(encoded).encode();
        if (!Arrays.equals(encoded, decoded)) throw new IOException("lifecycle recorded proof canonical roundtrip changed");
        return new RawJson(encoded);
    }
    @Override public ExactRef preserveMaterial(RawJson original) { return unchecked(() -> writing(() -> token(Objects.requireNonNull(original), true))); }
    @Override public RawJson loadMaterial(ExactRef original) { return unchecked(() -> token(Objects.requireNonNull(original))); }
    /** Explicit complete Driver/auxiliary DATA only. Borrow the same writer and existing
     * canonical original reader; never broaden ordinary/native JSON or infer Known/Ready. */
    @Override public RawJson loadFullMaterial(ExactRef original) {
        return unchecked(() -> writing(() -> RawJson.fullMaterial(
                readBytes(Objects.requireNonNull(original), RawJson.MAXIMUM_BYTES))));
    }
    @Override public ExactRef materialReferenceOf(RawJson original) { return unchecked(() -> token(Objects.requireNonNull(original), false)); }
    @Override public ExactRef materialReference(String sha256, long bytes) {
        return unchecked(() -> writing(() -> {
            Pin pin = artifacts.referenceOf(sha256, bytes, RawJson.MAXIMUM_BYTES);
            // Reopen the actual committed original under this writer, and validate its JSON token.
            // A digest naming a framed packet is not a material lookup; no external sidecar is read.
            token(pin.reference()); var held = activeSession();
            if (held == null) throw new IOException("material lookup lost its original writer session");
            held.verifyPin(pin); return pin.reference();
        }));
    }
    @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) {
        return unchecked(() -> writing(() -> {
            Objects.requireNonNull(original); NativeWire.Frame decoded = NativeWire.decode(original.originalPacket());
            if (!(decoded instanceof NativeWire.Snapshot snapshot) || !snapshot.snapshotId().equals(original.snapshotId())
                    || !snapshot.revision().equals(original.nativeRevision()) || !Arrays.equals(snapshot.state().value(), original.state().bytes()))
                throw new IOException("observed frame must retain its exact original snapshot packet");
            return packet(original.originalPacket(), true);
        }));
    }
    @Override public byte[] loadNativeFrame(ExactRef original) {
        return unchecked(() -> {
            byte[] bytes = readBytes(Objects.requireNonNull(original), WriterContracts.MAX_PIN_BYTES);
            if (!(NativeWire.decode(bytes) instanceof NativeWire.Snapshot)) throw new IOException("original archived state_snapshot required"); return bytes;
        });
    }
    /** Original HELLO/Snapshot/HEARTBEAT packet custody only; no source, runtime or observer qualification. */
    @Override public byte[] readOriginalPacket(ExactRef original) {
        return unchecked(() -> writing(() -> {
            byte[] bytes = readBytes(Objects.requireNonNull(original), WriterContracts.MAX_PIN_BYTES);
            NativeWire.Frame frame = NativeWire.decode(bytes);
            if (!(frame instanceof NativeWire.Hello || frame instanceof NativeWire.Snapshot
                    || frame instanceof NativeWire.Notice notice && notice.kind() == NativeWire.NoticeKind.HEARTBEAT))
                throw new IOException("original archive packet must retain its exact HELLO, state_snapshot or HEARTBEAT role");
            return bytes;
        }));
    }
}

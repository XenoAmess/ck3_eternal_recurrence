package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/**
 * Two original direct close calls retain a separately sampled, unchanged SEM.
 * This is finite execution DATA, never ordinary Applied, a newly published native frame,
 * gameplay credit, or permission to retry an UNKNOWN command.
 */
public final class NativeDirectFixedWindowObservation implements NativeEffectRegistry.Observer {
    public static final String SCHEMA = "xar.java.army-direct-fixed-window-completion/v1";
    public static final String BASIS_SCHEMA = "xar.java.army-direct-fixed-window-original/v1";
    public static final String RESOLUTION_SCHEMA = "xar.java.army-direct-fixed-window-owner-resolution/v1";
    private static final String PROFILE = "DIRECT_FIXED_WINDOW";
    private static final Set<String> BASIS_FIELDS = Set.of("schema", "profile", "action_id", "command_body_sha256",
            "request_id", "dispatch", "prepared", "before", "after", "sampling");
    private final NativeEffectSnapshots snapshots;
    private final Optional<PlanningReadPort> reads;
    private final Optional<java.util.function.Function<ArmyWarWindowReads.Selection, ArmyWarWindowReads.Queries>> routes;
    @FunctionalInterface public interface OwnerQueryAuthority {
        /** The actual installed Root verifies its private issuer/token, original lease, same writer and sampled Known. */
        void requireCurrent(DirectFixedWindowQueryContinuation token, ActionReceipt pending, Complete currentAtRead,
                ReadContract<?> contract, RootReadContractCatalog catalog, ActionPorts.OutcomeArchive boundArchive) throws java.io.IOException;
    }
    private Optional<OwnerQueryAuthority> ownerQueryAuthority = Optional.empty();
    private final ThreadLocal<CapturedOwnerQuery> capturedOwnerQuery = new ThreadLocal<>();
    private static final class CapturedOwnerQuery {
        private final Original original; private boolean consumed;
        private CapturedOwnerQuery(Original original) { this.original = original; }
    }
    public enum Resolution { DIRECT_AVAILABLE, LATER_OWNER_QUERY_RESOLVED }

    public NativeDirectFixedWindowObservation(NativeEffectSnapshots snapshots) {
        this.snapshots = Objects.requireNonNull(snapshots);
        this.reads = Optional.empty(); this.routes = Optional.empty();
    }
    public NativeDirectFixedWindowObservation(NativeEffectSnapshots snapshots, PlanningReadPort reads,
            java.util.function.Function<ArmyWarWindowReads.Selection, ArmyWarWindowReads.Queries> routes) {
        this.snapshots = Objects.requireNonNull(snapshots); this.reads = Optional.of(Objects.requireNonNull(reads));
        this.routes = Optional.of(Objects.requireNonNull(routes));
    }
    public synchronized void bindOwnerQueryAuthority(OwnerQueryAuthority actualPrivateRootAuthority) {
        StrictJson.require(ownerQueryAuthority.isEmpty(), "one actual Root owns direct-window public-query continuation");
        ownerQueryAuthority = Optional.of(Objects.requireNonNull(actualPrivateRootAuthority));
    }
    /** DATA eligibility only; it is never a public read permit or a replacement Root private issuer. */
    public boolean acceptsOwnerQuery(ActionReceipt actualCanonicalPending) {
        if (!(actualCanonicalPending.state() instanceof ActionState.Unknown pending) || pending.evidence().isEmpty()
                || actualCanonicalPending.ack().isEmpty() || !actualCanonicalPending.ack().orElseThrow().nativeOk()) return false;
        var attempt = ActionTransitions.attempt(actualCanonicalPending.state()).orElseThrow();
        if (pending.evidence().getFirst().equals(attempt.guard().nativeEvidence())) return false;
        Original original = snapshots.loadDirectFixedWindow(actualCanonicalPending);
        return original.completion().isEmpty() && completedClose(original.observation);
    }
    /**
     * Read-only DATA eligibility for observing an old CLOSE with this already received public QUERY.
     * A different current subject/connection returns its full independent QUERY without touching the
     * old pending action. Malformed archived originals or actual query guards/custody still fail.
     * Business availability and owner ticket/pump/thread resolution remain in requireOwnerQuery.
     */
    public boolean publicQueryCanObserveOriginal(ActionReceipt pending, PlanningReadReceipt query, Complete current,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(pending); Objects.requireNonNull(query); Objects.requireNonNull(current); Objects.requireNonNull(archive);
        requireCommand(pending.command());
        var selected = kind(pending.command().operation(), ArmyOrdinaryActionArguments.decode(pending.command().arguments()));
        var operation = new OperationKey(selected.step(ArmyWindowCodec.Operation.QUERY));
        requireArchivedOwnerQuery(query, archive);
        requirePublicOwnerRead(query, current, operation);
        ArmyWindowCodec.decode(selected, ArmyWindowCodec.Operation.QUERY, query.original().originalFrame().bytes(), query.requestId(),
                new ArmyTypes.Context(current.identity(), current.source(), current.sessionId(), query.request().deadline()),
                current.connectionGeneration(), driverGeneration(current));
        var custody = query.original().custody().orElseThrow(
                () -> new IllegalArgumentException("actual public owner QUERY has no original receive custody"));
        custody.verify(query);
        if (!acceptsOwnerQuery(pending)) return false;
        Original prior = snapshots.loadDirectFixedWindow(pending);
        if (!sameLaterIdentity(prior.before.identity(), current.identity())
                || !current.source().equals(prior.before.source()) || !current.sessionId().equals(prior.before.sessionId())
                || !current.connectionGeneration().equals(prior.before.connectionGeneration())
                || !driverGeneration(current).equals(driverGeneration(prior.before))) return false;
        var original = prior.ack.custody().orElseThrow();
        if (!custody.session().equals(original.session()) || !custody.custodyEpoch().equals(original.custodyEpoch())) return false;
        NativeRequestChronology.requireSampledAfter(query, prior.attempt, prior.ack);
        return true;
    }
    /**
     * Consume an already issued actual public QUERY exactly once while the central source-owned reducer runs.
     * The default is denial. An arbitrary Known, JSON record, catalog, or callback cannot replace the installed
     * Root authority's private original-token/lease/source/Session validation.
     */
    public <T> T withCapturedOwnerQuery(DirectFixedWindowQueryContinuation token, ActionReceipt pending,
            Complete currentAtRead, RootReadContractCatalog catalog, ActionPorts.OutcomeArchive boundArchive,
            java.util.function.Supplier<T> work) throws java.io.IOException {
        Objects.requireNonNull(token); Objects.requireNonNull(pending); Objects.requireNonNull(currentAtRead);
        Objects.requireNonNull(catalog); Objects.requireNonNull(boundArchive); Objects.requireNonNull(work);
        requirePublicOwnerQuery(token.queryReceipt().request(), currentAtRead);
        OwnerQueryAuthority authority;
        synchronized (this) { authority = ownerQueryAuthority.orElseThrow(
                () -> new java.io.IOException("actual direct-window public-query issuer is not installed")); }
        StrictJson.require(capturedOwnerQuery.get() == null && token.actionId().equals(pending.command().actionId())
                && Instant.now().isBefore(token.deadline()), "nested, foreign or expired direct-window captured query");
        var args = ArmyOrdinaryActionArguments.decode(pending.command().arguments());
        var kind = kind(pending.command().operation(), args);
        var selection = new ArmyWarWindowReads.Window(kind == ArmyWindowCodec.Kind.OVERVIEW
                ? ArmyWarWindowReads.WindowKind.OVERVIEW : ArmyWarWindowReads.WindowKind.RESULTS);
        var request = ArmyWarWindowReads.Request.fromReceipt(currentAtRead, selection, token.queryReceipt(), List.of());
        ReadContract<?> contract = selectedQuery(selection).contract(request);
        authority.requireCurrent(token, pending, currentAtRead, contract, catalog, boundArchive);
        StrictJson.require(catalog.containsIdentity(contract) && contract.contractId().equals(token.queryReceipt().contractId())
                && boundArchive.readReferenceOf(token.queryReceipt()).equals(token.queryRef())
                && boundArchive.loadRead(token.queryRef()).equals(token.queryReceipt()), "captured owner query changed its installed contract or archived original");
        contract.replay(token.queryReceipt());
        Original observed = snapshots.resolveDirectFixedWindow(pending, token.queryReceipt(), currentAtRead);
        CapturedOwnerQuery captured = new CapturedOwnerQuery(observed); capturedOwnerQuery.set(captured);
        try {
            T result = work.get();
            StrictJson.require(captured.consumed, "central reducer did not consume the one actual captured owner query");
            authority.requireCurrent(token, pending, currentAtRead, contract, catalog, boundArchive); return result;
        } finally { capturedOwnerQuery.remove(); }
    }

    /** A cold interval is DATA. Only the held receiver's actual ReadSample can enter capture. */
    public record Sampling(Instant startedAt, Instant completedAt, Instant deadline, ExactRef originalNativeFrame) {
        public Sampling {
            Objects.requireNonNull(startedAt); Objects.requireNonNull(completedAt); Objects.requireNonNull(deadline);
            Objects.requireNonNull(originalNativeFrame);
            StrictJson.require(!completedAt.isBefore(startedAt) && completedAt.isBefore(deadline)
                    && originalNativeFrame.bytes() > 0, "actual snapshot sample interval/deadline differs");
        }
    }

    /** Sole re-decoded original for both successful and still-pending public results. No live authority is exposed. */
    public static final class Original {
        private final ActionCommand command;
        private final ActionState.Attempt attempt;
        private final NativeActionPort.AckReceived ack;
        private final Complete before;
        private final Optional<Complete> after;
        private final FullSnapshot sampledAfter;
        private final Sampling sampling;
        private final ArmyWindowCodec.Observation observation;
        private final ExactRef basis;
        private final List<ExactRef> originals;
        private final Optional<OwnerQueryObservation> ownerQuery;
        private Original(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
                Complete before, FullSnapshot sampledAfter, Optional<Complete> after, Sampling sampling, ArmyWindowCodec.Observation observation,
                ExactRef basis, List<ExactRef> originals) {
            this(command, attempt, ack, before, sampledAfter, after, sampling, observation, basis, originals, Optional.empty());
        }
        private Original(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
                Complete before, FullSnapshot sampledAfter, Optional<Complete> after, Sampling sampling, ArmyWindowCodec.Observation observation,
                ExactRef basis, List<ExactRef> originals, Optional<OwnerQueryObservation> ownerQuery) {
            this.command = command; this.attempt = attempt; this.ack = ack; this.before = before; this.after = after; this.sampledAfter = sampledAfter;
            this.sampling = sampling; this.observation = observation; this.basis = basis; this.originals = List.copyOf(originals);
            this.ownerQuery = ownerQuery;
        }
        public Complete before() { return before; }
        public Optional<Complete> after() { return after; }
        public FullSnapshot sampledAfter() { return sampledAfter; }
        public NativeEffectEvidence.FrameBasis sampledBasis() { return fullBasis(sampledAfter); }
        public Sampling sampling() { return sampling; }
        public ArmyWindowCodec.Observation observation() { return observation; }
        public RawJson normalized() { return new RawJson(StrictJson.canonical(observation.normalized())); }
        public ExactRef basis() { return basis; }
        public List<ExactRef> references() { return originals; }
        public Optional<OwnerQueryObservation> ownerQuery() { return ownerQuery; }
        public Optional<OwnerResolution> ownerResolution() { return ownerQuery.filter(OwnerQueryObservation::executionResolved)
                .map(value -> new OwnerResolution(value.current(), value.originalQuery(), value.normalizedQuery(), value.retryDeferredForNativeFrame())); }
        public Optional<Completion> completion() {
            Optional<OwnerResolution> ownerResolution = ownerResolution();
            if (!observation.available() && ownerResolution.isEmpty()) return Optional.empty();
            return Optional.of(new Completion(command.actionId(), ActionCodec.bodySha256(command), attempt.requestId(),
                    basis, before.identity(), ownerResolution.map(value -> value.current().identity()).orElseGet(() -> after.orElseThrow().identity()),
                    command.source(), command.sessionId(), originals, ownerResolution.isPresent()
                        ? Resolution.LATER_OWNER_QUERY_RESOLVED : Resolution.DIRECT_AVAILABLE));
        }
    }
    public record OwnerResolution(Complete current, PlanningReadReceipt originalQuery, RawJson normalizedQuery,
            boolean retryDeferredForNativeFrame) {
        public OwnerResolution { Objects.requireNonNull(current); Objects.requireNonNull(originalQuery); Objects.requireNonNull(normalizedQuery); }
    }
    public record OwnerQueryObservation(Complete current, PlanningReadReceipt originalQuery, RawJson normalizedQuery,
            boolean executionResolved, boolean retryDeferredForNativeFrame) {
        public OwnerQueryObservation {
            Objects.requireNonNull(current); Objects.requireNonNull(originalQuery); Objects.requireNonNull(normalizedQuery);
            StrictJson.require(!retryDeferredForNativeFrame || executionResolved, "a pending owner query cannot authorize a retry latch");
        }
    }

    /**
     * Canonical settlement payload, explicitly DATA. The installed archived verifier must reload the
     * original ACK, full Driver/native originals, local sample interval and sole window decoder.
     */
    public record Completion(String actionId, String commandBodySha256, String originalRequestId, ExactRef basis,
            ObservationIdentity before, ObservationIdentity after, G2Source source, String sessionId, List<ExactRef> originals,
            Resolution resolution) {
        public Completion {
            StrictJson.text(actionId); StrictJson.text(originalRequestId); StrictJson.text(sessionId);
            StrictJson.require(commandBodySha256 != null && commandBodySha256.matches("[0-9a-f]{64}"),
                    "complete original direct-close command digest required");
            Objects.requireNonNull(basis); Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(source);
            originals = List.copyOf(originals);
            Objects.requireNonNull(resolution);
            StrictJson.require(!originals.isEmpty() && originals.size() <= 64 && originals.getFirst().equals(basis)
                    && new LinkedHashSet<>(originals).size() == originals.size(), "finite explicit original direct-close closure required");
            if (resolution == Resolution.DIRECT_AVAILABLE) requireFixedIdentity(before, after);
            else requireLaterIdentity(before, after);
        }
        public List<ExactRef> references() { return originals; }
        public void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch) {
            requireCommand(command);
            StrictJson.require(command.actionId().equals(actionId) && ActionCodec.bodySha256(command).equals(commandBodySha256)
                    && command.before().equals(before) && command.source().equals(source) && command.sessionId().equals(sessionId)
                    && attempt.requestId().equals(originalRequestId) && dispatch.requestId().equals(originalRequestId),
                    "direct-close completion changed the original command/attempt/source/session");
            StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk(),
                    "direct-close completion requires its actual successful ACK");
            requireAck(command, attempt, (NativeActionPort.AckReceived) dispatch);
        }
        public void validate(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.DispatchOutcome dispatch,
                ActionPorts.OutcomeArchive archive) {
            validate(command, attempt, dispatch);
            ObjectNode row = archived(basis, archive);
            requireHeader(command, attempt, row);
            StrictJson.require(archive.referenceOf(dispatch).equals(ExactRef.fromJson(row.get("dispatch")))
                    && archive.requestReferenceOf(attempt.preparedRequest()).equals(ExactRef.fromJson(row.get("prepared")))
                    && NativeDirectFixedWindowObservation.references(row, basis, archive).equals(originals)
                    && resolution == NativeDirectFixedWindowObservation.resolution(row), "direct-close completion original closure/variant differs");
        }
        public ObjectNode encode(ActionPorts.OutcomeArchive archive) {
            ObjectNode retained = archived(basis, archive);
            StrictJson.require(actionId.equals(StrictJson.text(retained.get("action_id")))
                    && commandBodySha256.equals(StrictJson.text(retained.get("command_body_sha256")))
                    && originalRequestId.equals(StrictJson.text(retained.get("request_id")))
                    && NativeDirectFixedWindowObservation.references(retained, basis, archive).equals(originals) && resolution == NativeDirectFixedWindowObservation.resolution(retained),
                    "direct-close DATA differs from its original basis");
            ObjectNode row = StrictJson.object().put("schema", SCHEMA).put("action_id", actionId)
                    .put("command_body_sha256", commandBodySha256).put("original_request_id", originalRequestId).put("session_id", sessionId)
                    .put("resolution", resolution.name());
            row.set("basis", basis.toJson()); row.set("before", ProposalLifecycleCodec.observation(before));
            row.set("after", ProposalLifecycleCodec.observation(after)); row.set("source", ProposalLifecycleCodec.source(source));
            var refs = row.putArray("originals"); originals.forEach(ref -> refs.add(ref.toJson())); return row;
        }
        public static Completion decode(JsonNode input, ActionPorts.OutcomeArchive archive) {
            ObjectNode row = StrictJson.object(input, Set.of("schema", "action_id", "command_body_sha256", "original_request_id",
                    "session_id", "basis", "before", "after", "source", "originals", "resolution"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact direct-close completion schema required");
            JsonNode refs = row.get("originals"); StrictJson.require(refs.isArray() && refs.size() <= 64, "finite direct-close originals required");
            List<ExactRef> originals = new ArrayList<>(); refs.forEach(ref -> originals.add(ExactRef.fromJson(ref)));
            Completion value = new Completion(StrictJson.text(row.get("action_id")), StrictJson.text(row.get("command_body_sha256")),
                    StrictJson.text(row.get("original_request_id")), ExactRef.fromJson(row.get("basis")),
                    ProposalLifecycleCodec.decodeObservation(row.get("before")), ProposalLifecycleCodec.decodeObservation(row.get("after")),
                    G2Wire.source(row.get("source")), StrictJson.text(row.get("session_id")), originals,
                    Resolution.valueOf(StrictJson.text(row.get("resolution"))));
            value.encode(archive); return value;
        }
    }

    public static ExpectedPostcondition expected(ObservationIdentity before, G2Source source, OperationKey operation, RawJson arguments) {
        var decoded = ArmyOrdinaryActionArguments.decode(arguments);
        ArmyWindowCodec.Kind kind = kind(operation, decoded);
        var selected = (ArmyCalls.Frame) ArmyCallCodec.decode(kind == ArmyWindowCodec.Kind.OVERVIEW
                ? PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1 : PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1, decoded.publicArguments());
        StrictJson.require(selected.revision().value() instanceof ArmyTypes.Present<java.math.BigInteger> revision
                && revision.value().signum() > 0 && revision.value().equals(before.frame().revision()),
                "direct fixed-window requires the actual positive public revision");
        return new ExpectedPostcondition(1, before, source, SCHEMA, List.of(
                new ExpectedText(new FieldKey("operation"), operation.value()),
                new ExpectedText(new FieldKey("window"), kind == ArmyWindowCodec.Kind.OVERVIEW ? "war_declared_overview" : "war_results"),
                new ExpectedBoolean(new FieldKey("native_execution_completed"), true),
                new ExpectedBoolean(new FieldKey("war_outcome_observed"), false)));
    }

    @Override public NativeEffectRegistry.Projected observe(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.DispatchOutcome dispatch) {
        requireCommand(command);
        CapturedOwnerQuery captured = capturedOwnerQuery.get();
        if (captured != null) {
            Original actual = captured.original;
            StrictJson.require(!captured.consumed && actual.command.equals(command) && actual.attempt.equals(attempt)
                    && actual.ack.equals(dispatch), "captured owner query escaped its sole original command/attempt/ACK callback");
            captured.consumed = true; return projected(actual);
        }
        if (!(dispatch instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk())
            return NativeEffectRegistry.Projected.pending("direct fixed-window call has no successful original native result; no after sample is invented",
                    List.of(attempt.guard().nativeEvidence()));
        Optional<ActionReceipt> pending = snapshots.pendingDirectFixedWindow(command, attempt);
        Original original = pending.map(snapshots::loadDirectFixedWindow).orElseGet(() -> snapshots.readDirectFixedWindow(command, attempt, ack));
        if (pending.isPresent() && original.completion().isEmpty() && completedClose(original.observation)
                && reads.isPresent() && routes.isPresent()) {
            try {
                Complete current = ActionReconciliationScope.requireFrame(command, attempt);
                var identity = ActionReconciliationScope.requireIdentity(command, attempt);
                var selection = new ArmyWarWindowReads.Window(original.observation.kind() == ArmyWindowCodec.Kind.OVERVIEW
                        ? ArmyWarWindowReads.WindowKind.OVERVIEW : ArmyWarWindowReads.WindowKind.RESULTS);
                var query = selectedQuery(selection);
                var result = query.read(reads.orElseThrow(), new ArmyWarWindowReads.Request(current, selection,
                        ActionObservationWindow.deadline(command), Optional.of(identity), List.of()));
                if (result instanceof PlanningReadResult.Known<?> known)
                    original = snapshots.resolveDirectFixedWindow(pending.orElseThrow(), known.receipt(), current);
            } catch (java.io.IOException unavailable) {
                throw new java.io.UncheckedIOException("actual original direct-window owner query is unavailable", unavailable);
            }
        }
        return projected(original);
    }
    private static NativeEffectRegistry.Projected projected(Original original) {
        if (original.completion().isEmpty())
            return NativeEffectSnapshots.withDirectFixedWindowEvidence(NativeEffectRegistry.Projected.pending(
                    "original direct fixed-window result remains unavailable or verification_pending; never resend", List.of()), original);
        return new NativeEffectRegistry.Projected(new ActionPorts.DirectFixedWindowObserved(original.completion().orElseThrow()),
                Optional.of(original.normalized()));
    }

    public void verifyArchived(ActionReceipt receipt) {
        Original original = snapshots.loadDirectFixedWindow(receipt);
        if (receipt.state() instanceof ActionState.Unknown) {
            StrictJson.require(original.completion().isEmpty(), "available original cannot masquerade as pending direct-close evidence"); return;
        }
        StrictJson.require(receipt.state() instanceof ActionState.Settled settled
                && settled.settlement() instanceof ActionState.DirectFixedWindowCompleted,
                "direct fixed-window original is not its explicit finite completion");
        var recorded = ((ActionState.DirectFixedWindowCompleted) ((ActionState.Settled) receipt.state()).settlement()).completion();
        StrictJson.require(original.completion().filter(recorded::equals).isPresent(), "replayed direct-close completion differs from canonical DATA");
        original.ownerResolution().ifPresent(owner -> {
            var selection = new ArmyWarWindowReads.Window(original.observation.kind() == ArmyWindowCodec.Kind.OVERVIEW
                    ? ArmyWarWindowReads.WindowKind.OVERVIEW : ArmyWarWindowReads.WindowKind.RESULTS);
            var replay = selectedQuery(selection).replay(ArmyWarWindowReads.Request.fromReceipt(owner.current(), selection,
                    owner.originalQuery(), List.of()), owner.originalQuery());
            ObjectNode normalized = EffectJson.object(EffectJson.parse(owner.normalizedQuery()));
            normalized.remove(List.of("prior_close_execution_observation", "close_retry_deferred_for_native_frame"));
            StrictJson.require(EffectJson.parse(replay.normalized()).equals(normalized), "later owner query differs from the same installed original producer replay");
        });
    }
    public Original original(ActionReceipt receipt) { return snapshots.loadDirectFixedWindow(receipt); }
    private ArmyWarWindowReads.Query<?> selectedQuery(ArmyWarWindowReads.Window selection) {
        var actual = Objects.requireNonNull(routes.orElseThrow(
                () -> new IllegalStateException("actual direct-window registered query routes are absent")).apply(selection));
        return selection.window() == ArmyWarWindowReads.WindowKind.OVERVIEW ? actual.overview() : actual.results();
    }

    /** Called only after the real held port issued and checked its ReadSample. Not a generic Complete constructor. */
    static Original capture(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
            Complete before, FullSnapshot sampledAfter, NativeSnapshotWaitPort.SampleData actualSample, Instant deadline,
            ActionPorts.OutcomeArchive archive) {
        requireCommand(command); requireAck(command, attempt, ack);
        ArmyWindowCodec.Observation observation = decode(command, attempt, ack, before);
        Optional<Complete> after = requireSampledFrames(command, attempt, before, sampledAfter, observation);
        Objects.requireNonNull(actualSample);
        var packet = actualSample.frame();
        StrictJson.require(packet.session().machineId().equals(sampledAfter.actual().session().machineId())
                && packet.session().game().equals(sampledAfter.actual().session().game()) && packet.session().sessionId().equals(sampledAfter.actual().session().sessionId())
                && packet.session().connectionGeneration().equals(sampledAfter.actual().session().connectionGeneration())
                && packet.snapshotId().equals(sampledAfter.actual().snapshotId())
                && packet.nativeRevision().equals(sampledAfter.actual().nativeRevision())
                && packet.observedAt().equals(sampledAfter.actual().observedAt()), "sampled original packet differs from the actual assembled after frame");
        RootGuardChecks.exact(sampledAfter.originalEvidence(), packet.originalPacket());
        Sampling interval = new Sampling(actualSample.startedAt(), actualSample.completedAt(), deadline, sampledAfter.originalEvidence());
        requireInterval(attempt, ack, interval, sampledAfter);
        ExactRef dispatch = archive.referenceOf(ack), prepared = archive.requestReferenceOf(attempt.preparedRequest());
        StrictJson.require(archive.load(dispatch).equals(ack) && archive.loadRequest(prepared).equals(attempt.preparedRequest()),
                "direct close has no exact original archived ACK/preparation");
        ObjectNode row = StrictJson.object().put("schema", BASIS_SCHEMA).put("profile", PROFILE).put("action_id", command.actionId())
                .put("command_body_sha256", ActionCodec.bodySha256(command)).put("request_id", attempt.requestId());
        row.set("dispatch", dispatch.toJson()); row.set("prepared", prepared.toJson());
        row.set("before", frameJson(NativeEffectEvidence.basis(before))); row.set("after", frameJson(fullBasis(sampledAfter)));
        row.set("sampling", samplingJson(interval));
        RawJson body = EffectJson.raw(row); ExactRef basis = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(basis)), "durable direct-close basis changed during preservation");
        List<ExactRef> closure = references(row, basis, archive); verifyFrames(row, archive);
        return new Original(command, attempt, ack, before, sampledAfter, after, interval, observation, basis, closure);
    }

    /** Mandatory cold DATA reader. It performs no current observation, submission, replay or qualification. */
    public static Original load(ActionReceipt receipt, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        Objects.requireNonNull(receipt); Objects.requireNonNull(archive); Objects.requireNonNull(frames);
        ActionCommand command = receipt.command(); requireCommand(command);
        ActionState.Attempt attempt = ActionTransitions.attempt(receipt.state()).orElseThrow(
                () -> new IllegalArgumentException("direct-close original attempt is absent"));
        var dispatch = ActionTransitions.dispatch(receipt.state()).orElseThrow(
                () -> new IllegalArgumentException("direct-close original dispatch is absent"));
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack && ack.nativeOk(),
                "direct-close original had no successful native result and no after basis");
        var ack = (NativeActionPort.AckReceived) dispatch;
        List<ExactRef> evidence;
        if (receipt.state() instanceof ActionState.Unknown pending) evidence = pending.evidence();
        else {
            StrictJson.require(receipt.state() instanceof ActionState.Settled settled
                    && settled.settlement() instanceof ActionState.DirectFixedWindowCompleted,
                    "ordinary/other settlement cannot authorize direct fixed-window evidence");
            evidence = ((ActionState.DirectFixedWindowCompleted) ((ActionState.Settled) receipt.state()).settlement()).completion().references();
        }
        StrictJson.require(!evidence.isEmpty(), "original direct-close after sampling evidence is absent");
        ExactRef basis = evidence.getFirst(); ObjectNode row = archived(basis, archive); requireHeader(command, attempt, row);
        StrictJson.require(archive.referenceOf(ack).equals(ExactRef.fromJson(row.get("dispatch")))
                && archive.requestReferenceOf(attempt.preparedRequest()).equals(ExactRef.fromJson(row.get("prepared"))),
                "direct-close outer original basis changed its actual ACK/preparation references");
        Original original;
        if (resolution(row) == Resolution.LATER_OWNER_QUERY_RESOLVED) {
            ExactRef initial = ExactRef.fromJson(row.get("original_basis"));
            Original prior = loadInitial(command, attempt, ack, initial, archive, frames);
            PlanningReadReceipt query = archive.loadRead(ExactRef.fromJson(row.get("owner_query")));
            Complete current = frames.load(frame(row.get("current")), archive);
            OwnerQueryObservation owner = requireOwnerQuery(prior, query, current, archive);
            original = new Original(command, attempt, ack, prior.before, prior.sampledAfter, prior.after, prior.sampling,
                    prior.observation, basis, references(row, basis, archive), Optional.of(owner));
        } else original = loadInitial(command, attempt, ack, basis, archive, frames);
        if (receipt.state() instanceof ActionState.Unknown)
            StrictJson.require(evidence.equals(List.of(basis)), "pending direct-close basis closure changed");
        else StrictJson.require(evidence.equals(original.references()), "completed direct-close evidence closure changed");
        return original;
    }

    private static Original loadInitial(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack,
            ExactRef basis, ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        ObjectNode row = archived(basis, archive); requireHeader(command, attempt, row);
        StrictJson.require(resolution(row) == Resolution.DIRECT_AVAILABLE, "owner-query resolution cannot recursively replace original close sampling");
        StrictJson.require(archive.load(ExactRef.fromJson(row.get("dispatch"))).equals(ack)
                && archive.referenceOf(ack).equals(ExactRef.fromJson(row.get("dispatch")))
                && archive.loadRequest(ExactRef.fromJson(row.get("prepared"))).equals(attempt.preparedRequest())
                && archive.requestReferenceOf(attempt.preparedRequest()).equals(ExactRef.fromJson(row.get("prepared"))),
                "direct-close original ACK/preparation changed");
        verifyFrames(row, archive);
        Complete before = frames.load(frame(row.get("before")), archive);
        StrictJson.require(frames instanceof DriverFrameEvidenceLoader, "full sampled after replay requires the sole original Driver frame loader");
        FullSnapshot sampledAfter = ((DriverFrameEvidenceLoader) frames).loadFull(frame(row.get("after")), archive);
        requireAck(command, attempt, ack);
        ArmyWindowCodec.Observation observation = decode(command, attempt, ack, before);
        Optional<Complete> after = requireSampledFrames(command, attempt, before, sampledAfter, observation);
        Sampling interval = sampling(row.get("sampling")); requireInterval(attempt, ack, interval, sampledAfter);
        List<ExactRef> closure = references(row, basis, archive);
        return new Original(command, attempt, ack, before, sampledAfter, after, interval, observation, basis, closure);
    }

    /** One later registered owner QUERY can clear execution uncertainty; it never alters the original CLOSE result. */
    public static Original resolvePending(ActionReceipt pending, PlanningReadReceipt query, Complete current,
            ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        StrictJson.require(pending.state() instanceof ActionState.Unknown, "owner query requires the original canonical unresolved close");
        Original prior = load(pending, archive, frames);
        OwnerQueryObservation owner = requireOwnerQuery(prior, query, current, archive);
        ObjectNode row = StrictJson.object().put("schema", RESOLUTION_SCHEMA).put("profile", PROFILE)
                .put("action_id", pending.command().actionId()).put("command_body_sha256", pending.bodySha256())
                .put("request_id", prior.attempt.requestId());
        row.set("dispatch", archive.referenceOf(prior.ack).toJson()); row.set("prepared", archive.requestReferenceOf(prior.attempt.preparedRequest()).toJson());
        ExactRef initial = resolution(archived(prior.basis, archive)) == Resolution.DIRECT_AVAILABLE ? prior.basis
                : ExactRef.fromJson(archived(prior.basis, archive).get("original_basis"));
        row.set("original_basis", initial.toJson()); row.set("owner_query", archive.readReferenceOf(query).toJson());
        row.set("current", frameJson(NativeEffectEvidence.basis(current)));
        RawJson body = EffectJson.raw(row); ExactRef basis = archive.preserveMaterial(body);
        StrictJson.require(body.equals(archive.loadMaterial(basis)), "later owner-query original basis changed during preservation");
        return new Original(prior.command, prior.attempt, prior.ack, prior.before, prior.sampledAfter, prior.after,
                prior.sampling, prior.observation, basis, references(row, basis, archive), Optional.of(owner));
    }

    private static void requireCommand(ActionCommand command) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay
                && command.expected().equals(expected(command.before(), command.source(), command.operation(),
                    new RawJson(org.xar.ck3.control.application.driver.DriverJson.encode(command.arguments())))),
                "explicit direct-close expected/profile/before/source differs");
    }
    private static ArmyWindowCodec.Kind kind(OperationKey operation, ArmyOrdinaryActionArguments args) {
        StrictJson.require(args.executionProfile() == ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW
                && args.preflightReads().isEmpty() && args.automaticSurrender().isEmpty(), "ordinary window call cannot borrow direct same-frame evidence");
        ArmyWindowCodec.Kind kind = switch (operation.value()) {
            case "close-war-declared-overview-v1" -> ArmyWindowCodec.Kind.OVERVIEW;
            case "close-war-results-window-v1" -> ArmyWindowCodec.Kind.RESULTS;
            default -> throw new IllegalArgumentException("not one of the two original fixed-window close operations");
        };
        StrictJson.require(args.kind() == (kind == ArmyWindowCodec.Kind.OVERVIEW
                ? ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1 : ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1),
                "direct-close operation and selected kind differ");
        ArmyCallCodec.decode(kind == ArmyWindowCodec.Kind.OVERVIEW ? PublicMethod.CLOSE_WAR_DECLARED_OVERVIEW_V1
                : PublicMethod.CLOSE_WAR_RESULTS_WINDOW_V1, args.publicArguments()); return kind;
    }
    private static ArmyWindowCodec.Observation decode(ActionCommand command, ActionState.Attempt attempt,
            NativeActionPort.AckReceived ack, Complete before) {
        ArmyWindowCodec.Kind kind = kind(command.operation(), ArmyOrdinaryActionArguments.decode(command.arguments()));
        var context = new ArmyTypes.Context(before.identity(), before.source(), before.sessionId(), command.deadline());
        ArmyWindowCodec.Observation result = ArmyWindowCodec.decode(kind, ArmyWindowCodec.Operation.CLOSE,
                ack.originalFrame().bytes(), attempt.requestId(), context, before.connectionGeneration(), driverGeneration(before));
        var top = StrictJson.parse(ack.originalFrame().bytes());
        StrictJson.require(ack.originalResultToken().isPresent()
                && StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()).equals(top.get("result")),
                "actual direct-close result token differs from its complete original TOP");
        return result;
    }
    private static void requireAck(ActionCommand command, ActionState.Attempt attempt, NativeActionPort.AckReceived ack) {
        StrictJson.require(ack.nativeOk() && ack.requestId().equals(attempt.requestId())
                && attempt.preparedRequest().step().equals(command.operation().value())
                && attempt.guard().observed().equals(command.before()) && attempt.guard().source().equals(command.source())
                && attempt.guard().sessionId().equals(command.sessionId()), "direct-close ACK crossed its original operation/attempt/guard");
        NativeStepDiscriminator.requireRequest(command.operation(), ExecutableStepBindings.Kind.ACTION, attempt.preparedRequest());
        NativeRequestChronology chronology = ack.custody().orElseThrow(
                () -> new IllegalArgumentException("direct-close original ACK lacks actual write/receive custody"));
        chronology.verify(ack, attempt.guard());
        byte[] packet = ack.originalPacket(), originalBody = ack.originalFrame().bytes();
        StrictJson.require(packet.length == originalBody.length + 4
                && java.nio.ByteBuffer.wrap(packet, 0, 4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt() == originalBody.length
                && java.util.Arrays.equals(java.util.Arrays.copyOfRange(packet, 4, packet.length), originalBody),
                "direct-close original TOP differs from its exact retained native response packet");
        StrictJson.require(attempt.preparedRequest().additionalFields().objectFieldNames().isEmpty(),
                "direct fixed-window native preparation has no arbitrary additional fields");
        byte[] outgoing = ack.outbound().orElseThrow().originalPacket();
        StrictJson.require(outgoing.length > 4 && java.nio.ByteBuffer.wrap(outgoing, 0, 4)
                .order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt() == outgoing.length - 4,
                "direct-close original outbound length prefix differs");
        ObjectNode request = StrictJson.object(StrictJson.parse(java.util.Arrays.copyOfRange(outgoing, 4, outgoing.length)),
                Set.of("type", "protocol_version", "request_id", "step", "expected_revision"));
        StrictJson.require("execute_step".equals(StrictJson.text(request.get("type")))
                && request.get("protocol_version").isIntegralNumber() && request.get("protocol_version").bigIntegerValue().equals(java.math.BigInteger.ONE)
                && attempt.requestId().equals(StrictJson.text(request.get("request_id")))
                && command.operation().value().equals(StrictJson.text(request.get("step")))
                && request.get("expected_revision").isIntegralNumber()
                && request.get("expected_revision").bigIntegerValue().equals(command.before().frame().identity().nativeRevision()),
                "direct-close actual native request differs from its prepared original command/native revision");
        StrictJson.require(!chronology.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "direct-close actual request predates its canonical attempt");
    }
    private static void requireFixedIdentity(ObservationIdentity before, ObservationIdentity after) {
        StrictJson.require(before.equals(after), "direct fixed-window sample changed snapshot/revision/native/date/Game/player/episode identity");
    }
    private static Optional<Complete> requireSampledFrames(ActionCommand command, ActionState.Attempt attempt, Complete before,
            FullSnapshot after, ArmyWindowCodec.Observation observation) {
        StrictJson.require(before.identity().equals(command.before()) && before.source().equals(command.source())
                && before.sessionId().equals(command.sessionId()) && before.originalEvidence().equals(attempt.guard().nativeEvidence())
                && before.connectionGeneration().equals(attempt.guard().connectionGeneration()), "direct-close before frame differs from original command guard");
        StrictJson.require(before.source().equals(after.facts().source()) && before.identity().machineId().equals(after.actual().session().machineId())
                && before.identity().game().equals(after.actual().session().game())
                && before.sessionId().equals(after.actual().session().sessionId())
                && before.connectionGeneration().equals(after.actual().session().connectionGeneration()),
                "direct-close sample crossed source/Game/session/HELLO connection");
        var projected = new DriverObservationAssembler().assemble(after.actual(), after.facts(), after.originalEvidence());
        Optional<Complete> complete = projected instanceof Complete value ? Optional.of(value) : Optional.empty();
        requirePausedMapLease(before);
        if (scopeTransition(observation)) return complete;
        StrictJson.require(complete.isPresent(), "ordinary direct-window after sample did not produce its actual Complete");
        Complete current = complete.orElseThrow(); requireFixedIdentity(before.identity(), current.identity());
        StrictJson.require(driverGeneration(before).equals(driverGeneration(current)), "same-frame direct-window Driver connection lease changed");
        requirePausedMapLease(current);
        return complete;
    }
    private static void requirePausedMapLease(Complete actual) {
        var semantic = actual.semantic();
        var json = org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(semantic);
        StrictJson.require(json.path("paused").isBoolean() && json.path("paused").booleanValue()
                && json.path("map_ready").isBoolean() && json.path("map_ready").booleanValue()
                && json.path("played_character").path("alive").isBoolean() && json.path("played_character").path("alive").booleanValue(),
                "direct-window original lease requires a living paused native map");
        JsonNode hello = json.path("diagnostics").path("hello");
        StrictJson.require(hello.isObject() && hello.path("expected_ck3_version").isTextual()
                && "1.20.0.4".equals(hello.get("expected_ck3_version").textValue())
                && hello.path("expected_ck3_sha256").isTextual()
                && "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518".equalsIgnoreCase(hello.get("expected_ck3_sha256").textValue()),
                "direct-window original lease has no exact actual .4 native HELLO build");
        var generation = org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.object(semantic.get("diagnostics"), "diagnostics").get("hello")
                    instanceof org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj bound ? bound.get("connection_generation") : null,
                "actual HELLO connection_generation");
        StrictJson.require(generation.signum() > 0 && generation.equals(actual.connectionGeneration()),
                "actual semantic HELLO generation differs from the sampled held receiver");
    }
    private static boolean scopeTransition(ArmyWindowCodec.Observation observation) {
        ObjectNode row = observation.leaf();
        return observation.kind() == ArmyWindowCodec.Kind.RESULTS && !observation.available()
                && "verification_pending".equals(observation.status()) && row.path("dispatch_attempted").asBoolean()
                && row.path("dispatch_invoked").asBoolean() && row.path("native_handled").asBoolean()
                && "callback_returned".equals(row.path("dismiss_stage").asText())
                && row.path("dismiss_exception_code").isIntegralNumber() && row.path("dismiss_exception_code").bigIntegerValue().signum() == 0
                && row.path("unavailable_reason").asText().startsWith("war_results_ui_scope_transition;");
    }
    private static boolean completedClose(ArmyWindowCodec.Observation observation) {
        ObjectNode row = observation.leaf();
        String stage = observation.kind() == ArmyWindowCodec.Kind.OVERVIEW ? "close_stage" : "dismiss_stage";
        boolean common = !observation.available() && "verification_pending".equals(observation.status())
                && !row.path("accepted").asBoolean() && "callback_returned".equals(row.path(stage).asText())
                && row.path("dispatch_invoked").asBoolean() && row.path("native_handled").asBoolean();
        if (!common) return false;
        boolean stable = row.path("scope_unchanged").asBoolean() && row.path("post_observed").asBoolean();
        return observation.kind() == ArmyWindowCodec.Kind.OVERVIEW ? stable
                : row.path("dismiss_exception_code").isIntegralNumber() && row.path("dismiss_exception_code").bigIntegerValue().signum() == 0
                    && (stable || scopeTransition(observation));
    }
    private static void requireLaterIdentity(ObservationIdentity before, ObservationIdentity after) {
        StrictJson.require(sameLaterIdentity(before, after),
                "later owner query crossed the original Game/actor/episode or regressed native revision/day");
    }
    private static boolean sameLaterIdentity(ObservationIdentity before, ObservationIdentity after) {
        return before.machineId().equals(after.machineId()) && before.game().equals(after.game())
                && before.observationVersion() == after.observationVersion()
                && before.frame().identity().player().equals(after.frame().identity().player())
                && before.frame().episodeRunId().equals(after.frame().episodeRunId())
                && after.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0
                && after.frame().identity().dateRaw().compareTo(before.frame().identity().dateRaw()) >= 0;
    }
    private static void requireArchivedOwnerQuery(PlanningReadReceipt query, ActionPorts.OutcomeArchive archive) {
        NativeRecordedEvidenceVerifier.requireRead(query, archive);
        StrictJson.require(archive.loadRead(archive.readReferenceOf(query)).equals(query), "later owner query is not its exact archived original");
    }
    private static void requirePublicOwnerRead(PlanningReadReceipt query, Complete current, OperationKey operation) {
        requirePublicOwnerQuery(query.request(), current);
        StrictJson.require(query.request().operation().equals(operation), "later owner query changed its selected window operation");
        for (var guard : List.of(query.before(), query.after()))
            StrictJson.require(guard.binding().observed().equals(current.identity())
                    && guard.binding().source().equals(current.source()) && guard.binding().sessionId().equals(current.sessionId())
                    && guard.binding().connectionGeneration().equals(current.connectionGeneration())
                    && guard.binding().nativeEvidence().equals(current.originalEvidence())
                    && guard.originalBindingSha256().equals(current.fullBindingSha256()),
                    "later ordinary owner query changed its full actual Native/Driver/source guard");
    }
    private static OwnerQueryObservation requireOwnerQuery(Original prior, PlanningReadReceipt query, Complete current,
            ActionPorts.OutcomeArchive archive) {
        StrictJson.require(completedClose(prior.observation) && prior.ownerResolution().isEmpty(),
                "only a completed original verification_pending callback accepts one later owner query");
        requireArchivedOwnerQuery(query, archive);
        ArmyWindowCodec.Kind kind = prior.observation.kind(); OperationKey operation = new OperationKey(kind.step(ArmyWindowCodec.Operation.QUERY));
        if (query.request().origin() instanceof CommandOrigin.Reconciliation)
            NativeEffectSnapshots.requireAfterRead(prior.command, prior.attempt, current, query, operation);
        else requirePublicOwnerRead(query, current, operation);
        NativeRequestChronology.requireSampledAfter(query, prior.attempt, prior.ack);
        requireLaterIdentity(prior.before.identity(), current.identity());
        StrictJson.require(current.source().equals(prior.before.source()) && current.sessionId().equals(prior.before.sessionId())
                && current.connectionGeneration().equals(prior.before.connectionGeneration()), "later owner query crossed original source/session/connection");
        var decoded = ArmyWindowCodec.decode(kind, ArmyWindowCodec.Operation.QUERY, query.original().originalFrame().bytes(),
                query.requestId(), new ArmyTypes.Context(current.identity(), current.source(), current.sessionId(), query.request().deadline()),
                current.connectionGeneration(), driverGeneration(current));
        ObjectNode row = decoded.normalized(), old = prior.observation.owner(), owner = decoded.owner();
        boolean resolved = decoded.available() && row.path("post_observed").asBoolean() && row.path("scope_unchanged").asBoolean()
                && row.get("queried_connection_generation").equals(prior.observation.normalized().get("queried_connection_generation"))
                && owner.get("ticket_sequence").bigIntegerValue().compareTo(old.get("ticket_sequence").bigIntegerValue()) > 0
                && owner.get("pump_epoch").bigIntegerValue().compareTo(old.get("pump_epoch").bigIntegerValue()) > 0
                && owner.get("thread_id").equals(old.get("thread_id"));
        boolean visible = row.get("post_effective_visible").booleanValue();
        boolean deferred = resolved && visible && current.identity().frame().identity().nativeRevision().equals(prior.before.identity().frame().identity().nativeRevision())
                && current.identity().frame().identity().dateRaw().equals(prior.before.identity().frame().identity().dateRaw());
        if (!resolved) return new OwnerQueryObservation(current, query, EffectJson.raw(row), false, false);
        ObjectNode previous = row.putObject("prior_close_execution_observation");
        previous.put("native_request_id", prior.attempt.requestId()).put("status", "callback_completed_closure_unverified")
                .put("followup_query_request_id", query.requestId()).put("fresh_window_visible", visible)
                .put("original_action_replayed", false).put("close_action_credit", false);
        previous.set("original_owner_receipt", old);
        row.put("close_retry_deferred_for_native_frame", deferred);
        return new OwnerQueryObservation(current, query, EffectJson.raw(row), true, deferred);
    }
    /**
     * Public QUERY DATA must retain its original Gameplay request. A separately scheduled Recon read
     * remains valid only in its own reconciliation path and cannot stand in for this public call.
     * This check issues no read lease, journal transition or private continuation permission.
     */
    public static void requirePublicOwnerQuery(PlanningReadRequest request, Complete current) {
        Objects.requireNonNull(request); Objects.requireNonNull(current);
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay
                && request.before().equals(current.identity()) && request.source().equals(current.source())
                && request.sessionId().equals(current.sessionId())
                && java.util.Arrays.stream(ArmyWindowCodec.Kind.values()).anyMatch(kind ->
                    kind.step(ArmyWindowCodec.Operation.QUERY).equals(request.operation().value())),
                "public owner QUERY requires its actual Gameplay request/frame/source/session and window operation");
    }
    private static java.math.BigInteger driverGeneration(Complete actual) {
        return ArmyWindowCodec.driverGeneration(actual);
    }
    private static NativeEffectEvidence.FrameBasis fullBasis(FullSnapshot full) {
        var value = full.semantic().get("java_driver_facts_evidence");
        StrictJson.require(value != null && value != org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,
                "full sampled Driver facts original is absent");
        return new NativeEffectEvidence.FrameBasis(full.originalEvidence(), DriverObservationEvidenceReader.reference(value));
    }
    private static void requireInterval(ActionState.Attempt attempt, NativeActionPort.AckReceived ack, Sampling sample, FullSnapshot after) {
        NativeRequestChronology custody = ack.custody().orElseThrow();
        StrictJson.require(!sample.startedAt().isBefore(custody.responseReceived().observedAt())
                && !sample.startedAt().isBefore(attempt.submittedAt()) && sample.originalNativeFrame().equals(after.originalEvidence()),
                "independent retained snapshot was not sampled after the original ACK or changed its accepted packet");
        StrictJson.require(custody.session().machineId().equals(after.actual().session().machineId())
                && custody.session().game().equals(after.actual().session().game()) && custody.session().sessionId().equals(after.actual().session().sessionId())
                && custody.session().connectionGeneration().equals(after.actual().session().connectionGeneration()), "direct-close sample and ACK came from different held receivers");
    }
    private static ObjectNode archived(ExactRef ref, ActionPorts.OutcomeArchive archive) {
        RawJson raw = archive.loadMaterial(ref); RootGuardChecks.exact(ref, raw.bytes());
        ObjectNode parsed = EffectJson.object(EffectJson.parse(raw));
        String schema = StrictJson.text(parsed.get("schema"));
        ObjectNode row = StrictJson.object(parsed, BASIS_SCHEMA.equals(schema) ? BASIS_FIELDS
                : Set.of("schema", "profile", "action_id", "command_body_sha256", "request_id", "dispatch", "prepared", "original_basis", "owner_query", "current"));
        StrictJson.require((BASIS_SCHEMA.equals(schema) || RESOLUTION_SCHEMA.equals(schema)) && PROFILE.equals(StrictJson.text(row.get("profile"))),
                "exact explicit direct fixed-window original profile required"); return row;
    }
    private static void requireHeader(ActionCommand command, ActionState.Attempt attempt, ObjectNode row) {
        StrictJson.require(command.actionId().equals(StrictJson.text(row.get("action_id")))
                && ActionCodec.bodySha256(command).equals(StrictJson.text(row.get("command_body_sha256")))
                && attempt.requestId().equals(StrictJson.text(row.get("request_id"))), "direct-close original basis crossed its canonical command/attempt");
    }
    private static ObjectNode frameJson(NativeEffectEvidence.FrameBasis basis) {
        ObjectNode row = StrictJson.object(); row.set("native_frame", basis.nativeFrame().toJson()); row.set("driver_facts", basis.driverFacts().toJson()); return row;
    }
    private static NativeEffectEvidence.FrameBasis frame(JsonNode input) {
        ObjectNode row = StrictJson.object(input, Set.of("native_frame", "driver_facts"));
        return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")), ExactRef.fromJson(row.get("driver_facts")));
    }
    private static ObjectNode samplingJson(Sampling value) {
        ObjectNode row = StrictJson.object().put("started_at", value.startedAt().toString()).put("completed_at", value.completedAt().toString())
                .put("deadline", value.deadline().toString()); row.set("original_native_frame", value.originalNativeFrame().toJson()); return row;
    }
    private static Sampling sampling(JsonNode input) {
        ObjectNode row = StrictJson.object(input, Set.of("started_at", "completed_at", "deadline", "original_native_frame"));
        return new Sampling(Instant.parse(StrictJson.text(row.get("started_at"))), Instant.parse(StrictJson.text(row.get("completed_at"))),
                Instant.parse(StrictJson.text(row.get("deadline"))), ExactRef.fromJson(row.get("original_native_frame")));
    }
    private static void verifyFrames(ObjectNode row, ActionPorts.OutcomeArchive archive) {
        for (var basis : List.of(frame(row.get("before")), frame(row.get("after")))) {
            RootGuardChecks.exact(basis.nativeFrame(), archive.loadNativeFrame(basis.nativeFrame()));
            RootGuardChecks.exact(basis.driverFacts(), archive.loadFullMaterial(basis.driverFacts()).bytes());
        }
    }
    private static List<ExactRef> references(ObjectNode row, ExactRef basis, ActionPorts.OutcomeArchive archive) {
        var refs = new LinkedHashSet<ExactRef>(); refs.add(basis); refs.add(ExactRef.fromJson(row.get("dispatch")));
        refs.add(ExactRef.fromJson(row.get("prepared")));
        if (resolution(row) == Resolution.LATER_OWNER_QUERY_RESOLVED) {
            ExactRef original = ExactRef.fromJson(row.get("original_basis")); ObjectNode old = archived(original, archive);
            StrictJson.require(resolution(old) == Resolution.DIRECT_AVAILABLE, "later owner-query evidence cannot form a recursive basis");
            refs.addAll(references(old, original, archive));
            ExactRef queryRef = ExactRef.fromJson(row.get("owner_query")); refs.add(queryRef);
            PlanningReadReceipt query = archive.loadRead(queryRef);
            StrictJson.require(archive.readReferenceOf(query).equals(queryRef), "later owner-query receipt reference changed");
            for (var guard : List.of(query.before().binding(), query.after().binding())) {
                refs.add(guard.nativeEvidence()); refs.add(guard.capabilityEvidence()); refs.addAll(guard.supportingEvidence());
            }
            addFrameReferences(refs, frame(row.get("current")), archive);
            StrictJson.require(refs.size() <= 64, "complete direct-window original closure exceeds its finite DATA bound");
            return List.copyOf(refs);
        }
        for (var original : List.of(frame(row.get("before")), frame(row.get("after")))) {
            addFrameReferences(refs, original, archive);
        }
        return List.copyOf(refs);
    }
    private static void addFrameReferences(LinkedHashSet<ExactRef> refs, NativeEffectEvidence.FrameBasis frame,
            ActionPorts.OutcomeArchive archive) {
        refs.add(frame.nativeFrame()); refs.add(frame.driverFacts());
        RawJson manifest = archive.loadFullMaterial(frame.driverFacts()); RootGuardChecks.exact(frame.driverFacts(), manifest.bytes());
        ExactRef driver = DriverObservationEvidenceReader.currentDriverReference(frame.driverFacts(), manifest);
        RootGuardChecks.exact(driver, archive.loadFullMaterial(driver).bytes()); refs.add(driver);
    }
    private static Resolution resolution(ObjectNode row) {
        return RESOLUTION_SCHEMA.equals(StrictJson.text(row.get("schema"))) ? Resolution.LATER_OWNER_QUERY_RESOLVED : Resolution.DIRECT_AVAILABLE;
    }
}

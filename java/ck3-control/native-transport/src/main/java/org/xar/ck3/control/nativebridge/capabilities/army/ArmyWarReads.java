package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import java.util.EnumMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Finite real native war reads over the sole held Root read port. Exit preview stays production-disabled. */
public final class ArmyWarReads {
    public static final Set<PublicMethod> METHODS = Set.of(PublicMethod.QUERY_DECLARABLE_WARS,
            PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1, PublicMethod.QUERY_WAR_TERMINATION_OPTIONS,
            PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS, PublicMethod.QUERY_WAR_TERMINATION_TERMS,
            PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2, PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1);
    /** Created only by redecoding an actual successful declaration receipt, not caller-authored selected facts. */
    public static final class DeclarationLease {
        private final ArmyRetreatFrames.Current before;
        private final ArmyWarReadCodec.Declarations declarations;
        private final ExactRef evidence;
        private final Optional<PlanningReadResult.Known<ArmyWarReadCodec.Observation>> originalRead;
        private DeclarationLease(ArmyRetreatFrames.Current before, ArmyWarReadCodec.Declarations declarations, ExactRef evidence) {
            this(before,declarations,evidence,Optional.empty());
        }
        private DeclarationLease(ArmyRetreatFrames.Current before, ArmyWarReadCodec.Declarations declarations, ExactRef evidence,
                Optional<PlanningReadResult.Known<ArmyWarReadCodec.Observation>> originalRead) {
            this.before = before; this.declarations = declarations; this.evidence = evidence; this.originalRead=Objects.requireNonNull(originalRead);
        }
        /** Returns the actual central Known retained by live publication or canonical activation; a pure detached replay cannot mint one. */
        public PlanningReadResult.Known<ArmyWarReadCodec.Observation> originalRead() {
            return originalRead.orElseThrow(() -> new IllegalStateException("detached declaration replay has no retained central Known"));
        }
        public static DeclarationLease from(Selection original, PlanningReadResult.Known<ArmyWarReadCodec.Observation> read) {
            require(original.input().method() == PublicMethod.QUERY_DECLARABLE_WARS, "declaration lease requires original query");
            var decoded = ArmyWarReadCodec.decode(scope(original, read.receipt().request()), read.receipt());
            require(decoded.equals(read.value()) && decoded instanceof ArmyWarReadCodec.Declarations, "declaration lease differs from actual original read");
            return new DeclarationLease(original.frame(), (ArmyWarReadCodec.Declarations) decoded, read.originalReceipt(),Optional.of(read));
        }
        public ArmyWarReadCodec.Declarations value() { return declarations; }
        public ExactRef evidence() { return evidence; }
        public DeclarationContract.Choice selected(ArmyRetreatFrames.Current current, String id) {
            ArmyRetreatFrames.same(before, current);
            return declarations.choices().stream().filter(choice -> choice.declarationId().equals(id)).findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("selected declaration absent from the same-frame current source"));
        }
        private Obj proof(ArmyRetreatFrames.Current current) {
            ArmyRetreatFrames.same(before, current); ObjectNode snapshot = parse(OpportunityJson.encode(current.actual().semantic()));
            snapshot.set("declarable_wars", DeclarationContract.encode(declarations.choices()));
            return DriverJson.object(bytes(snapshot), DriverJson.MAX_NATIVE_BYTES);
        }
    }
    public record IndependentDependencies(ArmyForecastReads forecasts, DriverReadHistoryPublisher history) {
        public IndependentDependencies { Objects.requireNonNull(forecasts); Objects.requireNonNull(history); }
    }
    /** Only this owner can mint it, after the sole publisher returns the actual archived independent Known. */
    public static final class IndependentAssessmentLease {
        private final ArmyRetreatFrames.Current before;
        private final String declarationId;
        private final PrewarPartialCodec.IndependentSource expected;
        private final ExactRef originalEvidence;
        private IndependentAssessmentLease(ArmyRetreatFrames.Current before, String declarationId, PrewarPartialCodec.IndependentSource expected, ExactRef originalEvidence) {
            this.before = before; this.declarationId = declarationId; this.expected = expected; this.originalEvidence = originalEvidence;
        }
        public ExactRef evidence() { return originalEvidence; }
        public PrewarPartialCodec.IndependentSource expected(ArmyRetreatFrames.Current current, String selectedId) {
            ArmyRetreatFrames.same(before, current); require(declarationId.equals(selectedId), "independent source selected another declaration"); return expected;
        }
    }
    public record Selection(ArmyCalls.Call input, ArmyRetreatFrames.Current frame, Optional<DeclarationLease> declarations,
            Optional<IndependentAssessmentLease> independentAssessment) {
        public Selection {
            Objects.requireNonNull(input); Objects.requireNonNull(frame); Objects.requireNonNull(declarations); Objects.requireNonNull(independentAssessment);
            require(METHODS.contains(input.method()), "no complete native war read for method");
            input.revision().requireCurrent(frame.context().before().frame().revision());
            if (input instanceof ArmyCalls.Declaration declaration) {
                declarations.orElseThrow(() -> new IllegalArgumentException("actual declaration lease required")).selected(frame, declaration.declarationId());
                if (input.method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1)
                    independentAssessment.orElseThrow(() -> new IllegalArgumentException("actual same-frame independent assessment lease required")).expected(frame, declaration.declarationId());
            }
        }
        public Selection(ArmyCalls.Call input, ArmyRetreatFrames.Current frame, Optional<DeclarationLease> declarations) {
            this(input, frame, declarations, Optional.empty());
        }
        public Context context() { return frame.context(); }
    }
    /** One producer retains the original sent request for both public and planner callers. */
    public record PendingDeclaration(Selection selection, ReadContract<ArmyWarReadCodec.Observation> contract,
            PlanningReadRequest request, NativeActionPort.Unknown originalUnknown, Duration originalTimeout,
            Optional<PlanningReadCoordinator.OriginalRead<ArmyWarReadCodec.Observation>> originalRead,
            Optional<NativeActionPort.AckReceived> resultFrame) {
        public PendingDeclaration {
            Objects.requireNonNull(selection); Objects.requireNonNull(contract); Objects.requireNonNull(request); Objects.requireNonNull(originalUnknown); Objects.requireNonNull(originalTimeout); Objects.requireNonNull(originalRead); Objects.requireNonNull(resultFrame);
            require(!originalTimeout.isZero() && !originalTimeout.isNegative(), "actual original declaration timeout required");
            require(selection.input().method() == PublicMethod.QUERY_DECLARABLE_WARS && originalUnknown.originalRequestPacket().length > 0
                    && contract.operation().equals(request.operation()), "pending declaration requires the actual original sent query");
        }
        /** Historical data-only test custody cannot mint a central late-adoption ticket. */
        public PendingDeclaration(Selection selection, ReadContract<ArmyWarReadCodec.Observation> contract,
                PlanningReadRequest request, NativeActionPort.Unknown originalUnknown, Duration originalTimeout) {
            this(selection,contract,request,originalUnknown,originalTimeout,Optional.empty(),Optional.empty());
        }
        private PendingDeclaration retain(NativeActionPort.AckReceived actual) {
            return new PendingDeclaration(selection,contract,request,originalUnknown,originalTimeout,originalRead,Optional.of(actual));
        }
    }
    private PendingDeclaration pendingDeclaration;
    public synchronized Optional<PendingDeclaration> pendingDeclaration() { return Optional.ofNullable(pendingDeclaration); }
    /** The original actual Root read link proves which one custody store is being inspected. */
    public synchronized Optional<PendingDeclaration> pendingDeclaration(PlanningReadPort actualOwner) {
        require(reads == Objects.requireNonNull(actualOwner), "pending declaration diagnostics crossed the actual Root read producer");
        return Optional.ofNullable(pendingDeclaration);
    }
    public synchronized void requirePendingDeclarationUnchanged(PlanningReadPort actualOwner, Optional<PendingDeclaration> captured) {
        require(reads == Objects.requireNonNull(actualOwner) && pendingDeclaration == Objects.requireNonNull(captured).orElse(null),
                "original declaration custody changed during diagnostic readback");
    }
    private final EnumMap<PublicMethod, RootReadContractCatalog.Family<Selection,ArmyWarReadCodec.Observation>> families = new EnumMap<>(PublicMethod.class);
    private final PlanningReadPort reads;
    private DeclarationLease publishedDeclarations;
    private final Optional<Supplier<IndependentDependencies>> independent;
    public ArmyWarReads(ExactRef definition, ExactRef decoder, PlanningReadPort actualRootReads) {
        this(definition, decoder, actualRootReads, Optional.empty());
    }
    public ArmyWarReads(ExactRef definition, ExactRef decoder, PlanningReadPort actualRootReads, IndependentDependencies actualIndependent) {
        this(definition, decoder, actualRootReads, fixed(actualIndependent));
    }
    /** Menu-time installation defers the once-bound publisher until the dependent query owns its real writer. */
    public ArmyWarReads(ExactRef definition, ExactRef decoder, PlanningReadPort actualRootReads, Supplier<IndependentDependencies> actualIndependent) {
        this(definition, decoder, actualRootReads, Optional.of(Objects.requireNonNull(actualIndependent)));
    }
    private static Optional<Supplier<IndependentDependencies>> fixed(IndependentDependencies actual) {
        Objects.requireNonNull(actual); return Optional.of(() -> actual);
    }
    private ArmyWarReads(ExactRef definition, ExactRef decoder, PlanningReadPort actualRootReads, Optional<Supplier<IndependentDependencies>> independent) {
        this.independent = independent;
        reads = Objects.requireNonNull(actualRootReads); Objects.requireNonNull(definition); Objects.requireNonNull(decoder);
        for (PublicMethod method : METHODS) {
            Optional<String> capability = switch (method) {
                case QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1, QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1 -> Optional.empty();
                case QUERY_DECLARABLE_WARS -> Optional.of("game.command.query-declarable-wars");
                case QUERY_WAR_OCCUPATION_TARGETS_V1 -> Optional.of("game.command.query-war-occupation-targets-v1-N");
                case QUERY_WAR_TERMINATION_OPTIONS -> Optional.of("game.command.query-war-termination-options-N");
                case QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS -> Optional.of("game.command.query-outbound-war-white-peace-status-v1-N");
                case QUERY_WAR_TERMINATION_TERMS -> Optional.of("game.command.query-war-termination-terms-v1-N");
                case QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2 -> Optional.of("game.command.query-prewar-force-coalition-coverage-v2-N");
                default -> throw new IllegalArgumentException("unregistered war read");
            };
            families.put(method, new RootReadContractCatalog.Family<>("army-war-" + method.pythonName(), Selection.class, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    capability, definition, decoder, s -> key(s), s -> operation(s, method), s -> {
                        var primitive = primitive(s, method);
                        return new ReadContract<>("army-war-" + method.pythonName() + "-" + ArmyReadKey.digest(key(s)),
                                operation(s, method), capability, primitive.permissionKey(), capability.isPresent() ? ReadContract.PermissionMode.ADVERTISED_CAPABILITY : ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                                primitive.wire(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definition, (request, requestId) -> { verify(request, s); return primitive.request(); },
                                receipt -> { verify(receipt.request(), s); return ArmyWarReadCodec.decode(scope(s, receipt.request()), receipt); },
                                receipt -> { verify(receipt.request(), s); return ArmyWarReadCodec.decode(scope(s, receipt.request()), receipt); },
                                (original, value, current, semantic) -> {
                                    if (method != PublicMethod.QUERY_DECLARABLE_WARS) {
                                        require(original.request().equals(current), "this war read has no cross-request canonical reuse predicate"); return;
                                    }
                                    verify(original.request(), s); verify(current, s);
                                    ArmyNativeReadEvidence.requireCanonicalEquivalent(original, current);
                                    var replayed = ArmyWarReadCodec.decode(scope(s, original.request()), original);
                                    require(replayed instanceof ArmyWarReadCodec.Declarations && replayed.equals(value),
                                            "canonical declarations differ from the sole complete original decoder");
                                });
                    }));
        }
    }
    /** Actual current source only; changed frame invalidates the old detached lease. Caller holds the original writer for planning. */
    public synchronized Optional<DeclarationLease> currentDeclarations(ArmyRetreatFrames.Current current) {
        if (publishedDeclarations == null) return Optional.empty();
        try { ArmyRetreatFrames.same(publishedDeclarations.before, current); return Optional.of(publishedDeclarations); }
        catch (IllegalArgumentException stale) { publishedDeclarations = null; return Optional.empty(); }
    }
    public synchronized DeclarationLease requireCurrentDeclarations(ArmyRetreatFrames.Current current) {
        return currentDeclarations(current).orElseThrow(() -> new IllegalStateException("actual current declarable query has not been published"));
    }
    /** Cold per-command reconstruction after the caller resolves the exact installed query and original before-frame. No Known, cache publication or Native query is created. */
    public static DeclarationLease replayDeclarationLease(Selection original, PlanningReadReceipt receipt, ExactRef expected,
            ActionPorts.OutcomeArchive sameArchive) {
        Objects.requireNonNull(original); Objects.requireNonNull(receipt); Objects.requireNonNull(expected); Objects.requireNonNull(sameArchive);
        require(original.input().method() == PublicMethod.QUERY_DECLARABLE_WARS, "cold declaration lease requires the actual original query");
        require(sameArchive.readReferenceOf(receipt).equals(expected) && sameArchive.loadRead(expected).equals(receipt), "cold declaration receipt differs from its original immutable archive reference");
        verify(receipt.request(), original);
        var decoded = ArmyWarReadCodec.decode(scope(original, receipt.request()), receipt);
        require(decoded instanceof ArmyWarReadCodec.Declarations, "cold declaration source did not decode the complete declaration result");
        return new DeclarationLease(original.frame(), (ArmyWarReadCodec.Declarations) decoded, expected);
    }
    /** Same callback after an original late read is centrally adopted. Never creates Known, a new query or a request ID. */
    public synchronized void publishOriginal(Selection original, PlanningReadResult.Known<ArmyWarReadCodec.Observation> known) {
        require(original.input().method() == PublicMethod.QUERY_DECLARABLE_WARS, "only original declaration query can publish the declaration cache");
        verify(known.receipt().request(), original);
        if (pendingDeclaration != null) {
            var pending = pendingDeclaration;
            require(pending.selection().equals(original) && pending.request().equals(known.receipt().request())
                    && pending.originalUnknown().requestId().equals(known.receipt().requestId())
                    && pending.contract().contractId().equals(known.receipt().contractId()),
                    "another read cannot replace the retained original unknown declaration query");
        }
        var lease = DeclarationLease.from(original, known);
        publishedDeclarations = lease; pendingDeclaration = null;
    }
    public List<RootReadContractCatalog.Family<?,?>> families() { return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(f -> f).toList(); }
    /** Effects must use this issued contract and this exact decoder for both live and archived results. */
    public ReadContract<ArmyWarReadCodec.Observation> contract(RootReadContractCatalog catalog, Selection selection) {
        return catalog.issue(Objects.requireNonNull(families.get(selection.input().method())), selection);
    }
    public PlanningReadResult<ArmyWarReadCodec.Observation> read(ContinuityStorePort.Session borrowed, RootReadContractCatalog catalog, Selection selection) {
        var contract = contract(catalog, selection);
        return read(borrowed, contract, selection);
    }
    public synchronized PlanningReadResult<ArmyWarReadCodec.Observation> read(ContinuityStorePort.Session borrowed, ReadContract<ArmyWarReadCodec.Observation> contract, Selection selection) {
        require(selection.input().method() != PublicMethod.QUERY_DECLARABLE_WARS, "declaration query requires its actual requested timeout before dispatch");
        return readOriginal(borrowed, contract, selection, Optional.empty());
    }
    /** The actual caller supplies the timeout it requested, before any read/permit/Native submission. */
    public synchronized PlanningReadResult<ArmyWarReadCodec.Observation> read(ContinuityStorePort.Session borrowed, ReadContract<ArmyWarReadCodec.Observation> contract, Selection selection, Duration actualRequestedTimeout) {
        Objects.requireNonNull(actualRequestedTimeout);
        require(selection.input().method() == PublicMethod.QUERY_DECLARABLE_WARS && !actualRequestedTimeout.isZero() && !actualRequestedTimeout.isNegative(),
                "finite positive actual declaration timeout required");
        return readOriginal(borrowed, contract, selection, Optional.of(actualRequestedTimeout));
    }
    private PlanningReadResult<ArmyWarReadCodec.Observation> readOriginal(ContinuityStorePort.Session borrowed, ReadContract<ArmyWarReadCodec.Observation> contract, Selection selection, Optional<Duration> actualRequestedTimeout) {
        boolean declarationQuery = selection.input().method() == PublicMethod.QUERY_DECLARABLE_WARS;
        require(!declarationQuery || pendingDeclaration == null, "original declaration query is pending; collect its original request without resubmission");
        Context c = selection.context(); var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), contract.operation(), arguments(selection.input()), c.deadline());
        PlanningReadAttempt<ArmyWarReadCodec.Observation> attempt = declarationQuery ? reads.readOriginal(borrowed,contract,request) : null;
        var result = declarationQuery ? Objects.requireNonNull(attempt).result() : reads.read(borrowed, contract, request);
        if (declarationQuery && result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known) publishOriginal(selection, known);
        else if (declarationQuery && result instanceof PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation> unavailable
                && unavailable.original().orElse(null) instanceof NativeActionPort.Unknown unknown)
            pendingDeclaration = new PendingDeclaration(selection, contract, request, unknown, actualRequestedTimeout.orElseThrow(),
                    Objects.requireNonNull(attempt).original(),Optional.empty());
        return result;
    }
    /** The sole pending lock covers nonblocking original-result delivery, first retention, validation and cache publication. */
    public synchronized ArmyDeclarationCollection.Result collectOriginal(ContinuityStorePort.Session same, ArmyCalls.Collect input,
            Complete current, Instant deadline) throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(current);Objects.requireNonNull(deadline);
        input.revision().requireCurrent(current.identity().frame().revision());
        require(pendingDeclaration!=null,"no pending declarable query for this request_id");
        var pending=pendingDeclaration;
        require(pending.originalUnknown().requestId().equals(input.requestId()),"no pending declarable query for this request_id");
        var before=pending.selection().frame().actual();
        require(before.source().equals(current.source()) && before.sessionId().equals(current.sessionId())
                && before.identity().machineId().equals(current.identity().machineId()) && before.identity().game().equals(current.identity().game()),
                "original UNKNOWN collection crossed its actual Root source/Game/session");
        verify(pending.request(),pending.selection());
        var ticket=pending.originalRead().orElseThrow(() -> new IllegalStateException("original central read ticket is unavailable; UNKNOWN cannot be adopted or replayed"));
        if(pending.resultFrame().isEmpty()) {
            var arrived=reads.pollOriginal(same,ticket);
            if(arrived.isPresent()) {
                pending=pending.retain(arrived.orElseThrow());
                pendingDeclaration=pending; // Transport pop must never lose an original response when later validation throws.
            }
        }
        var scope=new ArmyDeclarationCollection.Scope(input.requestId(),ArmyDeclarationCollectionCodec.binding(before),ArmyDeclarationCollectionCodec.binding(current));
        if(!scope.current()) {
            var result=new ArmyDeclarationCollection.Stale(scope,pending.resultFrame().map(ArmyDeclarationCollection::originalFrame));
            pendingDeclaration=null;return result;
        }
        if(pending.resultFrame().isEmpty())return new ArmyDeclarationCollection.Pending(scope);
        var ack=pending.resultFrame().orElseThrow();
        require(ack.requestId().equals(input.requestId()),"late declarable result request identity mismatch");
        var original=ArmyDeclarationCollection.originalFrame(ack);
        if(!ArmyDeclarationCollectionCodec.requireFrame(input.requestId(),original)) {
            var result=new ArmyDeclarationCollection.NativeRejected(scope,original);pendingDeclaration=null;return result;
        }
        var actualRequest=new PlanningReadRequest(current.identity(),current.source(),current.sessionId(),pending.request().operation(),pending.request().arguments(),deadline);
        var adopted=reads.adoptOriginal(same,ticket,ack,actualRequest,current.semantic());
        if(!(adopted instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known))
            throw new IllegalStateException(((PlanningReadResult.Unavailable<ArmyWarReadCodec.Observation>)adopted).reason());
        require(known.value() instanceof ArmyWarReadCodec.Declarations,"late original did not decode complete declarations");
        var result=new ArmyDeclarationCollection.Available(scope,original,(ArmyWarReadCodec.Declarations)known.value());
        publishOriginal(pending.selection(),known);
        return result;
    }
    public static Obj arguments(ArmyCalls.Call call) { return OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(call).bytes()), "actual war read arguments"); }
    /** V1 consumes actual canonical history only. Missing evidence never triggers a prerequisite Native query. */
    public Selection selection(ContinuityStorePort.Session same, RootReadContractCatalog catalog, ArmyCalls.Call call, ArmyRetreatFrames.Current frame) throws IOException {
        Optional<DeclarationLease> declarations = currentDeclarations(frame);
        if (call instanceof ArmyCalls.Declaration && declarations.isEmpty() && independent.isPresent())
            declarations = canonicalDeclarations(same, catalog, frame);
        if (call.method() != PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1) return new Selection(call, frame, declarations);
        var sources = independentSources();
        require(sources.history().catalog() == catalog, "independent source crossed the installed Root catalog");
        var declaration = (ArmyCalls.Declaration) call; var lease = declarations.orElseThrow(() -> new IllegalStateException("actual current declarations unavailable"));
        var selected = lease.selected(frame, declaration.declarationId()); int requested = selected.targetCharacterId().intValueExact();
        var inquiry = new ArmyCalls.WarEntry(new ArmyCalls.Revision(new Present<>(frame.context().before().frame().revision())), List.of(new PositiveId(requested)));
        var forecastSelection = new ArmyForecastReads.Selection(inquiry, frame.context()); var contract = sources.forecasts().contract(catalog, forecastSelection);
        Context c = frame.context(); var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), contract.operation(), arguments(inquiry), c.deadline());
        var witness = sources.history().canonicalReadWitness(same, contract, request).orElseThrow(() -> new IllegalStateException("independent current war-entry assessment is unavailable; no prerequisite query was sent"));
        var known = witness.requireCurrent(same, contract, request);
        var replayed = witness.originalContract().replay(known.receipt());
        require(replayed.equals(known.value()) && known.value() instanceof ForecastReadObservation.WarEntry, "independent cached value differs from its sole original decoder");
        var observed = (ForecastReadObservation.WarEntry) replayed; var target = observed.singleTarget();
        require(target.requested() == requested && !BigInteger.valueOf(target.effective()).equals(c.playerId()), "independent assessment target differs or collapses to actor");
        ObjectNode normalized = object(OpportunityJson.toNode(observed.normalizedResult())); equal(get(normalized, "status"), "available");
        equal(get(normalized, "queried_snapshot_id"), c.before().frame().snapshotId()); equal(get(normalized, "queried_revision"), c.before().frame().revision());
        equal(get(normalized, "queried_native_revision"), c.nativeRevision());
        ObjectNode provenance = object(get(object(OpportunityJson.toNode(observed.assessments())), "provenance"));
        equal(get(provenance, "game_version"), "1.20.0.4");
        require(text(get(provenance, "executable_sha256")).equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"), "independent assessment belongs to another exact build");
        var expected = new PrewarPartialCodec.IndependentSource(lease.value().querySequence(), positive(get(normalized, "query_sequence")), new PositiveId(requested), new PositiveId(target.effective()));
        return new Selection(call, frame, declarations, Optional.of(new IndependentAssessmentLease(frame, declaration.declarationId(), expected, known.originalReceipt())));
    }
    private IndependentDependencies independentSources() {
        return Objects.requireNonNull(independent.orElseThrow(() -> new IllegalStateException("actual independent forecast/history owners are not installed")).get(),
                "actual independent forecast/history owners are unavailable");
    }
    /** Canonical history supplies the unchanged original value; its sole owner rechecks it inside this same writer. */
    public synchronized Optional<DeclarationLease> canonicalDeclarations(ContinuityStorePort.Session same,
            RootReadContractCatalog catalog, ArmyRetreatFrames.Current current) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(catalog); Objects.requireNonNull(current);
        var sources = independentSources();
        require(sources.history().catalog() == catalog, "declaration history crossed the identical installed Root catalog");
        var input = new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,
                new ArmyCalls.Revision(new Present<>(current.context().before().frame().revision())));
        var selection = new Selection(input, current, Optional.empty()); var installed = contract(catalog, selection);
        Context c = current.context(); var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), installed.operation(), arguments(input), c.deadline());
        var candidate = sources.history().canonicalReadWitness(same, installed, request);
        if (candidate.isEmpty()) return Optional.empty();
        var witness = candidate.orElseThrow(); var known = witness.requireCurrent(same, installed, request);
        var replayed = witness.originalContract().replay(known.receipt());
        require(replayed instanceof ArmyWarReadCodec.Declarations && replayed.equals(known.value()),
                "canonical declaration witness differs from its identical original decoder");
        ArmyNativeReadEvidence.requireCanonicalEquivalent(known.receipt(), request);
        publishedDeclarations = new DeclarationLease(current, (ArmyWarReadCodec.Declarations) replayed, known.originalReceipt(),Optional.of(known));
        return Optional.of(publishedDeclarations);
    }
    public static ArmyWarReadCodec.Scope scope(Selection selection) { return scope(selection, null); }
    public static ArmyWarReadCodec.Scope scope(Selection selection, PlanningReadRequest originalRequest) {
        Optional<DeclarationContract.Choice> choice = selection.input() instanceof ArmyCalls.Declaration declaration
                ? Optional.of(selection.declarations().orElseThrow().selected(selection.frame(), declaration.declarationId())) : Optional.empty();
        Obj snapshot = choice.isPresent() ? selection.declarations().orElseThrow().proof(selection.frame()) : selection.frame().actual().semantic();
        Optional<PrewarPartialCodec.IndependentSource> independent = selection.input().method() == PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1
                ? Optional.of(selection.independentAssessment().orElseThrow().expected(selection.frame(), ((ArmyCalls.Declaration) selection.input()).declarationId())) : Optional.empty();
        Context context = originalRequest == null ? selection.context() : ArmyNativeReadEvidence.contextForRequest(selection.context(), originalRequest);
        return new ArmyWarReadCodec.Scope(selection.input(), context, snapshot, choice, independent);
    }
    private static ArmyNativeRecipes.Primitive primitive(Selection selection, PublicMethod method) {
        require(selection.input().method() == method, "war family method differs");
        ArmyNativeRecipes.SelectedFacts facts = new ArmyNativeRecipes.NoFacts();
        if (selection.input() instanceof ArmyCalls.Declaration declaration) {
            var lease = selection.declarations().orElseThrow(); var selected = lease.selected(selection.frame(), declaration.declarationId());
            if (declaration.method() == PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1)
                org.xar.ck3.control.wave2.military.holycost.HolyCostJsonAdapter.selectedJson(selected);
            facts = new ArmyNativeRecipes.DeclarationFacts(selection.context(), selected.declarationId(), selected.targetCharacterId().intValueExact(),
                    selected.casusBelliIndex().intValueExact(), selected.casusBelliKey(), selected.configurationIndex().intValueExact(), selected.claimantCharacterId().intValueExact(),
                    selected.targetTitleIds().stream().map(java.math.BigInteger::intValueExact).toList(), lease.evidence());
        }
        var recipe = ArmyNativeRecipes.prepare(selection.input(), selection.context(), facts, false);
        require(recipe instanceof ArmyNativeRecipes.Primitive p && p.effect() == ArmyNativeRecipes.Effect.READ_ONLY, "war reads cannot prepare mutation/local/disabled preview");
        return (ArmyNativeRecipes.Primitive) recipe;
    }
    private static RawJson key(Selection selection) {
        ObjectNode key = parse(ArmyReadKey.key(selection.input(), selection.context()).bytes());
        if (selection.input() instanceof ArmyCalls.Declaration) key.set("declaration_source", selection.declarations().orElseThrow().evidence().toJson());
        selection.independentAssessment().ifPresent(lease -> key.set("independent_assessment_source", lease.evidence().toJson()));
        return new RawJson(bytes(key));
    }
    private static OperationKey operation(Selection selection, PublicMethod method) { return new OperationKey(primitive(selection, method).request().step()); }
    private static void verify(PlanningReadRequest request, Selection selection) {
        Context c = selection.context();
        require(request.before().equals(c.before()) && request.source().equals(c.source()) && request.sessionId().equals(c.sessionId())
                && request.arguments().equals(arguments(selection.input())), "war read crossed exact context or typed arguments");
        if (selection.input() instanceof ArmyCalls.Declaration declaration) selection.declarations().orElseThrow().selected(selection.frame(), declaration.declarationId());
    }
}

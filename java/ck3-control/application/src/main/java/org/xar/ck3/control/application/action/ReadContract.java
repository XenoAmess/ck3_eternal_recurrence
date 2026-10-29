package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import java.util.function.BiFunction;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact source-bound query installed by the one composition root. No prefix or constructor grants permission. */
public final class ReadContract<T> {
    public enum PermissionMode { ADVERTISED_CAPABILITY, SOURCE_QUALIFIED_PRIVATE }
    public enum WireProfile { EXECUTE_STEP, G2_PRIVATE_QUERY, SNAPSHOT_REVISION_ONLY, COUNCIL_MAILBOX_STATUS }
    public enum GuardMode { GAMEPLAY_PAUSED_MAP, FRONTEND_SESSION, LIFECYCLE_TERMINAL_SESSION, RECONCILIATION_OBSERVATION, STATUS_ONLY }
    private final String contractId;
    private final OperationKey operation;
    private final Optional<String> requiredCapability;
    private final String permissionKey;
    private final ExactRef sourceRef;
    private final PermissionMode permissionMode;
    private final WireProfile wireProfile;
    private final GuardMode guardMode;
    private final BiFunction<PlanningReadRequest, String, NativeRequest> prepare;
    private final Function<PlanningReadReceipt, T> decode;
    private final Optional<Function<PlanningReadReceipt, T>> pureReplay;
    private final Optional<CanonicalReuse<T>> canonicalReuse;
    private final Optional<DeclaredOriginalHistory<T>> originalHistory;
    @FunctionalInterface public interface PostKnownFailureProjection<T> {
        Optional<org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Failure> project(
                PlanningReadReceipt original,T replayed,java.util.List<PlanningReadReceipt> actualEarlier);
    }
    private record DeclaredPostKnownFailure<T>(org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Kind kind,
            PostKnownFailureProjection<T> projector) {
        private DeclaredPostKnownFailure { Objects.requireNonNull(kind);Objects.requireNonNull(projector); }
    }
    private final Optional<DeclaredPostKnownFailure<T>> postKnownFailure;
    @FunctionalInterface public interface OriginalHistoryProjection<T> {
        org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.HistoryProjection project(PlanningReadReceipt original, T replayed);
    }
    private record DeclaredOriginalHistory<T>(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind kind,
            OriginalHistoryProjection<T> projector) {
        private DeclaredOriginalHistory { Objects.requireNonNull(kind); Objects.requireNonNull(projector); }
    }
    private Optional<Function<String, Optional<ReadContract<T>>>> originalContracts = Optional.empty();
    @FunctionalInterface
    public interface CanonicalReuse<T> {
        void requireEquivalent(PlanningReadReceipt original, T actualValue, PlanningReadRequest current,
                org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj currentSemantic);
    }
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, ExactRef sourceRef,
            Function<PlanningReadRequest, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile,
                GuardMode.GAMEPLAY_PAUSED_MAP, sourceRef, (request, requestId) -> prepare.apply(request), decode);
    }
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile,
                GuardMode.GAMEPLAY_PAUSED_MAP, sourceRef, prepare, decode);
    }
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            Function<PlanningReadRequest, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile,
                guardMode, sourceRef, (request, requestId) -> prepare.apply(request), decode);
    }
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile, guardMode, sourceRef, prepare, decode, Optional.empty());
    }
    /** Explicit read-only archival interpretation. Legacy constructors do not install a replay path. */
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode,
            Function<PlanningReadReceipt, T> pureReplay) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile, guardMode, sourceRef, prepare, decode, Optional.of(Objects.requireNonNull(pureReplay)));
    }
    private ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode,
            Optional<Function<PlanningReadReceipt, T>> pureReplay) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile, guardMode, sourceRef,
                prepare, decode, pureReplay, Optional.empty());
    }
    /** A source owner explicitly defines cross-request reuse; no generic deadline/history-field dropping. */
    public ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode,
            Function<PlanningReadReceipt, T> pureReplay, CanonicalReuse<T> canonicalReuse) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile, guardMode, sourceRef,
                prepare, decode, Optional.of(Objects.requireNonNull(pureReplay)), Optional.of(Objects.requireNonNull(canonicalReuse)));
    }
    private ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode,
            Optional<Function<PlanningReadReceipt, T>> pureReplay, Optional<CanonicalReuse<T>> canonicalReuse) {
        this(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile, guardMode, sourceRef,
                prepare, decode, pureReplay, canonicalReuse, Optional.empty());
    }
    private ReadContract(String contractId, OperationKey operation, Optional<String> requiredCapability, String permissionKey,
            PermissionMode permissionMode, WireProfile wireProfile, GuardMode guardMode, ExactRef sourceRef,
            BiFunction<PlanningReadRequest, String, NativeRequest> prepare, Function<PlanningReadReceipt, T> decode,
            Optional<Function<PlanningReadReceipt, T>> pureReplay, Optional<CanonicalReuse<T>> canonicalReuse,
            Optional<DeclaredOriginalHistory<T>> originalHistory) {
        this(contractId,operation,requiredCapability,permissionKey,permissionMode,wireProfile,guardMode,sourceRef,
                prepare,decode,pureReplay,canonicalReuse,originalHistory,Optional.empty());
    }
    private ReadContract(String contractId,OperationKey operation,Optional<String> requiredCapability,String permissionKey,
            PermissionMode permissionMode,WireProfile wireProfile,GuardMode guardMode,ExactRef sourceRef,
            BiFunction<PlanningReadRequest,String,NativeRequest> prepare,Function<PlanningReadReceipt,T> decode,
            Optional<Function<PlanningReadReceipt,T>> pureReplay,Optional<CanonicalReuse<T>> canonicalReuse,
            Optional<DeclaredOriginalHistory<T>> originalHistory,Optional<DeclaredPostKnownFailure<T>> postKnownFailure) {
        this.contractId = StrictJson.text(contractId); this.operation = Objects.requireNonNull(operation);
        this.requiredCapability = Objects.requireNonNull(requiredCapability); requiredCapability.ifPresent(StrictJson::text);
        NativeStepDiscriminator.requireRegistration(operation, ExecutableStepBindings.Kind.READ, requiredCapability);
        this.permissionKey = StrictJson.text(permissionKey); this.sourceRef = Objects.requireNonNull(sourceRef);
        StrictJson.require(sourceRef.bytes() > 0, "actual query definition source required");
        this.permissionMode = Objects.requireNonNull(permissionMode); this.wireProfile = Objects.requireNonNull(wireProfile);
        this.guardMode = Objects.requireNonNull(guardMode);
        StrictJson.require((permissionMode == PermissionMode.ADVERTISED_CAPABILITY) == requiredCapability.isPresent(),
                "advertised reads require capability; source-qualified private reads have no fake capability");
        StrictJson.require(guardMode != GuardMode.FRONTEND_SESSION || wireProfile != WireProfile.G2_PRIVATE_QUERY,
                "frontend cannot borrow the gameplay private-query wire profile");
        boolean councilStatus = operation.value().equals("private-council-application-main-status-v1");
        StrictJson.require(councilStatus == (wireProfile == WireProfile.COUNCIL_MAILBOX_STATUS),
                "council mailbox status requires its exact revisionless wire profile");
        StrictJson.require(!councilStatus || permissionMode == PermissionMode.SOURCE_QUALIFIED_PRIVATE
                && guardMode == GuardMode.GAMEPLAY_PAUSED_MAP && requiredCapability.isEmpty(),
                "council mailbox status requires source-qualified gameplay permission without a fabricated capability");
        this.prepare = Objects.requireNonNull(prepare); this.decode = Objects.requireNonNull(decode);
        this.pureReplay = Objects.requireNonNull(pureReplay); this.canonicalReuse = Objects.requireNonNull(canonicalReuse);
        this.originalHistory = Objects.requireNonNull(originalHistory);
        this.postKnownFailure=Objects.requireNonNull(postKnownFailure);
        if(postKnownFailure.isPresent())requirePostKnownSource();
        StrictJson.require(originalHistory.isEmpty() || pureReplay.isPresent(), "source-owned original history requires an explicit pure decoder");
        if (guardMode == GuardMode.STATUS_ONLY) {
            PhysicalStatusIdentity.requireProfile(this);
            StrictJson.require(pureReplay.isPresent() && canonicalReuse.isEmpty() && originalHistory.isEmpty(),
                    "physical status requires pure read replay and cannot adopt canonical reads or project ordinary history");
        }
    }
    public String contractId() { return contractId; }
    public OperationKey operation() { return operation; }
    public NativeStepDiscriminator.WireIdentity nativeIdentity() { return NativeStepDiscriminator.identity(operation); }
    public Optional<String> requiredCapability() { return requiredCapability; }
    public String permissionKey() { return permissionKey; }
    public ExactRef sourceRef() { return sourceRef; }
    public PermissionMode permissionMode() { return permissionMode; }
    public boolean advertisedRequired() { return permissionMode == PermissionMode.ADVERTISED_CAPABILITY; }
    public WireProfile wireProfile() { return wireProfile; }
    public GuardMode guardMode() { return guardMode; }
    public NativeRequest prepare(PlanningReadRequest request, String requestId) {
        StrictJson.require(request.operation().equals(operation), "query does not match exact registered operation");
        StrictJson.require(originMatches(request.origin()),
                "query origin does not match registered guard mode");
        if (guardMode == GuardMode.STATUS_ONLY)
            StrictJson.require(request.arguments().members().isEmpty()
                    && request.origin().requirePhysicalStatusOnly().source().equals(request.source())
                    && request.origin().requirePhysicalStatusOnly().sessionId().equals(request.sessionId()),
                    "physical status preparation changed original source/session or empty arguments");
        StrictJson.text(requestId); NativeRequest nativeRequest = Objects.requireNonNull(prepare.apply(request, requestId));
        NativeStepDiscriminator.requireRequest(operation, ExecutableStepBindings.Kind.READ, nativeRequest);
        StrictJson.require(nativeRequest.requiredCapability().equals(requiredCapability),
                "query preparation changed its registered native permission");
        return nativeRequest;
    }
    public T decode(PlanningReadReceipt receipt) {
        requireReceipt(receipt);
        T value = Objects.requireNonNull(decode.apply(receipt), "typed query decoder cannot silently turn missing input into null");
        requireAdoptedReuse(receipt, value); return value;
    }
    /** Never invokes the live decoder; callers must still resolve this exact installed catalog instance. */
    public T replay(PlanningReadReceipt receipt) {
        requireReceipt(receipt);
        Function<PlanningReadReceipt, T> decoder = pureReplay.orElseThrow(
                () -> new IllegalStateException("this exact read contract has no explicitly installed pure replay decoder"));
        T value = Objects.requireNonNull(decoder.apply(receipt), "pure query replay cannot silently turn missing input into null");
        requireAdoptedReuse(receipt, value); return value;
    }
    public boolean hasPureReplay() { return pureReplay.isPresent(); }
    /** Declared by the actual installed source factory, never inferred from a runtime value class or receipt. */
    public Optional<org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind> originalHistoryKind() {
        return originalHistory.map(DeclaredOriginalHistory::kind);
    }
    /** Configure before this returned immutable identity is installed. Existing installed objects are never mutated. */
    public ReadContract<T> withOriginalHistoryProjection(OriginalHistoryProjection<T> actual) {
        return withOriginalHistoryProjection(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS, actual);
    }
    public synchronized ReadContract<T> withOriginalHistoryProjection(
            org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind declared, OriginalHistoryProjection<T> actual) {
        Objects.requireNonNull(declared); Objects.requireNonNull(actual);
        StrictJson.require(originalHistory.isEmpty() && originalContracts.isEmpty(), "source projector cannot replace an installed history/escrow identity");
        return new ReadContract<>(contractId, operation, requiredCapability, permissionKey, permissionMode, wireProfile,
                guardMode, sourceRef, prepare, decode, pureReplay, canonicalReuse, Optional.of(new DeclaredOriginalHistory<>(declared, actual)),postKnownFailure);
    }
    /** Source configuration happens before installation; this returns a new immutable contract identity. */
    public synchronized ReadContract<T> withPostKnownFailureProjection(
            org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Kind kind,PostKnownFailureProjection<T> actual) {
        Objects.requireNonNull(kind);Objects.requireNonNull(actual);requirePostKnownSource();
        StrictJson.require(postKnownFailure.isEmpty()&&originalContracts.isEmpty(),
                "post-Known verifier cannot replace an installed source/family identity");
        return new ReadContract<>(contractId,operation,requiredCapability,permissionKey,permissionMode,wireProfile,guardMode,sourceRef,
                prepare,decode,pureReplay,canonicalReuse,originalHistory,Optional.of(new DeclaredPostKnownFailure<>(kind,actual)));
    }
    public Optional<org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Kind> postKnownFailureKind(){
        return postKnownFailure.map(DeclaredPostKnownFailure::kind);
    }
    /** Original-only replay may reopen exact source originals. No live decoder, Native query, capture, result storage or write is invoked here.
     * The actual fixed source function must keep peer/codec/source qualification failures outside its domain-computation catch.
     * Actual private Known custody, catalog identity and all earlier-read/archive membership remain the publisher's responsibility.
     */
    public Optional<org.xar.ck3.control.application.history.DriverPostKnownReadFailureMaterial.Failure> reproducePostKnownFailure(
            PlanningReadReceipt finalOriginal,java.util.List<PlanningReadReceipt> actualEarlier) {
        var installed=postKnownFailure.orElseThrow(()->new IllegalStateException("this exact installed source has no post-Known failure verifier"));
        java.util.List<PlanningReadReceipt> earlier=java.util.List.copyOf(actualEarlier);
        StrictJson.require(earlier.size()==installed.kind().requiredEarlierReads(),"post-Known failure changed its finite earlier-read cardinality");
        T replayed=replay(Objects.requireNonNull(finalOriginal));
        var failure=Objects.requireNonNull(installed.projector().project(finalOriginal,replayed,earlier),"fixed post-Known verifier cannot return null");
        failure.ifPresent(actual->StrictJson.require(actual.kind()==installed.kind(),
                "fixed failure verifier changed its declared finite kind"));
        return failure;
    }
    private void requirePostKnownSource(){
        StrictJson.require(guardMode==GuardMode.GAMEPLAY_PAUSED_MAP&&operation.value().equals("query-army-strengths-v1")
                &&pureReplay.isPresent()&&originalHistoryKind().filter(
                    org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS::equals).isPresent(),
                "only the actual Army-strengths original-history source may declare this finite post-Known verifier");
    }
    /** Only the same contract's pure native decoder and fixed projector can produce this finite full-history material. */
    public org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Projection projectOriginalHistory(PlanningReadReceipt receipt) {
        var projected = projectOriginalHistoryPayload(receipt);
        if (projected instanceof org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Projection complete) return complete;
        throw new IllegalStateException("this original history source issued a lazy summary plan, not a complete result; explicit private summary capture is required");
    }
    /** Replay first, then only the identical installed pure projector. Returning a source-owned plan performs no capture/store work. */
    public org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.HistoryProjection projectOriginalHistoryPayload(PlanningReadReceipt receipt) {
        DeclaredOriginalHistory<T> installed = originalHistory.orElseThrow(
                () -> new IllegalStateException("this exact source contract has no original history projector"));
        T replayed = replay(receipt);
        var projected = Objects.requireNonNull(installed.projector().project(receipt, replayed), "source history projector cannot return null");
        StrictJson.require(projected.kind() == installed.kind(), "source history projector changed its installed finite kind");
        return projected;
    }

    /** Bound once by the actual typed catalog family; no heterogeneous cast or reconstructed historical contract. */
    synchronized void bindOriginalContracts(Function<String, Optional<ReadContract<T>>> actual) {
        Objects.requireNonNull(actual);
        if (originalContracts.isPresent()) throw new IllegalStateException("actual original contract lookup already bound");
        originalContracts = Optional.of(actual);
    }
    public synchronized Optional<ReadContract<T>> originalContract(String actualOldId) {
        StrictJson.text(actualOldId);
        if (originalContracts.isEmpty()) return Optional.empty();
        Optional<ReadContract<T>> original = Objects.requireNonNull(originalContracts.orElseThrow().apply(actualOldId), "typed original contract lookup cannot return null");
        original.ifPresent(value -> StrictJson.require(value.contractId().equals(actualOldId), "original catalog lookup changed the exact actual contract ID"));
        return original;
    }
    /** This source-owner check supplements all Root source/caps/decoder/raw-native/installed-instance gates. */
    public void requireCanonicalReuse(PlanningReadReceipt original, T actualValue, PlanningReadRequest current,
            org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj currentSemantic) {
        requireReceipt(original); Objects.requireNonNull(actualValue); Objects.requireNonNull(current); Objects.requireNonNull(currentSemantic);
        StrictJson.require(current.operation().equals(operation) && originMatches(current.origin()), "canonical reuse crossed registered query origin/operation");
        if (canonicalReuse.isEmpty()) {
            StrictJson.require(original.request().equals(current), "this source has no explicit predicate for cross-request canonical reuse"); return;
        }
        canonicalReuse.orElseThrow().requireEquivalent(original, actualValue, current, currentSemantic);
    }
    private boolean originMatches(CommandOrigin origin) {
        return switch (guardMode) {
            case GAMEPLAY_PAUSED_MAP -> origin instanceof CommandOrigin.Gameplay;
            case FRONTEND_SESSION -> origin instanceof CommandOrigin.Frontend;
            case LIFECYCLE_TERMINAL_SESSION -> origin instanceof CommandOrigin.LifecycleTerminal;
            case RECONCILIATION_OBSERVATION -> origin instanceof CommandOrigin.Reconciliation;
            case STATUS_ONLY -> origin instanceof CommandOrigin.PhysicalStatusOnly;
        };
    }
    private void requireAdoptedReuse(PlanningReadReceipt receipt, T value) {
        receipt.adoption().ifPresent(adoption -> canonicalReuse.orElseThrow(
                () -> new IllegalStateException("late read requires an explicit source-owned canonical reuse predicate"))
                .requireEquivalent(receipt, value, adoption.currentRequest(), adoption.currentSemantic()));
    }
    private void requireReceipt(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        StrictJson.require(receipt.contractId().equals(contractId) && receipt.request().operation().equals(operation)
                && receipt.before().guardMode() == guardMode && receipt.after().guardMode() == guardMode && originMatches(receipt.request().origin()),
                "query decoder crossed registered origin/contract");
        StrictJson.require(guardMode != GuardMode.STATUS_ONLY || receipt.adoption().isEmpty(),
                "physical status cannot borrow a late/canonical read adoption");
        if (receipt.adoption().isPresent()) {
            PlanningReadAdoption adoption = receipt.adoption().orElseThrow(); adoption.requireReceipt(receipt);
            StrictJson.require(canonicalReuse.isPresent(), "late read requires this exact source's explicit canonical reuse predicate");
        }
    }
}


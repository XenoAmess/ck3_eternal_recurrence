package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.planning.ReadonlyPlanningRetry;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Exact read-contract identity plus the actual same-lock living paused frame, including its complete modal binding. */
public final class RootPlanningReadGuard implements PlanningReadCoordinator.ReadGuardPort {
    private final ReadinessAuthority authority;
    private final Supplier<ContinuityStorePort.Session> borrowedSession;
    private final ActionPorts.OutcomeArchive archive;
    private final G2Source expectedSource;
    private final Clock clock;
    private final String authorityId;
    private final OriginalEvidencePort originals;
    private final RootReadContractCatalog catalog;
    private final ThreadLocal<PlanningReadRequest> originalReadSource = new ThreadLocal<>();
    public RootPlanningReadGuard(ReadinessAuthority authority, Supplier<ContinuityStorePort.Session> borrowedSession,
            ActionPorts.OutcomeArchive archive, G2Source expectedSource, Clock clock, String authorityId, OriginalEvidencePort originals, RootReadContractCatalog catalog) {
        this.authority = Objects.requireNonNull(authority); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.archive = Objects.requireNonNull(archive); this.expectedSource = Objects.requireNonNull(expectedSource);
        this.clock = Objects.requireNonNull(clock); this.authorityId = StrictJson.text(authorityId); this.catalog = Objects.requireNonNull(catalog);
        this.originals = Objects.requireNonNull(originals);
    }
    /** The actual Council native read and after guards retain one physical source; publication remains outside. */
    @Override public <T> T withOriginalReadSource(WriterContracts.Head actualLockedHead, PlanningReadRequest request,
            ReadContract<?> contract, Supplier<T> work) {
        Objects.requireNonNull(work);
        if (!isCouncilRead(contract)) return work.get();
        StrictJson.require(catalog.containsIdentity(contract), "Council read source requires the identical installed contract");
        StrictJson.require(request.source().equals(expectedSource) && request.operation().equals(contract.operation())
                && request.origin() instanceof CommandOrigin.Gameplay, "Council read source changed its exact source, operation or origin");
        StrictJson.require(originalReadSource.get()==null,"Council read cannot replace an active physical source callback");
        try {
            var session=RootGuardChecks.session(borrowedSession,actualLockedHead);
            return authority.withOriginalReadSource(session,request,lease -> {
                // This selects the held guard only while the actual source producer owns its physical scope.
                originalReadSource.set(request);
                try { return work.get(); }
                finally { originalReadSource.remove(); }
            });
        } catch(IOException failure) { throw new UncheckedIOException("actual Council read physical source unavailable",failure); }
    }
    private static boolean isCouncilRead(ReadContract<?> contract) {
        String expectedId;
        ReadContract.WireProfile wire;
        switch(contract.operation().value()) {
            case "private-query-council-composition-candidates-v1" -> {
                expectedId="council-private-query-council-composition-candidates-v1";
                wire=ReadContract.WireProfile.EXECUTE_STEP;
            }
            case "private-query-council-final-gates-v1" -> {
                expectedId="council-private-query-council-final-gates-v1";
                wire=ReadContract.WireProfile.EXECUTE_STEP;
            }
            case "private-council-application-main-status-v1" -> {
                expectedId="council-private-mailbox-status-v1";
                wire=ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS;
            }
            default -> { return false; }
        }
        StrictJson.require(contract.contractId().equals(expectedId) && contract.permissionKey().equals(expectedId)
                && contract.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                && contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && contract.wireProfile()==wire && contract.requiredCapability().isEmpty() && contract.hasPureReplay(),
                "Council original-read scope differs from its exact installed typed profile");
        return true;
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head actualLockedHead, PlanningReadRequest request, ReadContract<?> contract) {
        if(originalReadSource.get()==request && isCouncilRead(contract))
            return verifyOriginalCurrent(actualLockedHead,request,contract);
        StrictJson.require(catalog.containsIdentity(contract), "read contract is not the actual Root-installed or bounded factory-issued object");
        StrictJson.require(request.source().equals(expectedSource) && request.operation().equals(contract.operation()), "query source or exact operation changed");
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay && contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                "frontend query requires the independent frontend authority");
        try {
            var session = RootGuardChecks.session(borrowedSession, actualLockedHead);
            var sameWriterArchive = archive.withSession(session);
            return authority.current(session, request.before(), request.deadline(), lease -> {
                if (isLocalRootPreflight(contract,request)) {
                    RootGuardChecks.livingPaused(lease);
                    contract.requiredCapability().ifPresent(capability -> StrictJson.require(lease.bridgeCapabilities().contains(capability), "actual bridge did not advertise the required query capability"));
                    var basis=RootGuardChecks.binding(lease,request.origin(),request.source(),request.sessionId(),request.operation(),request.deadline(),sameWriterArchive,clock,actualLockedHead,authorityId,session,originals);
                    requireLocalRootPreflight(session,actualLockedHead,request,contract,lease.frame(),basis);
                    return new PlanningReadGuard(basis,true,true,true,lease.frame().fullBindingSha256());
                }
                if (isHeirPreflight(contract)) {
                    // Actual originals qualify this frame predicate; the coordinator separately proves the READ phase.
                    // Upstream readiness errors stay errors.
                    var basis = RootGuardChecks.binding(lease, request.origin(), request.source(), request.sessionId(), request.operation(), request.deadline(), sameWriterArchive, clock, actualLockedHead, authorityId, session, originals);
                    requireHeirPreflight(session, actualLockedHead, request, contract, lease.frame(), basis);
                    RootGuardChecks.livingPaused(lease);
                    return new PlanningReadGuard(basis, true, true, true, lease.frame().fullBindingSha256());
                }
                RootGuardChecks.livingPaused(lease);
                contract.requiredCapability().ifPresent(capability -> StrictJson.require(lease.bridgeCapabilities().contains(capability), "actual bridge did not advertise the required query capability"));
                var binding = RootGuardChecks.binding(lease, request.origin(), request.source(), request.sessionId(), request.operation(), request.deadline(), sameWriterArchive, clock, actualLockedHead, authorityId, session, originals);
                return new PlanningReadGuard(binding, true, true, true, lease.frame().fullBindingSha256());
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual Root planning-read authority unavailable: "
                + failure.getClass().getSimpleName() + ":" + String.valueOf(failure.getMessage()), failure); }
    }

    /** Only an already-active real physical read scope may verify adoption; no ordinary-current fallback or recapture. */
    @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head actualLockedHead,PlanningReadRequest request,ReadContract<?> contract) {
        StrictJson.require(catalog.containsIdentity(contract),"held read contract is not the identical Root-installed or factory-issued object");
        StrictJson.require(request.source().equals(expectedSource) &&request.operation().equals(contract.operation()),"held query source or exact operation changed");
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay &&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&contract.hasPureReplay(),"held original query requires its actual paused-map contract and pure original replay");
        try {
            var session=RootGuardChecks.session(borrowedSession,actualLockedHead);
            var sameArchive=archive.withSession(session);
            return authority.currentHeldOriginal(session,request,lease->{
                RootGuardChecks.livingPaused(lease);
                contract.requiredCapability().ifPresent(capability->StrictJson.require(lease.bridgeCapabilities().contains(capability),
                        "actual held physical bridge did not advertise the query capability"));
                var binding=RootGuardChecks.binding(lease,request.origin(),request.source(),request.sessionId(),request.operation(),
                        request.deadline(),sameArchive,clock,actualLockedHead,authorityId,session,originals);
                return new PlanningReadGuard(binding,true,true,true,lease.frame().fullBindingSha256());
            });
        }catch(IOException failure){throw new UncheckedIOException("actual held-only original planning-read authority unavailable",failure);}
    }

    private static final String HEIR_OPERATION = "query-current-first-heir-relationship-v1-private";
    private static final String HEIR_CONTRACT = "family/current-first-heir-relationship12004/v2";
    private static final String HEIR_PERMISSION = "source_qualified_current_first_heir_relationship_v2";
    private static final String HEIR_PRECONDITION = "current heir relationship needs a paused living-player map frame";
    private static boolean isHeirPreflight(ReadContract<?> contract) {
        if (!contract.contractId().equals(HEIR_CONTRACT) || !contract.operation().value().equals(HEIR_OPERATION)) return false;
        StrictJson.require(contract.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && contract.permissionMode() == ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                && contract.wireProfile() == ReadContract.WireProfile.EXECUTE_STEP
                && contract.permissionKey().equals(HEIR_PERMISSION) && contract.requiredCapability().isEmpty()
                && contract.hasPureReplay(), "current heir preflight contract profile differs");
        return true;
    }
    private void requireHeirPreflight(ContinuityStorePort.Session same, WriterContracts.Head head,
            PlanningReadRequest request, ReadContract<?> contract, Complete frame, GuardEvidence basis) throws IOException {
        // Malformed or foreign canonical input is not a retryable frame observation.
        StrictJson.require(request.arguments().get("expected_native_revision") instanceof IntegerValue expected
                && expected.value().signum() > 0
                && expected.value().equals(request.before().frame().identity().nativeRevision()),
                "current heir canonical expected revision differs from its exact original request");
        if (heirFrameReady(request, frame)) return;
        var originalFailure = new HeirPreconditionFailure();
        var proof = new HeirPreflightFailure(this, same, head, contract, request, frame, basis, originalFailure);
        try {
            ReadonlyPlanningRetry.heirPreflightFailed(proof);
            throw originalFailure; // The seam must never silently authorize this rejected frame.
        } finally { proof.callbackOpen=false; }
    }
    private static boolean heirFrameReady(PlanningReadRequest request, Complete frame) {
        Obj snapshot = frame.semantic();
        return request.arguments().get("expected_native_revision").equals(new IntegerValue(frame.identity().frame().identity().nativeRevision()))
                && new Bool(true).equals(snapshot.get("paused")) && new Bool(true).equals(snapshot.get("map_ready"))
                && snapshot.get("played_character") instanceof Obj player && new Bool(true).equals(player.get("alive"))
                && player.get("character_id") instanceof IntegerValue actor && actor.value().signum() > 0
                && snapshot.get("revision") instanceof IntegerValue && snapshot.get("date_raw") instanceof IntegerValue;
    }
    /** The original source fault maps to the public BridgeUnavailable kind, including exhausted retries. */
    public static final class HeirPreconditionFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private HeirPreconditionFailure() { super(HEIR_PRECONDITION); }
    }
    /** Opaque source-frame failure; the coordinator separately proves the actual pre-READ phase.
     * This in-process callback proof has no Java object serialization interface. */
    @SuppressWarnings("serial")
    public static final class HeirPreflightFailure extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final RootPlanningReadGuard owner;
        private final ContinuityStorePort.Session session;
        private final long headSequence;
        private final String headDigest;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final Complete frame;
        private final GuardEvidence basis;
        private final RuntimeException originalFailure;
        private final Thread callbackThread=Thread.currentThread();
        private boolean callbackOpen=true;
        private HeirPreflightFailure(RootPlanningReadGuard owner, ContinuityStorePort.Session session,
                WriterContracts.Head head, ReadContract<?> contract, PlanningReadRequest request,
                Complete frame, GuardEvidence basis, RuntimeException originalFailure) {
            super(originalFailure.getMessage(), originalFailure);
            this.owner=owner;this.session=session;this.headSequence=head.state().sequence();this.headDigest=head.digest();
            this.contract=contract;this.request=request;this.frame=frame;this.basis=basis;this.originalFailure=originalFailure;
        }
        public ContinuityStorePort.Session session() { return session; }
        public ReadContract<?> contract() { return contract; }
        public PlanningReadRequest request() { return request; }
        public RuntimeException originalFailure() { return originalFailure; }
        public Obj projection() {
            return new Obj(java.util.Map.of("class",new Text("heir_readonly_frame_precondition"),"business_submission",new Bool(false)));
        }
        /** Reuses actual custody; the public planner cannot supply a substitute archive. */
        public void requireOriginal() throws IOException { requireOriginal(session, contract, request, owner.archive); }
        /** The live planning seam validates this exact source failure before its callback closes. */
        public void requireOriginal(ContinuityStorePort.Session same, ReadContract<?> identical,
                PlanningReadRequest exact, ActionPorts.OutcomeArchive originals) throws IOException {
            StrictJson.require(callbackOpen && Thread.currentThread()==callbackThread,
                    "heir preflight proof escaped its actual live source callback");
            StrictJson.require(same==session && identical==contract && exact==request && owner.catalog.containsIdentity(contract)
                    && isHeirPreflight(contract) && request.source().equals(owner.expectedSource)
                    && !heirFrameReady(request,frame), "heir preflight lost original source/contract/request/failure custody");
            var current=same.head();
            StrictJson.require(current.state().sequence()==headSequence && current.digest().equals(headDigest),
                    "heir preflight crossed its original canonical writer head");
            RootGuardChecks.source(same,contract.sourceRef());RootGuardChecks.source(same,owner.expectedSource.sourceRef());
            var archived=Objects.requireNonNull(originals).withSession(same);
            var point=RootGuardEvidence.writerPoint(basis,archived);
            StrictJson.require(point.sequence()==headSequence && point.digest().equals(headDigest)
                    && basis.observed().equals(frame.identity()) && basis.source().equals(request.source())
                    && basis.sessionId().equals(request.sessionId()) && basis.operation().equals(request.operation())
                    && RootGuardEvidence.frameBasis(basis,archived).equals(NativeEffectEvidence.basis(frame)),
                    "heir preflight actual physical originals or writer point changed");
            RootGuardChecks.exact(frame.originalEvidence(),archived.loadNativeFrame(frame.originalEvidence()));
            RootGuardChecks.requireSemanticOriginal(frame,archived.loadFullMaterial(RootGuardEvidence.semanticReference(basis,archived)));
            StrictJson.require(originalFailure==getCause() && originalFailure instanceof HeirPreconditionFailure
                    && HEIR_PRECONDITION.equals(originalFailure.getMessage()),
                    "heir preflight original public failure changed");
        }
    }
    private static final java.math.BigInteger SIGNED_REVISION_LIMIT=java.math.BigInteger.ONE.shiftLeft(63);
    private static boolean isLocalRootPreflight(ReadContract<?> contract, PlanningReadRequest request) {
        if (!contract.contractId().equals(FinanceReadContracts.ROOT_CONTRACT_ID)
                || !contract.operation().equals(FinanceReadContracts.Query.ROOT.operation())) return false;
        StrictJson.require(contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP && contract.hasPureReplay(),
                "local ROOT preflight differs from the actual typed ROOT read profile");
        // The identical installed Registration owns permission key/capability; no guessed replacement is created.
        return FinanceReadContracts.rootCapture(request.arguments())==FinanceReadContracts.RootCapture.PUBLIC_QUERY;
    }
    private void requireLocalRootPreflight(ContinuityStorePort.Session same, WriterContracts.Head head,
            PlanningReadRequest request, ReadContract<?> contract, Complete frame, GuardEvidence basis) throws IOException {
        var expected=request.before().frame().revision();var current=frame.identity().frame().revision();
        StrictJson.require(expected!=null && current!=null && expected.signum()>=0 && current.signum()>=0
                && frame.semantic().get("revision") instanceof IntegerValue actual && actual.value().equals(current),
                "local ROOT preflight requires strict original non-negative public revisions");
        if (expected.equals(current)) return;
        var originalFailure=new RootRevisionPreconditionFailure(expected,current);
        // The original classifier accepts only forward public drift in its signed-64 domain.
        // Future, negative or malformed inputs never acquire the private retry marker.
        // Every mismatch keeps actual source custody; only retryEligible() may acquire the planning budget.
        var proof=new LocalRootRevisionFailure(this,same,head,contract,request,frame,basis,expected,current,originalFailure);
        try {
            ReadonlyPlanningRetry.rootRevisionFailed(proof);
            throw originalFailure;
        } finally { proof.callbackOpen=false; }
    }
    /** The actual local pre-send revision fault, preserving the original public mismatch kind. */
    public static final class RootRevisionPreconditionFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final java.math.BigInteger expected,current;
        private RootRevisionPreconditionFailure(java.math.BigInteger expected,java.math.BigInteger current) {
            super("campaign-root revision mismatch: expected "+expected.toString()+", current "+current.toString());
            this.expected=expected;this.current=current;
        }
        public java.math.BigInteger expectedPublicRevision() { return expected; }
        public java.math.BigInteger currentPublicRevision() { return current; }
    }
    /** Source-owned public ROOT frame failure; the sole coordinator must also confirm its actual pre-READ phase.
     * This in-process callback proof has no Java object serialization interface. */
    @SuppressWarnings("serial")
    public static final class LocalRootRevisionFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final RootPlanningReadGuard owner;
        private final ContinuityStorePort.Session session;
        private final long headSequence;
        private final String headDigest;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final Complete frame;
        private final GuardEvidence basis;
        private final java.math.BigInteger expected,current;
        private final RootRevisionPreconditionFailure originalFailure;
        private final Thread callbackThread=Thread.currentThread();
        private boolean callbackOpen=true;
        private LocalRootRevisionFailure(RootPlanningReadGuard owner,ContinuityStorePort.Session same,
                WriterContracts.Head head,ReadContract<?> contract,PlanningReadRequest request,Complete frame,
                GuardEvidence basis,java.math.BigInteger expected,java.math.BigInteger current,
                RootRevisionPreconditionFailure originalFailure) {
            super(originalFailure.getMessage(),originalFailure);
            this.owner=owner;this.session=same;this.headSequence=head.state().sequence();this.headDigest=head.digest();
            this.contract=contract;this.request=request;this.frame=frame;this.basis=basis;
            this.expected=expected;this.current=current;this.originalFailure=originalFailure;
        }
        public ContinuityStorePort.Session session() { return session; }
        public ReadContract<?> contract() { return contract; }
        public PlanningReadRequest request() { return request; }
        public RootRevisionPreconditionFailure originalFailure() { return originalFailure; }
        public boolean retryEligible() { return expected.compareTo(current)<0 && current.compareTo(SIGNED_REVISION_LIMIT)<0; }
        public Obj projection() {
            StrictJson.require(retryEligible(),"nonretry ROOT mismatch has no retry projection");
            return new Obj(java.util.Map.of("class",new Text("campaign_root_local_revision_changed_before_send"),
                    "business_submission",new Bool(false),"expected_public_revision",new IntegerValue(expected),
                    "current_public_revision",new IntegerValue(current),"failed_root_query_native_request_sent",new Bool(false)));
        }
        public void requireOriginal() throws IOException { requireOriginal(session,contract,request,owner.archive); }
        public void requireOriginal(ContinuityStorePort.Session same,ReadContract<?> identical,
                PlanningReadRequest exact,ActionPorts.OutcomeArchive originals) throws IOException {
            StrictJson.require(callbackOpen && Thread.currentThread()==callbackThread,
                    "local ROOT revision proof escaped its actual live source callback");
            StrictJson.require(same==session && identical==contract && exact==request && owner.catalog.containsIdentity(contract)
                    && request.source().equals(owner.expectedSource) && isLocalRootPreflight(contract,request)
                    && expected.equals(request.before().frame().revision()) && current.equals(frame.identity().frame().revision())
                    && expected.signum()>=0 && current.signum()>=0 && !expected.equals(current)
                    && new Bool(true).equals(frame.semantic().get("paused"))
                    && frame.semantic().get("revision") instanceof IntegerValue revision && revision.value().equals(current),
                    "local ROOT revision proof lost actual source/contract/request/predicate custody");
            var head=same.head();
            StrictJson.require(head.state().sequence()==headSequence && head.digest().equals(headDigest),
                    "local ROOT revision proof crossed its original canonical writer head");
            RootGuardChecks.source(same,contract.sourceRef());RootGuardChecks.source(same,owner.expectedSource.sourceRef());
            var archived=Objects.requireNonNull(originals).withSession(same);
            var point=RootGuardEvidence.writerPoint(basis,archived);
            StrictJson.require(point.sequence()==headSequence && point.digest().equals(headDigest)
                    && basis.observed().equals(frame.identity()) && basis.source().equals(request.source())
                    && basis.sessionId().equals(request.sessionId()) && basis.operation().equals(request.operation())
                    && RootGuardEvidence.frameBasis(basis,archived).equals(NativeEffectEvidence.basis(frame)),
                    "local ROOT revision original frame or writer basis changed");
            RootGuardChecks.exact(frame.originalEvidence(),archived.loadNativeFrame(frame.originalEvidence()));
            RootGuardChecks.requireSemanticOriginal(frame,archived.loadFullMaterial(RootGuardEvidence.semanticReference(basis,archived)));
            StrictJson.require(originalFailure==getCause() && originalFailure.expectedPublicRevision().equals(expected)
                    && originalFailure.currentPublicRevision().equals(current),
                    "local ROOT revision proof changed its exact original public fault");
        }
    }
}

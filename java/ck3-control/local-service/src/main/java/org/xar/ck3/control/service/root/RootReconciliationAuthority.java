package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Observation-only custody of one actual unresolved primitive. The private lease lives inside the same
 * physical Native/source/Driver freeze for the complete observer callback. It grants no Ready or submit authority.
 */
public final class RootReconciliationAuthority {
    public enum QueryKind { COMMANDER_CANDIDATES, ORDINARY_INTERACTION, ARMY_M5, FAMILY_MARRIAGE_SEND, WINDOW2, HOLY_ORDER_EMPLOYER, MERCENARY_EMPLOYER, CHILD_EDUCATION_FOCUS_RECEIPT, WAR_EXIT_TRUCE, PENDING_SUCCESSOR_CLOSE_TIMELINE, UNKNOWN_SENTINEL_STATUS }
    /** Root wraps a domain-owned actual typed factory result; this constructor is data, not registration. */
    public record AllowedRead(ReadContract<?> contract,OpportunityJson.Obj arguments,QueryKind kind) {
        public AllowedRead {
            Objects.requireNonNull(contract);Objects.requireNonNull(arguments);Objects.requireNonNull(kind);
            require(contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION,
                    "reconciliation cannot borrow an ordinary or terminal read contract");
            require(contract.wireProfile()!=ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS
                    &&!contract.operation().value().equals("private-council-application-main-status-v1"),
                    "Council STATUS can mutate its mailbox and is excluded from reconciliation");
            String op=contract.operation().value();
            require(switch(kind) {
                case COMMANDER_CANDIDATES -> op.matches("query-army-commander-candidates-v1-for-army-(?:0|[1-9][0-9]*)");
                case ORDINARY_INTERACTION -> contract.contractId().equals(
                        org.xar.ck3.control.nativebridge.capabilities.interactions.GuardianReconciliationQueries.CONTRACT_ID)
                        &&op.equals(org.xar.ck3.control.nativebridge.capabilities.interactions.OrdinaryInteractionCodec.QUERY_STEP)
                        &&contract.requiredCapability().filter(
                                org.xar.ck3.control.nativebridge.capabilities.interactions.OrdinaryInteractionCodec.QUERY_CAPABILITY::equals).isPresent()
                        &&contract.permissionKey().equals(org.xar.ck3.control.nativebridge.capabilities.interactions.OrdinaryInteractionCodec.QUERY_CAPABILITY)
                        &&contract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                        &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP&&contract.hasPureReplay();
                case ARMY_M5 -> contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP;
                case WINDOW2 -> contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                        &&contract.permissionMode()==ReadContract.PermissionMode.ADVERTISED_CAPABILITY
                        &&Set.of("query-war-declared-overview-v1","query-war-results-window-v1").contains(op)
                        &&contract.requiredCapability().filter(("game.command."+op)::equals).isPresent()
                        &&contract.permissionKey().equals("game.command."+op);
                case HOLY_ORDER_EMPLOYER -> {
                    org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead.requireReconciliationProfile(contract);
                    require(arguments.members().isEmpty(),"holy-order employer query requires exact empty arguments");
                    yield true;
                }
                case MERCENARY_EMPLOYER -> {
                    org.xar.ck3.control.application.planning.finance.FinanceReadContracts.requireMercenaryEmployerProfile(contract);
                    require(arguments.members().isEmpty(),"mercenary employer query requires exact empty arguments");
                    yield true;
                }
                case CHILD_EDUCATION_FOCUS_RECEIPT -> contract.contractId().equals(
                        org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries.RECONCILIATION_RECEIPT_CONTRACT)
                        &&op.equals(org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.RECEIPT_STEP)
                        &&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                        &&contract.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                        &&contract.permissionKey().equals(org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.PERMISSION)
                        &&contract.requiredCapability().isEmpty()&&contract.hasPureReplay();
                case WAR_EXIT_TRUCE -> {
                    org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarExitTruceReads.requireProfile(contract);
                    require(contract.hasPureReplay(),"original-pending truce requires its actual explicit pure replay decoder");
                    yield true;
                }
                case PENDING_SUCCESSOR_CLOSE_TIMELINE -> {
                    RootPendingUiCloseReconciliation.requireProfile(contract);
                    yield true;
                }
                case UNKNOWN_SENTINEL_STATUS -> {
                    RootUnknownSentinelReadProfile.requireProfile(contract);
                    yield true;
                }
                case FAMILY_MARRIAGE_SEND -> op.equals(org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.STEP)
                        &&contract.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                        &&contract.permissionKey().equals(org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.PERMISSION)
                        &&contract.requiredCapability().isEmpty()&&contract.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP;
            },"query is outside the explicitly installed pure observation families");
        }
    }
    @FunctionalInterface public interface QueryPolicy {
        /** Actual original-intent domain factories only; no Native query, history publication or planner invocation. */
        List<AllowedRead> allowed(ActionReceipt original,ReconciliationIdentity actual,Complete actualData,Instant actualDeadline)throws IOException;
    }
    @FunctionalInterface public interface LeaseWork<T> { T apply(Lease actual)throws IOException; }
    public static final class Lease {
        private final RootReconciliationAuthority owner;
        private final RootLifecycleAuthority.SnapshotLease physical;
        private final ActionReceipt canonical;
        private final ActionState.Attempt attempt;
        private final Complete before,current;
        private final ReconciliationIdentity identity;
        private final List<AllowedRead> reads;
        private Lease(RootReconciliationAuthority owner,RootLifecycleAuthority.SnapshotLease physical,ActionReceipt canonical,
                ActionState.Attempt attempt,Complete before,Complete current,ReconciliationIdentity identity,List<AllowedRead> reads) {
            this.owner=owner;this.physical=physical;this.canonical=canonical;this.attempt=attempt;this.before=before;this.current=current;
            this.identity=identity;this.reads=List.copyOf(reads);
        }
        public ReconciliationIdentity identity(){return identity;}
        public DriverObservationAssembler.FullSnapshot fullSnapshot(){return physical.fullSnapshot();}
        /** Actual complete joined facts only. Ordinary readiness and action permission remain unavailable. */
        public Complete complete(){return current;}
        public Complete before(){return before;}
        public ActionReceipt canonical(){return canonical;}
        public ActionState.Attempt attempt(){return attempt;}
        public SourceQualification sourceQualification(){return physical.sourceQualification();}
        public ExactRef originalHello(){return physical.originalHello();}
        public ExactRef originalHeartbeat(){return physical.originalHeartbeat();}
        public ExactRef originalDriver(){return physical.originalDriver();}
        public ExactRef originalSemantic(){return physical.originalSemantic();}
        public Instant validUntil(){return physical.validUntil();}
        public Set<String> bridgeCapabilities(){return physical.bridgeCapabilities();}
        /** Actual push observation qualification; this operation is never an installed query or submit permission. */
        public GuardEvidence observationGuard(){
            Scope scope=owner.active.get();require(scope!=null&&scope.lease()==this,"observation qualification escaped its private Root callback");
            return scope.observation();
        }
        public void assertCurrent(ContinuityStorePort.Session same)throws IOException{
            Scope scope=owner.active.get();require(scope!=null&&scope.lease()==this,"detached reconciliation data is not a live query lease");
            owner.assertScope(scope,same,scope.deadline());
        }
    }
    private record Scope(ContinuityStorePort.Session session,Lease lease,GuardEvidence observation,List<WriterContracts.Pin> pins,String head,Instant deadline) { }
    private enum BasisRole { PUSH_OBSERVATION, PURE_QUERY }
    private static final class RawUnavailable extends IOException {
        private final List<ExactRef> originals;
        private RawUnavailable(String reason,List<ExactRef> originals){super(reason);this.originals=List.copyOf(originals);}
    }
    private static final String SCHEMA="xar.java.root-reconciliation-guard-original-basis/v1";
    private static final int MAX_BASIS=128<<10;
    private static final Set<String> FIELDS=Set.of("schema","role","authority_id","identity","semantic","read","writer_point");
    private final ContinuityStorePort store;
    private final ActionPorts.OutcomeArchive archive;
    private final RootLifecycleAuthority physical;
    private final ReconciliationPendingBinding pending;
    private final OriginalEvidencePort originals;
    private final NativeEffectEvidence.FrameLoader frames;
    private final RootReadContractCatalog catalog;
    private final QueryPolicy queries;
    private final Clock clock;
    private final ThreadLocal<Scope> active=new ThreadLocal<>();
    private final ThreadLocal<ContinuityStorePort.Session> publicWindowSnapshot=new ThreadLocal<>();
    public RootReconciliationAuthority(ContinuityStorePort soleStore,ActionPorts.OutcomeArchive soleArchive,
            RootLifecycleAuthority samePhysical,ReconciliationPendingBinding actualPending,OriginalEvidencePort originals,
            NativeEffectEvidence.FrameLoader actualBeforeLoader,RootReadContractCatalog sameCatalog,QueryPolicy actualPureFactories,Clock clock) {
        store=Objects.requireNonNull(soleStore);archive=Objects.requireNonNull(soleArchive);physical=Objects.requireNonNull(samePhysical);
        pending=Objects.requireNonNull(actualPending);this.originals=Objects.requireNonNull(originals);frames=Objects.requireNonNull(actualBeforeLoader);
        catalog=Objects.requireNonNull(sameCatalog);queries=Objects.requireNonNull(actualPureFactories);this.clock=Objects.requireNonNull(clock);
    }
    /** Construction/installation check only. Equal-looking wrappers or records cannot replace the actual shared objects. */
    public void requireOwner(ContinuityStorePort soleStore,ActionPorts.OutcomeArchive soleArchive,
            RootReadContractCatalog sameCatalog,RootLifecycleAuthority samePhysical) {
        require(store==soleStore&&archive==soleArchive&&catalog==sameCatalog&&physical==samePhysical,
                "reconciliation installation must retain the exact sole writer/archive/catalog/physical authority objects");
    }

    /** The canonical pending/Attempt is authenticated before any fresh Native I/O. No history publication occurs here. */
    public <T>T withObserved(ContinuityStorePort.Session same,ActionReceipt original,Instant deadline,LeaseWork<T> observer)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(deadline);Objects.requireNonNull(observer);store.requireSession(same);
        require(active.get()==null&&publicWindowSnapshot.get()==null,"reconciliation observation cannot replace an original pending/public-window scope");
        require(clock.instant().isBefore(deadline),"reconciliation deadline expired before any Native I/O");
        ActionState.Attempt attempt=pending.requirePending(same,original);
        var bound=archive.withSession(same);
        RootGuardEvidence.requireHistory(attempt.guard(),bound,same);
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),bound,frames);
        NativeEffectEvidence.FrameBasis oldBasis=RootGuardEvidence.frameBasis(attempt.guard(),bound);
        ExactRef oldDriver=originalDriver(same,oldBasis);
        ExactRef originalReceipt=bound.receiptReferenceOf(original);
        return physical.withSnapshot(same,deadline,captured->{
            captured.assertCurrent(same);
            if(captured.ordinary().isEmpty()) {
                captured.assertCurrent(same);
                throw new RawUnavailable("actual current player is missing, dead or changed; unresolved primitive has no same-actor reconciliation data",
                        java.util.stream.Stream.concat(List.of(captured.fullSnapshot().originalEvidence(),captured.originalHello(),captured.originalHeartbeat(),
                                captured.freshFacts().semanticFactsEvidence(),captured.originalDriver(),captured.originalSemantic()).stream(),captured.sourceQualification().proof().stream()).toList());
            }
            Complete actual=captured.ordinary().orElseThrow();
            require(actual.source().equals(original.command().source())&&actual.sessionId().equals(original.command().sessionId()),
                    "fresh reconciliation data crossed original source or held session");
            byte[] old=read(same,oldDriver,WriterContracts.MAX_PIN_BYTES);
            byte[] current=read(same,captured.originalDriver(),WriterContracts.MAX_PIN_BYTES);
            var evidence=new ReconciliationIdentity.Evidence(actual.originalEvidence(),captured.originalHello(),captured.originalHeartbeat(),
                    captured.freshFacts().semanticFactsEvidence(),captured.originalDriver(),captured.sourceQualification().proof());
            // This is DATA only. The same pending binder reopens all canonical originals and either authenticates
            // the exact unchanged Driver or invokes its private finite history-append provider before any lease exists.
            ReconciliationIdentity identity=Arrays.equals(old,current)
                    ?ReconciliationIdentity.fromCanonical(original,actual.identity(),actual.source(),actual.sessionId(),
                            actual.connectionGeneration(),originalReceipt,oldDriver,evidence,actual.observedAt())
                    :ReconciliationIdentity.fromCanonicalHistoryAppend(original,actual.identity(),actual.source(),actual.sessionId(),
                            actual.connectionGeneration(),originalReceipt,oldDriver,evidence,actual.observedAt(),
                            new RootGuardEvidence.WriterPoint(same.head().state().sequence(),same.head().digest()));
            pending.verify(same,identity);
            List<AllowedRead> reads=installed(same,original,identity,before,actual,captured.validUntil());
            List<WriterContracts.Pin> pins=new ArrayList<>();
            for(var read:reads) {
                pins.add(pin(same,read.contract().sourceRef()));
                pins.add(pin(same,decoder(read.contract())));
                if(read.kind()==QueryKind.FAMILY_MARRIAGE_SEND) {
                    var baseline=org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.arguments(read.arguments()).beforeRead().orElseThrow();
                    read(same,baseline,WriterContracts.MAX_PIN_BYTES);pins.add(same.capturePin(baseline,WriterContracts.MAX_PIN_BYTES));
                }
            }
            var lease=new Lease(this,captured,original,attempt,before,actual,identity,reads);
            GuardEvidence observation=observationBinding(lease,same);
            pins.add(same.capturePin(observation.supportingEvidence().getFirst(),MAX_BASIS));
            var scope=new Scope(same,lease,observation,List.copyOf(pins),same.head().digest(),deadline);active.set(scope);
            try {assertScope(scope,same,deadline);T result=observer.apply(lease);assertScope(scope,same,deadline);return result;}
            finally {active.remove();}
        });
    }

    /** Actual physical DATA and the existing physical producer's SEM; this is never an ordinary Ready or reconciliation lease. */
    public record PublicWindowSnapshot(RootLifecycleAuthority.SnapshotLease physical,
            org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence semantic) {
        public PublicWindowSnapshot {Objects.requireNonNull(physical);Objects.requireNonNull(semantic);}
    }
    @FunctionalInterface public interface PublicWindowWork<T> {T apply(PublicWindowSnapshot actual)throws IOException;}

    /**
     * Borrow only the two original direct fixed-window CLOSE primitives for their paired public window QUERY.
     * Canonical UNKNOWN, its original Attempt and optional dispatch remain unchanged. The installed query issuer must bind
     * its exact parent/query pair; this entry creates no query request, reconciliation identity or submit authority.
     */
    public <T>T withPublicWindowSnapshot(ContinuityStorePort.Session same,ActionReceipt original,Instant deadline,
            PublicWindowWork<T> work)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(deadline);Objects.requireNonNull(work);store.requireSession(same);
        require(active.get()==null&&publicWindowSnapshot.get()==null,"public window query cannot borrow or replace another physical/reconciliation scope");
        require(clock.instant().isBefore(deadline),"public window query deadline expired before Native IO");
        require(original.command().origin() instanceof CommandOrigin.Gameplay&&original.state() instanceof ActionState.Unknown,
                "public window query requires its actual canonical UNKNOWN gameplay primitive");
        var expected=switch(original.command().operation().value()) {
            case "close-war-declared-overview-v1" -> org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_DECLARED_OVERVIEW_V1;
            case "close-war-results-window-v1" -> org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.Kind.CLOSE_WAR_RESULTS_WINDOW_V1;
            default -> throw new IllegalArgumentException("public window query parent is outside the two exact original CLOSE operations");
        };
        var arguments=org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.decode(original.command().arguments());
        require(arguments.kind()==expected&&arguments.executionProfile()==
                org.xar.ck3.control.nativebridge.capabilities.army.ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW,
                "public window query requires the original direct fixed-window profile, never SDK or composite execution");
        var unknown=(ActionState.Unknown)original.state();
        require(unknown.attempt().isPresent(),"public window query requires its original canonical Attempt without resubmission");
        ActionState.Attempt attempt=pending.requirePending(same,original);
        require(unknown.attempt().orElseThrow().equals(attempt),"public window query lost its original canonical Attempt");
        unknown.dispatch().ifPresent(dispatch->require((dispatch instanceof NativeActionPort.AckReceived||dispatch instanceof NativeActionPort.Unknown)
                &&dispatch.requestId().equals(attempt.requestId()),"public window query dispatch differs from its original canonical Attempt"));
        var bound=archive.withSession(same);RootGuardEvidence.requireHistory(attempt.guard(),bound,same);
        RootGuardEvidence.loadFrame(attempt.guard(),bound,frames);
        String head=same.head().digest();publicWindowSnapshot.set(same);
        try {
            return physical.withSnapshot(same,deadline,captured->{
                captured.assertCurrent(same);
                Complete actual=captured.ordinary().orElseThrow(()->new IOException("actual living original player/episode is unavailable for the public window query"));
                require(actual.source().equals(original.command().source())&&actual.sessionId().equals(original.command().sessionId())
                        &&actual.identity().machineId().equals(original.command().origin().machineId())
                        &&actual.identity().game().equals(original.command().origin().game()),
                        "public window physical current Root/source/session/Game differs from its original canonical context");
                // Old ACK, actor/episode/connection and chronology determine resolution eligibility only.
                // A current read keeps its genuine new fields; it never copies an old subject or invents an ACK.
                var owner=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                        original.command().origin().machineId(),original.command().origin().game(),original.command().sessionId());
                var semantic=physical.semantic(same,owner,captured);
                require(head.equals(same.head().digest())&&active.get()==null,"public window snapshot changed canonical history or opened reconciliation");
                T value=work.apply(new PublicWindowSnapshot(captured,semantic));
                captured.assertCurrent(same);store.requireSession(same);
                require(publicWindowSnapshot.get()==same&&active.get()==null&&head.equals(same.head().digest())
                        &&pending.requirePending(same,original).equals(attempt),
                        "public window query changed its canonical pending/head/Attempt or opened reconciliation");
                return value;
            });
        } finally {publicWindowSnapshot.remove();}
    }
    /** Root's coordinator adapter retains qualified raw originals when the unchanged actor can no longer be joined as Complete data. */
    public ActionPorts.PostconditionResult observe(ContinuityStorePort.Session same,ActionReceipt original,Instant deadline,
            LeaseWork<ActionPorts.PostconditionResult> observer)throws IOException{
        try{return withObserved(same,original,deadline,observer);}
        catch(RawUnavailable raw){return new ActionPorts.Pending(raw.getMessage(),raw.originals);}
    }

    /** A copied identity can never acquire a new scope. Only the active original observer may issue its listed reads. */
    public <T>T current(ContinuityStorePort.Session same,ReconciliationIdentity expected,Instant deadline,LeaseWork<T> work)throws IOException{
        Objects.requireNonNull(expected);Objects.requireNonNull(work);Scope scope=active.get();
        require(scope!=null&&scope.lease().identity().sameGuardFrame(expected),"no exact original pending reconciliation scope is active");
        assertScope(scope,same,deadline);T value=work.apply(scope.lease());assertScope(scope,same,deadline);return value;
    }
    /** Presence is not admission. A mismatched active command/session is rejected instead of falling through to ordinary reads. */
    public boolean hasActiveFor(ContinuityStorePort.Session same,ActionCommand command)throws IOException{
        store.requireSession(same);Scope scope=active.get();if(scope==null)return false;
        requireCommand(scope,command);assertScope(scope,same,scope.deadline());return true;
    }
    /** Borrows the same private lease by the complete original canonical command, without collecting another snapshot. */
    public <T>T currentForCommand(ContinuityStorePort.Session same,ActionCommand original,LeaseWork<T> work)throws IOException{
        Scope scope=active.get();require(scope!=null,"no original pending reconciliation observer is active");
        return currentForCommand(same,original,scope.deadline(),work);
    }
    public <T>T currentForCommand(ContinuityStorePort.Session same,ActionCommand original,Instant deadline,LeaseWork<T> work)throws IOException{
        Objects.requireNonNull(work);Scope scope=active.get();require(scope!=null,"no original pending reconciliation observer is active");
        requireCommand(scope,original);assertScope(scope,same,deadline);T result=work.apply(scope.lease());assertScope(scope,same,deadline);return result;
    }
    private static void requireCommand(Scope scope,ActionCommand command){
        Objects.requireNonNull(command);ActionReceipt original=scope.lease().canonical();
        require(original.command().actionId().equals(command.actionId())&&original.bodySha256().equals(ActionCodec.bodySha256(command))
                &&Arrays.equals(ActionCodec.encodeCommand(original.command()),ActionCodec.encodeCommand(command)),
                "reconciliation observer cannot borrow another action or altered complete original command");
    }

    /** Called by the one Root read dispatcher; neither contract identity nor exact original-intent arguments may be substituted. */
    GuardEvidence binding(Lease lease,ContinuityStorePort.Session same,PlanningReadRequest request,ReadContract<?> contract,
            WriterContracts.Head head,String authorityId)throws IOException{
        lease.assertCurrent(same);
        require(request.origin() instanceof CommandOrigin.Reconciliation
                &&request.origin().requireReconciliation().sameGuardFrame(lease.identity())
                &&request.source().equals(lease.identity().source())&&request.sessionId().equals(lease.identity().sessionId()),
                "reconciliation read changed its active canonical pending/source/session");
        require(head.digest().equals(same.head().digest())&&head.state().sequence()==same.head().state().sequence(),
                "reconciliation guard does not hold the actual writer point");
        AllowedRead selected=select(lease.reads,request,contract);
        contract.requiredCapability().ifPresent(cap->require(lease.bridgeCapabilities().contains(cap),
                "received original hello does not advertise the exact pure reconciliation query"));
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("role",BasisRole.PURE_QUERY.name()).put("authority_id",authorityId);
        row.set("identity",ReconciliationIdentityCodec.encode(lease.identity()));
        row.set("semantic",lease.originalSemantic().toJson());row.set("read",descriptor(selected));
        row.set("writer_point",StrictJson.object().put("sequence",head.state().sequence()).put("digest",head.digest()));
        var bound=archive.withSession(same);RawJson raw=new RawJson(StrictJson.canonical(row,MAX_BASIS));ExactRef basis=bound.preserveMaterial(raw);
        require(raw.equals(bound.loadMaterial(basis)),"actual reconciliation basis changed during archive readback");
        Instant until=lease.validUntil().isBefore(request.deadline())?lease.validUntil():request.deadline();
        require(clock.instant().isBefore(until),"reconciliation query lease expired before permission");
        GuardEvidence guard=new GuardEvidence(new CommandOrigin.Reconciliation(lease.identity()),lease.identity().source(),
                lease.identity().sessionId(),lease.identity().connectionGeneration(),request.operation(),lease.identity().nativeEvidence(),
                lease.identity().capabilityEvidence(),StrictJson.text(authorityId),lease.identity().observedAt(),until,List.of(basis));
        verifyArchived(guard,bound,same,originals);lease.assertCurrent(same);return guard;
    }
    private GuardEvidence observationBinding(Lease lease,ContinuityStorePort.Session same)throws IOException{
        lease.physical.assertCurrent(same);pending.verify(same,lease.identity());var head=same.head();
        String authorityId=lease.attempt().guard().authorityId();
        ObjectNode row=StrictJson.object().put("schema",SCHEMA).put("role",BasisRole.PUSH_OBSERVATION.name()).put("authority_id",authorityId);
        row.set("identity",ReconciliationIdentityCodec.encode(lease.identity()));row.set("semantic",lease.originalSemantic().toJson());row.putNull("read");
        row.set("writer_point",StrictJson.object().put("sequence",head.state().sequence()).put("digest",head.digest()));
        var bound=archive.withSession(same);RawJson raw=new RawJson(StrictJson.canonical(row,MAX_BASIS));ExactRef basis=bound.preserveMaterial(raw);
        require(raw.equals(bound.loadMaterial(basis)),"actual push reconciliation qualification changed in its immutable archive");
        var guard=new GuardEvidence(new CommandOrigin.Reconciliation(lease.identity()),lease.identity().source(),lease.identity().sessionId(),
                lease.identity().connectionGeneration(),lease.canonical().command().operation(),lease.identity().nativeEvidence(),lease.identity().capabilityEvidence(),
                authorityId,lease.identity().observedAt(),lease.validUntil(),List.of(basis));
        verifyArchived(guard,bound,same,originals);lease.physical.assertCurrent(same);return guard;
    }

    /**
     * Durable interpretation only. Both canonical pending ancestry and the original basis writer point are authenticated.
     * Current settlement may be later than this historical read; it never authorizes another live query or a replay.
     */
    public Complete verifyArchived(GuardEvidence guard,ActionPorts.OutcomeArchive sameArchive,ContinuityStorePort.Session same,
            OriginalEvidencePort actualOriginals)throws IOException {
        Objects.requireNonNull(actualOriginals);store.requireSession(same);
        String originalHead=same.head().digest();List<WriterContracts.Pin> held=new ArrayList<>();
        require(guard.origin() instanceof CommandOrigin.Reconciliation&&guard.supportingEvidence().size()==1,
                "dedicated reconciliation source basis required");
        var identity=guard.origin().requireReconciliation();
        var bound=sameArchive.withSession(same);
        ExactRef basis=guard.supportingEvidence().getFirst();RawJson raw=bound.loadMaterial(basis);
        exact(basis,raw.bytes());require(Arrays.equals(raw.bytes(),actualOriginals.read(same,basis,MAX_BASIS)),
                "reconciliation basis does not have exact owned original custody");
        held.add(same.capturePin(basis,MAX_BASIS));
        ObjectNode row=StrictJson.object(StrictJson.parse(raw.bytes(),MAX_BASIS),FIELDS);
        require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&guard.authorityId().equals(StrictJson.text(row.get("authority_id")))
                &&identity.equals(ReconciliationIdentityCodec.decode(row.get("identity"))),"archived reconciliation identity or authority changed");
        BasisRole role=BasisRole.valueOf(StrictJson.text(row.get("role")));
        var point=StrictJson.object(row.get("writer_point"),Set.of("sequence","digest"));
        long sequence=StrictJson.integer(point.get("sequence"),java.math.BigInteger.ZERO,java.math.BigInteger.valueOf(9_007_199_254_740_991L)).longValueExact();
        var writerState=same.requireHistoricalState(sequence,StrictJson.text(point.get("digest")));
        pending.verifyHistorical(same,identity);
        ActionReceipt original=bound.loadReceipt(identity.pending().originalReceipt());
        ActionReceipt atPoint=ContinuityActionJournal.lookup(writerState,identity.pending().actionId(),bound)
                .orElseThrow(()->new IOException("reconciliation basis predates its original canonical pending primitive"));
        require(!atPoint.settled()&&Arrays.equals(ActionReceiptCodec.encodeReceipt(original,bound),ActionReceiptCodec.encodeReceipt(atPoint,bound)),
                "reconciliation basis writer point did not retain this exact original unresolved receipt");
        ActionState.Attempt attempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("actual historical primitive Attempt absent"));
        RootGuardEvidence.requireHistory(attempt.guard(),bound,same);
        Complete before=RootGuardEvidence.loadFrame(attempt.guard(),bound,frames);
        require(originalDriver(same,RootGuardEvidence.frameBasis(attempt.guard(),bound)).equals(identity.pending().originalBeforeDriver()),
                "reconciliation original Driver is not the actual original guard manifest Driver");
        for(ExactRef ref:identity.evidence().originals()) {
            int limit=identity.evidence().completeSourceQualification().filter(ref::equals).isPresent()?16<<20:WriterContracts.MAX_PIN_BYTES;
            exact(ref,actualOriginals.read(same,ref,limit));held.add(same.capturePin(ref,limit));
        }
        var basisFrames=new NativeEffectEvidence.FrameBasis(identity.nativeEvidence(),identity.evidence().observationManifest());
        Complete actual=frames.load(basisFrames,bound);
        require(actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())
                &&actual.sessionId().equals(identity.sessionId())&&actual.connectionGeneration().equals(identity.connectionGeneration())
                &&actual.originalEvidence().equals(identity.nativeEvidence())&&actual.observedAt().equals(identity.observedAt()),
                "archived reconciliation raw/Driver data differs from its factual identity");
        require(originalDriver(same,basisFrames).equals(identity.evidence().currentOriginalDriver()),
                "reconciliation full Driver is not the current actual manifest Driver");
        require(Arrays.equals(read(same,identity.pending().originalBeforeDriver(),WriterContracts.MAX_PIN_BYTES),
                read(same,identity.evidence().currentOriginalDriver(),WriterContracts.MAX_PIN_BYTES)),
                "archived unresolved primitive published another full Driver");
        require(before.identity().equals(identity.pending().originalBefore()),"actual before frame differs from the canonical primitive");
        ExactRef semantic=ExactRef.fromJson(row.get("semantic"));byte[] semanticBytes=actualOriginals.read(same,semantic,WriterContracts.MAX_PIN_BYTES);
        exact(semantic,semanticBytes);require(DriverJson.object(semanticBytes,DriverJson.MAX_NATIVE_BYTES).equals(actual.semantic()),
                "archived reconciliation semantic differs from the actual sole assembler");
        held.add(same.capturePin(semantic,WriterContracts.MAX_PIN_BYTES));
        require(guard.source().equals(identity.source())&&guard.sessionId().equals(identity.sessionId())
                &&guard.connectionGeneration().equals(identity.connectionGeneration())&&guard.nativeEvidence().equals(identity.nativeEvidence())
                &&guard.capabilityEvidence().equals(identity.capabilityEvidence())&&guard.observedAt().equals(identity.observedAt()),
                "archived reconciliation guard changed its canonical factual binding");
        Set<String> receivedCapabilities=requireHelloAndSource(same,identity,actualOriginals);
        if(role==BasisRole.PUSH_OBSERVATION) {
            require(row.get("read").isNull()&&guard.operation().equals(original.command().operation())
                    &&guard.authorityId().equals(attempt.guard().authorityId()),
                    "push qualification is not the actual original primitive operation/authority; it grants no query contract");
        }else {
            require(!row.get("read").isNull(),"pure query qualification requires its exact installed typed descriptor");
            List<AllowedRead> allowed=installed(same,original,identity,before,actual,guard.validUntil());
            List<AllowedRead> matches=allowed.stream().filter(read->descriptor(read).equals(row.get("read"))
                    &&read.contract().operation().equals(guard.operation())).toList();
            require(matches.size()==1,"archived read was not issued by the exact installed original-intent pure query factory");
            AllowedRead selected=matches.getFirst();
            selected.contract().requiredCapability().ifPresent(cap->require(receivedCapabilities.contains(cap),
                    "archived received hello did not advertise this exact pure query capability"));
            held.add(pin(same,selected.contract().sourceRef()));held.add(pin(same,decoder(selected.contract())));
            if(selected.kind()==QueryKind.FAMILY_MARRIAGE_SEND) {
                var baseline=org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.arguments(selected.arguments()).beforeRead().orElseThrow();
                read(same,baseline,WriterContracts.MAX_PIN_BYTES);held.add(same.capturePin(baseline,WriterContracts.MAX_PIN_BYTES));
            }
        }
        for(var pin:held)same.verifyPin(pin);
        store.requireSession(same);require(originalHead.equals(same.head().digest()),"writer changed during archived reconciliation interpretation");
        return actual;
    }

    private List<AllowedRead> installed(ContinuityStorePort.Session same,ActionReceipt original,ReconciliationIdentity identity,Complete before,Complete actual,Instant deadline)throws IOException{
        List<AllowedRead> allowed=List.copyOf(Objects.requireNonNull(queries.allowed(original,identity,actual,deadline)));
        require(allowed.size()<=4,"bounded original-intent pure reconciliation query list required");
        var operations=new java.util.HashSet<OperationKey>();
        for(AllowedRead read:allowed) {
            require(catalog.containsIdentity(read.contract())&&operations.add(read.contract().operation()),
                    "pure query factory did not return the identical installed unique catalog contract");
            if(read.kind()==QueryKind.ORDINARY_INTERACTION){
                var attempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("guardian reconciliation requires the actual canonical original Attempt"));
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                org.xar.ck3.control.nativebridge.capabilities.interactions.GuardianReconciliationQueries.requireOriginalRequest(
                        request,original.command(),attempt);
            }
            if(read.kind()==QueryKind.WAR_EXIT_TRUCE) {
                var originalAttempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("war-exit truce requires the actual canonical original Attempt"));
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                org.xar.ck3.control.application.effects.NativeWarExitEffects.requireOriginalRequest(
                        request,original.command(),originalAttempt,before,actual);
            }
            if(read.kind()==QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE) {
                var originalAttempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("pending Close timeline requires the actual canonical original Attempt"));
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                RootPendingUiCloseReconciliation.requireRequest(request,original,originalAttempt,before,actual,archive.withSession(same));
            }
            if(read.kind()==QueryKind.UNKNOWN_SENTINEL_STATUS) {
                var originalAttempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("Status requires the actual unresolved primitive Attempt"));
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                RootUnknownSentinelReadProfile.requireRequest(request,original,originalAttempt,before,actual,archive.withSession(same));
            }
            if(read.kind()==QueryKind.ARMY_M5)requireArmyM5(read,identity,deadline);
            if(read.kind()==QueryKind.WINDOW2) {
                var actualAttempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("Window2 reconciliation requires the canonical original Attempt"));
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowReconciliationBinding.verify(
                        original,actualAttempt,identity,read.contract(),request,
                        org.xar.ck3.control.nativebridge.capabilities.army.ArmyWindowReads.driverGeneration(actual));
            }
            if(read.kind()==QueryKind.HOLY_ORDER_EMPLOYER) {
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                org.xar.ck3.control.nativebridge.capabilities.religion.PlayerHolyOrderContextRead.requireCanonicalReconciliation(
                        original,ActionTransitions.attempt(original.state()).orElseThrow(),identity,read.contract(),request);
            }
            if(read.kind()==QueryKind.MERCENARY_EMPLOYER) {
                var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
                org.xar.ck3.control.application.effects.NativeFinanceEffects.requireCanonicalMercenaryReconciliation(
                        original,ActionTransitions.attempt(original.state()).orElseThrow(),identity,read.contract(),request);
            }
            if(read.kind()==QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT)requireChildEducationFocus(read,original,identity,deadline);
            if(read.kind()==QueryKind.FAMILY_MARRIAGE_SEND) {
                var args=org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.arguments(read.arguments());
                require(args.scope()==org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.Scope.POST_SUBMISSION
                        &&args.actionId().equals(original.command().actionId())&&args.bodySha256().equals(original.bodySha256())
                        &&args.attemptRequestId().equals(identity.pending().requestId())&&args.senderIntent().equals(original.command().arguments()),
                        "marriage observation changed the original canonical sender or borrowed preparation scope");
            }
        }
        return allowed;
    }
    /** Only the original UNKNOWN focus Attempt can name this independent receipt; the domain replays its full pending producer. */
    private static void requireChildEducationFocus(AllowedRead read,ActionReceipt original,ReconciliationIdentity identity,Instant deadline) {
        require(original.state() instanceof ActionState.Unknown
                &&original.command().operation().value().equals(
                        org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.SUBMIT_STEP),
                "child education focus receipt requires its exact original UNKNOWN focus action");
        var request=PlanningReadRequest.newReconciliation(identity,read.contract().operation(),read.arguments(),deadline);
        org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries.canonicalReceiptArguments(request);
    }
    /** The three sole Army codecs/recipes validate the closed typed call, including terminal nullable IDs and cursor/character forms. */
    private static void requireArmyM5(AllowedRead read,ReconciliationIdentity identity,Instant deadline) {
        var methods=List.of(
                org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_BATTLE_CONTROL_SNAPSHOT_V1,
                org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_BATTLE_TRANSITION_V1,
                org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1);
        int matches=0;
        for(var method:methods) {
            final org.xar.ck3.control.nativebridge.capabilities.army.ArmyCalls.Call call;
            try {call=org.xar.ck3.control.nativebridge.capabilities.army.ArmyCallCodec.decode(method,new RawJson(OpportunityJson.encode(read.arguments())));}
            catch(IllegalArgumentException invalidClosedShape){continue;}
            var context=new org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.Context(
                    identity.factual(),identity.source(),identity.sessionId(),deadline);
            var recipe=org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes.prepare(call,context,
                    new org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes.NoFacts(),false);
            require(recipe instanceof org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes.Primitive,
                    "closed reconciliation M5 call must produce its sole native primitive recipe");
            var primitive=(org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes.Primitive)recipe;
            if(primitive.effect()==org.xar.ck3.control.nativebridge.capabilities.army.ArmyNativeRecipes.Effect.READ_ONLY
                    &&read.contract().operation().value().equals(primitive.request().step())
                    &&read.contract().requiredCapability().equals(primitive.request().requiredCapability())
                    &&read.contract().permissionKey().equals(primitive.permissionKey())&&read.contract().wireProfile()==primitive.wire())matches++;
        }
        require(matches==1,"reconciliation M5 read differs from the one complete strict Army typed call/native recipe");
    }
    private static AllowedRead select(List<AllowedRead> reads,PlanningReadRequest request,ReadContract<?> contract) {
        List<AllowedRead> matches=reads.stream().filter(read->read.contract()==contract&&read.arguments().equals(request.arguments())
                &&read.contract().operation().equals(request.operation())).toList();
        require(matches.size()==1,"query is not the exact original-intent contract and arguments in this reconciliation scope");
        return matches.getFirst();
    }
    private ExactRef decoder(ReadContract<?> contract){
        var bindings=catalog.installed().stream().filter(binding->binding.contract()==contract).toList();
        require(bindings.size()==1,"actual read decoder is not uniquely installed");return bindings.getFirst().decoderSource();
    }
    private ObjectNode descriptor(AllowedRead allowed) {
        ReadContract<?> contract=allowed.contract();var row=StrictJson.object().put("kind",allowed.kind().name())
                .put("contract_id",contract.contractId()).put("operation",contract.operation().value())
                .put("permission_key",contract.permissionKey()).put("permission_mode",contract.permissionMode().name())
                .put("wire_profile",contract.wireProfile().name()).put("guard_mode",contract.guardMode().name());
        if(contract.requiredCapability().isPresent())row.put("required_capability",contract.requiredCapability().orElseThrow());else row.putNull("required_capability");
        row.set("source",contract.sourceRef().toJson());row.set("decoder",decoder(contract).toJson());
        row.set("arguments",StrictJson.parse(OpportunityJson.encode(allowed.arguments()),64<<10));return row;
    }
    private void assertScope(Scope scope,ContinuityStorePort.Session same,Instant deadline)throws IOException{
        store.requireSession(same);require(active.get()==scope&&scope.session()==same,"reconciliation query escaped its original writer/session/thread");
        scope.lease().physical.assertCurrent(same);pending.verify(same,scope.lease().identity());
        require(scope.head().equals(same.head().digest()),"reconciliation observer published a new writer history/head");
        require(clock.instant().isBefore(scope.deadline())&&clock.instant().isBefore(deadline)
                &&clock.instant().isBefore(scope.lease().validUntil()),"reconciliation caller/source freshness expired");
        for(var pin:scope.pins())same.verifyPin(pin);
    }
    private ExactRef originalDriver(ContinuityStorePort.Session same,NativeEffectEvidence.FrameBasis basis)throws IOException{
        byte[] packet=read(same,basis.nativeFrame(),WriterContracts.MAX_PIN_BYTES);
        RawJson manifest=new RawJson(read(same,basis.driverFacts(),WriterContracts.MAX_PIN_BYTES));
        ExactRef ref=DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest);
        RawJson driver=new RawJson(read(same,ref,WriterContracts.MAX_PIN_BYTES));
        var frame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,packet);
        DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,driver,frame);return ref;
    }
    private Set<String> requireHelloAndSource(ContinuityStorePort.Session same,ReconciliationIdentity identity,OriginalEvidencePort originals)throws IOException {
        byte[] hello=originals.read(same,identity.capabilityEvidence(),1<<20);
        var body=org.xar.ck3.control.application.readiness.RootNativeCapabilities.framedObject(hello);
        require(new OpportunityJson.Text("hello").equals(body.get("type"))
                &&OpportunityJson.integer(body.get("pid"),"pid").longValueExact()==identity.factual().game().pid()
                &&OpportunityJson.integer(body.get("connection_generation"),"connection_generation").equals(identity.connectionGeneration())
                &&OpportunityJson.bool(body.get("ck3_build_match"),"ck3_build_match")
                &&"ready".equals(OpportunityJson.text(body.get("game_adapter_status"),"game_adapter_status")),
                "reconciliation original hello differs from actual held Game/session/adapter");
        var caps=new java.util.HashSet<String>();for(var cap:OpportunityJson.array(body.get("capabilities"),"capabilities"))caps.add(OpportunityJson.text(cap,"capability"));
        require(caps.contains("game.state.snapshot"),"reconciliation original hello lacks snapshot support");
        byte[] heartbeat=originals.read(same,identity.evidence().originalHeartbeat(),1<<20);
        require(new OpportunityJson.Text("heartbeat").equals(org.xar.ck3.control.application.readiness.RootNativeCapabilities.framedObject(heartbeat).get("type")),
                "reconciliation original heartbeat is not a complete actual packet");
        if(identity.evidence().completeSourceQualification().isEmpty()){store.requireSession(same);return Set.copyOf(caps);}
        var sourceRef=identity.evidence().completeSourceQualification().orElseThrow();
        var proof=RootArchivedNativeSourceReader.readData(sourceRef,originals.read(same,sourceRef,16<<20));
        require(identity.factual().machineId().equals(proof.machineId())
                &&identity.sessionId().equals(proof.sessionId())&&proof.source().equals(identity.source().sourceRef()),
                "reconciliation archived complete source proof crossed its actual source/session");
        var epochPin=same.capturePin(proof.sourceEpochManifest(),16<<20);
        RootArchivedNativeSourceReader.readEpochData(proof.sourceEpochManifest(),
                originals.read(same,proof.sourceEpochManifest(),16<<20),proof);
        RootArchivedNativeSourceReader.requireOriginalFiles(proof);
        same.verifyPin(epochPin);store.requireSession(same);
        return Set.copyOf(caps);
    }
    private byte[] read(ContinuityStorePort.Session same,ExactRef ref,int maximum)throws IOException{
        byte[] raw=originals.read(same,ref,maximum);exact(ref,raw);return raw;
    }
    private static WriterContracts.Pin pin(ContinuityStorePort.Session same,ExactRef ref)throws IOException{
        require(ref.bytes()>0&&java.nio.file.Path.of(ref.path()).isAbsolute(),"installed query source must have an exact physical path");
        var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);return pin;
    }
    private static void exact(ExactRef ref,byte[] bytes){require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"reconciliation complete original bytes/SHA differ");}
}

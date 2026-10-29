package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeDirectFixedWindowObservation;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One actual public QUERY retains its whole result. Only a positive completed CLOSE may use the original reducer. */
public final class RootDirectFixedWindowQueryAuthority implements DirectFixedWindowQueryAuthority {
    private final RootInstalledCatalog catalog;
    private final RootRuntimeContext context;
    private final ArmyRuntimeInstaller.Installed army;
    private final ArmyWindowService service;
    private final NativeDirectFixedWindowObservation proof;
    private final ThreadLocal<Capture> active = new ThreadLocal<>();

    private RootDirectFixedWindowQueryAuthority(RootInstalledCatalog actual) throws IOException {
        catalog=Objects.requireNonNull(actual);context=actual.context();army=actual.army().products();
        service=army.windows();proof=actual.remainingDomains().armyOrdinary().directWindows();
        requireInstalled();
    }
    /** Catalog installation precedes bindSession; resolving a current Root is deferred to the actual public invocation. */
    public static void install(RootInstalledCatalog completed)throws IOException {
        var actual=new RootDirectFixedWindowQueryAuthority(completed);var context=actual.context;
        context.bindings().bindDirectWindowQueryAuthority(context.game().generation(),context.game().sessionId(),context.source(),actual);
        actual.proof.bindOwnerQueryAuthority(actual::requireCapturedOwnerQuery);
        actual.service.bindPublicQueryAccess(actual::read);
    }
    private void requireInstalled()throws IOException {
        require(catalog.context()==context&&catalog.army().products()==army&&army.windows()==service
                &&catalog.remainingDomains().armyOrdinary().directWindows()==proof,
                "public owner-query source lost its actual installed products");
        catalog.remainingDomains().requireContext(context);context.game().verify();
    }
    @Override public void requireOwner(GameGeneration game,String sessionId,G2Source source)throws IOException {
        requireInstalled();require(context.game().generation().equals(game)&&context.game().sessionId().equals(sessionId)
                &&context.source().equals(source),"public owner-query authority belongs to another Game/source/session");
    }
    private RootApplicationSession root()throws IOException {
        if(!(context.actions() instanceof RootApplicationSession original))
            throw new IOException("actual Root session has not been bound to its public owner-query source");
        return original;
    }
    private void requireRoot(ContinuityStorePort.Session same,RootApplicationSession root)throws IOException {
        requireInstalled();context.writer().requireSession(same);
        require(context.actions()==root&&root.writer()==context.writer()&&root.archive()==context.archive()
                &&root.driver()==context.adopted(),"public owner query crossed its actual Root/writer/Driver");
        context.core().requireCurrentForAccess(same,root);
        require(context.core().activeBorrowedSession()==same,"public owner query escaped the original Core borrowed writer");
    }
    private ArmyWindowService.Reply read(ArmyCalls.Frame input,Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);ArmyWindowReads.kind(input.method());
        RootApplicationSession root=root();
        return root.withPublicStandalonePublication(deadline,same->{
          try {
            requireRoot(same,root);require(active.get()==null,"an original public query cannot be replaced recursively");
            List<ActionReceipt> unresolved=context.core().actions().withFrozen(same,
                    lease->lease.snapshot().actions().stream().filter(value->!value.settled()).toList());
            if(unresolved.isEmpty())return service.read(same,input,deadline);
            require(unresolved.size()==1,"public window QUERY cannot borrow multiple or unrelated pending actions");
            ActionReceipt pending=unresolved.getFirst();requireSelectedOriginal(input,pending);
            final Capture captured;
            try {captured=context.reconciliation().withPublicWindowSnapshot(same,pending,deadline,actual->{
                var lease=actual.physical();lease.assertCurrent(same);requireRoot(same,root);
                Complete current=lease.ordinary().orElseThrow(()->new IOException("actual public QUERY has no living original frame"));
                input.revision().requireCurrent(current.identity().frame().revision());
                var selectedContext=new ArmyTypes.Context(current.identity(),current.source(),current.sessionId(),deadline);
                var selection=new ArmyWindowReads.Selection(input,selectedContext,current.connectionGeneration(),
                        ArmyWindowReads.driverGeneration(current));
                var contract=army.windowContracts().issue(context.readCatalog(),selection);
                var request=army.windowContracts().request(selection);
                WriterContracts.Head original=same.head();
                var reading=new Reading(root,same,pending,actual,current,contract,request,original,deadline);
                // This scoped READ adapter borrows the same journal, endpoint, archive and actual
                // cache observer. Its private physical guard grants only this one public QUERY.
                var queries=new PlanningReadCoordinator(context.readCatalog(),context.core().journal(),
                        (head,queried,installed)->publicReadGuard(reading,head,queried,installed),context.transport(),
                        context.archive(),context.clock(),originalReadObserver(root));
                var result=queries.read(same,contract,request);
                if(!(result instanceof PlanningReadResult.Known<ArmyWindowCodec.Observation> known))
                    throw new UnavailableQuery((PlanningReadResult.Unavailable<ArmyWindowCodec.Observation>)result,current,request);
                var archive=context.archive().withSession(same);
                NativeRecordedEvidenceVerifier.requireRead(known.receipt(),archive);
                ExactRef reference=archive.preserveRead(known.receipt());
                require(reference.equals(archive.readReferenceOf(known.receipt()))&&archive.loadRead(reference).equals(known.receipt()),
                        "public QUERY lost its actual received receipt and immutable archive identity");
                lease.assertCurrent(same);
                return new Capture(this,root,same,pending,current,contract,request,
                        known,reference,archive,same.head().digest(),deadline);
            });}catch(UnavailableQuery unavailable){
                return service.presentUnavailable(input,unavailable.current,unavailable.request,unavailable.actual);
            }
            requireCapturedRead(same,pending,captured);
            boolean completionEligible=proof.publicQueryCanObserveOriginal(pending,captured.queryReceipt(),captured.current,captured.archive);
            // The actual public QUERY remains readable when the old CLOSE has no completed callback or its
            // old subject/connection is incompatible. Only the sole original proof decides observer eligibility.
            if(!completionEligible){
                var presentation=new ArmyTypes.Context(captured.current.identity(),captured.current.source(),
                        captured.current.sessionId(),captured.request.deadline());
                return new ArmyWindowService.KnownQuery(input,presentation,captured.known);
            }
            // This point is outside every physical/read freeze. Only the original coordinator can reduce the pending CLOSE.
            active.set(captured);
            try {
                ActionReceipt actual=context.actions().reconcileOriginalDirectWindowQuery(same,captured);requireRoot(same,root);
                require(actual.command().equals(pending.command())&&actual.bodySha256().equals(pending.bodySha256())
                        &&ActionTransitions.attempt(actual.state()).equals(ActionTransitions.attempt(pending.state()))
                        &&ActionTransitions.dispatch(actual.state()).equals(ActionTransitions.dispatch(pending.state())),
                        "owner-query continuation changed its original command/attempt/dispatch");
                require(captured.called&&captured.observed!=null,"actual owner-query continuation was not consumed exactly once");
                var original=proof.original(actual);
                require(original.ownerQuery().filter(value->value.originalQuery().equals(captured.queryReceipt())).isPresent(),
                        "canonical CLOSE did not retain this public QUERY's exact original observation");
                return service.presentPublicQuery(input,captured.known,original);
            }finally{active.remove();}
          }catch(ArmyWindowQueryFailure failure){
            Optional<ExactRef> diagnostic=Optional.empty();
            try {
                var originals=context.archive().withSession(same);
                if(failure.original().isPresent())diagnostic=Optional.of(originals.preserve(failure.original().orElseThrow()));
            }catch(RuntimeException archiveFailure){failure.addSuppressed(archiveFailure);}
            var typed=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.getMessage(),diagnostic);
            typed.initCause(failure);throw typed;
          }
        });
    }
    /** Private lexical custody inside one real physical callback; it is never exposed as a read permit. */
    private record Reading(RootApplicationSession root,ContinuityStorePort.Session session,ActionReceipt pending,
            RootReconciliationAuthority.PublicWindowSnapshot actual,Complete current,
            ReadContract<ArmyWindowCodec.Observation> contract,PlanningReadRequest request,
            WriterContracts.Head original,Instant deadline) { }
    private PlanningReadGuard publicReadGuard(Reading reading,WriterContracts.Head head,PlanningReadRequest request,
            ReadContract<?> contract) {
        try {
            var same=reading.session();var physical=reading.actual().physical();var current=reading.current();
            physical.assertCurrent(same);requireRoot(same,reading.root());
            require(contract==reading.contract()&&request==reading.request()&&context.readCatalog().containsIdentity(contract)
                    &&request.origin() instanceof CommandOrigin.Gameplay&&request.before().equals(current.identity())
                    &&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                    &&request.source().equals(context.source())&&request.sessionId().equals(current.sessionId())
                    &&request.operation().equals(contract.operation())&&head.digest().equals(reading.original().digest())
                    &&same.head().digest().equals(head.digest()),"public QUERY lost its identical installed request/contract or original writer point");
            requireSelectedQuery(reading.pending(),request.operation());
            boolean paused=OpportunityJson.bool(current.semantic().get("paused"),"paused");
            boolean mapReady=OpportunityJson.bool(current.semantic().get("map_ready"),"map_ready");
            var player=OpportunityJson.object(current.semantic().get("played_character"),"played_character");
            boolean alive=OpportunityJson.bool(player.get("alive"),"played_character.alive");
            require(paused&&mapReady&&alive
                    &&OpportunityJson.integer(player.get("character_id"),"played_character.character_id")
                        .equals(current.identity().frame().identity().player())
                    &&OpportunityJson.integer(current.semantic().get("episode_character_id"),"episode_character_id")
                        .equals(current.identity().frame().identity().player()),
                    "public QUERY requires its actual living paused map player and episode");
            require(context.clock().instant().isBefore(reading.deadline())&&context.clock().instant().isBefore(physical.validUntil()),
                    "public QUERY physical or caller lease expired");
            contract.requiredCapability().ifPresent(capability->{
                if(!physical.bridgeCapabilities().contains(capability))throw new IllegalArgumentException("actual public QUERY capability is absent from original HELLO");
            });
            var archive=context.archive().withSession(same);
            var capabilities=new OpportunityJson.Obj(java.util.Map.of("bridge_capabilities",new OpportunityJson.Arr(
                    physical.bridgeCapabilities().stream().sorted().<OpportunityJson.Value>map(OpportunityJson.Text::new).toList())));
            var bytes=new RawJson(DriverJson.encode(capabilities));var capabilityRef=archive.preserveMaterial(bytes);
            require(bytes.equals(archive.loadMaterial(capabilityRef)),"original public QUERY capability projection changed");
            var originals=new RootGuardEvidence.PhysicalReadOriginals(current,reading.actual().semantic(),physical.originalHello(),
                    physical.originalHeartbeat(),physical.sourceQualification().proof(),capabilityRef);
            String authorityId=context.core().authorityId();
            var basis=RootGuardEvidence.preservePhysicalRead(originals,contract.operation(),authorityId,archive,head);
            Instant until=physical.validUntil().isBefore(request.deadline())?physical.validUntil():request.deadline();
            var binding=new GuardEvidence(new CommandOrigin.Gameplay(current.identity()),context.source(),current.sessionId(),
                    current.connectionGeneration(),contract.operation(),current.originalEvidence(),physical.originalHello(),authorityId,
                    current.observedAt(),until,List.of(basis));
            require(RootGuardEvidence.loadFrame(binding,archive,context.frameLoader()).equals(current),
                    "public QUERY guard changed its actual complete native/Driver frame");
            RootGuardEvidence.requireHistory(binding,archive,same);physical.assertCurrent(same);
            return new PlanningReadGuard(binding,paused,mapReady,alive,current.fullBindingSha256());
        }catch(IOException failure){throw new UncheckedIOException("actual public owner QUERY guard is unavailable",failure);}
    }
    private static void requireSelectedQuery(ActionReceipt pending,OperationKey query)throws IOException {
        String selected=switch(pending.command().operation().value()) {
            case "close-war-declared-overview-v1" -> "query-war-declared-overview-v1";
            case "close-war-results-window-v1" -> "query-war-results-window-v1";
            default -> throw new IOException("public QUERY has no matching original fixed-window CLOSE");
        };
        require(selected.equals(query.value()),"public QUERY changed its exact original CLOSE family");
    }
    /** Forward to the identical bound Driver producer, preserving normal original READ publication. */
    private PlanningReadCoordinator.KnownReadObserver originalReadObserver(RootApplicationSession root) {
        return new PlanningReadCoordinator.KnownReadObserver() {
            @Override public void afterKnown(ContinuityStorePort.Session same,ReadContract<?> installed,PlanningReadResult.Known<?> actual) {
                try {requireRoot(same,root);root.capabilityRuntime().afterKnown(same,installed,actual);}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            }
            @Override public void afterUnavailable(ContinuityStorePort.Session same,ReadContract<?> installed,
                    PlanningReadRequest request,PlanningReadResult.Unavailable<?> actual,Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
                try {
                    requireRoot(same,root);
                    org.xar.ck3.control.application.reads.PlanningPublicReadCollection.afterUnavailable(same,installed,request,actual,attempted);
                    root.capabilityRuntime().afterUnavailable(same,installed,request,actual,attempted);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            }
        };
    }
    private static void requireSelectedOriginal(ArmyCalls.Frame input,ActionReceipt pending)throws IOException {
        String selected=ArmyWindowReads.kind(input.method())==ArmyWindowCodec.Kind.OVERVIEW
                ?"close-war-declared-overview-v1":"close-war-results-window-v1";
        require(pending.command().operation().value().equals(selected)&&pending.command().origin() instanceof CommandOrigin.Gameplay,
                "public QUERY may only continue its matching original direct CLOSE");
        var arguments=ArmyOrdinaryActionArguments.decode(pending.command().arguments());
        require(arguments.executionProfile()==ArmyOrdinaryActionArguments.ExecutionProfile.DIRECT_FIXED_WINDOW,
                "public QUERY cannot consume an ordinary, SDK or composite action profile");
        var attempt=ActionTransitions.attempt(pending.state()).orElseThrow(()->new IOException("original CLOSE has no canonical attempt"));
        var dispatch=ActionTransitions.dispatch(pending.state());
        if(dispatch.isPresent())require((dispatch.orElseThrow() instanceof NativeActionPort.AckReceived
                    ||dispatch.orElseThrow() instanceof NativeActionPort.Unknown)
                &&dispatch.orElseThrow().requestId().equals(attempt.requestId()),
                "public owner QUERY changed its retained original CLOSE outcome identity");
    }
    @Override public ActionPorts.PostconditionResult observeOriginalQuery(ContinuityStorePort.Session same,
            ActionReceipt originalPending,DirectFixedWindowQueryContinuation token,ActionPorts.DirectWindowQueryWork work)
            throws IOException,InterruptedException {
        Capture captured=requireCapture(same,originalPending,token);
        require(!captured.called,"original public QUERY continuation cannot be invoked twice");captured.called=true;
        final ActionPorts.PostconditionResult result;
        try {
            result=proof.withCapturedOwnerQuery(token,originalPending,captured.current,context.readCatalog(),captured.archive,()->{
                try {
                    require(captured.observed==null,"original owner-query observer cannot execute twice");
                    captured.observed=Objects.requireNonNull(work.apply());return captured.observed;
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
        }catch(UncheckedIOException failure){throw failure.getCause();}
        requireCapture(same,originalPending,token);
        require(result==captured.observed&&(result instanceof ActionPorts.DirectFixedWindowObserved||result instanceof ActionPorts.Pending),
                "original-query observer returned a foreign or unrelated effect");return result;
    }
    private void requireCapturedOwnerQuery(DirectFixedWindowQueryContinuation token,ActionReceipt pending,
            Complete current,ReadContract<?> contract,RootReadContractCatalog installed,ActionPorts.OutcomeArchive archive)
            throws IOException {
        Capture captured=active.get();if(captured==null)throw new IOException("no private actual owner-query continuation is active");
        requireCapture(captured.session,pending,token);
        require(current==captured.current&&contract==captured.contract&&installed==context.readCatalog()&&archive==captured.archive,
                "owner-query witness substituted its original frame/contract/catalog/archive");
    }
    private Capture requireCapture(ContinuityStorePort.Session same,ActionReceipt pending,DirectFixedWindowQueryContinuation token)
            throws IOException {
        Capture captured=active.get();
        if(!(token instanceof Capture actual)||captured!=actual||actual.owner!=this||actual.session!=same||!actual.pending.equals(pending))
            throw new IOException("foreign or detached public owner-query token");
        requireCapturedRead(same,pending,captured);return captured;
    }
    /** Read-only provenance revalidation grants no continuation or completion eligibility. */
    private void requireCapturedRead(ContinuityStorePort.Session same,ActionReceipt pending,Capture captured)throws IOException {
        require(captured.owner==this&&captured.session==same&&captured.pending.equals(pending),
                "public QUERY substituted its original readonly capture");
        requireRoot(same,captured.root);
        require(context.clock().instant().isBefore(captured.deadline)&&same.head().digest().equals(captured.head),
                "public owner-query lease expired or its canonical point changed before reduction");
        require(context.readCatalog().containsIdentity(captured.contract)&&captured.queryReceipt().request().equals(captured.request)
                &&captured.queryReceipt().contractId().equals(captured.contract.contractId())
                &&captured.queryRef.equals(captured.archive.readReferenceOf(captured.queryReceipt()))
                &&captured.archive.loadRead(captured.queryRef).equals(captured.queryReceipt()),
                "public owner QUERY lost its original installed descriptor/request/receipt");
        NativeRecordedEvidenceVerifier.requireRead(captured.queryReceipt(),captured.archive);
        var current=context.core().actions().withFrozen(same,lease->lease.find(captured.actionId()).orElseThrow(
                ()->new IllegalArgumentException("original CLOSE disappeared from its canonical writer")));
        require(current.equals(pending),"public owner QUERY cannot consume a changed or settled canonical pending");
    }
    private static final class Capture implements DirectFixedWindowQueryContinuation {
        private final RootDirectFixedWindowQueryAuthority owner;
        private final RootApplicationSession root;
        private final ContinuityStorePort.Session session;
        private final ActionReceipt pending;
        private final Complete current;
        private final ReadContract<ArmyWindowCodec.Observation> contract;
        private final PlanningReadRequest request;
        private final PlanningReadResult.Known<ArmyWindowCodec.Observation> known;
        private final ExactRef queryRef;
        private final ActionPorts.OutcomeArchive archive;
        private final String head;
        private final Instant deadline;
        private boolean called;
        private ActionPorts.PostconditionResult observed;
        private Capture(RootDirectFixedWindowQueryAuthority owner,RootApplicationSession root,ContinuityStorePort.Session session,
                ActionReceipt pending,Complete current,
                ReadContract<ArmyWindowCodec.Observation> contract,PlanningReadRequest request,
                PlanningReadResult.Known<ArmyWindowCodec.Observation> known,ExactRef queryRef,ActionPorts.OutcomeArchive archive,
                String head,Instant deadline) {
            this.owner=owner;this.root=root;this.session=session;this.pending=pending;this.current=current;
            this.contract=contract;this.request=request;this.known=known;this.queryRef=queryRef;this.archive=archive;
            this.head=head;this.deadline=deadline;
        }
        @Override public String actionId(){return pending.command().actionId();}
        @Override public PlanningReadReceipt queryReceipt(){return known.receipt();}
        @Override public ExactRef queryRef(){return queryRef;}
        @Override public Instant deadline(){return deadline;}
    }
    private static final class UnavailableQuery extends RuntimeException {
        private final PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> actual;
        private final Complete current;
        private final PlanningReadRequest request;
        private UnavailableQuery(PlanningReadResult.Unavailable<ArmyWindowCodec.Observation> actual,Complete current,PlanningReadRequest request){
            this.actual=actual;this.current=current;this.request=request;
        }
    }
    private static void require(boolean condition,String message)throws IOException {if(!condition)throw new IOException(message);}
}

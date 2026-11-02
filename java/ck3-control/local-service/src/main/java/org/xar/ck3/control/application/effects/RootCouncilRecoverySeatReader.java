package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.CouncilContinuationCoordinator;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilActionCodec;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootRuntimeContext;

/** Actual current seat DATA for one private original-positive-ACK recovery, never a setter. */
public final class RootCouncilRecoverySeatReader {
    private final RootRuntimeContext context;
    private final PrivateCouncilReads definitions;
    private final CouncilContinuationCoordinator continuation;
    private final NativeEffectEvidence.FrameLoader frames;
    private final int maximumPolls;

    public RootCouncilRecoverySeatReader(RootRuntimeContext actualContext, PrivateCouncilReads actualInstalledDefinitions,
            CouncilContinuationCoordinator actualInstalledCoordinator, NativeEffectEvidence.FrameLoader actualFreshFrameLoader,
            int maximumStatusPolls) {
        context=Objects.requireNonNull(actualContext);definitions=Objects.requireNonNull(actualInstalledDefinitions);
        continuation=Objects.requireNonNull(actualInstalledCoordinator);
        frames=Objects.requireNonNull(actualFreshFrameLoader);
        StrictJson.require(maximumStatusPolls>0&&maximumStatusPolls<=3000,"bounded recovered Council seat polling required");
        maximumPolls=maximumStatusPolls;
    }

    public List<PlanningReadReceipt> read(ContinuityStorePort.Session same,
            CouncilContinuationCoordinator.RecoveryOriginal original, GuardEvidence observation, Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(original);Objects.requireNonNull(observation);Objects.requireNonNull(deadline);
        context.writer().requireSession(same);context.requireCurrent(deadline);original.requireCurrent();
        StrictJson.require(continuation.currentRecoveryOriginal(same,original.command().actionId())==original
                &&observation.origin() instanceof CommandOrigin.Reconciliation,
                "current Council seat read requires this installed private role and its exact captured observation");
        var origin=original.command();var identity=observation.origin().requireReconciliation();
        StrictJson.require(origin.operation().value().equals(CouncilActionCodec.PRIVATE_ASSIGN)
                &&context.source().equals(origin.source())&&observation.source().equals(context.source())
                &&context.game().generation().equals(identity.factual().game())
                &&context.game().sessionId().equals(observation.sessionId()),
                "current Council seat recovery crossed its actual Root source/Game/session");
        var bound=context.archive().withSession(same);
        Complete frame=context.reconciliation().verifyArchived(observation,bound,same,context.originals());
        var checkpoint=original.seatCheckpoint().orElseThrow(()->new IOException("actual current Council tuple has no canonical checkpoint"));
        if(!checkpoint.reads().isEmpty())return retained(same,original,frame,checkpoint,deadline);
        StrictJson.require(original.observationGuard()==observation,
                "only a new actual same-capture observation may issue the first seat QUERY");
        var provenance=original.observationProvenance();
        StrictJson.require(provenance instanceof ObservationProvenance.FreshSnapshotQuery,
                "current Council seat requires its actual same-occurrence fresh READ proof");
        frames.verifyFreshSnapshotQuery((ObservationProvenance.FreshSnapshotQuery)provenance,frame,bound);
        var expected=GovernanceActionPreparation.councilRequest(origin,original.attempt().requestId());
        var guards=new SeatGuards(same,original,observation,frame,expected.position().key());
        var reads=new PlanningReadCoordinator(context.readCatalog(),context.core().journal(),guards,
                context.transport(),context.archive(),context.clock());
        var receipts=new ArrayList<PlanningReadReceipt>();
        Instant until=deadline.isBefore(observation.validUntil())?deadline:observation.validUntil();
        StrictJson.require(context.clock().instant().isBefore(until),"current Council seat observer expired before query");
        var query=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),definitions.query().operation(),
                new OpportunityJson.Obj(Map.of()).with("position_key",new OpportunityJson.Text(expected.position().key())),until);
        var transport=context.transport();
        return transport.withRecoveredSeatMailbox(original,observation,until,scope->{
            PlanningReadResult<CouncilPrivateCodec.Reply> current=reads.read(same,definitions.query(),query,
                    new DeferredLifecycle(original.seatReadLifecycle()));
            for(int polls=0;;polls++) {
                if(current instanceof PlanningReadResult.Unavailable<CouncilPrivateCodec.Reply> unavailable) {
                    unavailable.original().ifPresent(bound::preserve);
                    throw new IOException("actual current Council seat query unavailable: "+unavailable.reason());
                }
                var known=(PlanningReadResult.Known<CouncilPrivateCodec.Reply>)current;receipts.add(known.receipt());
                if(known.value() instanceof CouncilPrivateCodec.Terminal terminal) {
                    CouncilPrivateCodec.requireTerminalBinding(terminal,CouncilPrivateCodec.QUERY,PrivateCouncilReads.nativeFrame(query));
                    guards.requireCurrent();scope.consumeReadOnlyPrefix(receipts);scope.complete(known.receipt().original());
                    return List.copyOf(receipts);
                }
                StrictJson.require(polls<maximumPolls&&receipts.size()<16&&context.clock().instant().isBefore(until),
                        "current Council seat remains pending; no query replay or assignment permitted");
                Thread.sleep(10);
                current=reads.read(same,definitions.status(),new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),
                        definitions.status().operation(),new OpportunityJson.Obj(Map.of()),until),new DeferredLifecycle(original.seatReadLifecycle()));
            }
        });
    }

    private List<PlanningReadReceipt> retained(ContinuityStorePort.Session same,
            CouncilContinuationCoordinator.RecoveryOriginal original,Complete frame,
            CouncilContinuationCoordinator.SeatCheckpoint checkpoint,Instant deadline)throws IOException,InterruptedException {
        var bound=context.archive().withSession(same);var result=new ArrayList<PlanningReadReceipt>();
        for(var old:checkpoint.reads()) {
            ReadContract<CouncilPrivateCodec.Reply> contract=old.contractId().equals(definitions.query().contractId())?definitions.query():definitions.status();
            StrictJson.require(old.contractId().equals(contract.contractId())&&context.readCatalog().containsIdentity(contract)
                    &&old.request().operation().equals(contract.operation())&&old.request().before().equals(frame.identity())
                    &&old.request().source().equals(frame.source())&&old.request().sessionId().equals(frame.sessionId()),
                    "retained Council read checkpoint changed its actual tuple/contract/source");
            if(old.known().isEmpty()) {
                // Only this exact previous ID may be collected. An absent outcome never permits another QUERY.
                var actual=context.transport().collectOriginalOutcome(old.requestId(),deadline);
                if(actual.isPresent())original.seatReadLifecycle().received(same,contract,old.request(),old.requestId(),actual.orElseThrow());
                throw new IOException("original Council seat read remains collect-only; request_id="+old.requestId());
            }
            var receipt=bound.loadRead(old.known().orElseThrow());
            StrictJson.require(receipt.contractId().equals(old.contractId())&&receipt.request().equals(old.request())
                    &&receipt.requestId().equals(old.requestId())&&bound.readReferenceOf(receipt).equals(old.known().orElseThrow())
                    &&bound.requestReferenceOf(contract.prepare(receipt.request(),receipt.requestId())).equals(old.prepared())
                    &&old.outcome().filter(bound.referenceOf(receipt.original())::equals).isPresent(),
                    "retained Council read differs from its complete original checkpoint");
            contract.decode(receipt);result.add(receipt);
        }
        original.requireCurrent();return List.copyOf(result);
    }

    /** Received retains actual originals inside the physical scope; canonical commits occur after it closes. */
    private final class DeferredLifecycle implements PlanningReadCoordinator.ReadLifecycleObserver {
        private final PlanningReadCoordinator.ReadLifecycleObserver delegate;
        private ContinuityStorePort.Session same;
        private ReadContract<?> contract;
        private PlanningReadRequest request;
        private String requestId;
        private NativeActionPort.DispatchOutcome outcome;
        private boolean flushed;
        private DeferredLifecycle(PlanningReadCoordinator.ReadLifecycleObserver delegate){this.delegate=Objects.requireNonNull(delegate);}
        @Override public void prepared(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,String id,NativeRequest prepared)throws IOException {
            delegate.prepared(same,contract,request,id,prepared);
        }
        @Override public void received(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,String id,NativeActionPort.DispatchOutcome actual)throws IOException {
            StrictJson.require(outcome==null,"one original Council read cannot replace its received outcome");
            context.archive().withSession(same).preserve(actual);
            this.same=same;this.contract=contract;this.request=request;requestId=id;outcome=actual;
        }
        private void flush()throws IOException {
            if(outcome!=null&&!flushed){delegate.received(same,contract,request,requestId,outcome);flushed=true;}
        }
        @Override public void known(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadResult.Known<?> actual)throws IOException {
            flush();delegate.known(same,contract,actual);
        }
        @Override public void failed(ContinuityStorePort.Session same,ReadContract<?> contract,PlanningReadRequest request,
                Optional<NativeActionPort.DispatchOutcome> actual,String reason)throws IOException {
            flush();delegate.failed(same,contract,request,actual,reason);
        }
    }

    private final class SeatGuards implements PlanningReadCoordinator.ReadGuardPort {
        private final ContinuityStorePort.Session same;
        private final CouncilContinuationCoordinator.RecoveryOriginal original;
        private final GuardEvidence observation;
        private final Complete frame;
        private final String position;
        private final RootReadContractCatalog catalog=context.readCatalog();
        private final ThreadLocal<ReadinessAuthority.PhysicalReadLease> active=new ThreadLocal<>();
        private SeatGuards(ContinuityStorePort.Session same,CouncilContinuationCoordinator.RecoveryOriginal original,
                GuardEvidence observation,Complete frame,String position) {
            this.same=same;this.original=original;this.observation=observation;this.frame=frame;this.position=position;
        }
        private void requireCurrent()throws IOException {
            context.writer().requireSession(same);original.requireCurrent();
            var owned=original.seatCheckpointHead();
            StrictJson.require(original.observationGuard()==observation&&same.head().digest().equals(owned.digest())
                    &&same.head().state().sequence()==owned.state().sequence(),
                    "current Council seat scope lost its original private role/capture/head");
        }
        private void requireRequest(WriterContracts.Head locked,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
            requireCurrent();RootGuardChecks.session(()->same,locked);
            StrictJson.require(catalog.containsIdentity(contract)
                    &&(contract==definitions.query()||contract==definitions.status())
                    &&request.operation().equals(contract.operation())&&request.origin() instanceof CommandOrigin.Gameplay
                    &&request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId())
                    &&!request.deadline().isAfter(observation.validUntil())
                    &&context.clock().instant().isBefore(request.deadline()),"only the exact installed current Council QUERY/STATUS source is eligible");
            var args=request.arguments().members();
            StrictJson.require(contract==definitions.query()
                    ?args.size()==1&&new OpportunityJson.Text(position).equals(args.get("position_key")):args.isEmpty(),
                    "current Council seat query changed the original selected position or STATUS arguments");
        }
        private PlanningReadGuard binding(WriterContracts.Head locked,PlanningReadRequest request,ReadinessAuthority.PhysicalReadLease lease)throws IOException {
            RootGuardChecks.livingPaused(lease);
            StrictJson.require(lease.frame().identity().equals(frame.identity())&&lease.frame().source().equals(frame.source())
                    &&lease.frame().sessionId().equals(frame.sessionId())&&lease.frame().connectionGeneration().equals(frame.connectionGeneration())
                    &&lease.frame().originalEvidence().equals(frame.originalEvidence()),
                    "current Council seat read crossed its chosen fresh physical frame");
            var guard=RootGuardChecks.readBinding(lease,request.origin(),request.source(),request.sessionId(),request.operation(),request.deadline(),
                    context.archive().withSession(same),context.clock(),locked,original.attempt().guard().authorityId(),same,context.originals());
            return new PlanningReadGuard(guard,true,true,true,lease.frame().fullBindingSha256());
        }
        @Override public PlanningReadGuard verify(WriterContracts.Head locked,PlanningReadRequest request,ReadContract<?> contract) {
            try {
                requireRequest(locked,request,contract);var held=active.get();
                if(held!=null)return binding(locked,request,held);
                return context.readiness().currentDerivedCleanup(same,frame.identity(),request.deadline(),lease->binding(locked,request,lease));
            } catch(IOException failure){throw new UncheckedIOException("actual current Council seat source unavailable",failure);}
        }
        @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head locked,PlanningReadRequest request,ReadContract<?> contract) {
            StrictJson.require(active.get()!=null,"failed current Council read escaped its actual source scope");
            return verify(locked,request,contract);
        }
        @Override public <T>T withOriginalReadSource(WriterContracts.Head locked,PlanningReadRequest request,ReadContract<?> contract,Supplier<T> work) {
            try {
                requireRequest(locked,request,contract);StrictJson.require(active.get()==null,"current Council READ cannot replace a physical source");
                return context.readiness().currentDerivedCleanup(same,frame.identity(),request.deadline(),lease->{
                    binding(locked,request,lease);active.set(lease);
                    try{return Objects.requireNonNull(work).get();}finally{active.remove();}
                });
            }catch(IOException failure){throw new UncheckedIOException("actual current Council seat read scope unavailable",failure);}
        }
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.Pending;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusEffects;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocusQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** One actual physical Root's child-focus preparer, canonical pending receipt authority and archived domain replay. */
public final class RootChildEducationFocusRuntime implements ActionPorts.PreparationPort {
    public record Sources(ExactRef preparation,ExactRef effects,ExactRef decoder,ExactRef reconciliationProfile,List<ExactRef> completeProducers) {
        public Sources {
            completeProducers=List.copyOf(completeProducers);
            StrictJson.require(!completeProducers.isEmpty()&&completeProducers.size()<=64&&new HashSet<>(completeProducers).size()==completeProducers.size(),
                    "complete unique actual focus producer closure required");
            for(var ref:List.of(preparation,effects,decoder,reconciliationProfile))
                StrictJson.require(ref.bytes()>0&&completeProducers.contains(ref),"focus implementation is outside the actual complete source closure");
            completeProducers.forEach(ref->StrictJson.require(ref.bytes()>0,"nonempty actual focus source required"));
        }
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final ReadContract<Obj> query;
    private final ReadContract<Obj> ordinaryReceipt;
    private final ReadContract<Obj> receipt;
    private final ChildEducationFocusEffects effects;
    private final RootExecutableBindings.IssuedAction issued;
    private final RootDomainInstallation.FixedDomain domain;
    private final List<RootReadContractCatalog.InstalledRead> installedReads;
    public RootChildEducationFocusRuntime(RootRuntimeContext actual,Sources sources,ReadContract<Obj> sameFocusQuery,
            ReadContract<Obj> sameOrdinaryReceipt)throws IOException {
        context=Objects.requireNonNull(actual);this.sources=Objects.requireNonNull(sources);
        query=Objects.requireNonNull(sameFocusQuery);ordinaryReceipt=Objects.requireNonNull(sameOrdinaryReceipt);
        context.requireCurrent(context.clock().instant().plusSeconds(1));
        requireOrdinary(query,ChildEducationFocusQueries.QUERY_CONTRACT,ChildEducationFocus.QUERY_STEP);
        requireOrdinary(ordinaryReceipt,ChildEducationFocusQueries.RECEIPT_CONTRACT,ChildEducationFocus.RECEIPT_STEP);
        receipt=ChildEducationFocusQueries.reconciliationReceipt(ordinaryReceipt,sources.reconciliationProfile(),new CanonicalAdmission());
        effects=new ChildEducationFocusEffects(query,receipt,context.reads(),
                new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader()),context.frameLoader());
        var operation=new OperationKey(ChildEducationFocusIntent.STEP);
        var binding=new NativeEffectRegistry.Binding(operation,sources.preparation(),this,(command,attempt,dispatch)->{
            try{var same=context.borrowedSession();context.writer().requireSession(same);
                return effects.observe(same,command,attempt,dispatch,context.archive().withSession(same));}
            catch(IOException failure){throw new UncheckedIOException("actual focus observer has no original writer Session",failure);}
        });
        issued=new RootExecutableBindings.IssuedAction(new RootExecutableBindings.ActionBinding(binding,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.decoder()),
                effects.archivedVerifier(sources.effects(),()->{try{return context.borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}}));
        domain=new RootDomainInstallation.FixedDomain(issued.action(),Domain.marriage);
        installedReads=List.of(new RootReadContractCatalog.InstalledRead(receipt,sources.decoder()));
    }
    private void requireOrdinary(ReadContract<Obj> actual,String contractId,String operation) {
        StrictJson.require(actual.contractId().equals(contractId)&&actual.operation().value().equals(operation)&&actual.hasPureReplay()
                &&actual.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&actual.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                &&actual.wireProfile()==ReadContract.WireProfile.EXECUTE_STEP
                &&actual.permissionKey().equals(ChildEducationFocus.PERMISSION)&&actual.requiredCapability().isEmpty()
                &&sources.completeProducers().contains(actual.sourceRef()),"actual identical source-qualified ordinary focus contract required");
    }
    public void requireContext(RootRuntimeContext actual){StrictJson.require(context==actual,"focus products belong to another physical Root");}
    public RootExecutableBindings.IssuedAction issued(){return issued;}
    public RootDomainInstallation.FixedDomain domain(){return domain;}
    public List<RootReadContractCatalog.InstalledRead> installedReads(){return installedReads;}
    public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return this::allowedReads;}
    public Sources sources(){return sources;}
    @Override public NativeRequest prepare(ActionCommand command){throw new IllegalStateException("focus preparation requires its actual request ID and writer Session");}
    @Override public NativeRequest prepare(ActionCommand command,String requestId){throw new IllegalStateException("focus preparation requires the actual same writer Session");}
    @Override public NativeRequest prepare(Session same,ActionCommand command,String requestId) {
        StrictJson.text(requestId);
        try {
            context.writer().requireSession(same);context.requireCurrent(command.deadline());requireInstalled();
            StrictJson.require(ChildEducationFocusEffects.accepts(command)&&ActionCommandScope.current().filter(command::equals).isPresent(),
                    "focus preparation escaped the sole coordinator's actual command scope");
            return context.readiness().current(same,command.before(),command.deadline(),lease->{
                var before=lease.frame();requireCommandFrame(command,before);
                var intent=ChildEducationFocusIntent.fromJson(command.arguments());
                var args=ChildEducationFocusQueries.queryArguments(new ChildEducationFocusQueries.QueryArguments(
                        command.before().frame().revision(),ChildEducationFocusEffects.selection(intent)));
                var request=new PlanningReadRequest(command.before(),command.source(),command.sessionId(),query.operation(),args,command.deadline());
                var known=context.reads().read(same,query,request);
                StrictJson.require(known instanceof PlanningReadResult.Known<Obj>,"actual fresh native focus query is unavailable");
                var observed=(PlanningReadResult.Known<Obj>)known;
                NativeRequest result=effects.prepare(command,requestId,before,observed.receipt(),context.archive().withSession(same));
                return context.readiness().current(same,command.before(),command.deadline(),current->{
                    StrictJson.require(NativeEffectEvidence.basis(current.frame()).equals(NativeEffectEvidence.basis(before))
                            &&current.frame().fullBindingSha256().equals(before.fullBindingSha256()),"focus fresh query crossed its actual full Root frame");
                    return result;
                });
            });
        }catch(IOException failure){throw new UncheckedIOException("actual same-writer focus preparation unavailable",failure);}
    }
    private void requireInstalled(){StrictJson.require(context.readCatalog().containsIdentity(query)&&context.readCatalog().containsIdentity(ordinaryReceipt)
            &&context.readCatalog().containsIdentity(receipt),"actual focus ordinary/reconciliation contracts are not identically installed");}
    private List<RootReconciliationAuthority.AllowedRead> allowedReads(ActionReceipt original,ReconciliationIdentity identity,
            Complete current,Instant deadline)throws IOException {
        if(!ChildEducationFocusEffects.accepts(original.command()))return List.of();
        var same=context.borrowedSession();context.writer().requireSession(same);requireInstalled();
        var archive=context.archive().withSession(same);
        // The sole Root authority has already qualified either the live pending or
        // its exact historical writer state. Replay must retain that original,
        // including after the current head has legitimately settled it.
        var canonical=archive.loadReceipt(identity.pending().originalReceipt());
        StrictJson.require(canonical.equals(original)&&!canonical.settled()&&current.identity().equals(identity.factual())
                &&identity.pending().actionId().equals(canonical.command().actionId())&&identity.pending().bodySha256().equals(canonical.bodySha256())
                &&ActionTransitions.attempt(canonical.state()).filter(attempt->attempt.requestId().equals(identity.pending().requestId())).isPresent(),
                "focus receipt policy crossed the actual canonical original/factual frame");
        Optional<Pending> pending=canonicalPending(same,canonical,archive);
        if(pending.isEmpty())return List.of();
        var arguments=ChildEducationFocusQueries.receiptArguments(new ChildEducationFocusQueries.ReceiptArguments(current.identity().frame().revision(),pending.orElseThrow()));
        return List.of(new RootReconciliationAuthority.AllowedRead(receipt,arguments,RootReconciliationAuthority.QueryKind.CHILD_EDUCATION_FOCUS_RECEIPT));
    }
    private Optional<Pending> canonicalPending(Session same,ActionReceipt canonical,ActionPorts.OutcomeArchive archive)throws IOException {
        StrictJson.require(ChildEducationFocusEffects.accepts(canonical.command()),"canonical pending is not an exact focus action");
        var attempt=ActionTransitions.attempt(canonical.state()).orElseThrow(()->new IllegalArgumentException("focus canonical Attempt absent"));
        var dispatch=ActionTransitions.dispatch(canonical.state()).orElseThrow(()->new IllegalArgumentException("focus canonical original dispatch absent"));
        RootGuardEvidence.requireHistory(attempt.guard(),archive,same);
        var before=RootGuardEvidence.loadFrame(attempt.guard(),archive,context.frameLoader());
        var original=effects.loadPreparation(canonical.command(),attempt,before,archive);
        return effects.pending(canonical.command(),attempt,dispatch,original,archive);
    }
    private final class CanonicalAdmission implements ChildEducationFocusQueries.CanonicalAdmission {
        @Override public void verifyCurrent(PlanningReadRequest request,Pending pending) {
            try {
                var same=context.borrowedSession();context.writer().requireSession(same);requireInstalled();
                var identity=request.origin().requireReconciliation();
                context.reconciliation().current(same,identity,request.deadline(),lease->{
                    var archive=context.archive().withSession(same);
                    StrictJson.require(canonicalPending(same,lease.canonical(),archive).filter(pending::equals).isPresent(),
                            "focus receipt borrowed a fabricated legacy pending or another actual canonical Attempt");
                    requireRequest(request,pending,lease.canonical(),identity);lease.assertCurrent(same);return null;
                });
            }catch(IOException failure){throw new UncheckedIOException("actual canonical focus receipt admission unavailable",failure);}
        }
        @Override public void verifyOriginal(PlanningReadReceipt read,Pending pending) {
            try {
                var same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
                // PlanningReadCoordinator decodes before preserveRead(). The
                // native profile verifies the exact original request/response
                // and custody; actual guard ancestry is checked below. Archived
                // domain replay additionally requires the persisted complete read.
                var identity=read.request().origin().requireReconciliation();var canonical=archive.loadReceipt(identity.pending().originalReceipt());
                StrictJson.require(canonicalPending(same,canonical,archive).filter(pending::equals).isPresent(),
                        "archived focus receipt changed its true original canonical Attempt/pending");
                requireRequest(read.request(),pending,canonical,identity);
                for(var guard:List.of(read.before(),read.after())) {
                    Complete original=context.reconciliation().verifyArchived(guard.binding(),archive,same,context.originals());
                    StrictJson.require(original.identity().equals(identity.factual())&&original.source().equals(identity.source())
                            &&original.sessionId().equals(identity.sessionId())&&NativeEffectEvidence.basis(original).driverFacts().equals(identity.evidence().observationManifest()),
                            "archived focus receipt lost its actual original full Driver/Native factual frame");
                }
            }catch(IOException failure){throw new UncheckedIOException("actual archived canonical focus admission unavailable",failure);}
        }
    }
    private static void requireRequest(PlanningReadRequest request,Pending pending,ActionReceipt canonical,ReconciliationIdentity identity) {
        var original=identity.pending();
        StrictJson.require(original.actionId().equals(canonical.command().actionId())&&original.bodySha256().equals(canonical.bodySha256())
                &&original.requestId().equals(pending.actionRequestId())&&original.originalBefore().equals(canonical.command().before())
                &&request.source().equals(canonical.command().source())&&request.sessionId().equals(canonical.command().sessionId())
                &&identity.source().equals(canonical.command().source())&&identity.sessionId().equals(canonical.command().sessionId())
                &&request.operation().value().equals(ChildEducationFocus.RECEIPT_STEP),"focus read changed original request/command/source/session");
    }
    private static void requireCommandFrame(ActionCommand command,Complete actual){StrictJson.require(actual.identity().equals(command.before())
            &&actual.source().equals(command.source())&&actual.sessionId().equals(command.sessionId()),"focus command changed its actual current full Root frame");}
}

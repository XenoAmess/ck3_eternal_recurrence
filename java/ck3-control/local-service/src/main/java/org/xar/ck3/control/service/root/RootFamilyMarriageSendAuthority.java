package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.*;

/** Actual same-writer admission. ACTION_PREPARATION never creates or borrows a durable pending document. */
public final class RootFamilyMarriageSendAuthority implements FamilyMarriageSendReads.Authority {
    @FunctionalInterface public interface FreshWork<T> { T run() throws IOException; }
    /** Only the real ROOTv2/PUBLIC_QUERY adapter may validate a retained original against actual current leaf guards. */
    @FunctionalInterface public interface RootFreshAdmission {
        void requireOriginal(Session same,PlanningReadReceipt retainedRoot,ActionCommand command,Complete actualTarget,
                List<ExactRef> retainedFreshReads)throws IOException;
        /** The default adds no historical qualification; the real installed adapter owns any target scope. */
        default <T> T withinFreshTarget(Session same,ActionCommand command,Complete actualTarget,
                List<ExactRef> retainedFreshReads,FreshWork<T> work)throws IOException { return work.run(); }
    }
    /** All values are identical already-installed pure contracts from the sole native family's real prepared read products. */
    public record FreshContract(ReadContract<?> contract,int minimum,int maximum) {
        public FreshContract {
            Objects.requireNonNull(contract);need(contract.hasPureReplay()&&contract.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    "actual fresh contract must be ordinary-qualified and explicitly replayable");
            need(minimum>=0&&maximum>=1&&minimum<=maximum&&maximum<=32,"bounded actual fresh read cardinality required");
        }
    }
    public record FreshContracts(List<FreshContract> firstHeir,List<FreshContract> fulfillment,
            List<FreshContract> childMatrilineal,List<FreshContract> childDefault,List<FreshContract> ruler,RootFreshAdmission rootAdmission) {
        public FreshContracts {
            firstHeir=checked(firstHeir);fulfillment=checked(fulfillment);childMatrilineal=checked(childMatrilineal);childDefault=checked(childDefault);ruler=checked(ruler);
            Objects.requireNonNull(rootAdmission);
        }
        public List<FreshContract> forRoute(Route route) {
            return switch(route){case FIRST_HEIR->firstHeir;case FULFILL_BETROTHAL->fulfillment;case CHILD_MATRILINEAL->childMatrilineal;case CHILD_DEFAULT->childDefault;case RULER->ruler;};
        }
        private static List<FreshContract> checked(List<FreshContract> source) {
            List<FreshContract> copy=List.copyOf(source);need(!copy.isEmpty()&&copy.size()<=32,"complete actual fresh route contracts required");
            var ids=new HashSet<String>();int minimum=0,maximum=0;
            for(var contract:copy){need(ids.add(contract.contract().contractId()),"each actual source-owned fresh contract is listed once");minimum+=contract.minimum();maximum+=contract.maximum();}
            need(minimum>=1&&maximum<=32,"actual route must require source originals within its total finite bound");
            return copy;
        }
    }
    private final RootRuntimeContext context;
    private final RootFamilyBridge bridge;
    private final FreshContracts contracts;
    private record FreshVerified(ReadContract<?> contract,PlanningReadReceipt original,boolean retainedRoot) { }
    public RootFamilyMarriageSendAuthority(RootRuntimeContext actual,RootFamilyBridge sameBridge,FreshContracts sameInstalledFreshContracts) {
        context=Objects.requireNonNull(actual);bridge=Objects.requireNonNull(sameBridge);contracts=Objects.requireNonNull(sameInstalledFreshContracts);
    }
    @Override public void verifyCurrent(PlanningReadRequest request,Arguments args) {
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);context.requireCurrent(request.deadline());
            if(args.scope()==Scope.ACTION_PREPARATION) {
                ActionCommand command=ActionCommandScope.current().orElseThrow(()->new IllegalArgumentException("actual coordinator command scope is absent"));
                requireCommand(command,request,args);
                need(request.origin() instanceof CommandOrigin.Gameplay&&request.before().equals(command.before())&&request.deadline().equals(command.deadline()),
                        "before outbox query escaped the actual pre-INTENT gameplay frame/deadline");
                context.readiness().current(same,command.before(),command.deadline(),lease->{
                    var original=args.freshBasis().orElseThrow();var retained=bridge.replay(same,original.bridge());
                    need(retained.semantic().equals(original.snapshot()),"before outbox retained Bridge/native semantic basis differs");
                    need(lease.frame().originalEvidence().equals(lease.semantic().originalNativePacket()),
                            "before outbox current frame and held native packet differ");
                    var owned=RootFamilyBridge.nativeOwnedNoticeKeys(retained.frame(),context.archive().withSession(same));
                    RootFamilyBridge.requireCurrentBasis(command,retained.frame(),lease.frame(),owned);
                    var reads=requireFresh(same,args,command,retained.frame());
                    for(var verified:reads)if(!verified.retainedRoot())for(var guard:List.of(verified.original().before(),verified.original().after()))
                        need(context.clock().instant().isBefore(guard.binding().validUntil()),"actual target legality original expired before outbox preparation");
                    return null;
                });
            } else {
                var identity=request.origin().requireReconciliation();
                context.reconciliation().current(same,identity,request.deadline(),lease->{
                    requireCommand(lease.canonical().command(),request,args);
                    need(lease.attempt().requestId().equals(args.attemptRequestId()),"after outbox request changed canonical primitive Attempt");
                    requireBefore(same,args,lease.canonical().command());lease.assertCurrent(same);return null;
                });
            }
        } catch(IOException failure){throw new UncheckedIOException("actual same-writer family outgoing admission unavailable",failure);}
    }
    @Override public void verifyOriginal(PlanningReadReceipt read,Arguments args) {
        try {
            Session same=context.borrowedSession();context.writer().requireSession(same);var archive=context.archive().withSession(same);
            NativeRecordedEvidenceVerifier.requireRead(read,archive);
            if(args.scope()==Scope.ACTION_PREPARATION) {
                var basis=args.freshBasis().orElseThrow();var actual=bridge.replay(same,basis.bridge());
                need(actual.semantic().equals(basis.snapshot()),"archived actual Bridge/native semantic basis differs");
                var frame=actual.frame();
                need(frame.identity().equals(read.request().before())&&frame.source().equals(read.request().source())&&frame.sessionId().equals(read.request().sessionId()),
                        "archived preparation changed its complete original source frame");
                ActionCommand command=originalCommand(args,read,archive);
                var fresh=requireFresh(same,args,command,frame);NativeRequestChronology query=read.original().custody().orElseThrow();
                query.verify(read);
                for(var verified:fresh) {
                    var original=verified.original();
                    NativeRequestChronology predecessor=original.original().custody().orElseThrow();predecessor.verify(original);
                    need(query.session().equals(predecessor.session())&&query.custodyEpoch().equals(predecessor.custodyEpoch())
                            &&predecessor.responseReceived().order().compareTo(query.writeEntered().order())<0
                            &&!predecessor.responseReceived().observedAt().isAfter(query.writeEntered().observedAt()),
                            "actual fresh legality/root query did not precede outbox write in the same live custody interval");
                    if(!verified.retainedRoot())for(var guard:List.of(original.before(),original.after()))
                        need(!query.writeEntered().observedAt().isAfter(guard.binding().validUntil()),"actual nonROOT target legality lease did not cover the outbox write");
                }
                for(var guard:List.of(read.before(),read.after())) {
                    RootGuardEvidence.requireHistory(guard.binding(),archive,same);
                    Complete reconstructed=RootGuardEvidence.loadFrame(guard.binding(),archive,context.frameLoader());
                    need(NativeEffectEvidence.basis(reconstructed).equals(NativeEffectEvidence.basis(frame))
                            &&reconstructed.fullBindingSha256().equals(frame.fullBindingSha256()),"preparation query did not retain its actual full native/Driver frame");
                }
            } else {
                var identity=read.request().origin().requireReconciliation();ActionReceipt original=archive.loadReceipt(identity.pending().originalReceipt());
                requireCommand(original.command(),read.request(),args);requireBefore(same,args,original.command());
                for(var guard:List.of(read.before(),read.after())) {
                    Complete actual=context.reconciliation().verifyArchived(guard.binding(),archive,same,context.originals());
                    need(actual.identity().equals(identity.factual())&&actual.source().equals(identity.source())&&actual.sessionId().equals(identity.sessionId()),
                            "after outbox original lacks the actual canonical factual source/Driver basis");
                }
            }
        } catch(IOException failure){throw new UncheckedIOException("actual archived family outgoing admission unavailable",failure);}
    }
    /** No synthetic ActionCommand is reconstructed. The immutable original command is retained explicitly by the source owner. */
    private ActionCommand originalCommand(Arguments args,PlanningReadReceipt read,ActionPorts.OutcomeArchive archive)throws IOException {
        // During initial decode the genuine live scope owns the same command. Archive replay
        // finds that very command in the canonical original chain; neither path mints an action.
        var live=ActionCommandScope.current().filter(command->command.actionId().equals(args.actionId()));
        if(live.isPresent()){requireCommand(live.orElseThrow(),read.request(),args);return live.orElseThrow();}
        var same=context.borrowedSession();
        ActionReceipt canonical=ContinuityActionJournal.lookup(same.head().state(),args.actionId(),archive)
                .orElseThrow(()->new IOException("original preparation command has neither a live coordinator scope nor its canonical intent"));
        requireCommand(canonical.command(),read.request(),args);return canonical.command();
    }
    private List<FreshVerified> requireFresh(Session same,Arguments args,ActionCommand command,Complete actualFrame)throws IOException {
        return contracts.rootAdmission().withinFreshTarget(same,command,actualFrame,List.copyOf(args.freshBasis().orElseThrow().reads()),
                ()->requireFreshAt(same,args,command,actualFrame));
    }
    private List<FreshVerified> requireFreshAt(Session same,Arguments args,ActionCommand command,Complete actualFrame)throws IOException {
        var archive=context.archive().withSession(same);var basis=args.freshBasis().orElseThrow();var expected=contracts.forRoute(FamilyMarriageSendReads.sender(command).route());
        need(basis.reads().size()>=expected.stream().mapToInt(FreshContract::minimum).sum()
                &&basis.reads().size()<=expected.stream().mapToInt(FreshContract::maximum).sum(),"fresh source original count differs from actual route cardinalities");
        var result=new ArrayList<FreshVerified>();var used=new java.util.HashMap<ReadContract<?>,Integer>();var unique=new HashSet<ExactRef>();
        for(ExactRef ref:basis.reads()) {
            need(unique.add(ref),"the same actual fresh original cannot fill two route inputs");
            var pin=same.capturePin(ref,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            PlanningReadReceipt read=archive.loadRead(ref);NativeRecordedEvidenceVerifier.requireRead(read,archive);
            need(archive.readReferenceOf(read).equals(ref)&&read.request().source().equals(command.source())
                    &&read.request().sessionId().equals(command.sessionId()),"actual fresh route original changed immutable command/frame/source/session");
            var matching=expected.stream().filter(value->value.contract().contractId().equals(read.contractId())&&value.contract().operation().equals(read.request().operation())).toList();
            need(matching.size()==1,"fresh route original is not one actual source-owned contract");var requirement=matching.getFirst();var contract=requirement.contract();
            int count=used.merge(contract,1,Integer::sum);
            need(context.readCatalog().containsIdentity(contract)&&count<=requirement.maximum(),"fresh route contract is not the identical installed product or exceeds its native route bound");
            contract.replay(read);
            read.original().custody().orElseThrow(()->new IllegalArgumentException("actual fresh native read chronology absent")).verify(read);
            boolean exact=read.request().before().equals(command.before());
            for(var guard:List.of(read.before(),read.after())) {
                RootGuardEvidence.requireHistory(guard.binding(),archive,same);
                var frame=RootGuardEvidence.loadFrame(guard.binding(),archive,context.frameLoader());
                exact&=NativeEffectEvidence.basis(frame).equals(NativeEffectEvidence.basis(actualFrame))
                        &&frame.fullBindingSha256().equals(actualFrame.fullBindingSha256());
            }
            if(!exact)contracts.rootAdmission().requireOriginal(same,read,command,actualFrame,List.copyOf(basis.reads()));
            same.verifyPin(pin);result.add(new FreshVerified(contract,read,!exact));
        }
        for(var requirement:expected)need(used.getOrDefault(requirement.contract(),0)>=requirement.minimum(),"fresh route original closure is incomplete");
        for(var retained:result)if(retained.retainedRoot())need(result.stream().anyMatch(target->!target.retainedRoot()&&target.contract()!=retained.contract()),
                "historical ROOT qualification requires an actual different-contract exact target legality original");
        return List.copyOf(result);
    }
    private void requireBefore(Session same,Arguments args,ActionCommand command)throws IOException {
        var archive=context.archive().withSession(same);ExactRef reference=args.beforeRead().orElseThrow();PlanningReadReceipt before=archive.loadRead(reference);
        need(archive.readReferenceOf(before).equals(reference),"original preparation outbox read identity changed");
        Arguments actual=FamilyMarriageSendReads.arguments(before.request().arguments());
        need(actual.scope()==Scope.ACTION_PREPARATION&&actual.actionId().equals(command.actionId())&&actual.bodySha256().equals(ActionCodec.bodySha256(command))
                &&actual.attemptRequestId().equals(args.attemptRequestId())&&actual.senderIntent().equals(command.arguments()),"after query borrowed a different original preparation");
        // Source authority is replayed first; the same complete domain decoder used by
        // the installed before contract then validates envelope/context/storage/guards.
        verifyOriginal(before,actual);
        need(args.senderCharacterId().orElseThrow()==FamilyMarriageSendReads.materializedSender(before),
                "after query sender filter differs from the actual materialized original before context");
    }
    private static void requireCommand(ActionCommand command,PlanningReadRequest request,Arguments args) {
        need(command.origin() instanceof CommandOrigin.Gameplay&&command.actionId().equals(args.actionId())&&ActionCodec.bodySha256(command).equals(args.bodySha256())
                &&command.arguments().equals(args.senderIntent())&&command.source().equals(request.source())&&command.sessionId().equals(request.sessionId()),
                "read scope differs from actual coordinator's immutable command/intent/source/session");
        FamilyMarriageSendReads.sender(command);
    }
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
}


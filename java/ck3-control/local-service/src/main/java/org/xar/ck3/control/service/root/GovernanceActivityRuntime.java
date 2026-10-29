package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeFeastEffects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.governance.FeastObservationCollector;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One actual Activity installation serves planning, shared finance inputs, and independent effect reads. */
public final class GovernanceActivityRuntime implements FeastObservationCollector.ActivityReads,
        NativeFeastEffects.Reads, FinanceReadContracts.ExternalFeastInputs {
    private final RootRuntimeContext context;
    private final ActivityNativeContracts.Installation installation;
    private Session hostedSession;private ActivityNativeContracts.Packet lastHosted;
    /** Reuse an already archived same-frame query from this exact writer lease; mutations force another frame. */
    public ActivityNativeContracts.Packet hosted(Session same,PlanningRequest request)throws IOException {
        require(same,request);
        if(hostedSession==same&&lastHosted!=null&&lastHosted.receipt().request().before().equals(request.before())
                &&lastHosted.receipt().request().source().equals(request.source())&&lastHosted.receipt().request().sessionId().equals(request.sessionId())) {
            requireOriginal(same,lastHosted.receipt(),context.archive().withSession(same).readReferenceOf(lastHosted.receipt()));return lastHosted;
        }
        var read=installation.read(same,Query.HOSTED,context.reads(),request,new Obj(java.util.Map.of()));
        if(read instanceof PlanningReadResult.Unavailable<ActivityNativeContracts.Packet> unavailable)throw new IOException(unavailable.reason());
        var known=(PlanningReadResult.Known<ActivityNativeContracts.Packet>)read;requireOriginal(same,known.receipt(),known.originalReceipt());
        hostedSession=same;lastHosted=known.value();return lastHosted;
    }
    public GovernanceActivityRuntime(RootRuntimeContext context, ActivityNativeContracts.Installation actualInstallation) {
        this.context=Objects.requireNonNull(context);installation=Objects.requireNonNull(actualInstallation);
    }
    public ActivityNativeContracts.Installation definitions() { return installation; }
    /** Identity-preserving catalog entries; no second Activity contract is minted for a different consumer. */
    public List<RootReadContractCatalog.InstalledRead> installedReads(ExactRef actualCodecSource) {
        Objects.requireNonNull(actualCodecSource);StrictJson.require(actualCodecSource.bytes()>0,"actual Activity decoder source required");
        return installation.contracts().stream().map(contract->new RootReadContractCatalog.InstalledRead(contract,actualCodecSource)).toList();
    }
    @Override public GovernanceObservationSupplier.Read<FeastObservationCollector.ActivityPacket> read(
            FeastObservationCollector.ActivityQuery query,PlanningRequest request,Obj arguments) {
        Query nativeQuery=switch(query) {
            case DIAGNOSTIC->Query.DIAGNOSTIC;case HOSTED->Query.HOSTED;case STAGE_ONE->Query.STAGE1_OPTION;
            case STAGE_TWO->Query.STAGE2_OPTION;case LOCATION->Query.STAGE2_LOCATION;
        };
        try {
            Session borrowed=context.borrowedSession();require(borrowed,request);
            var result=installation.read(borrowed,nativeQuery,context.reads(),request,arguments);
            if(result instanceof PlanningReadResult.Unavailable<ActivityNativeContracts.Packet> unavailable)
                return new GovernanceObservationSupplier.Unavailable<>(unavailable.reason());
            var known=(PlanningReadResult.Known<ActivityNativeContracts.Packet>)result;
            requireOriginal(borrowed,known.receipt(),known.originalReceipt());
            if(nativeQuery==Query.HOSTED){hostedSession=borrowed;lastHosted=known.value();}
            return new GovernanceObservationSupplier.Known<>(new FeastObservationCollector.ActivityPacket(known.receipt(),known.value().result()),
                    List.of(known.originalReceipt(),installation.contract(nativeQuery).sourceRef()));
        } catch(IOException | IllegalArgumentException | IllegalStateException unavailable) {
            return new GovernanceObservationSupplier.Unavailable<>("actual same-Session Activity read unavailable: "+unavailable.getMessage());
        }
    }
    /** Existing finance consumer receives the unique strict START_INPUTS receipt and its actual original ref. */
    @Override public PlanningReadResult<PlanningReadReceipt> read(PlanningRequest request) {
        try { return read(context.borrowedSession(),request); }
        catch(IOException unavailable) { return unavailable(unavailable.getMessage()); }
    }
    @Override public PlanningReadResult<PlanningReadReceipt> read(Session borrowed,PlanningRequest request) {
        try {
            require(borrowed,request);
            var result=installation.read(borrowed,Query.START_INPUTS,context.reads(),request,
                    new Obj(java.util.Map.of()));
            if(result instanceof PlanningReadResult.Unavailable<ActivityNativeContracts.Packet> unavailable)
                return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
            var known=(PlanningReadResult.Known<ActivityNativeContracts.Packet>)result;
            requireOriginal(borrowed,known.receipt(),known.originalReceipt());
            StrictJson.require(known.value().receipt().equals(known.receipt()),"Activity packet changed its actual original receipt");
            return new PlanningReadResult.Known<>(known.receipt(),known.receipt(),known.originalReceipt());
        } catch(IOException | IllegalArgumentException | IllegalStateException unavailable) { return unavailable(unavailable.getMessage()); }
    }
    /** Independent before/after native reads retain original wire bytes; normalized JSON is not material evidence. */
    @Override public PlanningReadResult<RawJson> read(NativeFeastEffects.Query query,PlanningReadRequest request) {
        Query nativeQuery=query==NativeFeastEffects.Query.DIAGNOSTIC?Query.DIAGNOSTIC:Query.HOSTED;
        try {
            Session borrowed=context.borrowedSession();context.writer().requireSession(borrowed);
            context.requireCurrent(request.deadline());
            StrictJson.require(request.before().game().equals(context.game().generation()) && request.source().equals(context.source())
                    && request.sessionId().equals(context.game().sessionId()),"Feast effect read crossed actual runtime Game/source/session");
            var result=context.reads().read(borrowed,installation.contract(nativeQuery),request);
            if(result instanceof PlanningReadResult.Unavailable<ActivityNativeContracts.Packet> unavailable)
                return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
            var known=(PlanningReadResult.Known<ActivityNativeContracts.Packet>)result;
            requireOriginal(borrowed,known.receipt(),known.originalReceipt());
            return new PlanningReadResult.Known<>(decode(query,known.receipt()),known.receipt(),known.originalReceipt());
        } catch(IOException | IllegalArgumentException | IllegalStateException unavailable) { return unavailable(unavailable.getMessage()); }
    }
    @Override public RawJson decode(NativeFeastEffects.Query query,PlanningReadReceipt receipt) {
        Query nativeQuery=query==NativeFeastEffects.Query.DIAGNOSTIC?Query.DIAGNOSTIC:Query.HOSTED;
        var packet=installation.contract(nativeQuery).decode(receipt);
        StrictJson.require(packet.receipt().equals(receipt),"installed Activity decoder changed original receipt");
        return receipt.original().originalResultToken().orElseThrow(()->new IllegalArgumentException("actual Activity result token missing"));
    }
    private void require(Session borrowed,PlanningRequest request)throws IOException {
        context.writer().requireSession(borrowed);context.requireCurrent(request.deadline());
        StrictJson.require(request.before().game().equals(context.game().generation()) && request.before().machineId().equals(context.game().machineId())
                && request.source().equals(context.source()) && request.sessionId().equals(context.game().sessionId()),
                "Activity consumer crossed actual runtime Game/source/session");
    }
    private void requireOriginal(Session borrowed,PlanningReadReceipt receipt,ExactRef original)throws IOException {
        context.writer().requireSession(borrowed);
        context.archive().inSession(borrowed,archive->{
            StrictJson.require(archive.readReferenceOf(receipt).equals(original) && archive.loadRead(original).equals(receipt),
                    "Activity read is not its archived original receipt");return Boolean.TRUE;
        });
    }
    private static <T> PlanningReadResult<T> unavailable(String reason) {
        return new PlanningReadResult.Unavailable<>("actual Activity installation unavailable: "+reason,Optional.empty());
    }
}

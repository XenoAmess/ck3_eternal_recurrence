package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real domain admission and pure historical replay. It proves ledger custody, not current kinship or a native result. */
public final class RootFamilyDomainReadAuthority implements FamilyDomainReadBinding.Authority {
    private static final int MAX=org.xar.ck3.control.continuity.ContinuityJson.DOMAIN_MAX_BYTES;
    private final RootRuntimeContext context;
    public RootFamilyDomainReadAuthority(RootRuntimeContext actual) {context=Objects.requireNonNull(actual);}
    @Override public FamilyDomainReadBinding current(ContinuityStorePort.Session same,Slot slot,Selection selection,Obj selected)throws IOException {
        context.writer().requireSession(same);StrictJson.require(same==context.borrowedSession(),"family domain must borrow the actual original writer");
        var current=available(same,slot);Obj body=FamilyDomainSource.validate(slot,current.canonicalBody());requireSelected(body,selection,selected);
        var head=same.head();var registered=DomainBodies.reference(head.state(),slot).orElseThrow(()->new IllegalArgumentException("actual family body absent from canonical head"));
        StrictJson.require(registered.equals(current.reference()) && current.head().equals(same.persistedHead()),"family domain/head changed while binding the original");
        return new FamilyDomainReadBinding(slot,current.reference().payload(),head.state().sequence(),head.digest());
    }
    @Override public Obj verifyCurrent(PlanningReadRequest request,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException {
        context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);requireOperation(request,binding,selection);
        StrictJson.require(request.source().equals(context.source()) && request.sessionId().equals(context.game().sessionId())
                && request.before().game().equals(context.game().generation()),"family domain read escaped the actual current Game/source/session");
        var actual=current(same,binding.slot(),selection,selected);StrictJson.require(actual.equals(binding),"family domain changed before the actual native query");
        Obj body=FamilyDomainSource.validate(binding.slot(),available(same,binding.slot()).canonicalBody());requireArguments(request,body,selection,selected);return body;
    }
    @Override public Obj verifyOriginal(PlanningReadReceipt receipt,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException {
        var same=context.borrowedSession();context.writer().requireSession(same);var request=receipt.request();requireOperation(request,binding,selection);
        StrictJson.require(receipt.original().nativeOk(),"original native family domain query was not accepted");
        for(var guard:List.of(receipt.before(),receipt.after()))StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                && guard.binding().observed().equals(request.before()) && guard.binding().source().equals(request.source())
                && guard.binding().sessionId().equals(request.sessionId()) && guard.binding().operation().equals(request.operation()),"original family domain query lost its source/frame/session guards");
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()),"original domain query crossed its complete connection binding");
        StrictJson.require(same.head().state().machineId().equals(request.before().machineId()) && request.before().machineId().equals(request.source().machineId()),"original family domain machine/history differs");
        Obj body=originalBody(same,binding,selection,selected);requireArguments(request,body,selection,selected);return body;
    }
    /** Pure ledger provenance only; native receipt and current-relationship qualification remain separate above. */
    public static Obj originalBody(ContinuityStorePort.Session same,FamilyDomainReadBinding binding,Selection selection,Obj selected)throws IOException {
        var historical=same.requireHistoricalState(binding.sequence(),binding.headDigest());
        var registered=DomainBodies.reference(historical,binding.slot()).orElseThrow(()->new IllegalArgumentException("no registered full body at the actual historical head"));
        StrictJson.require(registered.payload().equals(binding.body()) && registered.contractSchema().equals(FamilyDomainSource.schema(binding.slot())),"original family body does not belong to the actual historical registry");
        var pin=same.capturePin(binding.body(),MAX);StrictJson.require(pin.identity().equals(registered.identity()),"historical family body native file identity changed");
        Obj body=FamilyDomainSource.validate(binding.slot(),same.readPinned(pin,MAX));requireSelected(body,selection,selected);
        same.verifyPin(pin);return body;
    }
    public static Slot slot(FamilyPorts.Query query) {
        return switch(query) {
            case FAMILY_RESULT,FAMILY_ALLIANCE->Slot.FAMILY;
            case MATRILINEAL_RESULT,MATRILINEAL_ALLIANCE->Slot.CHILD_MATRILINEAL;
            case DEFAULT_RESULT,DEFAULT_ALLIANCE->Slot.DEFAULT_MARRIAGE;
            default->throw new IllegalArgumentException("not a family original-domain read");
        };
    }
    public static Selection selection(FamilyPorts.Query query) {
        slot(query);return switch(query) {case FAMILY_RESULT,MATRILINEAL_RESULT,DEFAULT_RESULT->Selection.PENDING;default->Selection.RESOLVED;};
    }
    private static void requireOperation(PlanningReadRequest request,FamilyDomainReadBinding binding,Selection selection) {
        var query=java.util.Arrays.stream(FamilyPorts.Query.values()).filter(value->value.operation().equals(request.operation())).findFirst().orElseThrow(()->new IllegalArgumentException("unknown original-domain family operation"));
        StrictJson.require(slot(query)==binding.slot() && selection(query)==selection,"family domain operation/slot/selection differ");
        Obj encoded=OpportunityJson.object(request.arguments().get("original_domain"),"original_domain");
        StrictJson.require(FamilyDomainReadBinding.fromJson(encoded).equals(binding),"family domain authority differs from original canonical arguments");
    }
    private static DomainBodies.Available available(ContinuityStorePort.Session same,Slot slot)throws IOException {
        var value=same.readDomain(slot);if(value instanceof DomainBodies.Available actual)return actual;
        throw new IOException("original full family domain is unavailable: "+slot);
    }
    private static void requireSelected(Obj body,Selection selection,Obj selected) {
        Objects.requireNonNull(selected);Value actual=body.get(selection.field());
        // Cold material rechecks carry the exact original source_pending of a resolved relation.
        boolean materialRecheck=selection==Selection.PENDING && actual==Nil.INSTANCE && body.get("resolved") instanceof Obj resolved
                && selected.equals(resolved.get("source_pending")) && material(resolved);
        StrictJson.require(selected.equals(actual) || materialRecheck,"family read selected record differs from its full original domain body");
        if(selection==Selection.RESOLVED)StrictJson.require(body.get("pending")==Nil.INSTANCE && material(selected),"alliance read requires an actually resolved material relation");
    }
    private static void requireArguments(PlanningReadRequest request,Obj body,Selection selection,Obj selected) {
        StrictJson.require(selected.equals(request.arguments().get(selection.field())),"domain admission record differs from the actual native canonical request");
        if(selection==Selection.PENDING && body.get("pending")==Nil.INSTANCE)
            StrictJson.require(request.arguments().get("cold") instanceof Bool cold && cold.value()
                    && request.arguments().get("material_recheck") instanceof Bool recheck && recheck.value(),"resolved material source_pending needs the explicit original cold recheck");
    }
    private static boolean material(Obj value) {return value.get("status") instanceof Text status && (status.value().equals("marriage") || status.value().equals("betrothal"))
            && value.get("material_result") instanceof Bool material && material.value();}
}

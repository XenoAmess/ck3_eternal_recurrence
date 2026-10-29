package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Concrete installed family reads plus secondary views of the central ordinary/root/heir producers. */
public final class RootFamilyReadProducts {
    public record Sources(ExactRef obligationsNative,ExactRef obligationsDecoder,ExactRef focusNative,ExactRef focusDecoder) {
        public Sources {for(var source:List.of(obligationsNative,obligationsDecoder,focusNative,focusDecoder))StrictJson.require(source.bytes()>0,"actual family native/decoder source required");}
    }
    private final RootRuntimeContext context;
    private final Map<FamilyPorts.Query,ReadContract<Obj>> own;
    private final FamilyPorts.Reads reads;
    private final List<RootReadContractCatalog.InstalledRead> installed;
    public RootFamilyReadProducts(RootRuntimeContext context,Sources sources,InteractionCapabilities actualInteractions,
            RootInteractionContextProjection actualProjection,RootFamilyCampaignRead actualRoot,
            Map<FamilyPorts.Query,ReadContract<Obj>> otherActualContracts,Map<FamilyPorts.Query,FamilyPorts.ProjectedSource> otherActualProjections,
            List<RootReadContractCatalog.InstalledRead> otherInstalledReads) {
        this.context=Objects.requireNonNull(context);Objects.requireNonNull(sources);
        var contracts=new EnumMap<FamilyPorts.Query,ReadContract<Obj>>(FamilyPorts.Query.class);
        contracts.put(FamilyPorts.Query.CHILD_HOUSE_PREVIEW,FamilyObligationsQueries.contract(sources.obligationsNative(),(request,args)->admit(request)));
        var focus=ChildEducationFocusQueries.contracts(sources.focusNative(),(request,pending)->{
            admit(request);if(pending.isPresent())requirePending(request,pending.orElseThrow());
        });
        contracts.put(FamilyPorts.Query.CHILD_FOCUS,focus.query());contracts.put(FamilyPorts.Query.CHILD_FOCUS_RECEIPT,focus.receipt());own=Map.copyOf(contracts);
        for(var entry:otherActualContracts.entrySet()) {
            StrictJson.require(contracts.putIfAbsent(entry.getKey(),entry.getValue())==null,"duplicate actual family contract");
            StrictJson.require(otherInstalledReads.stream().filter(row->row.contract()==entry.getValue()).count()==1,"family native contract is not its identical installed read");
        }
        var projected=new EnumMap<FamilyPorts.Query,FamilyPorts.ProjectedSource>(FamilyPorts.Query.class);projected.putAll(otherActualProjections);
        StrictJson.require(projected.putIfAbsent(FamilyPorts.Query.EDUCATION_CONTEXT,new RootFamilyEducationRead(context,actualInteractions,actualProjection))==null,"duplicate shared education producer");
        StrictJson.require(projected.putIfAbsent(FamilyPorts.Query.CAMPAIGN_ROOT,actualRoot)==null,"duplicate shared campaign root producer");
        StrictJson.require(projected.putIfAbsent(FamilyPorts.Query.HEIR_LEGALITY,new RootFamilyHeirLegalityRead(context,actualInteractions,actualProjection,actualRoot))==null,"duplicate shared heir legality producer");
        StrictJson.require(projected.putIfAbsent(FamilyPorts.Query.RULER_CHOICES,new RootFamilyRulerChoicesRead(context,actualInteractions,actualProjection))==null,"duplicate shared ruler choices producer");
        reads=new FamilyPorts.Reads(contracts,projected);
        var all=new java.util.ArrayList<>(otherInstalledReads);all.add(new RootReadContractCatalog.InstalledRead(own.get(FamilyPorts.Query.CHILD_HOUSE_PREVIEW),sources.obligationsDecoder()));
        all.add(new RootReadContractCatalog.InstalledRead(focus.query(),sources.focusDecoder()));all.add(new RootReadContractCatalog.InstalledRead(focus.receipt(),sources.focusDecoder()));installed=List.copyOf(all);
    }
    public FamilyPorts.Reads reads() {return reads;}
    public List<RootReadContractCatalog.InstalledRead> installedReads() {return installed;}
    public void requireContext(RootRuntimeContext actual) {StrictJson.require(context==actual,"family reads belong to another physical Game context");}
    private void admit(PlanningReadRequest request) {
        try {
            context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            var matches=own.values().stream().filter(contract->contract.operation().equals(request.operation())).toList();
            StrictJson.require(matches.size()==1 && context.readCatalog().containsIdentity(matches.getFirst()) && request.source().equals(context.source())
                    && request.sessionId().equals(context.game().sessionId()) && request.before().game().equals(context.game().generation()),"family private read is not the identical current Root-installed source");
        } catch(IOException failure) {throw new UncheckedIOException(failure);}
    }
    /** The native pending DTO must be the actual latest unclosed history producer from this full held Driver. */
    private void requirePending(PlanningReadRequest request,ChildEducationFocus.Pending pending) {
        try {
            var same=context.borrowedSession();context.readiness().current(same,request.before(),request.deadline(),lease->{
                var history=lease.driver().driver().commandHistory().stream().map(row->DriverJson.object(row.originalRow().json(),DriverJson.MAX_NATIVE_BYTES)).toList();
                Obj original=FamilyHistory.focusPending(history,lease.frame().semantic()).orElseThrow(()->new IllegalArgumentException("focus receipt lacks an actual unresolved original Driver submission"));
                StrictJson.require(original.equals(DriverJson.object(ChildEducationFocus.verifyPending(pending).bytes(),DriverJson.MAX_NATIVE_BYTES)),"focus pending differs from the actual unclosed original history");return null;
            });
        } catch(IOException failure) {throw new UncheckedIOException(failure);}
    }
}

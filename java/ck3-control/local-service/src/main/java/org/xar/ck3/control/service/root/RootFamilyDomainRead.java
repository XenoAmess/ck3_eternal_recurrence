package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Adds real ledger ancestry before the one installed native RESULT/ALLIANCE producer prepares its canonical context. */
public final class RootFamilyDomainRead implements FamilyPorts.ProjectedSource {
    @FunctionalInterface public interface Arguments {Obj canonical(InteractionModels.Context actual,Obj domainBoundFlat);}
    private final RootRuntimeContext context;private final FamilyPorts.Query query;private final ReadContract<Obj> contract;
    private final RootInteractionContextProjection projection;private final FamilyDomainReadBinding.Authority originals;private final Arguments arguments;
    public RootFamilyDomainRead(RootRuntimeContext actual,FamilyPorts.Query query,ReadContract<Obj> identicalNativeContract,
            RootInteractionContextProjection sameProjection,FamilyDomainReadBinding.Authority actualOriginals,Arguments actualCanonicalProducer) {
        context=Objects.requireNonNull(actual);this.query=Objects.requireNonNull(query);contract=Objects.requireNonNull(identicalNativeContract);
        projection=Objects.requireNonNull(sameProjection);originals=Objects.requireNonNull(actualOriginals);arguments=Objects.requireNonNull(actualCanonicalProducer);
        RootFamilyDomainReadAuthority.slot(query);StrictJson.require(contract.operation().equals(query.operation()),"family domain query/contract differ");
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest original,Obj flat) {
        StrictJson.require(!flat.members().containsKey("original_domain"),"a planning DTO cannot supply its own ledger ancestry");
        try {
            var same=context.borrowedSession();return context.collector().currentPlanning(same,original,original.deadline(),(request,lease)->{
                StrictJson.require(context.readCatalog().containsIdentity(contract),"family domain native contract is not the identical Root-installed read");
                var selection=RootFamilyDomainReadAuthority.selection(query);Obj selected=OpportunityJson.object(flat.get(selection.field()),selection.field());
                var binding=originals.current(same,RootFamilyDomainReadAuthority.slot(query),selection,selected);
                Obj canonical=arguments.canonical(projection.project(lease.frame(),original.deadline()),flat.with("original_domain",binding.toJson()));
                var read=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),query.operation(),canonical,original.deadline());
                originals.verifyCurrent(read,binding,selection,selected);
                var result=context.reads().read(same,contract,read);context.writer().requireSession(same);
                return new FamilyPorts.ProjectedRead(canonical,result);
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual original-domain family read unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {
        StrictJson.require(original.contractId().equals(contract.contractId()) && original.request().operation().equals(query.operation()),"family domain archive contract differs");
        var selection=RootFamilyDomainReadAuthority.selection(query);
        try {originals.verifyOriginal(original,FamilyDomainReadBinding.fromJson(OpportunityJson.object(original.request().arguments().get("original_domain"),"original_domain")),
                selection,OpportunityJson.object(original.request().arguments().get(selection.field()),selection.field()));}
        catch(IOException failure) {throw new UncheckedIOException("actual historical family domain body unavailable",failure);}
        return contract.replay(original);
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The current first-heir relation reads one genuine ROOT then binds that exact original to its one native leaf. */
public final class RootFamilyRootBoundRead implements FamilyPorts.ProjectedSource {
    @FunctionalInterface public interface Arguments {Obj canonical(InteractionModels.Context actual,Obj rootBoundFlat);}
    private final RootRuntimeContext context;private final RootInteractionContextProjection projection;private final RootFamilyCampaignRead root;
    private final ReadContract<Obj> contract;private final Arguments arguments;
    public RootFamilyRootBoundRead(RootRuntimeContext actual,RootInteractionContextProjection sameProjection,RootFamilyCampaignRead sameRoot,
            ReadContract<Obj> identicalRelationContract,Arguments actualCanonicalProducer) {
        context=Objects.requireNonNull(actual);projection=Objects.requireNonNull(sameProjection);root=Objects.requireNonNull(sameRoot);
        contract=Objects.requireNonNull(identicalRelationContract);arguments=Objects.requireNonNull(actualCanonicalProducer);
        StrictJson.require(contract.operation().equals(FamilyPorts.Query.CURRENT_RELATION.operation()),"root-bound relation uses the exact native operation");
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest original,Obj flat) {
        StrictJson.require(flat.members().keySet().equals(java.util.Set.of("expected_native_revision"))
                && new IntegerValue(original.before().frame().identity().nativeRevision()).equals(flat.get("expected_native_revision")),"root-bound relation expected native revision differs");
        try {
            var same=context.borrowedSession();return context.collector().currentPlanning(same,original,original.deadline(),(request,lease)->{
                StrictJson.require(context.readCatalog().containsIdentity(contract),"relation leaf is not the identical installed native read");
                var actual=projection.project(lease.frame(),original.deadline());
                var rootResult=root.current(same,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),contract.operation(),flat,original.deadline()));
                if(rootResult instanceof PlanningReadResult.Known<Obj> known) {
                    var basis=root.bind(known,actual);Obj canonical=arguments.canonical(actual,FamilyRootBinding.arguments(basis,flat));
                    var result=context.reads().read(same,contract,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),contract.operation(),canonical,original.deadline()));
                    context.writer().requireSession(same);return new FamilyPorts.ProjectedRead(canonical,result);
                }
                var unavailable=(PlanningReadResult.Unavailable<Obj>)rootResult;
                return new FamilyPorts.ProjectedRead(new Obj(Map.of()),new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original()));
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual ROOT-bound current relation unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {
        StrictJson.require(original.request().operation().equals(contract.operation()) && original.contractId().equals(contract.contractId()),"root-bound relation archive contract differs");
        return root.replayAt(original,()->contract.replay(original));
    }
}

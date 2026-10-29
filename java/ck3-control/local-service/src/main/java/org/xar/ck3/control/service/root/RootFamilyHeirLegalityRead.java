package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Family view of the identical typed heir-legality producer, including its original root receipt. */
public final class RootFamilyHeirLegalityRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;private final InteractionCapabilities interactions;
    private final RootInteractionContextProjection projection;private final RootFamilyCampaignRead root;
    public RootFamilyHeirLegalityRead(RootRuntimeContext context,InteractionCapabilities actualInteractions,
            RootInteractionContextProjection actualProjection,RootFamilyCampaignRead actualRoot) {
        this.context=Objects.requireNonNull(context);interactions=Objects.requireNonNull(actualInteractions);
        projection=Objects.requireNonNull(actualProjection);root=Objects.requireNonNull(actualRoot);
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj flat) {
        StrictJson.require(flat.members().keySet().equals(Set.of("expected_native_revision"))
                && new IntegerValue(request.before().frame().identity().nativeRevision()).equals(flat.get("expected_native_revision")),"family legality expected native revision differs");
        try {
            var same=context.borrowedSession();return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                var actual=projection.project(lease.frame(),request.deadline());var result=interactions.queryObservedFirstHeirMarriageLegalityV1(same,actual);
                if(result instanceof PlanningReadResult.Known<InteractionModels.HeirMarriageLegality> known)
                    return new FamilyPorts.ProjectedRead(known.receipt().request().arguments(),FamilyHeirNativeProjection.project(known,root.originals()));
                var unavailable=(PlanningReadResult.Unavailable<InteractionModels.HeirMarriageLegality>)result;
                return new FamilyPorts.ProjectedRead(new Obj(Map.of()),new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original()));
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual typed heir legality unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {return root.replayAt(original,()->FamilyHeirNativeProjection.project(RootFamilyTypedReplay.read(context,original,InteractionModels.HeirMarriageLegality.class),root.originals()).value());}
}

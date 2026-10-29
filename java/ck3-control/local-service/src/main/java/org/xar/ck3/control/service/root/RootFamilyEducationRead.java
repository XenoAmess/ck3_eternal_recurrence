package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Secondary family view of the one installed typed ordinary producer. It registers no native contract. */
public final class RootFamilyEducationRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;
    private final InteractionCapabilities interactions;
    private final RootInteractionContextProjection projection;
    public RootFamilyEducationRead(RootRuntimeContext context, InteractionCapabilities actualInteractions,
            RootInteractionContextProjection actualProjection) {
        this.context=Objects.requireNonNull(context);interactions=Objects.requireNonNull(actualInteractions);
        projection=Objects.requireNonNull(actualProjection);
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj familyArguments) {
        try {
            context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                var actual=projection.project(lease.frame(),request.deadline());
                Obj canonical=FamilyEducationNativeProjection.applicationArguments(actual,familyArguments);
                var result=interactions.queryCharacterInteractionOrdinaryV1(actual,FamilyEducationNativeProjection.intent(actual,familyArguments));
                PlanningReadResult<Obj> projected;
                if(result instanceof PlanningReadResult.Known<InteractionModels.OrdinaryContext> known)projected=FamilyEducationNativeProjection.project(known);
                else {var unavailable=(PlanningReadResult.Unavailable<InteractionModels.OrdinaryContext>)result;projected=new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());}
                context.writer().requireSession(same);return new FamilyPorts.ProjectedRead(canonical,projected);
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual shared ordinary education read unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {return FamilyEducationNativeProjection.project(RootFamilyTypedReplay.read(context,original,InteractionModels.OrdinaryContext.class)).value();}
}

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

/** Refreshes choices through the same central typed marriage producer; Driver publication remains Root-owned. */
public final class RootFamilyRulerChoicesRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;private final InteractionCapabilities interactions;private final RootInteractionContextProjection projection;
    public RootFamilyRulerChoicesRead(RootRuntimeContext context,InteractionCapabilities sameInteractions,RootInteractionContextProjection actualProjection) {
        this.context=Objects.requireNonNull(context);interactions=Objects.requireNonNull(sameInteractions);projection=Objects.requireNonNull(actualProjection);
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj flat) {
        StrictJson.require(flat.members().keySet().equals(Set.of("expected_revision"))
                && new IntegerValue(request.before().frame().revision()).equals(flat.get("expected_revision")),"ruler choice expected public revision differs");
        try {
            var same=context.borrowedSession();return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                var actual=projection.project(lease.frame(),request.deadline());var result=interactions.queryArrangeMarriageChoices(actual);
                if(result instanceof PlanningReadResult.Known<InteractionModels.MarriageChoices> known)
                    return new FamilyPorts.ProjectedRead(known.receipt().request().arguments(),FamilyMarriageChoicesProjection.project(known));
                var unavailable=(PlanningReadResult.Unavailable<InteractionModels.MarriageChoices>)result;
                return new FamilyPorts.ProjectedRead(new Obj(Map.of()),new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original()));
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual ruler choices unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {return FamilyMarriageChoicesProjection.project(RootFamilyTypedReplay.read(context,original,InteractionModels.MarriageChoices.class)).value();}
}

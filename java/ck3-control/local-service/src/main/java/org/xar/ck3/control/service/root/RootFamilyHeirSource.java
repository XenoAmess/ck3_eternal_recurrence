package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Supplies the typed InteractionCapabilities instance from the sole actual primary-title campaign-root read. */
public final class RootFamilyHeirSource implements InteractionCapabilities.RootHeirSource {
    private final RootRuntimeContext context;
    private final RootFamilyCampaignRead root;
    public RootFamilyHeirSource(RootRuntimeContext context,RootFamilyCampaignRead actualRoot) {this.context=Objects.requireNonNull(context);root=Objects.requireNonNull(actualRoot);}
    @Override public InteractionModels.HeirSubject requireSubject(InteractionModels.Context actual,PlanningReadResult.Known<InteractionModels.HeirSubject> known) {
        return FamilyHeirNativeProjection.requireSubject(known,actual,root.originals());
    }
    @Override public InteractionModels.HeirSubject requireSubject(Session same,InteractionModels.Context actual,PlanningReadResult.Known<InteractionModels.HeirSubject> known) {
        try {context.writer().requireSession(same);return requireSubject(actual,known);}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    @Override public PlanningReadResult<InteractionModels.HeirSubject> read(InteractionModels.Context actual) {
        try {return read(context.borrowedSession(),actual);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    @Override public PlanningReadResult<InteractionModels.HeirSubject> read(Session same,InteractionModels.Context actual) {
        try {
            context.requireCurrent(actual.deadline());context.writer().requireSession(same);
            return context.readiness().current(same,actual.before(),actual.deadline(),lease->{
                RootInteractionContextProjection.requireExact(lease.frame(),actual);
                var requested=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),
                        new OperationKey("query-campaign-root-context-v1"),new Obj(Map.of()),actual.deadline());
                var result=root.current(same,requested);
                if(result instanceof PlanningReadResult.Known<Obj> known)return FamilyHeirNativeProjection.subject(known,actual,root.originals());
                var unavailable=(PlanningReadResult.Unavailable<Obj>)result;
                return new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original());
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual primary-title heir source unavailable",failure);}
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Concrete held-session adapter of the identical five-candidate contract. No second native producer. */
public final class RootFamilyMarriageProjectionRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;
    private final RootInteractionContextProjection projection;
    private final FamilyMarriageProjectionQueries queries;
    private final RootFamilyCampaignRead root;
    public RootFamilyMarriageProjectionRead(RootRuntimeContext actualContext,RootInteractionContextProjection actualProjection,
            FamilyMarriageProjectionQueries actualQueries,RootFamilyCampaignRead sameRoot) {
        context=Objects.requireNonNull(actualContext);projection=Objects.requireNonNull(actualProjection);queries=Objects.requireNonNull(actualQueries);root=Objects.requireNonNull(sameRoot);root.requireContext(context);
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj flat) {
        try {
            var same=context.borrowedSession();context.writer().requireSession(same);
            StrictJson.require(context.readCatalog().containsIdentity(queries.contract()),"five-candidate read is not its identical Root-installed contract");
            return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                var actual=projection.project(lease.frame(),request.deadline());Obj canonical=queries.canonicalArguments(actual,flat);
                var read=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),queries.contract().operation(),canonical,request.deadline());
                return new FamilyPorts.ProjectedRead(canonical,context.reads().read(same,queries.contract(),read));
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual native marriage projection unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {
        StrictJson.require(context.readCatalog().containsIdentity(queries.contract()),"archived marriage projection contract was not installed");
        return root.replayAt(original,()->queries.contract().replay(original));
    }
    public static FamilyMarriageProjectionQueries.Originals originals(RootRuntimeContext actual) {
        Objects.requireNonNull(actual);
        return new FamilyMarriageProjectionQueries.Originals() {
            private ActionPorts.OutcomeArchive archive() {
                try {var same=actual.borrowedSession();actual.writer().requireSession(same);return actual.archive().withSession(same);}
                catch(IOException failure) {throw new UncheckedIOException(failure);}
            }
            @Override public PlanningReadReceipt load(ExactRef original) {return archive().loadRead(original);}
            @Override public ExactRef referenceOf(PlanningReadReceipt original) {return archive().readReferenceOf(original);}
        };
    }
}

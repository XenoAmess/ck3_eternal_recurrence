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

/** Actual held Driver -> one canonical child contract -> central read coordinator, with pure archive replay. */
public final class RootFamilyChildRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;
    private final RootInteractionContextProjection projection;
    private final FamilyChildMarriageQueries queries;
    private final FamilyPorts.Query query;
    private final ReadContract<Obj> contract;
    public RootFamilyChildRead(RootRuntimeContext actualContext,RootInteractionContextProjection actualProjection,
            FamilyChildMarriageQueries actualQueries,FamilyPorts.Query childQuery){
        context=Objects.requireNonNull(actualContext);projection=Objects.requireNonNull(actualProjection);queries=Objects.requireNonNull(actualQueries);query=Objects.requireNonNull(childQuery);
        StrictJson.require(query==FamilyPorts.Query.CHILD_SUBJECT||query==FamilyPorts.Query.CHILD_VALUE,"child adapter requires exact child route");
        contract=query==FamilyPorts.Query.CHILD_SUBJECT?queries.subject():queries.value();StrictJson.require(contract.operation().equals(query.operation()),"child route differs from identical actual contract");
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest request,Obj flat){
        try{
            context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            return context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
                StrictJson.require(context.readCatalog().containsIdentity(contract),"child query is not the identical installed Root read");
                var actual=projection.project(lease.frame(),request.deadline());
                Obj canonical=query==FamilyPorts.Query.CHILD_SUBJECT?FamilyChildMarriageQueries.canonicalSubject(actual,flat):queries.canonicalValue(actual,flat);
                var read=new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),contract.operation(),canonical,actual.deadline());
                var result=context.reads().read(same,contract,read);context.writer().requireSession(same);return new FamilyPorts.ProjectedRead(canonical,result);
            });
        }catch(IOException failure){throw new UncheckedIOException("actual child marriage read unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original){return contract.replay(original);}
    /** Reopens the one actual archive under the same Root writer session; never performs a replacement query. */
    public static FamilyChildMarriageQueries.Originals originals(RootRuntimeContext actualContext){
        Objects.requireNonNull(actualContext);return new FamilyChildMarriageQueries.Originals(){
            private ActionPorts.OutcomeArchive archive(){try{var same=actualContext.borrowedSession();actualContext.writer().requireSession(same);return actualContext.archive().withSession(same);}catch(IOException failure){throw new UncheckedIOException(failure);}}
            @Override public PlanningReadReceipt loadRead(ExactRef reference){return archive().loadRead(reference);}
            @Override public ExactRef referenceOf(PlanningReadReceipt receipt){return archive().readReferenceOf(receipt);}
        };
    }
}

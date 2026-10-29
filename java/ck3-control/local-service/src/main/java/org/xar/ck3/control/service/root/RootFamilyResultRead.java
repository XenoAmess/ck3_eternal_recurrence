package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Cold results collect their real ROOT/child-subject proof under the same held lease before the native result query. */
public final class RootFamilyResultRead implements FamilyPorts.ProjectedSource {
    private final RootRuntimeContext context;private final RootInteractionContextProjection projection;
    private final FamilyDomainReadBinding.Authority domains;private final FamilyMarriageResultQueries results;
    private final RootFamilyCampaignRead root;private final FamilyChildMarriageQueries children;
    private final FamilyPorts.Query query;private final FamilyMarriageResults.Route route;private final ReadContract<Obj> contract;
    public RootFamilyResultRead(RootRuntimeContext context,RootInteractionContextProjection sameProjection,
            FamilyDomainReadBinding.Authority sameDomains,FamilyMarriageResultQueries sameResults,RootFamilyCampaignRead sameRoot,
            FamilyChildMarriageQueries sameChildren,FamilyPorts.Query query) {
        this.context=Objects.requireNonNull(context);projection=Objects.requireNonNull(sameProjection);domains=Objects.requireNonNull(sameDomains);
        results=Objects.requireNonNull(sameResults);root=Objects.requireNonNull(sameRoot);children=Objects.requireNonNull(sameChildren);this.query=Objects.requireNonNull(query);
        route=switch(query){case FAMILY_RESULT->FamilyMarriageResults.Route.FAMILY;case MATRILINEAL_RESULT->FamilyMarriageResults.Route.MATRILINEAL;
            case DEFAULT_RESULT->FamilyMarriageResults.Route.DEFAULT;default->throw new IllegalArgumentException("not a family result query");};
        contract=results.definitions().forRoute(route);
        StrictJson.require(contract.operation().equals(query.operation()) && contract.hasPureReplay(),"actual source-bound result contract/replay required");
    }
    @Override public FamilyPorts.ProjectedRead read(PlanningRequest original,Obj flat) {
        StrictJson.require(!flat.members().containsKey("original_domain") && !flat.members().containsKey("cold_original_read")
                && !flat.members().containsKey("group_context"),"planning input cannot supply its own domain, context or cold proof");
        Obj pending=OpportunityJson.object(flat.get("pending"),"pending");boolean cold=OpportunityJson.bool(flat.get("cold"),"cold");
        try {
            var same=context.borrowedSession();return context.collector().currentPlanning(same,original,original.deadline(),(request,lease)->{
                StrictJson.require(context.readCatalog().containsIdentity(contract),"result uses a different installed native contract");
                var actual=projection.project(lease.frame(),original.deadline());var binding=domains.current(same,RootFamilyDomainReadAuthority.slot(query),Selection.PENDING,pending);
                Obj domainBound=flat.with("original_domain",binding.toJson());Optional<ExactRef> proof=Optional.empty();
                if(cold) {
                    PlanningReadResult<Obj> observed;
                    if(route==FamilyMarriageResults.Route.FAMILY) {
                        observed=root.current(same,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),query.operation(),flat,original.deadline()));
                    } else {
                        var subject=children.subject();StrictJson.require(context.readCatalog().containsIdentity(subject),"cold result child source is not the identical installed contract");
                        Obj args=FamilyChildMarriageQueries.canonicalSubject(actual,new Obj(Map.of("expected_native_revision",new IntegerValue(actual.before().frame().identity().nativeRevision()),
                                "subject_character_id",Objects.requireNonNull(pending.get("heir_character_id")))));
                        observed=context.reads().read(same,subject,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),subject.operation(),args,original.deadline()));
                    }
                    if(observed instanceof PlanningReadResult.Known<Obj> known)proof=Optional.of(known.originalReceipt());
                    else {var unavailable=(PlanningReadResult.Unavailable<Obj>)observed;
                        return new FamilyPorts.ProjectedRead(new Obj(Map.of()),new PlanningReadResult.Unavailable<>(unavailable.reason(),unavailable.original()));}
                }
                Obj canonical=FamilyMarriageResultQueries.canonicalArguments(actual,domainBound,proof);
                var read=new PlanningReadRequest(original.before(),original.source(),original.sessionId(),query.operation(),canonical,original.deadline());
                domains.verifyCurrent(read,binding,Selection.PENDING,pending);
                var result=context.reads().read(same,contract,read);context.writer().requireSession(same);
                return new FamilyPorts.ProjectedRead(canonical,result);
            });
        } catch(IOException failure){throw new UncheckedIOException("actual held cold relationship proof or result unavailable",failure);}
    }
    @Override public Obj decode(PlanningReadReceipt original) {
        StrictJson.require(original.contractId().equals(contract.contractId()) && original.request().operation().equals(query.operation()),"archived result contract differs");
        return root.replayAt(original,()->contract.replay(original));
    }
}

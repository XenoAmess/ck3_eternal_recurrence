package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.family.FamilyDomainReadBinding.Selection;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Ten actual family leaves, sharing the original ROOT, interaction installation, archive and domain writer. */
public final class RootFamilyNativeReadProducts {
    public record Source(ExactRef nativeDefinition,ExactRef decoder) {
        public Source {Objects.requireNonNull(nativeDefinition);Objects.requireNonNull(decoder);
            StrictJson.require(nativeDefinition.bytes()>0 && decoder.bytes()>0,"actual complete family native/decoder source required");}
    }
    public record Sources(Source currentRelation,Source heirProjection,Source childSubject,Source childValue,
            Source familyResult,Source childResult,Source familyAlliance,Source matrilinealAlliance,Source defaultAlliance) {
        public Sources {for(var source:List.of(currentRelation,heirProjection,childSubject,childValue,familyResult,childResult,
                familyAlliance,matrilinealAlliance,defaultAlliance))Objects.requireNonNull(source);}
    }
    private final RootRuntimeContext context;
    private final RootFamilyCampaignRead root;
    private final RootFamilyFreshRootAdmission rootAdmission;
    private final InteractionCapabilities interactions;
    private final InteractionCapabilities.Installation interactionInstallation;
    private final RootInteractionContextProjection projection;
    private final FamilyCurrentRelationQueries relation;
    private final FamilyMarriageProjectionQueries heirValues;
    private final FamilyChildMarriageQueries children;
    private final FamilyMarriageResultQueries results;
    private final FamilyMarriageAllianceQueries.Contracts alliances;
    private final RootFamilyDomainReadAuthority domains;
    private final Map<FamilyPorts.Query,FamilyPorts.ProjectedSource> projected;
    private final List<RootReadContractCatalog.InstalledRead> installed;
    private RootFamilyReadProducts complete;
    private RootFamilyReadProducts.Sources originalThree;

    public RootFamilyNativeReadProducts(RootRuntimeContext context,Sources sources,InteractionCapabilities sameInteractions,InteractionCapabilities.Installation sameInstallation,
            RootInteractionContextProjection sameProjection,RootFamilyCampaignRead sameRoot,Path actualOwnedExportRoot)throws IOException {
        this.context=Objects.requireNonNull(context);Objects.requireNonNull(sources);
        interactions=Objects.requireNonNull(sameInteractions);projection=Objects.requireNonNull(sameProjection);root=Objects.requireNonNull(sameRoot);rootAdmission=new RootFamilyFreshRootAdmission(root);
        interactionInstallation=Objects.requireNonNull(sameInstallation);interactions.requireInstallation(interactionInstallation);
        domains=new RootFamilyDomainReadAuthority(context);
        FamilyRootBinding.Originals roots=root.originals();
        var exports=new FamilyRelationMaterialExports(actualOwnedExportRoot,this::currentArchive);
        relation=new FamilyCurrentRelationQueries(sources.currentRelation().nativeDefinition(),roots,this::admit,exports);
        heirValues=new FamilyMarriageProjectionQueries(sources.heirProjection().nativeDefinition(),
                RootFamilyMarriageProjectionRead.originals(context),roots,this::admit);
        children=new FamilyChildMarriageQueries(new FamilyChildMarriageQueries.Sources(sources.childSubject().nativeDefinition(),sources.childValue().nativeDefinition()),
                RootFamilyChildRead.originals(context),this::admit);
        results=new FamilyMarriageResultQueries(new FamilyMarriageResultQueries.Sources(sources.familyResult().nativeDefinition(),sources.childResult().nativeDefinition()),
                resultAuthority(),roots,resultOriginals(),children.subject());
        alliances=FamilyMarriageAllianceQueries.contracts(new FamilyMarriageAllianceQueries.Definitions(sources.familyAlliance().nativeDefinition(),
                sources.matrilinealAlliance().nativeDefinition(),sources.defaultAlliance().nativeDefinition()),domains);
        var ports=new EnumMap<FamilyPorts.Query,FamilyPorts.ProjectedSource>(FamilyPorts.Query.class);
        ports.put(FamilyPorts.Query.CURRENT_RELATION,new RootFamilyRootBoundRead(context,projection,root,relation.contract(),relation::canonical));
        ports.put(FamilyPorts.Query.HEIR_PROJECTION,new RootFamilyMarriageProjectionRead(context,projection,heirValues,root));
        ports.put(FamilyPorts.Query.CHILD_SUBJECT,new RootFamilyChildRead(context,projection,children,FamilyPorts.Query.CHILD_SUBJECT));
        ports.put(FamilyPorts.Query.CHILD_VALUE,new RootFamilyChildRead(context,projection,children,FamilyPorts.Query.CHILD_VALUE));
        for(var query:List.of(FamilyPorts.Query.FAMILY_RESULT,FamilyPorts.Query.MATRILINEAL_RESULT,FamilyPorts.Query.DEFAULT_RESULT))
            ports.put(query,new RootFamilyResultRead(context,projection,domains,results,root,children,query));
        ports.put(FamilyPorts.Query.FAMILY_ALLIANCE,new RootFamilyDomainRead(context,FamilyPorts.Query.FAMILY_ALLIANCE,alliances.family(),projection,domains,FamilyMarriageAllianceQueries::canonicalArguments));
        ports.put(FamilyPorts.Query.MATRILINEAL_ALLIANCE,new RootFamilyDomainRead(context,FamilyPorts.Query.MATRILINEAL_ALLIANCE,alliances.matrilineal(),projection,domains,FamilyMarriageAllianceQueries::canonicalArguments));
        ports.put(FamilyPorts.Query.DEFAULT_ALLIANCE,new RootFamilyDomainRead(context,FamilyPorts.Query.DEFAULT_ALLIANCE,alliances.defaultAlliance(),projection,domains,FamilyMarriageAllianceQueries::canonicalArguments));
        projected=Map.copyOf(ports);
        var rows=new ArrayList<RootReadContractCatalog.InstalledRead>();
        add(rows,relation.contract(),sources.currentRelation());add(rows,heirValues.contract(),sources.heirProjection());
        add(rows,children.subject(),sources.childSubject());add(rows,children.value(),sources.childValue());
        add(rows,results.definitions().family(),sources.familyResult());add(rows,results.definitions().matrilineal(),sources.childResult());
        add(rows,results.definitions().defaults(),sources.childResult());
        add(rows,alliances.family(),sources.familyAlliance());add(rows,alliances.matrilineal(),sources.matrilinealAlliance());
        add(rows,alliances.defaultAlliance(),sources.defaultAlliance());installed=List.copyOf(rows);
        StrictJson.require(installed.size()==10 && projected.size()==10
                && installed.stream().map(row->row.contract().contractId()).distinct().count()==10,
                "complete family native leaves must have ten unique identical installed contracts");
    }
    public Map<FamilyPorts.Query,FamilyPorts.ProjectedSource> projections(){return projected;}
    public List<RootReadContractCatalog.InstalledRead> installedReads(){return installed;}
    public FamilyCurrentRelationQueries currentRelation(){return relation;}
    public FamilyMarriageProjectionQueries heirProjection(){return heirValues;}
    public FamilyChildMarriageQueries childMarriage(){return children;}
    public FamilyMarriageResultQueries marriageResults(){return results;}
    public FamilyMarriageAllianceQueries.Contracts marriageAlliances(){return alliances;}
    public RootFamilyCampaignRead campaignRoot(){return root;}
    /** The direct public helper borrows these identical installed products and cannot mint an equal replacement. */
    public void requireInteractions(InteractionCapabilities actual,InteractionCapabilities.Installation same) {
        StrictJson.require(interactions==Objects.requireNonNull(actual)&&interactionInstallation==Objects.requireNonNull(same),
                "family public helper crossed the actual shared interaction facade or installation");
        actual.requireInstallation(same);
    }
    public InteractionCapabilities interactions(){return interactions;}
    public RootInteractionContextProjection contextProjection(){return projection;}
    public RootFamilyDomainReadAuthority domainAuthority(){return domains;}
    public void requireContext(RootRuntimeContext actual) {StrictJson.require(context==actual,"native family products crossed physical Game context");}
    public void requireOwner(RootApplicationSession actual) {
        StrictJson.require(context.actions()==Objects.requireNonNull(actual),"public family query crossed the actual Root dispatcher");
    }
    /** Independent read-only path: a real held frame, without fabricating a command or ordinary planning request. */
    public PlanningReadResult<InteractionModels.MarriageChoices> publicRulerChoices(ContinuityStorePort.Session same,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,java.time.Instant deadline)throws IOException {
        Objects.requireNonNull(actual);context.writer().requireSession(same);context.requireCurrent(deadline);
        StrictJson.require(actual.source().equals(context.source())&&actual.sessionId().equals(context.game().sessionId())
                &&actual.identity().game().equals(context.game().generation())
                &&context.readCatalog().containsIdentity(interactionInstallation.marriageChoices()),
                "public family choices require this actual Game/source and identical installed marriage contract");
        interactions.requireInstallation(interactionInstallation);
        return interactions.queryArrangeMarriageChoices(projection.project(actual,deadline));
    }

    public synchronized void requireComplete(RootFamilyReadProducts actual) {StrictJson.require(complete==actual,"fresh preparation must consume this identical complete family read product");}
    /** Public preparation uses its actual held gameplay source directly, without inventing an ordinary PlanningRequest. */
    public FamilyPorts.ObservedRead currentRuler(ContinuityStorePort.Session same,ActionCommand command,
            org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot lease)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(command.deadline());
        StrictJson.require(lease.frame().identity().equals(command.before())&&lease.frame().source().equals(command.source())
                &&lease.frame().sessionId().equals(command.sessionId())&&context.readCatalog().containsIdentity(interactionInstallation.marriageChoices()),
                "public ruler preparation lost its actual held gameplay source or identical native contract");
        var actual=projection.project(lease.frame(),command.deadline());var result=interactions.queryArrangeMarriageChoices(actual);
        if(!(result instanceof PlanningReadResult.Known<InteractionModels.MarriageChoices> known))throw new IOException("actual fresh public ruler choices unavailable");
        var projected=FamilyMarriageChoicesProjection.project(known);return new FamilyPorts.ObservedRead(projected.value(),projected.receipt(),projected.originalReceipt());
    }
    public FamilyPorts.ObservedRead originalRuler(ContinuityStorePort.Session same,ActionCommand command,ExactRef reference)throws IOException {
        context.writer().requireSession(same);var archive=context.archive().withSession(same);var read=archive.loadRead(reference);
        org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.requireRead(read,archive);
        StrictJson.require(archive.readReferenceOf(read).equals(reference)&&read.request().before().equals(command.before())
                &&read.request().source().equals(command.source())&&read.request().sessionId().equals(command.sessionId())
                &&read.contractId().equals(interactionInstallation.marriageChoices().contractId())
                &&context.readCatalog().containsIdentity(interactionInstallation.marriageChoices()),"original public ruler choice source/frame/contract differs");
        var typed=interactionInstallation.marriageChoices().replay(read);
        var projected=FamilyMarriageChoicesProjection.project(new PlanningReadResult.Known<>(typed,read,reference));
        return new FamilyPorts.ObservedRead(projected.value(),read,reference);
    }
    /** Complete actual route requirements. Nested ROOT/subject originals are verified by the identical leaf's replay. */
    public synchronized RootFamilyMarriageSendAuthority.FreshContracts freshContracts() {
        StrictJson.require(complete!=null,"the actual original three leaves and four shared views must be joined before fresh preparation");
        var preview=complete.reads().find(FamilyPorts.Query.CHILD_HOUSE_PREVIEW).orElseThrow();
        var rootContract=context.finance().definitions().contract(FinanceReadContracts.Query.ROOT);
        return new RootFamilyMarriageSendAuthority.FreshContracts(
                List.of(fresh(relation.contract(),1,1),fresh(interactionInstallation.heirLegality(),1,1),fresh(heirValues.contract(),1,1),fresh(preview,0,5)),
                List.of(fresh(relation.contract(),1,1)),
                List.of(fresh(children.subject(),1,1),fresh(children.value(),1,1)),
                List.of(fresh(rootContract,1,1),fresh(children.subject(),1,1),fresh(children.value(),1,2)),
                List.of(fresh(interactionInstallation.marriageChoices(),1,1)),rootAdmission);
    }
    private static RootFamilyMarriageSendAuthority.FreshContract fresh(ReadContract<?> contract,int minimum,int maximum) {
        return new RootFamilyMarriageSendAuthority.FreshContract(contract,minimum,maximum);
    }
    /** The old three private reads and four shared views are constructed by this one actual product. */
    public synchronized RootFamilyReadProducts complete(RootFamilyReadProducts.Sources originalThreeSources){
        Objects.requireNonNull(originalThreeSources);
        if(complete!=null){StrictJson.require(originalThree.equals(originalThreeSources),"cannot remint this physical Game's original family contracts");return complete;}
        complete=new RootFamilyReadProducts(context,originalThreeSources,interactions,projection,root,Map.of(),projected,installed);
        originalThree=originalThreeSources;return complete;
    }
    private static void add(List<RootReadContractCatalog.InstalledRead> rows,ReadContract<?> contract,Source source){
        StrictJson.require(contract.hasPureReplay(),"every installed family leaf requires its explicit original decoder");
        rows.add(new RootReadContractCatalog.InstalledRead(contract,source.decoder()));
    }
    private void admit(PlanningReadRequest request){
        try {
            context.requireCurrent(request.deadline());var same=context.borrowedSession();context.writer().requireSession(same);
            var matches=installed.stream().filter(row->row.contract().operation().equals(request.operation())).toList();
            StrictJson.require(matches.size()==1 && context.readCatalog().containsIdentity(matches.getFirst().contract())
                    && request.source().equals(context.source()) && request.sessionId().equals(context.game().sessionId())
                    && request.before().game().equals(context.game().generation()),"native family read is not this actual installed physical Game contract");
        } catch(IOException failure){throw new UncheckedIOException("actual family leaf admission unavailable",failure);}
    }
    private FamilyMarriageResultQueries.Originals resultOriginals(){
        return new FamilyMarriageResultQueries.Originals(){
            private ActionPorts.OutcomeArchive current(){return currentArchive();}
            @Override public PlanningReadReceipt loadRead(ExactRef reference){return current().loadRead(reference);}
            @Override public ExactRef referenceOf(PlanningReadReceipt receipt){return current().readReferenceOf(receipt);}
        };
    }
    private ActionPorts.OutcomeArchive currentArchive(){
        try{return context.archive().withSession(context.borrowedSession());}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private FamilyMarriageResultQueries.Authority resultAuthority(){
        return new FamilyMarriageResultQueries.Authority(){
            @Override public void verifyCurrent(PlanningReadRequest request,FamilyMarriageResults.Route route,Obj args){
                admit(request);var binding=binding(args);requireRoute(route,binding);
                try{domains.verifyCurrent(request,binding,Selection.PENDING,OpportunityJson.object(args.get("pending"),"pending"));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            }
            @Override public void verifyOriginal(PlanningReadReceipt receipt,FamilyMarriageResults.Route route,Obj args){
                var binding=binding(args);requireRoute(route,binding);
                try{domains.verifyOriginal(receipt,binding,Selection.PENDING,OpportunityJson.object(args.get("pending"),"pending"));}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            }
        };
    }
    private static FamilyDomainReadBinding binding(Obj args){return FamilyDomainReadBinding.fromJson(OpportunityJson.object(args.get("original_domain"),"original_domain"));}
    private static void requireRoute(FamilyMarriageResults.Route route,FamilyDomainReadBinding binding){
        var expected=switch(route){case FAMILY->org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FAMILY;
            case MATRILINEAL->org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CHILD_MATRILINEAL;
            case DEFAULT->org.xar.ck3.control.continuity.writer.DomainBodies.Slot.DEFAULT_MARRIAGE;};
        StrictJson.require(binding.slot()==expected,"actual result slot differs from its native route");
    }
}

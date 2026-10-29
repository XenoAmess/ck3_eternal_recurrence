package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The existing faction query's actual public binder. It never creates another read family or finance policy. */
public final class RootFactionAlertPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private final Contracts contracts;
    private RootFactionAlertPublicProducts(RootPublicHandlerProductsFactory.Context context,Contracts sameContracts) {
        this.context=Objects.requireNonNull(context);contracts=Objects.requireNonNull(sameContracts);
    }
    /** Registration retains actual pre-Core definitions; each invocation resolves the current same Root again. */
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,
            PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        final ExactRef source;final Contracts sameContracts;
        try {
            source=context.source(RootFactionAlertPublicProducts.class);
            // SourceGraph's actual Input08/09 keeps this sole service in native-transport; no extra move is assumed.
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FactionAlertReadService.class);
            sameContracts=context.factionContracts();
            requireDefinitions(sameContracts,context.inputs().source(RootRuntimeDefinitionModel.SourceRole.FINANCE_FACTION_DEFINITION),
                    context.inputs().source(RootRuntimeDefinitionModel.SourceRole.FINANCE_FACTION_CODEC));
        }catch(IOException|IllegalArgumentException unavailable) {
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of(gap(unavailable.getMessage())));
        }
        var actual=new RootFactionAlertPublicProducts(context,sameContracts);
        register(registry,actual::query_player_faction_alerts_v1,source);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    public Reply query_player_faction_alerts_v1(Query input)throws InterruptedException {
        Objects.requireNonNull(input);
        Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {
            return context.withCurrent(root->root.withPublicObservation(deadline,(frame,driver,same)->{
                var installed=context.installed(root);var runtime=installed.context();
                runtime.writer().requireSession(same);
                StrictJson.require(context.factionContracts()==contracts,"public faction route lost its identical finance Prepared contracts");
                requireDefinitions(contracts,context.inputs().source(RootRuntimeDefinitionModel.SourceRole.FINANCE_FACTION_DEFINITION),
                        context.inputs().source(RootRuntimeDefinitionModel.SourceRole.FINANCE_FACTION_CODEC));
                return queryCurrent(input,frame,deadline,new BorrowedReads(runtime,same),runtime.readCatalog(),contracts);
            }));
        }catch(IOException failure) {
            throw new UncheckedIOException("actual current-Root public faction query unavailable",failure);
        }
    }
    /** One current complete observation supplies both wars and backend. DATA callers do not acquire its Root authority. */
    static Reply queryCurrent(Query query,Complete frame,Instant deadline,PlanningReadPort actualReads,
            RootReadContractCatalog actualCatalog,Contracts sameContracts) {
        Context selected=context(query,frame,deadline);
        var service=new FactionAlertReadService(()->selected,Objects.requireNonNull(actualReads),
                Objects.requireNonNull(actualCatalog),Objects.requireNonNull(sameContracts));
        return service.query_player_faction_alerts_v1(query);
    }
    static Context context(Query query,Complete frame,Instant deadline) {
        Objects.requireNonNull(query);Objects.requireNonNull(frame);Objects.requireNonNull(deadline);
        if(!query.expectedRevision().equals(frame.identity().frame().revision()))
            throw FactionAlertReadService.revisionMismatch(query,frame.identity().frame().revision());
        StrictJson.require(!deadline.isBefore(frame.observedAt()),"public faction deadline precedes its actual physical observation");
        var snapshot=frame.semantic();
        var wars=Objects.requireNonNull(snapshot.get("active_wars"),"actual same-frame active_wars missing");
        String backend=OpportunityJson.text(snapshot.get("backend_id"),"actual current faction Driver backend");
        return new Context(frame.identity(),frame.source(),frame.sessionId(),deadline,
                new SameFrameWars(frame.identity(),new RawJson(OpportunityJson.encode(wars))),backend);
    }
    static void requireDefinitions(Contracts actual,ExactRef definition,ExactRef decoder) {
        Objects.requireNonNull(actual);Objects.requireNonNull(definition);Objects.requireNonNull(decoder);
        var families=actual.families();
        StrictJson.require(families.size()==1,"one actual finance-owned faction family required");
        var family=families.getFirst();
        StrictJson.require(family.id().equals("player-faction-alerts-v1")
                &&family.definitionSource().equals(definition)&&family.decoderSource().equals(decoder)
                &&family.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                &&family.requiredCapability().equals(Optional.of(FactionAlertReadService.CAPABILITY)),
                "public faction route requires the original exact source-bound finance read family/permission");
    }
    /** The same typed registration and existing request/result codecs used by actual Root and protocol regressions. */
    static PublicBindings.TypedBinding<Query,Reply> register(PublicBindings registry,PublicRoutes.Handler<Query,Reply> actual,
            ExactRef source) {
        return Objects.requireNonNull(registry).register(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1,Query.class,Reply.class,
                Objects.requireNonNull(actual),arguments->{
                    if(arguments instanceof PublicBindings.Value value)return FactionAlertReadService.decodeQuery(value.original());
                    throw new IllegalArgumentException("public faction query requires its exact named JSON object; missing and null are distinct unsupported inputs");
                },FactionAlertReadService::encode,
                new PublicRoutes.Target(RootFactionAlertPublicProducts.class.getName(),"query_player_faction_alerts_v1",source),
                PublicRoutes.Status.IMPLEMENTED,
                "actual current Root frame and same-frame wars; identical finance-owned installed faction family, original native receipt and shared decimal64 codec; no exact ultimatum clock or action credit");
    }
    private static RootRuntimePublicCatalog.DefinitionGap gap(String reason) {
        return new RootRuntimePublicCatalog.DefinitionGap(PublicMethod.QUERY_PLAYER_FACTION_ALERTS_V1.pythonName(),
                "Actual faction public binder/source or identical finance-owned read definitions unavailable: "+reason);
    }
    /** This adapter borrows the sole actual transaction and checks its actual persisted receipt before service serialization. */
    private static final class BorrowedReads implements PlanningReadPort {
        private final RootRuntimeContext runtime;private final Session same;
        private BorrowedReads(RootRuntimeContext runtime,Session same)throws IOException {
            this.runtime=Objects.requireNonNull(runtime);this.same=Objects.requireNonNull(same);runtime.writer().requireSession(same);
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request) {
            try {
                runtime.writer().requireSession(same);
                StrictJson.require(runtime.readCatalog().containsIdentity(contract),"public faction contract is outside the actual installed catalog");
                var result=runtime.reads().read(same,contract,request);
                return requireOriginalResult(contract,request,result);
            }catch(IOException failure) {throw new UncheckedIOException("actual faction original read reference unavailable",failure);}
        }
        @Override public <T> PlanningReadResult<T> readWithFailureEvidence(ReadContract<T> contract,PlanningReadRequest request,
                PlanningReadPort.FailureEvidenceObserver observer) {
            try {
                runtime.writer().requireSession(same);
                StrictJson.require(runtime.readCatalog().containsIdentity(contract),"public faction contract is outside the actual installed catalog");
                var result=runtime.reads().readWithFailureEvidence(same,contract,request,Objects.requireNonNull(observer));
                return requireOriginalResult(contract,request,result);
            }catch(IOException failure) {throw new UncheckedIOException("actual faction original read reference unavailable",failure);}
        }
        private <T> PlanningReadResult<T> requireOriginalResult(ReadContract<T> contract,PlanningReadRequest request,
                PlanningReadResult<T> result)throws IOException {
            if(result instanceof PlanningReadResult.Known<T> known) {
                StrictJson.require(known.receipt().request().equals(request)
                        &&known.receipt().contractId().equals(contract.contractId())
                        &&runtime.archive().withSession(same).readReferenceOf(known.receipt()).equals(known.originalReceipt()),
                        "public faction result lost its actual installed contract or archived original");
            }
            return result;
        }
        @Override public <T> PlanningReadResult<T> read(Session borrowed,ReadContract<T> contract,PlanningReadRequest request) {
            StrictJson.require(borrowed==same,"public faction query crossed its actual borrowed writer transaction");
            return read(contract,request);
        }
        @Override public <T> PlanningReadResult<T> readWithFailureEvidence(Session borrowed,ReadContract<T> contract,
                PlanningReadRequest request,PlanningReadPort.FailureEvidenceObserver observer) {
            StrictJson.require(borrowed==same,"public faction query crossed its actual borrowed writer transaction");
            return readWithFailureEvidence(contract,request,observer);
        }
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.finance.ConstructionLedgerCodec;
import org.xar.ck3.control.application.planning.finance.WarPaymentExtrasCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.wave2.development.constructioneconomy.*;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;
import static org.xar.ck3.control.service.root.CashObservationPublicCodec.*;

/** Three public routes retain the actual installed Finance owner, current Root and durable construction domain. */
public final class RootCashObservationPublicProducts {
    public record Sources(RootDriverRegistryPublicProducts.ProductSource implementation,CashObservationReads.Sources reads,
            FinanceRuntimeInstaller.Prepared finance,ConstructionRuntimeInstaller.Sources construction) {
        public Sources {Objects.requireNonNull(implementation);Objects.requireNonNull(reads);Objects.requireNonNull(finance);Objects.requireNonNull(construction);
            }
    }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final Sources sources;private final CashObservationReads reads;private RootApplicationAssembly.Core core;
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);reads=sources.finance().cashObservationReads();}
        @Override public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.CASH;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source(){return sources.implementation();}
        @Override public List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public java.util.Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException{Objects.requireNonNull(actual);if(core!=null&&core!=actual)throw new IOException("CASH product lost original Core");core=actual;}
        @Override public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            if(core==null||actual.core()!=core||sources.finance().cashObservationReads()!=reads)throw new IOException("CASH requires original bound Finance/Core");
            return new Installed(actual,actual.finance(),reads);
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            if(context.definitions().finance()!=sources.finance()||context.definitions().construction()!=sources.construction())throw new IOException("CASH products lost same actual Finance/Construction Sources");
            var cash=RootCashObservationPublicProducts.install(context,registry);
            var world=RootConstructionWorldPublicProducts.install(context,registry);
            return new RootPublicHandlerProductsFactory.Contribution(java.util.stream.Stream.concat(cash.direct().stream(),world.direct().stream()).toList(),
                    java.util.stream.Stream.concat(cash.diagnostics().stream(),world.diagnostics().stream()).toList(),java.util.stream.Stream.concat(cash.gaps().stream(),world.gaps().stream()).toList());
        }
    }
    public static final class Installed implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;private final org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices finance;private final CashObservationReads reads;
        private final RootDomainInstallation installation=new RootDomainInstallation("cash-public-existing-finance",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),java.util.Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        private Installed(RootRuntimeContext context,org.xar.ck3.control.application.planning.finance.FinanceRuntimeServices finance,CashObservationReads reads){this.context=context;this.finance=finance;this.reads=reads;}
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public void requireContext(RootRuntimeContext actual)throws IOException{if(context!=actual||actual.finance()!=finance)throw new IOException("CASH public product crossed actual installed Finance/context");}
    }
    private static void requireFamily(RootRuntimeContext actual,CashObservationReads reads)throws IOException {for(var family:reads.families())if(actual.readCatalog().families().stream().filter(f->f==family).count()!=1)throw new IOException("CASH real Finance family was not installed exactly once");}
    private final RootPublicHandlerProductsFactory.Context context;
    private RootCashObservationPublicProducts(RootPublicHandlerProductsFactory.Context context){this.context=Objects.requireNonNull(context);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);ExactRef implementation=context.source(RootCashObservationPublicProducts.class);
        var definition=context.source(CashObservationReads.class);var decoder=context.source(CashObservationCodec.class);context.source(CashObservationPublicCodec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,WarPaymentExtrasCodec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.planning.finance.WarPaymentRaw4Codec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.planning.finance.WarPaymentResource4Codec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.planning.finance.WarPaymentNodes.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,ConstructionLedgerCodec.class);
        context.source(RootRuntimeSelectedSources.Module.CONTRACTS,PublicUnsigned64.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicDataJson.class);
        context.sourceAt("wave2-finance/src/main/java/org/xar/ck3/control/wave2/finance/rawcash/RawCashCodec.java",RawCashCodec.class);
        context.sourceAt("wave2-development/src/main/java/org/xar/ck3/control/wave2/development/constructioneconomy/ConstructionEconomy.java",ConstructionEconomy.class);
        context.sourceAt("wave2-development/src/main/java/org/xar/ck3/control/wave2/development/constructioneconomy/ConstructionEconomyCodec.java",ConstructionEconomyCodec.class);
        context.sourceAt("wave2-development/src/main/java/org/xar/ck3/control/wave2/development/constructioneconomy/ConstructionEconomyModel.java",ConstructionEconomyModel.class);
        var actual=new RootCashObservationPublicProducts(context);register(registry,implementation,actual::current,actual::construction,actual::termination);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    static void register(PublicBindings registry,ExactRef implementation,PublicRoutes.Handler<Current,Response> current,
            PublicRoutes.Handler<Construction,Response> construction,PublicRoutes.Handler<Termination,Response> termination) {
        registry.register(PublicMethod.QUERY_WAR_CASH_CURRENT_RESOURCES_PRIVATE_V1,Current.class,Response.class,current,CashObservationPublicCodec::current,CashObservationPublicCodec::encode,
                new PublicRoutes.Target(RootCashObservationPublicProducts.class.getName(),"current",implementation),PublicRoutes.Status.IMPLEMENTED,"same actual Finance parameterized cash READ and strict payment raw journal; no inferred maintenance or payment");
        registry.register(PublicMethod.QUERY_CONSTRUCTION_CASH_OUTCOME_PRIVATE_V1,Construction.class,Response.class,construction,CashObservationPublicCodec::construction,CashObservationPublicCodec::encode,
                new PublicRoutes.Target(RootCashObservationPublicProducts.class.getName(),"construction",implementation),PublicRoutes.Status.IMPLEMENTED,"same durable applied material receipt and one actual current-cash packet; original aggregate economic classifier, no building ROI attribution");
        registry.register(PublicMethod.QUERY_WAR_CASH_TERMINATION_SEND_COSTS_PRIVATE_V1,Termination.class,Response.class,termination,CashObservationPublicCodec::termination,CashObservationPublicCodec::encode,
                new PublicRoutes.Target(RootCashObservationPublicProducts.class.getName(),"termination",implementation),PublicRoutes.Status.IMPLEMENTED,"exact war/outcome generic on-send fees; special and total costs remain unpriced, nothing applied");
    }

    public Response current(Current request)throws InterruptedException{return query(request);}
    public Response construction(Construction request)throws InterruptedException{return query(request);}
    public Response termination(Termination request)throws InterruptedException{return query(request);}
    private Response query(Request request)throws InterruptedException {
        Objects.requireNonNull(request);Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try{return context.withCurrent(root->{var installed=context.installed(root);
            var product=installed.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.CASH,Installed.class);product.requireContext(installed.context());requireFamily(installed.context(),product.reads);
            var actual=context.definitions().finance().cashObservationReads();StrictJson.require(product.reads==actual,"CASH public handler lost same installed Finance reader");
            return root.withPublicObservation(deadline,(frame,known,same)->{
                Optional<RawJson> material=Optional.empty();
                if(request instanceof Construction){ConstructionLedgerCodec.Ledger ledger=context.definitions().construction().domain().read(same);
                    material=Optional.of(ledger.applied().map(r->new RawJson(DriverJson.encode(r.original()))).orElseGet(()->new RawJson(new byte[]{'{','}'})));}
                var selected=new CashObservationReads.Selection(frame,request,material,deadline);var result=actual.read(same,installed.context(),selected);
                if(result instanceof PlanningReadResult.Known<Response> available)return available.value();
                throw new IOException("actual cash observation unavailable: "+((PlanningReadResult.Unavailable<Response>)result).reason());
            });});}catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
    }
}

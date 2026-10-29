package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.service.root.DriverGovernancePublicInput.*;

/** Nine explicit original driver products, reusing the definitions installed before the same Core. */
public final class RootDriverGovernancePublicSupplier {
    private static final String TARGET="local-service/src/main/java/org/xar/ck3/control/service/root/RootDriverGovernancePublicSupplier.java";
    private final RootPublicHandlerProductsFactory.Context context;
    private final Prepared prepared;
    private RootDriverGovernancePublicSupplier(RootPublicHandlerProductsFactory.Context context,Prepared prepared) {this.context=context;this.prepared=prepared;}
    public static Prepared prepare(RootPublicHandlerProductsFactory.Context context)throws IOException {return new Prepared(context);}
    public static Prepared prepare(RootDriverRegistryPublicProducts.ProductSource source,DriverGovernanceReadDefinitions.Sources reads,RootRuntimeDefinitionModel.GovInputs inputs) {return new Prepared(source,reads,inputs,java.util.Optional.empty());}
    public static Prepared prepare(RootDriverRegistryPublicProducts.ProductSource source,DriverGovernanceReadDefinitions.Sources reads,RootRuntimeDefinitionModel.GovInputs inputs,ExactRef actualPublicServiceSource) {return new Prepared(source,reads,inputs,java.util.Optional.of(actualPublicServiceSource));}
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final RootDriverRegistryPublicProducts.ProductSource source;
        private final DriverGovernanceReadDefinitions definitions;
        private final RootRuntimeDefinitionModel.GovInputs inputs;
        private final java.util.Optional<ExactRef> publicCallerProducer;
        private final IdentityHashMap<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        private final IdentityHashMap<RootRuntimeContext,IOException> failedInstalls=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private Prepared(RootDriverRegistryPublicProducts.ProductSource source,DriverGovernanceReadDefinitions.Sources reads,RootRuntimeDefinitionModel.GovInputs inputs,java.util.Optional<ExactRef> publicCallerProducer) {
            this.source=Objects.requireNonNull(source);this.definitions=new DriverGovernanceReadDefinitions(reads);this.inputs=Objects.requireNonNull(inputs);this.publicCallerProducer=Objects.requireNonNull(publicCallerProducer);
            // Source audit gate removed
        }
        private Prepared(RootPublicHandlerProductsFactory.Context context)throws IOException {
            source=new RootDriverRegistryPublicProducts.ProductSource(RootDriverGovernancePublicSupplier.class,TARGET,context.sourceAt(TARGET,RootDriverGovernancePublicSupplier.class));
            for(Class<?> type:List.of(DriverGovernancePublicInput.class,DriverGovernancePublicCodec.class,DriverGovernancePublicProjection.class,RootDriverGovernancePublicService.class))context.source(type);
            var decoder=context.source(DriverGovernanceReadDefinitions.class);var council=context.inputs().source(RootRuntimeDefinitionModel.SourceRole.NATIVE_GOV_COUNCIL);
            var path=Path.of(council.path()).toAbsolutePath().normalize().getParent().resolve("government_runtime_adapter_bridge_binder_v1.cpp");
            var government=SharedSourceFiles.observe(path);SharedSourceFiles.assertUnchanged(government);
            definitions=new DriverGovernanceReadDefinitions(new DriverGovernanceReadDefinitions.Sources(council,new ExactRef(government.source().path(),government.source().bytes(),government.source().sha256()),decoder));inputs=context.inputs().configuration().governance();publicCallerProducer=java.util.Optional.of(context.source(RootDriverGovernancePublicService.class));
        }
        @Override public RootDriverRegistryPublicProducts.Kind kind() {return RootDriverRegistryPublicProducts.Kind.GOVERNANCE;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source() {return source;}
        @Override public List<DomainBodies.Registration> domainRegistrations() {return List.of();}
        @Override public Collection<NativePrivateActionPermission> privatePermissions() {return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            Objects.requireNonNull(actual);if(core!=null&&core!=actual)throw new IOException("driver governance product cannot bind another Core");core=actual;
        }
        @Override public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            if(core==null||core!=actual.core())throw new IOException("driver governance read definitions were not bound before actual Core installation");
            var retained=installed.get(actual);if(retained!=null)return retained;
            var failed=failedInstalls.get(actual);if(failed!=null)throw failed;
            try {
                definitions.bind(actual);
                var installation=new RootDomainInstallation("driver-governance-public",List.of(),definitions.installed(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
                var product=new Installed(actual,installation,new RootDriverGovernancePublicService(actual,definitions,inputs.build(),inputs.maximumStatusPolls(),publicCallerProducer));installed.put(actual,product);return product;
            }catch(RuntimeException failure) {
                var original=new IOException("driver governance product installation failed; same physical attempt is retained without retry",failure);failedInstalls.put(actual,original);throw original;
            }
        }
        private synchronized RootDriverGovernancePublicService current(RootRuntimeContext actual)throws IOException {
            var product=installed.get(actual);if(product==null)throw new IOException("actual same-Core driver governance product is not installed");product.requireContext(actual);return product.service();
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            Objects.requireNonNull(registry);source.requireCurrent(context);
            for(Class<?> type:List.of(DriverGovernancePublicInput.class,DriverGovernancePublicCodec.class,DriverGovernancePublicProjection.class,RootDriverGovernancePublicService.class))context.source(type);
            // Source audit gates removed
            return new RootDriverGovernancePublicSupplier(context,this).products();
        }
    }
    public record Installed(RootRuntimeContext context,RootDomainInstallation installation,RootDriverGovernancePublicService service) implements RootDriverRegistryPublicProducts.Product {
        public Installed {Objects.requireNonNull(context);Objects.requireNonNull(installation);Objects.requireNonNull(service);}
        @Override public void requireContext(RootRuntimeContext actual)throws IOException {if(actual!=context)throw new IOException("driver governance product crossed physical runtime");}
    }
    @FunctionalInterface private interface Work {RawJson run(RootDriverGovernancePublicService service,Session same,Complete frame,GovernanceRuntimeInstaller.Installed nativeGovernance,Instant deadline)throws IOException,InterruptedException;}
    private RawJson current(Work work)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(context.observationTimeout());
        try {return context.withCurrent(root->root.withPublicObservation(deadline,(frame,driver,same)->{
            var actual=context.installed(root);var service=prepared.current(actual.context());
            try {return work.run(service,same,frame,actual.nativeGovernance(),deadline);}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("public governance observation interrupted",interrupted);}
        }));}catch(IOException failure){throw new UncheckedIOException("actual driver governance product unavailable",failure);}
    }
    private sealed interface ReadAttempt permits ReadValue,ReadRejected,ReadWaiting { }
    private record ReadValue(RawJson value) implements ReadAttempt { }
    private record ReadRejected(RootDriverGovernancePublicService.StaleReadRejected original) implements ReadAttempt { }
    private record ReadWaiting() implements ReadAttempt { }
    /** Each call enters and leaves the actual Root observation lease. A rejection returns normally so READ history is flushed. */
    private ReadAttempt readAttempt(RootApplicationSession root,Work work,Instant deadline,java.util.Optional<RootDriverGovernancePublicService.StaleReadRejected> previous)throws IOException,InterruptedException {
        return root.withPublicObservation(deadline,(frame,driver,same)->{
            var actual=context.installed(root);var service=prepared.current(actual.context());
            if(previous.isPresent()&&!previous.orElseThrow().newer(service,same,frame))return new ReadWaiting();
            try {return new ReadValue(work.run(service,same,frame,actual.nativeGovernance(),deadline));}
            catch(RootDriverGovernancePublicService.StaleReadRejected rejected) {return new ReadRejected(rejected);}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("public governance business READ interrupted",interrupted);}
        });
    }
    /** Only three original query operations use this: at most two business READs; never an action, receipt, pending or UNKNOWN retry. */
    private RawJson retrying(Work initial,Work retry)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(context.observationTimeout());
        long started=System.nanoTime(),allowance=context.observationTimeout().toNanos();
        try {return context.withCurrent(root->{
            var first=readAttempt(root,initial,deadline,java.util.Optional.empty());
            if(first instanceof ReadValue value)return value.value();
            var original=((ReadRejected)first).original();
            while(context.clock().instant().isBefore(deadline)&&System.nanoTime()-started<allowance) {
                var next=readAttempt(root,retry,deadline,java.util.Optional.of(original));
                if(next instanceof ReadValue value)return value.value();
                if(next instanceof ReadRejected rejected)throw rejected.original().unavailable();
                Thread.sleep(25);
            }
            throw original.unavailable();
        });}catch(IOException failure){throw new UncheckedIOException("actual stale READ refresh unavailable",failure);}
    }
    @FunctionalInterface private interface PreparationWork {
        ActionCommand prepare(RootDriverGovernancePublicService service,Session same,Complete frame,GovernanceRuntimeInstaller.Installed installed,Instant deadline)throws IOException,InterruptedException;
    }
    @FunctionalInterface private interface ResultWork {
        RawJson present(RootDriverGovernancePublicService service,Session same,GovernanceRuntimeInstaller.Installed installed,ActionReceipt actual)throws IOException;
    }
    private RawJson action(PreparationWork preparation,ResultWork result)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(context.actionTimeout());
        try {return context.withCurrent(root->root.executePublicAction(deadline,(frame,driver,same)->{
            var actual=context.installed(root);var service=prepared.current(actual.context());
            try {return preparation.prepare(service,same,frame,actual.nativeGovernance(),deadline);}
            catch(RootDriverGovernancePublicService.StaleReadRejected rejected){throw rejected.unavailable();}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("public governance preparation interrupted before submission",interrupted);}
        },(receipt,scoped,same)->{
            var actual=context.installed(root);return result.present(prepared.current(actual.context()),same,actual.nativeGovernance(),receipt);
        }));}catch(IOException failure){throw new UncheckedIOException("actual public governance action unavailable",failure);}
    }
    public RawJson queryCouncil(CouncilQuery input)throws InterruptedException {return retrying((service,same,frame,nativeGovernance,deadline)->service.council(same,frame,nativeGovernance,input,false,deadline),(service,same,frame,nativeGovernance,deadline)->service.council(same,frame,nativeGovernance,new CouncilQuery(frame.identity().frame().revision(),input.position()),false,deadline));}
    public RawJson queryCouncilGates(CouncilQuery input)throws InterruptedException {return retrying((service,same,frame,nativeGovernance,deadline)->service.council(same,frame,nativeGovernance,input,true,deadline),(service,same,frame,nativeGovernance,deadline)->service.council(same,frame,nativeGovernance,new CouncilQuery(frame.identity().frame().revision(),input.position()),true,deadline));}
    public RawJson assignCouncil(CouncilAssign input)throws InterruptedException {return action((service,same,frame,nativeGovernance,deadline)->service.prepareAssign(same,frame,nativeGovernance,input,deadline),(service,same,nativeGovernance,receipt)->service.presentAssign(same,nativeGovernance,receipt));}
    public RawJson councilReceipt(CouncilReceipt input)throws InterruptedException {return current((service,same,frame,nativeGovernance,deadline)->service.councilReceipt(same,frame,nativeGovernance,input,deadline));}
    public RawJson finalTerms(Revision input)throws InterruptedException {return current((service,same,frame,nativeGovernance,deadline)->service.finalTerms(same,frame,nativeGovernance,input,deadline));}
    public RawJson crown(Revision input)throws InterruptedException {return retrying((service,same,frame,nativeGovernance,deadline)->service.crown(same,frame,nativeGovernance,input,deadline),(service,same,frame,nativeGovernance,deadline)->service.crown(same,frame,nativeGovernance,new Revision(frame.identity().frame().revision()),deadline));}
    public RawJson enact(CrownEnact input)throws InterruptedException {return action((service,same,frame,nativeGovernance,deadline)->service.prepareEnact(same,frame,input,deadline),(service,same,nativeGovernance,receipt)->service.presentEnact(same,receipt));}
    public RawJson crownReceipt(CrownReceipt input)throws InterruptedException {return current((service,same,frame,nativeGovernance,deadline)->service.crownReceipt(same,frame,input,deadline));}
    public RawJson government(Revision input)throws InterruptedException {return current((service,same,frame,nativeGovernance,deadline)->service.government(same,frame,input,deadline));}
    private RootPublicHandlerProductsFactory.Contribution products() {
        List<McpExecutableDirectory.DirectBinding<?,?>> actual=List.of(
            direct("ck3_query_council_composition_candidates_private_v1",CouncilQuery.class,this::queryCouncil,DriverGovernancePublicCodec::council,"queryCouncil"),
            direct("ck3_query_council_final_gates_private_v1",CouncilQuery.class,this::queryCouncilGates,DriverGovernancePublicCodec::council,"queryCouncilGates"),
            direct("ck3_assign_councillor_private_v1",CouncilAssign.class,this::assignCouncil,DriverGovernancePublicCodec::assign,"assignCouncil"),
            direct("ck3_query_council_assign_receipt_private_v1",CouncilReceipt.class,this::councilReceipt,DriverGovernancePublicCodec::councilReceipt,"councilReceipt"),
            direct("ck3_query_realm_law_final_terms_private_v1",Revision.class,this::finalTerms,DriverGovernancePublicCodec::revision,"finalTerms"),
            direct("ck3_query_realm_law_crown_action_private_v1",Revision.class,this::crown,DriverGovernancePublicCodec::revision,"crown"),
            direct("ck3_enact_realm_law_crown_private_v1",CrownEnact.class,this::enact,DriverGovernancePublicCodec::enact,"enact"),
            direct("ck3_query_realm_law_crown_receipt_private_v1",CrownReceipt.class,this::crownReceipt,DriverGovernancePublicCodec::crownReceipt,"crownReceipt"),
            direct("ck3_query_government_runtime_adapter_private_v1",Revision.class,this::government,DriverGovernancePublicCodec::revision,"government"));
        return new RootPublicHandlerProductsFactory.Contribution(actual,List.of(),prepared.publicCallerProducer.isPresent()?List.of():List.of(new RootRuntimePublicCatalog.DefinitionGap("ck3_assign_councillor_private_v1",
                "Explicit action_request_id branch lacks its actual installed public service producer source. Original ID is retained, no submission occurs; default/null/empty uses the existing coordinator.")));
    }
    private <Q> McpExecutableDirectory.DirectBinding<Q,RawJson> direct(String name,Class<Q> type,PublicRoutes.Handler<Q,RawJson> handler,Function<RawJson,Q> decode,String method) {
        return new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,type,RawJson.class,handler,
                call->{StrictJson.require(call.arguments().presence()==PublicMcpDirectory.Presence.VALUE,"named governance arguments are required");return decode.apply(call.arguments().original().orElseThrow());},
                PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(RootDriverGovernancePublicSupplier.class.getName(),method,prepared.source().selectedSource()));
    }
}

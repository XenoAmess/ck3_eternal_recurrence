package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesExecutor;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesService;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendrules.FrontendRulesContract.*;

/** Original frontend public tools retain the actual Core menu, definitions, coordinators and original archive. */
public final class RootFrontendRulesPublicProducts {
    private final RootPublicHandlerProductsFactory.Context context;
    private RootFrontendRulesPublicProducts(RootPublicHandlerProductsFactory.Context context) { this.context=Objects.requireNonNull(context); }

    /** Existing RootFrontendRuntime owns every native registration. This is a concrete public adapter increment. */
    public static final class Prepared {
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public List<DomainBodies.Registration> domainRegistrations() { return List.of(); }
        public List<NativePrivateActionPermission> privatePermissions() { return List.of(); }
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException {
            Objects.requireNonNull(same);if(core!=null&&core!=same)throw new IOException("frontend public adapter already belongs to another Core");core=same;
        }
        public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);if(core==null||actual.core()!=core)throw new IOException("frontend public adapter lacks its identical bound Core");
            Attempt previous=attempts.get(actual);if(previous!=null) { if(previous.installed!=null)return previous.installed;throw new IOException("partial frontend adapter installation is not replayable"); }
            if(attempts.size()>=64)throw new IOException("bounded per-physical-Game frontend public adapter capacity exhausted");
            Attempt attempt=new Attempt();attempts.put(actual,attempt);
            var sameRuntime=actual.frontend();var service=new FrontendRulesService(sameRuntime.rules().definitions(),actual.archive());
            var increment=new RootDomainInstallation("frontend-public-original-15",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
            attempt.installed=new Installed(increment,service);return attempt.installed;
        }
        private static final class Attempt { private Installed installed; }
    }
    public record Installed(RootDomainInstallation installation,FrontendRulesService service) {
        public Installed { Objects.requireNonNull(installation);Objects.requireNonNull(service); }
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        ExactRef source=context.source(RootFrontendRulesPublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendRulesContract.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendRulesCodec.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,FrontendRulesService.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,PublicSnapshotCodec.class);
        context.source(RootRuntimeSelectedSources.Module.APPLICATION,org.xar.ck3.control.application.capabilities.CampaignRootContextJson.class);
        var actual=new RootFrontendRulesPublicProducts(context);register(registry,actual::invoke,source);
        RootFixtureFrontendPublicProducts.install(context,registry);
        return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),List.of());
    }
    static List<RootRuntimePublicCatalog.DefinitionGap> definitionGaps() {
        return List.of(new RootRuntimePublicCatalog.DefinitionGap(Method.PREPARE_RULER.publicName(),
                "original up-to-eight random playable fallback lacks an actual independent selected-candidate/ineligible terminal producer; existing non-designer draw remains UNKNOWN and cannot authorize another draw"));
    }
    @FunctionalInterface public interface Handler { Response invoke(Request request)throws InterruptedException; }
    /** Same direct decoder/producer/encoder path used by the actual Root installation and mandatory SDK tests. */
    public static List<PublicBindings.TypedBinding<Request,Response>> register(PublicBindings registry,Handler handler,ExactRef source) {
        Objects.requireNonNull(registry);Objects.requireNonNull(handler);Objects.requireNonNull(source);
        return java.util.Arrays.stream(Method.values()).map(method->registry.register(publicMethod(method),Request.class,Response.class,request->{
                    StrictJson.require(request.method()==method,"decoded request differs from the original public tool");Response result=handler.invoke(request);StrictJson.require(result.method()==method,"public result came from another frontend tool");return result;
                },
                arguments->FrontendRulesCodec.decode(method,arguments),FrontendRulesCodec::encode,
                new PublicRoutes.Target(RootFrontendRulesPublicProducts.class.getName(),"invoke",source),PublicRoutes.Status.DELEGATED,
                "original frontend method over same Core menu/read/action authority; independent native postconditions and actual first Driver; current advertised permission guards remain authoritative")).toList();
    }
    public static PublicMethod publicMethod(Method method) { return PublicMethod.valueOf(method.publicName().substring(4).toUpperCase(java.util.Locale.ROOT)); }
    public Response invoke(Request request)throws InterruptedException {
        try {
            if(request instanceof Features features)return context.withCurrent(root->{
                var installed=context.installed(root);var service=installed.additionalDomains().frontendRules().service();
                var result=root.readCurrent(service.definitions().loadedFeatures(),features.expectedRevision(),new OpportunityJson.Obj(Map.of()),context.clock().instant().plus(context.observationTimeout()));
                return service.loadedFeatures(features,result);
            });
            // Context resolves the real same-Core menu and releases its initial read-only scope before this callback.
            Instant deadline=context.clock().instant().plus(context.observationTimeout());
            return context.withFrontend(deadline,(installed,menu,lease)->invokeMenu(installed,menu,lease,request,deadline));
        }catch(IOException unavailable) { throw new UncheckedIOException("actual original frontend operation did not produce a verified result; retain its canonical outcome and do not resend an unknown action",unavailable); }
    }
    private Response invokeMenu(RootInstalledCatalog installed,RootMenuSession menu,FrontendAuthority.LeaseSnapshot lease,Request request,Instant deadline)throws IOException,InterruptedException {
        var service=installed.additionalDomains().frontendRules().service();
        return service.execute(request,invocation(installed,menu,lease,"public-frontend-"+UUID.randomUUID(),deadline));
    }
    /** Main consumes this real model identity before its original canonical Start action. */
    static FrontendIdentity prepareFreshRobert(RootInstalledCatalog installed,RootMenuSession menu,FrontendAuthority.LeaseSnapshot lease,
            String actionId,Instant deadline)throws IOException,InterruptedException {
        var service=installed.additionalDomains().frontendRules().service();
        var selected=service.prepareFreshRobert(invocation(installed,menu,lease,actionId+"-frontend",deadline));
        return selected.receipt().after().binding().origin().requireFrontend();
    }
    private static FrontendRulesService.Invocation invocation(RootInstalledCatalog installed,RootMenuSession menu,FrontendAuthority.LeaseSnapshot lease,
            String actionId,Instant deadline)throws IOException {
        RootRuntimeContext same=installed.context();var runtime=installed.frontend();var service=installed.additionalDomains().frontendRules().service();
        StrictJson.require(same.frontend()==runtime&&service.definitions()==runtime.rules().definitions()&&same.core().requireFrontendMenu(same)==menu&&menu.frontend==runtime.authority()&&lease.source().equals(same.source())&&lease.identity().frontendSessionId().equals(same.game().sessionId()),"public frontend adapter crossed its installed Core/menu/definitions/source owner");
        var executor=new FrontendRulesExecutor(runtime.rules(),same.reads(),menu,same.archive());
        var initial=new FrontendRulesExecutor.Context(actionId,lease.identity(),same.source(),deadline);
        return new FrontendRulesService.Invocation(executor,menu,initial,
                (actual,key)->start(runtime,menu,actual,key),same.clock());
    }
    private static StartMaterial start(RootFrontendRuntime runtime,RootMenuSession menu,FrontendRulesExecutor.Context actual,String key)throws IOException,InterruptedException {
        GameplayEntryService entry=runtime.entry(menu);GameplayEntryService.Result result=entry.startSelected(actual.actionId(),actual.identity(),key,actual.deadline());
        if(!(result instanceof GameplayEntryService.Admitted admitted))throw new IOException("original Start has not completed its canonical first Driver entry; reconcile the original Start, never submit another");
        ActionReceipt receipt=admitted.actual();var state=(ActionState.Settled)receipt.state();var observation=((ActionState.GameplayEntered)state.settlement()).observation();observation.validate(receipt.command(),state.attempt());
        // This exact Complete is the provisional full Driver retained by the real initial adoption producer.
        var first=admitted.driver().first();StrictJson.require(first.identity().equals(observation.after())&&first.source().equals(observation.source()),"first actual adopted Driver differs from the independent Start source frame");
        RawJson snapshot=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(first,true));
        return new StartMaterial(receipt,snapshot,observation.campaignRootRead());
    }
}

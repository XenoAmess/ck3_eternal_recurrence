package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.function.Function;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.application.action.PhysicalActionRegistry;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaService;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** One public contract and actual Root registry for the finite CoA component producers. */
public final class RootFrontendCoaPublicProducts {
    private RootFrontendCoaPublicProducts() { }
    public static final Set<Method> DISK_METHODS=Set.of(Method.CONFIGURED_CATALOG,Method.DEFINITION_CATALOG,Method.DLC,
            Method.LOAD_CONFIGURATION,Method.RESOURCE_CATALOG,Method.CONFIGURED_ASSET,Method.DEFINITION,
            Method.RENDER_SUPPORT,Method.RESOURCE_ASSET);

    /** Prepared from explicit source inputs before Core; no public Context or invented Runtime. */
    public interface ComponentPrepared {
        Set<Method> methods();
        List<DomainBodies.Registration> domainRegistrations();
        List<NativePrivateActionPermission> privatePermissions();
        /** Components without a physical action advertise no physical producer. */
        default List<PhysicalActionRegistry.Binding> physicalBindings(){return List.of();}
        void bindCore(RootApplicationAssembly.Core same)throws IOException;
        ComponentInstalled install(RootRuntimeContext same)throws IOException;
    }
    /** Actual registrations and the service using those identical installed objects. */
    public record ComponentInstalled(RootDomainInstallation installation,FrontendCoaService.NativeAccess service) {
        public ComponentInstalled {Objects.requireNonNull(installation);Objects.requireNonNull(service);}
    }
    public record Installed(RootDomainInstallation installation,FrontendCoaService service) {
        public Installed {Objects.requireNonNull(installation);Objects.requireNonNull(service);}
    }
    private record Component(ComponentPrepared prepared,Set<Method> methods) {
        private Component {Objects.requireNonNull(prepared);methods=Set.copyOf(methods);}
    }
    public static final class Prepared {
        private final List<Component> components;
        private final Set<Method> methods;
        private final List<DomainBodies.Registration> registrations;
        private final List<NativePrivateActionPermission> permissions;
        private final List<PhysicalActionRegistry.Binding> physical;
        private final FrontendCoaService disk=new FrontendCoaService(List.of());
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private boolean bindingComplete;

        /** Explicit empty installation retains the nine disk products and advertises no absent component. */
        public Prepared(){this(List.of());}
        public Prepared(List<ComponentPrepared> actualComponents){
            var selected=new ArrayList<Component>();var owned=EnumSet.noneOf(Method.class);
            var registrationBySlot=new LinkedHashMap<DomainBodies.Slot,DomainBodies.Registration>();
            var allPermissions=new ArrayList<NativePrivateActionPermission>();
            var physicalByOperation=new LinkedHashMap<org.xar.ck3.control.application.action.OperationKey,PhysicalActionRegistry.Binding>();
            var identities=new IdentityHashMap<ComponentPrepared,Boolean>();
            for(ComponentPrepared prepared:List.copyOf(actualComponents)){
                Objects.requireNonNull(prepared);
                if(identities.put(prepared,Boolean.TRUE)!=null)throw new IllegalArgumentException("same CoA component supplied twice");
                Set<Method> finite=Set.copyOf(prepared.methods());
                if(finite.isEmpty()||finite.size()>7)throw new IllegalArgumentException("finite actual CoA component required");
                for(Method method:finite)if(DISK_METHODS.contains(method)||!owned.add(method))
                    throw new IllegalArgumentException("duplicate or foreign CoA method owner: "+method);
                selected.add(new Component(prepared,finite));
                for(var registration:List.copyOf(prepared.domainRegistrations())){
                    Objects.requireNonNull(registration);var old=registrationBySlot.putIfAbsent(registration.slot(),registration);
                    if(old!=null&&old!=registration)throw new IllegalArgumentException("distinct CoA canonical domain producers claim one slot");
                }
                allPermissions.addAll(List.copyOf(prepared.privatePermissions()));
                for(PhysicalActionRegistry.Binding binding:List.copyOf(prepared.physicalBindings())){
                    Objects.requireNonNull(binding);
                    if(physicalByOperation.putIfAbsent(binding.operation(),binding)!=null)
                        throw new IllegalArgumentException("distinct CoA physical producers claim one operation");
                }
            }
            if(selected.size()>4)throw new IllegalArgumentException("only the four finite CoA component families are supported");
            components=List.copyOf(selected);methods=Set.copyOf(owned);
            registrations=List.copyOf(registrationBySlot.values());permissions=List.copyOf(allPermissions);
            if(physicalByOperation.size()>32)throw new IllegalArgumentException("bounded actual physical CoA products required");
            physical=List.copyOf(physicalByOperation.values());
        }
        public List<DomainBodies.Registration> domainRegistrations(){return registrations;}
        public List<NativePrivateActionPermission> privatePermissions(){return permissions;}
        /** Identical source-owned producers reach the sole original coordinator once before Core use. */
        public List<PhysicalActionRegistry.Binding> physicalBindings(){return physical;}
        public Set<Method> componentMethods(){return methods;}
        public synchronized void bindCore(RootApplicationAssembly.Core same)throws IOException{
            Objects.requireNonNull(same);
            if(core!=null){if(core==same&&bindingComplete)return;throw new IOException("CoA Core binding already entered or belongs to another Core");}
            core=same;
            for(Component component:components)component.prepared().bindCore(same);
            bindingComplete=true;
        }
        public synchronized Installed install(RootRuntimeContext same)throws IOException{
            Objects.requireNonNull(same);
            if(!bindingComplete||same.core()!=core)throw new IOException("CoA installation requires its identical completely bound Core");
            Attempt prior=attempts.get(same);
            if(prior!=null){if(prior.installed!=null)return prior.installed;throw new IOException("partial CoA installation is not replayed",prior.failure);}
            if(attempts.size()>=64)throw new IOException("CoA actual installation bound exhausted");
            Attempt attempt=new Attempt();attempts.put(same,attempt);
            try{
                var installations=new ArrayList<RootDomainInstallation>();
                var services=new ArrayList<FrontendCoaService.ComponentBinding>();
                for(Component component:components){
                    if(!component.methods().equals(component.prepared().methods()))throw new IOException("CoA component method inventory changed after preparation");
                    ComponentInstalled actual=Objects.requireNonNull(component.prepared().install(same));
                    for(var registration:actual.installation().domainRegistrations())if(registrations.stream().noneMatch(original->original==registration))
                        throw new IOException("CoA component introduced a foreign canonical registration after Core");
                    installations.add(actual.installation());services.add(new FrontendCoaService.ComponentBinding(component.methods(),actual.service()));
                }
                attempt.installed=new Installed(combine(installations,registrations),new FrontendCoaService(services));return attempt.installed;
            }catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual CoA component installation failed",failure);throw attempt.failure;}
        }
        public FrontendCoaService staticService(){return disk;}
    }
    private static final class Attempt {Installed installed;IOException failure;}
    private static <T> List<T> all(List<RootDomainInstallation> actual,Function<RootDomainInstallation,List<T>> select){
        var out=new ArrayList<T>();for(var installation:actual)out.addAll(select.apply(installation));return List.copyOf(out);
    }
    private static RootDomainInstallation combine(List<RootDomainInstallation> actual,List<DomainBodies.Registration> registrations){
        var required=new LinkedHashSet<org.xar.ck3.control.application.action.OperationKey>();
        for(var installation:actual)required.addAll(installation.requiredPending());
        return new RootDomainInstallation("original-coa-actual-components/v1",registrations,
                all(actual,RootDomainInstallation::reads),all(actual,RootDomainInstallation::readFamilies),
                all(actual,RootDomainInstallation::actions),all(actual,RootDomainInstallation::composites),
                all(actual,RootDomainInstallation::archived),all(actual,RootDomainInstallation::actionFamilies),
                all(actual,RootDomainInstallation::compositeFamilies),all(actual,RootDomainInstallation::frontendAdmissions),
                all(actual,RootDomainInstallation::pending),Set.copyOf(required),all(actual,RootDomainInstallation::policies),
                all(actual,RootDomainInstallation::completions),all(actual,RootDomainInstallation::fixedDomains),
                all(actual,RootDomainInstallation::familyDomains),all(actual,RootDomainInstallation::compositeDomains));
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException{
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef implementation=context.source(RootFrontendCoaPublicProducts.class);
        context.sourceAt("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/publicmethods/frontendcoa/FrontendCoaContract.java",FrontendCoaContract.class);
        context.sourceAt("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/publicmethods/frontendcoa/FrontendCoaCodec.java",FrontendCoaCodec.class);
        context.sourceAt("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/publicmethods/frontendcoa/FrontendCoaService.java",FrontendCoaService.class);
        Prepared prepared=context.definitions().additionalDomains().frontendCoa();
        var bindings=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>(diskMethods(prepared.staticService(),implementation));
        bindings.addAll(componentMethods(prepared.componentMethods(),request->invokeInstalled(context,request),implementation));
        var gaps=new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
        for(Method method:Method.values())if(!DISK_METHODS.contains(method)&&!prepared.componentMethods().contains(method))
            gaps.add(new RootRuntimePublicCatalog.DefinitionGap(method.publicName(),"actual finite Root CoA component is not supplied in these source definitions"));
        return new RootPublicHandlerProductsFactory.Contribution(List.copyOf(bindings),List.of(),gaps);
    }
    @FunctionalInterface public interface ComponentHandler {
        Response invoke(Request request)throws InterruptedException;
    }
    /** Same finite binding producer for actual installed callbacks and source-only SDK parity DATA. */
    public static List<McpExecutableDirectory.DirectBinding<?,?>> componentMethods(Set<Method> installedMethods,
            ComponentHandler actual,ExactRef implementation){
        Set<Method> finite=Set.copyOf(installedMethods);Objects.requireNonNull(actual);Objects.requireNonNull(implementation);
        if(finite.size()>19||finite.stream().anyMatch(DISK_METHODS::contains))throw new IllegalArgumentException("only actual finite native CoA component methods required");
        var out=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>();
        for(Method method:Method.values())if(finite.contains(method))out.add(new McpExecutableDirectory.DirectBinding<>(
                method.publicName(),PublicMcpBindings.Kind.DRIVER_DIRECT,Request.class,Response.class,
                request->invokeComponent(actual,request),call->FrontendCoaCodec.decode(method,call.arguments().objectOrEmpty()),
                result->CallResult.fromBusinessJson(FrontendCoaCodec.encode(result)),
                new PublicRoutes.Target(RootFrontendCoaPublicProducts.class.getName(),"invokeComponent",implementation)));
        return List.copyOf(out);
    }
    private static Response invokeComponent(ComponentHandler actual,Request request)throws InterruptedException{return actual.invoke(request);}
    private static Response invokeInstalled(RootPublicHandlerProductsFactory.Context context,Request request)throws InterruptedException{
        try{return context.withActualView(
                root->context.installed(root).additionalDomains().frontendCoa().service().execute(request),
                (installed,menu,initial)->installed.additionalDomains().frontendCoa().service().execute(request));}
        catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static Response invokeDisk(FrontendCoaService actual,Request request)throws InterruptedException{
        try{return actual.execute(request);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    /** Mandatory original-descriptor producer-to-public-consumer regressions use these actual handlers. */
    public static List<McpExecutableDirectory.DirectBinding<?,?>> diskMethods(FrontendCoaService actual,ExactRef implementation){
        Objects.requireNonNull(actual);Objects.requireNonNull(implementation);var out=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>();
        for(Method method:Method.values())if(DISK_METHODS.contains(method))out.add(new McpExecutableDirectory.DirectBinding<>(method.publicName(),PublicMcpBindings.Kind.STATIC_KNOWLEDGE,
                Request.class,Response.class,request->invokeDisk(actual,request),call->FrontendCoaCodec.decode(method,call.arguments().objectOrEmpty()),
                result->CallResult.fromBusinessJson(FrontendCoaCodec.encode(result)),
                new PublicRoutes.Target(RootFrontendCoaPublicProducts.class.getName(),"invokeDisk",implementation)));
        return List.copyOf(out);
    }
}

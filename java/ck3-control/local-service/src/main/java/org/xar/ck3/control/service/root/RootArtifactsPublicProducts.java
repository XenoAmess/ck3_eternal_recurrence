package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Original artifact public products. A missing actual action product is a source join, never native unsupported. */
public final class RootArtifactsPublicProducts {
    /** Native inventory requires its real provider digest; absence defers only inventory operations. */
    public sealed interface InventoryBinding permits NativeInventoryDigest,InventoryDeferred { }
    public record NativeInventoryDigest(String sha256) implements InventoryBinding {
        public NativeInventoryDigest {StrictJson.require(sha256!=null&&sha256.matches("[0-9a-f]{64}"),"actual native inventory SHA required");}
    }
    public record InventoryDeferred(String reason) implements InventoryBinding {
        public InventoryDeferred {StrictJson.require(reason!=null&&!reason.isBlank(),"inventory defer reason required");}
    }
    public record Config(InventoryBinding inventory) {
        public Config {Objects.requireNonNull(inventory);}
    }
    public static Prepared ordinary(Config config,RootGuiPublicProducts.Prepared sameGui,
            RootReligionPublicProducts.SharedKernel sameReligion,RootCoreBoundPorts ports,
            RootAdditionalDomains.ImplementationMetadata metadata)throws IOException {
        return RootArtifactsSourcesFactory.prepareOrdinary(config,sameGui,sameReligion,ports,metadata);
    }
    /**
     * Source owner of real original-intent custody and coordinator action preparation/post/replay.
     * Implementations must use the supplied actual Root; source selection does not instantiate an invented session.
     */
    public interface ActionProducts {
        Set<Method> supportedMethods();
        RootDomainInstallation installation();
        List<NativePrivateActionPermission> privatePermissions();
        Reply execute(RootApplicationSession actualRoot,Request request,Instant deadline)throws IOException,InterruptedException;
    }
    public interface ActionFactory {
        Set<Method> supportedMethods();
        ActionProducts install(RootRuntimeContext actual,ArtifactsService sameService)throws IOException;
    }
    /** Exact actual source ports; missing actions do not become blanket unsupported handlers. */
    public record Sources(ArtifactsService.Sources nativeSources,ExactRef rootSource,
            List<DomainBodies.Registration> registrations,Optional<ActionFactory> actions,
            Optional<RootGuiPublicProducts.NavigationDefinition> navigation,
            Optional<RootGuiPublicProducts.InventoryFactory> inventory) {
        public Sources {
            Objects.requireNonNull(nativeSources);Objects.requireNonNull(rootSource);
            registrations=List.copyOf(registrations);Objects.requireNonNull(actions);
            Objects.requireNonNull(navigation);Objects.requireNonNull(inventory);
            StrictJson.require(rootSource.bytes()>0,"actual artifact Root product source required");
        }
    }
    public record Installed(RootDomainInstallation installation,ArtifactsService service) {
        public Installed {Objects.requireNonNull(installation);Objects.requireNonNull(service);}
    }
    private record Attempt(Optional<Installed> success,Optional<IOException> failure,Optional<ActionProducts> actions) {
        private Attempt {Objects.requireNonNull(success);Objects.requireNonNull(failure);Objects.requireNonNull(actions);
            StrictJson.require(success.isPresent()!=failure.isPresent(),"artifact install has one actual success/failure branch");}
    }
    /** Core lifetime, with one retained installation attempt per actual Game/context. */
    public static final class Prepared {
        private final Sources sources;
        private final List<DomainBodies.Registration> registrations;
        private final List<NativePrivateActionPermission> permissions;
        private final Set<Method> actionMethods;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        public Prepared(Sources sources) {
            this.sources=Objects.requireNonNull(sources);registrations=sources.registrations();
            // No late per-Game mutation of the pre-Core permission table.
            permissions=ArtifactsService.privatePermissions(sources.nativeSources());
            actionMethods=sources.actions().map(factory->requireFiniteActions(factory.supportedMethods())).orElseGet(Set::of);
            StrictJson.require(sources.nativeSources().enabled().containsAll(actionMethods),
                    "declared artifact actions lack their actual source-qualified methods");
        }
        public List<DomainBodies.Registration> domainRegistrations(){return registrations;}
        public List<NativePrivateActionPermission> privatePermissions(){return permissions;}
        public Set<Method> actionMethods(){return actionMethods;}
        public synchronized void bindCore(RootApplicationAssembly.Core actual) {
            StrictJson.require(core==null,"artifact Prepared binds its actual Core once");
            core=Objects.requireNonNull(actual);
        }
        public RootGuiPublicProducts.NavigationDefinition navigationDefinition() {
            return sources.navigation().orElseThrow(()->new IllegalStateException(
                    "SOURCE_JOIN_REQUIRED: actual artifact Nav preparation, original once custody, independent post and replay products absent"));
        }
        public List<RootGuiPublicProducts.NavigationDefinition> navigationDefinitions() {
            return sources.navigation().stream().toList();
        }
        public RootGuiPublicProducts.InventoryFactory inventoryDefinition() {
            if(sources.inventory().isPresent())return sources.inventory().orElseThrow();
            return actual->{
                Installed sameInstalled=install(actual);
                return invocation->actual.withSession(same->{
                    var original=invocation.nativeContext();
                    StrictJson.require(original.before().game().equals(actual.game().generation())
                            &&original.source().equals(actual.source())&&original.sessionId().equals(actual.game().sessionId()),
                            "GUI inventory call belongs to another actual Root/Game/source/session");
                    var identity=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(
                            actual.game().machineId(),actual.game().generation(),actual.game().sessionId());
                    return actual.collector().currentOwned(same,identity,original.deadline(),lease->{
                        var captured=lease.frame();
                        StrictJson.require(captured.identity().equals(original.before())&&captured.source().equals(original.source())
                                &&captured.sessionId().equals(original.sessionId()),"GUI internal inventory crossed the actual held frame");
                        var service=sameInstalled.service();var query=service.inventorySelection(captured,original.deadline());
                        var observed=actual.reads().read(same,service.inventoryContract(actual.readCatalog(),query),service.inventoryRequest(query));
                        if(observed instanceof PlanningReadResult.Known<ArtifactsService.InventoryResult> known){
                            var archive=actual.archive().withSession(same);var reference=archive.readReferenceOf(known.receipt());
                            // Internal READ mirrors GuiService.read; RootGuiPublicProducts.invokeObserved alone produces the actual public before/parsed-return tokens.
                            return new org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui.GuiContract.ReadReply(known.receipt(),reference,Optional.empty(),Optional.empty());
                        }
                        throw new IOException("actual internal inventory QUERY unavailable; no OPEN/CLOSE schema substitution: "+observed);
                    });
                });
            };
        }
        public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);
            StrictJson.require(core!=null&&actual.core()==core,"artifact actual context belongs to another/unbound Core");
            Attempt prior=attempts.get(actual);
            if(prior!=null){if(prior.failure().isPresent())throw new IOException("original artifact installation already failed; not replayed",prior.failure().orElseThrow());return prior.success().orElseThrow();}
            StrictJson.require(attempts.size()<64,"artifact bounded actual context history exhausted");
            try {
                var service=new ArtifactsService(actual.transport(),sources.nativeSources());
                Optional<ActionProducts> actions=sources.actions().map(factory->{
                    StrictJson.require(requireFiniteActions(factory.supportedMethods()).equals(actionMethods),
                            "artifact pre-Core action declaration changed before actual installation");
                    try{return factory.install(actual,service);}catch(IOException failure){throw new UncheckedIOException(failure);}
                });
                if(actions.isPresent())StrictJson.require(requireFiniteActions(actions.orElseThrow().supportedMethods()).equals(actionMethods),
                        "artifact actual action runtime differs from its pre-Core source declaration");
                RootDomainInstallation installation=installation(service,actions,sources);
                Installed result=new Installed(installation,service);
                attempts.put(actual,new Attempt(Optional.of(result),Optional.empty(),actions));return result;
            }catch(RuntimeException failure) {
                IOException retained=failure instanceof UncheckedIOException io?io.getCause():new IOException("artifact actual product installation failed",failure);
                attempts.put(actual,new Attempt(Optional.empty(),Optional.of(retained),Optional.empty()));throw retained;
            }
        }
        public synchronized Optional<ActionProducts> actionProducts(RootRuntimeContext actual)throws IOException {
            install(actual);return attempts.get(actual).actions();
        }
    }
    private static RootDomainInstallation installation(ArtifactsService service,Optional<ActionProducts> action,Sources sources) {
        if(action.isEmpty())return new RootDomainInstallation("original-artifacts-reads-12004/v1",sources.registrations(),
                List.of(),service.readFamilies(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                java.util.Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        RootDomainInstallation a=action.orElseThrow().installation();
        var families=new ArrayList<RootReadContractCatalog.Family<?,?>>(service.readFamilies());families.addAll(a.readFamilies());
        StrictJson.require(a.domainRegistrations().equals(sources.registrations()),"artifact action product changed pre-Core registrations");
        return new RootDomainInstallation("original-artifacts-12004/v1",a.domainRegistrations(),a.reads(),families,a.actions(),
                a.composites(),a.archived(),a.actionFamilies(),a.compositeFamilies(),a.frontendAdmissions(),a.pending(),
                a.requiredPending(),a.policies(),a.completions(),a.fixedDomains(),a.familyDomains(),a.compositeDomains());
    }
    @FunctionalInterface interface Read { Reply invoke(Request request)throws InterruptedException; }
    @FunctionalInterface interface Action { Reply invoke(Request request)throws InterruptedException; }
    static Set<Method> requireFiniteActions(Set<Method> actual) {
        Set<Method> frozen=Set.copyOf(Objects.requireNonNull(actual));
        Set<Method> finite=Set.of(Method.SELECT_RELIC,Method.RELIC_SLOT,Method.ENSHRINE,Method.REMOVE,Method.CREATION_SELECTION,Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT);
        StrictJson.require(finite.containsAll(frozen),"only the eight exact original artifact actions may be declared by actual source products");
        return frozen;
    }
    private RootArtifactsPublicProducts(){ }
    public static RootPublicHandlerProductsFactory.Contribution install(
            RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef source;Set<Method> actions;
        try {
            source=context.source(RootArtifactsPublicProducts.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArtifactsService.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArtifactsContract.class);
            context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ArtifactsCodec.class);
            actions=requireFiniteActions(context.definitions().additionalDomains().artifacts().actionMethods());
            if(!actions.isEmpty())context.source(RootArtifactsSourcesFactory.class);
        }catch(IOException unavailable){
            return new RootPublicHandlerProductsFactory.Contribution(List.of(),List.of(),missingAll(
                    "actual complete artifact source closure unavailable: "+unavailable.getMessage()));
        }
        var actual=new Current(context);
        // Action declarations come from the actual pre-Core source factory and are rechecked against its runtime.
        var gaps=new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
        for(Method method:Method.values())if(!method.readOnly()&&!actions.contains(method))gaps.add(new RootRuntimePublicCatalog.DefinitionGap(
                method.originalName(),"SOURCE_JOIN_REQUIRED: original once ledger/legacy custody, sameRoot action preparation, independent post/replay and finite GUI extension are not yet supplied; native .4 support is not denied"));
        var direct=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>(readBindings(source,actual::read));
        direct.addAll(actionBindings(source,actions,actual::action));
        return new RootPublicHandlerProductsFactory.Contribution(direct,List.of(),gaps);
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> actionBindings(ExactRef source,Set<Method> declared,Action current) {
        Objects.requireNonNull(source);Objects.requireNonNull(current);Set<Method> methods=requireFiniteActions(declared);
        var result=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>();
        for(Method method:Method.values())if(methods.contains(method))result.add(new McpExecutableDirectory.DirectBinding<>(
                method.originalName(),PublicMcpBindings.Kind.DRIVER_DIRECT,Request.class,Reply.class,request->{
                    StrictJson.require(request.method()==method,"artifact action named route changed its exact original method");
                    Reply reply=current.invoke(request);StrictJson.require(reply.method()==method,"artifact action result belongs to another original method");return reply;
                },call->ArtifactsCodec.decode(method.originalName(),required(call.arguments())),
                reply->PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(ArtifactsCodec.encode(reply)))),
                new PublicRoutes.Target(RootArtifactsPublicProducts.class.getName(),method.originalName(),source)));
        return List.copyOf(result);
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> readBindings(ExactRef source,Read current) {
        Objects.requireNonNull(source);Objects.requireNonNull(current);
        var result=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>();
        for(Method method:Method.values())if(method.readOnly())result.add(binding(source,method,current));
        return List.copyOf(result);
    }
    private static McpExecutableDirectory.DirectBinding<Request,Reply> binding(ExactRef source,Method method,Read current) {
        return new McpExecutableDirectory.DirectBinding<>(method.originalName(),PublicMcpBindings.Kind.DRIVER_DIRECT,
                Request.class,Reply.class,request->{
                    StrictJson.require(request.method()==method,"artifact actual named route differs");return current.invoke(request);
                },call->ArtifactsCodec.decode(method.originalName(),required(call.arguments())),
                reply->PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(ArtifactsCodec.encode(reply)))),
                new PublicRoutes.Target(RootArtifactsPublicProducts.class.getName(),method.originalName(),source));
    }
    static JsonNode required(PublicMcpDirectory.Arguments arguments) {
        StrictJson.require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,
                "original artifact named arguments must be present/non-null");
        JsonNode raw=StrictJson.parse(arguments.original().orElseThrow().bytes());
        StrictJson.require(raw.isObject(),"original artifact arguments must be a JSON object");return raw;
    }
    static List<RootRuntimePublicCatalog.DefinitionGap> missingAll(String reason) {
        var gaps=new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
        for(Method method:Method.values())gaps.add(new RootRuntimePublicCatalog.DefinitionGap(method.originalName(),reason));
        return List.copyOf(gaps);
    }
    private record Current(RootPublicHandlerProductsFactory.Context context) {
        private Reply action(Request request)throws InterruptedException {
            Instant deadline=context.clock().instant().plus(context.actionTimeout());
            try{return context.withCurrent(root->{
                var installed=context.installed(root);var actual=installed.context();
                StrictJson.require(actual.actions()==root,"artifact public action lost the identical current Root coordinator");
                var prepared=context.definitions().additionalDomains().artifacts();
                Set<Method> declared=prepared.actionMethods();
                StrictJson.require(declared.contains(request.method()),"artifact action lacks an actual pre-Core source declaration");
                ActionProducts product=prepared.actionProducts(actual).orElseThrow(()->new IOException("actual finite artifact action product missing"));
                StrictJson.require(requireFiniteActions(product.supportedMethods()).equals(declared),
                        "artifact runtime methods differ from their actual pre-Core declaration");
                return product.execute(root,request,deadline);
            });}catch(IOException unavailable){throw new UncheckedIOException("actual sameRoot artifact action unavailable; original pending custody is retained",unavailable);}
        }
        private Reply read(Request request)throws InterruptedException {
            Instant deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->{
                Installed installed=context.installed(root).additionalDomains().artifacts();
                StrictJson.require(context.installed(root).context().actions()==root,
                        "artifact public read lost identical current Root owner");
                return root.withPublicObservation(deadline,(complete,known,same)->{
                    ArtifactsService service=installed.service();var selection=service.select(complete,request,deadline);
                    var current=context.installed(root).context();
                    var value=current.reads().read(same,service.issue(current.readCatalog(),selection),service.request(selection));
                    if(value instanceof PlanningReadResult.Known<Reply> observed)return observed.value();
                    throw new IOException("actual original artifact read unavailable; no fabricated native body: "+value);
                });
            });}catch(IOException unavailable){throw new UncheckedIOException("actual sameRoot artifact observation unavailable",unavailable);}
        }
    }
}

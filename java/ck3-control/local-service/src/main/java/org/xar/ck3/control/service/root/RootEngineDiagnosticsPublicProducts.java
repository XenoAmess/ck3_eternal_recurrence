package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.NativePrelaunchInputs;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog.TextRules;
import static org.xar.ck3.control.service.root.EngineDiagnostics.*;

/** Two original fixed-profile read tools. Their private provider comes from the retained prelaunch inputs. */
public final class RootEngineDiagnosticsPublicProducts {
    public static final String DIAGNOSTICS="ck3_query_engine_diagnostics_v1",LITERALS="ck3_query_engine_log_literals_v1";
    private RootEngineDiagnosticsPublicProducts() { }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final NativeLaunchPlan plan;private final java.util.Optional<RootRuntimeStorageGuard> storage;private final TextRules textRules;
        private final java.util.Optional<RootRuntimeDefinitions.Inputs> inputs;private final Clock clock;private final Path profile;private final SharedSourceFiles.DirectoryIdentity directory;
        private final RootDriverRegistryPublicProducts.ProductSource source;private RootApplicationAssembly.Core core;
        private Prepared(NativeLaunchPlan plan,RootRuntimeStorageGuard storage,TextRules textRules,RootRuntimeDefinitions.Inputs inputs,Clock clock)throws IOException {
            this.plan=Objects.requireNonNull(plan);this.storage=java.util.Optional.of(Objects.requireNonNull(storage));this.textRules=Objects.requireNonNull(textRules);this.inputs=java.util.Optional.of(Objects.requireNonNull(inputs));this.clock=Objects.requireNonNull(clock);
            requireConfiguredPlan();NativePrelaunchInputs.requireCurrent(plan,clock);this.storage.get().requireReadAuthorityCurrent();this.inputs.get().application().requireCurrent(clock);
            profile=plan.profileDirectory();SharedSourceFiles.plainAncestors(profile);
            if(!Files.isDirectory(profile,LinkOption.NOFOLLOW_LINKS)||!profile.toRealPath().equals(profile))throw new IOException("actual canonical prepared Game profile directory required");
            source=new RootDriverRegistryPublicProducts.ProductSource(RootEngineDiagnosticsPublicProducts.class,"local-service/src/main/java/org/xar/ck3/control/service/root/RootEngineDiagnosticsPublicProducts.java",new RootRuntimeSelectedSources(this.inputs.get()).javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootEngineDiagnosticsPublicProducts.class));
            directory=SharedSourceFiles.nativeDirectory(profile);plan.sources().requireLoadedClass(RootEngineDiagnosticsPublicProducts.class);plan.sources().requireLoadedClass(EngineDiagnosticsReader.class);plan.sources().requireLoadedClass(EngineDiagnostics.class);
            if(!plan.sources().review().machineId().equals(this.inputs.get().application().machineId()))throw new IOException("diagnostic profile belongs to another actual startup machine");
        }
        private Prepared(NativeLaunchPlan plan,TextRules textRules,ExactRef actualImplementation,Clock clock)throws IOException {
            this.plan=Objects.requireNonNull(plan);this.storage=java.util.Optional.empty();this.textRules=Objects.requireNonNull(textRules);this.inputs=java.util.Optional.empty();this.clock=Objects.requireNonNull(clock);
            profile=plan.profileDirectory();SharedSourceFiles.plainAncestors(profile);
            if(!Files.isDirectory(profile,LinkOption.NOFOLLOW_LINKS)||!profile.toRealPath().equals(profile))throw new IOException("actual canonical prepared Game profile directory required");
            source=new RootDriverRegistryPublicProducts.ProductSource(RootEngineDiagnosticsPublicProducts.class,"local-service/src/main/java/org/xar/ck3/control/service/root/RootEngineDiagnosticsPublicProducts.java",actualImplementation);
            directory=SharedSourceFiles.nativeDirectory(profile);
        }
        @Override public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.ENGINE_DIAGNOSTICS;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source(){return source;}
        @Override public List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public java.util.Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            Objects.requireNonNull(actual);if(inputs.isPresent()&&!actual.configuration().equals(inputs.get().application())||core!=null&&core!=actual)throw new IOException("engine product crossed its actual Core");requireCurrent();core=actual;
        }
        @Override public synchronized RootDriverRegistryPublicProducts.Product install(RootRuntimeContext actual)throws IOException {
            if(core==null||actual.core()!=core)throw new IOException("engine product requires its bound identical actual Core");requireCurrent();return new Installed(actual,this);
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {requireOwner(context.inputs());source.requireCurrent(context);return RootEngineDiagnosticsPublicProducts.install(context,registry);}
        void requireOwner(RootRuntimeDefinitions.Inputs same)throws IOException {if(inputs.isPresent()&&inputs.get()!=same)throw new IOException("diagnostic profile belongs to another retained startup input instance");requireCurrent();}
        Path requireCurrent()throws IOException {
            if(inputs.isPresent()){inputs.get().application().requireCurrent(clock);requireConfiguredPlan();NativePrelaunchInputs.requireCurrent(plan,clock);storage.get().requireReadAuthorityCurrent();}
            SharedSourceFiles.plainAncestors(profile);if(!directory.equals(SharedSourceFiles.nativeDirectory(profile)))throw new IOException("configured diagnostic profile identity changed");return profile;
        }
        private void requireConfiguredPlan()throws IOException {
            var source=inputs.get().application().nativeLaunchPlan();var ref=new org.xar.ck3.control.build.ControlBuild.FileRef(source.path(),source.bytes(),source.sha256());
            if(ref.bytes()<1||ref.bytes()>NativeLaunchPlanCodec.MAXIMUM_BYTES)throw new IOException("bounded same-startup Native plan required");ref.verify();
            byte[] raw;try(var file=Files.newInputStream(Path.of(ref.path()))){raw=file.readNBytes(NativeLaunchPlanCodec.MAXIMUM_BYTES+1);}
            if(raw.length!=ref.bytes()||!NativeLaunchPlanCodec.fromJson(StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES)).equals(NativeLaunchPlanCodec.describe(plan)))throw new IOException("diagnostic actual plan differs from identical startup's exact original configuration");ref.verify();
        }
        Path profile(){return profile;}TextRules textRules(){return textRules;}Clock clock(){return clock;}
        public Diagnostics diagnostics(Query query,Duration timeout)throws IOException {return new EngineDiagnosticsReader(this).diagnostics(Objects.requireNonNull(query),deadline(timeout));}
        public EngineDiagnostics.Literals literals(LiteralQuery query,Duration timeout)throws IOException {return new EngineDiagnosticsReader(this).literals(Objects.requireNonNull(query),deadline(timeout));}
        private java.time.Instant deadline(Duration timeout){require(timeout!=null&&!timeout.isZero()&&!timeout.isNegative()&&timeout.compareTo(Duration.ofMinutes(2))<=0,"finite public observation timeout required");return clock.instant().plus(timeout);}
    }
    private static final class Installed implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;private final Prepared actual;
        private final RootDomainInstallation installation=new RootDomainInstallation("engine-diagnostics-fixed-profile",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        private Installed(RootRuntimeContext context,Prepared actual){this.context=Objects.requireNonNull(context);this.actual=Objects.requireNonNull(actual);}
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public void requireContext(RootRuntimeContext same)throws IOException {if(same!=context||same.core()!=actual.core)throw new IOException("engine product belongs to another physical Root context");actual.requireCurrent();}
    }
    public static Prepared prepare(NativeLaunchPlan sameActualPlan,RootRuntimeStorageGuard sameActualStorage,
            TextRules sharedOriginalTextRules,RootRuntimeDefinitions.Inputs identicalInputs,Clock clock)throws IOException {
        return new Prepared(sameActualPlan,sameActualStorage,sharedOriginalTextRules,identicalInputs,clock);
    }
    public static Prepared prepareOrdinary(NativeLaunchPlan plan,TextRules textRules,ExactRef actualImplementation,Clock clock)throws IOException {
        return new Prepared(plan,textRules,actualImplementation,clock);
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);require(!registry.frozen(),"public registry is frozen");
        Prepared actual=context.engineDiagnostics();actual.requireOwner(context.inputs());ExactRef source=context.source(RootEngineDiagnosticsPublicProducts.class);
        context.source(EngineDiagnosticsReader.class);context.source(EngineDiagnostics.class);
        var diagnostics=diagnosticsBinding(source,request->{try{actual.requireOwner(context.inputs());return EngineDiagnostics.encode(actual.diagnostics(request,context.observationTimeout()));}catch(IOException unavailable){throw new UncheckedIOException("actual configured engine diagnostics unavailable",unavailable);}});
        var literals=literalsBinding(source,request->{try{actual.requireOwner(context.inputs());return EngineDiagnostics.encode(actual.literals(request,context.observationTimeout()));}catch(IOException unavailable){throw new UncheckedIOException("actual configured engine log unavailable",unavailable);}});
        return new RootPublicHandlerProductsFactory.Contribution(List.of(diagnostics,literals),List.of(),List.of());
    }
    static McpExecutableDirectory.DirectBinding<Query,RawJson> diagnosticsBinding(ExactRef source,PublicRoutes.Handler<Query,RawJson> actual){return new McpExecutableDirectory.DirectBinding<>(DIAGNOSTICS,PublicMcpBindings.Kind.DRIVER_DIRECT,Query.class,RawJson.class,actual,call->decodeDiagnostics(call.arguments()),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(RootEngineDiagnosticsPublicProducts.class.getName(),"diagnostics",source));}
    static McpExecutableDirectory.DirectBinding<LiteralQuery,RawJson> literalsBinding(ExactRef source,PublicRoutes.Handler<LiteralQuery,RawJson> actual){return new McpExecutableDirectory.DirectBinding<>(LITERALS,PublicMcpBindings.Kind.DRIVER_DIRECT,LiteralQuery.class,RawJson.class,actual,call->decodeLiterals(call.arguments()),PublicMcpDirectory.CallResult::fromBusinessJson,new PublicRoutes.Target(RootEngineDiagnosticsPublicProducts.class.getName(),"literals",source));}
    public static Query decodeDiagnostics(PublicMcpDirectory.Arguments arguments) {
        ObjectNode row=arguments(arguments,Set.of("fingerprint_limit","tail_limit"));return new Query(row.has("fingerprint_limit")?(int)StrictJson.integer(row.get("fingerprint_limit"),1,100):50,row.has("tail_limit")?(int)StrictJson.integer(row.get("tail_limit"),1,100):25);
    }
    public static LiteralQuery decodeLiterals(PublicMcpDirectory.Arguments arguments) {
        ObjectNode row=arguments(arguments,Set.of("log_name","literals","sample_limit"));require(row.has("log_name")&&row.has("literals"),"log_name and literals are mandatory");
        JsonNode names=row.get("literals");require(names.isArray(),"literals must be an array");List<String> literals=new ArrayList<>();for(JsonNode value:names){require(value.isTextual(),"literal must be a string");literals.add(value.textValue());}
        return new LiteralQuery(LogName.decode(StrictJson.text(row.get("log_name"))),literals,row.has("sample_limit")?(int)StrictJson.integer(row.get("sample_limit"),0,5):3);
    }
    private static ObjectNode arguments(PublicMcpDirectory.Arguments arguments,Set<String> allowed) {
        Objects.requireNonNull(arguments);if(arguments.presence()==PublicMcpDirectory.Presence.MISSING)return StrictJson.object();
        require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,"named arguments object required");JsonNode raw=StrictJson.parse(arguments.original().orElseThrow().bytes(),65536);
        require(raw.isObject(),"named arguments object required");var keys=new HashSet<String>();raw.fieldNames().forEachRemaining(keys::add);require(allowed.containsAll(keys),"unknown diagnostic field; path and regex are forbidden");return StrictJson.object(raw,keys);
    }
}

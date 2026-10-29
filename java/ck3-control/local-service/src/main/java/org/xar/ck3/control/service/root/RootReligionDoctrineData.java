package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.Group;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.Kind;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.Selection;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.Observed;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.*;

/** Real source-qualified readonly installation shared by the doctrine-data and draft components. */
public final class RootReligionDoctrineData {
    private RootReligionDoctrineData() { }
    public record Definition(Kind kind,ReligionDoctrineDraftReads.Sources sources){public Definition{Objects.requireNonNull(kind);Objects.requireNonNull(sources);}}
    public record JavaSource(RootRuntimeSelectedSources.Module module,Class<?> type,ExactRef source){public JavaSource{Objects.requireNonNull(module);Objects.requireNonNull(type);Objects.requireNonNull(source);}}
    public record Sources(Group group,ExactRef implementation,ExactRef decoder,List<JavaSource> javaSources,List<Definition> definitions){
        public Sources{Objects.requireNonNull(group);Objects.requireNonNull(implementation);Objects.requireNonNull(decoder);javaSources=List.copyOf(javaSources);definitions=List.copyOf(definitions);need(definitions.stream().map(Definition::kind).toList().equals(kinds(group)),"complete exact original doctrine/draft definitions required");need(!javaSources.isEmpty(),"actual installed Java source closure required");}
        public Sources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeNativeOriginals.Bound originals,Clock clock,
                Group group,ExactRef implementation,ExactRef decoder,List<JavaSource> javaSources,List<Definition> definitions){
            this(group,implementation,decoder,javaSources,definitions);
        }
        public ReligionDoctrineDraftReads.Sources source(Kind kind){return definitions.stream().filter(d->d.kind()==kind).findFirst().orElseThrow().sources();}
    }
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){return ordinary(metadata,Group.DATA,RootReligionDoctrineData.class);}
    static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata,Group group,Class<?> entrypoint){
        Objects.requireNonNull(metadata);Objects.requireNonNull(group);var javaSources=new ArrayList<JavaSource>();
        var implementation=metadata.implementation(RootReligionDoctrineData.class);var decoder=metadata.implementation(ReligionDoctrineDraftReads.class);
        javaSources.add(new JavaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootReligionDoctrineData.class,implementation));
        if(entrypoint!=RootReligionDoctrineData.class)javaSources.add(new JavaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,entrypoint,metadata.implementation(entrypoint)));
        javaSources.add(new JavaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionDoctrineDraftReads.class,decoder));
        Class<?> validation=group==Group.DATA?ReligionDoctrineDataValidation.class:ReligionReformDraftValidation.class;
        javaSources.add(new JavaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,validation,metadata.implementation(validation)));
        var closure=javaSources.stream().map(JavaSource::source).distinct().toList();
        var definitions=kinds(group).stream().map(kind->new Definition(kind,new ReligionDoctrineDraftReads.Sources(decoder,decoder,closure))).toList();
        return new Prepared(new Sources(group,implementation,decoder,javaSources,definitions));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException{return prepare(inputs,selected,originals,clock,Group.DATA,RootReligionDoctrineData.class);}
    static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock,Group group,Class<?> entrypoint)throws IOException{
        var javaSources=new ArrayList<JavaSource>();var implementation=javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.LOCAL_SERVICE,entrypoint);
        if(entrypoint!=RootReligionDoctrineData.class)implementation=javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootReligionDoctrineData.class);
        var decoder=javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionDoctrineDraftReads.class);
        javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionTemporalFinance.class);
        if(group==Group.DATA)javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionDoctrineDataValidation.class);
        else javaSource(selected,javaSources,RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionReformDraftValidation.class);
        String prefix="ck3_autonomous_player/src/xar_autoplayer/bridge/";var shared=new ArrayList<ExactRef>();
        for(String name:List.of("native_driver.py","g2_private_query_transport.py","nonwar_private_build.py","version_identity.py"))shared.add(RootReligionSourcesFactory.original(inputs,selected,prefix+name));
        for(var source:javaSources)shared.add(source.source());var definitions=new ArrayList<Definition>();
        for(Kind kind:kinds(group)){
            var definition=RootReligionSourcesFactory.original(inputs,selected,prefix+kind.original());var closure=new ArrayList<>(shared);closure.add(definition);
            List<String> dependencies=switch(kind){case TENETS->List.of("target_rite_tenet_comparison_12003.py","player_tenet_knowledge_catalogue_12003.py");case REFORM_CONTEXT->List.of("player_religion_creation_terms12003.py");case DRAFT_RESOURCE_COSTS->List.of("religion_creation_price_source_12004.py");default->List.of();};
            for(String name:dependencies)closure.add(RootReligionSourcesFactory.original(inputs,selected,prefix+name));definitions.add(new Definition(kind,new ReligionDoctrineDraftReads.Sources(definition,decoder,closure)));
        }
        var sources=new Sources(inputs,originals,clock,group,implementation,decoder,javaSources,definitions);return new Prepared(sources);
    }
    private static ExactRef javaSource(RootRuntimeSelectedSources selected,List<JavaSource> closure,RootRuntimeSelectedSources.Module module,Class<?> type)throws IOException{var ref=selected.javaSource(module,type);closure.add(new JavaSource(module,type,ref));return ref;}
    public static List<Kind> kinds(Group group){return Arrays.stream(Kind.values()).filter(k->k.group()==group).toList();}
    public static List<String> methodsList(Group group){return kinds(group).stream().map(Kind::method).toList();}
    private static String id(Group group){return "religion-original-"+(group==Group.DATA?"doctrine-data":"reform-draft")+"/v1";}
    private static final class Attempt{Runtime runtime;IOException failure;}
    public static final class Prepared implements RootReligionPublicProducts.ExtensionPrepared{
        private final Sources sources;private RootReligionPublicProducts.SharedKernel kernel;private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        public String id(){return RootReligionDoctrineData.id(sources.group());}
        public List<String> originalMethods(){return methodsList(sources.group());}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindShared(RootReligionPublicProducts.SharedKernel same){need(kernel==null||kernel==same,"doctrine/draft changed actual shared kernel");kernel=Objects.requireNonNull(same);}
        public synchronized void bindCore(RootApplicationAssembly.Core same){need(core==null||core==same,"doctrine/draft changed actual Core");core=Objects.requireNonNull(same);}
        public synchronized RootReligionPublicProducts.ExtensionInstalled install(RootRuntimeContext context)throws IOException{
            if(core==null||kernel==null||context.core()!=core||context.writer()!=core.writer()||context.archive().writer()!=core.writer())throw new IOException("doctrine/draft requires same bound Core/shared kernel/writer");var prior=attempts.get(context);
            if(prior!=null){if(prior.failure!=null)throw new IOException("previous doctrine/draft partial install retained; never retry",prior.failure);return new RootReligionPublicProducts.ExtensionInstalled(prior.runtime.installation,prior.runtime);}
            if(attempts.size()>=64)throw new IOException("doctrine/draft per-Game installation bound exceeded");var attempt=new Attempt();attempts.put(context,attempt);
            try{attempt.runtime=new Runtime(context,sources,kernel);return new RootReligionPublicProducts.ExtensionInstalled(attempt.runtime.installation,attempt.runtime);}catch(RuntimeException failure){attempt.failure=new IOException("actual doctrine/draft install failed",failure);throw attempt.failure;}
        }
        private synchronized Runtime installed(RootRuntimeContext context)throws IOException{var attempt=attempts.get(context);if(attempt==null||attempt.runtime==null||attempt.failure!=null)throw new IOException("doctrine/draft was not actually installed in this physical Root");return attempt.runtime;}
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context publicContext,PublicBindings registry)throws IOException{
            need(!registry.frozen(),"doctrine/draft public factory crossed frozen registry");
            return new RootPublicHandlerProductsFactory.Contribution(bindings(sources.group(),sources.implementation(),request->{var deadline=publicContext.clock().instant().plus(timeout(request,publicContext.observationTimeout()));try{return publicContext.withCurrent(root->{var context=publicContext.installed(root).context();var runtime=installed(context);return root.withPublicObservation(deadline,(frame,known,same)->runtime.invoke(same,new ReligionService.ActualFrame(frame,context.transport().originalHello(),deadline),request));});}catch(IOException failure){throw new UncheckedIOException(failure);}}),List.of(),List.of());
        }
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> bindings(Group group,ExactRef source,PublicRoutes.Handler<ReligionContract.Request,ReligionContract.Response> actual){return methodsList(group).stream().<McpExecutableDirectory.DirectBinding<?,?>>map(name->new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,ReligionContract.Request.class,ReligionContract.Response.class,actual,call->{need(call.name().equals(name),"doctrine/draft public identity drift");var request=ReligionCodec.decode(name,call.arguments().objectOrEmpty());Selection.from(request);return request;},result->PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.encode(result)),new PublicRoutes.Target(Runtime.class.getName(),"invoke",source))).toList();}
    public static final class Runtime implements ReligionService.Component{
        private final RootRuntimeContext context;private final Sources sources;
        private final EnumMap<Kind,ReadContract<Observed>> fixed=new EnumMap<>(Kind.class);
        private final EnumMap<Kind,RootReadContractCatalog.Family<Selection,Observed>> selected=new EnumMap<>(Kind.class);
        private final RootDomainInstallation installation;
        private Runtime(RootRuntimeContext context,Sources sources,RootReligionPublicProducts.SharedKernel kernel){
            this.context=context;this.sources=sources;
            for(Kind kind:kinds(sources.group())){var source=sources.source(kind);if(kind.selectorFields().isEmpty())fixed.put(kind,ReligionDoctrineDraftReads.contract(Selection.fixed(kind),source,kernel.readAdmission()::verify));
                else selected.put(kind,new RootReadContractCatalog.Family<>("religion-original-"+kind.name().toLowerCase(Locale.ROOT)+"-selected/v1",Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),source.definition(),sources.decoder(),selection->{need(selection.kind()==kind,"doctrine/draft family kind drift");return raw(ReligionDoctrineDraftReads.selectionArguments(selection));},selection->{need(selection.kind()==kind,"doctrine/draft family operation drift");return new OperationKey(kind.step());},selection->{need(selection.kind()==kind,"doctrine/draft family contract drift");return ReligionDoctrineDraftReads.contract(selection,source,kernel.readAdmission()::verify);}));}
            var reads=fixed.values().stream().map(contract->new RootReadContractCatalog.InstalledRead(contract,sources.decoder())).toList();installation=new RootDomainInstallation(id(sources.group()),List.of(),reads,List.copyOf(selected.values()),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation(){return installation;}
        public List<String> methods(){return methodsList(sources.group());}
        public ReligionContract.Response invoke(Session same,ReligionService.ActualFrame actual,ReligionContract.Request request){
            try{
            context.writer().requireSession(same);need(actual.frame().source().equals(context.source())&&actual.frame().sessionId().equals(context.game().sessionId())&&actual.frame().identity().game().equals(context.game().generation())&&actual.frame().identity().frame().revision().equals(request.expectedRevision()),"doctrine/draft invocation crossed actual source/session/revision");var selection=Selection.from(request);need(selection.kind().group()==sources.group(),"doctrine/draft component kind drift");
            if(selection.includeKnowledge())need(!actual.hello().gameSha256().equalsIgnoreCase(Build.CROZIER2.sha256()),"Tenet knowledge catalogue requires exact .3/.4");
            ReadContract<Observed> contract=selection.kind().selectorFields().isEmpty()?fixed.get(selection.kind()):context.readCatalog().issue(selected.get(selection.kind()),selection);
            var result=ReligionService.readKnown(context.reads(),context.archive(),same,contract,actual,ReligionDoctrineDraftReads.selectionArguments(selection));return new ReligionContract.Response(request.method(),raw(result.value().publicResult()));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionCapabilities;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.*;

/** Pre-Core immutable READ registration; every invocation borrows the actual current Game's sole Root writer. */
public final class RootReligionPublicProducts {
    @FunctionalInterface public interface NativeReadMetadata {
        ExactRef source(ReligionCapabilities.ReadKind kind);
    }
    @FunctionalInterface public interface NativeActionMetadata {
        ExactRef source(ReligionCapabilities.MutationSource kind);
    }
    /** Native producer metadata and existing domain ports, without a definitions publication or legacy qualification. */
    public record Config(boolean holyCreationUi,boolean holyCreationOnce) {
        public Config {StrictJson.require(!holyCreationOnce||holyCreationUi,"Holy creation once requires its creation UI");}
    }
    public static Prepared ordinary(Config config,RootAdditionalDomains.ImplementationMetadata metadata) {
        return RootReligionSourcesFactory.ordinary(config,metadata);
    }
    public static final class SharedKernel {
        private final ReligionCapabilities.Registration legacy;
        private final List<ReligionService.FixedRead> reads;
        private final ReligionService.ReadAdmission admission;
        private NativePrivateActionPermission.QualificationVerifier actualQualification;
        private final NativePrivateActionPermission.QualificationVerifier deferred=(config,hello,guard,request)->{
            NativePrivateActionPermission.QualificationVerifier actual;
            synchronized(this){actual=actualQualification;}
            if(actual==null)throw new IOException("actual Root Religion private qualification has not been bound");
            return actual.verify(config,hello,guard,request);
        };
        public SharedKernel(ReligionCapabilities.Registration legacy,List<ReligionService.FixedRead> reads,ReligionService.ReadAdmission admission){this.legacy=Objects.requireNonNull(legacy);this.reads=List.copyOf(reads);this.admission=Objects.requireNonNull(admission);}
        public ReligionCapabilities.Registration legacyRegistration(){return legacy;}
        public List<ReligionService.FixedRead> legacyReads(){return reads;}
        public ReligionService.ReadAdmission readAdmission(){return admission;}
        public NativePrivateActionPermission.QualificationVerifier actionQualification(){return deferred;}
        private synchronized void bindQualification(NativePrivateActionPermission.QualificationVerifier actual){Objects.requireNonNull(actual);StrictJson.require(actualQualification==null||actualQualification==actual,"Religion cannot move to another actual Root qualifier");actualQualification=actual;}
    }
    public interface ExtensionPrepared {
        String id();
        List<String> originalMethods();
        List<DomainBodies.Registration> domainRegistrations();
        List<NativePrivateActionPermission> privatePermissions();
        void bindShared(SharedKernel same);
        void bindCore(RootApplicationAssembly.Core same);
        ExtensionInstalled install(RootRuntimeContext same) throws IOException;
        RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context same,PublicBindings registry) throws IOException;
        default List<RootGuiPublicProducts.NavigationDefinition> navigationDefinitions(){return List.of();}
    }
    public record ExtensionInstalled(RootDomainInstallation installation,Optional<ReligionService.Component> service) {
        public ExtensionInstalled {Objects.requireNonNull(installation);Objects.requireNonNull(service);}
        public ExtensionInstalled(RootDomainInstallation installation,ReligionService.Component service){this(installation,Optional.of(Objects.requireNonNull(service)));}
        public ExtensionInstalled(RootDomainInstallation installation){this(installation,Optional.empty());}
    }
    @FunctionalInterface public interface ExistingReadsFactory {
        ReligionService.ExistingReads resolve(RootRuntimeContext actualContext) throws IOException;
    }
    public record Sources(ExactRef implementation,ExactRef contract,ExactRef codec,ExactRef service,ExactRef legacyCapabilities,
            List<ReligionCapabilities.ReadSource> originalReadSources,List<ReligionCapabilities.ActionSource> originalActionSources,
            ExistingReadsFactory existingReads,List<ExtensionPrepared> extensions) {
        public Sources {
            for(ExactRef source:List.of(implementation,contract,codec,service,legacyCapabilities))StrictJson.require(source.bytes()>0,"actual Religion Java source required");
            originalReadSources=List.copyOf(originalReadSources);originalActionSources=List.copyOf(originalActionSources);Objects.requireNonNull(existingReads);extensions=List.copyOf(extensions);
            StrictJson.require(extensions.size()<=8&&extensions.stream().map(ExtensionPrepared::id).distinct().count()==extensions.size(),"finite distinct Religion extensions required");
            var methods=new java.util.HashSet<String>(ReligionService.actualReadNames());
            for(var extension:extensions)for(String method:extension.originalMethods())StrictJson.require(ReligionCodec.methods().stream().anyMatch(m->m.name().equals(method))&&methods.add(method),"duplicate or non-original Religion extension method: "+method);
        }
        public Sources(ExactRef implementation,ExactRef contract,ExactRef codec,ExactRef service,ExactRef legacyCapabilities,List<ReligionCapabilities.ReadSource> originalReadSources,List<ReligionCapabilities.ActionSource> originalActionSources,ExistingReadsFactory existingReads){this(implementation,contract,codec,service,legacyCapabilities,originalReadSources,originalActionSources,existingReads,List.of());}
    }
    public record Installed(RootDomainInstallation installation,ReligionService service) {
        public Installed {Objects.requireNonNull(installation);Objects.requireNonNull(service);}
    }
    private static final class Attempt {
        private Installed installed;private IOException failure;
    }
    public static final class Prepared {
        private final Sources sources;
        private final SharedKernel shared;
        private final List<ReligionService.FixedRead> fixed;
        private final List<RootReadContractCatalog.InstalledRead> registered;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        private RootApplicationAssembly.Core core;
        private RuntimeException coreFailure;
        public Prepared(Sources sources) {
            this.sources=Objects.requireNonNull(sources);
            var original=new ReligionCapabilities.Registration(sources.originalReadSources(),sources.originalActionSources(),List.of(),
                    (kind,request)->admit(request),(kind,command)->admit(new PlanningReadRequest(command.before(),command.source(),command.sessionId(),command.operation(),command.arguments(),command.deadline())));
            fixed=ReligionService.fixedReads(original);
            shared=new SharedKernel(original,fixed,this::admit);
            var reads=new ArrayList<RootReadContractCatalog.InstalledRead>();
            fixed.forEach(read->reads.add(new RootReadContractCatalog.InstalledRead(read.contract(),sources.service())));
            reads.add(new RootReadContractCatalog.InstalledRead(original.conversionReconciliationContract(),sources.service()));
            reads.add(new RootReadContractCatalog.InstalledRead(original.countyReconciliationContract(),sources.service()));
            registered=List.copyOf(reads);
            for(var extension:sources.extensions())extension.bindShared(shared);
        }
        public Sources sources(){return sources;}
        public SharedKernel sharedKernel(){return shared;}
        public List<DomainBodies.Registration> domainRegistrations(){return sources.extensions().stream().flatMap(e->e.domainRegistrations().stream()).toList();}
        public List<NativePrivateActionPermission> privatePermissions(){return sources.extensions().stream().flatMap(e->e.privatePermissions().stream()).toList();}
        public List<NativePrivateActionPermission> privatePermissions(NativePrivateActionPermission.QualificationVerifier actualRootQualifier){shared.bindQualification(actualRootQualifier);return privatePermissions();}
        public List<RootGuiPublicProducts.NavigationDefinition> navigationDefinitions(){return sources.extensions().stream().flatMap(e->e.navigationDefinitions().stream()).toList();}
        public synchronized void bindCore(RootApplicationAssembly.Core same) {
            Objects.requireNonNull(same);StrictJson.require(core==null||core==same,"Religion Prepared cannot move to a foreign actual Core");
            if(coreFailure!=null)throw new IllegalStateException("Religion partial Core binding cannot be replayed",coreFailure);
            if(core==same)return;core=same;
            try{for(var extension:sources.extensions())extension.bindCore(same);}catch(RuntimeException failure){coreFailure=failure;throw failure;}
        }
        public synchronized Installed install(RootRuntimeContext same) throws IOException {
            Objects.requireNonNull(same);
            if(core==null||coreFailure!=null||same.core()!=core||same.writer()!=core.writer()||same.archive().writer()!=core.writer())throw new IOException("Religion actual context belongs to another or unbound Core/writer");
            Attempt prior=attempts.get(same);
            if(prior!=null) {if(prior.failure!=null)throw new IOException("Religion previous partial installation is retained and cannot be replayed",prior.failure);return Objects.requireNonNull(prior.installed);}
            if(attempts.size()>=64)throw new IOException("finite Religion actual-context installation bound exceeded");
            Attempt attempt=new Attempt();attempts.put(same,attempt);
            try {
                var extensions=new ArrayList<ExtensionInstalled>();for(var extension:sources.extensions())extensions.add(extension.install(same));
                ReligionService service=new ReligionService(same.reads(),same.archive(),fixed,()->{
                    try {return Objects.requireNonNull(sources.existingReads().resolve(same),"actual existing Religion/HolyOrder producers required");}
                    catch(IOException failure){throw new UncheckedIOException(failure);}
                },extensions.stream().flatMap(i->i.service().stream()).toList());
                var installation=new RootDomainInstallation("original-religion-public-adapters-v3",List.of(),registered,List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                        List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
                var pieces=new ArrayList<RootDomainInstallation>();pieces.add(installation);extensions.forEach(i->pieces.add(i.installation()));
                attempt.installed=new Installed(merge(pieces),service);return attempt.installed;
            } catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure) {attempt.failure=new IOException("Religion actual installation failed before completion",failure);throw attempt.failure;}
        }
        private void admit(PlanningReadRequest request) {
            RootRuntimeContext current;
            synchronized(this) {
                var matches=attempts.entrySet().stream().filter(entry->entry.getValue().installed!=null&&entry.getValue().failure==null)
                        .map(java.util.Map.Entry::getKey).filter(context->context.core()==core&&context.game().generation().equals(request.origin().game())
                                &&context.game().sessionId().equals(request.sessionId())&&context.source().equals(request.source())).toList();
                StrictJson.require(matches.size()==1,"Religion READ must resolve exactly one installed actual Game/context");current=matches.getFirst();
            }
            try {
                current.requireCurrent(request.deadline());
                if(request.origin() instanceof CommandOrigin.Reconciliation){StrictJson.require(List.of("query-player-religion-conversion-result-private-v1","county-conversion-task-result-private-v1").contains(request.operation().value()),"only independent Religion results may enter actual reconciliation");return;}
                current.withSession(same->current.collector().current(same,request.before(),request.deadline(),lease->{
                    StrictJson.require(lease.frame().source().equals(request.source())&&lease.frame().sessionId().equals(request.sessionId()),"Religion original current READ source/session drift");return null;
                }));
            }catch(IOException failure){throw new UncheckedIOException("actual Religion READ admission unavailable",failure);}
        }
    }
    private static RootDomainInstallation merge(List<RootDomainInstallation> all) {
        return new RootDomainInstallation("original-religion-public-adapters-v3",
                all.stream().flatMap(i->i.domainRegistrations().stream()).toList(),all.stream().flatMap(i->i.reads().stream()).toList(),all.stream().flatMap(i->i.readFamilies().stream()).toList(),
                all.stream().flatMap(i->i.actions().stream()).toList(),all.stream().flatMap(i->i.composites().stream()).toList(),all.stream().flatMap(i->i.archived().stream()).toList(),
                all.stream().flatMap(i->i.actionFamilies().stream()).toList(),all.stream().flatMap(i->i.compositeFamilies().stream()).toList(),all.stream().flatMap(i->i.frontendAdmissions().stream()).toList(),
                all.stream().flatMap(i->i.pending().stream()).toList(),all.stream().flatMap(i->i.requiredPending().stream()).collect(java.util.stream.Collectors.toSet()),all.stream().flatMap(i->i.policies().stream()).toList(),
                all.stream().flatMap(i->i.completions().stream()).toList(),all.stream().flatMap(i->i.fixedDomains().stream()).toList(),all.stream().flatMap(i->i.familyDomains().stream()).toList(),all.stream().flatMap(i->i.compositeDomains().stream()).toList());
    }
    private final RootPublicHandlerProductsFactory.Context context;
    private RootReligionPublicProducts(RootPublicHandlerProductsFactory.Context context){this.context=Objects.requireNonNull(context);}
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry) throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        ExactRef implementation=context.source(RootReligionPublicProducts.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionContract.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionCodec.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionService.class);
        context.source(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionCapabilities.class);
        var actual=new RootReligionPublicProducts(context);
        var prepared=context.definitions().additionalDomains().religion();
        var direct=new ArrayList<McpExecutableDirectory.DirectBinding<?,?>>(bindings(implementation,actual::invoke));
        var diagnostics=new ArrayList<RootRuntimePublicCatalog.Diagnostic>();
        var gaps=new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
        for(var extension:prepared.sources().extensions()){
            var contribution=extension.products(context,registry);direct.addAll(contribution.direct());diagnostics.addAll(contribution.diagnostics());gaps.addAll(contribution.gaps());
            StrictJson.require(contribution.direct().stream().allMatch(binding->extension.originalMethods().contains(binding.name())),"Religion extension bound another owner's original method");
        }
        var names=new java.util.HashSet<String>();for(var binding:direct)StrictJson.require(names.add(binding.name()),"duplicate actual Religion public binding");
        for(var method:ReligionCodec.methods())if(!names.contains(method.name())&&gaps.stream().noneMatch(gap->gap.identity().equals(method.name())))gaps.add(new RootRuntimePublicCatalog.DefinitionGap(method.name(),
                "original declaration and strict argument contract migrated; this method's actual Java business producer/normalizer/effect installation is still missing"));
        return new RootPublicHandlerProductsFactory.Contribution(direct,diagnostics,gaps);
    }
    /** Same production binding constructor is used by descriptor/serde regressions; no invented Root is needed. */
    static List<McpExecutableDirectory.DirectBinding<?,?>> bindings(ExactRef implementation,PublicRoutes.Handler<ReligionContract.Request,ReligionContract.Response> actual) {
        return ReligionService.actualReadNames().stream().<McpExecutableDirectory.DirectBinding<?,?>>map(name->new McpExecutableDirectory.DirectBinding<>(name,
                PublicMcpBindings.Kind.DRIVER_DIRECT,ReligionContract.Request.class,ReligionContract.Response.class,actual,
                call->{StrictJson.require(call.name().equals(name),"Religion original tool identity differs");return ReligionCodec.decode(name,call.arguments().objectOrEmpty());},
                response->PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.encode(response)),
                new PublicRoutes.Target(RootReligionPublicProducts.class.getName(),"invoke",implementation))).toList();
    }
    public ReligionContract.Response invoke(ReligionContract.Request request) throws InterruptedException {
        var deadline=context.clock().instant().plus(context.observationTimeout());
        try {
            return context.withCurrent(root-> {
                var installed=context.installed(root);var actual=installed.additionalDomains().religion();var runtime=installed.context();
                return root.withPublicObservation(deadline,(frame,known,same)-> {
                    runtime.writer().requireSession(same);
                    var hello=runtime.transport().diagnostics().originalHello().orElseThrow(()->new IOException("actual current Religion HELLO missing")).original();
                    return actual.service().invoke(same,new ReligionService.ActualFrame(frame,hello,deadline),request);
                });
            });
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
}

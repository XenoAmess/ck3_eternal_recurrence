package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.FirstHeirRelationshipPublicCodec.*;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Context;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Contribution;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** The original real Driver-direct tool, using the current physical Root's identical qualified relation contract. */
public final class RootDriverHeirPublicSupplier {
    public static final String NAME="ck3_query_current_first_heir_relationship_private_v1";
    @FunctionalInterface interface Current {Reply query(Request request)throws InterruptedException;}
    private final Current current;
    private RootDriverHeirPublicSupplier(Current current){this.current=Objects.requireNonNull(current);}
    public Reply queryCurrentFirstHeirRelationship(Request request)throws InterruptedException {return current.query(Objects.requireNonNull(request));}
    public static Contribution install(Context context,PublicBindings unusedServiceRegistry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(unusedServiceRegistry);
        ExactRef source=context.source(RootDriverHeirPublicSupplier.class);
        for(Class<?> type:List.of(FirstHeirRelationshipPublicCodec.class,RootFamilyRuntimeFactory.class,RootFamilyNativeReadProducts.class,RootFamilyCampaignRead.class))context.source(type);
        for(Class<?> type:List.of(FamilyCurrentRelationQueries.class,FamilyCurrentRelationPublic.class,FamilyRelationCapture.class,FamilyRelationMaterialExports.class))context.source(Module.NATIVE_TRANSPORT,type);
        return new Contribution(List.of(binding(source,new Actual(context))),List.of(),List.of());
    }
    static McpExecutableDirectory.DirectBinding<Request,Reply> binding(ExactRef source,Current current){
        Objects.requireNonNull(source);Objects.requireNonNull(current);
        var actual=new RootDriverHeirPublicSupplier(current);
        return new McpExecutableDirectory.DirectBinding<>(NAME,PublicMcpBindings.Kind.DRIVER_DIRECT,Request.class,Reply.class,actual::queryCurrentFirstHeirRelationship,
                call->FirstHeirRelationshipPublicCodec.decode(call.arguments()),reply->PublicMcpDirectory.CallResult.fromBusinessJson(FirstHeirRelationshipPublicCodec.encode(reply)),
                new PublicRoutes.Target(RootDriverHeirPublicSupplier.class.getName(),"queryCurrentFirstHeirRelationship",source));
    }
    /** Direct-only integration marker; all Native contracts remain the one existing Family installation. */
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final RootDriverRegistryPublicProducts.ProductSource source;
        private RootApplicationAssembly.Core core;
        private final java.util.IdentityHashMap<RootRuntimeContext,Installed> installed=new java.util.IdentityHashMap<>();
        public Prepared(ExactRef actualSupplierSource){source=new RootDriverRegistryPublicProducts.ProductSource(RootDriverHeirPublicSupplier.class,
                "local-service/src/main/java/org/xar/ck3/control/service/root/RootDriverHeirPublicSupplier.java",Objects.requireNonNull(actualSupplierSource));}
        @Override public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.HEIR;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source(){return source;}
        @Override public List<org.xar.ck3.control.continuity.writer.DomainBodies.Registration> domainRegistrations(){return List.of();}
        @Override public java.util.Collection<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            Objects.requireNonNull(actual);if(core!=null&&core!=actual)throw new IOException("first-heir direct product changed its actual Core");core=actual;
        }
        @Override public synchronized Installed install(RootRuntimeContext actual)throws IOException {
            Objects.requireNonNull(actual);if(core==null||actual.core()!=core)throw new IOException("first-heir direct product lacks its identical bound Core");
            var old=installed.get(actual);if(old!=null)return old;if(installed.size()>=64)throw new IOException("first-heir physical product bound exhausted");
            var result=new Installed(actual,this);installed.put(actual,result);return result;
        }
        @Override public Contribution products(Context context,PublicBindings registry)throws IOException {
            source.requireCurrent(context);
            if(context.definitions().additionalDomains().driverRegistry().prepared(kind(),Prepared.class)!=this)
                throw new IOException("first-heir handler is not its actual prepared Driver product");
            return RootDriverHeirPublicSupplier.install(context,registry);
        }
    }
    public static final class Installed implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;private final Prepared owner;private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext context,Prepared owner){this.context=context;this.owner=owner;
            installation=new RootDomainInstallation("driver-heir-public",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),
                    List.of(),List.of(),List.of(),java.util.Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());}
        @Override public RootDomainInstallation installation(){return installation;}
        @Override public void requireContext(RootRuntimeContext actual)throws IOException {if(context!=actual)throw new IOException("first-heir direct product crossed physical contexts");}
        private void requirePrepared(Prepared actual)throws IOException {if(owner!=actual)throw new IOException("first-heir direct product changed its original prepared source");}
    }
    private static final class Actual implements Current {
        private final Context context;private Actual(Context context){this.context=Objects.requireNonNull(context);}
        @Override public Reply query(Request request)throws InterruptedException {
            Instant deadline=context.clock().instant().plus(request.capture().map(Capture::timeout).orElse(java.time.Duration.ofSeconds(360)));
            try{return context.withCurrent(root->root.withPublicObservation(deadline,(frame,known,same)->{
                request.requireCurrent(frame.identity().frame().identity().nativeRevision());
                var installed=context.installed(root);var runtime=installed.context();
                var product=installed.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.HEIR,Installed.class);
                product.requireContext(runtime);product.requirePrepared(context.definitions().additionalDomains().driverRegistry().prepared(RootDriverRegistryPublicProducts.Kind.HEIR,Prepared.class));
                var family=installed.remainingDomains().family().nativeReads();
                runtime.writer().requireSession(same);family.requireOwner(root);family.requireContext(runtime);
                var actual=installed.interactions();family.requireInteractions(actual.capabilities(),actual.definitions());
                FamilyRelationCapture.Query query=()->{
                    request.capture().ifPresent(capture->StrictJson.require(frame.identity().game().pid()==capture.request().ownedGamePid(),"capture PID differs from actual Root-owned Game"));
                    var queries=family.currentRelation();var contract=queries.contract();
                    StrictJson.require(runtime.readCatalog().containsIdentity(contract)&&contract.permissionMode()==ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                            &&contract.permissionKey().equals(FamilyCurrentRelationQueries.PERMISSION)&&contract.sourceRef().bytes()>0,
                            "actual private first-heir source-qualified contract is not identically installed");
                    var controls=family.contextProjection().project(frame,deadline);
                    var flat=new OpportunityJson.Obj(Map.of("expected_native_revision",new OpportunityJson.IntegerValue(request.expectedNativeRevision())));
                    var subjectRequest=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),flat,deadline);
                    var campaign=family.campaignRoot().current(same,subjectRequest);
                    if(!(campaign instanceof PlanningReadResult.Known<OpportunityJson.Obj> rootRead))throw new IOException("actual shared public primary-heir ROOT unavailable");
                    var basis=family.campaignRoot().bind(rootRead,controls);var arguments=queries.canonical(controls,FamilyRootBinding.arguments(basis,flat));
                    var readRequest=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),arguments,deadline);
                    var value=runtime.reads().read(same,contract,readRequest);
                    if(value instanceof PlanningReadResult.Unavailable<OpportunityJson.Obj> unavailable)
                        throw new FamilyRelationCapture.QueryUnavailable("actual current first-heir relationship query unavailable: "+unavailable.reason(),unavailable.original());
                    if(!(value instanceof PlanningReadResult.Known<OpportunityJson.Obj> observed))throw new IOException("unhandled actual current relationship result");
                    var archive=runtime.archive().withSession(same);NativeRecordedEvidenceVerifier.requireRead(observed.receipt(),archive);
                    StrictJson.require(archive.readReferenceOf(observed.receipt()).equals(observed.originalReceipt()),"public current relationship lost its exact original read reference");
                    var observation=family.campaignRoot().replayAt(observed.receipt(),()->queries.decodeReceipt(observed.receipt()));
                    return new FamilyRelationCapture.Original(queries,observed,observation,archive);
                };
                if(request.capture().isPresent())return new Captured(FamilyRelationCapture.capture(request.capture().orElseThrow().request(),context.clock(),
                        runtime.core().storageGuard(),context.inputs().application().ledger().lock(),query));
                var original=query.read();var observation=original.observation();
                StrictJson.require(observation.original().equals(original.read().value()),"public current-heir body differs from sole native producer");return new Relation(observation);
            }));}catch(IOException unavailable){throw new UncheckedIOException("actual private current first-heir query/capture unavailable",unavailable);}
        }
    }
}

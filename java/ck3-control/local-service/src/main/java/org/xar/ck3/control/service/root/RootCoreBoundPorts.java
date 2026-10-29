package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Duration;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityActionRoutes;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;

/** Pre-Core definitions resolve the same once-bound original writer and actual managed creator.
 * This port never creates an authority, a fallback Session or a private action qualification. */
public final class RootCoreBoundPorts implements ContinuityStorePort {
    private final RootApplicationConfiguration expected;
    private RootApplicationAssembly.Core core;
    private RootRuntimeCatalogFactory catalogs;
    private RootManagedLifecycleFactory managed;
    private record ActivityProducts(ActivityNativeContracts.Installation reads,FeastDomainRuntime policy,
            RootRuntimeDefinitionModel.Build build) { }
    private ActivityProducts activity;
    private record PhysicalBinding(Duration freshness,RootLifecycleAuthority authority) { }
    private final Map<RootRuntimeContext,PhysicalBinding> physicals=new IdentityHashMap<>();

    public RootCoreBoundPorts(RootApplicationConfiguration expected) {this.expected=Objects.requireNonNull(expected);}
    public synchronized void bindCatalogs(RootRuntimeCatalogFactory actual) {
        StrictJson.require(catalogs==null,"one actual runtime catalog factory must be bound once");catalogs=Objects.requireNonNull(actual);
    }
    public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
        Objects.requireNonNull(actual);
        if(core!=null)throw new IOException("original runtime Core binding cannot be replaced or replayed");
        if(!actual.configuration().equals(expected)||actual.archive().writer()!=actual.writer()
                ||!actual.writer().originalLockPath().equals(expected.ledger().lock()))
            throw new IOException("runtime prepared sources crossed their original Core/writer/archive/configuration");
        core=actual;
    }
    public synchronized RootApplicationAssembly.Core requireCore()throws IOException {
        if(core==null)throw new IOException("actual original runtime Core is not bound");return core;
    }
    /** Source definitions retain their real policy producer before Core exists; invoking either callback requires Core. */
    public synchronized void bindActivityProducts(ActivityNativeContracts.Installation actualReads,
            FeastDomainRuntime actualPolicy,RootRuntimeDefinitionModel.Build actualBuild)throws IOException {
        if(activity!=null)throw new IOException("actual Activity source/read/policy products bind exactly once");
        activity=new ActivityProducts(Objects.requireNonNull(actualReads),Objects.requireNonNull(actualPolicy),Objects.requireNonNull(actualBuild));
    }
    private synchronized ActivityProducts requireActivity()throws IOException {
        if(activity==null)throw new IOException("actual Activity producers are not bound");return activity;
    }
    /** Called inside the coordinator's existing held read scope; it performs no second Native observation. */
    public void verifyActivityRead(ActivityNativeContracts.Query query,PlanningReadRequest request) {
        try {
            Objects.requireNonNull(query);Objects.requireNonNull(request);var same=borrowedSession();var actual=requireActivity();
            RootRuntimeContext context=requireCurrent(same,new SessionIdentity(request.before().machineId(),request.before().game(),request.sessionId()));
            context.requireCurrent(request.deadline());RootRuntimeCatalogFactory selected;
            synchronized(this){selected=catalogs;}
            if(selected==null||selected.sources().activityDefinitions()!=actual.reads()
                    ||!query.operation().equals(request.operation())||!request.source().equals(context.source())
                    ||!context.readCatalog().containsIdentity(actual.reads().contract(query)))
                throw new IOException("Activity read did not use its identical installed current producer/operation/source");
            var privateRead=requireCore().withEpisodeDomainRead(same,context,request,actual.reads().contract(query),lease->{
                verifyActivityProducer(same,context,actual,query,lease.originalHello());return Boolean.TRUE;
            });
            if(privateRead.isEmpty())context.collector().currentHeldRead(same,request,lease->{
                verifyActivityProducer(same,context,actual,query,lease.originalHello());return Boolean.TRUE;
            });
        }catch(IOException unavailable){throw new UncheckedIOException("actual held Activity read admission unavailable",unavailable);}
    }
    private void verifyActivityProducer(ContinuityStorePort.Session same,RootRuntimeContext context,ActivityProducts actual,
            ActivityNativeContracts.Query query,ExactRef originalHello)throws IOException {
        var metadata=context.sources().optionalCurrentMetadata(same);
        if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
        var decoded=NativeWire.decode(requireCore().archive().readArtifact(same,originalHello,1<<20));
        if(!(decoded instanceof NativeWire.Hello hello)||!hello.buildMatch()||hello.pid()!=context.game().generation().pid()
                ||!hello.gameSha256().equalsIgnoreCase(actual.build().executableSha256())
                ||metadata.filter(value->!value.gameExecutable().sha256().equalsIgnoreCase(actual.build().executableSha256())).isPresent())
            throw new IOException("Activity read differs from its actual archived HELLO and source-qualified configured build");
        if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
    }
    /** The cached reader borrows the actual held read; registration never supplies a permissive admission. */
    public void verifyCachedRead(PlanningReadRequest request) throws IOException {
        Objects.requireNonNull(request); var same=borrowedSession();
        RootRuntimeContext context=requireCurrent(same,new SessionIdentity(request.before().machineId(),request.before().game(),request.sessionId()));
        context.requireCurrent(request.deadline()); RootRuntimeCatalogFactory selected;
        synchronized(this) { selected=catalogs; }
        if(selected==null)throw new IOException("actual cached-succession catalog is not bound");
        var definitions=selected.sources().additionalDomains().driverRegistry().cachedDefinitions();
        var contract=definitions.cached();
        if(!request.source().equals(context.source())||!request.operation().equals(contract.operation())
                ||!context.readCatalog().containsIdentity(contract)
                ||!contract.permissionKey().equals(org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004.PERMISSION)
                ||contract.permissionMode()!=org.xar.ck3.control.application.action.ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                ||contract.wireProfile()!=org.xar.ck3.control.application.action.ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY)
            throw new IOException("cached-succession read lost its identical installed private source/operation/contract");
        var privateRead=requireCore().withEpisodeDomainRead(same,context,request,contract,lease->{
            verifyCachedProducer(same,context,contract.sourceRef(),lease.originalHello()); return Boolean.TRUE;
        });
        if(privateRead.isEmpty())context.collector().currentHeldRead(same,request,lease->{
            verifyCachedProducer(same,context,contract.sourceRef(),lease.originalHello()); return Boolean.TRUE;
        });
    }
    private void verifyCachedProducer(ContinuityStorePort.Session same,RootRuntimeContext context,
            ExactRef producer,ExactRef originalHello) throws IOException {
        var metadata=context.sources().optionalCurrentMetadata(same);
        if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
        var decoded=NativeWire.decode(requireCore().archive().readArtifact(same,originalHello,1<<20));
        String expectedSha=org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004.EXE_SHA256;
        if(!(decoded instanceof NativeWire.Hello hello)||!hello.buildMatch()||hello.pid()!=context.game().generation().pid()
                ||!hello.gameSha256().equalsIgnoreCase(expectedSha)
                ||metadata.filter(value->!value.gameExecutable().sha256().equalsIgnoreCase(expectedSha)).isPresent())
            throw new IOException("cached-succession read differs from its actual archived HELLO/exact .4 executable");
        if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
    }
    /** The same retained Feast domain replays the original selected policy under the original writer before INTENT. */
    public void verifyActivityAction(ActivityActionRoutes.Kind kind,ActionCommand command) {
        try {var same=borrowedSession();requireSession(same);requireActivity().policy().verifyActivityAction(kind,command);}
        catch(IOException unavailable){throw new UncheckedIOException("actual Activity policy admission unavailable",unavailable);}
    }
    /** Binds the actual production object after catalog/Core binding, before its CREATE call. */
    public synchronized void bindManagedLifecycleFactory(RootManagedLifecycleFactory actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireOwner(requireCore());
        if(managed!=null)throw new IOException("actual managed lifecycle factory binds exactly once");managed=actual;
    }
    /** Uses the actual current Root and writer; returned caller metadata grants no source qualification. */
    public ExactRef qualifyPrivate(NativePipeEndpoint.Config config,NativeWire.Hello hello,
            GuardEvidence guard,NativeRequest request)throws IOException {
        var originalCore=requireCore();
        RootManagedLifecycleFactory actual;
        RootRuntimeCatalogFactory selected;
        synchronized(this){actual=managed;selected=catalogs;}
        if(selected==null)throw new IOException("actual runtime catalog factory is not bound");
        selected.requireBoundCore(originalCore);
        var same=originalCore.writer().borrowedSession();originalCore.writer().requireSession(same);
        if(actual!=null && selected.sources().historicalPackage().isPresent()) {
            actual.requireOwner(originalCore);return actual.qualifyPrivate(config,hello,guard,request);
        }
        var context=requireCurrent(same,new SessionIdentity(config.machineId(),config.game(),config.sessionId()));
        context.requireCurrent(guard.validUntil());
        if(!context.source().equals(guard.source()))throw new IOException("ordinary private action crossed the actual admitted Root context/source");
        if(!guard.origin().game().equals(config.game())||!guard.origin().machineId().equals(config.machineId()))
            throw new IOException("ordinary private action origin differs from actual config");
        if(!guard.sessionId().equals(config.sessionId())||!guard.connectionGeneration().equals(hello.connectionGeneration()))
            throw new IOException("ordinary private action session/connection differs from actual native HELLO");
        if(!guard.authorityId().equals(originalCore.authorityId()))
            throw new IOException("ordinary private action authority differs from actual Core");
        RootManagedLifecycleFactory.requireFrame(config,hello,guard,request,context.clock().instant());
        var transport=context.game().nativeTransport();
        if(transport.originalHello()!=hello)throw new IOException("ordinary private action did not retain the actual transport hello object");
        if(!context.game().launchPlan().pipeName().equals(config.pipeName()))
            throw new IOException("ordinary private action pipe differs from actual Game launch plan");
        var installed=context.bindings().resolve(guard.operation(),guard.origin()).orElseThrow(() -> new IOException("ordinary private action operation is not installed"));
        if(installed.kind()!=ExecutableStepBindings.Kind.ACTION||installed.requiredCapability().isPresent())
            throw new IOException("ordinary private action differs from its fixed installed ACTION operation");
        originalCore.writer().requireSession(same);context.requireCurrent(guard.validUntil());
        return context.source().sourceRef();
    }
    public ContinuityWriter requireWriter()throws IOException{return requireCore().writer();}
    public void requireSession(ContinuityStorePort.Session same)throws IOException {requireWriter().requireSession(Objects.requireNonNull(same));}
    public ContinuityStorePort.Session borrowedSession()throws IOException{return requireWriter().borrowedSession();}
    public Optional<ContinuityStorePort.Session> activeSession()throws IOException{return requireWriter().activeSession();}
    public RootRuntimeContext requireCurrent(SessionIdentity owner)throws IOException {
        RootRuntimeCatalogFactory actual;
        synchronized(this){if(catalogs==null)throw new IOException("actual runtime catalog factory is not bound");actual=catalogs;}
        RootRuntimeContext result=actual.requireCurrent(Objects.requireNonNull(owner));
        if(result.core()!=requireCore()||result.writer()!=requireWriter())throw new IOException("runtime context escaped the original Core/writer");
        return result;
    }
    public RootRuntimeContext requireCurrent(ContinuityStorePort.Session same,SessionIdentity owner)throws IOException {
        requireSession(same);return requireCurrent(owner);
    }
    public synchronized RootLifecycleAuthority physical(RootRuntimeContext context,Duration freshness)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(freshness);
        if(context.core()!=requireCore()||context.writer()!=requireWriter()||context.archive()!=requireCore().archive())
            throw new IOException("physical runtime context crossed the sole original Core/writer/archive");
        context.game().verify();PhysicalBinding existing=physicals.get(context);
        if(existing!=null){
            if(!existing.freshness().equals(freshness))throw new IOException("one physical snapshot owner cannot change its freshness policy");
            return existing.authority();
        }
        for(RootRuntimeContext prior:physicals.keySet())if(prior.game()==context.game())
            throw new IOException("same physical Game acquired another snapshot runtime context");
        if(physicals.size()>=64)throw new IOException("bounded retained physical snapshot owners require original reconciliation");
        RootRuntimeCatalogFactory factory;
        synchronized(this){if(catalogs==null)throw new IOException("actual runtime catalog factory is not bound");factory=catalogs;}
        var installed=factory.requireCurrentCatalog(new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId()));
        if(installed.context()!=context)throw new IOException("physical original does not belong to the identical installed catalog");
        var lifecycle=installed.remainingDomains().lifecycle();lifecycle.requireContext(context);
        RootLifecycleAuthority authority=lifecycle.physical();
        physicals.put(context,new PhysicalBinding(freshness,authority));return authority;
    }
    @Override public WriterContracts.Prepared preview(WriterContracts.Request request)throws IOException{return requireWriter().preview(Objects.requireNonNull(request));}
    @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared)throws IOException{return requireWriter().commit(Objects.requireNonNull(prepared));}
    @Override public ExactRef persistedHead()throws IOException{return requireWriter().persistedHead();}
    @Override public <T>T locked(ContinuityStorePort.SessionWork<T> work)throws IOException{return requireWriter().locked(Objects.requireNonNull(work));}
}

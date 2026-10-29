package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.PhysicalStatusIdentity;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.reconciliation.LateOutcome;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpHost;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory;

/**
 * Delivers original admitted Root objects while the one Main still owns their physical lifetime.
 * A request selects exact startup data; it cannot create Core, Prepared, a current session or a read receipt.
 */
public final class RootStartupInputsProducer {
    public static final String SCHEMA="xar.java-root-startup-inputs-request/v1";
    public static final int MAXIMUM_BYTES=4096;
    public static final String REQUEST_ENV="XAR_ROOT_STARTUP_INPUTS_REQUEST";
    private RootStartupInputsProducer() { }
    @FunctionalInterface interface Cleanup { void run()throws Exception; }
    /** Original Main cleanup is entered once, including when the actual close acceptance invokes it. */
    static final class Lifetime {
        private final Cleanup cleanup;
        private enum Phase { OPEN, CLOSING, CLOSED }
        private Phase phase=Phase.OPEN;
        private Exception failure;
        Lifetime(Cleanup cleanup){this.cleanup=Objects.requireNonNull(cleanup);}
        synchronized void requireOpen()throws IOException {
            if(phase!=Phase.OPEN)throw new IOException("original Root startup lifetime is "+phase+"; no new retained inputs");
        }
        void close()throws Exception {
            synchronized(this){
                if(phase!=Phase.OPEN){
                    if(phase==Phase.CLOSING)throw new IOException("original Root cleanup is already accepted and pending; no retry");
                    if(failure!=null)throw failure;
                    return;
                }
                phase=Phase.CLOSING;
            }
            try{cleanup.run();}
            catch(Exception actual){synchronized(this){failure=actual;}throw actual;}
            finally{synchronized(this){phase=Phase.CLOSED;}}
        }
        void finish(Exception primary)throws Exception {
            try{close();}
            catch(Exception actual){if(primary==null)throw actual;if(primary!=actual)primary.addSuppressed(actual);}
        }
    }

    public record Request(FileRef startup,Duration closeWait) {
        public Request {
            Objects.requireNonNull(startup);Objects.requireNonNull(closeWait);
            StrictJson.require(Path.of(startup.path()).isAbsolute()&&startup.bytes()>0
                    &&startup.bytes()<=RootStartupConfiguration.MAXIMUM_BYTES
                    &&startup.sha256().matches("[0-9a-f]{64}"),"exact absolute startup original required");
            StrictJson.require(closeWait.getNano()%1_000_000==0
                    &&closeWait.compareTo(Duration.ofMillis(100))>=0
                    &&closeWait.compareTo(Duration.ofSeconds(30))<=0,"finite 100ms..30s actual close wait required");
        }
    }
    @FunctionalInterface public interface Work {
        void consume(Actual actual) throws Exception;
    }
    @FunctionalInterface public interface MenuWork {
        void consume(MenuActual actual) throws Exception;
    }
    /** Synchronous capture validation of the original menu, attempted entry and genuine physical Driver. */
    public interface PhysicalWork {
        void menu(MenuActual actual)throws Exception;
        void entry(MenuActual actual,GameplayEntryService.Result result)throws Exception;
        void driver(PhysicalActual actual)throws Exception;
    }

    private static ReadContract<LateOutcome.Status> physicalStatusProfile(RootInstalledCatalog installed)throws IOException {
        var context=installed.context();
        var profiles=context.readCatalog().installed().stream().map(row->row.contract())
                .filter(row->row.contractId().equals(PhysicalStatusIdentity.CONTRACT_ID)).toList();
        var actual=installed.remainingDomains().life().infrastructure().physicalStatuses();
        if(profiles.size()!=1||profiles.getFirst()!=actual)
            throw new IOException("one identical actual installed physical Status profile required");
        PhysicalStatusIdentity.requireProfile(actual);context.physicalStatusReads().requireContext(context);return actual;
    }
    private static void requirePublicOwnership(OrdinarySessionHost ordinaryHost,PublicMcpHost publicHost,
            PublicMcpDirectory directory)throws IOException {
        if(ordinaryHost.current().isPresent()||publicHost.current().orElse(null)!=directory
                ||directory.scope()!=PublicMcpDirectory.Scope.COMPLETE_MIGRATION)
            throw new IOException("capture inputs lost the original empty ordinary host or installed complete public directory");
    }
    private static void requirePublicInstallation(RootRuntimeContext context,ReadContract<LateOutcome.Status> status,
            Clock clock,Instant deadline,RootPublicHandlerProductsFactory.Context publicContext,
            OrdinarySessionHost ordinaryHost,PublicMcpHost publicHost,PublicMcpDirectory directory)throws IOException {
        requirePublicOwnership(ordinaryHost,publicHost,directory);
        if(publicContext.clock()!=clock)throw new IOException("capture public Context uses another original clock");
        publicContext.withInstalledData(deadline,(installed,same)->{
            if(installed.context()!=context||installed.remainingDomains().life().infrastructure().physicalStatuses()!=status)
                throw new IOException("capture public Context lost its identical installed runtime/profile");
            return null;
        });
    }

    /** Only the original Main retains this synchronous pre-Driver scope. It issues no ordinary Ready or Driver. */
    public static final class MenuActual {
        private final RootRuntimeContext context;
        private final RootMenuSession menu;
        private final ReadContract<LateOutcome.Status> status;
        private final Clock clock;
        private final Instant deadline;
        private final JavaRuntimePackage.CapturedReviewAvailable capturedReview;
        private final RootPublicHandlerProductsFactory.Context publicContext;
        private final OrdinarySessionHost ordinaryHost;
        private final PublicMcpHost publicHost;
        private final PublicMcpDirectory directory;
        private final org.xar.ck3.control.continuity.writer.WriterContracts.Head originalHead;
        private final Thread owner=Thread.currentThread();
        private boolean open=true;
        private MenuActual(RootApplicationAssembly.Core core,RootInstalledCatalog installed,RootMenuSession menu,
                Clock clock,Instant deadline,JavaRuntimePackage.CapturedReviewAvailable capturedReview,
                RootPublicHandlerProductsFactory.Context publicContext,OrdinarySessionHost ordinaryHost,
                PublicMcpHost publicHost,PublicMcpDirectory directory)throws IOException {
            context=Objects.requireNonNull(installed).context();this.menu=Objects.requireNonNull(menu);
            this.clock=Objects.requireNonNull(clock);this.deadline=Objects.requireNonNull(deadline);
            this.capturedReview=Objects.requireNonNull(capturedReview);this.publicContext=Objects.requireNonNull(publicContext);
            this.ordinaryHost=Objects.requireNonNull(ordinaryHost);this.publicHost=Objects.requireNonNull(publicHost);
            this.directory=Objects.requireNonNull(directory);
            if(context.core()!=Objects.requireNonNull(core)||context.writer()!=core.writer()
                    ||context.archive()!=core.archive()||context.clock()!=clock
                    ||!capturedReview.request().equals(installed.definitions().packageRequest()))
                throw new IOException("menu inputs lost the identical installed Core/writer/archive/clock");
            status=physicalStatusProfile(installed);
            requirePublicInstallation(context,status,clock,deadline,publicContext,ordinaryHost,publicHost,directory);
            requireScope();originalHead=context.withSession(same->same.head());
        }
        public RootRuntimeContext context()throws IOException {requireScope();return context;}
        public ReadContract<LateOutcome.Status> status()throws IOException {requireScope();return status;}
        public Clock clock()throws IOException {requireScope();return clock;}
        public Instant deadline()throws IOException {requireScope();return deadline;}
        public JavaRuntimePackage.CapturedReviewAvailable capturedReview()throws IOException {requireScope();return capturedReview;}
        public RootPublicHandlerProductsFactory.Context publicContext()throws IOException {requireScope();return publicContext;}
        public PublicMcpHost publicHost()throws IOException {requireScope();return publicHost;}
        public PublicMcpDirectory directory()throws IOException {requireScope();return directory;}
        public void requireScope()throws IOException {
            if(!open||Thread.currentThread()!=owner||!clock.instant().isBefore(deadline)
                    ||menu.publicPhase()!=RootMenuSession.PublicPhase.FRONTEND
                    ||context.optionalDriverProducer().isPresent()||!context.readCatalog().containsIdentity(status))
                throw new IOException("original synchronous pre-Driver menu scope is unavailable");
            context.requireCurrent(deadline);requirePublicOwnership(ordinaryHost,publicHost,directory);
        }
        void finishScope()throws IOException {
            if(!open)return;
            try {
                requireScope();
                context.withSession(same->{
                    var actual=same.head();
                    if(!originalHead.digest().equals(actual.digest())||!originalHead.documents().equals(actual.documents())
                            ||!originalHead.absent().equals(actual.absent())||!originalHead.indexRepairs().equals(actual.indexRepairs())
                            ||originalHead.snapshotNeedsRecovery()!=actual.snapshotNeedsRecovery())
                        throw new IOException("capture Status callback changed its original writer Head");
                    return null;
                });
            } finally {open=false;}
        }
    }
    static MenuActual retainMenu(RootApplicationAssembly.Core core,RootInstalledCatalog installed,RootMenuSession menu,
            Clock clock,Instant deadline,JavaRuntimePackage.CapturedReviewAvailable capturedReview,
            RootPublicHandlerProductsFactory.Context publicContext,OrdinarySessionHost ordinaryHost,
            PublicMcpHost publicHost,PublicMcpDirectory directory)throws IOException {
        return new MenuActual(core,installed,menu,clock,deadline,capturedReview,publicContext,ordinaryHost,publicHost,directory);
    }

    /** Same admitted physical Driver before ordinary staging; this scope grants no Root, Ready, SAVE or AUTO. */
    public static final class PhysicalActual {
        private final RootRuntimeContext context;
        private final RootMenuSession menu;
        private final ReadContract<LateOutcome.Status> status;
        private final Clock clock;
        private final Instant deadline;
        private final JavaRuntimePackage.CapturedReviewAvailable capturedReview;
        private final GameplayEntryService.Admitted admitted;
        private final RootPublicHandlerProductsFactory.Context publicContext;
        private final OrdinarySessionHost ordinaryHost;
        private final PublicMcpHost publicHost;
        private final PublicMcpDirectory directory;
        private final org.xar.ck3.control.continuity.writer.WriterContracts.Head originalHead;
        private final Thread owner=Thread.currentThread();
        private boolean open=true;
        private PhysicalActual(RootApplicationAssembly.Core core,RootInstalledCatalog installed,RootMenuSession menu,
                Clock clock,Instant deadline,JavaRuntimePackage.CapturedReviewAvailable capturedReview,
                GameplayEntryService.Admitted admitted,RootPublicHandlerProductsFactory.Context publicContext,
                OrdinarySessionHost ordinaryHost,PublicMcpHost publicHost,PublicMcpDirectory directory)throws IOException {
            context=Objects.requireNonNull(installed).context();this.menu=Objects.requireNonNull(menu);
            this.clock=Objects.requireNonNull(clock);this.deadline=Objects.requireNonNull(deadline);
            this.capturedReview=Objects.requireNonNull(capturedReview);this.admitted=Objects.requireNonNull(admitted);
            this.publicContext=Objects.requireNonNull(publicContext);this.ordinaryHost=Objects.requireNonNull(ordinaryHost);
            this.publicHost=Objects.requireNonNull(publicHost);this.directory=Objects.requireNonNull(directory);
            if(context.core()!=Objects.requireNonNull(core)||context.writer()!=core.writer()
                    ||context.archive()!=core.archive()||context.clock()!=clock
                    ||!capturedReview.request().equals(installed.definitions().packageRequest()))
                throw new IOException("physical inputs lost the identical installed Core/writer/archive/clock");
            status=physicalStatusProfile(installed);
            requirePublicInstallation(context,status,clock,deadline,publicContext,ordinaryHost,publicHost,directory);
            requireScope();originalHead=context.withSession(same->same.head());
        }
        public RootRuntimeContext context()throws IOException {requireScope();return context;}
        public ReadContract<LateOutcome.Status> status()throws IOException {requireScope();return status;}
        public Clock clock()throws IOException {requireScope();return clock;}
        public Instant deadline()throws IOException {requireScope();return deadline;}
        public JavaRuntimePackage.CapturedReviewAvailable capturedReview()throws IOException {requireScope();return capturedReview;}
        public GameplayEntryService.Admitted admitted()throws IOException {requireScope();return admitted;}
        public RootPublicHandlerProductsFactory.Context publicContext()throws IOException {requireScope();return publicContext;}
        public PublicMcpHost publicHost()throws IOException {requireScope();return publicHost;}
        public PublicMcpDirectory directory()throws IOException {requireScope();return directory;}
        public void requireScope()throws IOException {
            if(!open||Thread.currentThread()!=owner||!clock.instant().isBefore(deadline)
                    ||menu.publicPhase()!=RootMenuSession.PublicPhase.FRONTEND
                    ||!context.readCatalog().containsIdentity(status)||context.adopted()!=admitted.driver()
                    ||!admitted.driver().source().equals(context.source())
                    ||!admitted.driver().session().game().equals(context.game().generation())
                    ||!admitted.driver().session().sessionId().equals(context.game().sessionId()))
                throw new IOException("original synchronous physical Driver capture scope is unavailable");
            context.requireCurrent(deadline);requirePublicOwnership(ordinaryHost,publicHost,directory);
        }
        void finishScope()throws IOException {
            if(!open)return;
            try {
                requireScope();
                context.withSession(same->{
                    var actual=same.head();
                    if(!originalHead.digest().equals(actual.digest())||!originalHead.documents().equals(actual.documents())
                            ||!originalHead.absent().equals(actual.absent())||!originalHead.indexRepairs().equals(actual.indexRepairs())
                            ||originalHead.snapshotNeedsRecovery()!=actual.snapshotNeedsRecovery())
                        throw new IOException("capture Status callback changed its original writer Head");
                    return null;
                });
            } finally {open=false;}
        }
    }
    static PhysicalActual retainPhysical(RootApplicationAssembly.Core core,RootInstalledCatalog installed,RootMenuSession menu,
            Clock clock,Instant deadline,JavaRuntimePackage.CapturedReviewAvailable capturedReview,
            GameplayEntryService.Admitted admitted,RootPublicHandlerProductsFactory.Context publicContext,
            OrdinarySessionHost ordinaryHost,PublicMcpHost publicHost,PublicMcpDirectory directory)throws IOException {
        return new PhysicalActual(core,installed,menu,clock,deadline,capturedReview,admitted,publicContext,ordinaryHost,publicHost,directory);
    }

    /** Only Main calls this constructor, after physical entry, full admission and both actual host installations. */
    public static final class Actual {
        private final RootApplicationAssembly.Core core;
        private final RootApplicationSession original;
        private final RootStartupNextResources.Prepared prepared;
        private final RootRuntimeDefinitions definitions;
        private final RootInstalledCatalog initialCatalog;
        private final OrdinarySessionHost host;
        private final McpExecutableDirectory.Complete directory;
        private final RootStartupConfiguration startup;
        private final NativeLaunchPlan plan;
        private final Clock clock;
        private final Lifetime lifetime;
        private Actual(RootApplicationAssembly.Core core,RootApplicationSession original,
                RootStartupNextResources.Prepared prepared,RootRuntimeDefinitions definitions,RootInstalledCatalog initialCatalog,
                OrdinarySessionHost host,McpExecutableDirectory.Complete directory,
                RootStartupConfiguration startup,NativeLaunchPlan plan,Clock clock,Lifetime lifetime)throws IOException {
            this.core=Objects.requireNonNull(core);this.original=Objects.requireNonNull(original);
            this.prepared=Objects.requireNonNull(prepared);this.definitions=Objects.requireNonNull(definitions);
            this.initialCatalog=Objects.requireNonNull(initialCatalog);this.host=Objects.requireNonNull(host);
            this.directory=Objects.requireNonNull(directory);this.startup=Objects.requireNonNull(startup);
            this.plan=Objects.requireNonNull(plan);this.clock=Objects.requireNonNull(clock);this.lifetime=Objects.requireNonNull(lifetime);
            prepared.requireCore(core);requireLifetime();
            if(core.sessionAccess().current()!=original||original.isRetired()||original.hostForPublication()!=host
                    ||initialCatalog.context().actions()!=original||initialCatalog.context().adopted()!=original.driver())
                throw new IOException("actual startup inputs require the identical admitted Core/session/catalog/Host");
        }
        public void closeOriginal()throws Exception {lifetime.close();}
        public RootApplicationAssembly.Core core(){return core;}
        public RootApplicationSession original(){return original;}
        public RootStartupNextResources.Prepared prepared(){return prepared;}
        public OrdinarySessionHost host(){return host;}
        public McpExecutableDirectory.Complete directory(){return directory;}
        public RootRuntimeDefinitions.Inputs privateInputs(){return definitions.inputs();}
        public Clock clock(){return clock;}
        public Instant deadline(){return plan.deadline();}
        public BatchLimits nextBatch(){return startup.batches().getFirst();}
        /** No cached before-NEXT catalog is relabelled current. Lookup consumes the original factory and writer scope. */
        public RootInstalledCatalog catalogFor(RootApplicationSession identicalPublished)throws IOException {
            requireLifetime();
            try {
                return core.withBorrowed(()->definitions.catalogFactory().requireCurrentCatalog(identicalPublished));
            }catch(InterruptedException interrupted){
                Thread.currentThread().interrupt();throw new IOException("actual retained catalog lookup interrupted",interrupted);
            }
        }
        /** Current read inputs are retained production objects, never reconstructed from JSON or historical law DATA. */
        public ReadInputs readInputs()throws IOException {
            requireLifetime();
            try {
                return core.withBorrowed(()->{
                    var current=core.sessionAccess().current();
                    var catalog=definitions.catalogFactory().requireCurrentCatalog(current);
                    return new ReadInputs(core,current,catalog);
                });
            }catch(InterruptedException interrupted){
                Thread.currentThread().interrupt();throw new IOException("actual current read inputs interrupted",interrupted);
            }
        }
        private void requireLifetime()throws IOException {
            lifetime.requireOpen();
            startup.requireCurrent(clock);definitions.requireApplication(startup.application());
            if(!clock.instant().isBefore(plan.deadline())||core.archive().writer()!=core.writer()
                    ||initialCatalog.context().core()!=core||initialCatalog.context().archive()!=core.archive()
                    ||initialCatalog.context().writer()!=core.writer()||!core.configuration().equals(definitions.inputs().application()))
                throw new IOException("original admitted startup lifetime, deadline or writer/archive changed");
            prepared.requireCore(core);
            lifetime.requireOpen();
        }
    }
    public static final class ReadInputs {
        private final RootApplicationAssembly.Core core;
        private final RootApplicationSession current;
        private final RootInstalledCatalog catalog;
        private ReadInputs(RootApplicationAssembly.Core core,RootApplicationSession current,RootInstalledCatalog catalog)throws IOException {
            this.core=core;this.current=current;this.catalog=catalog;
            var context=catalog.context();
            if(context.core()!=core||context.writer()!=core.writer()||context.archive()!=core.archive()
                    ||context.actions()!=current||context.adopted()!=current.driver()||current.isRetired()
                    ||current.writer()!=core.writer()||current.archive()!=core.archive()||!core.planningReads().isBound())
                throw new IOException("current read inputs lost original transport/Driver/Core/writer/archive");
        }
        public RootApplicationAssembly.Core core(){return core;}
        public RootApplicationSession current(){return current;}
        public RootInstalledCatalog catalog(){return catalog;}
        public RootPlanningReads reads(){return core.planningReads();}
        public org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive archive(){return core.archive();}
    }
    static Actual retain(RootApplicationAssembly.Core core,RootApplicationSession original,
            RootStartupNextResources.Prepared prepared,RootRuntimeDefinitions definitions,RootInstalledCatalog installed,
            OrdinarySessionHost host,McpExecutableDirectory.Complete directory,
            RootStartupConfiguration startup,NativeLaunchPlan plan,Clock clock,Lifetime lifetime)throws IOException {
        return new Actual(core,original,prepared,definitions,installed,host,directory,startup,plan,clock,lifetime);
    }

    /** Runs the existing Main, including all admission/refusal/UNKNOWN and cleanup paths, exactly once.
     * The actual consumer runs synchronously inside that original lifetime; no background startup or second writer exists. */
    public static void execute(Request request,OrdinarySessionHost actualHost,PublicMcpHost actualPublicHost,Work consumer)throws Exception {
        Objects.requireNonNull(request);Objects.requireNonNull(actualHost);Objects.requireNonNull(actualPublicHost);Objects.requireNonNull(consumer);
        var start=RootStartupConfiguration.readExact(request.startup());start.requireCurrent(Clock.systemUTC());
        if(start.batches().size()!=1)throw new IOException("actual Host NEXT acceptance requires its one complete original batch, not a truncated startup schedule");
        if(actualHost.current().isPresent()||actualPublicHost.current().isPresent())
            throw new IOException("actual startup cannot reuse or replace an already installed host");
        var main=new RootApplicationMain();main.ordinaryHost=actualHost;main.publicHost=actualPublicHost;
        boolean[] delivered={false};
        int exit=main.runWithAdmitted(actual->{
            if(delivered[0])throw new IOException("actual startup inputs cannot be delivered twice");
            delivered[0]=true;consumer.consume(actual);
        },request.startup().path(),Long.toString(request.startup().bytes()),request.startup().sha256());
        if(exit!=0||!delivered[0])throw new IOException("actual startup did not deliver admitted inputs; terminal="+exit);
    }
    /** Capture-only menu validation in the same Main/writer. Callback completion is followed by original cleanup. */
    public static void executeMenu(Request request,OrdinarySessionHost actualHost,PublicMcpHost actualPublicHost,MenuWork consumer)throws Exception {
        Objects.requireNonNull(request);Objects.requireNonNull(actualHost);Objects.requireNonNull(actualPublicHost);Objects.requireNonNull(consumer);
        var start=RootStartupConfiguration.readExact(request.startup());start.requireCurrent(Clock.systemUTC());
        if(actualHost.current().isPresent()||actualPublicHost.current().isPresent())
            throw new IOException("actual menu startup cannot reuse an installed host");
        var main=new RootApplicationMain();main.ordinaryHost=actualHost;main.publicHost=actualPublicHost;
        boolean[] delivered={false};
        int exit=main.runMenuValidation(actual->{
            if(delivered[0])throw new IOException("original menu inputs cannot be delivered twice");
            delivered[0]=true;consumer.consume(actual);
        },request.startup().path(),Long.toString(request.startup().bytes()),request.startup().sha256());
        if(exit!=0||!delivered[0])throw new IOException("actual menu startup did not complete its original Main; terminal="+exit);
    }
    /** Capture validation stays inside the original Main; it neither installs ordinary Root nor repeats Start. */
    public static void executePhysicalValidation(Request request,OrdinarySessionHost actualHost,
            PublicMcpHost actualPublicHost,PhysicalWork consumer)throws Exception {
        Objects.requireNonNull(request);Objects.requireNonNull(actualHost);Objects.requireNonNull(actualPublicHost);Objects.requireNonNull(consumer);
        var start=RootStartupConfiguration.readExact(request.startup());start.requireCurrent(Clock.systemUTC());
        if(actualHost.current().isPresent()||actualPublicHost.current().isPresent())
            throw new IOException("actual physical validation cannot reuse an installed host");
        var main=new RootApplicationMain();main.ordinaryHost=actualHost;main.publicHost=actualPublicHost;
        boolean[] menuDelivered={false},driverDelivered={false};
        int exit=main.runPhysicalStatusValidation(new PhysicalWork() {
            @Override public void menu(MenuActual actual)throws Exception {
                if(menuDelivered[0]||driverDelivered[0])throw new IOException("original capture menu cannot be delivered twice");
                actual.requireScope();menuDelivered[0]=true;consumer.menu(actual);actual.requireScope();
            }
            @Override public void entry(MenuActual actual,GameplayEntryService.Result result)throws Exception {
                if(!menuDelivered[0]||driverDelivered[0])throw new IOException("original attempted entry crossed its capture order");
                actual.requireScope();consumer.entry(actual,Objects.requireNonNull(result));actual.requireScope();
            }
            @Override public void driver(PhysicalActual actual)throws Exception {
                if(!menuDelivered[0]||driverDelivered[0])throw new IOException("original capture Driver cannot be delivered twice");
                actual.requireScope();driverDelivered[0]=true;consumer.driver(actual);actual.requireScope();
            }
        },request.startup().path(),Long.toString(request.startup().bytes()),request.startup().sha256());
        if(exit!=0||!menuDelivered[0])throw new IOException("actual physical validation did not complete its original Main; terminal="+exit);
    }
    public static byte[] encode(Request request) {
        Objects.requireNonNull(request);ObjectNode root=StrictJson.object();root.put("schema",SCHEMA);
        root.set("startup",new ExactRef(request.startup().path(),request.startup().bytes(),request.startup().sha256()).toJson());
        root.put("close_wait_ms",request.closeWait().toMillis());return StrictJson.canonical(root,MAXIMUM_BYTES);
    }
    public static Request decode(byte[] original) {
        ObjectNode root=StrictJson.object(StrictJson.parse(original,MAXIMUM_BYTES),Set.of("schema","startup","close_wait_ms"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))),"exact actual startup inputs request schema required");
        ExactRef ref=ExactRef.fromJson(root.get("startup"));
        return new Request(new FileRef(ref.path(),ref.bytes(),ref.sha256()),
                Duration.ofMillis(StrictJson.integer(root.get("close_wait_ms"),100,30000)));
    }
    public static Request readExact(FileRef original)throws IOException {
        try{return decode(RootRuntimeDefinitions.read(original,MAXIMUM_BYTES));}
        catch(IllegalArgumentException invalid){throw new IOException("invalid actual startup inputs request",invalid);}
    }
    public static Request fromEnvironment(Map<String,String> environment)throws IOException {
        Objects.requireNonNull(environment);String path=environment.get(REQUEST_ENV),bytes=environment.get(REQUEST_ENV+"_BYTES"),sha=environment.get(REQUEST_ENV+"_SHA256");
        if(path==null||bytes==null||sha==null||!bytes.matches("[1-9][0-9]{0,3}")||!sha.matches("[0-9a-f]{64}"))
            throw new IOException("MISSING_ACTUAL_ROOT_INPUTS: exact startup inputs request path/bytes/SHA required; no historical DATA fallback");
        try{return readExact(new FileRef(path,Long.parseLong(bytes),sha));}
        catch(IllegalArgumentException invalid){throw new IOException("invalid actual startup inputs request reference",invalid);}
    }
}

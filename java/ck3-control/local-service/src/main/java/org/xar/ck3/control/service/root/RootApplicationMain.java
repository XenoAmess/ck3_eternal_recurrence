package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.runtime.Quarkus;
import io.quarkus.runtime.QuarkusApplication;
import io.quarkus.runtime.annotations.QuarkusMain;
import jakarta.inject.Inject;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.OrdinarySessionHost;
import org.xar.ck3.control.service.OrdinarySessionResource;
import org.xar.ck3.control.service.mcp.PublicMcpHost;

/** The single Quarkus application entry: exact definitions, one real native owner, original entry, actual host, full ordinary batches. */
@QuarkusMain
public final class RootApplicationMain implements QuarkusApplication {
    @Inject OrdinarySessionHost ordinaryHost;
    @Inject PublicMcpHost publicHost;
    public static void main(String... args) { Quarkus.run(RootApplicationMain.class,args); }
    @Override public int run(String... args)throws Exception {return execute(java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.empty(),args);}
    /** Actual acceptance consumes the admitted original objects inside this same production lifetime. */
    public int runWithAdmitted(RootStartupInputsProducer.Work actualWork,String... args)throws Exception {
        return execute(java.util.Optional.of(Objects.requireNonNull(actualWork)),java.util.Optional.empty(),java.util.Optional.empty(),args);
    }
    /** Explicit capture-only menu validation; no ordinary entry, Driver or batch is performed. */
    public int runMenuValidation(RootStartupInputsProducer.MenuWork actualWork,String... args)throws Exception {
        return execute(java.util.Optional.empty(),java.util.Optional.of(Objects.requireNonNull(actualWork)),java.util.Optional.empty(),args);
    }
    /** Original fresh entry may retain its real physical Driver for read-only validation, never a full Root. */
    public int runPhysicalStatusValidation(RootStartupInputsProducer.PhysicalWork actualWork,String... args)throws Exception {
        return execute(java.util.Optional.empty(),java.util.Optional.empty(),java.util.Optional.of(Objects.requireNonNull(actualWork)),args);
    }
    @FunctionalInterface interface EntryCall {
        GameplayEntryService.Result call() throws IOException;
    }
    @FunctionalInterface interface EntryPause {
        void pause(java.time.Duration duration) throws InterruptedException;
    }
    /** The one Start is retained while its original entry reconciles under the unchanged deadline. */
    static GameplayEntryService.Result startAndAwaitEntry(EntryCall start, EntryCall resume,
            Instant deadline, Clock clock) throws IOException, InterruptedException {
        return startAndAwaitEntry(start,resume,deadline,clock,Thread::sleep);
    }
    @FunctionalInterface interface CaptureCall { void consume()throws Exception; }
    private static final class CaptureCallbackFailure extends RuntimeException {
        private final Exception original;
        private CaptureCallbackFailure(Exception original){super(original);this.original=original;}
    }
    private static void withCaptureCallback(RootRuntimeContext context,CaptureCall work,CaptureCall finish)throws Exception {
        try {
            context.core().withBorrowed(()->{
                try {
                    return context.bindings().withCaptureReadOnly(context.game().generation(),()->{
                        Throwable original=null;
                        try{work.consume();}
                        catch(Exception|Error failure){original=failure;throw failure;}
                        finally {
                            try{finish.consume();}
                            catch(Exception|Error cleanup){if(original!=null)original.addSuppressed(cleanup);else throw cleanup;}
                        }
                        return null;
                    });
                }catch(IOException|InterruptedException failure){throw failure;}
                catch(RuntimeException failure){throw failure;}
                catch(Exception failure){throw new CaptureCallbackFailure(failure);}
            });
        }catch(CaptureCallbackFailure failure){throw failure.original;}
    }
    /** The actual Main caller's finite continuation; the pause seam permits deterministic deadline regression. */
    static GameplayEntryService.Result startAndAwaitEntry(EntryCall start, EntryCall resume,
            Instant deadline, Clock clock, EntryPause pause) throws IOException, InterruptedException {
        return awaitOriginalEntry(start,resume,deadline,clock,pause,false);
    }
    /** Read-only capture observes the original UNKNOWN while its unchanged deadline is still usable. */
    static GameplayEntryService.Result startAndAwaitPhysicalEntry(EntryCall start, EntryCall resume,
            Instant deadline, Clock clock) throws IOException, InterruptedException {
        return startAndAwaitPhysicalEntry(start,resume,deadline,clock,Thread::sleep);
    }
    static GameplayEntryService.Result startAndAwaitPhysicalEntry(EntryCall start, EntryCall resume,
            Instant deadline, Clock clock, EntryPause pause) throws IOException, InterruptedException {
        return awaitOriginalEntry(start,resume,deadline,clock,pause,true);
    }
    private static GameplayEntryService.Result awaitOriginalEntry(EntryCall start, EntryCall resume,
            Instant deadline, Clock clock, EntryPause pause, boolean physicalValidation) throws IOException, InterruptedException {
        Objects.requireNonNull(start);Objects.requireNonNull(resume);Objects.requireNonNull(deadline);
        Objects.requireNonNull(clock);Objects.requireNonNull(pause);
        GameplayEntryService.Result entered=Objects.requireNonNull(start.call());
        while(entered instanceof GameplayEntryService.Awaiting waiting && !waiting.actual().settled()) {
            if(physicalValidation && waiting.actual().state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown)
                return entered;
            Instant now=clock.instant();
            if(!now.isBefore(deadline))break;
            java.time.Duration remaining=java.time.Duration.between(now,deadline);
            java.time.Duration interval=java.time.Duration.ofMillis(50);
            try {pause.pause(remaining.compareTo(interval)<0?remaining:interval);}
            catch(InterruptedException interrupted) {Thread.currentThread().interrupt();throw interrupted;}
            if(!clock.instant().isBefore(deadline))break;
            entered=Objects.requireNonNull(resume.call());
        }
        return entered;
    }
    private int execute(java.util.Optional<RootStartupInputsProducer.Work> admittedWork,
            java.util.Optional<RootStartupInputsProducer.MenuWork> menuValidation,
            java.util.Optional<RootStartupInputsProducer.PhysicalWork> physicalValidation,String... args)throws Exception {
        StrictJson.require((admittedWork.isPresent()?1:0)+(menuValidation.isPresent()?1:0)+(physicalValidation.isPresent()?1:0)<=1,
                "one original Main execution mode required");
        Clock clock=Clock.systemUTC();JavaGameLifecycle lifecycle=null;RootApplicationAssembly.Core ownedCore=null;RootRuntimeDefinitions receiptDefinitions=null;
        Path receipts=null;ExactRef startupRef=null;int exit=1;boolean cleanupRequired=false;Exception primary=null;
        RootStartupInputsProducer.Lifetime lifetime=null;
        try {
            var invocation=RootSavedNativeCoordinator.arguments(args);
            ControlBuild.FileRef original=invocation.startup();
            startupRef=exact(original);
            RootStartupConfiguration start=RootStartupConfiguration.readExact(original);start.requireCurrent(clock);
            RootApplicationConfiguration application=RootApplicationConfiguration.readExact(start.application());application.requireCurrent(clock);
            StrictJson.require(application.machineId().equals(start.machineId())&&application.mode()==HostMode.COMPLETE_MIGRATION
                    &&!start.reviewAt().isAfter(application.reviewAt()),"complete-migration application and original startup review must agree");
            // These are concrete Java definitions/installers. Missing native/cold/domain producers refuse before CREATE.
            RootRuntimeDefinitions definitions=RootRuntimeDefinitions.readExact(start.runtimeDefinitions(),clock);
            receiptDefinitions=definitions;
            definitions.requireApplication(start.application());
            definitions.bindStartup(original);
            definitions.requireCompleteMigration();
            RootRuntimeCatalogFactory catalogs=definitions.catalogFactory();
            RootApplicationAssembly.Core core=RootApplicationAssembly.open(application,clock,catalogs.domainRegistrations(),definitions.rollbackAuthority(),definitions.storageWriteGuard());
            ownedCore=core;
            catalogs.bindCore(core);
            NativeLaunchPlan plan=definitions.nativeLaunchPlan();
            lifecycle=definitions.gameLifecycle(core);
            boolean savedRoute=invocation.savedRoute().isPresent();
            StrictJson.require(physicalValidation.isEmpty()||!savedRoute,
                    "physical Status capture uses the original fresh entry; Saved requires its separate genuine cold producer");
            StrictJson.require((savedRoute?plan.load() instanceof NativeLaunchPlan.SavedGame:plan.load() instanceof NativeLaunchPlan.NewGame)
                    &&plan.sources().review().machineId().equals(start.machineId())&&!plan.deadline().isAfter(start.reviewAt()),
                    "explicit startup route requires its exact reviewed NewGame or Saved plan on this machine and deadline");
            var saved=savedRoute?java.util.Optional.of(RootSavedNativeCoordinator.readExact(invocation.savedRoute().orElseThrow(),original,plan,lifecycle,clock))
                    :java.util.Optional.<RootSavedNativeCoordinator>empty();
            plan.sources().requireLoadedClass(RootApplicationMain.class);plan.sources().requireLoadedClass(RootRuntimeDefinitions.class);
            StrictJson.require(catalogs.sources().hostConfiguration().equals(start.application()),"runtime definitions selected another actual Root host configuration");
            final java.util.Optional<JavaRuntimePackage.CapturedReviewAvailable> capturedMenu;
            var packageRequest=catalogs.sources().packageRequest();
            if(menuValidation.isPresent()||physicalValidation.isPresent()) {
                var reviewed=JavaRuntimePackage.reviewCapturedService(packageRequest,new RootPackageNativeVerifier());
                if(!(reviewed instanceof JavaRuntimePackage.CapturedReviewAvailable capture))
                    throw new IOException("actual capture-only menu review unavailable: "+reviewed);
                capture.verifyCurrent();capturedMenu=java.util.Optional.of(capture);
            } else {
                var verified=ControlBuild.verifiedCompletedReceipt(packageRequest.serviceBuildActual());
                StrictJson.require(verified.targetKind()==ControlBuild.TargetKind.SERVICE_FAST_JAR
                        &&verified.machineId().equals(start.machineId()),"ordinary Root requires its full verified service build");
                capturedMenu=java.util.Optional.empty();
                new RootPackageNativeVerifier().verify(packageRequest,catalogs.sources().hostConfiguration());
            }
            plan.sources().verify();start.requireCurrent(clock);
            // NativeLaunchPlan's real Port verifies actual ENV -> BUILD -> REGISTER. JavaGameLifecycle observes fresh background-only Steam offline before CREATE.
            receipts=start.receiptDirectory();
            ObjectNode intent=envelope(start.machineId(),clock,"STARTUP_QUALIFIED_NO_GAME_YET");intent.set("startup",exact(original).toJson());
            intent.set("application",exact(start.application()).toJson());intent.set("runtime_definitions",exact(start.runtimeDefinitions()).toJson());
            intent.set("native_launch_plan",application.nativeLaunchPlan().toJson());write(receiptDefinitions,receipts.resolve("startup-intent.json"),intent);
            JavaGameLifecycle.LaunchResult created=saved.isPresent()?saved.orElseThrow().launch():lifecycle.launchNew(plan);
            if(!(created instanceof JavaGameLifecycle.Started started)) {
                ObjectNode refused=envelope(start.machineId(),clock,created instanceof JavaGameLifecycle.Unknown?"LAUNCH_UNKNOWN_QUERY_ONLY":"LAUNCH_REJECTED");
                if(created instanceof JavaGameLifecycle.Unknown unknown){refused.put("request_id",unknown.requestId());refused.put("detail",bounded(unknown.reason()));
                    if(unknown.lastEvidence()==null)refused.putNull("actual_evidence");else refused.set("actual_evidence",unknown.lastEvidence().toJson());}
                else refused.put("detail",bounded(((JavaGameLifecycle.Rejected)created).reason()));
                write(receiptDefinitions,receipts.resolve("launch-terminal.json"),refused);return 2;
            }
            cleanupRequired=true;ManagedGameSession game=started.session();game.verify();
            ObjectNode launched=envelope(start.machineId(),clock,"PHYSICAL_HELLO_ONLY_NO_GAMEPLAY_ADMISSION");
            launched.set("game",game.generation().toJson());launched.set("native_hello",started.nativeHello().toJson());launched.set("launch_evidence",started.launchEvidence().toJson());
            write(receiptDefinitions,receipts.resolve("launch-terminal.json"),launched);
            var installed=catalogs.install(core,game,start.source(),core.planningReads(),clock,plan.deadline());
            definitions.bindOriginalResume(core,installed);
            // A merely physical Started/hello never becomes gameplay authority. Start uses the same sole coordinator and first full Driver/SEM producer.
            RootMenuSession menu=core.menu(start.authorityId(),game,start.source(),installed.bindings(),installed.frontend().authority());
            // Publish the actual frontend directory while this same original menu still owns the pre-game phase.
            StrictJson.require(menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND,
                    "frontend public installation requires the original unadmitted menu phase");
            var directory=definitions.installFrontendPublic(core,installed,Objects.requireNonNull(publicHost),clock);
            StrictJson.require(publicHost.current().filter(actual->actual==directory.directory()).isPresent(),
                    "the actual frontend public directory must be retained by the same Quarkus host");
            ObjectNode frontendPublic=envelope(game.machineId(),clock,"FRONTEND_PUBLIC_INSTALLED_NO_GAMEPLAY_ADMISSION");
            frontendPublic.set("game",game.generation().toJson());frontendPublic.put("session_id",game.sessionId());
            write(receiptDefinitions,receipts.resolve("frontend-public.json"),frontendPublic);
            if(physicalValidation.isPresent()) {
                var capture=capturedMenu.orElseThrow();capture.verifyCurrent();
                var actual=RootStartupInputsProducer.retainMenu(core,installed,menu,clock,plan.deadline(),capture,
                        definitions.publicHandlerContext(),ordinaryHost,publicHost,directory.directory());
                withCaptureCallback(actual.context(),()->physicalValidation.orElseThrow().menu(actual),actual::finishScope);
                StrictJson.require(menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND
                        &&installed.context().optionalDriverProducer().isEmpty()&&ordinaryHost.current().isEmpty(),
                        "capture menu callback cannot grant Driver or ordinary host authority");
                capture.verifyCurrent();
            }
            if(menuValidation.isPresent()) {
                var capture=capturedMenu.orElseThrow();capture.verifyCurrent();
                var actual=RootStartupInputsProducer.retainMenu(core,installed,menu,clock,plan.deadline(),capture,
                        definitions.publicHandlerContext(),ordinaryHost,publicHost,directory.directory());
                withCaptureCallback(actual.context(),()->menuValidation.orElseThrow().consume(actual),actual::finishScope);
                StrictJson.require(menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND
                        &&installed.context().optionalDriverProducer().isEmpty(),"menu validation cannot admit gameplay");
                capture.verifyCurrent();
                ObjectNode validated=envelope(game.machineId(),clock,"PRE_DRIVER_MENU_VALIDATION_COMPLETED_NO_GAMEPLAY_ADMISSION");
                validated.set("game",game.generation().toJson());validated.put("session_id",game.sessionId());
                validated.put("capture_qualification",capture.qualification().name());validated.put("capture_tests",capture.tests().name());
                validated.set("capture_build_actual",exact(packageRequest.serviceBuildActual()).toJson());
                write(receiptDefinitions,receipts.resolve("menu-validation-terminal.json"),validated);return 0;
            }
            final RootApplicationSession root;
            final ObjectNode admission;
            if(saved.isPresent()) {
                // The same menu has installed and sealed the sole coordinator/directory; Saved issues no fresh START action.
                var coordinator=saved.orElseThrow();root=definitions.finishSaved(core,installed,coordinator,lifecycle,start,clock);
                var cold=coordinator.original();admission=envelope(start.machineId(),clock,"ACTUAL_SAVED_COLD_CANONICAL_DRIVER_AND_FULL_ROOT_ADMITTED");
                admission.set("canonical_cold_evidence",cold.evidence().toJson());
                admission.put("cold_event_identity",cold.commitReceipt().eventIdentity());
                admission.put("cold_sequence",cold.commitReceipt().head().sequence());
            } else {
                var entry=installed.frontend().entry(menu);
                var actualMenu=core.withBorrowed(()->installed.frontend().observeMenu(core.writer().borrowedSession(),plan.deadline()));
                var selectedRobert=RootFrontendRulesPublicProducts.prepareFreshRobert(installed,menu,actualMenu,start.entry().actionId(),plan.deadline());
                EntryCall originalStart=()->entry.startRobert(start.entry().actionId(),selectedRobert,plan.deadline());
                var entered=physicalValidation.isPresent()
                        ?startAndAwaitPhysicalEntry(originalStart,entry::resume,plan.deadline(),clock)
                        :startAndAwaitEntry(originalStart,entry::resume,plan.deadline(),clock);
                if(!(entered instanceof GameplayEntryService.Admitted admitted)) {
                    if(physicalValidation.isPresent()) {
                        var capture=capturedMenu.orElseThrow();capture.verifyCurrent();
                        var actual=RootStartupInputsProducer.retainMenu(core,installed,menu,clock,plan.deadline(),capture,
                                definitions.publicHandlerContext(),ordinaryHost,publicHost,directory.directory());
                        withCaptureCallback(actual.context(),()->physicalValidation.orElseThrow().entry(actual,entered),actual::finishScope);
                        StrictJson.require(menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND
                                &&installed.context().optionalDriverProducer().isEmpty()&&ordinaryHost.current().isEmpty(),
                                "unresolved entry capture cannot grant Driver or ordinary authority");
                        capture.verifyCurrent();
                        if(entered instanceof GameplayEntryService.Awaiting waiting
                                &&waiting.actual().state() instanceof org.xar.ck3.control.application.action.ActionState.Unknown) {
                            ObjectNode captured=envelope(start.machineId(),clock,"ACTUAL_ENTRY_UNKNOWN_STATUS_CAPTURED_NO_GAMEPLAY_ADMISSION");
                            captured.put("start_action_id",waiting.actual().command().actionId());
                            captured.put("start_action_sequence",waiting.actual().sequence());
                            captured.set("start_receipt",core.withBorrowed(()->core.archive().withSession(core.writer().borrowedSession())
                                    .receiptReferenceOf(waiting.actual())).toJson());
                            captured.put("capture_qualification",capture.qualification().name());captured.put("capture_tests",capture.tests().name());
                            captured.set("capture_build_actual",exact(packageRequest.serviceBuildActual()).toJson());
                            write(receiptDefinitions,receipts.resolve("physical-status-validation-terminal.json"),captured);return 0;
                        }
                    }
                    ObjectNode pending=envelope(start.machineId(),clock,"ENTRY_UNRESOLVED_NO_REPLAY");pending.put("detail",bounded(entered.toString()));
                    write(receiptDefinitions,receipts.resolve("entry-terminal.json"),pending);return 3;
                }
                if(physicalValidation.isPresent()) {
                    var capture=capturedMenu.orElseThrow();capture.verifyCurrent();
                    installed.bindPhysicalDriver(admitted.driver());
                    core.writer().locked(same->{RootInitialEpisodeProof.require(installed.context(),same,admitted);return null;});
                    var actual=RootStartupInputsProducer.retainPhysical(core,installed,menu,clock,plan.deadline(),capture,admitted,
                            definitions.publicHandlerContext(),ordinaryHost,publicHost,directory.directory());
                    withCaptureCallback(actual.context(),()->physicalValidation.orElseThrow().driver(actual),actual::finishScope);
                    StrictJson.require(menu.publicPhase()==RootMenuSession.PublicPhase.FRONTEND&&ordinaryHost.current().isEmpty()
                            &&installed.context().adopted()==admitted.driver(),"physical Status validation cannot publish an ordinary Root");
                    capture.verifyCurrent();
                    ObjectNode captured=envelope(start.machineId(),clock,"ACTUAL_PHYSICAL_DRIVER_STATUS_VALIDATED_NO_GAMEPLAY_ADMISSION");
                    captured.set("game",game.generation().toJson());captured.put("session_id",game.sessionId());
                    captured.put("start_action_id",admitted.actual().command().actionId());captured.put("entry_event_identity",admitted.entry().eventIdentity());
                    captured.put("capture_qualification",capture.qualification().name());captured.put("capture_tests",capture.tests().name());
                    captured.set("capture_build_actual",exact(packageRequest.serviceBuildActual()).toJson());
                    write(receiptDefinitions,receipts.resolve("physical-status-validation-terminal.json"),captured);return 0;
                }
                root=definitions.finishInitial(core,installed,admitted,lifecycle,start,clock);
                admission=envelope(start.machineId(),clock,"ACTUAL_ENTRY_DRIVER_AND_FULL_ROOT_ADMITTED");
                admission.put("start_action_id",admitted.actual().command().actionId());admission.put("start_action_sequence",admitted.actual().sequence());
                admission.put("entry_event_identity",admitted.entry().eventIdentity());
            }
            root.install(Objects.requireNonNull(ordinaryHost),plan.deadline());
            var admittedDirectory=definitions.installPublic(core,installed,Objects.requireNonNull(publicHost),clock);
            StrictJson.require(admittedDirectory.directory()==directory.directory(),
                    "gameplay admission must retain the already installed frontend directory without a second registry or host installation");
            StrictJson.require(publicHost.current().filter(actual->actual==directory.directory()).isPresent(),
                    "the same Quarkus host must retain the actual complete typed public directory");
            admission.set("game",root.identity().game().toJson());admission.put("session_id",root.identity().sessionId());
            write(receiptDefinitions,receipts.resolve("root-admission.json"),admission);
            final var cleanupCore=ownedCore;final var cleanupLifecycle=lifecycle;
            final var cleanupDefinitions=receiptDefinitions;final var cleanupReceipts=receipts;
            lifetime=new RootStartupInputsProducer.Lifetime(()->cleanup(cleanupCore,cleanupLifecycle,true,cleanupDefinitions,cleanupReceipts,clock,null));
            if(admittedWork.isPresent()) {
                var actual=RootStartupInputsProducer.retain(core,root,definitions.nextResources(core),definitions,installed,
                        ordinaryHost,admittedDirectory,start,plan,clock,lifetime);
                admittedWork.orElseThrow().consume(actual);return 0;
            }
            exit=0;
            for(var batch:start.batches()) {
                start.requireCurrent(clock);if(!clock.instant().isBefore(plan.deadline()))throw new IOException("actual application deadline expired before the next batch");
                // This getter resolves the actual installed owner after a qualified physical handoff, never the last constructed candidate.
                RootApplicationSession current=core.sessionAccess().current();BatchReport report=current.batch(batch);
                write(receiptDefinitions,receipts.resolve("batch-"+batch.batchId()+".json"),OrdinarySessionResource.report(report));
                boolean continueOwned=switch(report.terminal()) {
                    case TURN_BOUND,WALL_TIMEOUT,CHECKPOINT_DEFERRED->true;
                    case EPISODE_HANDOFF->core.sessionAccess().current()!=current;
                    default->false;
                };
                if(!continueOwned){exit=4;break;}
            }
            return exit;
        }catch(InterruptedException interrupted){primary=interrupted;Thread.currentThread().interrupt();throw interrupted;}
        catch(Exception failure) {
            primary=failure;
            ObjectNode result=envelope(WindowsJobProcess.currentMachineId(),clock,"ROOT_STARTUP_OR_BATCH_UNAVAILABLE");
            result.put("exception_type",failure.getClass().getName());result.put("detail",bounded(String.valueOf(failure.getMessage())));
            if(startupRef==null)result.putNull("startup");else result.set("startup",startupRef.toJson());
            if(receipts!=null)try{write(receiptDefinitions,receipts.resolve("root-failure.json"),result);}catch(IOException recordFailure){failure.addSuppressed(recordFailure);}
            System.err.println(new String(StrictJson.canonical(result,1<<20),java.nio.charset.StandardCharsets.UTF_8));
            throw failure;
        }finally {
            if(lifetime!=null)lifetime.finish(primary);
            else cleanup(ownedCore,lifecycle,cleanupRequired,receiptDefinitions,receipts,clock,primary);
        }
    }
    private static void cleanup(RootApplicationAssembly.Core ownedCore,JavaGameLifecycle lifecycle,
            boolean cleanupRequired,RootRuntimeDefinitions receiptDefinitions,Path receipts,Clock clock,Exception primary)throws Exception {
        Exception shutdownFailure=null;
        if(ownedCore!=null)try{ownedCore.stopPublicRequests();}
        catch(Exception failure){if(primary!=null)primary.addSuppressed(failure);else shutdownFailure=failure;}
        if(cleanupRequired&&lifecycle!=null) {
            boolean interrupted=Thread.interrupted();
            try {
            var active=lifecycle.currentSession();
            if(active.isPresent()) {
                ManagedGameSession actual=active.orElseThrow();
                var shutdown=actual.stopTracked(actual.generation(),clock.instant().plusSeconds(25),false);
                if(receipts!=null) {
                    ObjectNode terminal=envelope(actual.machineId(),clock,"ORIGINAL_GAME_CLEANUP_CONSUMED");
                    terminal.set("game",shutdown.generation().toJson());terminal.put("was_running",shutdown.wasRunning());
                    terminal.put("cleanup_proven",shutdown.cleanupProven());terminal.put("terminal_kind",shutdown.kind().name());
                    terminal.set("actual_evidence",shutdown.evidence().toJson());terminal.put("full_job_terminal_passed",shutdown.terminal().passed());
                    write(receiptDefinitions,receipts.resolve("game-cleanup.json"),terminal);
                }
                if(!shutdown.cleanupProven())throw new IOException("original Game cleanup is not proven; preserve its actual UNKNOWN and do not replay CREATE");
            }
            }catch(Exception cleanup){if(primary!=null)primary.addSuppressed(cleanup);else if(shutdownFailure!=null)shutdownFailure.addSuppressed(cleanup);else shutdownFailure=cleanup;}
            finally{if(interrupted)Thread.currentThread().interrupt();}
        }
        if(ownedCore!=null) {
            try {
                ownedCore.close();
                ownedCore.closeCompletion().toCompletableFuture().get(55,java.util.concurrent.TimeUnit.SECONDS);
            }catch(java.util.concurrent.TimeoutException pending){
                ObjectNode drain=envelope(WindowsJobProcess.currentMachineId(),clock,"OFFLINE_DRAIN_PENDING");
                drain.put("detail","accepted analysis continues on the original non-daemon worker; this is not a completion receipt");
                System.err.println(new String(StrictJson.canonical(drain,1<<20),java.nio.charset.StandardCharsets.UTF_8));
            }catch(Exception closeFailure){
                if(closeFailure instanceof InterruptedException)Thread.currentThread().interrupt();
                if(primary!=null){if(primary!=closeFailure)primary.addSuppressed(closeFailure);}
                else if(shutdownFailure!=null)shutdownFailure.addSuppressed(closeFailure);else shutdownFailure=closeFailure;
            }
        }
        if(primary==null&&shutdownFailure!=null)throw shutdownFailure;
    }
    private static ExactRef exact(ControlBuild.FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static ObjectNode envelope(String machine,Clock clock,String status) {
        ObjectNode value=StrictJson.object();value.put("schema","xar.java-root-startup-result/v1");value.put("machine_id",machine);
        value.put("observed_at_utc",clock.instant().toString());value.put("status",status);return value;
    }
    private static String bounded(String value){return value.length()<=8192?value:value.substring(0,8192);}
    private static void write(RootRuntimeDefinitions actual,Path fresh,ObjectNode value)throws IOException {
        if(actual==null)throw new IOException("runtime receipt has no actual source-bound storage producer");
        actual.writeRuntimeReceipt(fresh,StrictJson.canonical(value,1<<20));
    }
}

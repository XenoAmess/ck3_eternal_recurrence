package org.xar.ck3.control.platform;

import java.io.IOException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.StrictJson;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicReference;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePipeEndpoint;
import org.xar.ck3.control.nativebridge.NativeProcessGuard;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;

/** Shared production creator/tracker. Python is neither invoked nor accepted as a Game owner. */
public final class JavaGameLifecycle {
    public sealed interface LaunchResult permits Started,Rejected,Unknown { }
    public record Started(ManagedGameSession session,ExactRef nativeHello,ExactRef launchEvidence) implements LaunchResult { }
    public record Rejected(String reason) implements LaunchResult { }
    public record Unknown(String requestId,String reason,ExactRef lastEvidence) implements LaunchResult { }
    public record ReplacementRequest(String parentLifecycleIntentId,GameGeneration expectedOld,NativeLaunchPlan savedPlan,boolean requireRunning){
        public ReplacementRequest{
            Objects.requireNonNull(expectedOld);Objects.requireNonNull(savedPlan);
            if(parentLifecycleIntentId==null||parentLifecycleIntentId.isBlank()||parentLifecycleIntentId.length()>256
                    ||!(savedPlan.load() instanceof NativeLaunchPlan.SavedGame)
                    ||!savedPlan.requestId().equals(replacementRequestId(parentLifecycleIntentId)))throw new IllegalArgumentException("One durable parent identity and its exact Saved child plan required");
        }
        public ReplacementRequest(String parentLifecycleIntentId,GameGeneration expectedOld,NativeLaunchPlan savedPlan){this(parentLifecycleIntentId,expectedOld,savedPlan,false);}
    }
    public sealed interface ReplacementResult permits Replaced,ReplacementRejected,ReplacementUnknown { }
    public record Replaced(GameGeneration previous,Started replacement,ExactRef lifecycleEvidence) implements ReplacementResult { }
    public record ReplacementRejected(String reason) implements ReplacementResult { }
    public record ReplacementUnknown(String parentLifecycleIntentId,String reason) implements ReplacementResult { }
    private enum ClaimState { RESERVED, CREATE_ENTERED, STARTED, CLEANUP_PROVEN, UNKNOWN }
    private sealed interface ControlRecord permits Claim,Tracking,ReplacementControl { }
    private record Claim(String schema,String machineId,String requestId,String sessionId,String nonce,ClaimState state,
            WindowsJobProcess.ProcessIdentity game,String observedAtUtc) implements ControlRecord {
        private Claim { Instant.parse(observedAtUtc); }
    }
    private record Tracking(String schema,String machineId,String requestId,String sessionId,String nonce,
            WindowsJobProcess.ProcessIdentity game,List<String> command,String kernelPolicy) implements ControlRecord { }
    private record ReplacementControl(String schema,String parentLifecycleIntentId,String phase,long oldPid,String oldBirthDecimal,
            ControlBuild.FileRef save,ExactRef stopEvidence,ExactRef launchEvidence) implements ControlRecord { }
    private static final ConcurrentHashMap<String,String> ACTIVE=new ConcurrentHashMap<>();
    private static final String MUTEX="Local\\XarJavaGameLifecycle-v1";
    private final Map<String,LaunchResult> results=new ConcurrentHashMap<>();
    private final Map<String,NativeLaunchPlanCodec.Configuration> launchRequests=new java.util.LinkedHashMap<>();
    private final ConcurrentHashMap<ManagedGameSession,TrackingState> tracking=new ConcurrentHashMap<>();
    private volatile ManagedGameSession currentSession;
    private final Map<String,ReplacementRequest> replacementRequests=new java.util.LinkedHashMap<>();
    private final Map<String,ReplacementResult> replacements=new java.util.LinkedHashMap<>();
    private final List<NativePrivateActionPermission> privateActions;
    private record TrackingState(NativeLaunchPlan plan,String nonce,String registryKey,Path trackingPath) { }

    /** The composition root supplies the entire immutable permission set before any physical Game exists. */
    private final Optional<Duration> operationTimeout;
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions) {
        this(actualPrivateActions,Optional.empty());
    }
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,Duration readOperationTimeout) {
        this(actualPrivateActions,validateTimeout(readOperationTimeout));
    }
    private JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,Optional<Duration> timeout) {
        privateActions=List.copyOf(actualPrivateActions);
        java.util.Set<String> operations=new java.util.HashSet<>();
        for(NativePrivateActionPermission permission:privateActions)
            if(!operations.add(permission.operation().value()))
                throw new IllegalArgumentException("one actual private permission per operation required");
        operationTimeout=timeout;
    }
    private static Optional<Duration> validateTimeout(Duration readOperationTimeout) {
        Objects.requireNonNull(readOperationTimeout);
        if(readOperationTimeout.isNegative()||readOperationTimeout.isZero())throw new IllegalArgumentException("readOperationTimeout must be positive");
        return Optional.of(readOperationTimeout);
    }

    /** Preserve object identity across initial and replacement transports; no late permission mutation is allowed. */
    List<NativePrivateActionPermission> privateActions() { return privateActions; }

    public synchronized LaunchResult launchNew(NativeLaunchPlan plan)throws IOException,InterruptedException{
        if(!(plan.load() instanceof NativeLaunchPlan.NewGame))return new Rejected("launchNew requires explicit NewGame");
        return launch(plan);
    }
    public synchronized LaunchResult launchSaved(NativeLaunchPlan plan)throws IOException,InterruptedException{
        if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))return new Rejected("launchSaved requires an exact physical save");
        return launch(plan);
    }
    /** Query is read-only. Missing owner memory cannot prove that an older CREATE never entered. */
    public synchronized LaunchResult query(String requestId){
        return results.getOrDefault(requestId,new Unknown(requestId,"No original launch result retained; query cannot reject prior CREATE, replay or adopt",null));
    }
    public synchronized java.util.Optional<ManagedGameSession> currentSession(){return java.util.Optional.ofNullable(currentSession);}

    public synchronized void adoptAttached(ManagedGameSession actual) throws IOException {
        Objects.requireNonNull(actual);
        if (actual.mode() != ManagedGameSession.Mode.ATTACHED)
            throw new IOException("Session must be ATTACHED");
        actual.verify();
        if (currentSession != null && currentSession != actual)
            throw new IOException("Cannot replace a different current session");
        currentSession = actual;
    }
    /** A cold consumer must retain this new daemon's genuine original creator result, never a parsed row. */
    void requireColdStarted(Started actual,Instant deadline)throws IOException{
        Objects.requireNonNull(actual);Win32Host.deadline(deadline);
        if(actual.session()==null||actual.nativeHello()==null||actual.launchEvidence()==null)
            throw new IOException("Cold bootstrap requires a complete original retained Started capability");
        ManagedGameSession session=actual.session();NativeLaunchPlan plan=session.launchPlan();
        if(deadline.isAfter(plan.deadline())||results.get(plan.requestId())!=actual||currentSession!=session
                ||!(plan.load() instanceof NativeLaunchPlan.SavedGame))
            throw new IOException("Cold bootstrap requires this daemon's exact privately retained Saved creator result");
        verifyTracking(session);session.verify();
        if(results.get(plan.requestId())!=actual||currentSession!=session)
            throw new IOException("Original cold creator changed during physical verification");
    }
    /** Deliberately acquire the named mutex without the lifecycle monitor: other creators take it in the opposite order. */
    Win32Host.Mutex retainColdBootstrapMutex(Started actual,Instant deadline)throws IOException,InterruptedException{
        requireColdStarted(actual,deadline);Win32Host.Mutex held=Win32Host.mutex(MUTEX,deadline);
        try{held.requireHeld();requireColdStarted(actual,deadline);return held;}
        catch(IOException|RuntimeException failure){try{held.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
    }
    public static String replacementRequestId(String parentLifecycleIntentId){
        try{return "replacement-"+java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(parentLifecycleIntentId.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }
    public synchronized ReplacementResult queryReplacement(String parentLifecycleIntentId){
        return replacements.getOrDefault(parentLifecycleIntentId,new ReplacementUnknown(parentLifecycleIntentId,"No retained original replacement; query never launches or adopts"));
    }
    /** Same producer for checkpoint restoration and immutable-seed next episode; no synthetic CheckpointPair needed. */
    public synchronized ReplacementResult replaceSavedOnce(ReplacementRequest request)throws IOException,InterruptedException{
        String id=request.parentLifecycleIntentId();
        if(replacementRequests.containsKey(id)){
            if(!replacementRequests.get(id).equals(request))return new ReplacementUnknown(id,"Original replacement parent changed its child/body; no replay");
            return queryReplacement(id);
        }
        if(replacementRequests.size()>=4096)return new ReplacementRejected("Replacement retention is full");
        NativeLaunchPlan plan=request.savedPlan();Win32Host.deadline(plan.deadline());
        NativeLaunchPolicy.requireCurrent(plan);
        ManagedGameSession previous=currentSession;
        if(previous==null||!previous.generation().equals(request.expectedOld()))return new ReplacementRejected("Expected old original managed generation is not retained");
        Path claim=plan.stateDirectory().resolve("control/"+plan.requestId()+"-parent.json");
        try(Win32Host.Mutex mutex=Win32Host.mutex(MUTEX,plan.deadline())){
            mutex.requireHeld();
            if(Files.exists(claim))return new ReplacementUnknown(id,"Persistent parent replacement already entered; no retry/adoption");
            NativeLaunchPlan.SavedGame save=(NativeLaunchPlan.SavedGame)plan.load();
            atomic(claim,new ReplacementControl("xar.java-game-replacement/v1",id,"STOP_ENTERED",request.expectedOld().pid(),request.expectedOld().creationFiletime().value().toString(),save.save(),null,null),true);
            replacementRequests.put(id,request);replacements.put(id,new ReplacementUnknown(id,"Original replacement entered; query only"));
            try{
                ManagedGameSession.Shutdown stopped=previous.stopTracked(request.expectedOld(),plan.deadline(),request.requireRunning());
                if(!stopped.cleanupProven())return queryReplacement(id);
                if(request.requireRunning()&&!stopped.wasRunning()){
                    ReplacementRejected rejected=new ReplacementRejected("Old generation was already signalled when running restore was required; original cleanup proved, no new Game created");
                    replacements.put(id,rejected);return rejected;
                }
                LaunchResult result=launchSaved(plan);
                if(!(result instanceof Started started)){
                    ReplacementUnknown unknown=new ReplacementUnknown(id,"Old Job stopped; Saved child not proven: "+result);
                    replacements.put(id,unknown);return unknown;
                }
                if(started.session().generation().equals(request.expectedOld()))throw new IOException("Replacement did not create a different measured generation");
                atomic(claim,new ReplacementControl("xar.java-game-replacement/v1",id,"NATIVE_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED",request.expectedOld().pid(),request.expectedOld().creationFiletime().value().toString(),save.save(),stopped.evidence(),started.launchEvidence()),false);
                Replaced replaced=new Replaced(request.expectedOld(),started,LifecycleEvidence.exact(ControlBuild.FileRef.measure(claim)));replacements.put(id,replaced);return replaced;
            }catch(IOException|RuntimeException failure){ReplacementUnknown unknown=new ReplacementUnknown(id,"Stop/create replacement UNKNOWN: "+failure);replacements.put(id,unknown);return unknown;}
        }
    }
    private LaunchResult launch(NativeLaunchPlan plan)throws IOException,InterruptedException{
        Objects.requireNonNull(plan);
        NativeLaunchPlanCodec.Configuration body=NativeLaunchPlanCodec.describe(plan),previous=launchRequests.get(plan.requestId());
        if(previous!=null){
            if(!previous.equals(body))return new Unknown(plan.requestId(),"Original launch ID changed its exact configuration; no replay",null);
            return results.getOrDefault(plan.requestId(),new Unknown(plan.requestId(),"Original launch entered without a retained terminal; query only",null));
        }
        if(launchRequests.size()>=4096)return new Rejected("Original once-only request retention is full");
        NativeLaunchPolicy.requireCurrent(plan);
        launchRequests.put(plan.requestId(),body);
        Win32Host.deadline(plan.deadline());
        Path control=plan.stateDirectory().resolve("control");Files.createDirectories(control);
        String key=plan.sources().review().machineId()+"|"+Path.of(plan.sources().review().gameExecutable().path()).toRealPath();
        String nonce=UUID.randomUUID().toString();
        boolean entered=false,registered=false;
        LifecycleEvidence evidence=new LifecycleEvidence(plan);ExactRef last=null;
        WindowsJobProcess process=null;SteamOfflineProbe.QualifiedOffline offline=null;
        AtomicReference<WindowsPreloadCustody.Lease> lease=new AtomicReference<>();
        AtomicReference<NativePipeEndpoint> endpoint=new AtomicReference<>();
        AtomicReference<NativePipeEndpoint.Config> endpointConfig=new AtomicReference<>();
        AtomicReference<NativeProcessGuard> endpointGuard=new AtomicReference<>();
        NativeGameTransport transport=null;
        try(Win32Host.Mutex ignored=Win32Host.mutex(MUTEX,plan.deadline())){
            ignored.requireHeld();
            if(ACTIVE.putIfAbsent(key,plan.requestId())!=null)return reject(plan,"Another original Java lifecycle owns this machine/Game");
            registered=true;
            if(Files.exists(claimPath(plan)))return reject(plan,"Persistent request claim already exists; no replay/adoption");
            Files.createDirectory(plan.evidenceRoot());
            writeClaim(plan,nonce,ClaimState.RESERVED,null,true);
            last=evidence.write(LifecycleEvidence.Event.INTENT,null,null,null,null,"Configured Java Game launch requested");
            offline=SteamOfflineProbe.observe(plan.steam(),plan.evidenceRoot().resolve("steam-offline.json"));
            if(!inventory(plan,evidence,"BEFORE_CREATE").isEmpty())throw new IOException("Qualified running CK3 appeared after preflight");
            offline.consumeBeforeGameCreate();
            prepareNoModsProfile(plan.preparedProfile(),plan.profileDirectory());
            if (plan.load() instanceof NativeLaunchPlan.SavedGame saved) {
                NativeSavedGameFiles.materialize(plan.profileDirectory(), saved);
            }
            writeMarker(plan,nonce,null);
            writeClaim(plan,nonce,ClaimState.CREATE_ENTERED,null,false);
            entered=true; // Every failure after entering original CREATE remains UNKNOWN and is never replayed.
            Map<String,String> environment=gameEnvironment(plan.environment(),plan.pipeName());
            WindowsJobProcess.CommandSpec command=new WindowsJobProcess.CommandSpec(Path.of(plan.sources().review().gameExecutable().path()),plan.gameArguments(),
                    Path.of(plan.sources().review().gameExecutable().path()).getParent(),environment,plan.evidenceRoot().resolve("game.stdout"),plan.evidenceRoot().resolve("game.stderr"),plan.gameMemoryBytes());
            WindowsJobProcess.ConsoleMode display=plan.windowPolicy()==NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE
                    ?WindowsJobProcess.ConsoleMode.GUI_MINIMIZED_NO_ACTIVATE:WindowsJobProcess.ConsoleMode.GUI_SHOWN_NO_ACTIVATE;
            process=WindowsJobProcess.start(command,display,suspended->{
                WindowsPreloadCustody.Lease held=WindowsPreloadCustody.prepare(suspended,new WindowsPreloadCustody.DllRef(plan.sources().review().bridgeDll(),plan.deadline(),()->{}));
                if(!lease.compareAndSet(null,held)){held.close();throw new IOException("Original suspended callback repeated");}
                try{
                    GameGeneration generation=ManagedGameSession.generation(held.targetIdentity());
                    writeMarker(plan,nonce,held.targetIdentity());
                    evidence.write(LifecycleEvidence.Event.SUSPENDED,held.targetIdentity(),null,null,null,"Actual held suspended Game; continuous DLL file lease and complete absent-module roster acquired");
                    NativePipeEndpoint.Config config=new NativePipeEndpoint.Config(plan.pipeName(),plan.sources().review().machineId(),generation,plan.sessionId(),plan.bridgeVersion(),plan.sources().review().gameExecutable().sha256(),plan.adapterId());
                    NativeProcessGuard guard=expected->{
                        if(!generation.equals(expected)||!generation.equals(ManagedGameSession.generation(held.targetIdentity())))throw new IOException("Native peer verifier differs from held original generation");
                    };
                    if(!endpointConfig.compareAndSet(null,config)||!endpointGuard.compareAndSet(null,guard))
                        throw new IOException("Original suspended launch endpoint inputs already retained; no second attachment");
                    NativePipeEndpoint pipe=NativePipeEndpoint.create(config,guard);
                    if(!endpoint.compareAndSet(null,pipe)){pipe.close();throw new IOException("Native server already created");}
                    injectStartup(plan,held,evidence);return held;
                }catch(IOException|RuntimeException failure){try{held.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}throw failure;}
            });
            WindowsPreloadCustody.Lease held=lease.get();
            if(held==null||endpoint.get()==null||endpointConfig.get()==null||endpointGuard.get()==null)
                throw new IOException("Original Game did not retain pre-resume resources and endpoint inputs");
            transport=operationTimeout.isPresent()?new NativeGameTransport(endpoint.get(),65536,1000000,privateActions,operationTimeout.get()):new NativeGameTransport(endpoint.get(),65536,1000000,privateActions);
            Instant helloDeadline=min(plan.deadline(),Instant.now().plus(plan.startupTimeout()));
            transport.awaitHello(helloDeadline);held.observeLoaded();
            Path hello=plan.evidenceRoot().resolve("native-hello.packet");Files.write(hello,transport.lastOriginalPacket(),StandardOpenOption.CREATE_NEW);
            last=evidence.write(LifecycleEvidence.Event.HELLO,process.identity(),process.accounting(),null,null,"Original Native hello/actual kernel peer/connection generation accepted; loaded DLL matches continuous pre-load FileID");
            ManagedGameSession session=new ManagedGameSession(plan,process,held,offline,transport,evidence,this,
                    endpointConfig.get(),endpointGuard.get());
            session.verify();
            Tracking record=new Tracking("xar.java-game-tracking/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,process.identity(),session.command(),"KILL_ON_JOB_CLOSE|JOB_MEMORY; exact retained process/thread and DLL lease");
            Path track=control.resolve("java-game.json");atomic(track,record,false);
            tracking.put(session,new TrackingState(plan,nonce,key,track));
            writeClaim(plan,nonce,ClaimState.STARTED,process.identity(),false);
            Started started=new Started(session,LifecycleEvidence.exact(ControlBuild.FileRef.measure(hello)),last);results.put(plan.requestId(),started);
            currentSession=session;session.activateRuntime();return started;
        }catch(IOException|RuntimeException failure){
            if(!entered){
                if(offline!=null)try{offline.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
                return reject(plan,failure.toString());
            }
            WindowsJobProcess.ProcessIdentity failedIdentity=process!=null?process.identity():null;
            ExactRef cleanup=cleanupUnknown(process,endpoint.get(),lease.get(),offline,evidence,failure);
            if(cleanup!=null)last=cleanup;
            writeClaim(plan,nonce,ClaimState.UNKNOWN,failedIdentity,false);
            Unknown unknown=new Unknown(plan.requestId(),failure.toString(),last);results.put(plan.requestId(),unknown);return unknown;
        }catch(InterruptedException interrupted){
            ExactRef cleanup=cleanupUnknown(process,endpoint.get(),lease.get(),offline,evidence,interrupted);
            if(cleanup!=null)last=cleanup;
            if(entered){Unknown unknown=new Unknown(plan.requestId(),"Interrupted after original CREATE; no replay",last);results.put(plan.requestId(),unknown);}
            Thread.currentThread().interrupt();throw interrupted;
        }finally{
            if(registered&&!entered)ACTIVE.remove(key,plan.requestId());
        }
    }
    private static ExactRef cleanupUnknown(WindowsJobProcess process,NativePipeEndpoint endpoint,WindowsPreloadCustody.Lease custody,
            SteamOfflineProbe.QualifiedOffline offline,LifecycleEvidence evidence,Exception original){
        ExactRef terminalProof=null;
        if(process!=null){
            boolean restoreInterrupt=Thread.interrupted();
            try{
                WindowsJobProcess.Accounting before=process.accounting();
                evidence.write(LifecycleEvidence.Event.STOP_REQUESTED,process.identity(),before,null,
                        org.xar.ck3.control.contracts.GameLifecycle.TerminalKind.UNKNOWN,"Failure cleanup of original held Job; no action retry or marker clearance");
                WindowsJobProcess.CommandResult actual=consumeUnknownCleanup(process,Instant.now().plusSeconds(25));
                terminalProof=evidence.write(LifecycleEvidence.Event.STOPPED,process.identity(),actual.accounting(),actual,
                        org.xar.ck3.control.contracts.GameLifecycle.TerminalKind.UNKNOWN,"Actual failed-launch cleanup terminal consumed; UNKNOWN claim and unsafe marker remain");
            }catch(InterruptedException interrupted){restoreInterrupt=true;original.addSuppressed(interrupted);}
            catch(IOException|RuntimeException error){original.addSuppressed(error);}
            finally{
                try{process.close();}catch(RuntimeException error){original.addSuppressed(error);}
                if(restoreInterrupt)Thread.currentThread().interrupt();
            }
        }
        if(endpoint!=null)try{endpoint.close();}catch(IOException|RuntimeException error){original.addSuppressed(error);}
        if(custody!=null)try{custody.close();}catch(IOException|RuntimeException error){original.addSuppressed(error);}
        if(offline!=null)try{offline.close();}catch(IOException|RuntimeException error){original.addSuppressed(error);}
        return terminalProof;
    }
    /** Bounded safety cleanup consumes the original process wait/exit/Job; it grants no retry authority. */
    static WindowsJobProcess.CommandResult consumeUnknownCleanup(WindowsJobProcess process,Instant cleanupDeadline)throws InterruptedException{
        if(process.isRunning()||process.accounting().activeProcesses()!=0)process.terminate(125);
        return process.await(Duration.ofSeconds(20),cleanupDeadline,()->{});
    }
    private static List<Win32Host.ProcessRow> inventory(NativeLaunchPlan plan,LifecycleEvidence evidence,String phase)throws IOException{
        Win32Host.ProcessInventory actual=Win32Host.processInventory("ck3.exe",plan.deadline());
        evidence.writeInventory(phase,actual);
        return actual.qualifiedRunning();
    }
    private LaunchResult reject(NativeLaunchPlan plan,String reason){Rejected result=new Rejected(reason);results.put(plan.requestId(),result);return result;}
    /** Apply the requested mod selection only when this owner is about to create a Game. */
    static void prepareNoModsProfile(NativeLaunchPlan.PreparedProfile profile,Path profileDirectory)throws IOException{
        Objects.requireNonNull(profile);
        if(profile.noMods().isEmpty())return;
        Path dlcLoad=profileDirectory.resolve("dlc_load.json");
        ObjectNode configuration;
        if(Files.exists(dlcLoad)){
            byte[] raw;
            try(var input=Files.newInputStream(dlcLoad)){raw=input.readNBytes(StrictJson.EXPLICIT_MAX_BYTES+1);}
            try{
                JsonNode parsed=StrictJson.parse(raw,StrictJson.EXPLICIT_MAX_BYTES);
                if(!(parsed instanceof ObjectNode object))throw new IOException("dlc_load.json must be a JSON object");
                configuration=object;
            }catch(IllegalArgumentException malformed){
                throw new IOException("Invalid JSON in dlc_load.json",malformed);
            }
        }else{
            Files.createDirectories(profileDirectory);
            configuration=StrictJson.object();configuration.putArray("disabled_dlcs");
        }
        configuration.putArray("enabled_mods");
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(configuration);
        Path temp=dlcLoad.resolveSibling(dlcLoad.getFileName()+"."+UUID.randomUUID()+".pending");
        try{
            try(FileChannel out=FileChannel.open(temp,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
                java.nio.ByteBuffer bytes=java.nio.ByteBuffer.wrap(raw);
                while(bytes.hasRemaining())out.write(bytes);
                out.force(true);
            }
            Files.move(temp,dlcLoad,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
        }finally{
            Files.deleteIfExists(temp);
        }
    }

    /** Actual Game child inheritance; explicit isolated paths override the parent without exposing its values. */
    static Map<String,String> gameEnvironment(Map<String,String> overrides,String pipeName){
        Objects.requireNonNull(overrides);Objects.requireNonNull(pipeName);
        Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());environment.putAll(overrides);
        environment.keySet().removeIf(k->k.equalsIgnoreCase("XAR_CK3_BRIDGE_MODE")||k.equalsIgnoreCase("XAR_CK3_BRIDGE_PIPE"));
        environment.put("XAR_CK3_BRIDGE_MODE","native-headless");environment.put("XAR_CK3_BRIDGE_PIPE",pipeName);
        return java.util.Collections.unmodifiableMap(environment);
    }
    private static void injectStartup(NativeLaunchPlan plan,WindowsPreloadCustody.Lease held,LifecycleEvidence evidence)throws IOException{
        Path root=plan.evidenceRoot();ControlBuild.FileRef injector=plan.sources().review().injector();
        WindowsJobProcess.CommandSpec command=new WindowsJobProcess.CommandSpec(Path.of(injector.path()),List.of(Long.toString(held.targetIdentity().pid()),plan.sources().review().bridgeDll().path()),root,plan.environment(),root.resolve("injector.stdout"),root.resolve("injector.stderr"),plan.injectorMemoryBytes());
        Files.write(root.resolve("injector-argv.json"),ControlBuild.strictMapper().writeValueAsBytes(command),StandardOpenOption.CREATE_NEW);
        try(WindowsJobProcess original=WindowsJobProcess.start(command)){
            WindowsJobProcess.CommandResult actual=original.await(plan.injectorTimeout(),plan.deadline(),()->{});
            evidence.write(LifecycleEvidence.Event.INJECTOR_EXIT,held.targetIdentity(),actual.accounting(),actual,null,"Original C++ startup argv [PID,DLL], exactly once, actual inner exit/Job preserved");
            if(!actual.passed())throw new IOException("C++ injector failed/UNKNOWN; no second submission: "+actual);
        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("Original injector interrupted; no retry",interrupted);}
    }
    void verifyTracking(ManagedGameSession session)throws IOException{
        if(!tracking.containsKey(session))throw new IOException("Session is not retained by this original creator");
    }
    void clearTrackingAfterProvenExit(ManagedGameSession session)throws IOException{
        TrackingState state=tracking.get(session);if(state==null)throw new IOException("No original tracking owner");
        writeClaim(state.plan(),state.nonce(),ClaimState.CLEANUP_PROVEN,session.identity(),false);
        Files.deleteIfExists(state.trackingPath());
        Files.deleteIfExists(state.plan().stateDirectory().resolve("control/unsafe-cleanup.json"));
        ACTIVE.remove(state.registryKey(),state.plan().requestId());tracking.remove(session);
    }
    private static Path claimPath(NativeLaunchPlan plan){return plan.stateDirectory().resolve("control/request-"+plan.requestId()+".json");}
    private static void writeClaim(NativeLaunchPlan plan,String nonce,ClaimState state,WindowsJobProcess.ProcessIdentity game,boolean fresh)throws IOException{
        atomic(claimPath(plan),new Claim("xar.java-game-launch-claim/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,state,game,Instant.now().toString()),fresh);
    }
    private static void writeMarker(NativeLaunchPlan plan,String nonce,WindowsJobProcess.ProcessIdentity game)throws IOException{
        atomic(plan.stateDirectory().resolve("control/unsafe-cleanup.json"),new Claim("xar.java-game-unsafe/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,ClaimState.CREATE_ENTERED,game,Instant.now().toString()),false);
    }
    private static void atomic(Path destination,ControlRecord value,boolean fresh)throws IOException{
        byte[] raw=ControlBuild.strictMapper().writeValueAsBytes(value);if(raw.length>65536)throw new IOException("Bounded lifecycle control record required");
        if(fresh){try(FileChannel out=FileChannel.open(destination,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){java.nio.ByteBuffer bytes=java.nio.ByteBuffer.wrap(raw);while(bytes.hasRemaining())out.write(bytes);out.force(true);}return;}
        Path temp=destination.resolveSibling(destination.getFileName()+"."+UUID.randomUUID()+".pending");
        try(FileChannel out=FileChannel.open(temp,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){java.nio.ByteBuffer bytes=java.nio.ByteBuffer.wrap(raw);while(bytes.hasRemaining())out.write(bytes);out.force(true);}
        Files.move(temp,destination,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
    }
    private static Instant min(Instant a,Instant b){return a.isBefore(b)?a:b;}
}

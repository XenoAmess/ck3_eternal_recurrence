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
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ImportedSaveTransfer;
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
    public record Replaced(GameGeneration previous,Started replacement,ExactRef lifecycleEvidence,
            Optional<ImportedSaveTransfer> importedSaveTransfer) implements ReplacementResult {
        public Replaced { Objects.requireNonNull(importedSaveTransfer); }
        public Replaced(GameGeneration previous,Started replacement,ExactRef lifecycleEvidence) {
            this(previous,replacement,lifecycleEvidence,Optional.empty());
        }
    }
    public record ReplacementRejected(String reason) implements ReplacementResult { }
    public record ReplacementUnknown(String parentLifecycleIntentId,String reason) implements ReplacementResult { }
    private enum ClaimState { RESERVED, CREATE_ENTERED, STARTED, CLEANUP_PROVEN, UNKNOWN }
    private sealed interface ControlRecord permits Claim,Tracking,ReplacementControl,ImportedReplacementControl { }
    private record Claim(String schema,String machineId,String requestId,String sessionId,String nonce,ClaimState state,
            WindowsJobProcess.ProcessIdentity game,String observedAtUtc) implements ControlRecord {
        private Claim { Instant.parse(observedAtUtc); }
    }
    private record Tracking(String schema,String machineId,String requestId,String sessionId,String nonce,
            WindowsJobProcess.ProcessIdentity game,List<String> command,String kernelPolicy) implements ControlRecord { }
    private record ReplacementControl(String schema,String parentLifecycleIntentId,String phase,long oldPid,String oldBirthDecimal,
            ControlBuild.FileRef save,ExactRef stopEvidence,ExactRef launchEvidence) implements ControlRecord { }
    private record ImportedReplacementControl(String schema,String parentLifecycleIntentId,String phase,long oldPid,
            String oldBirthDecimal,ControlBuild.FileRef save,ExactRef stopEvidence,ExactRef launchEvidence,
            ExactRef importedSaveTransfer) implements ControlRecord { }
    private static final ConcurrentHashMap<String,String> ACTIVE=new ConcurrentHashMap<>();
    static final String MUTEX="Local\\XarJavaGameLifecycle-v1";
    private final Map<String,LaunchResult> results=new ConcurrentHashMap<>();
    private final Map<String,NativeLaunchPlanCodec.Configuration> launchRequests=new java.util.LinkedHashMap<>();
    private final Map<String,ControlBuild.FileRef> launchModes=new java.util.LinkedHashMap<>();
    private final ConcurrentHashMap<ManagedGameSession,TrackingState> tracking=new ConcurrentHashMap<>();
    private volatile ManagedGameSession currentSession;
    private final Map<String,ReplacementRequest> replacementRequests=new java.util.LinkedHashMap<>();
    private final Map<String,ReplacementResult> replacements=new java.util.LinkedHashMap<>();
    private final Map<String,ExitedGeneration> exitedReplacementSources=new java.util.LinkedHashMap<>();
    private final List<NativePrivateActionPermission> privateActions;
    private record TrackingState(NativeLaunchPlan plan,String nonce,String registryKey,Path trackingPath) { }

    /** The composition root supplies the entire immutable permission set before any physical Game exists. */
    private final Optional<Duration> operationTimeout;
    /** Immutable DATA selected before any physical Game or Native endpoint exists. */
    public record TransportLimits(int maximumFramesPerOperation,int maximumSubmissions) {
        public TransportLimits {
            if(maximumFramesPerOperation<1||maximumFramesPerOperation>65_536
                    ||maximumSubmissions<1||maximumSubmissions>1_000_000)
                throw new IllegalArgumentException("explicit finite frame/submission bounds required");
        }
    }
    private static final TransportLimits DEFAULT_TRANSPORT_LIMITS=new TransportLimits(65_536,1_000_000);
    private final TransportLimits transportLimits;
    public TransportLimits transportLimits(){return transportLimits;}
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions) {
        this(actualPrivateActions,Optional.empty(),DEFAULT_TRANSPORT_LIMITS);
    }
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,Duration readOperationTimeout) {
        this(actualPrivateActions,validateTimeout(readOperationTimeout),DEFAULT_TRANSPORT_LIMITS);
    }
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,
            int maximumFramesPerOperation,int maximumSubmissions) {
        this(actualPrivateActions,Optional.empty(),new TransportLimits(maximumFramesPerOperation,maximumSubmissions));
    }
    public JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,Duration readOperationTimeout,
            int maximumFramesPerOperation,int maximumSubmissions) {
        this(actualPrivateActions,validateTimeout(readOperationTimeout),new TransportLimits(maximumFramesPerOperation,maximumSubmissions));
    }
    private JavaGameLifecycle(List<NativePrivateActionPermission> actualPrivateActions,Optional<Duration> timeout,TransportLimits limits) {
        privateActions=List.copyOf(actualPrivateActions);
        java.util.Set<String> operations=new java.util.HashSet<>();
        for(NativePrivateActionPermission permission:privateActions)
            if(!operations.add(permission.operation().value()))
                throw new IllegalArgumentException("one actual private permission per operation required");
        operationTimeout=timeout;transportLimits=Objects.requireNonNull(limits);
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
    @FunctionalInterface public interface SavedCreateHandoff { void verifyAndRelease()throws IOException; }
    /** Preparation owner verifies the persisted mapping and closes all handles before original CREATE. */
    public synchronized LaunchResult launchSaved(NativeLaunchPlan plan,SavedCreateHandoff handoff)throws IOException,InterruptedException {
        Objects.requireNonNull(handoff);
        if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))return new Rejected("mapped Saved launch requires exact SavedGame");
        return launch(plan,null,handoff);
    }
    /** Explicit user-authorized Saved launch in unchanged current Steam mode; no offline claim. */
    public synchronized LaunchResult launchSavedCurrentMode(NativeLaunchPlan plan,Path authorization)throws IOException,InterruptedException{
        if(!(plan.load() instanceof NativeLaunchPlan.SavedGame))return new Rejected("Current Steam mode launch requires exact SavedGame");
        return launch(plan,CurrentSteamLaunch.authorizationSource(authorization));
    }
    /** Query is read-only. Missing owner memory cannot prove that an older CREATE never entered. */
    public synchronized LaunchResult query(String requestId){
        return results.getOrDefault(requestId,new Unknown(requestId,"No original launch result retained; query cannot reject prior CREATE, replay or adopt",null));
    }
    public synchronized java.util.Optional<ManagedGameSession> currentSession(){return java.util.Optional.ofNullable(currentSession);}

    /** Opaque source role issued after reopening the real supervisor terminal and observing the OS.
     * It is neither a parsed terminal DTO nor a replacement ManagedGameSession/STOP capability. */
    public static final class ExitedGeneration {
        private final JavaGameLifecycle owner;
        private final NativeLaunchPlan template;
        private final ExitedGameSource.Qualified source;
        private final Instant deadline;
        private ExitedGeneration(JavaGameLifecycle owner,NativeLaunchPlan template,ExitedGameSource.Qualified source,Instant deadline) {
            this.owner=owner;this.template=template;this.source=source;this.deadline=deadline;
        }
        public GameGeneration generation(){return source.descriptor().generation();}
        public String sourceSessionId(){return source.descriptor().sessionId();}
        public String machineId(){return source.descriptor().machineId();}
        public ExactRef evidence(){return source.currentObservation();}
        public ExactRef terminalReference(){return source.terminalReference();}
        public Instant terminalObservedAt(){return source.terminal().observedAt();}
        public Instant observedAt(){return source.observedAt();}
        public Instant deadline(){return deadline;}
        public NativeLaunchPlanCodec.Configuration originalConfiguration(){return source.descriptor().configuration();}
        public void requireOwner(JavaGameLifecycle expectedOwner,Instant operationDeadline)throws IOException {
            if(expectedOwner!=owner)throw new IOException("exited-generation source belongs to another lifecycle instance");
            owner.requireExitedSource(this,template,operationDeadline);
        }
        /** Lexical membership only. It observes neither source files nor the OS and grants no current physical permit. */
        public void requireMembership(JavaGameLifecycle expectedOwner,Instant operationDeadline)throws IOException {
            if(expectedOwner!=owner)throw new IOException("exited-generation membership belongs to another lifecycle instance");
            owner.requireExitedMembership(this,template,operationDeadline);
        }
        /** Original source membership only; no expired submission window or physical Game permit is renewed. */
        public void requireHistoricalOwner(JavaGameLifecycle expectedOwner)throws IOException {
            if(expectedOwner!=owner)throw new IOException("historical exited source belongs to another lifecycle instance");
            ExitedGameSource.revalidateOriginals(source,template);
        }
        /** The exact privately retained replacement, never a parsed launch ACK, owns the new independent read. */
        public void requireReplacementOwner(JavaGameLifecycle expectedOwner,Replaced actual,Instant readDeadline)throws IOException {
            if(expectedOwner!=owner)throw new IOException("exited replacement belongs to another lifecycle instance");
            owner.requireExitedReplacement(this,actual,readDeadline);
        }
    }
    public synchronized ExitedGeneration qualifyExitedOwner(Path ownerDescriptor,GameGeneration expected,
            NativeLaunchPlan reviewedReplacementTemplate,Instant deadline)throws IOException {
        Win32Host.deadline(deadline);
        if(Instant.MAX.equals(deadline))throw new IOException("finite exited-generation source window required");
        if(currentSession!=null&&!currentSession.generation().equals(expected))
            throw new IOException("another current managed Game blocks exited owner import");
        var source=ExitedGameSource.qualify(ownerDescriptor,expected,reviewedReplacementTemplate,deadline);
        return new ExitedGeneration(this,reviewedReplacementTemplate,source,deadline);
    }
    synchronized void requireExitedSource(ExitedGeneration actual,NativeLaunchPlan template,Instant deadline)throws IOException {
        requireExitedMembership(actual,template,deadline);
        ExitedGameSource.revalidate(actual.source,template,deadline);
    }
    private synchronized void requireExitedMembership(ExitedGeneration actual,NativeLaunchPlan template,Instant deadline)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(deadline);Win32Host.deadline(deadline);
        if(actual.owner!=this||actual.template!=template||deadline.isAfter(actual.deadline)
                ||!Instant.now().isBefore(actual.deadline)
                ||currentSession!=null&&!currentSession.generation().equals(actual.generation()))
            throw new IOException("exited-generation role changed its actual owner, template, Game or original finite window");
    }
    private synchronized void requireExitedReplacement(ExitedGeneration original,Replaced actual,Instant deadline)throws IOException {
        Objects.requireNonNull(actual);Win32Host.deadline(deadline);
        boolean retained=false;
        for(var entry:replacements.entrySet())if(entry.getValue()==actual&&exitedReplacementSources.get(entry.getKey())==original)retained=true;
        if(original.owner!=this||!retained||!actual.previous().equals(original.generation())
                ||currentSession!=actual.replacement().session()||currentSession.generation().equals(original.generation()))
            throw new IOException("new read did not retain this exact source-owned exited replacement");
        ExitedGameSource.revalidateOriginals(original.source,original.template);currentSession.verify();
    }

    public synchronized void adoptAttached(ManagedGameSession actual) throws IOException {
        Objects.requireNonNull(actual);
        if (actual.mode() != ManagedGameSession.Mode.ATTACHED)
            throw new IOException("Session must be ATTACHED");
        actual.verify();
        if (currentSession != null && currentSession != actual)
            throw new IOException("Cannot replace a different current session");
        currentSession = actual;
    }
    /** Pure in-memory capture of an exact already-formed original Started, before descriptor publication. */
    public synchronized ManagedGameSession.CreatorOwnership captureStartedOwner(Started actual)throws IOException {
        if(actual==null||actual.session()==null||actual.nativeHello()==null||actual.launchEvidence()==null)
            throw new IOException("complete actual original Started required");
        ManagedGameSession session=actual.session();
        if(results.get(session.launchPlan().requestId())!=actual||currentSession!=session)
            throw new IOException("Started does not belong to this exact current creator result");
        return session.captureOriginalCreator(this);
    }
    /** A replacement may retain Started before its later parent-record publication fails. No IO or PID lookup. */
    public synchronized Optional<ManagedGameSession.CreatorOwnership> startedOwner(String originalRequestId)throws IOException {
        if(originalRequestId==null)throw new IOException("original request identity required");
        LaunchResult retained=results.get(originalRequestId);
        if(!(retained instanceof Started actual))return Optional.empty();
        return actual.session().existingCreatorOwnership(this);
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
    /** The original supervisor already proved exit and Job0. Import sends no old Game STOP. */
    public synchronized ReplacementResult replaceExitedSavedOnce(ReplacementRequest request,ExitedGeneration actual)
            throws IOException,InterruptedException {
        return replaceExitedSavedOnce(request,actual,null);
    }
    synchronized ReplacementResult replaceImportedExitedSavedOnce(ReplacementRequest request,ExitedGeneration actual,
            ImportedSavedGameTransfer.Prepared imported)throws IOException,InterruptedException {
        return replaceExitedSavedOnce(request,actual,Objects.requireNonNull(imported));
    }
    private ReplacementResult replaceExitedSavedOnce(ReplacementRequest request,ExitedGeneration actual,
            ImportedSavedGameTransfer.Prepared imported)throws IOException,InterruptedException {
        Objects.requireNonNull(request);Objects.requireNonNull(actual);String id=request.parentLifecycleIntentId();
        if(replacementRequests.containsKey(id)) {
            if(!replacementRequests.get(id).equals(request)||exitedReplacementSources.get(id)!=actual)
                return new ReplacementUnknown(id,"original exited replacement changed its exact body/source role; query only");
            return queryReplacement(id);
        }
        if(replacementRequests.size()>=4096)return new ReplacementRejected("Replacement retention is full");
        NativeLaunchPlan plan=request.savedPlan();
        if(request.requireRunning()||!request.expectedOld().equals(actual.generation()))
            return new ReplacementRejected("exited replacement needs its exact source-proven old generation");
        requireExitedSource(actual,actual.template,plan.deadline());
        NativeLaunchPlan.SavedGame save=(NativeLaunchPlan.SavedGame)plan.load();
        var exactPlan=actual.template.savedReplacement(id,save.save(),plan.deadline());
        if(!NativeLaunchPlanCodec.describe(exactPlan).equals(NativeLaunchPlanCodec.describe(plan)))
            return new ReplacementRejected("exited replacement changed its original exact Saved child producer");
        if(imported!=null) imported.requireCurrent(id,actual.generation(),plan);
        Path claim=plan.stateDirectory().resolve("control/"+plan.requestId()+"-parent.json");
        // Business workers are disposable. A new request ID or new lifecycle object cannot redispatch this old generation.
        String generationKey=actual.machineId()+":"+actual.generation().pid()+":"+actual.generation().creationFiletime().value();
        Path generationClaim=plan.stateDirectory().resolve("control/exited-generation-"+replacementRequestId(generationKey)+".json");
        try(Win32Host.Mutex mutex=Win32Host.mutex(MUTEX,plan.deadline())) {
            mutex.requireHeld();requireExitedSource(actual,actual.template,plan.deadline());
            if(Files.exists(claim)||Files.exists(generationClaim))return new ReplacementUnknown(id,"persistent exited-generation replacement already entered; no replay/adoption");
            NativeLaunchPolicy.requireCurrent(plan);
            var entered=exitedReplacementControl(id,"EXITED_SOURCE_ACCEPTED_SAVED_LAUNCH_ENTERED",
                    actual,save.save(),null,imported);
            atomic(generationClaim,entered,true);atomic(claim,entered,true);
            replacementRequests.put(id,request);exitedReplacementSources.put(id,actual);
            replacements.put(id,new ReplacementUnknown(id,"original exited replacement entered; query only"));
            try {
                // Attachments own only their old pipe/query handle. The supervisor already closed its original Job.
                if(currentSession!=null&&currentSession.mode()==ManagedGameSession.Mode.ATTACHED)currentSession.close();
                LaunchResult result=imported==null?launchSaved(plan):launchSaved(plan,imported::releaseBeforeCreate);
                if(!(result instanceof Started started)) {
                    replacements.put(id,new ReplacementUnknown(id,"exited original retained; Saved child not proven: "+result));
                    return queryReplacement(id);
                }
                captureStartedOwner(started); // before any post-Started replacement publication
                if(started.session().generation().equals(actual.generation()))throw new IOException("exited replacement did not create a different measured Game birth");
                if (imported!=null) imported.requireLoadedFile();
                var accepted=exitedReplacementControl(id,"EXITED_SOURCE_NEW_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED",
                        actual,save.save(),started.launchEvidence(),imported);
                atomic(generationClaim,accepted,false);atomic(claim,accepted,false);
                var replaced=new Replaced(actual.generation(),started,LifecycleEvidence.exact(ControlBuild.FileRef.measure(claim)),
                        Optional.ofNullable(imported).map(ImportedSavedGameTransfer.Prepared::transfer));
                replacements.put(id,replaced);return replaced;
            }catch(IOException|RuntimeException failure) {
                replacements.put(id,new ReplacementUnknown(id,"exited Saved replacement UNKNOWN: "+failure));return queryReplacement(id);
            }
        }
    }
    private static ControlRecord exitedReplacementControl(String id,String phase,ExitedGeneration actual,
            ControlBuild.FileRef staged,ExactRef launch,ImportedSavedGameTransfer.Prepared imported) {
        long pid=actual.generation().pid();
        String birth=actual.generation().creationFiletime().value().toString();
        return imported==null
                ?new ReplacementControl("xar.java-game-replacement/v1",id,phase,pid,birth,staged,actual.evidence(),launch)
                :new ImportedReplacementControl(RestoreCheckpointService.IMPORTED_REPLACEMENT_SCHEMA,id,phase,pid,birth,
                        staged,actual.evidence(),launch,imported.transfer().proof());
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
                captureStartedOwner(started); // before any post-Started replacement publication
                if(started.session().generation().equals(request.expectedOld()))throw new IOException("Replacement did not create a different measured generation");
                atomic(claim,new ReplacementControl("xar.java-game-replacement/v1",id,"NATIVE_HELLO_ACCEPTED_MAP_NOT_YET_VERIFIED",request.expectedOld().pid(),request.expectedOld().creationFiletime().value().toString(),save.save(),stopped.evidence(),started.launchEvidence()),false);
                Replaced replaced=new Replaced(request.expectedOld(),started,LifecycleEvidence.exact(ControlBuild.FileRef.measure(claim)));replacements.put(id,replaced);return replaced;
            }catch(IOException|RuntimeException failure){ReplacementUnknown unknown=new ReplacementUnknown(id,"Stop/create replacement UNKNOWN: "+failure);replacements.put(id,unknown);return unknown;}
        }
    }
    private LaunchResult launch(NativeLaunchPlan plan)throws IOException,InterruptedException{
        return launch(plan,null);
    }
    private LaunchResult launch(NativeLaunchPlan plan,ControlBuild.FileRef currentAuthorization)throws IOException,InterruptedException{
        return launch(plan,currentAuthorization,null);
    }
    private LaunchResult launch(NativeLaunchPlan plan,ControlBuild.FileRef currentAuthorization,SavedCreateHandoff handoff)throws IOException,InterruptedException{
        Objects.requireNonNull(plan);
        NativeLaunchPlanCodec.Configuration body=NativeLaunchPlanCodec.describe(plan),previous=launchRequests.get(plan.requestId());
        if(previous!=null){
            if(!previous.equals(body)||!Objects.equals(launchModes.get(plan.requestId()),currentAuthorization))
                return new Unknown(plan.requestId(),"Original launch ID changed its configuration or Steam admission mode; no replay",null);
            return results.getOrDefault(plan.requestId(),new Unknown(plan.requestId(),"Original launch entered without a retained terminal; query only",null));
        }
        if(launchRequests.size()>=4096)return new Rejected("Original once-only request retention is full");
        NativeLaunchPolicy.requireCurrent(plan);
        launchRequests.put(plan.requestId(),body);
        launchModes.put(plan.requestId(),currentAuthorization);
        Win32Host.deadline(plan.deadline());
        Path control=plan.stateDirectory().resolve("control");Files.createDirectories(control);
        String key=plan.sources().review().machineId()+"|"+Path.of(plan.sources().review().gameExecutable().path()).toRealPath();
        String nonce=UUID.randomUUID().toString();
        boolean entered=false,registered=false;
        LifecycleEvidence evidence=new LifecycleEvidence(plan);ExactRef last=null;
        WindowsJobProcess process=null;SteamOfflineProbe.QualifiedOffline offline=null;
        CurrentSteamLaunch.QualifiedCurrent currentSteam=null;
        AtomicReference<WindowsPreloadCustody.Lease> lease=new AtomicReference<>();
        AtomicReference<NativePipeEndpoint> endpoint=new AtomicReference<>();
        AtomicReference<NativePipeEndpoint.Config> endpointConfig=new AtomicReference<>();
        AtomicReference<NativeProcessGuard> endpointGuard=new AtomicReference<>();
        NativeGameTransport transport=null;
        try(Win32Host.Mutex ignored=Win32Host.mutex(MUTEX,plan.deadline())){
            ignored.requireHeld();
            ReleasedLaunchFailure.requireFresh(control,plan.requestId());
            if(ACTIVE.putIfAbsent(key,plan.requestId())!=null)return reject(plan,"Another original Java lifecycle owns this machine/Game");
            registered=true;
            if(Files.exists(claimPath(plan)))return reject(plan,"Persistent request claim already exists; no replay/adoption");
            Files.createDirectory(plan.evidenceRoot());
            writeClaim(plan,nonce,ClaimState.RESERVED,null,true);
            last=evidence.write(LifecycleEvidence.Event.INTENT,null,null,null,null,"Configured Java Game launch requested");
            if(currentAuthorization==null)offline=SteamOfflineProbe.observe(plan.steam(),plan.evidenceRoot().resolve("steam-offline.json"));
            else currentSteam=CurrentSteamLaunch.observe(plan,currentAuthorization);
            if(!inventory(plan,evidence,"BEFORE_CREATE").isEmpty())throw new IOException("Qualified running CK3 appeared after preflight");
            if(currentSteam==null)offline.consumeBeforeGameCreate();
            else currentSteam.consumeBeforeGameCreate();
            prepareNoModsProfile(plan.preparedProfile(),plan.profileDirectory());
            if (plan.load() instanceof NativeLaunchPlan.SavedGame saved) {
                NativeSavedGameFiles.materialize(plan.profileDirectory(), saved);
            }
            if(handoff!=null)handoff.verifyAndRelease();
            writeMarker(plan,nonce,null);
            writeClaim(plan,nonce,ClaimState.CREATE_ENTERED,null,false);
            entered=true; // Every failure after entering original CREATE remains UNKNOWN and is never replayed.
            Map<String,String> environment=gameEnvironment(plan.environment(),plan.pipeName());
            WindowsJobProcess.CommandSpec command=new WindowsJobProcess.CommandSpec(Path.of(plan.sources().review().gameExecutable().path()),plan.gameArguments(),
                    Path.of(plan.sources().review().gameExecutable().path()).getParent(),environment,plan.evidenceRoot().resolve("game.stdout"),plan.evidenceRoot().resolve("game.stderr"),plan.gameMemoryBytes());
            WindowsJobProcess.ConsoleMode display=plan.windowPolicy()==NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE
                    ?WindowsJobProcess.ConsoleMode.GUI_MINIMIZED_NO_ACTIVATE:WindowsJobProcess.ConsoleMode.GUI_SHOWN_NO_ACTIVATE;
            process=WindowsJobProcess.startBefore(command,display,plan.deadline(),suspended->{
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
            transport=operationTimeout.isPresent()
                    ?new NativeGameTransport(endpoint.get(),transportLimits.maximumFramesPerOperation(),transportLimits.maximumSubmissions(),privateActions,operationTimeout.get())
                    :new NativeGameTransport(endpoint.get(),transportLimits.maximumFramesPerOperation(),transportLimits.maximumSubmissions(),privateActions);
            Instant helloDeadline=min(plan.deadline(),Instant.now().plus(plan.startupTimeout()));
            Path firstPacket=plan.evidenceRoot().resolve("native-first.packet");
            try {
                transport.awaitHello(helloDeadline,raw->Files.write(firstPacket,raw,StandardOpenOption.CREATE_NEW));
            } catch(IOException failure) {
                try {
                    ControlBuild.FileRef packet=Files.isRegularFile(firstPacket)?ControlBuild.FileRef.measure(firstPacket):null;
                    last=evidence.writeHelloRejection(process.identity(),packet,plan,failure.toString());
                } catch(IOException diagnostic) {failure.addSuppressed(diagnostic);}
                throw failure;
            }
            held.observeLoaded();
            Path hello=plan.evidenceRoot().resolve("native-hello.packet");Files.write(hello,transport.lastOriginalPacket(),StandardOpenOption.CREATE_NEW);
            last=evidence.write(LifecycleEvidence.Event.HELLO,process.identity(),process.accounting(),null,null,"Original Native hello/actual kernel peer/connection generation accepted; loaded DLL matches continuous pre-load FileID");
            ManagedGameSession session=currentSteam==null
                    ?new ManagedGameSession(plan,process,held,offline,transport,evidence,this,endpointConfig.get(),endpointGuard.get())
                    :new ManagedGameSession(plan,process,held,currentSteam,transport,evidence,this,endpointConfig.get(),endpointGuard.get());
            session.verify();
            Tracking record=new Tracking("xar.java-game-tracking/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,process.identity(),session.command(),"KILL_ON_JOB_CLOSE|JOB_MEMORY; exact retained process/thread and DLL lease");
            Path track=control.resolve("java-game.json");atomic(track,record,false);
            tracking.put(session,new TrackingState(plan,nonce,key,track));
            writeClaim(plan,nonce,ClaimState.STARTED,process.identity(),false);
            ExactRef actualHello=LifecycleEvidence.exact(ControlBuild.FileRef.measure(hello));
            // Activation failure is still CREATE_UNKNOWN, never an already returned Started.
            currentSession=session;session.activateRuntime();
            Started started=new Started(session,actualHello,last);results.put(plan.requestId(),started);
            return started;
        }catch(IOException|RuntimeException failure){
            if(!entered){
                if(offline!=null)try{offline.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
                if(currentSteam!=null)try{currentSteam.close();}catch(IOException cleanup){failure.addSuppressed(cleanup);}
                return reject(plan,failure.toString());
            }
            WindowsJobProcess.ProcessIdentity failedIdentity=process!=null?process.identity():null;
            ExactRef cleanup=cleanupUnknown(process,endpoint.get(),lease.get(),offline,currentSteam,evidence,failure);
            if(cleanup!=null)last=cleanup;
            writeClaim(plan,nonce,ClaimState.UNKNOWN,failedIdentity,false);
            Unknown unknown=new Unknown(plan.requestId(),failure.toString(),last);results.put(plan.requestId(),unknown);return unknown;
        }catch(InterruptedException interrupted){
            ExactRef cleanup=cleanupUnknown(process,endpoint.get(),lease.get(),offline,currentSteam,evidence,interrupted);
            if(cleanup!=null)last=cleanup;
            if(entered){Unknown unknown=new Unknown(plan.requestId(),"Interrupted after original CREATE; no replay",last);results.put(plan.requestId(),unknown);}
            Thread.currentThread().interrupt();throw interrupted;
        }finally{
            if(registered&&!entered)ACTIVE.remove(key,plan.requestId());
        }
    }
    private static ExactRef cleanupUnknown(WindowsJobProcess process,NativePipeEndpoint endpoint,WindowsPreloadCustody.Lease custody,
            SteamOfflineProbe.QualifiedOffline offline,CurrentSteamLaunch.QualifiedCurrent currentSteam,LifecycleEvidence evidence,Exception original){
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
        if(currentSteam!=null)try{currentSteam.close();}catch(IOException|RuntimeException error){original.addSuppressed(error);}
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
        if(profile.settingsSeed().isPresent())prepareSettingsSeed(profile.settingsSeed().orElseThrow(),profileDirectory);
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

    /** Copies only an explicitly declared settings original into this launch's isolated profile. */
    private static void prepareSettingsSeed(ControlBuild.FileRef seed,Path profileDirectory)throws IOException{
        Path source=Path.of(seed.path()),target=profileDirectory.resolve("pdx_settings.txt");
        SharedSourceFiles.plainAncestors(source);SharedSourceFiles.plainAncestors(target);
        var original=SharedSourceFiles.observe(source);
        if(!Path.of(original.source().path()).equals(source)||original.source().bytes()!=seed.bytes()
                ||!original.source().sha256().equals(seed.sha256()))
            throw new IOException("Declared pdx_settings seed changed before profile preparation");
        byte[] complete;
        try(var input=Files.newInputStream(source)){complete=input.readNBytes((1<<20)+1);}
        if(complete.length!=seed.bytes()||complete.length==0||complete.length>(1<<20)
                ||!java.util.HexFormat.of().formatHex(sha256(complete)).equals(seed.sha256()))
            throw new IOException("Bounded exact pdx_settings seed required");
        SharedSourceFiles.assertUnchanged(original);
        if(Files.exists(target,java.nio.file.LinkOption.NOFOLLOW_LINKS)){
            var existing=SharedSourceFiles.observe(target);
            if(existing.source().bytes()!=seed.bytes()||!existing.source().sha256().equals(seed.sha256()))
                throw new IOException("Conflicting isolated pdx_settings.txt already exists");
            SharedSourceFiles.assertUnchanged(original);SharedSourceFiles.assertUnchanged(existing);return;
        }
        Files.createDirectories(profileDirectory);SharedSourceFiles.plainAncestors(profileDirectory);
        Path pending=Files.createTempFile(profileDirectory,"xar-settings-",".pending");
        try{
            try(FileChannel output=FileChannel.open(pending,StandardOpenOption.WRITE)){
                java.nio.ByteBuffer bytes=java.nio.ByteBuffer.wrap(complete);
                while(bytes.hasRemaining())output.write(bytes);output.force(true);
            }
            var staged=ControlBuild.FileRef.measure(pending);
            if(staged.bytes()!=seed.bytes()||!staged.sha256().equals(seed.sha256()))
                throw new IOException("Staged pdx_settings seed differs from declared original");
            SharedSourceFiles.assertUnchanged(original);
            Files.move(pending,target);
            var created=SharedSourceFiles.observe(target);
            if(created.source().bytes()!=seed.bytes()||!created.source().sha256().equals(seed.sha256()))
                throw new IOException("Created pdx_settings seed differs from declared original");
            SharedSourceFiles.assertUnchanged(original);
        }finally{Files.deleteIfExists(pending);}
    }
    private static byte[] sha256(byte[] bytes){
        try{return java.security.MessageDigest.getInstance("SHA-256").digest(bytes);}
        catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
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
        try(WindowsJobProcess original=WindowsJobProcess.startBefore(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,plan.deadline())){
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
        Files.deleteIfExists(markerPath(state.plan()));
        ACTIVE.remove(state.registryKey(),state.plan().requestId());tracking.remove(session);
    }
    static void releaseRetiredRegistry(String machine,WindowsJobProcess.ProcessIdentity game,String requestId)throws IOException{
        String key=machine+"|"+Path.of(game.executable()).toRealPath();
        String held=ACTIVE.get(key);
        if(held!=null&&!held.equals(requestId))throw new IOException("Another launch owns this machine/Game registry");
        ACTIVE.remove(key,requestId);
    }
    private static Path markerPath(NativeLaunchPlan plan){return plan.stateDirectory().resolve("control/unsafe-cleanup-"+plan.requestId()+".json");}
    private static Path claimPath(NativeLaunchPlan plan){return plan.stateDirectory().resolve("control/request-"+plan.requestId()+".json");}
    private static void writeClaim(NativeLaunchPlan plan,String nonce,ClaimState state,WindowsJobProcess.ProcessIdentity game,boolean fresh)throws IOException{
        atomic(claimPath(plan),new Claim("xar.java-game-launch-claim/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,state,game,Instant.now().toString()),fresh);
    }
    private static void writeMarker(NativeLaunchPlan plan,String nonce,WindowsJobProcess.ProcessIdentity game)throws IOException{
        atomic(markerPath(plan),new Claim("xar.java-game-unsafe/v1",plan.sources().review().machineId(),plan.requestId(),plan.sessionId(),nonce,ClaimState.CREATE_ENTERED,game,Instant.now().toString()),false);
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

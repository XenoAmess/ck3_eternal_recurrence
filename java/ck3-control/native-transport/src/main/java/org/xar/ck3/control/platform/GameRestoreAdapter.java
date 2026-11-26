package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;

/** Checkpoint consumer of the one physical replacement producer; no second stop/create state machine. */
public final class GameRestoreAdapter implements RestoreCheckpointService.LifecyclePort {
    private final JavaGameLifecycle lifecycle;
    private final NativeLaunchPlan template;
    private final Optional<JavaGameLifecycle.ExitedGeneration> exitedSource;
    private final Optional<RootProcessAttach.LoadedReplacement> loadedReplacement;
    private final CheckpointFiles files;
    private final Optional<ImportedStart> importedStart;

    private record ImportedStart(Clock clock,JavaGameLifecycle.ImportedStartedPublication ownerPublication) {
        ImportedStart { Objects.requireNonNull(clock); Objects.requireNonNull(ownerPublication); }
    }
    public GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate){
        this(lifecycle,reviewedTemplate,Optional.empty(),Optional.empty(),new NativeCheckpointFiles(),Optional.empty());
    }
    public GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate,JavaGameLifecycle.ExitedGeneration actualExitedSource){
        this(lifecycle,reviewedTemplate,Optional.of(actualExitedSource),Optional.empty(),new NativeCheckpointFiles(),Optional.empty());
    }
    public GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate,RootProcessAttach.LoadedReplacement actualLoadedReplacement){
        this(lifecycle,reviewedTemplate,Optional.empty(),Optional.of(actualLoadedReplacement),new NativeCheckpointFiles(),Optional.empty());
    }
    public static GameRestoreAdapter importedExited(JavaGameLifecycle lifecycle,NativeLaunchPlan template,
            JavaGameLifecycle.ExitedGeneration exited,CheckpointFiles admittedFiles,Clock clock,
            JavaGameLifecycle.ImportedStartedPublication ownerPublication) {
        return new GameRestoreAdapter(lifecycle,template,Optional.of(exited),Optional.empty(),admittedFiles,
                Optional.of(new ImportedStart(clock,ownerPublication)));
    }
    private GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan template,Optional<JavaGameLifecycle.ExitedGeneration> exited,
            Optional<RootProcessAttach.LoadedReplacement> loaded,CheckpointFiles files,Optional<ImportedStart> importedStart) {
        this.lifecycle=Objects.requireNonNull(lifecycle);
        this.template=Objects.requireNonNull(template);
        this.exitedSource=exited;
        this.loadedReplacement=loaded;
        this.files=Objects.requireNonNull(files);
        this.importedStart=importedStart;
    }
    @Override public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request)throws IOException,InterruptedException{
        if(loadedReplacement.isPresent())throw new IOException("existing loaded replacement is query-only; CREATE and STOP are unavailable");
        Objects.requireNonNull(request);Win32Host.deadline(request.deadline());
        files.verify(request.pair());template.sources().verify();
        JavaGameLifecycle.ReplacementResult result;
        if(exitedSource.isPresent()) {
            var actual=exitedSource.orElseThrow();lifecycle.requireExitedSource(actual,template,request.deadline());
            if(!actual.generation().equals(request.current().observed().game())
                    ||!actual.sourceSessionId().equals(request.current().sessionId()))
                throw new IOException("checkpoint restoration changed its actual exited source session or Game birth");
            if(importedStart.isPresent()) {
                var start=importedStart.orElseThrow();
                if(!(request.savedMaterial() instanceof SavedAttachmentSourceStore.SavedMaterial material)
                        ||material.importedOrigin().filter(origin -> origin.owner().game().equals(actual.generation())
                            && origin.owner().machineId().equals(actual.machineId())
                            && origin.owner().sessionId().equals(actual.sourceSessionId())).isEmpty())
                    throw new IOException("Imported lifecycle needs its exact private v5 material and departed owner");
                try(var imported=ImportedSavedGameTransfer.prepare(template,request.requestId(),actual.generation(),
                        request.pair().save(),files,request.deadline(),start.clock())) {
                    result=lifecycle.replaceImportedExitedSavedOnce(replacement(request,imported.child()),actual,imported,
                            start.ownerPublication());
                }
            } else result=lifecycle.replaceExitedSavedOnce(replacement(request,replacementPlan(request)),actual);
        } else result=lifecycle.replaceSavedOnce(replacement(request,replacementPlan(request)));
        if(result instanceof JavaGameLifecycle.Replaced replaced) return acknowledge(request.requestId(),replaced);
        if(result instanceof JavaGameLifecycle.ReplacementRejected rejected)return new RestoreCheckpointService.LaunchRejected(rejected.reason());
        return new RestoreCheckpointService.LaunchUnknown(result.toString());
    }
    @Override public RestoreCheckpointService.LaunchResult query(String requestId,Instant deadline)throws IOException{
        Win32Host.deadline(deadline);
        if(loadedReplacement.isPresent()){
            var actual=loadedReplacement.orElseThrow();
            if(!actual.originalParentId().equals(requestId))throw new IOException("loaded replacement query changed its original parent identity");
            var ack=actual.cachedAck();actual.requireAck(ack,deadline);return ack;
        }
        JavaGameLifecycle.ReplacementResult result=lifecycle.queryReplacement(requestId);
        if(result instanceof JavaGameLifecycle.Replaced replaced){
            ExactRef proof=replaced.lifecycleEvidence();new ControlBuild.FileRef(proof.path(),proof.bytes(),proof.sha256()).verify();
            return acknowledge(requestId,replaced);
        }
        if(result instanceof JavaGameLifecycle.ReplacementRejected rejected)return new RestoreCheckpointService.LaunchRejected(rejected.reason());
        return new RestoreCheckpointService.LaunchUnknown(result.toString());
    }
    private RestoreCheckpointService.ReplacementAck acknowledge(String requestId,JavaGameLifecycle.Replaced actual) throws IOException {
        var replacement=actual.replacement().session();
        var load=(NativeLaunchPlan.SavedGame)replacement.launchPlan().load();
        if(importedStart.isPresent()!=actual.importedSaveTransfer().isPresent())
            throw new IOException("Replacement result crossed the original imported or legacy load role");
        return new RestoreCheckpointService.ReplacementAck(requestId,actual.previous(),replacement.generation(),
                LifecycleEvidence.exact(load.save()),actual.lifecycleEvidence(),actual.importedSaveTransfer());
    }
    private JavaGameLifecycle.ReplacementRequest replacement(RestoreCheckpointService.Request request,NativeLaunchPlan child) {
        return new JavaGameLifecycle.ReplacementRequest(request.requestId(),request.current().observed().game(),child,exitedSource.isEmpty());
    }
    private NativeLaunchPlan replacementPlan(RestoreCheckpointService.Request request)throws IOException{
        ExactRef raw=request.pair().save().reference();
        return template.savedReplacement(request.requestId(),new ControlBuild.FileRef(raw.path(),raw.bytes(),raw.sha256()),request.deadline());
    }
}

package org.xar.ck3.control.platform;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Objects;
import java.util.UUID;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;

/** Checkpoint consumer of the one physical replacement producer; no second stop/create state machine. */
public final class GameRestoreAdapter implements RestoreCheckpointService.LifecyclePort {
    private final JavaGameLifecycle lifecycle;
    private final NativeLaunchPlan template;
    private final java.util.Optional<JavaGameLifecycle.ExitedGeneration> exitedSource;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    public GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate){
        this.lifecycle=Objects.requireNonNull(lifecycle);this.template=Objects.requireNonNull(reviewedTemplate);this.exitedSource=java.util.Optional.empty();
    }
    public GameRestoreAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate,JavaGameLifecycle.ExitedGeneration actualExitedSource){
        this.lifecycle=Objects.requireNonNull(lifecycle);this.template=Objects.requireNonNull(reviewedTemplate);
        this.exitedSource=java.util.Optional.of(Objects.requireNonNull(actualExitedSource));
    }
    @Override public RestoreCheckpointService.LaunchResult replaceOnce(RestoreCheckpointService.Request request)throws IOException,InterruptedException{
        Objects.requireNonNull(request);Win32Host.deadline(request.deadline());
        files.verify(request.pair());template.sources().verify();
        var replacement=new JavaGameLifecycle.ReplacementRequest(request.requestId(),request.current().observed().game(),
                replacementPlan(request),exitedSource.isEmpty());
        JavaGameLifecycle.ReplacementResult result;
        if(exitedSource.isPresent()) {
            var actual=exitedSource.orElseThrow();lifecycle.requireExitedSource(actual,template,request.deadline());
            if(!actual.generation().equals(request.current().observed().game())
                    ||!actual.sourceSessionId().equals(request.current().sessionId()))
                throw new IOException("checkpoint restoration changed its actual exited source session or Game birth");
            result=lifecycle.replaceExitedSavedOnce(replacement,actual);
        } else result=lifecycle.replaceSavedOnce(replacement);
        if(result instanceof JavaGameLifecycle.Replaced replaced)return new RestoreCheckpointService.ReplacementAck(request.requestId(),
                replaced.previous(),replaced.replacement().session().generation(),request.pair().save().reference(),replaced.lifecycleEvidence());
        if(result instanceof JavaGameLifecycle.ReplacementRejected rejected)return new RestoreCheckpointService.LaunchRejected(rejected.reason());
        return new RestoreCheckpointService.LaunchUnknown(result.toString());
    }
    @Override public RestoreCheckpointService.LaunchResult query(String requestId,Instant deadline)throws IOException{
        Win32Host.deadline(deadline);
        JavaGameLifecycle.ReplacementResult result=lifecycle.queryReplacement(requestId);
        if(result instanceof JavaGameLifecycle.Replaced replaced){
            ExactRef proof=replaced.lifecycleEvidence();new ControlBuild.FileRef(proof.path(),proof.bytes(),proof.sha256()).verify();
            NativeLaunchPlan.SavedGame source=(NativeLaunchPlan.SavedGame)replaced.replacement().session().launchPlan().load();
            return new RestoreCheckpointService.ReplacementAck(requestId,replaced.previous(),replaced.replacement().session().generation(),
                    LifecycleEvidence.exact(source.save()),proof);
        }
        if(result instanceof JavaGameLifecycle.ReplacementRejected rejected)return new RestoreCheckpointService.LaunchRejected(rejected.reason());
        return new RestoreCheckpointService.LaunchUnknown(result.toString());
    }
    private NativeLaunchPlan replacementPlan(RestoreCheckpointService.Request request)throws IOException{
        ExactRef raw=request.pair().save().reference();
        return template.savedReplacement(request.requestId(),new ControlBuild.FileRef(raw.path(),raw.bytes(),raw.sha256()),request.deadline());
    }
}

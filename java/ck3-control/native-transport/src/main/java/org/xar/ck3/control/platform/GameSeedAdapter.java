package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;

/** Immutable seed consumer of the same physical replacement producer, never a second creator or writer. */
public final class GameSeedAdapter implements LifecycleComposites.SeedLifecyclePort {
    private final JavaGameLifecycle lifecycle;
    private final NativeLaunchPlan template;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private final Map<GameGeneration,LifecycleComposites.SeedStarted> minted=new ConcurrentHashMap<>();
    private final Map<String,LifecycleComposites.SeedLaunch> requests=new ConcurrentHashMap<>();
    public GameSeedAdapter(JavaGameLifecycle lifecycle,NativeLaunchPlan reviewedTemplate){this.lifecycle=Objects.requireNonNull(lifecycle);this.template=Objects.requireNonNull(reviewedTemplate);}
    @Override public synchronized LifecycleComposites.SeedReplacement replaceOnce(LifecycleComposites.SeedLaunch request)throws IOException,InterruptedException{
        var prior=requests.get(request.parentLifecycleIntentId());
        if(prior!=null)return prior.equals(request)?query(request.parentLifecycleIntentId(),request.deadline()):new LifecycleComposites.SeedUnknown("Seed parent body changed; no replay");
        if(requests.size()>=4096)return new LifecycleComposites.SeedRejected("Seed receipt retention is full");
        Win32Host.deadline(request.deadline());request.seed().requireCurrent(files);requireOriginal(request.oldGame());
        var save=request.seed().save().reference();
        NativeLaunchPlan plan=template.savedReplacement(request.parentLifecycleIntentId(),new ControlBuild.FileRef(save.path(),save.bytes(),save.sha256()),request.deadline());
        requests.put(request.parentLifecycleIntentId(),request);
        return translate(lifecycle.replaceSavedOnce(new JavaGameLifecycle.ReplacementRequest(request.parentLifecycleIntentId(),request.oldGame(),plan,false)),request);
    }
    @Override public LifecycleComposites.SeedReplacement query(String parentLifecycleIntentId,Instant deadline)throws IOException{
        Win32Host.deadline(deadline);var request=requests.get(parentLifecycleIntentId);
        return request==null?new LifecycleComposites.SeedUnknown("No original seed request retained; query cannot adopt another replacement"):translate(lifecycle.queryReplacement(parentLifecycleIntentId),request);
    }
    private LifecycleComposites.SeedReplacement translate(JavaGameLifecycle.ReplacementResult result,LifecycleComposites.SeedLaunch request)throws IOException{
        if(result instanceof JavaGameLifecycle.Replaced replaced){
            var started=replaced.replacement();var session=started.session();var proof=replaced.lifecycleEvidence();new ControlBuild.FileRef(proof.path(),proof.bytes(),proof.sha256()).verify();
            request.seed().requireCurrent(files);
            if(!(session.launchPlan().load() instanceof NativeLaunchPlan.SavedGame save)||!LifecycleEvidence.exact(save.save()).equals(request.seed().save().reference())||!replaced.previous().equals(request.oldGame()))throw new IOException("Replacement is not this original seed request");
            var actual=new LifecycleComposites.SeedStarted(replaced.previous(),session.generation(),session.launchPlan().pipeName(),session.sessionId(),started.launchEvidence(),started.nativeHello(),proof);
            minted.putIfAbsent(session.generation(),actual);return actual;
        }
        if(result instanceof JavaGameLifecycle.ReplacementRejected rejected)return new LifecycleComposites.SeedRejected(rejected.reason());
        return new LifecycleComposites.SeedUnknown(result.toString());
    }
    @Override public void requireOriginal(GameGeneration expected)throws IOException{
        var session=lifecycle.currentSession().orElseThrow(()->new IOException("No original managed Game retained"));
        if(!session.generation().equals(expected))throw new IOException("Seed transition belongs to a different original Game");
        GameLifecycle.Observation observation=session.inspect(expected,Instant.now().plusSeconds(5));
        if(observation instanceof GameLifecycle.Unavailable unavailable)throw new IOException("Original Game identity/terminal is unavailable: "+unavailable.reason());
    }
    @Override public void requireCurrent(LifecycleComposites.SeedStarted actual)throws IOException{
        if(!actual.equals(minted.get(actual.newGame())))throw new IOException("No same-producer seed replacement receipt retained");
        var session=lifecycle.currentSession().orElseThrow(()->new IOException("No replacement managed Game retained"));
        if(!session.generation().equals(actual.newGame())||!session.sessionId().equals(actual.sessionId())||!session.launchPlan().pipeName().equals(actual.pipeName()))throw new IOException("Replacement generation/session/pipe changed");
        session.verify();
    }
    @Override public NativeObservationPort.ObservedFrame observe(LifecycleComposites.SeedStarted actual,Instant deadline)throws IOException,InterruptedException{
        requireCurrent(actual);return lifecycle.currentSession().orElseThrow(()->new IOException("Original replacement disappeared")).nativeTransport().observe(deadline);
    }
}

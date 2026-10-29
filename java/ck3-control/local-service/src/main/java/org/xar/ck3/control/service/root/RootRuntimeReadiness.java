package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.RestoreBinding;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** One capability observer and one ordinary collector per actual installed physical runtime.
 * Initial and restored startup use this identical construction path after their respective actual admissions. */
public final class RootRuntimeReadiness {
    private sealed interface Admission permits InitialAdmission,RestoredAdmission,NextAdmission,ColdAdmission { }
    private record InitialAdmission(RootApplicationAssembly.Staged stage) implements Admission {
        private InitialAdmission {Objects.requireNonNull(stage);}
    }
    private record RestoredAdmission(RestoreBinding binding) implements Admission {
        private RestoredAdmission {Objects.requireNonNull(binding);}
    }
    private record ColdAdmission(RootApplicationAssembly.Staged stage,RootPrivateBootstrap.Original original) implements Admission {
        private ColdAdmission {Objects.requireNonNull(stage);Objects.requireNonNull(original);}
    }
    private record NextAdmission(RootApplicationAssembly.NextEpisodeStage next,RootApplicationAssembly.Staged stage,
            RootNextEpisodeWindowRuntime.Baselined baseline) implements Admission {
        private NextAdmission {Objects.requireNonNull(next);Objects.requireNonNull(stage);Objects.requireNonNull(baseline);}
    }
    private static final class Attempt {
        final RootInstalledCatalog installed;
        final DriverBootstrap.Adopted adopted;
        final Admission admission;
        final RetainedRuntimeCreation<RootRestoreAdapters.RestoredRuntime> creation=new RetainedRuntimeCreation<>();
        Attempt(RootInstalledCatalog installed,DriverBootstrap.Adopted adopted,Admission admission){
            this.installed=installed;this.adopted=adopted;this.admission=admission;
        }
    }
    private final RootApplicationAssembly.Core core;
    private final NativeReadiness.Policy policy;
    private final Duration freshness;
    private final Clock clock;
    private final Map<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();

    public RootRuntimeReadiness(RootApplicationAssembly.Core core,NativeReadiness.Policy policy,Duration freshness,Clock clock){
        this.core=Objects.requireNonNull(core);this.policy=Objects.requireNonNull(policy);
        this.freshness=Objects.requireNonNull(freshness);this.clock=Objects.requireNonNull(clock);
        StrictJson.require(core.archive().writer()==core.writer(),"readiness retains the same original writer/archive");
        StrictJson.require(!freshness.isZero()&&!freshness.isNegative()&&freshness.compareTo(Duration.ofMinutes(1))<=0,
                "finite actual ordinary readiness freshness required");
    }

    public synchronized RootRestoreAdapters.RestoredRuntime initial(ContinuityStorePort.Session same,
            RootInstalledCatalog installed,RootApplicationAssembly.Staged staged,Instant deadline)throws IOException{
        Objects.requireNonNull(staged);
        var adopted=staged.driver();
        requireOwner(same,installed,adopted,deadline);
        if(policy.expectedActor().isPresent()&&!policy.expectedActor().orElseThrow()
                .equals(adopted.first().identity().frame().identity().player()))
            throw new IOException("actual first admission differs from the configured initial actor");
        StrictJson.require(staged.planningReads()==installed.context().reads(),
                "initial stage must retain the installed physical runtime's original read coordinator");
        Attempt selected=attempt(installed,adopted,new InitialAdmission(staged));
        return selected.creation.obtain(()->construct(same,installed,adopted,selected.admission,deadline));
    }

    public synchronized RootRestoreAdapters.RestoredRuntime restored(ContinuityStorePort.Session same,
            RootInstalledCatalog installed,DriverBootstrap.Adopted adopted,RestoreBinding binding,Instant deadline)throws IOException{
        Objects.requireNonNull(binding);
        requireOwner(same,installed,adopted,deadline);
        installed.context().requireRestorationOriginal(same,binding);
        Attempt selected=attempt(installed,adopted,new RestoredAdmission(binding));
        return selected.creation.obtain(()->construct(same,installed,adopted,selected.admission,deadline));
    }
    /** Only the actual committed cold original derives its admitted actor; configured cold/stability guards remain. */
    public NativeReadiness.Policy coldPolicy(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            RootPrivateBootstrap.Original original,Instant deadline)throws IOException {
        requireOwner(same,installed,original.adopted(),deadline);original.requireCurrent(same,installed.context());
        BigInteger actor=original.adopted().first().identity().frame().identity().player();
        return new NativeReadiness.Policy(policy.coldCheckpoint(),policy.allowTerminal(),java.util.Optional.of(actor),
                policy.stableFor(),policy.requirePostReadyPump());
    }
    public synchronized RootRestoreAdapters.RestoredRuntime cold(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            RootApplicationAssembly.Staged staged,RootPrivateBootstrap.Original original,Instant deadline)throws IOException {
        Objects.requireNonNull(staged);Objects.requireNonNull(original);var adopted=original.adopted();
        requireOwner(same,installed,adopted,deadline);original.requireCurrent(same,installed.context());
        if(staged.driver()!=adopted||staged.planningReads()!=installed.context().reads())
            throw new IOException("cold readiness crossed its actual private Driver or staged read coordinator");
        Attempt selected=attempt(installed,adopted,new ColdAdmission(staged,original));
        return selected.creation.obtain(()->construct(same,installed,adopted,selected.admission,deadline));
    }

    /** A real NEXT reuses its private actual candidate/collector and requires the committed first-SAVE BASELINE.
     * It does not apply the first campaign's configured actor to a different canonical episode. */
    public synchronized RootRestoreAdapters.RestoredRuntime nextEpisode(ContinuityStorePort.Session same,
            RootInstalledCatalog installed,RootApplicationAssembly.NextEpisodeStage next,
            RootApplicationAssembly.Staged staged,RootNextEpisodeWindowRuntime.Baselined baseline,Instant deadline)throws IOException {
        Objects.requireNonNull(next);Objects.requireNonNull(staged);Objects.requireNonNull(baseline);
        var admitted=new NextAdmission(next,staged,baseline);var adopted=next.driver();
        requireOwner(same,installed,adopted,deadline);requireNextOriginal(same,installed,admitted);
        Attempt selected=attempt(installed,adopted,admitted);
        return selected.creation.obtain(()->construct(same,installed,adopted,selected.admission,deadline));
    }

    /** Pre-first-SAVE policy derives only its actor from the real privately transferred adopted Driver.
     * All cold, terminal, stability and pump requirements remain the configured policy's exact values. */
    public NativeReadiness.Policy nextCandidatePolicy(ContinuityStorePort.Session same,
            RootApplicationAssembly.NextEpisodeStage next)throws IOException {
        core.writer().requireSession(same);Objects.requireNonNull(next);next.requireCurrent(same);
        RootRuntimeContext context=next.catalog().context();var driver=next.driver();
        if(context.core()!=core||context.game()!=next.replacement()||!context.source().equals(next.source())
                ||!driver.source().equals(next.source())||!driver.session().game().equals(context.game().generation())
                ||!driver.session().sessionId().equals(context.game().sessionId())
                ||!driver.first().identity().game().equals(context.game().generation()))
            throw new IOException("first NEXT checkpoint policy lost its actual privately transferred Driver/source/Game");
        next.candidate().requireNextCandidate(same,next.original(),next.previous().driver().authority());
        BigInteger actor=driver.first().identity().frame().identity().player();
        return new NativeReadiness.Policy(policy.coldCheckpoint(),policy.allowTerminal(),java.util.Optional.of(actor),
                policy.stableFor(),policy.requirePostReadyPump());
    }

    private void requireNextOriginal(ContinuityStorePort.Session same,RootInstalledCatalog installed,NextAdmission next)throws IOException {
        core.writer().requireSession(same);core.nextEpisodeWindows().requireBaseline(same,next.baseline());
        next.next().requireRetainedOriginal(same);
        if(next.baseline().begun().stage()!=next.next()||next.next().catalog()!=installed
                ||next.stage().driver()!=next.next().driver()||next.stage().planningReads()!=installed.context().reads()
                ||next.stage().readiness()!=installed.context().collector())
            throw new IOException("ordinary NEXT readiness requires its same retained private stage, first physical pair and catalog");
        next.next().candidate().requireNextCandidate(same,next.next().original(),next.next().previous().driver().authority());
        next.next().candidate().requireOwner(next.next().driver().authority(),core.archive(),installed.bindings());
    }

    private Attempt attempt(RootInstalledCatalog installed,DriverBootstrap.Adopted adopted,Admission admission)throws IOException{
        RootRuntimeContext context=installed.context();
        Attempt previous=attempts.get(context);
        if(previous!=null){
            if(previous.installed!=installed||previous.adopted!=adopted||!previous.admission.equals(admission))
                throw new IOException("one entered physical runtime cannot replace its admission, Driver or actual catalog");
            return previous;
        }
        if(attempts.size()>=64)throw new IOException("bounded readiness construction attempts require original reconciliation");
        Attempt created=new Attempt(installed,adopted,Objects.requireNonNull(admission));
        attempts.put(context,created);return created;
    }

    private RootRestoreAdapters.RestoredRuntime construct(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            DriverBootstrap.Adopted adopted,Admission admission,Instant deadline)throws IOException{
        RootRuntimeContext context=installed.context();
        var bindings=installed.bindings();bindings.requireCompleteArchiveCoverage();
        final DriverCapabilityRuntime capabilities;
        if(admission instanceof NextAdmission next){
            requireNextOriginal(same,installed,next);capabilities=next.next().candidate();
        }else{
            capabilities=new DriverCapabilityRuntime(adopted.authority(),core.archive(),
                    ()->{try{return core.writer().borrowedSession();}catch(IOException failure){throw new UncheckedIOException(failure);}},
                    bindings,installed.capabilityFiles(),installed.retreatDomain());
            capabilities.bindCurrentOptions(installed.remainingDomains().events()::issueCurrentOptions);
        }
        NativeReadinessCollector.PlanningInputsPort planning=installed.planningInputs(adopted,capabilities);
        final NativeReadinessCollector collector;
        if(admission instanceof InitialAdmission initial)collector=initial.stage().readiness();
        else if(admission instanceof ColdAdmission cold)collector=cold.stage().readiness();
        else if(admission instanceof NextAdmission next)collector=next.stage().readiness();
        else{
            var game=context.game();
            collector=new NativeReadinessCollector(identity(context),core.writer(),game.nativeTransport(),adopted.authority(),
                    new DriverObservationAssembler(),game,
                    (borrowed,role,bytes)->core.archive().preserveArtifact(borrowed,bytes,role.maximumBytes()),
                    core.semanticVerifier(),context.sources(),capabilities,planning,policy,freshness,clock);
            collector.bindObservationSession(core.writer()::requireSession);
            collector.bindActiveObservationSession(core.writer()::activeSession);
        }
        // The callback runs inside this exact adopted authority's frozen observation, never a second Driver read.
        collector.bindAdmittedActorAuthority((borrowed,owner,frame,actualDriver,limit)->
                requireAdmittedActor(borrowed,installed,adopted,admission,owner,frame,actualDriver,limit));
        // Core.nextCheckpointStage already bound these exact products before first SAVE.
        // A strict once-bound collector must not be rebound when BASELINE later admits its actor callback.
        if(!(admission instanceof NextAdmission)){
            installed.bindReadiness(adopted,collector);
            collector.bindReadyPublication(installed.readyPublication());
            collector.bindPlanningEvidence(installed.planningEvidence());
        }
        StrictJson.require(context.collector()==collector&&context.adopted()==adopted&&context.bindings()==bindings
                &&context.reads()==installed.context().reads(),"ordinary runtime crossed its actual retained products");
        capabilities.requireOwner(adopted.authority(),core.archive(),bindings);
        requireOwner(same,installed,adopted,deadline);
        // Root.finish alone binds lifecycle-parent and same physical semantic capture to this collector.
        return new RootRestoreAdapters.RestoredRuntime(collector,capabilities,bindings,context.reads(),planning,installed);
    }

    private BigInteger requireAdmittedActor(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            DriverBootstrap.Adopted adopted,Admission admission,SessionIdentity owner,
            DriverObservationAssembler.Complete frame,DriverSnapshotFacts.Known actualDriver,Instant deadline)throws IOException{
        requireOwner(same,installed,adopted,deadline);
        RootRuntimeContext context=installed.context();
        if(!identity(context).equals(owner))throw new IOException("admitted actor callback crossed its original collector owner");
        if(admission instanceof InitialAdmission initial){
            if(initial.stage().driver()!=adopted||initial.stage().planningReads()!=context.reads())
                throw new IOException("admitted actor callback lost its actual initial stage");
        }else if(admission instanceof RestoredAdmission restored){
            context.requireRestorationOriginal(same,restored.binding());
        }else if(admission instanceof ColdAdmission cold){
            cold.original().requireOriginal(same);
            if(cold.original().context()!=context||cold.original().adopted()!=adopted||cold.stage().driver()!=adopted)
                throw new IOException("cold actor callback lost its actual retained canonical original");
        }else if(admission instanceof NextAdmission next){
            // The Core verifies either the private post-BASELINE owner or the actually published same successor.
            // Candidate-only/expired transfer predicates cannot be applied to every later ordinary observation.
            core.requireAdmittedNext(same,next.next(),next.baseline(),installed,next.next().candidate());
        }
        adopted.producer().requireSameTransport(context.transport(),context.source());
        var driver=actualDriver.driver();
        BigInteger actor=driver.session().actorId();
        if(!actualDriver.stamp().game().equals(owner.game())
                ||driver.session().bridgePid()!=owner.game().pid()
                ||!driver.session().pipeName().equals(context.transport().pipeName())
                ||!actualDriver.stamp().episodeRunId().equals(driver.session().episodeRunId())
                ||!frame.identity().game().equals(owner.game())
                ||!frame.identity().frame().episodeRunId().equals(driver.session().episodeRunId())
                ||!frame.identity().frame().identity().player().equals(actor))
            throw new IOException("admitted actor requires the same actual frozen canonical Driver and native frame");
        // The retained adopted seed is the initial/restore admission. Actor changes require its canonical new epoch.
        if(!actor.equals(adopted.first().identity().frame().identity().player())
                &&(actualDriver.stamp().episodeEpoch()<=adopted.seed().episodeEpoch()
                    ||driver.session().episodeRunId().equals(adopted.first().identity().frame().episodeRunId())))
            throw new IOException("another actor lacks an actual later canonical episode in the admitted Driver");
        return actor;
    }

    private void requireOwner(ContinuityStorePort.Session same,RootInstalledCatalog installed,
            DriverBootstrap.Adopted adopted,Instant deadline)throws IOException{
        core.writer().requireSession(same);Objects.requireNonNull(installed);Objects.requireNonNull(adopted);
        RootRuntimeContext context=installed.context();
        if(context.core()!=core||context.writer()!=core.writer()||context.archive()!=core.archive()||context.clock()!=clock
                ||!clock.instant().isBefore(Objects.requireNonNull(deadline)))
            throw new IOException("actual ordinary runtime lost its original Core/writer/archive/clock/deadline");
        context.requireCurrent(deadline);context.game().verify();
        if(context.adopted()!=adopted||!adopted.source().equals(context.source())
                ||!adopted.session().game().equals(context.game().generation())
                ||!adopted.session().sessionId().equals(context.game().sessionId()))
            throw new IOException("ordinary runtime must use the actually adopted physical Driver");
        context.game().launchPlan().sources().requireLoadedClass(RootRuntimeReadiness.class);
        context.game().launchPlan().sources().requireLoadedClass(RetainedRuntimeCreation.class);
    }

    private static SessionIdentity identity(RootRuntimeContext context){
        return new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
    }
}

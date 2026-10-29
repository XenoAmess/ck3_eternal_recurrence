package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.LifeAdvanceEvidence;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverReadHistoryPublisher;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.effects.RootActionGuard;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.OrdinaryPlanningPipeline;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.NativeFrontendAuthority;

/** Retained actual inputs for Core's unique NEXT sequence. This class sends no SAVE and publishes no Host.
 * Dispatcher products exist before BEGIN; only the genuine committed BASELINE may produce FinishInputs. */
public final class RootNextEpisodeAssemblyInputs {
    private RootNextEpisodeAssemblyInputs(){ }

    /** Startup retains the actual all-scene ports and the new physical catalog. No port has an empty/default substitute.
     * Construction is input retention, not evidence that those producers have completed their runtime admission. */
    public record SessionResources(RootApplicationAssembly.Core core,RootInstalledCatalog catalog,
            RootRuntimeCatalogFactory catalogs,RootStartupConfiguration startup,RootRuntimeDomainSettings.Bound domainSettings,
            RootRuntimeStorageGuard storage,CheckpointFiles files,RootRuntimeReadiness readiness,int retainedFrames,
            OriginalWindowReducer.Policy cyclePolicy,SessionPorts.OfflineAnalysisPort offline,SessionClock sessionClock,
            SessionPorts.EpisodeContinuation episodes,RootCheckpointVerifier.SavedCaptureFactory savedCaptureFactory,
            RootRestoreMaterialFactory restoreMaterials,RootRestoreAdapters.PostAdoptionPort restorePublication) {
        public SessionResources {
            for(Object actual:List.of(core,catalog,catalogs,startup,domainSettings,storage,files,readiness,cyclePolicy,
                    offline,sessionClock,episodes,savedCaptureFactory,restoreMaterials,restorePublication))Objects.requireNonNull(actual);
            if(retainedFrames<2||retainedFrames>4096)throw new IllegalArgumentException("actual bounded NEXT retained-frame configuration required");
        }
    }
    public record CheckpointResources(CheckpointFiles files,Path driverCheckpointPath,Path checkpointEvidence,
            Path attachmentEvidence,CheckpointService.SeedAdoptionPort seeds,String lineageId,Path savePath,Duration freshness) {
        public CheckpointResources {
            Objects.requireNonNull(files);Objects.requireNonNull(seeds);Objects.requireNonNull(freshness);
            for(Path path:List.of(driverCheckpointPath,checkpointEvidence,attachmentEvidence,savePath))absolute(path);
            if(lineageId==null||!lineageId.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}"))
                throw new IllegalArgumentException("bounded original NEXT lineage identifier required");
            if(freshness.isZero()||freshness.isNegative()||freshness.compareTo(Duration.ofMinutes(1))>0)
                throw new IllegalArgumentException("bounded actual NEXT checkpoint freshness required");
        }
    }
    public record DispatcherInputs(String authorityId,RootExecutableBindings bindings,NativeFrontendAuthority frontend,
            RootLifecycleAuthority lifecycle,RootReconciliationAuthority reconciliation,
            RootLifecycleActionGuard.CloseAdmission closeAdmission,RootActionGuard.DerivedChildAdmission derivedChildren,
            NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedReplay,DriverCapabilityRuntime capabilities,
            DriverReadHistoryPublisher readHistory,List<RootDomainIntentPreparation.Binding> pending,Set<OperationKey> requiredPending,
            LifeAdvanceEvidence.BoundFrameVerifier actualLifeFrames) {
        public DispatcherInputs {pending=List.copyOf(pending);requiredPending=Set.copyOf(requiredPending);}
    }
    public record FinishInputs(String authorityId,RootExecutableBindings bindings,NativeFrontendAuthority frontend,
            RootLifecycleAuthority lifecycle,RootReconciliationAuthority reconciliation,
            RootLifecycleActionGuard.CloseAdmission closeAdmission,TerminalLifecycleDecisionProducer terminalDecisions,
            RootLifecycleRuntimeFactory.Installed actualLifecycleRuntime,RootActionGuard.DerivedChildAdmission derivedChildren,
            NativeRecordedEvidenceVerifier.DerivedGuardVerifier derivedReplay,DriverCapabilityRuntime capabilities,
            DriverReadHistoryPublisher readHistory,LifeAdvanceEvidence.BoundFrameVerifier actualLifeFrames,
            NativeReadinessCollector.PlanningInputsPort planningInputs,OrdinaryPlanningPipeline pipeline,
            List<RootDomainIntentPreparation.Binding> pending,Set<OperationKey> requiredPending,OriginalWindowReducer.Policy cyclePolicy,
            SessionPorts.OfflineAnalysisPort offline,SessionClock sessionClock,Optional<CheckpointPair> baseline,long admittedSavedDays,
            OrdinaryPlanCompletion completion,SessionPorts.EpisodeContinuation episodes,
            RootCheckpointVerifier.SavedCaptureFactory savedCaptureFactory,RootRestoreMaterialFactory restoreMaterials,
            RootRestoreAdapters.PostAdoptionPort restorePublication) {
        public FinishInputs {pending=List.copyOf(pending);requiredPending=Set.copyOf(requiredPending);Objects.requireNonNull(baseline);
            if(baseline.isEmpty()||admittedSavedDays!=0)throw new IllegalArgumentException("NEXT finish requires its real first physical SAVE pair and zero carried credit");}
    }
    public static StageInputs create(ContinuityStorePort.Session same,RootApplicationAssembly.NextEpisodeStage next,
            SessionResources resources)throws IOException {
        Objects.requireNonNull(same);Objects.requireNonNull(next);Objects.requireNonNull(resources);
        resources.core().writer().requireSession(same);next.requireCurrent(same);resources.catalogs().requireBoundCore(resources.core());
        RootInstalledCatalog catalog=resources.catalog();RootRuntimeContext context=catalog.context();
        if(next.catalog()!=catalog||context.core()!=resources.core()||context.game()!=next.replacement()
                ||!context.source().equals(next.source())||context.writer()!=resources.core().writer()
                ||context.archive()!=resources.core().archive()||!next.driver().source().equals(next.source()))
            throw new IOException("NEXT assembly inputs crossed their actual original Core/catalog/Game/source/Driver");
        resources.startup().requireCurrent(context.clock());resources.domainSettings().requireCurrent(context.clock());
        resources.storage().requireFilePort(resources.files());resources.domainSettings().requireManagedRoots(resources.storage());
        return new StageInputs(next,resources);
    }
    /** Same location constraint consumed by NativeLaunchPlan.savedReplacement: the original fixed native checkpoint filename directly below its profile save directory. */
    static Path canonicalSaveTarget(Path profileDirectory,Path configuredSaveGames,String uniquePhysicalToken)throws IOException {
        absolute(profileDirectory);absolute(configuredSaveGames);Objects.requireNonNull(uniquePhysicalToken);
        Path canonical=profileDirectory.resolve("save games");
        if(!canonical.equals(configuredSaveGames)||!uniquePhysicalToken.matches("next-[0-9a-f]{64}"))
            throw new IOException("NEXT SAVE must retain its actual profile save directory and canonical physical identity token");
        return canonical.resolve("xar_checkpoint.ck3");
    }
    public static final class StageInputs {
        private final RootApplicationAssembly.NextEpisodeStage next;
        private final SessionResources resources;
        private final CheckpointResources checkpoints;
        private final RootReconciliationAuthority reconciliation;
        private final RootDerivedChildAuthority.Installed derived;
        private final OrdinaryPlanningPipeline pipeline;
        private final OrdinaryPlanCompletion completion;
        private RootApplicationAssembly.Staged checkpointStage;
        private DispatcherInputs dispatcher;
        private RootNextEpisodeWindowRuntime.Baselined finishedBaseline;
        private FinishInputs finished;
        private StageInputs(RootApplicationAssembly.NextEpisodeStage next,SessionResources resources)throws IOException {
            this.next=next;this.resources=resources;var catalog=resources.catalog();var context=catalog.context();
            var actualLifecycle=catalog.remainingDomains().lifecycle();actualLifecycle.requireContext(context);
            var actualLife=catalog.remainingDomains().life();actualLife.requireContext(context);
            derived=RootDerivedChildAuthority.install(context,catalog.bindings(),actualLife.infrastructure());
            reconciliation=new RootReconciliationAuthority(context.writer(),context.archive(),actualLifecycle.physical(),
                    new ReconciliationPendingBinding(context.writer(),context.archive(),context.originals()),context.originals(),
                    context.frameLoader(),catalog.bindings().readCatalog(),catalog.remainingDomains().reconciliationReads(),context.clock());
            var lifecycle=resources.domainSettings().configuration().lifecycle();
            String identity=context.game().machineId()+"/"+context.game().generation().pid()+"/"
                    +context.game().generation().creationFiletime().value()+"/"+context.game().sessionId();
            String token="next-"+DriverJson.sha256(identity.getBytes(StandardCharsets.UTF_8));
            Path state=Path.of(lifecycle.stateRoot()).resolve("episodes").resolve(token);
            Path evidence=Path.of(lifecycle.evidenceRoot()).resolve("episodes").resolve(token);
            Path saves=Path.of(lifecycle.saveGames());
            Path saveTarget=canonicalSaveTarget(context.game().launchPlan().profileDirectory(),saves,token);
            var original=resources.startup().checkpoints();
            checkpoints=new CheckpointResources(resources.files(),state.resolve(original.driverCheckpoint().getFileName()),
                    evidence.resolve(original.checkpointEvidence().getFileName()),evidence.resolve(original.attachmentEvidence().getFileName()),
                    actualLifecycle.seedAdoption(),token,saveTarget,resources.startup().freshness());
            if(List.of(checkpoints.driverCheckpointPath(),checkpoints.checkpointEvidence(),checkpoints.attachmentEvidence(),checkpoints.savePath())
                    .stream().distinct().count()!=4)throw new IOException("NEXT physical checkpoint/evidence targets must remain distinct");
            pipeline=catalog.pipeline();completion=catalog.completion();
        }
        public CheckpointResources checkpoints(){return checkpoints;}
        public NativeReadiness.Policy policy(ContinuityStorePort.Session same)throws IOException {
            requirePending(same);return resources.readiness().nextCandidatePolicy(same,next);
        }
        /** Only explicit descendants of the actual admitted settings roots are created, through the one original guard. */
        public void prepareDirectories(ContinuityStorePort.Session same)throws IOException {
            requirePending(same);resources.storage().requireCompleteAdmission();
            for(Path path:List.of(checkpoints.driverCheckpointPath().getParent(),checkpoints.checkpointEvidence().getParent(),checkpoints.savePath().getParent()))
                resources.storage().createManagedDirectories(path);
            resources.storage().requireManagedRoots(List.of(checkpoints.driverCheckpointPath().getParent(),
                    checkpoints.checkpointEvidence().getParent(),checkpoints.savePath().getParent()));
        }
        public synchronized DispatcherInputs dispatcher(ContinuityStorePort.Session same,RootApplicationAssembly.Staged staged)throws IOException {
            requireStage(same,staged);if(dispatcher!=null)return dispatcher;
            var catalog=resources.catalog();var remaining=catalog.remainingDomains();
            derived.requireOwner(catalog.context(),catalog.bindings());
            reconciliation.requireOwner(resources.core().writer(),resources.core().archive(),catalog.bindings().readCatalog(),remaining.lifecycle().physical());
            dispatcher=new DispatcherInputs(resources.startup().authorityId(),catalog.bindings(),catalog.frontend().authority(),
                    remaining.lifecycle().physical(),reconciliation,remaining.lifecycle().closeAdmission(),derived.admission(),derived.replay(),
                    next.candidate(),catalog.readHistory(),catalog.pendingBindings(),catalog.requiredPending(),remaining.lifeReplay());
            return dispatcher;
        }
        public synchronized FinishInputs finish(ContinuityStorePort.Session same,RootApplicationAssembly.Staged staged,
                RootNextEpisodeWindowRuntime.Baselined baseline)throws IOException {
            requireStage(same,staged);resources.core().nextEpisodeWindows().requireBaseline(same,Objects.requireNonNull(baseline));
            if(baseline.begun().stage()!=next)throw new IOException("NEXT finish attempted another original first-SAVE BASELINE");
            if(finished!=null){if(finishedBaseline!=baseline)throw new IOException("retained NEXT finish cannot replace its real BASELINE token");return finished;}
            var actual=dispatcher(same,staged);var catalog=resources.catalog();
            var admitted=resources.readiness().nextEpisode(same,catalog,next,staged,baseline,next.deadline());
            if(admitted.collector()!=staged.readiness()||admitted.capabilities()!=actual.capabilities()||admitted.bindings()!=actual.bindings())
                throw new IOException("NEXT finish lost its identical original candidate/collector/catalog");
            finished=new FinishInputs(actual.authorityId(),actual.bindings(),actual.frontend(),actual.lifecycle(),actual.reconciliation(),actual.closeAdmission(),
                    catalog.remainingDomains().lifecycle().terminalDecisions(),catalog.remainingDomains().lifecycle(),actual.derivedChildren(),actual.derivedReplay(),
                    actual.capabilities(),actual.readHistory(),actual.actualLifeFrames(),admitted.planningInputs(),pipeline,actual.pending(),actual.requiredPending(),
                    resources.cyclePolicy(),resources.offline(),resources.sessionClock(),Optional.of(baseline.firstCheckpoint().pair()),0,completion,resources.episodes(),
                    resources.savedCaptureFactory(),resources.restoreMaterials(),resources.restorePublication());
            finishedBaseline=baseline;return finished;
        }
        private void requirePending(ContinuityStorePort.Session same)throws IOException {
            resources.core().writer().requireSession(same);next.requireRetainedOriginal(same);resources.catalogs().requireBoundCore(resources.core());
            if(next.catalog()!=resources.catalog()||resources.catalog().context().game()!=next.replacement())
                throw new IOException("retained NEXT assembly escaped its exact catalog/Game");
            resources.storage().requireFilePort(checkpoints.files());resources.domainSettings().requireCurrent(resources.catalog().context().clock());
        }
        private void requireStage(ContinuityStorePort.Session same,RootApplicationAssembly.Staged actual)throws IOException {
            requirePending(same);Objects.requireNonNull(actual);actual.requireCheckpointFiles(checkpoints.files());
            if(actual.driver()!=next.driver()||actual.readiness()!=resources.catalog().context().collector()
                    ||actual.planningReads()!=resources.catalog().context().reads())throw new IOException("NEXT inputs received another checkpoint stage/collector/Driver");
            if(checkpointStage==null)checkpointStage=actual;else if(checkpointStage!=actual)throw new IOException("retained NEXT inputs cannot acquire a second checkpoint stage");
        }
    }
    private static void absolute(Path path){Objects.requireNonNull(path);if(!path.isAbsolute()||!path.normalize().equals(path))
        throw new IllegalArgumentException("actual canonical absolute NEXT checkpoint path required");}
}

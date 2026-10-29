package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.ReconciliationPendingBinding;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.platform.ManagedGameSession;

/**
 * Actual restored-runtime inputs retained from the sole startup products and private restoration.
 * Creates neither a replacement Game, a SAVE, a restored binding nor a Host.
 */
public final class RootRestoreAssemblyInputs {
    private final RootStartupNextResources.Shared shared;
    private final RootApplicationSession previous;
    private final RestoreCheckpointService service;
    private final RestoreCheckpointService.RestoreBinding binding;
    private final ManagedGameSession replacement;
    private final RootRestoreAdapters.RestoredRuntime runtime;
    private final RootDerivedChildAuthority.Installed derived;
    private final RootReconciliationAuthority reconciliation;
    private final org.xar.ck3.control.application.session.SessionPorts.OfflineAnalysisPort offline;
    private final Path driverCheckpoint;
    private final Path checkpointEvidence;
    private final Path attachmentEvidence;
    private final Path save;
    private boolean assemblyEntered;
    private IOException assemblyFailure;
    private RootApplicationAssembly.Staged staged;
    private RootApplicationSession successor;

    private RootRestoreAssemblyInputs(ContinuityStorePort.Session same,RootStartupNextResources.Shared shared,
            RootApplicationSession previous,RestoreCheckpointService service,
            RestoreCheckpointService.RestoreBinding binding,ManagedGameSession replacement)throws IOException {
        this.shared=Objects.requireNonNull(shared);this.previous=Objects.requireNonNull(previous);
        this.service=Objects.requireNonNull(service);this.binding=Objects.requireNonNull(binding);
        this.replacement=Objects.requireNonNull(replacement);
        requireOriginal(same);
        runtime=previous.restoreAdapters().runtime(same,service,binding);
        var catalog=runtime.catalog();var context=catalog.context();
        if(context.core()!=shared.core()||context.game()!=replacement||context.writer()!=shared.core().writer()
                ||context.archive()!=shared.core().archive()||!context.source().equals(binding.source())
                ||runtime.collector()!=context.collector()||runtime.bindings()!=catalog.bindings()
                ||runtime.reads()!=context.reads()||runtime.capabilities().readHistoryPublisher()!=catalog.readHistory())
            throw new IOException("restored assembly inputs differ from their actual private physical publication");
        context.requireRestorationOriginal(same,binding);
        var remaining=catalog.remainingDomains();remaining.lifecycle().requireContext(context);remaining.life().requireContext(context);
        derived=RootDerivedChildAuthority.install(context,catalog.bindings(),remaining.life().infrastructure());
        var history=new RootUnresolvedHistoryQualification(context.writer(),context.archive(),context.adopted().authority(),
                catalog.readHistory(),catalog.bindings().readCatalog());
        var epoch=history.captureEpoch(same);
        var pending=new ReconciliationPendingBinding(context.writer(),context.archive(),context.originals(),history);
        context.archive().bindReconciliationHistory(same,pending,epoch);
        if(context.archive().reconciliationHistoryBinding(epoch)!=pending||pending.historyQualification()!=history)
            throw new IOException("restored history consumers lost their actual same-epoch private qualification");
        history.requireOwner(context.writer(),context.archive(),context.adopted().authority(),catalog.readHistory(),catalog.bindings().readCatalog());
        reconciliation=new RootReconciliationAuthority(context.writer(),context.archive(),remaining.lifecycle().physical(),
                pending,context.originals(),
                context.frameLoader(),catalog.bindings().readCatalog(),remaining.reconciliationReads(),context.clock());
        var installedOffline=shared.offline().install(catalog,remaining.events().eventSources());
        installedOffline.requireContext(catalog);offline=installedOffline.port();

        String identity=replacement.machineId()+"/"+replacement.generation().pid()+"/"
                +replacement.generation().creationFiletime().value()+"/"+replacement.sessionId();
        String token="restored-"+DriverJson.sha256(identity.getBytes(StandardCharsets.UTF_8));
        var settings=shared.domainSettings().configuration().lifecycle();var original=shared.startup().checkpoints();
        Path state=Path.of(settings.stateRoot()).resolve("restored").resolve(token);
        Path evidence=Path.of(settings.evidenceRoot()).resolve("restored").resolve(token);
        driverCheckpoint=state.resolve(original.driverCheckpoint().getFileName());
        checkpointEvidence=evidence.resolve(original.checkpointEvidence().getFileName());
        attachmentEvidence=evidence.resolve(original.attachmentEvidence().getFileName());
        // The lifecycle's savedReplacement validator requires this actual profile's direct save-games child.
        // Reuse the genuine loaded physical SAVE path; no caller supplies a replacement path.
        save=Path.of(binding.pair().save().reference().path());
        Path canonicalSaveRoot=replacement.launchPlan().profileDirectory().resolve("save games");
        if(!save.isAbsolute()||!save.normalize().equals(save)
                ||!save.getParent().toRealPath().equals(canonicalSaveRoot.toRealPath())
                ||List.of(driverCheckpoint,checkpointEvidence,attachmentEvidence,save).stream().distinct().count()!=4)
            throw new IOException("restored checkpoint destinations differ from the actual loaded profile SAVE");
        for(Path directory:List.of(driverCheckpoint.getParent(),checkpointEvidence,attachmentEvidence))
            shared.storage().createManagedDirectories(directory);
        shared.storage().requireManagedRoots(List.of(driverCheckpoint.getParent(),checkpointEvidence,attachmentEvidence,save.getParent()));
        requireOriginal(same);
    }

    public static RootRestoreAssemblyInputs create(ContinuityStorePort.Session same,RootStartupNextResources.Shared shared,
            RootApplicationSession previous,RestoreCheckpointService service,
            RestoreCheckpointService.RestoreBinding binding,ManagedGameSession replacement)throws IOException {
        return new RootRestoreAssemblyInputs(same,shared,previous,service,binding,replacement);
    }

    /** One real stage and finish. Partial construction is retained, never replayed as another graph. */
    public synchronized RootApplicationSession assemble(Instant deadline)throws IOException,InterruptedException {
        Objects.requireNonNull(deadline);
        if(successor!=null)return successor;
        if(assemblyEntered)throw new IOException("original partial restored assembly requires reconciliation; no second stage",assemblyFailure);
        assemblyEntered=true;
        try {
            var core=shared.core();var catalog=runtime.catalog();var remaining=catalog.remainingDomains();
            core.writer().locked(same->{requireOriginal(same);return null;});
            staged=core.restoredStage(previous,service,binding,replacement,shared.files(),driverCheckpoint,
                    checkpointEvidence,attachmentEvidence,remaining.lifecycle().seedAdoption(),binding.pair().lineageId(),save,deadline);
            // Core.restoredStage calls the exact catalog.bindSave, which binds this stage's sole seed store.
            successor=core.withBorrowed(()->{
                var same=core.writer().borrowedSession();requireOriginal(same);
                if(staged.readiness()!=runtime.collector()||staged.driver()!=previous.restoreAdapters().adopted(binding)
                        ||staged.planningReads()!=runtime.reads())
                    throw new IOException("actual restored stage lost its retained Driver/collector/read products");
                derived.requireOwner(catalog.context(),catalog.bindings());
                reconciliation.requireOwner(core.writer(),core.archive(),catalog.bindings().readCatalog(),remaining.lifecycle().physical());
                return staged.finish(shared.startup().authorityId(),runtime.bindings(),catalog.frontend().authority(),
                        remaining.lifecycle().physical(),reconciliation,remaining.lifecycle().closeAdmission(),
                        remaining.lifecycle().terminalDecisions(),remaining.lifecycle(),derived.admission(),derived.replay(),
                        runtime.capabilities(),catalog.readHistory(),remaining.lifeReplay(),runtime.planningInputs(),catalog.pipeline(),
                        catalog.pendingBindings(),catalog.requiredPending(),shared.cyclePolicy(),offline,shared.sessionClock(),
                        Optional.of(binding.pair()),binding.committedSavedDays(),catalog.completion(),shared.episodes(),
                        shared.savedCaptureFactory(),shared.restoreMaterials(),shared.restorePublication());
            });
            return successor;
        }catch(IOException failure){assemblyFailure=failure;throw failure;}
        catch(InterruptedException interrupted){
            assemblyFailure=new IOException("original restored assembly was interrupted; no second construction",interrupted);throw interrupted;
        }catch(RuntimeException failure){
            assemblyFailure=new IOException("original restored assembly failed; no second construction",failure);throw assemblyFailure;
        }
    }

    private void requireOriginal(ContinuityStorePort.Session same)throws IOException {
        var core=shared.core();core.writer().requireSession(same);shared.catalogs().requireBoundCore(core);
        if(!previous.ownedBy(core)||previous.writer()!=core.writer()||previous.archive()!=core.archive()
                ||!previous.isRetired()||!binding.source().equals(shared.source())
                ||!binding.session().machineId().equals(replacement.machineId())
                ||!binding.session().game().equals(replacement.generation())
                ||!binding.session().sessionId().equals(replacement.sessionId())
                ||shared.lifecycle().currentSession().orElse(null)!=replacement)
            throw new IOException("restored assembly requires the actual retired Root, private binding and lifecycle-owned replacement");
        shared.startup().requireCurrent(shared.clock());shared.domainSettings().requireCurrent(shared.clock());
        shared.domainSettings().requireManagedRoots(shared.storage());shared.storage().requireCompleteAdmission();
        shared.storage().requireFilePort(shared.files());shared.episodes().requireCore(core,shared.catalogs());
        replacement.verify();replacement.launchPlan().sources().requireLoadedClass(RootRestoreAssemblyInputs.class);
        service.requireRetainedOriginal(same,binding);binding.savedMaterial().requireRetained(same);
    }
}

package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.lifecycle.SeedAdoption;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** The original seed freezer remains the only file producer; its actual Available result publishes the cache. */
public final class SeedCapabilityAdoption implements CheckpointService.SeedAdoptionPort {
    @FunctionalInterface public interface FramePort {
        DriverObservationAssembler.Complete current(ContinuityStorePort.Session original,ActionReceipt appliedSave) throws IOException;
    }
    private final CheckpointService.SeedAdoptionPort actualFreezer;
    private final DriverStateAssembler authority;
    private final ActionPorts.OutcomeArchive archive;
    private final Supplier<ContinuityStorePort.Session> originalSession;
    private final FramePort frames;
    private final CheckpointFiles files;
    public SeedCapabilityAdoption(CheckpointService.SeedAdoptionPort actualFreezer,DriverStateAssembler authority,
            ActionPorts.OutcomeArchive archive,Supplier<ContinuityStorePort.Session> currentOriginalSession,
            FramePort actualCurrentFrames,CheckpointFiles actualFiles) {
        this.actualFreezer=Objects.requireNonNull(actualFreezer);this.authority=Objects.requireNonNull(authority);
        this.archive=Objects.requireNonNull(archive);originalSession=Objects.requireNonNull(currentOriginalSession);
        frames=Objects.requireNonNull(actualCurrentFrames);files=Objects.requireNonNull(actualFiles);
    }
    @Override public SeedAdoption freezeFirst(CheckpointPair actualPair,ActionReceipt appliedSave) throws IOException {
        SeedAdoption result=actualFreezer.freezeFirst(actualPair,appliedSave);
        if(!(result instanceof SeedAdoption.Available available))return result;
        ContinuityStorePort.Session borrowed=Objects.requireNonNull(originalSession.get());
        DriverObservationAssembler.Complete frame=frames.current(borrowed,appliedSave);
        authority.withFrozenFacts(borrowed,frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,"current full Driver unavailable after actual immutable seed adoption");
            var current=(DriverSnapshotFacts.Known)frozen.state();
            var publication=DriverCapabilityStateProducer.observeSeed(frame,current,available,files,archive.withSession(borrowed));
            authority.publishCapabilityInputs(borrowed,current.stamp(),publication.expectedAuxiliarySha256(),publication);return null;
        });
        return result;
    }
}

package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.JavaGameLifecycle;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** Builds the actual restore material chain for the current managed owner. */
public final class RootRestoreMaterialFactory {
    private final JavaGameLifecycle lifecycle;
    private final ExactRef source;
    private final int retainedFrames;
    private final Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen;
    private final Optional<NativeLaunchPlan> ordinaryPlan;

    public RootRestoreMaterialFactory(JavaGameLifecycle lifecycle,ExactRef source,int retainedFrames,
            RootFrozenRunProfile.FrozenRunProfile originalFrozen) {
        this(lifecycle,source,retainedFrames,Optional.of(originalFrozen),Optional.empty());
    }

    /** Configuration only: an actual SAVE is required when RESTORE is requested, never here. */
    public static RootRestoreMaterialFactory ordinary(JavaGameLifecycle lifecycle,ExactRef source,int retainedFrames,
            ManagedGameSession actualOriginal)throws IOException {
        Objects.requireNonNull(lifecycle);Objects.requireNonNull(actualOriginal);
        actualOriginal.verify();
        if(lifecycle.currentSession().orElseThrow(()->new IOException("actual managed owner unavailable"))!=actualOriginal)
            throw new IOException("ordinary restore configuration belongs to another current managed owner");
        return new RootRestoreMaterialFactory(lifecycle,source,retainedFrames,Optional.empty(),
                Optional.of(actualOriginal.launchPlan()));
    }

    private RootRestoreMaterialFactory(JavaGameLifecycle lifecycle,ExactRef source,int retainedFrames,
            Optional<RootFrozenRunProfile.FrozenRunProfile> originalFrozen,Optional<NativeLaunchPlan> ordinaryPlan) {
        this.lifecycle=Objects.requireNonNull(lifecycle);this.source=Objects.requireNonNull(source);this.retainedFrames=retainedFrames;
        this.originalFrozen=Objects.requireNonNull(originalFrozen);this.ordinaryPlan=Objects.requireNonNull(ordinaryPlan);
        StrictJson.require(originalFrozen.isPresent()!=ordinaryPlan.isPresent(),"one actual restore configuration branch required");
        StrictJson.require(source.bytes()>0&&retainedFrames>=2&&retainedFrames<=4096,"actual bounded restore material source required");
    }

    RootRestoreAdapters.MaterialPort create(ContinuityWriter writer,NativeOutcomeArchive archive,CheckpointFiles files,
            DriverCheckpointStore drivers,SavedCheckpointMaterialStore saved,DriverBootstrap.Adopted previous)throws IOException {
        if(originalFrozen.isPresent())
            return new RootRestoreMaterials(writer,archive,lifecycle,files,drivers,saved,previous,source,retainedFrames,
                    originalFrozen.orElseThrow());
        ManagedGameSession current=lifecycle.currentSession().orElseThrow(()->new IOException("actual managed owner unavailable"));
        current.verify();requireOrdinaryConfiguration(ordinaryPlan.orElseThrow(),current.launchPlan());
        return RootRestoreMaterials.ordinary(writer,archive,lifecycle,files,drivers,saved,previous,source,retainedFrames,current);
    }

    /** Actual launch configuration lineage; request, session and load change for genuine replacements. */
    static void requireOrdinaryConfiguration(NativeLaunchPlan original,NativeLaunchPlan current)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(current);
        if(original.sources()!=current.sources()||!original.profileDirectory().equals(current.profileDirectory())
                ||!original.stateDirectory().equals(current.stateDirectory())||!original.pipeName().equals(current.pipeName())
                ||!original.bridgeVersion().equals(current.bridgeVersion())||!original.adapterId().equals(current.adapterId())
                ||!original.preparedProfile().equals(current.preparedProfile())||!original.environment().equals(current.environment()))
            throw new IOException("ordinary restore factory crossed its actual launch configuration");
    }
}

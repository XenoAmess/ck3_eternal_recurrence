package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.campaign.M7KernelInputs;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual afterReady producer. Root binds this once to the collector and its same M7 policy supplier. */
public final class RootM7ReadyPublication implements NativeReadinessCollector.ReadyPublication {
    private final RootNativeSourceAuthority sources;
    private final M7KernelInputs inputs;

    public RootM7ReadyPublication(RootNativeSourceAuthority samePhysicalSourceAuthority, M7KernelInputs sameKernelInputs) {
        sources = Objects.requireNonNull(samePhysicalSourceAuthority);
        inputs = Objects.requireNonNull(sameKernelInputs);
    }

    @Override public void publish(ContinuityStorePort.Session borrowed, PlanningRequest request, Complete frame,
            Known actualDriver, NativeReadinessCollector.SourceQualification qualification) throws IOException {
        Objects.requireNonNull(actualDriver);
        // optionalMetadata() checks actual private issuer, original Session, complete source witnesses and manifest pin when present.
        Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata = sources.optionalMetadata(borrowed, qualification);
        M7KernelInputs.Captured captured = inputs.capture(borrowed, request, frame,
                metadata.map(m -> m.ownerSourceEpoch()), metadata.map(m -> m.gameExecutable()), Optional.empty());
        StrictJson.require(captured.driverStamp().equals(actualDriver.stamp())
                && captured.originalNative().equals(frame.originalEvidence()),
                "actual M7 readiness publication crossed the held full Driver or original native packet");
        // No government observation is invented; a source-bound actual government producer may enrich a later version.
        qualification.assertCurrent(borrowed);
        if (metadata.isPresent()) metadata.orElseThrow().requireCurrent(borrowed);
    }
}

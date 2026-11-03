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
    @FunctionalInterface interface GovernmentInputs {
        Optional<org.xar.ck3.control.wave2.governance.government.GovernmentContext.Context> current(
                ContinuityStorePort.Session same, PlanningRequest request, Complete frame, Known driver) throws IOException;
    }
    private final GovernmentInputs government;

    public RootM7ReadyPublication(RootNativeSourceAuthority samePhysicalSourceAuthority, M7KernelInputs sameKernelInputs) {
        this(samePhysicalSourceAuthority, sameKernelInputs, (same, request, frame, driver) -> Optional.empty());
    }

    RootM7ReadyPublication(RootNativeSourceAuthority samePhysicalSourceAuthority, M7KernelInputs sameKernelInputs,
            GovernmentInputs actualGovernmentInputs) {
        sources = Objects.requireNonNull(samePhysicalSourceAuthority);
        inputs = Objects.requireNonNull(sameKernelInputs);
        government = Objects.requireNonNull(actualGovernmentInputs);
    }

    @Override public void publish(ContinuityStorePort.Session borrowed, PlanningRequest request, Complete frame,
            Known actualDriver, NativeReadinessCollector.SourceQualification qualification) throws IOException {
        Objects.requireNonNull(actualDriver);
        // optionalMetadata() checks actual private issuer, original Session, complete source witnesses and manifest pin when present.
        Optional<RootNativeSourceAuthority.QualifiedMetadata> metadata = sources.optionalMetadata(borrowed, qualification);
        M7KernelInputs.Captured captured = inputs.capture(borrowed, request, frame,
                metadata.map(m -> m.ownerSourceEpoch()), metadata.map(m -> m.gameExecutable()), government.current(borrowed, request, frame, actualDriver));
        StrictJson.require(captured.driverStamp().equals(actualDriver.stamp())
                && captured.originalNative().equals(frame.originalEvidence()),
                "actual M7 readiness publication crossed the held full Driver or original native packet");
        // The installed producer returns only this same held observation's original READ data; Ready never queries.
        qualification.assertCurrent(borrowed);
        if (metadata.isPresent()) metadata.orElseThrow().requireCurrent(borrowed);
    }
}

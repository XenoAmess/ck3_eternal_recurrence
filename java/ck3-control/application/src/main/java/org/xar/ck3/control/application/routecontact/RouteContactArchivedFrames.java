package org.xar.ck3.control.application.routecontact;

import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.advance.AdvanceObservationPort;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Uses the sole complete Driver/native loader; push provenance is reconstructed from its actual original packet binding. */
public final class RouteContactArchivedFrames implements RouteContactArchivedVerifier.FrameReplay {
    private final NativeEffectEvidence.FrameLoader frames;
    public RouteContactArchivedFrames(NativeEffectEvidence.FrameLoader frames) { this.frames = Objects.requireNonNull(frames); }
    @Override public AdvanceObservationPort.Frame replay(WriterContracts.Head head, AdvanceObservationPort.Frame retained,
            ActionPorts.OutcomeArchive archive) {
        Objects.requireNonNull(head); Objects.requireNonNull(retained); Objects.requireNonNull(archive);
        var basis = new NativeEffectEvidence.FrameBasis(retained.originalEvidence(),
                DriverObservationEvidenceReader.reference(retained.semantic().get("java_driver_facts_evidence")));
        var rebuilt = frames.load(basis, archive);
        var provenance = new ObservationProvenance.Push(rebuilt.identity().frame().snapshotId(),
                rebuilt.identity().frame().identity().nativeRevision(), rebuilt.originalEvidence());
        var result = new AdvanceObservationPort.Frame(rebuilt.identity(), rebuilt.source(), rebuilt.sessionId(), rebuilt.semantic(),
                provenance, rebuilt.observedAt(), rebuilt.originalEvidence());
        StrictJson.require(result.equals(retained), "archived route native/full Driver/provenance frame differs");
        return result;
    }
}

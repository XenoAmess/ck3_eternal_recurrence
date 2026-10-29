package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.WriterContracts.Head;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Rebuilds the native snapshot and frozen Driver facts from their actual immutable originals. */
public final class ConstructionSnapshotVerifier implements OrdinaryConstructionMaterialFollowup.SnapshotVerifier {
    private final ActionPorts.OutcomeArchive archive;
    private final NativeEffectEvidence.FrameLoader frames;
    public ConstructionSnapshotVerifier(ActionPorts.OutcomeArchive archive, NativeEffectEvidence.FrameLoader frames) {
        this.archive = Objects.requireNonNull(archive); this.frames = Objects.requireNonNull(frames);
    }
    @Override public void verify(Head actualHead, Obj originalSnapshot, List<PlanningReadReceipt> originalReads) throws IOException {
        Objects.requireNonNull(actualHead); Objects.requireNonNull(originalSnapshot); originalReads = List.copyOf(originalReads);
        require(!originalReads.isEmpty() && originalReads.size() <= 3, "actual finite construction reads required");
        ExactRef facts = ExactRef.fromJson(StrictJson.parse(encode(object(originalSnapshot.get("java_driver_facts_evidence"), "actual frozen Driver facts reference"))));
        var first = originalReads.getFirst();
        var complete = frames.load(new NativeEffectEvidence.FrameBasis(first.before().binding().nativeEvidence(), facts), archive);
        require(complete.semantic().equals(originalSnapshot), "construction snapshot differs from the rebuilt original native/Driver publication");
        require(actualHead.state().machineId().equals(complete.identity().machineId()), "construction material belongs to another writer machine");
        for (PlanningReadReceipt read : originalReads) {
            NativeRecordedEvidenceVerifier.requireRead(read, archive);
            require(read.request().before().equals(complete.identity()) && read.request().source().equals(complete.source())
                    && read.request().sessionId().equals(complete.sessionId()), "construction read crossed the rebuilt complete source");
            require(read.before().binding().nativeEvidence().equals(complete.originalEvidence()) && read.after().binding().nativeEvidence().equals(complete.originalEvidence())
                    && read.before().binding().connectionGeneration().equals(complete.connectionGeneration())
                    && read.after().binding().connectionGeneration().equals(complete.connectionGeneration()), "construction read crossed physical Native publication/connection");
            require(read.before().originalBindingSha256().equals(complete.fullBindingSha256()) && read.after().originalBindingSha256().equals(complete.fullBindingSha256())
                    && read.before().binding().observed().equals(complete.identity()) && read.after().binding().observed().equals(complete.identity()), "construction read guard differs from rebuilt original full binding");
            require(read.before().paused() && read.after().paused() && read.before().mapReady() && read.after().mapReady()
                    && read.before().playerAlive() && read.after().playerAlive(), "construction material read lost its living paused player map");
        }
    }
}

package org.xar.ck3.control.application.history;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Explicit original v2 import through the existing full-envelope decoder; never accepts a legacy WAL tail as full history. */
public final class DriverHistoryImport {
    public static final String ADAPTER_SCHEMA = "xar.ck3.java-driver-surviving-history/v1";
    private DriverHistoryImport() { }
    public record Imported(DriverSnapshotFacts.Known facts, List<DriverSurvivingHistory.Row> completeSurvivingBranch) {
        public Imported {
            Objects.requireNonNull(facts); completeSurvivingBranch = DriverSurvivingHistory.completeBranch(completeSurvivingBranch);
            org.xar.ck3.control.contracts.StrictJson.require(completeSurvivingBranch.equals(DriverSurvivingHistory.entries(facts.driver())),
                    "imported surviving branch differs from the actual complete Driver");
        }
    }
    /** Reads an already committed physical original. Missing or replaced artifacts never create an empty history. */
    public static Imported archivedOriginalV2(ActionPorts.OutcomeArchive archive, ExactRef originalDriver,
            long actualDriverVersion, long actualEpisodeEpoch, GameGeneration actualGame, Obj actualAuxiliary) {
        Objects.requireNonNull(archive); Objects.requireNonNull(originalDriver);
        return originalV2(originalDriver, archive.loadMaterial(originalDriver).bytes(), actualDriverVersion,
                actualEpisodeEpoch, actualGame, actualAuxiliary);
    }
    public static Imported originalV2(ExactRef originalDriver, byte[] actualOriginalBytes, long actualDriverVersion,
            long actualEpisodeEpoch, GameGeneration actualGame, Obj actualAuxiliary) {
        DriverSnapshotFacts.Known facts = DriverFactsRepository.imported(originalDriver, actualOriginalBytes,
                actualDriverVersion, actualEpisodeEpoch, actualGame, actualAuxiliary);
        // This validates every original row before adoption. Required data is never replaced by an empty collection.
        return new Imported(facts, DriverSurvivingHistory.entries(facts.driver()));
    }
}

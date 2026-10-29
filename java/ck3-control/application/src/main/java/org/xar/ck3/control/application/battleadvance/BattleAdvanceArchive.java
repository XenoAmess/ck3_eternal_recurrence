package org.xar.ck3.control.application.battleadvance;

import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.contracts.ExactRef;

/** Adapter to the existing one application archive. This class creates no files, locks, ledger or second writer. */
public final class BattleAdvanceArchive implements BattleAdvanceComposite.EvidenceArchive {
    private final ActionPorts.OutcomeArchive originalArchive;
    public BattleAdvanceArchive(ActionPorts.OutcomeArchive originalArchive) { this.originalArchive = Objects.requireNonNull(originalArchive); }
    @Override public ExactRef completed(ActionCommand parent, BattleAdvanceComposite.Outcome outcome) {
        return originalArchive.preserveMaterial(BattleAdvanceResultCodec.completed(parent, outcome, originalArchive));
    }
    @Override public ExactRef failed(ActionCommand parent, BattleAdvanceComposite.Failure failure) {
        return TacticalClockFailureEvidence.preserve(parent, failure, originalArchive);
    }
    @Override public ExactRef readOnly(ActionCommand parent, BattleAdvanceComposite.ReadOnlyOutcome outcome) {
        return originalArchive.preserveMaterial(BattleAdvanceResultCodec.readOnly(parent, outcome));
    }
    public BattleAdvanceResultCodec.Decoded load(ExactRef reference, BattleAdvanceResultCodec.Profile profile) {
        return BattleAdvanceResultCodec.decode(originalArchive.loadMaterial(reference), profile);
    }
}

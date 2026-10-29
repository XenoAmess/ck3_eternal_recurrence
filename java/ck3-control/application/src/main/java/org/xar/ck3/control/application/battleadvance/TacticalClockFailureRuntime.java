package org.xar.ck3.control.application.battleadvance;

import java.util.Objects;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.session.AutoFailureDiagnostic;

/** Installs the actual producer/archive reader on the one existing writer archive. No new process or clock. */
public final class TacticalClockFailureRuntime {
    private TacticalClockFailureRuntime() { }
    public record Installed(BattleAdvanceComposite.EvidenceArchive failureArchive, AutoFailureDiagnostic.Port diagnostics) {
        public Installed { Objects.requireNonNull(failureArchive); Objects.requireNonNull(diagnostics); }
    }
    public static Installed install(NativeEffectEvidence.FrameLoader frames, ActionPorts.OutcomeArchive sameWriterArchive) {
        Objects.requireNonNull(frames); Objects.requireNonNull(sameWriterArchive);
        return new Installed(new BattleAdvanceArchive(sameWriterArchive), new TacticalClockFailureEvidence(frames));
    }
}

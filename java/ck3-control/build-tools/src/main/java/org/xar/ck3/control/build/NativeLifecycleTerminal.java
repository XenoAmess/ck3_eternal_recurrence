package org.xar.ck3.control.build;

import java.util.Objects;

/** Interprets the shared Job terminal without turning failure cleanup into natural exit. */
public final class NativeLifecycleTerminal {
    public enum Settlement { NOT_RETURNED, OWNED_PROCESSES_REMAIN, CLEANUP_SETTLED, NATURAL_SETTLED }
    public record Assessment(Settlement settlement, boolean rootSucceeded, boolean jobSettled,
            boolean successful, String stopReason) {
        public Assessment {
            Objects.requireNonNull(settlement);
            if (stopReason != null && stopReason.isBlank()) throw new IllegalArgumentException("nonempty stop reason required");
            if ((settlement == Settlement.NOT_RETURNED && (rootSucceeded || jobSettled || successful || stopReason != null))
                    || (settlement == Settlement.OWNED_PROCESSES_REMAIN && (jobSettled || successful))
                    || (settlement == Settlement.CLEANUP_SETTLED && (!jobSettled || successful || stopReason == null))
                    || (settlement == Settlement.NATURAL_SETTLED && (!jobSettled || stopReason != null))) {
                throw new IllegalArgumentException("settlement fields disagree");
            }
            if (successful && (settlement != Settlement.NATURAL_SETTLED || !rootSucceeded || !jobSettled
                    || stopReason != null)) throw new IllegalArgumentException("natural successful settlement required");
        }
    }
    private NativeLifecycleTerminal() { }

    public static Assessment assess(WindowsJobProcess.CommandResult terminal) {
        if (terminal == null) return new Assessment(Settlement.NOT_RETURNED, false, false, false, null);
        boolean settled = terminal.accounting().activeProcesses() == 0;
        Settlement state = !settled ? Settlement.OWNED_PROCESSES_REMAIN
                : terminal.stopReason() != null ? Settlement.CLEANUP_SETTLED : Settlement.NATURAL_SETTLED;
        return new Assessment(state, terminal.exitCode() == 0, settled,
                state == Settlement.NATURAL_SETTLED && terminal.passed(), terminal.stopReason());
    }
}

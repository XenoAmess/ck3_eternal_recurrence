package org.xar.ck3.research.m3.tail217;

import org.xar.ck3.research.m3.tail212.TerminalTail212Api;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;

public final class TerminalTailTargetBinding217 {
    private TerminalTailTargetBinding217() { }

    public static TerminalTail212Api.Ports bind(long moduleBase,
            TerminalTailTarget217Api.Memory capturedMemory,
            TerminalTailTarget217Api.Ports childPorts,
            TerminalTail212Api.Ports fallback) {
        java.util.Objects.requireNonNull(capturedMemory, "capturedMemory");
        java.util.Objects.requireNonNull(childPorts, "childPorts");
        java.util.Objects.requireNonNull(fallback, "fallback");

        return new TerminalTail212Api.Ports() {
            @Override
            public long tail42421c8(Terminal207Api.Memory memory, long siteRva, long rcx, int edx, int r8d) {
                return fallback.tail42421c8(memory, siteRva, rcx, edx, r8d);
            }

            @Override
            public long tail42421c8(Terminal207Api.Memory memory, long siteRva, long rcx, int edx, int r8d, long calleeEntryRsp) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("memory mismatch");
                }
                if (siteRva != 0x424235BL) {
                    throw new IllegalArgumentException("siteRva mismatch");
                }

                TerminalTailTarget217Api.Scratch scratch = new TerminalTailTarget217Api.Scratch(calleeEntryRsp);
                TerminalTailTarget217Api.Input input = new TerminalTailTarget217Api.Input(
                        moduleBase,
                        (int) rcx,
                        edx,
                        r8d,
                        scratch
                );

                TerminalTailTarget217Api.Outcome outcome = TerminalTailTarget217.execute(
                        capturedMemory,
                        childPorts,
                        input
                );

                if (outcome instanceof TerminalTailTarget217Api.NormalReturn) {
                    return ((TerminalTailTarget217Api.NormalReturn) outcome).rawRax();
                } else if (outcome instanceof TerminalTailTarget217Api.Trap) {
                    throw new UnsupportedOperationException("INT3 outcome");
                } else {
                    throw new IllegalStateException("Unknown outcome");
                }
            }
        };
    }
}
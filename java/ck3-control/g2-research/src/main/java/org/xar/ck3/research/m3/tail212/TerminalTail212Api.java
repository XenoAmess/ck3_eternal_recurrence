package org.xar.ck3.research.m3.tail212;

import org.xar.ck3.research.m3.terminal207.Terminal207Api;

/** Source-established operands of the actual 12-byte tail wrapper, not full CPU ABI. */
public interface TerminalTail212Api {
    interface Ports {
        long tail42421c8(Terminal207Api.Memory memory, long siteRva, long rcx, int edx, int r8d);
        default long tail42421c8(Terminal207Api.Memory memory, long siteRva, long rcx, int edx, int r8d, long calleeEntryRsp) {
            return tail42421c8(memory, siteRva, rcx, edx, r8d);
        }
    }
}

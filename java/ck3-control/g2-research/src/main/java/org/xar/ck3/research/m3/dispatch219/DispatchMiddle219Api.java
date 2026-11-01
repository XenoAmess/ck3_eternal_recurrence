package org.xar.ck3.research.m3.dispatch219;

import org.xar.ck3.research.m3.tail217.TerminalTailTarget217Api;

/** Normal 187B supplied-storage effects only; no CPU/stack/RET/NV/DF/EH projection. */
public interface DispatchMiddle219Api {
    /** Same nominal storage usable by the actual outer 217 and middle 218 consumers. */
    interface Memory extends TerminalTailTarget217Api.Memory {
        /** One whole exchange effect. Old DWORD is discarded; no concurrency qualification. */
        void exchangeInt32(long address, int value);
    }

    record Input(long moduleBase, long rcxAddress) { }

    interface Ports {
        void call43dbba8(Memory memory, long siteRva, long actualTarget,
                        long liveRax, int ecx, int edx, int r8d);
        void call424de88(Memory memory, long siteRva, long rcx);
        default void call424de88(Memory memory, long siteRva, long rcx, long calleeEntryRsp) {
            call424de88(memory, siteRva, rcx);
        }
        void call424e1ac(Memory memory, long siteRva, long rcx, long rdx);
    }
}

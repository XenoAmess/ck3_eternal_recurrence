package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/**
 * Adapter mapping existing machine-level Gate ports to declared Windows API imports and static dispatch.
 * Scope: static import, load-config and pointed-body evidence only.
 * Pointers, lock state, loaded CFG and the complete native ABI remain outside this adapter.
 */
public final class RequestGateStaticDispatchConsumer {
    private RequestGateStaticDispatchConsumer() { }

    public static RequestGate424cffc.Ports ports(long moduleBase,
            NativeTaskMemory memory,
            RequestCriticalSectionImportBinding.WindowsApiPorts api,
            RequestStaticDispatch4267630.TailTarget target) {
        return new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                // Reuse the existing decode consumer which handles the critical section import binding
                // and the decode logic for 424D02C.
                return RequestCriticalSectionDecodeConsumer.decode(moduleBase, memory, api);
            }

            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                // Reuse the existing static dispatch consumer which handles the JMP RAX target.
                return RequestStaticDispatch4267630.execute(knownRcx, liveRax, target);
            }
        };
    }
}

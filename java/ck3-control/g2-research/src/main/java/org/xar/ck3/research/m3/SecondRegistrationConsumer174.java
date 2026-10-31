package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Explicit call/memory effects of full154B25F8A00; raw RAX and EH are not projected. */
public final class SecondRegistrationConsumer174 {
    private SecondRegistrationConsumer174() { }

    public static RegistrationClearApi174.Completion invoke(
            NativeTaskMemory memory,
            RegistrationClearApi174.Ports ports,
            RegistrationClearApi174.Singleton singleton,
            long observedInvokeCode,
            long selectedInvokeCode,
            RegistrationClearApi174.Limits limits) {
        if (observedInvokeCode != selectedInvokeCode) {
            return RegistrationClearApi174.Completion.UNSUPPORTED_TARGET;
        }

        long receiver = singleton.get();
        return RegistrationClear174.clear(memory, ports, receiver, limits);
    }
}
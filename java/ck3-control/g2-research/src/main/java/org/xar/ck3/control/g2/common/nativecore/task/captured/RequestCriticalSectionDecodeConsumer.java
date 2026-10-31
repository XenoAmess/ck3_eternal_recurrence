package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class RequestCriticalSectionDecodeConsumer {
    private RequestCriticalSectionDecodeConsumer() { }

    public static long decode(long moduleBase,
            NativeTaskMemory memory,
            RequestCriticalSectionImportBinding.WindowsApiPorts api) {
        RequestCriticalSectionImportBinding.WindowsApiPorts apiPorts = api;
        RequestIndexedTails4247ffc.Ports tails = RequestCriticalSectionImportBinding.toTails(apiPorts);
        RequestDecode424d02c.Ports decodePorts = RequestDecodeTailConsumer.ports(moduleBase, tails);
        return RequestDecode424d02c.execute(moduleBase, memory, decodePorts);
    }
}

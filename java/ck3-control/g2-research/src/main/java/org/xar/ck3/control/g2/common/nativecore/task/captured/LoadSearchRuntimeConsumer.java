package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** New actual consumer for LoadSearch4260af0. */
public final class LoadSearchRuntimeConsumer {
    private LoadSearchRuntimeConsumer() { }

    public static LoadRuntimeImportBinding.SearchPorts ports(LoadSearch4260af0.ReadMemory memory, LoadRuntimeImportBinding.SearchPorts remainder) {
        return new LoadRuntimeImportBinding.SearchPorts() {
            @Override
            public long call4260af0(LoadRuntime4260e74.SearchCall call) {
                return LoadSearch4260af0.find(call, memory);
            }
            @Override
            public long call4260968(LoadRuntime4260e74.SearchCall call) {
                return remainder.call4260968(call);
            }
            @Override
            public long call4260c28(LoadRuntime4260e74.SearchCall call) {
                return remainder.call4260c28(call);
            }
        };
    }
}

package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Actual normal-parent assembly only; helpers have separate implementation owners. */
public final class LoadHierarchyRuntimeConsumer {
    private LoadHierarchyRuntimeConsumer() { }

    public static LoadRuntime4260e74.Ports ports(LoadHierarchySearch173.Memory memory,
            LoadRuntimeImportBinding.WindowsApiPorts api) {
        return LoadRuntimeImportBinding.ports(api, new LoadRuntimeImportBinding.SearchPorts() {
            @Override
            public long call4260af0(LoadRuntime4260e74.SearchCall call) {
                return LoadSearch4260af0.find(call, memory);
            }

            @Override
            public long call4260968(LoadRuntime4260e74.SearchCall call) {
                return LoadHierarchySearch173.find968(call, memory);
            }

            @Override
            public long call4260c28(LoadRuntime4260e74.SearchCall call) {
                return LoadHierarchySearch173.findC28(call, memory);
            }
        });
    }
}
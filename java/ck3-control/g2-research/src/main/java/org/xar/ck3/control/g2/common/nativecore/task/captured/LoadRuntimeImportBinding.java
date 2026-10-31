package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Declared static import and named opaque helpers; no Win32/native execution. */
public final class LoadRuntimeImportBinding {
    private LoadRuntimeImportBinding() { }
    public interface WindowsApiPorts {
        long rtlPcToFileHeader(long pcValue, LoadRuntime4260e74.LocalSlot64 baseOfImage);
    }
    public interface SearchPorts {
        long call4260af0(LoadRuntime4260e74.SearchCall call);
        long call4260968(LoadRuntime4260e74.SearchCall call);
        long call4260c28(LoadRuntime4260e74.SearchCall call);
    }
    public static LoadRuntime4260e74.Ports ports(WindowsApiPorts api, SearchPorts search) {
        return new LoadRuntime4260e74.Ports() {
            @Override
            public long call43da2d0(long rcx, LoadRuntime4260e74.LocalSlot64 outSlot, long knownR8, long knownR9, long liveRax) {
                return api.rtlPcToFileHeader(rcx, outSlot);
            }
            @Override
            public long call4260af0(LoadRuntime4260e74.SearchCall call) {
                return search.call4260af0(call);
            }
            @Override
            public long call4260968(LoadRuntime4260e74.SearchCall call) {
                return search.call4260968(call);
            }
            @Override
            public long call4260c28(LoadRuntime4260e74.SearchCall call) {
                return search.call4260c28(call);
            }
        };
    }
}

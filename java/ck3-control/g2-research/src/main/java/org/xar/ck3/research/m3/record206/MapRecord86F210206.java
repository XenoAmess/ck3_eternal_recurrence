package org.xar.ck3.research.m3.record206;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
public final class MapRecord86F210206 {
    private MapRecord86F210206() {
    }
    public static long store(NativeTaskMemory memory, long output, long map) {
        memory.writeInt64(output, map);
        return output;
    }
}
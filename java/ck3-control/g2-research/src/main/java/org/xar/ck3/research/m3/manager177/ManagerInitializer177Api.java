package org.xar.ck3.research.m3.manager177;

import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/** Normal business-field projection only. No prologue, EH, volatile-register or raw-RAX contract. */
public final class ManagerInitializer177Api {
    private ManagerInitializer177Api() { }
    public interface Memory extends NativeTaskMemory { void writeByte(long address, int lowByte); }
    public interface Ports {
        long context(long siteRva, Memory memory);
        long allocateObject(long siteRva, Memory memory, int bytes);
        long allocatorProvider(long siteRva, Memory memory);
        void initializeMap(long siteRva, Memory memory, long receiver);
        long allocateSlots(long siteRva, Memory memory, long target, long allocator, int bytes, int alignment);
        void copy(long siteRva, Memory memory, long destination, long source, long bytes);
        void releaseSlots(long siteRva, Memory memory, long target, long allocator, long data, int alignment);
        void destroyOld(long siteRva, Memory memory, long object);
        void freeOld(long siteRva, Memory memory, long object, int bytes);
    }
    /** globalValue is source-observed guard or final published value, not a claim about raw native RAX. */
    public record Outcome(boolean initialized, long globalValue) { }
    public record Cell(long address, int width, long value) { }
    /** Exact global script: reads/writes use {address,value}; callbacks use known source operands below. */
    public record Step(String kind, long[] args, long returned, List<Cell> effects) { }
    public record Scene(String name, long imageBase, List<Cell> initial, List<Step> steps,
                        Outcome expected, List<Cell> finalCells) { }
}

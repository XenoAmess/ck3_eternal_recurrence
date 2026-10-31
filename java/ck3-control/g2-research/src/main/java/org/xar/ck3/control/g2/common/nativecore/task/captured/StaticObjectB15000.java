package org.xar.ck3.control.g2.common.nativecore.task.captured;
/** Source93B supplied-storage effects, GS slot supplied explicitly; no current process/thread binding. */
public final class StaticObjectB15000 {
 private StaticObjectB15000() { }
 public interface Ports {
  /** Returns the supplied QWORD value read from GS:[0x58], not a GS/TLS base; get dereferences this slot. */
  long readGs58();
  /** RCX-only opaque projection; the source also has known RDX=16, outside this interface. Not a native ABI. */
  void call4223a84(long rcx);
  /** RCX-only opaque projection; remaining inputs and helper effects are unspecified. */
  void call4223a24(long rcx);
 }
public static long get(long moduleBase, SparseIntCells177.Memory memory, Ports ports) {
    final long slot = ports.readGs58();
    final long tlsBase = memory.readPointer(slot);
    final int epoch = memory.readInt32(tlsBase + 0x10L);
    final long guard = moduleBase + 0x5D1EB08L;
    if (memory.readInt32(guard) > epoch) {
        ports.call4223a84(guard);
        if (memory.readInt32(guard) == -1) {
            memory.writeByte(moduleBase + 0x5D1EAF0L, (byte) 0);
            memory.writeByte(moduleBase + 0x5D1EAFCL, (byte) 0xFF);
            ports.call4223a24(guard);
        }
    }
    return moduleBase + 0x5D1EAF0L;
}
}

package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
import java.util.concurrent.atomic.*;
/** Supplied-memory composition of known caller projections; no live native ABI or Game execution. */
public class Sparse177EndToEndTest {
@Test
public void event79eComposesClearAnd177Insert() {
    Sparse177TestMemory memory = new Sparse177TestMemory();
    Idler79eRegressionHost.Memory bytes = memory.bytes();
    long moduleBase = 0x50000000L;
    long header = 0x300000L;
    long event = bytes.allocate(16);
    long global = bytes.allocate(0xA8);
    long cells = bytes.allocate(120);
    bytes.map(header, 0x40);
    bytes.map(moduleBase + 0x5CC1628L, 4);
    bytes.map(moduleBase + 0x5C6A520L, 8);
    bytes.map(moduleBase + 0x5C68C50L, 8);
    bytes.seedInt64(moduleBase + 0x5C68C50L, global);
    bytes.seedInt64(global + 0xA0, header - 0x222E8);
    bytes.seedInt32(event + 4, 0x10203040);
    bytes.seedInt32(event + 8, 1);
    bytes.seedInt64(header + 0x20, cells);
    bytes.seedInt32(header + 0x28, 2);
    bytes.seedInt32(header + 0x2C, 7);
    bytes.seedByte(header + 0x30, 2);
    bytes.seedInt32(header + 0x34, Float.floatToRawIntBits(0.75f));
    bytes.seedByte(cells, 1);
    bytes.seedInt32(cells + 4, 0x12345678);
    bytes.seedInt32(cells + 8, 0x10203040);
    bytes.seedByte(cells + 12, 1);
    bytes.seedInt32(cells + 16, 7);
    bytes.seedInt32(cells + 20, 9);
    bytes.onAccess((storage, access) -> {
        if (access.op() == Idler79eRegressionHost.Op.DEC32
                && access.address() == header + 0x28 && access.value() == 0) {
            storage.seedInt32(event + 8, 0xCAFEBABE);
        }
    });
    AtomicInteger continuationCalls = new AtomicInteger();
    AtomicLong returnedOutput = new AtomicLong();
    Idler79eContinuationPorts ports = new Idler79eContinuationPorts(
        known -> { throw new AssertionError("root callback must be skipped"); },
        known -> {
            assertEquals(1, continuationCalls.incrementAndGet());
            assertEquals(header + 0x18, known.rcx());
            assertEquals(0xA3649785, known.r8d());
            assertEquals(0x12345678, known.savedR8d60());
            assertEquals(0xCAFEBABE, known.savedEdx58());
            assertEquals(Idler28eed20.FrameAddress.LOCAL_OUT_30, known.rdx());
            assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_R8D_60, known.r9());
            assertEquals(Idler28eed20.FrameAddress.SAVED_ORIGINAL_EDX_58, known.stack28());
            assertEquals(0, bytes.peekInt32(header + 0x28));
            assertEquals(0, bytes.peekUnsignedByte(cells));
            assertEquals(0, bytes.peekUnsignedByte(cells + 12));
            long output = bytes.allocate(16);
            long keyHome = bytes.allocate(4);
            long valueHome = bytes.allocate(4);
            bytes.seedInt32(keyHome, known.savedR8d60());
            bytes.seedInt32(valueHome, known.savedEdx58());
            bytes.seedInt64(output + 8, 0x7766554433221100L);
            SparseIntCells177.Ports opaque = new SparseIntCells177.Ports() {
                @Override public void call177fbd0(long rcx) {
                    throw new AssertionError("grow must not be called");
                }
                @Override public void call1783480(SparseIntCells177.Known1783480 ignored) {
                    throw new AssertionError("fallback must not be called");
                }
                @Override public SparseIntCells177.Raw128 call17836d0(SparseIntCells177.Known17836d0 ignored) {
                    throw new AssertionError("relocation helper must not be called");
                }
            };
            long actual = SparseIntCells177.put(known.rcx(), output, known.r8d(),
                    keyHome, valueHome, memory, opaque);
            assertEquals(output, actual);
            assertEquals(cells + 5 * 12, bytes.peekInt64(output));
            assertEquals(0x7766554433221101L, bytes.peekInt64(output + 8));
            returnedOutput.set(actual);
            return actual;
        });
    assertEquals(1, Idler79eEvent.handle79e(moduleBase, event, bytes, ports));
    assertEquals(1, continuationCalls.get());
    assertNotEquals(0L, returnedOutput.get());
    assertEquals(1, bytes.peekInt32(header + 0x28));
    assertEquals(0, bytes.peekUnsignedByte(cells));
    assertEquals(0, bytes.peekUnsignedByte(cells + 12));
    long inserted = cells + 5 * 12;
    assertEquals(1, bytes.peekUnsignedByte(inserted));
    assertEquals(0x12345678, bytes.peekInt32(inserted + 4));
    assertEquals(0xCAFEBABE, bytes.peekInt32(inserted + 8));
    assertEquals(1, memory.effects().size());
    assertEquals(Sparse177TestMemory.Primitive.INC32, memory.effects().get(0).primitive());
    assertEquals(header + 0x28, memory.effects().get(0).address());
}

}

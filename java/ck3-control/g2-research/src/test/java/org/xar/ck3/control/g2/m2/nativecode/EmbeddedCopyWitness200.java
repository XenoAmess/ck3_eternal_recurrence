package org.xar.ck3.control.g2.m2.nativecode;
import java.util.List;
import org.xar.ck3.control.g2.m2.nativecode.PendingEmbeddedCopy373ACF0.Memory;

public final class EmbeddedCopyWitness200 {
    public static int verify() {
        int count = 0;
        for (EmbeddedCopyScenario200.Scene scene : EmbeddedCopyCases200.scenes()) {
            List<EmbeddedCopyScenario200.Step> expected = scene.steps();
            int[] cursor = new int[1];

            class Script implements PendingEmbeddedCopy373ACF0.Memory, PendingEmbeddedCopy373ACF0.Calls {
                @Override
                public void write16(long address, int value) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.W16) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    if (step.b() != (value & 0xffffL)) throw new AssertionError("value mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void call8895D0(Memory memory, long rcx, long rdx) {
                    if (memory != this) throw new AssertionError("callee memory mismatch");
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.C889) throw new AssertionError("op mismatch");
                    if (step.a() != rcx) throw new AssertionError("rcx mismatch");
                    if (step.b() != rdx) throw new AssertionError("rdx mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void call37282B0(Memory memory, long rcx, long rdx) {
                    if (memory != this) throw new AssertionError("callee memory mismatch");
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.C37282) throw new AssertionError("op mismatch");
                    if (step.a() != rcx) throw new AssertionError("rcx mismatch");
                    if (step.b() != rdx) throw new AssertionError("rdx mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void call260E040(Memory memory, long rcx, long rdx) {
                    if (memory != this) throw new AssertionError("callee memory mismatch");
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.C260) throw new AssertionError("op mismatch");
                    if (step.a() != rcx) throw new AssertionError("rcx mismatch");
                    if (step.b() != rdx) throw new AssertionError("rdx mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void call3727180(Memory memory, long rcx, long rdx) {
                    if (memory != this) throw new AssertionError("callee memory mismatch");
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.C37271) throw new AssertionError("op mismatch");
                    if (step.a() != rcx) throw new AssertionError("rcx mismatch");
                    if (step.b() != rdx) throw new AssertionError("rdx mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void write8(long address, int value) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.W8) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    if (step.b() != (value & 0xffL)) throw new AssertionError("value mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void write32(long address, int value) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.W32) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    if (step.b() != Integer.toUnsignedLong(value)) throw new AssertionError("value mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public void write64(long address, long value) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.W64) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    if (step.b() != value) throw new AssertionError("value mismatch");
                    if (step.c() != 0L) throw new AssertionError("c mismatch");
                }

                @Override
                public int read32(long address) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.R32) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    return (int) step.b();
                }

                @Override
                public long read64(long address) {
                    throw new AssertionError("unexpected read64");
                }

                @Override
                public PendingContextCopy3076B60.Bits128 read128(long address) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.R128) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    return new PendingContextCopy3076B60.Bits128(step.b(), step.c());
                }

                @Override
                public void write128(long address, PendingContextCopy3076B60.Bits128 value) {
                    if (cursor[0] >= expected.size()) throw new AssertionError("unconsumed");
                    EmbeddedCopyScenario200.Step step = expected.get(cursor[0]++);
                    if (step.op() != EmbeddedCopyScenario200.Op.W128) throw new AssertionError("op mismatch");
                    if (step.a() != address) throw new AssertionError("address mismatch");
                    if (step.b() != value.low()) throw new AssertionError("low mismatch");
                    if (step.c() != value.high()) throw new AssertionError("high mismatch");
                }
            }

            Script script = new Script();
            long result = PendingEmbeddedCopy373ACF0.copy(script, script, scene.destination(), scene.source(), scene.moduleBase());
            if (result != scene.destination()) throw new AssertionError("return mismatch");
            if (cursor[0] != expected.size()) throw new AssertionError("unconsumed steps");
            count++;
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}
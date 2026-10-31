package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Consumer;
import org.xar.ck3.control.g2.common.nativecore.task.captured.Idler79eRegressionHost;

/** Test-only thin adapter to the existing formal79E byteimage, two genuinely new width primitives. */
public final class Sparse177TestMemory implements SparseIntCells177.Memory {

    public enum Primitive {
        INC32,
        WRITE128
    }

    public record Effect(Primitive primitive, long address, long low, long high) {
    }

    private final Idler79eRegressionHost.Memory backing;
    private final List<Effect> effects;
    private Consumer<Effect> primitiveObserver;

    public Sparse177TestMemory() {
        this.backing = new Idler79eRegressionHost.Memory();
        this.effects = new ArrayList<>();
        this.primitiveObserver = null;
    }

    public Idler79eRegressionHost.Memory bytes() {
        return backing;
    }

    public List<Effect> effects() {
        return Collections.unmodifiableList(new ArrayList<>(effects));
    }

    public void afterPrimitive(Consumer<Effect> observer) {
        this.primitiveObserver = observer;
    }

    public long readPointer(long address) {
        return backing.readPointer(address);
    }

    public int readInt32(long address) {
        return backing.readInt32(address);
    }

    public int readUnsignedByte(long address) {
        return backing.readUnsignedByte(address);
    }

    public void writeInt32(long address, int value) {
        backing.writeInt32(address, value);
    }

    public void writeInt64(long address, long value) {
        backing.writeInt64(address, value);
    }

    public void writeByte(long address, byte value) {
        backing.writeByte(address, value);
    }

    public void incrementInt32(long address) {
        int prior = backing.peekInt32(address);
        int next = prior + 1;
        backing.seedInt32(address, next);
        Effect effect = new Effect(Primitive.INC32, address, (long) next, 0L);
        effects.add(effect);
        if (primitiveObserver != null) {
            primitiveObserver.accept(effect);
        }
    }

    public void writeRaw128(long address, SparseIntCells177.Raw128 bits) {
        // Validate both QWORD destination slices with backing.peekInt64 before either mutation
        backing.peekInt64(address);
        backing.peekInt64(address + 8L);

        backing.seedInt64(address, bits.low());
        backing.seedInt64(address + 8L, bits.high());

        Effect effect = new Effect(Primitive.WRITE128, address, bits.low(), bits.high());
        effects.add(effect);
        if (primitiveObserver != null) {
            primitiveObserver.accept(effect);
        }
    }
}

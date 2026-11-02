package org.xar.ck3.study.m6.indexed229;

import java.util.Objects;
import org.xar.ck3.research.m3.indexed225.IndexedHelper225Api;
import org.xar.ck3.research.m3.indexed225.IndexedLookupHelper424E448;

/**
 * Real NEW229 same-RAM single-effect exchange bridge required by held470B uncached producer.
 * Reuses the complete current mature IndexedLookupHelper424E448 scalar/business algorithm unchanged.
 * This bridge is an independent public production consumer.
 */
public final class Indexed448AtomicBridge229 {
    private Indexed448AtomicBridge229() { }

    /**
     * Captures the same underlying RAM via an anonymous IndexedHelper225Api.Memory view.
     * Each method performs exactly one primitive delegation to the AtomicIndexedMemory229.
     */
    public static IndexedHelper225Api.Memory asIndexed(AtomicIndexedMemory229 memory) {
        Objects.requireNonNull(memory);
        return new IndexedHelper225Api.Memory() {
            @Override
            public long readPointer(long address) {
                return memory.readQword(address);
            }

            @Override
            public int readInt32(long address) {
                return memory.readDword(address);
            }

            @Override
            public void writeInt32(long address, int value) {
                memory.writeDword(address, value);
            }

            @Override
            public void writeInt64(long address, long value) {
                memory.writeQword(address, value);
            }

            @Override
            public long exchangeInt64(long address, long newValue) {
                return memory.exchangeQword(address, newValue);
            }
        };
    }

    /**
     * Executes the mature helper once using the captured view.
     * No copied loader/list/cookie/rotate algorithm, no retry/replay, no catching opaque port exceptions.
     */
    public static long execute(AtomicIndexedMemory229 memory, IndexedHelper225Api.Ports ports, IndexedHelper225Api.Input input) {
        return IndexedLookupHelper424E448.execute(asIndexed(memory), ports, input);
    }
}
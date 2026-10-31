package org.xar.ck3.control.g2.common.nativecore.task;

import org.xar.ck3.control.g2.common.nativecore.task.retained.Idler480Init;
import org.xar.ck3.control.g2.common.nativecore.task.retained.Idler480Ports;

/**
 * Public construction facade for native idler initialization.
 * Delegates to the retained kernel {@code Idler480Init.init} using exact supplied parameters.
 * Adapters preserve call ordering, argument values, and return types without pre-resolution or caching.
 * Caller owns real callback semantics; no address validation or game attachment is performed.
 */
public final class NativeIdlerConstruction {

    public interface Symbols {
        long address(long rva);
    }

    public record Descriptor(long data, int length, byte flag) {
    }

    public interface Calls {
        long allocate(long size);
        long constructChild(long storage, long freshH, int zero);
        long getRegistry(long architecturalRcx);
        long findName(long registry, Descriptor knownDescriptorFields);
        void virtual30(long receiver, long lookupResult, long savedO50);
    }

    private NativeIdlerConstruction() {
    }

    public static long construct(long object, long inputH, long inputK, NativeTaskMemory memory, Symbols symbols, Calls calls) {
        // Adapter for Symbols: delegates each address call lazily to preserve ordering and exact rva values.
        Idler480Ports.Symbols symbolsAdapter = new Idler480Ports.Symbols() {
            @Override
            public long address(long rva) {
                return symbols.address(rva);
            }
        };

        // Adapter for Calls: delegates each callback exactly, preserving order, args, returns, and exceptions.
        // findName converts the retained Descriptor to the public Descriptor with exact field values.
        Idler480Ports.Calls callsAdapter = new Idler480Ports.Calls() {
            @Override
            public long allocate(long size) {
                return calls.allocate(size);
            }

            @Override
            public long constructChild(long storage, long freshH, int zero) {
                return calls.constructChild(storage, freshH, zero);
            }

            @Override
            public long getRegistry(long architecturalRcx) {
                return calls.getRegistry(architecturalRcx);
            }

            @Override
            public long findName(long registry, Idler480Ports.Descriptor knownDescriptorFields) {
                // Convert retained Descriptor to public Descriptor with exact values
                Descriptor publicDescriptor = new Descriptor(
                    knownDescriptorFields.data(),
                    knownDescriptorFields.length(),
                    knownDescriptorFields.flag()
                );
                return calls.findName(registry, publicDescriptor);
            }

            @Override
            public void virtual30(long receiver, long lookupResult, long savedO50) {
                calls.virtual30(receiver, lookupResult, savedO50);
            }
        };

        // Delegate to retained kernel with exact object, inputH, inputK, and memory.
        return Idler480Init.init(object, inputH, inputK, memory, symbolsAdapter, callsAdapter);
    }
}

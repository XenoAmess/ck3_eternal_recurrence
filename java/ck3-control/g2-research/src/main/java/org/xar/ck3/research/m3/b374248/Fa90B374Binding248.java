package org.xar.ck3.research.m3.b374248;

import java.util.OptionalLong;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.m4cleanup.b374.B374Inputs;

/**
 * Thin consumer binding for Fa90Api245.Ports.
 * Active only on call42566fc at siteRVA 0x424FAD3 with original captured memory identity.
 * Delegates to mature B374Candidate.execute using a nominal view of the captured memory.
 * Passive callbacks forward exactly to fallback.
 */
public final class Fa90B374Binding248 {

    private Fa90B374Binding248() {
    }

    public static Fa90Api245.Ports bind(
            long moduleBase,
            F8a8Api242.Memory capturedMemory,
            B374Inputs.Calls matureCalls,
            Fa90Api245.Ports fallback) {

        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (matureCalls == null) {
            throw new RuntimeException("matureCalls");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new Binding(moduleBase, capturedMemory, matureCalls, fallback);
    }

    private static final class Binding implements Fa90Api245.Ports {
        private final long moduleBase;
        private final F8a8Api242.Memory capturedMemory;
        private final B374Inputs.Calls matureCalls;
        private final Fa90Api245.Ports fallback;
        private final B374Inputs.Memory view;

        Binding(long moduleBase, F8a8Api242.Memory capturedMemory, B374Inputs.Calls matureCalls, Fa90Api245.Ports fallback) {
            this.moduleBase = moduleBase;
            this.capturedMemory = capturedMemory;
            this.matureCalls = matureCalls;
            this.fallback = fallback;
            this.view = new B374MemoryView(capturedMemory);
        }

        @Override
        public void call42568fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax) {
            fallback.call42568fc(memory, siteRva, knownRcx, knownRdx, liveRax);
        }

        @Override
        public void call42566fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long liveRax) {
            if (memory != capturedMemory) {
                throw new RuntimeException("memory identity");
            }
            if (siteRva != 0x424FAD3L) {
                throw new RuntimeException("siteRva");
            }
            B374Inputs.CallInput input = new B374Inputs.CallInput(moduleBase, knownRcx);
            B374Candidate.execute(input, view, matureCalls);
        }

        @Override
        public void call4256670(F8a8Api242.Memory memory, long siteRva, long knownRcx, OptionalLong knownRdx, OptionalLong knownRax) {
            fallback.call4256670(memory, siteRva, knownRcx, knownRdx, knownRax);
        }
    }

    private static final class B374MemoryView implements B374Inputs.Memory {
        private final F8a8Api242.Memory backing;

        B374MemoryView(F8a8Api242.Memory backing) {
            this.backing = backing;
        }

        @Override
        public long readPointer(long address) {
            return backing.readPointer(address);
        }

        @Override
        public int readInt32(long address) {
            return backing.readInt32(address);
        }

        @Override
        public void writeInt32(long address, int value) {
            backing.writeInt32(address, value);
        }

        @Override
        public void writeInt64(long address, long value) {
            backing.writeInt64(address, value);
        }
    }
}
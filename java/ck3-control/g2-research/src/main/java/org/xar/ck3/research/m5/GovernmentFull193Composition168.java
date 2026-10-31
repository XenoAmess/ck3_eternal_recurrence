package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Calls;
import org.xar.ck3.research.m1.GovernmentLookup167Api;
import org.xar.ck3.research.m1.GovernmentLookup167;
import org.xar.ck3.research.m1.GovernmentLookup167Adapter;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api;
import org.xar.ck3.research.m5.GovernmentByteHash169;
import org.xar.ck3.research.m5.GovernmentResult168Api;
import org.xar.ck3.research.m5.GovernmentResult168Calls;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;

public final class GovernmentFull193Composition168 {
    private GovernmentFull193Composition168() { }

    public static NormalReturn execute(
            Entry entry,
            GovernmentFull193Composition168Api.Memory memory,
            Calls opaqueCalls,
            Mxcsr32 hashMxcsrAt2D0B4FE,
            GovernmentByteUpdate169Api.LoopBudget hashBudget,
            GovernmentLookup167Api.SpinBudget lookupBudget,
            GovernmentResult168Api.WorkBudget resultBudget) {

        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(opaqueCalls);
        Objects.requireNonNull(hashMxcsrAt2D0B4FE);
        Objects.requireNonNull(hashBudget);
        Objects.requireNonNull(lookupBudget);
        Objects.requireNonNull(resultBudget);

        long image = entry.imageBaseBits();

        // 1. Bind Manager Adapter (handles 3F8A7E0)
        // The manager adapter expects GovernmentSharedManager167Api.Memory which extends PrimaryTail155.Memory.
        // Our input memory is the intersection, so it satisfies the requirement.
        Calls managerCalls = GovernmentSharedManager167Calls.bind(image, memory, opaqueCalls);

        // 2. Bind Lookup Adapter (handles 3F8A6D0)
        // The lookup adapter expects PrimaryTail155.Memory and PrimaryTail155.Calls.
        // We pass the managerCalls as the fallback for the lookup adapter, so lookup can call manager if needed.
        // The target is the concrete method reference.
        GovernmentLookup167Api.Target lookupTarget = GovernmentLookup167::execute;
        Calls lookupCalls = new GovernmentLookup167Adapter(image, memory, managerCalls, lookupTarget, lookupBudget);

        // 3. Bind Result Adapter (handles 16F40A0)
        // The result adapter expects PrimaryTail155.Memory and PrimaryTail155.Calls.
        // We pass lookupCalls as the fallback.
        Calls resultCalls = GovernmentResult168Calls.bind(image, memory, lookupCalls, resultBudget);

        // 4. Bind Hash Adapter (handles 3F7E220)
        // This is the new private adapter required by the contract.
        // It wraps resultCalls as the fallback.
        Calls hashCalls = new HashAdapter(image, memory, resultCalls, hashMxcsrAt2D0B4FE, hashBudget);

        // Execute the parent callee with the fully assembled call chain.
        return GovernmentCallee164.execute(entry, memory, hashCalls);
    }

    private static final class HashAdapter implements Calls {
        private final long imageBaseBits;
        private final GovernmentFull193Composition168Api.Memory memory;
        private final Calls fallback;
        private final Mxcsr32 mxcsrInput;
        private final GovernmentByteUpdate169Api.LoopBudget budget;

        HashAdapter(long imageBaseBits, GovernmentFull193Composition168Api.Memory memory, Calls fallback, Mxcsr32 mxcsrInput, GovernmentByteUpdate169Api.LoopBudget budget) {
            this.imageBaseBits = imageBaseBits;
            this.memory = Objects.requireNonNull(memory);
            this.fallback = Objects.requireNonNull(fallback);
            this.mxcsrInput = Objects.requireNonNull(mxcsrInput);
            this.budget = Objects.requireNonNull(budget);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            Objects.requireNonNull(call);

            // Intercept only the specific hash call site and target
            if (call.callSiteRva() == 0x2D0B4FEL && call.targetRva() == 0x3F7E220L) {
                return handleHashCall(call);
            }

            return fallback.invoke(call);
        }

        private VolatileBits handleHashCall(OpaqueCall call) {
            long p = call.rspBits();
            long returnAddr = imageBaseBits + 0x2D0B503L;
            long s = p - 8L;

            // Materialize the native CALL push
            memory.writeQword(s, returnAddr);

            // Construct the entry for the hash wrapper
            // The hash wrapper expects GovernmentByteUpdate169Api.Entry
            GovernmentByteUpdate169Api.Entry hashEntry = new GovernmentByteUpdate169Api.Entry(
                imageBaseBits,
                s,
                call.volatileBits(),
                call.nonvolatileBits(),
                mxcsrInput
            );

            // Execute the concrete hash wrapper
            GovernmentByteUpdate169Api.NormalReturn result = GovernmentByteHash169.execute(hashEntry, memory, budget);

            // Validate boundaries and state preservation
            if (result.returnRipBits() != returnAddr) {
                throw new UnsupportedOperationException("Hash target returned unexpected RIP");
            }
            if (result.callerRspBits() != p) {
                throw new UnsupportedOperationException("Hash target returned unexpected caller RSP");
            }

            NonvolatileBits incoming = call.nonvolatileBits();
            NonvolatileBits restored = result.nonvolatileBits();

            if (incoming.rbxBits() != restored.rbxBits() ||
                incoming.rbpBits() != restored.rbpBits() ||
                incoming.rsiBits() != restored.rsiBits() ||
                incoming.rdiBits() != restored.rdiBits() ||
                incoming.r12Bits() != restored.r12Bits() ||
                incoming.r13Bits() != restored.r13Bits() ||
                incoming.r14Bits() != restored.r14Bits() ||
                incoming.r15Bits() != restored.r15Bits() ||
                !incoming.xmm6().equals(restored.xmm6())) {
                throw new UnsupportedOperationException("Hash target failed to preserve nonvolatile state");
            }

            if (!result.mxcsr().equals(mxcsrInput)) {
                throw new UnsupportedOperationException("Hash target MXCSR mismatch");
            }

            return result.volatileBits();
        }
    }
}

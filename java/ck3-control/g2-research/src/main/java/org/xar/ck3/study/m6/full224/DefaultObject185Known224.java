package org.xar.ck3.study.m6.full224;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m4.Retry60NormalFullState284;

/**
 * Actual full represented185 Entry consumers for DefaultObject185Known224.
 * Intercepts specific call/tail sites to route to mature Retry60NormalFullState284 and DefaultFreeThunks185224.
 * Delegates all other operations to supplied lower ports.
 */
public final class DefaultObject185Known224 {
    private DefaultObject185Known224() { }

    /**
     * fromSlot08: Actual 18B8571D0 wrapper.
     * Intercepts invoke at 0x8571D7 targeting 0x4223B94.
     * Constructs child entry and executes Retry60NormalFullState284.
     */
    public static NormalReturn fromSlot08(Entry entry, Memory memory, Calls lower, LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        // lower and budget may be null if not used by the specific path, but adapter creation is lazy/eager?
        // Contract says: "ZeroRDX fromSlot10 must remain legal with null lower/budget because actual wrapper shortcircuits, no eager lower/budget validation in adapter creation."
        // This implies we should NOT validate lower/budget if they are not needed for the specific branch taken by the wrapper.
        // However, fromSlot08 ALWAYS takes the CALL path (SUB RSP, MOV RCX, CALL). It does not shortcircuit on RDX.
        // So lower/budget are required for fromSlot08.
        Objects.requireNonNull(lower);
        Objects.requireNonNull(budget);

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Create adapter that intercepts the specific call site
        Calls adapter = new Calls() {
            @Override public VolatileBits invoke(Call call) {
                if (call.callSiteRva() == 0x8571D7L
                        && call.kind() == TargetKind.DIRECT_RVA
                        && call.targetBits() == 0x4223B94L) {

                    // Actual caller already wrote childRET[call.rspBits-0x8] in the wrapper logic (simulated by the adapter's context or assumed by the contract description of the wrapper).
                    // The contract says: "Actual caller already wrote childRET[call.rspBits-0x8]; construct actual childEntry..."
                    // This implies the memory write happened in the wrapper (DefaultObject185Wrappers224.fromSlot08) before calling invoke.
                    // We just need to construct the child entry and execute the mature consumer.

                    long childSP = call.rspBits() - 0x8L;
                    Entry childEntry = new Entry(image, childSP, call.volatileBits(), call.nonvolatileBits());

                    // Execute mature Retry60NormalFullState284
                    NormalReturn childNR = Retry60NormalFullState284.execute(childEntry, memory, lower, budget);

                    // Validate ACTUAL returned NR
                    long expectedRip = image + 0x8571DCL;
                    long expectedCallerSP = call.rspBits();

                    if (childNR.returnRipBits() != expectedRip) {
                        throw new IllegalStateException("Invalid return RIP: expected " + Long.toHexString(expectedRip) + " got " + Long.toHexString(childNR.returnRipBits()));
                    }
                    if (childNR.callerRspBits() != expectedCallerSP) {
                        throw new IllegalStateException("Invalid caller SP: expected " + Long.toHexString(expectedCallerSP) + " got " + Long.toHexString(childNR.callerRspBits()));
                    }
                    if (!childNR.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("Nonvolatile bits mismatch");
                    }

                    return childNR.volatileBits();
                }
                return lower.invoke(call);
            }

            @Override public NormalReturn tail(Tail transfer) {
                // fromSlot08 does not use tail, but adapter must handle it if called (though wrapper logic for 08 doesn't call tail).
                // Delegate to lower.
                return lower.tail(transfer);
            }

            @Override public long readGsQword58() {
                return lower.readGsQword58();
            }
        };

        // Call the actual wrapper with the adapter
        return DefaultObject185Wrappers224.fromSlot08(entry, memory, adapter);
    }

    /**
     * fromSlot10: Actual 14B8571C0 wrapper.
     * Intercepts tail at 0x8571C8 targeting 0x40EC530.
     * Shortcircuits on RDX==0 (no adapter needed for lower/budget in that case).
     */
    public static NormalReturn fromSlot10(Entry entry, Memory memory, Calls lower, LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        // lower and budget are NOT required if RDX is 0, as per contract.
        // We pass them to the adapter, but the adapter creation itself doesn't validate them if not used.
        // However, the wrapper fromSlot10 checks RDX. If RDX != 0, it calls tail.
        // If RDX == 0, it returns directly without calling tail or invoke.

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Check if we need the adapter. If RDX is 0, the wrapper shortcircuits.
        // But we must provide an adapter to the wrapper if it takes the non-zero path.
        // The wrapper signature is fromSlot10(Entry, Memory, Calls).
        // We create the adapter lazily or always? The contract says "no eager lower/budget validation in adapter creation".
        // This suggests we can create the adapter object even if lower is null, as long as we don't call methods that use it.

        Calls adapter = new Calls() {
            @Override public VolatileBits invoke(Call call) {
                // fromSlot10 wrapper does not call invoke (it calls tail or returns).
                // But if it did, we delegate.
                if (lower == null) {
                    throw new IllegalStateException("Lower calls required for invoke");
                }
                return lower.invoke(call);
            }

            @Override public NormalReturn tail(Tail transfer) {
                if (transfer.jumpSiteRva() == 0x8571C8L
                        && transfer.kind() == TargetKind.DIRECT_RVA
                        && transfer.targetBits() == 0x40EC530L
                        && transfer.entry().imageBaseBits() == image) {

                    // Intercept tail to 40EC530
                    // Execute DefaultFreeThunks185224
                    // Note: DefaultFreeThunks185224.execute takes (Entry, Memory, Calls lower).
                    // We pass the original 'lower' to the thunk, not the adapter, because the thunk's internal logic
                    // (Free61FullState201) expects the original lower ports for its own calls.
                    // The adapter is only for the wrapper's interaction.

                    if (lower == null) {
                         throw new IllegalStateException("Lower calls required for tail interception");
                    }

                    return DefaultFreeThunks185224.execute(transfer.entry(), memory, lower);
                }

                if (lower == null) {
                    throw new IllegalStateException("Lower calls required for tail delegation");
                }
                return lower.tail(transfer);
            }

            @Override public long readGsQword58() {
                if (lower == null) {
                    throw new IllegalStateException("Lower calls required for readGsQword58");
                }
                return lower.readGsQword58();
            }
        };

        return DefaultObject185Wrappers224.fromSlot10(entry, memory, adapter);
    }
}
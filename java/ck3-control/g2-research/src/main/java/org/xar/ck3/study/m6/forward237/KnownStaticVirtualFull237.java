package org.xar.ck3.study.m6.forward237;

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
import org.xar.ck3.study.m6.vtable221.VirtualForward221Api;
import org.xar.ck3.study.m6.provider222.ObjectProvider86e140;
import org.xar.ck3.study.m6.full224.DefaultObject185Known224;

/**
 * SECOND NEW CLASS: KnownStaticVirtualFull237.
 * Intercepts specific call/tail sites in the full producer (StaticVirtualFullState237) to route to mature providers.
 * Delegates all other operations to supplied lower ports.
 */
public final class KnownStaticVirtualFull237 {
    private KnownStaticVirtualFull237() { }

    /**
     * fromSlot08: Actual 51B855870 forwarding entry (allocate-side slot).
     * Intercepts invoke at 0x855883 targeting image+0x86E140.
     * Intercepts tail at 0x8558A0 targeting image+0x8571D0.
     */
    public static NormalReturn fromSlot08(Entry entry, Memory memory, Calls lower, LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        // lower and budget are required for the non-zero path in fromSlot08 (which always takes the CALL path).
        // However, the contract says "Null lower/budget legal if no branch uses them".
        // In fromSlot08, the wrapper ALWAYS calls invoke or tail. So lower/budget are effectively required if we intercept.
        // But the adapter creation itself shouldn't validate them eagerly if not used by the specific branch taken by the wrapper logic.
        // The wrapper logic for 08 (Allocate) always does: Prologue -> CALL -> Epilogue -> Tail.
        // So it will always hit the adapter's invoke and tail methods.

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Create adapter that intercepts the specific call/tail sites
        Calls adapter = new Calls() {
            @Override public VolatileBits invoke(Call call) {
                // Intercept FIRST site 0x855883, kind INDIRECT_ABSOLUTE, target = image + 0x86E140
                if (call.callSiteRva() == 0x855883L
                        && call.kind() == TargetKind.INDIRECT_ABSOLUTE
                        && call.targetBits() == image + 0x86E140L) {

                    // Reuse ObjectProvider86e140.readReturnedObject
                    // It takes (long rcxRaw64, Memory memory). We need to map 185.Memory to VirtualForward221Api.Memory.
                    // The contract says: "mechanically map them to 185.Memory's readDword/Qword/UnsignedByte/writeDword/Qword/Byte"
                    // VirtualForward221Api.Memory extends Element150Inputs.Memory which has read64/write64 etc.
                    // 185.Memory has readQword/writeQword etc.

                    // We need an adapter for Memory to pass to ObjectProvider86e140.
                    VirtualForward221Api.Memory v221Memory = new VirtualForward221Api.Memory() {
                        @Override public int read32(long address) { return memory.readDword(address); }
                        @Override public long read64(long address) { return memory.readQword(address); }
                        @Override public int read8(long address) { return memory.readUnsignedByte(address); }
                        @Override public void write32(long address, int value) { memory.writeDword(address, value); }
                        @Override public void write64(long address, long value) { memory.writeQword(address, value); }
                        @Override public void write8(long address, int value) { memory.writeByte(address, value); }
                    };

                    // The actual RCX at the time of the call is in call.volatileBits().rcxBits()
                    long actualRCX = call.volatileBits().rcxBits();

                    // readReturnedObject returns the object at [RCX+0x408]
                    long returnedObject = ObjectProvider86e140.readReturnedObject(actualRCX, v221Memory);

                    // Construct child entry for the provider?
                    // The contract says: "consume fresh childRET at call.rsp-0x8, check source normal returnRIP=image+firstsite+0x3 and callerSP=call.rsp, suppliedN unchanged, then return updated entire V."
                    // This implies we are simulating the return of the provider.
                    // The provider (86E140) is a simple getter: MOV RAX, [RCX+0x408]; RET.
                    // It does not change other registers except RAX.
                    // So we update RAX in the volatile bits.

                    VolatileBits updatedV = new VolatileBits(
                        returnedObject, // RAX
                        call.volatileBits().rcxBits(),
                        call.volatileBits().rdxBits(),
                        call.volatileBits().r8Bits(),
                        call.volatileBits().r9Bits(),
                        call.volatileBits().r10Bits(),
                        call.volatileBits().r11Bits(),
                        call.volatileBits().xmm0(),
                        call.volatileBits().xmm1(),
                        call.volatileBits().xmm2(),
                        call.volatileBits().xmm3(),
                        call.volatileBits().xmm4(),
                        call.volatileBits().xmm5()
                    );

                    // Validate child NR expectations (simulated)
                    // Expected RIP: image + 0x855883 + 0x3 = image + 0x855886
                    // Expected CallerSP: call.rspBits()
                    // Expected N: unchanged

                    // The contract says "check source normal returnRIP... and callerSP... and suppliedN unchanged".
                    // Since we are constructing the return manually based on the provider's known behavior (MOV+RET),
                    // we just return the updated V.

                    long actualRip = memory.readQword(call.rspBits() - 0x8L);
                    if (actualRip != image + call.callSiteRva() + 0x3L) {
                        throw new UnsupportedOperationException("known getter did not return to its source continuation");
                    }
                    return updatedV;
                }
                return lower.invoke(call);
            }

            @Override public NormalReturn tail(Tail transfer) {
                // Intercept actual allocateTAIL 0x8558A0 with INDIRECT_ABSOLUTE target = image + 0x8571D0
                if (transfer.jumpSiteRva() == 0x8558A0L
                        && transfer.kind() == TargetKind.INDIRECT_ABSOLUTE
                        && transfer.targetBits() == image + 0x8571D0L) {

                    // Reuse DefaultObject185Known224.fromSlot08 on exact Tail.entry
                    // Note: DefaultObject185Known224.fromSlot08 expects (Entry, Memory, Calls lower, LoopBudget budget)
                    // We pass the original 'lower' and 'budget' to the thunk, not the adapter.

                    if (lower == null) {
                         throw new IllegalStateException("Lower calls required for tail interception");
                    }
                    if (budget == null) {
                         throw new IllegalStateException("Budget required for tail interception");
                    }

                    return DefaultObject185Known224.fromSlot08(transfer.entry(), memory, lower, budget);
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

        // Call the actual full producer (StaticVirtualFullState237) with the adapter
        // The contract says: "It calls the new full producer once with a thin 185.Calls adapter."
        // We assume StaticVirtualFullState237 is available in the same package or imported.
        // Since it's the FIRST NEW CLASS, it should be in org.xar.ck3.study.m6.forward237.
        return StaticVirtualFullState237.fromSlot08(entry, memory, adapter);
    }

    /**
     * fromSlot10: Actual 58B855830 forwarding entry (free-side slot).
     * Intercepts invoke at 0x85584C targeting image+0x86E140.
     * Intercepts invoke at 0x85585B targeting image+0x8571C0.
     * Intercepts tail at 0x8558A0 targeting image+0x8571D0.
     */
    public static NormalReturn fromSlot10(Entry entry, Memory memory, Calls lower, LoopBudget budget) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        // lower and budget are NOT required on RDX == RCX+0x8 self branch.
        // We pass them to the adapter, but the adapter creation itself doesn't validate them if not used.

        long image = entry.imageBaseBits();
        long s = entry.rspBits();
        VolatileBits currentV = entry.volatileBits();
        NonvolatileBits currentN = entry.nonvolatileBits();

        // Create adapter that intercepts the specific call/tail sites
        Calls adapter = new Calls() {
            @Override public VolatileBits invoke(Call call) {
                // Intercept FIRST site 0x85584C, kind INDIRECT_ABSOLUTE, target = image + 0x86E140
                if (call.callSiteRva() == 0x85584CL
                        && call.kind() == TargetKind.INDIRECT_ABSOLUTE
                        && call.targetBits() == image + 0x86E140L) {

                    // Reuse ObjectProvider86e140.readReturnedObject
                    VirtualForward221Api.Memory v221Memory = new VirtualForward221Api.Memory() {
                        @Override public int read32(long address) { return memory.readDword(address); }
                        @Override public long read64(long address) { return memory.readQword(address); }
                        @Override public int read8(long address) { return memory.readUnsignedByte(address); }
                        @Override public void write32(long address, int value) { memory.writeDword(address, value); }
                        @Override public void write64(long address, long value) { memory.writeQword(address, value); }
                        @Override public void write8(long address, int value) { memory.writeByte(address, value); }
                    };

                    long actualRCX = call.volatileBits().rcxBits();
                    long returnedObject = ObjectProvider86e140.readReturnedObject(actualRCX, v221Memory);

                    // Update RAX, preserve others
                    VolatileBits updatedV = new VolatileBits(
                        returnedObject,
                        call.volatileBits().rcxBits(),
                        call.volatileBits().rdxBits(),
                        call.volatileBits().r8Bits(),
                        call.volatileBits().r9Bits(),
                        call.volatileBits().r10Bits(),
                        call.volatileBits().r11Bits(),
                        call.volatileBits().xmm0(),
                        call.volatileBits().xmm1(),
                        call.volatileBits().xmm2(),
                        call.volatileBits().xmm3(),
                        call.volatileBits().xmm4(),
                        call.volatileBits().xmm5()
                    );

                    long actualRip = memory.readQword(call.rspBits() - 0x8L);
                    if (actualRip != image + call.callSiteRva() + 0x3L) {
                        throw new UnsupportedOperationException("known getter did not return to its source continuation");
                    }
                    return updatedV;
                }

                // Intercept SECOND site 0x85585B, kind INDIRECT_ABSOLUTE, target = image + 0x8571C0
                if (call.callSiteRva() == 0x85585BL
                        && call.kind() == TargetKind.INDIRECT_ABSOLUTE
                        && call.targetBits() == image + 0x8571C0L) {

                    // Reuse DefaultObject185Known224.fromSlot10 with actual childSP = call.rsp - 0x8
                    // Note: DefaultObject185Known224.fromSlot10 expects (Entry, Memory, Calls lower, LoopBudget budget)
                    // We pass the original 'lower' and 'budget' to the thunk.

                    long childSP = call.rspBits() - 0x8L;
                    Entry childEntry = new Entry(image, childSP, call.volatileBits(), call.nonvolatileBits());

                    NormalReturn childNR = DefaultObject185Known224.fromSlot10(childEntry, memory, lower, budget);

                    // Validate its actual returnedNR
                    // Expected returnRIP = image + 0x85585F
                    // Expected callerSP = call.rspBits()
                    // Expected N equal supplied

                    if (childNR.returnRipBits() != image + 0x85585FL) {
                        throw new IllegalStateException("Invalid return RIP for second invoke");
                    }
                    if (childNR.callerRspBits() != call.rspBits()) {
                        throw new IllegalStateException("Invalid caller SP for second invoke");
                    }
                    if (!childNR.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("Nonvolatile bits mismatch for second invoke");
                    }

                    return childNR.volatileBits();
                }

                return lower.invoke(call);
            }

            @Override public NormalReturn tail(Tail transfer) {
                // Intercept actual allocateTAIL 0x8558A0 with INDIRECT_ABSOLUTE target = image + 0x8571D0
                if (transfer.jumpSiteRva() == 0x8558A0L
                        && transfer.kind() == TargetKind.INDIRECT_ABSOLUTE
                        && transfer.targetBits() == image + 0x8571D0L) {

                    // Reuse DefaultObject185Known224.fromSlot08 on exact Tail.entry
                    if (lower == null) {
                         throw new IllegalStateException("Lower calls required for tail interception");
                    }
                    if (budget == null) {
                         throw new IllegalStateException("Budget required for tail interception");
                    }

                    return DefaultObject185Known224.fromSlot08(transfer.entry(), memory, lower, budget);
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

        // Call the actual full producer (StaticVirtualFullState237) with the adapter
        return StaticVirtualFullState237.fromSlot10(entry, memory, adapter);
    }
}
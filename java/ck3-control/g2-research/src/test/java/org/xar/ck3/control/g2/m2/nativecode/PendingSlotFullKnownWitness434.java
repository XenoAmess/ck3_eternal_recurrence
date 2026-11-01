package org.xar.ck3.control.g2.m2.nativecode;

import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallFrame;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.CallResult;
import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api.Input;
import static org.xar.ck3.control.g2.m2.nativecode.PendingSlotFullStateWitness424.*;

/** One new compound NORMAL software scene, independently derived from the supplied source. */
public final class PendingSlotFullKnownWitness434 {
    private PendingSlotFullKnownWitness434() { }

    public static int verify() {
        Mem mem = new Mem();
        Ports ports = new Ports(mem);
        long oldData = 0x8100000000003000L;
        long allocator = 0x8100000000006000L;
        long freshAllocator = 0x8100000000006100L;
        long vtable = 0x8100000000007000L;
        long freshVtable = 0x8100000000007100L;
        long allocateTarget = 0x7FFF111122223333L;
        long releaseTarget = 0x7FFF444455556666L;
        long table16 = M + 0x60900B0L + 16 * 4L;

        mem.seed(E, RET, 8);
        mem.seed(T + 0x40, 0, 1);
        mem.seed(T + 0x24, 0, 4);
        mem.seed(T + 0x20, 0, 4);
        mem.seed(T + 0x38, 0xFFFFFF, 4);
        mem.seed(T + 0x18, oldData, 8);
        mem.seed(T + 0x28, allocator, 8);
        mem.seed(allocator, vtable, 8);
        mem.seed(vtable + 8, allocateTarget, 8);
        mem.seed(freshAllocator, freshVtable, 8);
        mem.seed(freshVtable + 0x10, releaseTarget, 8);
        // Actual dispatch-table DWORD, index 16 in the supplied seventeen-entry original.
        mem.seed(table16, 0x04227098, 4);

        VolatileBits incomingV = v(0x1000L, 0x8877665544332211L, T, 1);
        NonvolatileBits originalN = n();

        // 372 body SP=E-28h; child133 entry=E-30h and its body SP=E-58h.
        VolatileBits allocateV = new VolatileBits(
                vtable, allocator, 16, 8, 0x1009, 0x100A, 0x100B,
                x(0x1010), x(0x1020), x(0x1030), x(0x1040), x(0x1050), x(0x1060));
        NonvolatileBits allocateN = n(T + 0x18, T, 1, 1);
        CallFrame allocateFrame = f(0x1ACE4E1L, TargetKind.INDIRECT_ABSOLUTE,
                allocateTarget, E - 0x58, allocateV, allocateN, false, 3, M + 0x1ACE4E4L);
        CallResult allocateResult = new CallResult(new NormalReturn(
                v(0x5000L, B, 0x7172737475767778L, 0x8182838485868788L),
                M + 0x1ACE4E4L, E - 0x58, allocateN), true);
        ports.expect(allocateFrame, allocateResult, () -> mem.writeQword(T + 0x28, freshAllocator));

        VolatileBits releaseV = new VolatileBits(
                freshVtable, freshAllocator, oldData, 8, 0x5009, 0x500A, 0x500B,
                x(0x5010), x(0x5020), x(0x5030), x(0x5040), x(0x5050), x(0x5060));
        NonvolatileBits releaseN = n(T + 0x18, B, 0, 1);
        CallFrame releaseFrame = f(0x1ACE514L, TargetKind.INDIRECT_ABSOLUTE,
                releaseTarget, E - 0x58, releaseV, releaseN, true, 3, M + 0x1ACE517L);
        CallResult releaseResult = new CallResult(new NormalReturn(
                v(0x6000L, 0xDEADBEEF87654321L, 0x9192939495969798L, 0xA1A2A3A4A5A6A7A8L),
                M + 0x1ACE517L, E - 0x58, releaseN), true);
        ports.expect(releaseFrame, releaseResult, () -> {
            mem.writeDword(T + 0x24, 7);
            mem.writeByte(B + 0x20, 0x77);
        });

        VolatileBits finalV = new VolatileBits(
                B + 1, 0xFFFFFFFFL, 0, 0, B, 0, 0,
                x(0x6010), x(0x6020), x(0x6030), x(0x6040), x(0x6050), x(0x6060));
        CallResult expected = new CallResult(new NormalReturn(finalV, RET, E + 8, originalN), true);

        // Fixed source-derived events, including both nested known CALL pushes and actual RET reads.
        List<Ev> expectedTrace = List.of(
                e("W64", E + 0x10, 0x2001),             // 372 entry saves
                e("W64", E + 0x18, 0x2002),
                e("W64", E - 8, 0x2003),
                e("R8", T + 0x40, 0),
                e("R32", T + 0x24, 0),
                e("W64", E + 8, 0x2004),
                e("R32", T + 0x24, 0),
                e("W64", E - 0x30, M + 0x1ACDFF8L),   // 372 CALL133
                e("W64", E - 0x18, 0),                // 133 saves current outer RBX
                e("W64", E - 0x38, 0x2004),
                e("R32", T + 0x20, 0),
                e("R64", T + 0x28, allocator),
                e("W64", E - 0x28, T),
                e("W64", E - 0x20, 1),
                e("R64", allocator, vtable),
                e("R64", vtable + 8, allocateTarget),
                e("W64", E - 0x60, M + 0x1ACE4E4L),   // 133 virtual ALLOC
                e("W64", T + 0x28, freshAllocator),
                e("R32", T + 0x24, 0),               // COPY count=0, skip
                e("R64", T + 0x28, freshAllocator),   // fresh allocator after callback
                e("R64", T + 0x18, oldData),
                e("R64", freshAllocator, freshVtable),
                e("R64", freshVtable + 0x10, releaseTarget),
                e("W64", E - 0x60, M + 0x1ACE517L),
                e("W32", T + 0x24, 7),
                e("W8", B + 0x20, 0x77),
                e("W64", T + 0x18, B),
                e("R64", E - 0x28, T),
                e("W32", T + 0x24, 0),               // actual133 overwrites callback count7
                e("R64", E - 0x20, 1),
                e("W32", T + 0x20, 1),
                e("R64", E - 0x18, 0),
                e("R64", E - 0x38, 0x2004),
                e("R64", E - 0x30, M + 0x1ACDFF8L),
                e("R32", T + 0x24, 0),               // caller fresh count
                e("R64", T + 0x18, B),
                e("W64", E - 0x30, M + 0x1ACE01AL),   // actual372 CALL206
                e("R32", table16, 0x04227098),
                e("W64", B, 0),                      // actual206 N16 branch
                e("W64", B + 8, 0),
                e("R64", E - 0x30, M + 0x1ACE01AL),
                e("W32", T + 0x24, 1),
                e("STEP", 0x1ACE030L, 0),
                e("R64", T + 0x18, B),
                e("W32", B + 4, 0xFFFFFF),
                e("R64", T + 0x18, B),
                e("W64", B + 8, 0),
                e("R64", T + 0x18, B),
                e("W32", B, 0xFFFFFF),
                e("STEP", 0x1ACE030L, 0xFFFFFFFFL),
                e("R32", T + 0x38, 0xFFFFFF),
                e("R64", E + 8, 0x2004),
                e("W32", T + 0x38, 0),
                e("R64", E + 0x10, 0x2001),
                e("R64", E + 0x18, 0x2002),
                e("R64", E - 8, 0x2003),
                e("R64", E, RET));

        int[] steps = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (header, counter) -> {
            if (header != 0x1ACE030L && header != 0x1ACE0B0L) {
                throw new AssertionError("unexpected source loop header " + Long.toHexString(header));
            }
            if (steps[0] >= 4) {
                throw new AssertionError("finite shared step budget exhausted");
            }
            steps[0]++;
            mem.trace.add(e("STEP", header, counter));
        };
        Input input = new Input(new Entry(M, E, incomingV, originalN), false, budget);
        CallResult actual = PendingSlotCapacityWithKnownSetFullState1ACDFB0.execute(input, mem, ports);
        eq(expected, actual, "434 full compound V/N/XMM/RIP/SP/postDF");
        eq(expectedTrace, mem.trace, "434 complete source Memory and owned opaque effects");
        ports.done();
        eq(2, steps[0], "434 exactly two admitted source loop headers");
        eq(B, mem.peek(T + 0x18, 8), "434 actual133 buffer publication");
        eq(1L, mem.peek(T + 0x20, 4), "434 reserve capacity");
        eq(1L, mem.peek(T + 0x24, 4), "434 upper final count");
        eq(freshAllocator, mem.peek(T + 0x28, 8), "434 fresh allocator retained");
        eq(0L, mem.peek(T + 0x38, 4), "434 new free head");
        eq(0xFFFFFFL, mem.peek(B, 4), "434 slot0 index");
        eq(0xFFFFFFL, mem.peek(B + 4, 4), "434 slot0 marker");
        eq(0L, mem.peek(B + 8, 8), "434 slot0 qword");
        eq(0x77L, mem.peek(B + 0x20, 1), "434 opaque release byte effect");
        return 1;
    }

    public static void main(String[] args) {
        System.out.println(verify());
    }
}

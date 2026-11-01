package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind.*;

/** Owned software route-admission probes only; no normal return or native claim. */
public final class LoadRowReferenceGrowthRouting245Test {
    private LoadRowReferenceGrowthRouting245Test() { }
    private static final long IMAGE = 0x140000000L;
    private static final long RSP = 0x76000010L;
    private static final long TAIL_RSP = 0x76001008L;
    private static final long GS_BITS = 0x67000100L;
    private static final VolatileBits V = bits(0x11000200L);
    private static final NonvolatileBits NV = new NonvolatileBits(
            0x22000101L, 0x22000202L, 0x22000303L, 0x22000404L,
            0x22000505L, 0x22000606L, 0x22000707L, 0x22000808L,
            new Bits128(0x226601L, 0x226602L));
    private static VolatileBits bits(long seed) {
        return new VolatileBits(seed+1, seed+2, seed+3, seed+4, seed+5, seed+6, seed+7,
                new Bits128(seed+0x10, seed+0x11), new Bits128(seed+0x20, seed+0x21),
                new Bits128(seed+0x30, seed+0x31), new Bits128(seed+0x40, seed+0x41),
                new Bits128(seed+0x50, seed+0x51), new Bits128(seed+0x60, seed+0x61));
    }
    private static void require(boolean condition, String description) {
        if (!condition) throw new AssertionError(description);
    }
    private static final class Touched extends RuntimeException {
        private static final long serialVersionUID = 1L;
    }
    private static final class Probe implements GovernmentCrtBoundary185Api.Memory,
            GovernmentCrtBoundary185Api.Calls, GovernmentCrtBoundary185Api.LoopBudget,
            LoadRowReferenceCallee337b7e0199Api.Float32 {
        final Touched touched = new Touched();
        final VolatileBits callResult = bits(0x33000300L);
        final GovernmentCrtBoundary185Api.NormalReturn tailResult =
                new GovernmentCrtBoundary185Api.NormalReturn(bits(0x44000400L), 0x55000500L, 0x66000600L, NV);
        int memoryCount, callCount, tailCount, gsCount, budgetCount, floatingCount;
        String operation;
        long address, value;
        GovernmentCrtBoundary185Api.Call lastCall;
        GovernmentCrtBoundary185Api.Tail lastTail;
        final GovernmentCrtBoundary185Api.Calls bound;
        Probe() {
            bound = LoadRowReferenceGrowth244Calls.bind(IMAGE, this, this, this, this);
            quiet(0);
        }
        Touched hit(String op, long at, long supplied) {
            memoryCount++; operation=op; address=at; value=supplied; return touched;
        }
        @Override public int readDword(long at) { throw hit("readDword",at,0); }
        @Override public long readQword(long at) { throw hit("readQword",at,0); }
        @Override public int readUnsignedByte(long at) { throw hit("readUnsignedByte",at,0); }
        @Override public void writeDword(long at,int supplied) { throw hit("writeDword",at,supplied); }
        @Override public int lockedXaddDword(long at,int supplied) { throw hit("lockedXaddDword",at,supplied); }
        @Override public void writeQword(long at,long supplied) { throw hit("writeQword",at,supplied); }
        @Override public void writeByte(long at,int supplied) { throw hit("writeByte",at,supplied); }
        @Override public Bits128 read128(long at) { throw hit("read128",at,0); }
        @Override public void write128(long at,Bits128 supplied) { throw hit("write128",at,supplied.lowBits()); }
        @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            callCount++; lastCall=call; return callResult;
        }
        @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            tailCount++; lastTail=transfer; return tailResult;
        }
        @Override public long readGsQword58() { gsCount++; return GS_BITS; }
        @Override public void beforeStep(long header,long guard) {
            budgetCount++; throw new AssertionError("unexpected budget before first Memory");
        }
        @Override public int convertSignedDwordToFloatBits(int bits) {
            floatingCount++; throw new AssertionError("unexpected FP conversion before first Memory");
        }
        @Override public int divideScalarFloatBits(int a,int b) {
            floatingCount++; throw new AssertionError("unexpected FP division before first Memory");
        }
        @Override public boolean orderedAbove(int a,int b) {
            floatingCount++; throw new AssertionError("unexpected FP compare before first Memory");
        }
        void quiet(int expectedGs) {
            require(memoryCount==0 && callCount==0 && tailCount==0 && gsCount==expectedGs
                    && budgetCount==0 && floatingCount==0,"unexpected probe activity");
        }
        void expectTouch(Runnable action,String op,long at,long supplied,int expectedGs) {
            boolean reached=false;
            try { action.run(); } catch (Touched actual) {
                require(actual==touched,"foreign Touched exception"); reached=true;
            }
            require(reached,"selected route returned without first Memory");
            require(memoryCount==1 && op.equals(operation) && address==at && value==supplied,
                    "first Memory operation/address/value mismatch: "+operation+" @"+Long.toHexString(address));
            require(callCount==0 && tailCount==0 && gsCount==expectedGs && budgetCount==0
                    && floatingCount==0,"fallback/budget/FP before route admission");
        }
    }
    private static void admitCall(long site,long target,String op,long at,long supplied,int expectedGs) {
        Probe p=new Probe();
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,DIRECT_RVA,target,RSP,V,NV);
        p.expectTouch(()->p.bound.invoke(call),op,at,supplied,expectedGs);
    }
    private static void admitTail(long site,long target,String op,long at,long supplied,int expectedGs) {
        Probe p=new Probe();
        GovernmentCrtBoundary185Api.Entry entry=new GovernmentCrtBoundary185Api.Entry(IMAGE,TAIL_RSP,V,NV);
        GovernmentCrtBoundary185Api.Tail transfer=new GovernmentCrtBoundary185Api.Tail(site,DIRECT_RVA,target,entry);
        p.expectTouch(()->p.bound.tail(transfer),op,at,supplied,expectedGs);
    }
    private static void foreignCall(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target) {
        Probe p=new Probe();
        GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,kind,target,RSP,V,NV);
        require(p.bound.invoke(call)==p.callResult,"foreign Call result identity");
        require(p.callCount==1 && p.lastCall==call,"foreign Call argument/count");
        require(p.memoryCount==0 && p.tailCount==0 && p.gsCount==0 && p.budgetCount==0
                && p.floatingCount==0,"foreign Call activity");
    }
    private static void foreignTail(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target) {
        Probe p=new Probe();
        GovernmentCrtBoundary185Api.Entry entry=new GovernmentCrtBoundary185Api.Entry(IMAGE,TAIL_RSP,V,NV);
        GovernmentCrtBoundary185Api.Tail transfer=new GovernmentCrtBoundary185Api.Tail(site,kind,target,entry);
        require(p.bound.tail(transfer)==p.tailResult,"foreign Tail result identity");
        require(p.tailCount==1 && p.lastTail==transfer && p.lastTail.entry()==entry,"foreign Tail argument/count");
        require(p.memoryCount==0 && p.callCount==0 && p.gsCount==0 && p.budgetCount==0
                && p.floatingCount==0,"foreign Tail activity");
    }
    private static void foreignGs() {
        Probe p=new Probe(); require(p.bound.readGsQword58()==GS_BITS,"GS bits"); p.quiet(1);
    }
    public static void verifyRoutes() {
        // Twenty-three source-checked R2 admission statements retained verbatim.
        admitCall(0x34EF8C5L, 0x337B7E0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337B8EDL, 0xA636F0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337BA8BL, 0xA636F0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337BAE2L, 0xA636F0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337B93EL, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337B9CEL, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337BB4AL, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337B987L, 0xE23EA0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337BA17L, 0xE23EA0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337BAEAL, 0x337C040L, "readDword", 0x11000216L, 0L, 0);
        admitCall(0x337C7D7L, 0x337C040L, "readDword", 0x11000216L, 0L, 0);
        admitCall(0x337BB00L, 0x337C5D0L, "writeQword", RSP - 16L, 0x22000202L, 0);
        admitCall(0x337C198L, 0x337C5D0L, "writeQword", RSP - 16L, 0x22000202L, 0);
        admitCall(0x337C7F8L, 0x337C5D0L, "writeQword", RSP - 16L, 0x22000202L, 0);
        admitCall(0x337C8A0L, 0x337C5D0L, "writeQword", RSP - 16L, 0x22000202L, 0);
        admitCall(0x337C882L, 0x337C0C0L, "writeQword", RSP - 16L, 0x22000303L, 0);
        admitCall(0x337BB8BL, 0x337C0C0L, "writeQword", RSP - 16L, 0x22000303L, 0);
        admitCall(0x337BB7CL, 0x86E160L, "readQword", RSP - 8L, 0L, 0);
        admitCall(0x337C051L, 0x86E160L, "readQword", RSP - 8L, 0L, 0);
        admitCall(0x337C873L, 0x86E160L, "readQword", RSP - 8L, 0L, 0);
        admitCall(0x337BBA6L, 0x337C200L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337C161L, 0x8CEEB0L, "readQword", 0x67000100L, 0L, 1);
        admitCall(0x337C1C3L, 0x8CEEB0L, "readQword", 0x67000100L, 0L, 1);
        // Seven owner additions from actual mature239 transfer/swap CALL inventory.
        admitCall(0x337C6EAL, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337C71DL, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337C843L, 0x87C9B0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337C6FCL, 0xE23EA0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337C72FL, 0xE23EA0L, "writeQword", RSP, 0x22000101L, 0);
        admitCall(0x337C784L, 0xA636F0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitCall(0x337C7CFL, 0xA636F0L, "writeQword", RSP + 8L, 0x22000101L, 0);
        admitTail(0x337C064L, 0x337C0C0L, "writeQword", TAIL_RSP - 8L, 0x22000303L, 0);
        // Independent captured native inventory; never the private routing predicate.
        long[][] nativePairs = {
            {0x337BAEAL, 0x337C040L},
            {0x337BB00L, 0x337C5D0L},
            {0x337C882L, 0x337C0C0L},
            {0x337BB8BL, 0x337C0C0L},
            {0x337C198L, 0x337C5D0L},
            {0x337C7F8L, 0x337C5D0L},
            {0x337C8A0L, 0x337C5D0L},
            {0x337C7D7L, 0x337C040L},
            {0x337C6EAL, 0x87C9B0L},
            {0x337C71DL, 0x87C9B0L},
            {0x337C843L, 0x87C9B0L},
            {0x337C6FCL, 0xE23EA0L},
            {0x337C72FL, 0xE23EA0L},
            {0x337C784L, 0xA636F0L},
            {0x337C7CFL, 0xA636F0L},
            {0x337BB7CL, 0x86E160L},
            {0x337C051L, 0x86E160L},
            {0x337C873L, 0x86E160L},
            {0x337B93EL, 0x87C9B0L},
            {0x337B9CEL, 0x87C9B0L},
            {0x337BB4AL, 0x87C9B0L},
            {0x337B987L, 0xE23EA0L},
            {0x337BA17L, 0xE23EA0L},
            {0x337B8EDL, 0xA636F0L},
            {0x337BA8BL, 0xA636F0L},
            {0x337BAE2L, 0xA636F0L},
            {0x34EF8C5L, 0x337B7E0L},
            {0x337BBA6L, 0x337C200L},
            {0x337C161L, 0x8CEEB0L},
            {0x337C1C3L, 0x8CEEB0L},
        };
        require(nativePairs.length == 30, "finite native inventory size");
        for (long[] pair : nativePairs) {
            long site=pair[0], target=pair[1];
            // Added high bit cannot equal any captured low RVA in this inventory.
            foreignCall(site ^ 0x100000000L, DIRECT_RVA, target);
            foreignCall(site, DIRECT_RVA, target ^ 0x100000000L);
            foreignCall(site, INDIRECT_ABSOLUTE, target);
            // A CALL admission never awards a Tail at that same pair.
            foreignTail(site, DIRECT_RVA, target);
        }
        // Actual 207 self and unselected descendant sites remain foreign.
        foreignCall(0x337C593L, DIRECT_RVA, 0x337C200L);
        foreignCall(0x337C55CL, DIRECT_RVA, 0x86E160L);
        foreignCall(0x337C56BL, DIRECT_RVA, 0x337C0C0L);
        foreignCall(0x337C4CAL, DIRECT_RVA, 0x337C040L);
        foreignCall(0x337C4E0L, DIRECT_RVA, 0x337C5D0L);
        foreignCall(0x337C064L, DIRECT_RVA, 0x337C0C0L);
        foreignTail(0x337C065L, DIRECT_RVA, 0x337C0C0L);
        foreignTail(0x337C064L, DIRECT_RVA, 0x337C0C1L);
        foreignTail(0x337C064L, INDIRECT_ABSOLUTE, 0x337C0C0L);
        foreignGs();
    }
    public static void main(String[] args) {
        verifyRoutes(); System.out.println("route-admission245 complete; no normal-return/native claim");
    }
}

package org.xar.ck3.research.m4;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAllocate424fda0;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/**
 * Represented fullstate producer for the held 94-byte normal body.
 * Implements the complete control flow of 424FDA0 using the legacy RequestAllocate424fda0
 * as the single business algorithm owner, while providing the exact raw ABI ports
 * required by the frozen contract.
 */
public final class Allocate94FullState282 {
    private Allocate94FullState282() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {

        long base = entry.imageBaseBits();
        long entrySP = entry.rspBits();
        long bodypreSP = entrySP - 0x28L;

        // Initialize registers from the entry state
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(base, entrySP, entry.volatileBits(), entry.nonvolatileBits()));

        // Prologue: push RBX, sub rsp, mov rbx, rcx
        memory.writeQword(entrySP - 8L, r.rbx);
        r.rbx = r.rcx;
        r.rsp = bodypreSP;

        // ABI-only MOV EAX,1/CMOVE projection; legacy still owns the branch/loop.
        if (Long.compareUnsigned(r.rcx, 0xFFFFFFFFFFFFFFE0L) <= 0) {
            r.rax = 1L;
            if (r.rcx == 0L) r.rbx = 1L;
        }

        // Prepare ports for the legacy allocate call
        // We need a thin NativeTaskMemory view that delegates to the shared Memory
        NativeTaskMemory thinMemory = new NativeTaskMemory() {
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
        };

        // State for the failure port to capture the pending cell and address
        Cell32[] pendingCell = new Cell32[1];
        long[] pendingRax = new long[1];

        RequestAllocate424fda0.Ports ports = new RequestAllocate424fda0.Ports() {
            @Override
            public int call424e250() {
                // Legacy policy port: budget.beforeStep(rawFDBD=424FDBD,0) immediately before its ownedCALL
                budget.beforeStep(0x424FDBDL, 0L);

                // Call(rawsite424FDBD,DIRECT_RVA,rawtarget424E250,bodypreSP,V,N)
                // ownedpushI+424FDC2
                long retAddr = base + 0x424FDC2L;
                memory.writeQword(bodypreSP - 8L, retAddr);

                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424FDBDL,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x424E250L,
                    bodypreSP,
                    r.volatileBits(),
                    r.nonvolatileBits());

                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);

                // low32 actualpostRAX for legacy
                return (int)(r.rax & 0xFFFFFFFFL);
            }

            @Override
            public int call424cffc(long knownRcx) {
                // Legacy gateport: MOVRCX=givenknownRcx (retainedsize)
                r.rcx = knownRcx;

                // Call(rawsite424FDC9,DIRECT_RVA,rawtarget424CFFC,bodypreSP,V,N)
                // ownedpushI+424FDCE
                long retAddr = base + 0x424FDCEL;
                memory.writeQword(bodypreSP - 8L, retAddr);

                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424FDC9L,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x424CFFCL,
                    bodypreSP,
                    r.volatileBits(),
                    r.nonvolatileBits());

                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);

                // low32 actualpostRAX for legacy
                return (int)(r.rax & 0xFFFFFFFFL);
            }

            @Override
            public long heapAlloc(long heapHandleBits, int flagsBits, long bytesBits) {
                // Heapport sets RCX=givenheap,RDX=zeroextendedflags0,R8=givenbytes and leaves other currentV intact
                r.rcx = heapHandleBits;
                r.rdx = (long)flagsBits & 0xFFFFFFFFL;
                r.r8 = bytesBits;

                // Fresh rawtarget read[I+43DA768] BEFORE CALLpush
                long target = memory.readQword(base + 0x43DA768L);

                // Call(rawsite424FDDE,INDIRECT_ABSOLUTE,targetAbs,bodypreSP,V,N)
                // write[bodypreSP-8]=I+424FDE4 once then invoke/applyallV
                long retAddr = base + 0x424FDE4L;
                memory.writeQword(bodypreSP - 8L, retAddr);

                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424FDDEL,
                    GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,
                    target,
                    bodypreSP,
                    r.volatileBits(),
                    r.nonvolatileBits());

                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);

                return r.rax;
            }

            @Override
            public Cell32 call423b18c() {
                // Legacy failureport: Call(rawsite424FDEB,DIRECT_RVA,rawtarget423B18C,bodypreSP,V,N)
                // ownedpushI+424FDF0
                long retAddr = base + 0x424FDF0L;
                memory.writeQword(bodypreSP - 8L, retAddr);

                GovernmentCrtBoundary185Api.Call c = new GovernmentCrtBoundary185Api.Call(
                    0x424FDEBL,
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x423B18CL,
                    bodypreSP,
                    r.volatileBits(),
                    r.nonvolatileBits());

                GovernmentPrimaryTail155Api.VolatileBits postV = calls.invoke(c);
                r.apply(postV);

                // applyallpostV and retain actualfullRAX as pending DWORD-write address
                pendingRax[0] = r.rax;

                // Return private new Cell32(-1) scratch to legacy
                pendingCell[0] = new Cell32(-1);
                return pendingCell[0];
            }
        };

        // Exactly one legacy allocate invocation
        // Legacy RequestAllocate424fda0.allocate(base,originalsize,thinMemoryView,ports) exactly once owns the complete control flow
        long originalSize = entry.volatileBits().rcxBits();
        long result = RequestAllocate424fda0.allocate(base, originalSize, thinMemory, ports);

        // After allocate returns, if this pending cell exists, writeDword(retainedactualRAX,cell.value) exactly once
        // BEFORE RAX=scalarReturn0 and before epilogue
        if (pendingCell[0] != null) {
            memory.writeDword(pendingRax[0], pendingCell[0].value);
        }

        // Use legacy returnedfullRAX for r.rax
        r.rax = result;

        // Epilogue: ADD20 -> freshPOP savedRBX[S-8] -> freshRET[S] -> callerSP=S+8
        r.rsp += 0x20L;
        r.rbx = memory.readQword(r.rsp);
        r.rsp += 8L;
        long retRip = memory.readQword(r.rsp);
        r.rsp += 8L;

        return new GovernmentCrtBoundary185Api.NormalReturn(
            r.volatileBits(),
            retRip,
            r.rsp,
            r.nonvolatileBits());
    }
}
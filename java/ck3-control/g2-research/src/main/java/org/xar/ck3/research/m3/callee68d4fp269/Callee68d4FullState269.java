package org.xar.ck3.research.m3.callee68d4fp269;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee246.Callee42568D4247;
import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;

/**
 * Complete represented protocol around the existing storage business, with opaque children.
 * Implements the Callee68d4FullState269.execute contract from PUBLIC-CONTRACT269.txt.
 */
public final class Callee68d4FullState269 {
    private Callee68d4FullState269() { }

    public static QueueFp604Api.Normal execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long image = entry.imageBaseBits();
        long originalRsp = entry.rspBits();

        // Initialize registers from the entry
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(image, originalRsp,
                entry.volatileBits(), entry.nonvolatileBits()));

        // Prologue: No stack allocation in 42568D4 body (CFG closed, no CALL)
        // The contract says: "Complete37-byte normal CFG has no CALL, no stack allocation..."
        // So we do not modify RSP or write to stack for prologue.
        // However, the epilogue requires reading RET from entry.rspBits().
        // The entry RSP is the stack top at function entry.

        // Prepare Input for old core
        long entryRcx = entry.volatileBits().rcxBits();

        // Create the storage adapter
        Callee68d4Memory246 storage = new Callee68d4Memory246() {
            @Override public long readPointer(long address) {
                return memory.readQword(address);
            }
            @Override public int readInt32(long address) {
                return memory.readDword(address);
            }
            @Override public void writeInt32(long address, int value) {
                memory.writeDword(address, value);
            }
            @Override public void writeInt64(long address, long value) {
                memory.writeQword(address, value);
            }
            @Override public void writeInt16(long address, int value) {
                memory.writeWord(address, value);
            }
            @Override public void atomicAddInt32(long address, int deltaBits) {
                memory.lockedXaddDword(address, deltaBits);
            }
            @Override public int exchangeAddInt32(long address, int deltaBits) {
                // LOCK XADD32 maps to exactly one existing Full437.lockedXaddDword(address,delta) indivisible effect
                // returning actual old int bits.
                return memory.lockedXaddDword(address, deltaBits);
            }
        };

        // Execute the business logic exactly once
        long result = Callee42568D4247.execute(storage, image, entryRcx);

        // Epilogue
        // "Only after one old core normal return perform fresh memory.readQword(entry.rspBits()) for the RET"
        long returnRip = memory.readQword(originalRsp);
        // "callerRspBits=entrySP+8 modulo64"
        long callerRsp = originalRsp + 8L;

        // "Preserve every represented entry GPR/lowXMM/nonvolatile exceptRAX"
        // "Build full VolatileBits with replacedRAX and remaining exact entry values"
        // The result from Callee42568D4247.execute is the zeroextended RAX value.
        r.rax = result;

        // "preserve actual directionFlagSet and the very same input.mxcsr object"
        boolean df = input.base().directionFlagSet();
        QueueFp604Api.Mxcsr fp = input.mxcsr();

        // "Nonvolatile snapshot unchanged."
        // r.nonvolatileBits() is already initialized from entry.nonvolatileBits() and not modified by the business logic (no CALLs).

        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
            new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(), returnRip, callerRsp, r.nonvolatileBits()),
            df), fp);
    }
}
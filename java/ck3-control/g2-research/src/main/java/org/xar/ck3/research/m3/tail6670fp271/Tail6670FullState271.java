package org.xar.ck3.research.m3.tail6670fp271;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.tail249.Tail4256670249;
import org.xar.ck3.research.m3.tail249.Tail6670Api249;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670Fp271Api;

/**
 * Complete implementation of the Tail6670FullState271 contract.
 * Reuses the mature 249 business logic exactly once with a full same-RAM adapter.
 * Preserves full incoming R9, SP, N, DF, and MXCSR until the opaque tail transfer.
 */
public final class Tail6670FullState271 {
    private Tail6670FullState271() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, Tail6670Fp271Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        GovernmentCrtBoundary185Api.Entry entry = input.base().entry();
        long imageBase = entry.imageBaseBits();
        long entryRsp = entry.rspBits();
        GovernmentPrimaryTail155Api.VolatileBits entryV = entry.volatileBits();
        GovernmentPrimaryTail155Api.NonvolatileBits entryN = entry.nonvolatileBits();

        // Initialize registers from the entry to preserve all initial state
        GovernmentPrimaryTail155Api.Registers r = GovernmentCallee164Api.registers(
            new GovernmentCallee164Api.Entry(imageBase, entryRsp, entryV, entryN));

        // Prepare the input for the old 249 core
        Tail6670Api249.Input coreInput = new Tail6670Api249.Input(imageBase, entryV.rcxBits());

        // Create the same-RAM adapter for the old 249 core
        Callee68fcApi246.Memory adapterMemory = new Callee68fcApi246.Memory() {
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
            @Override public void atomicAddInt32(long address, int delta) {
                memory.lockedXaddDword(address, delta);
            }
        };

        // The result of the tail call, stored to be returned after the core finishes
        QueueFp604Api.Outcome[] storedOutcome = new QueueFp604Api.Outcome[1];

        // Create the Ports callback for the old 249 core
        Tail6670Api249.Ports ports = new Tail6670Api249.Ports() {
            @Override public void tail4256874(Callee68fcApi246.Memory m, long siteRva, long knownRcx, long knownRdx,
                    long liveRax, long knownR8) {
                // Build the updated VolatileBits with the four established values from the old port
                // Preserve all other initial represented GPR/lowXMM/nonvolatile and originalSP
                GovernmentPrimaryTail155Api.VolatileBits finalV = new GovernmentPrimaryTail155Api.VolatileBits(
                    liveRax, // RAX
                    knownRcx, // RCX
                    knownRdx, // RDX
                    knownR8, // R8
                    r.r9, // R9 (Preserve FULL incoming R9)
                    r.r10, // R10
                    r.r11, // R11
                    r.x0, r.x1, r.x2, r.x3, r.x4, r.x5 // XMM0-5
                );

                // Build the 185.Tail frame
                GovernmentCrtBoundary185Api.Tail tail = new GovernmentCrtBoundary185Api.Tail(
                    0x42566F6L, // jumpSiteRva
                    GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                    0x4256874L, // targetBits
                    new GovernmentCrtBoundary185Api.Entry(
                        imageBase,
                        entryRsp, // SP is preserved (no new push/stack allocation)
                        finalV,
                        entryN // NonvolatileBits are preserved
                    )
                );

                // Wrap actual input DF and SAME input.mxcsr object
                Tail6670Fp271Api.TailFrame frame = new Tail6670Fp271Api.TailFrame(
                    tail,
                    input.base().directionFlagSet(),
                    input.mxcsr()
                );

                // Invoke calls.tail once
                QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls.tail(frame));

                // If Normal, checkNormalReturn BEFORE storing
                if (outcome instanceof QueueFp604Api.Normal normal) {
                    frame.checkNormalReturn(normal);
                }

                // Store the actual Outcome (Normal or Stopped) with no additional processing
                storedOutcome[0] = outcome;
            }
        };

        // Execute the old 249 core exactly once
        Tail4256670249.execute(adapterMemory, ports, coreInput);

        // Guard absent stored result with explicit illegalstate
        if (storedOutcome[0] == null) {
            throw new IllegalStateException("Tail call did not produce an outcome");
        }

        // Return the actual Outcome (Normal or Stopped) with no additional processing
        return storedOutcome[0];
    }
}

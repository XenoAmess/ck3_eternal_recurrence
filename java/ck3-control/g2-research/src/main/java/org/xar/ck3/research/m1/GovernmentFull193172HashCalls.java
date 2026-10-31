package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Memory;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentByteUpdate169Api;
import org.xar.ck3.research.m5.GovernmentByteHash169;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/**
 * Owned-software consumer edge for the actual complete parent at RVA 2D1B7F0.
 * Handles only the direct CALL to 3F7E220 (hash wrapper) at site 2D1B85E.
 * Delegates all other calls and readGsQword58 to the provided delegate.
 */
public final class GovernmentFull193172HashCalls {

    private GovernmentFull193172HashCalls() { }

    /**
     * Adapts SharedManager.Memory to ByteUpdate169Api.Memory by forwarding
     * the actual declared methods of the shared interface.
     */
    private static GovernmentByteUpdate169Api.Memory adaptMemory(GovernmentSharedManager167Api.Memory shared) {
        return new GovernmentByteUpdate169Api.Memory() {
            @Override public void writeQword(long addressBits, long valueBits) { shared.writeQword(addressBits, valueBits); }
            @Override public void writeByte(long addressBits, int lowByteBits) { shared.writeByte(addressBits, lowByteBits); }
            @Override public Bits128 read128(long addressBits) { return shared.read128(addressBits); }
            @Override public void write128(long addressBits, Bits128 valueBits) { shared.write128(addressBits, valueBits); }
            @Override public int readDword(long addressBits) { return shared.readDword(addressBits); }
            @Override public long readQword(long addressBits) { return shared.readQword(addressBits); }
            @Override public int readUnsignedByte(long addressBits) { return shared.readUnsignedByte(addressBits); }
            @Override public void writeDword(long addressBits, int valueBits) { shared.writeDword(addressBits, valueBits); }
            @Override public int lockedXaddDword(long addressBits, int addendBits) { return shared.lockedXaddDword(addressBits, addendBits); }
        };
    }

    public static Calls bind(long imageBaseBits,
            GovernmentSharedManager167Api.Memory memory,
            Calls delegate,
            GovernmentByteUpdate169Api.LoopBudget hashBudget,
            GovernmentLookupLoop580Api.Mxcsr32 ownedMxcsrAtHash) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);
        Objects.requireNonNull(hashBudget);
        Objects.requireNonNull(ownedMxcsrAtHash);

        GovernmentByteUpdate169Api.Memory adaptedMemory = adaptMemory(memory);

        return new Calls() {
            @Override public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override public VolatileBits invoke(OpaqueCall call) {
                Objects.requireNonNull(call);
                if (call.callSiteRva() == 0x2D1B85EL && call.targetRva() == 0x3F7E220L) {
                    // Actual parent OpaqueCall rspBits is BEFORE CALL push.
                    // The hash wrapper expects Entry.frameRspBits to be AFTER CALL pushed its return QWORD.
                    long calleeRsp = call.rspBits() - 8L;
                    // The continuation RIP for the parent CALL to the wrapper is the next instruction after the CALL.
                    // CALL is 5 bytes (E8 + 4-byte offset). Site 2D1B85E + 5 = 2D1B863.
                    long expectedRip = imageBaseBits + 0x2D1B863L;

                    // Write the return address into owned memory at the callee entry position
                    adaptedMemory.writeQword(calleeRsp, expectedRip);

                    // Construct the Entry for the hash wrapper
                    GovernmentByteUpdate169Api.Entry entry = new GovernmentByteUpdate169Api.Entry(
                            imageBaseBits,
                            calleeRsp,
                            call.volatileBits(),
                            call.nonvolatileBits(),
                            ownedMxcsrAtHash
                    );

                    // Execute the actual hash wrapper
                    GovernmentByteUpdate169Api.NormalReturn result = GovernmentByteHash169.execute(
                            entry,
                            adaptedMemory,
                            hashBudget
                    );

                    // Verify normal return boundary
                    if (result.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("hash wrapper return RIP mismatch");
                    }
                    if (result.callerRspBits() != call.rspBits()) {
                        throw new UnsupportedOperationException("hash wrapper caller RSP mismatch");
                    }
                    if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new UnsupportedOperationException("hash wrapper nonvolatile mismatch");
                    }
                    if (!result.mxcsr().equals(ownedMxcsrAtHash)) {
                        throw new UnsupportedOperationException("hash wrapper MXCSR mismatch");
                    }

                    return result.volatileBits();
                }
                return delegate.invoke(call);
            }
        };
    }
}
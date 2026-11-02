package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentRoot178Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m4.AllocateJump6FullState283;
import org.xar.ck3.research.m4.Retry60NormalFullState284;
import org.xar.ck3.research.m4.Gate47FullState273;
import java.util.Objects;

public final class Retry60NormalFullState284Calls {
    private Retry60NormalFullState284Calls() { }

    public static GovernmentCrtBoundary185Api.Memory as185(GovernmentPrimaryTail155Api.Memory memory) {
        if (memory instanceof GovernmentCrtBoundary185Api.Memory) {
            return (GovernmentCrtBoundary185Api.Memory) memory;
        }
        return new GovernmentCrtBoundary185Api.Memory() {
            @Override
            public int readDword(long addressBits) {
                return memory.readDword(addressBits);
            }
            @Override
            public long readQword(long addressBits) {
                return memory.readQword(addressBits);
            }
            @Override
            public int readUnsignedByte(long addressBits) {
                return memory.readUnsignedByte(addressBits);
            }
            @Override
            public void writeDword(long addressBits, int valueBits) {
                memory.writeDword(addressBits, valueBits);
            }
            @Override
            public void writeQword(long addressBits, long valueBits) {
                memory.writeQword(addressBits, valueBits);
            }
            @Override
            public void writeByte(long addressBits, int lowByteBits) {
                memory.writeByte(addressBits, lowByteBits);
            }
            @Override
            public GovernmentPrimaryTail155Api.Bits128 read128(long addressBits) {
                return memory.read128(addressBits);
            }
            @Override
            public void write128(long addressBits, GovernmentPrimaryTail155Api.Bits128 valueBits) {
                memory.write128(addressBits, valueBits);
            }
            @Override
            public int lockedXaddDword(long addressBits, int addendBits) {
                return memory.lockedXaddDword(addressBits, addendBits);
            }
        };
    }

    public static GovernmentCrtBoundary185Api.Calls normalChildren(long imageBase, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls lower, GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                    if (call.callSiteRva() == 0x4223BAEL && call.targetBits() == 0x42420B8L) {
                        // Child entry for AllocateJump6FullState283
                        // Original Retry284 already owns CALL push at I+4223BB3.
                        // Child Entry rspBits is preSP - 8 (after push).
                        long childRsp = call.rspBits() - 8L;
                        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                                imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());

                        // Execute child
                        GovernmentCrtBoundary185Api.NormalReturn childReturn = AllocateJump6FullState283.execute(
                                childEntry, memory, this, budget);

                        // Validate return RIP and SP
                        long expectedRip = imageBase + 0x4223BB3L;
                        if (childReturn.returnRipBits() != expectedRip) {
                            throw new UnsupportedOperationException("Invalid child return RIP");
                        }
                        if (childReturn.callerRspBits() != call.rspBits()) {
                            throw new UnsupportedOperationException("Invalid child return SP");
                        }

                        // Return actual volatile bits
                        if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                        }
                        return childReturn.volatileBits();
                    } else if (call.callSiteRva() == 0x4223BA2L && call.targetBits() == 0x424CFFCL) {
                        // Child entry for Gate47FullState273
                        // Original Retry284 already owns CALL push at I+4223BA7.
                        long childRsp = call.rspBits() - 8L;
                        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                                imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());

                        // Execute child
                        GovernmentCrtBoundary185Api.NormalReturn childReturn = Gate47FullState273.execute(
                                childEntry, memory, lower);

                        // Validate return RIP and SP
                        long expectedRip = imageBase + 0x4223BA7L;
                        if (childReturn.returnRipBits() != expectedRip) {
                            throw new UnsupportedOperationException("Invalid child return RIP");
                        }
                        if (childReturn.callerRspBits() != call.rspBits()) {
                            throw new UnsupportedOperationException("Invalid child return SP");
                        }

                        // Return actual volatile bits
                        if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                        }
                        return childReturn.volatileBits();
                    } else if (call.callSiteRva() == 0x424FDC9L && call.targetBits() == 0x424CFFCL) {
                        // Child entry for Gate47FullState273 (from FDA0 path)
                        // Original FDA0 already owns CALL push at I+424FDCE.
                        long childRsp = call.rspBits() - 8L;
                        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                                imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());

                        // Execute child
                        GovernmentCrtBoundary185Api.NormalReturn childReturn = Gate47FullState273.execute(
                                childEntry, memory, lower);

                        // Validate return RIP and SP
                        long expectedRip = imageBase + 0x424FDCEL;
                        if (childReturn.returnRipBits() != expectedRip) {
                            throw new UnsupportedOperationException("Invalid child return RIP");
                        }
                        if (childReturn.callerRspBits() != call.rspBits()) {
                            throw new UnsupportedOperationException("Invalid child return SP");
                        }

                        // Return actual volatile bits
                        if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                        }
                        return childReturn.volatileBits();
                    }
                }

                // Delegate other calls to lower
                return lower.invoke(call);
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                return lower.tail(transfer);
            }

            @Override
            public long readGsQword58() {
                return lower.readGsQword58();
            }
        };
    }

    public static GovernmentRoot178Api.Calls bindRoot(long imageBase, GovernmentRoot178Api.Memory memory, GovernmentRoot178Api.Calls outerFallback, GovernmentCrtBoundary185Api.Calls lower, GovernmentCrtBoundary185Api.LoopBudget budget) {
        GovernmentCrtBoundary185Api.Memory m185 = as185(memory);
        GovernmentCrtBoundary185Api.Calls children = normalChildren(imageBase, m185, lower, budget);

        return new GovernmentRoot178Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.callSiteRva() == 0x3F5C0F7L && call.targetRva() == 0x4223B94L) {
                    // Execute Retry60NormalFullState284
                    // Root178 already owns CALL push at I+3F5C0FC.
                    long childRsp = call.rspBits() - 8L;
                    GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                            imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());

                    GovernmentCrtBoundary185Api.NormalReturn childReturn = Retry60NormalFullState284.execute(
                            childEntry, m185, children, budget);

                    // Validate return RIP and SP
                    long expectedRip = imageBase + 0x3F5C0FCL;
                    if (childReturn.returnRipBits() != expectedRip) {
                        throw new UnsupportedOperationException("Invalid child return RIP");
                    }
                    if (childReturn.callerRspBits() != call.rspBits()) {
                        throw new UnsupportedOperationException("Invalid child return SP");
                    }

                    // Return actual volatile bits
                    if (!childReturn.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new UnsupportedOperationException("Nonvolatile continuation mismatch");
                        }
                        return childReturn.volatileBits();
                }

                // Delegate other calls to outerFallback
                return outerFallback.invoke(call);
            }

            @Override
            public long readGsQword58() {
                return outerFallback.readGsQword58();
            }
        };
    }
}
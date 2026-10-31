package org.xar.ck3.research.m5;

import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.*;

/** Owner takeover after two incomplete model rounds. Exact owned normal tail, not native Game execution. */
public final class GovernmentPrimaryTail155 {
    private GovernmentPrimaryTail155() { }
    private static long u32(int bits) { return Integer.toUnsignedLong(bits); }
    private static void call(Registers r, Calls calls, long site, long target) {
        r.apply(calls.invoke(new OpaqueCall(site, target, r.rsp, r.volatileBits(), r.nonvolatileBits())));
    }
    public static NormalReturn execute(Entry entry, Memory memory, Calls calls, LoopBudget budget) {
        Registers r = new Registers(entry);
        long image = entry.imageBaseBits();
        long counter = image + 0x5c6a9dcL;
        long cap = image + 0x54582e4L;

        // 30A3F4D..30A3FE2: TLS skip keeps original EDX; other paths reload it at3FDA.
        r.rbx = r.rdi + 0xd98L;
        r.rdx = u32(memory.readDword(cap));
        if (memory.readDword(r.rbx) > (int) r.rdx) {
            memory.writeDword(r.rbp + 0x1258L, (int) r.rdx);
            r.rax = calls.readGsQword58();
            r.rcx = memory.readQword(r.rax);
            if (memory.readUnsignedByte(r.r12 + r.rcx) == 0) {
                r.rax = u32(memory.readDword(counter));
                if ((int) r.rax < 0x186a0) {
                    r.rcx = 0x10000L;
                    call(r, calls, 0x30a3f8eL, 0x3f5f970L);
                    if (r.rax != 0) {
                        memory.writeQword(r.rsp + 0x38L, r.rsi);
                        r.rcx = r.rbp + 0x1258L;
                        memory.writeQword(r.rsp + 0x30L, r.rcx);
                        memory.writeQword(r.rsp + 0x28L, r.rbx);
                        r.rcx = image + 0x48b74d8L;
                        memory.writeQword(r.rsp + 0x20L, r.rcx);
                        r.r8 = 0x1b3L;
                        r.rdx = image + 0x48b7a48L;
                        r.rcx = r.rax;
                        call(r, calls, 0x30a3fcaL, 0x19db5a0L);
                        r.rax = u32((int) r.r15);
                        r.rax = u32(memory.lockedXaddDword(counter, (int) r.rax));
                    }
                }
                r.rdx = u32(memory.readDword(cap));
            }
            memory.writeDword(r.rbx, (int) r.rdx);
        }

        // 30A3FE2..30A4062: every selected ordinary diagnostic gate joins the byte clear.
        if (memory.readUnsignedByte(r.rdi + 0x4d7L) != 0
                && memory.readUnsignedByte(r.rdi + 0x4d6L) == 10) {
            r.rax = calls.readGsQword58();
            r.rcx = memory.readQword(r.rax);
            if (memory.readUnsignedByte(r.r12 + r.rcx) == 0) {
                r.rax = u32(memory.readDword(counter));
                if ((int) r.rax < 0x186a0) {
                    r.rcx = 0x10000L;
                    call(r, calls, 0x30a401aL, 0x3f5f970L);
                    if (r.rax != 0) {
                        memory.writeQword(r.rsp + 0x28L, r.rsi);
                        r.rcx = image + 0x48b7520L;
                        memory.writeQword(r.rsp + 0x20L, r.rcx);
                        r.r9 = 4;
                        r.r8 = 0x1bcL;
                        r.rdx = image + 0x48b7a48L;
                        r.rcx = r.rax;
                        call(r, calls, 0x30a404bL, 0x8807d0L);
                        r.rax = u32((int) r.r15);
                        r.rax = u32(memory.lockedXaddDword(counter, (int) r.rax));
                    }
                }
            }
            memory.writeByte(r.rdi + 0x4d7L, 0);
        }

        // 30A4062..30A40C7: fixed end, equality termination, 3 untouched descriptor padding bytes.
        r.rbx = memory.readQword(r.rdi + 0xdb8L);
        r.r14 = ((long) memory.readDword(r.rdi + 0xdc4L)) << 4;
        r.r14 += r.rbx;
        if (r.rbx != r.r14) {
            r.r13 = image + 0x48b7498L;
            do {
                budget.beforeIteration(0x30a4083L, r.rbx, r.r14);
                if (memory.readUnsignedByte(r.rbx + 0xcL) != 0) {
                    memory.writeQword(r.rbp + 0x70L, r.r13);
                    memory.writeDword(r.rbp + 0x78L, 0x15);
                    memory.writeByte(r.rbp + 0x7cL, 0);
                    call(r, calls, 0x30a4098L, 0x8fc920L);
                    r.x0 = memory.read128(r.rbp + 0x70L);
                    memory.write128(r.rbp + 0x1c0L, r.x0);
                    r.r9 = r.rbp + 0x1c0L;
                    r.r8 = r.rsi;
                    r.rdx = r.rax;
                    r.rcx = r.rbx;
                    call(r, calls, 0x30a40b9L, 0x30a92d0L);
                }
                r.rbx += 0x10L;
            } while (r.rbx != r.r14);
        }

        // 30A40C7..30A4134: source+length and destination differ from the first loop.
        r.rbx = memory.readQword(r.rdi + 0xdd0L);
        r.r14 = ((long) memory.readDword(r.rdi + 0xddcL)) << 4;
        r.r14 += r.rbx;
        if (r.rbx != r.r14) {
            r.r13 = image + 0x48b74b0L;
            do {
                budget.beforeIteration(0x30a40e8L, r.rbx, r.r14);
                if (memory.readUnsignedByte(r.rbx + 0xcL) != 0) {
                    memory.writeQword(r.rbp + 0x80L, r.r13);
                    memory.writeDword(r.rbp + 0x88L, 0x20);
                    memory.writeByte(r.rbp + 0x8cL, 0);
                    call(r, calls, 0x30a4106L, 0x8fc920L);
                    r.x0 = memory.read128(r.rbp + 0x80L);
                    memory.write128(r.rsp + 0x40L, r.x0);
                    r.r9 = r.rsp + 0x40L;
                    r.r8 = r.rsi;
                    r.rdx = r.rax;
                    r.rcx = r.rbx;
                    call(r, calls, 0x30a4126L, 0x30a92d0L);
                }
                r.rbx += 0x10L;
            } while (r.rbx != r.r14);
        }

        // 30A4134..30A41B2: preserve both logical shifts and the actual R15B masks.
        r.rdx = memory.readQword(r.rdi + 0x40L);
        r.rax = r.rdx >>> 0x33;
        if ((((int) r.r15) & ((int) r.rax) & 0xff) != 0) {
            r.rdx >>>= 0x1d;
            if ((((int) r.r15) & ((int) r.rdx) & 0xff) == 0) {
                r.rax = calls.readGsQword58();
                r.rdx = memory.readQword(r.rax);
                if (memory.readUnsignedByte(r.r12 + r.rdx) == 0) {
                    r.rax = u32(memory.readDword(counter));
                    if ((int) r.rax < 0x186a0) {
                        r.rcx = 0x10000L;
                        call(r, calls, 0x30a4173L, 0x3f5f970L);
                        if (r.rax != 0) {
                            memory.writeQword(r.rsp + 0x28L, r.rsi);
                            r.rcx = image + 0x48b7410L;
                            memory.writeQword(r.rsp + 0x20L, r.rcx);
                            r.r9 = 4;
                            r.r8 = 0x1daL;
                            r.rdx = image + 0x48b7a48L;
                            r.rcx = r.rax;
                            call(r, calls, 0x30a41a4L, 0x8807d0L);
                            r.r15 = u32(memory.lockedXaddDword(counter, (int) r.r15));
                        }
                    }
                }
            }
        }

        // 30A41B2..RET: preserve actual reads and raw RAX, including alias-visible saved state.
        r.x6 = memory.read128(r.rsp + 0x12e0L);
        r.rsp += 0x12f8L;
        r.r15 = memory.readQword(r.rsp); r.rsp += 8;
        r.r14 = memory.readQword(r.rsp); r.rsp += 8;
        r.r13 = memory.readQword(r.rsp); r.rsp += 8;
        r.r12 = memory.readQword(r.rsp); r.rsp += 8;
        r.rdi = memory.readQword(r.rsp); r.rsp += 8;
        r.rsi = memory.readQword(r.rsp); r.rsp += 8;
        r.rbx = memory.readQword(r.rsp); r.rsp += 8;
        r.rbp = memory.readQword(r.rsp); r.rsp += 8;
        long returnRip = memory.readQword(r.rsp); r.rsp += 8;
        return new NormalReturn(r.rax, returnRip, r.rsp, r.nonvolatileBits());
    }
}

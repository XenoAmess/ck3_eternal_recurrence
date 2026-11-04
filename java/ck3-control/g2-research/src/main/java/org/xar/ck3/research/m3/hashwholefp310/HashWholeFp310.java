package org.xar.ck3.research.m3.hashwholefp310;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.hashfpgate305.HashFpGate305;
import org.xar.ck3.research.m3.hashwholefp309.HashWholeFp309Api;
import org.xar.ck3.research.m3.hashwholefp309.HashWholeFp309Api.Calls;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/** Source-specific full represented state for original[C39C60,C39F8E).
 * All thirteen lower CALLs remain explicit; no automatic recursive call or hardware proof. */
public final class HashWholeFp310 {
    private HashWholeFp310() { }

    public static HashWholeFp309Api.Result execute(HashWholeFp309Api.Input input,
            FullCopy437Api.Memory memory, Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        State s=new State(input,memory);
        try {
            long pc=enter(s);
            if (pc==0xC39CB0L) pc=probe(s,calls);
            if (pc==0xC39D3DL) {
                memory.writeQword(s.r.r15,s.r.rbx);
                memory.writeByte(s.r.r15+8,0);
            } else {
                pc=gate(s);
                if (pc==0xC39F28L) grow(s,calls);
                else if (pc==0xC39D11L) insert(s,calls);
                else throw new IllegalStateException("Unexpected gate continuation");
            }
            QueueFp604Api.Normal actual=leave(s);
            long observedReturnRip=actual.base().normalReturn().returnRipBits();
            input.checkNormalReturn(actual,observedReturnRip);
            return new HashWholeFp309Api.Forwarded(actual);
        } catch (Halt stopped) {
            return stopped.result;
        }
    }

    private static final class State {
        final HashWholeFp309Api.Input ownerInput;
        final long image;
        final long origin;
        final FullCopy437Api.Memory memory;
        final GovernmentCrtBoundary185Api.LoopBudget budget;
        final Registers r;
        boolean df;
        QueueFp604Api.Mxcsr fp;

        State(HashWholeFp309Api.Input input, FullCopy437Api.Memory sameMemory) {
            ownerInput=Objects.requireNonNull(input);
            var entry=input.entry();
            image=entry.imageBaseBits();
            origin=input.originCallSiteRva();
            memory=Objects.requireNonNull(sameMemory);
            budget=input.budget();
            df=input.directionFlagSet();
            fp=input.preMxcsr();
            r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                    image,entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
        }

        void setEntry(GovernmentCrtBoundary185Api.Entry entry) {
            if (entry.imageBaseBits()!=image) throw new IllegalArgumentException("Image mismatch");
            var n=entry.nonvolatileBits();
            r.rsp=entry.rspBits();
            r.apply(entry.volatileBits());
            r.rbx=n.rbxBits(); r.rbp=n.rbpBits(); r.rsi=n.rsiBits(); r.rdi=n.rdiBits();
            r.r12=n.r12Bits(); r.r13=n.r13Bits(); r.r14=n.r14Bits(); r.r15=n.r15Bits();
            r.x6=n.xmm6();
        }

        GovernmentCrtBoundary185Api.Entry entry() {
            return new GovernmentCrtBoundary185Api.Entry(
                    image,r.rsp,r.volatileBits(),r.nonvolatileBits());
        }

        QueueFp604Api.Snapshot snapshot(long instructionRva) {
            return new QueueFp604Api.Snapshot(entry(),instructionRva,df,fp);
        }

        void applyNormal(QueueFp604Api.Normal actual) {
            var value=actual.base().normalReturn();
            setEntry(new GovernmentCrtBoundary185Api.Entry(
                    image,value.callerRspBits(),value.volatileBits(),value.nonvolatileBits()));
            df=actual.base().postDirectionFlagSet();
            fp=actual.postMxcsr();
        }

        void applySnapshot(QueueFp604Api.Snapshot actual) {
            setEntry(actual.currentState());
            df=actual.directionFlagSet();
            fp=actual.mxcsr();
        }
    }

    private static long byteBits(long previous, int bits) {
        return (previous & ~0xFFL) | (bits & 0xFFL);
    }

    private static long dwordBits(int bits) {
        return Integer.toUnsignedLong(bits);
    }

    private static void push(State s, long bits) {
        s.r.rsp-=8;
        s.memory.writeQword(s.r.rsp,bits);
    }

    private static long pop(State s) {
        long bits=s.memory.readQword(s.r.rsp);
        s.r.rsp+=8;
        return bits;
    }

    private static long enter(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        m.writeQword(r.rsp+0x10L,r.rbx);
        push(s,r.rbp);
        push(s,r.rsi);
        push(s,r.rdi);
        push(s,r.r12);
        push(s,r.r13);
        push(s,r.r14);
        push(s,r.r15);
        r.rbp=r.rsp;
        r.rsp-=0x70L;
        r.rdi=r.r9;
        r.r13=(long)(int)r.r8;
        r.r14=r.rcx;
        r.rsi=byteBits(r.rsi,1);
        r.rcx=(long)m.readDword(r.rcx+0x14L);
        r.r15=r.rdx;
        r.r9=r.rcx;
        r.r9&=r.r13;
        r.rax=m.readQword(r.r14+8);
        r.r9=r.r9+r.r9*4;
        int occupant=m.readUnsignedByte(r.rax+r.r9*8+4);
        r.rbx=r.rax+r.r9*8;
        if (occupant<(int)(r.rsi&0xFFL)) return 0xC39CE4L;
        r.r12=m.readQword(r.rdi+0x18L);
        return 0xC39CB0L;
    }

    private static void incrementCount(State s) {
        long address=s.r.r14+0x10L;
        int value=s.memory.readDword(address);
        s.memory.writeDword(address,value+1);
    }

    private static QueueFp604Api.Normal leave(State s) {
        Registers r=s.r;
        r.rbx=s.memory.readQword(r.rsp+0xB8L);
        r.rax=r.r15;
        r.rsp+=0x70L;
        r.r15=pop(s);
        r.r14=pop(s);
        r.r13=pop(s);
        r.r12=pop(s);
        r.rdi=pop(s);
        r.rsi=pop(s);
        r.rbp=pop(s);
        long returnRip=s.memory.readQword(r.rsp);
        r.rsp+=8;
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(r.volatileBits(),returnRip,
                        r.rsp,r.nonvolatileBits()),s.df),s.fp);
    }

    private static boolean startOccupied(State s) {
        Registers r=s.r;
        r.rdx=dwordBits(s.memory.readDword(r.rbx));
        r.rax=byteBits(r.rax,(int)r.rax+1);
        r.r12=0;
        return s.memory.readUnsignedByte(r.rbx+0x2CL)!=0;
    }

    private static void moveAdjacent(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        m.writeDword(r.rbx+0x28L,(int)r.rdx);
        m.writeByte(r.rbx+0x2CL,(int)(r.rax&0xFFL));
        m.writeQword(r.rbx+0x30L,r.r12);
        m.writeQword(r.rbx+0x40L,r.r12);
        m.writeQword(r.rbx+0x48L,r.r12);
        r.x0=m.read128(r.rcx);
        m.write128(r.rbx+0x30L,r.x0);
        r.x1=m.read128(r.rcx+0x10L);
        m.write128(r.rbx+0x40L,r.x1);
        m.writeQword(r.rcx+0x10L,r.r12);
        m.writeQword(r.rcx+0x18L,0xFL);
        m.writeByte(r.rcx,(int)(r.r12&0xFFL));
        m.writeDword(r.rbx,(int)r.r13);
        m.writeByte(r.rbx+4,(int)(r.rsi&0xFFL));
    }

    private static void moveScratch(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        m.writeDword(r.rbp-0x30L,(int)r.rdx);
        m.writeByte(r.rbp-0x2CL,(int)(r.rax&0xFFL));
        r.x0=m.read128(r.rcx);
        m.write128(r.rbp-0x28L,r.x0);
        r.x1=m.read128(r.rcx+0x10L);
        m.write128(r.rbp-0x18L,r.x1);
        m.writeQword(r.rcx+0x10L,r.r12);
        m.writeQword(r.rcx+0x18L,0xFL);
        m.writeByte(r.rcx,(int)(r.r12&0xFFL));
        m.writeDword(r.rbx,(int)r.r13);
        m.writeByte(r.rbx+4,(int)(r.rsi&0xFFL));
    }

    private static void swapCurrent(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        r.rax=dwordBits(m.readDword(r.rbx));
        r.rcx=dwordBits(m.readDword(r.rbp-0x30L));
        m.writeDword(r.rbp-0x30L,(int)r.rax);
        r.rax=dwordBits(m.readUnsignedByte(r.rbx+4));
        m.writeDword(r.rbx,(int)r.rcx);
        r.rcx=dwordBits(m.readUnsignedByte(r.rbp-0x2CL));
        m.writeByte(r.rbp-0x2CL,(int)(r.rax&0xFFL));
        m.writeByte(r.rbx+4,(int)(r.rcx&0xFFL));
        r.x0=m.read128(r.rbx+8);
        r.x2=m.read128(r.rbp-0x28L);
        r.x3=m.read128(r.rbp-0x18L);
        m.write128(r.rbp-0x28L,r.x0);
        r.x1=m.read128(r.rbx+0x18L);
        m.write128(r.rbp-0x18L,r.x1);
        m.write128(r.rbx+8,r.x2);
        m.write128(r.rbx+0x18L,r.x3);
    }

    private static void swapOriginal(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        r.rax=dwordBits(m.readDword(r.rdi));
        r.rcx=dwordBits(m.readDword(r.rbp-0x30L));
        m.writeDword(r.rbp-0x30L,(int)r.rax);
        r.rax=dwordBits(m.readUnsignedByte(r.rdi+4));
        m.writeDword(r.rdi,(int)r.rcx);
        r.rcx=dwordBits(m.readUnsignedByte(r.rbp-0x2CL));
        m.writeByte(r.rbp-0x2CL,(int)(r.rax&0xFFL));
        m.writeByte(r.rdi+4,(int)(r.rcx&0xFFL));
        r.rcx=r.r14;
        r.x0=m.read128(r.rdi+8);
        r.x2=m.read128(r.rbp-0x28L);
        r.x3=m.read128(r.rbp-0x18L);
        m.write128(r.rbp-0x28L,r.x0);
        r.x1=m.read128(r.rdi+0x18L);
        m.write128(r.rbp-0x18L,r.x1);
        m.write128(r.rdi+8,r.x2);
        m.write128(r.rdi+0x18L,r.x3);
    }

    private static void fillEmpty(State s) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        r.rax=dwordBits(m.readDword(r.rbp-0x30L));
        m.writeByte(r.rbx+4,(int)(r.rcx&0xFFL));
        r.rcx=r.rbp-0x28L;
        m.writeDword(r.rbx,(int)r.rax);
        m.writeQword(r.rbx+8,r.r12);
        m.writeQword(r.rbx+0x18L,r.r12);
        m.writeQword(r.rbx+0x20L,r.r12);
        r.x0=m.read128(r.rbp-0x28L);
        m.write128(r.rbx+8,r.x0);
        r.x1=m.read128(r.rbp-0x18L);
        r.x0=m.read128(s.image+0x49F6EE0L);
        m.write128(r.rbx+0x18L,r.x1);
        m.writeByte(r.rbp-0x28L,(int)(r.r12&0xFFL));
        m.write128(r.rbp-0x18L,r.x0);
    }

    private static final class Halt extends RuntimeException {
        private static final long serialVersionUID=1L;
        final transient HashWholeFp309Api.Result result;
        Halt(HashWholeFp309Api.Result actual) {
            super(null,null,false,false);
            result=Objects.requireNonNull(actual);
        }
    }

    private record CallReturn(HashWholeFp309Api.CallFrame frame, QueueFp604Api.Normal actual) { }

    private static CallReturn invoke(State s, Calls calls, long site, long target) {
        var before=s.entry();
        var original=new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,
                before.rspBits(),before.volatileBits(),before.nonvolatileBits());
        var child=new GovernmentCrtBoundary185Api.Entry(s.image,before.rspBits()-8,
                before.volatileBits(),before.nonvolatileBits());
        var childInput=new QueueFp604Api.Input(
                new FullCopy437Api.Input(child,s.df,s.budget),s.fp);
        var frame=new HashWholeFp309Api.CallFrame(s.ownerInput,original,childInput);
        push(s,frame.returnRipBits());
        var actual=Objects.requireNonNull(calls.invoke(frame,s.memory));
        frame.checkResult(actual);
        if (actual instanceof HashWholeFp309Api.Forwarded forwarded
                && forwarded.actual() instanceof QueueFp604Api.Normal normal) {
            s.applyNormal(normal);
            return new CallReturn(frame,normal);
        }
        throw new Halt(actual);
    }

    private static long gate(State s) {
        Registers r=s.r;
        if ((int)(r.rsi&0xFFL)>s.memory.readUnsignedByte(r.r14+0x18L)) return 0xC39F28L;
        r.rax=dwordBits(s.memory.readDword(r.r14+0x10L)+1);
        var input=new HashFpGate305.Input(new QueueFp604Api.Input(
                new FullCopy437Api.Input(s.entry(),s.df,s.budget),s.fp),s.origin);
        var actual=HashFpGate305.execute(input,s.memory);
        if (actual instanceof HashFpGate305.NotCompleted stopped) {
            throw new Halt(new HashWholeFp309Api.Forwarded(stopped.stopped()));
        }
        var continued=(HashFpGate305.Continued)actual;
        s.applySnapshot(continued.snapshot());
        return continued.snapshot().instructionRva();
    }

    private static void prepareAssign(State s) {
        Registers r=s.r;
        boolean heap=Long.compareUnsigned(s.memory.readQword(r.rdi+0x18L),0x10L)>=0;
        r.r8=s.memory.readQword(r.rdi+0x10L);
        if (heap) r.rdi=s.memory.readQword(r.rdi);
        r.rdx=r.rdi;
    }

    private static void inserted(State s, long bucket) {
        incrementCount(s);
        s.memory.writeQword(s.r.r15,bucket);
        s.memory.writeByte(s.r.r15+8,1);
    }

    private static long probe(State s, Calls calls) {
        Registers r = s.r;
        FullCopy437Api.Memory m = s.memory;
        while (true) {
            s.budget.beforeStep(0xC39CB0L, r.rbx + 0x20L);
            long bucketCapacity = m.readQword(r.rbx + 0x20L);
            r.rdx = r.rbx + 8L;
            if (Long.compareUnsigned(bucketCapacity, 0x10L) >= 0) {
                r.rdx = m.readQword(r.rdx);
            }
            r.rcx = r.rdi;
            if (Long.compareUnsigned(r.r12, 0x10L) >= 0) {
                r.rcx = m.readQword(r.rdi);
            }
            var callResult = invoke(s, calls, 0xC39CCAL, 0x3F6D2B0L);
            int al = (int) callResult.actual().base().normalReturn().volatileBits().raxBits();
            if ((al & 0xFF) != 0) {
                return 0xC39D3DL;
            }
            r.rbx += 0x28L;
            r.rsi = byteBits(r.rsi, (int) (r.rsi + 1));
            int next = m.readUnsignedByte(r.rbx + 4L);
            if ((int) (r.rsi & 0xFFL) > next) {
                break;
            }
        }
        r.rcx = dwordBits(m.readDword(r.r14 + 0x14L));
        return 0xC39CE4L;
    }

    private static void insert(State s, Calls calls) {
        Registers r = s.r;
        FullCopy437Api.Memory m = s.memory;
        long currentRBX = r.rbx;

        // D11: movzx eax, byte ptr [rbx+4]
        r.rax = dwordBits(m.readUnsignedByte(r.rbx + 4L));
        // D15: lea rcx, [rbx+8]
        r.rcx = r.rbx + 8L;
        // D19: test al, al
        // D1B: jne 0xC39D4A (occupied path)
        if ((int)(r.rax & 0xFFL) != 0) {
            // Occupied path: D4A..D55 handled by startOccupied
            if (!startOccupied(s)) {
                // D55: next bucket is zero; use the D57 fallthrough.
                // D57..D8A: moveAdjacent
                moveAdjacent(s);
                // D8E: cmp rcx, rdi
                if (r.rcx != r.rdi) {
                    // D93..DA1: prepareAssign
                    prepareAssign(s);
                    // DA4: call 0x855DB0
                    invoke(s, calls, 0xC39DA4L, 0x855DB0L);
                }
                // DA9: inc dword ptr [r14+10h]
                incrementCount(s);
                // DAD: mov qword ptr [r15], rbx
                m.writeQword(r.r15, r.rbx);
                // DB0: mov byte ptr [r15+8], 1
                m.writeByte(r.r15 + 8L, 1);
                // DB5: jmp 0xC39F61
                return;
            } else {
                // DBA..DE1: moveScratch
                moveScratch(s);
                // DE5: cmp rcx, rdi
                if (r.rcx != r.rdi) {
                    // DEA..DF8: prepareAssign
                    prepareAssign(s);
                    // DFB: call 0x855DB0
                    invoke(s, calls, 0xC39DFBL, 0x855DB0L);
                }
                // E00: movzx ecx, byte ptr [rbp-2Ch]
                r.rcx = dwordBits(m.readUnsignedByte(r.rbp - 0x2CL));
                // E04: mov rdi, rbx
                r.rdi = r.rbx;
                // E07: nop
                // E10: movzx eax, byte ptr [rbx+2Ch] ... loop head
                displace(s, calls);
                // F61 reached by displace or return
                return;
            }
        } else {
            // Empty path: D1D..D33
            // D1D: mov rdx, rdi
            r.rdx = r.rdi;
            // D20: mov dword ptr [rbx], r13d
            m.writeDword(r.rbx, (int)r.r13);
            // D23: mov byte ptr [rbx+4], sil
            m.writeByte(r.rbx + 4L, (int)(r.rsi & 0xFFL));
            // D27: call 0x855F00
            invoke(s, calls, 0xC39D27L, 0x855F00L);
            // D2C: inc dword ptr [r14+10h]
            incrementCount(s);
            // D30: mov qword ptr [r15], rbx
            m.writeQword(r.r15, r.rbx);
            // D33: mov byte ptr [r15+8], 1
            m.writeByte(r.r15 + 8L, 1);
            // D38: jmp 0xC39F61
            return;
        }
    }

    private static void displace(State s, Calls calls) {
        Registers r=s.r;
        FullCopy437Api.Memory m=s.memory;
        while (true) {
            s.budget.beforeStep(0xC39E10L,r.rbx+0x2CL);
            r.rax=dwordBits(m.readUnsignedByte(r.rbx+0x2CL));
            r.rbx+=0x28L;
            if ((r.rax&0xFFL)==0) {
                fillEmpty(s);
                invoke(s,calls,0xC39F15L,0x856050L);
                inserted(s,r.rdi);
                return;
            }
            if ((r.rax&0xFFL)<(r.rcx&0xFFL)) {
                swapCurrent(s);
                r.rcx=dwordBits(m.readUnsignedByte(r.rbp-0x2CL));
                r.rcx=byteBits(r.rcx,(int)r.rcx+1);
                m.writeByte(r.rbp-0x2CL,(int)(r.rcx&0xFFL));
                continue;
            }
            r.rcx=byteBits(r.rcx,(int)r.rcx+1);
            m.writeByte(r.rbp-0x2CL,(int)(r.rcx&0xFFL));
            if ((r.rcx&0xFFL)<=m.readUnsignedByte(r.r14+0x18L)) continue;
            swapOriginal(s);
            invoke(s,calls,0xC39EADL,0xC3A400L);
            r.r8=dwordBits(m.readDword(r.rbp-0x30L));
            r.r9=r.rbp-0x28L;
            r.rdx=r.rbp-0x40L;
            r.rcx=r.r14;
            invoke(s,calls,0xC39EC1L,0xC3B960L);
            r.rcx=r.rbp-0x28L;
            invoke(s,calls,0xC39ECAL,0x856050L);
            r.x0=m.read128(r.rbp-0x40L);
            m.write128(r.r15,r.x0);
            return;
        }
    }

    private static void grow(State s, Calls calls) {
        Registers r = s.r;
        FullCopy437Api.Memory m = s.memory;

        // F28: inc ecx (32-bit)
        r.rcx = dwordBits((int)r.rcx + 1);
        // F2A: mov edx, 1
        r.rdx = 1L;

        // F2F: call 0x86E160
        var capacityCall = invoke(s, calls, 0xC39F2FL, 0x86E160L);
        int capacity = (int)capacityCall.actual().base().normalReturn().volatileBits().raxBits();

        // F34: cmp eax, 1Fh
        // F37: jge 0xC39F7C
        if (capacity >= 0x1F) {
            // Fatal path: F7C..F8D
            // F7C: mov rdx, r14
            r.rdx = r.r14;
            // F7F: lea rcx, [rbp+40h]
            r.rcx = r.rbp + 0x40L;
            // F83: call 0x86F210
            invoke(s, calls, 0xC39F83L, 0x86F210L);
            // F88: call 0x4232CF4
            var terminalCall = invoke(s, calls, 0xC39F88L, 0x4232CF4L);
            // F8D: int 3
            var boundary = new HashWholeFp309Api.Int3Boundary(
                    terminalCall.frame(),
                    terminalCall.actual(),
                    s.snapshot(0xC39F8DL));
            throw new Halt(boundary);
        }

        // Normal capacity path: F39..F5C
        // F39: mov edx, eax
        r.rdx = dwordBits(capacity);
        // F3B: mov rcx, r14
        r.rcx = r.r14;
        // F3E: call 0xC3B700
        invoke(s, calls, 0xC39F3EL, 0xC3B700L);

        // F43: lea rax, [rbp+50h]
        r.rax = r.rbp + 0x50L;
        // F47: mov byte ptr [rbp+50h], 0
        m.writeByte(r.rbp + 0x50L, 0);
        // F4B: mov r9, rdi
        r.r9 = r.rdi;
        // F4E: mov qword ptr [rsp+20h], rax
        m.writeQword(r.rsp + 0x20L, r.rax);
        // F53: mov r8d, r13d
        r.r8 = dwordBits((int)r.r13);
        // F56: mov rdx, r15
        r.rdx = r.r15;
        // F59: mov rcx, r14
        r.rcx = r.r14;

        // F5C: call 0xC39C60 (recursive)
        invoke(s, calls, 0xC39F5CL, 0xC39C60L);
    }
}

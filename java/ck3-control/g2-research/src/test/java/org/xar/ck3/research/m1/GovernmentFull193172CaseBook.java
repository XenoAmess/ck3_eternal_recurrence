package org.xar.ck3.research.m1;

import java.util.List;
import org.xar.ck3.research.m1.GovernmentAbf170CaseApi.BudgetScript;
import org.xar.ck3.research.m1.GovernmentFull193172CaseApi.Case;
import org.xar.ck3.research.m1.GovernmentFull193172CaseApi.HashScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.AtomicDword;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentLookupLoop580Api.Mxcsr32;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner independent fixed-literal oracle from retained ASM; no subject run or expected-state evaluator. */
public final class GovernmentFull193172CaseBook {
    private GovernmentFull193172CaseBook() { }
    private static final long B=0x1_0000_0000L,E=0x7000_0008L,S=0x6FFF_FFE0L;
    private static final long RETURN=0x1234_5678_7654_3210L;
    private static final long ROW=0x4000_0000L,CONTEXT=0x5000_0000L;
    private static final long GS=0x6000_0000L,TLS=0x6000_1000L;
    private static final long M=B+0x5DC1390L,ROWS=0x8000_0000L,Q=0x8000_0020L;
    private static final long DATA=0x8200_0003L,TABLE=0x9000_0000L,HIT=0xA000_3000L;
    private static final long INLINE_BUCKET=0x9000_32B8L;
    private static final long COLLISION_BUCKET=0x9000_4BD8L,NEXT_BUCKET=0x9000_4BF0L;
    private static final GovernmentLookup167Api.SpinBudget NO_LOOKUP_SPIN=(rva,address)-> {
        throw new UnsupportedOperationException("unexpected lookup spin "+Long.toHexString(rva));
    };
    private record Setup(MemoryImage memory,GovernmentRowResolve164Api.Entry entry,CallScript calls) { }

    public static List<Case> cases() { return List.of(inlineByteTail(),heapBlockCollision()); }

    /** Constant input construction only. Nonzero whole length makes both actual193 hash paths reachable. */
    private static Setup seed(long length,long capacity,int mode,int hitMagic) {
        MemoryImage m=new MemoryImage();
        NonvolatileBits n=new NonvolatileBits(0x1111_2222_3333_4444L,0x5555_6666_7777_8888L,
                0x1111_3333_5555_7777L,0x2222_4444_6666_8888L,0x3333_5555_7777_9999L,
                0x4444_6666_8888_AAAAL,0x5555_7777_9999_BBBBL,0x6666_8888_AAAA_CCCCL,vector(0x7070_7070L));
        VolatileBits v=bits(0x1200L,0x1010L,ROW,CONTEXT);
        m.writeQword(E,RETURN);
        m.writeQword(ROW,0xFACE_FACE_CAFE_CAFEL);m.writeDword(ROW+8,1);m.writeDword(ROW+0xC,0xA1B2C301);
        m.writeQword(GS,TLS);m.writeDword(TLS+0x10,5);m.writeDword(B+0x5DC1388L,-3);
        m.writeDword(M+0x48,0);m.writeDword(M+0x3C,2);m.writeQword(M+0x30,ROWS);
        m.writeQword(Q+0x10,length);m.writeQword(Q+0x18,capacity);
        if(capacity>=16) { m.writeQword(Q,DATA);m.writeDword(DATA,0x4211FF80); }
        else m.writeByte(Q,0x80);
        m.writeQword(CONTEXT+0x180,TABLE);m.writeDword(CONTEXT+0x18C,0x3FF);m.writeByte(CONTEXT+0xEE0,mode);
        if(mode==0)m.writeDword(CONTEXT+0xEA0,0);
        m.writeDword(HIT+0x38,hitMagic);
        return new Setup(m,new GovernmentRowResolve164Api.Entry(B,E,v,n),new CallScript(GS));
    }

    private static Case inlineByteTail() {
        Setup s=seed(1,15,1,0x4744624F);MemoryImage m=s.memory();VolatileBits v=s.entry().volatileBits();
        // Fixed raw-ASM arithmetic: byte80 -> packed80000001 -> hash0FEB9E1D, index21D.
        m.writeDword(INLINE_BUCKET+4,0xC4C3C201);m.writeDword(INLINE_BUCKET+8,0x0FEB9E1D);
        m.writeDword(INLINE_BUCKET+0xC,0xD5D6D7D8);m.writeQword(INLINE_BUCKET+0x10,HIT);
        HashScript hash=new HashScript().expect(0x3F7E1B0L,Q,1,Q,()-> { });
        BudgetScript resolve=new BudgetScript().expect(0xABF8B8L,INLINE_BUCKET,()-> { });
        VolatileBits out=new VolatileBits(0,0,0x201L,0xFFFF_FFFFL,0x3FFL,TABLE,0xFFFF_FFFEL,
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        GovernmentRowResolve164Api.Result expected=new GovernmentRowResolve164Api.Result(
                RETURN,0x7000_0010L,out,s.entry().nonvolatileBits());
        List<AtomicDword> atomics=List.of(new AtomicDword(M+0x48,2,0),new AtomicDword(M+0x48,-2,2),
                new AtomicDword(M+0x48,2,0),new AtomicDword(M+0x48,-2,2));
        return new Case("full193-inline-byte80-tail-unlocked-hit",s.entry(),m,s.calls(),NO_LOOKUP_SPIN,
                resolve,hash,new Mxcsr32(0x3F80),expected,2,()-> {
                    checkCommon(s,1,15,0x80000001,atomics);
                    equal(0x80,m.readUnsignedByte(Q),"single inline input byte unchanged");
                    equal(0xC4C3C201,m.readDword(INLINE_BUCKET+4),"inline bucket flag/padding");
                    equal(0x0FEB9E1D,m.readDword(INLINE_BUCKET+8),"literal inline-byte hash key");
                    equal(0xD5D6D7D8,m.readDword(INLINE_BUCKET+0xC),"inline bucket value padding");
                    equal(HIT,m.readQword(INLINE_BUCKET+0x10),"inline bucket value");
                    equal(1,m.readUnsignedByte(CONTEXT+0xEE0),"unlocked mode byte");
                    equal(0x4744624F,m.readDword(HIT+0x38),"inline matching result magic");
                });
    }

    private static Case heapBlockCollision() {
        Setup s=seed(4,16,0,0x10203040);MemoryImage m=s.memory();VolatileBits v=s.entry().volatileBits();
        // Fixed raw-ASM arithmetic: dword4211FF80 -> hashCAEB2F29, index329, two probes.
        m.writeDword(COLLISION_BUCKET+4,0x11223301);m.writeDword(COLLISION_BUCKET+8,0xDEADBEEF);
        m.writeDword(COLLISION_BUCKET+0xC,0x55667788);m.writeQword(COLLISION_BUCKET+0x10,0xB000_4000L);
        m.writeDword(NEXT_BUCKET+4,0xAABBCC02);m.writeDword(NEXT_BUCKET+8,0xCAEB2F29);
        m.writeDword(NEXT_BUCKET+0xC,0x99AABBCC);m.writeQword(NEXT_BUCKET+0x10,HIT);
        HashScript hash=new HashScript().expect(0x3F7E180L,DATA,4,0x8200_0007L,()-> { });
        BudgetScript resolve=new BudgetScript().expect(0xABF8B8L,COLLISION_BUCKET,()-> { })
                .expect(0xABF8B8L,NEXT_BUCKET,()-> { });
        VolatileBits out=new VolatileBits(1,1,0x302L,0,0x3FFL,TABLE,2,
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
        GovernmentRowResolve164Api.Result expected=new GovernmentRowResolve164Api.Result(
                RETURN,0x7000_0010L,out,s.entry().nonvolatileBits());
        List<AtomicDword> atomics=List.of(new AtomicDword(M+0x48,2,0),new AtomicDword(M+0x48,-2,2),
                new AtomicDword(M+0x48,2,0),new AtomicDword(M+0x48,-2,2),
                new AtomicDword(CONTEXT+0xEA0,2,0),new AtomicDword(CONTEXT+0xEA0,-2,2));
        return new Case("full193-heap-fourbytes-block-reader-collision-hit",s.entry(),m,s.calls(),NO_LOOKUP_SPIN,
                resolve,hash,new Mxcsr32(0x5FA0),expected,2,()-> {
                    checkCommon(s,4,16,0,atomics);
                    equal(DATA,m.readQword(Q),"actual heap string pointer unchanged");
                    equal(0x4211FF80,m.readDword(DATA),"unaligned four input bytes unchanged");
                    equal(0x11223301,m.readDword(COLLISION_BUCKET+4),"collision flag/padding");
                    equal(0xDEADBEEF,m.readDword(COLLISION_BUCKET+8),"occupied distinct wrong key");
                    equal(0x55667788,m.readDword(COLLISION_BUCKET+0xC),"collision value padding");
                    equal(0xB000_4000L,m.readQword(COLLISION_BUCKET+0x10),"unselected collision pointer");
                    equal(0xAABBCC02,m.readDword(NEXT_BUCKET+4),"second probe flag/padding");
                    equal(0xCAEB2F29,m.readDword(NEXT_BUCKET+8),"literal four-byte hash key");
                    equal(0x99AABBCC,m.readDword(NEXT_BUCKET+0xC),"second probe value padding");
                    equal(HIT,m.readQword(NEXT_BUCKET+0x10),"second probe actual hit pointer");
                    equal(0,m.readDword(CONTEXT+0xEA0),"actual reader counter restored");
                    equal(0,m.readUnsignedByte(CONTEXT+0xEE0),"reader mode byte");
                    equal(0x10203040,m.readDword(HIT+0x38),"heap differing result magic");
                });
    }

    private static void checkCommon(Setup s,long length,long capacity,int packed,List<AtomicDword> atomics) {
        MemoryImage m=s.memory();NonvolatileBits n=s.entry().nonvolatileBits();
        equal(HIT,m.readQword(ROW),"parent publishes actual selected result pointer");
        equal(1,m.readDword(ROW+8),"parent row id unchanged");
        equal(0xA1B2C302,m.readDword(ROW+0xC),"parent tag2 and adjacent padding unchanged");
        equal(RETURN,m.readQword(E),"original parent RET remains owned value");
        equal(n.rdiBits(),m.readQword(E-8),"parent saved incoming RDI");
        equal(n.rbxBits(),m.readQword(E+8),"parent saved incoming RBX");
        equal(n.rsiBits(),m.readQword(E+0x10),"parent saved incoming RSI");
        equal(B+0x2D1B86DL,m.readQword(E-0x30),"last actual ABF CALL return overwrites prior child return");
        equal(1L,m.readQword(S),"ABF incoming RBX save overwrites hash accumulator home");
        equal(1L,m.readQword(E-0x38),"wrapper saved actual parent row id RBX");
        equal(B+0x3F7E24BL,m.readQword(E-0x60),"actual nested updater CALL return slot");
        equal(length,m.readQword(E-0x58),"updater saved wrapper zero-extended length RBX");
        equal(CONTEXT,m.readQword(E-0x50),"updater saved actual parent RSI context");
        equal(ROW,m.readQword(E-0x48),"updater saved actual parent RDI row");
        equal(n.r14Bits(),m.readQword(E-0x40),"updater saved full original R14");
        equal(packed,m.readDword(E-0x18),"surviving exact hash packed home DWORD");
        equal(length,m.readQword(Q+0x10),"whole original string length word");
        equal(capacity,m.readQword(Q+0x18),"whole original string capacity word");
        equal(0,m.readDword(M+0x48),"lookup counter restored");
        equal(2,m.readDword(M+0x3C),"manager row count unchanged");
        equal(ROWS,m.readQword(M+0x30),"manager rows pointer unchanged");
        equal(atomics,m.atomicDwords,"all exact DWORD atomic observations in order");
        equal(List.of(),m.atomicBytes,"warm manager has no byte atomic");
    }
}

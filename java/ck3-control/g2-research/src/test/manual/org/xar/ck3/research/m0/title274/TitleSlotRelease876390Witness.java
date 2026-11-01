package org.xar.ck3.research.m0.title274;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m0.title274.TitleReleaseWitnessSupport274.*;

/** Owner-authored literal counterexamples; no incomplete model witness was adopted. */
public final class TitleSlotRelease876390Witness {
    private static final long I=0x140000000L, SP=0x7000L, RIP=0x123456789ABCDEF0L;
    private TitleSlotRelease876390Witness() { }

    public static void main(String[] ignored) {
        zeroDlPreservesBits(); nonBitZeroTailAndFailure(); nullReceiverComposition();
        nonnullReceiverComposition(); narrowFallbacks();
        System.out.println("PASS title-release274 cases=5 checks="+checks);
    }

    private static void zeroDlPreservesBits() {
        Image m=new Image(); m.seedQ(SP,RIP);
        VolatileBits before=v(0xFEDCBA9876543210L,0xDEADBEEFL,0x1122334455667700L,0x8888L,0x9999L,0xAAAAL,0xBBBBL);
        NonvolatileBits nv=n();
        NormalReturn out=TitleSlotRelease876390.execute(new Entry(I,SP,before,nv),m,new RejectCalls());
        eq(before,out.volatileBits(),"DLzero complete volatile bits"); eq(nv,out.nonvolatileBits(),"DLzero nonvolatile bits");
        eq(RIP,out.returnRipBits(),"DLzero original RET"); eq(0x7008L,out.callerRspBits(),"DLzero one pop");
        eq(List.of("rq@7000"),m.events,"DLzero never reads receiver/home/global");
    }

    private static void nonBitZeroTailAndFailure() {
        Image m=new Image();
        VolatileBits before=v(0xF0E1D2C3B4A59687L,0x9000L,0x100000002L,0x8888L,0x9999L,0xAAAAL,0xBBBBL);
        NonvolatileBits nv=n();
        VolatileBits atTail=v(0xF0E1D2C3B4A59687L,0x9000L,0x10L,0x8888L,0x9999L,0xAAAAL,0xBBBBL);
        NormalReturn answer=new NormalReturn(v(7L,8L,9L,10L,11L,12L,13L),0xC0DEC0DEL,0xABCDL,nv);
        List<Tail> seen=new ArrayList<>();
        Calls calls=new RejectCalls(){@Override public NormalReturn tail(Tail t){seen.add(t);return answer;}};
        NormalReturn out=TitleSlotRelease876390.execute(new Entry(I,SP,before,nv),m,calls);
        same(answer,out,"opaque tail normal result unchanged"); eq(1L,seen.size(),"whole DL2 triggers exactly one tail");
        Tail t=seen.getFirst();eq(0x876399L,t.jumpSiteRva(),"tail site");eq(TargetKind.DIRECT_RVA,t.kind(),"tail kind");
        eq(0x4223F44L,t.targetBits(),"tail target");eq(I,t.entry().imageBaseBits(),"tail image");eq(SP,t.entry().rspBits(),"tail original SP");
        eq(atTail,t.entry().volatileBits(),"MOV EDX zero extends before tail");eq(nv,t.entry().nonvolatileBits(),"tail nonvolatile bits");
        eq(List.of(),m.events,"leaf tail has no synthetic push/RET");
        RuntimeException original=new IllegalStateException("owned opaque stop");
        try {
            TitleSlotRelease876390.execute(new Entry(I,SP,before,nv),m,
                    new RejectCalls(){@Override public NormalReturn tail(Tail transfer){throw original;}});
            throw new AssertionError("throwing tail returned normally");
        } catch(RuntimeException failure){same(original,failure,"opaque exception identity");}
        eq(List.of(),m.events,"exception path has no added RET read");
    }

    private static void nullReceiverComposition() {
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(0x7010L,0xAABBCCDD11223344L);
        VolatileBits before=v(0xDEAD000000000001L,0L,2L,0x8888L,0x9999L,0xAAAAL,0xBBBBL);
        NonvolatileBits nv=n();
        NormalReturn out=TitleSlotRelease876390.execute(new Entry(I,SP,before,nv),m,
                TitleSlotRelease876390FreeCalls.bind(I,m,new RejectCalls()));
        eq(v(0L,0L,0x10L,0x8888L,0x9999L,0xAAAAL,0xBBBBL),out.volatileBits(),"null lower61 preserves thunk result/size");
        eq(nv,out.nonvolatileBits(),"null composition nonvolatile");eq(RIP,out.returnRipBits(),"null composition original RET");
        eq(0x7008L,out.callerRspBits(),"null composition one pop");eq(0xAABBCCDD00000000L,m.peekQ(0x7010L),"home write is DWORD only");
        eq(List.of("wd@7010=0","rd@7010","rq@7000"),m.events,"known thunks no extra CALL or heap read");
    }

    private static void nonnullReceiverComposition() {
        Image m=new Image();m.seedQ(SP,RIP);m.seedQ(0x7010L,0xAABBCCDD11223344L);
        m.seedQ(0x145C5DE30L,0xCAFEL);m.seedQ(0x1443DA748L,0x8000123456789ABCL);
        VolatileBits before=v(0xDEAD000000000001L,0x9000L,0x8000000000000080L,0x8888L,0x9999L,0xAAAAL,0xBBBBL);
        NonvolatileBits nv=n();
        VolatileBits returned=new VolatileBits(0x8000000100000001L,0xF101L,0xF202L,0xF303L,0xF404L,0xF505L,0xF606L,
                new Bits128(0xA1L,0xA2L),new Bits128(0xB1L,0xB2L),new Bits128(0xC1L,0xC2L),
                new Bits128(0xD1L,0xD2L),new Bits128(0xE1L,0xE2L),new Bits128(0xF1L,0xF2L));
        Calls opaque=new RejectCalls(){@Override public VolatileBits invoke(Call c){
            eq(0x424E37AL,c.callSiteRva(),"actual existing lower61 IAT site");eq(TargetKind.INDIRECT_ABSOLUTE,c.kind(),"IAT target kind");
            eq(0x8000123456789ABCL,c.targetBits(),"actual IAT contents");eq(0x6FD8L,c.rspBits(),"existing lower61 preCALL SP");
            eq(v(0L,0xCAFEL,0L,0x9000L,0x9999L,0xAAAAL,0xBBBBL),c.volatileBits(),"real free call state replaces incoming size with flags0");
            eq(nv,c.nonvolatileBits(),"opaque call nonvolatile input");
            eq(0x14424E380L,m.peekQ(0x6FD0L),"only actual lower61 CALL pushes its return");
            eq(0x1111222233334444L,m.peekQ(0x6FF8L),"actual lower61 saved RBX");
            eq(0xAABBCCDD00000000L,m.peekQ(0x7010L),"shared thunk home high half");
            m.events.add("opaque-heap");m.writeQword(SP,0x3333444455556666L);return returned;
        }};
        NormalReturn out=TitleSlotRelease876390.execute(new Entry(I,SP,before,nv),m,TitleSlotRelease876390FreeCalls.bind(I,m,opaque));
        eq(returned,out.volatileBits(),"complete opaque return bits propagated");eq(nv,out.nonvolatileBits(),"existing epilogue restores NV");
        eq(0x3333444455556666L,out.returnRipBits(),"RET reads current shared memory after callback");eq(0x7008L,out.callerRspBits(),"composed tail no second RET");
        eq(List.of("wd@7010=0","rd@7010","wq@6ff8=1111222233334444","rq@145c5de30","rq@1443da748",
                "wq@6fd0=14424e380","opaque-heap","wq@7000=3333444455556666","rq@6ff8","rq@7000"),m.events,"complete new composition memory/callback ordering");
    }

    private static void narrowFallbacks() {
        Image m=new Image();VolatileBits bits=v(1L,2L,3L,4L,5L,6L,7L);NonvolatileBits nv=n();
        Entry e=new Entry(I,SP,bits,nv);NormalReturn answer=new NormalReturn(bits,0x1234L,0x5678L,nv);
        List<Object> seen=new ArrayList<>();
        Calls opaque=new RejectCalls(){
            @Override public NormalReturn tail(Tail t){seen.add(t);return answer;}
            @Override public VolatileBits invoke(Call c){seen.add(c);return bits;}
            @Override public long readGsQword58(){seen.add("GS");return 0x8877665544332211L;}
        };
        Calls bound=TitleSlotRelease876390FreeCalls.bind(I,m,opaque);
        Tail[] mismatches={new Tail(0x876398L,TargetKind.DIRECT_RVA,0x4223F44L,e),
                new Tail(0x876399L,TargetKind.INDIRECT_ABSOLUTE,0x4223F44L,e),
                new Tail(0x876399L,TargetKind.DIRECT_RVA,0x4223F45L,e),
                new Tail(0x876399L,TargetKind.DIRECT_RVA,0x4223F44L,new Entry(I+1L,SP,bits,nv))};
        for(Tail t:mismatches){same(answer,bound.tail(t),"unmatched tail returned exact fallback result");same(t,seen.getLast(),"unmatched tail passed same object");}
        Call original=new Call(0x42L,TargetKind.DIRECT_RVA,0x424E364L,SP,bits,nv);
        same(bits,bound.invoke(original),"ordinary invoke returns same callback state");same(original,seen.getLast(),"ordinary invoke passed same object");
        eq(0x8877665544332211L,bound.readGsQword58(),"GS fallback value");eq("GS",seen.getLast(),"GS delegated");
        eq(6L,seen.size(),"four tail/invoke/GS delegates only");eq(List.of(),m.events,"fallbacks never touch bridge memory");
    }
}

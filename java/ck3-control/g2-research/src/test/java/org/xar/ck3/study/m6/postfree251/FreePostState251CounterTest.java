package org.xar.ck3.study.m6.postfree251;

import java.util.HashMap;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api.AlreadyPushedCallFrame;

/** Sole selected finite case: Stop at third actual child, after two complete opaque normal returns. */
public final class FreePostState251CounterTest {
    private static final long IMAGE=0x140000000L,S=0x100000L,P=S-0x28L;
    private static final long BLOCK=0x200000L,HEAP=0x300000L,CELL=0x600000L,RET=IMAGE+0xCC0010L;
    private static final int ERROR0=0x74747474;
    private static final QueueFp604Api.Mxcsr M0=new QueueFp604Api.Mxcsr(0x1F80,0xFFC0);
    private static final QueueFp604Api.Mxcsr M1=new QueueFp604Api.Mxcsr(0x1F81,0xFFFF);
    private static final QueueFp604Api.Mxcsr M2=new QueueFp604Api.Mxcsr(0x1F82,0xFFFF);
    private static final NonvolatileBits N0=new NonvolatileBits(0x1111222233334444L,
            0x2222333344445555L,0x3333444455556666L,0x4444555566667777L,
            0xABCDEF0112345678L,0x6666777788889999L,0x777788889999AAAAL,
            0x88889999AAAABBBBL,new Bits128(0x6061626364656667L,0x68696A6B6C6D6E6FL));
    private static final VolatileBits V1=tagged(1,0xABCD000000000000L);
    private static final VolatileBits V2=tagged(2,CELL);
    private FreePostState251CounterTest() { }

    public static void main(String[] args) {
        thirdActualChildStop();
        System.out.println("FreePostState251CounterTest: 1 finite third-child Stop case");
    }

    private static void thirdActualChildStop() {
        Ram ram=new Ram();ram.seed64(S,RET);ram.seed32(CELL,ERROR0);
        ram.seed64(IMAGE+0x5C5DE30L,HEAP);
        ram.seed64(IMAGE+0x43DA748L,IMAGE+0xAA0100L);
        ram.seed64(IMAGE+0x43DA738L,IMAGE+0xAA0300L);
        VolatileBits entryV=tagged(0,0x12345678ABCDEFF0L);
        entryV=new VolatileBits(entryV.raxBits(),BLOCK,entryV.rdxBits(),entryV.r8Bits(),entryV.r9Bits(),
                entryV.r10Bits(),entryV.r11Bits(),entryV.xmm0(),entryV.xmm1(),entryV.xmm2(),
                entryV.xmm3(),entryV.xmm4(),entryV.xmm5());
        PostState240Api.Input input=new PostState240Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,S,entryV,N0),false,M0,0xEE0010L);
        Port port=new Port(ram);
        QueueFp604Api.Outcome result=new FreePostState251(port).execute(input,ram);
        need(port.stopped!=null && result==port.stopped,"third Stop object identity was replaced");
        need(port.seen==3,"actual source did not stop after exactly three children");
        QueueFp604Api.Snapshot snapshot=port.stopped.snapshot();
        need(snapshot.currentState()==port.thirdInput.entry(),"actual child Entry identity was replaced");
        need(snapshot.currentState().rspBits()==P-8L && snapshot.currentState().volatileBits().equals(V2),
                "third stop is not the actual post-push/fullV prefix");
        NonvolatileBits expectedN=new NonvolatileBits(CELL,N0.rbpBits(),N0.rsiBits(),N0.rdiBits(),
                N0.r12Bits(),N0.r13Bits(),N0.r14Bits(),N0.r15Bits(),N0.xmm6());
        need(snapshot.currentState().nonvolatileBits().equals(expectedN),"actual failure-cell RBX/fullN was lost");
        need(!snapshot.directionFlagSet() && snapshot.mxcsr().equals(M2),"last completed child post-state was lost");
        need(snapshot.instructionRva()==0xAA0300L && port.stopped.originCallSiteRva()==0x424E38CL,
                "explicit controlled target Stop location/origin changed");
        need(ram.qwrite(P-8L)==3 && ram.qread(P-8L)==2,"Stop needs three source pushes but only two childRET reads");
        need(ram.qread(S)==0 && ram.qread(S-8L)==0,"Stop executed sourceRET or POP");
        need(ram.dwrite(CELL)==0 && ram.peek32(CELL)==ERROR0,"pending Cell32 became an erroneous RAM store");
        need(ram.peek64(S-8L)==N0.rbxBits() && ram.peek64(S)==RET,"Stop manufactured a local epilogue");
        need(ram.peek64(P-8L)==IMAGE+0x424E392L,"third preCALL owned return qword was lost");
        need(ram.dwrite(S+0x10L)==1 && ram.peek32(S+0x10L)==0,"actual17-byte thunk did not run once");
    }

    private static final class Port implements FreePostState251Api.Children {
        private final Ram ram;private int seen;
        private QueueFp604Api.Stopped stopped;private PostState240Api.Input thirdInput;
        private Port(Ram ram) { this.ram=ram; }
        @Override public QueueFp604Api.Outcome invoke(AlreadyPushedCallFrame frame,
                GovernmentCrtBoundary185Api.Memory sameMemory) {
            int stage=seen++;need(sameMemory==ram,"opaque child did not receive the same RAM");
            long site=frame.call().callSiteRva();
            if(stage==0) {
                need(site==0x424E37AL && !frame.childInput().directionFlagSet()
                        && frame.childInput().mxcsr().equals(M0),"actual first source/environment differs");
                return normal(frame,V1,true,M1);
            }
            if(stage==1) {
                need(site==0x424E384L && frame.childInput().directionFlagSet()
                        && frame.childInput().mxcsr().equals(M1),"second source missed first actual post-state");
                return normal(frame,V2,false,M2);
            }
            need(stage==2 && site==0x424E38CL,"mapper/fourth child was reached after typed Stop");
            need(!frame.childInput().directionFlagSet() && frame.childInput().mxcsr().equals(M2),
                    "third source missed second actual post-state");
            thirdInput=frame.childInput();
            stopped=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                    new QueueFp604Api.Snapshot(thirdInput.entry(),0xAA0300L,
                            thirdInput.directionFlagSet(),thirdInput.mxcsr()),0,site);
            return stopped; // explicit controlled target-entry Stop; no third childRET
        }
        private QueueFp604Api.Normal normal(AlreadyPushedCallFrame frame,VolatileBits v,
                boolean df,QueueFp604Api.Mxcsr mxcsr) {
            long actualRip=ram.readQword(frame.childInput().entry().rspBits());
            GovernmentCrtBoundary185Api.NormalReturn nr=new GovernmentCrtBoundary185Api.NormalReturn(
                    v,actualRip,frame.call().rspBits(),frame.call().nonvolatileBits());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr,df),mxcsr);
        }
    }

    private static VolatileBits tagged(int index,long rax) {
        long t=index;
        return new VolatileBits(rax,0x51000000L+t,0x52000000L+t,0x58000000L+t,
                0x59000000L+t,0x5A000000L+t,0x5B000000L+t,
                bits(index,0),bits(index,1),bits(index,2),bits(index,3),bits(index,4),bits(index,5));
    }
    private static Bits128 bits(int index,int lane) {
        return new Bits128(0xA000000000000000L+index*0x100L+lane,
                0xB000000000000000L+index*0x100L+lane);
    }
    private static void need(boolean value,String message) { if(!value)throw new AssertionError(message); }

    /** Strict byte RAM, without read-triggered mutation or branch scripting. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final Map<Long,Integer> qr=new HashMap<>(),qw=new HashMap<>(),dw=new HashMap<>();
        private int raw(long address) {
            Byte value=bytes.get(address);if(value==null)throw new AssertionError("Unseeded RAM "+Long.toHexString(address));
            return value&0xFF;
        }
        private void seed32(long address,int value) {
            for(int i=0;i<4;i++)bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        private void seed64(long address,long value) {
            for(int i=0;i<8;i++)bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        private int peek32(long address) { int value=0;for(int i=0;i<4;i++)value|=raw(address+i)<<(8*i);return value; }
        private long peek64(long address) { long value=0;for(int i=0;i<8;i++)value|=(long)raw(address+i)<<(8*i);return value; }
        private int qread(long address) { return qr.getOrDefault(address,0); }
        private int qwrite(long address) { return qw.getOrDefault(address,0); }
        private int dwrite(long address) { return dw.getOrDefault(address,0); }
        @Override public int readDword(long address) { return peek32(address); }
        @Override public long readQword(long address) { qr.merge(address,1,Integer::sum);return peek64(address); }
        @Override public int readUnsignedByte(long address) { return raw(address); }
        @Override public void writeDword(long address,int value) { dw.merge(address,1,Integer::sum);seed32(address,value); }
        @Override public void writeQword(long address,long value) { qw.merge(address,1,Integer::sum);seed64(address,value); }
        @Override public void writeByte(long address,int value) { bytes.put(address,(byte)value); }
        @Override public int lockedXaddDword(long address,int addend) { throw new AssertionError("Unexpected LOCK XADD"); }
        @Override public Bits128 read128(long address) { throw new AssertionError("Unexpected vector load"); }
        @Override public void write128(long address,Bits128 value) { throw new AssertionError("Unexpected vector store"); }
    }
}

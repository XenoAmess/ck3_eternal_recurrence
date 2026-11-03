package org.xar.ck3.study.m6.freeerror243;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postfree251.FreePostState251;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** One new251 bridge prefix: actual224/201, first child Normal, second ordinary exception. */
public final class FreePost251ChildError243Test {
    private static final long IMAGE=0x140000000L,SP=0x39008L,H=SP-0x28L,PUSH=H-8L;
    private static final long BLOCK=0x34000L,HEAP=0x35000L,ERRCELL=0x36000L;
    private static final long HEAP_SLOT=IMAGE+0x5C5DE30L,FIRST_SLOT=IMAGE+0x43DA748L,UNREACHED_SLOT=IMAGE+0x43DA738L;
    private static final long TARGET=0xF2431001L,RET=0xABCDEF0123456789L;
    private static final long FIRST_RET=IMAGE+0x424E380L,SECOND_RET=IMAGE+0x424E389L;
    private static final long RELOADED_SLOT=0x5566778800000000L;
    private static final int INITIAL_BLOCK=0x10293847,CHILD_BLOCK=0xF17E243A,ERROR_SENTINEL=0x7A6B5C4D;
    private static final Mxcsr ENTRY_M=new Mxcsr(0x1F80,0xFFC0),FIRST_POST_M=new Mxcsr(0x5F84,0xFFC4);
    private static int checks;
    private FreePost251ChildError243Test() { }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("one new251 child-error scene only");
        ordinarySecondChildPreservesPrefixAndIdentity();
        System.out.println("PASS newScenes=1 checks="+checks
                +" actual224to201=true firstNormalPoststateCarried=true secondOriginalException=true"
                +" bridgeExtraPushOrRetRead=false errorStore=false outerRet=false returnedOutcome=false"
                +" nativeChildSemantics=false JavaFloat=false Game=false");
    }

    private static void ordinarySecondChildPreservesPrefixAndIdentity() {
        Ram ram=fixture();
        NonvolatileBits incomingN=n();
        VolatileBits incomingV=replace(v(0x1200L),0xE243E243L,BLOCK,0xD243D243L,0x82438243L);
        // Complete explicitly qualified ordinary opaque result. Low EAX is zero, full RAX is distinct.
        VolatileBits firstReturned=replace(v(0x9400L),0xCD34000000000000L,0xC491L,0xD492L,0x8493L);
        IllegalStateException originalFailure=new IllegalStateException("original ordinary child at424E384");
        int[] calls={0};List<Long> sites=new ArrayList<>();
        FreePostState251Api.Children children=(frame,sameMemory)->{
            check(sameMemory==ram);
            int ordinal=calls[0]++;check(ordinal<2);
            Call call=frame.call();sites.add(call.callSiteRva());
            long site=ordinal==0?0x424E37AL:0x424E384L;
            long continuation=ordinal==0?FIRST_RET:SECOND_RET;
            VolatileBits expectedV=ordinal==0?replace(incomingV,0L,HEAP,0L,BLOCK):firstReturned;
            eq(frame.ownerEntryRva(),0x424E364L);eq(frame.imageBaseBits(),IMAGE);
            eq(call.callSiteRva(),site);eq(call.rspBits(),H);
            eq(call.kind(),ordinal==0?TargetKind.INDIRECT_ABSOLUTE:TargetKind.DIRECT_RVA);
            eq(call.targetBits(),ordinal==0?TARGET:0x423B18CL);
            eq(frame.instructionLength(),ordinal==0?6:5);eq(frame.returnRipBits(),continuation);
            eq(call.volatileBits(),expectedV);eq(call.nonvolatileBits(),incomingN);
            eq(frame.childInput().entry(),new Entry(IMAGE,PUSH,expectedV,incomingN));
            eq(frame.childInput().originCallSiteRva(),site);
            eq(frame.childInput().directionFlagSet(),ordinal!=0);
            eq(frame.childInput().mxcsr(),ordinal==0?ENTRY_M:FIRST_POST_M);
            eq(ram.peek64(PUSH),continuation);eq(ram.peek64(SP-8L),incomingN.rbxBits());
            eq(ram.peek64(SP+0x10L),RELOADED_SLOT);
            if(ordinal==0) {
                eq(ram.accesses,firstCallPrefix(incomingN));
                eq(ram.peek32(BLOCK),INITIAL_BLOCK);
                ram.writeDword(BLOCK,CHILD_BLOCK);
                // Actual child RET read belongs to this qualified port, not the metadata bridge.
                long actualRip=sameMemory.readQword(frame.childInput().entry().rspBits());
                NormalReturn nr=new NormalReturn(firstReturned,actualRip,H,call.nonvolatileBits());
                return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr,true),FIRST_POST_M);
            }
            // The failure path uses low EAX only; the entire first result must reach this next CALL.
            eq((int)call.volatileBits().raxBits(),0);eq(call.volatileBits().raxBits(),0xCD34000000000000L);
            eq(call.nonvolatileBits().rbxBits(),ERRCELL); // MOV RBX,RAX is after this child's return.
            check(!frame.childInput().mxcsr().isExact());check(!frame.childInput().mxcsr().equals(ENTRY_M));
            eq(frame.childInput().directionFlagSet(),true);
            eq(ram.accesses,exceptionPrefix(incomingN));
            eq(ram.peek32(BLOCK),CHILD_BLOCK);eq(ram.peek32(ERRCELL),ERROR_SENTINEL);
            // No read of this second child RET, no RAM effect, and no typed Outcome is supplied.
            throw originalFailure;
        };

        FreePostState251 producer=new FreePostState251(children);
        QueueFp604Api.Outcome[] offered={null};
        try {
            offered[0]=producer.execute(new PostState240Api.Input(new Entry(IMAGE,SP,incomingV,incomingN),false,ENTRY_M,0L),ram);
            throw new AssertionError("plain child exception was replaced by a returned Outcome");
        } catch(IllegalStateException thrown) {
            check(thrown==originalFailure);
        }
        check(offered[0]==null);eq(calls[0],2);eq(sites,List.of(0x424E37AL,0x424E384L));
        // Exact source/child read/write trace rejects bridge RAM operations and any source continuation.
        eq(ram.accesses,exceptionPrefix(incomingN));
        eq(ram.peek64(PUSH),SECOND_RET);eq(ram.peek64(SP-8L),ERRCELL);eq(ram.peek64(SP),RET);
        eq(ram.peek64(SP+0x10L),RELOADED_SLOT);
        eq(ram.peek32(BLOCK),CHILD_BLOCK);eq(ram.peek32(BLOCK+4L),0x31415926);
        eq(ram.peek32(ERRCELL),ERROR_SENTINEL);eq(ram.peek32(ERRCELL+4L),0x27182818);
        eq(ram.peek64(HEAP_SLOT),HEAP);eq(ram.peek64(FIRST_SLOT),TARGET);
        eq(ram.peek64(UNREACHED_SLOT),0xF2431002L);
        // No internal Context, runtime Snapshot or typed stop is constructed/captured by this test.
    }

    private static List<Access> firstCallPrefix(NonvolatileBits incomingN) {
        return List.of(new Access("W32",SP+0x10L,0L),new Access("R32",SP+0x10L,0L),
                new Access("W64",SP-8L,incomingN.rbxBits()),new Access("R64",HEAP_SLOT,HEAP),
                new Access("R64",FIRST_SLOT,TARGET),new Access("W64",PUSH,FIRST_RET));
    }
    private static List<Access> exceptionPrefix(NonvolatileBits incomingN) {
        List<Access> expected=new ArrayList<>(firstCallPrefix(incomingN));
        expected.add(new Access("W32",BLOCK,Integer.toUnsignedLong(CHILD_BLOCK)));
        expected.add(new Access("R64",PUSH,FIRST_RET));
        expected.add(new Access("W64",PUSH,SECOND_RET));return expected;
    }
    private static Ram fixture() {
        Ram ram=new Ram();ram.seed64(SP,RET);ram.seed64(SP+0x10L,0x55667788D4C3B2A1L);
        ram.seed32(BLOCK,INITIAL_BLOCK);ram.seed32(BLOCK+4L,0x31415926);
        ram.seed32(ERRCELL,ERROR_SENTINEL);ram.seed32(ERRCELL+4L,0x27182818);
        // All three static pointer cells are owned fixture values; child meanings remain opaque.
        ram.seed64(HEAP_SLOT,HEAP);ram.seed64(FIRST_SLOT,TARGET);ram.seed64(UNREACHED_SLOT,0xF2431002L);
        return ram;
    }
    private static Bits128 x(long tag) { return new Bits128(0x8A00000000000000L|tag,0xF600000000000000L|tag); }
    private static VolatileBits v(long tag) {
        return new VolatileBits(0xA100000000000000L|tag|1L,0xB200000000000000L|tag|2L,0xC300000000000000L|tag|3L,
                0xD400000000000000L|tag|4L,0xE500000000000000L|tag|5L,0xF600000000000000L|tag|6L,
                0x9700000000000000L|tag|7L,x(tag+8L),x(tag+9L),x(tag+10L),x(tag+11L),x(tag+12L),x(tag+13L));
    }
    private static VolatileBits replace(VolatileBits v,long a,long c,long d,long r8) {
        return new VolatileBits(a,c,d,r8,v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits n() {
        return new NonvolatileBits(ERRCELL,0xB201020304050607L,0xB311121314151617L,0xB421222324252627L,
                0xB531323334353637L,0xB641424344454647L,0xB751525354555657L,0xB861626364656667L,x(0x251243L));
    }
    private record Access(String op,long address,long value) { }

    /** Stable owned byte memory. Access trace observes effects; data reads do not mutate any byte. */
    private static final class Ram implements Memory {
        private final Map<Long,Integer> bytes=new HashMap<>();
        private final List<Access> accesses=new ArrayList<>();
        void seed64(long a,long v) { for(int j=0;j<8;j++)bytes.put(a+j,(int)(v>>>(8*j))&255); }
        void seed32(long a,int v) { for(int j=0;j<4;j++)bytes.put(a+j,(v>>>(8*j))&255); }
        int byteAt(long a) { Integer b=bytes.get(a);if(b==null)throw new UnsupportedOperationException("unheld251-errorRAM "+Long.toHexString(a));return b; }
        long peek64(long a) { long v=0;for(int j=0;j<8;j++)v|=(long)byteAt(a+j)<<(8*j);return v; }
        int peek32(long a) { int v=0;for(int j=0;j<4;j++)v|=byteAt(a+j)<<(8*j);return v; }
        @Override public long readQword(long a) { long v=peek64(a);accesses.add(new Access("R64",a,v));return v; }
        @Override public int readDword(long a) { int v=peek32(a);accesses.add(new Access("R32",a,Integer.toUnsignedLong(v)));return v; }
        @Override public int readUnsignedByte(long a) { int v=byteAt(a);accesses.add(new Access("R8",a,v));return v; }
        @Override public void writeQword(long a,long v) { accesses.add(new Access("W64",a,v));seed64(a,v); }
        @Override public void writeDword(long a,int v) { accesses.add(new Access("W32",a,Integer.toUnsignedLong(v)));seed32(a,v); }
        @Override public void writeByte(long a,int v) { accesses.add(new Access("W8",a,v&255));bytes.put(a,v&255); }
        @Override public Bits128 read128(long a) { return new Bits128(readQword(a),readQword(a+8L)); }
        @Override public void write128(long a,Bits128 v) { writeQword(a,v.lowBits());writeQword(a+8L,v.highBits()); }
        @Override public int lockedXaddDword(long a,int v) { throw new AssertionError("unexpected251 atomic"); }
    }
    private static void eq(long a,long e) { checks++;if(a!=e)throw new AssertionError("check="+checks+" actual="+Long.toHexString(a)+" expected="+Long.toHexString(e)); }
    private static void eq(boolean a,boolean e) { checks++;if(a!=e)throw new AssertionError("check="+checks+" actual="+a+" expected="+e); }
    private static void eq(Object a,Object e) { checks++;if(!Objects.equals(a,e))throw new AssertionError("check="+checks+" actual="+a+" expected="+e); }
    private static void check(boolean condition) { checks++;if(!condition)throw new AssertionError("check="+checks); }
}

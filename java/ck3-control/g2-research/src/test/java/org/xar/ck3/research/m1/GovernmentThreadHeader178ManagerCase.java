package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.Ports;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner fixed source-derived caller literals after two rejected model books; no subject-derived expected values. */
public final class GovernmentThreadHeader178ManagerCase {
    private GovernmentThreadHeader178ManagerCase() { }
    private static int checks;
    private static void e(Object expected,Object actual,String label){checks++;equal(expected,actual,label);}
    private static VolatileBits fields(VolatileBits old,long rax,long rcx,long rdx,long r8) {
        return new VolatileBits(rax,rcx,rdx,r8,old.r9Bits(),old.r10Bits(),old.r11Bits(),
                old.xmm0(),old.xmm1(),old.xmm2(),old.xmm3(),old.xmm4(),old.xmm5());
    }

    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");
        final long B=0x1_0000_0000L,S=0x7000_0008L,RET=0x1234_5678_7654_3210L;
        final long GS=0x6000_0000L,TLS=0x6000_1000L,G=B+0x5DC1388L,CS=B+0x5C5CB18L;
        MemoryImage memory=new MemoryImage();
        memory.writeQword(S,RET);memory.writeQword(GS,TLS);memory.writeDword(TLS+0x10,-10);
        memory.writeDword(G,-5);memory.writeDword(B+0x5C5CBC4L,0);memory.writeDword(B+0x542F090L,-3);
        VolatileBits incoming=bits(0x1200,0x1010,0x2020,0x3030);
        NonvolatileBits n=new NonvolatileBits(0x1111_2222_3333_4444L,0x5555_6666_7777_8888L,
                0x1111_3333_5555_7777L,0x2222_4444_6666_8888L,0x3333_5555_7777_9999L,
                0x4444_6666_8888_AAAAL,0x5555_7777_9999_BBBBL,0x6666_8888_AAAA_CCCCL,vector(0x7070_7070L));
        Entry entry=new Entry(B,S,incoming,n);
        VolatileBits enterPost=bits(0xE500,0xE601,0xE702,0xE803);
        VolatileBits leavePost=bits(0xC500,0xC601,0xC702,0xC803);
        NonvolatileBits inside=new NonvolatileBits(G,n.rbpBits(),n.rsiBits(),n.rdiBits(),
                n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        IatCall expectedEnter=new IatCall(0x4223A94L,0x43DA500L,0x6FFF_FFB0L,false,
                fields(incoming,0xFFFF_FFF6L,CS,0x10,incoming.r8Bits()),inside);
        IatCall expectedLeave=new IatCall(0x4223AE4L,0x43DA4F0L,0x6FFF_FFD8L,true,
                fields(enterPost,0xFFFF_FFFDL,CS,TLS,0x10),n);
        int[] managerGs={0},headerGs={0},iat={0};
        Calls delegate=new Calls() {
            @Override public long readGsQword58(){managerGs[0]++;return GS;}
            @Override public VolatileBits invoke(OpaqueCall call){throw new AssertionError("unexpected unbound manager call "+call);}
        };
        Ports ports=new Ports() {
            @Override public long readGsQword58(){headerGs[0]++;return GS;}
            @Override public VolatileBits invoke(OpaqueCall call){throw new AssertionError("unexpected wait "+call);}
            @Override public VolatileBits invokeIat(IatCall actual) {
                if(iat[0]++==0) {
                    e(expectedEnter,actual,"actual complete Enter frame through manager");
                    e(B+0x3F8A818L,memory.readQword(0x6FFF_FFD8L),"manager actual CALL continuation");
                    e(B+0x4223A9AL,memory.readQword(0x6FFF_FFA8L),"header actual Enter CALL continuation");
                    e(n.rbxBits(),memory.readQword(0x6FFF_FFD0L),"header saved incoming RBX");
                    return enterPost;
                }
                if(iat[0]!=2)throw new AssertionError("extra import port");
                e(expectedLeave,actual,"actual complete Leave tail frame through manager");
                e(-3,memory.readDword(TLS+0x10),"completed header updated same manager TLS DWORD");
                e(B+0x3F8A818L,memory.readQword(0x6FFF_FFD8L),"tail did not push over original child RET");
                e(B+0x4223A9AL,memory.readQword(0x6FFF_FFA8L),"tail did not invent CALL continuation");
                return leavePost;
            }
        };
        NormalReturn actual=GovernmentThreadHeader178Calls.executeManager(entry,memory,delegate,ports,
                (header,guard,observed)->{throw new AssertionError("completed guard unexpectedly waited");});
        NormalReturn expected=new NormalReturn(fields(leavePost,B+0x5DC1390L,leavePost.rcxBits(),
                leavePost.rdxBits(),leavePost.r8Bits()),n,RET,S+8);
        e(expected,actual,"full actual manager return after concrete header consumer");
        e(1,managerGs[0],"original manager GS query");e(1,headerGs[0],"concrete header GS query");e(2,iat[0],"two actual typed import ports");
        e(-5,memory.readDword(G),"completed guard unchanged");e(-3,memory.readDword(TLS+0x10),"updated TLS retained");
        e(0,memory.readDword(B+0x5C5CBC4L),"TLS index unchanged");e(-3,memory.readDword(B+0x542F090L),"epoch source unchanged");
        e(RET,memory.readQword(S),"original manager RET unchanged");
        System.out.println("{\"new_manager_consumer_cases\":1,\"counted_assertions\":"+checks+",\"Game_calls\":0}");
    }
}

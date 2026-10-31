package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.Ports;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** One owner source-derived literal from the pre-implementation held-ASM plan184.
 * All full volatile import/library results are controlled ports, not observed OS behavior. */
public final class GovernmentColdManager184Case {
    private GovernmentColdManager184Case() { }
    private static final long B=0x1_0000_0000L,S=0x7000_0008L,RET=0x1234_5678_7654_3210L;
    private static final long GS=0x6000_0000L,TLS=0x6000_1000L,CS=0x1_05C5_CB18L,CV=0x1_05C5_CB08L;
    private static final long FN=0x1234_0000_ABCD_EF00L,MG=0x1_05DC_1388L,MR=0x1_05DC_1390L;
    private static final long GG=0x1_05D2_E27CL,GR=0x1_05D2_E280L,CB=0x1_043D_7BE0L;
    private static int checks;
    private static void eq(Object e,Object a,String s){checks++;equal(e,a,s);}
    private static VolatileBits v(VolatileBits p,long a,long c,long d,long r8,long r9,Bits128 x0) {
        return new VolatileBits(a,c,d,r8,r9,p.r10Bits(),p.r11Bits(),x0,p.xmm1(),p.xmm2(),p.xmm3(),p.xmm4(),p.xmm5());
    }
    private static VolatileBits regs(VolatileBits p,long a,long c,long d){return v(p,a,c,d,p.r8Bits(),p.r9Bits(),p.xmm0());}
    private static NonvolatileBits rbx(NonvolatileBits p,long a){return new NonvolatileBits(a,p.rbpBits(),p.rsiBits(),p.rdiBits(),p.r12Bits(),p.r13Bits(),p.r14Bits(),p.r15Bits(),p.xmm6());}
    /** Test-only write observation delegating all storage to the already existing byte-memory fixture. */
    private static final class ObservedMemory implements GovernmentSharedManager167Api.Memory {
        final MemoryImage image=new MemoryImage();int recordFooterPush;
        @Override public int readDword(long a){return image.readDword(a);}
        @Override public long readQword(long a){return image.readQword(a);}
        @Override public int readUnsignedByte(long a){return image.readUnsignedByte(a);}
        @Override public void writeDword(long a,int b){image.writeDword(a,b);}
        @Override public int lockedXaddDword(long a,int b){return image.lockedXaddDword(a,b);}
        @Override public int lockedXaddByte(long a,int b){return image.lockedXaddByte(a,b);}
        @Override public void writeByte(long a,int b){image.writeByte(a,b);}
        @Override public void writeQword(long a,long b){if(a==0x6FFF_FFA8L&&b==0x1_02D8_88CBL)recordFooterPush++;image.writeQword(a,b);}
        @Override public Bits128 read128(long a){return image.read128(a);}
        @Override public void write128(long a,Bits128 b){image.write128(a,b);}
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");checks=0;
        ObservedMemory m=new ObservedMemory();
        m.writeQword(S,RET);m.writeQword(GS,TLS);m.writeDword(TLS+0x10,-1);
        m.writeDword(MG,0);m.writeDword(GG,0);m.writeDword(B+0x542F090L,0);m.writeDword(B+0x5C5CBC4L,0);
        m.writeQword(B+0x5C5CB68L,-1);m.writeQword(B+0x5C5CB48L,FN);
        m.writeByte(B+0x5DC1360L,0xFE);m.writeDword(B+0x49F6430L,0x3FC00000);
        for(int i=0;i<0x40;i++)m.writeByte(GR+i,0xA5);
        VolatileBits incoming=bits(0x1000,0x1111,0x2222,0x3333);
        VolatileBits p=bits(0xD000,0xAABB_CCDD_0011_2233L,0xE000,0xF000);
        NonvolatileBits n=new NonvolatileBits(0x3111_2222_3333_4400L,0x3111_2222_3333_4401L,
                0x3111_2222_3333_4402L,0x3111_2222_3333_4403L,0x3111_2222_3333_4404L,
                0x3111_2222_3333_4405L,0x3111_2222_3333_4406L,0x3111_2222_3333_4407L,vector(0x3111_2222_3333_4408L));
        IatCall[] expected={
            new IatCall(0x4223A94L,0x43DA500L,0x6FFF_FFB0L,false,regs(incoming,0xFFFF_FFFFL,CS,0x10),rbx(n,MG)),
            new IatCall(0x4223AE4L,0x43DA4F0L,0x6FFF_FFD8L,true,regs(p,p.raxBits(),CS,p.rdxBits()),n),
            new IatCall(0x4223A94L,0x43DA500L,0x6FFF_FF80L,false,regs(p,0xFFFF_FFFFL,CS,0x10),rbx(n,GG)),
            new IatCall(0x4223AE4L,0x43DA4F0L,0x6FFF_FFA8L,true,regs(p,p.raxBits(),CS,p.rdxBits()),n),
            new IatCall(0x4223A34L,0x43DA500L,0x6FFF_FF80L,false,regs(p,p.raxBits(),CS,p.rdxBits()),rbx(n,GG)),
            new IatCall(0x4223A74L,0x43DA4F0L,0x6FFF_FF80L,false,v(p,1,CS,0,TLS,0x10,p.xmm0()),rbx(n,GG)),
            new IatCall(0x4223B07L,0x43DBBA8L,0x6FFF_FFA8L,true,regs(p,FN,CV,p.rdxBits()),n),
            new IatCall(0x4223A34L,0x43DA500L,0x6FFF_FFB0L,false,regs(p,0,CS,CB),rbx(n,MG)),
            new IatCall(0x4223A74L,0x43DA4F0L,0x6FFF_FFB0L,false,v(p,2,CS,0,TLS,0x10,p.xmm0()),rbx(n,MG)),
            new IatCall(0x4223B07L,0x43DBBA8L,0x6FFF_FFD8L,true,regs(p,FN,CV,p.rdxBits()),n)
        };
        int[] iat={0},portGs={0},delegateGs={0},library={0};
        Ports ports=new Ports() {
            @Override public long readGsQword58(){portGs[0]++;return GS;}
            @Override public VolatileBits invoke(OpaqueCall c){throw new AssertionError("unexpected wait/opaque port "+c);}
            @Override public VolatileBits invokeIat(IatCall c) {
                if(iat[0]>=expected.length)throw new AssertionError("extra IAT");
                eq(expected[iat[0]++],c,"full cold IAT frame");return p;
            }
        };
        VolatileBits libV=v(p,B+0x54DE218L,CB,0,p.r8Bits(),p.r9Bits(),new Bits128(0x3FC00000L,0));
        OpaqueCall libExpected=new OpaqueCall(0x4223EFBL,0x424DE78L,0x6FFF_FF80L,libV,rbx(n,CB));
        Calls delegate=new Calls() {
            @Override public long readGsQword58(){delegateGs[0]++;return GS;}
            @Override public VolatileBits invoke(OpaqueCall c) {
                eq(0,library[0]++,"one real unresolved library edge");eq(libExpected,c,"full library source frame");
                eq(0x1_0422_3F00L,m.readQword(0x6FFF_FF78L),"library original CALL push");
                return regs(p,0,p.rcxBits(),p.rdxBits());
            }
        };
        NormalReturn result=GovernmentColdManager184.execute(new Entry(B,S,incoming,n),m,delegate,ports,
                (h,g,observed)->{throw new AssertionError("unexpected wait budget");});
        eq(new NormalReturn(regs(p,MR,p.rcxBits(),p.rdxBits()),n,RET,0x7000_0010L),result,"complete cold raw normal return");
        eq(10,iat[0],"ten actual import edges");eq(2,portGs[0],"two footer GS reads");
        eq(2,delegateGs[0],"manager/getter GS reads");eq(1,library[0],"one library call");
        eq(1,m.recordFooterPush,"getter Footer return physically pushed once, bridge no duplicate");
        eq(2,m.readDword(B+0x542F090L),"global epoch twice incremented");eq(2,m.readDword(MG),"manager epoch");
        eq(1,m.readDword(GG),"getter epoch");eq(2,m.readDword(TLS+0x10),"last footer TLS epoch");
        eq(0xFF,m.readUnsignedByte(B+0x5DC1360L),"atomic oldFE increments FF");eq(0xFE,m.readUnsignedByte(MR),"old atomic byte stored");
        eq(GR,m.readQword(B+0x5DC13A0L),"actual getter record stored");eq(0x3FC00000,m.readDword(B+0x5DC13B4L),"scalar raw bits stored");
        eq(B+0x54E8EA8L,m.readQword(B+0x5DC13B8L),"first source address");eq(B+0x54DE218L,m.readQword(B+0x5DC13D0L),"second source address");
        eq(0L,m.readQword(B+0x5DC13A8L),"zero qword A8");eq(0,m.readUnsignedByte(B+0x5DC13B0L),"zero byte B0");
        eq(0L,m.readQword(B+0x5DC13C0L),"zero qword C0");eq(0L,m.readQword(B+0x5DC13C8L),"zero qword C8");eq(0,m.readDword(B+0x5DC13D8L),"zero dword D8");
        for(int i=0;i<0x40;i++)eq(i==4?0:i==0x34?0xFF:0xA5,m.readUnsignedByte(GR+i),"getter exact two BYTE writes and padding");
        eq(-1L,m.readQword(B+0x5C5CB68L),"registry sentinel unchanged");
        eq(1,m.image.atomicBytes.size(),"one actual atomicBYTE");
        eq(new GovernmentSharedComposition168Fixture.AtomicByte(B+0x5DC1360L,1,0xFE),m.image.atomicBytes.get(0),"atomicBYTE exact address/addend/old");
        System.out.println("{\"new_actual_manager_cold_cases\":1,\"counted_assertions\":"+checks+",\"IAT_edges\":10,\"opaque_library_edges\":1,\"Native_or_Game\":0}");
    }
}

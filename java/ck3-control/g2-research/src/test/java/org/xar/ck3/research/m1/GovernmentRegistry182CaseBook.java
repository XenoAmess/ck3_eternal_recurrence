package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner literals from held23B/58B ASM after all model case candidates were rejected.
 * The owner reviewed implementation candidates; expected records are source-derived, never run-derived.
 * Scripted stack writes are controlled memory effects, not observed library/Windows behavior. */
public final class GovernmentRegistry182CaseBook {
    private GovernmentRegistry182CaseBook() { }
    private static final long B=0x1_0000_0000L,E=0x7000_0008L,W=0x6FFF_FFE0L;
    private static final long RET=0x1234_5678_7654_3210L,G=0x1_05C5_CB68L;
    private static int checks;
    private static void eq(Object expected,Object actual,String message){checks++;equal(expected,actual,message);}
    private static NonvolatileBits n(long b) {
        return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,vector(b+8));
    }
    private static NonvolatileBits rbx(NonvolatileBits n,long value) {
        return new NonvolatileBits(value,n.rbpBits(),n.rsiBits(),n.rdiBits(),
                n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits fields(VolatileBits v,long rax,long rcx,long rdx) {
        return new VolatileBits(rax,rcx,rdx,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static Calls one(OpaqueCall expected,VolatileBits post,Runnable effect,int[] count) {
        return new Calls() {
            @Override public long readGsQword58(){throw new AssertionError("unexpected GS read");}
            @Override public VolatileBits invoke(OpaqueCall actual) {
                eq(0,count[0]++,"single actual port");eq(expected,actual,"full source call frame");
                effect.run();return post;
            }
        };
    }
    private static void zeroStatus() {
        MemoryImage m=new MemoryImage();m.writeQword(E,RET);
        NonvolatileBits nv=n(0x3111_2222_3333_4400L);
        VolatileBits incoming=bits(0x1100,0xA110,0xB110,0xC110);
        VolatileBits post=bits(0xD100,0,0xE110,0xF110);
        int[] calls={0};long changedRet=0x2233_4455_6677_8899L;
        OpaqueCall expected=new OpaqueCall(0x4223F28L,0x4223EE8L,W,incoming,nv);
        NormalReturn actual=GovernmentRegistryStatus182.execute(new Entry(B,E,incoming,nv),m,
                one(expected,post,()->{
                    eq(0x1_0422_3F2DL,m.readQword(0x6FFF_FFD8L),"status actual pushed RIP");
                    m.writeQword(E,changedRet);
                },calls));
        eq(new NormalReturn(fields(post,0xFFFF_FFFFL,post.rcxBits(),post.rdxBits()),nv,changedRet,0x7000_0010L),actual,"zero rawRAX status and fresh originalRET");
        eq(1,calls[0],"one status call");
        eq(0x1_0422_3F2DL,m.readQword(0x6FFF_FFD8L),"status return-slot retained");
    }
    private static void highOnlyStatus() {
        MemoryImage m=new MemoryImage();m.writeQword(E,RET);
        NonvolatileBits nv=n(0x3222_3333_4444_5500L);
        VolatileBits incoming=bits(0x1200,0xA120,0xB120,0xC120);
        VolatileBits post=bits(0xD200,0x8000_0000_0000_0000L,0xE120,0xF120);
        int[] calls={0};OpaqueCall expected=new OpaqueCall(0x4223F28L,0x4223EE8L,W,incoming,nv);
        NormalReturn actual=GovernmentRegistryStatus182.execute(new Entry(B,E,incoming,nv),m,
                one(expected,post,()->eq(0x1_0422_3F2DL,m.readQword(0x6FFF_FFD8L),"high-only actual pushed RIP"),calls));
        eq(new NormalReturn(fields(post,0,post.rcxBits(),post.rdxBits()),nv,RET,0x7000_0010L),actual,"full64 NEG carry despite zero lowEAX");
        eq(1,calls[0],"one high-only status call");
    }
    private static void minusOneEntry() {
        MemoryImage m=new MemoryImage();m.writeQword(E,RET);m.writeQword(G,-1);
        NonvolatileBits nv=n(0x3333_4444_5555_6600L);
        long callback=0x9988_7766_5544_3322L,changedRbx=0x8877_6655_4433_2211L;
        VolatileBits incoming=bits(0x1300,0xA130,callback,0xC130);
        VolatileBits post=bits(0xD300,0x1234_5678_0000_0000L,0xE130,0xF130);
        int[] calls={0};OpaqueCall expected=new OpaqueCall(0x4223EFBL,0x424DE78L,W,incoming,rbx(nv,callback));
        NormalReturn actual=GovernmentRegistryEntry183.execute(new Entry(B,E,incoming,nv),m,
                one(expected,post,()->{
                    eq(0x1_0422_3F00L,m.readQword(0x6FFF_FFD8L),"sentinel actual pushed RIP");
                    eq(nv.rbxBits(),m.readQword(0x7000_0000L),"actual saved incoming RBX");
                    m.writeQword(0x7000_0000L,changedRbx);
                },calls));
        eq(new NormalReturn(fields(post,callback,post.rcxBits(),callback),rbx(nv,changedRbx),RET,0x7000_0010L),actual,"lowEAX0 selects raw callback register and POP reads modified slot");
        eq(-1L,m.readQword(G),"sentinel global unchanged");eq(1,calls[0],"one sentinel branch call");
    }
    private static void otherEntry() {
        MemoryImage m=new MemoryImage();m.writeQword(E,RET);m.writeQword(G,0);
        NonvolatileBits nv=n(0x3444_5555_6666_7700L);
        long callback=0x7766_5544_3322_1100L;
        VolatileBits incoming=bits(0x1400,0xA140,callback,0xC140);
        VolatileBits offered=fields(incoming,incoming.raxBits(),G,callback);
        VolatileBits post=bits(0xD400,0x8000_0001L,0xE140,0xF140);
        int[] calls={0};OpaqueCall expected=new OpaqueCall(0x4223F0CL,0x424DEECL,W,offered,rbx(nv,callback));
        NormalReturn actual=GovernmentRegistryEntry183.execute(new Entry(B,E,incoming,nv),m,
                one(expected,post,()->{
                    eq(0x1_0422_3F11L,m.readQword(0x6FFF_FFD8L),"other actual pushed RIP");
                    eq(nv.rbxBits(),m.readQword(0x7000_0000L),"other saved incoming RBX");
                },calls));
        eq(new NormalReturn(fields(post,0,post.rcxBits(),0),nv,RET,0x7000_0010L),actual,"nonzero lowEAX selects zero without changing other postV");
        eq(0L,m.readQword(G),"other global unchanged");eq(1,calls[0],"one other branch call");
    }
    public static int runAll(){checks=0;zeroStatus();highOnlyStatus();minusOneEntry();otherEntry();return checks;}
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");
        int count=runAll();System.out.println("{\"new_cases\":4,\"counted_assertions\":"+count+",\"Native_or_Game\":0}");
    }
}

package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Source-only literal oracles. Opaque scripts describe owned inputs, not real CRT behavior. */
public final class GovernmentRegistryTable186Cases {
    private static final long B=0x100000000L;
    private static int assertions;
    private GovernmentRegistryTable186Cases() { }
    private static void equal(Object expected, Object actual, String label) {
        assertions++;
        if (!Objects.equals(expected,actual)) throw new AssertionError(label+" expected="+expected+" actual="+actual);
    }
    private static NonvolatileBits n() {
        return new NonvolatileBits(0x1111111111111111L,0x2222222222222222L,
                0x3333333333333333L,0x4444444444444444L,0x5555555555555555L,
                0x6666666666666666L,0x7777777777777777L,0x8888888888888888L,vector(0x70707070L));
    }
    private static NonvolatileBits changed(NonvolatileBits n,long rbx,long rbp) {
        return new NonvolatileBits(rbx,rbp,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits offered(VolatileBits v,long rcx,long rdx,long r8,long r9) {
        return new VolatileBits(2,rcx,rdx,r8,r9,v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static void directMutableFrame() {
        MemoryImage m=new MemoryImage();
        VolatileBits in=bits(0x1100,0x1010,0x40000000,0x50000000);
        VolatileBits post=bits(0x2200,0xA0A0,0xB0B0,0xC0C0);
        NonvolatileBits incoming=n();
        m.writeQword(0x70000008L,0x1234567876543210L);
        m.writeDword(0x6FFFFFE4L,0xA1B2C3D4);
        m.writeDword(0x7000002CL,0x55667788);
        m.writeQword(0x70000020L,0xF0E1D2C3B4A59687L);
        int[] calls={0};
        Calls port=new Calls() {
            @Override public long readGsQword58() { throw new AssertionError("186 has no GS read"); }
            @Override public VolatileBits invoke(OpaqueCall call) {
                equal(0,calls[0]++,"one DB38 call");
                equal(new OpaqueCall(0x424DF29L,0x424DB38L,0x6FFFFFC0L,
                        offered(in,0x70000020L,0x6FFFFFE0L,0x6FFFFFE8L,0x70000028L),
                        changed(incoming,0x1111111111111111L,0x70000000L)),call,"complete call ABI");
                equal(0x10424DF2EL,m.readQword(0x6FFFFFB8L),"physical DB38 CALL return");
                equal(0x40000000L,m.readQword(0x70000010L),"RCX home qword");
                equal(0x50000000L,m.readQword(0x70000018L),"RDX home qword");
                equal(0x70000010L,m.readQword(0x6FFFFFE8L),"first pointer address");
                equal(0x70000018L,m.readQword(0x6FFFFFF0L),"second pointer address");
                equal(2,m.readDword(0x6FFFFFE0L),"local DWORD2");
                equal(2,m.readDword(0x70000028L),"home DWORD2");
                equal(0xA1B2C3D4,m.readDword(0x6FFFFFE4L),"local adjacent upper DWORD");
                equal(0x55667788,m.readDword(0x7000002CL),"home adjacent upper DWORD");
                equal(0xF0E1D2C3B4A59687L,m.readQword(0x70000020L),"LEA address not loaded or written");
                equal(0x2222222222222222L,m.readQword(0x70000000L),"real PUSH RBP");
                m.writeQword(0x70000000L,0xABCDEF0123456789L);
                m.writeQword(0x70000008L,0x8877665544332211L);
                return post;
            }
        };
        GovernmentCallee164Api.NormalReturn result=GovernmentRegistryTable186.execute(
                new GovernmentCallee164Api.Entry(B,0x70000008L,in,incoming),m,port);
        equal(1,calls[0],"single opaque invocation");
        equal(post,result.volatileBits(),"all supplied postV");
        equal(changed(incoming,0x1111111111111111L,0xABCDEF0123456789L),result.nonvolatileBits(),"actual mutable POP RBP");
        equal(0x8877665544332211L,result.returnRipBits(),"actual mutable RET");
        equal(0x70000010L,result.callerRspBits(),"actual epilogue RSP");
        equal(0,m.atomicDwords.size(),"no atomic DWORD invented");
        equal(0,m.atomicBytes.size(),"no atomic BYTE invented");
    }
    private static void actualEntry183Regular() {
        MemoryImage m=new MemoryImage();
        NonvolatileBits incoming=n();
        VolatileBits in=bits(0x3300,0x11112222,0x44000000,0x55556666);
        VolatileBits post=bits(0x4400,0x100000000L,0x12344321,0x56788765);
        m.writeQword(0x105C5CB68L,0);
        m.writeQword(0x71000008L,0x5566778899AABBCCL);
        m.writeDword(0x70FFFFB4L,0x10293847);
        m.writeDword(0x70FFFFFCL,0x56473829);
        int[] calls={0};
        Calls port=new Calls() {
            @Override public long readGsQword58() { throw new AssertionError("regular path has no GS read"); }
            @Override public VolatileBits invoke(OpaqueCall call) {
                equal(0,calls[0]++,"sole actual DB38 call through both methods");
                equal(new OpaqueCall(0x424DF29L,0x424DB38L,0x70FFFF90L,
                        offered(in,0x70FFFFF0L,0x70FFFFB0L,0x70FFFFB8L,0x70FFFFF8L),
                        changed(incoming,0x44000000L,0x70FFFFD0L)),call,"actual183 to186 frame");
                equal(0x104223F11L,m.readQword(0x70FFFFD8L),"producer original CALL return survives");
                equal(0x10424DF2EL,m.readQword(0x70FFFF88L),"child DB38 CALL return");
                equal(0x105C5CB68L,m.readQword(0x70FFFFE0L),"actual global-address home");
                equal(0x44000000L,m.readQword(0x70FFFFE8L),"actual incoming query home");
                equal(0x70FFFFE0L,m.readQword(0x70FFFFB8L),"actual first stack pointer");
                equal(0x70FFFFE8L,m.readQword(0x70FFFFC0L),"actual second stack pointer");
                equal(2,m.readDword(0x70FFFFB0L),"actual local DWORD");
                equal(2,m.readDword(0x70FFFFF8L),"actual upper stack DWORD");
                equal(0x10293847,m.readDword(0x70FFFFB4L),"actual local padding");
                equal(0x56473829,m.readDword(0x70FFFFFCL),"actual home padding");
                return post;
            }
        };
        GovernmentCallee164Api.NormalReturn result=GovernmentRegistryTable186Calls.executeEntry183(
                new GovernmentCallee164Api.Entry(B,0x71000008L,in,incoming),m,port);
        VolatileBits expected=new VolatileBits(0x44000000L,post.rcxBits(),0x44000000L,
                post.r8Bits(),post.r9Bits(),post.r10Bits(),post.r11Bits(),post.xmm0(),post.xmm1(),
                post.xmm2(),post.xmm3(),post.xmm4(),post.xmm5());
        equal(1,calls[0],"only DB38 remains opaque");
        equal(expected,result.volatileBits(),"low EAX zero uses original query in parent");
        equal(incoming,result.nonvolatileBits(),"whole actual caller restores N");
        equal(0x5566778899AABBCCL,result.returnRipBits(),"whole actual caller RET");
        equal(0x71000010L,result.callerRspBits(),"whole actual caller RSP");
    }
    private static void exactForeignDelegation() {
        MemoryImage m=new MemoryImage();
        VolatileBits in=bits(0x5500,1,2,3), post=bits(0x6600,4,5,6);
        OpaqueCall[] foreign={new OpaqueCall(0x4223F0CL,0x424DE78L,0x72000000L,in,n()),
                new OpaqueCall(0x4223EFBL,0x424DEECL,0x73000000L,in,n())};
        int[] calls={0},gs={0};
        Calls delegate=new Calls() {
            @Override public long readGsQword58() { gs[0]++;return 0xFEDCBA9876543210L; }
            @Override public VolatileBits invoke(OpaqueCall call) {
                equal(true,call==foreign[calls[0]++],"foreign call object identity");return post;
            }
        };
        Calls bound=GovernmentRegistryTable186Calls.bind(B,m,delegate);
        for (OpaqueCall call:foreign) equal(post,bound.invoke(call),"foreign fullV");
        equal(0xFEDCBA9876543210L,bound.readGsQword58(),"GS exact delegate result");
        equal(2,calls[0],"two foreign pairs delegated");
        equal(1,gs[0],"GS exact delegate count");
    }
    private static void missingOpaqueRejects() {
        MemoryImage m=new MemoryImage();
        UnsupportedOperationException missing=new UnsupportedOperationException("424DB38 owned poststate unavailable");
        Calls port=new Calls() {
            @Override public long readGsQword58() { throw new AssertionError("no GS"); }
            @Override public VolatileBits invoke(OpaqueCall call) { throw missing; }
        };
        try {
            GovernmentRegistryTable186.execute(new GovernmentCallee164Api.Entry(B,0x74000008L,
                    bits(0x7700,1,2,3),n()),m,port);
            throw new AssertionError("must not synthesize successful opaque result");
        } catch (UnsupportedOperationException actual) {
            equal(true,actual==missing,"missing opaque propagates identity");
        }
        equal(0x10424DF2EL,m.readQword(0x73FFFFB8L),"CALL was physically pushed before rejection");
    }
    public static int run() {
        assertions=0;
        directMutableFrame();actualEntry183Regular();exactForeignDelegation();missingOpaqueRejects();
        return assertions;
    }
}

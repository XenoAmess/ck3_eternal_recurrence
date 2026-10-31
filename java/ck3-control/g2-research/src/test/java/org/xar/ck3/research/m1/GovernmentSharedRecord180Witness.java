package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner literal book after two rejected model books; target never supplies expected values. */
public final class GovernmentSharedRecord180Witness {
    public static final long B=0x1_0000_0000L,S=0x7000_0008L,GS=0x6000_0000L,TLS=0x6000_1000L;
    public static final long GUARD=B+0x5D2E27CL,RECORD=B+0x5D2E280L,RET=0x1234_5678_7654_3210L;
    private GovernmentSharedRecord180Witness() { }

    /** Only qword-write observations required to detect an otherwise invisible duplicate CALL push. */
    public static final class OwnedMemory implements GovernmentSharedManager167Api.Memory {
        private final MemoryImage image=new MemoryImage();
        public final List<Long> qwordWrites=new ArrayList<>();
        @Override public int readUnsignedByte(long a){return image.readUnsignedByte(a);}
        @Override public int readDword(long a){return image.readDword(a);}
        @Override public long readQword(long a){return image.readQword(a);}
        @Override public Bits128 read128(long a){return image.read128(a);}
        @Override public void writeByte(long a,int v){image.writeByte(a,v);}
        @Override public void writeDword(long a,int v){image.writeDword(a,v);}
        @Override public void writeQword(long a,long v){qwordWrites.add(a);image.writeQword(a,v);}
        @Override public void write128(long a,Bits128 v){image.write128(a,v);}
        @Override public int lockedXaddDword(long a,int v){return image.lockedXaddDword(a,v);}
        @Override public int lockedXaddByte(long a,int v){return image.lockedXaddByte(a,v);}
    }
    public record Seed(OwnedMemory memory,GovernmentCallee164Api.Entry entry) { }
    public static Seed seed(int global,int thread) {
        OwnedMemory m=new OwnedMemory();
        m.writeQword(S,RET);m.writeQword(GS,TLS);m.writeDword(TLS+0x10,thread);
        m.writeDword(GUARD,global);m.writeDword(RECORD+4,0x44332211);m.writeDword(RECORD+0x34,0x88776655);
        NonvolatileBits n=new NonvolatileBits(0x1111222233334444L,0x5555666677778888L,
                0x1111333355557777L,0x2222444466668888L,0x3333555577779999L,
                0x444466668888AAAAL,0x555577779999BBBBL,0x66668888AAAACCCCL,vector(0x71717171));
        VolatileBits v=bits(0x1200,0x2200,0x3200,0x4200);
        m.qwordWrites.clear();return new Seed(m,new GovernmentCallee164Api.Entry(B,S,v,n));
    }
    /** Mechanical expected-record construction, with remaining fields from explicit input/post-port values. */
    public static VolatileBits fields(VolatileBits v,long rax,long rcx,long rdx) {
        return new VolatileBits(rax,rcx,rdx,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
                v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static void returned(Seed s,VolatileBits expected,CallScript calls) {
        GovernmentCallee164Api.NormalReturn actual=GovernmentSharedRecord180.execute(s.entry(),s.memory(),calls);
        equal(new GovernmentCallee164Api.NormalReturn(expected,s.entry().nonvolatileBits(),RET,S+8),actual,"whole raw93 result");
        equal(RET,s.memory().readQword(S),"original parent RET unchanged");calls.done(1);
    }
    private static void fast(int global,int thread) {
        Seed s=seed(global,thread);VolatileBits v=s.entry().volatileBits();
        returned(s,fields(v,RECORD,TLS,0x10),new CallScript(GS));
        equal(List.of(),s.memory().qwordWrites,"no child CALL on fast path");
        equal(0x44332211,s.memory().readDword(RECORD+4),"fast byte4 unchanged");
        equal(0x88776655,s.memory().readDword(RECORD+0x34),"fast byte34 unchanged");
    }
    private static void headerPublished() {
        Seed s=seed(100,1);OwnedMemory m=s.memory();VolatileBits in=s.entry().volatileBits();
        VolatileBits post=bits(0x2300,0x3300,0x4300,0x5300);
        CallScript calls=new CallScript(GS).expect(new OpaqueCall(0x2D888A3,0x4223A84,S-0x28,
                fields(in,1,GUARD,0x10),s.entry().nonvolatileBits()),post,()->{
            equal(B+0x2D888A8,m.readQword(S-0x30),"Header actual CALL push");m.writeDword(GUARD,7);
        });
        returned(s,fields(post,RECORD,post.rcxBits(),post.rdxBits()),calls);
        equal(List.of(S-0x30),m.qwordWrites,"one exact child push");
        equal(0x44332211,m.readDword(RECORD+4),"published Header skips initialization byte4");
        equal(0x88776655,m.readDword(RECORD+0x34),"published Header skips initialization byte34");
    }
    private static void initialization() {
        Seed s=seed(100,1);OwnedMemory m=s.memory();VolatileBits in=s.entry().volatileBits();
        VolatileBits h=bits(0x2400,0x3400,0x4400,0x5400),f=bits(0x3500,0x4500,0x5500,0x6500);
        CallScript calls=new CallScript(GS).expect(new OpaqueCall(0x2D888A3,0x4223A84,S-0x28,
                fields(in,1,GUARD,0x10),s.entry().nonvolatileBits()),h,()->{
            equal(B+0x2D888A8,m.readQword(S-0x30),"Header physical return before invoke");
            equal(0x44332211,m.readDword(RECORD+4),"before Header byte4");
            equal(0x88776655,m.readDword(RECORD+0x34),"before Header byte34");m.writeDword(GUARD,-1);
        }).expect(new OpaqueCall(0x2D888C6,0x4223A24,S-0x28,
                fields(h,h.raxBits(),GUARD,h.rdxBits()),s.entry().nonvolatileBits()),f,()->{
            equal(B+0x2D888CB,m.readQword(S-0x30),"Footer overwrote same CALL return slot");
            equal(0x44332200,m.readDword(RECORD+4),"only low BYTE4 written before Footer");
            equal(0x887766FF,m.readDword(RECORD+0x34),"only low BYTE34 written before Footer");
        });
        returned(s,fields(f,RECORD,f.rcxBits(),f.rdxBits()),calls);
        equal(List.of(S-0x30,S-0x30),m.qwordWrites,"two exact source CALL pushes");
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");
        fast(7,7);fast(Integer.MIN_VALUE,1);headerPublished();initialization();
        System.out.println("GovernmentSharedRecord180Witness:4 new raw93 literal cases");
    }
}

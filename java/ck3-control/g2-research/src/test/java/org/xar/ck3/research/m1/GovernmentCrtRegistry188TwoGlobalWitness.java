package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtCallee186;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import static org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
import static org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner literals frozen from held58B/15B/72B before bridge implementation.
 * Newcallee implementation was not supplied to this oracle; no run-derived expected values.
 * DB38 effects are owned full-state software ports, not actual OS/library behavior. */
public final class GovernmentCrtRegistry188TwoGlobalWitness {
    private GovernmentCrtRegistry188TwoGlobalWitness() { }
    private static final long B=0x1_0000_0000L,P=0x7000_0038L,RET=0x1234_5678_7654_3210L;
    private static final long G=0x1_05C5_CB68L,H=0x1_05C5_D698L,C=0x7000_0008L;
    private static int checks;
    private static void eq(Object expected,Object actual,String message){checks++;equal(expected,actual,message);}
    private static NonvolatileBits nonvolatile(long s) {
        return new NonvolatileBits(s,s+1,s+2,s+3,s+4,s+5,s+6,s+7,vector(s+8));
    }
    private static VolatileBits fields(VolatileBits v,long a,long c,long d,long r8,long r9) {
        return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits frameN(NonvolatileBits n,long bx,long bp) {
        return new NonvolatileBits(bx,bp,n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    /** Existing byte storage with only the actual185.Memory interface, not a stronger fabricated capability. */
    private static final class BaseMemory implements GovernmentCrtBoundary185Api.Memory {
        final MemoryImage image=new MemoryImage();int childWrites,earlyChildReads;boolean enteredDb38;
        @Override public int readDword(long a){return image.readDword(a);}
        @Override public long readQword(long a){if(a==C&&!enteredDb38)earlyChildReads++;return image.readQword(a);}
        @Override public int readUnsignedByte(long a){return image.readUnsignedByte(a);}
        @Override public void writeDword(long a,int v){image.writeDword(a,v);}
        @Override public int lockedXaddDword(long a,int v){return image.lockedXaddDword(a,v);}
        @Override public void writeQword(long a,long v){if(a==C)childWrites++;image.writeQword(a,v);}
        @Override public void writeByte(long a,int v){image.writeByte(a,v);}
        @Override public Bits128 read128(long a){return image.read128(a);}
        @Override public void write128(long a,Bits128 v){image.write128(a,v);}
    }
    private static void runCase(int id,long initialG,long initialH,long selected,long callback,
            long childReturn,long postRax,long finalRax,long marker) {
        BaseMemory m=new BaseMemory();
        eq(false,GovernmentSharedManager167Api.Memory.class.isInstance(m),"real input is base-only185.Memory");
        m.image.writeQword(P,RET);m.image.writeQword(G,initialG);m.image.writeQword(H,initialH);
        m.image.writeQword(0x7000_0028L,0xAABB_CCDD_1122_3344L);
        m.image.writeQword(0x6FFF_FFE0L,0x9988_7766_5544_3322L);
        VolatileBits incoming=bits(0x1100+id*0x100L,0xA110+id,callback,0xD110+id);
        VolatileBits post=bits(0xE100+id*0x100L,postRax,0xE001+id,0xF001+id);
        NonvolatileBits n=nonvolatile(0x3111_2222_3333_4400L+id*0x100L);
        VolatileBits dbV=fields(incoming,0x2,0x7000_0020L,0x6FFF_FFE0L,0x6FFF_FFE8L,0x7000_0028L);
        Call expected=new Call(0x424DF29L,DIRECT_RVA,0x424DB38L,0x6FFF_FFC0L,dbV,frameN(n,callback,0x7000_0000L));
        int[] invocations={0};
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                eq(0,invocations[0]++,"one actual unresolvedDB38 call");
                eq(expected,call,"full directDB38 frame after concrete source bodies");
                eq(0,m.earlyChildReads,"bridge made no return-slot qualification read");
                m.enteredDb38=true;
                eq(1,m.childWrites,"actualM4CALL pushed once, bridge did not push again");
                eq(childReturn,m.image.readQword(C),"actualcaller child continuation");
                eq(selected,m.image.readQword(0x7000_0010L),"distinct actualtable pointer home");
                eq(callback,m.image.readQword(0x7000_0018L),"originalcallback home");
                eq(0x7000_0010L,m.image.readQword(0x6FFF_FFE8L),"first pointerpair slot");
                eq(0x7000_0018L,m.image.readQword(0x6FFF_FFF0L),"second pointerpair slot");
                eq(0xAABB_CCDD_0000_0002L,m.image.readQword(0x7000_0028L),"rightDWORDstore preserves padding");
                eq(0x9988_7766_0000_0002L,m.image.readQword(0x6FFF_FFE0L),"leftDWORDstore preserves padding");
                eq(B+0x424DF2EL,m.image.readQword(0x6FFF_FFB8L),"sourceDB38CALL physical return");
                eq(n.rbpBits(),m.image.readQword(0x7000_0000L),"source savedRBP");
                eq(n.rbxBits(),m.image.readQword(0x7000_0030L),"actualM4 savedRBX");
                eq(initialG,m.image.readQword(G),"G before ownedport effect");
                eq(initialH,m.image.readQword(H),"H before ownedport effect");
                m.writeQword(selected,marker);
                return post;
            }
            @Override public NormalReturn tail(Tail transfer){throw new AssertionError("unexpected tail "+transfer);}
            @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
        };
        Calls bound=GovernmentCrtRegistry188Bridge.bind(B,m,fallback);
        NormalReturn actual=GovernmentCrtCallee186.execute(new Entry(B,P,incoming,n),m,bound);
        VolatileBits finalV=fields(post,finalRax,post.rcxBits(),finalRax,post.r8Bits(),post.r9Bits());
        eq(new NormalReturn(finalV,RET,0x7000_0040L,n),actual,"complete actualnewcallee normal return");
        eq(1,invocations[0],"actualtarget call count");eq(1,m.childWrites,"no extra bridge push through return");
        eq(marker,m.image.readQword(selected),"fallback writes visible through sameMemory");
        eq(selected==G?initialH:initialG,m.image.readQword(selected==G?H:G),"otherglobal unaffected");
        eq(RET,m.image.readQword(P),"originalparentRET retained");
    }
    private static void foreignPorts() {
        BaseMemory m=new BaseMemory();VolatileBits v=bits(0x5100,0x6111,0x6222,0x6333);
        NonvolatileBits n=nonvolatile(0x7333_4444_5555_6600L);
        Call[] seen={null};Tail[] seenTail={null};int[] calls={0},tails={0},gs={0};
        NormalReturn tailReply=new NormalReturn(v,0xABCDL,0x7000_0090L,n);
        Calls fallback=new Calls() {
            @Override public VolatileBits invoke(Call c){calls[0]++;seen[0]=c;return v;}
            @Override public NormalReturn tail(Tail t){tails[0]++;seenTail[0]=t;return tailReply;}
            @Override public long readGsQword58(){gs[0]++;return 0x1234_5678_9ABCL;}
        };
        Calls bridge=GovernmentCrtRegistry188Bridge.bind(B,m,fallback);
        Call[] foreign={new Call(0x4223EFDL,DIRECT_RVA,0x424DE78L,0x7000_0010L,v,n),
            new Call(0x4223EFBL,INDIRECT_ABSOLUTE,0x424DE78L,0x7000_0010L,v,n),
            new Call(0x4223EFBL,DIRECT_RVA,0x424DEECL,0x7000_0010L,v,n)};
        for(Call c:foreign){eq(true,bridge.invoke(c)==v,"foreign fullV returned unchanged");eq(true,seen[0]==c,"foreignCall object forwarded unchanged");}
        Tail transfer=new Tail(0x4223EFBL,DIRECT_RVA,0x424DE78L,new Entry(B,P,v,n));
        eq(true,bridge.tail(transfer)==tailReply,"tail result exact forward");eq(true,seenTail[0]==transfer,"tail object exact forward");
        eq(0x1234_5678_9ABCL,bridge.readGsQword58(),"GS exact forward");
        eq(3,calls[0],"foreign invoke count");eq(1,tails[0],"foreign tail count");eq(1,gs[0],"foreignGS count");
        eq(0,m.childWrites,"unhandledports made no push");eq(0,m.earlyChildReads,"unhandledports made no read");
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");checks=0;
        runCase(1,-1L,0x1122_3344_5566_7788L,H,0x2233_4455_6677_8899L,
                0x1_0422_3F00L,0xABCD_EF00_0000_0000L,0x2233_4455_6677_8899L,0x3344_5566_7788_99AAL);
        runCase(2,0x5566_7788_99AA_BBCCL,-1L,G,0x8877_6655_4433_2211L,
                0x1_0422_3F11L,0x8000_0001L,0,0x4455_6677_8899_AABBL);
        foreignPorts();
        System.out.println("{\"actual_new_callee_two_global_cases\":2,\"foreign_invoke_cases\":3,\"tail_GS_forward\":true,\"counted_assertions\":"+checks+",\"Native_or_Game\":0}");
    }
}

package org.xar.ck3.research.m1;

import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner literals from held59B/72B and pre-candidate INPUTS194; both model books rejected.
 * Raw software normal ports only. Actual UHANDLER/EH and all three callees remain unqualified. */
public final class GovernmentRegistryDispatch194Witness {
    private GovernmentRegistryDispatch194Witness() { }
    private static final long B=0x1_0000_0000L;
    private static int checks;
    private static void eq(Object expected,Object actual,String label){checks++;equal(expected,actual,label);}
    private static final NonvolatileBits N=new NonvolatileBits(0x1111_2222_3333_4444L,
        0x2222_3333_4444_5555L,0x3333_4444_5555_6666L,0x4444_5555_6666_7777L,
        0x5555_6666_7777_8888L,0x6666_7777_8888_9999L,0x7777_8888_9999_AAAAL,
        0x8888_9999_AAAA_BBBBL,vector(0x5555_1111_2222_3333L));
    private static NonvolatileBits frame(long bx,long bp,long di){
        return new NonvolatileBits(bx,bp,N.rsiBits(),di,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }
    private static VolatileBits v(long seed,long a,long c,long d,long r8,long r9,long r10,long r11){
        return new VolatileBits(a,c,d,r8,r9,r10,r11,vector(seed+0x10),vector(seed+0x20),
            vector(seed+0x30),vector(seed+0x40),vector(seed+0x50),vector(seed+0x60));
    }
    private static VolatileBits change(VolatileBits v,long a,long c){
        return new VolatileBits(a,c,v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),
            v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits post(int id,long a){
        long h=id==1?0x1111_1111_0000_0000L:id==2?0x2222_2222_0000_0000L:0x3333_3333_0000_0000L;
        return v(id*0x100L+0x100,a,h+2,h+3,h+4,h+5,h+6,h+7);
    }
    private static final class Memory implements GovernmentSharedManager167Api.Memory {
        final MemoryImage image=new MemoryImage();
        int childWrites,earlyChildReads;boolean enteredFirst;
        @Override public int readDword(long a){return image.readDword(a);}
        @Override public long readQword(long a){if(a==0x8FFF_FFB8L&&!enteredFirst)earlyChildReads++;return image.readQword(a);}
        @Override public int readUnsignedByte(long a){return image.readUnsignedByte(a);}
        @Override public void writeDword(long a,int b){image.writeDword(a,b);}
        @Override public int lockedXaddDword(long a,int b){return image.lockedXaddDword(a,b);}
        @Override public void writeQword(long a,long b){if(a==0x8FFF_FFB8L)childWrites++;image.writeQword(a,b);}
        @Override public void writeByte(long a,int b){image.writeByte(a,b);}
        @Override public Bits128 read128(long a){return image.read128(a);}
        @Override public void write128(long a,Bits128 b){image.write128(a,b);}
        @Override public int lockedXaddByte(long a,int b){return image.lockedXaddByte(a,b);}
    }
    private static final class Script implements Calls {
        final Memory m;final OpaqueCall[] expected;final VolatileBits[] replies;
        final long[] pushed;final long mutationAddress;final int mutationValue;final boolean composed;
        int index,gs;
        Script(Memory m,OpaqueCall[] expected,VolatileBits[] replies,long[] pushed,
                long mutationAddress,int mutationValue,boolean composed){
            this.m=m;this.expected=expected;this.replies=replies;this.pushed=pushed;
            this.mutationAddress=mutationAddress;this.mutationValue=mutationValue;this.composed=composed;
        }
        @Override public long readGsQword58(){gs++;throw new AssertionError("unexpected GS");}
        @Override public VolatileBits invoke(OpaqueCall actual){
            if(index>=3)throw new AssertionError("unexpected fourth call "+actual);
            int i=index++;eq(expected[i],actual,"full original threecallee frame "+i);
            eq(pushed[i],m.image.readQword(actual.rspBits()-8),"actual physical CALL return "+i);
            if(composed&&i==0){
                eq(1,m.childWrites,"Table pushed child once; adapter did not duplicate push");
                eq(0,m.earlyChildReads,"adapter did not qualify by prereading childRET");
                eq(0x1_0424_DF2EL,m.image.readQword(0x8FFF_FFB8L),"realTable child continuation");
                m.enteredFirst=true;
            }
            if(i==1)m.writeDword(mutationAddress,mutationValue);
            return replies[i];
        }
        void done(){eq(3,index,"three actual opaque normalcalls");eq(0,gs,"no GS");}
    }
    private static OpaqueCall call(long site,long target,long sp,VolatileBits v,NonvolatileBits n){
        return new OpaqueCall(site,target,sp,v,n);
    }
    private static final long[] PUSHED={0x1_0424_DB54L,0x1_0424_DB5DL,0x1_0424_DB66L};
    private static void direct(){
        Memory m=new Memory();m.image.writeQword(0x8000_0008L,0x1234_5678_7654_3210L);
        m.image.writeDword(0x6000_2000L,0xF1234567);m.image.writeDword(0x6000_4000L,0x10203040);
        VolatileBits in=v(0x100,0xAAAA_0000_1111_2222L,0xBBBB_0000_3333_4444L,
            0x6000_2000L,0x6000_3000L,0x6000_4000L,0xAAAA_5555_6666_7777L,0xBBBB_6666_7777_8888L);
        VolatileBits p1=post(1,0x1111_1111_0000_0001L),p2=post(2,0xFEDC_BA98_8000_0001L),p3=post(3,0x1234_5678_9ABC_DEF0L);
        NonvolatileBits n1=frame(0x6000_4000L,N.rbpBits(),0x6000_3000L),n3=frame(0x6000_4000L,N.rbpBits(),0x8000_0001L);
        OpaqueCall[] expected={
            call(0x424DB4FL,0x4247FFCL,0x7FFF_FFE0L,change(in,in.raxBits(),0xF123_4567L),n1),
            call(0x424DB58L,0x424DBB0L,0x7FFF_FFE0L,change(p1,p1.raxBits(),0x6000_3000L),n1),
            call(0x424DB61L,0x4248050L,0x7FFF_FFE0L,change(p2,p2.raxBits(),0x89AB_CDEFL),n3)};
        Script script=new Script(m,expected,new VolatileBits[]{p1,p2,p3},PUSHED,0x6000_4000L,0x89ABCDEF,false);
        NormalReturn actual=GovernmentRegistryDispatch194.execute(new Entry(B,0x8000_0008L,in,N),m,script);script.done();
        eq(new NormalReturn(change(p3,0x8000_0001L,p3.rcxBits()),N,0x1234_5678_7654_3210L,0x8000_0010L),actual,"full directnormalresult");
        eq(N.rbxBits(),m.image.readQword(0x8000_0010L),"savedRBX originalhome");
        eq(0x6000_4000L,m.image.readQword(0x8000_0028L),"saved originalR9home");
        eq(N.rdiBits(),m.image.readQword(0x8000_0000L),"savedRDI actualpush");
        eq(0x1_0424_DB66L,m.image.readQword(0x7FFF_FFD8L),"thirdcalllast physicalpush");
        eq(0x89ABCDEF,m.image.readDword(0x6000_4000L),"post2mutation stillpresent");
        eq(0x1234_5678_7654_3210L,m.image.readQword(0x8000_0008L),"actual RET reads originalword");
    }
    private static void table(){
        Memory m=new Memory();m.image.writeQword(0x9000_0008L,0x2233_4455_6677_8899L);
        VolatileBits in=v(0x100,0xAAAA_0000_1111_2222L,0x5000_1000L,0x4444_5555_6666_7777L,
            0xBBBB_CCCC_DDDD_EEEEL,0xCCCC_DDDD_EEEE_FFFFL,0xAAAA_5555_6666_7777L,0xBBBB_6666_7777_8888L);
        VolatileBits p1=post(1,0x1111_1111_0000_0001L),p2=post(2,0xDEAD_BEEF_0000_0000L),p3=post(3,0x1234_5678_9ABC_DEF0L);
        VolatileBits first=v(0x100,2,2,0x8FFF_FFE0L,0x8FFF_FFE8L,0x9000_0028L,0xAAAA_5555_6666_7777L,0xBBBB_6666_7777_8888L);
        NonvolatileBits n1=frame(0x9000_0028L,0x9000_0000L,0x8FFF_FFE8L),n3=frame(0x9000_0028L,0x9000_0000L,0);
        OpaqueCall[] expected={
            call(0x424DB4FL,0x4247FFCL,0x8FFF_FF90L,first,n1),
            call(0x424DB58L,0x424DBB0L,0x8FFF_FF90L,change(p1,p1.raxBits(),0x8FFF_FFE8L),n1),
            call(0x424DB61L,0x4248050L,0x8FFF_FF90L,change(p2,p2.raxBits(),0xAABB_CCDDL),n3)};
        Script script=new Script(m,expected,new VolatileBits[]{p1,p2,p3},PUSHED,0x9000_0028L,0xAABBCCDD,true);
        NormalReturn actual=GovernmentRegistryTable186.execute(new Entry(B,0x9000_0008L,in,N),m,
            GovernmentRegistryDispatch194Calls.bind(B,m,script));script.done();
        eq(new NormalReturn(change(p3,0,p3.rcxBits()),N,0x2233_4455_6677_8899L,0x9000_0010L),actual,"full actualTable→194 result");
        eq(1,m.childWrites,"still one childphysicalpush");
        eq(N.rbxBits(),m.image.readQword(0x8FFF_FFC0L),"childRBXsave");
        eq(0x9000_0028L,m.image.readQword(0x8FFF_FFD8L),"childR9home");
        eq(N.rdiBits(),m.image.readQword(0x8FFF_FFB0L),"childRDIpush");
        eq(0x1_0424_DB66L,m.image.readQword(0x8FFF_FF88L),"thirdcallreturn");
        eq(N.rbpBits(),m.image.readQword(0x9000_0000L),"outerTableRBPsave");
        eq(0x5000_1000L,m.image.readQword(0x9000_0010L),"outerTablefirsthome");
        eq(0x4444_5555_6666_7777L,m.image.readQword(0x9000_0018L),"outerTablesecondhome");
        eq(0x9000_0010L,m.image.readQword(0x8FFF_FFE8L),"actualpointerpairfirst");
        eq(0x9000_0018L,m.image.readQword(0x8FFF_FFF0L),"actualpointerpairsecond");
        eq(2,m.image.readDword(0x8FFF_FFE0L),"outerinitialleftcount");
        eq(0xAABBCCDD,m.image.readDword(0x9000_0028L),"callbacksharedmutation");
        eq(0x1_0424_DF2EL,m.image.readQword(0x8FFF_FFB8L),"preservedTablechildRET");
    }
    private static void foreign(){
        Memory m=new Memory();VolatileBits reply=post(3,0xFEDCBA9876543210L);OpaqueCall[] seen={null};int[] count={0},gs={0};
        Calls fallback=new Calls(){
            @Override public long readGsQword58(){gs[0]++;return 0x1234_5678_9ABCL;}
            @Override public VolatileBits invoke(OpaqueCall call){seen[0]=call;count[0]++;return reply;}
        };
        Calls bound=GovernmentRegistryDispatch194Calls.bind(B,m,fallback);
        OpaqueCall[] calls={call(0x424DF28L,0x424DB38L,0x7000_0000L,reply,N),call(0x424DF29L,0x424DB39L,0x7000_0000L,reply,N)};
        for(OpaqueCall c:calls){eq(true,bound.invoke(c)==reply,"foreign resultidentity");eq(true,seen[0]==c,"foreign originalcallidentity");}
        eq(0x1234_5678_9ABCL,bound.readGsQword58(),"GSforward");eq(1,gs[0],"oneGS");eq(2,count[0],"twoforeign");
        eq(0,m.childWrites,"foreignnopush");eq(0,m.earlyChildReads,"foreignnopreRead");
    }
    public static void main(String[] args){
        if(args.length!=0)throw new IllegalArgumentException("no args");checks=0;direct();table();foreign();
        System.out.println("{\"new_normal_scenes\":2,\"actual_Table_to_194\":1,\"foreign_calls\":2,\"counted_assertions\":"+checks+",\"Native_or_Game\":0}");
    }
}

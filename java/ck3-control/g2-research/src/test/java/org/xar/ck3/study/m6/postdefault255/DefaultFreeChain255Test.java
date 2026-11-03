package org.xar.ck3.study.m6.postdefault255;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.postforward250.Known715PostForward250;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/** One actual715 deep Normal. Full constants project the independent frozen pre-255 literal. */
public final class DefaultFreeChain255Test {
    private static final long IMAGE=0x140000000L,S=0x300008L,P=S-0x478,E=P-8,F=E-0x28,G=F-8,H=G-0x28,J=H-8;
    private static final long DEST=0x2000,SOURCE=0x3000,DATA=0x5000,NEW=0x6000,OLD=0x7000;
    private static final long OBJECT=0x8000,TABLE=0x9000,PROVIDER=0xa000,PROVIDER_TABLE=0xb000,SOURCE_ALLOC=0xc000,HEAP=0xd000,CELL=0xe000;
    private static final long RET=0x7fff0000feed0255L,ORIGIN=0x700255L;
    private static final Bits128 PAYLOAD1=new Bits128(0x0123456789abcdefL,0xfedcba9876543210L);
    private static final Bits128 PAYLOAD2=new Bits128(0x1122334455667788L,0x8877665544332211L);
    private static final QueueFp604Api.Mxcsr PRE=QueueFp604Api.Mxcsr.exact(0x1f80);
    private static final QueueFp604Api.Mxcsr[] ENV={QueueFp604Api.Mxcsr.exact(0x1f81),QueueFp604Api.Mxcsr.exact(0x1f82),
            new QueueFp604Api.Mxcsr(0x5f84,0xffc4),new QueueFp604Api.Mxcsr(0x9f81,0xffc1),new QueueFp604Api.Mxcsr(0x9fa5,0xffe5)};
    private static final boolean[] DF={false,true,false,true,true};
    private static final long[] SITES={0x424e37aL,0x424e384L,0x424e38cL,0x424e394L};
    private static final int[] LENGTHS={6,5,6,5};
    private static final long[] TARGETS={IMAGE+0xf50100L,0x423b18cL,IMAGE+0xf50300L,0x423b0d4L};
    private static int checks;
    private DefaultFreeChain255Test() { }
    private static final VolatileBits INPUT_V=new VolatileBits(0x1111L,0x2000L,0x3000L,0x1234000000000004L,0x1234000000000005L,0x1234000000000006L,0x1234000000000007L,new Bits128(0x1234000000000000L,0xedcbffffffffffffL),new Bits128(0x1234000000000002L,0xedcbfffffffffffdL),new Bits128(0x1234000000000004L,0xedcbfffffffffffbL),new Bits128(0x1234000000000006L,0xedcbfffffffffff9L),new Bits128(0x1234000000000008L,0xedcbfffffffffff7L),new Bits128(0x123400000000000aL,0xedcbfffffffffff5L));
    private static final NonvolatileBits INPUT_N=new NonvolatileBits(0x1111111111111111L,0x2222222222222222L,0x3333333333333333L,0x4444444444444444L,0x5555555555555555L,0x6666666666666666L,0x7777777777777777L,0x8888888888888888L,new Bits128(0x8967896789678973L,0x769876987698768cL));
    private static final VolatileBits ENTRY18_V=new VolatileBits(0xa000L,0xa000L,0x20L,0x8L,0x1408571d0L,0x1234000000000006L,0x1234000000000007L,new Bits128(0x3fc00000L,0x0L),new Bits128(0x1234000000000002L,0xedcbfffffffffffdL),new Bits128(0x1234000000000004L,0xedcbfffffffffffbL),new Bits128(0x1234000000000006L,0xedcbfffffffffff9L),new Bits128(0x1234000000000008L,0xedcbfffffffffff7L),new Bits128(0x123400000000000aL,0xedcbfffffffffff5L));
    private static final NonvolatileBits ALLOC_N=new NonvolatileBits(0x5000L,0x0L,0x2000L,0x5020L,0x5555555555555555L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL));
    private static final VolatileBits B94_PRE_V=new VolatileBits(0xa000L,0x20L,0x20L,0x8L,0x1408571d0L,0x1234000000000006L,0x1234000000000007L,new Bits128(0x3fc00000L,0x0L),new Bits128(0x1234000000000002L,0xedcbfffffffffffdL),new Bits128(0x1234000000000004L,0xedcbfffffffffffbL),new Bits128(0x1234000000000006L,0xedcbfffffffffff9L),new Bits128(0x1234000000000008L,0xedcbfffffffffff7L),new Bits128(0x123400000000000aL,0xedcbfffffffffff5L));
    private static final VolatileBits ALLOC_V=new VolatileBits(0x6000L,0xa110000000000002L,0xa110000000000003L,0xa110000000000004L,0xa110000000000005L,0xa110000000000006L,0xa110000000000007L,new Bits128(0xa110000000000000L,0x5eefffffffffffffL),new Bits128(0xa110000000000002L,0x5eeffffffffffffdL),new Bits128(0xa110000000000004L,0x5eeffffffffffffbL),new Bits128(0xa110000000000006L,0x5eeffffffffffff9L),new Bits128(0xa110000000000008L,0x5eeffffffffffff7L),new Bits128(0xa11000000000000aL,0x5eeffffffffffff5L));
    private static final VolatileBits ENTRY14_V=new VolatileBits(0xa000L,0xa000L,0x7000L,0x8L,0xb000L,0xa110000000000006L,0xa110000000000007L,new Bits128(0x1122334455667788L,0x8877665544332211L),new Bits128(0xa110000000000002L,0x5eeffffffffffffdL),new Bits128(0xa110000000000004L,0x5eeffffffffffffbL),new Bits128(0xa110000000000006L,0x5eeffffffffffff9L),new Bits128(0xa110000000000008L,0x5eeffffffffffff7L),new Bits128(0xa11000000000000aL,0x5eeffffffffffff5L));
    private static final NonvolatileBits ENTRY14_N=new NonvolatileBits(0x7000L,0x0L,0x2000L,0x8L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL));
    private static final VolatileBits TAIL14_V=new VolatileBits(0xa000L,0x7000L,0x7000L,0x8L,0xb000L,0xa110000000000006L,0xa110000000000007L,new Bits128(0x1122334455667788L,0x8877665544332211L),new Bits128(0xa110000000000002L,0x5eeffffffffffffdL),new Bits128(0xa110000000000004L,0x5eeffffffffffffbL),new Bits128(0xa110000000000006L,0x5eeffffffffffff9L),new Bits128(0xa110000000000008L,0x5eeffffffffffff7L),new Bits128(0xa11000000000000aL,0x5eeffffffffffff5L));
    private static final VolatileBits FINAL251_V=new VolatileBits(0xcafe000076543210L,0xf454000000000002L,0xf454000000000003L,0xf454000000000004L,0xf454000000000005L,0xf454000000000006L,0xf454000000000007L,new Bits128(0xf454000000000000L,0xbabffffffffffffL),new Bits128(0xf454000000000002L,0xbabfffffffffffdL),new Bits128(0xf454000000000004L,0xbabfffffffffffbL),new Bits128(0xf454000000000006L,0xbabfffffffffff9L),new Bits128(0xf454000000000008L,0xbabfffffffffff7L),new Bits128(0xf45400000000000aL,0xbabfffffffffff5L));
    private static final NonvolatileBits FINAL58_N=new NonvolatileBits(0x5020L,0x0L,0x2000L,0x5020L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL));
    private static final VolatileBits FINAL715_V=new VolatileBits(0x2000L,0xf454000000000002L,0xf454000000000003L,0xf454000000000004L,0xf454000000000005L,0xf454000000000006L,0x2fffe0L,new Bits128(0xf454000000000000L,0xbabffffffffffffL),new Bits128(0xf454000000000002L,0xbabfffffffffffdL),new Bits128(0xf454000000000004L,0xbabfffffffffffbL),new Bits128(0xf454000000000006L,0xbabfffffffffff9L),new Bits128(0xf454000000000008L,0xbabfffffffffff7L),new Bits128(0xf45400000000000aL,0xbabfffffffffff5L));
    private static final VolatileBits[] LOWER_PRE_V={
        new VolatileBits(0x0L,0xd000L,0x0L,0x7000L,0xb000L,0xa110000000000006L,0xa110000000000007L,new Bits128(0x1122334455667788L,0x8877665544332211L),new Bits128(0xa110000000000002L,0x5eeffffffffffffdL),new Bits128(0xa110000000000004L,0x5eeffffffffffffbL),new Bits128(0xa110000000000006L,0x5eeffffffffffff9L),new Bits128(0xa110000000000008L,0x5eeffffffffffff7L),new Bits128(0xa11000000000000aL,0x5eeffffffffffff5L)),
        new VolatileBits(0xc001000000000000L,0xf151000000000002L,0xf151000000000003L,0xf151000000000004L,0xf151000000000005L,0xf151000000000006L,0xf151000000000007L,new Bits128(0xf151000000000000L,0xeaeffffffffffffL),new Bits128(0xf151000000000002L,0xeaefffffffffffdL),new Bits128(0xf151000000000004L,0xeaefffffffffffbL),new Bits128(0xf151000000000006L,0xeaefffffffffff9L),new Bits128(0xf151000000000008L,0xeaefffffffffff7L),new Bits128(0xf15100000000000aL,0xeaefffffffffff5L)),
        new VolatileBits(0xe000L,0xf252000000000002L,0xf252000000000003L,0xf252000000000004L,0xf252000000000005L,0xf252000000000006L,0xf252000000000007L,new Bits128(0xf252000000000000L,0xdadffffffffffffL),new Bits128(0xf252000000000002L,0xdadfffffffffffdL),new Bits128(0xf252000000000004L,0xdadfffffffffffbL),new Bits128(0xf252000000000006L,0xdadfffffffffff9L),new Bits128(0xf252000000000008L,0xdadfffffffffff7L),new Bits128(0xf25200000000000aL,0xdadfffffffffff5L)),
        new VolatileBits(0xfee1000089abcdefL,0x89abcdefL,0xf353000000000003L,0xf353000000000004L,0xf353000000000005L,0xf353000000000006L,0xf353000000000007L,new Bits128(0xf353000000000000L,0xcacffffffffffffL),new Bits128(0xf353000000000002L,0xcacfffffffffffdL),new Bits128(0xf353000000000004L,0xcacfffffffffffbL),new Bits128(0xf353000000000006L,0xcacfffffffffff9L),new Bits128(0xf353000000000008L,0xcacfffffffffff7L),new Bits128(0xf35300000000000aL,0xcacfffffffffff5L))};
    private static final NonvolatileBits[] LOWER_PRE_N={
        new NonvolatileBits(0x7000L,0x0L,0x2000L,0x8L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL)),
        new NonvolatileBits(0x7000L,0x0L,0x2000L,0x8L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL)),
        new NonvolatileBits(0xe000L,0x0L,0x2000L,0x8L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL)),
        new NonvolatileBits(0xe000L,0x0L,0x2000L,0x8L,0x6000L,0x2L,0x3000L,0x2L,new Bits128(0x8967896789678973L,0x769876987698768cL))};
    private static final VolatileBits[] LOWER_POST_V={
        new VolatileBits(0xc001000000000000L,0xf151000000000002L,0xf151000000000003L,0xf151000000000004L,0xf151000000000005L,0xf151000000000006L,0xf151000000000007L,new Bits128(0xf151000000000000L,0xeaeffffffffffffL),new Bits128(0xf151000000000002L,0xeaefffffffffffdL),new Bits128(0xf151000000000004L,0xeaefffffffffffbL),new Bits128(0xf151000000000006L,0xeaefffffffffff9L),new Bits128(0xf151000000000008L,0xeaefffffffffff7L),new Bits128(0xf15100000000000aL,0xeaefffffffffff5L)),
        new VolatileBits(0xe000L,0xf252000000000002L,0xf252000000000003L,0xf252000000000004L,0xf252000000000005L,0xf252000000000006L,0xf252000000000007L,new Bits128(0xf252000000000000L,0xdadffffffffffffL),new Bits128(0xf252000000000002L,0xdadfffffffffffdL),new Bits128(0xf252000000000004L,0xdadfffffffffffbL),new Bits128(0xf252000000000006L,0xdadfffffffffff9L),new Bits128(0xf252000000000008L,0xdadfffffffffff7L),new Bits128(0xf25200000000000aL,0xdadfffffffffff5L)),
        new VolatileBits(0xfee1000089abcdefL,0xf353000000000002L,0xf353000000000003L,0xf353000000000004L,0xf353000000000005L,0xf353000000000006L,0xf353000000000007L,new Bits128(0xf353000000000000L,0xcacffffffffffffL),new Bits128(0xf353000000000002L,0xcacfffffffffffdL),new Bits128(0xf353000000000004L,0xcacfffffffffffbL),new Bits128(0xf353000000000006L,0xcacfffffffffff9L),new Bits128(0xf353000000000008L,0xcacfffffffffff7L),new Bits128(0xf35300000000000aL,0xcacfffffffffff5L)),
        new VolatileBits(0xcafe000076543210L,0xf454000000000002L,0xf454000000000003L,0xf454000000000004L,0xf454000000000005L,0xf454000000000006L,0xf454000000000007L,new Bits128(0xf454000000000000L,0xbabffffffffffffL),new Bits128(0xf454000000000002L,0xbabfffffffffffdL),new Bits128(0xf454000000000004L,0xbabfffffffffffbL),new Bits128(0xf454000000000006L,0xbabfffffffffff9L),new Bits128(0xf454000000000008L,0xbabfffffffffff7L),new Bits128(0xf45400000000000aL,0xbabfffffffffff5L))};
    private record Access(String kind,long address,long low,long high) { }
    private record Budget(long site,long cursor,long end) { }

    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        final Map<Long,Integer> data=new HashMap<>();
        final List<Access> accesses=new ArrayList<>();
        void fill(long address,int length,int value){for(int i=0;i<length;i++)data.put(address+i,value&255);}
        int byteAt(long address){
            Integer value=data.get(address);
            if(value==null)throw new AssertionError("unprovided RAM "+Long.toHexString(address));
            return value;
        }
        long load(long address,int length){long value=0;for(int i=0;i<length;i++)value|=(long)byteAt(address+i)<<(8*i);return value;}
        void store(long address,long value,int length){for(int i=0;i<length;i++){byteAt(address+i);data.put(address+i,(int)(value>>>(8*i))&255);}}
        long peek(long address){return load(address,8);}
        int peekDword(long address){return(int)load(address,4);}
        Bits128 peek128(long address){return new Bits128(load(address,8),load(address+8,8));}
        long count(String kind,long address,long low){return accesses.stream().filter(a->a.kind().equals(kind)&&a.address()==address&&a.low()==low).count();}
        @Override public long readQword(long address){long value=load(address,8);accesses.add(new Access("r64",address,value,0));return value;}
        @Override public int readDword(long address){int value=(int)load(address,4);accesses.add(new Access("r32",address,value,0));return value;}
        @Override public int readUnsignedByte(long address){int value=byteAt(address);accesses.add(new Access("r8",address,value,0));return value;}
        @Override public void writeQword(long address,long value){store(address,value,8);accesses.add(new Access("w64",address,value,0));}
        @Override public void writeDword(long address,int value){store(address,value,4);accesses.add(new Access("w32",address,value,0));}
        @Override public void writeByte(long address,int value){store(address,value,1);accesses.add(new Access("w8",address,value&255,0));}
        @Override public int lockedXaddDword(long address,int value){throw new AssertionError("unexpected XADD");}
        @Override public Bits128 read128(long address){var value=peek128(address);accesses.add(new Access("r128",address,value.lowBits(),value.highBits()));return value;}
        @Override public void write128(long address,Bits128 value){store(address,value.lowBits(),8);store(address+8,value.highBits(),8);accesses.add(new Access("w128",address,value.lowBits(),value.highBits()));}
    }


    private static void check(boolean condition,String message){checks++;if(!condition)throw new AssertionError(message);}
    private static void normal(QueueFp604Api.Normal actual,VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df,QueueFp604Api.Mxcsr fp,String where){
        var nr=actual.base().normalReturn();
        check(nr.volatileBits().equals(v)&&nr.nonvolatileBits().equals(n),where+" fullV/N");
        check(nr.returnRipBits()==rip&&nr.callerRspBits()==sp&&actual.base().postDirectionFlagSet()==df&&actual.postMxcsr()==fp,where+" actualRET/SP/DF/same fullMxcsr");
    }
    private static final class Operations implements PostState240Api.FloatingStages {
        final List<Long> sites=new ArrayList<>();
        void before(PostState240Api.FpFrame f,long site,long low){
            sites.add(site);check(f.before().instructionRva()==site&&f.originCallSiteRva()==ORIGIN,"actual FP site/origin");
            check(f.before().currentState().rspBits()==P&&f.before().currentState().volatileBits().xmm0().equals(new Bits128(low,0)),"finite FP raw input lanes");
            check(f.before().directionFlagSet()&&f.before().mxcsr()==PRE,"explicit complete FP pre-environment");
        }
        @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame f){
            before(f,0x21a5192L,1);return new PostState240Api.VectorCompleted(new Bits128(0x3f800000L,0),true,PRE);
        }
        @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame f,int raw){
            before(f,0x21a5195L,0x3f800000L);check(raw==0x3fc00000,"artificial RAM copies separately held1.5f literal");
            return new PostState240Api.VectorCompleted(new Bits128(0x3fc00000L,0),true,PRE);
        }
        @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame f){
            before(f,0x21a519dL,0x3fc00000L);return new PostState240Api.IntegerCompleted(1,true,PRE);
        }
    }
    private static final class Scene {
        final Ram ram=new Ram();final Operations operations=new Operations();
        final List<Budget> budgets=new ArrayList<>();
        final List<CallOutcome242Api.CallFrame> outerFrames=new ArrayList<>();
        final List<QueueFp604Api.Outcome> outerOutcomes=new ArrayList<>();
        final List<PostVtable247Api.CallFrame> secondFrames=new ArrayList<>();
        final List<PostVtable247Api.TailFrame> tailFrames=new ArrayList<>();
        final List<FreePostState251Api.AlreadyPushedCallFrame> lowerFrames=new ArrayList<>();
        final List<QueueFp604Api.Normal> lowerNormals=new ArrayList<>();
        int b94Calls;QueueFp604Api.Normal b94Normal,actual18,actualFree;
        Scene(){
            ram.fill(S-0x1000,0x2000,0xdd);ram.fill(DEST,0x30,0);ram.fill(SOURCE,0x30,0);
            ram.fill(DATA,0x20,0);ram.fill(NEW,0x20,0xcc);ram.fill(OLD,0x10,0xa7);
            ram.fill(OBJECT,0x410,0);ram.fill(TABLE,0x50,0);ram.fill(PROVIDER,0x20,0);ram.fill(PROVIDER_TABLE,0x20,0);
            for(long a:new long[]{IMAGE+0x5c5de30L,IMAGE+0x43da748L,IMAGE+0x43da738L,CELL})ram.fill(a,8,0);
            ram.fill(IMAGE+0x49f64f0L,4,0);
            ram.writeQword(S,RET);ram.writeQword(DEST,OLD);ram.writeDword(DEST+8,1);ram.writeQword(DEST+0x10,OBJECT);
            ram.writeQword(SOURCE,DATA);ram.writeDword(SOURCE+8,2);ram.writeDword(SOURCE+0xc,2);ram.writeQword(SOURCE+0x10,SOURCE_ALLOC);
            ram.write128(DATA,PAYLOAD1);ram.write128(DATA+16,PAYLOAD2);
            ram.writeQword(OBJECT,TABLE);ram.writeQword(OBJECT+0x408,PROVIDER);
            ram.writeQword(TABLE+8,IMAGE+0x855870L);ram.writeQword(TABLE+0x10,IMAGE+0x855830L);ram.writeQword(TABLE+0x38,IMAGE+0x86e140L);
            ram.writeQword(PROVIDER,PROVIDER_TABLE);ram.writeQword(PROVIDER_TABLE+8,IMAGE+0x8571d0L);ram.writeQword(PROVIDER_TABLE+0x10,IMAGE+0x8571c0L);
            ram.writeQword(IMAGE+0x5c5de30L,HEAP);ram.writeQword(IMAGE+0x43da748L,TARGETS[0]);ram.writeQword(IMAGE+0x43da738L,TARGETS[2]);
            ram.writeDword(CELL,0x74747474);ram.writeDword(CELL+4,0x25252525);ram.writeDword(IMAGE+0x49f64f0L,0x3fc00000);ram.accesses.clear();
        }
        QueueFp604Api.Outcome run(){
            FreePostState251Api.Children explicitFree=(frame,same)->{
                int k=lowerFrames.size();check(k<4&&same==ram,"four exact sameRAM free children");lowerFrames.add(frame);
                var c=frame.call();
                check(frame.ownerEntryRva()==0x424e364L&&frame.imageBaseBits()==IMAGE&&c.callSiteRva()==SITES[k]
                        &&frame.instructionLength()==LENGTHS[k]&&c.targetBits()==TARGETS[k],"actual201 source CALL descriptor");
                check(c.kind()==((k==0||k==2)?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA),"actual lower target kind");
                check(c.rspBits()==H&&frame.childInput().entry().rspBits()==J&&frame.returnRipBits()==IMAGE+SITES[k]+LENGTHS[k],"actual201 unique push/continuation/SP");
                check(c.volatileBits().equals(LOWER_PRE_V[k])&&c.nonvolatileBits().equals(LOWER_PRE_N[k]),"full literal actual201 pre-call V/N");
                check(frame.childInput().entry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,J,LOWER_PRE_V[k],LOWER_PRE_N[k])),"full literal already-pushed Entry");
                check(frame.childInput().originCallSiteRva()==SITES[k]&&frame.childInput().directionFlagSet()==DF[k]
                        &&frame.childInput().mxcsr()==ENV[k],"actual lower origin and preceding explicit post-environment");
                // This qualified opaque child owns this actual RET read; the251 bridge does not.
                long rip=ram.readQword(J);
                var offered=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                        LOWER_POST_V[k],rip,H,LOWER_PRE_N[k]),DF[k+1]),ENV[k+1]);
                lowerNormals.add(offered);return offered;
            };
            DefaultStaticFp648Api.Calls defaults=new DefaultStaticFp648Api.Calls(){
                @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame f){
                    b94Calls++;
                    check(f.call().callSiteRva()==0x8571d7L&&f.call().kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                            &&f.call().targetBits()==0x4223b94L&&f.instructionLength()==5,"only explicit actual18 B94 delegate, never free251");
                    check(f.call().rspBits()==F&&f.childEntry().rspBits()==G&&f.returnRipBits()==IMAGE+0x8571dcL,"actual18 B94 frame SP/RET");
                    check(f.childEntry().volatileBits().equals(B94_PRE_V)&&f.childEntry().nonvolatileBits().equals(ALLOC_N)
                            &&f.directionFlagSet()&&f.preMxcsr()==PRE,"full literal18 B94 input");
                    b94Normal=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                            ALLOC_V,ram.readQword(G),F,ALLOC_N),false),ENV[0]);return b94Normal;
                }
                @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame f){throw new AssertionError("selected actual14 free tail was not bound through253");}
            };
            var chain=DefaultFreeChain255.bind(explicitFree,defaults,new PostVtable247Api.Children(){
                @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame f,GovernmentCrtBoundary185Api.Memory m){throw new AssertionError("unexpected247 remaining CALL");}
                @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame f,GovernmentCrtBoundary185Api.Memory m){throw new AssertionError("unexpected247 remaining tail");}
            });
            PostVtable247Api.Children traced=new PostVtable247Api.Children(){
                @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame f,GovernmentCrtBoundary185Api.Memory m){
                    check(m==ram,"actual14 sameRAM");secondFrames.add(f);
                    check(f.ownerEntryRva()==0x855830L&&f.call().callSiteRva()==0x85585bL&&f.instructionLength()==4&&f.call().targetBits()==IMAGE+0x8571c0L,"real58 second14 qualifier");
                    check(f.childInput().originCallSiteRva()==0x85585bL,"observable actual247 incoming continuation origin;255 source binds this exact field");
                    check(f.childInput().entry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,G,ENTRY14_V,ENTRY14_N))
                            &&!f.childInput().directionFlagSet()&&f.childInput().mxcsr()==ENV[0],"complete actual14 nonzero input");
                    var out=chain.invoke(f,m);check(out instanceof QueueFp604Api.Normal,"actual14/253/251 whole Normal");actualFree=(QueueFp604Api.Normal)out;return out;
                }
                @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame f,GovernmentCrtBoundary185Api.Memory m){
                    check(m==ram,"actual18 sameRAM");tailFrames.add(f);
                    check(f.ownerEntryRva()==0x855870L&&f.transfer().jumpSiteRva()==0x8558a0L&&f.instructionLength()==3
                            &&f.transfer().targetBits()==IMAGE+0x8571d0L&&f.targetInput().originCallSiteRva()==0x21a51b9L,"real51 whole18 tail/origin");
                    check(f.targetInput().entry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,E,ENTRY18_V,ALLOC_N))
                            &&f.targetInput().directionFlagSet()&&f.targetInput().mxcsr()==PRE,"complete actual18 input");
                    var out=chain.tail(f,m);check(out instanceof QueueFp604Api.Normal,"actual18 Normal");actual18=(QueueFp604Api.Normal)out;return out;
                }
            };
            var port=Known715PostForward250.bind(ram,traced,f->{throw new AssertionError("unexpected715 callback");});
            CallOutcome242Api.OutcomePort trace=f->{outerFrames.add(f);var out=port.invoke(f);outerOutcomes.add(out);return out;};
            var whole=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(operations),(site,cursor,end)->budgets.add(new Budget(site,cursor,end)),trace);
            return whole.transfer715(new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,S,INPUT_V,INPUT_N),true,PRE,ORIGIN),ram);
        }
    }
    private static void real715NonzeroFreeThroughFourLowerOutcomes(){
        Scene s=new Scene();var out=s.run();
        check(out instanceof QueueFp604Api.Normal&&s.outerFrames.size()==2&&s.outerOutcomes.size()==2,"actual715 normal after real18/14/251");
        check(s.tailFrames.size()==1&&s.secondFrames.size()==1&&s.b94Calls==1&&s.lowerFrames.size()==4,"exact reached producer/callback counts");
        check(s.actual18!=s.b94Normal&&s.outerOutcomes.get(0)==s.actual18,"51/250 forwards actual18 body Normal");
        normal(s.actual18,ALLOC_V,ALLOC_N,IMAGE+0x21a51bcL,P,false,ENV[0],"actual18");
        normal(s.actualFree,FINAL251_V,ENTRY14_N,IMAGE+0x85585fL,F,DF[4],ENV[4],"actual251 ->253 ->14 tail result");
        check(s.lowerNormals.stream().noneMatch(n->n==s.actualFree),"actual251 final epilogue result is not an opaque lower Normal");
        normal((QueueFp604Api.Normal)s.outerOutcomes.get(1),FINAL251_V,FINAL58_N,IMAGE+0x21a5226L,P,DF[4],ENV[4],"actual58 restore andRET");
        normal((QueueFp604Api.Normal)out,FINAL715_V,INPUT_N,RET,S+8,DF[4],ENV[4],"actual715 final restore andRET");
        check(!ENV[4].isExact()&&ENV[4]!=PRE&&ENV[4]!=ENV[0],"final full partial-knowledgeMxcsr is explicit fourth child object");
        check(s.outerFrames.get(0).normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N
                &&s.outerFrames.get(1).normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N,"original242 N admission unchanged");
        check(s.operations.sites.equals(List.of(0x21a5192L,0x21a5195L,0x21a519dL)),"three actual qualified finite FP operations");
        check(s.budgets.equals(List.of(new Budget(0x21a5050L,S,0),new Budget(0x21a51d0L,DATA,DATA+32),new Budget(0x21a51d0L,DATA+16,DATA+32))),"two true source copies; cleared oldcount prevents5200 range");
        check(s.ram.peek128(NEW).equals(PAYLOAD1)&&s.ram.peek128(NEW+16).equals(PAYLOAD2),"sameRAM two actual MOV128 payloads");
        for(int k=0;k<2;k++){
            long low=k==0?PAYLOAD1.lowBits():PAYLOAD2.lowBits();
            check(s.ram.count("r128",DATA+16*k,low)==1&&s.ram.count("w128",NEW+16*k,low)==1,"each actual source/destination vector effect once");
        }
        check(s.ram.peek(DEST)==NEW&&s.ram.peekDword(DEST+8)==2&&s.ram.peekDword(DEST+0xc)==2&&s.ram.peekDword(SOURCE+0xc)==0
                &&s.ram.count("w32",SOURCE+0xc,0)==1,"actual715 header commit/source count clear");
        check(s.ram.peekDword(CELL)==0x76543210&&s.ram.peekDword(CELL+4)==0x25252525&&s.ram.count("w32",CELL,0x76543210)==1,"actual201 lowEAX failure-cell store and adjacent word");
        check(s.ram.count("w32",G+16,0)==1&&s.ram.count("r32",G+16,0)==1&&s.ram.count("w64",G-8,OLD)==1&&s.ram.count("r64",G-8,OLD)==1,"actual17 thunk and61 push/pop exactly once");
        check(s.ram.count("r64",OBJECT+0x408,PROVIDER)==2,"two fresh actual8B getter loads");
        for(long rip:new long[]{IMAGE+0x21a51bcL,IMAGE+0x21a5226L})check(s.ram.count("w64",E,rip)==1&&s.ram.count("r64",E,rip)==1,"one each outer715 CALLpush/calleeRET");
        for(long rip:new long[]{IMAGE+0x855886L,IMAGE+0x8571dcL,IMAGE+0x85584fL,IMAGE+0x85585fL})check(s.ram.count("w64",G,rip)==1&&s.ram.count("r64",G,rip)==1,"one each getter/B94/14call push and calleeRET");
        for(int k=0;k<4;k++){long rip=IMAGE+SITES[k]+LENGTHS[k];check(s.ram.count("w64",J,rip)==1&&s.ram.count("r64",J,rip)==1,"201 owns each lower push, opaque child owns each lowerRET");}
        check(s.ram.count("r64",S,RET)==1,"only actual715 finalRET");
        for(int k=0;k<16;k++)check(s.ram.byteAt(OLD+k)==0xa7,"no inferred native free RAM semantics");
    }
    public static void main(String[] args){
        if(args.length>1||(args.length==1&&!args[0].equals("real715NonzeroFreeThroughFourLowerOutcomes")))throw new IllegalArgumentException("unknown new scene");
        real715NonzeroFreeThroughFourLowerOutcomes();
        System.out.println("PASS defaultchain255 one new whole715 deepNormal/"+checks+" checks; synthetic RAM/complete FP/B94/free lower ports; no Native/hardware/Root/natural credit");
    }
}

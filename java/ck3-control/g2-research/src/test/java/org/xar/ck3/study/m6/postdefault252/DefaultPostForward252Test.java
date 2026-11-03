package org.xar.ck3.study.m6.postdefault252;

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
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/** One new actual18/14 producer integration; explicit B94/FP ports do not model those algorithms. */
public final class DefaultPostForward252Test {
    private static final long IMAGE=0x140000000L,S=0x300008L,P=S-0x478,E=P-8,F=E-0x28,G=F-8;
    private static final long DEST=0x2000,SOURCE=0x3000,DATA=0x5000,NEW=0x6000;
    private static final long OBJECT=0x8000,TABLE=0x9000,PROVIDER=0xa000,PROVIDER_TABLE=0xb000,SOURCE_ALLOC=0xc000;
    private static final long ALLOC_TARGET=IMAGE+0x8571d0L,FREE_TARGET=IMAGE+0x8571c0L;
    private static final long RET=0x7fff0000feed0250L,ORIGIN=0x700001L;
    private static final QueueFp604Api.Mxcsr PRE=QueueFp604Api.Mxcsr.exact(0x1f80);
    private static final QueueFp604Api.Mxcsr B94_POST=QueueFp604Api.Mxcsr.exact(0x1f81);
    private static final Bits128 PAYLOAD=new Bits128(0x0123456789abcdefL,0xfedcba9876543210L),ZERO=new Bits128(0,0);
    private static int checks;
    private DefaultPostForward252Test() { }
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

    private static Bits128 x(long seed,int k){return new Bits128(seed+2*k,~seed-2*k);}
    private static VolatileBits v(long seed){return new VolatileBits(seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,
            x(seed,0),x(seed,1),x(seed,2),x(seed,3),x(seed,4),x(seed,5));}
    private static VolatileBits change(VolatileBits b,long a,long c,long d,long r8,long r9,long r11,Bits128 x0){
        return new VolatileBits(a,c,d,r8,r9,b.r10Bits(),r11,x0,b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());
    }
    private static NonvolatileBits n(){return new NonvolatileBits(0x8181818181818181L,0x8282828282828282L,
            0x8383838383838383L,0x8484848484848484L,0x8585858585858585L,0x8686868686868686L,
            0x8787878787878787L,0x8888888888888888L,x(0x8967896789678967L,6));}
    private static NonvolatileBits allocN(){return new NonvolatileBits(DATA,0,DEST,DATA+0x10,n().r12Bits(),1,SOURCE,1,n().xmm6());}
    private static NonvolatileBits freeN(){return new NonvolatileBits(DATA+0x10,0,DEST,DATA+0x10,NEW,1,SOURCE,1,n().xmm6());}
    private static NonvolatileBits secondN(){return new NonvolatileBits(0,0,DEST,8,NEW,1,SOURCE,1,n().xmm6());}
    private static void check(boolean condition,String message){checks++;if(!condition)throw new AssertionError(message);}

    /** Artificial, finite zero-input complete operations admitted by the actual243 provider. */
    private static final class ZeroOperations implements PostState240Api.FloatingStages {
        final List<Long> sites=new ArrayList<>();
        private void before(PostState240Api.FpFrame frame,long site){
            sites.add(frame.before().instructionRva());
            check(frame.before().instructionRva()==site&&frame.originCallSiteRva()==ORIGIN,"actual growth SSE site/origin");
            check(frame.before().currentState().rspBits()==P&&frame.before().currentState().volatileBits().xmm0().equals(ZERO),"finite zero-input operation");
            check(frame.before().directionFlagSet()&&frame.before().mxcsr()==PRE,"complete operation pre-environment");
        }
        @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame frame){
            before(frame,0x21a5192L);return new PostState240Api.VectorCompleted(ZERO,true,PRE);
        }
        @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame frame,int raw){
            before(frame,0x21a5195L);check(raw==0x3fc00000,"artificial RAM uses separately held1.5f literal");
            return new PostState240Api.VectorCompleted(ZERO,true,PRE);
        }
        @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame frame){
            before(frame,0x21a519dL);return new PostState240Api.IntegerCompleted(0,true,PRE);
        }
    }

    private static final class Scene {
        final Ram memory=new Ram();
        final ZeroOperations operations=new ZeroOperations();
        final List<Budget> budgets=new ArrayList<>();
        final List<CallOutcome242Api.CallFrame> outerFrames=new ArrayList<>();
        final List<QueueFp604Api.Outcome> outerOutcomes=new ArrayList<>();
        final List<PostVtable247Api.CallFrame> secondFrames=new ArrayList<>();
        final List<PostVtable247Api.TailFrame> tailFrames=new ArrayList<>();
        final List<DefaultStaticFp648Api.CallFrame> lowerFrames=new ArrayList<>();
        final VolatileBits initial=v(0x1234000000000000L),postSeed=v(0xa110000000000000L);
        final VolatileBits allocatedV=change(postSeed,NEW,postSeed.rcxBits(),postSeed.rdxBits(),postSeed.r8Bits(),postSeed.r9Bits(),postSeed.r11Bits(),postSeed.xmm0());
        QueueFp604Api.Normal explicitB94Normal,actual18Normal,actual14Normal;

        Scene(){
            memory.fill(S-0x1000,0x2000,0xdd);memory.fill(DEST,0x30,0);memory.fill(SOURCE,0x30,0);
            memory.fill(DATA,0x10,0);memory.fill(NEW,0x10,0xcc);memory.fill(OBJECT,0x410,0);
            memory.fill(TABLE,0x50,0);memory.fill(PROVIDER,0x20,0);memory.fill(PROVIDER_TABLE,0x20,0);
            memory.fill(IMAGE+0x49f64f0L,4,0);
            memory.writeQword(S,RET);memory.writeQword(DEST+0x10,OBJECT);
            memory.writeQword(SOURCE,DATA);memory.writeDword(SOURCE+8,1);memory.writeDword(SOURCE+0xc,1);memory.writeQword(SOURCE+0x10,SOURCE_ALLOC);
            memory.write128(DATA,PAYLOAD);memory.writeQword(OBJECT,TABLE);memory.writeQword(OBJECT+0x408,PROVIDER);
            memory.writeQword(TABLE+8,IMAGE+0x855870L);memory.writeQword(TABLE+0x10,IMAGE+0x855830L);memory.writeQword(TABLE+0x38,IMAGE+0x86e140L);
            memory.writeQword(PROVIDER,PROVIDER_TABLE);memory.writeQword(PROVIDER_TABLE+8,ALLOC_TARGET);memory.writeQword(PROVIDER_TABLE+0x10,FREE_TARGET);
            memory.writeDword(IMAGE+0x49f64f0L,0x3fc00000);memory.accesses.clear();
        }

        QueueFp604Api.Outcome run(){
            DefaultStaticFp648Api.Calls unknownDefaults=new DefaultStaticFp648Api.Calls(){
                @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame){
                    lowerFrames.add(frame);
                    check(frame.call().callSiteRva()==0x8571d7L&&frame.call().kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                            &&frame.call().targetBits()==0x4223b94L&&frame.instructionLength()==5,"actual18 direct B94 CALL descriptor");
                    check(frame.call().rspBits()==F&&frame.childEntry().rspBits()==G&&frame.returnRipBits()==IMAGE+0x8571dcL,"actual18 owns one B94 push with exact continuation");
                    check(frame.childEntry().volatileBits().equals(change(initial,PROVIDER,0x10,0x10,8,ALLOC_TARGET,initial.r11Bits(),ZERO))
                            &&frame.childEntry().nonvolatileBits().equals(allocN()),"actual18 MOV RCX,RDX and complete represented state");
                    check(frame.directionFlagSet()&&frame.preMxcsr()==PRE,"actual18 receives original explicit environment");
                    long freshRip=memory.readQword(frame.childEntry().rspBits());
                    explicitB94Normal=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                            allocatedV,freshRip,frame.childEntry().rspBits()+8,frame.childEntry().nonvolatileBits()),false),B94_POST);
                    return explicitB94Normal;
                }
                @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame){
                    throw new AssertionError("14zero must not enter unheld40EC530 producer");
                }
            };
            var exact=DefaultPostForward252.bind(unknownDefaults,new PostVtable247Api.Children(){
                @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame f,GovernmentCrtBoundary185Api.Memory m){throw new AssertionError("unexpected247 CALL delegate");}
                @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame f,GovernmentCrtBoundary185Api.Memory m){throw new AssertionError("unexpected247 tail delegate");}
            });
            PostVtable247Api.Children tracedChildren=new PostVtable247Api.Children(){
                @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,GovernmentCrtBoundary185Api.Memory same){
                    check(same==memory,"real14 receives the same actual RAM");secondFrames.add(frame);
                    check(frame.ownerEntryRva()==0x855830L&&frame.call().callSiteRva()==0x85585bL&&frame.instructionLength()==4
                            &&frame.call().targetBits()==FREE_TARGET&&frame.childInput().originCallSiteRva()==0x85585bL,"actual58 second CALL/original frame origin");
                    check(frame.childInput().entry().rspBits()==G&&frame.childInput().entry().nonvolatileBits().equals(secondN()),"actual14zero childSP/fullN");
                    check(frame.call().volatileBits().equals(secondV())&&!frame.childInput().directionFlagSet()
                            &&frame.childInput().mxcsr()==B94_POST,"B94 full poststate reaches actual14 input through715/copy/58/getter");
                    var result=exact.invoke(frame,same);check(result instanceof QueueFp604Api.Normal,"actual14zero Normal");
                    actual14Normal=(QueueFp604Api.Normal)result;return result;
                }
                @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,GovernmentCrtBoundary185Api.Memory same){
                    check(same==memory,"real18 receives the same actual RAM");tailFrames.add(frame);
                    check(frame.ownerEntryRva()==0x855870L&&frame.transfer().jumpSiteRva()==0x8558a0L&&frame.instructionLength()==3
                            &&frame.transfer().targetBits()==ALLOC_TARGET&&frame.targetInput().originCallSiteRva()==0x21a51b9L,"actual51 tail/original continuation origin");
                    var entry=frame.targetInput().entry();
                    check(entry.rspBits()==E&&entry.nonvolatileBits().equals(allocN()),"actual51 fresh restore before18; no tail push");
                    check(entry.volatileBits().equals(change(initial,PROVIDER,PROVIDER,0x10,8,ALLOC_TARGET,initial.r11Bits(),ZERO))
                            &&frame.targetInput().directionFlagSet()&&frame.targetInput().mxcsr()==PRE,"full actual51/getter-produced18 input");
                    var result=exact.tail(frame,same);check(result instanceof QueueFp604Api.Normal,"actual18 whole Normal");
                    actual18Normal=(QueueFp604Api.Normal)result;return result;
                }
            };
            var bound=Known715PostForward250.bind(memory,tracedChildren,frame->{throw new AssertionError("unexpected715 callback delegate");});
            CallOutcome242Api.OutcomePort traced=frame->{outerFrames.add(frame);var outcome=bound.invoke(frame);outerOutcomes.add(outcome);return outcome;};
            var whole=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(operations),
                    (site,cursor,end)->budgets.add(new Budget(site,cursor,end)),traced);
            var inputV=change(initial,0x1111,DEST,SOURCE,initial.r8Bits(),initial.r9Bits(),initial.r11Bits(),initial.xmm0());
            return whole.transfer715(new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,S,inputV,n()),true,PRE,ORIGIN),memory);
        }
        VolatileBits secondV(){return change(allocatedV,PROVIDER,PROVIDER,0,8,PROVIDER_TABLE,allocatedV.r11Bits(),PAYLOAD);}
    }

    private static void real18AllocateAnd14ZeroReturnThrough715(){
        Scene s=new Scene();var result=s.run();
        check(result instanceof QueueFp604Api.Normal&&s.outerFrames.size()==2&&s.outerOutcomes.size()==2,"real715 completes two actual whole forwarders");
        check(s.tailFrames.size()==1&&s.secondFrames.size()==1&&s.lowerFrames.size()==1,"one real18/B94 and one real14zero path");
        check(s.operations.sites.equals(List.of(0x21a5192L,0x21a5195L,0x21a519dL)),"three finite complete SSE operations admitted once");
        var first=s.outerFrames.get(0);var second=s.outerFrames.get(1);
        check(first.ownerEntryRva()==0x21a5050L&&first.call().callSiteRva()==0x21a51b9L&&first.call().targetBits()==IMAGE+0x855870L
                &&first.instructionLength()==3&&first.normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N,"outer alloc qualifier and original N admission");
        check(first.call().rspBits()==P&&first.childEntry().rspBits()==E&&first.call().nonvolatileBits().equals(allocN()),"real715 alloc fullN/preCALL/childSP");
        check(first.call().volatileBits().equals(change(s.initial,TABLE,OBJECT,0x10,8,s.initial.r9Bits(),s.initial.r11Bits(),ZERO)),"real715 allocation fullV");
        check(s.outerOutcomes.get(0)==s.actual18Normal&&s.actual18Normal!=s.explicitB94Normal,"51/250 return actual18 body Normal without rebuilding it from B94");
        var allocated=s.actual18Normal;var an=allocated.base().normalReturn();
        check(an.volatileBits().equals(s.allocatedV)&&an.nonvolatileBits().equals(allocN())&&an.returnRipBits()==IMAGE+0x21a51bcL
                &&an.callerRspBits()==P&&!allocated.base().postDirectionFlagSet()&&allocated.postMxcsr()==B94_POST,"actual18 fresh RET and complete B94 V/DF/MXCSR");
        check(second.call().callSiteRva()==0x21a5223L&&second.call().targetBits()==IMAGE+0x855830L
                &&second.normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N&&!second.preDirectionFlagSet()&&second.preMxcsr()==B94_POST,"actual copy/free inherits validated B94 postenvironment");
        check(second.call().volatileBits().equals(change(s.allocatedV,TABLE,OBJECT,0,8,s.allocatedV.r9Bits(),s.allocatedV.r11Bits(),PAYLOAD))
                &&second.call().nonvolatileBits().equals(freeN()),"real715 copy/free fullV/N");
        var release=s.actual14Normal;var rn=release.base().normalReturn();
        check(rn.volatileBits().equals(s.secondV())&&rn.nonvolatileBits().equals(secondN())&&rn.returnRipBits()==IMAGE+0x85585fL&&rn.callerRspBits()==F
                &&!release.base().postDirectionFlagSet()&&release.postMxcsr()==B94_POST,"actual14zero retains full input state and reads its real RET");
        var outerRelease=(QueueFp604Api.Normal)s.outerOutcomes.get(1);var on=outerRelease.base().normalReturn();
        check(on.volatileBits().equals(s.secondV())&&on.nonvolatileBits().equals(freeN())&&on.returnRipBits()==IMAGE+0x21a5226L&&on.callerRspBits()==P
                &&!outerRelease.base().postDirectionFlagSet()&&outerRelease.postMxcsr()==B94_POST,"actual58 fresh restore/RET carries real14 result");
        var normal=(QueueFp604Api.Normal)result;var nr=normal.base().normalReturn();var finalV=s.secondV();
        check(nr.volatileBits().equals(change(finalV,DEST,finalV.rcxBits(),finalV.rdxBits(),finalV.r8Bits(),finalV.r9Bits(),S-0x28,finalV.xmm0()))
                &&nr.nonvolatileBits().equals(n()),"actual715 final fullV/fresh restoredN");
        check(nr.returnRipBits()==RET&&nr.callerRspBits()==S+8&&!normal.base().postDirectionFlagSet()&&normal.postMxcsr()==B94_POST,"actual715 RET/SP/postDF/fullMXCSR from B94 via real18/14");
        check(s.budgets.equals(List.of(new Budget(0x21a5050L,S,0),new Budget(0x21a51d0L,DATA,DATA+0x10))),"one real entry and one copy iteration");
        check(s.memory.peek128(NEW).equals(PAYLOAD)&&s.memory.count("r128",DATA,PAYLOAD.lowBits())==1&&s.memory.count("w128",NEW,PAYLOAD.lowBits())==1,"one sameRAM MOV128");
        check(s.memory.peek(DEST)==NEW&&s.memory.peekDword(DEST+8)==1&&s.memory.peekDword(DEST+0xc)==1
                &&s.memory.peekDword(SOURCE+0xc)==0&&s.memory.count("w32",SOURCE+0xc,0)==1,"actual destination commit/source count clear");
        check(s.memory.peek(SOURCE)==DATA&&s.memory.peekDword(SOURCE+8)==1&&s.memory.peek(SOURCE+0x10)==SOURCE_ALLOC,"source pointer/capacity/allocator remain actual");
        check(s.memory.count("r64",OBJECT+0x408,PROVIDER)==2,"two actual8B getter loads");
        for(long rip:new long[]{IMAGE+0x21a51bcL,IMAGE+0x21a5226L})
            check(s.memory.count("w64",E,rip)==1&&s.memory.count("r64",E,rip)==1,"each real715 CALL/whole callee RET exactly once");
        for(long rip:new long[]{IMAGE+0x855886L,IMAGE+0x8571dcL,IMAGE+0x85584fL,IMAGE+0x85585fL})
            check(s.memory.count("w64",G,rip)==1&&s.memory.count("r64",G,rip)==1,"each actual getter/B94/second CALL push and actual callee RET exactly once");
        check(s.memory.count("r64",S,RET)==1,"one real715 final RET; no consumer/tail synthetic RET");
    }

    public static void main(String[] args){
        if(args.length>1||(args.length==1&&!args[0].equals("real18AllocateAnd14ZeroReturnThrough715")))
            throw new IllegalArgumentException("unknown new scene");
        real18AllocateAnd14ZeroReturnThrough715();
        System.out.println("PASS postdefault252 one new actual18/14 producer scene/"+checks
                +" checks; artificial RAM/complete B94 and FP ports; no Native/hardware/Root/natural credit");
    }
}

package org.xar.ck3.study.m6.postforward250;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postentry242.WholeTransferPostState242;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api;

/** Actual deep callback consumer; explicit complete artificial FP/opaque ports give no hardware credit. */
public final class Known715PostForward250Test {
    private static final long IMAGE=0x140000000L,S=0x300008L,P=S-0x478,E=P-8,F=E-0x28,G=F-8;
    private static final long DEST=0x2000,SOURCE=0x3000,DATA=0x5000,NEW=0x6000;
    private static final long OBJECT=0x8000,TABLE=0x9000,PROVIDER=0xa000,PROVIDER_TABLE=0xb000,SOURCE_ALLOC=0xc000;
    private static final long ALLOC_TARGET=IMAGE+0x710000L,FREE_TARGET=IMAGE+0x720000L;
    private static final long RET=0x7fff0000feed0250L,ORIGIN=0x700001L;
    private static final QueueFp604Api.Mxcsr PRE=QueueFp604Api.Mxcsr.exact(0x1f80);
    private static final QueueFp604Api.Mxcsr ALLOC_POST=QueueFp604Api.Mxcsr.exact(0x1f81);
    private static final QueueFp604Api.Mxcsr FREE_POST=new QueueFp604Api.Mxcsr(0x1fa1,0xffe1);
    private static final Bits128 PAYLOAD=new Bits128(0x0123456789abcdefL,0xfedcba9876543210L),ZERO=new Bits128(0,0);
    private static int checks;
    private Known715PostForward250Test() { }
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
        long readsAt(long address){return accesses.stream().filter(a->a.kind().startsWith("r")&&a.address()==address).count();}
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
    private static void check(boolean condition,String message){checks++;if(!condition)throw new AssertionError(message);}

    /** Finite explicit operation inputs for this zero-capacity scene; no host floating implementation. */
    private static final class ZeroOperations implements PostState240Api.FloatingStages {
        final List<Long> sites=new ArrayList<>();
        private void before(PostState240Api.FpFrame frame,long site){
            sites.add(frame.before().instructionRva());
            check(frame.before().instructionRva()==site&&frame.originCallSiteRva()==ORIGIN,"actual source SSE site/origin");
            check(frame.before().currentState().rspBits()==P&&frame.before().currentState().volatileBits().xmm0().equals(ZERO),"finite zero-input source stage");
            check(frame.before().directionFlagSet()&&frame.before().mxcsr()==PRE,"explicit full operation pre-environment");
        }
        @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame frame){
            before(frame,0x21a5192L);return new PostState240Api.VectorCompleted(ZERO,true,PRE);
        }
        @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame frame,int raw){
            before(frame,0x21a5195L);check(raw==0x3fc00000,"artificial RAM carries separately held1.5f rawliteral");
            return new PostState240Api.VectorCompleted(ZERO,true,PRE);
        }
        @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame frame){
            before(frame,0x21a519dL);return new PostState240Api.IntegerCompleted(0,true,PRE);
        }
    }

    private static final class Scene {
        final boolean stopTail;
        final Ram memory=new Ram();
        final ZeroOperations operations=new ZeroOperations();
        final List<Budget> budgets=new ArrayList<>();
        final List<CallOutcome242Api.CallFrame> outerFrames=new ArrayList<>(),remainingFrames=new ArrayList<>();
        final List<QueueFp604Api.Outcome> outerOutcomes=new ArrayList<>();
        final List<PostVtable247Api.CallFrame> opaqueSecondFrames=new ArrayList<>();
        final List<PostVtable247Api.TailFrame> tailFrames=new ArrayList<>();
        final VolatileBits initial=v(0x1234000000000000L),allocV=v(0xa110000000000000L),freeV=v(0xf250000000000000L);
        QueueFp604Api.Normal actualAllocNormal,actualFreeSecondNormal;
        QueueFp604Api.Stopped actualDeepStop;

        Scene(boolean stopTail){
            this.stopTail=stopTail;
            memory.fill(S-0x1000,0x2000,0xdd);memory.fill(DEST,0x30,0);memory.fill(SOURCE,0x30,0);
            memory.fill(DATA,0x10,0);memory.fill(NEW,0x10,0xcc);memory.fill(OBJECT,0x410,0);
            memory.fill(TABLE,0x50,0);memory.fill(PROVIDER,0x20,0);memory.fill(PROVIDER_TABLE,0x20,0);
            memory.fill(IMAGE+0x49f64f0L,4,0);
            memory.writeQword(S,RET);memory.writeQword(DEST,0);memory.writeDword(DEST+8,0);memory.writeDword(DEST+0xc,0);memory.writeQword(DEST+0x10,OBJECT);
            memory.writeQword(SOURCE,DATA);memory.writeDword(SOURCE+8,1);memory.writeDword(SOURCE+0xc,1);memory.writeQword(SOURCE+0x10,SOURCE_ALLOC);
            memory.write128(DATA,PAYLOAD);memory.writeQword(OBJECT,TABLE);memory.writeQword(OBJECT+0x408,PROVIDER);
            memory.writeQword(TABLE+8,IMAGE+0x855870L);memory.writeQword(TABLE+0x10,IMAGE+0x855830L);memory.writeQword(TABLE+0x38,IMAGE+0x86e140L);
            memory.writeQword(PROVIDER,PROVIDER_TABLE);memory.writeQword(PROVIDER_TABLE+8,ALLOC_TARGET);memory.writeQword(PROVIDER_TABLE+0x10,FREE_TARGET);
            memory.writeDword(IMAGE+0x49f64f0L,0x3fc00000);memory.accesses.clear();
        }

        QueueFp604Api.Outcome run(){
            PostVtable247Api.Children explicitOpaque=new PostVtable247Api.Children(){
                @Override public QueueFp604Api.Outcome invoke(PostVtable247Api.CallFrame frame,GovernmentCrtBoundary185Api.Memory same){
                    check(same==memory,"actual58 opaque second receives same RAM");opaqueSecondFrames.add(frame);
                    check(frame.ownerEntryRva()==0x855830L&&frame.call().callSiteRva()==0x85585bL&&frame.instructionLength()==4
                            &&frame.call().targetBits()==FREE_TARGET,"only actual58 second CALL is opaque");
                    check(!frame.childInput().directionFlagSet()&&frame.childInput().mxcsr()==ALLOC_POST,"allocation postDF/MXCSR reach actual58 second");
                    check(frame.call().volatileBits().equals(change(allocV,PROVIDER,PROVIDER,0,8,PROVIDER_TABLE,allocV.r11Bits(),PAYLOAD)),"complete current58 second V includes actual source copy XMM0");
                    var current=freeN();var expected=new NonvolatileBits(0,0,DEST,8,NEW,1,SOURCE,1,current.xmm6());
                    check(frame.call().nonvolatileBits().equals(expected)&&frame.childInput().entry().rspBits()==G,"actual58 current fullN and second childSP");
                    actualFreeSecondNormal=opaqueNormal(frame.childInput().entry(),freeV,true,FREE_POST);return actualFreeSecondNormal;
                }
                @Override public QueueFp604Api.Outcome tail(PostVtable247Api.TailFrame frame,GovernmentCrtBoundary185Api.Memory same){
                    check(same==memory,"actual51 tail receives same RAM");tailFrames.add(frame);
                    check(frame.transfer().jumpSiteRva()==0x8558a0L&&frame.transfer().targetBits()==ALLOC_TARGET
                            &&frame.targetInput().originCallSiteRva()==0x21a51b9L,"actual known51 JMP retains outer CALL continuation origin");
                    var entry=frame.targetInput().entry();
                    check(entry.rspBits()==E&&entry.nonvolatileBits().equals(allocN()),"actual51 fresh local restore before tail, no extra push");
                    check(entry.volatileBits().equals(change(initial,PROVIDER,PROVIDER,0x10,8,ALLOC_TARGET,initial.r11Bits(),ZERO)),"full actual51/getter-produced tail state");
                    check(frame.targetInput().directionFlagSet()&&frame.targetInput().mxcsr()==PRE,"getter does not invent post-environment");
                    if(stopTail){
                        actualDeepStop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                                new QueueFp604Api.Snapshot(entry,0x710000L,true,PRE),0,frame.targetInput().originCallSiteRva());
                        return actualDeepStop;
                    }
                    var allocated=change(allocV,NEW,allocV.rcxBits(),allocV.rdxBits(),allocV.r8Bits(),allocV.r9Bits(),allocV.r11Bits(),allocV.xmm0());
                    actualAllocNormal=opaqueNormal(entry,allocated,false,ALLOC_POST);return actualAllocNormal;
                }
            };
            var bound=Known715PostForward250.bind(memory,explicitOpaque,frame->{
                remainingFrames.add(frame);
                return new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                        new QueueFp604Api.Snapshot(frame.childEntry(),frame.call().targetBits()-IMAGE,frame.preDirectionFlagSet(),frame.preMxcsr()),0,frame.call().callSiteRva());
            });
            CallOutcome242Api.OutcomePort traced=frame->{
                outerFrames.add(frame);var actual=bound.invoke(frame);outerOutcomes.add(actual);return actual;
            };
            var whole=new WholeTransferPostState242(new OpaqueSseOutcomeProvider243(operations),
                    (site,cursor,end)->budgets.add(new Budget(site,cursor,end)),traced);
            var inputV=change(initial,0x1111,DEST,SOURCE,initial.r8Bits(),initial.r9Bits(),initial.r11Bits(),initial.xmm0());
            return whole.transfer715(new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,S,inputV,n()),true,PRE,ORIGIN),memory);
        }

        /** Explicit complete opaque callback contract, never original allocator/free algorithm. */
        QueueFp604Api.Normal opaqueNormal(GovernmentCrtBoundary185Api.Entry actualEntry,VolatileBits postV,boolean postDF,QueueFp604Api.Mxcsr postFP){
            long actualRip=memory.readQword(actualEntry.rspBits());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(
                    postV,actualRip,actualEntry.rspBits()+8,actualEntry.nonvolatileBits()),postDF),postFP);
        }
    }

    private static void commonPrefix(Scene s){
        check(s.operations.sites.equals(List.of(0x21a5192L,0x21a5195L,0x21a519dL)),"three actual growth hooks through243 admission once");
        check(s.remainingFrames.isEmpty()&&s.tailFrames.size()==1,"only exact known250 forwarding route; one actual51 tail");
        var first=s.outerFrames.get(0);
        check(first.ownerEntryRva()==0x21a5050L&&first.call().callSiteRva()==0x21a51b9L&&first.call().targetBits()==IMAGE+0x855870L
                &&first.instructionLength()==3&&first.normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N,"original outer242 admission unchanged");
        check(first.call().rspBits()==P&&first.childEntry().rspBits()==E&&first.call().nonvolatileBits().equals(allocN()),"actual715 full allocation frame and single-push SP");
        check(first.call().volatileBits().equals(change(s.initial,TABLE,OBJECT,0x10,8,s.initial.r9Bits(),s.initial.r11Bits(),ZERO)),"actual715 allocation fullV");
        check(s.memory.count("w64",E,IMAGE+0x21a51bcL)==1&&s.memory.count("w64",G,IMAGE+0x855886L)==1
                &&s.memory.count("r64",G,IMAGE+0x855886L)==1,"outer CALL and real51 getter CALL each own only one push/RET");
        check(s.memory.count("r64",OBJECT+0x408,PROVIDER)==(s.stopTail?1:2),"real8B getter reads actual object field freshly per reached first CALL");
        check(s.memory.count("w32",DEST+0xc,0)==1,"actual715 different-allocator prefix remains");
        check(s.memory.peek(SOURCE)==DATA&&s.memory.peekDword(SOURCE+8)==1&&s.memory.peek(SOURCE+0x10)==SOURCE_ALLOC,"source pointer/capacity/allocator retained");
    }

    private static void positiveGrowthThroughBothForwarders(){
        Scene s=new Scene(false);var result=s.run();commonPrefix(s);
        check(result instanceof QueueFp604Api.Normal&&s.outerFrames.size()==2&&s.outerOutcomes.size()==2,"actual715 normal after both real forwarders");
        check(s.opaqueSecondFrames.size()==1,"only one explicitly complete unknown freeSecond");
        var allocated=(QueueFp604Api.Normal)s.outerOutcomes.get(0);var released=(QueueFp604Api.Normal)s.outerOutcomes.get(1);
        check(allocated==s.actualAllocNormal&&!allocated.base().postDirectionFlagSet()&&allocated.postMxcsr()==ALLOC_POST,"51 tail returns original fullOutcome through250/242");
        var freeFrame=s.outerFrames.get(1);
        check(freeFrame.call().callSiteRva()==0x21a5223L&&freeFrame.call().targetBits()==IMAGE+0x855830L
                &&freeFrame.normalRule()==CallOutcome242Api.NormalRule.OPAQUE_PRESERVES_N,"actual715 free selects real58 without rule change");
        check(!freeFrame.preDirectionFlagSet()&&freeFrame.preMxcsr()==ALLOC_POST,"opaque allocation post-state reaches outer715 then58");
        check(freeFrame.call().volatileBits().equals(change(s.allocV,TABLE,OBJECT,0,8,s.allocV.r9Bits(),s.allocV.r11Bits(),PAYLOAD))
                &&freeFrame.call().nonvolatileBits().equals(freeN()),"actual715 copy/free current fullV/N");
        check(released.base().normalReturn().volatileBits().equals(s.freeV)&&released.base().normalReturn().nonvolatileBits().equals(freeN())
                &&released.base().postDirectionFlagSet()&&released.postMxcsr()==FREE_POST,"actual58 fresh local restore and full opaqueSecond poststate");
        check(allocated.base().normalReturn().returnRipBits()==IMAGE+0x21a51bcL&&allocated.base().normalReturn().callerRspBits()==P
                &&released.base().normalReturn().returnRipBits()==IMAGE+0x21a5226L&&released.base().normalReturn().callerRspBits()==P,"both actual outer continuations");
        var normal=(QueueFp604Api.Normal)result;var nr=normal.base().normalReturn();
        check(nr.volatileBits().equals(change(s.freeV,DEST,s.freeV.rcxBits(),s.freeV.rdxBits(),s.freeV.r8Bits(),s.freeV.r9Bits(),S-0x28,s.freeV.xmm0()))
                &&nr.nonvolatileBits().equals(n()),"actual715 final fullV/N from new contexts");
        check(nr.returnRipBits()==RET&&nr.callerRspBits()==S+8&&normal.base().postDirectionFlagSet()&&normal.postMxcsr()==FREE_POST,"actual715 RET/SP/DF/fullpartialMXCSR");
        check(s.budgets.equals(List.of(new Budget(0x21a5050L,S,0),new Budget(0x21a51d0L,DATA,DATA+0x10))),"one real entry and one realcopy loop budget");
        check(s.memory.peek128(NEW).equals(PAYLOAD)&&s.memory.count("r128",DATA,PAYLOAD.lowBits())==1
                &&s.memory.count("w128",NEW,PAYLOAD.lowBits())==1,"one true MOV128 transfer on same RAM");
        check(s.memory.peek(DEST)==NEW&&s.memory.peekDword(DEST+8)==1&&s.memory.peekDword(DEST+0xc)==1
                &&s.memory.peekDword(SOURCE+0xc)==0&&s.memory.count("w32",SOURCE+0xc,0)==1,"real postfree header commit/source clear");
        check(s.memory.count("r64",E,IMAGE+0x21a51bcL)==1&&s.memory.count("w64",E,IMAGE+0x21a5226L)==1
                &&s.memory.count("r64",E,IMAGE+0x21a5226L)==1,"51 tail no extra push/sourceRET; explicit tail owns inheritedRET,58 trueRET once");
        check(s.memory.count("w64",G,IMAGE+0x85584fL)==1&&s.memory.count("r64",G,IMAGE+0x85584fL)==1
                &&s.memory.count("w64",G,IMAGE+0x85585fL)==1&&s.memory.count("r64",G,IMAGE+0x85585fL)==1
                &&s.memory.count("r64",S,RET)==1,"real58 firstgetter/secondCALL and outer715 true RET counts");
    }

    private static void deepTailStoppedPrefix(){
        Scene s=new Scene(true);var result=s.run();commonPrefix(s);
        check(result==s.actualDeepStop&&s.outerOutcomes.size()==1&&s.outerOutcomes.get(0)==result,"exact inner Stopped propagates247/250/242/240/whole715");
        var stopped=s.actualDeepStop;var tail=s.tailFrames.get(0);
        check(stopped.snapshot().currentState()==tail.targetInput().entry()&&stopped.snapshot().instructionRva()==0x710000L
                &&stopped.originCallSiteRva()==0x21a51b9L&&stopped.snapshot().currentState().rspBits()==E,"Stopped retains actual deep tail state/origin after51 epilogue");
        check(stopped.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE&&stopped.raisedConditionBits()==0
                &&stopped.snapshot().directionFlagSet()&&stopped.snapshot().mxcsr()==PRE,"no fabricated postDF/MXCSR for unexecuted opaque tail");
        check(s.outerFrames.size()==1&&s.opaqueSecondFrames.isEmpty()&&s.actualAllocNormal==null&&s.actualFreeSecondNormal==null,"deep stop prevents allocationNormal/free subtree");
        check(s.budgets.equals(List.of(new Budget(0x21a5050L,S,0))),"no source copy budget after deep stop");
        check(s.memory.peek(DEST)==0&&s.memory.peekDword(DEST+8)==0&&s.memory.peekDword(DEST+0xc)==0
                &&s.memory.peekDword(SOURCE+0xc)==1&&s.memory.count("w32",SOURCE+0xc,0)==0,"actual prefix retained without header/sourceclear suffix");
        check(s.memory.accesses.stream().noneMatch(a->a.kind().equals("r128")||a.kind().equals("w128")),"deep stop prevents both vector effects");
        check(s.memory.count("r64",E,IMAGE+0x21a51bcL)==0&&s.memory.count("w64",E,IMAGE+0x21a5226L)==0
                &&s.memory.count("w64",G,IMAGE+0x85584fL)==0&&s.memory.readsAt(S)==0,"no opaqueTail RET/free subtree/outer715 epilogue fabricated");
    }

    public static void main(String[] args){
        String[] selected=args.length==0?new String[]{"positiveGrowthThroughBothForwarders","deepTailStoppedPrefix"}:args;
        for(String name:selected)switch(name){
            case "positiveGrowthThroughBothForwarders" -> positiveGrowthThroughBothForwarders();
            case "deepTailStoppedPrefix" -> deepTailStoppedPrefix();
            default -> throw new IllegalArgumentException("unknown new scene "+name);
        }
        System.out.println("PASS postforward250 "+selected.length+" new deep callback scenes/"+checks
                +" checks; explicit complete artificial operation ports; no Native/hardware/Root/natural credit");
    }
}

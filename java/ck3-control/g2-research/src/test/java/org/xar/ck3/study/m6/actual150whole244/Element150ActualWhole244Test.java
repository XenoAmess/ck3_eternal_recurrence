package org.xar.ck3.study.m6.actual150whole244;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.Element150Fp643Api;
import org.xar.ck3.control.g2.m2.nativecode.Element150FullState643;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.poststate242.CallOutcome242Api;
import org.xar.ck3.study.m6.poststate243.OpaqueSseOutcomeProvider243;

/** Actual new whole-body consumer source witness; no manufactured Normal or FP arithmetic. */
public final class Element150ActualWhole244Test {
    private static final long IMAGE=0x140000000L,S=0x100008L,F=S-0x28,L=S-0x30;
    private static final long DEST=0x6000,SOURCE=0x5000,DATA1=0x8000,DATA2=0x8100;
    private static final long ALLOC1=0x9000,ALLOC2=0x9100,RET=0x7fff0000feed0044L;
    private static final long MULTIPLIER=IMAGE+0x49f64f0L;
    private static final QueueFp604Api.Mxcsr MXCSR=new QueueFp604Api.Mxcsr(0x1f81,0xffc1);
    private static int checks;
    private Element150ActualWhole244Test() { }
    private record Access(String kind,long address,long value) { }
    private record BudgetEntry(long site,long cursor,long end) { }

    private static final class Ram implements Element150Fp643Api.Memory {
        final Map<Long,Integer> data=new HashMap<>();
        final List<Access> accesses=new ArrayList<>();
        void fill(long address,int length,int value) {
            for(int i=0;i<length;i++)data.put(address+i,value&255);
        }
        int byteAt(long address) {
            Integer value=data.get(address);
            if(value==null)throw new AssertionError("unprovided RAM "+Long.toHexString(address));
            return value;
        }
        long load(long address,int length) {
            long value=0;
            for(int i=0;i<length;i++)value|=(long)byteAt(address+i)<<(8*i);
            return value;
        }
        void store(long address,long value,int length) {
            for(int i=0;i<length;i++){byteAt(address+i);data.put(address+i,(int)(value>>>(8*i))&255);}
        }
        long peek(long address){return load(address,8);}
        int peekDword(long address){return(int)load(address,4);}
        int peekByte(long address){return byteAt(address);}
        long count(String kind,long address,long value){return accesses.stream().filter(a->a.kind().equals(kind)&&a.address()==address&&a.value()==value).count();}
        long readsAt(long address){return accesses.stream().filter(a->a.kind().startsWith("r")&&a.address()==address).count();}
        @Override public long readQword(long address){long value=load(address,8);accesses.add(new Access("r64",address,value));return value;}
        @Override public int readDword(long address){int value=(int)load(address,4);accesses.add(new Access("r32",address,value));return value;}
        @Override public int readUnsignedByte(long address){int value=byteAt(address);accesses.add(new Access("r8",address,value));return value;}
        @Override public void writeQword(long address,long value){store(address,value,8);accesses.add(new Access("w64",address,value));}
        @Override public void writeDword(long address,int value){store(address,value,4);accesses.add(new Access("w32",address,value));}
        @Override public void writeByte(long address,int value){store(address,value,1);accesses.add(new Access("w8",address,value&255));}
        @Override public int lockedXaddDword(long address,int addend){throw new AssertionError("unexpected XADD");}
        @Override public Bits128 read128(long address){throw new AssertionError("unexpected data vector read");}
        @Override public void write128(long address,Bits128 value){throw new AssertionError("unexpected data vector write");}
    }

    private static Bits128 x(long seed,int lane){return new Bits128(seed+lane*2L,~seed-lane*2L);}
    private static VolatileBits v(){
        long seed=0x1234000000000000L;
        return new VolatileBits(0x1111,DEST,SOURCE,seed+4,seed+5,seed+6,seed+7,
                x(seed,0),x(seed,1),x(seed,2),x(seed,3),x(seed,4),x(seed,5));
    }
    private static NonvolatileBits n(){
        return new NonvolatileBits(0x8181818181818181L,0x8282828282828282L,0x8383838383838383L,
                0x8484848484848484L,0x8585858585858585L,0x8686868686868686L,
                0x8787878787878787L,0x8888888888888888L,x(0x8967896789678967L,6));
    }
    private static VolatileBits expectedV(long rax,long rcx,long rdx,long r11,Bits128 xmm0){
        var initial=v();
        return new VolatileBits(rax,rcx,rdx,initial.r8Bits(),initial.r9Bits(),initial.r10Bits(),r11,
                xmm0,initial.xmm1(),initial.xmm2(),initial.xmm3(),initial.xmm4(),initial.xmm5());
    }
    private static void check(boolean condition,String message){checks++;if(!condition)throw new AssertionError(message);}

    /** Uses the actual243 provider's typed pre-operation stop; no arithmetic result is supplied. */
    private static final class RecordingStages implements PostState240Api.FloatingStages {
        final OpaqueSseOutcomeProvider243 actual=OpaqueSseOutcomeProvider243.missingPostState();
        int convert,multiply,truncate;
        PostState240Api.FpFrame before;
        QueueFp604Api.Stopped stopped;
        private <T> T remember(T offered){
            if(offered instanceof PostState240Api.StageStopped stage)stopped=stage.actual();
            return offered;
        }
        @Override public PostState240Api.VectorResult convertSignedDwords(PostState240Api.FpFrame frame){convert++;before=frame;return remember(actual.convertSignedDwords(frame));}
        @Override public PostState240Api.VectorResult multiplyLowSingle(PostState240Api.FpFrame frame,int raw){multiply++;before=frame;return remember(actual.multiplyLowSingle(frame,raw));}
        @Override public PostState240Api.IntegerResult truncateLowSingle(PostState240Api.FpFrame frame){truncate++;before=frame;return remember(actual.truncateLowSingle(frame));}
    }

    private static final class Scenario {
        final Ram memory=new Ram();
        final RecordingStages stages=new RecordingStages();
        final List<BudgetEntry> budgets=new ArrayList<>();
        final List<Element150Fp643Api.CallFrame> frames=new ArrayList<>();
        final List<QueueFp604Api.Outcome> outcomes=new ArrayList<>();
        final List<CallOutcome242Api.CallFrame> opaqueCalls=new ArrayList<>();

        Scenario(int firstCount){
            memory.fill(S-0x800,0x1000,0xdd);memory.fill(SOURCE,0x100,0x55);memory.fill(DEST,0x100,0xcc);
            memory.fill(DATA1,0x50,0x7a);memory.fill(DATA2,0x20,0x7a);memory.fill(MULTIPLIER,4,0);
            memory.writeQword(S,RET);memory.writeDword(SOURCE+8,0xfedcba98);
            memory.writeDword(SOURCE+0x40,0x89abcdef);memory.writeByte(SOURCE+0x44,0xe7);
            memory.writeQword(SOURCE+0x10,DATA1);memory.writeDword(SOURCE+0x18,5);memory.writeDword(SOURCE+0x1c,firstCount);memory.writeQword(SOURCE+0x20,ALLOC1);
            memory.writeQword(SOURCE+0x28,DATA2);memory.writeDword(SOURCE+0x30,7);memory.writeDword(SOURCE+0x34,0);memory.writeQword(SOURCE+0x38,ALLOC2);
            memory.writeDword(DEST+0x40,0x13579bdf);memory.writeByte(DEST+0x44,0xa5);
            // Artificial RAM carries the parent-qualified held1.5f bits. Both selected paths read it zero times.
            memory.writeDword(MULTIPLIER,0x3fc00000);
            memory.accesses.clear();
        }

        QueueFp604Api.Outcome run(){
            var actualCalls=Element150WholePostState244.bind(memory,stages,
                    (site,cursor,end)->budgets.add(new BudgetEntry(site,cursor,end)),
                    frame->{
                        opaqueCalls.add(frame);
                        long target=frame.call().kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                                ?frame.call().targetBits():frame.call().targetBits()-frame.imageBaseBits();
                        return new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                                new QueueFp604Api.Snapshot(frame.childEntry(),target,frame.preDirectionFlagSet(),frame.preMxcsr()),0,frame.call().callSiteRva());
                    });
            Element150Fp643Api.Calls traced=frame->{
                frames.add(frame);
                QueueFp604Api.Outcome actual=actualCalls.invoke(frame);
                outcomes.add(actual);return actual;
            };
            var entry=new GovernmentCrtBoundary185Api.Entry(IMAGE,S,v(),n());
            return Element150FullState643.execute(new Element150Fp643Api.Input(entry,true,MXCSR),memory,traced);
        }
    }

    private static void assertFirstConstructorPrefix(Scenario s){
        check(s.memory.peek(DEST)==IMAGE+0x45648a0L&&s.memory.peekDword(DEST+8)==0xfedcba98,"actual643 vtable/tag initialization");
        check(s.memory.peek(DEST+0x10)==0&&s.memory.peek(DEST+0x18)==0&&s.memory.peek(DEST+0x20)==IMAGE+0x54de260L,"actual first header initialization retained");
        check(s.memory.count("w64",L,IMAGE+0x3729600L)==1,"actual643 first CALL owns exactly one push");
        check(s.memory.count("w32",DEST+0x1c,0)==1,"real715 different-allocator body writes its destination count once");
        check(s.memory.readsAt(MULTIPLIER)==0,"known held1.5f cell is not consumed on selected prefix");
        check(s.opaqueCalls.isEmpty(),"no unqualified opaque CALL reached");
    }

    private static void bothRealEmptyNormals(){
        Scenario s=new Scenario(0);QueueFp604Api.Outcome result=s.run();
        check(result instanceof QueueFp604Api.Normal,"actual643 and both actual whole bodies return Normal");
        check(s.frames.size()==2&&s.outcomes.size()==2,"both actual643 sites execute once");
        check(s.budgets.equals(List.of(new BudgetEntry(0x21a5050L,L,0),new BudgetEntry(0xb2eee0L,L,0))),"two actual whole entry budgets exactly once");
        check(s.stages.convert==0&&s.stages.multiply==0&&s.stages.truncate==0,"empty source paths perform no FP operation");
        var first=(QueueFp604Api.Normal)s.outcomes.get(0);var second=(QueueFp604Api.Normal)s.outcomes.get(1);
        check(first.base().normalReturn().volatileBits().equals(expectedV(DEST+0x10,IMAGE+0x54de260L,SOURCE+0x10,L-0x28,v().xmm0())),"full actual715 V includes its fresh source epilogue R11");
        check(second.base().normalReturn().volatileBits().equals(expectedV(DEST+0x28,IMAGE+0x54de268L,SOURCE+0x28,L-0x28,v().xmm0())),"full actual Move V retains actual715 R11");
        for(int i=0;i<2;i++){
            var normal=(QueueFp604Api.Normal)s.outcomes.get(i);var frame=s.frames.get(i);
            check(frame.childEntry().rspBits()==L&&frame.call().rspBits()==F,"actual643 child stack frame");
            check(normal.base().normalReturn().nonvolatileBits().equals(frame.call().nonvolatileBits()),"whole body freshly restores exact supplied N");
            check(normal.base().normalReturn().returnRipBits()==frame.returnRipBits()&&normal.base().normalReturn().callerRspBits()==F,"actual whole RET and callerSP");
            check(normal.base().postDirectionFlagSet()&&normal.postMxcsr()==MXCSR,"actual context keeps full DF/MXCSR carrier");
        }
        check(s.frames.get(1).preMxcsr()==first.postMxcsr()&&s.frames.get(1).directionFlagSet()==first.base().postDirectionFlagSet(),"actual first context post-state reaches second643 CALL");
        var normal=(QueueFp604Api.Normal)result;var nr=normal.base().normalReturn();
        check(nr.volatileBits().equals(expectedV(DEST,IMAGE+0x54de268L,SOURCE+0x28,L-0x28,v().xmm0())),"actual643 full tail V comes from both new whole contexts");
        check(nr.nonvolatileBits().equals(n())&&nr.returnRipBits()==RET&&nr.callerRspBits()==S+8,"actual643 final full N/RET/RSP");
        check(normal.base().postDirectionFlagSet()&&normal.postMxcsr()==MXCSR,"actual643 retains last actual whole DF/MXCSR");
        check(s.memory.peekDword(DEST+0x40)==0x89abcdef&&s.memory.peekByte(DEST+0x44)==0xe7,"actual643 trailer writes reached");
        check(s.memory.peek(DEST+0x28)==0&&s.memory.peek(DEST+0x30)==0&&s.memory.peek(DEST+0x38)==IMAGE+0x54de268L,"second empty destination header exact");
        check(s.memory.peek(SOURCE+0x10)==DATA1&&s.memory.peekDword(SOURCE+0x18)==5&&s.memory.peekDword(SOURCE+0x1c)==0&&s.memory.peek(SOURCE+0x20)==ALLOC1,"first source header retained");
        check(s.memory.peek(SOURCE+0x28)==DATA2&&s.memory.peekDword(SOURCE+0x30)==7&&s.memory.peekDword(SOURCE+0x34)==0&&s.memory.peek(SOURCE+0x38)==ALLOC2,"second source header retained");
        check(s.memory.count("w32",SOURCE+0x1c,0)==1&&s.memory.count("w32",SOURCE+0x34,0)==1,"both actual whole source-clear stores once");
        check(s.memory.count("w64",L,IMAGE+0x3729625L)==1&&s.memory.count("r64",L,IMAGE+0x3729600L)==1
                &&s.memory.count("r64",L,IMAGE+0x3729625L)==1&&s.memory.count("r64",S,RET)==1,"all reached true RET push/read counts");
        assertFirstConstructorPrefix(s);
    }

    private static void firstRealGrowthMissingPostState(){
        Scenario s=new Scenario(1);QueueFp604Api.Outcome result=s.run();
        check(result==s.stages.stopped&&result instanceof QueueFp604Api.Stopped,"actual243 Stopped identity survives actual715 context/binder/643");
        check(s.frames.size()==1&&s.outcomes.size()==1&&s.outcomes.get(0)==result,"second actual643 B2 port is not executed");
        check(s.budgets.equals(List.of(new BudgetEntry(0x21a5050L,L,0))),"only first actual whole entry budget");
        check(s.stages.convert==1&&s.stages.multiply==0&&s.stages.truncate==0,"actual growth stops at first source SSE instruction");
        var stopped=(QueueFp604Api.Stopped)result;var snapshot=stopped.snapshot();
        check(stopped.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE&&stopped.raisedConditionBits()==0&&stopped.originCallSiteRva()==0x37295fbL,"truthful missing actual FP post-state");
        check(snapshot==s.stages.before.before()&&snapshot.instructionRva()==0x21a5192L,"actual provider snapshot identity and current instruction");
        check(snapshot.currentState().rspBits()==L-0x478&&snapshot.currentState().imageBaseBits()==IMAGE,"stopped snapshot is current715 prologue frame");
        check(snapshot.currentState().volatileBits().equals(expectedV(0,IMAGE+0x54de260L,SOURCE+0x10,v().r11Bits(),new Bits128(0,0))),"actual MOVD/current V preserved before unexecuted conversion");
        NonvolatileBits expectedN=new NonvolatileBits(DATA1,0,DEST+0x10,DATA1+0x10,n().r12Bits(),n().r13Bits(),SOURCE+0x10,1,n().xmm6());
        check(snapshot.currentState().nonvolatileBits().equals(expectedN),"actual715 current N is not repaired outer entry N");
        check(snapshot.directionFlagSet()&&snapshot.mxcsr()==MXCSR,"unexecuted source stage keeps actual input DF/MXCSR knowledge");
        check(s.memory.peekDword(SOURCE+0x1c)==1&&s.memory.count("w32",SOURCE+0x1c,0)==0,"unreached715 source-clear suffix absent");
        check(s.memory.peek(DEST+0x28)==0xccccccccccccccccL&&s.memory.peekDword(DEST+0x40)==0x13579bdf&&s.memory.peekByte(DEST+0x44)==0xa5,"second header and643 trailer remain untouched");
        check(s.memory.count("w64",L,IMAGE+0x3729625L)==0&&s.memory.count("r64",L,IMAGE+0x3729600L)==0&&s.memory.count("r64",S,RET)==0,"Stopped adds no second CALL or fabricated epilogue RET");
        assertFirstConstructorPrefix(s);
    }

    public static void main(String[] args){
        String[] selected=args.length==0?new String[]{"bothRealEmptyNormals","firstRealGrowthMissingPostState"}:args;
        for(String name:selected)switch(name){
            case "bothRealEmptyNormals" -> bothRealEmptyNormals();
            case "firstRealGrowthMissingPostState" -> firstRealGrowthMissingPostState();
            default -> throw new IllegalArgumentException("unknown new scene "+name);
        }
        System.out.println("PASS actual150whole244 "+selected.length+" new actual whole-body consumer scenes/"+checks
                +" checks; explicit missing FP/opaque ports; no Native/hardware/Root/natural credit");
    }
}

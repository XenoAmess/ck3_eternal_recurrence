package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture647.check;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture647.e;

/** Owner fallback after the first model cohort; literal source refinement predates this Java.
 * Original private oracle is retained. No model fixture/code or647 implementation is reused.
 * Represented software prefix only; no Native/OS/hardware/runtime acceptance. */
public final class ParentRevivedMoveStop647 {
    private ParentRevivedMoveStop647() { }
    private static final long I=0x140000000L,P=0x70004008L;
    private static final long DC=0x8000000000011000L,SC=0xf000000000022000L;
    private static final long OLD=0x8000000000001100L,SE=0xf000000000002200L,NEW=0x8000000000040000L;
    private static final long CT=0x9000000000004000L,CA=0x800000000000aaaaL;
    private static final long AO=0x9000000000010000L,AP=0xf00000000000cafeL;
    private static final long RIP=I+0x123456L,POISON=0x1122334455667788L;
    private static final QueueFp604Api.Mxcsr F0=QueueFp604Api.Mxcsr.exact(0x1f80);
    private static final QueueFp604Api.Mxcsr CF1=new QueueFp604Api.Mxcsr(8,12);
    private static final QueueFp604Api.Mxcsr AF=new QueueFp604Api.Mxcsr(0x80,0xc0);

    private static Bits128 x(long a) {return new Bits128(a,~a);}
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9) {
        return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));
    }
    private static VolatileBits rootV() {return bank(0x1000,0x111,DC,SC,0x114,0x115);}
    private static VolatileBits clearV() {return bank(0x1000,CT,OLD,0,0x114,0x115);}
    private static VolatileBits clearOfferV() {return bank(0x3000,0x3001,0x3002,0x3003,0x3004,0x3005);}
    private static VolatileBits allocatorV() {return bank(0x3000,2,AO,0x90,8,AP);}
    private static VolatileBits allocatorOfferV() {return bank(0x5000,NEW,0x5002,0x5003,0x5004,0x5005);}
    private static VolatileBits moveV() {return bank(0x5000,NEW,NEW,OLD,0x5004,0x5005);}
    private static VolatileBits firstLowerV() {return bank(0x5000,I+0x54de260L,NEW+0x10,OLD+0x10,0x5004,0x5005);}
    private static NonvolatileBits rootN() {return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109));}
    private static NonvolatileBits parentN() {return new NonvolatileBits(2,SE,DC,0x104,0x105,0x106,0x107,0x108,x(0x109));}
    private static NonvolatileBits clearN() {return new NonvolatileBits(OLD,SE,DC,1,0x105,0x106,0x107,0x108,x(0x109));}
    private static NonvolatileBits moveN() {return new NonvolatileBits(2,SE,DC,NEW,NEW,0x106,1,OLD,x(0x109));}
    private static NonvolatileBits lowerN() {return new NonvolatileBits(OLD,SE,0,NEW,NEW,0x106,1,OLD,x(0x109));}

    private static EmbeddedElements578Api.CallFrame parentFrame(long site,long target,int length,
            GovernmentCrtBoundary185Api.TargetKind kind,VolatileBits v,NonvolatileBits n,boolean df) {
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,P-0x48,v,n);
        return new EmbeddedElements578Api.CallFrame(call,
                new GovernmentCrtBoundary185Api.Entry(I,P-0x50,v,n),df,length,I+site+length);
    }
    private static EmbeddedClear587Api.CallFrame clearFrame() {
        var call=new GovernmentCrtBoundary185Api.Call(0x8897a8L,
                GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,CA,P-0x78,clearV(),clearN());
        return new EmbeddedClear587Api.CallFrame(call,
                new GovernmentCrtBoundary185Api.Entry(I,P-0x80,clearV(),clearN()),true,2,I+0x8897aaL);
    }
    private static Element150Fp643Api.CallFrame firstLowerFrame() {
        var call=new GovernmentCrtBoundary185Api.Call(0x37295fbL,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x21a5050L,P-0x78,firstLowerV(),lowerN());
        return new Element150Fp643Api.CallFrame(call,
                new GovernmentCrtBoundary185Api.Entry(I,P-0x80,firstLowerV(),lowerN()),true,AF,5,I+0x3729600L);
    }

    private static void assertParent(EmbeddedElementsFp637.CallFrame actual,
            EmbeddedElements578Api.CallFrame wanted,QueueFp604Api.Mxcsr fp,ParentFixture647.Ram ram) {
        check(actual.original().equals(wanted),"full original parent CALL/Entry/DF/length/RIP");
        check(actual.preMxcsr()==fp,"actual current parent MXCSR object");
        check(ram.peek(P-0x50,8)==wanted.returnRipBits(),"actual parent CALL return-address write");
    }
    private static QueueFp604Api.Normal normal(VolatileBits v,long rip,long sp,
            NonvolatileBits n,boolean df,QueueFp604Api.Mxcsr fp) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df),fp);
    }
    private static void fill(ParentFixture647.Ram ram,long p,int count,int value) {
        for(int j=0;j<count;j++)ram.seed(p+j,1,value);
    }
    private static void seed(ParentFixture647.Ram ram) {
        fill(ram,0x0000000070003e08L,592,90);
        fill(ram,0x8000000000011000L,24,204);
        fill(ram,0xf000000000022000L,24,204);
        fill(ram,0x8000000000001100L,72,204);
        fill(ram,0xf000000000002200L,72,204);
        fill(ram,0x8000000000040000L,72,204);
        ram.seed(0x0000000070004008L,8,0x0000000140123456L);
        ram.seed(0x8000000000011000L,8,0x8000000000001100L);
        ram.seed(0x8000000000011008L,4,0x0000000000000000L);
        ram.seed(0x800000000001100cL,4,0x0000000000000001L);
        ram.seed(0x8000000000011010L,8,0x9000000000010000L);
        ram.seed(0xf000000000022000L,8,0xf000000000002200L);
        ram.seed(0xf00000000002200cL,4,0x0000000000000001L);
        ram.seed(0x8000000000001100L,8,0x9000000000004000L);
        ram.seed(0x8000000000001108L,4,0x0000000076543210L);
        ram.seed(0x8000000000001140L,4,0x0000000055667788L);
        ram.seed(0x8000000000001144L,1,0x0000000000000099L);
        ram.seed(0x9000000000004000L,8,0x800000000000aaaaL);
        ram.seed(0xf000000000006000L,8,0x900000000000ccccL);
        ram.seed(0x8000000000007000L,8,0x800000000000ddddL);
        ram.seed(0x9000000000010000L,8,0x8000000000020000L);
        ram.seed(0x8000000000020008L,8,0xf00000000000cafeL);
        ram.seed(0x0000000000007700L,1,0x00000000000000ccL);
        ram.seed(0x0000000000007710L,1,0x00000000000000ccL);
        ram.seed(0x0000000000007720L,1,0x00000000000000ccL);
        ram.seed(0x0000000000007770L,1,0x00000000000000ccL);
        ram.seed(0xf000000000002208L,4,0x0000000076543210L);
        ram.seed(0xf000000000002210L,8,0x0000000000004000L);
        ram.seed(0xf00000000000221cL,4,0x0000000000000002L);
        ram.seed(0xf000000000002228L,8,0x0000000000005000L);
        ram.seed(0xf000000000002234L,4,0x0000000000000003L);
        ram.seed(0xf000000000002240L,4,0x0000000055667788L);
        ram.seed(0xf000000000002244L,1,0x0000000000000099L);
        ram.seed(0x8000000000011008L,4,0x0000000000000001L);
        ram.seed(0xf00000000002200cL,4,0x0000000000000002L);
    }
    private static List<ParentFixture647.Event> literalEvents() {
        return List.of(
            e("W64",0x0000000070004010L,0x0000000000000101L),
            e("W64",0x0000000070004018L,0x0000000000000102L),
            e("W64",0x0000000070004020L,0x0000000000000103L),
            e("W64",0x0000000070004028L,0x0000000000000104L),
            e("W64",0x0000000070004000L,0x0000000000000105L),
            e("W64",0x0000000070003ff8L,0x0000000000000107L),
            e("W64",0x0000000070003ff0L,0x0000000000000108L),
            e("R32",0xf00000000002200cL,0x0000000000000002L),
            e("R64",0xf000000000022000L,0xf000000000002200L),
            e("W64",0x0000000070003fb8L,0x00000001437282e6L),
            e("CALL_PARENT",0x00000000037282e1L,0x0000000000889780L),
            e("W64",0x0000000070003fc8L,0x8000000000011000L),
            e("W64",0x0000000070003fb0L,0x0000000000000104L),
            e("R32",0x800000000001100cL,0x0000000000000001L),
            e("W64",0x0000000070003fc0L,0x0000000000000002L),
            e("R64",0x8000000000011000L,0x8000000000001100L),
            e("BUDGET",0x00000000008897a0L,0x8000000000001100L),
            e("R64",0x8000000000001100L,0x9000000000004000L),
            e("R64",0x9000000000004000L,0x800000000000aaaaL),
            e("W64",0x0000000070003f88L,0x00000001408897aaL),
            e("CALL_CLEAR",0x00000000008897a8L,0x800000000000aaaaL),
            e("W8",0x0000000000007700L,0x0000000000000011L),
            e("R64",0x0000000070003fc0L,0x0000000000000002L),
            e("W32",0x800000000001100cL,0x0000000000000000L),
            e("R64",0x0000000070003fc8L,0x8000000000011000L),
            e("R64",0x0000000070003fb0L,0x0000000000000104L),
            e("R64",0x0000000070003fb8L,0x00000001437282e6L),
            e("R32",0x800000000001100cL,0x0000000000000000L),
            e("R32",0x8000000000011008L,0x0000000000000001L),
            e("R64",0x8000000000011010L,0x9000000000010000L),
            e("R64",0x9000000000010000L,0x8000000000020000L),
            e("R64",0x8000000000020008L,0xf00000000000cafeL),
            e("W64",0x0000000070003fb8L,0x0000000143728319L),
            e("CALL_PARENT",0x0000000003728316L,0xf00000000000cafeL),
            e("W8",0x0000000000007710L,0x0000000000000044L),
            e("W32",0x800000000001100cL,0x0000000000000001L),
            e("R32",0x800000000001100cL,0x0000000000000001L),
            e("R64",0x8000000000011000L,0x8000000000001100L),
            e("W64",0x0000000070003fe0L,0x8000000000040000L),
            e("W64",0x0000000070003fe8L,0x8000000000040000L),
            e("BUDGET",0x0000000003728335L,0x8000000000001100L),
            e("W64",0x0000000070003fb8L,0x0000000143728340L),
            e("CALL_PARENT",0x000000000372833bL,0x00000000037295b0L),
            e("W64",0x0000000070003fd0L,0x0000000000000002L),
            e("W64",0x0000000070003fd8L,0x8000000000011000L),
            e("W64",0x0000000070003fc0L,0x8000000000040000L),
            e("W64",0x0000000070003fb0L,0x8000000000040000L),
            e("W64",0x8000000000040000L,0x00000001445648a0L),
            e("R32",0x8000000000001108L,0x0000000076543210L),
            e("W32",0x8000000000040008L,0x0000000076543210L),
            e("W64",0x0000000070003fc8L,0x8000000000040010L),
            e("W64",0x8000000000040010L,0x0000000000000000L),
            e("W64",0x8000000000040018L,0x0000000000000000L),
            e("W64",0x8000000000040020L,0x00000001454de260L),
            e("W64",0x0000000070003f88L,0x0000000143729600L),
            e("CALL_150",0x00000000037295fbL,0x00000000021a5050L),
            e("W8",0x0000000000007720L,0x0000000000000055L));
    }
    private static Map<Long,Byte> expectedRam(Map<Long,Byte> initial,List<ParentFixture647.Event> trace) {
        var want=new HashMap<Long,Byte>(initial);
        for(var event:trace) {
            int width=switch(event.kind()) {case "W64"->8;case "W32"->4;case "W8"->1;default->0;};
            for(int j=0;j<width;j++)want.put(event.address()+j,(byte)(event.a()>>>(8*j)));
        }
        return want;
    }
    private static void compare(ParentFixture647.Ram ram,List<ParentFixture647.Event> trace,Map<Long,Byte> want) {
        if(!ram.events.equals(trace)) {
            int j=0;while(j<ram.events.size()&&j<trace.size()&&ram.events.get(j).equals(trace.get(j)))j++;
            throw new AssertionError("647 literal cursor "+j+" actual="+(j<ram.events.size()?ram.events.get(j):"END")+
                    " expected="+(j<trace.size()?trace.get(j):"END"));
        }
        check(ram.bytes.equals(want),"complete original owned RAM plus only literal prefix writes/padding");
    }
    public static void realClearThenRevivedCountMoveStopped() {
        var ram=new ParentFixture647.Ram();seed(ram);
        var initial=new HashMap<Long,Byte>(ram.bytes);
        var trace=literalEvents();var want=expectedRam(initial,trace);
        GovernmentCrtBoundary185Api.LoopBudget budget=ram::step;
        var input=new QueueFp604Api.Input(new FullCopy437Api.Input(
                new GovernmentCrtBoundary185Api.Entry(I,P,rootV(),rootN()),true,budget),F0);
        var rootClear=parentFrame(0x37282e1L,0x889780L,5,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,rootV(),parentN(),true);
        var rootAllocator=parentFrame(0x3728316L,AP,3,
                GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,allocatorV(),parentN(),false);
        var rootMove=parentFrame(0x372833bL,0x37295b0L,5,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,moveV(),moveN(),true);
        var lowerFirst=firstLowerFrame();
        QueueFp604Api.Normal clearNormal=normal(clearOfferV(),I+0x8897aaL,P-0x78,clearN(),false,CF1);
        QueueFp604Api.Normal allocatorNormal=normal(allocatorOfferV(),I+0x3728319L,P-0x48,parentN(),true,AF);
        int[] reached={0,0,0,0}; // parent, actual clear virtual, allocator, actual150 lower
        EmbeddedElementsFp637.CallFrame[] activeParent={null};
        QueueFp604Api.Stopped offeredStop=new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(
                        I,P-0x80,firstLowerV(),lowerN()),0x21a5050L,true,AF),0,0x37295fbL);
        QueueFp604Api.Outcome[] selectedOutcome={null};
        EmbeddedClearFp645Api.Calls clearCalls=frame->{
            check(++reached[1]==1,"one real clear virtual CALL");
            check(frame.original().equals(clearFrame())&&frame.preMxcsr()==F0,"complete clear virtual frame/current FP");
            check(ram.peek(P-0x80,8)==I+0x8897aaL,"actual clear lower CALL push");
            ram.events.add(e("CALL_CLEAR",0x8897a8L,CA));
            ram.writeByte(0x7700,0x11);
            return clearNormal;
        };
        EmbeddedElementsFp637.Calls foreignParent=frame->{
            check(++reached[2]==1&&frame==activeParent[0],"one identical foreign allocator frame");
            assertParent(frame,rootAllocator,CF1,ram);
            check(ram.peek(DC+0xc,4)==0,"real known clear already wrote zero before allocator revival");
            ram.writeByte(0x7710,0x44);
            ram.writeDword(DC+0xc,1); // explicit shared-RAM effect, never a nonvolatile-register substitute
            return allocatorNormal;
        };
        Element150Fp643Api.Calls constructCalls=frame->{
            check(++reached[3]==1,"D stops at FIRST actual150 lower; no second lower");
            check(frame.equals(lowerFirst)&&frame.preMxcsr()==AF,"complete first150 lower frame/DF/current FP");
            check(ram.peek(P-0x80,8)==I+0x3729600L,"actual first150 CALL push");
            ram.events.add(e("CALL_150",0x37295fbL,0x21a5050L));
            ram.writeByte(0x7720,0x55);
            return offeredStop;
        };
        Range16Fp638Api.Calls rangeCalls=frame->{throw new AssertionError("no parent172/range after terminal150 prefix");};
        Add4Fp639Api.Calls addCalls=frame->{throw new AssertionError("no Add4 after terminal150 prefix");};
        FullCopyWithFp613.TailCalls tails=frame->{throw new AssertionError("no COPY tail after terminal150 prefix");};
        EmbeddedElementsFp637.Calls bound=EmbeddedElementsAllKnown647.bind(
                ram,budget,rangeCalls,tails,addCalls,constructCalls,clearCalls,foreignParent);
        check(ram.events.isEmpty()&&ram.bytes.equals(initial),"new factory performs no RAM/CALL/budget actions");
        EmbeddedElementsFp637.Calls observed=frame->{
            int index=reached[0]++;activeParent[0]=frame;
            if(index==0)assertParent(frame,rootClear,F0,ram);
            else if(index==1)assertParent(frame,rootAllocator,CF1,ram);
            else if(index==2)assertParent(frame,rootMove,AF,ram);
            else throw new AssertionError("no DBDB80/172/destruct/later parent CALL");
            ram.events.add(e("CALL_PARENT",frame.original().call().callSiteRva(),frame.original().call().targetBits()));
            QueueFp604Api.Outcome result=bound.invoke(frame);
            if(index==2)selectedOutcome[0]=result;
            return result;
        };
        QueueFp604Api.Outcome result=EmbeddedElementsFp637.execute(input,ram,observed);
        check(result==offeredStop&&selectedOutcome[0]==offeredStop,"same precreated Stopped through known643/644/645 and outer637");
        check(offeredStop.snapshot().currentState().equals(lowerFirst.childEntry())
                &&offeredStop.snapshot().mxcsr()==AF&&offeredStop.snapshot().directionFlagSet(),
                "complete explicit stop entry/DF/FP without invented native poststate");
        check(reached[0]==3&&reached[1]==1&&reached[2]==1&&reached[3]==1,"exact reached parent/clear/allocator/150 counts");
        compare(ram,trace,want);
        check(ram.peek(DC+0xc,4)==1&&ram.peek(DC+8,4)==1&&ram.peek(SC+0xc,4)==2,
                "clear0 then explicit allocator1 preserved; source2/cap1 not old preserved-count scenario");
        check(ram.peek(P,8)==RIP,"root RET remains unchanged and unexecuted");
        check(ram.peek(NEW+0x28,8)==0xccccccccccccccccL&&ram.peek(NEW+0x40,4)==0xccccccccL,
                "no second150 header or final fields after FIRST lower Stop");
    }
    public static int verify() {realClearThenRevivedCountMoveStopped();return 1;}
    public static void main(String[] args) {System.out.println(verify());}
}

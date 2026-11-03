package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture647.*;

/** Owner100 fallback after R1 review. Exact literal private source-oracle lineage is frozen
 * in OWNER-FALLBACK-LITERAL647-BCF.json. No model Java or target-produced state is adopted. */
public final class ParentClearSecondStop647 {
    private ParentClearSecondStop647() { }
    private static final long I=0x0000000140000000L,P=0x0000000070004008L;
    private static final long D=0x8000000000011000L,S=0xF000000000022000L;
    private static final long E=0x8000000000001100L,E1=0x8000000000001148L;
    private static final long T1NEW=0x8000000000007000L,A1=0xF00000000000BBBBL;
    private static final QueueFp604Api.Mxcsr F0=QueueFp604Api.Mxcsr.exact(0x1F80);
    private static final QueueFp604Api.Mxcsr CF1=new QueueFp604Api.Mxcsr(8,12);
    private static final QueueFp604Api.Mxcsr CF2=new QueueFp604Api.Mxcsr(0x40,0xC0);
    private static VolatileBits rootV(){return new VolatileBits(0x0000000000000111L,0x8000000000011000L,0xF000000000022000L,0x0000000000000114L,0x0000000000000115L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001000L,0xFFFFFFFFFFFFEFFFL),new Bits128(0x0000000000001001L,0xFFFFFFFFFFFFEFFEL),new Bits128(0x0000000000001002L,0xFFFFFFFFFFFFEFFDL),new Bits128(0x0000000000001003L,0xFFFFFFFFFFFFEFFCL),new Bits128(0x0000000000001004L,0xFFFFFFFFFFFFEFFBL),new Bits128(0x0000000000001005L,0xFFFFFFFFFFFFEFFAL));}
    private static NonvolatileBits rootN(){return new NonvolatileBits(0x0000000000000101L,0x0000000000000102L,0x0000000000000103L,0x0000000000000104L,0x0000000000000105L,0x0000000000000106L,0x0000000000000107L,0x0000000000000108L,new Bits128(0x0000000000000109L,0xFFFFFFFFFFFFFEF6L));}
    private static VolatileBits firstV(){return new VolatileBits(0x9000000000004000L,0x8000000000001100L,0x0000000000000000L,0x0000000000000114L,0x0000000000000115L,0x000000000000100AL,0x000000000000100BL,new Bits128(0x0000000000001000L,0xFFFFFFFFFFFFEFFFL),new Bits128(0x0000000000001001L,0xFFFFFFFFFFFFEFFEL),new Bits128(0x0000000000001002L,0xFFFFFFFFFFFFEFFDL),new Bits128(0x0000000000001003L,0xFFFFFFFFFFFFEFFCL),new Bits128(0x0000000000001004L,0xFFFFFFFFFFFFEFFBL),new Bits128(0x0000000000001005L,0xFFFFFFFFFFFFEFFAL));}
    private static NonvolatileBits firstN(){return new NonvolatileBits(0x8000000000001100L,0xF000000000002200L,0x8000000000011000L,0x0000000000000002L,0x0000000000000105L,0x0000000000000106L,0x0000000000000107L,0x0000000000000108L,new Bits128(0x0000000000000109L,0xFFFFFFFFFFFFFEF6L));}
    private static VolatileBits offerC1(){return new VolatileBits(0x0000000000003001L,0x0000000000003002L,0x0000000000003003L,0x0000000000003004L,0x0000000000003005L,0x000000000000300AL,0x000000000000300BL,new Bits128(0x0000000000003000L,0xFFFFFFFFFFFFCFFFL),new Bits128(0x0000000000003001L,0xFFFFFFFFFFFFCFFEL),new Bits128(0x0000000000003002L,0xFFFFFFFFFFFFCFFDL),new Bits128(0x0000000000003003L,0xFFFFFFFFFFFFCFFCL),new Bits128(0x0000000000003004L,0xFFFFFFFFFFFFCFFBL),new Bits128(0x0000000000003005L,0xFFFFFFFFFFFFCFFAL));}
    private static VolatileBits offerC2(){return new VolatileBits(0x0000000000004001L,0x0000000000004002L,0x0000000000004003L,0x0000000000004004L,0x0000000000004005L,0x000000000000400AL,0x000000000000400BL,new Bits128(0x0000000000004000L,0xFFFFFFFFFFFFBFFFL),new Bits128(0x0000000000004001L,0xFFFFFFFFFFFFBFFEL),new Bits128(0x0000000000004002L,0xFFFFFFFFFFFFBFFDL),new Bits128(0x0000000000004003L,0xFFFFFFFFFFFFBFFCL),new Bits128(0x0000000000004004L,0xFFFFFFFFFFFFBFFBL),new Bits128(0x0000000000004005L,0xFFFFFFFFFFFFBFFAL));}
    private static VolatileBits secondV(){return new VolatileBits(0x8000000000007000L,0x8000000000001148L,0x0000000000000000L,0x0000000000003004L,0x0000000000003005L,0x000000000000300AL,0x000000000000300BL,new Bits128(0x0000000000003000L,0xFFFFFFFFFFFFCFFFL),new Bits128(0x0000000000003001L,0xFFFFFFFFFFFFCFFEL),new Bits128(0x0000000000003002L,0xFFFFFFFFFFFFCFFDL),new Bits128(0x0000000000003003L,0xFFFFFFFFFFFFCFFCL),new Bits128(0x0000000000003004L,0xFFFFFFFFFFFFCFFBL),new Bits128(0x0000000000003005L,0xFFFFFFFFFFFFCFFAL));}
    private static NonvolatileBits secondN(){return new NonvolatileBits(0x8000000000001148L,0xF000000000002200L,0x8000000000011000L,0x0000000000000001L,0x0000000000000105L,0x0000000000000106L,0x0000000000000107L,0x0000000000000108L,new Bits128(0x0000000000000109L,0xFFFFFFFFFFFFFEF6L));}
    private static void fill(Ram m,long address,int count,int value){
        for(int j=0;j<count;j++)m.seed(address+j,1,value);
    }
    private static Ram seed(){
        Ram m=new Ram();
        fill(m,0x0000000070003E08L,592,90);
        fill(m,0x8000000000011000L,24,204);
        fill(m,0xF000000000022000L,24,204);
        fill(m,0x8000000000001100L,144,204);
        fill(m,0xF000000000002200L,72,204);
        m.seed(0x0000000070004008L,8,0x0000000140123456L);
        m.seed(0x8000000000011000L,8,0x8000000000001100L);
        m.seed(0x8000000000011008L,4,0x0000000000000001L);
        m.seed(0x800000000001100CL,4,0x0000000000000002L);
        m.seed(0x8000000000011010L,8,0x9000000000010000L);
        m.seed(0xF000000000022000L,8,0xF000000000002200L);
        m.seed(0xF00000000002200CL,4,0x0000000000000001L);
        m.seed(0x8000000000001100L,8,0x9000000000004000L);
        m.seed(0x8000000000001108L,4,0x0000000076543210L);
        m.seed(0x8000000000001140L,4,0x0000000055667788L);
        m.seed(0x8000000000001144L,1,0x0000000000000099L);
        m.seed(0x8000000000001148L,8,0xF000000000006000L);
        m.seed(0x9000000000004000L,8,0x800000000000AAAAL);
        m.seed(0xF000000000006000L,8,0x900000000000CCCCL);
        m.seed(0x8000000000007000L,8,0x800000000000DDDDL);
        m.seed(0x9000000000010000L,8,0x8000000000020000L);
        m.seed(0x8000000000020008L,8,0xF00000000000CAFEL);
        m.seed(0x0000000000007700L,1,0x00000000000000CCL);
        m.seed(0x0000000000007710L,1,0x00000000000000CCL);
        m.seed(0x0000000000007720L,1,0x00000000000000CCL);
        m.seed(0x0000000000007770L,1,0x00000000000000CCL);
        m.seed(0xF000000000002208L,4,0x0000000076543210L);
        m.seed(0xF000000000002210L,8,0x0000000000004000L);
        m.seed(0xF00000000000221CL,4,0x0000000000000002L);
        m.seed(0xF000000000002228L,8,0x0000000000005000L);
        m.seed(0xF000000000002234L,4,0x0000000000000003L);
        m.seed(0xF000000000002240L,4,0x0000000055667788L);
        m.seed(0xF000000000002244L,1,0x0000000000000099L);
        return m;
    }
    private static List<Event> expectedEvents(){
        return List.of(
            e("W64",0x0000000070004010L,0x0000000000000101L),
            e("W64",0x0000000070004018L,0x0000000000000102L),
            e("W64",0x0000000070004020L,0x0000000000000103L),
            e("W64",0x0000000070004028L,0x0000000000000104L),
            e("W64",0x0000000070004000L,0x0000000000000105L),
            e("W64",0x0000000070003FF8L,0x0000000000000107L),
            e("W64",0x0000000070003FF0L,0x0000000000000108L),
            e("R32",0xF00000000002200CL,0x0000000000000001L),
            e("R64",0xF000000000022000L,0xF000000000002200L),
            e("W64",0x0000000070003FB8L,0x00000001437282E6L),
            e("W64",0x0000000070003FC8L,0x8000000000011000L),
            e("W64",0x0000000070003FB0L,0x0000000000000104L),
            e("R32",0x800000000001100CL,0x0000000000000002L),
            e("W64",0x0000000070003FC0L,0x0000000000000001L),
            e("R64",0x8000000000011000L,0x8000000000001100L),
            e("BUDGET",0x00000000008897A0L,0x8000000000001100L),
            e("R64",0x8000000000001100L,0x9000000000004000L),
            e("R64",0x9000000000004000L,0x800000000000AAAAL),
            e("W64",0x0000000070003F88L,0x00000001408897AAL),
            e("W8",0x0000000000007700L,0x0000000000000011L),
            e("W64",0x8000000000001148L,0x8000000000007000L),
            e("W64",0x8000000000007000L,0xF00000000000BBBBL),
            e("W32",0x800000000001100CL,0x0000000000000009L),
            e("BUDGET",0x00000000008897A0L,0x8000000000001148L),
            e("R64",0x8000000000001148L,0x8000000000007000L),
            e("R64",0x8000000000007000L,0xF00000000000BBBBL),
            e("W64",0x0000000070003F88L,0x00000001408897AAL),
            e("W8",0x0000000000007700L,0x0000000000000022L)
        );
    }
    private static void completeRamAndTrace(Ram m,Map<Long,Byte> initial){
        List<Event> expected=expectedEvents();
        check(m.events.equals(expected),"complete literal RAM/budget prefix: expected="+expected+" actual="+m.events);
        Map<Long,Byte> expectedRam=new HashMap<>(initial);
        for(Event event:expected){
            int width=switch(event.kind()){case "W64"->8;case "W32"->4;case "W8"->1;default->0;};
            for(int j=0;j<width;j++)expectedRam.put(event.address()+j,(byte)(event.a()>>>(8*j)));
        }
        check(m.bytes.equals(expectedRam),"every owned byte and untouched padding/stack equals source-literal writes");
    }
    private static void frame(GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,
            boolean df,QueueFp604Api.Mxcsr fp,int length,long rip,long site,
            GovernmentCrtBoundary185Api.TargetKind kind,long target,long pre,VolatileBits v,NonvolatileBits n,
            boolean wantedDf,QueueFp604Api.Mxcsr wantedFp,int wantedLength,String why){
        check(call.equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,pre,v,n)),why+" complete Call V/N/target/SP");
        check(child.equals(new GovernmentCrtBoundary185Api.Entry(I,pre-8,v,n)),why+" complete child Entry");
        check(df==wantedDf&&fp==wantedFp&&length==wantedLength&&rip==I+site+wantedLength,
                why+" exact DF/currentFP identity/length/returnRIP");
    }
    private static void parentFrame(EmbeddedElementsFp637.CallFrame wrapped){
        var f=wrapped.original();
        frame(f.call(),f.childEntry(),f.directionFlagSet(),wrapped.preMxcsr(),f.instructionLength(),f.returnRipBits(),
                0x37282E1,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x889780,P-0x48,
                rootV(),new NonvolatileBits(0x0000000000000001L,0xF000000000002200L,0x8000000000011000L,0x0000000000000104L,0x0000000000000105L,0x0000000000000106L,0x0000000000000107L,0x0000000000000108L,new Bits128(0x0000000000000109L,0xFFFFFFFFFFFFFEF6L)),true,F0,5,"parent knownclear");
    }
    private static void firstFrame(EmbeddedClearFp645Api.CallFrame wrapped){
        var f=wrapped.original();
        frame(f.call(),f.childEntry(),f.directionFlagSet(),wrapped.preMxcsr(),f.instructionLength(),f.returnRipBits(),
                0x8897A8,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x800000000000AAAAL,P-0x78,
                firstV(),firstN(),true,F0,2,"first actual93 destructor");
    }
    private static void secondFrame(EmbeddedClearFp645Api.CallFrame wrapped){
        var f=wrapped.original();
        frame(f.call(),f.childEntry(),f.directionFlagSet(),wrapped.preMxcsr(),f.instructionLength(),f.returnRipBits(),
                0x8897A8,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,A1,P-0x78,
                secondV(),secondN(),false,CF1,2,"second actual93 destructor current first poststate");
    }
    private static QueueFp604Api.Normal normal(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df,QueueFp604Api.Mxcsr fp){
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df),fp);
    }
    private static QueueFp604Api.Input input(GovernmentCrtBoundary185Api.LoopBudget budget){
        return new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,P,rootV(),rootN()),true,budget),F0);
    }
    public static void secondVirtualStoppedAfterFirstNormal(){
        Ram m=seed();Map<Long,Byte> initial=new HashMap<>(m.bytes);
        int[] parentSeen={0},clearSeen={0},budgetSeen={0};
        final QueueFp604Api.Normal firstOffer=normal(offerC1(),firstN(),I+0x8897AA,P-0x78,false,CF1);
        // Pre-created from independent literal second-frame state, not from an actual callback frame.
        final QueueFp604Api.Stopped expectedStop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                new QueueFp604Api.Snapshot(new GovernmentCrtBoundary185Api.Entry(I,0x0000000070003F88L,secondV(),secondN()),0x00000000008897A8L,false,CF1),0,0x00000000008897A8L);
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,cursor)->{
            int turn=++budgetSeen[0];
            check(turn<=2&&pc==0x8897A0L&&cursor==(turn==1?E:E1),"exact source loop budget and cursor");
            m.step(pc,cursor);

        };
        EmbeddedClearFp645Api.Calls clearCalls=f->{
            int turn=++clearSeen[0];
            if(turn==1){
                firstFrame(f);
                m.writeByte(0x7700,0x11);m.writeQword(E1,T1NEW);m.writeQword(T1NEW,A1);m.writeDword(D+0xC,9);
                return firstOffer;
            }
            check(turn==2,"only second actual destructor stops");secondFrame(f);m.writeByte(0x7700,0x22);return expectedStop;
        };
        var bound=EmbeddedElementsAllKnown647.bind(m,budget,
                f->{throw new AssertionError("Range16 forbidden in this source scenario");},
                f->{throw new AssertionError("COPY tail forbidden in this source scenario");},
                f->{throw new AssertionError("Add4 forbidden in this source scenario");},
                f->{throw new AssertionError("150 forbidden in this source scenario");},clearCalls,
                f->{throw new AssertionError("foreign parent/allocator forbidden in this source scenario");});
        EmbeddedElementsFp637.Calls checked=f->{
            parentFrame(f);check(++parentSeen[0]==1,"only parent cleanup CALL");
            var offered=bound.invoke(f);
            check(offered==expectedStop,"same pre-existing Stop through645 andNEW647");return offered;
        };
        var result=EmbeddedElementsFp637.execute(input(budget),m,checked);
        check(result==expectedStop,"same pre-existing Stop through whole637 privatecarrier");
        check(parentSeen[0]==1&&clearSeen[0]==2&&budgetSeen[0]==2,"firstNormal then SECOND actual destructor Stop");
        check(m.peek(D+0xC,4)==9,"callback count9 retained; no clearcount0 or parent continuation");
        completeRamAndTrace(m,initial);
    }
    public static int verify(){secondVirtualStoppedAfterFirstNormal();return 1;}
    public static void main(String[] args){System.out.println(verify());}
}

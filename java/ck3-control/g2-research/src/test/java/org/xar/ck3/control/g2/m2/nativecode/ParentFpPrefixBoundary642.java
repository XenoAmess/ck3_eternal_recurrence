package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture642.check;
import static org.xar.ck3.control.g2.m2.nativecode.ParentFixture642.e;

/** Owner literal whole-parent missing-controls witness, frozen before this source.
 * Unknown controls stop software admission before the seeded factor operand is read.
 * This is represented software state, not an OS/hardware exception or native acceptance. */
public final class ParentFpPrefixBoundary642 {
    private ParentFpPrefixBoundary642() { }
    private static final long I=0x140000000L,P=0x70001008L;
    private static final long ROOT_D=0x8000000000001100L,ROOT_S=0xf000000000002200L;
    private static final long D=0x30000L,S=0x40000L,B16=0x50000L,B4=0x60000L,MARK=0x61000L;
    private static final long A16=I+0x54de260L,FACTOR=I+0x49f64f0L;

    private static Bits128 x(long v) {return new Bits128(v,~v);}
    private static VolatileBits initialV() {
        return new VolatileBits(0x101,ROOT_D,ROOT_S,0x104,0x105,0x106,0x107,
                x(0x108),x(0x109),x(0x10a),x(0x10b),x(0x10c),x(0x10d));
    }
    private static NonvolatileBits initialN() {
        return new NonvolatileBits(0x201,0x202,0x203,0x204,0x205,0x206,0x207,0x208,x(0x209));
    }
    private static NonvolatileBits cleanupN() {
        return new NonvolatileBits(1,S,ROOT_D,0x204,0x205,0x206,0x207,0x208,x(0x209));
    }
    private static VolatileBits cleanupPostV() {
        return new VolatileBits(0x901,0x902,0x903,0x904,0x905,0x906,0x907,
                x(0x908),x(0x909),x(0x90a),x(0x90b),x(0x90c),x(0x90d));
    }
    private static VolatileBits parentChildV() {
        return new VolatileBits(0,D,S,0x904,0x905,0x906,0x907,
                x(0x908),x(0x909),x(0x90a),x(0x90b),x(0x90c),x(0x90d));
    }
    private static NonvolatileBits parentChildN() {
        return new NonvolatileBits(1,S,ROOT_D,D,0x205,0x206,0x207,0x208,x(0x209));
    }
    private static VolatileBits stoppedV() {
        return new VolatileBits(0,A16,0,8,B16+0x20,0x906,0x907,
                new Bits128(0,0),x(0x909),x(0x90a),x(0x90b),x(0x90c),x(0x90d));
    }
    private static NonvolatileBits stoppedN() {
        return new NonvolatileBits(B16,2,B16+0x20,D+0x10,0x205,2,0,2,x(0x209));
    }
    private static void fill(ParentFixture642.Ram ram,long address,int size,int salt) {
        for(int j=0;j<size;j++)ram.seed(address+j,1,(j*37+salt)&255);
    }
    private static void seed(ParentFixture642.Ram ram) {
        fill(ram,P-0x100,0x141,0x31);
        fill(ram,ROOT_D,0x40,0x41);fill(ram,ROOT_S,0x40,0x53);
        fill(ram,D,0x60,0x65);fill(ram,S,0x60,0x77);
        fill(ram,B16,0x30,0x89);fill(ram,B4,0x30,0x9b);
        fill(ram,MARK,8,0xad);fill(ram,A16,0x20,0xbf);fill(ram,FACTOR,8,0xd1);
        ram.seed(P,8,I+0x123456L);
        ram.seed(ROOT_D,8,D);ram.seed(ROOT_D+8,4,1);ram.seed(ROOT_D+0xc,4,0);
        ram.seed(ROOT_D+0x10,8,0xdeadbeefL);
        ram.seed(ROOT_S,8,S);ram.seed(ROOT_S+8,4,1);ram.seed(ROOT_S+0xc,4,1);
        ram.seed(S+8,4,0x87654321L);ram.seed(S+0x10,8,B16);ram.seed(S+0x1c,4,2);
        ram.seed(S+0x28,8,B4);ram.seed(S+0x34,4,3);
        ram.seed(FACTOR,4,0x7f800001L); // unread poison; not the reason for the admission stop
    }
    private static void checkFrame(EmbeddedElementsFp637.CallFrame fpFrame,long site,long target,
            long returnRva,VolatileBits v,NonvolatileBits n,boolean df,QueueFp604Api.Mxcsr fp,
            ParentFixture642.Ram ram) {
        EmbeddedElements578Api.CallFrame frame=fpFrame.original();
        var call=new GovernmentCrtBoundary185Api.Call(site,
                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,P-0x48,v,n);
        check(frame.call().equals(call),"complete parent CALL "+Long.toHexString(site));
        check(frame.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0x50,v,n)),
                "complete child Entry "+Long.toHexString(site));
        check(frame.instructionLength()==5&&frame.returnRipBits()==I+returnRva,
                "parent instruction/return RIP "+Long.toHexString(site));
        check(frame.directionFlagSet()==df,"parent pre-DF "+Long.toHexString(site));
        check(fpFrame.preMxcsr()==fp,"parent current MXCSR identity "+Long.toHexString(site));
        check(ram.peek(P-0x50,8)==I+returnRva,"actual parent return-address push");
    }
    private static List<ParentFixture642.Event> literalEvents() {
        return List.of(
            e("W64",P+8,0x201),e("W64",P+0x10,0x202),e("W64",P+0x18,0x203),e("W64",P+0x20,0x204),
            e("W64",P-8,0x205),e("W64",P-0x10,0x207),e("W64",P-0x18,0x208),
            e("R32",ROOT_S+0xc,1),e("R64",ROOT_S,S),e("W64",P-0x50,I+0x37282e6L),
            e("CALL",0x37282e1L,0x889780L),e("W32",MARK,0x12345678),
            e("R32",ROOT_D+0xc,0),e("R32",ROOT_D+8,1),e("W32",ROOT_D+0xc,1),e("R64",ROOT_D,D),
            e("BUDGET",0x37283b0L,S),e("W64",P-0x50,I+0x37283bbL),e("CALL",0x37283b6L,0x37297f0L),
            e("W64",P-0x48,1),e("W64",P-0x40,ROOT_D),e("W64",P-0x58,D),e("W64",D,I+0x45648a0L),
            e("R32",S+8,(int)0x87654321L),e("W32",D+8,(int)0x87654321L),
            e("W64",D+0x18,0),e("W64",D+0x20,0),e("W64",D+0x10,0),e("W64",D+0x18,0),e("W64",D+0x20,A16),
            e("R32",S+0x1c,2),e("R64",S+0x10,B16),e("W64",P-0x80,I+0x372984bL),
            e("W64",P-0x88,S),e("W64",P-0x90,0),e("W64",P-0x98,D),e("W64",P-0xa0,0x207),
            e("R32",D+0x1c,0),e("W64",P-0x78,S),e("R32",D+0x18,0),e("W64",P-0xa8,0x208),
            e("R64",D+0x20,A16),e("W64",P-0x70,0x205),e("W64",P-0x68,0x206));
    }
    private static Map<Long,Byte> literalFinalRam(Map<Long,Byte> initial,List<ParentFixture642.Event> trace) {
        Map<Long,Byte> expected=new HashMap<>(initial);
        for(var event:trace) {
            int width=event.kind().equals("W64")?8:event.kind().equals("W32")?4:0;
            for(int j=0;j<width;j++)expected.put(event.address()+j,(byte)(event.a()>>>(j*8)));
        }
        return expected;
    }
    public static int verify() {
        var ram=new ParentFixture642.Ram();seed(ram);
        Map<Long,Byte> initial=new HashMap<>(ram.bytes);
        List<ParentFixture642.Event> expectedTrace=literalEvents();
        Map<Long,Byte> expectedRam=literalFinalRam(initial,expectedTrace);
        QueueFp604Api.Mxcsr initialFp=QueueFp604Api.Mxcsr.exact(0x1f80);
        QueueFp604Api.Mxcsr unknown=QueueFp604Api.Mxcsr.unknown();
        GovernmentCrtBoundary185Api.LoopBudget budget=ram::step;
        QueueFp604Api.Input input=ParentFixture642.input(ROOT_D,ROOT_S,true,initialFp,budget);
        check(input.base().entry().equals(new GovernmentCrtBoundary185Api.Entry(I,P,initialV(),initialN())),
                "raw fixture input banks");
        check(input.mxcsr()==initialFp&&input.base().directionFlagSet()&&input.base().budget()==budget,
                "raw fixture FP/DF/budget identity");
        int[] calls={0,0,0,0}; // observed parent, foreign cleanup, forbidden range, forbidden add
        EmbeddedElementsFp637.CallFrame[] current={null};
        QueueFp604Api.Stopped[] captured={null};
        EmbeddedElementsFp637.Calls foreign=frame->{
            calls[1]++;
            check(frame==current[0],"foreign receives the exact parent wrapper frame");
            checkFrame(frame,0x37282e1L,0x889780L,0x37282e6L,initialV(),cleanupN(),true,initialFp,ram);
            ram.writeDword(MARK,0x12345678);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                    new GovernmentCrtBoundary185Api.NormalReturn(cleanupPostV(),I+0x37282e6L,P-0x48,cleanupN()),false),unknown);
        };
        Range16Fp638Api.Calls range=frame->{calls[2]++;throw new AssertionError("range opaque CALL after admission stop");};
        Add4Fp639Api.Calls add=frame->{calls[3]++;throw new AssertionError("add CALL after first lower stopped");};
        EmbeddedElementsFp637.Calls bound=EmbeddedElementsKnownLower642.bind(ram,budget,range,add,foreign);
        check(ram.events.isEmpty()&&ram.bytes.equals(initial),"factory has no RAM/access/budget effects");
        EmbeddedElementsFp637.Calls observed=frame->{
            current[0]=frame;
            long site=frame.original().call().callSiteRva();
            if(calls[0]==0) {
                checkFrame(frame,0x37282e1L,0x889780L,0x37282e6L,initialV(),cleanupN(),true,initialFp,ram);
            } else if(calls[0]==1) {
                checkFrame(frame,0x37283b6L,0x37297f0L,0x37283bbL,parentChildV(),parentChildN(),false,unknown,ram);
            } else throw new AssertionError("unexpected additional parent CALL");
            calls[0]++;
            ram.events.add(e("CALL",site,frame.original().call().targetBits()));
            QueueFp604Api.Outcome offered=bound.invoke(frame);
            if(site==0x37283b6L) {
                check(offered instanceof QueueFp604Api.Stopped,"selected child returns Stopped");
                captured[0]=(QueueFp604Api.Stopped)offered;
            } else {
                check(offered instanceof QueueFp604Api.Normal,"explicit cleanup normal offer");
                check(((QueueFp604Api.Normal)offered).postMxcsr()==unknown,"cleanup offer retained current FP identity");
            }
            return offered;
        };
        QueueFp604Api.Outcome outcome=EmbeddedElementsFp637.execute(input,ram,observed);
        check(outcome instanceof QueueFp604Api.Stopped,"whole parent does not complete normally");
        QueueFp604Api.Stopped stopped=(QueueFp604Api.Stopped)outcome;
        check(stopped==captured[0],"outer 637 private carrier returns exact captured child Stopped identity");
        check(stopped.reason()==QueueFp604Api.StopReason.MISSING_FP_INPUT,"software missing controls reason");
        check(stopped.originCallSiteRva()==0x3729846L&&stopped.raisedConditionBits()==0,"actual first lower origin/no condition raised");
        var snapshot=stopped.snapshot();
        check(snapshot.instructionRva()==0x8c7114L&&!snapshot.directionFlagSet(),"local MULSS PC/post-cleanup DF");
        check(snapshot.mxcsr()==unknown&&snapshot.mxcsr().knownMaskBits()==0&&snapshot.mxcsr().valueBits()==0,
                "unknown controls retained without defaulting or synthetic status flags");
        check(snapshot.currentState().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0xc8,stoppedV(),stoppedN())),
                "complete literal Range prefix V/N/RSP/image snapshot");
        check(calls[0]==2&&calls[1]==1&&calls[2]==0&&calls[3]==0,"only cleanup and first element parent CALL");
        check(ram.events.equals(expectedTrace),"44 literal ordered access/CALL/budget prefix events");
        check(ram.bytes.equals(expectedRam),"complete owned RAM equals only literal prefix writes; all padding retained");
        check(ram.peek(FACTOR,4)==0x7f800001L,"unread SNaN poison remains unchanged");
        check(ram.peek(ROOT_D+0xc,4)==1&&ram.peek(MARK,4)==0x12345678L,
                "parent count and explicit foreign side effect precede stop; no rollback");
        return 1;
    }
    public static void main(String[] args) {System.out.println(verify());}
}

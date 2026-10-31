package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.Ports;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Owner fixed literals from96B+65B ASM, no target runs used to construct expected values.
 * FullV and stack/global sideeffects are controlled ports, not real Windows effects. */
public final class GovernmentThreadFooter181Cases {
    private GovernmentThreadFooter181Cases() { }
    private static final long B=0x1_0000_0000L,E=0x7000_0008L,W=0x6FFF_FFE0L,G=0x4000_0000L;
    private static final long CS=0x1_05C5_CB18L,EPOCH=0x1_0542_F090L,INDEX=0x1_05C5_CBC4L;
    private static final long FN=0x1_05C5_CB48L,ARG=0x1_05C5_CB08L,HANDLE=0x1_05C5_CB10L;
    private static final long RET=0x1234_5678_7654_3210L,MANAGER_RET=0x1_03F8_A8A7L;
    private static int checks;
    private static void e(Object expected,Object actual,String message) {checks++;equal(expected,actual,message);}
    private record Setup(MemoryImage m,Entry entry) { }
    private record Step(IatCall frame,VolatileBits post,Runnable effect) { }
    private static Setup setup(int id) {
        MemoryImage m=new MemoryImage();long n=0x4000_0000_0000_0000L+id*0x100L;
        NonvolatileBits nv=new NonvolatileBits(n+1,n+2,n+3,n+4,n+5,n+6,n+7,n+8,vector(n+9));
        VolatileBits v=bits(0x2100+id*0x1000L,0x1210+id*0x1000L,G,0x3230+id*0x1000L);
        m.writeDword(G,-1);return new Setup(m,new Entry(B,E,v,nv));
    }
    private static NonvolatileBits rbx(NonvolatileBits n,long x) {return new NonvolatileBits(x,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long x8,long x9) {return new VolatileBits(a,c,d,x8,x9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static VolatileBits ac(VolatileBits v,long a,long c) {return change(v,a,c,v.rdxBits(),v.r8Bits(),v.r9Bits());}
    private static VolatileBits post(long seed) {return bits(seed,seed+0x101,seed+0x202,seed+0x303);}
    private static IatCall enter(Setup s) {VolatileBits v=s.entry().volatileBits();return new IatCall(0x4223A34L,0x43DA500L,W,false,ac(v,v.raxBits(),CS),rbx(s.entry().nonvolatileBits(),G));}
    private static IatCall leave(Setup s,VolatileBits en,long epoch,long index,long tls) {return new IatCall(0x4223A74L,0x43DA4F0L,W,false,change(en,epoch,CS,index,tls,0x10),rbx(s.entry().nonvolatileBits(),G));}

    private static final class Script implements Ports {
        private final List<Step> steps=new ArrayList<>();
        private final long gs;
        private final Runnable gsEffect;
        private final int expectedGs;
        private int index,gsReads;
        Script(long gs,int expectedGs,Runnable gsEffect) {this.gs=gs;this.expectedGs=expectedGs;this.gsEffect=gsEffect;}
        Script add(IatCall frame,VolatileBits post,Runnable effect) {steps.add(new Step(frame,post,effect));return this;}
        @Override public long readGsQword58() {gsReads++;if(gsReads>expectedGs)throw new AssertionError("unexpected GS read");gsEffect.run();return gs;}
        @Override public VolatileBits invokeIat(IatCall actual) {if(index==steps.size())throw new AssertionError("unexpected IAT frame");Step s=steps.get(index++);e(s.frame(),actual,"complete V/N IAT frame"+index);s.effect().run();return s.post();}
        @Override public VolatileBits invoke(OpaqueCall actual) {throw new AssertionError("concrete Notify must not use opaque direct tail "+actual);}
        void done() {e(steps.size(),index,"all exact ordered IAT frames");e(expectedGs,gsReads,"owned GS count");}
    }
    private static void entered(Setup s,long expectedRet) {
        e(s.entry().nonvolatileBits().rbxBits(),s.m().readQword(E-8),"actual saved incoming RBX");
        e(B+0x4223A3AL,s.m().readQword(W-8),"Enter actual CALL continuation");
        e(expectedRet,s.m().readQword(E),"original callee RET slot");
    }

    private static void adapterWrapFreshEpochCfg() {
        Setup s=setup(1);long gs=0x6000_0000L,tls=0x6000_1000L,fn=0x7777_0000L;
        s.m().writeDword(EPOCH,-1);s.m().writeDword(INDEX,0x8000_0001);
        s.m().writeQword(0x4_6000_0008L,tls);s.m().writeDword(tls+0xC,0xAABB_CCDD);s.m().writeDword(tls+0x10,0x0102_0304);s.m().writeDword(tls+0x14,0x1122_3344);s.m().writeQword(FN,fn);
        VolatileBits en=post(0xE110),lv=post(0xD110),out=post(0xC110);
        Script p=new Script(gs,1,()->{
            e(0,s.m().readDword(EPOCH),"FFFFFFFF epoch wrapped0 before GS callback");
            e(0,s.m().readDword(G),"guard received increment before callback");
            e(0x8000_0001,s.m().readDword(INDEX),"index loaded before GS callback");
            s.m().writeDword(EPOCH,0x8000_002A);s.m().writeDword(INDEX,3);
        }).add(enter(s),en,()->entered(s,MANAGER_RET))
          .add(leave(s,en,0x8000_002AL,0x8000_0001L,tls),lv,()->{
              e(B+0x4223A7AL,s.m().readQword(W-8),"Leave is second real CALL");
              e(0x8000_002A,s.m().readDword(tls+0x10),"fresh epoch after GS stored at old unsigned index TLS");
              e(0xAABB_CCDD,s.m().readDword(tls+0xC),"lower TLS padding");e(0x1122_3344,s.m().readDword(tls+0x14),"upper TLS padding");
          }).add(new IatCall(0x4223B07L,0x43DBBA8L,E,true,ac(lv,fn,ARG),s.entry().nonvolatileBits()),out,()->{
              e(B+0x4223A7AL,s.m().readQword(W-8),"Footer/Notify direct tails did not push");
              e(s.entry().nonvolatileBits().rbxBits(),s.m().readQword(E-8),"saved RBX slot unchanged by tails");e(MANAGER_RET,s.m().readQword(E),"same manager RET through both tails");
          });
        Calls unexpected=new Calls() {
            @Override public long readGsQword58() {throw new AssertionError("unexpected caller GS delegation");}
            @Override public VolatileBits invoke(OpaqueCall c) {throw new AssertionError("matched Footer escaped binder "+c);}
        };
        Calls bound=GovernmentThreadFooter181Calls.bind(B,s.m(),unexpected,p);
        VolatileBits actual=bound.invoke(new OpaqueCall(0x3F8A8A2L,0x4223A24L,E+8,s.entry().volatileBits(),s.entry().nonvolatileBits()));
        e(out,actual,"adapter returns actual complete tail V");e(0,s.m().readDword(G),"guard retains increment0");
        e(0x8000_002A,s.m().readDword(EPOCH),"GS mutation retained fresh global epoch");e(3,s.m().readDword(INDEX),"global index mutation retained");p.done();
    }

    private static void directSignedBoundaryFreshHandleAndPop() {
        Setup s=setup(2);long gs=0x6000_0000L,tls=0x6000_2000L,h1=0x8100_1000L,h2=0x8100_2000L;
        long saved=0xA201_A202_A203_A204L,retAfterSet=0xB201_B202_B203_B204L,retAfterReset=0xB211_B212_B213_B214L;
        s.m().writeQword(E,RET);s.m().writeDword(EPOCH,0x7FFF_FFFF);s.m().writeDword(INDEX,2);
        s.m().writeQword(gs+16,tls);s.m().writeDword(tls+0x10,0x0102_0304);s.m().writeQword(FN,0);s.m().writeQword(HANDLE,h1);
        VolatileBits en=post(0xE210),lv=post(0xD210),se=post(0xA210),out=post(0xC210);
        NonvolatileBits restored=rbx(s.entry().nonvolatileBits(),saved);
        Script p=new Script(gs,1,()->{
            e(0x8000_0000,s.m().readDword(EPOCH),"7FFFFFFF raw INC wraps to80000000");e(0x8000_0000,s.m().readDword(G),"signed-boundary guard store");
        }).add(enter(s),en,()->entered(s,RET))
          .add(leave(s,en,0x8000_0000L,2,tls),lv,()->{
              e(B+0x4223A7AL,s.m().readQword(W-8),"Leave actual CALL push");s.m().writeQword(E-8,saved);
          }).add(new IatCall(0x4223B15L,0x43DA5B0L,W,false,ac(lv,0,h1),restored),se,()->{
              e(B+0x4223B1BL,s.m().readQword(W-8),"SetEvent actual CALL push");e(saved,s.m().readQword(E-8),"actual RBX pop precedes Notify");
              s.m().writeQword(HANDLE,h2);s.m().writeQword(E,retAfterSet);
          }).add(new IatCall(0x4223B26L,0x43DA4A8L,E,true,ac(se,se.raxBits(),h2),restored),out,()->{
              e(B+0x4223B1BL,s.m().readQword(W-8),"ResetEvent tail does not push new continuation");
              e(saved,s.m().readQword(E-8),"ResetEvent tail preserves saved slot");e(retAfterSet,s.m().readQword(E),"fresh original RET after SetEvent script");s.m().writeQword(E,retAfterReset);
          });
        NormalReturn actual=GovernmentThreadFooter181.execute(s.entry(),s.m(),p);
        e(new NormalReturn(out,restored,retAfterReset,E+8),actual,"fullV/N and actual post-tail RET");
        e(0x8000_0000,s.m().readDword(tls+0x10),"exact signed-boundary TLS DWORD");e(h2,s.m().readQword(HANDLE),"fresh mutated handle remains");p.done();
    }

    private static void foreignPairsAndGsDelegate() {
        MemoryImage m=new MemoryImage();NonvolatileBits n=setup(3).entry().nonvolatileBits();VolatileBits v=post(0xE310),out=post(0xC310);
        List<OpaqueCall> expected=List.of(new OpaqueCall(0x3F8A813L,0x4223A24L,E+8,v,n),new OpaqueCall(0x3F8A8A2L,0x4223A84L,E+8,v,n));
        int[] calls={0},gs={0};Script ports=new Script(0,0,()->{});
        Calls delegate=new Calls() {
            @Override public long readGsQword58() {gs[0]++;return 0x8888L;}
            @Override public VolatileBits invoke(OpaqueCall actual) {e(expected.get(calls[0]++),actual,"unmatched exact call forwarded");return out;}
        };
        Calls bound=GovernmentThreadFooter181Calls.bind(B,m,delegate,ports);
        for(OpaqueCall call:expected)e(out,bound.invoke(call),"foreign pair returns delegate fullV");
        e(0x8888L,bound.readGsQword58(),"caller GS delegates unchanged");e(2,calls[0],"two foreign pairs");e(1,gs[0],"one forwarded GS read");ports.done();
    }
    public static int runAll() {checks=0;adapterWrapFreshEpochCfg();directSignedBoundaryFreshHandleAndPop();foreignPairsAndGsDelegate();return checks;}
}

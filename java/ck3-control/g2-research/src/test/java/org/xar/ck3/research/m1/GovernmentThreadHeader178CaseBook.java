package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.Ports;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.WaitBudget;
import org.xar.ck3.research.m5.GovernmentCallee164Api.Entry;
import org.xar.ck3.research.m5.GovernmentCallee164Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.equal;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Independent owner literals from103B ASM, after two model outputs were rejected.
 * Scripted fullV and stack sideeffects are controlled ports, never observed Windows behavior. */
public final class GovernmentThreadHeader178CaseBook {
    private GovernmentThreadHeader178CaseBook() { }
    private static final long B=0x1_0000_0000L,E=0x7000_0008L,W=0x6FFF_FFE0L,G=0x4000_0000L;
    private static final long CS=0x1_05C5_CB18L,RET=0x1234_5678_7654_3210L;
    private static final long ENTER_RET=0x1_0422_3A9AL,WAIT_RET=0x1_0422_3AAEL;
    private static int checks;
    private static void e(Object expected,Object actual,String message) {checks++;equal(expected,actual,message);}
    private record Setup(MemoryImage m,Entry entry) { }
    private record Step(IatCall iat,OpaqueCall direct,VolatileBits post,Runnable effect) { }

    private static Setup setup(int id,int guard) {
        MemoryImage m=new MemoryImage();
        long n=0x3000_0000_0000_0000L+id*0x100L;
        NonvolatileBits nv=new NonvolatileBits(n+1,n+2,n+3,n+4,n+5,n+6,n+7,n+8,vector(n+9));
        VolatileBits v=bits(0x1100L+id*0x1000L,0x1010L+id*0x1000L,G,0x3030L+id*0x1000L);
        m.writeQword(E,RET);m.writeDword(G,guard);
        return new Setup(m,new Entry(B,E,v,nv));
    }
    private static NonvolatileBits rbx(NonvolatileBits n,long value) {
        return new NonvolatileBits(value,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
    }
    private static VolatileBits v(VolatileBits old,long rax,long rcx,long rdx,long r8) {
        return new VolatileBits(rax,rcx,rdx,r8,old.r9Bits(),old.r10Bits(),old.r11Bits(),
                old.xmm0(),old.xmm1(),old.xmm2(),old.xmm3(),old.xmm4(),old.xmm5());
    }
    private static VolatileBits rcx(VolatileBits old,long value) {return v(old,old.raxBits(),value,old.rdxBits(),old.r8Bits());}
    private static VolatileBits post(long seed) {return bits(seed,seed+0x101,seed+0x202,seed+0x303);}
    private static IatCall enter(Setup s) {return new IatCall(0x4223A94L,0x43DA500L,W,false,rcx(s.entry().volatileBits(),CS),rbx(s.entry().nonvolatileBits(),G));}
    private static IatCall leave(VolatileBits before,NonvolatileBits n) {return new IatCall(0x4223AE4L,0x43DA4F0L,E,true,rcx(before,CS),n);}
    private static OpaqueCall waitCall(VolatileBits before,NonvolatileBits n) {return new OpaqueCall(0x4223AA9L,0x4223B30L,W,rcx(before,100),rbx(n,G));}

    private static final class Script implements Ports {
        private final List<Step> steps=new ArrayList<>();
        private final long gs;
        private final int expectedGs;
        private int index,gsReads;
        Script(long gs,int expectedGs) {this.gs=gs;this.expectedGs=expectedGs;}
        Script iat(IatCall call,VolatileBits result,Runnable effect) {steps.add(new Step(call,null,result,effect));return this;}
        Script direct(OpaqueCall call,VolatileBits result,Runnable effect) {steps.add(new Step(null,call,result,effect));return this;}
        private Step next() {if(index==steps.size())throw new AssertionError("unexpected extra port");return steps.get(index++);}
        @Override public long readGsQword58() {gsReads++;if(gsReads>expectedGs)throw new AssertionError("unexpected GS read");return gs;}
        @Override public VolatileBits invokeIat(IatCall actual) {Step s=next();e(s.iat(),actual,"complete IAT frame"+index);s.effect().run();return s.post();}
        @Override public VolatileBits invoke(OpaqueCall actual) {Step s=next();e(s.direct(),actual,"complete direct frame"+index);s.effect().run();return s.post();}
        void done() {e(steps.size(),index,"all ordered ports consumed");e(expectedGs,gsReads,"owned GS reads");}
    }
    private static void entered(Setup s) {
        e(s.entry().nonvolatileBits().rbxBits(),s.m().readQword(E-8),"actual prologue saved incoming RBX");
        e(ENTER_RET,s.m().readQword(W-8),"actual Enter CALL pushed continuation");
        e(RET,s.m().readQword(E),"entry original RET still present");
    }
    private static WaitBudget noWait() {return (header,guard,observed)->{throw new AssertionError("unexpected wait budget");};}

    private static void claimZero() {
        Setup s=setup(1,0);VolatileBits en=post(0xE100),lv=post(0xC100);
        long saved=0xA101_A102_A103_A104L,tailRet=0xB101_B102_B103_B104L;
        NonvolatileBits restored=rbx(s.entry().nonvolatileBits(),saved);
        Script p=new Script(0,0)
            .iat(enter(s),en,()->{entered(s);s.m().writeQword(E-8,saved);})
            .iat(leave(en,restored),lv,()->{
                e(-1,s.m().readDword(G),"zero guard claimed -1");
                e(saved,s.m().readQword(E-8),"tail JMP did not push over saved-RBX slot");
                e(ENTER_RET,s.m().readQword(W-8),"tail JMP did not invent CALL continuation");
                s.m().writeQword(E,tailRet);
            });
        NormalReturn actual=GovernmentThreadHeader178.execute(s.entry(),s.m(),p,noWait());
        e(new NormalReturn(lv,restored,tailRet,E+8),actual,"claim normal full return reads post-tail RET");
        e(-1,s.m().readDword(G),"claim retained guard");p.done();
    }

    private static void completedHighUnsignedIndex() {
        Setup s=setup(2,0x8000_0005);VolatileBits en=post(0xE200),lv=post(0xC200);
        long gs=0x6000_0000L,tls=0x6000_1000L;
        s.m().writeDword(0x1_05C5_CBC4L,0x8000_0001);
        s.m().writeDword(0x1_0542_F090L,0x8000_002A);
        s.m().writeQword(0x4_6000_0008L,tls);
        s.m().writeDword(tls+0xC,0xAABB_CCDD);s.m().writeDword(tls+0x10,0x0102_0304);s.m().writeDword(tls+0x14,0x1122_3344);
        VolatileBits beforeLeave=v(en,0x8000_002AL,CS,tls,0x10);
        Script p=new Script(gs,1)
            .iat(enter(s),en,()->entered(s))
            .iat(leave(beforeLeave,s.entry().nonvolatileBits()),lv,()->{
                e(0x8000_0005,s.m().readDword(G),"completed negative guard unchanged");
                e(0x8000_002A,s.m().readDword(tls+0x10),"raw negative epoch stored DWORD");
                e(0xAABB_CCDD,s.m().readDword(tls+0xC),"lower TLS padding unchanged");
                e(0x1122_3344,s.m().readDword(tls+0x14),"upper TLS padding unchanged");
                e(s.entry().nonvolatileBits().rbxBits(),s.m().readQword(E-8),"completed real RBX pop slot");
                e(ENTER_RET,s.m().readQword(W-8),"completed tail JMP no new CALL push");
            });
        NormalReturn actual=GovernmentThreadHeader178.execute(s.entry(),s.m(),p,noWait());
        e(new NormalReturn(lv,s.entry().nonvolatileBits(),RET,E+8),actual,"completed full poststate and original RET");
        e(0x8000_002A,s.m().readDword(tls+0x10),"completed final TLS DWORD");p.done();
    }

    private static void twoWaitsFreshGuard() {
        Setup s=setup(3,-1);VolatileBits en=post(0xE300),w1=post(0xA310),w2=post(0xA320),lv=post(0xC300);
        long saved1=0xA301_A302_A303_A304L,saved2=0xA311_A312_A313_A314L;
        NonvolatileBits restored=rbx(s.entry().nonvolatileBits(),saved2);
        Script p=new Script(0,0)
            .iat(enter(s),en,()->entered(s))
            .direct(waitCall(en,s.entry().nonvolatileBits()),w1,()->{
                e(WAIT_RET,s.m().readQword(W-8),"first wait actual CALL push");
                e(0,s.m().readDword(G),"selected wait still runs after budget mutates guard");
                s.m().writeDword(G,-1);s.m().writeQword(E-8,saved1);
            })
            .direct(waitCall(w1,s.entry().nonvolatileBits()),w2,()->{
                e(WAIT_RET,s.m().readQword(W-8),"second wait actual CALL push");
                e(-1,s.m().readDword(G),"second wait fresh -1 guard");
                s.m().writeDword(G,0);s.m().writeQword(E-8,saved2);
            })
            .iat(leave(w2,restored),lv,()->{
                e(-1,s.m().readDword(G),"fresh zero after second wait is claimed");
                e(saved2,s.m().readQword(E-8),"final RBX restored from modified real slot");
                e(WAIT_RET,s.m().readQword(W-8),"leave tail did not push");
            });
        int[] budget={0};
        WaitBudget b=(header,guard,observed)->{
            e(0x4223AA4L,header,"actual wait header");e(G,guard,"guard pointer offered to budget");e(-1,observed,"branch-observed guard");
            e(budget[0]==0?ENTER_RET:WAIT_RET,s.m().readQword(W-8),"budget precedes new wait CALL push");
            if(budget[0]++==0)s.m().writeDword(G,0);
        };
        NormalReturn actual=GovernmentThreadHeader178.execute(s.entry(),s.m(),p,b);
        e(new NormalReturn(lv,restored,RET,E+8),actual,"two-wait full normal return");
        e(2,budget[0],"two real selected wait edges");p.done();
    }

    private static void budgetRejectsBeforePush() {
        Setup s=setup(4,-1);VolatileBits en=post(0xE400);
        Script p=new Script(0,0).iat(enter(s),en,()->entered(s));
        UnsupportedOperationException rejection=new UnsupportedOperationException("owned178 finite wait budget");
        int[] budget={0};
        WaitBudget b=(header,guard,observed)->{
            budget[0]++;e(0x4223AA4L,header,"reject wait header");e(G,guard,"reject guard pointer");e(-1,observed,"reject observed guard");
            e(ENTER_RET,s.m().readQword(W-8),"rejection before new CALL push");throw rejection;
        };
        try {GovernmentThreadHeader178.execute(s.entry(),s.m(),p,b);throw new AssertionError("budget rejection returned normally");}
        catch(UnsupportedOperationException actual) {e(rejection,actual,"exact budget rejection propagated");}
        e(1,budget[0],"one rejected edge");e(-1,s.m().readDword(G),"rejected guard unchanged");
        e(ENTER_RET,s.m().readQword(W-8),"no wait CALL push on rejected edge");
        e(s.entry().nonvolatileBits().rbxBits(),s.m().readQword(E-8),"rejected stack retains saved incoming RBX");
        e(RET,s.m().readQword(E),"rejected original RET untouched");p.done();
    }

    public static int runAll() {
        checks=0;claimZero();completedHighUnsignedIndex();twoWaitsFreshGuard();budgetRejectsBeforePush();return checks;
    }
}

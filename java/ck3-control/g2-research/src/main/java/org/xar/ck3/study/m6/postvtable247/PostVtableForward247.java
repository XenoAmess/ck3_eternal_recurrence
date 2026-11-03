package org.xar.ck3.study.m6.postvtable247;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.CallFrame;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.Children;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.Input;
import org.xar.ck3.study.m6.postvtable247.PostVtable247Api.TailFrame;

/** Complete held51/58 source bodies with typed child Outcomes, not old237 NR plus presumed flags. */
public final class PostVtableForward247 {
    private PostVtableForward247() { }

    /** Exact85587051B: one first virtual CALL, actual fresh local epilogue, then JMP R9. */
    public static QueueFp604Api.Outcome fromSlot08(Input input,
            GovernmentCrtBoundary185Api.Memory memory,Children children) {
        State f=start(input,memory);Registers r=f.r;
        r.rax=memory.readQword(r.rcx);                  //85587A
        r.rbx=r.r8;                                   //85587D
        r.rdi=r.rdx;                                  //855880
        long target=memory.readQword(r.rax+0x38L);
        QueueFp604Api.Outcome offered=f.call(0x855870L,0x855883L,3,target,children);
        if(offered instanceof QueueFp604Api.Stopped)return offered;
        r.r8=r.rbx;                                   //855886
        r.rdx=r.rdi;                                  //855889
        r.rcx=memory.readQword(r.rax);                 //85588C
        r.r9=memory.readQword(r.rcx+8L);                //85588F
        r.rcx=r.rax;                                  //855893
        restoreAndPop(f);                             //855896..85589F
        GovernmentCrtBoundary185Api.Entry targetEntry=f.currentEntry();
        GovernmentCrtBoundary185Api.Tail transfer=new GovernmentCrtBoundary185Api.Tail(
                0x8558A0L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,r.r9,targetEntry);
        Input targetInput=new Input(targetEntry,f.df,f.mxcsr,input.originCallSiteRva());
        TailFrame frame=new TailFrame(0x855870L,transfer,targetInput,3);
        // No push, no source RET read, no synthetic normal result, no post-state rewrite.
        return Objects.requireNonNull(Objects.requireNonNull(children).tail(frame,memory));
    }

    /** Exact85583058B: source self branch, otherwise two real CALLs of lengths3 and4, actual RET. */
    public static QueueFp604Api.Outcome fromSlot10(Input input,
            GovernmentCrtBoundary185Api.Memory memory,Children children) {
        State f=start(input,memory);Registers r=f.r;
        r.rax=r.rcx+8L;                               //85583A raw64 wrap
        r.rdi=r.r8;                                   //85583E
        r.rbx=r.rdx;                                  //855841
        if(r.rdx!=r.rax) {                            //855844/855847
            r.rax=memory.readQword(r.rcx);             //855849
            long target=memory.readQword(r.rax+0x38L);
            QueueFp604Api.Outcome offered=f.call(0x855830L,0x85584CL,3,target,children);
            if(offered instanceof QueueFp604Api.Stopped)return offered;
            r.r8=r.rdi;                               //85584F
            r.rdx=r.rbx;                              //855852
            r.rcx=r.rax;                              //855855
            r.r9=memory.readQword(r.rax);              //855858
            long secondTarget=memory.readQword(r.r9+0x10L);
            offered=f.call(0x855830L,0x85585BL,4,secondTarget,children);
            if(offered instanceof QueueFp604Api.Stopped)return offered;
        }
        restoreAndPop(f);                             //85585F..855868
        long actualRip=memory.readQword(r.rsp);         //855869 actual source RET
        r.rsp+=8L;
        return f.finish(actualRip);
    }

    /** Identical source prologues; null children are deliberately not checked on free-self branch. */
    private static State start(Input input,GovernmentCrtBoundary185Api.Memory memory) {
        State f=new State(input,memory);Registers r=f.r;
        memory.writeQword(r.rsp+8L,r.rbx);
        r.rsp-=8L;memory.writeQword(r.rsp,r.rdi);
        r.rsp-=0x20L;
        return f;
    }

    /** Identical source local epilogues. Both save slots are freshly read after child RAM effects. */
    private static void restoreAndPop(State f) {
        Registers r=f.r;
        r.rbx=f.memory.readQword(r.rsp+0x30L);
        r.rsp+=0x20L;
        r.rdi=f.memory.readQword(r.rsp);r.rsp+=8L;
    }

    private static final class State {
        private final long image;
        private final Registers r;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private boolean df;
        private QueueFp604Api.Mxcsr mxcsr;
        private State(Input input,GovernmentCrtBoundary185Api.Memory memory) {
            Objects.requireNonNull(input);this.memory=Objects.requireNonNull(memory);
            GovernmentCrtBoundary185Api.Entry entry=input.entry();image=entry.imageBaseBits();
            r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(image,
                    entry.rspBits(),entry.volatileBits(),entry.nonvolatileBits()));
            df=input.directionFlagSet();mxcsr=input.mxcsr();
        }
        private GovernmentCrtBoundary185Api.Entry currentEntry() {
            return new GovernmentCrtBoundary185Api.Entry(image,r.rsp,r.volatileBits(),r.nonvolatileBits());
        }
        private QueueFp604Api.Outcome call(long owner,long site,int length,long target,Children children) {
            GovernmentCrtBoundary185Api.Call call=new GovernmentCrtBoundary185Api.Call(site,
                    GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,target,r.rsp,
                    r.volatileBits(),r.nonvolatileBits());
            Input child=new Input(new GovernmentCrtBoundary185Api.Entry(image,r.rsp-8L,
                    call.volatileBits(),call.nonvolatileBits()),df,mxcsr,site);
            long rip=image+site+length;
            CallFrame frame=new CallFrame(owner,image,call,child,length,rip);
            memory.writeQword(child.entry().rspBits(),rip); // exactly one source CALL push
            QueueFp604Api.Outcome offered=Objects.requireNonNull(Objects.requireNonNull(children).invoke(frame,memory));
            if(offered instanceof QueueFp604Api.Normal normal) {
                frame.checkNormalReturn(normal);
                GovernmentCrtBoundary185Api.NormalReturn nr=normal.base().normalReturn();
                r.apply(nr.volatileBits());r.rsp=nr.callerRspBits();
                df=normal.base().postDirectionFlagSet();mxcsr=normal.postMxcsr();
            }
            return offered; // Stopped identity and its current state/origin are not rebuilt
        }
        private QueueFp604Api.Normal finish(long actualReadRip) {
            GovernmentCrtBoundary185Api.NormalReturn nr=new GovernmentCrtBoundary185Api.NormalReturn(
                    r.volatileBits(),actualReadRip,r.rsp,r.nonvolatileBits());
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr,df),mxcsr);
        }
    }
}

package org.xar.ck3.study.m6.postfree251;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full224.DefaultFreeThunks185224;
import org.xar.ck3.study.m6.poststate240.PostState240Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api.AlreadyPushedCallFrame;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api.Children;

/** Whole held5+17+61 entry, reusing224/201 once and collecting every actual child post-state. */
public final class FreePostState251 implements PostState240Api.EntryExecutor {
    private final Children children;
    public FreePostState251(Children children) { this.children=Objects.requireNonNull(children); }

    @Override public QueueFp604Api.Outcome execute(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(input);Objects.requireNonNull(memory);
        Invocation invocation=new Invocation(input,memory,children);
        try {
            GovernmentCrtBoundary185Api.NormalReturn actual=DefaultFreeThunks185224.execute(
                    input.entry(),memory,invocation);
            // All local5/17/61 instructions preserve DF/MXCSR; every reached CALL went through invocation.
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(actual,invocation.df),invocation.mxcsr);
        } catch(StoppedTransfer transfer) {
            if(transfer.owner!=invocation)throw transfer;
            return transfer.original;
        }
    }

    private static final class Invocation implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final Children children;
        private boolean df;
        private QueueFp604Api.Mxcsr mxcsr;
        private Invocation(PostState240Api.Input input,GovernmentCrtBoundary185Api.Memory memory,
                Children children) {
            image=input.entry().imageBaseBits();this.memory=memory;this.children=children;
            df=input.directionFlagSet();mxcsr=input.mxcsr();
        }
        @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            AlreadyPushedCallFrame frame=FreePostState251Api.alreadyPushed(image,call,df,mxcsr);
            //201 already wrote the source RET once. No push, target lookup or fresh RET read here.
            QueueFp604Api.Outcome offered=Objects.requireNonNull(children.invoke(frame,memory));
            if(offered instanceof QueueFp604Api.Stopped stopped)throw new StoppedTransfer(this,stopped);
            QueueFp604Api.Normal normal=(QueueFp604Api.Normal)offered;
            frame.checkNormalReturn(normal);
            df=normal.base().postDirectionFlagSet();mxcsr=normal.postMxcsr();
            return normal.base().normalReturn().volatileBits();
        }
        @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            throw new IllegalStateException("No tail child in held5/17/61 source");
        }
        @Override public long readGsQword58() {
            throw new IllegalStateException("No GS read in held5/17/61 source");
        }
    }

    /** Private software transfer only; no manufactured machine snapshot or caught ordinary exception. */
    private static final class StoppedTransfer extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final transient Invocation owner;
        private final transient QueueFp604Api.Stopped original;
        private StoppedTransfer(Invocation owner,QueueFp604Api.Stopped original) {
            super(null,null,false,false);this.owner=owner;this.original=original;
        }
    }
}

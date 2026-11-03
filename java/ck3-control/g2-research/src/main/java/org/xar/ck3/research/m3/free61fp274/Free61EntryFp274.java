package org.xar.ck3.research.m3.free61fp274;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.research.m4.Free61FullState201;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Source-specific retained61 protocol for bare E364 entry.
 * Uses existing 201 logic and 251 metadata; no 5/17 prefix, no default FP/DF.
 */
public final class Free61EntryFp274 {
    private Free61EntryFp274() { }

    public static QueueFp604Api.Outcome execute(
            QueueFp604Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory,
            FreePostState251Api.Children children) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(children);

        PrivateInvocation invoker = new PrivateInvocation(
                input.base().entry().imageBaseBits(),
                input.base().directionFlagSet(),
                input.mxcsr(),
                memory,
                children);

        try {
            GovernmentCrtBoundary185Api.NormalReturn result = Free61FullState201.execute(
                    input.base().entry(),
                    memory,
                    invoker);

            return new QueueFp604Api.Normal(
                    new FullCopy437Api.CallResult(result, invoker.currentDF),
                    invoker.currentMxcsr);
        } catch (StoppedTransfer transfer) {
            if (transfer.owner != invoker) {
                throw transfer;
            }
            return transfer.actual;
        }
    }

    private static final class StoppedTransfer extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient Object owner;
        private final transient QueueFp604Api.Stopped actual;

        private StoppedTransfer(Object owner, QueueFp604Api.Stopped actual) {
            super(null, null, false, false);
            this.owner = Objects.requireNonNull(owner);
            this.actual = Objects.requireNonNull(actual);
        }
    }

    private static final class PrivateInvocation implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBase;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final FreePostState251Api.Children children;
        private boolean currentDF;
        private QueueFp604Api.Mxcsr currentMxcsr;

        PrivateInvocation(long imageBase, boolean currentDF, QueueFp604Api.Mxcsr currentMxcsr,
                GovernmentCrtBoundary185Api.Memory memory, FreePostState251Api.Children children) {
            this.imageBase = imageBase;
            this.currentDF = currentDF;
            this.currentMxcsr = currentMxcsr;
            this.memory = memory;
            this.children = children;
        }

        @Override
        public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            Objects.requireNonNull(call);

            FreePostState251Api.AlreadyPushedCallFrame frame = FreePostState251Api.alreadyPushed(
                    imageBase, call, currentDF, currentMxcsr);

            QueueFp604Api.Outcome outcome = children.invoke(frame, memory);
            Objects.requireNonNull(outcome);

            if (outcome instanceof QueueFp604Api.Normal normal) {
                frame.checkNormalReturn(normal);
                currentDF = normal.base().postDirectionFlagSet();
                currentMxcsr = normal.postMxcsr();
                return normal.base().normalReturn().volatileBits();
            } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                throw new StoppedTransfer(this, stopped);
            } else {
                throw new IllegalStateException("Unknown outcome type");
            }
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            throw new IllegalStateException("No source tail in held61");
        }

        @Override
        public long readGsQword58() {
            throw new IllegalStateException("No source readGsQword58 in held61");
        }
    }
}
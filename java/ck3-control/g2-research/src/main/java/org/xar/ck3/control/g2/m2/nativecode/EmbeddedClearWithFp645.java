package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner current-FP/Stopped carrier around the unchanged complete held93 algorithm. */
public final class EmbeddedClearWithFp645 {
    private EmbeddedClearWithFp645() { }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input,
            FullCopy437Api.Memory memory, EmbeddedClearFp645Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        QueueFp604Api.Mxcsr[] current = { input.mxcsr() };
        EmbeddedClear587Api.Calls adapted = frame -> {
            EmbeddedClearFp645Api.CallFrame fpFrame =
                    new EmbeddedClearFp645Api.CallFrame(frame, current[0]);
            QueueFp604Api.Outcome offered = Objects.requireNonNull(calls.invoke(fpFrame));
            if (offered instanceof QueueFp604Api.Normal normal) {
                fpFrame.checkNormalReturn(normal);
                current[0] = normal.postMxcsr();
                return normal.base();
            }
            throw new StoppedCarrier((QueueFp604Api.Stopped) offered);
        };
        try {
            FullCopy437Api.CallResult actual =
                    EmbeddedClearFullState889780.execute(input.base(), memory, adapted);
            return new QueueFp604Api.Normal(actual, current[0]);
        } catch (StoppedCarrier carrier) {
            return carrier.stopped;
        }
    }

    /** Narrow parent37282E1 binding; all other parent frames keep the supplied fallback. */
    public static EmbeddedElementsFp637.Calls bindClear(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget, EmbeddedClearFp645Api.Calls clearCalls,
            EmbeddedElementsFp637.Calls foreignParentCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(clearCalls);
        Objects.requireNonNull(foreignParentCalls);
        return frame -> {
            Objects.requireNonNull(frame);
            EmbeddedElements578Api.CallFrame original = frame.original();
            GovernmentCrtBoundary185Api.Call call = original.call();
            if (call.callSiteRva() == 0x37282E1L
                    && call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == 0x889780L && original.instructionLength() == 5) {
                FullCopy437Api.Input clearBase = new FullCopy437Api.Input(
                        original.childEntry(), original.directionFlagSet(), budget);
                QueueFp604Api.Input clearInput = new QueueFp604Api.Input(clearBase, frame.preMxcsr());
                QueueFp604Api.Outcome offered = Objects.requireNonNull(execute(clearInput, memory, clearCalls));
                if (offered instanceof QueueFp604Api.Normal normal)
                    original.checkNormalReturn(normal.base());
                return offered;
            }
            return Objects.requireNonNull(foreignParentCalls.invoke(frame));
        };
    }

    private static final class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final transient QueueFp604Api.Stopped stopped;
        private StoppedCarrier(QueueFp604Api.Stopped stopped) {
            super(null, null, false, false);
            this.stopped = stopped;
        }
    }
}

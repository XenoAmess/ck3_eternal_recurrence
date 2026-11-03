package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.e900227.E900FullState227;

/** Explicit call/tail post-state carrier; the existing normal70B producer owns its algorithm. */
public final class KnownFc74E900Fp627 {
    private KnownFc74E900Fp627() { }

    private static final class StopSignal extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;
        StopSignal(QueueFp604Api.Stopped outcome) { this.outcome = outcome; }
    }

    public static Fc74Fp626Api.Calls bind(GovernmentCrtBoundary185Api.Memory memory,
            E900Fp627Api.Calls inner, Fc74Fp626Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(foreign);
        return frame -> {
            Objects.requireNonNull(frame);
            var original = frame.original();
            if (original.callSiteRva() != 0x424FC96L
                    || original.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    || original.targetBits() != 0x424E900L) {
                return Objects.requireNonNull(foreign.invoke(frame));
            }
            boolean[] df = { frame.directionFlagSet() };
            QueueFp604Api.Mxcsr[] fp = { frame.preMxcsr() };
            GovernmentCrtBoundary185Api.Calls lower = new GovernmentCrtBoundary185Api.Calls() {
                @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                    var child = new GovernmentCrtBoundary185Api.Entry(frame.childEntry().imageBaseBits(),
                            call.rspBits() - 8, call.volatileBits(), call.nonvolatileBits());
                    var offeredFrame = new E900Fp627Api.CallFrame(call, child, df[0], fp[0]);
                    var outcome = Objects.requireNonNull(inner.invoke(offeredFrame));
                    if (outcome instanceof QueueFp604Api.Stopped stopped) throw new StopSignal(stopped);
                    var normal = (QueueFp604Api.Normal) outcome;
                    offeredFrame.checkNormalReturn(normal.base());
                    df[0] = normal.base().postDirectionFlagSet();
                    fp[0] = normal.postMxcsr();
                    return normal.base().normalReturn().volatileBits();
                }
                @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail tail) {
                    var offeredFrame = new E900Fp627Api.TailFrame(tail, frame, df[0], fp[0]);
                    var outcome = Objects.requireNonNull(inner.tail(offeredFrame));
                    if (outcome instanceof QueueFp604Api.Stopped stopped) throw new StopSignal(stopped);
                    var normal = (QueueFp604Api.Normal) outcome;
                    offeredFrame.checkNormalReturn(normal.base());
                    df[0] = normal.base().postDirectionFlagSet();
                    fp[0] = normal.postMxcsr();
                    return normal.base().normalReturn();
                }
                @Override public long readGsQword58() {
                    throw new UnsupportedOperationException("No GS read in the held E900 body");
                }
            };
            try {
                var actual = E900FullState227.execute(frame.childEntry(), memory, lower);
                var base = new FullCopy437Api.CallResult(actual, df[0]);
                frame.checkNormalReturn(base);
                return new QueueFp604Api.Normal(base, fp[0]);
            } catch (StopSignal stopped) {
                return stopped.outcome;
            }
        };
    }
}

package org.xar.ck3.study.m6.postfree253;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.study.m6.postfree251.FreePostState251;
import org.xar.ck3.study.m6.postfree251.FreePostState251Api;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Actual648 tail-to-251 glue; no producer-body dependency or inferred machine input. */
public final class DefaultFreePost253 {
    private DefaultFreePost253() { }

    /**
     * Bind for the actual incoming continuation, using the same supplied RAM.
     * The caller must take incomingContinuationOriginRva from its actual247 frame:
     * current252's release selection is the second CALL's childInput().originCallSiteRva().
     * Neither648 Input nor its tail exposes that value; this parameter has no default.
     */
    public static DefaultStaticFp648Api.Calls bind(
            GovernmentCrtBoundary185Api.Memory sameMemory,
            FreePostState251Api.Children freeChildren,
            long incomingContinuationOriginRva,
            DefaultStaticFp648Api.Calls delegate) {
        Objects.requireNonNull(sameMemory);
        Objects.requireNonNull(delegate);
        FreePostState251 free = new FreePostState251(Objects.requireNonNull(freeChildren));
        return new DefaultStaticFp648Api.Calls() {
            @Override public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                return delegate.invoke(frame);
            }

            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                GovernmentCrtBoundary185Api.Tail transfer = frame.transfer();
                if (transfer.jumpSiteRva() == 0x8571C8L
                        && transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && transfer.targetBits() == 0x40EC530L) {
                    PostState240Api.Input actual = new PostState240Api.Input(transfer.entry(),
                            frame.directionFlagSet(), frame.preMxcsr(), incomingContinuationOriginRva);
                    return free.execute(actual, sameMemory);
                }
                return delegate.tail(frame);
            }
        };
    }
}

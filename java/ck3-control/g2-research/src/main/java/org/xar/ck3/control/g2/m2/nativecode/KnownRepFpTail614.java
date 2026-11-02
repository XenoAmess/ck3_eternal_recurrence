package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyRep4226840;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Known REP producer tail handler for the COPY context.
 * Selects only specific indirect absolute tails targeting the held REP function at 0x4226840.
 */
public final class KnownRepFpTail614 {
    private KnownRepFpTail614() { }

    /**
     * Binds a TailCalls handler that routes known REP tails to the mature producer
     * and delegates all other tails to the foreign handler.
     */
    public static FullCopyWithFp613.TailCalls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullCopyWithFp613.TailCalls foreignTails) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(foreignTails);

        return new FullCopyWithFp613.TailCalls() {
            @Override
            public QueueFp604Api.Outcome tail(FullCopyWithFp613.TailCall frame) {
                Objects.requireNonNull(frame);

                FullCopy437Api.TailFrame original = frame.original();
                GovernmentCrtBoundary185Api.Tail transfer = original.transfer();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();

                // Check if this is a known REP tail
                long jumpSite = transfer.jumpSiteRva();
                boolean isKnownSite = (jumpSite == 0x422688BL || jumpSite == 0x4226AD2L ||
                                      jumpSite == 0x4226C02L || jumpSite == 0x4226D76L);

                boolean isIndirect = (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE);

                long imageBase = transfer.entry().imageBaseBits();
                long target = transfer.targetBits();
                // Raw long bits comparison, allowing normal Java wrapping
                boolean isRepTarget = (target == imageBase + 0x4226840L);

                if (isKnownSite && isIndirect && isRepTarget) {
                    // Execute the known REP producer
                    GovernmentCrtBoundary185Api.Entry entry = transfer.entry();
                    boolean directionFlag = original.directionFlagSet();

                    // Construct input with exact entry, original direction flag, and captured budget
                    FullCopy437Api.Input repInput = new FullCopy437Api.Input(
                        entry,
                        directionFlag,
                        budget
                    );

                    // Call the mature REP executor
                    FullCopy437Api.CallResult result = FullCopyRep4226840.execute(repInput, memory);

                    // Wrap in Normal with the SAME incoming MXCSR
                    return new QueueFp604Api.Normal(result, preMxcsr);
                } else {
                    // Delegate to foreign tails unchanged
                    return foreignTails.tail(frame);
                }
            }
        };
    }
}
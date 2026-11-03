package org.xar.ck3.research.m3.copy437259;

import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.KnownRepFpTail614;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Sole M3 component binding for Add4 COPY sites.
 * Selects only the four actual direct CALLs to 0x4226860 in the 351-byte Add4 body.
 * Reuses mature FullCopyWithFp613 and KnownRepFpTail614 without rewriting them.
 */
public final class Add4Copy259 {
    private Add4Copy259() { }

    /**
     * Binds the COPY handler for the four direct 0x4226860 call sites.
     * @param memory The owned memory view.
     * @param budget The loop budget.
     * @param unknownCopyTails The handler for unknown tails.
     * @param foreignCalls The handler for other legal 639 frames.
     * @return The Add4Fp639Api.Calls implementation.
     */
    public static Add4Fp639Api.Calls bind(Add4Fp639Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            FullCopyWithFp613.TailCalls unknownCopyTails,
            Add4Fp639Api.Calls foreignCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(unknownCopyTails);
        Objects.requireNonNull(foreignCalls);

        // Bind the known REP tail handler once
        FullCopyWithFp613.TailCalls repTails = KnownRepFpTail614.bind(memory, budget, unknownCopyTails);

        return new Add4Fp639Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Add4Fp639Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call call = frame.call();
                long site = call.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
                long target = call.targetBits();
                int length = frame.instructionLength();

                // Select only the four actual direct CALLs to 0x4226860 with length 5
                boolean isCopySite = (site == 0xADD16DL || site == 0xADD17CL ||
                                      site == 0xADD1A0L || site == 0xADD1F7L);
                boolean isDirect = (kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA);
                boolean isTarget = (target == 0x4226860L);
                boolean isLength = (length == 5);

                if (isCopySite && isDirect && isTarget && isLength) {
                    // Construct FullCopy437Api.Input from EXACT frame.childEntry(), frame.directionFlagSet() and SAME supplied budget
                    FullCopy437Api.Input copyInput = new FullCopy437Api.Input(
                        frame.childEntry(),
                        frame.directionFlagSet(),
                        budget
                    );

                    // Construct QueueFp604Api.Input using SAME frame.preMxcsr()
                    QueueFp604Api.Input fpInput = new QueueFp604Api.Input(copyInput, frame.preMxcsr());

                    // Invoke actual FullCopyWithFp613.execute once with SAME memory and the bound614 tail router
                    QueueFp604Api.Outcome outcome = FullCopyWithFp613.execute(fpInput, memory, repTails);

                    if (outcome instanceof QueueFp604Api.Normal) {
                        // Use actual639 frame.checkNormalReturn before returning that SAME Outcome
                        frame.checkNormalReturn((QueueFp604Api.Normal)outcome);
                        return outcome;
                    } else {
                        // Stopped retains exact identity and gets no Normal validation
                        return outcome;
                    }
                } else {
                    // Other legal639 frames invoke foreignCalls with the identical frame once
                    QueueFp604Api.Outcome outcome = foreignCalls.invoke(frame);
                    Objects.requireNonNull(outcome);
                    // Return SAME outcome unchanged
                    return outcome;
                }
            }
        };
    }
}
package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCalls;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopyWithFp613;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueWithPartialFp611;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueFp609Api;

/**
 * Actual upper consumer with public static execute.
 * Composes through actual EmbeddedQueueWithPartialFp611, intercepting ONLY actual597 directCALL8803C5->4226860.
 */
public final class EmbeddedQueueWithKnownFpCopy613 {
    private EmbeddedQueueWithKnownFpCopy613() { }

    public static Outcome execute(Input input, EmbeddedQueueFp609Api.Memory memory,
                                   AppendCalls otherCalls, FullCopyWithFp613.TailCalls copyTails) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherCalls);
        Objects.requireNonNull(copyTails);

        // Create the bound AppendCalls adapter that routes the specific 8803C5 call
        // to FullCopyWithFp613 for all raw R8 sizes, and everything else to otherCalls.
        AppendCalls boundAppendCalls = new AppendCalls() {
            @Override
            public Outcome invoke(AppendCallFrame frame) {
                Objects.requireNonNull(frame);
                QueueAppend597Api.CallFrame base = frame.base();
                long site = base.call().callSiteRva();

                if (site == 0x8803C5L) {
                    // Intercept ONLY actual597 directCALL8803C5->4226860
                    // Build a QueueFp604Api.Input with original597 childEntry/directionFlagSet,
                    // ORIGINAL top-level input.base().budget(), and originalframe.preMxcsr
                    Input fpInput = new Input(
                        new FullCopy437Api.Input(
                            base.childEntry(),
                            base.directionFlagSet(),
                            input.base().budget()
                        ),
                        frame.preMxcsr()
                    );

                    // Pass identical memory and copyTails to FullCopyWithFp613 once
                    Outcome result = FullCopyWithFp613.execute(fpInput, memory, copyTails);

                    if (result instanceof Normal normal) {
                        // On Normal, run original597 checkNormalReturn on its original CallResult
                        base.checkNormalReturn(normal.base());
                        // Return the same Outcome
                        return result;
                    } else if (result instanceof Stopped stopped) {
                        // Stopped goes back with identity, no forcednormal/restore/unlock/epilogue
                        return result;
                    }

                    // Should not reach here if Outcome is sealed interface permits Normal, Stopped
                    throw new IllegalStateException("Unexpected Outcome type");
                }

                // All other append frames/outcomes/exceptions delegate unchanged to otherCalls.invoke
                // with exact original frame.
                return otherCalls.invoke(frame);
            }
        };

        // Compose through actual EmbeddedQueueWithPartialFp611
        return EmbeddedQueueWithPartialFp611.execute(input, memory, boundAppendCalls);
    }
}
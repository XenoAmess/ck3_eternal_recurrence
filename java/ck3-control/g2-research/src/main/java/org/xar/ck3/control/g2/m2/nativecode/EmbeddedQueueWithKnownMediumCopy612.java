package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.AppendCalls;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy4226860;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueWithPartialFp611;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueFp609Api;

/**
 * Thin actual consumer of EmbeddedQueueWithPartialFp611 that binds the exact
 * 8803C5 direct call to FullCopy4226860.execute for the admitted 16..32 byte
 * MOVDQU path. All other calls and sizes route to the original AppendCalls.
 */
public final class EmbeddedQueueWithKnownMediumCopy612 {
    private EmbeddedQueueWithKnownMediumCopy612() { }

    public static Outcome execute(Input input, EmbeddedQueueFp609Api.Memory memory, AppendCalls otherCalls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(otherCalls);

        // Create the bound AppendCalls adapter that routes the specific 8803C5 call
        // to FullCopy4226860 for the admitted 16..32 byte path, and everything else
        // to the original otherCalls.
        AppendCalls boundAppendCalls = new AppendCalls() {
            @Override
            public Outcome invoke(AppendCallFrame frame) {
                Objects.requireNonNull(frame);
                QueueAppend597Api.CallFrame base = frame.base();
                long site = base.call().callSiteRva();

                if (site == 0x8803C5L) {
                    // Check if this is the admitted medium copy path (R8 in 16..32)
                    // The childEntry volatile bits contain R8.
                    long r8 = base.childEntry().volatileBits().r8Bits();

                    // Admitted path: unsigned R8 in [16, 32]
                    if (Long.compareUnsigned(r8, 16L) >= 0 && Long.compareUnsigned(r8, 32L) <= 0) {
                        // Construct FullCopy437Api.Input from the actual childEntry,
                        // directionFlagSet, and the ORIGINAL top-level budget.
                        FullCopy437Api.Input copyInput = new FullCopy437Api.Input(
                            base.childEntry(),
                            base.directionFlagSet(),
                            input.base().budget()
                        );

                        // Execute the real FullCopy4226860 with the identical Memory object.
                        // The Calls implementation for FullCopy4226860 must throw if reached,
                        // as the admitted 16..32 path has no nested calls.
                        FullCopy437Api.Calls throwingCalls = new FullCopy437Api.Calls() {
                            @Override
                            public FullCopy437Api.CallResult invoke(FullCopy437Api.CallFrame frame) {
                                throw new UnsupportedOperationException("No nested calls in admitted 16..32 MOVDQU path");
                            }
                            @Override
                            public FullCopy437Api.CallResult tail(FullCopy437Api.TailFrame frame) {
                                throw new UnsupportedOperationException("No tail calls in admitted 16..32 MOVDQU path");
                            }
                            @Override
                            public long readGsQword58() {
                                throw new UnsupportedOperationException("No GS read in admitted 16..32 MOVDQU path");
                            }
                        };

                        FullCopy437Api.CallResult actualResult = FullCopy4226860.execute(copyInput, memory, throwingCalls);

                        // Validate the return against the original 597 frame expectations.
                        base.checkNormalReturn(actualResult);

                        // Return Normal with the unchanged FullCopy CallResult and the SAME preMxcsr.
                        return new Normal(actualResult, frame.preMxcsr());
                    }
                }

                // All other calls (including COPY sizes outside 16..32) go to otherCalls.invoke
                // with the original frame object.
                return otherCalls.invoke(frame);
            }
        };

        // Compose through existing 611 so its upper classification/locking/FP path
        // and frame checks remain real.
        return EmbeddedQueueWithPartialFp611.execute(input, memory, boundAppendCalls);
    }
}
package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.QueueCallFrame;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.QueueCalls;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueue591Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppendFpWhole608;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedClassifyFullState3727580;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueFpFull609;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueueFp609Api;

/**
 * Thin binding class for the known FP path of the embedded queue.
 * Routes the classify call (3727ECF) to the integer classifier and the append call (3727F0D) to the FP-aware whole227 producer.
 * Preserves MXCSR state for the integer classifier and propagates it for the FP producer.
 */
public final class EmbeddedQueueWithKnownFp609 {
    private EmbeddedQueueWithKnownFp609() { }

    public static Outcome execute(Input input, EmbeddedQueueFp609Api.Memory memory, QueueFp604Api.AppendCalls appendCalls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(appendCalls);

        // Create the bound QueueCalls adapter that routes to the specific implementations
        QueueCalls boundQueueCalls = new QueueCalls() {
            @Override
            public Outcome invoke(QueueCallFrame frame) {
                Objects.requireNonNull(frame);
                long site = frame.base().call().callSiteRva();

                if (site == 0x3727ECFL) {
                    // Route to EmbeddedClassifyFullState3727580 (integer classifier, no FP)
                    // The classifier does not use MXCSR, so we preserve the preMxcsr unchanged.
                    FullCopy437Api.Input classifyInput = new FullCopy437Api.Input(
                        frame.base().childEntry(),
                        frame.base().directionFlagSet(),
                        input.base().budget()
                    );
                    FullCopy437Api.CallResult actualResult = EmbeddedClassifyFullState3727580.execute(classifyInput, memory);

                    // Validate the return against the frame expectations
                    frame.base().checkNormalReturn(actualResult);

                    // Wrap in Normal, preserving the preMxcsr as the postMxcsr since no FP occurred
                    return new Normal(actualResult, frame.preMxcsr());

                } else if (site == 0x3727F0DL) {
                    // Route to QueueAppendFpWhole608 (FP-aware whole227)
                    // Construct the FP Input with the preMxcsr from the frame
                    Input fpInput = new Input(
                        new FullCopy437Api.Input(
                            frame.base().childEntry(),
                            frame.base().directionFlagSet(),
                            input.base().budget()
                        ),
                        frame.preMxcsr()
                    );

                    // Execute the whole227 FP producer
                    // The originCallSiteRva is the actual call site in the 103-byte function
                    Outcome result = QueueAppendFpWhole608.execute(fpInput, memory, appendCalls, 0x3727F0DL);
                    if (result instanceof Normal normal) {
                        frame.checkNormalReturn(normal);
                    }
                    return result;

                } else {
                    // Unknown queue port: reject with IllegalArgumentException
                    throw new IllegalArgumentException("Unknown queue call site: " + Long.toHexString(site));
                }
            }
        };

        // Invoke the owner FP producer with the bound calls
        return EmbeddedQueueFpFull609.execute(input, memory, boundQueueCalls);
    }
}
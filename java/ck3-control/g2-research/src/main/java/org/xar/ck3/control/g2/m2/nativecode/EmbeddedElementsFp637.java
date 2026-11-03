package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElements578Api;
import org.xar.ck3.control.g2.m2.nativecode.Element172Fp636Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;

/**
 * Complete caller composition for the 322-byte function at RVA 0x37282B0.
 * Reuses EmbeddedElementsFullState37282B0.execute exactly once and Element172FullState636.execute once per selected CALL.
 * Preserves all frames, state, Memory, Stopped identity, and Normal guards.
 */
public final class EmbeddedElementsFp637 {
    private EmbeddedElementsFp637() { }

    /**
     * Memory interface extending both FullCopy437Api.Memory and Element172Fp636Api.Memory.
     * The same object instance must satisfy both contracts.
     */
    public interface Memory extends FullCopy437Api.Memory, Element172Fp636Api.Memory {
    }

    /**
     * Call frame wrapper combining the original 578 API frame with the current MXCSR state.
     */
    public record CallFrame(EmbeddedElements578Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Opaque interaction model for the six call instructions in the 322-byte body.
     */
    public interface Calls {
        /**
         * Handles a direct or indirect call to one of the six targets.
         * @param frame The validated call frame.
         * @return The complete result including post-state volatile/nonvolatile bits, DF, and MXCSR.
         */
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }

    /**
     * Executes the complete 322-byte function body using the provided memory and calls.
     * @param input The input containing the base entry, direction flag, and MXCSR.
     * @param memory The shared memory view.
     * @param calls The opaque call handler.
     * @return The outcome of the execution (Normal or Stopped).
     */
    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input, Memory memory, Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        // Create a holder for the current MXCSR state, initialized from input
        final QueueFp604Api.Mxcsr[] mxcsrHolder = new QueueFp604Api.Mxcsr[1];
        mxcsrHolder[0] = input.mxcsr();

        // Create the narrow 578 API calls adapter that routes to the new 637 calls
        EmbeddedElements578Api.Calls narrow578Calls = new EmbeddedElements578Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(EmbeddedElements578Api.CallFrame frame) {
                // Wrap the original frame with the current MXCSR
                CallFrame newFrame = new CallFrame(frame, mxcsrHolder[0]);

                // Invoke the new 637 calls handler
                QueueFp604Api.Outcome offered = calls.invoke(newFrame);

                if (offered instanceof QueueFp604Api.Normal normal) {
                    // Validate the normal return against the original 578 frame expectations
                    frame.checkNormalReturn(normal.base());

                    // Update the MXCSR holder with the post-state MXCSR
                    mxcsrHolder[0] = normal.postMxcsr();

                    // Return the base CallResult to the old body
                    return normal.base();
                } else if (offered instanceof QueueFp604Api.Stopped stopped) {
                    // Throw a carrier exception to bypass the old body continuation
                    throw new StoppedCarrier(stopped);
                } else {
                    throw new NullPointerException("Null outcome");
                }
            }
        };

        try {
            // Execute the mature 322-byte body exactly once
            FullCopy437Api.CallResult result = EmbeddedElementsFullState37282B0.execute(
                input.base(),
                memory,
                narrow578Calls
            );

            // Wrap the result with the current MXCSR state
            return new QueueFp604Api.Normal(result, mxcsrHolder[0]);
        } catch (StoppedCarrier carrier) {
            // Return the exact Stopped outcome immediately
            return carrier.stopped;
        }
    }

    /**
     * Binds the 172-byte function execution to the 322-byte function's call handler.
     * @param memory The shared memory view.
     * @param lower172 The opaque call handler for the 172-byte function.
     * @param foreign The opaque call handler for the other five calls in the 322-byte function.
     * @return A Calls instance that routes the 37283B6 call to the 172-byte function.
     */
    public static Calls bind172(Memory memory, Element172Fp636Api.Calls lower172, Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(lower172);
        Objects.requireNonNull(foreign);

        return new Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(CallFrame frame) {
                Objects.requireNonNull(frame);
                EmbeddedElements578Api.CallFrame original = frame.original();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();

                // Check if this is the call to the 172-byte function at site 0x37283B6
                GovernmentCrtBoundary185Api.Call call = original.call();
                if (call.callSiteRva() == 0x37283B6L &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0x37297F0L) {

                    // Execute the 172-byte function exactly once
                    Element172Fp636Api.Input input172 = new Element172Fp636Api.Input(
                        original.childEntry(),
                        original.directionFlagSet(),
                        preMxcsr
                    );

                    QueueFp604Api.Outcome result = Element172FullState636.execute(
                        input172,
                        memory,
                        lower172
                    );

                    if (result instanceof QueueFp604Api.Normal normal) {
                        // Validate the original 578 frame against the actual base
                        original.checkNormalReturn(normal.base());
                        // Return the same offered outcome
                        return result;
                    } else if (result instanceof QueueFp604Api.Stopped stopped) {
                        // Return the same Stopped identity without fake NR
                        return result;
                    } else {
                        throw new NullPointerException("Null outcome");
                    }
                } else {
                    // Route to the foreign handler for the other five legal ports
                    QueueFp604Api.Outcome offered = foreign.invoke(frame);
                    if (offered == null) {
                        throw new NullPointerException("Null outcome");
                    }
                    return offered;
                }
            }
        };
    }

    /**
     * Private exception carrier for Stopped outcomes to bypass the old body continuation.
     */
    private static final class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped stopped;

        StoppedCarrier(QueueFp604Api.Stopped stopped) {
            this.stopped = stopped;
        }
    }
}
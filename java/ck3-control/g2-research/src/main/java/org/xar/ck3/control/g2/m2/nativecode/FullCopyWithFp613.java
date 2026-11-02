package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Input;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Mxcsr;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Normal;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Outcome;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api.Stopped;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy4226860;

/**
 * COPY-specific FP carrier around the supplied actual FullCopy4226860.
 * Known family/REP instructions are integer/move/copy/branch/fence operations with no FP arithmetic/control writes.
 * Unknown tails are handled via explicit nonlocal transfer to preserve Outcome identity.
 */
public final class FullCopyWithFp613 {
    private FullCopyWithFp613() { }

    /**
     * Wrapper for a tail call frame carrying the original FullCopy437Api.TailFrame and the pre-call MXCSR state.
     */
    public record TailCall(FullCopy437Api.TailFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public TailCall {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    /**
     * Functional interface for handling tail calls in the COPY context.
     */
    @FunctionalInterface
    public interface TailCalls {
        Outcome tail(TailCall frame);
    }

    /**
     * Private exception used to propagate the Outcome from a tail call back to the execute method.
     * This allows the bridge to intercept the tail call and return the Outcome directly without
     * manufacturing a legacy normal return or processing continuation.
     */
    private static final class TailOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final Outcome outcome;

        TailOutcomeException(Outcome outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Executes the COPY logic with FP awareness.
     * @param input The FP input containing the base FullCopy437Api.Input and MXCSR state.
     * @param memory The owned memory view.
     * @param tails The handler for unknown tail calls.
     * @return The Outcome (Normal or Stopped) resulting from the execution.
     */
    public static Outcome execute(Input input, FullCopy437Api.Memory memory, TailCalls tails) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(tails);

        // Narrow Calls implementation that throws for invoke/readGs and handles tail via exception
        FullCopy437Api.Calls calls = new FullCopy437Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(FullCopy437Api.CallFrame frame) {
                throw new UnsupportedOperationException("No invoke in COPY bridge");
            }

            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("No GS read in COPY bridge");
            }

            @Override
            public FullCopy437Api.CallResult tail(FullCopy437Api.TailFrame frame) {
                // Pass the EXACT original TailFrame and SAME incomingMxcsr to tails.tail
                Outcome result = tails.tail(new TailCall(frame, input.mxcsr()));
                if (result == null) {
                    throw new NullPointerException("Tail callback returned null");
                }
                // Throw to propagate the Outcome back to execute
                throw new TailOutcomeException(result);
            }
        };

        try {
            // Execute the actual FullCopy4226860 with the narrow calls
            FullCopy437Api.CallResult result = FullCopy4226860.execute(input.base(), memory, calls);

            // Normal completion wholly in known family: wrap exact original CallResult with SAME input.mxcsr
            return new Normal(result, input.mxcsr());
        } catch (TailOutcomeException e) {
            // Return the explicit Outcome from the tail call unchanged
            return e.outcome;
        }
    }
}
package org.xar.ck3.research.m3.tail6874fp272;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m3.tail6670fp271.Tail6670Fp271Api;
import org.xar.ck3.research.m3.tail6874fp272.Tail6874FullState272;

/**
 * Binder for the tail transfer from 0x42566F6 to 0x4256874.
 * Implements Tail6670Fp271Api.Calls by delegating to Tail6874FullState272.execute.
 */
public final class Tail6874From6670272 {
    private Tail6874From6670272() { }

    public static Tail6670Fp271Api.Calls bind(FullCopy437Api.Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);

        return new Tail6670Fp271Api.Calls() {
            @Override
            public QueueFp604Api.Outcome tail(Tail6670Fp271Api.TailFrame frame) {
                Objects.requireNonNull(frame);

                // Construct the input for the core execution using the frame's entry, DF, and MXCSR
                FullCopy437Api.Input baseInput = new FullCopy437Api.Input(
                    frame.original().entry(),
                    frame.directionFlagSet(),
                    budget
                );
                QueueFp604Api.Input input = new QueueFp604Api.Input(baseInput, frame.preMxcsr());

                // Execute the core logic exactly once
                QueueFp604Api.Normal result = Tail6874FullState272.execute(input, memory);

                // Validate the normal return against the frame's expectations
                frame.checkNormalReturn(result);

                // Return the same Normal object
                return result;
            }
        };
    }
}
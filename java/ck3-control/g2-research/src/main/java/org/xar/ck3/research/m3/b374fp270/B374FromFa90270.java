package org.xar.ck3.research.m3.b374fp270;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.research.m3.b374fp270.B374Fp270Api;
import org.xar.ck3.research.m3.b374fp270.B374FullState270;

/**
 * Binder for the FA90 context that routes the specific 424FAD3 call site to the B374 implementation.
 * Other FA90 call sites are delegated to the foreign calls interface.
 */
public final class B374FromFa90270 {
    private B374FromFa90270() { }

    public static Fa90Fp267Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            B374Fp270Api.Calls calls,
            Fa90Fp267Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);

        return new Fa90Fp267Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Fa90Fp267Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                long site = frame.original().callSiteRva();

                if (site == 0x424FAD3L) {
                    // Exact selected source 424FAD3 DIRECT 42566FC
                    // Construct 604.Input from actual 267 frame childEntry/DF/preMxcsr and same budget
                    QueueFp604Api.Input input = new QueueFp604Api.Input(
                        new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            budget
                        ),
                        frame.preMxcsr()
                    );

                    // Execute B374FullState270 once with same Memory
                    QueueFp604Api.Outcome outcome = B374FullState270.execute(input, memory, calls);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        // If Normal, check frame return
                        frame.checkNormalReturn(normal);
                    }
                    // Return same Outcome (Normal or Stopped)
                    return outcome;
                } else {
                    // All other legal 267 frames foreign once exact same frame/nonnull same Outcome
                    return Objects.requireNonNull(foreign.invoke(frame));
                }
            }
        };
    }
}
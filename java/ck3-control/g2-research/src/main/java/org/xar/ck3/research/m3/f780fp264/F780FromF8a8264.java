package org.xar.ck3.research.m3.f780fp264;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8Fp263Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8FullState263;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Only the actual F955 edge selects the represented264 child on the same storage.
 * No implementation of the child itself, no memory effects, no validation of foreign outcomes.
 */
public final class F780FromF8a8264 {
    private F780FromF8a8264() { }

    /**
     * Binds the new F780 child into the F8A8 call flow.
     * @param memory The shared FullCopy437Api.Memory.
     * @param budget The shared GovernmentCrtBoundary185Api.LoopBudget.
     * @param calls The new F780Fp264Api.Calls implementation (assumed available in package).
     * @param foreign The existing F8A8 F8a8Fp263Api.Calls implementation.
     * @return A F8a8Fp263Api.Calls that delegates to the new child only for the specific F955 call.
     */
    public static F8a8Fp263Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            F780Fp264Api.Calls calls,
            F8a8Fp263Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);

        return new F8a8Fp263Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(F8a8Fp263Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call original = frame.original();

                // Check if this is the specific call to 424F780 from site 424F955
                if (original.callSiteRva() == 0x424F955L
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x424F780L) {

                    // Construct the input for the new F780 child
                    QueueFp604Api.Input input = new QueueFp604Api.Input(
                        new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            budget
                        ),
                        frame.preMxcsr()
                    );

                    // Execute the new child using the same memory and the new calls
                    QueueFp604Api.Outcome outcome = F780FullState264.execute(input, memory, calls);

                    // Validate the outcome against the original frame expectations
                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal);
                    }

                    return outcome;
                }

                // Delegate all other frames to the foreign implementation
                return Objects.requireNonNull(foreign.invoke(frame));
            }
        };
    }
}
package org.xar.ck3.research.m3.f800fp265;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f8a8fp263.F8a8Fp263Api;
import org.xar.ck3.research.m3.f800fp265.F800FullState265;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Only the actual F96A edge selects the represented69 child on the same storage.
 * No implementation of the child body is provided here; this class binds the edge.
 */
public final class F800FromF8a8265 {
    private F800FromF8a8265() { }

    /**
     * Binds the new F800 child to the existing F8A8 caller context.
     * @param memory The shared storage view.
     * @param budget The loop budget for the child.
     * @param calls The new F800 calls interface (opaque).
     * @param foreign The existing F8A8 calls interface for other edges.
     * @return A Calls implementation that routes F96A to the new child and others to foreign.
     */
    public static F8a8Fp263Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            F800Fp265Api.Calls calls,
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

                // Check if this is the specific F96A edge targeting 424F800
                if (original.callSiteRva() == 0x424F96AL
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x424F800L) {

                    // Construct the input for the new child execution
                    QueueFp604Api.Input input = new QueueFp604Api.Input(
                        new FullCopy437Api.Input(
                            frame.childEntry(),
                            frame.directionFlagSet(),
                            budget
                        ),
                        frame.preMxcsr()
                    );

                    // Execute the new child exactly once
                    QueueFp604Api.Outcome outcome = F800FullState265.execute(input, memory, calls);

                    // Validate the selected Normal return against the original frame
                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal);
                    }

                    return outcome;
                }

                // All other legal frames go once to supplied foreign
                return Objects.requireNonNull(foreign.invoke(frame));
            }
        };
    }
}
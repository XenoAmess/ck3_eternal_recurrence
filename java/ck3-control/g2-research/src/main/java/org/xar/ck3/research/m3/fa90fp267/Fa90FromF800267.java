package org.xar.ck3.research.m3.fa90fp267;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.f800fp265.F800Fp265Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90FullState267;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Only the actual 424F82D edge selects the represented267 child on the same storage.
 * No implementation of the child body is provided here; this class binds the edge.
 */
public final class Fa90FromF800267 {
    private Fa90FromF800267() { }

    /**
     * Binds the new Fa90 child to the existing F800 caller context.
     * @param memory The shared storage view.
     * @param budget The loop budget for the child.
     * @param calls The new Fa90 calls interface (opaque).
     * @param foreign The existing F800 calls interface for other edges.
     * @return A Calls implementation that routes 424F82D to the new child and others to foreign.
     */
    public static F800Fp265Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Fa90Fp267Api.Calls calls,
            F800Fp265Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);

        return new F800Fp265Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(F800Fp265Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call original = frame.original();

                // Check if this is the specific 424F82D edge targeting 424FA90
                if (original.callSiteRva() == 0x424F82DL
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x424FA90L) {

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
                    QueueFp604Api.Outcome outcome = Fa90FullState267.execute(input, memory, calls);

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
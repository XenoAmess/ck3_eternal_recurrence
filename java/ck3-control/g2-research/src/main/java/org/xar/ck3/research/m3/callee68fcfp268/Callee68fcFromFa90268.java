package org.xar.ck3.research.m3.callee68fcfp268;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.fa90fp267.Fa90Fp267Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFp268Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFullState268;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Only the actual 424FAAC edge selects the represented268 child on the same storage.
 * No implementation of the child body is provided here; this class binds the edge.
 */
public final class Callee68fcFromFa90268 {
    private Callee68fcFromFa90268() { }

    /**
     * Binds the new Callee68fc child to the existing Fa90 caller context.
     * @param memory The shared storage view.
     * @param budget The loop budget for the child.
     * @param calls The new Callee68fc calls interface (opaque).
     * @param foreign The existing Fa90 calls interface for other edges.
     * @return A Calls implementation that routes 424FAAC to the new child and others to foreign.
     */
    public static Fa90Fp267Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Callee68fcFp268Api.Calls calls,
            Fa90Fp267Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(foreign);

        return new Fa90Fp267Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Fa90Fp267Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call original = frame.original();

                // Check if this is the specific 424FAAC edge targeting 42568FC
                if (original.callSiteRva() == 0x424FAACL
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x42568FCL) {

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
                    QueueFp604Api.Outcome outcome = Callee68fcFullState268.execute(input, memory, calls);

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
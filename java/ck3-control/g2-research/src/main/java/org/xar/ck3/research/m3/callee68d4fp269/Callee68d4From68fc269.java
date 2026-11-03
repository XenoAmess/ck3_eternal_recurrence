package org.xar.ck3.research.m3.callee68d4fp269;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.callee68fcfp268.Callee68fcFp268Api;
import org.xar.ck3.research.m3.callee68d4fp269.Callee68d4FullState269;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Only the actual 425699A edge selects the represented269 child on the same storage.
 * No implementation of the child body is provided here; this class binds the edge.
 */
public final class Callee68d4From68fc269 {
    private Callee68d4From68fc269() { }

    /**
     * Binds the new Callee68d4 child to the existing Callee68fc caller context.
     * @param memory The shared storage view.
     * @param budget The loop budget for the child.
     * @return A Calls implementation that routes 425699A to the new child.
     */
    public static Callee68fcFp268Api.Calls bind(FullCopy437Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);

        return new Callee68fcFp268Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Callee68fcFp268Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call original = frame.original();

                // Check if this is the specific 425699A edge targeting 42568D4
                if (original.callSiteRva() == 0x425699AL
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x42568D4L) {

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
                    QueueFp604Api.Normal normal = Callee68d4FullState269.execute(input, memory);

                    // Validate the selected Normal return against the original frame
                    frame.checkNormalReturn(normal);

                    return normal;
                }

                // The supplied268 CallFrame itself permits only actual direct site425699A target42568D4.
                // If the frame is valid, it must match the condition above. If not, it's an invalid frame
                // which should have been rejected by the CallFrame constructor or invoke contract.
                // However, to be safe and explicit as per "No foreign fallback", we throw if not matching.
                throw new IllegalArgumentException("Invalid call frame for Callee68d4From68fc269");
            }
        };
    }
}
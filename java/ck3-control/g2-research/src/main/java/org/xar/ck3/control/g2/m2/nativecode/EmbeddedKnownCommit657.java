package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFp637;
import org.xar.ck3.control.g2.m2.nativecode.Dbdb80Fp656Api;
import org.xar.ck3.control.g2.m2.nativecode.Dbdb80WithFp656;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;

/**
 * Owner-required public shape for binding the known DBDB80 commit execution
 * into the EmbeddedElementsFp637 call handler.
 */
public final class EmbeddedKnownCommit657 {
    private EmbeddedKnownCommit657() { }

    /**
     * Nested public Memory extends EmbeddedElementsFp637.Memory and Dbdb80Fp656Api.Memory.
     */
    public interface Memory extends EmbeddedElementsFp637.Memory, Dbdb80Fp656Api.Memory {
    }

    /**
     * Binds the known DBDB80 commit execution to the parent call handler.
     * @param memory The shared memory view.
     * @param budget The loop budget for the child execution.
     * @param commitCalls The opaque call handler for the DBDB80 body.
     * @param foreign The opaque call handler for other parent calls.
     * @return A Calls instance that routes the 372836C call to the DBDB80 body.
     */
    public static EmbeddedElementsFp637.Calls bind(Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            Dbdb80Fp656Api.Calls commitCalls, EmbeddedElementsFp637.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(commitCalls);
        Objects.requireNonNull(foreign);

        return new EmbeddedElementsFp637.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(EmbeddedElementsFp637.CallFrame frame) {
                Objects.requireNonNull(frame);
                EmbeddedElements578Api.CallFrame original = frame.original();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();

                GovernmentCrtBoundary185Api.Call call = original.call();
                if (call.callSiteRva() == 0x372836CL &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0xDBDB80L &&
                    original.instructionLength() == 5 &&
                    original.returnRipBits() == original.childEntry().imageBaseBits() + 0x3728371L) {

                    // Execute the DBDB80 body exactly once
                    QueueFp604Api.Input input = new QueueFp604Api.Input(
                        new FullCopy437Api.Input(
                            original.childEntry(),
                            original.directionFlagSet(),
                            budget
                        ),
                        preMxcsr
                    );

                    QueueFp604Api.Outcome result = Dbdb80WithFp656.execute(
                        input,
                        memory,
                        commitCalls
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
                    // Route to the foreign handler for the other legal ports
                    QueueFp604Api.Outcome offered = foreign.invoke(frame);
                    if (offered == null) {
                        throw new NullPointerException("Null outcome");
                    }
                    return offered;
                }
            }
        };
    }
}
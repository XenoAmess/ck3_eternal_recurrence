package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedElementsFp637;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32Copy581Api;
import org.xar.ck3.control.g2.m2.nativecode.Embedded32FullState3727180;

public final class Embedded32Fp659 {
    private Embedded32Fp659() { }

    public interface Memory extends EmbeddedElementsFp637.Memory {
    }

    public record CallFrame(Embedded32Copy581Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(preMxcsr);
        }
    }

    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }

    public static QueueFp604Api.Outcome execute(QueueFp604Api.Input input, Memory memory, Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        final QueueFp604Api.Mxcsr[] mxcsrHolder = new QueueFp604Api.Mxcsr[1];
        mxcsrHolder[0] = input.mxcsr();

        Embedded32Copy581Api.Calls narrow581Calls = new Embedded32Copy581Api.Calls() {
            @Override
            public FullCopy437Api.CallResult invoke(Embedded32Copy581Api.CallFrame frame) {
                CallFrame newFrame = new CallFrame(frame, mxcsrHolder[0]);
                QueueFp604Api.Outcome offered = calls.invoke(newFrame);

                if (offered == null) {
                    throw new NullPointerException("Null outcome");
                }

                if (offered instanceof QueueFp604Api.Normal normal) {
                    frame.checkNormalReturn(normal.base());
                    mxcsrHolder[0] = normal.postMxcsr();
                    return normal.base();
                } else if (offered instanceof QueueFp604Api.Stopped stopped) {
                    throw new StoppedCarrier(stopped);
                } else {
                    throw new NullPointerException("Unknown outcome");
                }
            }
        };

        try {
            FullCopy437Api.CallResult result = Embedded32FullState3727180.execute(
                input.base(),
                memory,
                narrow581Calls
            );
            return new QueueFp604Api.Normal(result, mxcsrHolder[0]);
        } catch (StoppedCarrier carrier) {
            return carrier.stopped;
        }
    }

    /**
     * Routes the selected elements call using the captured shared objects.
     * Pass the returned handler to execute with these same Memory and LoopBudget
     * instances; other legal calls are delegated to the supplied foreign handler.
     */
    public static Calls bindElements(Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget,
            EmbeddedElementsFp637.Calls elements, Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(elements);
        Objects.requireNonNull(foreign);

        return new Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(CallFrame frame) {
                Objects.requireNonNull(frame);
                Embedded32Copy581Api.CallFrame original = frame.original();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();

                GovernmentCrtBoundary185Api.Call call = original.call();
                if (call.callSiteRva() == 0x37272F0L &&
                    call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA &&
                    call.targetBits() == 0x37282B0L) {

                    QueueFp604Api.Input input637 = new QueueFp604Api.Input(
                        new FullCopy437Api.Input(
                            original.childEntry(),
                            original.directionFlagSet(),
                            budget
                        ),
                        preMxcsr
                    );

                    QueueFp604Api.Outcome result = EmbeddedElementsFp637.execute(
                        input637,
                        memory,
                        elements
                    );

                    if (result instanceof QueueFp604Api.Normal normal) {
                        original.checkNormalReturn(normal.base());
                        return result;
                    } else if (result instanceof QueueFp604Api.Stopped stopped) {
                        return result;
                    } else {
                        throw new NullPointerException("Null outcome");
                    }
                } else {
                    QueueFp604Api.Outcome offered = foreign.invoke(frame);
                    if (offered == null) {
                        throw new NullPointerException("Null outcome");
                    }
                    return offered;
                }
            }
        };
    }

    private static final class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped stopped;

        StoppedCarrier(QueueFp604Api.Stopped stopped) {
            this.stopped = stopped;
        }
    }
}
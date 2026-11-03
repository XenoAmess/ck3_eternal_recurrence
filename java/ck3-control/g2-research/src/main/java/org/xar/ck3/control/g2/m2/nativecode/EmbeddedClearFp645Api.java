package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;

/** Current MXCSR and explicit complete outcomes for the actual held93 virtual port. */
public final class EmbeddedClearFp645Api {
    private EmbeddedClearFp645Api() { }

    public record CallFrame(EmbeddedClear587Api.CallFrame original, QueueFp604Api.Mxcsr preMxcsr) {
        public CallFrame { Objects.requireNonNull(original); Objects.requireNonNull(preMxcsr); }

        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            original.checkNormalReturn(actual.base());
        }
    }

    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}

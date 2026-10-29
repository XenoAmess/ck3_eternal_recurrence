package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import java.util.Objects;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanCodec;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.Observation;

/** Reuses the exact native loan-cost producer. Final gates alone never become principal, debt or funding. */
public final class M4LoanInputProducer {
    private M4LoanInputProducer() { }

    public static final class ProducedObservation {
        private final Observation observation;
        private final byte[] utf8;

        private ProducedObservation(Observation observation) {
            this.observation = Objects.requireNonNull(observation); this.utf8 = HolyLoanCodec.encode(observation);
        }

        public Observation observation() { return observation; }
        public byte[] utf8() { return utf8.clone(); }
    }

    public static ProducedObservation produce(byte[] nativeProviderUtf8, ExpectedFrame expectedFrame) {
        Objects.requireNonNull(expectedFrame, "actual owner's bound frame");
        return new ProducedObservation(HolyLoanCodec.project(nativeProviderUtf8, expectedFrame));
    }

    /** External integer tokens are validated before the shared ExpectedFrame is constructed. No new wrapper schema. */
    public static ProducedObservation produce(byte[] nativeProviderUtf8, byte[] expectedFrameUtf8) {
        return produce(nativeProviderUtf8, HolyLoanCodec.decodeExpectedFrame(expectedFrameUtf8));
    }
}

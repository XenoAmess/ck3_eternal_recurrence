package org.xar.ck3.control.wave3.runtime.processcustody;

import org.junit.jupiter.api.Test;

/** Keep the same focused producer/serialization regression on the default Maven test path. */
public final class ProcessCustodyExceptionSerializationTest {
    @Test void typedObservationAndThrowableDiagnosticsSurviveSerialization() throws Exception {
        ProcessCustodyExceptionSerializationVerification.main(new String[0]);
    }
}

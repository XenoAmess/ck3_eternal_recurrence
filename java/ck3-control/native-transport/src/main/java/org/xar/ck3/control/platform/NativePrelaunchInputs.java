package org.xar.ck3.control.platform;

import java.io.IOException;
import java.time.Clock;
import java.util.Objects;

/** Checks the operation timeout; launch no longer repeats source or profile provenance checks. */
public final class NativePrelaunchInputs {
    private NativePrelaunchInputs() { }
    public static void requireCurrent(NativeLaunchPlan actual,Clock clock)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(clock);
        if(!clock.instant().isBefore(actual.deadline()))throw new IOException("actual prelaunch plan deadline expired");
    }
}

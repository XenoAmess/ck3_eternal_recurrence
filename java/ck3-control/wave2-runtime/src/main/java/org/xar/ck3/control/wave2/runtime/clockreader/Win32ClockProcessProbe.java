package org.xar.ck3.control.wave2.runtime.clockreader;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.reconciliation.LateOutcome.ProcessIdentity;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.KernelProcessProbe;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockReaderPorts.ProcessObservation;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityReader;

/** Reuses the shared qualified held-HANDLE GetProcessTimes/Image/GetTickCount64 reader. */
public final class Win32ClockProcessProbe implements KernelProcessProbe {
    private final ProcessIdentityReader reader;
    public Win32ClockProcessProbe(ProcessIdentityReader reader) { this.reader = Objects.requireNonNull(reader); }
    @Override public ProcessObservation observe(long pid) throws IOException {
        var actual = reader.observe(pid);
        return new ProcessObservation(new ProcessIdentity(actual.pid(), new CrossJsDecimalUInt64(actual.creationFiletimeDecimal())),
                actual.executable(), new CrossJsDecimalUInt64(actual.uptimeMillisDecimal()));
    }
}

package org.xar.ck3.control.wave2.runtime.stdioidentity;

import java.nio.file.Path;
import java.time.Instant;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsJobProcess.LiveProcessObservation;
import org.xar.ck3.control.build.WindowsJobProcess.ProcessIdentity;
import org.xar.ck3.control.wave2.runtime.stdioidentity.IdentityUnavailableException.Reason;

/** Reuses the single shared Win32 implementation and its held-handle live checks. */
public final class Win32ProcessIdentityReader implements ProcessIdentityReader {
    @Override
    public MeasuredProcessIdentity observe(long pid) throws IdentityUnavailableException {
        if (pid < 1 || pid > 0xffff_ffffL) {
            throw new IdentityUnavailableException(Reason.INVALID_PID, "positive DWORD PID required");
        }
        try {
            LiveProcessObservation observed = WindowsJobProcess.observeLiveProcess(pid);
            ProcessIdentity identity = observed.identity();
            return new MeasuredProcessIdentity(new ProcessIdentityClaimV1(identity.pid(),
                    identity.creationFiletimeDecimal(), Path.of(identity.executable())),
                    observed.uptimeMillisDecimal(), Instant.now());
        } catch (UnsupportedOperationException error) {
            throw new IdentityUnavailableException(Reason.NATIVE_UNAVAILABLE,
                    "actual Windows process observation is unavailable", error);
        } catch (RuntimeException error) {
            throw new IdentityUnavailableException(Reason.PROCESS_UNAVAILABLE,
                    "process is absent, exited, inaccessible or could not be measured", error);
        }
    }
}

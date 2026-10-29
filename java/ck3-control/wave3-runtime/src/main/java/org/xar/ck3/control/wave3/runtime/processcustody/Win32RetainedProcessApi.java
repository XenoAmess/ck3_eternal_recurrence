package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import java.nio.file.Path;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsJobProcess.ReadOnlyProcessHandle;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;

/** Thin adapter over the shared retained Win32 query handle; never copies native bindings. */
public final class Win32RetainedProcessApi implements RetainedProcessApi {
    @Override
    public Handle open(long pid) throws IOException {
        try {
            ReadOnlyProcessHandle actual = WindowsJobProcess.retainReadOnlyProcess(pid);
            try { return new OwnedQueryHandle(actual); }
            catch (RuntimeException | Error error) {
                try { actual.close(); }
                catch (RuntimeException | Error closeError) {
                    if (closeError != error) { error.addSuppressed(closeError); }
                }
                throw error;
            }
        }
        catch (RuntimeException error) { throw unavailable("retain actual query handle", error); }
    }

    private static final class OwnedQueryHandle implements Handle {
        private final ReadOnlyProcessHandle actual;
        private final ProcessIdentityClaimV1 identity;

        private OwnedQueryHandle(ReadOnlyProcessHandle actual) {
            this.actual = actual;
            var measured = actual.identity();
            this.identity = new ProcessIdentityClaimV1(measured.pid(), measured.creationFiletimeDecimal(),
                    Path.of(measured.executable()));
        }

        @Override public ProcessIdentityClaimV1 identity() { return identity; }
        @Override public long waitZero() throws IOException {
            try { return actual.waitZero(); }
            catch (RuntimeException error) { throw unavailable("read actual held wait result", error); }
        }
        @Override public long exitCode() throws IOException {
            try { return actual.exitCode(); }
            catch (RuntimeException error) { throw unavailable("read actual held exit code", error); }
        }
        @Override public void close() throws IOException {
            try { actual.close(); }
            catch (RuntimeException error) { throw unavailable("close actual held query handle", error); }
        }
    }

    private static IOException unavailable(String stage, RuntimeException error) {
        return new IOException("could not " + stage, error);
    }
}

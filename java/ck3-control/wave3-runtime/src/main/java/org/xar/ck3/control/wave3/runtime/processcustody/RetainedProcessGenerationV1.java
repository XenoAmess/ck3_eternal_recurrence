package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.IOException;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ErrorStage;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ObservationError;

/** One retained query/synchronize handle. It has no process creation/termination authority. */
public final class RetainedProcessGenerationV1 implements AutoCloseable {
    private final RetainedProcessApi.Handle handle;
    private final ProcessIdentityClaimV1 identity;
    private boolean closed;

    private RetainedProcessGenerationV1(RetainedProcessApi.Handle handle, ProcessIdentityClaimV1 identity) {
        this.handle = handle; this.identity = identity;
    }

    public static RetainedProcessGenerationV1 capture(ProcessExpectationV1 expected,
            RetainedProcessApi api) throws IOException {
        Objects.requireNonNull(expected); Objects.requireNonNull(api);
        RetainedProcessApi.Handle handle = Objects.requireNonNull(api.open(expected.pid()), "retained handle required");
        try {
            ProcessIdentityClaimV1 identity = Objects.requireNonNull(handle.identity());
            if (identity.pid() != expected.pid()
                    || expected.creationFiletimeDecimal().isPresent()
                        && !expected.creationFiletimeDecimal().orElseThrow().equals(identity.creationFiletimeDecimal())
                    || expected.executable().isPresent()
                        && !image(expected.executable().orElseThrow().toString()).equals(image(identity.executable().toString()))) {
                throw new IOException("actual captured generation or image differs from expectation");
            }
            return new RetainedProcessGenerationV1(handle, identity);
        } catch (IOException | RuntimeException | Error error) {
            try { handle.close(); }
            catch (IOException | RuntimeException | Error closeError) {
                if (closeError != error) { error.addSuppressed(closeError); }
            }
            throw error;
        }
    }

    public static RetainedProcessGenerationV1 system(ProcessExpectationV1 expected) throws IOException {
        return capture(expected, new Win32RetainedProcessApi());
    }

    public ProcessIdentityClaimV1 identity() { return identity; }

    public synchronized ProcessObservationV1 observe() {
        if (closed) {
            return failed(OptionalLong.empty(), KernelSignal.UNKNOWN, ErrorStage.CLOSED,
                    new IllegalStateException("retained handle is closed"));
        }
        OptionalLong wait = OptionalLong.empty();
        KernelSignal signal;
        try {
            long actual = handle.waitZero();
            wait = OptionalLong.of(actual);
            if (actual != 0 && actual != 258) {
                throw new IOException("unexpected native wait result: " + actual);
            }
            signal = actual == 0 ? KernelSignal.SIGNALED : KernelSignal.UNSIGNALED;
        } catch (IOException | RuntimeException error) {
            return failed(wait, KernelSignal.UNKNOWN, ErrorStage.WAIT, error);
        }
        try {
            long exit = handle.exitCode();
            if (exit < 0 || exit > 0xffff_ffffL) { throw new IOException("actual exit code is not a DWORD"); }
            return new ProcessObservationV1(identity, wait, signal, OptionalLong.of(exit), Optional.empty());
        } catch (IOException | RuntimeException error) {
            return failed(wait, signal, ErrorStage.EXIT_CODE, error);
        }
    }

    public ProcessObservationV1 requireLive() throws ProcessCustodyUnavailableException {
        ProcessObservationV1 result = observe();
        if (result.signal() != KernelSignal.UNSIGNALED || result.error().isPresent()) {
            throw new ProcessCustodyUnavailableException("retained generation is not verified live", result);
        }
        return result;
    }

    @Override
    public synchronized void close() throws IOException {
        if (closed) { return; }
        closed = true;
        handle.close();
    }

    private ProcessObservationV1 failed(OptionalLong wait, KernelSignal signal, ErrorStage stage, Exception error) {
        String message = error.getMessage() == null ? error.toString() : error.getMessage();
        return new ProcessObservationV1(identity, wait, signal, OptionalLong.empty(), Optional.of(
                new ObservationError(stage, error.getClass().getSimpleName(), message)));
    }

    private static String image(String path) { return path.replace('/', '\\').toLowerCase(Locale.ROOT); }
}

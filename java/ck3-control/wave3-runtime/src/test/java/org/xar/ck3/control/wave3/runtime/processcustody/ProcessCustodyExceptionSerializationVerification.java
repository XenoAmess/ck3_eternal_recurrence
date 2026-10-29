package org.xar.ck3.control.wave3.runtime.processcustody;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.xar.ck3.control.wave2.runtime.stdioidentity.ProcessIdentityClaimV1;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ErrorStage;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.KernelSignal;
import org.xar.ck3.control.wave3.runtime.processcustody.ProcessObservationV1.ObservationError;

/** Actual requireLive and serialization code, with explicitly synthetic query-only handles. */
public final class ProcessCustodyExceptionSerializationVerification {
    private ProcessCustodyExceptionSerializationVerification() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 0) { throw new IllegalArgumentException("no live process input accepted"); }
        ProcessIdentityClaimV1 identity = new ProcessIdentityClaimV1(17, "18446744073709551615",
                Path.of("synthetic-process-identity.exe").toAbsolutePath());
        int live = 0, unavailable = 0;
        for (Scenario scenario : List.of(new Scenario(258, 259, false, false, false),
                new Scenario(258, 0, false, false, false), new Scenario(0, 259, false, false, false),
                new Scenario(0, 0, false, false, false), new Scenario(258, 259, true, false, false),
                new Scenario(0, 259, false, true, false), new Scenario(258, 259, false, false, true),
                new Scenario(1234, 259, false, false, false))) {
            FakeHandle handle = new FakeHandle(identity, scenario);
            RetainedProcessGenerationV1 generation = RetainedProcessGenerationV1.capture(ProcessExpectationV1.exact(identity), pid -> handle);
            try {
                if (scenario.closed()) { generation.close(); }
                try {
                    ProcessObservationV1 observation = generation.requireLive();
                    if (observation.signal() != KernelSignal.UNSIGNALED || observation.error().isPresent()) {
                        throw new AssertionError("native signal no longer decides liveness");
                    }
                    live++;
                } catch (ProcessCustodyUnavailableException original) {
                    original.initCause(new IOException("retained cause marker"));
                    original.addSuppressed(new IllegalStateException("retained suppressed marker"));
                    ProcessCustodyUnavailableException restored = roundtrip(original);
                    if (!original.observation().equals(restored.observation())
                            || !Arrays.equals(LegacyProcessObservationCodecV1.encode(original.observation()),
                                    LegacyProcessObservationCodecV1.encode(restored.observation()))) {
                        throw new AssertionError("typed diagnostic or original JSON error/status representation changed");
                    }
                    if (!original.getMessage().equals(restored.getMessage())
                            || !Arrays.equals(original.getStackTrace(), restored.getStackTrace())
                            || !restored.getCause().getMessage().equals("retained cause marker")
                            || restored.getSuppressed().length != 1
                            || !restored.getSuppressed()[0].getMessage().equals("retained suppressed marker")) {
                        throw new AssertionError("IOException diagnostics were not retained");
                    }
                    unavailable++;
                }
            } finally { generation.close(); }
            if (handle.closes != 1) { throw new AssertionError("original query-only handle must close once"); }
        }
        if (live != 2 || unavailable != 6) { throw new AssertionError("original producer failure paths were not all reached"); }
        ProcessObservationV1 large = new ProcessObservationV1(identity, OptionalLong.empty(), KernelSignal.UNKNOWN,
                OptionalLong.empty(), Optional.of(new ObservationError(ErrorStage.WAIT, "SyntheticReadFailure", "界".repeat(32_768))));
        if (!large.equals(roundtrip(new ProcessCustodyUnavailableException("large typed diagnostic", large)).observation())) {
            throw new AssertionError("valid typed Unicode diagnostic was truncated or dropped");
        }
        System.out.println("{\"schema\":\"xar.process-custody-exception-serialization-test/v1\",\"synthetic_handles\":true,\"require_live_cases\":8,\"live_cases\":2,\"unavailable_cases\":6,\"serialization_roundtrips\":7,\"game_calls\":0,\"native_handle_opens\":0}");
    }
    private static ProcessCustodyUnavailableException roundtrip(ProcessCustodyUnavailableException original) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream output = new ObjectOutputStream(bytes)) { output.writeObject(original); }
        try (ObjectInputStream input = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()))) {
            Object restored = input.readObject();
            if (!(restored instanceof ProcessCustodyUnavailableException result)) { throw new AssertionError("wrong restored exception type"); }
            return result;
        }
    }
    private record Scenario(long waitResult, long exitCode, boolean failWait, boolean failExit, boolean closed) { }
    private static final class FakeHandle implements RetainedProcessApi.Handle {
        private final ProcessIdentityClaimV1 identity;
        private final Scenario scenario;
        private int closes;
        private FakeHandle(ProcessIdentityClaimV1 identity, Scenario scenario) { this.identity = identity; this.scenario = scenario; }
        @Override public ProcessIdentityClaimV1 identity() { return identity; }
        @Override public long waitZero() throws IOException {
            if (scenario.failWait()) { throw new IOException("synthetic native wait error code5"); }
            return scenario.waitResult();
        }
        @Override public long exitCode() throws IOException {
            if (scenario.failExit()) { throw new IOException("synthetic native exit query code6"); }
            return scenario.exitCode();
        }
        @Override public void close() { closes++; }
    }
}

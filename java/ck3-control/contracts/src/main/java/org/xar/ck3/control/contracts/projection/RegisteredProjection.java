package org.xar.ck3.control.contracts.projection;

import java.util.Objects;
import java.util.Optional;

/** Generic capture keeps decode -> typed application -> typed encoder connected without casts. */
public final class RegisteredProjection {
    @FunctionalInterface private interface Executor { ProjectionResult execute(ProjectionCall call); }
    private final ProjectionOperation operation;
    private final int inputMaximumBytes;
    private final int outputMaximumBytes;
    private final Executor executor;
    private RegisteredProjection(ProjectionOperation operation, int inputMaximumBytes, int outputMaximumBytes, Executor executor) {
        this.operation = operation; this.inputMaximumBytes = inputMaximumBytes; this.outputMaximumBytes = outputMaximumBytes; this.executor = executor;
    }
    public ProjectionOperation operation() { return operation; }
    public int inputMaximumBytes() { return inputMaximumBytes; }
    public int outputMaximumBytes() { return outputMaximumBytes; }
    public ProjectionResult execute(ProjectionCall call) {
        if (call.identity().operation() != operation) { throw new IllegalArgumentException("registered operation mismatch"); }
        return executor.execute(call);
    }

    public static <I, O> RegisteredProjection of(ProjectionPort<I, O> port) {
        Objects.requireNonNull(port); ProjectionOperation operation = Objects.requireNonNull(port.operation());
        int inputLimit = limit(port.inputMaximumBytes()); int outputLimit = limit(port.outputMaximumBytes());
        return new RegisteredProjection(operation, inputLimit, outputLimit, call -> {
            if (call.payload().size() > inputLimit) { return rejected(call, ProjectionError.Code.PAYLOAD_TOO_LARGE, "payload exceeds registered operation budget"); }
            I input;
            try { input = Objects.requireNonNull(port.decode(call.payload().bytes())); }
            catch (ProjectionProtocolException error) { return unavailableOrFailed(call, error); }
            catch (ProjectionDomainRejection error) { return rejected(call, ProjectionError.Code.DOMAIN_REJECTED, reason(error, "domain rejected input")); }
            catch (IllegalArgumentException error) { return rejected(call, ProjectionError.Code.INVALID_PAYLOAD, reason(error, "payload rejected by registered domain codec")); }
            catch (RuntimeException error) { return rejected(call, ProjectionError.Code.PROJECTION_FAILED, "registered domain decoder failed internally"); }
            O result;
            try { result = port.project(input); }
            catch (ProjectionProtocolException error) { return unavailableOrFailed(call, error); }
            catch (ProjectionDomainRejection error) { return rejected(call, ProjectionError.Code.DOMAIN_REJECTED, reason(error, "domain rejected projection")); }
            catch (RuntimeException error) { return rejected(call, ProjectionError.Code.PROJECTION_FAILED, "registered pure projection failed"); }
            try {
                return new ProjectionResult.Succeeded(call.identity(), ProjectionJson.value(port.encode(result), outputLimit));
            } catch (RuntimeException error) { return rejected(call, ProjectionError.Code.INVALID_RESULT, "result rejected by registered encoder or role budget"); }
        });
    }

    private static int limit(int maximum) {
        if (maximum < 1 || maximum > ProjectionJson.MAX_BYTES) { throw new IllegalArgumentException("registered finite JSON role budget required"); }
        return maximum;
    }
    private static ProjectionResult.Rejected unavailableOrFailed(ProjectionCall call, ProjectionProtocolException error) {
        return error.code() == ProjectionError.Code.OPERATION_UNAVAILABLE
                ? rejected(call, ProjectionError.Code.OPERATION_UNAVAILABLE, "registered operation server context unavailable")
                : rejected(call, ProjectionError.Code.PROJECTION_FAILED, "registered operation emitted an invalid protocol failure");
    }
    private static String reason(RuntimeException error, String fallback) {
        String message = error.getMessage();
        if (message == null || message.isBlank()) { return fallback; }
        if (message.length() > 512) {
            int end = Character.isHighSurrogate(message.charAt(511)) ? 511 : 512;
            message = message.substring(0, end);
        }
        try { return new ProjectionError(ProjectionError.Code.DOMAIN_REJECTED, message).message(); }
        catch (IllegalArgumentException invalidUnicode) { return fallback; }
    }
    private static ProjectionResult.Rejected rejected(ProjectionCall call, ProjectionError.Code code, String message) {
        return new ProjectionResult.Rejected(Optional.of(call.identity()), new ProjectionError(code, message));
    }
}

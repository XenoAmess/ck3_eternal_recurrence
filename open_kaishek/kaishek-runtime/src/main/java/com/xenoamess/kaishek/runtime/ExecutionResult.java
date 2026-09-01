package com.xenoamess.kaishek.runtime;

import java.util.Objects;

public record ExecutionResult<T>(ExecutionStatus status, T value, String reason, ExecutionTrace trace) {
    public ExecutionResult { Objects.requireNonNull(status); reason = reason == null ? "" : reason; Objects.requireNonNull(trace); }
    public boolean isSuccess() { return status == ExecutionStatus.SUCCESS; }
    public static <T> ExecutionResult<T> success(T value, ExecutionTrace trace) { return new ExecutionResult<>(ExecutionStatus.SUCCESS, value, "", trace); }
    public static <T> ExecutionResult<T> unsupported(String reason, ExecutionTrace trace) { return new ExecutionResult<>(ExecutionStatus.UNSUPPORTED, null, reason, trace); }
}

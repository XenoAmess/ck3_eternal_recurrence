package com.xenoamess.kaishek.runtime;

import java.util.Map;

public record TraceEntry(long sequence, String operation, String phase, Map<String, Object> data) {
    public TraceEntry { data = Map.copyOf(data == null ? Map.of() : data); }
}

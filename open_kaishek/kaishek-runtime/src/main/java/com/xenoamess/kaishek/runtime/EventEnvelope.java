package com.xenoamess.kaishek.runtime;

import java.util.*;

public record EventEnvelope(long sequence, String hook, long dueEpochDay, CaseBinding binding, Map<String,Object> payload) {
    public EventEnvelope { if (sequence < 0 || dueEpochDay < 0) throw new IllegalArgumentException("invalid event"); Objects.requireNonNull(hook); Objects.requireNonNull(binding); payload = Map.copyOf(payload == null ? Map.of() : payload); }
}

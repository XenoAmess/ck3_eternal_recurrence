package com.xenoamess.kaishek.runtime;

import java.time.LocalDate;
import java.util.*;

/** Mutable execution frame; all mutation is observable through trace/read-write sets. */
public final class ExecutionContext {
    private ScopeContext scopes;
    private final Map<String, TypedValue> variables = new LinkedHashMap<>();
    private final DrawTape drawTape;
    private final ExecutionTrace trace;
    private final PriorityQueue<EventEnvelope> events = new PriorityQueue<>(Comparator.comparingLong(EventEnvelope::dueEpochDay).thenComparingLong(EventEnvelope::sequence));
    private long epochDay;
    private long eventSequence;
    public ExecutionContext(ScopeContext scopes, long epochDay, DrawTape drawTape) {
        if (epochDay < 0) throw new IllegalArgumentException("negative epoch day"); this.scopes = Objects.requireNonNull(scopes); this.epochDay = epochDay; this.drawTape = Objects.requireNonNull(drawTape); this.trace = new ExecutionTrace();
    }
    public ScopeContext scopes() { return scopes; }
    public void scopes(ScopeContext scopes) { this.scopes = Objects.requireNonNull(scopes); }
    public long epochDay() { return epochDay; }
    public LocalDate date() { return LocalDate.ofEpochDay(epochDay); }
    public void advanceTo(long day) { if (day < epochDay) throw new IllegalArgumentException("clock cannot go backwards"); epochDay = day; trace.add("clock", "advance", Map.of("epochDay", day)); }
    public DrawTape drawTape() { return drawTape; }
    public ExecutionTrace trace() { return trace; }
    public Optional<TypedValue> get(String key) { trace.read(key); return Optional.ofNullable(variables.get(key)); }
    public void set(String key, TypedValue value) { if (key == null || key.isBlank()) throw new IllegalArgumentException("blank variable"); variables.put(key, Objects.requireNonNull(value)); trace.write(key); trace.add("set", "write", Map.of("key", key)); }
    public void set(String key, Object value) { set(key, TypedValue.of(value)); }
    public boolean has(String key) { trace.read(key); return variables.containsKey(key); }
    public Optional<TypedValue> remove(String key) { trace.write(key); return Optional.ofNullable(variables.remove(key)); }
    public Map<String, TypedValue> variables() { return Collections.unmodifiableMap(variables); }
    public EventEnvelope schedule(String hook, long dueDay, CaseBinding binding, Map<String,Object> payload) {
        if (dueDay < epochDay) throw new IllegalArgumentException("event due date in past"); EventEnvelope e = new EventEnvelope(eventSequence++, hook, dueDay, binding, payload); events.add(e); trace.add(hook, "schedule", Map.of("dueEpochDay", dueDay, "sequence", e.sequence())); return e;
    }
    public List<EventEnvelope> dueEvents() { List<EventEnvelope> out = new ArrayList<>(); while (!events.isEmpty() && events.peek().dueEpochDay() <= epochDay) out.add(events.remove()); return out; }
    public int queuedEvents() { return events.size(); }
}

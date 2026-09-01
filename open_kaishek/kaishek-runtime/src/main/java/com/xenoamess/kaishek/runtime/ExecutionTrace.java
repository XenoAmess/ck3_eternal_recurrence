package com.xenoamess.kaishek.runtime;

import java.util.*;

public final class ExecutionTrace {
    private final List<TraceEntry> entries = new ArrayList<>();
    private final ReadWriteSet sets = new ReadWriteSet();
    public synchronized void add(String operation, String phase, Map<String, Object> data) {
        entries.add(new TraceEntry(entries.size(), operation, phase, data));
    }
    public void read(String key) { sets.read(key); }
    public void write(String key) { sets.write(key); }
    public List<TraceEntry> entries() { return List.copyOf(entries); }
    public ReadWriteSet readWriteSet() { return sets.snapshot(); }
}

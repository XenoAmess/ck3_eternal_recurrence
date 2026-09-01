package com.xenoamess.kaishek.runtime;

import java.util.*;

public final class ReadWriteSet {
    private final Set<String> reads = new LinkedHashSet<>(), writes = new LinkedHashSet<>();
    public void read(String key) { if (key != null) reads.add(key); }
    public void write(String key) { if (key != null) writes.add(key); }
    public Set<String> reads() { return Collections.unmodifiableSet(reads); }
    public Set<String> writes() { return Collections.unmodifiableSet(writes); }
    public ReadWriteSet snapshot() { var r = new ReadWriteSet(); r.reads.addAll(reads); r.writes.addAll(writes); return r; }
}

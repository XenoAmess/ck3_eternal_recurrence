package com.xenoamess.kaishek.runtime;

import java.util.*;

/** Replayable finite source of random draws. Never falls back to system randomness. */
public final class DrawTape {
    private final List<Integer> values;
    private final List<DrawRecord> records = new ArrayList<>();
    private int cursor;

    public DrawTape(List<Integer> values) {
        this.values = List.copyOf(Objects.requireNonNull(values, "values"));
    }
    public static DrawTape of(int... values) {
        List<Integer> boxed = new ArrayList<>(values.length); for (int v : values) boxed.add(v); return new DrawTape(boxed);
    }
    public synchronized int drawInt(int bound) { return drawInt(bound, ""); }
    public synchronized int drawInt(int bound, String purpose) {
        if (bound <= 0) throw new IllegalArgumentException("bound must be positive");
        if (cursor >= values.size()) throw new DrawTapeExhaustedException(cursor);
        int p = cursor++, raw = values.get(p), result = Math.floorMod(raw, bound);
        records.add(new DrawRecord(p, raw, bound, result, purpose == null ? "" : purpose));
        return result;
    }
    public boolean drawBoolean() { return drawBoolean(""); }
    /** Consume one tape cell and retain the caller's semantic purpose in trace. */
    public boolean drawBoolean(String purpose) { return drawInt(2, purpose) == 1; }
    public <T> T choose(List<T> candidates, String purpose) {
        Objects.requireNonNull(candidates); if (candidates.isEmpty()) throw new IllegalArgumentException("empty candidates");
        return candidates.get(drawInt(candidates.size(), purpose));
    }
    public synchronized int position() { return cursor; }
    public int size() { return values.size(); }
    public synchronized int remaining() { return values.size() - cursor; }
    public synchronized List<DrawRecord> records() { return List.copyOf(records); }
}

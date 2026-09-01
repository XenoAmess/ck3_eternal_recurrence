package com.xenoamess.kaishek.profile;

import java.lang.reflect.RecordComponent;
import java.time.temporal.TemporalAccessor;
import java.util.*;

/** Small deterministic JSON writer for contract records; parsing is intentionally delegated to adapters. */
public final class JsonCodec {
    private JsonCodec() {}
    public static String write(Object value) { var out = new StringBuilder(); append(value, out); return out.toString(); }
    private static void append(Object v, StringBuilder out) {
        if (v == null) { out.append("null"); return; }
        if (v instanceof String || v instanceof Character || v instanceof TemporalAccessor || v instanceof Enum<?>) { quote(v.toString(), out); return; }
        if (v instanceof Double d && !Double.isFinite(d))
            throw new IllegalArgumentException("non-finite numbers are not valid JSON");
        if (v instanceof Float f && !Float.isFinite(f))
            throw new IllegalArgumentException("non-finite numbers are not valid JSON");
        if (v instanceof Number || v instanceof Boolean) { out.append(v); return; }
        if (v instanceof Optional<?> o) { append(o.orElse(null), out); return; }
        if (v instanceof Map<?, ?> m) {
            out.append('{'); boolean first = true;
            var entries = new ArrayList<Map.Entry<?, ?>>(m.entrySet());
            entries.sort(Comparator.comparing(e -> String.valueOf(e.getKey())));
            String previousKey = null;
            for (var entry : entries) {
                String key = String.valueOf(entry.getKey());
                if (previousKey != null && previousKey.equals(key))
                    throw new IllegalArgumentException("map contains duplicate JSON key: " + key);
                previousKey = key;
                if (!first) out.append(','); first = false; quote(key, out); out.append(':'); append(entry.getValue(), out);
            }
            out.append('}'); return;
        }
        if (v instanceof Set<?> set) {
            // Set iteration order is not part of the Java contract.  Sort by
            // the canonical scalar spelling so repeated writes are stable.
            var values = new ArrayList<>(set);
            values.sort(Comparator.comparing(JsonCodec::sortKey));
            appendIterable(values, out);
            return;
        }
        if (v instanceof Iterable<?> it) { appendIterable(it, out); return; }
        if (v.getClass().isArray()) { out.append('['); int n = java.lang.reflect.Array.getLength(v); for (int i=0;i<n;i++) { if (i>0) out.append(','); append(java.lang.reflect.Array.get(v,i),out); } out.append(']'); return; }
        if (v.getClass().isRecord()) {
            out.append('{'); boolean first = true;
            for (RecordComponent c : v.getClass().getRecordComponents()) { try { var x = c.getAccessor().invoke(v); if (!first) out.append(','); first = false; quote(c.getName(),out); out.append(':'); append(x,out); } catch (ReflectiveOperationException e) { throw new IllegalArgumentException("cannot serialize " + v.getClass(), e); } }
            out.append('}'); return;
        }
        quote(v.toString(), out);
    }
    private static void quote(String s, StringBuilder out) {
        out.append('"'); for (int i=0;i<s.length();i++) { char c=s.charAt(i); switch (c) { case '"' -> out.append("\\\""); case '\\' -> out.append("\\\\"); case '\n' -> out.append("\\n"); case '\r' -> out.append("\\r"); case '\t' -> out.append("\\t"); default -> { if (c < 0x20) out.append(String.format("\\u%04x", (int)c)); else out.append(c); } } } out.append('"');
    }

    private static void appendIterable(Iterable<?> values, StringBuilder out) {
        out.append('[');
        boolean first = true;
        for (var e : values) {
            if (!first) out.append(',');
            first = false;
            append(e, out);
        }
        out.append(']');
    }

    private static String sortKey(Object value) {
        if (value == null) return "null";
        if (value instanceof String || value instanceof Character || value instanceof Enum<?>
                || value instanceof TemporalAccessor || value instanceof Number || value instanceof Boolean)
            return value.toString();
        return value.getClass().getName() + ':' + value.toString();
    }
}

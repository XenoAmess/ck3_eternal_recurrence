package org.xar.ck3.control.wave2.events.nativepulse;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual .4 name hash and sorted native-table lookup. No Java case folding or guessed VFS ordering. */
public final class NativeOnActionNameIndex {
    private NativeOnActionNameIndex() { }
    public record Name(String text) {
        public Name {
            Objects.requireNonNull(text); if (!text.isEmpty()) StrictJson.text(text);
            StrictJson.require(text.indexOf('\0') < 0 && text.getBytes(StandardCharsets.UTF_8).length <= 16384,
                "bounded UTF-8 native name without embedded C-string terminator required");
        }
        public byte[] utf8() { return text.getBytes(StandardCharsets.UTF_8); }
    }
    public record Entry(Name name, BigInteger address, long nativeHashU32) {
        public Entry { Objects.requireNonNull(name); pointer(address); u32(nativeHashU32); }
    }
    /** Preserve the actual parallel arrays' order; equal-hash entries must not be re-sorted in Java. */
    public record Table(NativePlayableAnnualGate.Executable executable, List<Entry> definitions, List<Long> parallelHashes) {
        public Table {
            Objects.requireNonNull(executable); definitions = List.copyOf(definitions); parallelHashes = List.copyOf(parallelHashes);
            StrictJson.require(definitions.size() == parallelHashes.size() && definitions.size() <= 8192, "bounded complete parallel definition/hash arrays required");
            long previous = 0; Set<Name> names = new HashSet<>(); Set<BigInteger> addresses = new HashSet<>();
            for (int i = 0; i < definitions.size(); i++) {
                Entry entry = definitions.get(i); long hash = parallelHashes.get(i); u32(hash);
                StrictJson.require((i == 0 || previous <= hash) && entry.nativeHashU32() == hash
                    && hash(entry.name()) == hash && names.add(entry.name()) && addresses.add(entry.address()),
                    "native definition arrays changed their unsigned hash, name, identity or original sorted order");
                previous = hash;
            }
        }
    }
    /** 3F7E220 -> 3F7E0E0, seed zero, low32 arithmetic over original UTF-8 bytes. */
    public static long hash(Name name) {
        byte[] raw = Objects.requireNonNull(name).utf8(); int h = 0, at = 0;
        while (at + 4 <= raw.length) {
            int value = (raw[at] & 255) | (raw[at + 1] & 255) << 8 | (raw[at + 2] & 255) << 16 | (raw[at + 3] & 255) << 24;
            value = Integer.rotateLeft(value * 0xcc9e2d51, 15) * 0x1b873593;
            h = (Integer.rotateLeft(h ^ value, 13) + 0xfaddaf14) * 5; at += 4;
        }
        int tail = 0;
        for (int i = at; i < raw.length; i++) tail |= (raw[i] & 255) << ((i - at) * 8);
        if (at < raw.length) h ^= Integer.rotateLeft(tail * 0xcc9e2d51, 15) * 0x1b873593;
        h ^= raw.length; h ^= h >>> 16; h *= 0x85ebca6b; h ^= h >>> 13; h *= 0xc2b2ae35; h ^= h >>> 16;
        return Integer.toUnsignedLong(h);
    }
    /** 37CBB40's unsigned lower-bound variant, followed by its contiguous collision scan and exact byte equality. */
    public static Optional<Entry> find(Table table, Name query) {
        Objects.requireNonNull(table); Objects.requireNonNull(query); long hash = hash(query);
        int cursor = 0, count = table.parallelHashes().size();
        while (count > 0) {
            int half = count >>> 1, advance = count - half;
            if (table.parallelHashes().get(cursor + half) < hash) cursor += advance;
            count = half;
        }
        if (cursor == table.parallelHashes().size() || hash < table.parallelHashes().get(cursor)) return Optional.empty();
        for (int i = cursor; i < table.definitions().size(); i++) {
            Entry entry = table.definitions().get(i);
            if (entry.nativeHashU32() != hash) break;
            if (java.util.Arrays.equals(query.utf8(), entry.name().utf8())) return Optional.of(entry);
        }
        return Optional.empty();
    }
    public static void pointer(BigInteger value) {
        StrictJson.require(value != null && value.signum() > 0 && value.compareTo(StrictJson.UINT64_MAX) <= 0, "nonzero uint64 native address required");
    }
    private static void u32(long value) { StrictJson.require(value >= 0 && value <= 0xffffffffL, "native uint32 hash required"); }
}

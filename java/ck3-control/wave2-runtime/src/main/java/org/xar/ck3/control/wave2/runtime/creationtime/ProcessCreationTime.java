package org.xar.ck3.control.wave2.runtime.creationtime;

import java.time.DateTimeException;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.ResolverStyle;
import java.util.Locale;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Original Windows birth spellings remain evidence; this class only compares exact microsecond instants. */
public final class ProcessCreationTime {
    private static final Pattern DMTF = Pattern.compile("([0-9]{14})\\.([0-9]{6})([+-])([0-9]{3})");
    private static final Pattern CIM = Pattern.compile("([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})\\.([0-9]{7})Z");
    private static final DateTimeFormatter DMTF_STAMP = DateTimeFormatter.ofPattern("uuuuMMddHHmmss", Locale.ROOT).withResolverStyle(ResolverStyle.STRICT);
    private static final DateTimeFormatter ISO_STAMP = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss", Locale.ROOT).withResolverStyle(ResolverStyle.STRICT);
    private ProcessCreationTime() { }

    public enum Comparison { SAME, DIFFERENT, UNAVAILABLE }

    /** Cannot be constructed by a caller with an unverified instant or a rewritten birth spelling. */
    public static final class UtcBirth {
        private final String original;
        private final Instant instant;
        private UtcBirth(String original, Instant instant) { this.original = original; this.instant = instant; }
        public String original() { return original; }
        public Instant instant() { return instant; }
        public String utcIsoformat() {
            LocalDateTime utc = LocalDateTime.ofInstant(instant, ZoneOffset.UTC);
            String suffix = utc.getNano() == 0 ? "" : String.format(Locale.ROOT, ".%06d", utc.getNano() / 1000);
            return ISO_STAMP.format(utc) + suffix + "+00:00";
        }
        @Override public boolean equals(Object other) { return other instanceof UtcBirth birth && instant.equals(birth.instant); }
        @Override public int hashCode() { return instant.hashCode(); }
        @Override public String toString() { return utcIsoformat(); }
    }

    /** Parse ASCII Windows DMTF or seven-digit UTC CIM, refusing to truncate a nonzero 100 ns digit. */
    public static UtcBirth parse(String original) {
        if (original == null || original.length() > 32768) { throw new IllegalArgumentException("supported bounded process birth spelling required"); }
        String text = strip(original); Matcher dmtf = DMTF.matcher(text);
        try {
            Instant instant;
            if (dmtf.matches()) {
                int minutes = Integer.parseInt(dmtf.group(4));
                if (minutes > 14 * 60) { throw new IllegalArgumentException("DMTF UTC offset is outside the supported range"); }
                if (dmtf.group(3).equals("-")) { minutes = -minutes; }
                LocalDateTime local = LocalDateTime.parse(dmtf.group(1), DMTF_STAMP).withNano(Integer.parseInt(dmtf.group(2)) * 1000);
                requirePythonYear(local); instant = local.toInstant(ZoneOffset.ofTotalSeconds(minutes * 60));
            } else {
                Matcher cim = CIM.matcher(text);
                if (!cim.matches()) { throw new IllegalArgumentException("unsupported process creation timestamp"); }
                if (cim.group(2).charAt(6) != '0') { throw new IllegalArgumentException("CIM process timestamp exceeds DMTF precision"); }
                LocalDateTime utc = LocalDateTime.parse(cim.group(1), ISO_STAMP).withNano(Integer.parseInt(cim.group(2).substring(0, 6)) * 1000);
                requirePythonYear(utc); instant = utc.toInstant(ZoneOffset.UTC);
            }
            requirePythonYear(LocalDateTime.ofInstant(instant, ZoneOffset.UTC));
            return new UtcBirth(original, instant);
        } catch (DateTimeException | NumberFormatException error) { throw new IllegalArgumentException("invalid process creation timestamp", error); }
    }
    /** The original same_process_creation_time predicate treats unsupported input as false. */
    public static boolean same(String first, String second) { return compare(first, second) == Comparison.SAME; }
    /** Unlike a boolean inequality, UNAVAILABLE cannot authorize a replaced-process path. */
    public static Comparison compare(String first, String second) {
        try { return parse(first).equals(parse(second)) ? Comparison.SAME : Comparison.DIFFERENT; }
        catch (IllegalArgumentException error) { return Comparison.UNAVAILABLE; }
    }
    private static void requirePythonYear(LocalDateTime value) {
        if (value.getYear() < 1 || value.getYear() > 9999) { throw new IllegalArgumentException("process time is outside Python datetime years"); }
    }
    private static String strip(String value) {
        Objects.requireNonNull(value); int first = 0, last = value.length();
        while (first < last && whitespace(value.codePointAt(first))) { first += Character.charCount(value.codePointAt(first)); }
        while (first < last && whitespace(value.codePointBefore(last))) { last -= Character.charCount(value.codePointBefore(last)); }
        return value.substring(first, last);
    }
    private static boolean whitespace(int code) {
        return code >= 9 && code <= 13 || code >= 28 && code <= 32 || code == 0x85 || code == 0xa0 || code == 0x1680
            || code >= 0x2000 && code <= 0x200a || code == 0x2028 || code == 0x2029 || code == 0x202f || code == 0x205f || code == 0x3000;
    }
}

package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact .4 instruction-derived annual hash gate. It does not model candidate-bucket membership or script eligibility. */
public final class NativePlayableAnnualGate {
    public static final String EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final String SCHEMA = "xar.ck3.native-playable-annual-hash-gate-input/v1";
    public static final int REGISTERED_ACTION_INDEX = 6;
    private static final Set<String> FIELDS = Set.of("schema", "executable_sha256", "character_id_u32", "year", "day_of_year");
    private NativePlayableAnnualGate() { }

    public enum Executable {
        CURRENT_12004;
        public static Optional<Executable> exact(String sha256) {
            return sha256 != null && EXECUTABLE_SHA256.equals(sha256.toLowerCase(Locale.ROOT)) ? Optional.of(CURRENT_12004) : Optional.empty();
        }
    }
    /** year/day come from actual CDate decoding; a displayed year string is not an input witness. */
    public record Input(Executable executable, long characterIdU32, int year, int dayOfYear) {
        public Input {
            Objects.requireNonNull(executable);
            StrictJson.require(characterIdU32 >= 0 && characterIdU32 <= 0xffffffffL, "full uint32 native character identity required");
            StrictJson.require(dayOfYear >= 0 && dayOfYear < 365, "actual native day of year 0..364 required");
        }
    }
    public record Evaluation(Input input, long seedU32, long candidateU32, boolean hashGateOpen) {
        public Evaluation { Objects.requireNonNull(input); }
        public boolean candidateBucketMembershipProven() { return false; }
        public boolean scriptEligibilityProven() { return false; }
        public boolean eventSelected() { return false; }
        public boolean materialCreditGranted() { return false; }
    }
    /**
     * 2AE8996..2AE89CE creates the wrapped uint32 candidate; 2AE8BAB/2AE8BAF gates
     * the table+0x30 call at 2AE8BDD. The final compare uses native unsigned /365
     * via magic 0x6719f361; the literal instruction arithmetic is retained here.
     */
    public static Evaluation evaluate(Input input) {
        Objects.requireNonNull(input);
        int value = input.year() + (int) input.characterIdU32();
        int seed = (value * 0x2b3d + 0x6d4f) * value;
        int candidate = seed + input.dayOfYear();
        int high = (int) ((Integer.toUnsignedLong(candidate) * 0x6719f361L) >>> 32);
        int quotient = (((candidate - high) >>> 1) + high) >>> 8;
        boolean due = candidate == quotient * 365;
        return new Evaluation(input, Integer.toUnsignedLong(seed), Integer.toUnsignedLong(candidate), due);
    }
    /** Strict JSON entrance retains integer tokens and rejects bool/float/unknown fields and unsupported binaries. */
    public static Input decode(byte[] raw) {
        ObjectNode value = StrictJson.object(StrictJson.parse(raw, 4096), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact native annual gate schema required");
        Executable executable = Executable.exact(StrictJson.text(value.get("executable_sha256")))
            .orElseThrow(() -> new IllegalArgumentException("native annual gate source is not the reviewed .4 executable"));
        return new Input(executable, StrictJson.integer(value.get("character_id_u32"), 0, 0xffffffffL),
            Math.toIntExact(StrictJson.integer(value.get("year"), Integer.MIN_VALUE, Integer.MAX_VALUE)),
            Math.toIntExact(StrictJson.integer(value.get("day_of_year"), 0, 364)));
    }
    public static byte[] encode(Input input) {
        Objects.requireNonNull(input);
        ObjectNode value = StrictJson.object().put("schema", SCHEMA).put("executable_sha256", EXECUTABLE_SHA256)
            .put("character_id_u32", input.characterIdU32()).put("year", input.year()).put("day_of_year", input.dayOfYear());
        return StrictJson.canonical(value, 4096);
    }
}

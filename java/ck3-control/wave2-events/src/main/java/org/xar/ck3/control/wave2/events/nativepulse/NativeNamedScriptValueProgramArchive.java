package org.xar.ck3.control.wave2.events.nativepulse;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFieldArchive.Store;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeNamedScriptValueProgram.*;

/** Existing Math/Raw archives retain nested original custody; this archive checks the real named producer again. */
public final class NativeNamedScriptValueProgramArchive {
    private NativeNamedScriptValueProgramArchive() { }
    public record Recorded(ExactRef original, ExactRef derived, NativeScriptMathProgramArchive.Recorded math,
                           Optional<NativeRawScriptValueArchive.Recorded> raw) {
        public Recorded { Objects.requireNonNull(original); Objects.requireNonNull(derived); Objects.requireNonNull(math); Objects.requireNonNull(raw); }
    }
    public record Replayed(Input original, Result recomputed) {
        public Replayed { Objects.requireNonNull(original); Objects.requireNonNull(recomputed); }
    }
    public record ObservedRecorded(ExactRef original, Recorded named) {
        public ObservedRecorded { Objects.requireNonNull(original); Objects.requireNonNull(named); }
    }
    public record ObservedReplayed(ObservedLoad original, Result recomputed) {
        public ObservedReplayed { Objects.requireNonNull(original); Objects.requireNonNull(recomputed); }
    }
    public static ObservedRecorded preserve(ObservedLoad input, Store store) throws IOException {
        Result result = run(input); load(input.observation().originalObservation(), store); Recorded named = preserve(input.original(), store);
        StrictJson.require(Arrays.equals(load(named.derived(), store), NativeNamedScriptValueProgramJson.encode(result)), "same observed producer and nested consumers required");
        return new ObservedRecorded(preserve(NativeNamedScriptValueProgramJson.encode(input), store), named);
    }
    public static ObservedReplayed replay(ObservedRecorded record, Store store) throws IOException {
        ObservedLoad input = NativeNamedScriptValueProgramJson.decodeObserved(load(record.original(), store)); load(input.observation().originalObservation(), store);
        Replayed nested = replay(record.named(), store); StrictJson.require(nested.original().equals(input.original()), "observed archive must bind the exact original named input");
        Result result = run(input); StrictJson.require(result.equals(nested.recomputed()), "actual observed producer cold replay differs from nested consumers");
        return new ObservedReplayed(input, result);
    }
    public static byte[] encode(ObservedRecorded record) {
        var row = StrictJson.object().put("schema", "xar.native-named-load-observed-archive/v1"); row.set("original", record.original().toJson());
        row.set("named", StrictJson.parse(encode(record.named()))); return StrictJson.canonical(row);
    }
    public static ObservedRecorded decodeObserved(byte[] bytes) {
        var row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "original", "named"));
        StrictJson.require("xar.native-named-load-observed-archive/v1".equals(StrictJson.text(row.get("schema"))), "exact observed archive schema required");
        return new ObservedRecorded(ExactRef.fromJson(row.get("original")), decode(StrictJson.canonical(row.get("named"))));
    }
    public static Recorded preserve(Input input, Store store) throws IOException {
        load(input.originalLoadSource(), store);
        var math = NativeScriptMathProgramArchive.preserve(input.originalMath(), store);
        Optional<NativeRawScriptValueArchive.Recorded> raw = input.originalRawConsumer().isEmpty() ? Optional.empty()
            : Optional.of(NativeRawScriptValueArchive.preserve(input.originalRawConsumer().orElseThrow(), store));
        return new Recorded(preserve(NativeNamedScriptValueProgramJson.encode(input), store), preserve(NativeNamedScriptValueProgramJson.encode(run(input)), store), math, raw);
    }
    public static Replayed replay(Recorded record, Store store) throws IOException {
        Input input = NativeNamedScriptValueProgramJson.decode(load(record.original(), store)); load(input.originalLoadSource(), store);
        StrictJson.require(NativeScriptMathProgramArchive.replay(record.math(), store).original().equals(input.originalMath()), "nested math archive must be this actual named Load input");
        StrictJson.require(record.raw().isPresent() == input.originalRawConsumer().isPresent(), "raw observation missing/null distinction must survive archive");
        if (record.raw().isPresent()) StrictJson.require(NativeRawScriptValueArchive.replay(record.raw().orElseThrow(), store).original().equals(input.originalRawConsumer().orElseThrow()), "same original Raw consumer required");
        Result recomputed = run(input);
        StrictJson.require(Arrays.equals(load(record.derived(), store), NativeNamedScriptValueProgramJson.encode(recomputed)), "named result must equal original producer/consumer cold replay");
        return new Replayed(input, recomputed);
    }
    public static byte[] encode(Recorded record) {
        var row = StrictJson.object().put("schema", "xar.native-named-kind3-archive/v1"); row.set("original", record.original().toJson()); row.set("derived", record.derived().toJson());
        row.set("math", StrictJson.parse(NativeScriptMathProgramArchive.encode(record.math())));
        if (record.raw().isEmpty()) row.putNull("raw"); else row.set("raw", StrictJson.parse(NativeRawScriptValueArchive.encode(record.raw().orElseThrow())));
        return StrictJson.canonical(row);
    }
    public static Recorded decode(byte[] bytes) {
        var row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "original", "derived", "math", "raw"));
        StrictJson.require("xar.native-named-kind3-archive/v1".equals(StrictJson.text(row.get("schema"))), "exact named archive schema required");
        return new Recorded(ExactRef.fromJson(row.get("original")), ExactRef.fromJson(row.get("derived")), NativeScriptMathProgramArchive.decode(StrictJson.canonical(row.get("math"))),
            row.get("raw").isNull() ? Optional.empty() : Optional.of(NativeRawScriptValueArchive.decode(StrictJson.canonical(row.get("raw")))));
    }
    private static ExactRef preserve(byte[] bytes, Store store) throws IOException { ExactRef ref = store.preserve(bytes.clone()); verify(bytes, ref); StrictJson.require(Arrays.equals(bytes, load(ref, store)), "exact named original preservation required"); return ref; }
    private static byte[] load(ExactRef ref, Store store) throws IOException { StrictJson.require(ref.bytes() > 0 && ref.bytes() <= NativeScriptMathProgramJson.MAX_BYTES, "bounded original named custody required"); byte[] bytes = store.load(ref); verify(bytes, ref); return bytes; }
    private static void verify(byte[] bytes, ExactRef ref) { try { StrictJson.require(bytes != null && bytes.length == ref.bytes() && HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(ref.sha256()), "named custody length/SHA mismatch"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
}

package org.xar.ck3.control.wave2.events.nativepulse;

import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFieldArchive.Store;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeScriptMathProgram.*;

/** One existing store port; original root/field/operand custody and same producer/consumer cold replay. */
public final class NativeScriptMathProgramArchive {
    private NativeScriptMathProgramArchive() { }
    public record FactoryRecorded(ExactRef original, ExactRef derived) {
        public FactoryRecorded { Objects.requireNonNull(original); Objects.requireNonNull(derived); }
    }
    public static FactoryRecorded preserveFactory(ExactRef original, Store store) throws IOException {
        FactoryReview review = reviewFactory(original, load(original, store));
        return new FactoryRecorded(original, preserve(NativeScriptMathProgramJson.encodeFactoryReview(review), store));
    }
    public static FactoryReview replayFactory(FactoryRecorded record, Store store) throws IOException {
        return NativeScriptMathProgramJson.replayFactoryReview(load(record.derived(), store), record.original(), load(record.original(), store));
    }
    public static byte[] encodeFactory(FactoryRecorded record) {
        var row = StrictJson.object().put("schema", "xar.native-script-math-factory-archive/v1");
        row.set("original", record.original().toJson()); row.set("derived", record.derived().toJson()); return StrictJson.canonical(row);
    }
    public static FactoryRecorded decodeFactory(byte[] bytes) {
        var row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "original", "derived"));
        StrictJson.require("xar.native-script-math-factory-archive/v1".equals(StrictJson.text(row.get("schema"))), "exact factory archive schema required");
        return new FactoryRecorded(ExactRef.fromJson(row.get("original")), ExactRef.fromJson(row.get("derived")));
    }
    public record Recorded(ExactRef original, ExactRef derived) { public Recorded { Objects.requireNonNull(original); Objects.requireNonNull(derived); } }
    public record Replayed(Input original, Result recomputed) { public Replayed { Objects.requireNonNull(original); Objects.requireNonNull(recomputed); } }
    public static Recorded preserve(Input input, Store store) throws IOException {
        custody(input, store); return new Recorded(preserve(NativeScriptMathProgramJson.encode(input), store), preserve(NativeScriptMathProgramJson.encode(run(input)), store));
    }
    public static Replayed replay(Recorded record, Store store) throws IOException {
        Input input = NativeScriptMathProgramJson.decode(load(record.original(), store)); custody(input, store); Result recomputed = run(input);
        StrictJson.require(Arrays.equals(load(record.derived(), store), NativeScriptMathProgramJson.encode(recomputed)), "math result differs from actual original producer/consumer replay");
        return new Replayed(input, recomputed);
    }
    public static byte[] encode(Recorded record) { var row = StrictJson.object().put("schema", "xar.native-script-math-archive/v1"); row.set("original", record.original().toJson()); row.set("derived", record.derived().toJson()); return StrictJson.canonical(row); }
    public static Recorded decode(byte[] bytes) { var row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "original", "derived"));
        StrictJson.require("xar.native-script-math-archive/v1".equals(StrictJson.text(row.get("schema"))), "exact math archive schema required");
        return new Recorded(ExactRef.fromJson(row.get("original")), ExactRef.fromJson(row.get("derived"))); }
    private static void custody(Input input, Store store) throws IOException {
        load(input.originalObservation(), store);
        for (Field field : input.originalFields()) {
            load(field.originalSource(), store);
            if (field instanceof SimpleField simple) {
                NativeRawScriptValue.Input operand = simple.originalOperand(); load(operand.originalObservation(), store); load(operand.originalAstSource(), store);
                for (NativeRawScriptValue.OriginalRawCall call : operand.originalRawCalls()) load(call.originalObservation(), store);
                for (NativeRawScriptValue.OriginalScopeCall call : operand.originalScopeCalls()) load(call.originalObservation(), store);
            }
        }
    }
    private static ExactRef preserve(byte[] bytes, Store store) throws IOException { ExactRef ref = store.preserve(bytes.clone()); verify(bytes, ref);
        StrictJson.require(Arrays.equals(bytes, load(ref, store)), "store failed to preserve exact math original bytes"); return ref; }
    private static byte[] load(ExactRef ref, Store store) throws IOException { StrictJson.require(ref.bytes() > 0 && ref.bytes() <= NativeScriptMathProgramJson.MAX_BYTES, "bounded exact custody object required");
        byte[] bytes = store.load(ref); verify(bytes, ref); return bytes; }
    private static void verify(byte[] bytes, ExactRef ref) { StrictJson.require(bytes != null && bytes.length == ref.bytes() && sha256(bytes).equals(ref.sha256()), "math original custody length/SHA mismatch"); }
    private static String sha256(byte[] bytes) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
}

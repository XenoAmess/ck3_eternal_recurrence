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
import static org.xar.ck3.control.wave2.events.nativepulse.NativeRawScriptValue.*;

/** Exact-byte original custody and cold replay use the same finite native-control reconstruction. */
public final class NativeRawScriptValueArchive {
    private NativeRawScriptValueArchive() { }
    public record Recorded(ExactRef original, ExactRef derived) {
        public Recorded { Objects.requireNonNull(original); Objects.requireNonNull(derived); }
    }
    public record Replayed(Input original, Result recomputed) {
        public Replayed { Objects.requireNonNull(original); Objects.requireNonNull(recomputed); }
    }
    public static Recorded preserve(Input input, Store store) throws IOException {
        custody(input, store);
        return new Recorded(preserve(NativeRawScriptValueJson.encode(input), store), preserve(NativeRawScriptValueJson.encode(analyze(input)), store));
    }
    public static Replayed replay(Recorded recorded, Store store) throws IOException {
        Input input = NativeRawScriptValueJson.decode(load(recorded.original(), store)); custody(input, store);
        Result result = analyze(input);
        StrictJson.require(Arrays.equals(NativeRawScriptValueJson.encode(result), load(recorded.derived(), store)), "raw ScriptValue derived bytes differ from original recomputation");
        return new Replayed(input, result);
    }
    public static byte[] encode(Recorded recorded) {
        var row = StrictJson.object().put("schema", "xar.native-raw-script-value-archive/v1"); row.set("original", recorded.original().toJson()); row.set("derived", recorded.derived().toJson()); return StrictJson.canonical(row);
    }
    public static Recorded decode(byte[] bytes) {
        var row = StrictJson.object(StrictJson.parse(bytes), Set.of("schema", "original", "derived"));
        StrictJson.require("xar.native-raw-script-value-archive/v1".equals(StrictJson.text(row.get("schema"))), "exact raw ScriptValue archive schema required");
        return new Recorded(ExactRef.fromJson(row.get("original")), ExactRef.fromJson(row.get("derived")));
    }
    private static void custody(Input input, Store store) throws IOException {
        load(input.originalObservation(), store); load(input.originalAstSource(), store);
        for (OriginalRawCall call : input.originalRawCalls()) load(call.originalObservation(), store);
        for (OriginalScopeCall call : input.originalScopeCalls()) load(call.originalObservation(), store);
    }
    private static ExactRef preserve(byte[] bytes, Store store) throws IOException {
        ExactRef reference = store.preserve(bytes.clone()); verify(bytes, reference);
        StrictJson.require(Arrays.equals(bytes, load(reference, store)), "store did not preserve exact raw ScriptValue bytes"); return reference;
    }
    private static byte[] load(ExactRef reference, Store store) throws IOException {
        StrictJson.require(reference.bytes() > 0 && reference.bytes() <= NativeRawScriptValueJson.MAX_BYTES, "bounded original custody object required");
        byte[] bytes = store.load(reference); verify(bytes, reference); return bytes;
    }
    private static void verify(byte[] bytes, ExactRef reference) {
        StrictJson.require(bytes != null && bytes.length == reference.bytes() && sha256(bytes).equals(reference.sha256()), "raw ScriptValue custody bytes/SHA mismatch");
    }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

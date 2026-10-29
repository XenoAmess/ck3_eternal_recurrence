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
import static org.xar.ck3.control.wave2.events.nativepulse.NativeOnActionFields.*;

/** Original-input custody and pure replay of the same producer, postload and concrete consumers. */
public final class NativeOnActionFieldArchive {
    private NativeOnActionFieldArchive() { }
    /** Implementations preserve immutable exact bytes. This interface grants no loaded-state or Game authority. */
    public interface Store {
        ExactRef preserve(byte[] original) throws IOException;
        byte[] load(ExactRef exact) throws IOException;
    }
    public record Recorded(ExactRef original, ExactRef derived) {
        public Recorded { Objects.requireNonNull(original); Objects.requireNonNull(derived); }
    }
    public record Replayed(Input original, Projection recomputed) {
        public Replayed { Objects.requireNonNull(original); Objects.requireNonNull(recomputed); }
    }
    public static Recorded preserve(Input original, Store store) throws IOException {
        Objects.requireNonNull(store); custody(original, store);
        byte[] input = NativeOnActionFieldsJson.encode(original), output = NativeOnActionFieldsJson.encode(run(original));
        return new Recorded(preserve(input, store), preserve(output, store));
    }
    public static Replayed replay(Recorded recorded, Store store) throws IOException {
        Input original = NativeOnActionFieldsJson.decode(load(recorded.original(), store)); custody(original, store);
        Projection projection = run(original);
        StrictJson.require(Arrays.equals(NativeOnActionFieldsJson.encode(projection), load(recorded.derived(), store)), "derived four-field output differs from original replay");
        return new Replayed(original, projection);
    }
    public static Projection run(Input original) { return project(original, postload(original, produce(original))); }
    public static byte[] encode(Recorded recorded) {
        var root = StrictJson.object().put("schema", "xar.native-on-action-four-field-archive/v1");
        root.set("original", recorded.original().toJson()); root.set("derived", recorded.derived().toJson()); return StrictJson.canonical(root);
    }
    public static Recorded decode(byte[] raw) {
        var root = StrictJson.object(StrictJson.parse(raw), Set.of("schema", "original", "derived"));
        StrictJson.require("xar.native-on-action-four-field-archive/v1".equals(StrictJson.text(root.get("schema"))), "exact four-field archive schema required");
        return new Recorded(ExactRef.fromJson(root.get("original")), ExactRef.fromJson(root.get("derived")));
    }
    private static void custody(Input original, Store store) throws IOException {
        load(original.originalObservation(), store);
        for (Block block : original.originalBlocks()) load(block.originalSourcePiece(), store);
    }
    private static ExactRef preserve(byte[] raw, Store store) throws IOException {
        ExactRef ref = store.preserve(raw.clone()); verify(raw, ref); StrictJson.require(Arrays.equals(raw, load(ref, store)), "archive did not preserve exact original bytes"); return ref;
    }
    private static byte[] load(ExactRef ref, Store store) throws IOException {
        StrictJson.require(ref.bytes() > 0 && ref.bytes() <= NativeOnActionFieldsJson.MAX_BYTES, "bounded nonempty original custody object required");
        byte[] raw = store.load(ref); verify(raw, ref); return raw;
    }
    private static void verify(byte[] raw, ExactRef ref) {
        StrictJson.require(raw != null && raw.length == ref.bytes() && sha256(raw).equals(ref.sha256()), "original archive length or SHA-256 mismatch");
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Original source custody around the existing four-field producer and both concrete consumers.
 * A file name, a definition address or a reload notification cannot stand in for the bytes read
 * by the native loader. No value returned here grants current loaded-state or Game authority.
 */
public final class NativeOnActionSourceEnvelope {
    public static final String SCHEMA = "xar.native-on-action-source-envelope/v1";
    public static final int MAX_BYTES = NativeOnActionFieldsJson.MAX_BYTES;
    private NativeOnActionSourceEnvelope() { }

    /** EXTERNAL_CAPTURE remains untrusted custody material until an independent native reader qualifies it. */
    public enum Origin { EXTERNAL_CAPTURE, SOFTWARE_FIXTURE }
    public enum Custody { SOURCE_BINDING_UNAVAILABLE, CHANGED_DURING_CAPTURE, ORIGINAL_BYTES_ACCOUNTED, SOFTWARE_FIXTURE }

    /** Block refers to the one existing Input.originalBlocks order. No duplicate field contract. */
    public record Piece(int block, int offset) {
        public Piece {
            StrictJson.require(block >= 0 && block < 1024 && offset >= 0 && offset <= MAX_BYTES,
                    "bounded original block index and byte offset required");
        }
    }
    /** nativePathHex preserves original filename bytes and case; it never supplies a Java filesystem path. */
    public record OpenedFile(int ordinal, String nativePathHex, ExactRef originalBytes, List<Piece> pieces) {
        public OpenedFile {
            StrictJson.require(ordinal >= 0 && ordinal < 8192, "bounded native load ordinal required");
            StrictJson.require(nativePathHex != null && nativePathHex.matches("(?:[0-9a-f]{2}){1,4096}"),
                    "bounded canonical original native path bytes required");
            for (byte value : HexFormat.of().parseHex(nativePathHex))
                StrictJson.require(value != 0, "native path must exclude the terminating NUL");
            Objects.requireNonNull(originalBytes); pieces = List.copyOf(pieces);
            StrictJson.require(originalBytes.bytes() <= MAX_BYTES && pieces.size() <= 1024,
                    "bounded opened file and source pieces required");
        }
    }
    /**
     * These are independently preserved original snapshots, not an invented native generation field.
     * Mount/replacement records and each side of the VFS/payload capture must all remain readable.
     */
    public record Boundary(ExactRef mountTable, ExactRef replacementRules, ExactRef vfsBefore, ExactRef vfsAfter,
                           ExactRef payloadBefore, ExactRef payloadAfter) {
        public Boundary {
            Objects.requireNonNull(mountTable); Objects.requireNonNull(replacementRules);
            Objects.requireNonNull(vfsBefore); Objects.requireNonNull(vfsAfter);
            Objects.requireNonNull(payloadBefore); Objects.requireNonNull(payloadAfter);
        }
    }
    public record Sources(String machineId, String observedAtUtc, Origin origin, List<OpenedFile> files,
                          Optional<Boundary> boundary) {
        public Sources {
            StrictJson.text(machineId); StrictJson.utc(observedAtUtc); Objects.requireNonNull(origin);
            files = List.copyOf(files); Objects.requireNonNull(boundary);
            StrictJson.require(files.size() <= 8192, "bounded native returned load sequence required");
            long total = 0;
            for (int index = 0; index < files.size(); index++) {
                StrictJson.require(files.get(index).ordinal() == index, "contiguous original load order required");
                total += files.get(index).originalBytes().bytes();
            }
            StrictJson.require(total <= 16L * MAX_BYTES, "whole original file byte budget exceeded");
        }
    }
    public record Envelope(Sources sources, NativeOnActionFieldArchive.Recorded fieldArchive) {
        public Envelope { Objects.requireNonNull(sources); Objects.requireNonNull(fieldArchive); }
    }
    public record Replayed(Envelope envelope, NativeOnActionFieldArchive.Replayed fields, Custody custody) {
        public Replayed { Objects.requireNonNull(envelope); Objects.requireNonNull(fields); Objects.requireNonNull(custody); }
    }

    /** Preserves the same original producer -> postload -> both consumers and then its external source envelope. */
    public static ExactRef preserve(NativeOnActionFields.Input input, Sources sources,
                                    NativeOnActionFieldArchive.Store store) throws IOException {
        Objects.requireNonNull(input); Objects.requireNonNull(sources); Objects.requireNonNull(store);
        inspect(input, sources, store);
        var recorded = NativeOnActionFieldArchive.preserve(input, store);
        byte[] raw = encode(new Envelope(sources, recorded));
        ExactRef ref = store.preserve(raw.clone());
        StrictJson.require(Arrays.equals(raw, load(ref, store, false)), "source envelope was not preserved exactly");
        return ref;
    }

    /** Cold replay reads all retained originals; it never issues another live query or substitutes current disk files. */
    public static Replayed replay(ExactRef exact, NativeOnActionFieldArchive.Store store) throws IOException {
        Objects.requireNonNull(store);
        Envelope envelope = decode(load(exact, store, false));
        NativeOnActionFieldArchive.Replayed fields = NativeOnActionFieldArchive.replay(envelope.fieldArchive(), store);
        Custody custody = inspect(fields.original(), envelope.sources(), store);
        return new Replayed(envelope, fields, custody);
    }

    private static Custody inspect(NativeOnActionFields.Input input, Sources sources,
                                   NativeOnActionFieldArchive.Store store) throws IOException {
        boolean[] covered = new boolean[input.originalBlocks().size()];
        for (OpenedFile file : sources.files()) {
            byte[] whole = load(file.originalBytes(), store, true);
            for (Piece piece : file.pieces()) {
                StrictJson.require(piece.block() < covered.length && !covered[piece.block()],
                        "original block must bind to exactly one opened-file slice");
                byte[] raw = load(input.originalBlocks().get(piece.block()).originalSourcePiece(), store, false);
                StrictJson.require(piece.offset() <= whole.length && raw.length <= whole.length - piece.offset(),
                        "original source slice exceeds opened byte buffer");
                StrictJson.require(Arrays.equals(raw, Arrays.copyOfRange(whole, piece.offset(), piece.offset() + raw.length)),
                        "original block bytes differ from the actual retained opened-file slice");
                covered[piece.block()] = true;
            }
        }
        boolean complete = !sources.files().isEmpty();
        for (boolean present : covered) complete &= present;
        if (sources.boundary().isEmpty())
            return sources.origin() == Origin.SOFTWARE_FIXTURE ? Custody.SOFTWARE_FIXTURE : Custody.SOURCE_BINDING_UNAVAILABLE;
        Boundary boundary = sources.boundary().orElseThrow();
        load(boundary.mountTable(), store, false); load(boundary.replacementRules(), store, false);
        byte[] vfsBefore = load(boundary.vfsBefore(), store, false), vfsAfter = load(boundary.vfsAfter(), store, false);
        byte[] payloadBefore = load(boundary.payloadBefore(), store, false), payloadAfter = load(boundary.payloadAfter(), store, false);
        // A stable native object address is intentionally absent from this comparison.
        if (!Arrays.equals(vfsBefore, vfsAfter) || !Arrays.equals(payloadBefore, payloadAfter)) return Custody.CHANGED_DURING_CAPTURE;
        if (sources.origin() == Origin.SOFTWARE_FIXTURE) return Custody.SOFTWARE_FIXTURE;
        return complete ? Custody.ORIGINAL_BYTES_ACCOUNTED : Custody.SOURCE_BINDING_UNAVAILABLE;
    }

    public static byte[] encode(Envelope envelope) {
        Objects.requireNonNull(envelope); Sources sources = envelope.sources();
        ObjectNode root = StrictJson.object().put("schema", SCHEMA).put("exe_sha256", NativePlayableAnnualGate.EXECUTABLE_SHA256)
                .put("machine_id", sources.machineId()).put("observed_at_utc", sources.observedAtUtc()).put("origin", sources.origin().name());
        ArrayNode files = root.putArray("opened_files");
        for (OpenedFile file : sources.files()) {
            ObjectNode row = files.addObject().put("ordinal", file.ordinal()).put("native_path_hex", file.nativePathHex());
            row.set("original_bytes", file.originalBytes().toJson()); ArrayNode pieces = row.putArray("pieces");
            for (Piece piece : file.pieces()) pieces.addObject().put("block", piece.block()).put("offset", piece.offset());
        }
        if (sources.boundary().isEmpty()) root.putNull("boundary");
        else {
            Boundary boundary = sources.boundary().orElseThrow(); ObjectNode row = root.putObject("boundary");
            row.set("mount_table", boundary.mountTable().toJson()); row.set("replacement_rules", boundary.replacementRules().toJson());
            row.set("vfs_before", boundary.vfsBefore().toJson()); row.set("vfs_after", boundary.vfsAfter().toJson());
            row.set("payload_before", boundary.payloadBefore().toJson()); row.set("payload_after", boundary.payloadAfter().toJson());
        }
        root.set("field_archive", StrictJson.parse(NativeOnActionFieldArchive.encode(envelope.fieldArchive())));
        return StrictJson.canonical(root, MAX_BYTES);
    }

    public static Envelope decode(byte[] raw) {
        ObjectNode root = exact(StrictJson.parse(raw, MAX_BYTES), "schema", "exe_sha256", "machine_id", "observed_at_utc", "origin", "opened_files", "boundary", "field_archive");
        StrictJson.require(SCHEMA.equals(StrictJson.text(root.get("schema"))), "exact source envelope schema required");
        StrictJson.require(NativePlayableAnnualGate.EXECUTABLE_SHA256.equals(StrictJson.text(root.get("exe_sha256"))), "source-reviewed native executable required");
        List<OpenedFile> files = new ArrayList<>();
        for (JsonNode rawFile : array(root.get("opened_files"), 8192)) {
            ObjectNode file = exact(rawFile, "ordinal", "native_path_hex", "original_bytes", "pieces"); List<Piece> pieces = new ArrayList<>();
            for (JsonNode rawPiece : array(file.get("pieces"), 1024)) {
                ObjectNode piece = exact(rawPiece, "block", "offset"); pieces.add(new Piece(integer(piece.get("block")), integer(piece.get("offset"))));
            }
            files.add(new OpenedFile(integer(file.get("ordinal")), StrictJson.text(file.get("native_path_hex")), ExactRef.fromJson(file.get("original_bytes")), pieces));
        }
        JsonNode rawBoundary = root.get("boundary"); Optional<Boundary> boundary;
        if (rawBoundary.isNull()) boundary = Optional.empty();
        else {
            ObjectNode row = exact(rawBoundary, "mount_table", "replacement_rules", "vfs_before", "vfs_after", "payload_before", "payload_after");
            boundary = Optional.of(new Boundary(ExactRef.fromJson(row.get("mount_table")), ExactRef.fromJson(row.get("replacement_rules")),
                    ExactRef.fromJson(row.get("vfs_before")), ExactRef.fromJson(row.get("vfs_after")),
                    ExactRef.fromJson(row.get("payload_before")), ExactRef.fromJson(row.get("payload_after"))));
        }
        Sources sources = new Sources(StrictJson.text(root.get("machine_id")), StrictJson.text(root.get("observed_at_utc")),
                Origin.valueOf(StrictJson.text(root.get("origin"))), files, boundary);
        var recorded = NativeOnActionFieldArchive.decode(StrictJson.canonical(root.get("field_archive")));
        return new Envelope(sources, recorded);
    }
    private static ObjectNode exact(JsonNode node, String... fields) { return StrictJson.object(node, Set.of(fields)); }
    private static int integer(JsonNode node) { return StrictJson.integer(node, BigInteger.ZERO, BigInteger.valueOf(MAX_BYTES)).intValueExact(); }
    private static ArrayNode array(JsonNode node, int maximum) {
        StrictJson.require(node instanceof ArrayNode && node.size() <= maximum, "bounded exact JSON array required"); return (ArrayNode) node;
    }
    private static byte[] load(ExactRef ref, NativeOnActionFieldArchive.Store store, boolean emptyAllowed) throws IOException {
        Objects.requireNonNull(ref); StrictJson.require(ref.bytes() >= (emptyAllowed ? 0 : 1) && ref.bytes() <= MAX_BYTES, "bounded original custody object required");
        byte[] raw = store.load(ref);
        StrictJson.require(raw != null && raw.length == ref.bytes() && sha256(raw).equals(ref.sha256()), "retained original length or SHA-256 drift");
        return raw.clone();
    }
    private static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

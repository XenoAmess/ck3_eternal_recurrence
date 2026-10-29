package org.xar.ck3.control.application.readiness;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Set;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Sole strict v3 source-proof wire boundary, independent of build tools and current Game guards. */
public final class NativeSourceProofCodec {
    private static final Set<String> FIELDS = Set.of("schema", "machine_id", "session_id", "observed_at_utc",
            "mode", "host_configuration", "source", "owner_source_epoch", "source_epoch_manifest",
            "game_executable", "complete_evidence_closure", "live_witnesses");
    private static final Set<String> NATIVE_FIELDS = Set.of("volume_serial_decimal", "file_id_decimal",
            "legacy_volume_serial_decimal", "legacy_file_id_decimal", "creation_filetime_decimal",
            "last_write_filetime_decimal", "change_filetime_decimal", "logical_bytes", "allocated_bytes", "link_count");
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(NativeSourceProofDocument.MAXIMUM_BYTES)
                    .maxNumberLength(64).maxNestingDepth(12).build())
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private NativeSourceProofCodec() { }

    public static NativeSourceProofDocument decode(byte[] original) throws IOException {
        if (original == null || original.length < 1 || original.length > NativeSourceProofDocument.MAXIMUM_BYTES)
            throw new IOException("bounded complete original native source proof required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(original)).toString();
            ObjectNode row = StrictJson.object(MAPPER.readTree(text), FIELDS);
            StrictJson.require(NativeSourceProofDocument.SCHEMA.equals(StrictJson.text(row.get("schema"))),
                    "original v3 live Witnesses required; v2 identity is MISSING");
            ArrayList<ExactRef> sources = new ArrayList<>();
            JsonNode closure = row.get("complete_evidence_closure");
            StrictJson.require(closure != null && closure.isArray()
                            && closure.size() <= NativeSourceProofDocument.MAXIMUM_WITNESSES,
                    "bounded source closure array required");
            for (JsonNode value : closure) sources.add(ExactRef.fromJson(value));
            ArrayList<SourceWitness> witnesses = new ArrayList<>();
            JsonNode retained = row.get("live_witnesses");
            StrictJson.require(retained != null && retained.isArray()
                            && retained.size() <= NativeSourceProofDocument.MAXIMUM_WITNESSES,
                    "bounded original live Witness array required");
            for (JsonNode value : retained) {
                ObjectNode witness = StrictJson.object(value, Set.of("source", "native_file"));
                witnesses.add(new SourceWitness(ExactRef.fromJson(witness.get("source")), nativeIdentity(witness.get("native_file"))));
            }
            return new NativeSourceProofDocument(StrictJson.text(row.get("machine_id")),
                    StrictJson.text(row.get("session_id")), StrictJson.text(row.get("observed_at_utc")),
                    NativeSourceProofDocument.Mode.valueOf(StrictJson.text(row.get("mode"))),
                    ExactRef.fromJson(row.get("host_configuration")), ExactRef.fromJson(row.get("source")),
                    StrictJson.text(row.get("owner_source_epoch")), ExactRef.fromJson(row.get("source_epoch_manifest")),
                    ExactRef.fromJson(row.get("game_executable")), sources, witnesses);
        } catch (CharacterCodingException error) {
            throw new IOException("invalid UTF-8 original source proof", error);
        } catch (IllegalArgumentException | NullPointerException error) {
            throw new IOException("invalid original v3 native source proof", error);
        }
    }

    private static NativeSourceFileIdentity nativeIdentity(JsonNode value) {
        ObjectNode row = StrictJson.object(value, NATIVE_FIELDS);
        return new NativeSourceFileIdentity(StrictJson.text(row.get("volume_serial_decimal")),
                StrictJson.text(row.get("file_id_decimal")), StrictJson.text(row.get("legacy_volume_serial_decimal")),
                legacyHex(row.get("legacy_file_id_decimal")), StrictJson.text(row.get("creation_filetime_decimal")),
                StrictJson.text(row.get("last_write_filetime_decimal")), StrictJson.text(row.get("change_filetime_decimal")),
                StrictJson.integer(row.get("logical_bytes"), 0, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("allocated_bytes"), 0, StrictJson.MAX_SAFE_INTEGER),
                StrictJson.integer(row.get("link_count"), 1, 0xffff_ffffL));
    }

    /** The original exporter uses sixteen hex digits in memory; all persisted FileIDs use decimal. */
    private static String legacyHex(JsonNode value) {
        String decimal = StrictJson.text(value);
        StrictJson.require(decimal.length() <= 20 && decimal.matches("0|[1-9][0-9]*"),
                "canonical unsigned legacy FileID64 decimal required");
        BigInteger number = new BigInteger(decimal);
        StrictJson.require(number.bitLength() <= 64, "legacy FileID64 exceeds unsigned 64-bit range");
        String hex = number.toString(16);
        return "0".repeat(16 - hex.length()) + hex;
    }

    public static byte[] encode(NativeSourceProofDocument document) throws IOException {
        ObjectNode row = StrictJson.object();
        row.put("schema", NativeSourceProofDocument.SCHEMA);
        row.put("machine_id", document.machineId()); row.put("session_id", document.sessionId());
        row.put("observed_at_utc", document.observedAtUtc()); row.put("mode", document.mode().name());
        row.set("host_configuration", document.hostConfiguration().toJson()); row.set("source", document.source().toJson());
        row.put("owner_source_epoch", document.ownerSourceEpoch()); row.set("source_epoch_manifest", document.sourceEpochManifest().toJson());
        row.set("game_executable", document.gameExecutable().toJson());
        var closure = row.putArray("complete_evidence_closure");
        document.completeEvidenceClosure().forEach(reference -> closure.add(reference.toJson()));
        var witnesses = row.putArray("live_witnesses");
        for (SourceWitness witness : document.liveWitnesses()) {
            ObjectNode value = witnesses.addObject(); value.set("source", witness.source().toJson());
            NativeSourceFileIdentity nativeFile = witness.nativeFile(); ObjectNode facts = value.putObject("native_file");
            facts.put("volume_serial_decimal", nativeFile.volumeSerialDecimal()); facts.put("file_id_decimal", nativeFile.fileIdDecimal());
            facts.put("legacy_volume_serial_decimal", nativeFile.legacyVolumeSerialDecimal());
            facts.put("legacy_file_id_decimal", new BigInteger(nativeFile.legacyFileIdHex(), 16).toString());
            facts.put("creation_filetime_decimal", nativeFile.creationFiletimeDecimal()); facts.put("last_write_filetime_decimal", nativeFile.lastWriteFiletimeDecimal());
            facts.put("change_filetime_decimal", nativeFile.changeFiletimeDecimal()); facts.put("logical_bytes", nativeFile.logicalBytes());
            facts.put("allocated_bytes", nativeFile.allocatedBytes()); facts.put("link_count", nativeFile.linkCount());
        }
        byte[] original = MAPPER.writeValueAsBytes(row);
        if (original.length < 1 || original.length > NativeSourceProofDocument.MAXIMUM_BYTES)
            throw new IOException("complete native source proof exceeds finite role limit");
        if (!decode(original).equals(document)) throw new IOException("native source proof did not roundtrip through its sole contract");
        return original;
    }
}

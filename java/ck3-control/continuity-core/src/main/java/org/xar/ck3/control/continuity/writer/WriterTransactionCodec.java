package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Sole strict transaction DATA codec. Decoding never proves canonical membership or authorizes a write. */
public final class WriterTransactionCodec {
    public static final String PREPARED_SCHEMA = "xar.continuity-writer.prepared/v1";
    public static final String RECEIPT_SCHEMA = "xar.continuity-writer.receipt/v1";
    public static final int MAXIMUM_BYTES = Math.multiplyExact(4, ContinuityJson.DOCUMENT_MAX_BYTES);
    private WriterTransactionCodec() { }

    public static byte[] encodePrepared(Prepared value) {
        Objects.requireNonNull(value);
        StrictJson.require(value.predecessor().state().machineId().equals(value.reduced().machineId())
                && value.predecessor().state().sequence() == value.reduced().sequence(),
                "prepared reducer must retain its actual predecessor machine and sequence");
        StrictJson.require(!value.sources().isEmpty() && value.sources().size() <= MAXIMUM_CONFIGURED_SOURCES
                && value.evidence().stream().map(Pin::reference).toList().equals(value.request().evidence()),
                "prepared retains its finite configured sources and exact request evidence pins");
        ObjectNode row = StrictJson.object().put("schema", PREPARED_SCHEMA);
        row.set("predecessor", head(value.predecessor()));
        ObjectNode request = row.putObject("request").put("kind", value.request().kind());
        request.set("details", value.request().detailsObject());
        references(request.putArray("evidence"), value.request().evidence());
        pins(row.putArray("sources"), value.sources()); pins(row.putArray("evidence"), value.evidence());
        row.set("reduced", value.reduced().toJson()); row.put("precondition_digest", value.preconditionDigest());
        return bounded(row);
    }

    public static Prepared decodePrepared(byte[] raw, String expectedMachineId) {
        StrictJson.text(expectedMachineId);
        ObjectNode row = strict(raw, Set.of("schema", "predecessor", "request", "sources", "evidence", "reduced", "precondition_digest"));
        StrictJson.require(PREPARED_SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact prepared schema required");
        ObjectNode request = StrictJson.object(row.get("request"), Set.of("kind", "details", "evidence"));
        Prepared value = new Prepared(head(row.get("predecessor"), expectedMachineId),
                new Request(StrictJson.text(request.get("kind")), ContinuityJson.canonical(object(request.get("details"))),
                        references(request.get("evidence"))), pins(row.get("sources")), pins(row.get("evidence")),
                ContinuityState.fromJson(row.get("reduced"), expectedMachineId), StrictJson.text(row.get("precondition_digest")));
        requireExact(raw, encodePrepared(value)); return value;
    }

    public static byte[] encodeReceipt(Receipt value) {
        Objects.requireNonNull(value);
        ObjectNode row = StrictJson.object().put("schema", RECEIPT_SCHEMA).put("disposition", value.disposition().name());
        row.set("head", value.head().toJson()); row.put("event_identity", value.eventIdentity());
        row.put("writes", value.writes()).put("recovered_committed_receipt", value.recoveredCommittedReceipt());
        return bounded(row);
    }

    public static Receipt decodeReceipt(byte[] raw, String expectedMachineId) {
        StrictJson.text(expectedMachineId);
        ObjectNode row = strict(raw, Set.of("schema", "disposition", "head", "event_identity", "writes", "recovered_committed_receipt"));
        StrictJson.require(RECEIPT_SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact receipt schema required");
        JsonNode recovered = row.get("recovered_committed_receipt");
        StrictJson.require(recovered != null && recovered.isBoolean(), "explicit recovered receipt boolean required");
        Receipt value = new Receipt(Disposition.valueOf(StrictJson.text(row.get("disposition"))),
                ContinuityState.fromJson(row.get("head"), expectedMachineId), StrictJson.text(row.get("event_identity")),
                Math.toIntExact(StrictJson.integer(row.get("writes"), 0, Integer.MAX_VALUE)), recovered.booleanValue());
        requireExact(raw, encodeReceipt(value)); return value;
    }

    private static ObjectNode head(Head value) {
        ObjectNode row = StrictJson.object(); row.set("state", value.state().toJson());
        pins(row.putArray("documents"), value.documents());
        ArrayNode absent = row.putArray("absent"); value.absent().forEach(path -> absent.add(path(path)));
        ArrayNode repairs = row.putArray("index_repairs");
        for (IndexRepair repair : value.indexRepairs()) {
            ObjectNode encoded = repair.toJson(); encoded.put("path", path(repair.path())); repairs.add(encoded);
        }
        row.put("snapshot_needs_recovery", value.snapshotNeedsRecovery()); return row;
    }

    private static Head head(JsonNode input, String machine) {
        ObjectNode row = StrictJson.object(input, Set.of("state", "documents", "absent", "index_repairs", "snapshot_needs_recovery"));
        List<Path> absent = new ArrayList<>();
        for (JsonNode value : array(row.get("absent"))) absent.add(path(value));
        List<IndexRepair> repairs = new ArrayList<>();
        for (JsonNode value : array(row.get("index_repairs"))) {
            ObjectNode repair = StrictJson.object(value, Set.of("path", "sequence", "identity"));
            repairs.add(new IndexRepair(path(repair.get("path")), StrictJson.integer(repair.get("sequence"), 1, StrictJson.MAX_SAFE_INTEGER),
                    StrictJson.text(repair.get("identity"))));
        }
        JsonNode recovery = row.get("snapshot_needs_recovery");
        StrictJson.require(recovery != null && recovery.isBoolean(), "explicit snapshot recovery boolean required");
        return new Head(ContinuityState.fromJson(row.get("state"), machine), pins(row.get("documents")), absent, repairs, recovery.booleanValue());
    }

    private static void pins(ArrayNode output, List<Pin> values) { values.forEach(value -> output.add(value.toJson())); }
    private static List<Pin> pins(JsonNode input) {
        List<Pin> values = new ArrayList<>(); for (JsonNode value : array(input)) values.add(Pin.fromJson(value)); return List.copyOf(values);
    }
    private static void references(ArrayNode output, List<ExactRef> values) { values.forEach(value -> output.add(value.toJson())); }
    private static List<ExactRef> references(JsonNode input) {
        List<ExactRef> values = new ArrayList<>(); for (JsonNode value : array(input)) values.add(ExactRef.fromJson(value)); return List.copyOf(values);
    }
    private static ArrayNode array(JsonNode input) {
        StrictJson.require(input instanceof ArrayNode, "explicit transaction array required"); return (ArrayNode) input;
    }
    private static ObjectNode object(JsonNode value) { return ContinuityJson.object(value); }
    private static ObjectNode strict(byte[] raw, Set<String> fields) {
        return StrictJson.object(ContinuityJson.parseObject(Objects.requireNonNull(raw), MAXIMUM_BYTES), fields);
    }
    private static byte[] bounded(ObjectNode row) {
        byte[] bytes = ContinuityJson.canonical(row, MAXIMUM_BYTES);
        StrictJson.require(bytes.length <= MAXIMUM_BYTES, "transaction DATA exceeds explicit finite transaction cap"); return bytes;
    }
    private static String path(Path value) {
        Objects.requireNonNull(value); StrictJson.require(value.isAbsolute() && value.normalize().equals(value), "absolute normalized transaction path required");
        return value.toString();
    }
    private static Path path(JsonNode value) {
        String text = StrictJson.text(value); Path path = Path.of(text);
        StrictJson.require(path(path).equals(text), "canonical absolute transaction path required"); return path;
    }
    private static void requireExact(byte[] original, byte[] encoded) {
        StrictJson.require(Arrays.equals(original, encoded), "canonical transaction DATA changed during strict roundtrip");
    }
}

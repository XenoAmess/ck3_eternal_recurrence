package org.xar.ck3.control.wave2.development.constructionreadback;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.CurrentProcess;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.LastCheckDate;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Ledger;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.MaterialObservation;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Receipt;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.ReceiptIdentity;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Scope;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Snapshot;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.SourceFrame;

/** Bounded, strict new request; only declared members of old SDK and ledger containers are projected. */
public final class ConstructionReadbackJson {
    public static final String SCHEMA = "xar.ck3.construction-readback-java-request/v1";
    public static final int MAX_BYTES = 65_536;
    private static final ObjectMapper OUTPUT = new ObjectMapper();
    private ConstructionReadbackJson() { }

    /** Returns the old scope object or the old selected receipt/null, retaining SDK extension values. */
    public static byte[] project(byte[] raw) {
        ObjectNode request = object(StrictJson.parse(raw, MAX_BYTES));
        StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "readback request schema mismatch");
        String operation = StrictJson.text(request.get("operation"));
        if ("scope".equals(operation)) {
            StrictJson.object(request, Set.of("schema", "operation", "receipt"));
            return StrictJson.canonical(scopeTree(ConstructionReceiptReadback.readbackScope(receipt(request.get("receipt")))));
        }
        StrictJson.require("priority".equals(operation), "unknown construction readback operation");
        StrictJson.object(request, Set.of("schema", "operation", "ledger", "snapshot", "process_identity"));
        ObjectNode originalLedger = object(request.get("ledger"));
        ObjectNode originalSnapshot = object(request.get("snapshot"));
        Ledger ledger = ledger(originalLedger);
        Snapshot snapshot = new Snapshot(text(originalSnapshot.get("episode_run_id")),
                integer(originalSnapshot.get("native_revision")), integer(originalSnapshot.get("date_raw")));
        Optional<CurrentProcess> process = Optional.empty();
        JsonNode processInput = request.get("process_identity");
        if (!processInput.isNull()) {
            ObjectNode originalProcess = StrictJson.object(processInput, Set.of("pid", "creation_time"));
            BigInteger pid = integer(originalProcess.get("pid"));
            String creation = text(originalProcess.get("creation_time"));
            StrictJson.require(pid != null && pid.signum() > 0 && creation != null && !creation.isEmpty(),
                    "current process observation must be explicitly supplied");
            process = Optional.of(new CurrentProcess(pid, creation));
        }
        if (process.isEmpty() && !ConstructionReceiptReadback.appliedReceipts(ledger, snapshot.episodeRunId()).isEmpty()) {
            throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE,
                    "nonempty receipt priority requires an actual process observation");
        }
        var priority = ConstructionReceiptReadback.priorityReceipt(ledger, snapshot, process);
        if (priority.isEmpty()) { return new byte[]{'n', 'u', 'l', 'l'}; }
        List<JsonNode> originals = originalReceipts(originalLedger, snapshot.episodeRunId());
        return output(originals.get(priority.orElseThrow().receiptIndex()));
    }

    public static Receipt receipt(JsonNode raw) {
        ObjectNode row = object(raw);
        ReceiptIdentity identity = new ReceiptIdentity(text(row.get("action_request_id")), text(row.get("episode_run_id")),
                integer(row.get("actor_character_id")));
        Scope old = new Scope(integer(row.get("post_bridge_pid")), text(row.get("post_bridge_creation_date")),
                integer(row.get("post_native_revision")), integer(row.get("post_date_raw")));
        MaterialObservation observation = observation(row.get("material_observation_unavailable_v1"));
        JsonNode postCash = row.get("post_cash_v2");
        StrictJson.require(postCash == null || postCash.isNull() || postCash.isObject(), "post cash must be object or null");
        ObjectNode province = nullableObject(row.get("construction_province_income_observation"));
        return new Receipt(identity, old, observation, text(row.get("completion_status")),
                integer(row.get("observed_player_monthly_gold_income_raw")), postCash != null && postCash.isObject(),
                province == null ? null : text(province.get("status")),
                new LastCheckDate(row.has("completion_last_check_date_raw"), integer(row.get("completion_last_check_date_raw"))));
    }

    public static Ledger ledger(JsonNode raw) {
        ObjectNode row = object(raw);
        List<Receipt> prior = new ArrayList<>();
        for (JsonNode original : priorRows(row.get("applied_prior"))) { prior.add(receipt(original)); }
        JsonNode applied = row.get("applied");
        return new Ledger(prior, applied == null || applied.isNull() ? null : receipt(applied));
    }

    public static ObjectNode scopeTree(Scope scope) {
        ObjectNode result = StrictJson.object();
        result.put("bridge_pid", scope.bridgePid());
        result.put("bridge_creation_date", scope.bridgeCreationDate());
        result.put("native_revision", scope.nativeRevision());
        result.put("date_raw", scope.dateRaw());
        return result;
    }

    private static MaterialObservation observation(JsonNode raw) {
        ObjectNode row = nullableObject(raw);
        if (row == null) { return null; }
        ObjectNode source = nullableObject(row.get("source_frame"));
        SourceFrame frame = source == null ? null : new SourceFrame(integer(source.get("actor_character_id")),
                text(source.get("episode_run_id")), integer(source.get("native_revision")), integer(source.get("revision")),
                integer(source.get("date_raw")), integer(source.get("bridge_pid")), text(source.get("snapshot_id")),
                text(source.get("bridge_creation_date")));
        return new MaterialObservation(text(row.get("schema")), evidence(row.get("read_only")),
                evidence(row.get("business_submission")), integer(row.get("native_submit_calls")),
                text(row.get("action_request_id")), frame);
    }

    private static List<JsonNode> originalReceipts(ObjectNode ledger, String episodeRunId) {
        List<JsonNode> originals = new ArrayList<>(priorRows(ledger.get("applied_prior")));
        JsonNode applied = ledger.get("applied");
        if (applied != null && !applied.isNull()) { originals.add(object(applied)); }
        return originals.stream().filter(row -> Objects.equals(text(row.get("episode_run_id")), episodeRunId)).toList();
    }

    private static List<JsonNode> priorRows(JsonNode value) {
        if (value == null || value.isNull()) { return List.of(); }
        StrictJson.require(value instanceof ArrayNode, "applied prior receipts must be array or null");
        List<JsonNode> rows = new ArrayList<>();
        for (JsonNode row : value) { rows.add(object(row)); }
        return List.copyOf(rows);
    }

    private static byte[] output(JsonNode value) {
        try {
            byte[] raw = OUTPUT.writeValueAsBytes(value);
            StrictJson.require(raw.length <= MAX_BYTES, "readback selected receipt exceeds budget");
            return raw;
        } catch (JsonProcessingException error) {
            throw new ContractViolationException("cannot serialize readback projection", error);
        }
    }

    private static ObjectNode nullableObject(JsonNode value) { return value == null || value.isNull() ? null : object(value); }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "readback object required");
        return (ObjectNode) value;
    }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "readback text must be string or null");
        return value.textValue().isEmpty() ? "" : StrictJson.text(value);
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "readback exact integer required");
        return value.bigIntegerValue();
    }
    private static Evidence evidence(JsonNode value) {
        if (value == null || value.isNull()) { return Evidence.UNKNOWN; }
        StrictJson.require(value.isBoolean(), "readback exact boolean required");
        return Evidence.of(value.booleanValue());
    }
}

package org.xar.ck3.control.warbudget;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** One in-process boundary to the existing political producer/qualifier. It grants no action eligibility. */
public final class BudgetPoliticalStakesCodec {
    private static final int MAX_RECEIPT_BYTES = 65_536;
    private static final JsonFactory JSON = new JsonFactory();
    private BudgetPoliticalStakesCodec() { }
    public enum Status { AVAILABLE, UNAVAILABLE }

    /** A single privately owned SDK decode; raw array ordinals remain stable and no mutable JSON escapes. */
    public static final class Context {
        private final ObjectNode snapshot;
        private final ObjectNode currentRoot;
        private Context(ObjectNode snapshot, JsonNode root) {
            this.snapshot = snapshot.deepCopy();
            this.currentRoot = BudgetObservations.currentRoot(this.snapshot, root).deepCopy();
        }
        public byte[] currentRootJsonBytes() { return encodeProjection(currentRoot); }
        public int activeWarCount() {
            JsonNode wars = snapshot.get("active_wars");
            return wars != null && wars.isArray() ? wars.size() : 0;
        }
    }

    /** Boundary receipt: immutable original projection plus qualifier computed by the unique source algorithm. */
    public static final class Result {
        private final byte[] projection;
        private final Status status;
        private final String reason;
        private final boolean qualified;
        private Result(ObjectNode observed) {
            this.qualified = BudgetObservations.politicalQualified(observed);
            this.status = BudgetJson.text(observed.get("status"), "available") ? Status.AVAILABLE : Status.UNAVAILABLE;
            this.reason = StrictJson.text(observed.get("reason"));
            this.projection = encodeProjection(observed);
        }
        public Status status() { return status; }
        public String reason() { return reason; }
        public byte[] toJsonBytes() { return projection.clone(); }
    }

    /** Root is an actual JSON object or literal null. Same-frame root selection is performed once here. */
    public static Context parseContext(byte[] snapshotJson, byte[] campaignRootJson) {
        ObjectNode snapshot = BudgetJson.record(StrictJson.parse(snapshotJson));
        JsonNode root = StrictJson.parse(campaignRootJson);
        StrictJson.require(root.isObject() || root.isNull(), "political root must be object or explicit null");
        return new Context(snapshot, root);
    }
    /** Observe the actual row at the raw SDK array index, preserving the original unique-war check. */
    public static Result observe(Context context, int activeWarOrdinal) {
        Objects.requireNonNull(context);
        StrictJson.require(activeWarOrdinal >= 0 && activeWarOrdinal < context.activeWarCount(), "active war ordinal outside original SDK rows");
        ObjectNode war = BudgetJson.record(context.snapshot.get("active_wars").get(activeWarOrdinal));
        return new Result(BudgetObservations.political(context.snapshot, war, context.currentRoot));
    }
    public static boolean qualified(Result result) { return Objects.requireNonNull(result).qualified; }
    /** Parse a persisted source profile and invoke the same original qualifier; no caller boolean substitutes for it. */
    public static boolean qualify(byte[] persistedProfileJson) {
        return BudgetObservations.politicalQualified(StrictJson.parse(persistedProfileJson));
    }

    /** SDK identity extensions remain opaque JSON, including finite fractional values; known IDs stay strict. */
    private static byte[] encodeProjection(JsonNode value) {
        try (ByteArrayOutputStream out = new ByteArrayOutputStream(); JsonGenerator writer = JSON.createGenerator(out)) {
            append(value, writer); writer.flush();
            StrictJson.require(out.size() <= MAX_RECEIPT_BYTES, "political receipt exceeds finite byte budget");
            return out.toByteArray();
        } catch (IOException error) { throw new ContractViolationException("political projection could not be encoded", error); }
    }
    private static void append(JsonNode value, JsonGenerator writer) throws IOException {
        if (value.isObject()) {
            writer.writeStartObject();
            var fields = value.fieldNames();
            while (fields.hasNext()) { String name = fields.next(); if (!name.isEmpty()) { StrictJson.text(name); } writer.writeFieldName(name); append(value.get(name), writer); }
            writer.writeEndObject();
        } else if (value.isArray()) {
            writer.writeStartArray(); for (JsonNode row : value) { append(row, writer); } writer.writeEndArray();
        } else if (value.isIntegralNumber()) { writer.writeNumber(value.bigIntegerValue()); }
        else if (value.isFloatingPointNumber()) {
            String spelling = value.decimalValue().toString();
            if (spelling.indexOf('.') < 0 && spelling.indexOf('E') < 0 && spelling.indexOf('e') < 0) { spelling += ".0"; }
            writer.writeNumber(spelling);
        } else if (value.isTextual()) { if (!value.textValue().isEmpty()) { StrictJson.text(value); } writer.writeString(value.textValue()); }
        else if (value.isBoolean()) { writer.writeBoolean(value.booleanValue()); }
        else if (value.isNull()) { writer.writeNull(); }
        else { throw new ContractViolationException("unsupported SDK projection token"); }
    }
}

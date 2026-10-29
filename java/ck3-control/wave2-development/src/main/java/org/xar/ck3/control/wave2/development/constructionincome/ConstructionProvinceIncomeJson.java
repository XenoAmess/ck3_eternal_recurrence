package org.xar.ck3.control.wave2.development.constructionincome;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.Frame;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.Observation;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.PriorObservation;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.PriorReceipt;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.ProvinceRow;
import org.xar.ck3.control.wave2.development.constructionincome.ConstructionProvinceIncome.Target;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;

/** Strict observation boundary; old world/receipt containers are declared projections with extension preservation. */
public final class ConstructionProvinceIncomeJson {
    public static final String SCHEMA = "xar.ck3.construction-province-income-java-request/v1";
    private static final ObjectMapper OUTPUT = new ObjectMapper();
    private ConstructionProvinceIncomeJson() { }

    public static byte[] project(byte[] raw) {
        ObjectNode request = object(StrictJson.parse(raw));
        StrictJson.require(SCHEMA.equals(StrictJson.text(request.get("schema"))), "province income schema mismatch");
        String operation = StrictJson.text(request.get("operation"));
        if ("observe".equals(operation)) {
            StrictJson.object(request, Set.of("schema", "operation", "world", "candidate", "source_frame"));
        } else {
            StrictJson.require("receipt_income".equals(operation), "unknown province income operation");
            StrictJson.object(request, Set.of("schema", "operation", "world", "candidate", "source_frame",
                    "prior_receipt", "cold_recheck", "completed"));
        }
        ObjectNode world = object(request.get("world"));
        ObjectNode candidate = object(request.get("candidate"));
        ObjectNode frame = object(request.get("source_frame"));
        Observation current = ConstructionProvinceIncome.observe(rows(world.get("active_constructions")),
                target(candidate), new Frame(text(frame.get("snapshot_id")), integer(frame.get("native_revision")),
                        integer(frame.get("date_raw"))));
        ObjectNode result = tree(current);
        if ("receipt_income".equals(operation)) {
            ObjectNode receipt = object(request.get("prior_receipt"));
            ObjectNode previous = nullableObject(receipt.get("construction_province_income_observation"));
            PriorReceipt prior = new PriorReceipt(text(receipt.get("completion_status")),
                    integer(receipt.get("completion_observed_date_raw")), previous == null ? null
                            : new PriorObservation(text(previous.get("status")), integer(previous.get("date_raw"))));
            if (ConstructionProvinceIncome.retainPrior(current.status(), prior,
                    bool(request.get("cold_recheck")), bool(request.get("completed")))) {
                StrictJson.require(previous != null, "retained province observation absent");
                result = previous.deepCopy();
            }
        }
        try {
            byte[] output = OUTPUT.writeValueAsBytes(result);
            StrictJson.require(output.length <= StrictJson.INPUT_MAX_BYTES, "province observation exceeds budget");
            return output;
        } catch (JsonProcessingException error) {
            throw new ContractViolationException("cannot serialize province income observation", error);
        }
    }

    public static ObjectNode tree(Observation observation) {
        ObjectNode result = StrictJson.object();
        result.put("status", observation.status().wire());
        result.put("barony_title_id", observation.target().baronyTitleId());
        result.put("province_id", observation.target().provinceId());
        result.put("snapshot_id", observation.frame().snapshotId());
        result.put("native_revision", observation.frame().nativeRevision());
        result.put("date_raw", observation.frame().dateRaw());
        result.put("native_province_monthly_income_raw", observation.monthlyIncomeRaw());
        return result;
    }

    private static List<ProvinceRow> rows(JsonNode raw) {
        if (raw == null || raw.isNull()) { return List.of(); }
        StrictJson.require(raw instanceof ArrayNode, "active constructions must be array or null");
        List<ProvinceRow> result = new ArrayList<>();
        for (JsonNode value : raw) {
            // The source intentionally ignores non-mapping elements in this extensible world list.
            if (value instanceof ObjectNode row) {
                result.add(new ProvinceRow(target(row), evidence(row.get("native_province_monthly_income_observed")),
                        integer(row.get("native_province_monthly_income_raw"))));
            }
        }
        return List.copyOf(result);
    }
    private static Target target(ObjectNode row) {
        return new Target(integer(row.get("barony_title_id")), integer(row.get("province_id")));
    }
    private static ObjectNode nullableObject(JsonNode value) { return value == null || value.isNull() ? null : object(value); }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "province income object required");
        return (ObjectNode) value;
    }
    private static String text(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isTextual(), "province income text must be string or null");
        return value.textValue().isEmpty() ? "" : StrictJson.text(value);
    }
    private static BigInteger integer(JsonNode value) {
        if (value == null || value.isNull()) { return null; }
        StrictJson.require(value.isIntegralNumber(), "province income exact integer required");
        return value.bigIntegerValue();
    }
    private static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "province income exact boolean required");
        return value.booleanValue();
    }
    private static Evidence evidence(JsonNode value) {
        return value == null || value.isNull() ? Evidence.UNKNOWN : Evidence.of(bool(value));
    }
}

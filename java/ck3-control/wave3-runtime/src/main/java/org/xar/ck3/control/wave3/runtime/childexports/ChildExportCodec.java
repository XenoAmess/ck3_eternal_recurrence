package org.xar.ck3.control.wave3.runtime.childexports;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackCodec;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.ProcessKey;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.Export;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.Packet;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.ProcessReadbacks;
import org.xar.ck3.control.wave3.runtime.childexports.ChildExportValues.RemoteLocation;

/** Exact original private wire. Actual retained edge, handle transfer and issuer remain with the original adapter. */
public final class ChildExportCodec {
    public static final String KIND = "actual_child_exports";
    public static final int PRIVATE_MESSAGE_MAX_BYTES = OriginReadbackCodec.PRIVATE_MESSAGE_MAX_BYTES;
    /** Original managed interpreter's private JSON wire profile; the in-memory integer model remains unbounded. */
    public static final int PRIVATE_INTEGER_MAX_DECIMAL_DIGITS =
            StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300.maximumDecimalDigits();

    private ChildExportCodec() { }

    public static Packet decode(ChildRole exportingRole, byte[] raw) {
        return parse(exportingRole, StrictJson.parse(raw, PRIVATE_MESSAGE_MAX_BYTES,
                StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300));
    }

    public static Packet parse(ChildRole exportingRole, JsonNode value) {
        ObjectNode root = StrictJson.object(value, Set.of("kind", "exports"));
        StrictJson.require(root.get("kind").isTextual() && KIND.equals(root.get("kind").textValue()),
                "exact actual child export message kind required");
        JsonNode rows = root.get("exports");
        StrictJson.require(exportingRole != null && rows.isArray()
                        && rows.size() == exportingRole.exportedRoles().size(), "actual child export shape differs");
        ArrayList<Export> exports = new ArrayList<>(rows.size());
        for (JsonNode valueRow : rows) {
            ObjectNode row = StrictJson.object(valueRow, Set.of("role", "location"));
            JsonNode location = row.get("location");
            StrictJson.require(location.isIntegralNumber() && location.bigIntegerValue().signum() > 0,
                    "exact positive original remote location integer required");
            exports.add(new Export(ChildRole.parse(StrictJson.text(row.get("role"))),
                    new RemoteLocation(location.bigIntegerValue())));
        }
        return new Packet(exportingRole, exports);
    }

    /** Original insertion order, ASCII role strings, compact JSON, final LF and private 16 KiB budget. */
    public static byte[] encode(Packet value) {
        StrictJson.require(value != null, "actual child export values required");
        StringBuilder wire = new StringBuilder("{\"kind\":\"actual_child_exports\",\"exports\":[");
        boolean first = true;
        for (Export row : value.exports()) {
            if (!first) { wire.append(','); }
            first = false;
            String decimal = row.location().value().toString();
            StrictJson.require(decimal.length() <= PRIVATE_INTEGER_MAX_DECIMAL_DIGITS,
                    "original private JSON serialization integer digit profile exceeded");
            wire.append("{\"role\":\"").append(row.role().wire()).append("\",\"location\":")
                    .append(decimal).append('}');
        }
        byte[] raw = wire.append("]}\n").toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= PRIVATE_MESSAGE_MAX_BYTES, "private message exceeds bound");
        return raw;
    }

    public static ObjectNode toJson(Packet value) {
        StrictJson.require(value != null, "actual child export values required");
        ObjectNode root = StrictJson.object(); root.put("kind", KIND);
        ArrayNode rows = root.putArray("exports");
        for (Export row : value.exports()) {
            ObjectNode entry = rows.addObject(); entry.put("role", row.role().wire());
            entry.put("location", row.location().value());
        }
        return root;
    }

    /** Value projection after the original OS reader; this array is not an alternative private packet schema. */
    public static ProcessReadbacks parseReadbacks(ChildRole directRole, JsonNode value) {
        StrictJson.require(directRole != null && value != null && value.isArray()
                        && value.size() == directRole.exportedRoles().size() + 1, "complete original process-key array required");
        ArrayList<ProcessKey> processes = new ArrayList<>(value.size());
        for (JsonNode row : value) { processes.add(OriginReadbackCodec.parseProcessKey(row)); }
        return new ProcessReadbacks(directRole, processes);
    }
}

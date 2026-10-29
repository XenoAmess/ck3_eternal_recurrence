package org.xar.ck3.control.contracts.projection;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict metadata boundary for the fixed server manifest, separate from caller payload JSON. */
public final class ProjectionEvidenceCodec {
    public static final String SCHEMA = "xar.projection-evidence-grants/v1";
    public static final int MAX_BYTES = 1_048_576;
    public static final int MAX_GRANTS = 1024;
    private static final Set<String> TOP_FIELDS = Set.of("schema", "grants");
    private static final Set<String> GRANT_FIELDS = Set.of("role", "path", "bytes", "sha256", "origin_machine_id");
    public record WireGrant(String role, String path, long bytes, String sha256, String origin_machine_id) { }
    public static WireGrant wire(ProjectionEvidenceGrant grant) {
        return new WireGrant(grant.role().wire(), grant.path().toString(), grant.bytes(), grant.sha256(), grant.originMachineId());
    }
    private ProjectionEvidenceCodec() { }
    public static List<ProjectionEvidenceGrant> decode(byte[] raw) {
        JsonNode root = StrictJson.parse(raw, MAX_BYTES); exact(root, TOP_FIELDS);
        if (!SCHEMA.equals(text(root, "schema")) || !root.get("grants").isArray() || root.get("grants").size() > MAX_GRANTS) {
            throw new IllegalArgumentException("exact bounded projection evidence manifest required");
        }
        List<ProjectionEvidenceGrant> grants = new ArrayList<>();
        for (JsonNode row : root.get("grants")) {
            exact(row, GRANT_FIELDS); JsonNode bytes = row.get("bytes");
            if (!bytes.isIntegralNumber() || !bytes.canConvertToLong()) { throw new IllegalArgumentException("exact evidence byte count required"); }
            grants.add(new ProjectionEvidenceGrant(Path.of(text(row, "path")), bytes.longValue(), text(row, "sha256"),
                    text(row, "origin_machine_id"), ProjectionEvidenceRole.fromWire(text(row, "role"))));
        }
        return validated(grants);
    }
    public static byte[] encode(List<ProjectionEvidenceGrant> grants) {
        var root = StrictJson.object(); root.put("schema", SCHEMA); var rows = root.putArray("grants");
        for (ProjectionEvidenceGrant grant : validated(grants)) {
            WireGrant value = wire(grant); var row = rows.addObject(); row.put("role", value.role()); row.put("path", value.path());
            row.put("bytes", value.bytes()); row.put("sha256", value.sha256()); row.put("origin_machine_id", value.origin_machine_id());
        }
        return StrictJson.canonical(root, MAX_BYTES);
    }
    public static List<ProjectionEvidenceGrant> validated(List<ProjectionEvidenceGrant> grants) {
        List<ProjectionEvidenceGrant> snapshot = List.copyOf(grants);
        if (snapshot.size() > MAX_GRANTS) { throw new IllegalArgumentException("bounded evidence grant list required"); }
        record Identity(java.nio.file.Path path, ProjectionEvidenceRole role) { }
        Set<Identity> seen = new HashSet<>();
        for (ProjectionEvidenceGrant grant : snapshot) {
            if (!seen.add(new Identity(grant.path(), grant.role()))) { throw new IllegalArgumentException("duplicate evidence path and role"); }
        }
        return snapshot;
    }
    private static String text(JsonNode object, String field) {
        JsonNode value = object.get(field);
        if (value == null || !value.isTextual()) { throw new IllegalArgumentException("exact evidence text field required"); }
        return StrictJson.text(value);
    }
    private static void exact(JsonNode object, Set<String> expected) {
        if (object == null || !object.isObject()) { throw new IllegalArgumentException("evidence object required"); }
        Set<String> fields = new HashSet<>(); object.fieldNames().forEachRemaining(fields::add);
        if (!fields.equals(expected)) { throw new IllegalArgumentException("exact evidence fields required"); }
    }
}

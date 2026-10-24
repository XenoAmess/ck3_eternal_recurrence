package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Exact data binding for a packaged mechanical caller; changing an admitted window does not change code. */
public record SharedOwnedCommandBinding(
        String schema, String machineId, FileRef launcherSourceRef, FileRef standingRef, FileRef deliveryRef,
        Path nativeTemporaryRoot, Path privateTemporaryAggregateRoot,
        AuthorityExpectation standingExpectation, AuthorityExpectation deliveryExpectation) {
    public static final String SCHEMA = "xar.shared-owned-command-binding/v1";
    private static final Set<String> KEYS = Set.of("schema", "machine_id", "launcher_source_ref", "standing_ref", "delivery_ref",
            "native_temporary_root", "private_temporary_aggregate_root", "standing_expectation", "delivery_expectation");

    public record AuthorityExpectation(String schema, String status) {
        public AuthorityExpectation {
            if (schema == null || schema.isBlank() || status == null || !status.matches("[A-Z][A-Z0-9_]{0,127}"))
                throw new IllegalArgumentException("Exact nonempty authority schema and canonical status required");
        }
    }

    public SharedOwnedCommandBinding {
        if (!SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{0,127}")
                || launcherSourceRef == null || standingRef == null || deliveryRef == null
                || standingExpectation == null || deliveryExpectation == null)
            throw new IllegalArgumentException("Complete shared command binding required");
        nativeTemporaryRoot = absolute(nativeTemporaryRoot);
        privateTemporaryAggregateRoot = absolute(privateTemporaryAggregateRoot);
    }

    public static SharedOwnedCommandBinding read(FileRef exactRef) throws IOException {
        if (exactRef == null || exactRef.bytes() > 65536) throw new IOException("Binding must have an exact ref and at most64KiB");
        exactRef.verify();
        return parse(ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(exactRef.path()))));
    }

    /** JSON uses canonical path strings; it never delegates Path serialization to a provider-specific URI form. */
    public ObjectNode toJson() {
        var mapper=ControlBuild.strictMapper(); ObjectNode value=mapper.createObjectNode();
        value.put("schema",schema); value.put("machine_id",machineId);
        value.set("launcher_source_ref",mapper.valueToTree(launcherSourceRef));
        value.set("standing_ref",mapper.valueToTree(standingRef)); value.set("delivery_ref",mapper.valueToTree(deliveryRef));
        value.put("native_temporary_root",nativeTemporaryRoot.toString());
        value.put("private_temporary_aggregate_root",privateTemporaryAggregateRoot.toString());
        value.set("standing_expectation",mapper.valueToTree(standingExpectation));
        value.set("delivery_expectation",mapper.valueToTree(deliveryExpectation)); return value;
    }

    public static SharedOwnedCommandBinding parse(JsonNode value) throws IOException {
        keys(value, KEYS);
        try {
            return new SharedOwnedCommandBinding(text(value, "schema"), text(value, "machine_id"),
                    ref(field(value, "launcher_source_ref")), ref(field(value, "standing_ref")), ref(field(value, "delivery_ref")),
                    absolute(Path.of(text(value, "native_temporary_root"))),
                    absolute(Path.of(text(value, "private_temporary_aggregate_root"))),
                    expectation(field(value, "standing_expectation")), expectation(field(value, "delivery_expectation")));
        } catch (IllegalArgumentException error) {
            throw new IOException("Invalid shared command binding", error);
        }
    }

    static void verifyAuthority(JsonNode value, AuthorityExpectation expected, String machineId) throws IOException {
        if (!text(value, "schema").equals(expected.schema()) || !text(value, "status").equals(expected.status())
                || !text(value, "machine_id").equals(machineId)) throw new IOException("Authority schema/status/machine mismatch");
    }

    private static AuthorityExpectation expectation(JsonNode value) throws IOException {
        keys(value, Set.of("schema", "status"));
        return new AuthorityExpectation(text(value, "schema"), text(value, "status"));
    }
    private static FileRef ref(JsonNode value) throws IOException {
        keys(value, Set.of("path", "bytes", "sha256"));
        JsonNode bytes = field(value, "bytes");
        if (!bytes.isIntegralNumber() || !bytes.canConvertToLong()) throw new IOException("Exact integer FileRef bytes required");
        try {
            return new FileRef(absolute(Path.of(text(value, "path"))).toString(), bytes.longValue(), text(value, "sha256"));
        } catch (IllegalArgumentException error) {
            throw new IOException("Invalid exact FileRef", error);
        }
    }
    private static Path absolute(Path value) {
        if (value == null || !value.isAbsolute()) throw new IllegalArgumentException("Absolute binding path required");
        return value.toAbsolutePath().normalize();
    }
    private static JsonNode field(JsonNode value, String name) throws IOException {
        if (value == null || !value.isObject() || !value.has(name)) throw new IOException("Missing binding field: " + name);
        return value.get(name);
    }
    private static String text(JsonNode value, String name) throws IOException {
        JsonNode item = field(value, name);
        if (!item.isTextual()) throw new IOException("Binding string required: " + name);
        return item.textValue();
    }
    private static void keys(JsonNode value, Set<String> expected) throws IOException {
        if (value == null || !value.isObject() || value.size() != expected.size()) throw new IOException("Exact binding fields required");
        for (var item : value.properties()) if (!expected.contains(item.getKey())) throw new IOException("Unknown binding field: " + item.getKey());
    }
}

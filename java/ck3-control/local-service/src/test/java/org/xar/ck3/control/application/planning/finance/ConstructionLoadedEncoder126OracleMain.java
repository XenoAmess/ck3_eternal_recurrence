package org.xar.ck3.control.application.planning.finance;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Finite, manual DATA oracle. No SDK factory, Loaded, writer, archive, permission,
 * mapper configuration mutation, custom serializer, Game or Native operation.
 * Equality is restricted to the current frozen defaults and parser-owned trees.
 */
public final class ConstructionLoadedEncoder126OracleMain {
    private static final int FULL = FullJsonTree.MAXIMUM_BYTES;
    private static final int METADATA_LIMIT = 4 * 1024 * 1024;
    private static final JsonNodeFactory N = JsonNodeFactory.instance;
    private static final Path FIXED_DATA = Path.of(
            "D:/ck3-state/resume91-native-integration/p114-consumer-data02/shared-cas");
    private static final String[] FILES = {"input-q1.json", "input-q2.json", "input-small.json"};
    private static final long[] LENGTHS = {6_831_978L, 6_832_024L, 28_318L};
    private static final String[] SHAS = {
        "fe413956e14af2487bbec3b900e7ef6f08e653fc405ad5b71466eaa9e2cb9cdd",
        "a5a09c41abe1a73a358e986f241774f4cb3b9a19d85e2b70f7678a71237661be",
        "942dd2dab275c620bc6267182b1f1c139a8d7c6498dd8414654e5892fb938b9c"
    };

    private final ObjectNode report = N.objectNode();
    private final ArrayNode rows = N.arrayNode();
    private Path output;
    private boolean outputCreated;
    private long metadataWritten;
    private int passed;

    private ConstructionLoadedEncoder126OracleMain() { }

    public static void main(String[] args) throws Throwable {
        long began = System.nanoTime();
        new ConstructionLoadedEncoder126OracleMain().execute(args, began);
    }

    private void execute(String[] args, long began) throws Throwable {
        Throwable primary = null;
        report.put("schema", "ck3.p126.loaded-encoder-finite-oracle.v1");
        report.put("boundary", "Existing FullJsonTree / DriverJson / RawJson.fullMaterial DATA only; no Loaded admission, production optimization or performance conclusion");
        report.put("configuration", "Existing frozen defaults; no configuration access or mutation and no custom JsonNode/serializer");
        report.put("input_source", "Three immutable DATA02 files and fixed literal raw query cases; no PREP or new capture");
        report.put("metadata_limit_bytes", METADATA_LIMIT);
        report.put("expected_case_count", 24);
        report.put("main_clock_boundary", "main_ns_before_output excludes final result serialization; terminal stdout records main_ns_after_result_output and Native actor retains the complete process window");
        report.set("cases", rows);
        try {
            check(args.length == 2, "arguments: fixed DATA02 directory, absent exclusive metadata directory");
            Path data = Path.of(args[0]).toRealPath();
            check(data.equals(FIXED_DATA.toRealPath()), "only the pinned DATA02 input root is allowed");
            output = Path.of(args[1]).toAbsolutePath().normalize();
            check(!output.startsWith(data), "metadata must be outside the immutable DATA root");
            check(!Files.exists(output), "exclusive metadata directory must be absent");
            Files.createDirectory(output);
            outputCreated = true;
            report.put("data_root", data.toString());
            report.put("exclusive_metadata_root", output.toString());
            for (int index = 0; index < FILES.length; index++) {
                runData(data, index);
            }

            positive("literal_order_null_empty",
                    "{\"z\":null,\"a\":[],\"m\":{},\"empty\":\"\",\"opaque\":{\"second\":2,\"first\":1}}");
            positive("literal_integer_negative_zero",
                    "{\"opaque\":{\"negative_integer_zero\":-0,\"zero\":0,\"negative\":-17,\"large\":1234567890123456789012345678901234567890}}");
            positive("literal_decimal_tokens",
                    "{\"opaque\":{\"negative_decimal_zero\":-0.0,\"fixed\":1.00,\"exponent\":1e+0,\"leading_exponent\":1e+"
                            + "0".repeat(512) + "}}");
            positive("literal_long_big_integer",
                    "{\"opaque\":{\"integer\":" + "1" + "7".repeat(5_000) + "}}");
            positive("literal_control_and_escaping",
                    "{\"opaque\":{\"text\":\"quote\\\" backslash\\\\ slash/ controls\\b\\f\\n\\r\\t\\u0000\\u001f\","
                            + "\"key\\\"\\\\\\u0001\":\"value\"}}");
            String emoji = new String(Character.toChars(0x1F600));
            String separator = Character.toString(0x2028);
            positive("literal_unicode_and_escape_spelling",
                    "{\"opaque\":{\"literal\":\"" + emoji + separator + "\",\"escaped\":\"\\ud83d\\ude00\\u2028\","
                            + "\"bmp\":\"\\u00e9\",\"slash\":\"\\/\"}}");
            positive("literal_empty_and_long_opaque_keys",
                    "{\"\":null,\"" + "k".repeat(32_769) + "\":\"" + "v".repeat(40_000) + "\"}");
            positive("depth63_empty_container_accept", nestedArrays(62, "{}"));
            positive("depth63_nonempty_container_accept", nestedArrays(62, "{\"leaf\":0}"));
            positive("depth64_scalar_accept", nestedArrays(63, "0"));

            rawCase("depth64_empty_container_reject", utf8(nestedArrays(63, "{}")), false, false, true);
            rawCase("depth64_nonempty_container_reject", utf8(nestedArrays(63, "{\"leaf\":0}")), false, false, true);
            rawCase("depth65_scalar_reject", utf8(nestedArrays(64, "0")), false, false, true);
            rawCase("duplicate_member_reject", utf8("{\"a\":1,\"a\":2}"), false, false, false);
            rawCase("escaped_duplicate_member_reject", utf8("{\"a\":1,\"\\u0061\":2}"), false, false, false);
            rawCase("trailing_document_reject", utf8("{\"a\":1} {\"b\":2}"), false, false, false);
            rawCase("lone_high_surrogate_value_physical_reject", utf8("{\"a\":\"\\ud800\"}"), true, true, false);
            rawCase("lone_low_surrogate_value_physical_reject", utf8("{\"a\":\"\\udc00\"}"), true, true, false);
            rawCase("lone_surrogate_key_physical_reject", utf8("{\"\\ud800\":1}"), true, true, false);
            rawCase("malformed_utf8_reject", new byte[] {
                '{', '"', 'a', '"', ':', '"', (byte) 0xC3, 0x28, '"', '}'
            }, false, false, false);
            rawCase("empty_document_reject", new byte[0], false, false, false);

            ArrayNode rechecked = report.putArray("pinned_input_rechecks");
            for (int index = 0; index < FILES.length; index++) {
                Path file = data.resolve(FILES[index]);
                byte[] current = readPinned(file, LENGTHS[index], SHAS[index]);
                ObjectNode row = rechecked.addObject();
                row.put("path", file.toString());
                describe(row, "input", current);
            }
            check(rows.size() == 24 && passed == 24, "all fixed 24 cases must complete");
            report.put("pinned_inputs_unchanged", true);
            report.put("all_expected_outcomes", true);
            report.put("finite_oracle_only", true);
        } catch (Throwable failure) {
            primary = failure;
            report.put("all_expected_outcomes", false);
            report.set("failure", failure(failure));
        } finally {
            report.put("completed_case_count", rows.size());
            report.put("passed_case_count", passed);
            report.put("main_ns_before_output", System.nanoTime() - began);
            report.put("metadata_bytes_before_final", metadataWritten);
            try {
                if (outputCreated) {
                    write("ORACLE-RESULT.json", report);
                }
            } catch (Throwable outputFailure) {
                if (primary == null) primary = outputFailure;
                else primary.addSuppressed(outputFailure);
            }
        }
        System.out.println("P126 terminal status=" + (primary == null ? "passed" : "failed")
                + " cases=" + passed + " main_ns_after_result_output=" + (System.nanoTime() - began)
                + " metadata_bytes=" + metadataWritten + " root=" + output);
        if (primary != null) throw primary;
    }

    private void runData(Path data, int index) throws Throwable {
        ObjectNode row = start("data_" + FILES[index].replace(".json", "").replace('-', '_'), "full_outer_two_independent_parses");
        Path file = data.resolve(FILES[index]);
        row.put("input_path", file.toString());
        row.put("pinned_input_bytes", LENGTHS[index]);
        row.put("pinned_input_sha256", SHAS[index]);
        Throwable primary = null;
        long began = System.nanoTime();
        try {
            byte[] raw = readPinned(file, LENGTHS[index], SHAS[index]);
            describe(row, "input", raw);
            JsonNode full = FullJsonTree.parse(raw, FULL);
            JsonNode query = full.get("quoted_outlay").get("query_observation");
            check(query != null && query.isObject(), "DATA full query object required");
            // Separate parse of the same pinned full input, not conversion of the first tree.
            OpportunityJson.Obj model = DriverJson.object(raw, FULL);
            OpportunityJson.Obj modelQuery = OpportunityJson.object(
                    OpportunityJson.object(model.get("quoted_outlay"), "DATA quoted outlay").get("query_observation"),
                    "DATA query");
            byte[] first = FullJsonTree.encode(query, FULL);
            byte[] second = DriverJson.encode(modelQuery);
            describe(row, "full_tree_encoded_query", first);
            describe(row, "driver_encoded_query", second);
            row.put("encoded_query_bytes_equal", Arrays.equals(first, second));
            row.put("full_tree_accepted", true);
            row.put("driver_accepted", true);
            RawJson physical = RawJson.fullMaterial(raw);
            row.put("raw_full_material_accepted", true);
            check(physical.contentEquals(raw), "physical full material must retain exact input");
            check(Arrays.equals(first, second), "independent DATA full query encodings differ");
            row.put("raw_equality_not_claimed", true);
            passed++;
            row.put("passed", true);
        } catch (Throwable error) {
            primary = error;
            row.put("passed", false);
            row.set("failure", failure(error));
        } finally {
            row.put("case_ns", System.nanoTime() - began);
            finish(row, primary);
        }
    }

    private void positive(String id, String literalJson) throws Throwable {
        rawCase(id, utf8(literalJson), true, true, true);
    }

    private void rawCase(String id, byte[] raw, boolean expectTree, boolean expectDriver, boolean expectPhysical) throws Throwable {
        ObjectNode row = start(id, "literal_raw_query");
        row.put("wire_origin", "Raw literal UTF-8 or explicit byte vector; never tree-encoded before either parser");
        describe(row, "input", raw);
        if (raw.length <= 1_024) row.put("literal_wire_base64", java.util.Base64.getEncoder().encodeToString(raw));
        row.put("expected_full_tree_accepted", expectTree);
        row.put("expected_driver_accepted", expectDriver);
        row.put("expected_raw_full_material_accepted", expectPhysical);
        Throwable primary = null;
        long began = System.nanoTime();
        try {
            JsonNode tree = null;
            OpportunityJson.Obj driver = null;
            boolean treeAccepted;
            boolean driverAccepted;
            boolean physicalAccepted;
            try {
                tree = FullJsonTree.parse(raw, FULL);
                treeAccepted = true;
            } catch (IllegalArgumentException rejected) {
                treeAccepted = false;
                row.set("full_tree_rejection", failure(rejected));
            }
            row.put("full_tree_accepted", treeAccepted);
            try {
                driver = DriverJson.object(raw, FULL);
                driverAccepted = true;
            } catch (IllegalArgumentException rejected) {
                driverAccepted = false;
                row.set("driver_rejection", failure(rejected));
            }
            row.put("driver_accepted", driverAccepted);
            RawJson physical = null;
            try {
                physical = RawJson.fullMaterial(raw);
                physicalAccepted = true;
            } catch (IllegalArgumentException rejected) {
                physicalAccepted = false;
                row.set("raw_full_material_rejection", failure(rejected));
            }
            if (physical != null) check(physical.contentEquals(raw), "RawJson full must retain exact literal input");
            row.put("raw_full_material_accepted", physicalAccepted);
            if (treeAccepted && driverAccepted) {
                byte[] first = FullJsonTree.encode(tree, FULL);
                byte[] second = DriverJson.encode(driver);
                describe(row, "full_tree_encoded_query", first);
                describe(row, "driver_encoded_query", second);
                row.put("encoded_query_bytes_equal", Arrays.equals(first, second));
                check(Arrays.equals(first, second), "literal query encodings differ: " + id);
            }
            check(treeAccepted == expectTree, "FullJsonTree outcome differs: " + id);
            check(driverAccepted == expectDriver, "DriverJson outcome differs: " + id);
            check(physicalAccepted == expectPhysical, "RawJson physical outcome differs: " + id);
            row.put("no_loaded_or_command_admission", true);
            row.put("passed", true);
            passed++;
        } catch (Throwable error) {
            primary = error;
            row.put("passed", false);
            row.set("failure", failure(error));
        } finally {
            row.put("case_ns", System.nanoTime() - began);
            finish(row, primary);
        }
    }

    private ObjectNode start(String id, String kind) {
        ObjectNode row = N.objectNode();
        row.put("case_id", id);
        row.put("case_kind", kind);
        rows.add(row);
        return row;
    }

    private void finish(ObjectNode row, Throwable primary) throws Throwable {
        try {
            write(String.format("CASE-%02d-%s.json", rows.size(), row.get("case_id").textValue()), row);
        } catch (Throwable outputFailure) {
            if (primary == null) primary = outputFailure;
            else primary.addSuppressed(outputFailure);
        }
        if (primary != null) throw primary;
    }

    private void write(String name, JsonNode value) throws IOException {
        byte[] bytes = FullJsonTree.encode(value, METADATA_LIMIT);
        check(metadataWritten + bytes.length <= METADATA_LIMIT, "cumulative metadata exceeds 4MiB");
        Files.write(output.resolve(name), bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        metadataWritten += bytes.length;
    }

    private static byte[] readPinned(Path file, long length, String sha) throws IOException {
        check(Files.isRegularFile(file) && Files.size(file) == length, "pinned input length differs: " + file);
        byte[] raw = Files.readAllBytes(file);
        check(raw.length == length && sha256(raw).equals(sha), "pinned input SHA differs: " + file);
        return raw;
    }

    private static String nestedArrays(int count, String leaf) {
        return "{\"v\":" + "[".repeat(count) + leaf + "]".repeat(count) + "}";
    }

    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }

    private static void describe(ObjectNode row, String prefix, byte[] raw) {
        row.put(prefix + "_bytes", raw.length);
        row.put(prefix + "_sha256", sha256(raw));
    }

    private static String sha256(byte[] raw) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new IllegalStateException(impossible);
        }
    }

    private static ObjectNode failure(Throwable error) {
        ObjectNode out = N.objectNode();
        out.put("type", error.getClass().getName());
        String text = String.valueOf(error.getMessage());
        out.put("message", text.length() <= 4_096 ? text : text.substring(0, 4_096));
        ArrayNode causes = out.putArray("causes");
        Throwable next = error.getCause();
        for (int count = 0; next != null && count < 8; count++) {
            ObjectNode item = causes.addObject();
            item.put("type", next.getClass().getName());
            String message = String.valueOf(next.getMessage());
            item.put("message", message.length() <= 4_096 ? message : message.substring(0, 4_096));
            next = next.getCause();
        }
        return out;
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}

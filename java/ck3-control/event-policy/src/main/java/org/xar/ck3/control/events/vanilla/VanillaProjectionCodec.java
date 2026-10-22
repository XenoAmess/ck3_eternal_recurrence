package org.xar.ck3.control.events.vanilla;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.OptionContract;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.RegistryBinding;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.RegistryState;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.RenderedOption;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.Request;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.Result;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.SourceAnchor;

/** Strict, bounded wire adapter. The wire is an explicit projection, not the full native context. */
public final class VanillaProjectionCodec {
    public static final String REQUEST_SCHEMA = "xar.ck3.vanilla-option-projection-request";
    public static final String RESULT_SCHEMA = "xar.ck3.vanilla-option-projection-result";
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
        .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
    private static final Set<String> OPTION_FIELDS = Set.of("rendered_index", "native_option_index", "shown", "enabled", "fallback", "cancel");
    private VanillaProjectionCodec() { }

    public static Request decode(byte[] bytes) {
        JsonNode node = read(bytes);
        fields(node, Set.of("schema", "schema_version", "binding", "contract", "options", "snapshot_option_count"));
        if (!REQUEST_SCHEMA.equals(text(node, "schema")) || integer(node, "schema_version") != 1) {
            throw invalid("unsupported request schema");
        }
        RegistryBinding binding = binding(required(node, "binding"));
        JsonNode rawContract = required(node, "contract");
        OptionContract contract = rawContract.isNull() ? null : contract(rawContract);
        List<RenderedOption> options = new ArrayList<>();
        for (JsonNode row : array(required(node, "options"))) options.add(option(row));
        return new Request(binding, contract, options, integer(node, "snapshot_option_count"));
    }

    public static byte[] encode(Request request) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("schema", REQUEST_SCHEMA).put("schema_version", 1);
        node.set("binding", bindingNode(request.binding()));
        if (request.contract() == null) node.putNull("contract");
        else node.set("contract", contractNode(request.contract()));
        ArrayNode options = node.putArray("options");
        request.options().forEach(row -> options.add(optionNode(row)));
        node.put("snapshot_option_count", request.snapshotOptionCount());
        return write(node);
    }

    public static byte[] encode(Result result) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("schema", RESULT_SCHEMA).put("schema_version", 1);
        node.put("status", switch (result.status()) {
            case PROJECTION_READY -> "projection_ready";
            case BLOCKED -> "blocked";
            case NOT_REGISTERED -> "not_registered";
        });
        node.set("binding", bindingNode(result.binding()));
        ObjectNode checks = node.putObject("checks");
        result.checks().forEach((name, value) -> checks.put(name, value.booleanValue()));
        if (result.selectedOption() == null) node.putNull("selected_option");
        else node.set("selected_option", optionNode(result.selectedOption()));
        ArrayNode failed = node.putArray("failed_checks");
        result.failedChecks().forEach(failed::add);
        node.put("action_authorized", false).put("semantic_decision_ready", false);
        return write(node);
    }

    private static RegistryBinding binding(JsonNode node) {
        fields(node, Set.of("event_definition_key", "ck3_build", "ck3_exe_sha256", "registry_state", "source_anchors"));
        RegistryState state = switch (text(node, "registry_state")) {
            case "available" -> RegistryState.AVAILABLE;
            case "source_analyzed_no_occurrence_contract" -> RegistryState.SOURCE_ANALYZED_NO_OCCURRENCE_CONTRACT;
            case "not_registered" -> RegistryState.NOT_REGISTERED;
            default -> throw invalid("unknown registry state");
        };
        List<SourceAnchor> anchors = new ArrayList<>();
        for (JsonNode row : array(required(node, "source_anchors"))) {
            fields(row, Set.of("relative_path", "registry_sha256", "indexed_sha256"));
            anchors.add(new SourceAnchor(text(row, "relative_path"), text(row, "registry_sha256"), text(row, "indexed_sha256")));
        }
        return new RegistryBinding(text(node, "event_definition_key"), text(node, "ck3_build"), text(node, "ck3_exe_sha256"), state, anchors);
    }

    private static OptionContract contract(JsonNode node) {
        fields(node, Set.of("option_count", "native_option_indices", "selected_native_option_index", "selected_option_number",
            "disabled_native_option_indices", "snapshot_option_counts"));
        return new OptionContract(integer(node, "option_count"), integers(required(node, "native_option_indices")),
            integer(node, "selected_native_option_index"), integer(node, "selected_option_number"),
            integers(required(node, "disabled_native_option_indices")), integers(required(node, "snapshot_option_counts")));
    }

    private static RenderedOption option(JsonNode node) {
        fields(node, OPTION_FIELDS);
        return new RenderedOption(integer(node, "rendered_index"), integer(node, "native_option_index"), bool(node, "shown"),
            bool(node, "enabled"), bool(node, "fallback"), bool(node, "cancel"));
    }

    private static ObjectNode bindingNode(RegistryBinding binding) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("event_definition_key", binding.eventDefinitionKey()).put("ck3_build", binding.ck3Build())
            .put("ck3_exe_sha256", binding.ck3ExeSha256()).put("registry_state", switch (binding.registryState()) {
                case AVAILABLE -> "available";
                case SOURCE_ANALYZED_NO_OCCURRENCE_CONTRACT -> "source_analyzed_no_occurrence_contract";
                case NOT_REGISTERED -> "not_registered";
            });
        ArrayNode sources = node.putArray("source_anchors");
        binding.sourceAnchors().forEach(row -> sources.addObject().put("relative_path", row.relativePath())
            .put("registry_sha256", row.registrySha256()).put("indexed_sha256", row.indexedSha256()));
        return node;
    }

    private static ObjectNode contractNode(OptionContract contract) {
        ObjectNode node = MAPPER.createObjectNode();
        node.put("option_count", contract.optionCount()).put("selected_native_option_index", contract.selectedNativeOptionIndex())
            .put("selected_option_number", contract.selectedOptionNumber());
        ArrayNode nativeIndices = node.putArray("native_option_indices");
        contract.nativeOptionIndices().forEach(nativeIndices::add);
        ArrayNode disabled = node.putArray("disabled_native_option_indices");
        contract.disabledNativeOptionIndices().forEach(disabled::add);
        ArrayNode counts = node.putArray("snapshot_option_counts");
        contract.snapshotOptionCounts().forEach(counts::add);
        return node;
    }

    private static ObjectNode optionNode(RenderedOption row) {
        return MAPPER.createObjectNode().put("rendered_index", row.renderedIndex()).put("native_option_index", row.nativeOptionIndex())
            .put("shown", row.shown()).put("enabled", row.enabled()).put("fallback", row.fallback()).put("cancel", row.cancel());
    }

    private static JsonNode read(byte[] bytes) {
        if (bytes == null || bytes.length == 0 || bytes.length > 65_536) throw invalid("request size outside domain");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            try (JsonParser parser = MAPPER.createParser(utf8)) {
                JsonNode node = MAPPER.readTree(parser);
                if (node == null || parser.nextToken() != null) throw invalid("multiple or missing JSON values");
                return node;
            }
        } catch (CharacterCodingException error) {
            throw new IllegalArgumentException("invalid UTF-8", error);
        } catch (IOException error) {
            throw new IllegalArgumentException("invalid JSON", error);
        }
    }
    private static byte[] write(JsonNode node) {
        try { return MAPPER.writeValueAsBytes(node); }
        catch (IOException error) { throw new IllegalStateException("cannot serialize validated projection", error); }
    }
    private static void fields(JsonNode node, Set<String> expected) {
        if (!node.isObject()) throw invalid("expected object");
        Set<String> actual = new HashSet<>();
        node.fieldNames().forEachRemaining(actual::add);
        if (!actual.equals(expected)) throw invalid("missing or unknown fields");
    }
    private static JsonNode required(JsonNode node, String name) {
        JsonNode value = node.get(name);
        if (value == null) throw invalid("missing field: " + name);
        return value;
    }
    private static String text(JsonNode node, String name) {
        JsonNode value = required(node, name);
        if (!value.isTextual()) throw invalid("expected string: " + name);
        return value.textValue();
    }
    private static int integer(JsonNode node, String name) { return integer(required(node, name)); }
    private static int integer(JsonNode value) {
        if (!value.isIntegralNumber() || !value.canConvertToInt()) throw invalid("expected bounded integer token");
        return value.intValue();
    }
    private static boolean bool(JsonNode node, String name) {
        JsonNode value = required(node, name);
        if (!value.isBoolean()) throw invalid("expected boolean: " + name);
        return value.booleanValue();
    }
    private static List<JsonNode> array(JsonNode node) {
        if (!node.isArray() || node.size() > 32) throw invalid("expected bounded array");
        List<JsonNode> rows = new ArrayList<>();
        node.forEach(rows::add);
        return rows;
    }
    private static List<Integer> integers(JsonNode node) {
        return array(node).stream().map(VanillaProjectionCodec::integer).toList();
    }
    private static IllegalArgumentException invalid(String message) { return new IllegalArgumentException(message); }
}

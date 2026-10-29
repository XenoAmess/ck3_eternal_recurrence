package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

/** Strict JSON-schema boundary for the actual original producer's vocabulary. Unknown keywords fail registration. */
final class McpSchema {
    private static final Set<String> KEYWORDS = Set.of("$schema", "$id", "$ref", "$defs", "type", "title", "description",
            "default", "examples", "deprecated", "readOnly", "writeOnly", "properties", "required", "additionalProperties",
            "anyOf", "allOf", "oneOf", "not", "enum", "const", "items", "minItems", "maxItems", "uniqueItems",
            "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minLength", "maxLength", "pattern");
    private static final Set<String> TYPES = Set.of("null", "object", "array", "string", "integer", "number", "boolean");
    private McpSchema() { }

    static void supported(JsonNode schema) { inspect(schema, 0); }
    private static void inspect(JsonNode schema, int depth) {
        McpJson.require(depth < 100, "schema nesting exceeds finite bound");
        if (schema.isBoolean()) return;
        var row = McpJson.object(schema);
        row.fieldNames().forEachRemaining(key -> McpJson.require(KEYWORDS.contains(key), "unsupported schema keyword: " + key));
        if (row.has("type")) {
            JsonNode type = row.get("type");
            if (type.isArray()) for (JsonNode value : type) McpJson.require(TYPES.contains(McpJson.text(value)), "unknown schema type");
            else McpJson.require(TYPES.contains(McpJson.text(type)), "unknown schema type");
        }
        for (String field : Set.of("properties", "$defs")) if (row.has(field)) {
            var children = McpJson.object(row.get(field)); children.elements().forEachRemaining(child -> inspect(child, depth + 1));
        }
        for (String field : Set.of("items", "additionalProperties", "not")) if (row.has(field)) inspect(row.get(field), depth + 1);
        for (String field : Set.of("allOf", "anyOf", "oneOf")) if (row.has(field)) {
            McpJson.require(row.get(field).isArray() && !row.get(field).isEmpty(), "nonempty schema alternatives required");
            for (JsonNode child : row.get(field)) inspect(child, depth + 1);
        }
        if (row.has("required")) { McpJson.require(row.get("required").isArray(), "required must be an array");
            for (JsonNode name : row.get("required")) McpJson.text(name); }
        if (row.has("enum")) McpJson.require(row.get("enum").isArray() && !row.get("enum").isEmpty(), "nonempty enum required");
        for (String field : Set.of("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"))
            if (row.has(field)) McpJson.require(row.get(field).isNumber(), "numeric schema constraint required");
        for (String field : Set.of("minLength", "maxLength", "minItems", "maxItems")) if (row.has(field)) limit(row.get(field));
        if (row.has("pattern")) Pattern.compile(McpJson.text(row.get("pattern")));
        if (row.has("$ref")) McpJson.require(McpJson.text(row.get("$ref")).startsWith("#/$defs/"), "only local $defs references admitted");
    }

    static void validate(JsonNode schema, JsonNode value) {
        McpJson.require(value != null, "schema value must distinguish missing from null");
        check(schema, value, schema, 0);
    }
    private static void check(JsonNode schema, JsonNode value, JsonNode root, int depth) {
        McpJson.require(depth < 100, "schema validation nesting exceeds finite bound");
        if (schema.isBoolean()) { McpJson.require(schema.booleanValue(), "value rejected by false schema"); return; }
        var row = McpJson.object(schema);
        if (row.has("$ref")) {
            JsonNode target = root.at(McpJson.text(row.get("$ref")).substring(1));
            McpJson.require(!target.isMissingNode(), "missing local schema definition"); check(target, value, root, depth + 1);
        }
        if (row.has("type")) {
            JsonNode type = row.get("type"); boolean matches = false;
            if (type.isArray()) { for (JsonNode item : type) matches |= type(McpJson.text(item), value); }
            else matches = type(McpJson.text(type), value);
            McpJson.require(matches, "JSON type differs from declared schema");
        }
        if (row.has("const")) McpJson.require(equal(row.get("const"), value), "value differs from schema const");
        if (row.has("enum")) {
            boolean found = false; for (JsonNode item : row.get("enum")) found |= equal(item, value);
            McpJson.require(found, "value outside declared enum");
        }
        for (String choice : Set.of("anyOf", "oneOf", "allOf")) if (row.has(choice)) {
            int matched = 0; for (JsonNode alternative : row.get(choice)) if (accepts(alternative, value, root, depth + 1)) matched++;
            McpJson.require(choice.equals("allOf") ? matched == row.get(choice).size() : choice.equals("oneOf") ? matched == 1 : matched > 0,
                    "value fails schema alternatives");
        }
        if (row.has("not")) McpJson.require(!accepts(row.get("not"), value, root, depth + 1), "value matches prohibited schema");
        if (value.isObject()) {
            if (row.has("required")) for (JsonNode name : row.get("required"))
                McpJson.require(value.has(McpJson.text(name)), "required argument is missing");
            var names = value.fieldNames();
            while (names.hasNext()) {
                String name = names.next(); JsonNode declared = row.path("properties").get(name);
                if (declared != null) check(declared, value.get(name), root, depth + 1);
                else if (row.has("additionalProperties")) check(row.get("additionalProperties"), value.get(name), root, depth + 1);
            }
        }
        if (value.isArray()) {
            boundSize(row, value.size(), "minItems", "maxItems");
            if (row.has("items")) for (JsonNode item : value) check(row.get("items"), item, root, depth + 1);
            if (row.path("uniqueItems").asBoolean(false)) {
                Set<JsonNode> seen = new HashSet<>(); for (JsonNode item : value) McpJson.require(seen.add(item), "array values must be unique");
            }
        }
        if (value.isTextual()) {
            String text = value.textValue(); boundSize(row, text.codePointCount(0, text.length()), "minLength", "maxLength");
            if (row.has("pattern")) McpJson.require(Pattern.compile(McpJson.text(row.get("pattern"))).matcher(text).find(), "string fails schema pattern");
        }
        if (value.isNumber()) {
            BigDecimal number = value.decimalValue();
            if (row.has("minimum")) McpJson.require(number.compareTo(row.get("minimum").decimalValue()) >= 0, "number below minimum");
            if (row.has("maximum")) McpJson.require(number.compareTo(row.get("maximum").decimalValue()) <= 0, "number above maximum");
            if (row.has("exclusiveMinimum")) McpJson.require(number.compareTo(row.get("exclusiveMinimum").decimalValue()) > 0, "number below exclusive minimum");
            if (row.has("exclusiveMaximum")) McpJson.require(number.compareTo(row.get("exclusiveMaximum").decimalValue()) < 0, "number above exclusive maximum");
            if (row.has("multipleOf")) { BigDecimal unit = row.get("multipleOf").decimalValue();
                McpJson.require(unit.signum() > 0 && number.remainder(unit).signum() == 0, "number fails multipleOf"); }
        }
    }
    private static boolean accepts(JsonNode schema, JsonNode value, JsonNode root, int depth) {
        try { check(schema, value, root, depth); return true; } catch (IllegalArgumentException invalid) { return false; }
    }
    private static boolean type(String name, JsonNode value) {
        return switch (name) {
            case "null" -> value.isNull(); case "object" -> value.isObject(); case "array" -> value.isArray();
            case "string" -> value.isTextual(); case "integer" -> value.isIntegralNumber();
            case "number" -> value.isNumber(); case "boolean" -> value.isBoolean(); default -> false;
        };
    }
    private static boolean equal(JsonNode first, JsonNode second) {
        return first.isNumber() && second.isNumber() ? first.decimalValue().compareTo(second.decimalValue()) == 0 : first.equals(second);
    }
    private static int limit(JsonNode value) {
        McpJson.require(value.isIntegralNumber() && value.canConvertToInt() && value.intValue() >= 0, "nonnegative bounded schema limit required");
        return value.intValue();
    }
    private static void boundSize(JsonNode schema, int size, String minimum, String maximum) {
        if (schema.has(minimum)) McpJson.require(size >= limit(schema.get(minimum)), "value below minimum size");
        if (schema.has(maximum)) McpJson.require(size <= limit(schema.get(maximum)), "value above maximum size");
    }
}

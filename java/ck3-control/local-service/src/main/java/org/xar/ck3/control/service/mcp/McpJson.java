package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.math.BigInteger;

/** Narrow JSON boundary. Exact argument/result tokens never travel through double, aliases, or an object map. */
final class McpJson {
    static final int BODY_MAX = 64 * 1024 * 1024;
    static final int INPUT_MAX = BODY_MAX + 64 * 1024;
    static final int OUTPUT_MAX = 7 * BODY_MAX + 64 * 1024;
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(OUTPUT_MAX).maxNumberLength(4300).maxNestingDepth(1000).build()).build();
    private static final ObjectMapper JSON = new ObjectMapper(FACTORY).enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
            DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final JsonFactory RESULT_FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(OUTPUT_MAX).maxNumberLength(BODY_MAX).maxNestingDepth(1000).build()).build();
    private static final ObjectMapper RESULT_JSON = new ObjectMapper(RESULT_FACTORY).enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
            DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS, DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private McpJson() { }
    static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    static JsonNode parse(byte[] raw) { return parse(raw,JSON); }
    /** Output DATA only: the 64 MiB business material lease does not enlarge request/native tokens. */
    static JsonNode parseResult(byte[] raw) { return parse(raw,RESULT_JSON); }
    private static JsonNode parse(byte[] raw,ObjectMapper mapper) {
        require(raw != null && raw.length > 0 && raw.length <= OUTPUT_MAX, "bounded MCP JSON required");
        require(!(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "MCP BOM rejected");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = mapper.readTree(text); require(node != null, "MCP JSON value required"); unicode(node); return node;
        } catch (IOException failure) { throw new IllegalArgumentException("invalid UTF-8/duplicate/trailing MCP JSON", failure); }
    }
    static ObjectNode object(JsonNode node) { require(node instanceof ObjectNode, "MCP object required"); return (ObjectNode) node; }
    static String text(JsonNode node) { require(node != null && node.isTextual(), "MCP string required"); return node.textValue(); }
    static void fields(ObjectNode node, Set<String> allowed, Set<String> required) {
        Set<String> actual = new HashSet<>(); node.fieldNames().forEachRemaining(actual::add);
        require(allowed.containsAll(actual) && actual.containsAll(required), "wrong or missing MCP fields");
    }
    static byte[] encode(JsonNode node) {
        try { return JSON.writeValueAsBytes(node); }
        catch (IOException failure) { throw new IllegalArgumentException("MCP JSON encoding failed", failure); }
    }
    static ObjectNode object() { return JSON.createObjectNode(); }
    static byte[] quote(String text) { return encode(JSON.getNodeFactory().textNode(text)); }
    static byte[] token(byte[] raw, String field) { return token(raw,field,FACTORY); }
    static byte[] tokenResult(byte[] raw,String field) { return token(raw,field,RESULT_FACTORY); }
    private static byte[] token(byte[] raw,String field,JsonFactory factory) {
        try (JsonParser parser = factory.createParser(raw)) {
            require(parser.nextToken() == JsonToken.START_OBJECT, "source object required");
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String name = parser.currentName(); parser.nextToken();
                int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset()); parser.skipChildren(); parser.finishToken();
                int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                if (field.equals(name)) return Arrays.copyOfRange(raw, start, end);
            }
        } catch (IOException failure) { throw new IllegalArgumentException("MCP token extraction failed", failure); }
        throw new IllegalArgumentException("required original MCP token absent: " + field);
    }
    static byte[] member(byte[] raw, String name, byte[] replacement) { return member(raw,name,replacement,false); }
    static byte[] memberResult(byte[] raw,String name,byte[] replacement) { return member(raw,name,replacement,true); }
    private static byte[] member(byte[] raw,String name,byte[] replacement,boolean result) {
        ObjectNode object = object(result?parseResult(raw):parse(raw));
        ByteArrayOutputStream out = new ByteArrayOutputStream(); out.write('{'); boolean first = true;
        for (var iterator = object.fieldNames(); iterator.hasNext();) {
            String field = iterator.next(); if (field.equals(name)) continue;
            if (!first) out.write(','); first = false;
            out.writeBytes(quote(field)); out.write(':'); out.writeBytes(result?tokenResult(raw,field):token(raw, field));
        }
        if (!first) out.write(','); out.writeBytes(quote(name)); out.write(':'); out.writeBytes(replacement); out.write('}');
        return bounded(out.toByteArray());
    }
    static byte[] without(byte[] raw, Set<String> excluded) { return without(raw,excluded,false); }
    static byte[] withoutResult(byte[] raw,Set<String> excluded) { return without(raw,excluded,true); }
    private static byte[] without(byte[] raw,Set<String> excluded,boolean result) {
        ObjectNode row = object(result?parseResult(raw):parse(raw)); ByteArrayOutputStream out = new ByteArrayOutputStream(); out.write('{'); boolean first = true;
        for (var fields = row.fieldNames(); fields.hasNext();) {
            String field = fields.next(); if (excluded.contains(field)) continue;
            if (!first) out.write(','); first = false; out.writeBytes(quote(field)); out.write(':'); out.writeBytes(result?tokenResult(raw,field):token(raw, field));
        }
        out.write('}'); return bounded(out.toByteArray());
    }
    /** Mirrors pydantic_core.to_json(indent=2) used by the original MCPServer result/resource producers. */
    static String pretty(JsonNode node) {
        StringBuilder text = new StringBuilder(); pretty(node, text, 0); return text.toString();
    }
    /** Existing validated business tokens, including -0.0 and exponent spelling, survive the text representation. */
    static String prettyOriginal(byte[] original) {
        parseResult(original);StringBuilder text=new StringBuilder();
        try(JsonParser parser=RESULT_FACTORY.createParser(original)) {
            require(parser.nextToken()!=null,"original business value required");prettyOriginal(parser,text,0);
            require(parser.nextToken()==null,"one original business value required");return text.toString();
        }catch(IOException failure){throw new IllegalArgumentException("original MCP token formatting failed",failure);}
    }
    private static void prettyOriginal(JsonParser parser,StringBuilder text,int depth)throws IOException {
        JsonToken kind=parser.currentToken();
        if(kind==JsonToken.START_OBJECT||kind==JsonToken.START_ARRAY) {
            boolean object=kind==JsonToken.START_OBJECT;JsonToken end=object?JsonToken.END_OBJECT:JsonToken.END_ARRAY;
            text.append(object?'{':'[');boolean first=true;
            while(parser.nextToken()!=end) {
                require(parser.currentToken()!=null,"complete original business container required");
                if(first)text.append('\n');else text.append(",\n");first=false;text.append("  ".repeat(depth+1));
                if(object){require(parser.currentToken()==JsonToken.FIELD_NAME,"original object field required");
                    text.append(new String(quote(parser.currentName()),StandardCharsets.UTF_8)).append(": ");parser.nextToken();}
                prettyOriginal(parser,text,depth+1);
            }
            if(!first)text.append('\n').append("  ".repeat(depth));text.append(object?'}':']');return;
        }
        if(kind==JsonToken.VALUE_STRING)text.append(new String(quote(parser.getText()),StandardCharsets.UTF_8));
        else {require(kind==JsonToken.VALUE_NUMBER_INT||kind==JsonToken.VALUE_NUMBER_FLOAT||kind==JsonToken.VALUE_TRUE||kind==JsonToken.VALUE_FALSE||kind==JsonToken.VALUE_NULL,"original scalar JSON required");text.append(parser.getText());}
    }
    private static void pretty(JsonNode node, StringBuilder text, int depth) {
        if (!node.isContainerNode()) { text.append(new String(encode(node), StandardCharsets.UTF_8)); return; }
        boolean object = node.isObject(); text.append(object ? '{' : '[');
        if (!node.isEmpty()) {
            text.append('\n'); boolean first = true;
            if (object) {
                for (var fields = node.fieldNames(); fields.hasNext();) {
                    String field = fields.next(); if (!first) text.append(",\n"); first = false;
                    text.append("  ".repeat(depth + 1)).append(new String(quote(field), StandardCharsets.UTF_8)).append(": ");
                    pretty(node.get(field), text, depth + 1);
                }
            } else for (JsonNode value : node) {
                if (!first) text.append(",\n"); first = false; text.append("  ".repeat(depth + 1)); pretty(value, text, depth + 1);
            }
            text.append('\n').append("  ".repeat(depth));
        }
        text.append(object ? '}' : ']');
    }
    static byte[] join(byte[]... parts) {
        long length = 0; for (byte[] part : parts) length = Math.addExact(length, part.length);
        require(length > 0 && length <= OUTPUT_MAX, "MCP full envelope exceeds finite limit");
        byte[] result = new byte[Math.toIntExact(length)]; int at = 0;
        for (byte[] part : parts) { System.arraycopy(part, 0, result, at, part.length); at += part.length; }
        return result;
    }
    static byte[] bounded(byte[] raw) { require(raw.length > 0 && raw.length <= OUTPUT_MAX, "MCP full envelope exceeds finite limit"); return raw; }
    static void validateResult(byte[] original) {
        ObjectNode row = object(parseResult(original));
        publicNumbers(row);
        fields(row, Set.of("_meta", "content", "structuredContent", "isError", "resultType", "ttlMs", "cacheScope"), Set.of("content"));
        require(row.get("content").isArray(), "complete MCP content array required");
        for (JsonNode block : row.get("content")) {
            ObjectNode content = object(block); String type = text(content.get("type"));
            require(Set.of("text", "image", "audio", "resource_link", "resource").contains(type), "known MCP content type required");
            if (type.equals("text")) text(content.get("text"));
            if (type.equals("image") || type.equals("audio")) { text(content.get("data")); text(content.get("mimeType")); }
            if (type.equals("resource_link")) { text(content.get("uri")); text(content.get("name")); }
            if (type.equals("resource")) resourceContents(content.get("resource"));
            if (content.hasNonNull("annotations")) object(content.get("annotations"));
            if (content.hasNonNull("_meta")) object(content.get("_meta"));
        }
        if (row.has("isError")) require(row.get("isError").isBoolean(), "MCP isError must be boolean");
        if (row.has("resultType")) require("complete".equals(text(row.get("resultType"))), "non-complete gameplay result must not be treated as complete");
        if (row.hasNonNull("_meta")) object(row.get("_meta"));
        if (row.has("ttlMs")) require(row.get("ttlMs").isIntegralNumber() && row.get("ttlMs").bigIntegerValue().signum() >= 0, "exact nonnegative ttlMs required");
        if (row.has("cacheScope")) require(Set.of("private", "public").contains(text(row.get("cacheScope"))), "known cache scope required");
    }
    static void resourceUri(String uri) { require(Set.of("ck3://capabilities", "ck3://state/current").contains(uri), "only the two original source-bound resource URIs are admitted"); }
    static void resourceContents(JsonNode node) {
        ObjectNode row = object(node); text(row.get("uri"));
        require(row.has("text") != row.has("blob"), "resource content requires exactly one text/blob body");
        text(row.get(row.has("text") ? "text" : "blob"));
        if (row.hasNonNull("mimeType")) text(row.get("mimeType"));
        if (row.hasNonNull("_meta")) object(row.get("_meta"));
    }
    /** Public numeric interfaces must be JS-safe. Typed domain codecs serialize full-width identities as decimal strings. */
    static void publicNumbers(JsonNode node) {
        if (node.isIntegralNumber()) require(node.bigIntegerValue().abs().compareTo(BigInteger.valueOf(9_007_199_254_740_991L)) <= 0,
                "unsafe public integer; typed full-width identity/time serializer must produce a canonical decimal string");
        if (node.isFloatingPointNumber()) require(Double.isFinite(node.doubleValue()), "public floating value exceeds finite numeric range");
        if (node.isContainerNode()) for (JsonNode child : node) publicNumbers(child);
    }
    static void toolName(String name) {
        require(name != null && !name.isBlank() && name.length() <= 256, "bounded MCP tool name required");
        require(!name.equals("ck3_plan_nonwar_turn") && !name.equals("ck3_auto_nonwar_turn"), "retired nonwar public route cannot register or dispatch");
    }
    private static void unicode(JsonNode node) {
        if (node.isTextual()) unicode(node.textValue());
        if (node.isObject()) node.fieldNames().forEachRemaining(McpJson::unicode);
        if (node.isContainerNode()) for (JsonNode child : node) unicode(child);
    }
    private static void unicode(String value) {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) require(index + 1 < value.length() && Character.isLowSurrogate(value.charAt(++index)), "unpaired MCP surrogate");
            else require(!Character.isLowSurrogate(current), "unpaired MCP surrogate");
        }
    }
    static void require(boolean valid, String message) { if (!valid) throw new IllegalArgumentException(message); }
}

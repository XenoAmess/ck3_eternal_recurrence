package org.xar.ck3.save;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.CoercionAction;
import com.fasterxml.jackson.databind.cfg.CoercionInputShape;
import com.fasterxml.jackson.databind.type.LogicalType;
import java.io.IOException;

/** One strict JSON boundary for the new shared contract; v2 hosts retain their existing codecs. */
public final class SaveJson {
    private static final ObjectMapper JSON = mapper();
    private SaveJson() { }
    private static ObjectMapper mapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
        mapper.enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES,
                DeserializationFeature.FAIL_ON_MISSING_CREATOR_PROPERTIES, DeserializationFeature.FAIL_ON_NULL_CREATOR_PROPERTIES,
                DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.FAIL_ON_NUMBERS_FOR_ENUMS);
        mapper.disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT);
        for (LogicalType type : new LogicalType[]{LogicalType.Integer, LogicalType.Boolean, LogicalType.Textual}) {
            for (CoercionInputShape shape : new CoercionInputShape[]{CoercionInputShape.String, CoercionInputShape.Integer, CoercionInputShape.Float, CoercionInputShape.Boolean, CoercionInputShape.EmptyString}) {
                boolean same = type == LogicalType.Integer && shape == CoercionInputShape.Integer
                        || type == LogicalType.Boolean && shape == CoercionInputShape.Boolean || type == LogicalType.Textual && shape == CoercionInputShape.String;
                if (!same) mapper.coercionConfigFor(type).setCoercion(shape, CoercionAction.Fail);
            }
        }
        return mapper;
    }
    public static <T> T read(byte[] bytes, Class<T> type) throws IOException {
        JsonNode node = JSON.readTree(bytes);
        if (node == null || !node.isObject()) throw new IOException("JSON object required");
        return JSON.treeToValue(node, type);
    }
    public static byte[] write(Object value) throws IOException { return JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(value); }
}

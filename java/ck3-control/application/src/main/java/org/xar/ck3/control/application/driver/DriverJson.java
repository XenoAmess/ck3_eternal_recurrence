package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Full native/Driver boundary; the proposal parser's 128 KiB budget is not a full-frame budget. */
public final class DriverJson {
    public static final int MAX_NATIVE_BYTES = 64 * 1024 * 1024;
    private static final JsonFactory JSON = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxStringLength(FullJsonTree.MAXIMUM_DRIVER_BYTES).maxNumberLength(FullJsonTree.MAXIMUM_DRIVER_BYTES).build()).build();
    private DriverJson() { }

    /** Full-frame typed tree interop; it does not borrow StrictJson's smaller receipt-size parameter lane. */
    public static JsonNode toNode(OpportunityJson.Value value) { return toNode(value,MAX_NATIVE_BYTES); }
    /** Explicit full-material lane; each caller retains its narrower domain budget. */
    public static JsonNode toNode(OpportunityJson.Value value,int maximumBytes) {
        StrictJson.require(maximumBytes>=1 && maximumBytes<=FullJsonTree.MAXIMUM_DRIVER_BYTES,"explicit full tree budget required");
        StrictJson.require(encode(value).length<=maximumBytes,"bounded native tree required");
        return node(value,0);
    }
    /** Already-normalized semantic tree interop; never invokes a native normalizer. */
    public static JsonNode toNormalizedNode(OpportunityJson.Value value) { return toNode(value); }
    public static OpportunityJson.Value fromNode(JsonNode value) {
        OpportunityJson.Value result=model(value,0);
        StrictJson.require(encode(result).length<=MAX_NATIVE_BYTES,"bounded normalized native tree required");
        return result;
    }
    /** Derived semantic floats were produced by the sole native normalizer, not by parsing an integer identity. */
    public static OpportunityJson.Value fromNormalizedNode(JsonNode value) {
        OpportunityJson.Value result=normalizedModel(value,0);
        StrictJson.require(encode(result).length<=MAX_NATIVE_BYTES,"bounded normalized native tree required");
        return result;
    }
    private static OpportunityJson.Value normalizedModel(JsonNode value,int depth) {
        StrictJson.require(value!=null && depth<=64,"bounded normalized JSON node required");
        if(value.isObject()) {
            Map<String,OpportunityJson.Value> fields=new LinkedHashMap<>();
            value.properties().forEach(entry->fields.put(entry.getKey(),normalizedModel(entry.getValue(),depth+1)));
            return new OpportunityJson.Obj(fields);
        }
        if(value.isArray()) {List<OpportunityJson.Value> rows=new ArrayList<>();value.forEach(item->rows.add(normalizedModel(item,depth+1)));return new OpportunityJson.Arr(rows);}
        if(value.isFloatingPointNumber() && (value.isDouble() || value.isFloat())) {
            double number=value.doubleValue();StrictJson.require(Double.isFinite(number),"finite normalized float required");
            return new OpportunityJson.DecimalValue(Double.toString(number));
        }
        return model(value,depth);
    }
    public static byte[] encodeNode(JsonNode value) { return encode(fromNode(value)); }
    private static JsonNode node(OpportunityJson.Value value,int depth) {
        StrictJson.require(value!=null && depth<=64,"bounded typed native tree required");
        var factory=JsonNodeFactory.instance;
        return switch(value) {
            case OpportunityJson.Obj object -> {var result=factory.objectNode();object.members().forEach((key,item)->result.set(key,node(item,depth+1)));yield result;}
            case OpportunityJson.Arr array -> {var result=factory.arrayNode();array.items().forEach(item->result.add(node(item,depth+1)));yield result;}
            case OpportunityJson.Text text -> factory.textNode(text.value());
            case OpportunityJson.IntegerValue integer -> factory.numberNode(integer.value());
            case OpportunityJson.DecimalValue decimal -> new DecimalTokenNode(decimal.token());
            case OpportunityJson.Bool bool -> factory.booleanNode(bool.value());
            case OpportunityJson.Nil ignored -> factory.nullNode();
        };
    }
    private static OpportunityJson.Value model(JsonNode value,int depth) {
        StrictJson.require(value!=null && depth<=64,"bounded original native JSON node required");
        if(value.isObject()) {
            Map<String,OpportunityJson.Value> fields=new LinkedHashMap<>();
            value.properties().forEach(entry->fields.put(entry.getKey(),model(entry.getValue(),depth+1)));
            return new OpportunityJson.Obj(fields);
        }
        if(value.isArray()) {List<OpportunityJson.Value> rows=new ArrayList<>();value.forEach(item->rows.add(model(item,depth+1)));return new OpportunityJson.Arr(rows);}
        if(value.isTextual())return new OpportunityJson.Text(value.textValue());
        if(value.isIntegralNumber())return new OpportunityJson.IntegerValue(value.bigIntegerValue());
        if(value.isFloatingPointNumber()) {
            StrictJson.require(!value.isDouble() && !value.isFloat(),"native decimal interop must retain exact BigDecimal tokens");
            return new OpportunityJson.DecimalValue(value instanceof DecimalTokenNode token ? token.originalToken() : value.asText());
        }
        if(value.isBoolean())return new OpportunityJson.Bool(value.booleanValue());
        if(value.isNull())return OpportunityJson.Nil.INSTANCE;
        throw new IllegalArgumentException("unsupported original native JSON node type");
    }

    public static OpportunityJson.Obj object(byte[] raw, int maximumBytes) {
        // The lower parser owns UTF-8, duplicate, token, depth and explicit material-budget validation.
        return OpportunityJson.object(model(FullJsonTree.parse(raw,maximumBytes),0), "full JSON");
    }
    public static DriverStateSnapshot.Slot slot(OpportunityJson.Obj object, String field) {
        if (!object.members().containsKey(field)) return new DriverStateSnapshot.Missing();
        return object.get(field) == OpportunityJson.Nil.INSTANCE ? new DriverStateSnapshot.NullValue()
                : new DriverStateSnapshot.Value(encode(object.get(field)));
    }
    public static byte[] encode(OpportunityJson.Value value) {
        try {
            ByteArrayOutputStream output=new ByteArrayOutputStream();
            try(JsonGenerator generator=JSON.createGenerator(output)) { write(generator,value,0); }
            byte[] raw=output.toByteArray();
            StrictJson.require(raw.length<=268435456,"bounded full Driver JSON required");
            return raw;
        } catch(IOException failure) { throw new IllegalArgumentException("full JSON encoding failed",failure); }
    }
    /** Legacy character-generator wire: keeps original non-BMP UTF-8 and numeric tokens. */
    public static byte[] encodeCharacters(OpportunityJson.Value value) {
        requireCharacters(value,0);
        try {
            var output=new java.io.StringWriter();
            try(JsonGenerator generator=JSON.createGenerator(output)) { write(generator,value,0); }
            var encoder=java.nio.charset.StandardCharsets.UTF_8.newEncoder()
                    .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
                    .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT);
            var bytes=encoder.encode(java.nio.CharBuffer.wrap(output.toString()));
            StrictJson.require(bytes.remaining()<=268435456,"bounded full character JSON required");
            byte[] raw=new byte[bytes.remaining()];bytes.get(raw);return raw;
        } catch(IOException failure) { throw new IllegalArgumentException("full character JSON encoding failed",failure); }
    }
    private static void requireCharacters(OpportunityJson.Value value,int depth) {
        StrictJson.require(depth<=64,"bounded full character JSON depth");
        switch(value) {
            case OpportunityJson.Text text -> requireUnicode(text.value());
            case OpportunityJson.Obj object -> { for(var entry:object.members().entrySet()){requireUnicode(entry.getKey());requireCharacters(entry.getValue(),depth+1);} }
            case OpportunityJson.Arr array -> { for(var item:array.items())requireCharacters(item,depth+1); }
            default -> { }
        }
    }
    private static void requireUnicode(String text) {
        for(int index=0;index<text.length();index++) {
            char current=text.charAt(index);
            if(Character.isHighSurrogate(current)) {
                StrictJson.require(index+1<text.length()&&Character.isLowSurrogate(text.charAt(index+1)),"unpaired JSON high surrogate");index++;
            }else StrictJson.require(!Character.isLowSurrogate(current),"unpaired JSON low surrogate");
        }
    }
    private static void write(JsonGenerator out,OpportunityJson.Value value,int depth) throws IOException {
        StrictJson.require(depth<=64,"bounded full JSON depth");
        switch(value) {
            case OpportunityJson.Obj row -> { out.writeStartObject(); for(var field:row.members().entrySet()) { out.writeFieldName(field.getKey());write(out,field.getValue(),depth+1); }out.writeEndObject(); }
            case OpportunityJson.Arr rows -> { out.writeStartArray();for(var row:rows.items())write(out,row,depth+1);out.writeEndArray(); }
            case OpportunityJson.Text text -> out.writeString(text.value());
            case OpportunityJson.IntegerValue number -> out.writeNumber(number.value());
            case OpportunityJson.DecimalValue number -> out.writeNumber(number.token());
            case OpportunityJson.Bool bool -> out.writeBoolean(bool.value());
            case OpportunityJson.Nil ignored -> out.writeNull();
        }
    }
    public static boolean same(DriverStateSnapshot.Slot first, DriverStateSnapshot.Slot second) {
        if (first instanceof DriverStateSnapshot.Value a && second instanceof DriverStateSnapshot.Value b) {
            return java.util.Arrays.equals(a.json(), b.json());
        }
        return first.equals(second);
    }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

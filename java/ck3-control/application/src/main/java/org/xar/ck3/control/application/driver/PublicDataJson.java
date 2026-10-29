package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.math.BigDecimal;
import java.util.Objects;
import java.util.TreeSet;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Typed public DATA bridge over the existing full Driver/RawJson lane, never the small Map JSON lane. */
public final class PublicDataJson {
    private PublicDataJson() { }

    public static ObjectNode object(RawJson actual) {
        var semantic = DriverJson.object(actual.bytes(), RawJson.MAXIMUM_BYTES);
        return (ObjectNode) OpportunityJson.toNode(semantic);
    }

    /** Sorted object keys; JSON integer/decimal/string categories remain exact. No Java object maps cross this boundary. */
    public static RawJson encode(JsonNode value) {
        RawJson result = new RawJson(DriverJson.encode(domain(value, 0)));
        // The existing real Driver parser retains its own finite depth/number limits.
        // RawJson additionally enforces the existing UTF-8/surrogate and full-token rules.
        return result;
    }

    /** Explicit complete node DATA; callers retain their source-owned role checks. */
    public static RawJson encodeFullMaterial(JsonNode value) {
        return RawJson.fullMaterial(DriverJson.encode(domain(value, 0)));
    }

    /** Deterministic typed DATA encoding without a JsonNode/double conversion.
     * Decimal tokens, including negative zero and arbitrarily scaled finite JSON tokens,
     * remain exact. Arrays retain their original order; object keys retain the existing Java natural ordering. */
    public static RawJson encodeTyped(OpportunityJson.Value value) {
        return new RawJson(encodeTypedBytes(value, RawJson.MAXIMUM_BYTES));
    }

    /** Explicit complete Driver/auxiliary DATA only; Native/public protocol encoding retains its original number bound. */
    public static RawJson encodeFullMaterial(OpportunityJson.Value value) {
        return RawJson.fullMaterial(encodeTypedBytes(value, RawJson.MAXIMUM_BYTES));
    }

    /** Explicit material lease for callers whose already-existing typed wire exceeds RawJson's 64 MiB lane.
     * This does not enlarge RawJson or the small StrictJson parser; all consumers retain their own limits. */
    public static byte[] encodeTypedBytes(OpportunityJson.Value value, int maximumBytes) {
        StrictJson.require(maximumBytes > 0 && maximumBytes <= 268435456, "explicit bounded typed JSON material lease required");
        byte[] encoded = DriverJson.encodeCharacters(sorted(Objects.requireNonNull(value), 0));
        StrictJson.require(encoded.length <= maximumBytes, "typed JSON exceeds its explicit material lease");
        return encoded;
    }

    private static OpportunityJson.Value sorted(OpportunityJson.Value value, int depth) {
        StrictJson.require(value != null && depth <= 64, "bounded typed public DATA required");
        if (value instanceof OpportunityJson.Obj object) {
            var names = new TreeSet<>(object.members().keySet());
            var fields = new LinkedHashMap<String, OpportunityJson.Value>();
            for (String name : names) fields.put(name, sorted(object.get(name), depth + 1));
            return new OpportunityJson.Obj(fields);
        }
        if (value instanceof OpportunityJson.Arr array) {
            var rows = new ArrayList<OpportunityJson.Value>();
            for (var row : array.items()) rows.add(sorted(row, depth + 1));
            return new OpportunityJson.Arr(rows);
        }
        return value;
    }

    /** Retain the validated source's decimal tokens, including category and negative zero, across a DATA projection.
     * Integer identity transformations remain the caller's explicit contract. No decimal is converted to double. */
    public static RawJson encodePreservingDecimals(JsonNode projected,RawJson original) {
        Objects.requireNonNull(original);
        var source=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        return new RawJson(DriverJson.encode(preserveDecimals(source,domain(projected,0),"")));
    }
    /** The same decimal-preserving projection over an explicitly complete Driver DATA material. */
    public static RawJson encodePreservingFullMaterial(JsonNode projected,RawJson original) {
        Objects.requireNonNull(original);
        var source=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        return RawJson.fullMaterial(DriverJson.encode(preserveDecimals(source,domain(projected,0),"")));
    }
    private static OpportunityJson.Value preserveDecimals(OpportunityJson.Value original,OpportunityJson.Value projected,String path) {
        if(original instanceof OpportunityJson.DecimalValue decimal) {
            StrictJson.require(projected instanceof OpportunityJson.DecimalValue,"original decimal category changed at "+path);
            var after=(OpportunityJson.DecimalValue)projected;
            StrictJson.require(new BigDecimal(decimal.token()).compareTo(new BigDecimal(after.token()))==0,
                    "original decimal value changed at "+path);
            return decimal;
        }
        if(original instanceof OpportunityJson.Obj before&&projected instanceof OpportunityJson.Obj after) {
            var fields=new LinkedHashMap<String,OpportunityJson.Value>();
            for(var entry:after.members().entrySet())fields.put(entry.getKey(),preserveDecimals(before.get(entry.getKey()),entry.getValue(),path+"/"+entry.getKey()));
            for(var entry:before.members().entrySet())if(!after.members().containsKey(entry.getKey()))
                requireNoDecimal(entry.getValue(),path+"/"+entry.getKey());
            return new OpportunityJson.Obj(fields);
        }
        if(original instanceof OpportunityJson.Arr before&&projected instanceof OpportunityJson.Arr after) {
            var rows=new ArrayList<OpportunityJson.Value>();
            for(int index=0;index<after.items().size();index++)rows.add(preserveDecimals(index<before.items().size()?before.items().get(index):null,after.items().get(index),path+"/"+index));
            for(int index=after.items().size();index<before.items().size();index++)requireNoDecimal(before.items().get(index),path+"/"+index);
            return new OpportunityJson.Arr(rows);
        }
        requireNoDecimal(original,path);return projected;
    }
    private static void requireNoDecimal(OpportunityJson.Value value,String path) {
        StrictJson.require(!(value instanceof OpportunityJson.DecimalValue),"original decimal removed at "+path);
        if(value instanceof OpportunityJson.Obj object)for(var entry:object.members().entrySet())requireNoDecimal(entry.getValue(),path+"/"+entry.getKey());
        else if(value instanceof OpportunityJson.Arr array)for(int index=0;index<array.items().size();index++)requireNoDecimal(array.items().get(index),path+"/"+index);
    }

    private static OpportunityJson.Value domain(JsonNode value, int depth) {
        StrictJson.require(value != null && depth <= 64, "bounded complete public DATA node required");
        if (value.isObject()) {
            var names = new TreeSet<String>(); value.fieldNames().forEachRemaining(names::add);
            var fields = new LinkedHashMap<String, OpportunityJson.Value>();
            for (String name : names) fields.put(name, domain(value.get(name), depth + 1));
            return new OpportunityJson.Obj(fields);
        }
        if (value.isArray()) {
            var rows = new ArrayList<OpportunityJson.Value>();
            for (JsonNode row : value) rows.add(domain(row, depth + 1));
            return new OpportunityJson.Arr(rows);
        }
        if (value.isTextual()) return new OpportunityJson.Text(value.textValue());
        if (value.isIntegralNumber()) return new OpportunityJson.IntegerValue(value.bigIntegerValue());
        if (value.isFloatingPointNumber()) {
            StrictJson.require(Double.isFinite(value.doubleValue()), "finite original public decimal required");
            return new OpportunityJson.DecimalValue(value.toString());
        }
        if (value.isBoolean()) return new OpportunityJson.Bool(value.booleanValue());
        StrictJson.require(value.isNull(), "unsupported public DATA JSON node"); return OpportunityJson.Nil.INSTANCE;
    }
}

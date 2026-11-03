package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.math.BigDecimal;
import java.util.Objects;
import java.util.TreeSet;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Typed public DATA bridge over the existing full Driver/RawJson lane, never the small Map JSON lane. */
public final class PublicDataJson {
    private PublicDataJson() { }

    public static ObjectNode object(RawJson actual) {
        var parsed = FullJsonTree.parse(actual.bytes(), RawJson.MAXIMUM_BYTES);
        if (!(parsed instanceof ObjectNode result)) {
            throw new IllegalArgumentException("full JSON must be an object");
        }
        return result;
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
            java.util.Iterator<?> originalNames = object.members().keySet().iterator();
            boolean unchanged = names.size() == object.members().size();
            for (String name : names) {
                var original = object.get(name);
                var child = sorted(original, depth + 1);
                fields.put(name, child);
                unchanged &= name.equals(originalNames.next()) && child == original;
            }
            // Reuse only after the original sort and complete recursive checks.
            return unchanged ? object : new OpportunityJson.Obj(fields);
        }
        if (value instanceof OpportunityJson.Arr array) {
            var rows = new ArrayList<OpportunityJson.Value>();
            boolean unchanged = true;
            for (var row : array.items()) {
                var child = sorted(row, depth + 1);
                rows.add(child);
                unchanged &= child == row;
            }
            return unchanged ? array : new OpportunityJson.Arr(rows);
        }
        return value;
    }

    /** Retain the validated source's decimal tokens, including category and negative zero, across a DATA projection.
     * Integer identity transformations remain the caller's explicit contract. No decimal is converted to double. */
    public static RawJson encodePreservingDecimals(JsonNode projected,RawJson original) {
        Objects.requireNonNull(original);
        var source=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        return new RawJson(DriverJson.encode(preserveDecimals(source,domain(projected,0),new String[65],new int[65],0)));
    }
    /** The same decimal-preserving projection over an explicitly complete Driver DATA material. */
    public static RawJson encodePreservingFullMaterial(JsonNode projected,RawJson original) {
        Objects.requireNonNull(original);
        var source=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        return RawJson.fullMaterial(DriverJson.encode(preserveDecimals(source,domain(projected,0),new String[65],new int[65],0)));
    }
    private static OpportunityJson.Value preserveDecimals(OpportunityJson.Value original,OpportunityJson.Value projected,String[] names,int[] indexes,int depth) {
        if(original instanceof OpportunityJson.DecimalValue decimal) {
            boolean category=projected instanceof OpportunityJson.DecimalValue;
            StrictJson.require(category,category?null:"original decimal category changed at "+diagnosticPath(names,indexes,depth));
            var after=(OpportunityJson.DecimalValue)projected;
            var originalValue=new BigDecimal(decimal.token());
            boolean equal=originalValue.compareTo(
                    decimal.token().equals(after.token()) ? originalValue : new BigDecimal(after.token()))==0;
            StrictJson.require(equal,equal?null:"original decimal value changed at "+diagnosticPath(names,indexes,depth));
            return decimal;
        }
        if(original instanceof OpportunityJson.Obj before&&projected instanceof OpportunityJson.Obj after) {
            var fields=new LinkedHashMap<String,OpportunityJson.Value>();
            boolean unchanged=true;
            for(var entry:after.members().entrySet()) {
                var child=preserveDecimals(before.get(entry.getKey()),entry.getValue(),names,indexes,objectPath(names,depth,entry.getKey()));
                fields.put(entry.getKey(),child);
                unchanged &= child==entry.getValue();
            }
            for(var entry:before.members().entrySet())if(!after.members().containsKey(entry.getKey()))
                requireNoDecimal(entry.getValue(),names,indexes,objectPath(names,depth,entry.getKey()));
            return unchanged ? after : new OpportunityJson.Obj(fields);
        }
        if(original instanceof OpportunityJson.Arr before&&projected instanceof OpportunityJson.Arr after) {
            var rows=new ArrayList<OpportunityJson.Value>();
            boolean unchanged=true;
            for(int index=0;index<after.items().size();index++) {
                var child=preserveDecimals(index<before.items().size()?before.items().get(index):null,after.items().get(index),names,indexes,arrayPath(names,indexes,depth,index));
                rows.add(child);
                unchanged &= child==after.items().get(index);
            }
            for(int index=after.items().size();index<before.items().size();index++)requireNoDecimal(before.items().get(index),names,indexes,arrayPath(names,indexes,depth,index));
            return unchanged ? after : new OpportunityJson.Arr(rows);
        }
        requireNoDecimal(original,names,indexes,depth);return projected;
    }
    private static void requireNoDecimal(OpportunityJson.Value value,String[] names,int[] indexes,int depth) {
        boolean noDecimal=!(value instanceof OpportunityJson.DecimalValue);
        StrictJson.require(noDecimal,noDecimal?null:"original decimal removed at "+diagnosticPath(names,indexes,depth));
        if(value instanceof OpportunityJson.Obj object)for(var entry:object.members().entrySet())requireNoDecimal(entry.getValue(),names,indexes,objectPath(names,depth,entry.getKey()));
        else if(value instanceof OpportunityJson.Arr array)for(int index=0;index<array.items().size();index++)requireNoDecimal(array.items().get(index),names,indexes,arrayPath(names,indexes,depth,index));
    }
    private static int objectPath(String[] names,int depth,String name) {
        names[depth]=name;return depth+1;
    }
    private static int arrayPath(String[] names,int[] indexes,int depth,int index) {
        names[depth]=null;indexes[depth]=index;return depth+1;
    }
    private static String diagnosticPath(String[] names,int[] indexes,int depth) {
        String path="";
        for(int index=0;index<depth;index++)path=names[index]==null?path+"/"+indexes[index]:path+"/"+names[index];
        return path;
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

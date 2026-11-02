package org.xar.ck3.control.service.root;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.LinkedHashMap;
import java.util.Map;
import java.math.BigInteger;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.DecimalValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Actual private pure helper versus the original public encode/hash expression.
 * No Root/current/writer/issuer permission; depth/null failures test first-encode validity.
 * The giant byte limit is source-order evidence only, not a192MiB-JVM allocation test or speed claim.
 */
public final class PlanningAuxiliary316Test {
    private static boolean invokeSameAuxiliary(Obj first, Obj second) throws Exception {
        Method method = RootPlanningInputsFactory.class.getDeclaredMethod("sameAuxiliary", Obj.class, Obj.class);
        method.setAccessible(true);
        try {
            return (Boolean) method.invoke(null, first, second);
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof Exception original) throw original;
            if (cause instanceof Error original) throw original;
            throw new AssertionError("unexpected throwable", cause);
        }
    }

    private static boolean oracle(Obj first, Obj second) {
        return DriverJson.sha256(DriverJson.encode(first)).equals(DriverJson.sha256(DriverJson.encode(second)));
    }

    @Test
    void finiteCompatibility() throws Exception {
        // Same reference
        Map<String, OpportunityJson.Value> nested = new LinkedHashMap<>();
        nested.put("inner", new Obj(new LinkedHashMap<>()));
        Obj valid = new Obj(nested);
        assertTrue(invokeSameAuxiliary(valid, valid));
        assertTrue(oracle(valid, valid));

        // Distinct equal encoded roots
        Map<String, OpportunityJson.Value> nestedCopy = new LinkedHashMap<>();
        nestedCopy.put("inner", new Obj(new LinkedHashMap<>()));
        Obj distinctEqual = new Obj(nestedCopy);
        assertTrue(invokeSameAuxiliary(valid, distinctEqual));
        assertTrue(oracle(valid, distinctEqual));

        // Changed payload
        Map<String, OpportunityJson.Value> changed = new LinkedHashMap<>();
        changed.put("inner", new Obj(new LinkedHashMap<>()));
        changed.put("extra", new Text("changed"));
        Obj changedObj = new Obj(changed);
        assertFalse(invokeSameAuxiliary(valid, changedObj));
        assertFalse(oracle(valid, changedObj));

        // Different insertion order
        Map<String, OpportunityJson.Value> order1 = new LinkedHashMap<>();
        order1.put("a", new Obj(new LinkedHashMap<>()));
        order1.put("b", new Obj(new LinkedHashMap<>()));
        Map<String, OpportunityJson.Value> order2 = new LinkedHashMap<>();
        order2.put("b", new Obj(new LinkedHashMap<>()));
        order2.put("a", new Obj(new LinkedHashMap<>()));
        Obj obj1 = new Obj(order1);
        Obj obj2 = new Obj(order2);
        assertFalse(invokeSameAuxiliary(obj1, obj2));
        assertFalse(oracle(obj1, obj2));

        // Exact decimal tokens
        Map<String, OpportunityJson.Value> dec1 = new LinkedHashMap<>();
        dec1.put("v", new DecimalValue("1.0"));
        Map<String, OpportunityJson.Value> dec2 = new LinkedHashMap<>();
        dec2.put("v", new DecimalValue("1.00"));
        assertFalse(invokeSameAuxiliary(new Obj(dec1), new Obj(dec2)));
        assertFalse(oracle(new Obj(dec1), new Obj(dec2)));

        // Signed zero
        Map<String, OpportunityJson.Value> neg1 = new LinkedHashMap<>();
        neg1.put("v", new DecimalValue("-0.0"));
        Map<String, OpportunityJson.Value> pos1 = new LinkedHashMap<>();
        pos1.put("v", new DecimalValue("0.0"));
        assertFalse(invokeSameAuxiliary(new Obj(neg1), new Obj(pos1)));
        assertFalse(oracle(new Obj(neg1), new Obj(pos1)));

        // Mixed nested values
        Map<String, OpportunityJson.Value> mixed = new LinkedHashMap<>();
        mixed.put("arr", new Arr(java.util.List.of(new Bool(false), Nil.INSTANCE,
                new IntegerValue(new BigInteger("9007199254740993")),
                new Obj(Map.of("leaf", new Text("nested"))))));
        mixed.put("bool", new Bool(true));
        mixed.put("nil", Nil.INSTANCE);
        mixed.put("int", new IntegerValue(BigInteger.valueOf(9007199254740993L)));
        Obj mixedObj = new Obj(mixed);
        assertTrue(invokeSameAuxiliary(mixedObj, mixedObj));
        assertTrue(oracle(mixedObj, mixedObj));

        // Caller mutation after construction
        Map<String, OpportunityJson.Value> mutable = new LinkedHashMap<>();
        mutable.put("key", new Text("original"));
        Obj immutable = new Obj(mutable);
        mutable.put("key", new Text("mutated"));
        Obj fresh = new Obj(Map.of("key", new Text("original")));
        assertTrue(invokeSameAuxiliary(immutable, fresh));
        assertTrue(oracle(immutable, fresh));
    }

    @Test
    void invalidInputPreservesOracleException() throws Exception {
        // Depth > 64
        Obj current = new Obj(new LinkedHashMap<>());
        for (int i = 0; i < 65; i++) {
            Map<String, OpportunityJson.Value> parent = new LinkedHashMap<>();
            parent.put("child", current);
            current = new Obj(parent);
        }
        Exception helperEx = null;
        try { invokeSameAuxiliary(current, current); } catch (Exception e) { helperEx = e; }
        Exception oracleEx = null;
        try { oracle(current, current); } catch (Exception e) { oracleEx = e; }
        assertNotNull(helperEx);
        assertNotNull(oracleEx);
        assertEquals(oracleEx.getClass(), helperEx.getClass());
        assertEquals(oracleEx.getMessage(), helperEx.getMessage());

        // Null child
        Map<String, OpportunityJson.Value> nullChild = new LinkedHashMap<>();
        nullChild.put("bad", null);
        Obj invalid = new Obj(nullChild);
        helperEx = null;
        try { invokeSameAuxiliary(invalid, invalid); } catch (Exception e) { helperEx = e; }
        oracleEx = null;
        try { oracle(invalid, invalid); } catch (Exception e) { oracleEx = e; }
        assertNotNull(helperEx);
        assertNotNull(oracleEx);
        assertEquals(oracleEx.getClass(), helperEx.getClass());
        assertEquals(oracleEx.getMessage(), helperEx.getMessage());

        // Valid first, invalid second
        Map<String, OpportunityJson.Value> validMap = new LinkedHashMap<>();
        validMap.put("ok", new Obj(new LinkedHashMap<>()));
        Obj validObj = new Obj(validMap);
        helperEx = null;
        try { invokeSameAuxiliary(validObj, invalid); } catch (Exception e) { helperEx = e; }
        oracleEx = null;
        try { oracle(validObj, invalid); } catch (Exception e) { oracleEx = e; }
        assertNotNull(helperEx);
        assertNotNull(oracleEx);
        assertEquals(oracleEx.getClass(), helperEx.getClass());
        assertEquals(oracleEx.getMessage(), helperEx.getMessage());
    }
}
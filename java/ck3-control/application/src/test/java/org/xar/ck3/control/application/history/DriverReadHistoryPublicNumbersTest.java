package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real transport-role producer -> persisted typed roles -> both public consumers. DATA supplies no Native/writer authority. */
final class DriverReadHistoryPublicNumbersTest {
    private static final BigInteger SIGNED=new BigInteger("-9223372036854775808");
    private static final BigInteger UNSIGNED=new BigInteger("18446744073709551615");
    private static final BigInteger DERIVED=BigInteger.TEN.pow(80).negate();
    private static RawJson raw(Obj value){return new RawJson(DriverJson.encode(value));}
    private static Obj original() {
        return new Obj(Map.of("signed",new IntegerValue(SIGNED),"unsigned",new IntegerValue(UNSIGNED),
                "derived",new IntegerValue(DERIVED),"raw_text",new Text("18446744073709551615"),
                "unchanged",new IntegerValue(BigInteger.ONE),"null_value",Nil.INSTANCE,
                "rows",new Arr(List.of(new Obj(Map.of("epoch",new IntegerValue(UNSIGNED),"enabled",new Bool(true)))))));
    }
    /** Explicit test formatter, mirroring a source-owned domain codec rather than guessing roles from field names or magnitude. */
    private static Obj publicResult(Obj original) {
        Obj row=OpportunityJson.object(OpportunityJson.array(original.get("rows"),"rows").getFirst(),"row");
        return original.with("signed",new Text(SIGNED.toString())).with("unsigned",new Text(UNSIGNED.toString()))
                .with("derived",new Text(DERIVED.toString())).with("rows",new Arr(List.of(row.with("epoch",new Text(UNSIGNED.toString())))));
    }
    @Test void actualProducerRolesSurviveJsonAndBothConsumerDirectionsWithoutLosingTypes() {
        Obj internal=original(),exposed=publicResult(internal);
        PublicNumbers produced=PublicNumbers.fromResults(raw(internal),raw(exposed));
        assertEquals(4,produced.decimalIntegers().size());
        PublicNumbers persisted=PublicNumbers.fromJson(OpportunityJson.parse(OpportunityJson.encode(produced.toJson())));
        assertEquals(produced,persisted);assertEquals(exposed,persisted.toPublic(internal));
        assertEquals(internal,persisted.fromPublic(exposed));
        assertEquals(new Text(UNSIGNED.toString()),persisted.fromPublic(exposed).get("raw_text"));
        assertEquals(Nil.INSTANCE,persisted.fromPublic(exposed).get("null_value"));
        assertEquals(new IntegerValue(BigInteger.ONE),persisted.toPublic(internal).get("unchanged"));
    }
    @Test void roleOrderIsCanonicalAcrossOriginalObjectMemberOrder() {
        Obj internal=original();var entries=new java.util.ArrayList<>(internal.members().entrySet());java.util.Collections.reverse(entries);
        var reverse=new java.util.LinkedHashMap<String,Value>();entries.forEach(entry->reverse.put(entry.getKey(),entry.getValue()));
        Obj reordered=new Obj(reverse);
        PublicNumbers first=PublicNumbers.fromResults(raw(internal),raw(publicResult(internal)));
        PublicNumbers second=PublicNumbers.fromResults(raw(reordered),raw(publicResult(reordered)));
        assertEquals(first,second);assertArrayEquals(OpportunityJson.encode(first.toJson()),OpportunityJson.encode(second.toJson()));
        var paths=new java.util.ArrayList<>(first.toJson().items());java.util.Collections.reverse(paths);
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromJson(new Arr(paths)));
    }
    @Test void producerRejectsShapeTypeNullAndValueChangesAndUndeclaredWideNumbers() {
        Obj internal=original(),exposed=publicResult(internal);
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(exposed.with("unsigned",new Text("1")))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(exposed.with("raw_text",new IntegerValue(UNSIGNED)))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(exposed.with("null_value",new Text("null")))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(exposed.with("rows",new Arr(List.of())))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(exposed.with("extra",new Bool(true)))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromResults(raw(internal),raw(internal)));
        Obj textOnly=new Obj(Map.of("raw",new Text(UNSIGNED.toString())));
        assertTrue(PublicNumbers.fromResults(raw(textOnly),raw(textOnly)).decimalIntegers().isEmpty());
    }
    @Test void persistedRolesRejectWrongTokensDuplicatesAndNoncanonicalDecimals() {
        Obj internal=original(),exposed=publicResult(internal);PublicNumbers produced=PublicNumbers.fromResults(raw(internal),raw(exposed));
        Value first=produced.toJson().items().getFirst();
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromJson(new Arr(List.of(first,first))));
        for(Value bad:List.of(new Bool(true),new DecimalValue("0.0"),new IntegerValue(BigInteger.valueOf(-1)))) {
            Value path=new Arr(List.of(new Arr(List.of(new Obj(Map.of("index",bad))))));
            assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromJson(path));
        }
        Value wrongField=new Arr(List.of(new Arr(List.of(new Obj(Map.of("field",new Text("signed"),"extra",new Text("unsigned")))))));
        assertThrows(IllegalArgumentException.class,()->PublicNumbers.fromJson(wrongField));
        for(String bad:List.of("01","-0","+1","1.0","1e0"))
            assertThrows(IllegalArgumentException.class,()->produced.fromPublic(exposed.with("unsigned",new Text(bad))));
        assertThrows(IllegalArgumentException.class,()->produced.fromPublic(exposed.with("unsigned",new Bool(true))));
        PublicNumbers missing=new PublicNumbers(List.of(new NumberPath(List.of(new Field("absent")))));
        assertThrows(IllegalArgumentException.class,()->missing.toPublic(internal));
        PublicNumbers outside=new PublicNumbers(List.of(new NumberPath(List.of(new Field("rows"),new Element(1),new Field("epoch")))));
        assertThrows(IllegalArgumentException.class,()->outside.toPublic(internal));
    }
}

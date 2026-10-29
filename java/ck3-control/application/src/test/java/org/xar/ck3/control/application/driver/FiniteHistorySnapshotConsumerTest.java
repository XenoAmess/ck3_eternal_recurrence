package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.history.*;

/** Pure consumers of the finite owning row codecs. No canonical row, private Source or Root is issued here. */
public final class FiniteHistorySnapshotConsumerTest {
    private static final List<String> MARKERS=List.of(DriverReturnedActionHistoryRowProducer.SOURCE_FIELD,
            DriverReturnedPublicReadHistoryRowProducer.SOURCE_FIELD,DriverPostKnownReadFailureRowProducer.SOURCE_FIELD,
            DriverEarlyExecuteFailureRowProducer.SOURCE_FIELD);
    @Test void everyNewMarkerRequiresItsClosedOwningSourceRatherThanPassingAsUnknownHistory() {
        for(String marker:MARKERS) {
            var row=new Obj(Map.of("index",new IntegerValue(BigInteger.ONE),"command",new Text("query-army-strengths-v1"),
                    "ok",new Bool(false),"error",new Text("actual error DATA"),marker,new Obj(Map.of())));
            var history=new Arr(List.of(row));
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningHistoryData(history),marker);
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decodePlanningHistoryData(history),marker);
            assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodePlanningHistoryData(new Arr(List.of(
                    row.with("result",new Obj(Map.of("undeclared_wide_integer",new IntegerValue(BigInteger.ONE.shiftLeft(63)))))))),marker);
        }
    }
    /** Owning actual software producer tests/central writer tests supply their original rows here.
     * Calling this DATA assertion never creates a source-qualified row or substitutes for full Root acceptance. */
    public static Arr assertOwningRowsRoundTrip(Arr actualNumericRows) {
        assertFalse(array(actualNumericRows,"actual rows").isEmpty());
        boolean known=false;
        for(Value value:array(actualNumericRows,"actual rows")) {
            Obj row=object(value,"actual owning history row");
            for(String marker:MARKERS)if(row.members().containsKey(marker))known=true;
        }
        assertTrue(known,"at least one actual new finite producer row is required");
        Arr encoded=PublicSnapshotCodec.encodePlanningHistoryData(actualNumericRows);
        assertEquals(actualNumericRows,PublicSnapshotCodec.decodePlanningHistoryData(encoded));
        return encoded;
    }
}

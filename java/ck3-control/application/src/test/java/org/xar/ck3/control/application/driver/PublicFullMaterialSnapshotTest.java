package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;

/** Explicit full Driver material DATA. Native/ACK/default protocol numeric bounds are unchanged. */
final class PublicFullMaterialSnapshotTest {
    private static final String TOKEN="0."+"1".repeat(5000);
    private static Obj original() {
        Obj actual=assertInstanceOf(DriverObservationAssembler.Complete.class,DriverObservationAssemblerTest.join(DriverObservationAssemblerTest.STATE)).semantic();
        var row=new Obj(java.util.Map.of()).with("index",new IntegerValue(BigInteger.valueOf(3))).with("command",new Text("source-only-full-material"))
                .with("ok",new Bool(true)).with("result",new Obj(java.util.Map.of()).with("opaque_decimal",new DecimalValue(TOKEN)).with("opaque_negative_zero",new DecimalValue("-0.0")));
        return actual.with("opaque_full_decimal",new DecimalValue(TOKEN)).with("native_command_history",new Arr(List.of(row)));
    }
    @Test void fullSemanticAndHistoryMaterialKeepLegalLongFiniteDecimalTokensWithoutProtocolWidening() {
        Obj original=original();byte[] bytes=DriverJson.encode(original);RawJson full=RawJson.fullMaterial(bytes);
        assertThrows(IllegalArgumentException.class,()->new RawJson(bytes));assertThrows(IllegalArgumentException.class,full::requireProtocolBound);
        RawJson encoded=PublicSnapshotCodec.encodeSemanticData(full);assertThrows(IllegalArgumentException.class,encoded::requireProtocolBound);
        assertEquals(original,PublicSnapshotCodec.decode(encoded));
        assertEquals(original,DriverJson.object(PublicSnapshotCodec.decodeSemanticData(encoded).bytes(),RawJson.MAXIMUM_BYTES));
        assertTrue(new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains(TOKEN));
        assertTrue(new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("-0.0"));
    }
    @Test void planningSnapshotAndHistoryDataUseTheSameExplicitFullMaterialLane() {
        Obj original=original();var fields=new LinkedHashMap<>(original.members());
        for(String key:List.of("native_command_history","native_rollback_war_failure","native_rollback_war_failures"))fields.remove(key);
        Obj without=new Obj(fields);RawJson encoded=PublicSnapshotCodec.encodePlanningSnapshotData(RawJson.fullMaterial(DriverJson.encode(without)));
        assertEquals(without,DriverJson.object(PublicSnapshotCodec.decodePlanningSnapshotData(encoded).bytes(),RawJson.MAXIMUM_BYTES));
        var rows=new Arr(array(original.get("native_command_history"),"history"));
        assertEquals(rows,PublicSnapshotCodec.decodePlanningHistoryData(PublicSnapshotCodec.encodePlanningHistoryData(rows)));
    }
    @Test void fullMaterialDoesNotGuessUnknownWideIntegerRolesOrAdmitNonFinitePublicFloats() {
        Obj original=original();
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(RawJson.fullMaterial(DriverJson.encode(original.with("unqualified_identity",new IntegerValue(BigInteger.valueOf(Long.MAX_VALUE)))))));
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.encodeSemanticData(RawJson.fullMaterial(DriverJson.encode(original.with("unqualified_float",new DecimalValue("1e10000"))))));
    }
}

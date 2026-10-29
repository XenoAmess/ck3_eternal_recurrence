package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Real full semantic producer -> actual retained-preclock frame consumer. DATA only, no Root/native/cause qualification. */
final class RootNaturalFullSemanticTest {
    private static final BigInteger PUBLIC=new BigInteger("18446744073709551615"),NATIVE=PUBLIC.subtract(BigInteger.ONE);
    private static OpportunityJson.Obj semantic() {
        var fields=new LinkedHashMap<String,OpportunityJson.Value>();
        fields.put("snapshot_id",new OpportunityJson.Text("retained-original-full-semantic"));
        fields.put("revision",new OpportunityJson.IntegerValue(PUBLIC));fields.put("native_revision",new OpportunityJson.IntegerValue(NATIVE));
        fields.put("date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(741221)));fields.put("local_player_id",new OpportunityJson.IntegerValue(BigInteger.ZERO));
        fields.put("unrelated_complete_material",new OpportunityJson.Text("x".repeat(1_048_600)));
        fields.put("original_negative_zero",new OpportunityJson.DecimalValue("-0.0"));fields.put("original_ratio_float",new OpportunityJson.DecimalValue("1.0"));
        return new OpportunityJson.Obj(fields);
    }
    @Test void actualCompleteSemanticBeyondSmallJsonLaneKeepsFrameAndOriginalBytes()throws Exception {
        byte[] original=DriverJson.encode(semantic());assertTrue(original.length>StrictJson.EXPLICIT_MAX_BYTES);
        byte[] digest=MessageDigest.getInstance("SHA-256").digest(original);
        assertEquals(new Frame("retained-original-full-semantic",PUBLIC,NATIVE,741221,42,0),RootNaturalSuccessionOriginals.originalPredecessorFrame(original,42));
        assertArrayEquals(digest,MessageDigest.getInstance("SHA-256").digest(original),"consumer must not rewrite retained original semantic bytes");
    }
    @Test void fullLaneStillRejectsBooleanFloatingAndMissingFrameIdentities() {
        var original=semantic();
        for(var wrong:new OpportunityJson.Value[]{new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("18446744073709551615.0")})
            assertThrows(IllegalArgumentException.class,()->RootNaturalSuccessionOriginals.originalPredecessorFrame(DriverJson.encode(original.with("revision",wrong)),42));
        var missing=new LinkedHashMap<>(original.members());missing.remove("native_revision");
        assertThrows(IllegalArgumentException.class,()->RootNaturalSuccessionOriginals.originalPredecessorFrame(DriverJson.encode(new OpportunityJson.Obj(missing)),42));
    }
}

package org.xar.ck3.control.wave2.military.exitresult;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

/** Actual shared composer and live/cold literal grammar retain the original public route identity without int truncation. */
final class OrdinaryWarExitIdentityTest {
    @Test void enforceZeroAndFullSafeIntegerScopeUseTheSameComposerAndLiteralConsumer() throws Exception {
        for (long id : List.of(0L, 2147483664L, 9007199254740991L)) {
            ObjectNode input = base();
            ((ObjectNode) input.path("action_result")).put("step", "enforce-demands-" + id);
            ((ObjectNode) input.path("before_snapshot").path("active_wars").get(0)).put("war_id", id);
            var result = OrdinaryWarExitObservationCodec.decodeAndCompose(StrictJson.canonical(input));
            assertNotNull(result); assertNotNull(result.bound()); assertTrue(result.bound().warAbsent());
            assertEquals(id, result.action().warId());
            assertEquals(result.action().warId(), OrdinaryWarExitObservationCodec.actionForLiteral("enforce-demands-" + id).warId());
            JsonNode encoded = StrictJson.parse(OrdinaryWarExitObservationCodec.encode(result));
            assertEquals(BigInteger.valueOf(id), encoded.path("war_id").bigIntegerValue());
            assertTrue(encoded.path("observed_result_identity").isNull());
        }
    }
    @Test void whiteAndSurrenderKeepPositiveInt32AndInvalidNativeTokensCannotBindAnExit() throws Exception {
        for (String prefix : List.of("offer-white-peace-", "surrender-war-")) for (String token : List.of("0", "2147483648", "-1", "01", "+1", "1.0"))
            assertThrows(IllegalArgumentException.class, () -> OrdinaryWarExitObservationCodec.actionForLiteral(prefix + token));
        for (String token : List.of("9007199254740992", "-1", "00", "+0", "0.0"))
            assertThrows(IllegalArgumentException.class, () -> OrdinaryWarExitObservationCodec.actionForLiteral("enforce-demands-" + token));
        ObjectNode input = base(); ((ObjectNode) input.path("action_result")).put("step", "enforce-demands-0");
        ((ObjectNode) input.path("before_snapshot").path("active_wars").get(0)).put("war_id", false);
        var result = OrdinaryWarExitObservationCodec.decodeAndCompose(StrictJson.canonical(input));
        assertNotNull(result); assertNull(result.bound()); assertTrue(result.resources().isEmpty());
        input = base(); ((ObjectNode) input.path("before_snapshot").path("active_wars").get(0)).put("war_id", 9007199254740992L);
        assertNull(OrdinaryWarExitObservationCodec.decodeAndCompose(StrictJson.canonical(input)).bound());
    }
    @Test void typedCompleteFramesUseOneComposerWithoutMaterialEnvelopeByteCap() throws Exception {
        ObjectNode input=base();
        var original=OrdinaryWarExitObservationCodec.decodeAndCompose(StrictJson.canonical(input));
        byte[] expected=OrdinaryWarExitObservationCodec.encode(original);
        ((ObjectNode)input.get("before_snapshot")).put("opaque_full_driver_extension","x".repeat(1_048_577));
        ((ObjectNode)input.get("post_snapshot")).put("opaque_full_driver_extension","y".repeat(1_048_577));
        // The small material parser stays bounded; the genuine Root/Driver has already parsed these frames.
        assertThrows(IllegalArgumentException.class,()->StrictJson.canonical(input,StrictJson.EXPLICIT_MAX_BYTES));
        var same=OrdinaryWarExitObservationCodec.compose(input.get("before_snapshot"),input.get("post_snapshot"),
                input.get("action_result"),input.get("claims_result"),input.get("title_holder_results"),input.get("truce_result"));
        assertArrayEquals(expected,OrdinaryWarExitObservationCodec.encode(same));
        // Full frames do not weaken the existing typed WarID guard or turn absence into settlement identity.
        ((ObjectNode)input.path("before_snapshot").path("active_wars").get(0)).put("war_id",false);
        var malformed=OrdinaryWarExitObservationCodec.compose(input.get("before_snapshot"),input.get("post_snapshot"),
                input.get("action_result"),input.get("claims_result"),input.get("title_holder_results"),input.get("truce_result"));
        assertNotNull(malformed);assertNull(malformed.bound());assertTrue(malformed.resources().isEmpty());
    }
    @Test void originalDriverAndNativeObserverRetainTheirDifferentOriginalActionDomains() throws Exception {
        for(String prefix:List.of("enforce-demands-","offer-white-peace-","surrender-war-"))
            for(long id:List.of(0L,1L,2147483647L,2147483648L,9007199254740991L)) {
                ObjectNode input=base();((ObjectNode)input.get("action_result")).put("step",prefix+id);
                ((ObjectNode)input.path("before_snapshot").path("active_wars").get(0)).put("war_id",id);
                var result=OrdinaryWarExitObservationCodec.compose(OrdinaryWarExitObservationCodec.ActionProfile.ORIGINAL_DRIVER,
                        input.get("before_snapshot"),input.get("post_snapshot"),input.get("action_result"),
                        input.get("claims_result"),input.get("title_holder_results"),input.get("truce_result"));
                if(id==0||id>Integer.MAX_VALUE)assertNull(result,"original Python composer returns None outside positive int32");
                else {assertNotNull(result);assertEquals(id,result.action().warId());}
                if(prefix.equals("enforce-demands-")) {
                    var nativeResult=OrdinaryWarExitObservationCodec.compose(input.get("before_snapshot"),input.get("post_snapshot"),
                            input.get("action_result"),input.get("claims_result"),input.get("title_holder_results"),input.get("truce_result"));
                    assertNotNull(nativeResult);assertEquals(id,nativeResult.action().warId());
                }
            }
        assertThrows(IllegalArgumentException.class,()->OrdinaryWarExitObservationCodec.compose(null,null,null,null,null,null,null));
    }
    /** The actual original producer supplies frames; a static cleanup lookup and an ACK supply no domain read. */
    @Test void warAbsenceAndEitherAckKeepIndependentSettlementMaterialsUnobserved() throws Exception {
        for (boolean acknowledged : List.of(false, true)) {
            ObjectNode input = base();
            ((ObjectNode) input.get("action_result")).put("accepted", acknowledged);
            var actual = OrdinaryWarExitObservationCodec.compose(input.get("before_snapshot"), input.get("post_snapshot"),
                    input.get("action_result"), input.get("claims_result"), input.get("title_holder_results"), input.get("truce_result"));
            assertNotNull(actual); assertNotNull(actual.bound()); assertTrue(actual.bound().warAbsent());
            assertEquals(acknowledged, actual.action().acknowledged());
            JsonNode encoded = StrictJson.parse(OrdinaryWarExitObservationCodec.encode(actual));
            assertTrue(encoded.get("observed_result_identity").isNull());
            assertEquals("no_independent_result_observer", encoded.get("result_identity_reason").textValue());
            for (String domain : List.of("claims", "titles", "truce"))
                assertEquals("not_observed", encoded.path(domain).path("status").textValue());
            assertTrue(encoded.path("truce").get("expiry_date_raw").isNull());
            for (String resource : List.of("gold", "prestige", "piety"))
                assertEquals("unproven", encoded.path("resources").path(resource).path("action_attribution").textValue());
        }
    }
    private static ObjectNode base() throws Exception {
        try (InputStream input = OrdinaryWarExitIdentityTest.class.getResourceAsStream("/exitresult/producer-golden-v1.json")) {
            if (input == null) throw new IllegalStateException("required actual original producer capture is absent");
            ObjectNode original = (ObjectNode) StrictJson.parse(input.readAllBytes()).path("base_input").deepCopy();
            original.putNull("claims_result").putNull("title_holder_results").putNull("truce_result"); return original;
        }
    }
}

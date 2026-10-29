package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** The existing original-result receipt producer feeds the ordinary installed decoder.
 * These are pure DATA fixtures; they issue no native read, private Root or runtime authority. */
final class ArmyClosedReceiptIntegerTokenTest {
    @Test void originalOrdinaryReceiptReplaysItsStrictIntegerBaseline() throws IOException {
        var context=ArmyClosedReadCodecTest.context("1.20.0.4",0);
        var call=call();var original=ArmyClosedOriginalResultCodecTest.receipt(call,context,token());
        assertInstanceOf(ArmyClosedReads.Truce.class,ArmyClosedReadCodec.decode(call,context,original));
    }

    @Test void floatingOwnerCannotBecomeAnIntegerBetweenTheOriginalReceiptAndDecoder() throws IOException {
        var context=ArmyClosedReadCodecTest.context("1.20.0.4",0);var call=call();
        var floating=token();ArmyJson.object(floating.get("raiktor_actual_truce_expiry")).put("owner_character_id",0.0);
        var original=ArmyClosedOriginalResultCodecTest.receipt(call,context,floating);
        var retained=original.original().originalResultToken().orElseThrow().bytes();
        assertTrue(new String(retained,StandardCharsets.UTF_8).contains("\"owner_character_id\":0.0"),
                "the existing packet/receipt producer must retain the actual floating token");
        assertThrows(IllegalArgumentException.class,()->ArmyClosedReadCodec.decodeToken(call,context,retained));
        assertThrows(IllegalArgumentException.class,()->ArmyClosedReadCodec.decode(call,context,original));
    }

    private static ArmyCalls.Truce call() {
        return new ArmyCalls.Truce(new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(7))),new PositiveId(2));
    }
    private static ObjectNode token() {
        var body=ArmyJson.empty().put("schema_version",1).put("backend_id","ck3-1.20.0.4-native-player-truce-expiry-v1")
                .put("ck3_build","1.20.0.4").put("executable_sha256",ArmyResponseCodec.ACTUAL4_SHA).put("status","no_truce")
                .put("snapshot_revision",11).put("current_date_raw",53238336).put("owner_character_id",0).put("toward_character_id",2)
                .put("native_has_truce",false).put("actual_expiry_observable",false).putNull("expiry_date_raw")
                .put("same_frame_stable",true).put("readiness",false).put("temporal_semantics","post_application_persisted_relation_state")
                .put("unavailable_reason","native_has_truce_false");
        var token=ArmyJson.empty().put("step","query-raiktor-actual-truce-expiry-v1-2").put("accepted",true)
                .put("query_sequence",ArmyClosedReadCodecTest.MAX).put("snapshot_revision",11).put("date_raw",53238336)
                .put("read_only",true).put("backend_id","native-headless");
        token.set("raiktor_actual_truce_expiry",body);return token;
    }
}

package org.xar.ck3.control.contracts;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;

final class DefaultRaiseObservationTest {
    private static final DefaultRaiseObservation.Expected EXPECTED=new DefaultRaiseObservation.Expected("1.20.0.4",BigInteger.ZERO,BigInteger.ONE,BigInteger.valueOf(24000));
    @Test void actualNativePayloadPreservesPublicActorZeroAndRoundTripsTheSameJsonDomain() {
        ObjectNode original=payload();byte[] bytes=StrictJson.canonical(original);
        var parsed=DefaultRaiseObservation.parse(StrictJson.parse(bytes),EXPECTED);
        assertEquals(0,parsed.actor());assertTrue(parsed.raising().legal().orElseThrow());
        assertEquals(900,parsed.reserve().unraisedSoldiers().orElseThrow());
        assertArrayEquals(bytes,StrictJson.canonical(StrictJson.parse(bytes)));
    }
    @Test void nullObservationIsRetainedButMissingNullableFieldsCannotPass() {
        var negative=payload();negative.put("status","unavailable").put("default_raise_legality_ready",false).put("failure","not_ready");
        negative.putNull("native_default_raise_legal").putNull("default_raise_province_id");
        negative.put("unraised_troops_status","unavailable").put("unraised_troops_ready",false).put("unraised_troops_failure","not_observed").putNull("unraised_soldiers");
        var parsed=DefaultRaiseObservation.parse(negative,EXPECTED);
        assertTrue(parsed.raising().legal().isEmpty());assertTrue(parsed.reserve().unraisedSoldiers().isEmpty());
        for(String required:java.util.List.of("native_default_raise_legal","default_raise_province_id","unraised_soldiers")) {
            var missing=negative.deepCopy();missing.remove(required);
            assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(missing,EXPECTED));
        }
    }
    @Test void wrongIntegerTypesFrameBuildAndReadinessRejectBeforeAnyReserveAction() {
        var floating=payload();floating.put("unraised_troops_scale",1.0);assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(floating,EXPECTED));
        var bool=payload();bool.put("actor_character_id",false);assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(bool,EXPECTED));
        var stale=payload();stale.put("snapshot_revision",2);assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(stale,EXPECTED));
        var mixed=payload();mixed.put("game_version","1.20.0.3");assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(mixed,EXPECTED));
        var falseReady=payload();falseReady.put("default_raise_legality_ready",false);assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(falseReady,EXPECTED));
        var rounded=payload();rounded.put("snapshot_revision","1");assertThrows(IllegalArgumentException.class,()->DefaultRaiseObservation.parse(rounded,EXPECTED));
    }
    private static ObjectNode payload() {
        var row=StrictJson.object();row.put("schema","ck3_12004_player_default_raise_v1").put("game_version","1.20.0.4")
                .put("executable_sha256","98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518")
                .put("status","available").put("snapshot_revision",1).put("date_raw",24000).put("actor_character_id",0)
                .put("default_raise_province_id",20).put("native_default_raise_legal",true).put("default_raise_legality_ready",true).put("failure","none")
                .put("unraised_troops_status","available").put("unraised_soldiers",900).put("unraised_troops_ready",true).put("unraised_troops_failure","none")
                .put("unraised_troops_scale",1).put("unraised_troops_scope","native_all_actor_categories");return row;
    }
}

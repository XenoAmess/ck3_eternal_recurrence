package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

final class SwayPublicCodecTest {
    @Test void originalSafeNumericAndFullWidthDecimalInputsHaveOneCanonicalRoundtrip() {
        var input=raw("{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":33554443,\"scheme_instance_generation\":2}");
        var request=SwayPublicCodec.decodeFinish(input);assertEquals(BigInteger.valueOf(17),request.expectedRevision());
        var encoded=SwayPublicCodec.encodeFinishRequest(request);assertTrue(StrictJson.parse(encoded.bytes()).get("expected_revision").isTextual());assertEquals(request,SwayPublicCodec.decodeFinish(encoded));
        var wide=new SwayPublicCodec.JournalRequest(SwayObservationReads.Kind.EXECUTION,new BigInteger("18446744073709551615"),50331650,33554443,new BigInteger("9007199254740993"));
        assertEquals(wide,SwayPublicCodec.decodeJournal(wide.kind(),SwayPublicCodec.encodeJournalRequest(wide)));
        var zero=SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.TERMINATION,raw("{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":33554443}"));assertEquals(BigInteger.ZERO,zero.afterSequence());
    }
    @Test void missingNullAliasBoolFloatRoundedAndNoncanonicalCursorsAreRejected() {
        String base="{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":33554443,\"after_sequence\":%s}";
        for(String value:new String[]{"null","true","1.0","9007199254740993","\"01\"","\"-1\"","\"18446744073709551616\"","\" 1\""})
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.EXECUTION,raw(base.formatted(value))),value);
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.EXECUTION,raw("{\"expected_revision\":17,\"target_character_id\":50331650}")));
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeJournal(SwayObservationReads.Kind.EXECUTION,raw("{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":1,\"afterSequence\":0}")));
        assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeFinish(raw("{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":33554443,\"scheme_instance_generation\":0}")));
    }
    @Test void originalFinishRejectsPublicFieldDriftAndWrongTypesBeforeInternalConstruction() {
        for(String input:new String[]{
                "{\"expected_revision\":true,\"target_character_id\":50331650,\"scheme_instance_id\":1,\"scheme_instance_generation\":0}",
                "{\"expected_revision\":17,\"target_character_id\":50331650.0,\"scheme_instance_id\":1,\"scheme_instance_generation\":0}",
                "{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":1,\"scheme_instance_generation\":false}",
                "{\"expected_revision\":17,\"target_character_id\":50331650,\"scheme_instance_id\":1,\"scheme_instance_generation\":0,\"action_id\":\"stop-sway-caller-forged\"}"})
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeFinish(raw(input)));
    }
    private static RawJson raw(String value){return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
}

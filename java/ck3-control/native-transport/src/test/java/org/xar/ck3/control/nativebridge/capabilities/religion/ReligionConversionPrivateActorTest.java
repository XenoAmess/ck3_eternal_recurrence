package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionActions.*;

/** Controlled original-owner JSON exercises the real normalizer; no submission or Game authority. */
final class ReligionConversionPrivateActorTest {
    @Test void conversionKeepsItsPrivatePositiveActorGateAfterSharedFrameExpansion() {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0)) {
            Input input=input(Kind.CONVERSION,actor);RawJson original=ReligionCodec.raw(input.envelope());
            assertThrows(IllegalArgumentException.class,()->normalize(input));
            assertArrayEquals(original.bytes(),ReligionCodec.raw(input.envelope()).bytes());
        }
        for(int actor:List.of(1,Integer.MAX_VALUE)) {
            Input input=input(Kind.CONVERSION,actor);ConversionSubmission value=(ConversionSubmission)normalize(input);
            assertEquals(BigInteger.valueOf(actor),value.owner().playerId());assertFalse(value.copyCalled());
            ObjectNode publicResult=presentSubmission(value);assertEquals(actor,publicResult.get("player_character_id").intValue());
            assertFalse(publicResult.get("submitted").booleanValue());assertFalse(publicResult.get("material_result").booleanValue());
        }
    }
    @Test void countyAndObservedFramesRetainSignedActorsIncludingZero() {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0,1,Integer.MAX_VALUE)) {
            Input input=input(Kind.COUNTY,actor);CountySubmission value=(CountySubmission)normalize(input);
            assertEquals(actor,value.owner().playerId());assertFalse(value.copyCalled());
            assertEquals(actor,presentSubmission(value).get("player_character_id").intValue());
            assertEquals(BigInteger.valueOf(actor),input.frame().player());
        }
    }
    @Test void persistedOriginalOwnerRoundTripCannotBypassTheConversionGate() {
        for(int actor:List.of(-2,0,1)) {
            Input input=input(Kind.CONVERSION,actor);
            Input cold=new Input(input.kind(),ReligionCodec.object(ReligionCodec.raw(input.envelope())),ReligionCodec.object(ReligionCodec.raw(input.intent())),input.frame());
            if(actor<=0)assertThrows(IllegalArgumentException.class,()->normalize(cold));
            else assertEquals(BigInteger.ONE,((ConversionSubmission)normalize(cold)).owner().playerId());
        }
    }
    private record Input(Kind kind,ObjectNode envelope,ObjectNode intent,ReligionConversionRead.BoundFrame frame) { }
    private static Submission normalize(Input input) {
        return normalizeSubmission(input.kind(),ReligionCodec.raw(input.envelope()),input.frame(),BigInteger.valueOf(9),BigInteger.valueOf(11),"controlled-original-request",ReligionCodec.raw(input.intent()));
    }
    private static Input input(Kind kind,int actor) {
        var build=PlayerReligionContext.Build.CROZIER3;
        ObjectNode intent=StrictJson.object().put("expected_revision",9).put("action_id","controlled-original-caller");
        if(kind==Kind.CONVERSION)intent.put("target_rite_id",17).put("max_piety_cost_raw",0);
        else intent.put("expected_active_task_id",17).put("expected_incumbent_character_id",29).put("province_id",42).put("replace_existing_task",true);
        ObjectNode owner=StrictJson.object().put("request_id","controlled-original-request").put("native_revision",11).put("date_raw",100).put("capture_epoch",3).put("played_character_id",actor).put("command_channel",14).put("native_submit_copy_called",false).put("status","not_submitted").put("failure","not_sampled");
        owner.set("request",intent.deepCopy());
        if(kind==Kind.CONVERSION) {
            owner.put("command_target_rite_id",17).put("command_pay_piety",true).putNull("before").putNull("paid_terms").putNull("native_reasons");
        } else {
            owner.put("native_final_can_dispatch",false).putNull("target_county_title_id");
            ObjectNode task=StrictJson.object().put("available",false).put("failure","not_sampled").put("capture_epoch",0).put("date_raw",100).put("owner_character_id",actor).put("task_key","");
            for(String field:List.of("incumbent_character_id","active_task_id","target_province_id","target_county_title_id","progress_kind","target_scope_tag","percentage_progress_raw"))task.putNull(field);
            owner.set("before",task);
        }
        ObjectNode envelope=StrictJson.object().put("step",kind.operation().value()).put("accepted",true).put("private_build",true).put("advertised",false).put("read_only",false).put("backend_id","native-headless").put("game_version",build.version()).put("executable_sha256",build.sha256()).put("snapshot_revision",11).put("public_revision",9).put("date_raw",100).put("capture_epoch",3);
        envelope.set("submission",owner);
        return new Input(kind,envelope,intent,new ReligionConversionRead.BoundFrame(build,BigInteger.valueOf(100),BigInteger.valueOf(actor)));
    }
}

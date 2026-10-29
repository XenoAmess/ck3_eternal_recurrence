package org.xar.ck3.control.nativebridge.capabilities.religion;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import static org.junit.jupiter.api.Assertions.*;

/** Controlled owner DATA exercises the independent result decoder. It grants no original Native or Game proof. */
final class ConversionResultOwnerActorTest {
    @Test void independentConversionOwnerKeepsTheOriginalPrivatePositiveActorGate() {
        for(int actor:List.of(Integer.MIN_VALUE,-2,0)){
            ObjectNode original=owner(actor);var bytes=ReligionCodec.raw(original);
            assertThrows(IllegalArgumentException.class,()->ConversionDecoders.religionOwner(original,BigInteger.valueOf(actor)));
            assertThrows(IllegalArgumentException.class,()->ConversionDecoders.religionOwner(ReligionCodec.object(bytes),BigInteger.valueOf(actor)));
            assertEquals(original,ReligionCodec.object(bytes));
            assertEquals(actor,NativeCharacterId.of(BigInteger.valueOf(actor)).value());
        }
        for(int actor:List.of(1,Integer.MAX_VALUE)){
            ObjectNode original=owner(actor);var decoded=ConversionDecoders.religionOwner(original,BigInteger.valueOf(actor));
            assertEquals(BigInteger.valueOf(actor),decoded.playerId());assertFalse(decoded.submitCopyCalled());
            assertEquals(ReligionModels.SubmitStatus.NOT_SUBMITTED,decoded.status());
            assertEquals(decoded,ConversionDecoders.religionOwner(ReligionCodec.object(ReligionCodec.raw(original)),BigInteger.valueOf(actor)));
        }
    }
    @Test void ownerFrameAssociationAndTargetReferenceDomainsRemainDistinct() {
        assertEquals(BigInteger.ZERO,ReligionJson.id(StrictJson.object().put("target",0),"target"));
        assertThrows(IllegalArgumentException.class,()->ConversionDecoders.religionOwner(owner(1),BigInteger.TWO));
        var malformed=owner(1).put("played_character_id",true);assertThrows(IllegalArgumentException.class,()->ConversionDecoders.religionOwner(malformed,BigInteger.ONE));
    }
    private static ObjectNode owner(int actor){
        ObjectNode request=StrictJson.object().put("expected_revision",9).put("target_rite_id",17).put("max_piety_cost_raw",0).put("action_id","controlled-original-caller");
        ObjectNode owner=StrictJson.object().put("request_id","controlled-original-request").put("native_revision",11).put("date_raw",100).put("capture_epoch",3)
                .put("played_character_id",actor).put("command_target_rite_id",17).put("command_pay_piety",true).put("command_channel",14)
                .put("native_submit_copy_called",false).put("status","not_submitted").put("failure","not_sampled").putNull("before").putNull("paid_terms").putNull("native_reasons");
        owner.set("request",request);return owner;
    }
}

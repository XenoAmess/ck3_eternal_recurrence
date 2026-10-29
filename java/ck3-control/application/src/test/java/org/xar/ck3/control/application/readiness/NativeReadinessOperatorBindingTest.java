package org.xar.ck3.control.application.readiness;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverCapabilityStateProducer;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Typed Driver DATA and strict field tests, never a fabricated observed-frame Complete or private Root proof. */
final class NativeReadinessOperatorBindingTest {
    @Test void sharedReplacementAndActualSessionPresentationFeedTheSameReadinessConsumer() {
        var nil=new DriverStateSnapshot.NullValue();
        var before=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,BigInteger.valueOf(3),"same-run"),
                List.of(),nil,nil,nil,nil,nil,nil,nil);
        var auxiliary=new OpportunityJson.Obj(Map.of("driver_state_restored",new OpportunityJson.Bool(false),"driver_state_error",OpportunityJson.Nil.INSTANCE,
                "restore_kind",new OpportunityJson.Text("new_episode"),"episode_binding_state",new OpportunityJson.Text("active_new"),
                "cold_candidate_rejection",OpportunityJson.Nil.INSTANCE,"episode_transition_error",OpportunityJson.Nil.INSTANCE,
                "capability_session_paths",new OpportunityJson.Obj(Map.of("queue_dir",OpportunityJson.Nil.INSTANCE,"driver_state_path",OpportunityJson.Nil.INSTANCE))));
        var replaced=OperatorPlayerSwitch.replacement(before,auxiliary,new OperatorPlayerSwitch.Request(7,BigInteger.TEN));
        assertEquals("same-run",replaced.driver().session().episodeRunId());assertEquals(BigInteger.valueOf(7),replaced.driver().session().actorId());
        assertEquals(new OpportunityJson.Text("operator_played_character_rebind"),replaced.auxiliary().get("restore_kind"));
        assertFalse(replaced.auxiliary().members().containsKey("driver_state_restore_kind"));
        var presented=DriverCapabilityStateProducer.sessionPresentation(replaced.auxiliary());
        assertEquals(presented,CapabilitySessionPresentation.decode(presented.original()));
        var restored=DriverJson.object(DriverJson.encode(presented.original()),DriverJson.MAX_NATIVE_BYTES);
        String binding=NativeReadiness.activeBinding(restored);assertEquals("active_operator_rebind",binding);
        assertFalse(restored.members().containsKey("restore_kind"));
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.requireColdCheckpoint(restored,binding));
    }
    @Test void actualPublicPresentationPairSurvivesTheSharedSerdeAndLegacyBindingsRemainValid() {
        var control=object("{\"episode_binding_state\":\"active_operator_rebind\",\"driver_state_restore_kind\":\"operator_played_character_rebind\"}");
        assertEquals("active_operator_rebind",NativeReadiness.activeBinding(control));
        var restored=DriverJson.object(DriverJson.encode(control),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(control,restored);assertEquals("active_operator_rebind",NativeReadiness.activeBinding(restored));
        for(String legacy:List.of("active_new","active_resumed","active_natural_successor"))
            assertEquals(legacy,NativeReadiness.activeBinding(object("{\"episode_binding_state\":\""+legacy+"\"}")));
    }

    @Test void missingNullWrongTokenOrOtherRestoreKindCannotAliasTheOperatorPair() {
        for(String token:List.of("null","true","1","1.0","[]","{}","\"cold_checkpoint\"","\"operator_played_character_rebind \"")) {
            var control=object("{\"episode_binding_state\":\"active_operator_rebind\",\"driver_state_restore_kind\":"+token+"}");
            assertThrows(IllegalArgumentException.class,()->NativeReadiness.activeBinding(control),token);
        }
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.activeBinding(object("{\"episode_binding_state\":\"active_operator_rebind\"}")));
        for(String token:List.of("null","true","1","[]","{}","\"operator_played_character_rebind\""))
            assertThrows(IllegalArgumentException.class,()->NativeReadiness.activeBinding(object("{\"episode_binding_state\":"+token+"}")));
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.activeBinding(object("{}")));
    }

    @Test void operatorPairCannotBecomeColdCheckpointEvenWithRestoredFlagAndNoRejection() {
        var operator=object("{\"episode_binding_state\":\"active_operator_rebind\",\"driver_state_restore_kind\":\"operator_played_character_rebind\",\"driver_state_restored\":true,\"cold_candidate_rejection\":null}");
        String binding=NativeReadiness.activeBinding(operator);
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.requireColdCheckpoint(operator,binding));
        var cold=object("{\"episode_binding_state\":\"active_resumed\",\"driver_state_restore_kind\":\"cold_checkpoint\",\"driver_state_restored\":true,\"cold_candidate_rejection\":null}");
        assertDoesNotThrow(()->NativeReadiness.requireColdCheckpoint(cold,NativeReadiness.activeBinding(cold)));
        assertThrows(IllegalArgumentException.class,()->NativeReadiness.requireColdCheckpoint(cold,"active_operator_rebind"));
    }
    private static Obj object(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
}

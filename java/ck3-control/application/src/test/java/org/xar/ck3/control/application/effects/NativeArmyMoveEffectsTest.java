package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.application.effects.NativeArmyMoveEffects.*;

final class NativeArmyMoveEffectsTest {
    private static ObjectNode frame(int position, String target, String route, int revision) {
        String raw = "{\"paused\":true,\"map_ready\":true,\"date_raw\":53144328,\"revision\":" + revision + ",\"native_revision\":" + revision
                + ",\"played_character\":{\"character_id\":9,\"alive\":true},\"player_armies\":[{\"army_id\":1,\"owner_character_id\":9,\"controllable\":true,\"in_combat\":false,\"retreating\":false,\"army_state\":\"regular\",\"army_state_code\":1,\"current_province_id\":" + position
                + ",\"move_target_province_id\":" + target + ",\"route_province_ids\":" + route + "}]}";
        return EffectJson.object(StrictJson.parse(raw.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    @Test void actualRouteAdmissionAndActualArrivalStayDifferent() {
        var move = new Move(1,3); var before = frame(2,"null","[]",10);
        assertEquals(State.MOVING, verify(move,before,frame(2,"3","[2,3]",11)));
        assertEquals(State.ARRIVED, verify(move,before,frame(3,"null","[]",11)));
        assertEquals(State.NOT_OBSERVED, verify(move,before,frame(2,"3","[2,4]",11)));
    }
    @Test void sameProvinceMoveRequiresLaterStationaryRouteClear() {
        var move = new Move(1,2); var before = frame(2,"3","[2,3]",10);
        assertEquals(State.NOT_OBSERVED, verify(move,before,frame(2,"3","[2,3]",11)));
        assertEquals(State.NOT_OBSERVED, verify(move,before,frame(2,"null","[]",10)));
        assertEquals(State.ARRIVED, verify(move,before,frame(2,"null","[]",11)));
    }
    @Test void ownershipCombatAndDateDriftCannotBeAcknowledgedAsMovement() {
        var before = frame(2,"null","[]",10); var after = frame(3,"null","[]",11);
        ((ObjectNode)after.path("player_armies").get(0)).put("owner_character_id",8);
        assertThrows(IllegalArgumentException.class,()->verify(new Move(1,3),before,after));
        var wrongDate=frame(3,"null","[]",11);wrongDate.put("date_raw",53144352);
        assertThrows(IllegalArgumentException.class,()->verify(new Move(1,3),before,wrongDate));
        var combat=frame(3,"null","[]",11);((ObjectNode)combat.path("player_armies").get(0)).put("in_combat",true);
        assertThrows(IllegalArgumentException.class,()->verify(new Move(1,3),before,combat));
    }
}

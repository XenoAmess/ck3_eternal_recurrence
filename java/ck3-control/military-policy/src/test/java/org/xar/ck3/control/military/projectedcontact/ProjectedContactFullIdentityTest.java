package org.xar.ck3.control.military.projectedcontact;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.*;

final class ProjectedContactFullIdentityTest {
    @Test void highBitAndZeroFullCombatIdentitiesSurviveBothSharedConsumersAndRoundtrip() {
        for(int combat:List.of(Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE)) {
            Scope scope=new Scope(BigInteger.valueOf(9),1000,0,81,29829,30,31,30,List.of(21),List.of(combat),Transition.JOIN_EXISTING,combat,0,Side.ATTACKER,false,null,1,List.of(11,0),List.of(21));
            Scope roundtrip=ProjectedContactCodec.decodeScope(StrictJson.parse(StrictJson.canonical(ProjectedContactCodec.encodeScope(scope))));
            assertEquals(scope,roundtrip);assertEquals(List.of(combat),roundtrip.observedTargetCombatIds());
            Capture capture=new Capture("native:9",BigInteger.valueOf(7),BigInteger.valueOf(9),BigInteger.valueOf(3),"episode");
            var selected=assertInstanceOf(Available.class,ProjectedContactPolicy.select(new Snapshot(capture,1000),List.of(new CapturedRow(new QueryKey(0,31,30),capture,roundtrip)),new Request(new QueryKey(0,31,30),30,29829)));
            assertEquals(Transition.JOIN_EXISTING,selected.projection().transition());assertFalse(selected.futureContactAuthorized());
            var invalid=ProjectedContactCodec.encodeScope(scope);invalid.put("selected_current_combat_id",true);
            assertThrows(IllegalArgumentException.class,()->ProjectedContactCodec.decodeScope(invalid));
            var missing=ProjectedContactCodec.encodeScope(scope);missing.remove("selected_current_combat_id");assertThrows(IllegalArgumentException.class,()->ProjectedContactCodec.decodeScope(missing));
        }
        assertThrows(IllegalArgumentException.class,()->new Scope(BigInteger.ONE,1000,0,81,29829,30,31,30,List.of(21),List.of(-1),Transition.JOIN_EXISTING,-1,0,Side.ATTACKER,false,null,1,List.of(11,0),List.of(21)));
    }
}

package org.xar.ck3.control.application.history;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Typed projection DATA domain only; no original Native query, receipt, Root or private source qualification is minted. */
final class DriverReadHistoryObservedActorTest {
    @Test void originalObservedSamplingActorKeepsSignedI32ThroughTypedProjectionAndPublicRoleSerde() {
        for(long id:List.of((long)Integer.MIN_VALUE,-2L,0L,1L,(long)Integer.MAX_VALUE)) {
            Obj internal=result(new IntegerValue(BigInteger.valueOf(id)));
            Obj exposed=internal.with("queried_connection_generation",new Text("18446744073709551615"));
            var roles=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(raw(internal),raw(exposed));
            var actual=new DriverReadHistoryRichMaterial.Projection(DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,raw(internal),roles,List.of(source()));
            assertEquals(internal,DriverJson.object(actual.fullResult().bytes(),RawJson.MAXIMUM_BYTES));
            var retained=DriverReadHistoryRichMaterial.PublicNumbers.fromJson(OpportunityJson.parse(OpportunityJson.encode(roles.toJson())));
            assertEquals(exposed,retained.toPublic(internal));assertEquals(internal,retained.fromPublic(exposed));
            assertEquals(new IntegerValue(BigInteger.valueOf(id)),exposed.get("queried_player_character_id"));
        }
    }
    @Test void absentSentinelWrongTypeAndOutOfNativeRangeRemainRejectedWithoutWideningU64Counters() {
        for(Value bad:List.of(new IntegerValue(BigInteger.valueOf(-1)),new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                new IntegerValue(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),new Text("-2"),new Bool(true),new DecimalValue("1.0"),Nil.INSTANCE)) {
            Obj body=result(bad);var exposed=body.with("queried_connection_generation",new Text("18446744073709551615"));
            var roles=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(raw(body),raw(exposed));
            assertThrows(IllegalArgumentException.class,()->new DriverReadHistoryRichMaterial.Projection(DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,raw(body),roles,List.of(source())));
        }
        Obj negativeCounter=result(new IntegerValue(BigInteger.valueOf(-2))).with("queried_revision",new IntegerValue(BigInteger.valueOf(-2)));
        var exposed=negativeCounter.with("queried_connection_generation",new Text("18446744073709551615"));
        var roles=DriverReadHistoryRichMaterial.PublicNumbers.fromResults(raw(negativeCounter),raw(exposed));
        assertThrows(IllegalArgumentException.class,()->new DriverReadHistoryRichMaterial.Projection(DriverReadHistoryRichMaterial.Kind.ARMY_OBSERVER_SAMPLING,raw(negativeCounter),roles,List.of(source())));
    }
    private static Obj result(Value actor) {
        var counters=new LinkedHashMap<String,Value>();
        for(String flag:List.of("installed","available","capture_enabled","busy","clear_completed"))counters.put(flag,new Bool(false));
        for(String count:List.of("epoch","active_captures","retained_records","qualified_records"))counters.put(count,new IntegerValue(BigInteger.ZERO));
        counters.put("status",new Text("unavailable"));counters.put("readiness",new Text("unavailable"));
        var body=new LinkedHashMap<String,Value>();body.put("step",new Text("query-army-observer-research-sampling-v1"));
        body.put("accepted",new Bool(true));body.put("status",new Text("completed"));body.put("backend_id",new Text("native-headless"));
        body.put("observer_family",new Text("natural_phase"));body.put("army_observer_research_sampling_v1",new Obj(Map.of("natural_phase",new Obj(counters))));
        body.put("queried_snapshot_id",new Text("data-only-snapshot"));body.put("queried_revision",new IntegerValue(BigInteger.ONE));
        body.put("queried_native_revision",new IntegerValue(BigInteger.ONE));body.put("queried_date_raw",new IntegerValue(BigInteger.ZERO));
        body.put("queried_connection_generation",new IntegerValue(new BigInteger("18446744073709551615")));
        body.put("queried_episode_run_id",Nil.INSTANCE);body.put("queried_player_character_id",actor);return new Obj(body);
    }
    private static RawJson raw(Obj body){return new RawJson(OpportunityJson.encode(body));}
    private static ExactRef source(){return new ExactRef("data-only-sampling-source",1,"1".repeat(64));}
}

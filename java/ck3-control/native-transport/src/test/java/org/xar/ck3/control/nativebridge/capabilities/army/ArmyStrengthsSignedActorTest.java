package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Observed actor DATA correction, not old Python negative-ID parity or private scalar eligibility. */
final class ArmyStrengthsSignedActorTest {
    private static ArmyTypes.Context context(int actor) {
        Instant now=Instant.now();var source=new G2Source("signed-actor-data",now.toString(),"source-only",ref());
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(11),BigInteger.valueOf(53144328)),"native:11",BigInteger.valueOf(7),"data-episode");
        return new ArmyTypes.Context(new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),frame,1),source,"data-session",now.plusSeconds(60));
    }
    private static ObjectNode numeric(int actor) {
        var raw=ArmyJson.empty().put("snapshot_id","native:11").put("revision",7).put("native_revision",11).put("date_raw",53144328)
                .put("episode_run_id","data-episode").put("paused",true).put("map_ready",true);
        raw.putObject("played_character").put("character_id",actor).put("alive",true);
        raw.putObject("diagnostics").put("connection_generation",5);raw.putArray("player_armies");raw.putArray("active_wars");return raw;
    }
    private static Snapshot snapshot(int actor){return ArmyStrengthsCodec.snapshot(context(actor),new RawJson(ArmyJson.bytes(numeric(actor))));}
    @Test void actualSnapshotCodecBindingAndCacheKeepSignedObservedActorWithoutAliasing()throws Exception {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}) {
            var actual=snapshot(actor);assertEquals(actor,actual.binding().actorCharacterId());
            var cold=ArmyStrengthsCodec.snapshot(actual.context(),new RawJson(ArmyJson.bytes(ArmyStrengthsCodec.parseValue(actual.original()))));
            assertEquals(actual.binding(),cold.binding());assertEquals(BigInteger.valueOf(actor),ArmyJson.object(ArmyStrengthsCodec.parseValue(actual.original())).get("played_character").get("character_id").bigIntegerValue());
            var read=originalRead(actual);var cache=new ArmyStrengthsCache();cache.publish(actual,read,false);
            assertEquals(actor,cache.forSnapshot(cold,Profile.ORDINARY_CORE_V1).orElseThrow().binding().actorCharacterId());
            int other=actor==0?-2:0;assertTrue(cache.forSnapshot(snapshot(other),Profile.ORDINARY_CORE_V1).isEmpty());
            assertTrue(cache.forSnapshot(actual,Profile.ORDINARY_CORE_V1).isEmpty());
        }
    }
    @Test void missingSentinelWrongJsonTypesAndOutOfSignedRangeRemainRejected() {
        var actual=context(-2);
        var bad=List.of(ArmyJson.empty().put("value",true).get("value"),ArmyJson.empty().put("value",-2.0).get("value"),
                ArmyJson.empty().put("value","-2").get("value"),ArmyJson.empty().putNull("value").get("value"),
                ArmyJson.empty().put("value",-1).get("value"),ArmyJson.empty().put("value",BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)).get("value"),
                ArmyJson.empty().put("value",new BigInteger("4294967294")).get("value"));
        for(JsonNode wrong:bad) {
            var raw=numeric(-2);((ObjectNode)raw.get("played_character")).set("character_id",wrong);
            assertThrows(IllegalArgumentException.class,()->ArmyStrengthsCodec.snapshot(actual,new RawJson(ArmyJson.bytes(raw))));
        }
        var raw=numeric(-2);((ObjectNode)raw.get("played_character")).remove("character_id");
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsCodec.snapshot(actual,new RawJson(ArmyJson.bytes(raw))));
        var valid=snapshot(-2).binding();assertThrows(IllegalArgumentException.class,()->new Binding(valid.machineId(),valid.game(),valid.sessionId(),valid.connectionGeneration(),valid.snapshotId(),valid.publicRevision(),valid.nativeRevision(),valid.dateRaw(),valid.episodeRunId(),-1));
    }
    /** Same exact actor/context request -> native wire DATA -> production decoder -> cache. No live read permit. */
    private static Read originalRead(Snapshot snapshot)throws Exception {
        var context=snapshot.context();var operation=new OperationKey(STEP);var now=Instant.now();
        var request=new PlanningReadRequest(context.before(),context.source(),context.sessionId(),operation,new OpportunityJson.Obj(java.util.Map.of()),context.deadline());
        var evidence=new GuardEvidence(context.before(),context.source(),context.sessionId(),BigInteger.valueOf(5),operation,ref(),ref(),"source-only-data",now,context.deadline());
        var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
        var result=ArmyJson.empty().put("step",STEP).put("accepted",true).put("status","available").put("query_sequence",1)
                .put("backend_id","source-only-data").put("army_strengths_profile","ordinary_core_v1").put("army_observed_phase_coverage","not_requested");result.putArray("army_strengths");
        var response=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","signed-actor-read").put("ok",true);response.set("result",result);
        byte[] packet=NativeWire.packet(ArmyJson.bytes(response));var original=(NativeWire.CommandResult)NativeWire.decode(packet);
        var ack=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),Optional.of(new RawJson(original.result().token().orElseThrow().value())),new RawJson(original.payload().value()),packet);
        var receipt=new PlanningReadReceipt(request,original.requestId(),original.requestId(),guard,guard,ack);
        var query=new Query(Profile.ORDINARY_CORE_V1,Mode.AUTO_CORE,new ArmyTypes.Missing<>(),EntryMode.OBSERVED_PREPARED,EntryMode.OBSERVED_PREPARED);
        return ArmyStrengthsCodec.decode(snapshot,query,false,receipt,new ArmyStrengthsFamilies.Registry());
    }
    private static ExactRef ref(){return new ExactRef("source-only/signed-actor-capability",1,"a".repeat(64));}
}

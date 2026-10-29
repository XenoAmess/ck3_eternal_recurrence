package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerOptionIntent;
import static org.junit.jupiter.api.Assertions.*;

/** Actual contract producer and sole parser, with software packets only; no Root custody or Game qualification. */
final class PrisonerNativeQueriesReplayTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final BigInteger PUBLIC=BigInteger.valueOf(56),NATIVE=BigInteger.valueOf(90);
    private static final ExactRef PRODUCER=new ExactRef("synthetic/native-collection-producer",1,"1".repeat(64));
    private static final G2Source SOURCE=new G2Source("synthetic-prisoner-machine",NOW.toString(),
            "1.20.0.4@sha256:"+CachedSuccession12004.EXE_SHA256,PRODUCER);
    private static final ObservationIdentity BEFORE=new ObservationIdentity(SOURCE.machineId(),
            new GameGeneration(321,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),NATIVE,BigInteger.valueOf(53220000)),
                    "native:90",PUBLIC,"synthetic-prisoner-episode"),1);

    @Test void all64ActualContractsInstallPureReplayWithoutCallingLiveAdmission() throws Exception {
        var calls=new AtomicInteger();var queries=new PrisonerNativeQueries(PRODUCER,(ordinal,request,args)->calls.incrementAndGet());
        assertEquals(64,queries.contracts().size());
        for(int ordinal=0;ordinal<64;ordinal++) {
            var contract=queries.contract(ordinal);assertSame(contract,queries.contracts().get(ordinal));
            assertSame(PRODUCER,contract.sourceRef());assertTrue(contract.hasPureReplay());
            assertEquals(ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,contract.guardMode());
            var request=request(contract,SOURCE);var prepared=contract.prepare(request,"independent-query-"+ordinal);
            assertEquals(PrisonerNativeQueries.step(ordinal),prepared.step());
            assertEquals(StrictJson.object(),StrictJson.parse(prepared.additionalFields().bytes()));
            int before=calls.get();var read=receipt(contract,request,packet(ordinal,false));
            assertArrayEquals(contract.decode(read).bytes(),contract.replay(read).bytes());assertEquals(before,calls.get());
        }
        assertEquals(64,calls.get(),"only current preparation calls current Root admission");
    }
    @Test void ordinalZeroAvailableEmptyCollectionNormalizesTheActualCurrentPlayerFrame() throws Exception {
        var contract=queries().contract(0);var read=receipt(contract,request(contract,SOURCE),packet(0,true));
        var decoded=PrisonerNativeQueries.decode(read,0);assertEquals(PrisonerNativeQueries.CollectionStatus.AVAILABLE,decoded.status());
        assertEquals(List.of(),decoded.prisonerIds());assertTrue(decoded.releaseMaterial().isEmpty());
        var live=contract.decode(read);var replay=contract.replay(read);assertArrayEquals(live.bytes(),replay.bytes());
        var normalized=StrictJson.parse(new RawJson(replay.bytes()).bytes());
        assertEquals(PUBLIC,normalized.get("queried_revision").bigIntegerValue());
        assertEquals(NATIVE,normalized.get("queried_native_revision").bigIntegerValue());
        assertEquals("native:90",normalized.get("queried_snapshot_id").textValue());
        assertEquals(101,normalized.path("player_prisoner_collection").get("played_character_id").longValue());
        assertFalse(normalized.has("queried_release_material_target_character_id"));
    }
    @Test void liveAndPureReplayShareStrictMissingWrongTypeAndCurrentPlayerFailures() throws Exception {
        var contract=queries().contract(0);var request=request(contract,SOURCE);
        var missing=packet(0,true);((ObjectNode)missing.get("player_prisoner_collection")).remove("collection_complete");reject(contract,request,missing);
        var booleanCount=packet(0,true);((ObjectNode)booleanCount.get("player_prisoner_collection")).put("total_count",false);reject(contract,request,booleanCount);
        var floatingCount=packet(0,true);((ObjectNode)floatingCount.get("player_prisoner_collection")).put("returned_count",0.0);reject(contract,request,floatingCount);
        var foreignPlayer=packet(0,true);((ObjectNode)foreignPlayer.get("player_prisoner_collection")).put("played_character_id",202);reject(contract,request,foreignPlayer);
        var nullCount=packet(0,true);((ObjectNode)nullCount.get("player_prisoner_collection")).putNull("total_count");reject(contract,request,nullCount);
    }
    @Test void anotherBuildOrOrdinalCannotAcquireThisReplayContract() throws Exception {
        var contract=queries().contract(0);
        var foreign=new G2Source(SOURCE.machineId(),NOW.toString(),"1.20.0.2",PRODUCER);
        reject(contract,request(contract,foreign),packet(0,true));
        reject(contract,request(contract,SOURCE),packet(1,false));
        var read=receipt(contract,request(contract,SOURCE),packet(0,false));
        assertThrows(IllegalArgumentException.class,()->queries().contract(1).replay(read));
    }
    private static PrisonerNativeQueries queries(){return new PrisonerNativeQueries(PRODUCER,(ordinal,request,args)->{throw new AssertionError("decoding cannot acquire live admission");});}
    private static PlanningReadRequest request(ReadContract<RawJson> contract,G2Source source){
        return new PlanningReadRequest(BEFORE,source,"synthetic-prisoner-session",contract.operation(),
                PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),OptionalLong.empty()),NOW.plusSeconds(30));
    }
    private static ObjectNode packet(int ordinal,boolean available){
        var root=StrictJson.object().put("step",PrisonerNativeQueries.step(ordinal)).put("accepted",true).put("status",available?"available":"unavailable")
                .put("query_sequence",11).put("observation_revision",12).put("snapshot_revision",NATIVE).put("private_build",true)
                .put("read_only",true).put("advertised",false).put("backend_id","native-headless");
        var collection=root.putObject("player_prisoner_collection").put("schema","player-prisoner-collection-private-v1")
                .put("schema_version",1).put("snapshot_revision",NATIVE).put("status",available?"available":"unavailable");
        if(available)collection.putNull("unavailable_reason").put("date_raw",53220000).put("played_character_id",101).put("total_count",0).put("returned_count",0);
        else collection.put("unavailable_reason","source_unavailable").putNull("date_raw").putNull("played_character_id").putNull("total_count").putNull("returned_count");
        collection.put("collection_complete",available).putArray("prisoners");return root;
    }
    private static PlanningReadReceipt receipt(ReadContract<RawJson> contract,PlanningReadRequest request,ObjectNode nativeResult)throws Exception {
        String id="synthetic-independent-read";var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",nativeResult);
        byte[] body=StrictJson.canonical(frame);var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(nativeResult))),new RawJson(body),NativeWire.packet(body));
        var binding=new GuardEvidence(BEFORE,request.source(),request.sessionId(),BigInteger.TWO,contract.operation(),PRODUCER,PRODUCER,"synthetic-authority",NOW,NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(binding,true,true,true,"2".repeat(64));return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static void reject(ReadContract<RawJson> contract,PlanningReadRequest request,ObjectNode nativeResult)throws Exception{
        var read=receipt(contract,request,nativeResult);assertThrows(IllegalArgumentException.class,()->contract.decode(read));assertThrows(IllegalArgumentException.class,()->contract.replay(read));
    }
}

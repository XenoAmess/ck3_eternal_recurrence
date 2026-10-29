package org.xar.ck3.control.nativebridge.capabilities.activity;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.activity.ActivityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.Build;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original Python HOSTED producer fixture -> native envelope -> identical installed live/replay decoder.
 * Synthetic boundary guards are DATA; this test creates no Root lease, catalog qualification or Game. */
final class ActivityHostedReplayTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final String REQUEST="original-hosted-archive";
    @TempDir Path temporary;
    private record Fixture(ActivityNativeContracts.Installation installed,ReadContract<ActivityNativeContracts.Packet> contract,
            PlanningReadRequest request,PlanningReadGuard guard,ObjectNode result,AtomicInteger admissions) { }
    private ExactRef preserve(String name,byte[] bytes)throws Exception {
        Path file=temporary.resolve(name);Files.write(file,bytes);var observed=SharedSourceFiles.observe(file).source();
        return new ExactRef(observed.path(),observed.bytes(),observed.sha256());
    }
    private Fixture fixture()throws Exception {
        JsonNode original=null;
        for(JsonNode candidate:ActivityOriginalProducerTest.originalCases())if("HOSTED".equals(text(candidate,"query")))original=candidate;
        assertNotNull(original,"required actual original HOSTED fixture");
        var payload=(ObjectNode)original.get("payload");
        BigInteger nativeRevision=payload.get("snapshot_revision").bigIntegerValue(),date=payload.get("date_raw").bigIntegerValue(),actor=payload.get("actor_character_id").bigIntegerValue();
        ExactRef source=preserve("hosted-producer-source.txt",new byte[]{'h','o','s','t','e','d'});
        ObjectNode hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",123).put("connection_generation",1)
                .put("bridge_version","original-hosted-fixture").put("expected_ck3_sha256",Build.CROZIER4.sha256())
                .put("game_adapter_id","ck3-"+Build.CROZIER4.version()+"-msvc-x64").put("game_adapter_status","ready").put("ck3_build_match",true);
        hello.putArray("capabilities");ExactRef cap=preserve("original-hello.bin",NativeWire.packet(raw(hello).bytes()));
        var identity=new ObservationIdentity("synthetic-hosted-machine",new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("134000000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(actor,nativeRevision,date),"hosted-original-frame",BigInteger.valueOf(41),"hosted-original-episode"),1);
        var sourceFrame=new G2Source(identity.machineId(),NOW.toString(),"1.20.0.4",source);var admissions=new AtomicInteger();
        var installed=new ActivityNativeContracts.Installation(Arrays.stream(ActivityNativeContracts.Query.values()).map(query->new ActivityNativeContracts.Source(query,source)).toList(),(query,request)->admissions.incrementAndGet());
        var contract=installed.contract(ActivityNativeContracts.Query.HOSTED);
        var request=new PlanningReadRequest(identity,sourceFrame,"hosted-original-session",contract.operation(),new OpportunityJson.Obj(java.util.Map.of()),NOW.plusSeconds(30));
        var guard=new PlanningReadGuard(new GuardEvidence(identity,sourceFrame,request.sessionId(),BigInteger.ONE,contract.operation(),source,cap,"synthetic-data-boundary",NOW,request.deadline()),true,true,true,"b".repeat(64));
        ObjectNode result=StrictJson.object().put("step",contract.operation().value()).put("accepted",true).put("status",text(original,"status"))
                .put("private_build",true).put("read_only",true).put("advertised",false).put("backend_id","native-headless");
        result.set(ActivityNativeContracts.Query.HOSTED.payloadKey(),payload);
        return new Fixture(installed,contract,request,guard,result,admissions);
    }
    private static PlanningReadReceipt receipt(Fixture f,ObjectNode result,String contractId)throws Exception {
        ObjectNode returned=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",REQUEST).put("ok",true);returned.set("result",result);
        var ack=new NativeActionPort.AckReceived(REQUEST,true,Optional.of(raw(result)),raw(returned),NativeWire.packet(raw(returned).bytes()));
        return new PlanningReadReceipt(f.request(),contractId,REQUEST,f.guard(),f.guard(),ack);
    }
    @Test void actualHostedProducerReplaysWithoutAdmissionPreparationOrAnotherRead()throws Exception {
        var f=fixture();assertSame(f.contract(),f.installed().contract(ActivityNativeContracts.Query.HOSTED));assertTrue(f.contract().hasPureReplay());
        for(var query:ActivityNativeContracts.Query.values())if(query!=ActivityNativeContracts.Query.HOSTED)assertFalse(f.installed().contract(query).hasPureReplay());
        f.contract().prepare(f.request(),REQUEST);assertEquals(1,f.admissions().get());
        var retained=receipt(f,f.result(),f.contract().contractId());var live=f.contract().decode(retained);var replay=f.contract().replay(retained);
        assertSame(retained,replay.receipt());assertInstanceOf(ActivityPayload.Hosted.class,replay.payload());
        assertEquals(live,replay,"actual Root retained Known value must equal its complete pure replay");
        assertEquals(live.hashCode(),replay.hashCode());
        assertEquals(StrictJson.parse(ActivityNativeContracts.normalizedForPublic(live).bytes()),StrictJson.parse(ActivityNativeContracts.normalizedForPublic(replay).bytes()));
        assertEquals(1,f.admissions().get(),"archival replay must not call live admission/prepare");
    }
    @Test void archivalHostedDecoderKeepsOriginalEnvelopeAndContractGuards()throws Exception {
        var f=fixture();var wrong=f.result().deepCopy();wrong.put("read_only",false);
        var malformed=receipt(f,wrong,f.contract().contractId());assertThrows(IllegalArgumentException.class,()->f.contract().replay(malformed));
        var detached=receipt(f,f.result(),"activity/native/start_inputs");assertThrows(IllegalArgumentException.class,()->f.contract().replay(detached));
        assertEquals(0,f.admissions().get(),"replay refusal must not invoke a live provider");
    }
}

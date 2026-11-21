package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import org.xar.ck3.control.application.action.FullSnapshotClockControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** DATA and software packet-port tests only. No Managed owner, actual Native call, process, exit, Full receipt or active lease is created. */
final class Current131SourceAndSentinelDataTest {
    private static final ExactCk3Build FULL=ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final ExactCk3Build CORE=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final CoreFrame.Prefix LIVE=new CoreFrame.Prefix(
            53179344,3,true,0,true,true,0x81000002,true);

    private static final ExactRef SOURCE131=new ExactRef("software-no-dll-read131",12389376L,"060a22216f6d7642ce2ee392dc7ffffbd17f1bb8d2029cd79eb17e47599b23f4");
    private static final ExactRef SOURCE125=new ExactRef("software-no-dll-read125",12389376L,
            "863b4893611d1101e4f5e7f82b43f4fab2c7259bd0db6c0065a59a9a016c12f7");
    private static final ExactRef SOURCE112=new ExactRef("software-no-dll-read112",12381696L,
            "2634e6408331426ab546f59c5efa62f3d6b257bc0f6a583cbcec2ed07f7009e6");

    @Test void corrected131125And112KeepTheirExactSourcePairs() {
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE131));
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE125));
        assertTrue(FullSnapshotClockControl.isMappedSave112Bridge(SOURCE112));
        for(var bad:List.of(
                new ExactRef(SOURCE131.path(),12389375L,SOURCE131.sha256()),
                new ExactRef("crossed112size131sha",SOURCE112.bytes(),SOURCE131.sha256()),
                new ExactRef("crossed131size112sha",SOURCE131.bytes(),SOURCE112.sha256()),
                new ExactRef("wrong-sha",SOURCE125.bytes(),"0".repeat(64)),
                new ExactRef("independent114",12382720L,"42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a"),
                new ExactRef("withdrawn111",13792256L,"803da0130362c58bf8ba98c9e8bd41c3046c7dba4b12a0fa2fbbb29c6073eaa0")))
            assertFalse(FullSnapshotClockControl.isMappedSave112Bridge(bad));
    }

    @Test void mapped131SaveKeepsCurrentTupleOriginalRevisionAndNanosecondCallerDeadline() {
        var revision=new BigInteger("9007199254740993");
        var deadline=Instant.parse("2030-01-02T03:04:05.123456789Z");
        var request=FullSnapshotClockControl.requestMappedSave112(
                SOURCE131,"native:"+revision,revision,deadline);
        var fields=StrictJson.parse(request.additionalFields().bytes(),1<<20).path("full_snapshot_clock_control");
        assertEquals("save-checkpoint",request.step());
        assertEquals(FULL.version(),fields.path("game_version").textValue());
        assertEquals(FULL.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(FULL.coreFullBackend(),fields.path("backend").textValue());
        assertEquals(revision,fields.path("native_revision").bigIntegerValue());
        assertEquals(deadline.toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.request(
                FULL,"save-checkpoint","native:1",BigInteger.ONE,deadline));
    }

    @Test void matching131HelloStillCannotReplaceActualManagedCustody()throws Exception {
        var source=new Replay();
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        String slash=Character.toString(92);
        var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"source131-software",
                "source131-software",game,"source131-software-session","source131-software",
                FULL.executableSha256(),FULL.coreFrameAdapterId());
        try(var actual=new NativeGameTransport(source,config,16,16,List.of(),Clock.systemUTC())) {
            assertThrows(NullPointerException.class,()->actual.bindFull112Source(null));
            var read=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    actual.readFreshFullState(Instant.now().plusSeconds(30)));
            var rejected=assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,read.dispatch());
            assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,rejected.proof().stage());
            assertEquals(0,rejected.proof().requestBytesWritten());
            assertTrue(read.reason().contains("actual Managed source is not bound"),read::reason);
            assertEquals(0,source.writes);
            assertTrue(actual.latestAcceptedSnapshotRevision().isEmpty());
        }
    }

    @Test void admissionFixDoesNotQualifyDifferentSpeedOrBorrowIndependent114Save()throws Exception {
        var before=new RawJson(StrictJson.canonical(StrictJson.object().put("speed",3)));
        assertDoesNotThrow(()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-3",before));
        assertThrows(IOException.class,()->NativeGameTransport.requireCurrent112SpeedData(FULL,"set-speed-4",before));
        var independent=new ExactRef("independent114",12382720L,
                "42cecc8a69bc5f6142e10b8d5bb044fab9a63d26bcfd3a01a6de25501f4a604a");
        assertThrows(IllegalArgumentException.class,()->FullSnapshotClockControl.requestMappedSave112(
                independent,"native:1",BigInteger.ONE,Instant.parse("2030-01-02T03:04:05Z")));
    }

    @Test void campaignCapUsesTheProductionRewriteAndNeverFallsBackToPolled() {
        var request=planning(Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP));
        var original=command(request);var cap=cap(request);
        var prepared=AdvanceRewrite.rewrite(request,original,"life-advance",cap);
        var plan=AdvancePlan.decode(prepared);
        assertEquals(AdvancePlan.ClockMode.CAMPAIGN_SENTINEL,plan.clockMode());
        assertEquals(30,plan.horizonDays());assertEquals(original.deadline(),prepared.deadline());
        assertEquals(original.actionId(),prepared.actionId());assertEquals(original.origin(),prepared.origin());
        assertEquals(original.claims(),prepared.claims());assertEquals(cap.boundaryDateRaw(),plan.campaignDeadline().orElseThrow().boundaryDateRaw());
        assertEquals(original.deadline(),Instant.parse("2030-01-02T03:04:05.123456789Z"));
    }

    @Test void eachMissingNativeSentinelCapabilityRejectsTheCampaignRewrite() {
        var all=Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP);
        for(String missing:all) {
            var reduced=new HashSet<>(all);reduced.remove(missing);var request=planning(reduced);
            assertFalse(ClockStatusRead.available(reduced));
            assertThrows(IllegalArgumentException.class,()->AdvanceRewrite.rewrite(request,command(request),"life-advance",cap(request)),missing);
        }
    }

    @Test void currentArmKeepsCanonicalDateAndStrictGenerationStatusData() {
        var request=planning(Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP));
        var plan=AdvancePlan.decode(AdvanceRewrite.rewrite(request,command(request),"life-advance",cap(request)));
        var arm=FullSnapshotDateSentinelArm.request(FULL,plan.armStep(),request.before().frame().snapshotId(),
                request.before().frame().identity().nativeRevision(),request.deadline());
        assertEquals(ClockStatusRead.ARM_CAP,arm.requiredCapability().orElseThrow());
        var fields=StrictJson.parse(arm.additionalFields().bytes()).path("date_sentinel_arm");
        assertEquals(8,fields.size());assertEquals(FULL.coreFullAdapterId(),fields.path("adapter_id").textValue());
        assertEquals(FULL.coreFullBackend(),fields.path("backend").textValue());
        assertEquals(request.deadline().toEpochMilli(),fields.path("deadline_unix_ms").longValue());
        assertEquals(request.before().frame().identity().nativeRevision(),fields.path("native_revision").bigIntegerValue());
        var spec=AdvancePrimitives.armSpec(arm.step());assertEquals(plan.startingDateRaw().intValueExact(),spec.startingDateRaw());
        assertEquals(plan.targetDateRaw().intValueExact(),spec.targetDateRaw());assertTrue(spec.armyIds().isEmpty());
        var slot=status();var decoded=SentinelObservation.decode(slot);assertEquals("7",decoded.generation().decimal());
        assertEquals(BigInteger.valueOf(7),AdvancePrimitives.cancelGeneration(ClockStatusRead.CANCEL_PREFIX+"7"));
        var missing=slot.deepCopy();missing.remove("generation");assertThrows(IllegalArgumentException.class,()->SentinelObservation.decode(missing));
        var wrongType=slot.deepCopy().put("generation","7");assertThrows(IllegalArgumentException.class,()->SentinelObservation.decode(wrongType));
        var changed=slot.deepCopy().put("generation",8);assertNotEquals(decoded,SentinelObservation.decode(changed));
        // A different well-formed generation is DATA, never proof of the original armed generation.
        assertFalse(AdvancePrimitives.statusValues(SentinelObservation.decode(changed)).contains(
                new ExpectedText(new FieldKey("sentinel.generation"),"7")));
    }

    @Test @EnabledIfSystemProperty(named="current131.actual54.stdout",matches=".+")
    void retiredActual54FullAndLastPlanReachTheStrictCampaignRewrite()throws Exception {
        var out=Files.readAllLines(Path.of(System.getProperty("current131.actual54.stdout")));
        ActionCommand original=null;
        for(String line:out)if(line.startsWith("{")) {
            var row=StrictJson.parse(line.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var candidate=row.path("last_plan").path("final_plan").path("command");
            if(candidate.isObject())original=ActionCodec.decodeCommand(StrictJson.canonical(candidate));
        }
        assertNotNull(original,"actual54 must retain its original selected command");
        String fullPath=System.getProperty("current131.actual54.full");assertNotNull(fullPath);
        var full=StrictJson.parse(Files.readAllBytes(Path.of(fullPath)));
        assertEquals("ck3_1210_full_state_v1",full.path("schema").textValue());
        assertEquals(FULL.version(),full.path("game_version").textValue());
        assertEquals(FULL.executableSha256(),full.path("executable_sha256").textValue().toLowerCase(java.util.Locale.ROOT));
        assertEquals(FULL.coreFullBackend(),full.path("backend").textValue());
        assertEquals(FULL.coreFullAdapterId(),full.path("adapter_id").textValue());
        assertEquals(original.before().frame().identity().dateRaw(),full.path("date_raw").bigIntegerValue());
        assertEquals(original.before().frame().identity().player(),full.path("played_character").path("character_id").bigIntegerValue());
        // Retired Full semantic DATA and the actual last-plan identity are inspected independently;
        // no fresh Received, Managed source, current occurrence or expired request is revived.
        var projection=((com.fasterxml.jackson.databind.node.ObjectNode)full).deepCopy();
        projection.put("snapshot_id",original.before().frame().snapshotId()).put("revision",original.before().frame().revision())
                .put("native_revision",original.before().frame().identity().nativeRevision()).put("episode_run_id",original.before().frame().episodeRunId());
        projection.putObject("diagnostics"); // Empty history uses no connection diagnostic fields; retired Full bytes stay unchanged.
        var observation=new PlanningObservation((org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj)DriverJson.fromNode(projection),List.of(),
                Set.of(new OperationKey("life-advance"),new OperationKey("set-speed-1"),new OperationKey("set-speed-5")),
                Set.of(ClockStatusRead.ARM_CAP,ClockStatusRead.STATUS_CAP,ClockStatusRead.CANCEL_CAP),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        var request=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),observation);
        var rewritten=AdvanceRewrite.rewrite(request,original,"life-advance",cap(request));
        assertEquals(AdvancePlan.ClockMode.CAMPAIGN_SENTINEL,AdvancePlan.decode(rewritten).clockMode());
        assertEquals(original.deadline(),rewritten.deadline());assertEquals(original.actionId(),rewritten.actionId());
    }

    private static PlanningRequest planning(Set<String> capabilities) {
        var date=BigInteger.valueOf(53179344);var revision=BigInteger.ONE;
        var before=new ObservationIdentity("software-current131",new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993"))),
                new ProposalFrame(new Frame(BigInteger.valueOf(31254),revision,date),"native:1",revision,"software-current131-episode"),1);
        var source=new G2Source(before.machineId(),"2030-01-02T03:00:00Z",FULL.executableSha256(),SOURCE131);
        var row=StrictJson.object().put("date_raw",date).put("paused",true).put("map_ready",true).put("speed",5);
        row.put("revision",1).put("native_revision",1).put("snapshot_id","native:1").put("episode_run_id","software-current131-episode");
        row.putObject("played_character").put("character_id",31254).put("alive",true);
        row.putArray("player_armies");row.putArray("active_wars");
        row.putObject("diagnostics"); // Empty software projection holder; no query history or Native diagnostic is manufactured.
        var observation=new PlanningObservation((org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj)DriverJson.fromNode(row),List.of(),
                Set.of(new OperationKey("life-advance"),new OperationKey("set-speed-1"),new OperationKey("set-speed-5")),capabilities,
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(before,source,"software-current131-session",Instant.parse("2030-01-02T03:04:05.123456789Z"),observation);
    }
    private static ActionCommand command(PlanningRequest request) {
        return new ActionCommand("software-current131-campaign",request.before(),request.source(),request.sessionId(),new OperationKey("life-advance"),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1,request.before(),request.source(),AdvancePlan.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("paused"),true))),
                new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
    }
    private static CampaignDeadline.Cap cap(PlanningRequest request) {
        var start=request.before().frame().identity().dateRaw();var requested=start.add(AdvancePlan.DAY);
        return new CampaignDeadline.Cap("software-current131-campaign",CampaignDeadline.CALENDAR_PROFILE,start,requested,
                start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(31))),start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(365))),requested,CampaignDeadline.Status.ADVANCE);
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode status() {
        var row=StrictJson.object().put("state","armed").put("generation",7).put("starting_date_raw",53179344).put("target_date_raw",53180064)
                .put("last_observed_date_raw",53179344).put("trigger_date_raw",0).put("speed",5).put("mode","terminal_or_sentinel")
                .put("army_count",0).put("combat_count",0).put("completed_daily_ticks",0).put("intermediate_pause_count",0)
                .put("trigger_flags",0).put("signed_date_delta_from_target_raw",-720).put("overshoot_days",-1)
                .put("pause_wrapper_called",false).put("pause_observed",false).put("terminal_observed",false).put("abnormal",false);
        row.putArray("trigger_reasons");return row;
    }

    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int writes;boolean closed;
        Replay()throws IOException {
            var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42)
                    .put("connection_generation",1).put("bridge_version","source131-software")
                    .put("expected_ck3_version",FULL.version()).put("expected_ck3_sha256",FULL.executableSha256())
                    .put("game_adapter_id",FULL.coreFullAdapterId()).put("game_adapter_status","ready")
                    .put("ck3_build_match",true);
            row.putArray("capabilities").add(CoreFrame.CAPABILITY).add(NativeFreshSnapshotPort.CAPABILITY)
                    .add("game.state.snapshot").add("game.command.save-checkpoint")
                    .add(CoreApplicationExit.CAPABILITY);
            packets.add(NativeWire.packet(StrictJson.canonical(row)));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("software endpoint closed");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {
            verify();if(packets.isEmpty())throw new IOException("software packet absent");return packets.removeFirst();
        }
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            writes++;throw new IOException("unbound131 DATA must not write a Full query or command");
        }
        @Override public void close(){closed=true;}
    }
}

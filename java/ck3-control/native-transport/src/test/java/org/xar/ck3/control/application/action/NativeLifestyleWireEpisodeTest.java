package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.effects.NativeGovernanceEffects;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;

/** Source-shaped Native63 ABI vectors through real Java producers/consumers. No Game, writer or action is available. */
final class NativeLifestyleWireEpisodeTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186", SESSION="memory-life-episode";
    private static final String EXE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final Instant NOW=Instant.parse("2026-10-29T20:00:00Z"), DEADLINE=NOW.plusSeconds(30);
    private static final ExactRef REF=new ExactRef("D:/test-memory/life-native63-source.json",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source(MACHINE,NOW.toString(),"1.20.0.4",REF);
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static ObservationIdentity identity(String episode,long actor,GameGeneration game,long revision,long publicRevision){
        return new ObservationIdentity(MACHINE,game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(revision),BigInteger.valueOf(53144328)),
                "public:"+publicRevision,BigInteger.valueOf(publicRevision),episode),1);
    }
    private static GovernancePlanningReads definitions(){return new GovernancePlanningReads(new GovernancePlanningReads.Sources(REF,REF),"1.20.0.4",EXE);}
    private static PlanningReadRequest request(ObservationIdentity identity,ReadContract<?> contract){
        return new PlanningReadRequest(identity,SOURCE,SESSION,contract.operation(),new Obj(Map.of()),DEADLINE);
    }
    private static String queryWire(ObservationIdentity identity){var c=definitions().formal();return StrictJson.text(StrictJson.parse(c.prepare(request(identity,c),"wire-identity").additionalFields().bytes()).get("episode_run_id"));}
    private static PlanningReadReceipt receipt(PlanningReadRequest request,String contract,String id,ObjectNode result)throws java.io.IOException{
        var full=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);full.set("result",result);
        byte[] raw=StrictJson.canonical(full);var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(raw),NativeWire.packet(raw));
        var basis=new GuardEvidence(request.before(),SOURCE,SESSION,BigInteger.valueOf(5),request.operation(),REF,REF,"software-native63-ABI",NOW,DEADLINE);
        var guard=new PlanningReadGuard(basis,true,true,true,"b".repeat(64));return new PlanningReadReceipt(request,contract,id,guard,guard,ack);
    }
    private static ObjectNode nativeLife(PlanningReadRequest request,String episode){
        var actual=request.before().frame().identity();var rev=actual.nativeRevision();
        var result=StrictJson.object().put("step",request.operation().value()).put("private_build",true).put("advertised",false)
                .put("status","available").put("episode_run_id",episode).put("formal_precondition_status","ready");
        var snapshot=result.putObject("snapshot").put("private_build",true).put("advertised",false).put("status","available")
                .put("snapshot_id","native:"+rev).put("public_revision",rev).put("native_revision",rev).put("proof_epoch",rev)
                .put("date_raw",actual.dateRaw()).put("player_character_id",actual.player());
        snapshot.putObject("current_focus").put("presence","absent");snapshot.putObject("current_lifestyle_progress").put("presence","absent");
        snapshot.putArray("owned_perk_keys");snapshot.putObject("actor_traits").put("status","available").putArray("observed_keys");
        for(String key:List.of("legal_focus_candidates","legal_perk_candidates"))snapshot.putObject(key).put("status","unavailable").put("reason","not_requested").putArray("items");
        var readiness=snapshot.putObject("readiness");for(String key:List.of("current_focus_ready","lifestyle_progress_ready","owned_perks_ready","same_frame_ready"))readiness.put(key,true);
        readiness.put("legal_focus_candidates_ready",false).put("legal_perk_candidates_ready",false);return result;
    }
    private static ObjectNode nativeFocus(PlanningReadRequest request,String episode){
        var focus=StrictJson.object().put("step",GovernancePlanningReads.MARTIAL).put("private_build",true).put("advertised",false)
                .put("status","observed_native_legal").put("read_only",true).put("policy_scoped",true)
                .put("episode_run_id",episode).put("snapshot_id","native:"+request.before().frame().identity().nativeRevision())
                .put("target_key","martial_authority_focus").put("native_legal",true).put("scanned_database_rows",20).put("target_lifestyle_key","martial_lifestyle");
        focus.putObject("target_lifestyle_progress").put("presence","present").put("source","exact_native_getters").put("xp_total_raw",0)
                .put("xp_within_level_raw",0).put("xp_per_level",1000).put("unspent_perk_points",0).put("used_perk_points",0);return focus;
    }
    private static void nativeAbi(NativeRequest prepared,ObservationIdentity actual,String field)throws java.io.IOException{
        var fields=StrictJson.parse(prepared.additionalFields().bytes());String episode=StrictJson.text(fields.get(field));
        String prefix="native-"+actual.frame().identity().player()+"-";
        assertTrue(episode.startsWith(prefix),()->"Native63 rejects episode outside actual actor prefix: "+episode);
        assertTrue(episode.getBytes(StandardCharsets.UTF_8).length<64,"Native63 fixed episode capacity");
        assertEquals(actual.frame().identity().player(),fields.get("expected_player_character_id").bigIntegerValue());
        assertEquals(actual.frame().identity().dateRaw(),fields.get("expected_date_raw").bigIntegerValue());
        assertEquals("native:"+actual.frame().identity().nativeRevision(),fields.get("expected_snapshot_id").textValue());
        byte[] packet=NativeWire.execute("native63-shaped",prepared.step(),actual.frame().identity().nativeRevision(),prepared.additionalFields().bytes());
        var body=StrictJson.parse(java.util.Arrays.copyOfRange(packet,4,packet.length));
        assertEquals(actual.frame().identity().nativeRevision(),body.get("expected_revision").bigIntegerValue());
    }
    @Test void logicalEpisodesMapToBoundedNativeActorWireAndStrictlyDecodeToTheirOriginalLogicalIdentity()throws Exception{
        var d=definitions();
        for(String logical:List.of("resume63_vanilla_ordinary01","native-73-already-logical","native-74-foreign-looking-logical","root/long/"+"x".repeat(180))){
            var actual=identity(logical,73,GAME,40,100);String wire=queryWire(actual);assertNotEquals(logical,wire);
            for(var contract:List.of(d.formal(),d.state(),d.focus("martial_authority_focus"),d.focus("stewardship_wealth_focus"))){
                var r=request(actual,contract);var prepared=contract.prepare(r,"life-wire");nativeAbi(prepared,actual,"episode_run_id");
                assertEquals(wire,StrictJson.text(StrictJson.parse(prepared.additionalFields().bytes()).get("episode_run_id")));
            }
            var r=request(actual,d.formal());var original=nativeLife(r,wire);byte[] unchanged=StrictJson.canonical(original);
            var observed=d.formal().decode(receipt(r,d.formal().contractId(),"life-normalize",original));
            assertEquals(new Text(logical),observed.get("episode_run_id"));assertEquals(new Text(logical),object(observed.get("snapshot"),"snapshot").get("episode_run_id"));
            assertArrayEquals(unchanged,StrictJson.canonical(original));assertEquals(observed,d.formal().replay(receipt(r,d.formal().contractId(),"life-normalize",original)));
            for(String foreign:List.of(queryWire(identity(logical+"-foreign",73,GAME,40,100)),queryWire(identity(logical,74,GAME,40,100)))){
                assertThrows(IllegalArgumentException.class,()->d.formal().decode(receipt(r,d.formal().contractId(),"life-crossed",nativeLife(r,foreign))));
            }
        }
        var first=identity("root-a",73,GAME,40,100);String wire=queryWire(first);
        assertNotEquals(wire,queryWire(identity("root-b",73,GAME,40,100)));assertNotEquals(wire,queryWire(identity("root-a",74,GAME,40,100)));
        assertNotEquals(wire,queryWire(identity("root-a",73,new GameGeneration(43,GAME.creationFiletime()),40,100)));
        assertEquals(wire,queryWire(identity("root-a",73,GAME,41,101)),"wire episode must remain stable across observation revisions");
    }
    private static ActionCommand focusCommand(ObservationIdentity before,Obj query){
        var args=new Obj(Map.of("target_key",new Text("martial_authority_focus"),"target_lifestyle_key",new Text("martial_lifestyle"),"original_query",query,"decision",new Obj(Map.of())));
        return new ActionCommand("life-wire-action",before,SOURCE,SESSION,new OperationKey(GovernanceActionPreparation.FOCUS),args,
                new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,before,SOURCE,"xar.java.governance-independent-effect/v1",List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true))),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
    }
    private static Obj focusQuery(ObservationIdentity before,String wire){
        var d=definitions();var r=request(before,d.state());var state=GovernancePlanningReads.life(nativeLife(r,wire),r,GovernancePlanningReads.STATE);
        var focus=GovernancePlanningReads.focus(nativeFocus(r,wire),r,GovernancePlanningReads.MARTIAL);
        return object(parse(StrictJson.canonical(GovernancePlanningReads.combine(state,focus))),"composed actual query");
    }
    @Test void actionPreparationUsesTheSameWireAndDoesNotFoldForeignLogicalQueryIdentity()throws Exception{
        var before=identity("resume63_vanilla_ordinary01",73,GAME,40,100);String wire=queryWire(before);
        var query=focusQuery(before,wire);var command=focusCommand(before,query);
        var preparation=new GovernanceActionPreparation("1.20.0.4",EXE,(same,c,id)->{throw new AssertionError("no Council refresh");},(same,c)->{throw new AssertionError("no writer admission");});
        var actual=preparation.prepare(command,"life-action-wire");nativeAbi(actual,before,"expected_episode_run_id");
        assertEquals(wire,StrictJson.text(StrictJson.parse(actual.additionalFields().bytes()).get("expected_episode_run_id")));
        assertEquals(actual.additionalFields(),GovernanceActionPreparation.lifestyleFields(command));
        var foreign=identity("another-root-episode",73,GAME,40,100);
        assertThrows(IllegalArgumentException.class,()->preparation.prepare(focusCommand(foreign,query),"crossed-logical"));
        assertThrows(IllegalArgumentException.class,()->focusQuery(before,queryWire(foreign)));
    }

    /** Pure archived domain replay only: the injected preparation verifier grants no writer or live submit authority. */
    @Test void archivedEffectUsesStrictWireAckAndReceiptButPreservesLogicalCompatibleHistory()throws Exception{
        String logical="resume63_vanilla_ordinary01";
        var before=identity(logical,73,GAME,40,100);String wire=queryWire(before);
        assertArchivedEffect(logical,wire,wire,logical,false);
        String foreign=queryWire(identity("another-root-episode",73,GAME,40,100));
        assertArchivedEffect(logical,foreign,wire,logical,true);
        assertArchivedEffect(logical,wire,foreign,logical,true);
        assertArchivedEffect(logical,logical,wire,logical,true);
        assertArchivedEffect(logical,wire,logical,logical,true);
        assertArchivedEffect(logical,wire,wire,wire,true);
    }
    private static void assertArchivedEffect(String logical,String ackEpisode,String receiptEpisode,String compatibleEpisode,boolean reject)throws Exception{
        var archive=new MemoryArchive();var before=frame(identity(logical,73,GAME,40,100),NOW,archive);
        var after=frame(identity(logical,73,GAME,41,101),NOW.plusSeconds(2),archive);
        var command=focusCommand(before.identity(),focusQuery(before.identity(),queryWire(before.identity())));
        var prepared=new NativeRequest(command.operation().value(),Optional.empty(),GovernanceActionPreparation.lifestyleFields(command));
        var guard=new GuardEvidence(before.identity(),SOURCE,SESSION,BigInteger.valueOf(5),command.operation(),before.originalEvidence(),REF,"software-life-effect",NOW,DEADLINE);
        var attempt=new ActionState.Attempt("life-original-submit",NOW.plusSeconds(1),guard,prepared);
        var ackResult=StrictJson.object().put("step",command.operation().value()).put("private_build",true).put("advertised",false)
                .put("status","submitted_verification_pending").put("verification_pending",true).put("action_request_id",attempt.requestId())
                .put("target_key","martial_authority_focus").put("pre_snapshot_id","native:40").put("episode_run_id",ackEpisode)
                .put("pre_public_revision",40).put("failure_class","none").put("rejection_reason","");
        var dispatch=ack(attempt.requestId(),ackResult);
        var contracts=NativeGovernanceEffects.readContracts(REF,REF,REF);var contract=contracts.lifestyle();
        var fields=new Obj(Map.of("action_request_id",new Text(attempt.requestId()),"expected_snapshot_id",new Text("native:41"),
                "expected_episode_run_id",new Text(queryWire(after.identity())),"expected_date_raw",new IntegerValue(BigInteger.valueOf(53144328)),
                "expected_player_character_id",new IntegerValue(BigInteger.valueOf(73))));
        var request=new PlanningReadRequest(after.identity(),SOURCE,SESSION,contract.operation(),fields,DEADLINE);
        var result=StrictJson.object().put("step",contract.operation().value()).put("private_build",true).put("advertised",false)
                .put("status","applied").put("action_request_id",attempt.requestId()).put("post_snapshot_id","native:41")
                .put("episode_run_id",receiptEpisode).put("post_public_revision",41).put("post_target_perk_owned",false)
                .put("post_has_current_focus",true).put("post_current_focus_key","martial_authority_focus").put("postcondition_verified",true).put("reason","");
        var readAck=ack("life-independent-receipt",result);
        var binding=new GuardEvidence(after.identity(),SOURCE,SESSION,BigInteger.valueOf(5),contract.operation(),after.originalEvidence(),REF,"software-life-effect",after.observedAt(),DEADLINE);
        var readGuard=new PlanningReadGuard(binding,true,true,true,after.fullBindingSha256());
        var read=new PlanningReadReceipt(request,contract.contractId(),readAck.requestId(),readGuard,readGuard,readAck);
        archive.preserve(readAck);archive.preserveRead(read);
        var compatible=result.deepCopy().put("kind","focus").put("target_key","martial_authority_focus").put("post_date_raw",53144328).put("episode_run_id",compatibleEpisode);
        var pair=new NativeEffectSnapshots.Pair(before,after);
        var basis=NativeEffectEvidence.preserve(command,attempt,pair,List.of(read),new RawJson(StrictJson.canonical(compatible)),archive);
        var actual=List.<ExpectedValue>of(new ExpectedText(new FieldKey("lifestyle.target_key"),"martial_authority_focus"),
                new ExpectedBoolean(new FieldKey("lifestyle.has_current_focus"),true),new ExpectedText(new FieldKey("lifestyle.current_focus_key"),"martial_authority_focus"),
                new ExpectedBoolean(new FieldKey("native.gameplay_verified"),true));
        var observation=new ActionState.EffectObservation(after.identity(),SOURCE,SESSION,NativeGovernanceEffects.SCHEMA,actual,read.requestId(),after.observedAt(),after.originalEvidence(),List.of(basis));
        var settled=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,dispatch,new ActionState.Applied(observation)));
        var verifier=NativeGovernanceEffects.archivedVerifier(command.operation(),REF,(original,ar)->{
            if(original.equals(NativeEffectEvidence.basis(before)))return before;
            assertEquals(NativeEffectEvidence.basis(after),original);return after;
        },contracts,(c,a,originals,ar)->assertTrue(originals.isEmpty(),"this narrow archived domain seam has no live preparation authority"));
        if(reject)assertThrows(IllegalArgumentException.class,()->verifier.verifier().verify(null,settled,archive));
        else assertDoesNotThrow(()->verifier.verifier().verify(null,settled,archive));
        assertEquals(new Text(receiptEpisode),object(parse(readAck.originalResultToken().orElseThrow().bytes()),"raw receipt").get("episode_run_id"));
        assertEquals(new Text(ackEpisode),object(parse(dispatch.originalResultToken().orElseThrow().bytes()),"raw ACK").get("episode_run_id"));
    }
    private static NativeActionPort.AckReceived ack(String id,ObjectNode result)throws java.io.IOException{
        var full=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);full.set("result",result);
        byte[] raw=StrictJson.canonical(full);return new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(raw),NativeWire.packet(raw));
    }
    private static Complete frame(ObservationIdentity id,Instant at,MemoryArchive archive)throws java.io.IOException{
        String logical=id.frame().episodeRunId();var actor=id.frame().identity().player();var revision=id.frame().identity().nativeRevision();
        byte[] wire=("{\"format_version\":2,\"pipe_name\":\"memory-life\",\"bridge_pid\":42,\"episode_character_id\":"+actor+",\"episode_run_id\":\""+logical+"\",\"last_checkpoint\":null,\"command_history\":[],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":{\"campaign_id\":\"original\",\"anchor\":{\"character_id\":"+actor+"}},\"rollback_war_failures\":[]}").getBytes(StandardCharsets.UTF_8);
        var full=archive.preserveMaterial(new RawJson(wire));var known=DriverFactsRepository.imported(full,wire,3,7,GAME,new Obj(Map.of()));
        byte[] state=("{\"paused\":true,\"map_ready\":true,\"speed\":3,\"date_raw\":53144328,\"played_character\":{\"character_id\":"+actor+",\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal\":false,\"one_life_terminal_reason\":null,\"episode_identity_pending\":false,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}").getBytes(StandardCharsets.UTF_8);
        var packet=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","memory-native-"+revision).put("revision",revision);packet.set("state",StrictJson.parse(state));
        var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE,GAME,BigInteger.valueOf(5),SESSION),"memory-native-"+revision,revision,new RawJson(state),NativeWire.packet(StrictJson.canonical(packet)),at);
        var nativeRef=archive.preserveNativeFrame(actual);var protocol=new Obj(Map.of("backend_id",new Text("native-headless"),"source",new Text("injected-dll-named-pipe"),"diagnostics",DriverJson.object(state,65536).get("diagnostics")));
        var currentDriver=new RawJson(known.driver().encode());var currentFull=archive.preserveMaterial(currentDriver);
        var encoded=DriverObservationEvidenceReader.encode(known,actual,id.frame().revision(),1,SOURCE,protocol,currentFull);
        var manifest=archive.preserveMaterial(encoded);var facts=DriverObservationEvidenceReader.decode(manifest,encoded,currentDriver,actual);
        return assertInstanceOf(Complete.class,new DriverObservationAssembler().assemble(actual,facts,nativeRef));
    }
    private static final class MemoryArchive implements ActionPorts.OutcomeArchive{
        final Map<ExactRef,byte[]> materials=new java.util.HashMap<>();final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new java.util.HashMap<>();final Map<ExactRef,PlanningReadReceipt> reads=new java.util.HashMap<>();
        ExactRef ref(byte[] raw){return new ExactRef("D:/test-memory/life-effect/"+DriverJson.sha256(raw)+".json",raw.length,DriverJson.sha256(raw));}
        @Override public ExactRef preserveMaterial(RawJson raw){var ref=ref(raw.bytes());materials.putIfAbsent(ref,raw.bytes());return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){return new RawJson(materials.get(ref));}
        @Override public RawJson loadFullMaterial(ExactRef ref){return loadMaterial(ref);}
        @Override public ExactRef materialReferenceOf(RawJson raw){var ref=ref(raw.bytes());assertArrayEquals(raw.bytes(),materials.get(ref));return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame actual){byte[] raw=actual.originalPacket();var ref=ref(raw);materials.putIfAbsent(ref,raw);return ref;}
        @Override public byte[] loadNativeFrame(ExactRef ref){return materials.get(ref).clone();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original){var ack=(NativeActionPort.AckReceived)original;var ref=preserveMaterial(ack.originalFrame());outcomes.put(ref,original);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return outcomes.get(ref);}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original){return outcomes.entrySet().stream().filter(e->e.getValue().equals(original)).findFirst().orElseThrow().getKey();}
        @Override public ExactRef preserveRead(PlanningReadReceipt original){var ref=preserve(original.original());reads.put(ref,original);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return reads.get(ref);}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original){return reads.entrySet().stream().filter(e->e.getValue().equals(original)).findFirst().orElseThrow().getKey();}
        private AssertionError unavailable(){return new AssertionError("archived DATA seam cannot issue requests, write actions or grant runtime authority");}
        @Override public ExactRef preserveRequest(NativeRequest original){throw unavailable();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw unavailable();}
        @Override public ExactRef requestReferenceOf(NativeRequest original){throw unavailable();}
        @Override public ExactRef preserveRecord(ActionRecord original){throw unavailable();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unavailable();}
        @Override public ExactRef recordReferenceOf(ActionRecord original){throw unavailable();}
        @Override public ExactRef preserveReceipt(ActionReceipt original){throw unavailable();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unavailable();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt original){throw unavailable();}
    }
}

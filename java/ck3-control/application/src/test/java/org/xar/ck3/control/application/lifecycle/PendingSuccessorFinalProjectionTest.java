package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Actual M3 pure producer -> strict persisted state -> final goal consumer. Software DATA, never a private Root permit. */
final class PendingSuccessorFinalProjectionTest {
    private static final Instant AT=Instant.parse("2026-10-24T04:40:00Z");
    private static ExactRef ref(String name,byte[] body){return new ExactRef("D:/synthetic-pending-final/"+name,body.length,DriverJson.sha256(body));}
    private static ExactRef ref(String name){return ref(name,new byte[]{1});}
    private static ObjectNode lifecycle(){
        return LifecycleJson.row().put("schema","xar.ck3.succession-lifecycle-binding/v1")
                .put("lifecycle","ordinary_campaign_succession").put("xar_enabled","xar_on")
                .put("pact_contract","test-pact").put("source","test-bound-source")
                .put("environment_sha256","a".repeat(64));
    }
    private record Fixture(DriverSnapshotFacts.Known known,DriverObservationAssembler.FullSnapshot full,SuccessorUiObligation before,Finalization finalized,RawJson estate) { }
    private static Fixture fixture(){return fixture(2,3);}
    private static Fixture fixture(int predecessor,int successor){
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var nil=new DriverStateSnapshot.NullValue();var lifecycle=new DriverStateSnapshot.Value(LifecycleJson.bytes(lifecycle()));
        var goal=new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("campaign",predecessor)));
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,BigInteger.valueOf(successor),"new-episode"),List.of(),nil,nil,nil,nil,lifecycle,goal,new DriverStateSnapshot.Value(new byte[]{'[',']'}));
        var driverRef=ref("driver",driver.encode());var old=new LifecycleIdentity("synthetic-final-machine",game,"session",BigInteger.ONE,new LifecycleIdentity.Subject(BigInteger.valueOf(predecessor),"old-episode",1,2),new LifecycleIdentity.Frame("actual-13",BigInteger.valueOf(113),BigInteger.valueOf(13),BigInteger.valueOf(100),true,true),new LifecycleIdentity.Character(BigInteger.valueOf(successor),true),LifecycleIdentity.TerminalReason.CHANGED,new LifecycleIdentity.Evidence(ref("old-native"),ref("hello"),ref("old-manifest"),ref("old-driver"),ref("source")),AT);
        var binding=new Binding(old,BigInteger.valueOf(successor),"new-episode","b".repeat(64),"c".repeat(64),"parent","d".repeat(64),ref("parent"),ref("preclock"),ref("cause"),AT);
        var nativeState=LifecycleJson.row().put("snapshot_id","actual-20").put("revision",20).put("date_raw",100).put("paused",true).put("map_ready",true).putNull("one_life_terminal_reason");nativeState.putObject("played_character").put("character_id",successor).put("alive",true);
        var packetBody=LifecycleJson.row().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","actual-20").put("revision",20);packetBody.set("state",nativeState);
        byte[] body=LifecycleJson.bytes(packetBody),packet=java.nio.ByteBuffer.allocate(body.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();var packetRef=ref("packet",packet);
        var transport=new NativeObservationPort.TransportSession(old.machineId(),game,BigInteger.ONE,"session");var frame=new NativeObservationPort.ObservedFrame(transport,"actual-20",BigInteger.valueOf(20),new RawJson(LifecycleJson.bytes(nativeState)),packet,AT.plusSeconds(1));
        var fullSemantic=nativeState.deepCopy().put("revision",120).put("native_revision",20).put("episode_run_id","new-episode").put("episode_character_id",successor);var semantic=LifecycleJson.immutable(fullSemantic);var source=new G2Source(old.machineId(),AT.toString(),"synthetic-build",ref("source"));
        var facts=new DriverObservationFacts(driver,3,2,transport,"actual-20",BigInteger.valueOf(20),DriverJson.sha256(frame.state().bytes()),BigInteger.valueOf(120),1,source,new OpportunityJson.Obj(java.util.Map.of()),ref("facts"));
        var full=new DriverObservationAssembler.FullSnapshot(frame,facts,OpportunityJson.object(semantic,"full semantic"),packetRef,"e".repeat(64));
        var ui=new UiFrame(old.machineId(),game,"session",BigInteger.ONE,binding.sourceEpochSha256(),"actual-20",BigInteger.valueOf(120),BigInteger.valueOf(20),BigInteger.valueOf(100),BigInteger.valueOf(successor),"new-episode",2,3,packetRef,ref("sem"),driverRef,Optional.of(ref("source")),frame.observedAt());
        var observation=new Observation(ui,UiState.CLEAR,BigInteger.ONE,BigInteger.ONE,ref("query"),ref("raw-query"),Optional.empty(),Optional.empty());
        var before=SuccessorUiObligationCodec.decode(SuccessorUiObligationCodec.encode(SuccessorUiObligationReducer.observe(SuccessorUiObligationReducer.pending(binding),observation)));
        var aux=SuccessorUiObligationReducer.withState(new OpportunityJson.Obj(java.util.Map.of("family_marriage_ledger",OpportunityJson.Nil.INSTANCE)),before);
        var known=new DriverSnapshotFacts.Known(driver,new DriverSnapshotFacts.Stamp(3,2,game,"new-episode",DriverJson.sha256(driver.encode())),ref("history"),List.of(),aux,Optional.empty(),Optional.empty());
        var frozen=SuccessionNativeEstate12004.freeze(LifecycleJson.bytes(rootForPair(11,predecessor,false,successor)),semanticForPair(11,predecessor,false,predecessor));var estate=new RawJson(SuccessionNativeEstate12004.reconcile(frozen,LifecycleJson.bytes(rootForPair(13,successor,true,successor)),semanticForPair(13,successor,true,predecessor)).wire());
        return new Fixture(known,full,before,new Finalization(binding.causeDigest(),ref("actual-private-final-m3-DATA-projection"),ui,Optional.empty(),Optional.empty(),AT.plusSeconds(2)),estate);
    }
    @Test void genuineM3DataCreditsGoalOnlyAtFinalProjectionAndPreservesCurrentEpisode() {
        var f=fixture();var beforeGoal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)f.known().driver().campaignGoal()).json());assertEquals(2,beforeGoal.currentCharacterId());assertEquals(0,beforeGoal.progress().reconciledSuccessions());
        var result=SuccessorUiObligationReducer.finalEpisode(f.known(),f.before(),f.finalized(),f.full(),f.estate(),AT.plusSeconds(3));
        assertEquals(f.known().driver().session(),result.driver().session());assertEquals(f.known().driver().commandHistory(),result.driver().commandHistory());
        var goal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)result.driver().campaignGoal()).json());assertEquals(3,goal.currentCharacterId());assertEquals(1,goal.progress().reconciledSuccessions());
        var state=SuccessorUiObligationCodec.fromJson(OpportunityJson.toNode(result.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));assertEquals(Phase.FINALIZED,state.phase());
        var wire=LifecycleJson.parse(result.result(),LifecycleProofCodec.MAX_RESULT_BYTES);assertEquals("synthetic-final-machine",wire.get("machine_id").textValue());assertEquals(f.full().actual().observedAt().toString(),wire.get("observed_at_utc").textValue());assertEquals("old-episode",wire.get("source_run_id").textValue());assertEquals("new-episode",wire.get("episode_run_id").textValue());
        assertArrayEquals(result.driver().encode(),DriverStateSnapshot.decodeComplete(result.driver().encode()).encode());
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.finalEpisode(f.known(),state,f.finalized(),f.full(),f.estate(),AT.plusSeconds(4)));
    }
    @Test void dataCannotCreditBeforeClearanceOrWithWrongEstateOrBeforeActualObservation() {
        var f=fixture();var wrong=LifecycleJson.parse(f.estate().bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);wrong.put("actual_successor_character_id",99);
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.finalEpisode(f.known(),f.before(),f.finalized(),f.full(),new RawJson(LifecycleJson.bytes(wrong)),AT.plusSeconds(3)));
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.finalEpisode(f.known(),f.before(),f.finalized(),f.full(),f.estate(),AT));
        assertThrows(IllegalArgumentException.class,()->SuccessorUiObligationReducer.finalEpisode(f.known(),SuccessorUiObligationReducer.pending(f.before().binding()),f.finalized(),f.full(),f.estate(),AT.plusSeconds(3)));
    }
    @Test void actualCacheResetDiscardsPreviousPendingCauseAndBothPublicationMarkers() {
        var f=fixture();var stale=f.known().auxiliary().with("driver_pending_episode_source",new OpportunityJson.Text("stale")).with("driver_pending_episode_mutation_source",new OpportunityJson.Text("stale"));
        var reset=LifecycleReducer.clearEpisodeCaches(stale);assertFalse(reset.members().containsKey(SuccessorUiObligation.AUXILIARY_KEY));assertFalse(reset.members().containsKey("driver_pending_episode_source"));assertFalse(reset.members().containsKey("driver_pending_episode_mutation_source"));assertTrue(stale.members().containsKey(SuccessorUiObligation.AUXILIARY_KEY));
    }
    private static ObjectNode root(int revision, int actor, boolean after) {
        ObjectNode result = LifecycleJson.row().put("step", "query-campaign-root-context-v1").put("accepted", true).put("status", "available")
                .put("query_sequence", revision).put("snapshot_revision", revision).put("backend_id", "native-headless");
        ObjectNode root = result.putObject("campaign_root_context").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", revision).put("date_raw", 100).put("player_character_id", actor).put("player_character_alive", true).putNull("unavailable_reason");
        root.set("primary_title", title(10)); root.putArray("primary_title_succession_character_ids").add(after ? 6 : 3);
        ObjectNode provenance = root.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id", "ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset", "0x1E0").put("primary_title_rva", "0x289DA10");
        ObjectNode readiness = root.putObject("readiness");
        for (String key : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready", "same_frame_ready")) readiness.put(key, true);
        var rows = root.putArray("held_title_partition"); rows.add(row(10, after ? 6 : 3, true));
        if (!after) rows.add(row(20, 4, false));
        return result;
    }
    private static ObjectNode rootForPair(int revision,int actor,boolean after,int successor) {
        var result=root(revision,actor,after);
        if(!after) {
            var context=(ObjectNode)result.get("campaign_root_context");
            ((com.fasterxml.jackson.databind.node.ArrayNode)context.get("primary_title_succession_character_ids")).removeAll().add(successor);
            ((ObjectNode)context.get("held_title_partition").get(0)).put("first_heir_character_id",successor);
        }
        return result;
    }
    private static byte[] semanticForPair(int revision,int actor,boolean changed,int predecessor) {
        var result=LifecycleJson.parse(semantic(revision,actor,changed),LifecycleProofCodec.MAX_RESULT_BYTES);
        result.put("episode_character_id",predecessor);return LifecycleJson.bytes(result);
    }
    private static ObjectNode title(int id) { return LifecycleJson.row().put("title_id", id).put("tier_raw", 2).put("tier_key", "county"); }
    private static ObjectNode row(int id, int heir, boolean primary) {
        ObjectNode row = LifecycleJson.row().put("first_heir_character_id", heir).put("primary", primary).put("capital_province_id", id + 1); row.set("title", title(id)); return row;
    }
    private static byte[] semantic(int revision, int actor, boolean changed) {
        ObjectNode semantic = LifecycleJson.row().put("snapshot_id", "actual-" + revision).put("revision", revision + 100).put("native_revision", revision)
                .put("date_raw", 100).put("episode_run_id", "old-episode").put("episode_character_id", 2).put("paused", true).put("map_ready", true)
                .put("one_life_terminal", changed).putNull("active_event").putNull("pending_character_interaction");
        if (changed) semantic.put("one_life_terminal_reason", "played_character_changed"); else semantic.putNull("one_life_terminal_reason");
        semantic.putObject("played_character").put("character_id", actor).put("alive", true);
        semantic.set("succession_lifecycle",lifecycle()); return LifecycleJson.bytes(semantic);
    }

    /** Derived from the actual positive M3 DATA producer; no Root proof or native actor is minted. */
    private static LifecycleObservationPort.Snapshot changedCharacterData(int predecessor,
            com.fasterxml.jackson.databind.JsonNode successor,boolean ordinary) {
        var original=fixture();
        var estate=LifecycleJson.parse(original.estate().bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);
        estate.put("predecessor_character_id",predecessor);
        estate.set("expected_successor_character_id",successor.deepCopy());
        estate.set("actual_successor_character_id",successor.deepCopy());
        ((ObjectNode)estate.get("predecessor_binding")).put("episode_character_id",predecessor);
        var successorFrame=(ObjectNode)estate.get("successor_binding");
        var lifecycle=lifecycle();if(!ordinary)lifecycle.put("lifecycle","rogue_one_life");
        var nil=new DriverStateSnapshot.NullValue();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,
                BigInteger.valueOf(predecessor),"old-episode"),List.of(),nil,nil,nil,nil,
                new DriverStateSnapshot.Value(LifecycleJson.bytes(lifecycle)),
                new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.newGoal("campaign",predecessor))),
                new DriverStateSnapshot.Value(new byte[]{'[',']'}));
        var actual=original.full().actual();var game=actual.session().game();
        var known=new DriverSnapshotFacts.Known(driver,new DriverSnapshotFacts.Stamp(1,2,game,
                "old-episode",DriverJson.sha256(driver.encode())),ref("typed-role-driver",driver.encode()),
                List.of(),new OpportunityJson.Obj(java.util.Map.of("family_marriage_ledger",OpportunityJson.Nil.INSTANCE)),
                Optional.empty(),Optional.empty());
        var state=LifecycleJson.row().put("paused",true).put("map_ready",true)
                .put("one_life_terminal_reason","played_character_changed");
        state.set("played_character",LifecycleJson.row().set("character_id",successor.deepCopy()));
        ((ObjectNode)state.get("played_character")).put("alive",true);
        for(String key:List.of("snapshot_id","date_raw"))state.set(key,successorFrame.get(key).deepCopy());
        state.set("revision",successorFrame.get("native_revision").deepCopy());
        var envelope=LifecycleJson.row().put("type","state_snapshot").put("protocol_version",1);
        envelope.set("snapshot_id",state.get("snapshot_id").deepCopy());envelope.set("revision",state.get("revision").deepCopy());
        envelope.set("state",state.deepCopy());
        byte[] body=LifecycleJson.bytes(envelope),packet=java.nio.ByteBuffer.allocate(body.length+4)
                .order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var frame=new NativeObservationPort.ObservedFrame(actual.session(),state.get("snapshot_id").textValue(),
                state.get("revision").bigIntegerValue(),new RawJson(LifecycleJson.bytes(state)),packet,AT);
        var semantic=state.deepCopy().put("episode_run_id","old-episode").put("episode_character_id",predecessor);
        semantic.set("revision",successorFrame.get("revision").deepCopy());
        semantic.set("native_revision",successorFrame.get("native_revision").deepCopy());
        semantic.set("succession_reconciliation",estate);semantic.putNull("one_life_settlement");
        return new LifecycleObservationPort.Snapshot(frame,original.full().facts().source(),
                OpportunityJson.object(LifecycleJson.immutable(semantic),"derived typed M3 DATA"),
                known,ref("typed-role-packet",packet));
    }

    private static ActionPorts.OutcomeArchive memoryOriginals() {
        var retained=new java.util.HashMap<String,RawJson>();
        return (ActionPorts.OutcomeArchive)java.lang.reflect.Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,arguments)->{
                    return switch(method.getName()) {
                        case "preserveMaterial" -> {
                            var body=(RawJson)arguments[0];String digest=DriverJson.sha256(body.bytes());retained.put(digest,body);
                            yield new ExactRef("D:/synthetic-pending-final/memory/"+digest,body.bytes().length,digest);
                        }
                        case "materialReferenceOf" -> {
                            var body=(RawJson)arguments[0];String digest=DriverJson.sha256(body.bytes());
                            assertArrayEquals(body.bytes(),java.util.Objects.requireNonNull(retained.get(digest),"original not retained").bytes());
                            yield new ExactRef("D:/synthetic-pending-final/memory/"+digest,body.bytes().length,digest);
                        }
                        case "loadMaterial" -> {
                            var original=(ExactRef)arguments[0];var body=java.util.Objects.requireNonNull(retained.get(original.sha256()),"original missing");
                            assertEquals(original.bytes(),body.bytes().length);assertEquals(original.sha256(),DriverJson.sha256(body.bytes()));yield body;
                        }
                        default -> throw new UnsupportedOperationException("unexpected non-material test archive call: "+method.getName());
                    };
                });
    }
    private record PendingInput(LifecycleObservationPort.Snapshot snapshot,Binding binding) { }
    private static PendingInput actualPendingInput(Fixture finalized,int predecessor,int successor) {
        var retained=finalized.before().binding();var old=retained.predecessor();
        var state=LifecycleJson.row().put("snapshot_id",old.frame().snapshotId()).put("revision",old.frame().nativeRevision())
                .put("date_raw",old.frame().dateRaw()).put("paused",true).put("map_ready",true)
                .put("one_life_terminal_reason","played_character_changed");
        state.putObject("played_character").put("character_id",successor).put("alive",true);
        var envelope=LifecycleJson.row().put("type","state_snapshot").put("protocol_version",1)
                .put("snapshot_id",old.frame().snapshotId()).put("revision",old.frame().nativeRevision());envelope.set("state",state.deepCopy());
        byte[] body=LifecycleJson.bytes(envelope),packet=java.nio.ByteBuffer.allocate(body.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var packetRef=ref("actual-pending-"+predecessor+"-"+successor,packet);
        var transport=finalized.full().actual().session();
        var actual=new NativeObservationPort.ObservedFrame(transport,old.frame().snapshotId(),old.frame().nativeRevision(),new RawJson(LifecycleJson.bytes(state)),packet,AT);
        var nil=new DriverStateSnapshot.NullValue();var goal=finalized.known().driver().campaignGoal();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,BigInteger.valueOf(predecessor),"old-episode"),List.of(),nil,nil,nil,nil,
                finalized.known().driver().successionLifecycle(),goal,new DriverStateSnapshot.Value(new byte[]{'[',']'}));
        var known=new DriverSnapshotFacts.Known(driver,new DriverSnapshotFacts.Stamp(old.subject().driverVersion(),old.subject().episodeEpoch(),old.game(),"old-episode",DriverJson.sha256(driver.encode())),
                ref("pending-input-history"),List.of(),new OpportunityJson.Obj(java.util.Map.of("family_marriage_ledger",OpportunityJson.Nil.INSTANCE)),Optional.empty(),Optional.empty());
        var semantic=state.deepCopy().put("revision",old.frame().revision()).put("native_revision",old.frame().nativeRevision())
                .put("episode_run_id","old-episode").put("episode_character_id",predecessor)
                .putNull("succession_reconciliation").putNull("one_life_settlement");
        var origin=new LifecycleIdentity(old.machineId(),old.game(),old.sessionId(),old.connectionGeneration(),old.subject(),old.frame(),old.currentPlayer(),old.terminalReason(),
                new LifecycleIdentity.Evidence(packetRef,old.evidence().helloPacket(),old.evidence().observationManifest(),old.evidence().originalDriver(),old.evidence().completeSourceQualification()),AT);
        var binding=new Binding(origin,retained.successorCharacterId(),retained.successorEpisodeRunId(),retained.sourceEpochSha256(),retained.causeDigest(),retained.parentActionId(),
                retained.parentBodySha256(),retained.originalParentCommand(),retained.preclockDocument(),retained.qualifiedCause(),retained.qualifiedAtUtc());
        return new PendingInput(new LifecycleObservationPort.Snapshot(actual,finalized.full().facts().source(),
                OpportunityJson.object(LifecycleJson.immutable(semantic),"actual synthetic changed-player input"),known,packetRef),binding);
    }
    @Test void signedProducerPrepareArchivePersistedObligationAndFinalConsumerPreserveNativeRoles() {
        int[][] pairs={{2,0},{2,-2},{2,Integer.MIN_VALUE},{2,Integer.MAX_VALUE},{0,3},{-2,3},{Integer.MIN_VALUE,3}};
        for(int[] pair:pairs) {
            var finalInput=fixture(pair[0],pair[1]);var input=actualPendingInput(finalInput,pair[0],pair[1]);
            var pending=SuccessorUiObligationReducer.pendingEpisode(input.snapshot(),input.binding());
            assertArrayEquals(finalInput.known().driver().encode(),pending.driver().encode());
            var archive=memoryOriginals();archive.preserveMaterial(new RawJson(input.snapshot().facts().driver().encode()));
            var prepared=DriverPendingEpisodeProjection.prepare(input.snapshot().facts(),pending,archive);
            var child=DriverPendingEpisodeProjection.decode(archive.loadMaterial(prepared.originalRef()).bytes());
            assertEquals(prepared.projection(),child);assertEquals(BigInteger.valueOf(pair[0]),child.oldActor());assertEquals(BigInteger.valueOf(pair[1]),child.newActor());
            var retained=SuccessorUiObligationCodec.decode(archive.loadMaterial(child.obligation()).bytes());
            assertEquals(pending.obligation(),retained);assertTrue(retained.blocksOrdinaryActionsAndSave());
            assertEquals(0,GoalCodec.decodeGoal(((DriverStateSnapshot.Value)pending.driver().campaignGoal()).json()).progress().reconciledSuccessions());
            var known=new DriverSnapshotFacts.Known(pending.driver(),new DriverSnapshotFacts.Stamp(child.afterVersion(),child.afterEpoch(),child.game(),child.newEpisodeRunId(),DriverJson.sha256(pending.driver().encode())),
                    ref("retained-empty-pending-history"),List.of(),pending.auxiliary(),Optional.empty(),Optional.empty());
            var bytes=DriverSnapshotFacts.encodeKnownOriginal(known);
            var reopened=DriverSnapshotFacts.decodeKnownOriginal(DriverSnapshotFacts.originalKnownJson(bytes.bytes()),Optional.empty());
            var persisted=SuccessorUiObligationCodec.fromJson(OpportunityJson.toNode(reopened.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            var finalPrepared=DriverPendingEpisodeMutations.prepare(reopened,persisted,
                    new DriverPendingEpisodeSource.Finalize(finalInput.finalized(),finalInput.before().observation().orElseThrow(),finalInput.full(),finalInput.estate(),AT.plusSeconds(3)),archive);
            var result=finalPrepared.projection();
            assertArrayEquals(SuccessorUiObligationCodec.encode(result.obligation()),archive.loadMaterial(finalPrepared.afterObligation()).bytes());
            assertArrayEquals(result.result().orElseThrow().bytes(),archive.loadMaterial(finalPrepared.originalResult().orElseThrow()).bytes());
            var goal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)result.driver().campaignGoal()).json());
            assertEquals(pair[1],goal.currentCharacterId());assertEquals(1,goal.progress().reconciledSuccessions());
            assertEquals(reopened.driver().session(),result.driver().session());assertEquals(BigInteger.valueOf(pair[1]),result.driver().session().actorId());
            assertArrayEquals(result.driver().encode(),DriverStateSnapshot.decodeComplete(result.driver().encode()).encode());
            var finalState=SuccessorUiObligationCodec.fromJson(OpportunityJson.toNode(result.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            assertEquals(Phase.FINALIZED,finalState.phase());assertFalse(finalState.blocksOrdinaryActionsAndSave());
            var wire=LifecycleJson.parse(result.result().orElseThrow().bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);
            assertEquals(BigInteger.valueOf(pair[0]),wire.get("predecessor_character_id").bigIntegerValue());
            assertEquals(BigInteger.valueOf(pair[1]),wire.get("actual_successor_character_id").bigIntegerValue());
            assertFalse(wire.get("ck3_command_submitted").booleanValue());assertTrue(finalState.closeAttempt().isEmpty());
        }
    }

    @Test void signedCharacterDataContinuesTheGoalWithoutChangingItsIntegerBits() {
        int[][] pairs={{2,0},{2,-2},{2,Integer.MIN_VALUE},{2,Integer.MAX_VALUE},{0,3},{-2,3},{Integer.MIN_VALUE,3}};
        for(int[] pair:pairs) {
            var snapshot=changedCharacterData(pair[0],com.fasterxml.jackson.databind.node.IntNode.valueOf(pair[1]),true);
            byte[] originalDriver=snapshot.facts().driver().encode();
            var result=LifecycleReducer.continueSuccessor(snapshot,"continued-typed-episode",AT.plusSeconds(3));
            assertEquals(BigInteger.valueOf(pair[1]),result.driver().session().actorId());
            assertEquals("continued-typed-episode",result.driver().session().episodeRunId());
            var goal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)result.driver().campaignGoal()).json());
            assertEquals(pair[1],goal.currentCharacterId());assertEquals(1,goal.progress().reconciledSuccessions());
            var wire=LifecycleJson.parse(result.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
            assertEquals(BigInteger.valueOf(pair[0]),wire.get("predecessor_character_id").bigIntegerValue());
            assertEquals(BigInteger.valueOf(pair[1]),wire.get("actual_successor_character_id").bigIntegerValue());
            assertTrue(wire.get("actual_successor_character_id").isIntegralNumber());
            assertEquals("old-episode",wire.get("source_run_id").textValue());
            assertEquals(100,wire.get("date_raw").intValue());assertEquals(113,wire.get("revision").intValue());
            assertFalse(wire.get("ck3_command_submitted").booleanValue());
            assertArrayEquals(result.driver().encode(),DriverStateSnapshot.decodeComplete(result.driver().encode()).encode());
            assertArrayEquals(originalDriver,snapshot.facts().driver().encode());
        }
    }

    @Test void changedPlayerTerminalRetainsSignedDataWithoutGrantingContinuation() {
        var persistence=new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of());
        for(int successor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE}) {
            var snapshot=changedCharacterData(2,com.fasterxml.jackson.databind.node.IntNode.valueOf(successor),false);
            var result=LifecycleReducer.death(snapshot,null,persistence,AT.plusSeconds(3));
            var wire=LifecycleJson.parse(result.result(),LifecycleProofCodec.MAX_RESULT_BYTES);
            assertEquals(BigInteger.valueOf(successor),wire.get("played_character").get("character_id").bigIntegerValue());
            assertEquals(snapshot.facts().driver().session(),result.driver().session());
            assertFalse(wire.get("continue_as_heir_after_death").booleanValue());
            assertEquals(0,wire.get("heir_gameplay_actions").intValue());
            assertEquals("settlement_unavailable",wire.get("settlement_status").textValue());
            assertArrayEquals(result.driver().encode(),DriverStateSnapshot.decodeComplete(result.driver().encode()).encode());
        }
    }

    @Test void characterBoundaryRejectsAbsenceWrongJsonTypesAndUnsignedWidening() {
        var values=List.<com.fasterxml.jackson.databind.JsonNode>of(
                com.fasterxml.jackson.databind.node.IntNode.valueOf(-1),
                com.fasterxml.jackson.databind.node.LongNode.valueOf(2147483648L),
                com.fasterxml.jackson.databind.node.LongNode.valueOf(4294967294L),
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("2.0")),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("2"),
                com.fasterxml.jackson.databind.node.NullNode.instance,
                com.fasterxml.jackson.databind.node.IntNode.valueOf(2));
        var persistence=new DeathSettlement.Persistence(DeathSettlement.PersistenceStatus.NO_NEW_RECORD,false,Optional.empty(),List.of());
        for(var value:values) {
            var ordinary=changedCharacterData(2,value,true);
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(ordinary,"next",AT.plusSeconds(3)));
            var rogue=changedCharacterData(2,value,false);
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.death(rogue,null,persistence,AT.plusSeconds(3)));
        }
        var valid=changedCharacterData(2,com.fasterxml.jackson.databind.node.IntNode.valueOf(0),true);
        for(String fault:List.of("predecessor","revision","paused","map_ready")) {
            var semantic=LifecycleJson.object(OpportunityJson.toNode(valid.semantic())).deepCopy();
            if(fault.equals("predecessor"))((ObjectNode)semantic.get("succession_reconciliation").get("predecessor_binding")).put("episode_character_id",77);
            else if(fault.equals("revision"))semantic.put("revision",114);
            else semantic.put(fault,false);
            var changed=new LifecycleObservationPort.Snapshot(valid.actual(),valid.source(),
                    OpportunityJson.object(LifecycleJson.immutable(semantic),"faulted typed M3 DATA"),valid.facts(),valid.originalEvidence());
            assertThrows(IllegalArgumentException.class,()->LifecycleReducer.continueSuccessor(changed,"next",AT.plusSeconds(3)));
        }
    }
}

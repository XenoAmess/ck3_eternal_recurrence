package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.planning.campaign.CrossRunPlanning;
import org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Shared pure domain algorithm used by preflight and original locked writer revalidation. No file/Native writes. */
public final class LifecycleReducer {
    private LifecycleReducer(){ }
    public record Reduction(DriverStateSnapshot.Complete driver,OpportunityJson.Obj auxiliary,byte[] result) {
        public Reduction{result=result.clone();}
        @Override public byte[] result(){return result.clone();}
    }
    static ObjectNode semantic(LifecycleObservationPort.Snapshot snapshot){return LifecycleJson.object(OpportunityJson.toNode(snapshot.semantic()));}
    static ObjectNode auxiliary(DriverSnapshotFacts.Known facts){return LifecycleJson.object(OpportunityJson.toNode(facts.auxiliary()));}
    static OpportunityJson.Obj immutable(ObjectNode row){return OpportunityJson.object(LifecycleJson.immutable(row),"lifecycle auxiliary");}
    static ObjectNode slot(DriverStateSnapshot.Slot slot){StrictJson.require(slot instanceof DriverStateSnapshot.Value,"actual complete lifecycle/goal value required");return LifecycleJson.parse(((DriverStateSnapshot.Value)slot).json(),LifecycleProofCodec.MAX_RESULT_BYTES);}
    public static String lifecycle(DriverStateSnapshot.Complete driver){
        ObjectNode value=slot(driver.successionLifecycle());
        LifecycleJson.exact(value,java.util.Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256"));
        StrictJson.require(LifecycleJson.text(value.get("schema")).equals("xar.ck3.succession-lifecycle-binding/v1"),"original full six-field lifecycle schema required");
        String mode=LifecycleJson.text(value.get("lifecycle"));StrictJson.require(mode.equals("rogue_one_life")||mode.equals("ordinary_campaign_succession"),"supported original lifecycle required");
        return mode;
    }
    public static Reduction continueSuccessor(LifecycleObservationPort.Snapshot observed,String newRunId,Instant at){
        var old=observed.facts().driver();ObjectNode frame=semantic(observed),aux=auxiliary(observed.facts());
        StrictJson.require(observed.paused()&&observed.mapReady()&&LifecycleJson.text(frame.get("one_life_terminal_reason")).equals("played_character_changed"),"paused actual changed-player terminal required");
        ObjectNode player=LifecycleJson.object(frame.get("played_character"));BigInteger actor=org.xar.ck3.control.contracts.NativeCharacterId.fromJson(player.get("character_id")).asBigInteger();
        StrictJson.require(LifecycleJson.bool(player.get("alive"))&&!actor.equals(old.session().actorId()),"actual distinct living successor required");
        ObjectNode reconciliation=LifecycleJson.object(frame.get("succession_reconciliation"));
        var matched=GoalCodec.decodeReconciliation(LifecycleJson.bytes(reconciliation));
        StrictJson.require(matched.verdict()==OrdinaryCampaignGoal.Verdict.MATCHED
                && BigInteger.valueOf(matched.predecessorCharacterId()).equals(old.session().actorId())
                && BigInteger.valueOf(matched.actualSuccessorCharacterId()).equals(actor),"actual complete M3 matched predecessor/successor required");
        ObjectNode binding=LifecycleJson.object(reconciliation.get("successor_binding"));
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw"))
            StrictJson.require(LifecycleJson.same(binding.get(key),frame.get(key)),"M3 successor frame drift: "+key);
        ObjectNode predecessor=LifecycleJson.object(reconciliation.get("predecessor_binding"));
        StrictJson.require(LifecycleJson.text(predecessor.get("episode_run_id")).equals(old.session().episodeRunId())
                && org.xar.ck3.control.contracts.NativeCharacterId.fromJson(predecessor.get("episode_character_id")).asBigInteger().equals(old.session().actorId()),"M3 predecessor episode differs");
        String mode=lifecycle(old);if(mode.equals("rogue_one_life"))requireScoredTerminal(old);
        StrictJson.text(newRunId);StrictJson.require(!newRunId.equals(old.session().episodeRunId()),"new successor episode identity required after actual M3 proof");
        DriverStateSnapshot.Slot goal=old.campaignGoal();
        if(mode.equals("ordinary_campaign_succession")) {
            var current=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)goal).json());
            goal=new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.continueGoal(current,matched)));
            archiveFamily(aux,old.session().episodeRunId(),newRunId,old.session().actorId(),actor);
        }
        clearEpisodeCaches(aux);aux.put("episode_binding_state","active_natural_successor");aux.put("restore_kind","natural_succession");
        aux.putNull("succession_reconciliation");aux.put("driver_state_restored",false);aux.put("migration_required",false);
        var replacement=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(old.session().pipeName(),old.session().bridgePid(),actor,newRunId),List.of(),
                new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),old.successionLifecycle(),goal,new DriverStateSnapshot.Value("[]".getBytes(java.nio.charset.StandardCharsets.US_ASCII)));
        ObjectNode result=LifecycleJson.row();result.put("status","continued");result.put("source","native-played-character-transition");result.put("lifecycle_intent","natural_succession");
        result.set("succession_lifecycle",slot(old.successionLifecycle()));result.put("predecessor_character_id",old.session().actorId());result.put("actual_successor_character_id",actor);
        result.put("source_run_id",old.session().episodeRunId());result.put("episode_run_id",newRunId);result.set("succession_reconciliation",reconciliation.deepCopy());
        result.put("continue_as_heir_after_death",true);result.put("heir_gameplay_actions",0);result.put("ck3_command_submitted",false);result.put("process_restarted",false);
        for(String key:List.of("date_raw","snapshot_id","revision"))result.set(key,frame.get(key).deepCopy());result.put("observed_at",at.toString());
        return new Reduction(replacement,immutable(aux),LifecycleJson.bytes(result));
    }
    /** DATA projection only. The actual source proves private M3 Finalized and canonical ancestry under its writer. */
    public static Reduction finalizePendingSuccessor(DriverSnapshotFacts.Known current,SuccessorUiObligation before,
            SuccessorUiObligation finalized,org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot actual,
            org.xar.ck3.control.application.action.RawJson actualMatchedEstate,Instant at) {
        java.util.Objects.requireNonNull(current);java.util.Objects.requireNonNull(before);java.util.Objects.requireNonNull(finalized);java.util.Objects.requireNonNull(actual);java.util.Objects.requireNonNull(actualMatchedEstate);java.util.Objects.requireNonNull(at);
        var binding=before.binding();var old=binding.predecessor();var driver=current.driver();var proof=finalized.finalization().orElseThrow();
        StrictJson.require(before.blocksOrdinaryActionsAndSave()&&finalized.phase()==SuccessorUiObligation.Phase.FINALIZED&&finalized.binding().equals(binding)&&proof.causeDigest().equals(binding.causeDigest()),"actual final pending source/cause required");
        StrictJson.require(lifecycle(driver).equals("ordinary_campaign_succession")&&driver.session().actorId().equals(binding.successorCharacterId())&&driver.session().episodeRunId().equals(binding.successorEpisodeRunId())&&current.stamp().episodeEpoch()==binding.successorEpisodeEpoch()&&current.stamp().driverVersion()>old.subject().driverVersion()&&current.stamp().game().equals(old.game()),"actual new ordinary successor episode required");
        var now=proof.current();var transport=actual.actual().session();
        StrictJson.require(!at.isBefore(actual.actual().observedAt()),"final result precedes its actual native observation");
        StrictJson.require(transport.machineId().equals(now.machineId())&&transport.game().equals(now.game())&&transport.sessionId().equals(now.sessionId())&&transport.connectionGeneration().equals(now.connectionGeneration())&&actual.actual().snapshotId().equals(now.snapshotId())&&actual.actual().nativeRevision().equals(now.nativeRevision())&&actual.actual().observedAt().equals(now.observedAtUtc())&&actual.originalEvidence().equals(now.nativePacket())&&actual.facts().publicRevision().equals(now.revision())&&actual.facts().episodeEpoch()==current.stamp().episodeEpoch()&&actual.facts().driverVersion()==current.stamp().driverVersion()&&java.util.Arrays.equals(actual.facts().driver().encode(),driver.encode())&&now.driverVersion()==current.stamp().driverVersion()&&now.originalDriver().sha256().equals(current.stamp().driverSha256()),"final pending frame is not the actual current full Driver/native join");
        var semantic=LifecycleJson.object(OpportunityJson.toNode(actual.semantic()));var player=LifecycleJson.object(semantic.get("played_character"));
        StrictJson.require(LifecycleJson.bool(player.get("alive"))&&org.xar.ck3.control.contracts.NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(binding.successorCharacterId())&&semantic.has("one_life_terminal_reason")&&semantic.get("one_life_terminal_reason").isNull()&&LifecycleJson.integer(semantic.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE)).equals(now.dateRaw()),"final ordinary native player/date differs");
        var reconciliation=LifecycleJson.parse(actualMatchedEstate.bytes(),LifecycleProofCodec.MAX_RESULT_BYTES);var matched=GoalCodec.decodeReconciliation(actualMatchedEstate.bytes());
        StrictJson.require(matched.verdict()==OrdinaryCampaignGoal.Verdict.MATCHED&&BigInteger.valueOf(matched.predecessorCharacterId()).equals(old.subject().characterId())&&BigInteger.valueOf(matched.actualSuccessorCharacterId()).equals(binding.successorCharacterId()),"final credit requires actual M3 predecessor/successor estate match");
        var predecessor=LifecycleJson.object(reconciliation.get("predecessor_binding"));var successor=LifecycleJson.object(reconciliation.get("successor_binding"));
        StrictJson.require(LifecycleJson.text(predecessor.get("episode_run_id")).equals(old.subject().episodeRunId())&&org.xar.ck3.control.contracts.NativeCharacterId.fromJson(predecessor.get("episode_character_id")).asBigInteger().equals(old.subject().characterId())&&LifecycleJson.integer(successor.get("revision"),BigInteger.ZERO).equals(old.frame().revision())&&LifecycleJson.integer(successor.get("native_revision"),BigInteger.ONE).equals(old.frame().nativeRevision())&&LifecycleJson.integer(successor.get("date_raw"),BigInteger.valueOf(Integer.MIN_VALUE)).equals(old.frame().dateRaw()),"final estate crossed original qualified precommit episode/frame");
        StrictJson.require(driver.campaignGoal() instanceof DriverStateSnapshot.Value,"actual original ordinary campaign goal required");
        var goal=GoalCodec.decodeGoal(((DriverStateSnapshot.Value)driver.campaignGoal()).json());
        var continued=new DriverStateSnapshot.Value(GoalCodec.encodeGoal(OrdinaryCampaignGoal.continueGoal(goal,matched)));
        var aux=LifecycleJson.object(OpportunityJson.toNode(SuccessorUiObligationReducer.withState(current.auxiliary(),finalized)));
        archiveFamily(aux,old.subject().episodeRunId(),binding.successorEpisodeRunId(),old.subject().characterId(),binding.successorCharacterId());
        aux.put("restore_kind","natural_succession");aux.putNull("succession_reconciliation");aux.put("driver_state_restored",false);aux.put("migration_required",false);
        var replacement=new DriverStateSnapshot.Complete(driver.session(),driver.commandHistory(),driver.lastCheckpoint(),driver.rollbackWarFailure(),driver.managedRestoreTransaction(),driver.successionExpectation(),driver.successionLifecycle(),continued,driver.rollbackWarFailures());
        var result=LifecycleJson.row().put("status","continued").put("source","native-post-continue-successor-ui").put("machine_id",transport.machineId()).put("observed_at_utc",actual.actual().observedAt().toString()).put("lifecycle_intent","natural_succession").put("predecessor_character_id",old.subject().characterId()).put("actual_successor_character_id",binding.successorCharacterId()).put("source_run_id",old.subject().episodeRunId()).put("episode_run_id",binding.successorEpisodeRunId()).put("observed_at",at.toString()).put("continue_as_heir_after_death",true).put("heir_gameplay_actions",0).put("ck3_command_submitted",false).put("process_restarted",false);
        result.set("succession_lifecycle",slot(driver.successionLifecycle()));result.set("succession_reconciliation",reconciliation);
        result.set("post_continue_m3_finalization",proof.finalM3Proof().toJson());result.set("pending_cause",binding.qualifiedCause().toJson());
        for(String key:List.of("date_raw","snapshot_id","revision"))result.set(key,semantic.get(key).deepCopy());
        return new Reduction(replacement,immutable(aux),LifecycleJson.bytes(result));
    }
    public static Reduction death(LifecycleObservationPort.Snapshot observed,DeathSettlement.Ready settlement,DeathSettlement.Persistence persistence,Instant at){
        var old=observed.facts().driver();StrictJson.require(lifecycle(old).equals("rogue_one_life"),"death-terminal is not ordinary campaign succession");
        ObjectNode frame=semantic(observed),aux=auxiliary(observed.facts());String reason=LifecycleJson.text(frame.get("one_life_terminal_reason"));
        StrictJson.require(List.of("played_character_changed","played_character_missing","played_character_dead").contains(reason),"actual native one-life terminal reason required");
        JsonNode player=frame.get("played_character");
        if(reason.equals("played_character_changed"))StrictJson.require(player instanceof ObjectNode&&!org.xar.ck3.control.contracts.NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(old.session().actorId()),"native changed-player evidence required");
        if(reason.equals("played_character_dead"))StrictJson.require(player instanceof ObjectNode&&!LifecycleJson.bool(player.get("alive")),"native dead-player evidence required");
        if(reason.equals("played_character_missing"))StrictJson.require(player==null||player.isNull(),"actual missing or explicit null native player required");
        ObjectNode result=LifecycleJson.row();result.put("observed_at",at.toString());result.put("terminal",true);result.put("kind",switch(reason){case "played_character_changed"->"native_played_character_changed";case "played_character_missing"->"native_played_character_missing";default->"native_played_character_dead";});
        result.put("terminal_reason",reason);result.put("episode_character_id",old.session().actorId());result.put("technical_settlement_handoff",false);result.put("continue_as_heir_after_death",false);result.put("heir_gameplay_actions",0);
        for(String key:List.of("played_character","date_raw","snapshot_id","revision")){JsonNode value=frame.get(key);if(value==null)result.putNull(key);else result.set(key,value.deepCopy());}
        if(settlement==null){result.putNull("score");result.putNull("one_life_settlement");result.put("settlement_status","settlement_unavailable");result.put("settlement_unavailable",true);}
        else{
            StrictJson.require(settlement.sourceCharacterId().equals(old.session().actorId()),"settlement belongs to another original episode actor");
            result.set("score",settlement.scoreJson());result.set("one_life_settlement",settlement.normalizedJson());result.put("settlement_status","complete");
        }
        ObjectNode persisted=result.putObject("record_persistence");persisted.put("status",persistence.status().wire());persisted.put("required",persistence.required());
        persistence.file().ifPresent(file->{persisted.put("path",file.reference().path());persisted.put("bytes",file.reference().bytes());persisted.put("sha256",file.reference().sha256());});
        List<DriverStateSnapshot.HistoryEntry> history=new ArrayList<>(old.commandHistory());
        ObjectNode virtual=LifecycleJson.row();virtual.put("index",history.size()+1L);virtual.put("command","death-terminal");virtual.put("ok",true);virtual.set("result",result);
        if(settlement!=null){
            StrictJson.require(aux.has("one_life_strategy"),"actual original one-life strategy presence/absence source required");
            ObjectNode strategy=recordEpisode(old,result,aux.get("one_life_strategy"),at);result.set("cross_run_strategy",strategy);aux.set("one_life_strategy",strategy.deepCopy());aux.set("scored_terminal",result.deepCopy());
        }
        history.add(new DriverStateSnapshot.HistoryEntry(history.size()+1L,new DriverStateSnapshot.Value(LifecycleJson.bytes(virtual))));
        var replacement=new DriverStateSnapshot.Complete(old.session(),history,old.lastCheckpoint(),old.rollbackWarFailure(),old.managedRestoreTransaction(),old.successionExpectation(),old.successionLifecycle(),old.campaignGoal(),old.rollbackWarFailures());
        return new Reduction(replacement,immutable(aux),LifecycleJson.bytes(result));
    }
    public static void requireScoredTerminal(DriverStateSnapshot.Complete driver){scoredTerminal(driver);}
    private static ObjectNode scoredTerminal(DriverStateSnapshot.Complete driver){
        for(int i=driver.commandHistory().size()-1;i>=0;i--){ObjectNode row=LifecycleJson.parse(driver.commandHistory().get(i).originalRow().json(),LifecycleProofCodec.MAX_RESULT_BYTES);
            if(!"death-terminal".equals(row.path("command").asText()))continue;
            StrictJson.require(row.get("ok")!=null&&row.get("ok").isBoolean()&&row.get("ok").booleanValue(),"latest death terminal must be successful");
            ObjectNode result=LifecycleJson.object(row.get("result"));StrictJson.require(LifecycleJson.bool(result.get("terminal"))&&"complete".equals(LifecycleJson.text(result.get("settlement_status")))&&result.get("score").isNumber(),"completed scored death terminal required");
            ObjectNode settlement=LifecycleJson.object(result.get("one_life_settlement"));StrictJson.require(settlement.hasNonNull("final_score"),"settlement final score required");
            ObjectNode recorded=LifecycleJson.object(LifecycleJson.object(result.get("cross_run_strategy")).get("recorded_episode"));
            StrictJson.require(LifecycleJson.text(recorded.get("run_id")).equals(driver.session().episodeRunId())&&LifecycleJson.same(recorded.get("score"),result.get("score")),"durable scored strategy episode differs");return result;
        }throw new IllegalArgumentException("completed scored terminal absent");
    }
    /** Pure original-data check. The actual caller separately replays this source and checks its canonical domain under the writer. */
    public static CrossRunPlanning.Plan requireNextRunPlan(DriverSnapshotFacts.Known before){
        StrictJson.require(lifecycle(before.driver()).equals("rogue_one_life"),"new one-life plan requires its original rogue lifecycle");
        ObjectNode terminal=scoredTerminal(before.driver());
        var retained=CrossRunStrategySource.decode(OpportunityJson.object(LifecycleJson.immutable(terminal.get("cross_run_strategy")),"actual scored terminal strategy")).state();
        var current=CrossRunStrategySource.decode(OpportunityJson.object(before.auxiliary().get("one_life_strategy"),"actual source-bound current strategy")).state();
        var sourceValue=before.auxiliary().get(org.xar.ck3.control.application.driver.DriverPersistentPlanningState.STRATEGY_SOURCE);
        StrictJson.require(sourceValue!=null,"actual canonical strategy source absent");
        var source=org.xar.ck3.control.contracts.ExactRef.fromJson(OpportunityJson.toNode(sourceValue));
        StrictJson.require(source.bytes()>0&&current.equals(retained),"NEXT canonical strategy or actual scored life differs");
        return current.nextRunPlan();
    }
    public static Reduction nextEpisode(DriverSnapshotFacts.Known before,SeedArtifact seed,long actualNewPid,BigInteger actualActor,BigInteger actualDate,String newRunId,Instant at){
        var old=before.driver();var usedPlan=requireNextRunPlan(before);
        StrictJson.require(actualNewPid!=old.session().bridgePid()&&actualNewPid>0&&actualActor.equals(seed.characterId())&&actualDate.equals(seed.dateRaw()),"actual new Game must load immutable seed actor/date");
        StrictJson.text(newRunId);StrictJson.require(!newRunId.equals(old.session().episodeRunId()),"new episode identity must differ after actual seed load");
        ObjectNode aux=auxiliary(before);clearEpisodeCaches(aux);aux.putNull("succession_reconciliation");aux.put("episode_binding_state","active_new");aux.put("restore_kind","new_episode");aux.putNull("scored_terminal");aux.putNull("episode_transition");
        var replacement=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session(old.session().pipeName(),actualNewPid,actualActor,newRunId),List.of(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.NullValue(),old.successionLifecycle(),new DriverStateSnapshot.NullValue(),new DriverStateSnapshot.Value("[]".getBytes(java.nio.charset.StandardCharsets.US_ASCII)));
        ObjectNode result=LifecycleJson.row();result.put("status","started");result.put("source","java-managed-game-lifecycle");result.put("lifecycle_intent","new_episode");result.put("source_run_id",old.session().episodeRunId());result.put("episode_run_id",newRunId);result.put("episode_character_id",actualActor);result.put("date_raw",actualDate);result.put("observed_at",at.toString());result.put("previous_pid",old.session().bridgePid());result.put("resumed_pid",actualNewPid);result.put("same_character_as_episode_seed",true);result.set("cross_run_plan_used",OpportunityJson.toNode(CrossRunPlanning.planJson(usedPlan)));result.put("continue_as_heir_after_death",false);return new Reduction(replacement,immutable(aux),LifecycleJson.bytes(result));
    }
    /** Pure cache projection shared by pre-final PendingUI; it does not continue the goal or award lifecycle credit. */
    public static OpportunityJson.Obj clearEpisodeCaches(OpportunityJson.Obj original) {
        java.util.Objects.requireNonNull(original);
        ObjectNode actual=LifecycleJson.object(OpportunityJson.toNode(original)).deepCopy();
        clearEpisodeCaches(actual);return immutable(actual);
    }
    private static void clearEpisodeCaches(ObjectNode aux){
        for(String key:List.of("declaration_query_sequence","declaration_query_binding","army_strength_query","combat_simulation_inputs_query","combat_simulation_inputs_v3_query","battle_control_snapshot_query","active_combat_retreat_token","war_entry_assessments_query","arrange_marriage_query_sequence"))aux.putNull(key);
        for(String key:List.of("declarable_wars","arrange_marriage_choices"))aux.putArray(key);
        for(String key:List.of("war_termination_options","war_termination_terms","war_termination_exit_terms"))aux.putObject(key);
        aux.put("arrange_marriage_dirty",true);
        var invalidated=org.xar.ck3.control.application.driver.DriverCapabilityStateProducer.afterEpisodeCacheClear(immutable(aux));
        var cleared=org.xar.ck3.control.application.driver.DriverPendingEpisodeSource.clearEpisodeData(invalidated);
        ObjectNode actual=LifecycleJson.object(OpportunityJson.toNode(cleared));aux.removeAll();aux.setAll(actual);
    }
    private static void archiveFamily(ObjectNode aux,String oldRun,String newRun,BigInteger oldActor,BigInteger newActor){
        StrictJson.require(aux.has("family_marriage_ledger"),"actual family ledger presence/absence source required");if(aux.get("family_marriage_ledger").isNull())return;
        ObjectNode family=LifecycleJson.object(aux.get("family_marriage_ledger")).deepCopy();ObjectNode archived=LifecycleJson.row();
        for(String key:List.of("pending","resolved")){JsonNode value=family.get(key);if(value instanceof ObjectNode&&value.path("episode_run_id").isTextual()&&value.get("episode_run_id").textValue().equals(oldRun)){archived.set(key,value.deepCopy());family.putNull(key);}}
        if(archived.isEmpty())return;
        archived.put("source","matched_ordinary_successor_episode");archived.put("source_run_id",oldRun);archived.put("successor_run_id",newRun);archived.put("predecessor_character_id",oldActor);archived.put("actual_successor_character_id",newActor);
        ArrayNode history=family.has("episode_history")?(ArrayNode)family.get("episode_history"):family.putArray("episode_history");history.add(archived);aux.set("family_marriage_ledger",family);
    }
    private static ObjectNode recordEpisode(DriverStateSnapshot.Complete old,ObjectNode terminal,JsonNode original,Instant at){
        StrictJson.require(original instanceof ObjectNode,"actual initialized canonical strategy object required; null is not an empty life");
        var previous=CrossRunStrategySource.decode(OpportunityJson.object(LifecycleJson.immutable(original),"original canonical cross-run strategy")).state();
        var history=old.commandHistory().stream().map(item->OpportunityJson.object(
                LifecycleJson.immutable(LifecycleJson.parse(item.originalRow().json(),LifecycleProofCodec.MAX_RESULT_BYTES)),
                "complete original terminal predecessor history")).toList();
        var actual=OpportunityJson.object(LifecycleJson.immutable(terminal),"actual scored terminal result");
        var produced=CrossRunPlanning.recordScoredTerminal(previous,old.session().episodeRunId(),history,actual,at);
        ObjectNode strategy=LifecycleJson.parse(CrossRunPlanning.encodeState(produced),CrossRunPlanning.MAX_BYTES);
        strategy.set("recorded_episode",OpportunityJson.toNode(CrossRunPlanning.episodeJson(produced.episodes().getLast())));
        return strategy;
    }
}

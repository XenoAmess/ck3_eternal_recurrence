package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyNextEpisodeMigration.Episode;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Full-body DATA regression only. Actual SAVE/private restore/CAS/FamilyDomainSource is checked by the managed Root consumer. */
final class FamilyOrdinaryRestoreMigrationTest {
    private static final List<Slot> SLOTS=List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE);
    private static final SessionIdentity SAVED=owner(123,"saved-session",1), FIRST=owner(456,"first-restored-session",2),
            SECOND=owner(789,"second-restored-session",3);
    private static final Episode EPISODE=new Episode("same-saved-episode",BigInteger.valueOf(202));

    @Test void naturalNextAndUnmarkedBodiesPreserveActiveUnknownRecordsAndRejectTheOldPhysicalOwner() {
        for(Slot slot:SLOTS)for(String marker:List.of("natural","next","unmarked")) {
            byte[] saved=body(slot,marker), before=saved.clone();
            ObjectNode changed=object(StrictJson.parse(before));object(changed.get("pending")).put("retained_after_save_extension","do-not-lose");
            byte[] previous=StrictJson.canonical(changed);
            var transition=transition(saved,previous,SAVED,FIRST,"restore-one");
            byte[] actual=FamilyOrdinaryRestoreMigration.derive(slot,saved,previous,transition);
            assertArrayEquals(before,saved,"the genuine saved source bytes remain separate");
            ObjectNode output=object(StrictJson.parse(actual)), input=object(StrictJson.parse(previous));
            for(String field:List.of("pending","resolved","episode_history","unknown_extension"))assertEquals(input.get(field),output.get(field));
            JsonNode entry=output.get(FamilyOrdinaryRestoreMigration.HISTORY).get(0);
            assertEquals(transition,FamilyOrdinaryRestoreMigration.Transition.fromJson(entry.get("transition")));
            assertFalse(entry.get("ck3_command_submitted").booleanValue());assertFalse(entry.get("relation_completion_credit").booleanValue());
            assertEquals(input.has(FamilyNaturalEpisodeMigration.FIELD)?input.get(FamilyNaturalEpisodeMigration.FIELD):com.fasterxml.jackson.databind.node.NullNode.instance,
                    entry.get("previous_natural_episode_binding"));
            assertEquals(input.has(FamilyNextEpisodeMigration.FIELD)?input.get(FamilyNextEpisodeMigration.FIELD):com.fasterxml.jackson.databind.node.NullNode.instance,
                    entry.get("previous_next_episode_binding"));
            requireCurrent(slot,actual,FIRST,EPISODE);
            assertThrows(IllegalArgumentException.class,()->requireCurrent(slot,actual,SAVED,EPISODE));
            assertThrows(IllegalArgumentException.class,()->requireCurrent(slot,actual,FIRST,new Episode("foreign-episode",EPISODE.player())));
            assertEquals(FamilyDomainSource.validate(slot,actual),FamilyDomainSource.validate(slot,DriverJson.encode(FamilyDomainSource.validate(slot,actual))));
        }
    }

    @Test void repeatingTheOriginalSaveKeepsTheFirstRebindHistoryAndDoesNotClearAnyPendingToken() {
        for(Slot slot:SLOTS)for(String marker:List.of("natural","next","unmarked")) {
            byte[] saved=body(slot,marker);
            byte[] first=FamilyOrdinaryRestoreMigration.derive(slot,saved,saved,transition(saved,saved,SAVED,FIRST,"restore-one"));
            byte[] second=FamilyOrdinaryRestoreMigration.derive(slot,saved,first,transition(saved,first,FIRST,SECOND,"restore-two"));
            ObjectNode a=object(StrictJson.parse(first)),b=object(StrictJson.parse(second));
            assertEquals(2,b.get(FamilyOrdinaryRestoreMigration.HISTORY).size());
            assertEquals(a.get(FamilyOrdinaryRestoreMigration.HISTORY).get(0),b.get(FamilyOrdinaryRestoreMigration.HISTORY).get(0));
            for(String field:List.of("pending","resolved","episode_history","unknown_extension"))assertEquals(a.get(field),b.get(field));
            requireCurrent(slot,second,SECOND,EPISODE);
            assertThrows(IllegalArgumentException.class,()->requireCurrent(slot,second,FIRST,EPISODE));
            var successor=new Episode("later-natural-episode",BigInteger.valueOf(303));
            byte[] later=FamilyNaturalEpisodeMigration.derive(slot,second,new FamilyNaturalEpisodeMigration.Transition(
                    SECOND,EPISODE,successor,reference("real-lifecycle-data",new byte[]{8}),reference("second-full-body",second)));
            requireCurrent(slot,later,SECOND,successor);
            assertEquals(b.get(FamilyOrdinaryRestoreMigration.HISTORY),StrictJson.parse(later).get(FamilyOrdinaryRestoreMigration.HISTORY));
        }
    }

    @Test void partialImportResumeAcceptsOnlyTheExactPredecessorOrExactDerivedOutput() {
        for(Slot slot:SLOTS) {
            byte[] saved=body(slot,"natural");var transition=transition(saved,saved,SAVED,FIRST,"restore-one");
            byte[] output=FamilyOrdinaryRestoreMigration.derive(slot,saved,saved,transition);
            assertDoesNotThrow(()->FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(slot,saved,saved,saved,transition));
            assertDoesNotThrow(()->FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(slot,saved,saved,output,transition));
            ObjectNode altered=object(StrictJson.parse(output));object(altered.get("pending")).put("candidate_character_id",999);
            assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(
                    slot,saved,saved,StrictJson.canonical(altered),transition));
            var foreign=transition(saved,saved,SAVED,FIRST,"foreign-restoration");
            assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.requireCompatibleCurrent(slot,saved,saved,output,foreign));
        }
    }

    @Test void strictTransitionAndSourceValidationRejectWrongTypesOwnerEpisodeAndMissingPins() {
        byte[] saved=body(Slot.FAMILY,"natural");var transition=transition(saved,saved,SAVED,FIRST,"restore-one");
        assertEquals(transition,FamilyOrdinaryRestoreMigration.Transition.fromJson(StrictJson.parse(StrictJson.canonical(transition.toJson()))));
        for(String field:List.of("saved_owner","before_owner","after_owner","episode","saved_material","restoration_basis","saved_body","previous_body")) {
            ObjectNode absent=transition.toJson();absent.remove(field);
            assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.Transition.fromJson(absent));
            ObjectNode nullable=transition.toJson();nullable.putNull(field);
            assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.Transition.fromJson(nullable));
        }
        ObjectNode bool=transition.toJson();object(bool.get("episode")).put("played_character_id",true);
        assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.Transition.fromJson(bool));
        ObjectNode extra=transition.toJson();extra.put("qualified",true);
        assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.Transition.fromJson(extra));
        var wrongBefore=transition(saved,saved,SECOND,FIRST,"wrong-before");
        assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.derive(Slot.FAMILY,saved,saved,wrongBefore));
        byte[] corrupt=saved.clone();corrupt[corrupt.length-1]=' ';
        assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.derive(Slot.FAMILY,saved,corrupt,transition));
        ObjectNode wrong=object(StrictJson.parse(saved));object(wrong.get("pending")).put("episode_run_id","other");
        byte[] foreign=StrictJson.canonical(wrong);
        assertThrows(IllegalArgumentException.class,()->FamilyOrdinaryRestoreMigration.derive(Slot.FAMILY,saved,foreign,transition(saved,foreign,SAVED,FIRST,"wrong-episode")));
        assertThrows(IllegalArgumentException.class,()->transition(saved,saved,SAVED,SAVED,"same-owner"));
    }

    private static void requireCurrent(Slot slot,byte[] bytes,SessionIdentity owner,Episode episode) {
        var body=FamilyDomainSource.validate(slot,bytes);var request=request(owner,episode);
        FamilyOrdinaryRestoreMigration.requireCurrent(body,request);FamilyNextEpisodeMigration.requireCurrent(body,request);
    }
    private static byte[] body(Slot slot,String marker) {
        ObjectNode body=StrictJson.object().put("schema",FamilyDomainSource.schema(slot));
        for(String field:List.of("pending","resolved"))body.putObject(field).put("episode_run_id",EPISODE.runId()).put("played_character_id",EPISODE.player())
                .put("heir_character_id",11).put("candidate_character_id",12).put("source_bridge_pid",123).put("source_bridge_creation_date","saved-bridge")
                .put("pre_native_revision",5).put("status",field.equals("pending")?"receipt_pending":"refused")
                .put("java_action_id","original-unknown-never-resubmit").putObject("opaque_original").put("keep",true);
        body.putArray("episode_history").addObject().put("source","older-preserved-episode");
        body.putObject("unknown_extension").putArray("values").addNull().add(false).add(7);
        var predecessor=new Episode("older-episode",BigInteger.valueOf(101));
        if(marker.equals("natural"))body.set(FamilyNaturalEpisodeMigration.FIELD,new FamilyNaturalEpisodeMigration.Transition(
                SAVED,predecessor,EPISODE,reference("lifecycle",new byte[]{1}),reference("pre-natural",new byte[]{2})).toJson());
        if(marker.equals("next"))body.set(FamilyNextEpisodeMigration.FIELD,new FamilyNextEpisodeMigration.Transition(
                owner(99,"older-session",9),SAVED,predecessor,EPISODE,reference("baseline",new byte[]{3}),reference("pre-next",new byte[]{4})).toJson());
        return StrictJson.canonical(body);
    }
    private static FamilyOrdinaryRestoreMigration.Transition transition(byte[] saved,byte[] previous,SessionIdentity before,SessionIdentity after,String name) {
        return new FamilyOrdinaryRestoreMigration.Transition(SAVED,before,after,EPISODE,reference("saved-material",new byte[]{5}),
                reference(name,new byte[]{6}),reference("saved-full-body",saved),reference("previous-full-body",previous));
    }
    private static ExactRef reference(String name,byte[] bytes){return new ExactRef("D:/synthetic-family-ordinary-restore/"+name,bytes.length,ActionCodec.sha256(bytes));}
    private static SessionIdentity owner(long pid,String session,long birth){return new SessionIdentity("fixture-family-restore-machine",new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(birth))),session);}
    private static ObjectNode object(JsonNode value){if(!(value instanceof ObjectNode object))throw new IllegalArgumentException("fixture object required");return object;}
    private static PlanningRequest request(SessionIdentity owner,Episode episode) {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(episode.player(),BigInteger.ONE,BigInteger.ONE),"fixture",BigInteger.ONE,episode.runId());
        var identity=new ObservationIdentity(owner.machineId(),owner.game(),frame,1);
        ObjectNode snapshot=StrictJson.object().put("snapshot_id",frame.snapshotId()).put("revision",frame.revision()).put("native_revision",BigInteger.ONE)
                .put("date_raw",BigInteger.ONE).put("episode_run_id",episode.runId()).put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",episode.player());snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        return new PlanningRequest(identity,new G2Source(owner.machineId(),"2026-10-27T00:00:00Z","fixture-build",reference("source",new byte[]{1})),owner.sessionId(),
                Instant.parse("2099-01-01T00:00:00Z"),new PlanningObservation(DriverJson.object(StrictJson.canonical(snapshot),DriverJson.MAX_NATIVE_BYTES),
                List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
}

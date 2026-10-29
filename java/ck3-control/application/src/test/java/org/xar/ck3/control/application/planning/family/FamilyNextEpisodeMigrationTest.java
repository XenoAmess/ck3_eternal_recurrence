package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure full-body producer -> JSON -> the actual Family consumer guards. Does not mint a private Root proof. */
final class FamilyNextEpisodeMigrationTest {
    private static final List<Slot> SLOTS=List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE);
    private static final String MACHINE="fixture-family-next-machine";
    private static final SessionIdentity BEFORE=owner(123,"before",1),AFTER=owner(456,"after",2);
    private static final FamilyNextEpisodeMigration.Episode OLD=new FamilyNextEpisodeMigration.Episode("original-episode",BigInteger.valueOf(101));
    private static final FamilyNextEpisodeMigration.Episode NEW=new FamilyNextEpisodeMigration.Episode("new-episode",BigInteger.valueOf(202));
    @Test void threeFullDomainProducersKeepAllOriginalRecordsAndExtensionsAndBindOnlyTheNewEpisode() {
        for(Slot slot:SLOTS) {
            byte[] original=original(slot);var transition=transition(original,NEW);byte[] result=FamilyNextEpisodeMigration.derive(slot,original,transition);
            var decoded=FamilyDomainSource.validate(slot,result);var body=DriverJson.toNode(decoded);var prior=StrictJson.parse(original);
            assertTrue(body.get("pending").isNull());assertTrue(body.get("resolved").isNull());
            assertEquals(prior.get("extension"),body.get("extension"));assertEquals(prior.get("episode_history").get(0),body.get("episode_history").get(0));
            var archived=body.get("episode_history").get(1);assertEquals(prior.get("pending"),archived.get("pending"));assertEquals(prior.get("resolved"),archived.get("resolved"));
            assertEquals("retained_original_unresolved_no_replay",archived.get("pending_status").textValue());assertFalse(archived.get("ck3_command_submitted").booleanValue());assertFalse(archived.get("relation_completion_credit").booleanValue());
            assertEquals(transition,FamilyNextEpisodeMigration.Transition.fromJson(body.get(FamilyNextEpisodeMigration.FIELD)));
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(decoded,request(AFTER,NEW)));
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(decoded,request(BEFORE,OLD)));
            assertEquals(decoded,FamilyDomainSource.validate(slot,DriverJson.encode(decoded)));
        }
    }
    @Test void aRestartWithTheSameActualCharacterStillHasDistinctGameSessionAndEpisode() {
        byte[] original=original(Slot.FAMILY);var newEpisode=new FamilyNextEpisodeMigration.Episode("new-episode",OLD.player());
        var changed=FamilyDomainSource.validate(Slot.FAMILY,FamilyNextEpisodeMigration.derive(Slot.FAMILY,original,transition(original,newEpisode)));
        assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(changed,request(AFTER,newEpisode)));
        assertThrows(IllegalArgumentException.class,()->new FamilyNextEpisodeMigration.Transition(BEFORE,BEFORE,OLD,newEpisode,reference("baseline",new byte[]{1}),reference("old",original)));
        assertThrows(IllegalArgumentException.class,()->new FamilyNextEpisodeMigration.Transition(BEFORE,AFTER,OLD,OLD,reference("baseline",new byte[]{1}),reference("old",original)));
    }
    @Test void anotherEpisodeOrActualPlayerCannotBeSilentlyClearedToQualifyTheNewDomain() {
        var wrong=requireObject(StrictJson.parse(original(Slot.FAMILY)));((ObjectNode)wrong.get("pending")).put("episode_run_id","unrelated");reject(Slot.FAMILY,StrictJson.canonical(wrong));
        wrong=requireObject(StrictJson.parse(original(Slot.FAMILY)));((ObjectNode)wrong.get("resolved")).put("played_character_id",999);reject(Slot.FAMILY,StrictJson.canonical(wrong));
        wrong=requireObject(StrictJson.parse(original(Slot.FAMILY)));wrong.remove("pending");reject(Slot.FAMILY,StrictJson.canonical(wrong));
        wrong=requireObject(StrictJson.parse(original(Slot.FAMILY)));wrong.putNull("episode_history");reject(Slot.FAMILY,StrictJson.canonical(wrong));
        wrong=requireObject(StrictJson.parse(original(Slot.DEFAULT_MARRIAGE)));((ObjectNode)wrong.get("pending")).put("played_character_id",101.0);
        // Keep the malformed wire number for the actual derive input; the strict producer encoder rejects it.
        reject(Slot.DEFAULT_MARRIAGE,wrong.toString().getBytes(StandardCharsets.UTF_8));
    }
    @Test void migratedConsumerRefusesWrongSessionGameSnapshotOrPlayerDespiteMatchingBodyShape() {
        var original=original(Slot.CHILD_MATRILINEAL);var body=FamilyDomainSource.validate(Slot.CHILD_MATRILINEAL,FamilyNextEpisodeMigration.derive(Slot.CHILD_MATRILINEAL,original,transition(original,NEW)));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(body,request(owner(456,"wrong-session",2),NEW)));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(body,request(owner(457,"after",3),NEW)));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(body,request(AFTER,new FamilyNextEpisodeMigration.Episode(NEW.runId(),BigInteger.valueOf(203)))));
        var changed=request(AFTER,NEW);var snapshot=requireObject(DriverJson.toNode(changed.observations().snapshot()));snapshot.put("episode_run_id","old-episode");
        var observation=new PlanningObservation(DriverJson.object(StrictJson.canonical(snapshot),DriverJson.MAX_NATIVE_BYTES),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(body,new PlanningRequest(changed.before(),changed.source(),changed.sessionId(),changed.deadline(),observation)));
    }
    @Test void originalContentPinAndClosedTransitionSerializationAreMandatory() {
        byte[] original=original(Slot.DEFAULT_MARRIAGE);var transition=transition(original,NEW);var encoded=transition.toJson();assertEquals(transition,FamilyNextEpisodeMigration.Transition.fromJson(StrictJson.parse(StrictJson.canonical(encoded))));
        var modified=requireObject(StrictJson.parse(original));modified.put("extra_after_capture",true);
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.derive(Slot.DEFAULT_MARRIAGE,StrictJson.canonical(modified),transition));
        for(String field:List.of("before_owner","after_owner","before_episode","after_episode","baseline_material","previous_body")) {
            var missing=encoded.deepCopy();missing.remove(field);assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.Transition.fromJson(missing));
            var nullable=encoded.deepCopy();nullable.putNull(field);assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.Transition.fromJson(nullable));
        }
        var alias=encoded.deepCopy();alias.put("extra",true);assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.Transition.fromJson(alias));
        var bool=encoded.deepCopy();((ObjectNode)bool.get("after_episode")).put("played_character_id",true);assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.Transition.fromJson(bool));
    }
    @Test void nextMigrationUsesTheActualPreviouslyInitializedOwnerAndKeepsPriorHistoryIntact() {
        byte[] initial=original(Slot.FAMILY);byte[] first=FamilyNextEpisodeMigration.derive(Slot.FAMILY,initial,transition(initial,NEW));
        var thirdOwner=owner(789,"third",3);var third=new FamilyNextEpisodeMigration.Episode("third-episode",BigInteger.valueOf(303));
        var valid=new FamilyNextEpisodeMigration.Transition(AFTER,thirdOwner,NEW,third,reference("baseline3",new byte[]{3}),reference("previous",first));
        var result=FamilyDomainSource.validate(Slot.FAMILY,FamilyNextEpisodeMigration.derive(Slot.FAMILY,first,valid));
        assertEquals(3,DriverJson.toNode(result).get("episode_history").size());assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(result,request(thirdOwner,third)));
        var wrong=new FamilyNextEpisodeMigration.Transition(BEFORE,thirdOwner,OLD,third,reference("baseline3",new byte[]{3}),reference("previous",first));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.derive(Slot.FAMILY,first,wrong));
    }
    @Test void firstColdRestoreRebindsCurrentPhysicalOwnerWithoutArchivingOriginalRecordsAgain() {
        var restoredOwner=owner(901,"restored",9);
        for(Slot slot:SLOTS) {
            byte[] original=original(slot);var originalTransition=transition(original,NEW);byte[] next=FamilyNextEpisodeMigration.derive(slot,original,originalTransition);
            var restored=new FamilyNextEpisodeMigration.Transition(BEFORE,restoredOwner,OLD,NEW,originalTransition.baselineMaterial(),originalTransition.previousBody());
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCompatibleCurrent(slot,original,next,restored));
            byte[] output=FamilyNextEpisodeMigration.derive(slot,original,restored);var restoredBody=FamilyDomainSource.validate(slot,output);
            assertEquals(StrictJson.parse(next).get("episode_history"),StrictJson.parse(output).get("episode_history"));
            assertEquals(2,StrictJson.parse(output).get("episode_history").size());
            assertEquals(originalTransition.baselineMaterial(),FamilyNextEpisodeMigration.Transition.fromJson(StrictJson.parse(output).get(FamilyNextEpisodeMigration.FIELD)).baselineMaterial());
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(restoredBody,request(restoredOwner,NEW)));
            assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(restoredBody,request(AFTER,NEW)));
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCompatibleCurrent(slot,original,output,restored));
        }
    }
    @Test void partialRestoreUsesTheSameBaselineTransformForOriginalNextAndAlreadyRestoredSlots() {
        var restoredOwner=owner(902,"restored-partial",10);int index=0;
        for(Slot slot:SLOTS) {
            byte[] original=original(slot);var next=transition(original,NEW);
            var restored=new FamilyNextEpisodeMigration.Transition(BEFORE,restoredOwner,OLD,NEW,next.baselineMaterial(),next.previousBody());
            byte[] desired=FamilyNextEpisodeMigration.derive(slot,original,restored);
            byte[] current=switch(index++){case 0->original;case 1->FamilyNextEpisodeMigration.derive(slot,original,next);default->desired;};
            assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCompatibleCurrent(slot,original,current,restored));
            assertArrayEquals(desired,FamilyNextEpisodeMigration.derive(slot,original,FamilyNextEpisodeMigration.Transition.fromJson(restored.toJson())));
        }
    }
    @Test void restoreCannotBorrowAnotherBaselineOrErasePostInitializationBusinessMutations() {
        byte[] original=original(Slot.FAMILY);var next=transition(original,NEW);byte[] initialized=FamilyNextEpisodeMigration.derive(Slot.FAMILY,original,next);
        var wrongBaseline=new FamilyNextEpisodeMigration.Transition(BEFORE,owner(903,"restore-wrong",11),OLD,NEW,reference("foreign-baseline",new byte[]{9}),next.previousBody());
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCompatibleCurrent(Slot.FAMILY,original,initialized,wrongBaseline));
        var restored=new FamilyNextEpisodeMigration.Transition(BEFORE,owner(903,"restored",11),OLD,NEW,next.baselineMaterial(),next.previousBody());
        var changed=requireObject(StrictJson.parse(initialized));changed.put("business_after_initialization",true);
        byte[] businessChanged=StrictJson.canonical(changed);
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCompatibleCurrent(Slot.FAMILY,original,businessChanged,restored));
        changed=requireObject(StrictJson.parse(initialized));changed.putArray("episode_history");byte[] lost=StrictJson.canonical(changed);
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCompatibleCurrent(Slot.FAMILY,original,lost,restored));
        var foreign=requireObject(StrictJson.parse(original));foreign.put("unrelated_full_body",true);byte[] different=StrictJson.canonical(foreign);
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCompatibleCurrent(Slot.FAMILY,different,initialized,restored));
    }
    @Test void exactNewPhysicalOwnerMayReuseALogicalSessionLabelWithoutReusingTheOldGame() {
        byte[] original=original(Slot.DEFAULT_MARRIAGE);var restoredOwner=owner(904,BEFORE.sessionId(),12);
        var restored=new FamilyNextEpisodeMigration.Transition(BEFORE,restoredOwner,OLD,NEW,reference("baseline",new byte[]{1}),reference("previous",original));
        var body=FamilyDomainSource.validate(Slot.DEFAULT_MARRIAGE,FamilyNextEpisodeMigration.derive(Slot.DEFAULT_MARRIAGE,original,restored));
        assertDoesNotThrow(()->FamilyNextEpisodeMigration.requireCurrent(body,request(restoredOwner,NEW)));
        assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.requireCurrent(body,request(BEFORE,NEW)));
    }
    private static ObjectNode requireObject(JsonNode node) {
        if (!(node instanceof ObjectNode object)) throw new IllegalArgumentException("Expected JSON object");
        return object;
    }
    private static byte[] original(Slot slot) {
        var body=StrictJson.object().put("schema",FamilyDomainSource.schema(slot));
        for(String field:List.of("pending","resolved"))body.putObject(field).put("episode_run_id",OLD.runId()).put("played_character_id",101).put("heir_character_id",11).put("candidate_character_id",12)
                .put("source_bridge_pid",123).put("source_bridge_creation_date","2026-10-24T00:00:00.0000000Z").put("pre_native_revision",1).put("unknown_original_extension","retained");
        body.putObject("extension").put("keep",true).putArray("values").add(7).addNull();body.putArray("episode_history").addObject().put("source","prior-real-history");return StrictJson.canonical(body);
    }
    private static FamilyNextEpisodeMigration.Transition transition(byte[] original,FamilyNextEpisodeMigration.Episode after) {return new FamilyNextEpisodeMigration.Transition(BEFORE,AFTER,OLD,after,reference("baseline",new byte[]{1}),reference("previous",original));}
    private static ExactRef reference(String name,byte[] bytes) {return new ExactRef("D:/synthetic-family-next/"+name,bytes.length,ActionCodec.sha256(bytes));}
    private static SessionIdentity owner(long pid,String session,long born) {return new SessionIdentity(MACHINE,new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(born))),session);}
    private static PlanningRequest request(SessionIdentity owner,FamilyNextEpisodeMigration.Episode episode) {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(episode.player(),BigInteger.ONE,BigInteger.ONE),"synthetic",BigInteger.ONE,episode.runId());
        var identity=new ObservationIdentity(MACHINE,owner.game(),frame,1);
        var snapshot=StrictJson.object().put("snapshot_id",frame.snapshotId()).put("revision",frame.revision())
                .put("native_revision",frame.identity().nativeRevision()).put("date_raw",frame.identity().dateRaw())
                .put("episode_run_id",episode.runId()).put("paused",true).put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",episode.player());
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        return new PlanningRequest(identity,new G2Source(MACHINE,"2026-10-24T00:00:00Z","fixture-build",reference("source",new byte[]{1})),owner.sessionId(),Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(DriverJson.object(StrictJson.canonical(snapshot),DriverJson.MAX_NATIVE_BYTES),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static void reject(Slot slot,byte[] body) {assertThrows(IllegalArgumentException.class,()->FamilyNextEpisodeMigration.derive(slot,body,transition(body,NEW)));}
}

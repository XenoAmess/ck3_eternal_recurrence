package org.xar.ck3.control.application.planning.prisoners;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerEpisodeLedger12004.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;

/** Synthetic DATA only: the real private Core proof cannot be minted by this fixture. */
final class PrisonerFirstInitialization12004Test {
    private static final Instant NOW=Instant.parse("2026-10-24T01:00:00Z");
    private static final ExactRef ORIGINAL=new ExactRef("D:/software/first-original",1,"a".repeat(64));
    private static final ExactRef MATERIAL=new ExactRef("D:/software/first-baselined",2,"b".repeat(64));
    private static final Baseline BASELINE=new Baseline(12,"c".repeat(64));
    private static Owner owner(int generation,long actor,String episode) {
        var game=new GameGeneration(700+generation,new PythonOnlyUInt64(new BigInteger("133700000000000001").add(BigInteger.valueOf(generation))));
        var source=new G2Source("software-first-machine",NOW.plusSeconds(generation).toString(),"1.20.0.4",ORIGINAL);
        return new Owner(new SessionIdentity(source.machineId(),game,"physical-"+generation),actor,episode,source);
    }
    private static ObservationIdentity frame(Owner owner,long nativeRevision) {
        var identity=new JointBudgetSelector.Frame(BigInteger.valueOf(owner.player()),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(100));
        return new ObservationIdentity(owner.session().machineId(),owner.session().game(),
                new JointBudgetSelector.ProposalFrame(identity,"native:"+nativeRevision,BigInteger.valueOf(nativeRevision+1),owner.episodeRunId()),1);
    }
    private static InitializationOrigins restored(Owner saved,Owner current) {
        return new InitializationOrigins(InitializationKind.RESTORED_FIRST,saved.session(),frame(saved,600),current,frame(current,2),new Baseline(21,"d".repeat(64)));
    }
    private static RawJson pending(Family family,long player) {
        var row=StrictJson.object().put("stage","submission_unresolved").put("action_id","original-unknown-action").put("player_character_id",player)
                .put("prisoner_character_id",0xFE000001L).put("pre_native_revision",8).put("pre_date_raw",99).put("material_result",false);
        if(family==Family.RELEASE){row.put("release_query_sequence",8).put("release_option_mask_bits",0).putArray("release_option_keys");row.putObject("costs");row.putObject("acceptance");}
        else row.put("payer_character_id",9001).put("selected_option","gold").put("amount_is_acceptance_time_quote",false).put("quoted_gold_raw",500).put("pre_player_gold_raw",1000000);
        return new RawJson(StrictJson.canonical(row));
    }
    private static RawJson originalBody(Family family,Owner old) {
        var original=decode(family,fresh(family,old,ORIGINAL));
        return encode(new Ledger(family,original.epoch(),Optional.of(pending(family,old.player())),Optional.empty(),List.of()));
    }
    private static DomainBodies.BodyRef reference(Family family,RawJson body) {
        var digest=ActionCodec.sha256(body.bytes());var ref=new ExactRef("D:/software/first-"+family+"-"+digest,body.bytes().length,digest);
        return new DomainBodies.BodyRef(family==Family.RELEASE?DomainBodies.Slot.PRISONER_RELEASE:DomainBodies.Slot.PRISONER_RANSOM,contractSchema(family),ref,
                new WriterContracts.FileIdentity("18446744073709551614","18446744073709551613","133700000000000001",NOW.toString(),ref.bytes()),List.of(ORIGINAL));
    }
    private static Epoch epoch(Owner old,Owner actual,DomainBodies.BodyRef oldRef,long revision) {
        var actualReceipt=new ExactRef("D:/software/current-query-"+actual.session().sessionId(),3,"e".repeat(64));
        var observed=new Collection(actualReceipt,frame(actual,revision),new BigInteger("18446744073709551614"),List.of(0xFE000001L));
        return new Epoch(Kind.NEXT,actual,MATERIAL,Optional.of(BASELINE),Optional.of(new Predecessor(old,oldRef)),Optional.of(observed));
    }
    @Test void nextAndRestoredFirstOriginsKeepOriginalSaveAndCurrentPhysicalIdentitySeparateThroughJson() {
        var saved=owner(2,8,"episode-next");var actual=owner(3,8,"episode-next");
        var next=new InitializationOrigins(InitializationKind.NEXT,saved.session(),frame(saved,600),saved,frame(saved,600),BASELINE);
        assertEquals(next,origins(StrictJson.parse(StrictJson.canonical(origins(next)))));
        var restored=restored(saved,actual);var roundTrip=origins(StrictJson.parse(StrictJson.canonical(origins(restored))));
        assertEquals(restored,roundTrip);assertNotEquals(roundTrip.savedSession().game(),roundTrip.currentOwner().session().game());
        assertEquals(BigInteger.valueOf(600),roundTrip.savedFrame().frame().identity().nativeRevision());
        assertEquals(BigInteger.TWO,roundTrip.currentFrame().frame().identity().nativeRevision());
        assertEquals(21,roundTrip.initializationHead().sequence());assertNotEquals(BASELINE,roundTrip.initializationHead());
        assertEquals("133700000000000003",StrictJson.parse(StrictJson.canonical(origins(roundTrip))).path("saved_session").path("game").path("creation_filetime").textValue());
    }
    @Test void restoredReducerUsesOnlyImmutableOldDomainAndDoesNotArchiveTheSavedNextBodyAsAnotherUnknown() {
        var old=owner(1,7,"episode-old");var saved=owner(2,8,"episode-next");var current=owner(3,8,"episode-next");
        var bodies=new EnumMap<Family,RawJson>(Family.class);
        for(Family family:Family.values()){
            var original=originalBody(family,old);var originalRef=reference(family,original);
            var savedBody=PrisonerEpisodeLedger12004.next(family,original,old,originalRef,epoch(old,saved,originalRef,600));
            var restoredBody=PrisonerEpisodeLedger12004.next(family,original,old,originalRef,epoch(old,current,originalRef,2));
            assertFalse(java.util.Arrays.equals(savedBody.bytes(),restoredBody.bytes()));
            var decoded=decode(family,restoredBody);assertEquals(current,decoded.epoch().owner());assertEquals(originalRef,decoded.epoch().predecessor().orElseThrow().body());
            assertEquals(1,decoded.inheritedUnknowns().size());assertEquals(old,decoded.inheritedUnknowns().getFirst().owner());
            assertEquals(pending(family,old.player()),decoded.inheritedUnknowns().getFirst().originalPending());assertTrue(decoded.pending().isEmpty());
            assertThrows(IllegalArgumentException.class,()->PrisonerEpisodeLedger12004.next(family,savedBody,old,originalRef,epoch(old,current,originalRef,2)));
            assertArrayEquals(restoredBody.bytes(),PrisonerEpisodeLedger12004.next(family,original,old,originalRef,epoch(old,current,originalRef,2)).bytes());
            bodies.put(family,restoredBody);
        }
        var store=new DomainBodies.Store(){
            @Override public DomainBodies.Read read(DomainBodies.Slot slot){var family=slot==DomainBodies.Slot.PRISONER_RELEASE?Family.RELEASE:Family.RANSOM;var body=bodies.get(family);return new DomainBodies.Available(reference(family,body),body.bytes(),MATERIAL,List.of());}
            @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request){throw new AssertionError("reader has no import authority");}
            @Override public WriterContracts.Receipt commitImport(DomainBodies.PreparedImport request){throw new AssertionError("reader has no import authority");}
        };
        var reader=new PrisonerDomainBodyReader12004(store,current.session().machineId());
        assertInstanceOf(KnownLedger.class,reader.read(request(current,2)));
        assertInstanceOf(LedgerUnavailable.class,reader.read(request(saved,600)));
        assertInstanceOf(LedgerUnavailable.class,reader.read(request(old,8)));
    }
    private static PlanningRequest request(Owner owner,long revision) {
        var observed=frame(owner,revision);var f=observed.frame();var n=StrictJson.object().put("paused",true).put("map_ready",true).put("revision",f.revision())
                .put("native_revision",f.identity().nativeRevision()).put("date_raw",f.identity().dateRaw()).put("snapshot_id",f.snapshotId()).put("episode_run_id",f.episodeRunId());
        n.putObject("played_character").put("character_id",owner.player());n.putArray("active_wars");n.putArray("player_armies");
        return new PlanningRequest(observed,owner.source(),owner.session().sessionId(),NOW.plusSeconds(30),
                new PlanningObservation(object(StrictJson.canonical(n)),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    @Test void restoredOriginCannotBorrowTheOriginalSavedGameOrCrossActorEpisodeAndDay() {
        var saved=owner(2,8,"episode-next");var current=owner(3,8,"episode-next");
        assertThrows(IllegalArgumentException.class,()->new InitializationOrigins(InitializationKind.RESTORED_FIRST,saved.session(),frame(saved,600),saved,frame(saved,2),BASELINE));
        assertThrows(IllegalArgumentException.class,()->new InitializationOrigins(InitializationKind.NEXT,saved.session(),frame(saved,600),current,frame(current,2),BASELINE));
        var otherActor=owner(3,9,"episode-next");assertThrows(IllegalArgumentException.class,()->restored(saved,otherActor));
        var otherEpisode=owner(3,8,"episode-other");assertThrows(IllegalArgumentException.class,()->restored(saved,otherEpisode));
        var f=frame(current,2);var wrongDay=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(8),BigInteger.TWO,BigInteger.valueOf(101)),f.frame().snapshotId(),f.frame().revision(),current.episodeRunId());
        assertThrows(IllegalArgumentException.class,()->new InitializationOrigins(InitializationKind.RESTORED_FIRST,saved.session(),frame(saved,600),current,
                new ObservationIdentity(current.session().machineId(),current.session().game(),wrongDay,1),BASELINE));
    }
    @Test void originBoundaryRejectsMissingNullUnknownKindAndNumericFiletimeRatherThanAliasingAnOldProof() {
        var saved=owner(2,8,"episode-next");var current=owner(3,8,"episode-next");var valid=origins(restored(saved,current));
        var missing=valid.deepCopy();missing.remove("current_owner");assertThrows(IllegalArgumentException.class,()->origins(missing));
        var nil=valid.deepCopy();nil.putNull("saved_session");assertThrows(IllegalArgumentException.class,()->origins(nil));
        var kind=valid.deepCopy();kind.put("kind","RESTORED");assertThrows(IllegalArgumentException.class,()->origins(kind));
        var numeric=valid.deepCopy();((ObjectNode)numeric.path("saved_session").path("game")).put("creation_filetime",133700000000000003L);
        assertThrows(IllegalArgumentException.class,()->origins(numeric));
        var head=valid.deepCopy();((ObjectNode)head.path("initialization_head")).put("sequence",true);assertThrows(IllegalArgumentException.class,()->origins(head));
    }
    @Test void repeatedRestoreRetainsPriorPhysicalBodyAndSourceProofDataWithoutDuplicatingOldUnknown() {
        var old=owner(1,7,"episode-old");var previousPhysical=owner(3,8,"episode-next");var currentPhysical=owner(4,8,"episode-next");
        var original=originalBody(Family.RELEASE,old);var originalRef=reference(Family.RELEASE,original);
        var first=PrisonerEpisodeLedger12004.next(Family.RELEASE,original,old,originalRef,epoch(old,previousPhysical,originalRef,2));
        var previous=decode(Family.RELEASE,first);var previousRef=reference(Family.RELEASE,first);
        var proofRef=new ExactRef("D:/software/prior-source-qualification",11,"f".repeat(64));
        var data=new PriorInitialization(previousRef,previousPhysical,previous.epoch().collection().orElseThrow(),List.of(proofRef));
        var roundTrip=prior(StrictJson.parse(StrictJson.canonical(prior(data))));assertEquals(data,roundTrip);
        assertEquals(previousRef,roundTrip.body());assertEquals(List.of(proofRef),roundTrip.sourceProofs());
        var current=decode(Family.RELEASE,PrisonerEpisodeLedger12004.next(Family.RELEASE,original,old,originalRef,epoch(old,currentPhysical,originalRef,1)));
        assertEquals(currentPhysical,current.epoch().owner());assertEquals(1,current.inheritedUnknowns().size());assertEquals(old,current.inheritedUnknowns().getFirst().owner());
        assertThrows(IllegalArgumentException.class,()->new PriorInitialization(previousRef,currentPhysical,data.collection(),List.of(proofRef)));
        assertThrows(IllegalArgumentException.class,()->new PriorInitialization(previousRef,previousPhysical,data.collection(),List.of()));
        var missing=prior(data);missing.remove("source_proofs");assertThrows(IllegalArgumentException.class,()->prior(missing));
        var wrong=prior(data);((ObjectNode)wrong.path("collection")).put("query_sequence",true);assertThrows(IllegalArgumentException.class,()->prior(wrong));
    }
}

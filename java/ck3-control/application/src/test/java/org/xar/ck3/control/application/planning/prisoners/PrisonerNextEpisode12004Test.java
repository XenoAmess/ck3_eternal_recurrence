package org.xar.ck3.control.application.planning.prisoners;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.EnumMap;
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
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerPlanningPorts.*;
import static org.xar.ck3.control.application.planning.prisoners.PrisonerEpisodeLedger12004.*;

/** Pure production converter -> codec -> actual reader software regression. It cannot construct Root's private NEXT proof or import authority. */
final class PrisonerNextEpisode12004Test {
    private static final ExactRef SOURCE=new ExactRef("D:/software/prisoner-source",1,"a".repeat(64));
    private static final ExactRef BASIS=new ExactRef("D:/software/baseline-material",2,"b".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static Owner owner(int generation,long actor) {
        var game=new GameGeneration(900+generation,new PythonOnlyUInt64(new BigInteger("133700000000000001").add(BigInteger.valueOf(generation))));
        var source=new G2Source("software-prison-machine",NOW.toString(),"1.20.0.4",SOURCE);
        return new Owner(new SessionIdentity(source.machineId(),game,"session-"+generation),actor,"episode-"+generation,source);
    }
    private static ObservationIdentity observed(Owner owner) {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(owner.player()),BigInteger.TEN,BigInteger.valueOf(100)),"native:10",BigInteger.valueOf(20),owner.episodeRunId());
        return new ObservationIdentity(owner.session().machineId(),owner.session().game(),frame,1);
    }
    private static RawJson pending(Family family,long actor) {
        var n=StrictJson.object().put("stage","submission_unresolved").put("player_character_id",actor).put("prisoner_character_id",0xFE000001L)
                .put("pre_native_revision",8).put("pre_date_raw",99).put("action_id","actual-original-unresolved").put("material_result",false);
        if(family==Family.RANSOM)n.put("payer_character_id",7001).put("selected_option","gold").put("amount_is_acceptance_time_quote",false).put("quoted_gold_raw",500).put("pre_player_gold_raw",10000000);
        else {n.put("release_query_sequence",8).put("release_option_mask_bits",0).putArray("release_option_keys");n.putObject("costs");n.putObject("acceptance");}
        return new RawJson(StrictJson.canonical(n));
    }
    private static DomainBodies.BodyRef reference(Family family,RawJson body,String contract) {
        var ref=new ExactRef("D:/software/"+family+"-"+ActionCodec.sha256(body.bytes()),body.bytes().length,ActionCodec.sha256(body.bytes()));
        return new DomainBodies.BodyRef(family==Family.RELEASE?DomainBodies.Slot.PRISONER_RELEASE:DomainBodies.Slot.PRISONER_RANSOM,
                contract,ref,new WriterContracts.FileIdentity("18446744073709551614","18446744073709551613","133700000000000001",NOW.toString(),ref.bytes()),List.of(SOURCE));
    }
    private static Epoch nextEpoch(Owner old,Owner current,DomainBodies.BodyRef ref,List<Long> ids) {
        var collection=new Collection(new ExactRef("D:/software/actual-query-receipt",3,"c".repeat(64)),observed(current),new BigInteger("18446744073709551614"),ids);
        return new Epoch(Kind.NEXT,current,BASIS,Optional.of(new Baseline(12,"d".repeat(64))),Optional.of(new Predecessor(old,ref)),Optional.of(collection));
    }
    private static RawJson unresolved(Family family,Owner old) {
        var initial=decode(family,fresh(family,old,BASIS));
        return encode(new Ledger(family,initial.epoch(),Optional.of(pending(family,old.player())),Optional.of(new RawJson("{\"status\":\"original-preserved-material\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8))),List.of()));
    }
    @Test void bothActualSlotConvertersRetainOldUnknownAndDistinctGameOwnershipThroughJsonRoundTrip() {
        for(Family family:Family.values()){
            var old=owner(1,29829);var current=owner(2,30470);var prior=unresolved(family,old);var ref=reference(family,prior,contractSchema(family));
            var next=PrisonerEpisodeLedger12004.next(family,prior,old,ref,nextEpoch(old,current,ref,List.of(0xFE000001L)));
            var parsed=decode(family,next);PrisonerLedgerReducer12004.validate(family,StrictJson.parse(next.bytes()));
            assertTrue(parsed.pending().isEmpty());assertTrue(parsed.resolved().isEmpty());assertEquals(current,parsed.epoch().owner());
            assertEquals(ref,parsed.epoch().predecessor().orElseThrow().body());assertEquals(1,parsed.inheritedUnknowns().size());
            assertEquals(old,parsed.inheritedUnknowns().getFirst().owner());
            assertEquals(StrictJson.parse(pending(family,old.player()).bytes()),StrictJson.parse(parsed.inheritedUnknowns().getFirst().originalPending().bytes()));
            assertEquals(StrictJson.parse(next.bytes()),StrictJson.parse(encode(parsed).bytes()));
            assertEquals("18446744073709551614",StrictJson.parse(next.bytes()).path("epoch").path("collection").path("query_sequence").textValue());
            assertEquals("18446744073709551613",StrictJson.parse(next.bytes()).path("epoch").path("predecessor").path("body").path("native_identity").path("file_id_decimal").textValue());
            assertThrows(IllegalArgumentException.class,()->parsed.epoch().owner().require(observed(old),old.source(),old.session().sessionId()));
        }
    }
    @Test void anotherNextKeepsCompleteUnknownAncestryWithoutRelaunchingOldAction() {
        var first=owner(1,7);var second=owner(2,8);var third=owner(3,9);var prior=unresolved(Family.RELEASE,first);var priorRef=reference(Family.RELEASE,prior,contractSchema(Family.RELEASE));
        var current=PrisonerEpisodeLedger12004.next(Family.RELEASE,prior,first,priorRef,nextEpoch(first,second,priorRef,List.of()));
        var currentRef=reference(Family.RELEASE,current,contractSchema(Family.RELEASE));
        var next=decode(Family.RELEASE,PrisonerEpisodeLedger12004.next(Family.RELEASE,current,second,currentRef,nextEpoch(second,third,currentRef,List.of(0xFE000001L))));
        assertEquals(1,next.inheritedUnknowns().size());assertEquals(first,next.inheritedUnknowns().getFirst().owner());assertEquals(priorRef,next.inheritedUnknowns().getFirst().originalBody());
        assertEquals(List.of(0xFE000001L),next.epoch().collection().orElseThrow().prisonerIds());assertTrue(next.pending().isEmpty());
    }
    @Test void exactSameBaselineReplayProducesTheSameBothSlotBodiesConsumedByTheActualCurrentReader() {
        var old=owner(1,7);var current=owner(2,8);var currentBodies=new EnumMap<Family,RawJson>(Family.class);
        for(Family family:Family.values()){
            var baselineBody=unresolved(family,old);var original=reference(family,baselineBody,contractSchema(family));
            var actualEpoch=nextEpoch(old,current,original,List.of(0xFE000001L));
            var first=PrisonerEpisodeLedger12004.next(family,baselineBody,old,original,actualEpoch);
            // A partial retry reduces the immutable original BASELINE again; it never uses the first new body as an old actor body.
            var retry=PrisonerEpisodeLedger12004.next(family,baselineBody,old,original,actualEpoch);
            assertArrayEquals(first.bytes(),retry.bytes());currentBodies.put(family,retry);
            assertThrows(IllegalArgumentException.class,()->PrisonerEpisodeLedger12004.next(family,first,old,original,actualEpoch));
        }
        var store=new DomainBodies.Store(){
            @Override public DomainBodies.Read read(DomainBodies.Slot slot){
                Family family=slot==DomainBodies.Slot.PRISONER_RELEASE?Family.RELEASE:Family.RANSOM;RawJson body=currentBodies.get(family);
                return new DomainBodies.Available(reference(family,body,contractSchema(family)),body.bytes(),BASIS,List.of());
            }
            @Override public DomainBodies.PreparedImport previewImport(DomainBodies.ImportRequest request){throw new AssertionError("current read cannot grant imports");}
            @Override public WriterContracts.Receipt commitImport(DomainBodies.PreparedImport request){throw new AssertionError("current read cannot grant imports");}
        };
        var observation=observed(current);var frame=observation.frame();
        var snapshot=StrictJson.object().put("paused",true).put("map_ready",true).put("revision",frame.revision())
                .put("native_revision",frame.identity().nativeRevision()).put("date_raw",frame.identity().dateRaw())
                .put("snapshot_id",frame.snapshotId()).put("episode_run_id",frame.episodeRunId());
        snapshot.putObject("played_character").put("character_id",current.player());snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        var request=new PlanningRequest(observation,current.source(),current.session().sessionId(),NOW.plusSeconds(5),
                new PlanningObservation(object(StrictJson.canonical(snapshot)),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var actual=new PrisonerDomainBodyReader12004(store,current.session().machineId());
        var read=assertInstanceOf(KnownLedger.class,actual.read(request));assertTrue(read.release().isEmpty());assertTrue(read.ransom().isEmpty());
    }
    @Test void missingObservationAndWrongScopeCannotBecomeEmptyCustodyOrReplayPermission() {
        var old=owner(1,7);var current=owner(2,8);var body=unresolved(Family.RANSOM,old);var ref=reference(Family.RANSOM,body,contractSchema(Family.RANSOM));
        assertThrows(IllegalArgumentException.class,()->new Epoch(Kind.NEXT,current,BASIS,Optional.of(new Baseline(12,"d".repeat(64))),Optional.of(new Predecessor(old,ref)),Optional.empty()));
        var next=PrisonerEpisodeLedger12004.next(Family.RANSOM,body,old,ref,nextEpoch(old,current,ref,List.of()));
        ObjectNode replay=(ObjectNode)StrictJson.parse(next.bytes());((ObjectNode)replay.path("inherited_unknowns").get(0)).put("replay_allowed",true);
        assertThrows(IllegalArgumentException.class,()->decode(Family.RANSOM,new RawJson(StrictJson.canonical(replay))));
        ObjectNode wrong=(ObjectNode)StrictJson.parse(next.bytes());((ObjectNode)wrong.path("epoch").path("collection")).put("query_sequence",18446744073709551614.0);
        assertThrows(IllegalArgumentException.class,()->decode(Family.RANSOM,new RawJson(StrictJson.canonical(wrong))));
        ObjectNode missing=(ObjectNode)StrictJson.parse(next.bytes());((ObjectNode)missing.path("epoch")).remove("collection");
        assertThrows(IllegalArgumentException.class,()->decode(Family.RANSOM,new RawJson(StrictJson.canonical(missing))));
    }
    @Test void explicitLegacyBodyIsReadableForPureAuditWithoutAcquiringCurrentEpochQualification() {
        for(Family family:Family.values()){
            var old=owner(1,7);var current=owner(2,8);var n=StrictJson.object().putNull("resolved");
            if(family==Family.RANSOM)n.put("schema","xar.ck3.prisoner-ransom-formal.v1");n.set("pending",StrictJson.parse(pending(family,7).bytes()));
            var legacy=new RawJson(StrictJson.canonical(n));PrisonerLedgerReducer12004.validate(family,StrictJson.parse(legacy.bytes()));
            assertThrows(IllegalArgumentException.class,()->decode(family,legacy));
            var ref=reference(family,legacy,family==Family.RELEASE?"xar.java.prisoner-release-ledger/v1":"xar.java.prisoner-ransom-ledger/v1");
            var audited=decode(family,PrisonerEpisodeLedger12004.next(family,legacy,old,ref,nextEpoch(old,current,ref,List.of())));
            assertEquals(1,audited.inheritedUnknowns().size());assertEquals(ref,audited.inheritedUnknowns().getFirst().originalBody());
        }
    }
}

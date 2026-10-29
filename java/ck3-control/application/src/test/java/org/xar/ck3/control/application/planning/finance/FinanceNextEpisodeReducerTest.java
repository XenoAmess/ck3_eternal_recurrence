package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** One actual pure producer for NEXT and restored FIRST -> serde -> actual finance state/pending consumer. Private Root proofs are never fabricated. */
final class FinanceNextEpisodeReducerTest {
    private static ExactRef ref(String name){return new ExactRef("D:/fixture/"+name,1,"a".repeat(64));}
    private static final ExactRef REF=ref("first-baseline.json");
    private static MercenaryProcurement.Frame frame(int actor,String episode,int nativeRevision) {
        return new MercenaryProcurement.Frame(BigInteger.valueOf(actor),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(53789952),"native-"+nativeRevision,BigInteger.ONE,episode);
    }
    private static Obj snapshot(MercenaryProcurement.Frame source,long gold) {
        return OrdinaryFinanceCollector.obj("played_character",OrdinaryFinanceCollector.obj("character_id",new IntegerValue(source.player()),"alive",new Bool(true)),
                "native_revision",new IntegerValue(source.nativeRevision()),"date_raw",new IntegerValue(source.dateRaw()),
                "snapshot_id",new Text(source.snapshotId()),"revision",new IntegerValue(source.revision()),"episode_run_id",new Text(source.episodeId()),
                "played_character_gold",OrdinaryFinanceCollector.obj("raw",new IntegerValue(BigInteger.valueOf(gold)),"scale",new IntegerValue(BigInteger.valueOf(100000))),
                "paused",new Bool(true),"map_ready",new Bool(true),"active_wars",new Arr(List.of()),"player_armies",new Arr(List.of()),"active_event",Nil.INSTANCE,"pending_character_interaction",Nil.INSTANCE);
    }
    private static MercenaryProcurement.Ledger previous() {
        var original=OrdinaryFinanceCollector.obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",OrdinaryFinanceCollector.obj(
                "action_request_id",new Text("original-unknown-hire"),"company_id",new IntegerValue(BigInteger.valueOf(17)),
                "status",new Text("submission_unresolved"),"pre_capture_epoch",new IntegerValue(BigInteger.ONE),
                "source_frame",frame(32904,"old-episode",1).json(),"pre_player_army_ids",new Arr(List.of()),
                "decision",OrdinaryFinanceCollector.obj("status",new Text("original-qualified-decision"))),
                "observed",new Arr(List.of()),"retained_extension",new Text("original debt/commitment evidence is not reset"),
                "next_episode_finance_basis_v1",OrdinaryFinanceCollector.obj("original_legacy_marker",new Text("kept verbatim, never an alias for v2")));
        return MercenaryProcurement.decode(DriverJson.encode(original));
    }
    private static MercenaryProcurement.EpisodeBasis basis(MercenaryProcurement.EpisodeOrigin kind,Obj saved,Obj current,String physical) {
        return new MercenaryProcurement.EpisodeBasis(kind,frame(32904,"old-episode",1),MercenaryProcurement.fromSnapshot(saved),MercenaryProcurement.fromSnapshot(current),saved,current,
                REF,ref("original-saved-sem.json"),ref("first-saved-driver.json"),ref(physical+"-sem.json"),ref(physical+"-driver.json"),ref("retained-gift.json"),
                new MercenaryProcurement.NextCashUnavailable("actual optional native cash unavailable",ref(physical+"-cash-source.json")));
    }
    private static MercenaryProcurement.EpisodeBasis basisWithCash(MercenaryProcurement.EpisodeOrigin kind,Obj saved,Obj current,String physical,MercenaryProcurement.NextCash cash) {
        return new MercenaryProcurement.EpisodeBasis(kind,frame(32904,"old-episode",1),MercenaryProcurement.fromSnapshot(saved),MercenaryProcurement.fromSnapshot(current),saved,current,
                REF,ref("original-saved-sem.json"),ref("first-saved-driver.json"),ref(physical+"-sem.json"),ref(physical+"-driver.json"),ref("retained-gift.json"),cash);
    }
    private static Obj unavailableExpense(MercenaryProcurement.Frame frame) {
        return OrdinaryFinanceCollector.obj("status",new Text("unavailable"),"owner_character_id",new IntegerValue(frame.player()),
                "resource_id",new Text(frame.player().toString()),"war_ids",new Arr(List.of()),"raw_scale",new IntegerValue(BigInteger.valueOf(100000)),
                "time_basis",new Text("month"),"source_scope",new Text("actor_owned_military_once_across_all_wars"),"future_war_cost_upper_ready",new Bool(false),
                "resource_raw_native",Nil.INSTANCE,"gold_raw",Nil.INSTANCE,"treasury_raw",Nil.INSTANCE,"unavailable_reason",new Text("fixture has no military expense observation"));
    }
    private static org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.NormalizedCurrentCash observedCash(Obj current) {
        var frame=MercenaryProcurement.fromSnapshot(current);
        var raw=OrdinaryFinanceCollector.obj("schema",new Text(org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.SCHEMA),
                "game_version",new Text("1.19.0.6"),"executable_sha256",new Text("2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"),
                "played_character_id",new IntegerValue(frame.player()),"snapshot_revision",new IntegerValue(frame.nativeRevision()),"date_raw",new IntegerValue(frame.dateRaw()),
                "read_only",new Bool(true),"advertised",new Bool(false),"formal_action_ready",new Bool(false),"status",new Text("available"),
                "active_war_ids",new Arr(List.of()),"player_army_ids",new Arr(List.of()),"current_treasury",current.get("played_character_gold"),"player_monthly_net_income",Nil.INSTANCE,
                "readiness",OrdinaryFinanceCollector.obj("same_frame_ready",new Bool(true),"current_treasury_ready",new Bool(true),"monthly_gross_income_ready",new Bool(false),
                        "monthly_total_expenses_ready",new Bool(false),"monthly_net_income_ready",new Bool(false),"current_military_expenses_ready",new Bool(false),"all_raised_military_expenses_ready",new Bool(false)),
                "military_expenses",OrdinaryFinanceCollector.obj("current",unavailableExpense(frame),"all_raised",unavailableExpense(frame)),
                "queried_snapshot_id",new Text(frame.snapshotId()),"queried_revision",new IntegerValue(frame.revision()),"queried_native_revision",new IntegerValue(frame.nativeRevision()));
        return org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec.normalize(DriverJson.encode(raw),DriverJson.encode(current));
    }
    private static FinanceStatePort.Snapshot consume(MercenaryProcurement.Ledger body,Obj current) {
        var frame=MercenaryProcurement.fromSnapshot(current);var source=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-24T01:00:00Z","1.20.0.4",REF);
        var identity=new ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(frame.player(),frame.nativeRevision(),frame.dateRaw()),frame.snapshotId(),frame.revision(),frame.episodeId()),1);
        var request=new PlanningRequest(identity,source,"current-restored-session",Instant.parse("2099-01-01T00:00:00Z"),
                new PlanningObservation(current,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        byte[] raw=MercenaryProcurement.encode(body);var document=new FinanceStatePort.Document(FinanceStatePort.Domain.MERCENARY,new ExactRef("D:/fixture/current-domain.json",raw.length,ActionCodec.sha256(raw)),raw);
        var reader=new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.MERCENARY,REF,original->MercenaryProcurement.decode(original.bytes()).pending().isPresent()?FinanceStatePort.Pending.PENDING:FinanceStatePort.Pending.CLEAR);
        var actual=new FinanceStatePort(ignored->new FinanceStatePort.Head(identity,REF,List.of(document),List.of(),Optional.empty()),List.of(reader));
        return assertInstanceOf(FinanceStatePort.Known.class,actual.read(request)).snapshot();
    }
    @Test void bothActualOriginsPreserveUnknownAndDistinctOriginalSavedAndCurrentWalletsThroughTheRealConsumer() {
        var old=previous();var saved=snapshot(frame(33000,"new-episode",1),123456);var current=snapshot(frame(33000,"new-episode",7),456789);
        for(var kind:MercenaryProcurement.EpisodeOrigin.values()) {
            var transformed=MercenaryProcurement.initializeEpisode(old,basis(kind,saved,current,kind.name()));
            byte[] serialized=MercenaryProcurement.encode(transformed);var restored=MercenaryProcurement.decode(serialized);assertArrayEquals(serialized,MercenaryProcurement.encode(restored));
            assertEquals(old.pending().orElseThrow().original(),restored.pending().orElseThrow().original());assertEquals(old.observed(),restored.observed());
            assertEquals(old.original().get("retained_extension"),restored.original().get("retained_extension"));assertEquals(old.original().get("next_episode_finance_basis_v1"),restored.original().get("next_episode_finance_basis_v1"));
            Obj marker=object(restored.original().get("episode_finance_basis_v2"),"episode basis");assertEquals(new Text(kind.name()),marker.get("initialization_kind"));
            assertEquals(saved.get("played_character_gold"),object(marker.get("original_saved_wallet"),"saved wallet").get("played_character_gold"));
            assertEquals(current.get("played_character_gold"),object(marker.get("current_wallet"),"current wallet").get("played_character_gold"));
            assertNotEquals(marker.get("first_saved_driver"),marker.get("current_driver"));
            assertEquals(new IntegerValue(BigInteger.ZERO),marker.get("funding_credited_raw"));assertEquals(new Text("unavailable"),marker.get("debt_status"));assertEquals(new Bool(false),marker.get("payment_verified"));
            assertEquals(FinanceStatePort.Pending.PENDING,consume(restored,current).ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow().pending());
            assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(current,restored));
        }
    }
    @Test void optionalSourceMetadataDoesNotChangeObservedCashOrClearUnknownObligationsThroughSerdeAndConsumer() {
        var old=previous();var saved=snapshot(frame(33000,"new-episode",1),123456);var current=snapshot(frame(33000,"new-episode",7),456789);
        var nativeCash=observedCash(current);ExactRef read=ref("actual-current-cash-read.json"),metadata=ref("optional-cash-source.json");
        for(var kind:MercenaryProcurement.EpisodeOrigin.values())for(var source:List.<Optional<ExactRef>>of(Optional.empty(),Optional.of(metadata))) {
            for(var cash:List.<MercenaryProcurement.NextCash>of(new MercenaryProcurement.NextCashObserved(nativeCash,read,source),
                    new MercenaryProcurement.NextCashUnavailable("actual current cash unavailable",source))) {
                var produced=MercenaryProcurement.initializeEpisode(old,basisWithCash(kind,saved,current,kind+"-"+cash.getClass().getSimpleName()+"-"+source.isPresent(),cash));
                byte[] wire=MercenaryProcurement.encode(produced);var restored=MercenaryProcurement.decode(wire);assertArrayEquals(wire,MercenaryProcurement.encode(restored));
                Obj marker=object(restored.original().get("episode_finance_basis_v2"),"complete episode basis");
                assertTrue(marker.members().containsKey("current_cash_source_proof"));
                if(source.isPresent())assertEquals(metadata,ExactRef.fromJson(StrictJson.parse(DriverJson.encode(marker.get("current_cash_source_proof")))));
                else assertEquals(Nil.INSTANCE,marker.get("current_cash_source_proof"));
                if(cash instanceof MercenaryProcurement.NextCashObserved) {
                    assertEquals(new Text("observed"),marker.get("native_cash_status"));
                    assertEquals(read,ExactRef.fromJson(StrictJson.parse(DriverJson.encode(marker.get("current_cash_original_read")))));
                    assertArrayEquals(StrictJson.canonical(StrictJson.parse(nativeCash.toJson())),StrictJson.canonical(StrictJson.parse(DriverJson.encode(marker.get("war_cash_current_resources")))));
                } else {
                    assertEquals(new Text("unavailable"),marker.get("native_cash_status"));
                    assertEquals(new Text("actual current cash unavailable"),marker.get("current_cash_unavailable_reason"));
                }
                assertEquals(old.pending().orElseThrow().original(),restored.pending().orElseThrow().original());
                assertEquals(current.get("played_character_gold"),object(marker.get("current_wallet"),"actual current wallet").get("played_character_gold"));
                assertEquals(new IntegerValue(BigInteger.ZERO),marker.get("funding_credited_raw"));assertEquals(new Bool(false),marker.get("payment_verified"));
                assertEquals(FinanceStatePort.Pending.PENDING,consume(restored,current).ledger(FinanceStatePort.Domain.MERCENARY).orElseThrow().pending());
                assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(current,restored));
            }
        }
    }
    @Test void optionalSourceContainerIsNonNullAndMissingMetadataCannotHideAnObservedFrameMismatch() {
        var current=snapshot(frame(33000,"new-episode",7),456789);var saved=snapshot(frame(33000,"new-episode",1),123456);var nativeCash=observedCash(current);
        assertThrows(NullPointerException.class,()->new MercenaryProcurement.NextCashObserved(nativeCash,ref("cash-read.json"),(Optional<ExactRef>)null));
        assertThrows(NullPointerException.class,()->new MercenaryProcurement.NextCashUnavailable("unavailable",(Optional<ExactRef>)null));
        var knownWithoutMetadata=new MercenaryProcurement.NextCashObserved(nativeCash,ref("cash-read.json"),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->basisWithCash(MercenaryProcurement.EpisodeOrigin.NEXT,snapshot(frame(33001,"new-episode",1),123456),snapshot(frame(33001,"new-episode",7),456789),"wrong-current-frame",knownWithoutMetadata));
    }
    @Test void restoringTheSameEpisodeRecordsANewPhysicalOriginAndRetainsThePreviousBasisButSameOriginConflictsFail() {
        var saved=snapshot(frame(33000,"new-episode",1),123);var current=snapshot(frame(33000,"new-episode",7),456);
        var nextBasis=basis(MercenaryProcurement.EpisodeOrigin.NEXT,saved,saved,"first-physical");var next=MercenaryProcurement.initializeEpisode(previous(),nextBasis);
        assertSame(next,MercenaryProcurement.initializeEpisode(next,nextBasis));
        var restoredBasis=basis(MercenaryProcurement.EpisodeOrigin.RESTORED_FIRST,saved,current,"restored-physical");var restored=MercenaryProcurement.initializeEpisode(next,restoredBasis);
        assertEquals(List.of(next.original().get("episode_finance_basis_v2")),array(restored.original().get("episode_finance_basis_history_v2"),"retained basis history"));
        assertSame(restored,MercenaryProcurement.initializeEpisode(restored,restoredBasis));
        var changed=basis(MercenaryProcurement.EpisodeOrigin.RESTORED_FIRST,saved,current.with("played_character_gold",snapshot(frame(33000,"new-episode",7),999).get("played_character_gold")),"restored-physical");
        assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.initializeEpisode(restored,changed));
        assertThrows(IllegalArgumentException.class,()->basis(MercenaryProcurement.EpisodeOrigin.RESTORED_FIRST,saved,snapshot(frame(33001,"new-episode",7),1),"foreign-player"));
        assertThrows(IllegalArgumentException.class,()->basis(MercenaryProcurement.EpisodeOrigin.RESTORED_FIRST,saved,snapshot(frame(33000,"foreign-episode",7),1),"foreign-episode"));
    }
    @Test void missingNullMalformedAndWrongDenominationWalletsKeepTheirActualMeaningsForEachOrigin() {
        var saved=snapshot(frame(33000,"new-episode",1),123);var current=snapshot(frame(33000,"new-episode",7),456);
        for(var kind:MercenaryProcurement.EpisodeOrigin.values()) {
            var fields=new java.util.LinkedHashMap<>(current.members());fields.remove("played_character_gold");
            Obj missing=object(MercenaryProcurement.initializeEpisode(previous(),basis(kind,saved,new Obj(fields),"missing"+kind)).original().get("episode_finance_basis_v2"),"missing basis");
            assertFalse(object(missing.get("current_wallet"),"missing wallet").members().containsKey("played_character_gold"));
            Obj nil=object(MercenaryProcurement.initializeEpisode(previous(),basis(kind,saved,current.with("played_character_gold",Nil.INSTANCE),"null"+kind)).original().get("episode_finance_basis_v2"),"null basis");
            assertEquals(Nil.INSTANCE,object(nil.get("current_wallet"),"null wallet").get("played_character_gold"));
            assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.initializeEpisode(previous(),basis(kind,saved,current.with("played_character_gold",new Bool(false)),"invalid")));
            assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.initializeEpisode(previous(),basis(kind,saved,current.with("played_character_gold",OrdinaryFinanceCollector.obj("raw",new IntegerValue(BigInteger.ONE),"scale",new IntegerValue(BigInteger.ONE))),"denomination")));
        }
    }
}

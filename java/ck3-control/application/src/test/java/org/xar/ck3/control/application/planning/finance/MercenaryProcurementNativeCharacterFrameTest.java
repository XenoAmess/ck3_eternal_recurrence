package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyMercenaryContextCodec;

/** Real pure source-frame and market/inventory consumers; no Native command or Applied authority. */
final class MercenaryProcurementNativeCharacterFrameTest {
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final BigInteger U64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private static final List<BigInteger> ACTORS=List.of(BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MIN_VALUE+5),
            BigInteger.valueOf(-67108906),BigInteger.valueOf(-2),BigInteger.ZERO,BigInteger.ONE,BigInteger.valueOf(67108906),BigInteger.valueOf(Integer.MAX_VALUE));
    private static ObservationIdentity observation(BigInteger actor,long revision) {
        var identity=new JointBudgetSelector.Frame(NativeCharacterId.of(actor).asBigInteger(),BigInteger.valueOf(revision),BigInteger.valueOf(100));
        var frame=new JointBudgetSelector.ProposalFrame(identity,"native-"+revision,BigInteger.valueOf(revision),"actual-episode");
        return new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",new GameGeneration(17,new PythonOnlyUInt64(BigInteger.valueOf(100))),frame,1);
    }
    private static Obj snapshot(BigInteger actor,long revision) {
        Obj frame=OrdinaryFinanceCollector.sourceFrame(observation(actor,revision));
        return frame.with("played_character",obj("character_id",new IntegerValue(actor),"alive",new Bool(true)))
                .with("active_wars",new Arr(List.of())).with("paused",new Bool(true)).with("map_ready",new Bool(true))
                .with("player_armies",new Arr(List.of(obj("army_id",new IntegerValue(BigInteger.ONE),"soldiers",new IntegerValue(BigInteger.valueOf(50)),
                        "current_province_id",new IntegerValue(BigInteger.valueOf(12)),"controllable",new Bool(true)),
                        obj("army_id",new IntegerValue(new BigInteger("4294967294")),"soldiers",new IntegerValue(BigInteger.valueOf(100)),
                                "current_province_id",new IntegerValue(BigInteger.valueOf(12)),"controllable",new Bool(true)))))
                .with("played_character_gold",obj("raw",new IntegerValue(BigInteger.valueOf(49000000)),"scale",new IntegerValue(BigInteger.valueOf(100000))))
                .with("diagnostics",obj("hello",obj("expected_ck3_version",new Text("1.20.0.4"),"expected_ck3_sha256",new Text(EXE))));
    }
    private static Obj claim(BigInteger actor,BigInteger company) {
        return obj("action_request_id",new Text("native-original-request"),"company_id",new IntegerValue(company),"status",new Text("submission_unresolved"),
                "pre_capture_epoch",new IntegerValue(U64),"pre_player_army_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE))),
                "source_frame",OrdinaryFinanceCollector.sourceFrame(observation(actor,10)),
                "decision",obj("selected_candidate",obj("company_id",new IntegerValue(company),"gold_cost_raw",new IntegerValue(BigInteger.valueOf(1000000)),
                        "predicted_auto_raise_province_id",new IntegerValue(BigInteger.valueOf(12)),"purpose_war_ids",new Arr(List.of()),
                        "finance",obj("observed_treasury_raw",new IntegerValue(BigInteger.valueOf(50000000))))));
    }
    private static MercenaryProcurement.Ledger ledger(Obj pending) {
        return MercenaryProcurement.decode(encode(obj("schema",new Text(MercenaryProcurement.SCHEMA),"pending",pending,"observed",new Arr(List.of()))));
    }
    private static Obj market(BigInteger actor) {
        return obj("schema",new Text("ck3_12004_player_mercenary_context_v1"),"game_version",new Text("1.20.0.4"),"executable_sha256",new Text(EXE),
                "actor_character_id",new IntegerValue(actor),"date_raw",new IntegerValue(BigInteger.valueOf(100)),"capture_epoch",new IntegerValue(U64),
                "read_only",new Bool(true),"native_hire_mode",new IntegerValue(BigInteger.ONE),"available",new Bool(true),"unavailable_reason",Nil.INSTANCE,"rows",new Arr(List.of()));
    }
    @Test void actualSourceFrameAndMarketActorPreserveEverySignedIdentityIncludingZero() {
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(BigInteger actor:ACTORS)checks.add(()->{
            var original=observation(actor,11);Obj produced=OrdinaryFinanceCollector.sourceFrame(original);
            assertEquals(new IntegerValue(actor),produced.get("played_character_id"));
            Obj actual=snapshot(actor,11);var decodedMarket=ArmyMercenaryContextCodec.decode(market(actor),actual);
            assertEquals(actor,decodedMarket.actor());
            var frame=MercenaryProcurement.fromObservation(original);
            assertEquals(actor,frame.player());assertEquals(produced,frame.json());assertEquals(frame,MercenaryProcurement.fromSnapshot(actual));
            Obj absentMirror=new Obj(actual.members().entrySet().stream().filter(e->!e.getKey().equals("played_character_id"))
                    .collect(java.util.stream.Collectors.toMap(java.util.Map.Entry::getKey,java.util.Map.Entry::getValue)));
            assertEquals(frame,MercenaryProcurement.fromSnapshot(absentMirror));assertEquals(frame,MercenaryProcurement.fromSnapshot(actual.with("played_character_id",Nil.INSTANCE)));
        });
        assertAll(checks);
    }
    @Test void actualClaimRaisedAndLedgerRoundTripKeepSignedActorAndUnknownAuthority() {
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(BigInteger actor:ACTORS)checks.add(()->{
            Obj actual=snapshot(actor,11);var pending=ledger(claim(actor,new BigInteger("4294967294")));
            var original=pending.pending().orElseThrow();assertEquals(actor,original.source().player());
            Obj post=MercenaryProcurement.postInventory(actual,original);Obj first=MercenaryProcurement.firstRaised(actual,original).orElseThrow();
            assertEquals(new IntegerValue(actor),object(post.get("source_frame"),"post frame").get("played_character_id"));
            assertEquals(new IntegerValue(actor),object(first.get("source_frame"),"first frame").get("played_character_id"));
            assertEquals(new Bool(false),post.get("payment_verified"));assertEquals(new Bool(false),first.get("army_creation_verified"));
            assertEquals(new Bool(false),first.get("company_to_new_army_binding_verified"));
            var refreshed=MercenaryProcurement.refreshInventory(pending,actual);var restored=MercenaryProcurement.decode(MercenaryProcurement.encode(refreshed));
            assertEquals(refreshed.original(),restored.original());assertEquals(actor,restored.pending().orElseThrow().source().player());
            assertEquals(MercenaryProcurement.Status.SUBMISSION_UNRESOLVED,restored.pending().orElseThrow().status());
            assertEquals(MercenaryProcurement.NewHireBarrier.UNKNOWN_PENDING,MercenaryProcurement.barrier(actual,restored));
        });
        assertAll(checks);
    }
    @Test void invalidCharacterDomainsCannotEnterDirectSnapshotOrRetainedClaimFrames() {
        List<BigInteger> invalid=List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE),new BigInteger("4294967294"),new BigInteger("4294967295"),BigInteger.ONE.shiftLeft(100));
        var checks=new java.util.ArrayList<org.junit.jupiter.api.function.Executable>();
        for(BigInteger actor:invalid)checks.add(()->assertAll("invalid actor "+actor,
                ()->assertThrows(IllegalArgumentException.class,()->new MercenaryProcurement.Frame(actor,BigInteger.ONE,BigInteger.ZERO,"s",BigInteger.ONE,"e")),
                ()->{Obj actual=snapshot(BigInteger.ONE,11).with("played_character_id",new IntegerValue(actor))
                        .with("played_character",obj("character_id",new IntegerValue(actor),"alive",new Bool(true)));
                    assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.fromSnapshot(actual));},
                ()->{Obj original=claim(BigInteger.ONE,BigInteger.ZERO);Obj source=object(original.get("source_frame"),"source").with("played_character_id",new IntegerValue(actor));
                    assertThrows(IllegalArgumentException.class,()->ledger(original.with("source_frame",source)));}));
        Obj valid=snapshot(BigInteger.ONE,11);
        for(String literal:List.of("true","1.0","\"1\"","null"))checks.add(()->{
            Value invalidActor=parse(literal.getBytes(StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.fromSnapshot(valid.with("played_character_id",invalidActor)
                    .with("played_character",obj("character_id",invalidActor,"alive",new Bool(true)))));
        });
        assertAll(checks);
    }
    @Test void fullSignedIdentityDoesNotAliasAnotherActorAndOtherFrameDomainsStayUnchanged() {
        var original=MercenaryProcurement.fromSnapshot(snapshot(BigInteger.valueOf(-2),11));
        for(BigInteger other:List.of(BigInteger.TWO,BigInteger.valueOf(16777214),BigInteger.ZERO))
            assertFalse(original.sameLife(MercenaryProcurement.fromSnapshot(snapshot(other,11))));
        assertFalse(original.sameLife(new MercenaryProcurement.Frame(BigInteger.valueOf(-2),BigInteger.ONE,BigInteger.ZERO,"s",BigInteger.ONE,"other-episode")));
        assertThrows(IllegalArgumentException.class,()->MercenaryProcurement.fromSnapshot(snapshot(BigInteger.ZERO,11).with("played_character_id",new IntegerValue(BigInteger.ONE))));
        var wide=new MercenaryProcurement.Frame(BigInteger.ONE,U64,BigInteger.ONE.shiftLeft(100),"s",U64,"e");assertEquals(U64,wide.nativeRevision());
        for(BigInteger bad:List.of(BigInteger.ZERO,BigInteger.valueOf(-1),U64.add(BigInteger.ONE))) {
            assertThrows(IllegalArgumentException.class,()->new MercenaryProcurement.Frame(BigInteger.ONE,bad,BigInteger.ZERO,"s",BigInteger.ONE,"e"));
            assertThrows(IllegalArgumentException.class,()->new MercenaryProcurement.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.ZERO,"s",bad,"e"));
        }
        assertThrows(IllegalArgumentException.class,()->new MercenaryProcurement.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(-1),"s",BigInteger.ONE,"e"));
        assertEquals(BigInteger.ZERO,ledger(claim(BigInteger.ONE,BigInteger.ZERO)).pending().orElseThrow().company());
        assertEquals(new BigInteger("4294967294"),ledger(claim(BigInteger.ONE,new BigInteger("4294967294"))).pending().orElseThrow().company());
        for(BigInteger bad:List.of(BigInteger.valueOf(-2),new BigInteger("4294967295")))
            assertThrows(IllegalArgumentException.class,()->ledger(claim(BigInteger.ONE,bad)));
        Obj pending=claim(BigInteger.ONE,BigInteger.ZERO);Obj decision=object(pending.get("decision"),"decision");Obj selected=object(decision.get("selected_candidate"),"selected");
        assertEquals(Optional.empty(),MercenaryProcurement.firstRaised(snapshot(BigInteger.ONE,11),ledger(pending.with("decision",decision.with("selected_candidate",
                selected.with("predicted_auto_raise_province_id",new IntegerValue(BigInteger.ZERO))))).pending().orElseThrow()));
    }
}

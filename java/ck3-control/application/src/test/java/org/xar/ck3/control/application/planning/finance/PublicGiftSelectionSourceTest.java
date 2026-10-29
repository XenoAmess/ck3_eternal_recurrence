package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.LinkedHashMap;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicCodec;
import org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicContract.Method;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.factiongift.FactionGiftChoice;
import org.xar.ck3.control.finance.factiongift.FactionGiftPolicy;

/** Real shared producer -> public numeric projection -> source-selection guard.
 * This pure test constructs no Root, Ready object, action, writer or Game qualification. */
final class PublicGiftSelectionSourceTest {
    private record Source(Obj choice,Value observation,BigInteger minimum,FinanceStatePort.Checkpoint checkpoint,Obj candidate,Obj suppliedCheckpoint) { }
    private static Source source()throws Exception { return source(null); }
    private static Source source(BigInteger requestedMinimum)throws Exception {
        try(var stream=PublicGiftSelectionSourceTest.class.getResourceAsStream("/public-gift-source-case.json")) {
            assertNotNull(stream);
            Obj root=object(parse(stream.readAllBytes()),"retained original producer vector");
            Obj vector=object(root.get("case"),"case");Obj input=object(vector.get("input"),"actual pure producer input");
            if(requestedMinimum!=null)input=input.with("minimum_gold_reserve_raw",new IntegerValue(requestedMinimum));
            var selected=assertInstanceOf(FactionGiftChoice.Selected.class,FactionGiftPolicy.choose(encode(input)));
            Obj choice=object(parse(FactionGiftPolicy.encode(selected)),"actual selected Gift");
            assertEquals(vector.get("expected"),choice);
            var fields=new LinkedHashMap<String,Value>(choice.members());fields.remove("status");fields.remove("reason");
            BigInteger minimum=integer(input.get("minimum_gold_reserve_raw"),"reserve");fields.put("minimum_gold_reserve_raw",new IntegerValue(minimum));
            Value observation=array(input.get("observations"),"actual original observations").getFirst();
            var checkpoint=new FinanceStatePort.Checkpoint(new ExactRef("pure-test-save-reference",1,"c".repeat(64)),"actual-fixture-episode",selected.dateRaw());
            Obj supplied=obj("sha256",new Text(checkpoint.saveReference().sha256()),"episode_run_id",new Text(checkpoint.episodeRunId()),"date_raw",new IntegerValue(checkpoint.dateRaw()));
            return new Source(choice,observation,minimum,checkpoint,obj("choice",new Obj(fields),"observation",observation),supplied);
        }
    }
    private static void verify(Source s,Obj candidate,Obj checkpoint) {
        OrdinaryFinancePolicies.requirePublicGiftSelection(s.choice(),s.observation(),s.minimum(),s.checkpoint(),candidate,checkpoint);
    }
    @Test void actualSharedProducerPublicWireAndJsonRoundTripPreserveSelection()throws Exception {
        Source s=source();
        RawJson publicWire=FactionGiftPublicCodec.businessPublic(Method.CANDIDATE,new RawJson(DriverJson.encode(s.candidate())));
        Obj nativeAgain=DriverJson.object(FactionGiftPublicCodec.candidateNative(publicWire).bytes(),RawJson.MAXIMUM_BYTES);
        verify(s,nativeAgain,object(parse(encode(s.suppliedCheckpoint())),"persisted checkpoint"));
        assertEquals(s.candidate(),nativeAgain);
    }
    @Test void changedChoiceObservationAndCheckpointFailBeforeAnyCommandExists()throws Exception {
        Source s=source();Obj choice=object(s.candidate().get("choice"),"choice");
        assertThrows(IllegalArgumentException.class,()->verify(s,s.candidate().with("choice",choice.with("recipient_character_id",new IntegerValue(BigInteger.ONE))),s.suppliedCheckpoint()));
        assertThrows(IllegalArgumentException.class,()->verify(s,s.candidate().with("observation",new Obj(java.util.Map.of())),s.suppliedCheckpoint()));
        assertThrows(IllegalArgumentException.class,()->verify(s,s.candidate(),s.suppliedCheckpoint().with("sha256",new Text("d".repeat(64)))));
        assertThrows(IllegalArgumentException.class,()->verify(s,s.candidate(),s.suppliedCheckpoint().with("date_raw",new Bool(true))));
        assertThrows(IllegalArgumentException.class,()->verify(s,s.candidate(),s.suppliedCheckpoint().with("episode_run_id",new Text("another-episode"))));
    }
    @Test void nondefaultReserveSurvivesPublicSelectionAndPersistedCurrentBudgetInput()throws Exception {
        for(BigInteger minimum:java.util.List.of(BigInteger.ZERO,BigInteger.valueOf(15_810_153))) {
            Source s=source(minimum);
            RawJson publicWire=FactionGiftPublicCodec.businessPublic(Method.CANDIDATE,new RawJson(DriverJson.encode(s.candidate())));
            Obj nativeAgain=DriverJson.object(FactionGiftPublicCodec.candidateNative(publicWire).bytes(),RawJson.MAXIMUM_BYTES);
            verify(s,nativeAgain,s.suppliedCheckpoint());
            BigInteger selectedMinimum=OrdinaryFinancePolicies.giftMinimumReserve(object(nativeAgain.get("choice"),"public selected choice"));
            Obj retained=object(parse(encode(obj("minimum_gold_reserve_raw",new IntegerValue(selectedMinimum)))),"persisted command budget");
            assertEquals(minimum,OrdinaryFinancePolicies.giftMinimumReserve(retained));
            assertNotEquals(BigInteger.valueOf(10_000_000),OrdinaryFinancePolicies.giftMinimumReserve(retained));
        }
    }
    @Test void currentBudgetUsesSelectedReserveAtTheActualTreasuryBoundary()throws Exception {
        Source s=source();
        Obj observation=object(s.observation(),"retained original observation");
        BigInteger cashAfter=integer(observation.get("player_gold_raw"),"observed wallet")
                .subtract(integer(object(observation.get("gift_preview"),"original quote").get("gold_cost_raw"),"quoted cost"));
        assertEquals(BigInteger.valueOf(15_810_153),cashAfter);
        Obj input=obj("observations",new Arr(java.util.List.of(observation)),"complete_native_enumeration",new Bool(true),
                "minimum_gold_reserve_raw",new IntegerValue(cashAfter));
        assertInstanceOf(FactionGiftChoice.Selected.class,FactionGiftPolicy.choose(encode(input)));
        Obj retained=object(parse(encode(obj("minimum_gold_reserve_raw",new IntegerValue(cashAfter.add(BigInteger.ONE))))),"persisted higher reserve");
        BigInteger originalMinimum=OrdinaryFinancePolicies.giftMinimumReserve(retained);
        var rejected=assertInstanceOf(FactionGiftChoice.Declined.class,FactionGiftPolicy.choose(encode(input.with("minimum_gold_reserve_raw",new IntegerValue(originalMinimum)))));
        assertEquals(FactionGiftChoice.Reason.GOLD_RESERVE_NOT_SATISFIED,rejected.reason());
        assertInstanceOf(FactionGiftChoice.Selected.class,FactionGiftPolicy.choose(encode(input.with("minimum_gold_reserve_raw",new IntegerValue(BigInteger.valueOf(10_000_000))))));
    }
    @Test void missingNullBooleanFloatTextAndNegativeReserveCannotBecomeTheDefaultBudget() {
        for(String json:java.util.List.of("{}","{\"minimum_gold_reserve_raw\":null}","{\"minimum_gold_reserve_raw\":true}",
                "{\"minimum_gold_reserve_raw\":10000000.0}","{\"minimum_gold_reserve_raw\":\"10000000\"}","{\"minimum_gold_reserve_raw\":-1}")) {
            Obj retained=DriverJson.object(json.getBytes(java.nio.charset.StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
            assertThrows(IllegalArgumentException.class,()->OrdinaryFinancePolicies.giftMinimumReserve(retained));
        }
    }

}

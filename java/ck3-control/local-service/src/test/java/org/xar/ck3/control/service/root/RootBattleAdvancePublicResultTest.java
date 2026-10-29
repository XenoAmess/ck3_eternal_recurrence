package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.battleadvance.BattleAdvanceResultCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.routecontact.RouteContactSteps;
import org.xar.ck3.control.contracts.StrictJson;

/** Representation-only DATA regressions. No constructed report is an execution, canonical receipt or Root qualification. */
final class RootBattleAdvancePublicResultTest {
    private static final OperationKey WINDOW=new OperationKey(RouteContactSteps.format(new RouteContactSteps.Request(0,7,List.of(1),2),RouteContactSteps.WINDOW));
    private static RawJson data() {
        var node=StrictJson.object().put("schema",BattleAdvanceResultCodec.SCHEMA).put("step",WINDOW.value())
                .put("revision",new BigInteger("9007199254740993"))
                .put("native_revision",new BigInteger("18446744073709551615"));
        node.putNull("armed_tactical_daily_sentinel");node.putNull("tactical_daily_sentinel");
        node.putNull("player_decision_boundary");node.putArray("actions");
        // RawJson and DriverJson preserve the literal -0.0 token; it is not decoded through a double.
        String text=node.toString();return new RawJson((text.substring(0,text.length()-1)+",\"original_float\":-0.0}")
                .getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    @Test void knownUint64RolesRoundTripExactlyAndUnrelatedDecimalTokenRemainsOriginal() {
        RawJson original=data();RawJson encoded=RootBattleAdvancePublicResult.encodeClockReport(original,WINDOW);
        var publicTree=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("9007199254740993"),publicTree.get("revision"));
        assertEquals(DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES),
                DriverJson.object(RootBattleAdvancePublicResult.decodeClockReport(encoded,WINDOW).bytes(),RawJson.MAXIMUM_BYTES));
        assertTrue(new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("-0.0"));
    }
    @Test void wrongSchemaWrongOperationWrongJsonDomainAndUnsafeUnknownIntegerRefuse() {
        var original=DriverJson.object(data().bytes(),RawJson.MAXIMUM_BYTES);
        for(String value:List.of("life-advance","battle-decision-epoch-advance",RouteContactSteps.format(new RouteContactSteps.Request(0,7,List.of(1),1),RouteContactSteps.HORIZON)))
            assertThrows(IllegalArgumentException.class,()->RootBattleAdvancePublicResult.encodeClockReport(data(),new OperationKey(value)));
        for(String member:List.of("schema","step","revision")) {
            var malformed=original.with(member,new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true));
            assertThrows(IllegalArgumentException.class,()->RootBattleAdvancePublicResult.encodeClockReport(new RawJson(DriverJson.encode(malformed)),WINDOW));
        }
        var unknown=original.with("unowned_integer",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(new BigInteger("9007199254740993")));
        assertThrows(IllegalArgumentException.class,()->RootBattleAdvancePublicResult.encodeClockReport(new RawJson(DriverJson.encode(unknown)),WINDOW));
    }
    @Test void actualRootRevisionDomainRetainsMaxUint64PlusOneAndFull4300DigitPublicIntegers() {
        var original=DriverJson.object(data().bytes(),RawJson.MAXIMUM_BYTES);
        for(BigInteger value:List.of(new BigInteger("18446744073709551616"),new BigInteger("9".repeat(4300)))) {
            var numeric=original.with("revision",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(value))
                    .with("native_revision",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(value));
            var report=new RawJson(DriverJson.encode(numeric));
            var publicReport=RootBattleAdvancePublicResult.encodeClockReport(report,WINDOW);
            assertEquals(numeric,DriverJson.object(RootBattleAdvancePublicResult.decodeClockReport(publicReport,WINDOW).bytes(),RawJson.MAXIMUM_BYTES));
        }
        var publicTree=DriverJson.object(RootBattleAdvancePublicResult.encodeClockReport(data(),WINDOW).bytes(),RawJson.MAXIMUM_BYTES);
        var tooLong=publicTree.with("revision",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("9".repeat(4301)));
        assertThrows(IllegalArgumentException.class,()->RootBattleAdvancePublicResult.decodeClockReport(new RawJson(DriverJson.encode(tooLong)),WINDOW));
    }

}

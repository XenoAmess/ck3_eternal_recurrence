package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.effects.HolyHirePoststate.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit unit observations, not Native qualification or a completed hire loop. */
final class HolyHirePoststateTest {
    private static BigInteger n(long value){return BigInteger.valueOf(value);}
    private static Scope scope(long date){return new Scope("action","request",n(0),n(73),"episode","native:10","native:11",n(11),n(11),n(100),n(date),"a".repeat(64));}
    private static Stocks stocks(long piety){return new Stocks(Quantity.value(n(100)),Quantity.value(n(200)),Quantity.value(n(piety)));}
    private static List<BigInteger> quote(long piety){var values=new ArrayList<>(java.util.Collections.nCopies(10,BigInteger.ZERO));values.set(2,n(piety));return List.copyOf(values);}
    private static Association association(){return new Association(Status.AVAILABLE,List.of(new Member(n(9),true,true,true,Optional.of(n(33554433)),false,Optional.empty())),Optional.empty());}
    @Test void walletSeparatesObservedDeltaQuoteMatchAndUnprovenDebitAttribution(){
        Wallet wallet=HolyHirePoststate.wallet(scope(100),stocks(500000),stocks(300000),quote(200000));
        assertEquals(Quantity.value(n(200000)),wallet.delta().piety());assertEquals(QuoteMatch.MATCH,wallet.quoteMatch());
        assertEquals(QuoteMatch.MISMATCH,HolyHirePoststate.wallet(scope(100),stocks(500000),stocks(400000),quote(200000)).quoteMatch());
        assertEquals(QuoteMatch.UNAVAILABLE,HolyHirePoststate.wallet(scope(101),stocks(500000),stocks(300000),quote(200000)).quoteMatch());
        var unsupported=new ArrayList<>(quote(200000));unsupported.set(5,n(1));
        assertEquals(QuoteMatch.UNAVAILABLE,HolyHirePoststate.wallet(scope(100),stocks(500000),stocks(300000),unsupported).quoteMatch());
        Report report=new Report(scope(100),wallet,HolyHirePoststate.troops(association(),Status.AVAILABLE,List.of(),Optional.empty()),Expenses.unavailable("not observed"));
        ObjectNode json=HolyHirePoststate.json(report);assertFalse(json.get("debit_attribution_observed").booleanValue());assertFalse(json.get("full_hire_loop_complete").booleanValue());assertFalse(json.get("automatic_retry").booleanValue());
    }
    @Test void knownNullAndUnavailableRemainDistinctAndNeverBecomeZero(){
        Stocks before=new Stocks(Quantity.knownNull(),Quantity.unavailable(),Quantity.value(n(10)));
        Wallet wallet=HolyHirePoststate.wallet(scope(100),before,stocks(0),quote(10));
        assertEquals(Presence.NULL,wallet.before().gold().presence());assertEquals(Presence.UNAVAILABLE,wallet.before().prestige().presence());
        assertEquals(Presence.UNAVAILABLE,wallet.delta().gold().presence());assertEquals(QuoteMatch.UNAVAILABLE,wallet.quoteMatch());
        assertThrows(IllegalArgumentException.class,()->new Quantity(Presence.NULL,Optional.of(n(0))));
    }
    @Test void usableTroopsRequireNativeAssociationPublicControlAndPositiveCurrentSoldiers(){
        List<Strength> rows=List.of(
                new Strength(n(0),Optional.of(n(33554433)),Quantity.value(n(100)),true,Optional.of(n(4444)),Optional.of(n(460))),
                new Strength(n(2),Optional.of(n(33554433)),Quantity.value(n(200)),false,Optional.of(n(73)),Optional.empty()),
                new Strength(n(3),Optional.of(n(33554434)),Quantity.value(n(300)),true,Optional.of(n(73)),Optional.empty()),
                new Strength(n(4),Optional.of(n(33554433)),Quantity.value(n(0)),true,Optional.of(n(73)),Optional.empty()),
                new Strength(n(5),Optional.of(n(33554433)),Quantity.unavailable(),true,Optional.of(n(73)),Optional.empty()));
        Troops result=HolyHirePoststate.troops(association(),Status.AVAILABLE,rows,Optional.empty());
        assertTrue(result.usableArmyObserved());assertEquals(1,result.materialArmies().size());assertEquals(n(0),result.materialArmies().getFirst().armyId());
        assertEquals(Optional.of(n(4444)),result.materialArmies().getFirst().ownerId(),"controllable order troops may have another owner");
        Troops missing=HolyHirePoststate.troops(association(),Status.UNAVAILABLE,rows,Optional.of("original strengths unavailable"));
        assertFalse(missing.usableArmyObserved());
        var absent=new Association(Status.UNAVAILABLE,List.of(),Optional.of("no association"));
        assertFalse(HolyHirePoststate.troops(absent,Status.AVAILABLE,rows,Optional.empty()).usableArmyObserved());
    }
    @Test void reportSerdeRetainsExactIntegersNullSemanticsAndUnavailability(){
        var maximum=Quantity.value(new BigInteger("9223372036854775807"));
        var wallet=HolyHirePoststate.wallet(scope(100),new Stocks(maximum,Quantity.knownNull(),Quantity.unavailable()),stocks(0),quote(0));
        var report=new Report(scope(100),wallet,HolyHirePoststate.troops(association(),Status.NOT_REQUESTED,List.of(),Optional.of("no current public armies")),Expenses.unavailable("cash producer unavailable"));
        var encoded=HolyHirePoststate.encode(report);var decoded=StrictJson.parse(encoded.bytes());
        assertEquals(HolyHirePoststate.json(report),decoded);
        assertEquals(new BigInteger("9223372036854775807"),decoded.path("wallet").path("before").path("gold").path("value").bigIntegerValue());
        assertTrue(decoded.path("wallet").path("before").path("prestige").path("value").isNull());
        assertEquals("UNAVAILABLE",decoded.path("expenses").path("status").textValue());
        assertFalse(decoded.path("troops").path("usable_army_observed").booleanValue());
    }
}

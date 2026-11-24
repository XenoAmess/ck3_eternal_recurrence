package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Draft DATA boundaries only. No Native response is synthesized or assigned genuine provenance. NOT_RUN. */
final class NativeCurrentRmtmRemainingDataTest {
    private static CurrentRmtmActorTransitionSource song(int date,boolean captured,int days,boolean advance) {
        return new CurrentRmtmActorTransitionSource(CurrentRmtmActorTransitionSource.Role.SONG,true,Optional.of(true),
                BigInteger.ZERO,Optional.of(0),Optional.empty(),Optional.empty(),days,14,date,captured,Optional.empty(),true,true,advance,false);
    }
    @Test void signedDateAndFullActorGuardDataDoNotAcquirePermission() {
        for(int date:new int[]{Integer.MIN_VALUE,0,-24,Integer.MAX_VALUE}) {
            var p=new CoreFrame.Prefix(date,3,true,0,true,true,-2,true);
            assertDoesNotThrow(()->CurrentRmtmActorTransition.requireCore(p));
            var s=song(date,false,0,false);assertFalse(s.advanceAdmissible());assertFalse(s.caseStartCaptured());
        }
    }
    @Test void capturedZeroDateCanDescribeAZeroDayCase()throws IOException {
        var s=song(0,true,0,true);assertEquals(s,CurrentRmtmActorTransitionSource.decode(s.encode()));
        assertTrue(s.caseStartCaptured());assertEquals(0,s.completedNaturalDays());assertTrue(s.executeTimeIdentityConfirmed().isEmpty());
    }
    @Test void originalMaximumFourteenCannotBecomeThirteenOrFifteen() {
        assertEquals(14,CurrentRmtmActorTransition.MAXIMUM_NATURAL_DAYS);
        assertDoesNotThrow(()->song(-48,true,14,false));
        assertThrows(IllegalArgumentException.class,()->song(-48,true,15,false));
        assertThrows(IllegalArgumentException.class,()->song(-48,true,14,true));
    }
    @Test void actualPendingCanBeConfirmedOnDayFiveWithoutAnInventedExecutionObservation()throws IOException {
        var p=new CurrentRmtmActorTransitionSource.Pending("original-day-five",BigInteger.ONE,BigInteger.TWO,NativeWire.UINT64_MAX,0,-2,0,24,1,true,true,true);
        var s=new CurrentRmtmActorTransitionSource(CurrentRmtmActorTransitionSource.Role.SUCCESSOR,true,Optional.of(true),BigInteger.ZERO,
                Optional.of(0),Optional.of(-2),Optional.of(p),5,14,-96,true,Optional.empty(),true,true,false,true);
        assertTrue(s.confirmAdmissible());assertTrue(s.executeTimeIdentityConfirmed().isEmpty());
        assertEquals(NativeWire.UINT64_MAX,CurrentRmtmActorTransitionSource.decode(s.encode()).pending().orElseThrow().originalDeadlineUnixMs());
    }
    @Test void pendingRetainsExactFullActorsAndOriginalDay() {
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmActorTransitionSource.Pending("op",BigInteger.ONE,BigInteger.ONE,BigInteger.ONE,0,0,0,24,1,true,true,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmActorTransitionSource.Pending("op",BigInteger.ONE,BigInteger.ONE,BigInteger.ONE,0,-2,0,25,1,true,true,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmActorTransitionSource.Pending("op",BigInteger.ONE,BigInteger.ONE,BigInteger.ONE,0,-1,0,24,1,true,true,true));
    }
    @Test void originalRunningFlagsRemainDataWithoutACompletedDay() {
        var p=new CurrentRmtmActorTransitionResult.Progress(BigInteger.ONE,0,24,0,0,-1,0,0,-1,true,true,true,false,false,false,true,false);
        assertTrue(p.armAttempted());assertTrue(p.armed());assertFalse(p.exactDayConfirmed());assertEquals(-1,p.afterActorId());
    }
    private static CurrentRmtmDecisionSource detail(Optional<Boolean> can,String tooltip,boolean admissible) {
        return new CurrentRmtmDecisionSource(true,true,true,true,true,true,false,false,true,false,admissible,true,true,Optional.of(tooltip),
                Optional.of(1),Optional.of(5),Optional.of(0),Optional.of(CurrentRmtmDecision.DecisionKey.RESTORE),can,
                List.of(new CurrentRmtmDecisionSource.Row(CurrentRmtmDecision.DecisionKey.RESTORE,false,true)));
    }
    @Test void selectedFalseCanAndCompleteEmptyOrRichTooltipAreRealData()throws IOException {
        for(String text:List.of("","\u0000\u0015\n#P actual 50%#!")) {
            var s=detail(Optional.of(false),text,false);assertFalse(s.nativeCanConfirm().orElseThrow());
            assertEquals(text,CurrentRmtmDecisionSource.decode(s.encode()).confirmTooltip().orElseThrow());
        }
    }
    @Test void nullCanDoesNotBecomeFalseAndCanTrueDoesNotReverseAdmissibility()throws IOException {
        var absent=detail(Optional.empty(),"",false);assertTrue(CurrentRmtmDecisionSource.decode(absent.encode()).nativeCanConfirm().isEmpty());
        var data=detail(Optional.of(true),"native explanation",false);assertFalse(data.confirmAdmissible());
        assertThrows(IllegalArgumentException.class,()->detail(Optional.empty(),"",true));
    }
    @Test void exactlyFiveFixedKeysHaveNoCallerArbitrarySelector()throws IOException {
        assertEquals(5,CurrentRmtmDecision.DecisionKey.values().length);
        assertEquals(CurrentRmtmDecision.DecisionKey.PREPARE_FIFTYONE,CurrentRmtmDecision.DecisionKey.parse("rqaui_prepare_fiftyone_decision"));
        assertThrows(IOException.class,()->CurrentRmtmDecision.DecisionKey.parse("xccc_corruption_policy_decision"));
        assertThrows(IOException.class,()->CurrentRmtmDecision.DecisionKey.parse("rmtm.1001"));
    }
    @Test void tooltipHasSixteenKiBReadBudgetWithoutInventedTextParsing()throws IOException {
        String full="a".repeat(16384);assertEquals(full,CurrentRmtmDecisionSource.decode(detail(Optional.of(false),full,false).encode()).confirmTooltip().orElseThrow());
        assertThrows(IllegalArgumentException.class,()->detail(Optional.of(false),full+"a",false));
        var r=detail(Optional.of(false),"actual text",false).encode();r.put("unexpected_expiry","1069.9.18");
        assertThrows(IOException.class,()->CurrentRmtmDecisionSource.decode(r));
    }
    private static CurrentLydSource.EventRow event(int instance,String definition,boolean can) {
        return new CurrentLydSource.EventRow(instance,0,1,definition,"opening","description",true,true,true,
                List.of(new CurrentLydSource.EventOption(0,can,"actual option","",Optional.empty(),Optional.empty())));
    }
    @Test void actionDefinesTwoFixedChannelsWithoutAnOptionRole()throws IOException {
        assertEquals(5,CurrentRmtmEvent.Action.values().length);
        assertEquals(CurrentRmtmEvent.Action.ACK_CHAOS,CurrentRmtmEvent.Action.QUERY_CHAOS.ackAction());
        assertEquals(CurrentRmtmEvent.Action.QUERY_SUMMARY,CurrentRmtmEvent.Action.ACK_SUMMARY.queryAction());
        assertThrows(IOException.class,()->CurrentRmtmEvent.Action.parse("select_tier_four"));
    }
    @Test void knownEmptyCensusRemainsDataWithoutAnAck()throws IOException {
        var s=new CurrentRmtmEventSource(new CurrentLydSource.Events(true,0,List.of()),Optional.empty(),false,false,true);
        assertEquals(s,CurrentRmtmEventSource.decode(s.encode()));assertFalse(s.ackAdmissible());
    }
    @Test void oneMaterialFixedOptionCanBeObservedFalseWithoutReversingPermission()throws IOException {
        var row=event(1,CurrentRmtmEvent.SUMMARY_DEFINITION,false);
        var s=new CurrentRmtmEventSource(new CurrentLydSource.Events(true,1,List.of(row)),Optional.of(1),true,false,true);
        assertEquals(s,CurrentRmtmEventSource.decode(s.encode()));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmEventSource(s.eventCensus(),Optional.of(1),true,true,true));
    }
    @Test void multipleEventsNeverBecomeAnAcknowledgementByFilteringOneMatch() {
        var all=new CurrentLydSource.Events(true,2,List.of(event(1,CurrentRmtmEvent.SUMMARY_DEFINITION,true),event(2,"other.1",true)));
        assertDoesNotThrow(()->new CurrentRmtmEventSource(all,Optional.empty(),true,false,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmEventSource(all,Optional.of(1),true,true,true));
    }
    @Test void councilVacancyIsOnlyANullIncumbentOfAnActualFixedTask()throws IOException {
        var seats=new java.util.ArrayList<CurrentRmtmObservationSource.Seat>();
        for(int n=0;n<9;n++)seats.add(new CurrentRmtmObservationSource.Seat(CurrentRmtmObservationSource.COUNCIL_KEYS.get(n),0x80000000L+n,Optional.empty(),Optional.empty()));
        var c=new CurrentRmtmObservationSource.Council(-2,12,true,true,seats);
        var s=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.COUNCIL,true,true,Optional.empty(),Optional.of(c),Optional.empty(),Optional.empty());
        assertEquals(s,CurrentRmtmObservationSource.decode(s.encode()));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmObservationSource.Council(-2,12,true,true,seats.subList(0,8)));
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmObservationSource.Seat("councillor_chancellor",0xffffffffL,Optional.empty(),Optional.empty()));
    }
    @Test void physicalEmptyDoesNotInventItsIndependentRealmOrScriptBooleans()throws IOException {
        var physical=new CurrentRmtmTitleQuerySource(0,0,Optional.empty(),Optional.empty(),0,List.of(),0,true);
        var p=new CurrentRmtmObservationSource.TitlePhase(CurrentRmtmObservation.Phase.D3,physical,false,false,true,true);
        var s=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.TITLE_PHASE,true,true,Optional.of(p),Optional.empty(),Optional.empty(),Optional.empty());
        var read=CurrentRmtmObservationSource.decode(s.encode()).titlePhase().orElseThrow();
        assertEquals(0,read.physical().nativeLawCount());assertFalse(read.holderRealmSingleHeir());assertFalse(read.scriptOwnSingleHeir());
    }
    @Test void ordinaryBudgetHiddenDataDoesNotImplyAnOpenOrAnEnact()throws IOException {
        var b=new CurrentRmtmObservationSource.Budget(false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),false,false,"my_realm_player",true);
        var s=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.BUDGET,false,true,Optional.empty(),Optional.empty(),Optional.of(b),Optional.empty());
        assertEquals(s,CurrentRmtmObservationSource.decode(s.encode()));assertFalse(b.openAdmissible());assertFalse(b.cancelAdmissible());
        assertThrows(IllegalArgumentException.class,()->new CurrentRmtmObservationSource.Budget(false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),true,false,"hud_top_liege",true));
    }
    @Test void offerReadKeepsNulControlsAndTargetIdentityWithoutGrantingSend()throws IOException {
        var o=new CurrentRmtmObservationSource.Offer(CurrentRmtmObservation.OfferTarget.RELEASED_A,false,false,false,false,0,-2,"offer_vassalization_interaction","\u0000\u0015actual\n",false,false,true);
        var s=new CurrentRmtmObservationSource(CurrentRmtmObservation.Kind.OFFER,false,true,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(o));
        assertEquals(s,CurrentRmtmObservationSource.decode(s.encode()));
        assertThrows(IOException.class,()->CurrentRmtmObservation.Action.parse("send_offer"));
        assertThrows(IOException.class,()->CurrentRmtmObservation.OfferTarget.parse("caller_character_123"));
    }
    @Test void eventReadPolicyKeepsNulAndCanonicalHyphenKeysAsData()throws IOException {
        var row=new CurrentLydSource.EventRow(1,-2,1,"other-key.1","\u0000\u0015opening","actual\n",true,true,true,
                List.of(new CurrentLydSource.EventOption(0,false,"\u0000text","\u0015reason",Optional.empty(),Optional.empty())));
        var s=new CurrentRmtmEventSource(new CurrentLydSource.Events(true,1,List.of(row)),Optional.empty(),false,false,true);
        assertEquals(s,CurrentRmtmEventSource.decode(s.encode()));assertFalse(s.ackAdmissible());
    }
}

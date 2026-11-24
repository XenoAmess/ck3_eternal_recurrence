package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA only. No Native response, displayed popup or action lease is fabricated. */
final class NativeCurrentLivingDisplayedOptionsDataTest {
    private static final int ACTOR=-2;
    private static final int INSTANCE=41;
    private static CurrentLydSource.EventOption option(int index,boolean can) {
        return new CurrentLydSource.EventOption(index,can,"Java DATA \0 actual text","",
                Optional.empty(),Optional.empty());
    }
    private static CurrentLydSource.EventRow event(int count,List<CurrentLydSource.EventOption> displayed) {
        return new CurrentLydSource.EventRow(INSTANCE,ACTOR,count,"xalw.10","","",true,true,true,displayed);
    }
    private static CurrentLivingUiSource.EventBinding binding(int actor) {
        var target=new CurrentLivingUiSource.ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,36,Optional.of(0L));
        var absent=new CurrentLivingUiSource.ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState.ABSENT,0,Optional.empty());
        return new CurrentLivingUiSource.EventBinding(INSTANCE,actor,"xalw.10",target,absent,true,false,false,true,true);
    }
    private static CurrentLivingUiSource source(CurrentLydSource.EventRow row,List<CurrentLivingUiSource.FixedAction> actions) {
        var census=new CurrentLivingUiSource.Events(true,1,List.of(row),List.of(binding(ACTOR)),actions,true);
        return new CurrentLivingUiSource(CurrentLivingUiSource.Kind.EVENTS,Integer.toUnsignedLong(ACTOR),
                Optional.empty(),Optional.of(census),Optional.empty(),true);
    }
    private static CurrentLivingUiSource.FixedAction fixed(CurrentLivingUi.Action action,int index,boolean admitted) {
        return new CurrentLivingUiSource.FixedAction(action,INSTANCE,index,admitted);
    }

    @Test void actualDisplayedSubsetRetainsAuthoredCountAndNoncontiguousIndices() throws Exception {
        var row=event(10,List.of(option(9,true),option(0,false),option(1,true),option(3,false)));
        var source=source(row,List.of(fixed(CurrentLivingUi.Action.CLOSE_MANAGEMENT,9,true),
                fixed(CurrentLivingUi.Action.FEED_COMMON,1,true),fixed(CurrentLivingUi.Action.FEED_FAMED,3,false)));
        var decoded=CurrentLivingUiSource.decode(source.encode());
        assertEquals(source,decoded);
        var actual=decoded.events().orElseThrow().events().get(0);
        assertEquals(10,actual.authoredOptionCount());
        assertEquals(List.of(9,0,1,3),actual.options().stream().map(CurrentLydSource.EventOption::authoredOptionIndex).toList());
        assertEquals(4,actual.options().size());
        assertTrue(decoded.actionAdmissible(CurrentLivingUi.Action.FEED_COMMON));
        assertFalse(decoded.actionAdmissible(CurrentLivingUi.Action.FEED_FAMED));
        assertTrue(decoded.actionAdmissible(CurrentLivingUi.Action.CLOSE_MANAGEMENT));
        var prefix=new CoreFrame.Prefix(Integer.MIN_VALUE,3,true,0,true,true,ACTOR,true);
        var owner=new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4L);
        var result=new CurrentLivingUiResult(CurrentLivingUi.Action.QUERY_EVENTS,CurrentLivingUiResult.Status.AVAILABLE,
                false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ZERO,Optional.of(prefix),Optional.of(owner),
                Optional.of(decoded),Optional.empty());
        assertEquals(result,CurrentLivingUiResult.decode(result.encode()));
        assertEquals(0xffff_fffeL,result.source().orElseThrow().actorFullId());
    }

    @Test void missingFixedActionsDoNotCreatePermissionOrPlaceholderOptions() throws Exception {
        var hidden=source(event(10,List.of(option(0,true),option(9,true))),List.of());
        assertEquals(List.of(0,9),hidden.events().orElseThrow().events().get(0).options().stream()
                .map(CurrentLydSource.EventOption::authoredOptionIndex).toList());
        assertTrue(hidden.actionAdmissible(CurrentLivingUi.Action.QUERY_EVENTS));
        for(var action:List.of(CurrentLivingUi.Action.FEED_COMMON,CurrentLivingUi.Action.FEED_MASTERWORK,
                CurrentLivingUi.Action.FEED_FAMED,CurrentLivingUi.Action.FEED_ILLUSTRIOUS,CurrentLivingUi.Action.CLOSE_MANAGEMENT))
            assertFalse(hidden.actionAdmissible(action));
        assertEquals(hidden,CurrentLivingUiSource.decode(hidden.encode()));
        for(boolean admitted:List.of(false,true))
            assertThrows(IllegalArgumentException.class,()->source(event(10,List.of(option(0,true),option(9,true))),
                    List.of(fixed(CurrentLivingUi.Action.FEED_COMMON,1,admitted))));
        var shownButNotLeased=source(event(10,List.of(option(1,true),option(9,true))),List.of());
        assertFalse(shownButNotLeased.actionAdmissible(CurrentLivingUi.Action.FEED_COMMON));
    }

    @Test void displayedSubsetKeepsIndexIdentityBindingAndCompletenessGuards() {
        assertThrows(IllegalArgumentException.class,()->event(10,List.of(option(1,true),option(1,false))));
        assertThrows(IllegalArgumentException.class,()->event(10,List.of(option(10,true))));
        assertThrows(IllegalArgumentException.class,()->source(event(9,List.of(option(1,true))),List.of()));
        assertThrows(IllegalArgumentException.class,()->source(event(10,List.of(option(0,true),option(1,true))),
                List.of(fixed(CurrentLivingUi.Action.FEED_COMMON,0,true))));
        var row=event(10,List.of(option(1,true),option(9,true)));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(true,2,List.of(row,row),List.of(),List.of(),true));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(true,1,List.of(row),
                List.of(binding(ACTOR),binding(ACTOR)),List.of(),true));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(true,1,List.of(row),
                List.of(binding(0)),List.of(),true));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(false,1,List.of(row),
                List.of(binding(ACTOR)),List.of(),true));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(true,1,List.of(row),
                List.of(binding(ACTOR)),List.of(),false));
        var withKey=new CurrentLydSource.EventOption(1,true,"Java DATA","",Optional.of("java_data.key"),Optional.empty());
        assertThrows(IllegalArgumentException.class,()->source(event(10,List.of(withKey)),List.of()));
        var complete=new CurrentLivingUiSource.Events(true,1,List.of(row),List.of(binding(ACTOR)),List.of(),true);
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource(CurrentLivingUiSource.Kind.EVENTS,
                Integer.toUnsignedLong(ACTOR),Optional.empty(),Optional.of(complete),Optional.empty(),false));
    }
}

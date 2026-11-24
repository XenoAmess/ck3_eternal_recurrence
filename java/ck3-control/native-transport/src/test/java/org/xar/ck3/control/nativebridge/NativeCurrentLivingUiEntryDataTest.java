package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure Java DATA. No C++ resources/frames, Native responses, live views or action permissions are fabricated. */
final class NativeCurrentLivingUiEntryDataTest {
    private static final BigInteger ONE=BigInteger.ONE;
    private static final BigInteger MAX=NativeWire.UINT64_MAX;
    private static final Set<String> CLAIM=Set.of("schema","game_version","executable_sha256","adapter_id","backend",
            "action","expected_core","provider_generation","query_sequence");
    private static CoreFrame.Partial core(int actor) {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(Integer.MIN_VALUE,3,true,0,true,true,actor,true));
    }
    private static CurrentLetterResult.OwnerWitness owner() {
        return new CurrentLetterResult.OwnerWitness(ONE,BigInteger.TWO,BigInteger.valueOf(3),4L);
    }
    private static CurrentLivingEntrySource inventory(int actor,boolean visible,boolean bound,boolean modal,boolean open) {
        var view=new CurrentLivingEntrySource.View(Integer.toUnsignedLong(actor),true,visible,true,bound,modal,open);
        return new CurrentLivingEntrySource(CurrentLivingEntrySource.Kind.INVENTORY,Integer.toUnsignedLong(actor),
                Optional.empty(),Optional.of(view),Optional.empty(),true);
    }
    private static CurrentLivingEntrySource.Manage manage(String tooltip,boolean nativeCan,boolean admissible) {
        return new CurrentLivingEntrySource.Manage(true,true,true,true,true,true,Optional.of(0),Optional.of(0),true,false,false,
                Optional.of(CurrentLivingEntry.MANAGE_DECISION),Optional.of(0),Optional.of(nativeCan),admissible,false,List.of(),true,
                Optional.of(tooltip),true);
    }
    private static CurrentLivingUiSource.ArtifactReference artifact(long id) {
        return new CurrentLivingUiSource.ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,36,Optional.of(id));
    }
    private static CurrentLivingUiSource.ArtifactReference absent() {
        return new CurrentLivingUiSource.ArtifactReference(CurrentLivingInventoryQuerySource.ReferenceState.ABSENT,0,Optional.empty());
    }
    private static CurrentLivingUiSource event(int actor,String definition,int count,CurrentLivingUi.Action action,int index,boolean admitted) {
        var options=new ArrayList<CurrentLydSource.EventOption>();
        for(int i=0;i<count;i++)options.add(new CurrentLydSource.EventOption(i,i==index,"Java DATA option","",
                Optional.empty(),Optional.empty()));
        var row=new CurrentLydSource.EventRow(41,actor,count,definition,"","",true,true,true,options);
        boolean review=definition.equals("xalw.11");
        var binding=new CurrentLivingUiSource.EventBinding(41,actor,definition,artifact(0),review?artifact(1):absent(),
                true,review,review,true,true);
        var data=new CurrentLivingUiSource.Events(true,1,List.of(row),List.of(binding),
                List.of(new CurrentLivingUiSource.FixedAction(action,41,index,admitted)),true);
        return new CurrentLivingUiSource(CurrentLivingUiSource.Kind.EVENTS,Integer.toUnsignedLong(actor),Optional.empty(),Optional.of(data),Optional.empty(),true);
    }
    private static void maxEnvelope(NativeRequest request,String family,boolean query) throws Exception {
        var fields=StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments",family));
        assertEquals(0,fields.get("arguments").size());
        var claim=StrictJson.object(fields.get(family),CLAIM);
        assertTrue(claim.get("provider_generation").isIntegralNumber());assertTrue(claim.get("query_sequence").isIntegralNumber());
        assertEquals(query?BigInteger.ZERO:MAX,claim.get("provider_generation").bigIntegerValue());
        assertEquals(query?BigInteger.ZERO:MAX,claim.get("query_sequence").bigIntegerValue());
        assertEquals(-2,claim.get("expected_core").get("played_character_id").intValue());
        assertEquals(Integer.MIN_VALUE,claim.get("expected_core").get("date_raw").intValue());
        // This is an explicitly authored Java DATA envelope, never an original C++ request or a Transport exchange.
        var envelope=StrictJson.object().put("type","execute_step").put("protocol_version",1)
                .put("request_id","java-data-living-max").put("step",request.step()).put("actor","local_player").put("deadline_unix_ms",MAX);
        envelope.putObject("target").put("kind","none");envelope.putObject("arguments").set(family,claim);
        byte[] packet=NativeWire.packet(StrictJson.canonical(envelope));
        assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        var actual=StrictJson.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)),
                Set.of("type","protocol_version","request_id","step","actor","target","arguments","deadline_unix_ms"));
        assertEquals(MAX,actual.get("deadline_unix_ms").bigIntegerValue());
        assertEquals(NativeWire.parse(StrictJson.canonical(envelope)),actual);assertFalse(actual.has("expected_revision"));
    }

    @Test void exactFactoriesKeepThreeQueryAndFiveEntryEffectGenerationsAndMaxDeadline() throws Exception {
        int queries=0,effects=0;
        for(var action:CurrentLivingEntry.Action.values()) {
            boolean query=action.queryOnly();if(query)queries++;else effects++;
            var request=CurrentLivingEntry.request(core(-2),action,query?BigInteger.ZERO:MAX,query?BigInteger.ZERO:MAX);
            assertEquals(CurrentLivingEntry.STEP,request.step());assertEquals(Optional.of(CurrentLivingEntry.CAPABILITY),request.requiredCapability());
            maxEnvelope(request,"living_entry",query);
            assertThrows(IllegalArgumentException.class,()->CurrentLivingEntry.request(core(-2),action,query?ONE:BigInteger.ZERO,query?ONE:BigInteger.ZERO));
        }
        assertEquals(3,queries);assertEquals(5,effects);
        for(var action:CurrentLivingUi.Action.values()) {
            boolean query=action.queryOnly();
            maxEnvelope(CurrentLivingUi.request(core(-2),action,query?BigInteger.ZERO:MAX,query?BigInteger.ZERO:MAX),"living_ui",query);
        }
        assertThrows(IllegalArgumentException.class,()->CurrentLivingEntry.request(core(-2),CurrentLivingEntry.Action.OPEN_INVENTORY,
                MAX.add(ONE),ONE));
    }

    @Test void observedFalseCanAndEmptyOrNulTooltipRemainDataWithoutConfirmPermission() throws Exception {
        for(String tooltip:List.of("","\0#P observed\ntext#!","x".repeat(16384))) {
            var m=manage(tooltip,false,false);
            var source=new CurrentLivingEntrySource(CurrentLivingEntrySource.Kind.MANAGE,0L,Optional.of(m),Optional.empty(),Optional.empty(),true);
            assertEquals(Optional.of(false),m.nativeCanConfirm());assertTrue(m.confirmTooltipObserved());
            assertEquals(Optional.of(tooltip),m.confirmTooltip());assertEquals(Optional.of(0),m.groupsCount());
            assertTrue(source.actionAdmissible(CurrentLivingEntry.Action.QUERY_MANAGE));
            assertFalse(source.actionAdmissible(CurrentLivingEntry.Action.CONFIRM_MANAGE));
            assertEquals(source,CurrentLivingEntrySource.decode(source.encode()));
        }
        assertThrows(IllegalArgumentException.class,()->manage("actual false is not permission",false,true));
        assertThrows(IllegalArgumentException.class,()->manage("x".repeat(16385),false,false));
        assertThrows(IllegalArgumentException.class,()->manage("\uD800",false,false));
    }

    @Test void knownClosedAndVisibleOtherPayloadOrModalDoNotInventOpenPermission() throws Exception {
        var closed=inventory(-2,false,false,false,true);
        assertTrue(closed.actionAdmissible(CurrentLivingEntry.Action.OPEN_INVENTORY)); // Necessary DATA shape, not a native lease.
        assertEquals(0xffff_fffeL,closed.inventory().orElseThrow().expectedPayloadFullId());
        var otherPayload=inventory(-2,true,false,false,false);
        assertFalse(otherPayload.inventory().orElseThrow().payloadBound());
        assertFalse(otherPayload.actionAdmissible(CurrentLivingEntry.Action.OPEN_INVENTORY));
        var modal=inventory(-2,false,false,true,false);
        assertFalse(modal.actionAdmissible(CurrentLivingEntry.Action.OPEN_INVENTORY));
        assertThrows(IllegalArgumentException.class,()->inventory(-2,true,false,false,true));
        assertThrows(IllegalArgumentException.class,()->inventory(-2,false,false,true,true));
        var detail=new CurrentLivingEntrySource(CurrentLivingEntrySource.Kind.DETAIL,0L,Optional.empty(),Optional.empty(),
                Optional.of(new CurrentLivingEntrySource.View(0xffff_fffeL,true,false,true,false,false,true)),true);
        assertTrue(detail.actionAdmissible(CurrentLivingEntry.Action.OPEN_DETAIL));
        assertFalse(detail.actionAdmissible(CurrentLivingEntry.Action.OPEN_INVENTORY));
        assertEquals(detail,CurrentLivingEntrySource.decode(detail.encode()));
    }

    @Test void managementCloseIsOnlyActualCountTenIndexNineNotTutorialClose() throws Exception {
        var source=event(0,"xalw.10",10,CurrentLivingUi.Action.CLOSE_MANAGEMENT,9,true);
        assertEquals(13,CurrentLivingUi.Action.CLOSE_MANAGEMENT.ordinal());
        assertTrue(source.actionAdmissible(CurrentLivingUi.Action.CLOSE_MANAGEMENT));
        var row=source.events().orElseThrow().fixedActions().get(0);
        assertEquals(41,row.instanceId());assertEquals(9,row.authoredOptionIndex());
        assertEquals(source,CurrentLivingUiSource.decode(source.encode()));
        assertThrows(IllegalArgumentException.class,()->event(0,"xalw.12",2,CurrentLivingUi.Action.CLOSE_MANAGEMENT,1,true));
        assertThrows(IllegalArgumentException.class,()->event(0,"xalw.10",10,CurrentLivingUi.Action.CLOSE_MANAGEMENT,0,true));
        assertFalse(event(0,"xalw.10",10,CurrentLivingUi.Action.CLOSE_MANAGEMENT,9,false)
                .actionAdmissible(CurrentLivingUi.Action.CLOSE_MANAGEMENT));
        // A close request's actual latest instance/settled_mask/lease and independent absence are not present in this public DATA test.
    }

    @Test void completeSixtyFourRootLivingContainerDoesNotWidenLegacyLydThirtyTwo() throws Exception {
        var rows=new ArrayList<CurrentLydSource.EventRow>();
        for(int i=1;i<=64;i++)rows.add(new CurrentLydSource.EventRow(i,0,0,"java_data.foreign_"+i,"\0","",true,false,false,List.of()));
        var census=new CurrentLivingUiSource.Events(true,64,rows,List.of(),List.of(),true);
        var source=new CurrentLivingUiSource(CurrentLivingUiSource.Kind.EVENTS,0L,Optional.empty(),Optional.of(census),Optional.empty(),true);
        assertEquals(source,CurrentLivingUiSource.decode(source.encode()));assertEquals(64,census.events().size());
        assertThrows(IllegalArgumentException.class,()->new CurrentLydSource.Events(true,64,rows));
        assertThrows(UnsupportedOperationException.class,()->census.events().clear());
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.Events(true,63,rows,List.of(),List.of(),true));
    }

    @Test void reviewRequiresDistinctOwnedKindThirtySixButConsumedQueryReferenceIsStillData() throws Exception {
        var review=event(0,"xalw.11",2,CurrentLivingUi.Action.CONFIRM_REVIEW,0,true);
        var binding=review.events().orElseThrow().bindings().get(0);
        assertEquals(Optional.of(0L),binding.target().artifactFullId());assertEquals(Optional.of(1L),binding.material().artifactFullId());
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.EventBinding(41,0,"xalw.11",artifact(0),artifact(0),true,true,true,true,true));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingUiSource.EventBinding(41,0,"xalw.11",artifact(0),artifact(1),true,false,true,true,true));
        assertThrows(IllegalArgumentException.class,()->artifact(0xffff_ffffL));assertEquals(Optional.of(0xffff_fffeL),artifact(0xffff_fffeL).artifactFullId());
        var refs=new ArrayList<CurrentLivingInventoryQuerySource.Reference>();
        for(var role:CurrentLivingInventoryQuerySource.ReferenceRole.values()) {
            boolean retained=role==CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_COMMON;
            refs.add(new CurrentLivingInventoryQuerySource.Reference(role,retained?CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT
                    :CurrentLivingInventoryQuerySource.ReferenceState.ABSENT,retained?36:0,retained?Optional.of(1L):Optional.empty()));
        }
        var afterConsumption=new CurrentLivingInventoryQuerySource(0L,List.of(),List.of(),Optional.empty(),refs,true,true);
        assertTrue(afterConsumption.artifacts().isEmpty());
        assertEquals(Optional.of(1L),afterConsumption.fixedReferences().get(1).artifactFullId());
        assertEquals(afterConsumption,CurrentLivingInventoryQuerySource.decode(afterConsumption.encode()));
        // The surviving public reference is not an owned material proof and cannot replace the .11 binding above.
    }

    @Test void dispatchRetainsBeforeSourceCoreOwnerAndCannotClaimAppliedOrClosed() throws Exception {
        var before=inventory(-2,false,false,false,true);
        var result=new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,CurrentLivingEntryResult.Status.DISPATCHED,
                true,true,true,ONE,ONE,ONE,Optional.of(core(-2).prefix()),Optional.of(owner()),Optional.of(before),Optional.empty());
        assertTrue(result.successful());assertFalse(result.source().orElseThrow().inventory().orElseThrow().visible());
        assertFalse(result.nativeHandled());assertFalse(result.newDateObserved());assertFalse(result.physicalSaveConfirmed());
        assertEquals(result,CurrentLivingEntryResult.decode(result.encode()));
        var after=inventory(-2,true,true,false,false);
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,
                CurrentLivingEntryResult.Status.DISPATCHED,true,true,true,ONE,ONE,ONE,Optional.of(core(-2).prefix()),Optional.of(owner()),Optional.of(after),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,
                CurrentLivingEntryResult.Status.DISPATCHED,true,true,true,ONE,ONE,ONE,Optional.of(core(0).prefix()),Optional.of(owner()),Optional.of(before),Optional.empty()));
        var closeBefore=event(0,"xalw.10",10,CurrentLivingUi.Action.CLOSE_MANAGEMENT,9,true);
        var close=new CurrentLivingUiResult(CurrentLivingUi.Action.CLOSE_MANAGEMENT,CurrentLivingUiResult.Status.DISPATCHED,
                true,true,true,ONE,ONE,ONE,Optional.of(core(0).prefix()),Optional.of(owner()),Optional.of(closeBefore),Optional.empty());
        assertEquals(1,close.source().orElseThrow().events().orElseThrow().events().size());
        assertEquals(close,CurrentLivingUiResult.decode(close.encode()));
        var forbidden=NativeWire.object(NativeWire.parse(close.encode().bytes())).deepCopy();forbidden.put("event_closed",true);
        assertThrows(IOException.class,()->CurrentLivingUiResult.decode(new RawJson(StrictJson.canonical(forbidden))));
    }

    @Test void unknownPreservesActualGenerationsClaimEntryAndUnknownCleanupWithSourceNull() throws Exception {
        var unknown=new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,CurrentLivingEntryResult.Status.INDETERMINATE,
                true,false,false,MAX,MAX,MAX,Optional.of(core(-2).prefix()),Optional.of(owner()),Optional.empty(),Optional.of("java_data_unknown"));
        assertFalse(unknown.successful());assertTrue(unknown.effectAttempted());assertFalse(unknown.nativeReturned());
        assertFalse(unknown.cleanupKnown());assertTrue(unknown.source().isEmpty());assertEquals(MAX,unknown.claimSequence());
        assertEquals(unknown,CurrentLivingEntryResult.decode(unknown.encode()));
        var ui=new CurrentLivingUiResult(CurrentLivingUi.Action.CLOSE_MANAGEMENT,CurrentLivingUiResult.Status.INDETERMINATE,
                true,false,false,MAX,MAX,MAX,Optional.of(core(-2).prefix()),Optional.of(owner()),Optional.empty(),Optional.of("java_data_unknown"));
        assertEquals(ui,CurrentLivingUiResult.decode(ui.encode()));assertEquals(MAX,ui.providerGeneration());assertEquals(MAX,ui.querySequence());
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,
                CurrentLivingEntryResult.Status.INDETERMINATE,true,false,false,MAX,MAX,MAX,Optional.of(core(-2).prefix()),Optional.of(owner()),
                Optional.of(inventory(-2,false,false,false,true)),Optional.of("java_data_unknown")));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingEntryResult(CurrentLivingEntry.Action.OPEN_INVENTORY,
                CurrentLivingEntryResult.Status.REJECTED,true,false,false,MAX,MAX,MAX,Optional.of(core(-2).prefix()),Optional.of(owner()),
                Optional.empty(),Optional.of("java_data_unknown")));
        var illegal=NativeWire.object(NativeWire.parse(unknown.encode().bytes())).deepCopy();illegal.put("native_returned",true).put("effect_attempted",false);
        assertThrows(IOException.class,()->CurrentLivingEntryResult.decode(new RawJson(StrictJson.canonical(illegal))));
    }
}

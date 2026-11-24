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
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Pure Java DATA only: no C++ frame, live case, actual payment or private action custody is invented. */
final class NativeCurrentZg361Ae2DataTest {
    private static final BigInteger ZERO = BigInteger.ZERO;
    private static final BigInteger ONE = BigInteger.ONE;
    private static final BigInteger MAX = NativeWire.UINT64_MAX;
    private static final Set<String> CLAIM = Set.of("schema","game_version","executable_sha256","adapter_id",
            "backend","action","expected_core","provider_generation","query_sequence");

    private static CoreFrame.Partial core(int actor) {
        return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(Integer.MIN_VALUE,3,true,0,true,true,actor,true));
    }
    private static CurrentLetterResult.OwnerWitness owner() {
        return new CurrentLetterResult.OwnerWitness(MAX,ONE,BigInteger.TWO,0xffff_ffffL);
    }
    private static CurrentZg361Ae2Source controls(boolean confirm) {
        var which = CurrentZg361Ae2Source.Control.PRESENT;
        var row = new CurrentZg361Ae2Source.ControlRow(which,which.definitionKey(),!confirm,!confirm,
                confirm ? Optional.of(true) : Optional.empty(),confirm);
        var controls = new CurrentZg361Ae2Source.Controls(true,!confirm,confirm,true,true,false,false,
                confirm ? Optional.of(which) : Optional.empty(),List.of(row));
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(controls),Optional.empty());
    }
    private static CurrentZg361Ae2Source.Option option(int index, boolean can, String text, String why, String tooltip) {
        return new CurrentZg361Ae2Source.Option(index,"zg361comp.1.ae2.r"+(index-14),can,text,why,tooltip);
    }
    private static CurrentZg361Ae2Source events(long recipient, boolean pay) {
        var options = List.of(option(17,false,"later","not selected","#P third#!"),
                option(15,pay,"pay now","","first\0tooltip\n\t"),option(16,false,"other","unavailable","second"));
        var snapshot = new CurrentZg361Ae2Source.Ae2(41,recipient,"zg361comp.1",42,true,true,true,true,true,options,pay);
        var census = List.of(new CurrentZg361Ae2Source.EventIdentity(7,0,"java_data.foreign"),
                new CurrentZg361Ae2Source.EventIdentity(41,recipient,"zg361comp.1"));
        return new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.EVENTS,Optional.empty(),
                Optional.of(new CurrentZg361Ae2Source.Events(true,census,Optional.of(snapshot))));
    }
    private static CurrentZg361Ae2Result result(CurrentZg361Ae2.Action action, CurrentZg361Ae2Result.Status status,
            int actor, CurrentZg361Ae2Source source) {
        boolean dispatch = status.dispatched();
        return new CurrentZg361Ae2Result(action,status,dispatch,dispatch,true,MAX,MAX,dispatch?MAX:ZERO,
                Optional.of(core(actor).prefix()),Optional.of(owner()),Optional.of(source),Optional.empty());
    }

    @Test void factoriesCaptureActualCoreAndCanonicalStringGenerationsWithoutCallerSelectors() throws Exception {
        int queries = 0;
        for (var action : CurrentZg361Ae2.Action.values()) {
            boolean query = action.queryOnly(); if (query) queries++;
            var request = CurrentZg361Ae2.request(core(-2),action,query?ZERO:MAX,query?ZERO:MAX);
            assertEquals(CurrentZg361Ae2.STEP,request.step()); assertEquals(Optional.of(action.capability()),request.requiredCapability());
            var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()),Set.of("arguments","zg361_ae2"));
            assertEquals(0,fields.get("arguments").size());
            var claim = StrictJson.object(fields.get("zg361_ae2"),CLAIM);
            assertTrue(claim.get("provider_generation").isTextual()); assertTrue(claim.get("query_sequence").isTextual());
            assertEquals((query?ZERO:MAX).toString(),claim.get("provider_generation").textValue());
            assertEquals(-2,claim.get("expected_core").get("played_character_id").intValue());
            assertEquals(Integer.MIN_VALUE,claim.get("expected_core").get("date_raw").intValue());
            byte[] packet = NativeGameTransport.currentZg361Ae2Packet("java-data-ae2-max",request,MAX);
            assertEquals(packet.length-4,ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt());
            var envelope = StrictJson.object(NativeWire.parse(Arrays.copyOfRange(packet,4,packet.length)),
                    Set.of("type","protocol_version","request_id","step","actor","target","arguments","deadline_unix_ms"));
            assertTrue(envelope.get("deadline_unix_ms").isIntegralNumber());
            assertEquals(MAX,envelope.get("deadline_unix_ms").bigIntegerValue());
            assertEquals(claim,envelope.get("arguments").get("zg361_ae2"));
            assertEquals("local_player",envelope.get("actor").textValue());
            assertEquals("none",envelope.get("target").get("kind").textValue());
            var decoded = NativeWire.decodeExecuteRequest(packet);
            assertTrue(decoded.expectedRevision().isEmpty()); assertTrue(decoded.expectedSnapshotRevision().isEmpty());
            assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(core(-2),action,query?ONE:ZERO,query?ONE:ZERO));
        }
        assertEquals(2,queries);
        assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(core(0),CurrentZg361Ae2.Action.CONFIRM_PRESENT,MAX.add(ONE),ONE));
        var invalidLocal = new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,
                new CoreFrame.Prefix(0,3,true,-1,true,true,0,true));
        assertThrows(IllegalArgumentException.class,()->CurrentZg361Ae2.request(invalidLocal,CurrentZg361Ae2.Action.QUERY_CONTROLS,ZERO,ZERO));
        assertThrows(IllegalArgumentException.class,()->core(-1));
        // The actual production packer supplies strict8; no test-only correct envelope replaces it.
    }

    @Test void falseCanAndIncompleteControlsAreReadableDataWithoutManufacturedPermission() throws Exception {
        var present = CurrentZg361Ae2Source.Control.PRESENT;
        var row = new CurrentZg361Ae2Source.ControlRow(present,present.definitionKey(),false,false,Optional.of(false),false);
        var controls = new CurrentZg361Ae2Source.Controls(false,false,true,false,false,false,false,Optional.of(present),List.of(row));
        var source = new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.CONTROLS,Optional.of(controls),Optional.empty());
        assertEquals(source,CurrentZg361Ae2Source.decode(source.encode()));
        assertEquals(Optional.of(false),controls.row(present).orElseThrow().nativeCanConfirm());
        assertTrue(source.actionAdmissible(CurrentZg361Ae2.Action.QUERY_CONTROLS));
        assertFalse(source.actionAdmissible(CurrentZg361Ae2.Action.CONFIRM_PRESENT));
        assertFalse(source.actionAdmissible(CurrentZg361Ae2.Action.OPEN_CONTROLS_LIST));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Controls(false,false,false,true,false,false,true,Optional.empty(),List.of()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.ControlRow(present,present.definitionKey(),false,false,Optional.of(false),true));
    }

    @Test void fixedControlIdentitySelectedDetailAndUnionRemainExact() {
        var present = CurrentZg361Ae2Source.Control.PRESENT;
        var row = new CurrentZg361Ae2Source.ControlRow(present,present.definitionKey(),false,false,Optional.of(false),false);
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.ControlRow(present,"zga_ae2_verify_decision",false,false,Optional.empty(),false));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Controls(true,false,true,true,true,false,false,Optional.empty(),List.of(row)));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Controls(true,false,true,true,true,false,false,Optional.of(present),List.of(row,row)));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source(CurrentZg361Ae2Source.Kind.EVENTS,Optional.of(controls(false).controls().orElseThrow()),Optional.empty()));
        assertTrue(controls(false).actionAdmissible(CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL));
        assertFalse(controls(false).actionAdmissible(CurrentZg361Ae2.Action.CONFIRM_PRESENT));
        assertTrue(controls(true).actionAdmissible(CurrentZg361Ae2.Action.CONFIRM_PRESENT));
        assertFalse(controls(true).actionAdmissible(CurrentZg361Ae2.Action.CONFIRM_VERIFY));
    }

    @Test void completeCensusRetainsForeignRowsAndPayJoinsAuthoredFifteenNotDisplayZero() throws Exception {
        var source = events(0xffff_fffeL,true); var events = source.events().orElseThrow();
        assertEquals(List.of(17,15,16),events.ae2().orElseThrow().options().stream().map(CurrentZg361Ae2Source.Option::authoredOptionIndex).toList());
        assertEquals(15,events.ae2().orElseThrow().payNowOption().authoredOptionIndex());
        assertEquals(2,events.census().size()); assertEquals("java_data.foreign",events.census().get(0).definitionKey());
        assertEquals(source,CurrentZg361Ae2Source.decode(source.encode()));
        assertThrows(UnsupportedOperationException.class,()->events.census().clear());
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Events(true,List.of(events.census().get(0)),events.ae2()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Events(false,List.of(),Optional.empty()));
        var duplicate = new ArrayList<>(events.census()); duplicate.add(events.census().get(1));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Events(true,duplicate,events.ae2()));
        var boundary = new ArrayList<CurrentZg361Ae2Source.EventIdentity>();
        for (int i=1;i<=32;i++) boundary.add(new CurrentZg361Ae2Source.EventIdentity(i,0,"java_data.event_"+i));
        assertEquals(32,new CurrentZg361Ae2Source.Events(true,boundary,Optional.empty()).census().size());
        boundary.add(new CurrentZg361Ae2Source.EventIdentity(33,0,"java_data.event_33"));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Events(true,boundary,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.EventIdentity(0,0,"java_data.zero"));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.EventIdentity(1,0xffff_ffffL,"java_data.invalid"));
        assertEquals(0,new CurrentZg361Ae2Source.EventIdentity(1,0,"java_data.zero_actor").recipientCharacterId());
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Source.Option(15,"zg361comp.1.ae2.r3",true,"","",""));
    }

    @Test void cachedLetterAndOwnedTooltipKeepTheirDistinctUnicodeAndNulBoundaries() throws Exception {
        String limit = "\uD83D\uDE00".repeat(4096);
        var row = option(15,false,"","\n\t",limit);
        assertEquals(limit,row.tooltip());
        assertEquals("\0\n\t#P rich#!",option(15,false,"","","\0\n\t#P rich#!").tooltip());
        assertThrows(IllegalArgumentException.class,()->option(15,false,"\0","",""));
        assertThrows(IllegalArgumentException.class,()->option(15,false,"","\0",""));
        assertThrows(IllegalArgumentException.class,()->option(15,false,"","",limit+"x"));
        assertThrows(IllegalArgumentException.class,()->option(15,false,"","","\uD800"));
        assertFalse(events(0,false).actionAdmissible(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW));
        assertEquals(events(0,false),CurrentZg361Ae2Source.decode(events(0,false).encode()));
    }

    @Test void successfulDispatchRequiresOriginalBeforeSourceAndOnlyPaySuccessJoinsActor() throws Exception {
        var open = result(CurrentZg361Ae2.Action.OPEN_PRESENT_DETAIL,CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,0,controls(false));
        assertEquals(open,CurrentZg361Ae2Result.decode(open.encode())); assertTrue(open.successful()); assertFalse(open.nativeHandled());
        var pay = result(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW,CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED,-2,events(0xffff_fffeL,true));
        assertEquals(pay,CurrentZg361Ae2Result.decode(pay.encode()));
        assertThrows(IllegalArgumentException.class,()->result(CurrentZg361Ae2.Action.CHOOSE_PAY_NOW,CurrentZg361Ae2Result.Status.SELECTION_DISPATCHED,-2,events(0,true)));
        var foreignQuery = result(CurrentZg361Ae2.Action.QUERY_AE2,CurrentZg361Ae2Result.Status.AVAILABLE,-2,events(0,false));
        assertEquals(foreignQuery,CurrentZg361Ae2Result.decode(foreignQuery.encode()));
        assertThrows(IllegalArgumentException.class,()->result(CurrentZg361Ae2.Action.CONFIRM_PRESENT,CurrentZg361Ae2Result.Status.NAVIGATION_DISPATCHED,0,controls(true)));
        assertThrows(IllegalArgumentException.class,()->result(CurrentZg361Ae2.Action.CONFIRM_PRESENT,CurrentZg361Ae2Result.Status.CONFIRMATION_DISPATCHED,0,controls(false)));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_AE2,
                CurrentZg361Ae2Result.Status.AVAILABLE,false,false,true,ONE,ONE,ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty()));
    }

    @Test void indeterminateRetainsPoisonedOriginalFlagsWithoutTurningThemIntoPermission() throws Exception {
        var unknown = new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_AE2,CurrentZg361Ae2Result.Status.INDETERMINATE,
                false,true,false,MAX,MAX,MAX,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual diagnostic"));
        assertEquals(unknown,CurrentZg361Ae2Result.decode(unknown.encode()));
        assertFalse(unknown.successful()); assertFalse(unknown.sourceAvailable()); assertTrue(unknown.nativeReturned());
        assertFalse(unknown.effectAttempted()); assertEquals(MAX,unknown.claimSequence());
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_AE2,
                CurrentZg361Ae2Result.Status.UNAVAILABLE,false,true,true,MAX,MAX,MAX,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("bad known refusal")));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_AE2,
                CurrentZg361Ae2Result.Status.UNAVAILABLE,false,false,false,ZERO,ZERO,ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("cleanup unknown")));
        assertThrows(IllegalArgumentException.class,()->new CurrentZg361Ae2Result(CurrentZg361Ae2.Action.QUERY_AE2,
                CurrentZg361Ae2Result.Status.INDETERMINATE,false,false,true,ZERO,ZERO,ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("")));
    }

    @Test void resultRejectsExtraBusinessFieldsMistypedNumbersAndOverflowWithoutErasingOriginalData() throws Exception {
        var valid = result(CurrentZg361Ae2.Action.QUERY_CONTROLS,CurrentZg361Ae2Result.Status.AVAILABLE,0,controls(false));
        var encoded = (ObjectNode)NativeWire.parse(valid.encode().bytes()); assertEquals(20,encoded.size());
        var extra = encoded.deepCopy(); extra.put("new_date_observed",false);
        assertThrows(IOException.class,()->CurrentZg361Ae2Result.decode(new RawJson(StrictJson.canonical(extra))));
        var numeric = encoded.deepCopy(); numeric.put("provider_generation",MAX);
        assertThrows(IOException.class,()->CurrentZg361Ae2Result.decode(new RawJson(StrictJson.canonical(numeric))));
        var overflow = encoded.deepCopy(); overflow.put("query_sequence",MAX.add(ONE).toString());
        assertThrows(IOException.class,()->CurrentZg361Ae2Result.decode(new RawJson(StrictJson.canonical(overflow))));
        var handled = encoded.deepCopy(); handled.put("native_handled",true);
        assertThrows(IOException.class,()->CurrentZg361Ae2Result.decode(new RawJson(StrictJson.canonical(handled))));
        var unavailable = encoded.deepCopy(); unavailable.put("source_available",false);
        assertThrows(IOException.class,()->CurrentZg361Ae2Result.decode(new RawJson(StrictJson.canonical(unavailable))));
        var oldCase = controls(false).encode(); oldCase.putObject("actual_case").put("owner_character_id",0);
        assertThrows(IOException.class,()->CurrentZg361Ae2Source.decode(oldCase));
    }
}

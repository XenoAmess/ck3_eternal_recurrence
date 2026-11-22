package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSource;
import org.xar.ck3.control.nativebridge.CurrentXqolPrompt;
import org.xar.ck3.control.nativebridge.CurrentXqolPromptSource;
import org.xar.ck3.control.nativebridge.CurrentXqolPromptResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Explicit Java DATA only. These tests grant no private Transport authority or Native/live credit. */
final class NativeOwnerCurrentXqolPromptSelectionTest {
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v29").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/xqol-prompt-selection-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static CoreFrame.Prefix core(int raw) {return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentXqolPromptSource absent() {return new CurrentXqolPromptSource(3,2,true,Optional.empty(),Optional.empty(),false,false);}
    private static CurrentXqolPromptSource source(int instance,boolean confirm,boolean cancel,boolean visible,boolean enabled,String opening) {
        var options=List.of(new CurrentLetterSource.Option(0,confirm,"confirm DATA","",Optional.of(CurrentXqolPrompt.CONFIRM_OPTION)),
                new CurrentLetterSource.Option(1,cancel,"cancel DATA","",Optional.of(CurrentXqolPrompt.CANCEL_OPTION)));
        var event=new CurrentXqolPromptSource.Event(3,true,true,visible,enabled,instance,42,CurrentXqolPrompt.KNOWN_DEFINITION,opening," description DATA ",options);
        return new CurrentXqolPromptSource(3,2,true,Optional.of(2),Optional.of(event),visible&&enabled&&confirm,visible&&enabled&&cancel);
    }
    private static CurrentXqolPromptSource ready() {return source(7,true,true,true,true," opening DATA ");}
    private static CurrentXqolPromptResult frame(CurrentXqolPrompt.Action action,int provider,int query,int raw,int connection,CurrentXqolPromptSource source) {
        boolean effect=action!=CurrentXqolPrompt.Action.QUERY_PROMPT;
        return new CurrentXqolPromptResult(action,effect?CurrentXqolPromptResult.dispatchedStatus(action):CurrentXqolPromptResult.Status.AVAILABLE,
                effect,effect,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(raw)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),
                Optional.of(source),Optional.empty(),effect?source.event().map(CurrentXqolPromptSource.Event::instanceId):Optional.empty());
    }
    private static CurrentXqolPromptResult query(CurrentXqolPromptSource source) {return frame(CurrentXqolPrompt.Action.QUERY_PROMPT,1,2,1000,1,source);}

    @Test void threeExplicitModesSelectOnlyOneFixedIndependentAction() {
        var modes=List.of("current_xqol_conversion_prompt_query","current_xqol_conversion_prompt_confirm","current_xqol_conversion_prompt_cancel");
        var actions=List.of(CurrentXqolPrompt.Action.QUERY_PROMPT,CurrentXqolPrompt.Action.CONFIRM_CONVERSION,CurrentXqolPrompt.Action.CANCEL_CONVERSION);
        var expected=List.of(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_QUERY,
                NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CONFIRM,NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_CANCEL);
        for(int i=0;i<modes.size();i++) {
            assertEquals(actions.get(i),NativeOwnerSnapshotMain268.currentXqolPromptAction(config(modes.get(i))));
            assertEquals(expected.get(i),NativeOwnerSnapshotMain268.observationMode(config(modes.get(i))));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_confirm ")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_confirm_then_cancel")));
    }
    @Test void allSixCommonFieldsAndBoundedIntegerLimitsAreRequired() {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=config("current_xqol_conversion_prompt_query");n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        for(String field:List.of("overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put(field,true)));
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put(field,0)));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put("overall_timeout_seconds",601)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put("read_timeout_seconds",61)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put("maximum_frames_per_operation",65537)));
    }
    @Test void ownerDescriptorRequiresExactFilePinObjectAndRealIntegerBytes() {
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put("owner_descriptor","D:/owner.json")));
        for(String field:List.of("path","bytes","sha256")) {
            var n=config("current_xqol_conversion_prompt_query");((ObjectNode)n.get("owner_descriptor")).remove(field);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        for(var invalid:List.of(StrictJson.object().put("path","D:/owner.json").put("bytes",true).put("sha256","0".repeat(64)),
                StrictJson.object().put("path","D:/owner.json").put("bytes",1.0).put("sha256","0".repeat(64)),
                StrictJson.object().put("path","D:/owner.json").put("bytes",1).put("sha256","bad"),
                StrictJson.object().put("path","D:/owner.json").put("bytes",1).put("sha256","0".repeat(64)).put("lease",1))) {
            var n=config("current_xqol_conversion_prompt_query");n.set("owner_descriptor",invalid);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
    }
    @Test void everyModeRejectsCallerEventInstanceOptionCoreLeaseAndAutomaticFollowup() {
        for(String mode:List.of("current_xqol_conversion_prompt_query","current_xqol_conversion_prompt_confirm","current_xqol_conversion_prompt_cancel"))
            for(String field:List.of("instance_id","event","event_key","definition_key","option","option_key","authored_option_index","index","expected_core","provider_generation","query_sequence","claim_sequence","native_can_select","action","decision_key","deadline","control_step","auto_confirm","auto_cancel"))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode).put(field,1)),field);
    }
    @Test void oldV24ThroughV28DiscriminatorsRemainAndCannotBorrowNewModes() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v24","xar.native-owner-snapshot-config/v25","xar.native-owner-snapshot-config/v26","xar.native-owner-snapshot-config/v27","xar.native-owner-snapshot-config/v28"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_prompt_query").put("schema",schema)));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_letter_query").put("schema","xar.native-owner-snapshot-config/v24")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_SET_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_letter_set_query").put("schema","xar.native-owner-snapshot-config/v26")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FULLSCREEN_EVENT_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_fullscreen_event_query").put("schema","xar.native-owner-snapshot-config/v27")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CURATED_DECISIONS_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_curated_decisions_query").put("schema","xar.native-owner-snapshot-config/v28")));
    }
    @Test void observedAbsentKnownPromptRetainsOtherResidentWindowsButGrantsNoAction() {
        var q=query(absent());assertEquals(3,q.source().orElseThrow().residentCount());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptQueryFrame(q,core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptQueryFrame(q,core(1024)));
        for(var action:CurrentXqolPrompt.Action.values())assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(q,action));
    }
    @Test void confirmAndCancelEachRequireTheirOwnActualNativeCanWithoutFallback() {
        var confirmOnly=query(source(7,true,false,true,true,"DATA"));var cancelOnly=query(source(7,false,true,true,true,"DATA"));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(confirmOnly,CurrentXqolPrompt.Action.CONFIRM_CONVERSION));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(confirmOnly,CurrentXqolPrompt.Action.CANCEL_CONVERSION));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(cancelOnly,CurrentXqolPrompt.Action.CANCEL_CONVERSION));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(cancelOnly,CurrentXqolPrompt.Action.CONFIRM_CONVERSION));
        for(var s:List.of(source(7,true,true,false,true,"DATA"),source(7,true,true,true,false,"DATA")))
            for(var a:List.of(CurrentXqolPrompt.Action.CONFIRM_CONVERSION,CurrentXqolPrompt.Action.CANCEL_CONVERSION))
                assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(query(s),a));
    }
    @Test void callbackMustRetainFullSourceCoreProviderQueryActualInstanceAndConnection() {
        var q=query(ready());var action=CurrentXqolPrompt.Action.CONFIRM_CONVERSION;
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptDispatchFrame(q,frame(action,1,2,1000,1,ready()),action));
        for(var bad:List.of(frame(action,2,2,1000,1,ready()),frame(action,1,3,1000,1,ready()),frame(action,1,2,1024,1,ready()),
                frame(action,1,2,1000,2,ready()),frame(action,1,2,1000,1,source(8,true,true,true,true," opening DATA ")),
                frame(action,1,2,1000,1,source(7,true,true,true,true,"opening DATA")),q))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptDispatchFrame(q,bad,action));
    }
    @Test void otherFixedActionOrReadonlyFrameCannotStandInForThisDispatch() {
        var q=query(ready());
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptDispatchFrame(q,frame(CurrentXqolPrompt.Action.CANCEL_CONVERSION,1,2,1000,1,ready()),CurrentXqolPrompt.Action.CONFIRM_CONVERSION));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptDispatchFrame(q,q,CurrentXqolPrompt.Action.CONFIRM_CONVERSION));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolPromptSource(q,CurrentXqolPrompt.Action.QUERY_PROMPT));
    }
    @Test void voidCallbackDataNeverProvesClosedPromptConversionDateOrSave()throws IOException {
        for(var action:List.of(CurrentXqolPrompt.Action.CONFIRM_CONVERSION,CurrentXqolPrompt.Action.CANCEL_CONVERSION)) {
            var f=frame(action,1,2,1000,1,ready());assertTrue(f.successful());
            var n=StrictJson.parse(f.encode().bytes(),1<<20);assertTrue(n.get("effect_attempted").booleanValue());assertTrue(n.get("native_returned").booleanValue());
            for(String field:List.of("native_handled","event_closed","conversion_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(field).booleanValue(),field);
        }
    }
}

package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEvent;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEventResult;
import org.xar.ck3.control.nativebridge.CurrentFullscreenEventSource;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA selection only. Private query authority and runtime effect remain separate. */
final class NativeOwnerCurrentFullscreenEventSelectionTest {
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v27").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/fullscreen-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static CoreFrame.Prefix core(int date) {return new CoreFrame.Prefix(date,1,true,0,true,true,42,true);}
    private static CurrentFullscreenEventSource source(int instance,int count,boolean visible,boolean nativeCan,boolean known,String opening) {
        return new CurrentFullscreenEventSource(count,true,true,visible,true,Optional.of(instance),Optional.of(42),
                Optional.of(known?CurrentFullscreenEvent.KNOWN_DEFINITION:"java_data_unknown_intro"),Optional.of(opening),Optional.of("Java DATA description"),
                List.of(new CurrentFullscreenEventSource.Option(0,nativeCan,"Java DATA acknowledgement","",known?Optional.of(CurrentFullscreenEvent.KNOWN_OPTION):Optional.empty())),
                count==1&&visible&&nativeCan&&known);
    }
    private static CurrentFullscreenEventSource known(int instance) {return source(instance,1,true,true,true,"  Java DATA opening  ");}
    private static CurrentFullscreenEventResult frame(boolean dispatched,int provider,int query,int date,CurrentFullscreenEventSource source) {
        return new CurrentFullscreenEventResult(dispatched?CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN:CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,
                dispatched?CurrentFullscreenEventResult.Status.ACK_DISPATCHED:CurrentFullscreenEventResult.Status.AVAILABLE,
                dispatched,dispatched,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),dispatched?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(date)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(source),Optional.empty(),
                dispatched?source.instanceId():Optional.empty());
    }
    private static CurrentFullscreenEventResult query() {return frame(false,1,2,1000,known(7));}
    @Test void explicitV27SeparatesReadonlyQueryFromFixedKnownIntroAcknowledge() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FULLSCREEN_EVENT_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_fullscreen_event_query")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FULLSCREEN_EVENT_ACK_KNOWN_INTRO,NativeOwnerSnapshotMain268.observationMode(config("current_fullscreen_event_ack_known_intro")));
        for(String mode:List.of("current_fullscreen_event_ack","current_fullscreen_event_query ","current_letter_query",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)),mode);
    }
    @Test void bothModesRequireAllCommonFields() {
        for(String mode:List.of("current_fullscreen_event_query","current_fullscreen_event_ack_known_intro"))
            for(String field:List.of("mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
                var n=config(mode);n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),mode+"/"+field);
            }
    }
    @Test void noConfiguredEventOptionInstanceCoreLeaseOrAuthority() {
        for(String mode:List.of("current_fullscreen_event_query","current_fullscreen_event_ack_known_intro"))
            for(String field:List.of("instance_id","event","event_key","definition_key","option","option_key","authored_option_index","index","native_token",
                    "expected_core","provider_generation","query_sequence","claim_sequence","deadline","recipient_character_id","native_can_select","known_intro_admissible","caller_bool","control_step")) {
                var n=config(mode);n.put(field,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),mode+"/"+field);
            }
    }
    @Test void olderSchemasCannotBorrowNewModes() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v24","xar.native-owner-snapshot-config/v25","xar.native-owner-snapshot-config/v26"))
            for(String mode:List.of("current_fullscreen_event_query","current_fullscreen_event_ack_known_intro"))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode).put("schema",schema)));
    }
    @Test void oldV24AndV26StillSelectTheirOriginalModesAndFieldContracts() {
        var old=config("current_letter_query").put("schema","xar.native-owner-snapshot-config/v24");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
        var set=config("current_letter_set_query").put("schema","xar.native-owner-snapshot-config/v26");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_SET_QUERY,NativeOwnerSnapshotMain268.observationMode(set));
        var reply=config("current_letter_set_reply_known_instance").put("schema","xar.native-owner-snapshot-config/v26").put("instance_id",3);
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_SET_REPLY_KNOWN_INSTANCE,NativeOwnerSnapshotMain268.observationMode(reply));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(set.put("instance_id",3)));
    }
    @Test void readonlyQueryNeedsItsActualCoreAndCannotMasqueradeAsAcknowledgement() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentFullscreenQueryFrame(query(),core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentFullscreenQueryFrame(query(),core(1024)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentFullscreenQueryFrame(frame(true,1,2,1000,known(7)),core(1000)));
    }
    @Test void emptyCompleteAbsenceIsReadableButCannotAuthorizeAcknowledgement() {
        var absent=new CurrentFullscreenEventSource(0,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of(),false);
        var q=frame(false,1,2,1000,absent);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentFullscreenQueryFrame(q,core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentFullscreenAcknowledgementSource(q));
    }
    @Test void actualMultipleUnknownHiddenAndNativeCanFalseSourcesDoNotGrantFixedAck()throws IOException {
        assertEquals(7,NativeOwnerSnapshotMain268.requireCurrentFullscreenAcknowledgementSource(query()).instanceId().orElseThrow());
        for(var source:List.of(source(7,2,true,true,true,"Java DATA multiple"),source(7,1,true,true,false,"Java DATA unknown"),
                source(7,1,false,true,true,"Java DATA hidden"),source(7,1,true,false,true,"Java DATA native false"))) {
            var q=frame(false,1,2,1000,source);
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentFullscreenQueryFrame(q,core(1000)));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentFullscreenAcknowledgementSource(q));
        }
    }
    @Test void callbackRequiresExactOriginalCoreProviderQueryInstanceAndUntrimmedFullSource() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentFullscreenAcknowledgementFrame(query(),frame(true,1,2,1000,known(7))));
        for(var invalid:List.of(frame(true,2,2,1000,known(7)),frame(true,1,3,1000,known(7)),frame(true,1,2,1024,known(7)),
                frame(true,1,2,1000,known(8)),frame(true,1,2,1000,source(7,1,true,true,true,"Java DATA opening")),query()))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentFullscreenAcknowledgementFrame(query(),invalid));
    }
    @Test void voidCallbackRetainsTextAndStillDeclaresNoClosureDateOrSave()throws IOException {
        var n=StrictJson.parse(frame(true,1,2,1000,known(7)).encode().bytes(),1<<20);
        assertEquals("  Java DATA opening  ",n.get("source").get("opening").textValue());assertTrue(n.get("native_returned").booleanValue());
        for(String key:List.of("native_handled","fullscreen_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
}

package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLetter;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.CurrentLetterSource;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Explicit Java DATA validates selection only; no private Transport authority or live outcome. */
final class NativeOwnerCurrentLetterSelectionTest {
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v24").put("mode",mode)
                .put("overall_timeout_seconds",60).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/letter-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static CoreFrame.Prefix core(int date) {return new CoreFrame.Prefix(date,1,true,0,true,true,42,true);}
    private static CurrentLetterSource source(int instance) {
        return new CurrentLetterSource(1,true,true,true,true,Optional.of(instance),Optional.of(42),Optional.of(CurrentLetter.KNOWN_DEFINITION),
                Optional.of("Java DATA opening"),Optional.of("Java DATA description"),List.of(new CurrentLetterSource.Option(0,true,"Java DATA reply","",Optional.of(CurrentLetter.KNOWN_OPTION))),true);
    }
    private static CurrentLetterResult frame(CurrentLetter.Action action,CurrentLetterResult.Status status,int provider,int query,
            CoreFrame.Prefix p,CurrentLetterSource s) {
        boolean dispatched=status==CurrentLetterResult.Status.REPLY_DISPATCHED;
        return new CurrentLetterResult(action,status,dispatched,dispatched,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),dispatched?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(p),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(s),Optional.empty());
    }
    private static CurrentLetterResult query() {return frame(CurrentLetter.Action.QUERY_LETTER,CurrentLetterResult.Status.AVAILABLE,1,2,core(1000),source(7));}
    private static CurrentLetterResult reply(int provider,int query,int date,int instance) {return frame(CurrentLetter.Action.REPLY_KNOWN,CurrentLetterResult.Status.REPLY_DISPATCHED,provider,query,core(date),source(instance));}
    @Test void explicitV24SeparatesReadonlyFromOneFixedReply() {
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_letter_query")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_REPLY_KNOWN,NativeOwnerSnapshotMain268.observationMode(config("current_letter_reply_known")));
        for(String mode:List.of("reply","current_djc_declaration_submit","current_succession_default_continue","current_letter_query ",""))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)),mode);
    }
    @Test void everyCommonFieldIsRequiredAndAdditionalInputAuthorityIsRejected() {
        for(String field:List.of("mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=config("current_letter_reply_known");n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
        for(String field:List.of("definition","definition_key","option","authored_option_index","instance_id","recipient_character_id","target_character_id",
                "expected_core","provider_generation","query_sequence","native_can_select","known_reply_admissible","deadline","control_step","maximum_status_polls","cb_key")) {
            var n=config("current_letter_reply_known");n.put(field,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
    }
    @Test void oldSchemasCannotBorrowLetterModesAndV22V23RemainSelected() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v22","xar.native-owner-snapshot-config/v23","xar.native-owner-snapshot-config/v25"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_letter_reply_known").put("schema",schema)));
        var old=config("current_succession_default_continue").put("schema","xar.native-owner-snapshot-config/v22");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUCCESSION_CONTINUE,NativeOwnerSnapshotMain268.observationMode(old));
        var djc=config("current_djc_declaration_ui").put("schema","xar.native-owner-snapshot-config/v23").put("target_character_id",17).put("cb_key","duchy_de_jure_greatwar");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DJC_DECLARATION_UI,NativeOwnerSnapshotMain268.observationMode(djc));
    }
    @Test void queryFrameMustHaveItsActualCoreAndReadonlyRole() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterQueryFrame(query(),core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterQueryFrame(query(),core(1024)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterQueryFrame(reply(1,2,1000,7),core(1000)));
    }
    @Test void readonlyAvailableDoesNotInventKnownReplyAuthority() {
        var none=new CurrentLetterSource(0,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of(),false);
        var q=frame(CurrentLetter.Action.QUERY_LETTER,CurrentLetterResult.Status.AVAILABLE,1,2,core(1000),none);
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterQueryFrame(q,core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterReplyFrame(q,reply(1,2,1000,7)));
    }
    @Test void callbackNeedsExactOriginalProviderQueryCoreAndFullBeforeSource() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentLetterReplyFrame(query(),reply(1,2,1000,7)));
        for(var different:List.of(reply(2,2,1000,7),reply(1,3,1000,7),reply(1,2,1024,7),reply(1,2,1000,8),query()))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLetterReplyFrame(query(),different));
    }
    @Test void voidCallbackEncodingStillDeclaresNoClosureDateOrSave()throws IOException {
        var n=StrictJson.parse(reply(1,2,1000,7).encode().bytes(),1<<20);
        assertTrue(n.get("native_returned").booleanValue());
        for(String key:List.of("native_handled","letter_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
}

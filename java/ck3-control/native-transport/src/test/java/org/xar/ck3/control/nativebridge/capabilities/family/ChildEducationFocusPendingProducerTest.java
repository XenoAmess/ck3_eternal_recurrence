package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Actual canonical DATA producer -> sole native codecs/metadata consumer. No writer, Native source or Root authority is manufactured. */
final class ChildEducationFocusPendingProducerTest {
    private static final Context BEFORE=new Context(frame(9),BigInteger.valueOf(19));
    private static Frame frame(int revision){return new Frame("native:"+revision,"focus-source-shaped-episode",BigInteger.valueOf(revision),100,7);}
    private static Selection selection(Key key){return new Selection(0xFE000001L,key);}
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
    private static Submitted submitted(Selection selected,SubmitStatus status,boolean accepted){
        var n=StrictJson.object().put("schema",SCHEMA).put("kind","submit").put("status",status.name().toLowerCase(java.util.Locale.ROOT))
                .putNull("unavailable_reason").put("action_request_id","original-focus").put("accepted",accepted)
                .put("child_full_id",selected.child()).put("requested_focus_key",selected.target().wire());n.set("pre_frame",encodeFrame(BEFORE.frame()));
        return decodeSubmitted(raw(n),BEFORE.frame(),selected,"original-focus");
    }
    private static RawJson receipt(Pending pending,Frame after,ReceiptStatus status,boolean applied,boolean published,boolean includePost){
        var n=StrictJson.object().put("schema",SCHEMA).put("kind","receipt").put("status",status.name().toLowerCase(java.util.Locale.ROOT))
                .putNull("unavailable_reason").put("observed_applied",applied);
        var submission=(ObjectNode)StrictJson.parse(submitted(pending.selection(),SubmitStatus.SUBMITTED_VERIFICATION_PENDING,true).original().bytes());
        submission.remove(List.of("schema","kind"));n.set("submission",submission);
        if(includePost){var p=n.putObject("post_observation").put("action_request_id",pending.actionRequestId())
                .put("independently_published_after_submission",published).put("child_full_id",pending.selection().child());p.set("source_frame",encodeFrame(after));
            p.putObject("current_focus").put("available",true).putNull("unavailable_reason").put("presence","present").put("key",pending.selection().target().wire());
        }else n.putNull("post_observation");
        return raw(n);
    }
    @Test void fiveRealKeysAndFullNativeChildIdentityRoundtripWithoutInventingAcceptance(){
        assertEquals(Key.values().length,ChildEducationFocusIntent.FocusKey.values().length);
        for(var key:ChildEducationFocusIntent.FocusKey.values()){
            var intent=new ChildEducationFocusIntent(0xFE000001L,key,Optional.empty());
            var selected=ChildEducationFocusEffects.selection(intent);assertEquals(key.wire(),selected.target().wire());
            var pending=ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.empty()).orElseThrow();
            assertEquals(PendingStatus.ACTION_STATE_UNKNOWN,pending.status());assertTrue(pending.accepted().isEmpty());assertTrue(pending.nativeCommandSubmitted().isEmpty());
            assertEquals(pending,decodePending(pending.original()));assertEquals(pending.original(),verifyPending(pending));
            var n=StrictJson.parse(pending.original().bytes());assertTrue(n.get("accepted").isNull());assertTrue(n.get("native_command_submitted").isNull());
            assertEquals(0xFE000001L,pending.selection().child());assertEquals(BEFORE,pending.sourceContext());
            assertFalse(n.has("driver_history"));assertFalse(n.has("observed_applied"));
        }
    }
    @Test void originalSubmittedPayloadFeedsTheOnePendingProducerAndReceiptConsumer(){
        var selected=selection(Key.EDUCATION_STEWARDSHIP);var original=submitted(selected,SubmitStatus.SUBMITTED_VERIFICATION_PENDING,true);
        var pending=ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.of(original)).orElseThrow();
        assertEquals(PendingStatus.SUBMITTED_VERIFICATION_PENDING,pending.status());assertEquals(Optional.of(true),pending.accepted());assertEquals(Optional.of(true),pending.nativeCommandSubmitted());
        var after=frame(10);var observed=decodeReceipt(receipt(pending,after,ReceiptStatus.OBSERVED_APPLIED,true,true,true),after,pending);
        assertTrue(observed.observedApplied());assertEquals(selected.target().wire(),observed.post().orElseThrow().focus().key().orElseThrow());
        var projected=ChildEducationFocusQueries.project(observed,new Context(after,BigInteger.valueOf(20)),"independent-focus-read",Optional.of(pending));
        assertEquals("original-focus",((org.xar.ck3.control.planning.opportunity.OpportunityJson.Text)projected.get("action_request_id")).value());
        assertEquals(pending.preFrame(),decodePending(pending.original()).preFrame());
    }
    @Test void unknownNeverBecomesAnAckAndExplicitNativeRejectionDoesNotBecomePending(){
        var selected=selection(Key.EDUCATION_LEARNING);
        var unknown=ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.of(submitted(selected,SubmitStatus.SUBMIT_UNKNOWN,false))).orElseThrow();
        assertEquals(PendingStatus.SUBMIT_UNKNOWN,unknown.status());assertEquals(Optional.of(false),unknown.accepted());assertTrue(unknown.nativeCommandSubmitted().isEmpty());
        assertTrue(ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.of(submitted(selected,SubmitStatus.REJECTED_BEFORE_SUBMIT,false))).isEmpty());
        var valid=submitted(selected,SubmitStatus.SUBMITTED_VERIFICATION_PENDING,true);
        var changed=new Submitted(new Submission(SubmitStatus.SUBMIT_UNKNOWN,Optional.empty(),"original-focus",false,selected,BEFORE.frame()),valid.original());
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.of(changed)));
    }
    @Test void realPostQueueErrorAckBranchRetainsUnknownWithoutInventingAcceptedFalse() throws Exception {
        var selected=selection(Key.EDUCATION_LEARNING);
        byte[] body=StrictJson.canonical(StrictJson.object().put("type","command_result").put("protocol_version",1)
                .put("request_id","original-focus").put("ok",false).put("error","native completion could not reclaim submitted command"));
        var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(NativeWire.packet(body)));
        var error=new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),
                decoded.result().token().map(token->new RawJson(token.value())),new RawJson(decoded.payload().value()),decoded.packet().value());
        var original=ChildEducationFocusEffects.submittedData(error,BEFORE,selected,"original-focus");
        assertTrue(original.isEmpty());
        var pending=ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",original).orElseThrow();
        assertEquals(PendingStatus.ACTION_STATE_UNKNOWN,pending.status());assertTrue(pending.accepted().isEmpty());assertTrue(pending.nativeCommandSubmitted().isEmpty());
        // A source-shaped receipt exercises the codec only; it grants no Root authority.
        assertTrue(decodeReceipt(receipt(pending,frame(10),ReceiptStatus.OBSERVED_APPLIED,true,true,true),frame(10),pending).observedApplied());
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusEffects.submittedData(error,BEFORE,selected,"different-request"));
    }
    @Test void ackCurrentFocusAndSameSemCannotReplaceTheNativeIndependentReceipt(){
        var pending=ChildEducationFocusEffects.pendingData(BEFORE,selection(Key.EDUCATION_MARTIAL),"original-focus",Optional.empty()).orElseThrow();
        assertThrows(IllegalArgumentException.class,()->decodeReceipt(receipt(pending,frame(9),ReceiptStatus.OBSERVED_APPLIED,true,true,true),frame(9),pending));
        assertThrows(IllegalArgumentException.class,()->decodeReceipt(receipt(pending,frame(10),ReceiptStatus.OBSERVED_APPLIED,true,false,true),frame(10),pending));
        assertThrows(IllegalArgumentException.class,()->decodeReceipt(receipt(pending,frame(10),ReceiptStatus.OBSERVED_APPLIED,true,true,false),frame(10),pending));
        var onlyFocus=decodeReceipt(receipt(pending,frame(10),ReceiptStatus.VERIFICATION_PENDING,false,true,true),frame(10),pending);
        assertFalse(onlyFocus.observedApplied());assertEquals(ReceiptStatus.VERIFICATION_PENDING,onlyFocus.status());
    }
    @Test void missingLiveBridgePendingAfterRestartCannotBeInventedFromCurrentFocus(){
        var pending=ChildEducationFocusEffects.pendingData(BEFORE,selection(Key.EDUCATION_DIPLOMACY),"original-focus",Optional.empty()).orElseThrow();
        var missing=decodeReceipt(receipt(pending,frame(10),ReceiptStatus.UNAVAILABLE,false,false,false),frame(10),pending);
        assertFalse(missing.observedApplied());assertTrue(missing.post().isEmpty());
        var falseSubmission=(ObjectNode)StrictJson.parse(receipt(pending,frame(10),ReceiptStatus.OBSERVED_APPLIED,true,true,true).bytes());
        ((ObjectNode)falseSubmission.get("submission")).put("accepted",false).put("status","submit_unknown");
        assertThrows(IllegalArgumentException.class,()->decodeReceipt(raw(falseSubmission),frame(10),pending));
    }
    @Test void wrongOriginalActionChildKeyAndScalarWireTypesAreRefused(){
        var selected=selection(Key.EDUCATION_INTRIGUE);var source=submitted(selected,SubmitStatus.SUBMITTED_VERIFICATION_PENDING,true);
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusEffects.pendingData(BEFORE,selected,"different-action",Optional.of(source)));
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusEffects.pendingData(BEFORE,selection(Key.EDUCATION_MARTIAL),"original-focus",Optional.of(source)));
        var pending=ChildEducationFocusEffects.pendingData(BEFORE,selected,"original-focus",Optional.empty()).orElseThrow();
        for(var changed:List.of(((ObjectNode)StrictJson.parse(pending.original().bytes())).put("child_full_id",true),
                ((ObjectNode)StrictJson.parse(pending.original().bytes())).put("child_full_id",1.0),
                ((ObjectNode)StrictJson.parse(pending.original().bytes())).put("accepted",1),
                ((ObjectNode)StrictJson.parse(pending.original().bytes())).put("driver_history",true)))
            assertThrows(IllegalArgumentException.class,()->decodePending(raw(changed)));
        var missing=(ObjectNode)StrictJson.parse(pending.original().bytes());missing.remove("native_command_submitted");
        assertThrows(IllegalArgumentException.class,()->decodePending(raw(missing)));
    }
}

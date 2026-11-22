package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisionsSource;
import org.xar.ck3.control.nativebridge.CurrentDecisionsClose;
import org.xar.ck3.control.nativebridge.CurrentDecisionsCloseResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundaries only; no original private Transport receipt, Native producer or live credit. */
final class NativeOwnerCurrentDecisionsCloseSelectionTest {
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v32").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/decisions-close-selection-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static CoreFrame.Prefix core(int raw){return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentCuratedDecisionsSource source(boolean visible,boolean enabled,boolean detailVisible,boolean complete,boolean modal,int rows){
        return new CurrentCuratedDecisionsSource(true,visible,enabled,true,detailVisible,true,false,false,complete,modal,false,
                complete?Optional.of(2):Optional.empty(),complete?Optional.of(rows):Optional.empty(),Optional.of(0),Optional.empty(),Optional.empty(),List.of());
    }
    private static CurrentCuratedDecisionsSource ready(int rows){return source(true,true,false,true,false,rows);}
    private static CurrentDecisionsCloseResult frame(CurrentDecisionsClose.Action action,boolean handled,boolean admitted,int provider,int query,int raw,int connection,CurrentCuratedDecisionsSource source){
        boolean effect=action==CurrentDecisionsClose.Action.CLOSE_LIST;
        return new CurrentDecisionsCloseResult(action,effect?CurrentDecisionsCloseResult.Status.CLOSE_DISPATCHED:CurrentDecisionsCloseResult.Status.AVAILABLE,
                effect,effect,handled,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(raw)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(source),admitted,Optional.empty());
    }
    private static CurrentDecisionsCloseResult query(CurrentCuratedDecisionsSource source,boolean admitted){return frame(CurrentDecisionsClose.Action.QUERY_CLOSE,false,admitted,1,2,1000,1,source);}
    @Test void twoIndependentModesContainOnlyTheSixCommonFields()throws IOException {
        assertEquals(CurrentDecisionsClose.Action.QUERY_CLOSE,NativeOwnerSnapshotMain268.currentDecisionsCloseAction(config("current_decisions_close_query")));
        assertEquals(CurrentDecisionsClose.Action.CLOSE_LIST,NativeOwnerSnapshotMain268.currentDecisionsCloseAction(config("current_decisions_close")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DECISIONS_CLOSE_QUERY,NativeOwnerSnapshotMain268.observationMode(config("current_decisions_close_query")));
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DECISIONS_CLOSE,NativeOwnerSnapshotMain268.observationMode(config("current_decisions_close")));
    }
    @Test void exactCommonFieldsAndDescriptorPinRejectMissingMistypedAndOutOfRangeData()throws IOException {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=config("current_decisions_close");n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        var boolBytes=config("current_decisions_close");((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        for(var n:List.of(boolBytes,config("current_decisions_close").put("owner_descriptor","D:/owner.json"),config("current_decisions_close").put("overall_timeout_seconds",0),
                config("current_decisions_close").put("read_timeout_seconds",61),config("current_decisions_close").put("maximum_frames_per_operation",65537)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
    }
    @Test void selectorPermissionCoreLeaseAndAutomaticCloseAllAreRejected()throws IOException {
        for(String field:List.of("product","control","decision_key","instance_id","index","root","scope","action","native_handled","close_admissible","expected_core","provider_generation","query_sequence","claim_sequence","deadline","target_threshold"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_decisions_close").put(field,1)),field);
        for(String mode:List.of("current_decisions_close_all","current_decisions_close_detail","current_decisions_query_then_close","CLOSE_LIST"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)));
    }
    @Test void oldSchemasAndOldIndependentModesDoNotBorrowTheCloseMode()throws IOException {
        var modes=List.of("current_letter_query","current_djc_selected_cost","current_letter_set_query","current_fullscreen_event_query","current_curated_decisions_query","current_xqol_conversion_prompt_query","current_xqol_conversion_threshold_query","current_courtier_creator_controls_query");
        for(int i=0;i<modes.size();i++) {
            String schema="xar.native-owner-snapshot-config/v"+(24+i);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_decisions_close").put("schema",schema)));
            var n=config(modes.get(i)).put("schema",schema);
            if(i==1)n.put("target_character_id",42).put("cb_key","duchy_de_jure_greatwar");
            if(i==6)n.put("target_threshold",50);
            if(i==7)n.put("product","main").put("control","confirm");
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(n));
        }
    }
    @Test void incompleteAndAbsentListQueriesKeepUnknownCountsAndNeverGrantClose()throws IOException {
        var absent=new CurrentCuratedDecisionsSource(false,false,false,false,false,false,false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        for(var s:List.of(absent,source(true,true,false,false,false,0))) {
            var q=query(s,false);assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseQueryFrame(q,core(1000)));
            assertTrue(q.source().orElseThrow().totalModelRows().isEmpty());
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseSource(q));
        }
    }
    @Test void eligibleFactsNeverImplyPrivateAdmissionAndAdmissionRejectsContradictions()throws IOException {
        var s=ready(0);assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseSource(query(s,false)));
        assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseSource(query(s,true)));
        for(var bad:List.of(source(false,true,false,true,false,0),source(true,false,false,true,false,0),source(true,true,true,true,false,0),source(true,true,false,true,true,0),source(true,true,false,false,false,0)))
            assertThrows(IllegalArgumentException.class,()->query(bad,true));
    }
    @Test void bothNativeBoolReturnsAreValidDispatchedAndArePreserved()throws IOException {
        var s=ready(37);var q=query(s,true);
        for(boolean handled:List.of(false,true)) {
            var done=frame(CurrentDecisionsClose.Action.CLOSE_LIST,handled,true,1,2,1000,1,s);
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseDispatchFrame(q,done));
            assertEquals(handled,StrictJson.parse(done.encode().bytes(),1<<20).get("native_handled").booleanValue());
            assertTrue(done.successful());
        }
    }
    @Test void originalCompleteSourceIsComparedWithoutAnyFixedRowCountRequirement()throws IOException {
        for(int count:List.of(0,1,37,64,100)) {
            var s=ready(count);var q=query(s,true);var done=frame(CurrentDecisionsClose.Action.CLOSE_LIST,false,true,1,2,1000,1,s);
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseDispatchFrame(q,done));
        }
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseDispatchFrame(query(ready(37),true),frame(CurrentDecisionsClose.Action.CLOSE_LIST,false,true,1,2,1000,1,ready(38))));
    }
    @Test void readonlyUnavailableCoreLeaseOrConnectionDriftCannotStandInForClose()throws IOException {
        var s=ready(37);var q=query(s,true);var a=CurrentDecisionsClose.Action.CLOSE_LIST;
        for(var bad:List.of(q,frame(a,false,true,2,2,1000,1,s),frame(a,false,true,1,3,1000,1,s),frame(a,false,true,1,2,1024,1,s),frame(a,false,true,1,2,1000,2,s)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseDispatchFrame(q,bad));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseQueryFrame(q,core(1024)));
        var missing=new CurrentDecisionsCloseResult(CurrentDecisionsClose.Action.QUERY_CLOSE,CurrentDecisionsCloseResult.Status.UNAVAILABLE,false,false,false,true,BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),false,Optional.of("DATA unavailable"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentDecisionsCloseQueryFrame(missing,core(1000)));
    }
    @Test void dispatchedDoesNotConfirmPanelsClosedNewDateOrPhysicalSave()throws IOException {
        for(boolean handled:List.of(false,true)) {
            var done=frame(CurrentDecisionsClose.Action.CLOSE_LIST,handled,true,1,2,1000,1,ready(37));var n=StrictJson.parse(done.encode().bytes(),1<<20);
            assertTrue(n.get("effect_attempted").booleanValue());assertTrue(n.get("native_returned").booleanValue());
            for(String key:List.of("panels_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
        }
    }
}

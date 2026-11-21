package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisions;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisionsSource;
import org.xar.ck3.control.nativebridge.CurrentCuratedDecisionsResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA selection/source tests only; no private Transport authority or live qualification. */
final class NativeOwnerCurrentCuratedDecisionSelectionTest {
    private static final CurrentCuratedDecisions.DecisionKey KEY=CurrentCuratedDecisions.DecisionKey.ENABLE_AUTO_APPOINTMENT;
    private static final CurrentCuratedDecisions.DecisionKey OTHER=CurrentCuratedDecisions.DecisionKey.DISABLE_AUTO_APPOINTMENT;
    private static ObjectNode config(String mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v28").put("mode",mode)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/curated-selection-data/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static NativeOwnerSnapshotMain268.CuratedDecisionConfig intent(CurrentCuratedDecisions.Action action,Optional<CurrentCuratedDecisions.DecisionKey> key) {
        return new NativeOwnerSnapshotMain268.CuratedDecisionConfig(action,key);
    }
    private static CoreFrame.Prefix core(int raw) {return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentCuratedDecisionsSource absent(boolean canOpen) {
        return new CurrentCuratedDecisionsSource(false,false,false,false,false,false,false,canOpen,false,false,false,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),List.of());
    }
    private static CurrentCuratedDecisionsSource list(boolean second) {
        var rows=second?List.of(new CurrentCuratedDecisionsSource.Row(KEY,true,false),new CurrentCuratedDecisionsSource.Row(OTHER,true,false))
                :List.of(new CurrentCuratedDecisionsSource.Row(KEY,true,false));
        return new CurrentCuratedDecisionsSource(true,true,true,false,false,false,false,false,true,false,false,
                Optional.of(1),Optional.of(rows.size()),Optional.empty(),Optional.empty(),Optional.empty(),rows);
    }
    private static CurrentCuratedDecisionsSource selected(CurrentCuratedDecisions.DecisionKey key,boolean can) {
        return new CurrentCuratedDecisionsSource(true,true,true,true,true,true,false,false,true,false,can,
                Optional.of(1),Optional.of(1),Optional.of(1),Optional.of(key),Optional.of(can),List.of(new CurrentCuratedDecisionsSource.Row(key,false,true)));
    }
    private static CurrentCuratedDecisionsResult frame(CurrentCuratedDecisions.Action action,int provider,int query,int raw,
            CurrentCuratedDecisionsSource source,Optional<CurrentCuratedDecisions.DecisionKey> key,boolean handled) {
        boolean effect=action!=CurrentCuratedDecisions.Action.QUERY;
        return new CurrentCuratedDecisionsResult(action,effect?CurrentCuratedDecisionsResult.dispatchedStatus(action):CurrentCuratedDecisionsResult.Status.AVAILABLE,
                effect,effect,handled,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(raw)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(source),Optional.empty(),key);
    }
    private static CurrentCuratedDecisionsResult query(CurrentCuratedDecisionsSource source) {return frame(CurrentCuratedDecisions.Action.QUERY,1,2,1000,source,Optional.empty(),false);}
    @Test void fourExplicitModesSelectExactlyOneFixedAction() {
        var modes=List.of("current_curated_decisions_query","current_curated_decisions_open","current_curated_decision_detail","current_curated_decision_confirm");
        var actions=List.of(CurrentCuratedDecisions.Action.QUERY,CurrentCuratedDecisions.Action.OPEN_LIST,CurrentCuratedDecisions.Action.OPEN_DETAIL,CurrentCuratedDecisions.Action.CONFIRM);
        var expected=List.of(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CURATED_DECISIONS_QUERY,NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CURATED_DECISIONS_OPEN,
                NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CURATED_DECISION_DETAIL,NativeOwnerSnapshotMain268.ObservationMode.CURRENT_CURATED_DECISION_CONFIRM);
        for(int i=0;i<modes.size();i++) {
            var n=config(modes.get(i));if(i>=2)n.put("decision_key",KEY.wire());
            assertEquals(actions.get(i),NativeOwnerSnapshotMain268.currentCuratedDecisionConfig(n).action());assertEquals(expected.get(i),NativeOwnerSnapshotMain268.observationMode(n));
        }
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_curated_decision_confirm ").put("decision_key",KEY.wire())));
    }
    @Test void onlyDetailAndConfirmRequireOneOfExactNineParsedKeys() {
        assertEquals(9,CurrentCuratedDecisions.DecisionKey.values().length);
        for(String mode:List.of("current_curated_decision_detail","current_curated_decision_confirm")) {
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode)));
            for(var key:CurrentCuratedDecisions.DecisionKey.values())assertEquals(Optional.of(key),NativeOwnerSnapshotMain268.currentCuratedDecisionConfig(config(mode).put("decision_key",key.wire())).decisionKey());
            for(var invalid:List.of(config(mode).put("decision_key",true),config(mode).put("decision_key",0),config(mode).put("decision_key",KEY.wire()+" "),config(mode).put("decision_key","unreviewed_decision")))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(invalid));
        }
        for(String mode:List.of("current_curated_decisions_query","current_curated_decisions_open"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(mode).put("decision_key",KEY.wire())));
    }
    @Test void commonFieldsAreRequiredAndCallerAuthorityOrAutomaticSequenceIsRejected() {
        for(String field:List.of("mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=config("current_curated_decisions_query");n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        for(String field:List.of("action","index","ordinal","row","native_token","expected_core","provider_generation","query_sequence","claim_sequence","native_can_confirm","decision_applied","deadline","auto_confirm","control_step")) {
            var n=config("current_curated_decision_confirm").put("decision_key",KEY.wire()).put(field,1);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n),field);
        }
    }
    @Test void oldV24ThroughV27RemainSelectedAndCannotBorrowNewKeyOrMode() {
        for(String schema:List.of("xar.native-owner-snapshot-config/v24","xar.native-owner-snapshot-config/v25","xar.native-owner-snapshot-config/v26","xar.native-owner-snapshot-config/v27"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_curated_decisions_query").put("schema",schema)));
        var old=config("current_letter_query").put("schema","xar.native-owner-snapshot-config/v24");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LETTER_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.put("decision_key",KEY.wire())));
        var full=config("current_fullscreen_event_query").put("schema","xar.native-owner-snapshot-config/v27");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_FULLSCREEN_EVENT_QUERY,NativeOwnerSnapshotMain268.observationMode(full));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(full.put("decision_key",KEY.wire())));
    }
    @Test void readonlyUnmaterializedSourceIsPreservedWithoutEffectAuthority() {
        var q=query(absent(false));assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionQueryFrame(q,core(1000)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionQueryFrame(q,core(1024)));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(q,intent(CurrentCuratedDecisions.Action.OPEN_LIST,Optional.empty())));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(q,intent(CurrentCuratedDecisions.Action.QUERY,Optional.empty())));
    }
    @Test void nativeOpenListHandledFalseIsStillKnownDispatchAndNotRetried() {
        var q=query(absent(true));var action=intent(CurrentCuratedDecisions.Action.OPEN_LIST,Optional.empty());
        for(boolean handled:List.of(false,true))assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionDispatchFrame(q,frame(CurrentCuratedDecisions.Action.OPEN_LIST,1,2,1000,absent(true),Optional.empty(),handled),action));
    }
    @Test void detailRequiresActualKeyedRowAndNeverOpensListImplicitly() {
        var action=intent(CurrentCuratedDecisions.Action.OPEN_DETAIL,Optional.of(KEY));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(query(list(true)),action));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(query(absent(true)),action));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(query(list(false)),intent(CurrentCuratedDecisions.Action.OPEN_DETAIL,Optional.of(OTHER))));
    }
    @Test void confirmRequiresActualSelectedSameKeyAndNativeCanTrue() {
        var action=intent(CurrentCuratedDecisions.Action.CONFIRM,Optional.of(KEY));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(query(selected(KEY,true)),action));
        for(var s:List.of(selected(KEY,false),selected(OTHER,true),list(true),absent(true)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionSource(query(s),action));
    }
    @Test void callbackNeedsOriginalProviderQueryCoreWholeSourceAndConfiguredFixedKey() {
        var q=query(list(true));var action=intent(CurrentCuratedDecisions.Action.OPEN_DETAIL,Optional.of(KEY));
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionDispatchFrame(q,frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,1,2,1000,list(true),Optional.of(KEY),false),action));
        for(var bad:List.of(frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,2,2,1000,list(true),Optional.of(KEY),false),frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,1,3,1000,list(true),Optional.of(KEY),false),
                frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,1,2,1024,list(true),Optional.of(KEY),false),frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,1,2,1000,list(false),Optional.of(KEY),false),
                frame(CurrentCuratedDecisions.Action.OPEN_DETAIL,1,2,1000,list(true),Optional.of(OTHER),false),q))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCuratedDecisionDispatchFrame(q,bad,action));
    }
    @Test void dispatchEncodingDoesNotGrantAppliedDecisionDateOrSave()throws IOException {
        var n=StrictJson.parse(frame(CurrentCuratedDecisions.Action.OPEN_LIST,1,2,1000,absent(true),Optional.empty(),false).encode().bytes(),1<<20);
        assertTrue(n.get("native_returned").booleanValue());assertFalse(n.get("native_handled").booleanValue());
        for(String field:List.of("decision_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(field).booleanValue(),field);
    }
}

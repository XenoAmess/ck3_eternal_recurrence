package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentLyd;
import org.xar.ck3.control.nativebridge.CurrentLydResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA/configuration boundaries only. No Native positive frame or private Transport authority is fabricated. */
final class NativeOwnerCurrentLydSelectionTest {
    private static ObjectNode config(NativeOwnerSnapshotMain268.LydMode mode) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v37").put("mode",mode.wire())
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/lyd-Main-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));
        if(mode.decision())n.put("decision_key",CurrentLyd.DecisionKey.ENTRY.wire());
        if(mode.personal())n.put("personal_key",CurrentLyd.PersonalKey.REVERENT_HEAVEN.wire());
        if(mode.event())n.put("event_role",CurrentLyd.EventRole.WELCOME_CONTINUE.wire());return n;
    }
    private static ObjectNode query(){return config(NativeOwnerSnapshotMain268.LydMode.QUERY_DECISIONS);}
    private static CoreFrame.Prefix prefix(){return new CoreFrame.Prefix(1000,1,true,0,true,true,42,true);}
    @Test void allElevenModesSelectOnlyTheirFixedQueryActionAndFiniteSubmissionCount()throws IOException {
        assertEquals(11,NativeOwnerSnapshotMain268.LydMode.values().length);
        for(var m:NativeOwnerSnapshotMain268.LydMode.values()) {
            var c=NativeOwnerSnapshotMain268.currentLydConfig(config(m));assertEquals(m,c.mode());
            assertTrue(m.queryAction().isQuery());assertEquals(m.action().kind(),m.queryAction().kind());
            assertEquals(m==NativeOwnerSnapshotMain268.LydMode.ADD_PERSONAL?6:m.action().isQuery()?2:3,m.submissions());
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_LYD,NativeOwnerSnapshotMain268.observationMode(config(m)));
        }
        for(String bad:List.of("current_lyd_query_add_confirmation","current_lyd_select_personal_candidate","current_lyd_confirm_personal_add","current_lyd_query_then_confirm","CURRENT_LYD_QUERY_EVENTS","current_lyd_query_events "))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("mode",bad)));
    }
    @Test void exactDecisionKeysAllowBeginDetailButNeverBeginConfirmation()throws IOException {
        for(var key:CurrentLyd.DecisionKey.values()) {
            var detail=config(NativeOwnerSnapshotMain268.LydMode.OPEN_DETAIL).put("decision_key",key.wire());
            assertEquals(key,NativeOwnerSnapshotMain268.currentLydConfig(detail).decisionKey().orElseThrow());
            var confirm=config(NativeOwnerSnapshotMain268.LydMode.CONFIRM_DECISION).put("decision_key",key.wire());
            if(key==CurrentLyd.DecisionKey.BEGIN_READONLY)assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(confirm));
            else assertEquals(key,NativeOwnerSnapshotMain268.currentLydConfig(confirm).decisionKey().orElseThrow());
        }
        for(String bad:List.of("lyd_i3b_begin_decision ","unknown_decision","LYD_ENTER_DECISION"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLydConfig(config(NativeOwnerSnapshotMain268.LydMode.OPEN_DETAIL).put("decision_key",bad)));
    }
    @Test void everyPersonalModeIncludingReadonlyQueryRequiresItsOwnExactPersonalKey()throws IOException {
        for(var m:NativeOwnerSnapshotMain268.LydMode.values())if(m.personal()) {
            for(var key:CurrentLyd.PersonalKey.values()) {
                var c=NativeOwnerSnapshotMain268.currentLydConfig(config(m).put("personal_key",key.wire()));
                assertEquals(CurrentLyd.Target.personal(key),c.queryTarget());assertEquals(key,c.personalKey().orElseThrow());
            }
            var missing=config(m);missing.remove("personal_key");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
            for(var n:List.of(config(m).putNull("personal_key"),config(m).put("personal_key",1),config(m).put("personal_key",true),config(m).put("personal_key","lyd_tenet_reverent_heaven ")))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
    }
    @Test void eventOptionUsesSemanticRoleDataWithoutAcceptingInstanceIndexOrArbitraryKey()throws IOException {
        for(var role:CurrentLyd.EventRole.values()) {
            var c=NativeOwnerSnapshotMain268.currentLydConfig(config(NativeOwnerSnapshotMain268.LydMode.CHOOSE_KNOWN_EVENT_OPTION).put("event_role",role.wire()));
            assertEquals(role,c.eventRole().orElseThrow());assertEquals(CurrentLyd.Target.none(),c.queryTarget());
        }
        for(String bad:List.of("lyd.1002","lyd_play_cancel","first","0","welcome_continue "))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.currentLydConfig(config(NativeOwnerSnapshotMain268.LydMode.CHOOSE_KNOWN_EVENT_OPTION).put("event_role",bad)));
        for(String extra:List.of("instance_id","option_index","option_key","event_id","definition_key"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(NativeOwnerSnapshotMain268.LydMode.CHOOSE_KNOWN_EVENT_OPTION).put(extra,1)));
    }
    @Test void modeSpecificSelectorsCannotLeakBetweenQueriesOrFixedActions()throws IOException {
        for(var m:NativeOwnerSnapshotMain268.LydMode.values()) {
            for(String key:List.of("decision_key","personal_key","event_role")) {
                boolean required=key.equals("decision_key")?m.decision():key.equals("personal_key")?m.personal():m.event();
                if(!required)assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(m).putNull(key)));
                else {var n=config(m);n.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));}
            }
        }
    }
    @Test void exactOwnerFilePinAndCommonIntegerBoundsRemainMandatory()throws IOException {
        var boolBytes=query();((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        for(var bad:List.of(boolBytes,query().put("owner_descriptor","D:/owner.json"),query().put("overall_timeout_seconds",601),query().put("overall_timeout_seconds",0),query().put("read_timeout_seconds",61),query().put("read_timeout_seconds",0),query().put("maximum_frames_per_operation",0)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(bad));
        for(String key:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var bad=query();bad.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(bad));
        }
    }
    @Test void callerCannotSupplyAnyCoreLeasePermissionOrOpaqueCandidateAuthority()throws IOException {
        for(String key:List.of("action","choice_token","token","ordinal","index","scope","expected_core","connection_generation","provider_generation","query_sequence","claim_sequence","deadline","can_accept","select_admissible","native_can_pick","is_adding","source","gold","piety","retry","restore_progress","maximum_status_polls","checkpoint_archive_path"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config(NativeOwnerSnapshotMain268.LydMode.ADD_PERSONAL).put(key,1)),key);
    }
    @Test void oldModesCannotBorrowPersonalOrEventFieldsAndV35KeepsItsOwnQuery()throws IOException {
        for(int v=24;v<=36;v++){final int schemaVersion=v;for(String extra:List.of("personal_key","event_role"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("schema","xar.native-owner-snapshot-config/v"+schemaVersion).put(extra,"x")));}
        var old=query().put("schema","xar.native-owner-snapshot-config/v35").put("mode","current_superman_health_query").put("phase","completed");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_SUPERMAN_HEALTH_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(old.deepCopy().put("personal_key",CurrentLyd.PersonalKey.REVERENT_HEAVEN.wire())));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(query().put("schema","xar.native-owner-snapshot-config/v36")));
    }
    @Test void knownRefusalAndUnknownDataNeverQualifyAsAvailableOrDispatched()throws IOException {
        // Typed Java DATA, not a manufactured Native frame: each command has its own actual ticket/pump witness.
        var queryOwner=new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4);
        var actionOwner=new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.valueOf(5),BigInteger.valueOf(6),4);
        assertNotEquals(queryOwner,actionOwner);
        NativeOwnerSnapshotMain268.requireCurrentLydOwnerConnection(queryOwner,actionOwner);
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLydOwnerConnection(queryOwner,
                new CurrentLetterResult.OwnerWitness(BigInteger.TWO,BigInteger.valueOf(5),BigInteger.valueOf(6),4)));
        for(var status:List.of(CurrentLydResult.Status.UNAVAILABLE,CurrentLydResult.Status.EXPIRED,CurrentLydResult.Status.INDETERMINATE)) {
            var refusal=new CurrentLydResult(CurrentLyd.Action.QUERY_DECISIONS,status,false,false,false,status!=CurrentLydResult.Status.INDETERMINATE,
                    BigInteger.ZERO,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("Java DATA refusal"));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLydQueryFrame(refusal,prefix(),CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Target.none()));
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLydDispatchFrame(refusal,refusal,CurrentLyd.Action.OPEN_LIST,CurrentLyd.Target.none()));
        }
        var witnessed=new CurrentLydResult(CurrentLyd.Action.QUERY_DECISIONS,CurrentLydResult.Status.UNAVAILABLE,false,false,false,true,BigInteger.ONE,BigInteger.ONE,BigInteger.ZERO,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(prefix()),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.empty(),Optional.of("Java DATA no Source"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentLydQueryFrame(witnessed,prefix(),CurrentLyd.Action.QUERY_DECISIONS,CurrentLyd.Target.none()));
    }
    @Test void everySummaryStartsWithoutBusinessPaymentDateOrSaveCredit()throws IOException {
        for(var m:NativeOwnerSnapshotMain268.LydMode.values()) {
            var out=StrictJson.object();NativeOwnerSnapshotMain268.initializeCurrentLydResult(out,NativeOwnerSnapshotMain268.currentLydConfig(config(m)),"Java-DATA-machine");
            for(String flag:List.of("callback_dispatched","native_returned","native_handled","event_closed","personal_applied","gold_paid","piety_paid","modifiers_applied","new_date_observed","physical_save_confirmed"))assertFalse(out.get(flag).booleanValue(),flag);
            assertEquals(0,out.get("save_calls").intValue());assertEquals(0,out.get("action_calls").intValue());assertEquals(m.action().wire(),out.get("action").textValue());
        }
        assertEquals(CurrentLydResult.Status.NAVIGATION_DISPATCHED,CurrentLydResult.dispatchedStatus(CurrentLyd.Action.OPEN_LIST));
        assertEquals(CurrentLydResult.Status.NAVIGATION_DISPATCHED,CurrentLydResult.dispatchedStatus(CurrentLyd.Action.OPEN_PERSONAL));
        assertEquals(CurrentLydResult.Status.CONFIRMATION_DISPATCHED,CurrentLydResult.dispatchedStatus(CurrentLyd.Action.CONFIRM_PERSONAL_ADD));
    }
}

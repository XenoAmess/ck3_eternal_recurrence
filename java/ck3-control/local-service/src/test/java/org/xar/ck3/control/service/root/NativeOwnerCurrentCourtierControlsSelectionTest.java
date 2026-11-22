package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentCourtierControls;
import org.xar.ck3.control.nativebridge.CurrentCourtierControlsSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierControlsResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundaries only; no original private Transport receipt, Native producer or live credit. */
final class NativeOwnerCurrentCourtierControlsSelectionTest {
    private static ObjectNode config(String mode,String product,String control) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v31").put("mode",mode).put("product",product).put("control",control)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/courtier-selection-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static ObjectNode execute(){return config("current_courtier_creator_control_execute","main","confirm");}
    private static CoreFrame.Prefix core(int raw){return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentCourtierControlsSource ready(CurrentCourtierControls.Product product,CurrentCourtierControls.Control control){
        return new CurrentCourtierControlsSource(product,control,true,true,true,true,true,true,Optional.of(true),Optional.of(true),Optional.of(true),true);
    }
    private static CurrentCourtierControlsSource ready(){return ready(CurrentCourtierControls.Product.MAIN,CurrentCourtierControls.Control.CONFIRM);}
    private static CurrentCourtierControlsResult frame(CurrentCourtierControls.Action action,int provider,int query,int raw,int connection,CurrentCourtierControlsSource source){
        boolean effect=action==CurrentCourtierControls.Action.EXECUTE_CONTROL;
        return new CurrentCourtierControlsResult(action,effect?CurrentCourtierControlsResult.Status.CONTROL_DISPATCHED:CurrentCourtierControlsResult.Status.AVAILABLE,
                effect,effect,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(raw)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(source),Optional.empty(),source.product(),source.control());
    }
    private static CurrentCourtierControlsResult query(CurrentCourtierControlsSource source){return frame(CurrentCourtierControls.Action.QUERY_CONTROL,1,2,1000,1,source);}
    private static NativeOwnerSnapshotMain268.CourtierControlsConfig intent(CurrentCourtierControlsSource source){
        return NativeOwnerSnapshotMain268.currentCourtierControlsConfig(config("current_courtier_creator_control_execute",source.product().wire(),source.control().wire()));
    }
    @Test void bothModesRequireOneFixedProductAndControlWithoutAutomaticSequence() {
        for(var product:CurrentCourtierControls.Product.values())for(var control:CurrentCourtierControls.Control.values()) {
            var q=config("current_courtier_creator_controls_query",product.wire(),control.wire());var e=config("current_courtier_creator_control_execute",product.wire(),control.wire());
            assertEquals(CurrentCourtierControls.Action.QUERY_CONTROL,NativeOwnerSnapshotMain268.currentCourtierControlsConfig(q).action());
            assertEquals(CurrentCourtierControls.Action.EXECUTE_CONTROL,NativeOwnerSnapshotMain268.currentCourtierControlsConfig(e).action());
            assertEquals(product,NativeOwnerSnapshotMain268.currentCourtierControlsConfig(q).product());
            assertEquals(control,NativeOwnerSnapshotMain268.currentCourtierControlsConfig(e).control());
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CREATOR_CONTROLS_QUERY,NativeOwnerSnapshotMain268.observationMode(q));
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CREATOR_CONTROL_EXECUTE,NativeOwnerSnapshotMain268.observationMode(e));
        }
    }
    @Test void missingMistypedOrNonliteralProductControlAndCombinedModeAreRejected() {
        for(String mode:List.of("current_courtier_creator_controls_query","current_courtier_creator_control_execute")) {
            for(String key:List.of("product","control")) {
                var missing=config(mode,"main","confirm");missing.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
                for(var n:List.of(config(mode,"main","confirm").put(key,true),config(mode,"main","confirm").put(key,1),config(mode,"main","confirm").putNull(key)))
                    assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
            }
        }
        for(String product:List.of("MAIN","Vivhite"," main","other"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_creator_controls_query",product,"confirm")));
        for(String control:List.of("CONFIRM","age_plus_ten","age_plus_one ","create"))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_creator_control_execute","main",control)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_creator_query_then_confirm","main","confirm")));
    }
    @Test void exactCommonFieldsAndDescriptorFilePinRejectMissingBooleanAndOutOfRangeValues() {
        for(String key:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=execute();n.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        var boolBytes=execute();((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(boolBytes));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(execute().put("owner_descriptor","D:/owner.json")));
        for(var n:List.of(execute().put("overall_timeout_seconds",601),execute().put("read_timeout_seconds",61),execute().put("maximum_frames_per_operation",0)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
    }
    @Test void callerAgeKeysNamesScopesOrdinalsCorePermissionsAndLeasesCannotAuthorizeExecute() {
        for(String field:List.of("age","name","description","scripted_gui_key","scope","ordinal","index","instance_id","expected_core","provider_generation","query_sequence","claim_sequence","native_valid","execute_admissible","action","deadline","auto_confirm"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(execute().put(field,1)),field);
    }
    @Test void oldSchemasCannotBorrowProductControlAndOldIndependentModesRemainAvailable() {
        var old=List.of("current_letter_query","current_djc_selected_cost","current_letter_set_query","current_fullscreen_event_query","current_curated_decisions_query","current_xqol_conversion_prompt_query","current_xqol_conversion_threshold_query");
        for(int i=0;i<old.size();i++) {
            String schema="xar.native-owner-snapshot-config/v"+(24+i);
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(execute().put("schema",schema)));
            var n=config(old.get(i),"main","confirm").put("schema",schema);n.remove("product");n.remove("control");
            if(i==1)n.put("target_character_id",42).put("cb_key","duchy_de_jure_greatwar");
            if(i==6)n.put("target_threshold",50);
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.observationMode(n));
            var borrowed=n.deepCopy().put("product","main");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(borrowed));
        }
    }
    @Test void observedAbsentCreatorIsValidReadonlyDataButNeverExecuteAuthority() {
        var absent=new CurrentCourtierControlsSource(CurrentCourtierControls.Product.MAIN,CurrentCourtierControls.Control.CANCEL,true,false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),false);
        var q=query(absent);assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsQueryFrame(q,core(1000),absent.product(),absent.control()));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsSource(q,intent(absent)));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierControlsSource(absent.product(),absent.control(),false,false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),false));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierControlsSource(absent.product(),absent.control(),true,false,false,false,false,false,Optional.of(false),Optional.empty(),Optional.empty(),false));
    }
    @Test void hiddenDisabledMissingDefinitionShownOrValidCannotAuthorizeFixedCallback() {
        var p=CurrentCourtierControls.Product.MAIN;var c=CurrentCourtierControls.Control.CONFIRM;
        for(var s:List.of(new CurrentCourtierControlsSource(p,c,true,true,true,true,false,true,Optional.of(true),Optional.of(true),Optional.of(true),false),
                new CurrentCourtierControlsSource(p,c,true,true,true,true,true,false,Optional.of(true),Optional.of(true),Optional.of(true),false),
                new CurrentCourtierControlsSource(p,c,true,true,true,true,true,true,Optional.of(false),Optional.empty(),Optional.empty(),false),
                new CurrentCourtierControlsSource(p,c,true,true,true,true,true,true,Optional.of(true),Optional.of(false),Optional.of(true),false),
                new CurrentCourtierControlsSource(p,c,true,true,true,true,true,true,Optional.of(true),Optional.of(true),Optional.of(false),false)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsSource(query(s),intent(s)));
    }
    @Test void eachFixedProductControlRetainsFullActualSourceThroughOneVoidDispatch()throws IOException {
        for(var product:CurrentCourtierControls.Product.values())for(var control:CurrentCourtierControls.Control.values()) {
            var s=ready(product,control);var q=query(s);var expected=intent(s);
            assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentCourtierControlsSource(q,expected));
            assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsDispatchFrame(q,frame(CurrentCourtierControls.Action.EXECUTE_CONTROL,1,2,1000,1,s),expected));
        }
    }
    @Test void callbackRejectsReadonlyCoreLeaseConnectionProductOrControlDrift() {
        var q=query(ready());var a=CurrentCourtierControls.Action.EXECUTE_CONTROL;var expected=intent(ready());
        for(var bad:List.of(q,frame(a,2,2,1000,1,ready()),frame(a,1,3,1000,1,ready()),frame(a,1,2,1024,1,ready()),frame(a,1,2,1000,2,ready()),
                frame(a,1,2,1000,1,ready(CurrentCourtierControls.Product.VIVHITE,CurrentCourtierControls.Control.CONFIRM)),
                frame(a,1,2,1000,1,ready(CurrentCourtierControls.Product.MAIN,CurrentCourtierControls.Control.CANCEL))))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsDispatchFrame(q,bad,expected));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsQueryFrame(q,core(1024),expected.product(),expected.control()));
        var queryIntent=NativeOwnerSnapshotMain268.currentCourtierControlsConfig(config("current_courtier_creator_controls_query","main","confirm"));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierControlsSource(q,queryIntent));
    }
    @Test void voidCallbackEncodingDoesNotConfirmCloseCreationAgeDateOrSave()throws IOException {
        var f=frame(CurrentCourtierControls.Action.EXECUTE_CONTROL,1,2,1000,1,ready());var n=StrictJson.parse(f.encode().bytes(),1<<20);
        assertTrue(n.get("effect_attempted").booleanValue());assertTrue(n.get("native_returned").booleanValue());
        for(String field:List.of("native_handled","creator_closed","courtier_created","age_changed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(field).booleanValue(),field);
    }
}

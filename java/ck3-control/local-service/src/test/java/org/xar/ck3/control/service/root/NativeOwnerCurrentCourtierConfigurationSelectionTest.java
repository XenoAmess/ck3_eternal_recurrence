package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.CurrentCourtierControls;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfiguration;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfigurationSource;
import org.xar.ck3.control.nativebridge.CurrentCourtierConfigurationResult;
import org.xar.ck3.control.nativebridge.CurrentLetterResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundaries only; no original private Transport receipt, Native producer or live credit. */
final class NativeOwnerCurrentCourtierConfigurationSelectionTest {
    private static ObjectNode config(String mode,String product,String setting) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v33").put("mode",mode).put("product",product).put("setting",setting)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/courtier-configuration-selection-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static ObjectNode execute(){return config("current_courtier_configuration_execute","main","choose_female");}
    private static CoreFrame.Prefix core(int raw){return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentCourtierConfigurationSource.Configuration raw(List<Optional<Long>> values) {
        return new CurrentCourtierConfigurationSource.Configuration(values.get(0),values.get(1),values.get(2),values.get(3),values.get(4),values.get(5),values.get(6),values.get(7),values.get(8),values.get(9));
    }
    private static List<Optional<Long>> values(){return List.of(Optional.of(31L),Optional.of(0L),Optional.of(7L),Optional.of(8L),Optional.of(9L),Optional.of(10L),Optional.of(11L),Optional.of(12L),Optional.of(0L),Optional.of(777L));}
    private static CurrentCourtierConfigurationSource source(CurrentCourtierControls.Product product,CurrentCourtierConfiguration.Setting setting,
            CurrentCourtierConfigurationSource.Configuration data,boolean definition,boolean shown,boolean valid,boolean admitted) {
        return new CurrentCourtierConfigurationSource(product,setting,true,true,true,true,true,true,Optional.of(definition),definition?Optional.of(shown):Optional.empty(),definition?Optional.of(valid):Optional.empty(),admitted,Optional.of(data),data.complete());
    }
    private static CurrentCourtierConfigurationSource ready(CurrentCourtierControls.Product product,CurrentCourtierConfiguration.Setting setting){return source(product,setting,raw(values()),true,true,true,true);}
    private static CurrentCourtierConfigurationSource ready(){return ready(CurrentCourtierControls.Product.MAIN,CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE);}
    private static CurrentCourtierConfigurationResult frame(CurrentCourtierConfiguration.Action action,int provider,int query,int date,int connection,CurrentCourtierConfigurationSource s) {
        boolean effect=action==CurrentCourtierConfiguration.Action.EXECUTE_SETTING;
        return new CurrentCourtierConfigurationResult(action,effect?CurrentCourtierConfigurationResult.Status.SETTING_DISPATCHED:CurrentCourtierConfigurationResult.Status.AVAILABLE,
                effect,effect,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(date)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(s),Optional.empty(),s.product(),s.setting());
    }
    private static CurrentCourtierConfigurationResult query(CurrentCourtierConfigurationSource s){return frame(CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION,1,2,1000,1,s);}
    private static NativeOwnerSnapshotMain268.CourtierConfigurationConfig intent(CurrentCourtierConfigurationSource s){return NativeOwnerSnapshotMain268.currentCourtierConfigurationConfig(config("current_courtier_configuration_execute",s.product().wire(),s.setting().wire()));}
    @Test void bothIndependentModesRequireOneOfTwoProductsAndFourExactSettings()throws IOException {
        for(var product:CurrentCourtierControls.Product.values())for(var setting:CurrentCourtierConfiguration.Setting.values()) {
            var q=config("current_courtier_configuration_query",product.wire(),setting.wire());var e=config("current_courtier_configuration_execute",product.wire(),setting.wire());
            assertEquals(CurrentCourtierConfiguration.Action.QUERY_CONFIGURATION,NativeOwnerSnapshotMain268.currentCourtierConfigurationConfig(q).action());
            assertEquals(CurrentCourtierConfiguration.Action.EXECUTE_SETTING,NativeOwnerSnapshotMain268.currentCourtierConfigurationConfig(e).action());
            assertEquals(product,NativeOwnerSnapshotMain268.currentCourtierConfigurationConfig(q).product());assertEquals(setting,NativeOwnerSnapshotMain268.currentCourtierConfigurationConfig(e).setting());
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CONFIGURATION_QUERY,NativeOwnerSnapshotMain268.observationMode(q));
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_COURTIER_CONFIGURATION_EXECUTE,NativeOwnerSnapshotMain268.observationMode(e));
        }
    }
    @Test void missingMistypedAndNonliteralProductOrSettingCannotBecomeAnAction()throws IOException {
        for(String mode:List.of("current_courtier_configuration_query","current_courtier_configuration_execute"))for(String key:List.of("product","setting")) {
            var missing=config(mode,"main","choose_female");missing.remove(key);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
            for(var n:List.of(config(mode,"main","choose_female").put(key,true),config(mode,"main","choose_female").put(key,1),config(mode,"main","choose_female").putNull(key)))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        for(String product:List.of("MAIN","Vivhite","main "))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_configuration_query",product,"choose_female")));
        for(String setting:List.of("CHOOSE_FEMALE","choose_male","age_plus_one","cost","choose_female "))assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_configuration_execute","main",setting)));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_courtier_configuration_query_then_execute","main","choose_female")));
    }
    @Test void exactCommonFieldsAndFilePinKeepTheirOwnTypedRanges()throws IOException {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=execute();n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        var boolBytes=execute();((ObjectNode)boolBytes.get("owner_descriptor")).put("bytes",true);
        for(var n:List.of(boolBytes,execute().put("owner_descriptor","D:/owner.json"),execute().put("read_timeout_seconds",61),execute().put("overall_timeout_seconds",0),execute().put("maximum_frames_per_operation",65537)))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
    }
    @Test void callerNumericConfigurationPermissionsAndOldSchemaBorrowingAreRejected()throws IOException {
        for(String field:List.of("age","female","diplomacy","cost","configuration","numeric_complete","execute_admissible","native_valid","expected_core","provider_generation","query_sequence","claim_sequence","ordinal","index","key","scope","control","action","instance_id","deadline"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(execute().put(field,1)),field);
        for(int version=24;version<=32;version++) {
            String schema="xar.native-owner-snapshot-config/v"+version;
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(execute().put("schema",schema)));
        }
        var old=execute().put("schema","xar.native-owner-snapshot-config/v32").put("mode","current_decisions_close_query");old.remove("product");old.remove("setting");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_DECISIONS_CLOSE_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
    }
    @Test void observedAbsentCreatorRetainsNullConfigurationAndNoExecuteAuthority()throws IOException {
        var s=new CurrentCourtierConfigurationSource(CurrentCourtierControls.Product.MAIN,CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE,true,false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),false,Optional.empty(),false);
        var q=query(s);assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationQueryFrame(q,core(1000),s.product(),s.setting()));
        assertTrue(s.configuration().isEmpty());assertFalse(s.numericComplete());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationSource(q,intent(s)));
        assertThrows(IllegalArgumentException.class,()->new CurrentCourtierConfigurationSource(s.product(),s.setting(),false,false,false,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),false,Optional.empty(),false));
    }
    @Test void numericCompletenessRequiresEveryOneOfTenRawValuesAndMissingNeverMeansZero()throws IOException {
        for(int index=0;index<10;index++) {
            var values=new ArrayList<>(values());values.set(index,Optional.empty());var data=raw(values);
            var s=source(CurrentCourtierControls.Product.MAIN,CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE,data,true,true,true,false);
            assertFalse(data.complete());assertFalse(s.numericComplete());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationSource(query(s),intent(s)));
            assertThrows(IllegalArgumentException.class,()->new CurrentCourtierConfigurationSource(s.product(),s.setting(),true,true,true,true,true,true,Optional.of(true),Optional.of(true),Optional.of(true),false,Optional.of(data),true));
        }
    }
    @Test void signedRawExtremesRoundTripAsStringsWithoutScaleAgeOrPriceInterpretation()throws IOException {
        var values=new ArrayList<>(values());values.set(0,Optional.of(Long.MIN_VALUE));values.set(9,Optional.of(Long.MAX_VALUE));var data=raw(values);
        var s=source(CurrentCourtierControls.Product.MAIN,CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE,data,true,true,true,true);
        var n=StrictJson.parse(query(s).encode().bytes(),1<<20).get("source").get("configuration");
        assertEquals(Long.toString(Long.MIN_VALUE),n.get("age").textValue());assertEquals(Long.toString(Long.MAX_VALUE),n.get("cost").textValue());
        assertTrue(s.numericComplete());assertEquals(Long.MIN_VALUE,s.configuration().orElseThrow().age().orElseThrow().longValue());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationSource(query(s),intent(s)));
    }
    @Test void actualNativePredicatesAndExplicitExecuteAdmissionRemainNecessary()throws IOException {
        var data=raw(values());var p=CurrentCourtierControls.Product.MAIN;var setting=CurrentCourtierConfiguration.Setting.CHOOSE_FEMALE;
        for(var s:List.of(source(p,setting,data,false,false,false,false),source(p,setting,data,true,false,true,false),source(p,setting,data,true,true,false,false),source(p,setting,data,true,true,true,false)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationSource(query(s),intent(s)));
        for(var product:CurrentCourtierControls.Product.values())for(var selected:CurrentCourtierConfiguration.Setting.values()) {
            var s=ready(product,selected);assertEquals(s,NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationSource(query(s),intent(s)));
        }
    }
    @Test void callbackRequiresWholeNumericSourceProductSettingCoreAndPrivateLease()throws IOException {
        var s=ready();var q=query(s);var action=CurrentCourtierConfiguration.Action.EXECUTE_SETTING;
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationDispatchFrame(q,frame(action,1,2,1000,1,s),intent(s)));
        var changedValues=new ArrayList<>(values());changedValues.set(9,Optional.of(778L));
        var changed=source(s.product(),s.setting(),raw(changedValues),true,true,true,true);
        for(var bad:List.of(q,frame(action,2,2,1000,1,s),frame(action,1,3,1000,1,s),frame(action,1,2,1024,1,s),frame(action,1,2,1000,2,s),frame(action,1,2,1000,1,changed),
                frame(action,1,2,1000,1,ready(CurrentCourtierControls.Product.VIVHITE,s.setting())),frame(action,1,2,1000,1,ready(s.product(),CurrentCourtierConfiguration.Setting.CHOOSE_SAME_HOUSE))))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationDispatchFrame(q,bad,intent(s)));
    }
    @Test void knownClaimRefusalIsNotDispatchAndVoidDispatchGrantsNoPoststate()throws IOException {
        var s=ready();var q=query(s);
        var denied=new CurrentCourtierConfigurationResult(CurrentCourtierConfiguration.Action.EXECUTE_SETTING,CurrentCourtierConfigurationResult.Status.CLAIM_CONSUMED,false,false,true,BigInteger.ONE,BigInteger.TWO,BigInteger.ONE,
                q.factsBefore(),q.owner(),q.source(),Optional.of("DATA original claim already consumed"),s.product(),s.setting());
        assertFalse(denied.effectAttempted());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentCourtierConfigurationDispatchFrame(q,denied,intent(s)));
        var done=frame(CurrentCourtierConfiguration.Action.EXECUTE_SETTING,1,2,1000,1,s);var n=StrictJson.parse(done.encode().bytes(),1<<20);
        assertTrue(n.get("effect_attempted").booleanValue());assertTrue(n.get("native_returned").booleanValue());
        for(String field:List.of("native_handled","creator_closed","courtier_created","age_changed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(field).booleanValue(),field);
    }
}

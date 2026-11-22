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
import org.xar.ck3.control.nativebridge.CurrentXqolThreshold;
import org.xar.ck3.control.nativebridge.CurrentXqolThresholdSource;
import org.xar.ck3.control.nativebridge.CurrentXqolThresholdResult;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Java DATA boundary tests only; no original Transport receipt, Native producer or live credit. */
final class NativeOwnerCurrentXqolThresholdSelectionTest {
    private static ObjectNode config(String mode,int target) {
        var n=StrictJson.object().put("schema","xar.native-owner-snapshot-config/v30").put("mode",mode).put("target_threshold",target)
                .put("overall_timeout_seconds",120).put("read_timeout_seconds",20).put("maximum_frames_per_operation",128);
        n.putObject("owner_descriptor").put("path","D:/threshold-selection-DATA/owner.json").put("bytes",1).put("sha256","0".repeat(64));return n;
    }
    private static CoreFrame.Prefix core(int raw){return new CoreFrame.Prefix(raw,1,true,0,true,true,42,true);}
    private static CurrentXqolPromptSource prompt(int instance,String opening) {
        var options=List.of(new CurrentLetterSource.Option(0,true,"confirm DATA","",Optional.of(CurrentXqolPrompt.CONFIRM_OPTION)),
                new CurrentLetterSource.Option(1,true,"cancel DATA","",Optional.of(CurrentXqolPrompt.CANCEL_OPTION)));
        var e=new CurrentXqolPromptSource.Event(3,true,true,true,true,instance,42,CurrentXqolPrompt.KNOWN_DEFINITION,opening," description DATA ",options);
        return new CurrentXqolPromptSource(3,2,true,Optional.of(2),Optional.of(e),true,true);
    }
    private static CurrentXqolThresholdSource source(int target,int instance,long bits,boolean shown,boolean valid,String opening) {
        return new CurrentXqolThresholdSource(prompt(instance,opening),true,true,true,Optional.of(shown),Optional.of(valid),Optional.of(bits),Optional.of(0L),Optional.of(0x42c80000L),Optional.of(0x3f800000L),target,shown&&valid);
    }
    private static CurrentXqolThresholdSource ready(int target){return source(target,7,0x42480000L,true,true," opening DATA ");}
    private static CurrentXqolThresholdResult frame(CurrentXqolThreshold.Action action,int provider,int query,int raw,int connection,CurrentXqolThresholdSource s) {
        boolean effect=action==CurrentXqolThreshold.Action.SET_THRESHOLD;
        return new CurrentXqolThresholdResult(action,effect?CurrentXqolThresholdResult.Status.THRESHOLD_ROUTE_DISPATCHED:CurrentXqolThresholdResult.Status.AVAILABLE,
                effect,effect,true,BigInteger.valueOf(provider),BigInteger.valueOf(query),effect?BigInteger.ONE:BigInteger.ZERO,
                Optional.of(core(raw)),Optional.of(new CurrentLetterResult.OwnerWitness(BigInteger.valueOf(connection),BigInteger.TWO,BigInteger.valueOf(3),4)),Optional.of(s),Optional.empty(),effect?s.prompt().event().map(CurrentXqolPromptSource.Event::instanceId):Optional.empty());
    }
    private static CurrentXqolThresholdResult query(CurrentXqolThresholdSource s){return frame(CurrentXqolThreshold.Action.QUERY_THRESHOLD,1,2,1000,1,s);}
    @Test void twoIndependentModesKeepExplicitTargetInBothQueryAndSet() {
        for(int target:List.of(0,50,100)) {
            var q=config("current_xqol_conversion_threshold_query",target);var set=config("current_xqol_conversion_threshold_set",target);
            assertEquals(CurrentXqolThreshold.Action.QUERY_THRESHOLD,NativeOwnerSnapshotMain268.currentXqolThresholdConfig(q).action());
            assertEquals(CurrentXqolThreshold.Action.SET_THRESHOLD,NativeOwnerSnapshotMain268.currentXqolThresholdConfig(set).action());
            assertEquals(target,NativeOwnerSnapshotMain268.currentXqolThresholdConfig(q).targetThreshold());
            assertEquals(target,NativeOwnerSnapshotMain268.currentXqolThresholdConfig(set).targetThreshold());
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_QUERY,NativeOwnerSnapshotMain268.observationMode(q));
            assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_THRESHOLD_SET,NativeOwnerSnapshotMain268.observationMode(set));
        }
    }
    @Test void targetCannotBeMissingBooleanFloatStringOrOutsideZeroToOneHundred() {
        for(String mode:List.of("current_xqol_conversion_threshold_query","current_xqol_conversion_threshold_set")) {
            var missing=config(mode,50);missing.remove("target_threshold");assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(missing));
            for(var n:List.of(config(mode,-1),config(mode,101),config(mode,50).put("target_threshold",true),config(mode,50).put("target_threshold",50.0),config(mode,50).put("target_threshold","50")))
                assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
    }
    @Test void commonFieldsAndOwnerExactFilePinRemainStrict() {
        for(String field:List.of("schema","mode","owner_descriptor","overall_timeout_seconds","read_timeout_seconds","maximum_frames_per_operation")) {
            var n=config("current_xqol_conversion_threshold_query",50);n.remove(field);assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(n));
        }
        var booleanBytes=config("current_xqol_conversion_threshold_query",50);((ObjectNode)booleanBytes.get("owner_descriptor")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(booleanBytes));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_threshold_query",50).put("owner_descriptor","D:/owner.json")));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_threshold_query",50).put("read_timeout_seconds",61)));
    }
    @Test void callerPermissionInstanceKeyCoreLeaseAndOldSchemaBorrowingAreRejected() {
        for(String field:List.of("instance_id","event_key","option_key","index","expected_core","provider_generation","query_sequence","claim_sequence","native_valid","set_admissible","action","value_bits_u32","deadline","auto_confirm"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_threshold_set",50).put(field,1)),field);
        for(String schema:List.of("xar.native-owner-snapshot-config/v24","xar.native-owner-snapshot-config/v25","xar.native-owner-snapshot-config/v26","xar.native-owner-snapshot-config/v27","xar.native-owner-snapshot-config/v28","xar.native-owner-snapshot-config/v29"))
            assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_threshold_query",50).put("schema",schema)));
        var old=config("current_xqol_conversion_prompt_query",50).put("schema","xar.native-owner-snapshot-config/v29");old.remove("target_threshold");
        assertEquals(NativeOwnerSnapshotMain268.ObservationMode.CURRENT_XQOL_CONVERSION_PROMPT_QUERY,NativeOwnerSnapshotMain268.observationMode(old));
        assertThrows(IllegalArgumentException.class,()->NativeOwnerSnapshotMain268.observationMode(config("current_xqol_conversion_threshold_set_then_confirm",50)));
    }
    @Test void absentKnownPromptRetainsNullFieldsAndNeverGrantsSetAuthority() {
        var p=new CurrentXqolPromptSource(3,2,true,Optional.empty(),Optional.empty(),false,false);
        var s=new CurrentXqolThresholdSource(p,false,false,false,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),75,false);
        var q=query(s);assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdQueryFrame(q,core(1000),75));
        assertTrue(s.observedValue().isEmpty());assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdSource(q,75));
    }
    @Test void actualNativeShownAndValidMustBothBeObservedTrue() {
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdSource(query(ready(75)),75));
        for(var s:List.of(source(75,7,0x42480000L,false,true,"DATA"),source(75,7,0x42480000L,true,false,"DATA"),
                new CurrentXqolThresholdSource(prompt(7,"DATA"),true,true,false,Optional.empty(),Optional.empty(),Optional.of(0x42480000L),Optional.of(0L),Optional.of(0x42c80000L),Optional.of(0x3f800000L),75,false)))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdSource(query(s),75));
    }
    @Test void rawBinary32ObservationIsNotTheBoundTargetOrAppliedScriptValue() {
        var s=ready(75);assertEquals(50.0f,s.observedValue().orElseThrow().floatValue());assertEquals(75,s.targetThreshold());
        assertDoesNotThrow(()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdDispatchFrame(query(s),frame(CurrentXqolThreshold.Action.SET_THRESHOLD,1,2,1000,1,s),75));
        assertThrows(IllegalArgumentException.class,()->source(75,7,0x7fc00000L,true,true,"DATA"));
        assertThrows(IllegalArgumentException.class,()->source(75,7,0x42ca0000L,true,true,"DATA"));
    }
    @Test void callbackKeepsWholeSourceCoreTargetInstanceProviderAndQuery() {
        var q=query(ready(75));var a=CurrentXqolThreshold.Action.SET_THRESHOLD;
        for(var bad:List.of(frame(a,2,2,1000,1,ready(75)),frame(a,1,3,1000,1,ready(75)),frame(a,1,2,1024,1,ready(75)),
                frame(a,1,2,1000,1,ready(76)),frame(a,1,2,1000,1,source(75,8,0x42480000L,true,true," opening DATA ")),
                frame(a,1,2,1000,1,source(75,7,0x42480000L,true,true,"opening DATA"))))
            assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdDispatchFrame(q,bad,75));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdQueryFrame(q,core(1000),76));
    }
    @Test void readonlyOrForeignConnectionCannotStandInForThisRoute() {
        var q=query(ready(75));assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdDispatchFrame(q,q,75));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdDispatchFrame(q,frame(CurrentXqolThreshold.Action.SET_THRESHOLD,1,2,1000,2,ready(75)),75));
        assertThrows(IOException.class,()->NativeOwnerSnapshotMain268.requireCurrentXqolThresholdSource(q,74));
    }
    @Test void callbackEncodingNeverConfirmsThresholdEventConversionDateOrSave()throws IOException {
        var f=frame(CurrentXqolThreshold.Action.SET_THRESHOLD,1,2,1000,1,ready(75));var n=StrictJson.parse(f.encode().bytes(),1<<20);
        assertTrue(n.get("effect_attempted").booleanValue());assertTrue(n.get("native_returned").booleanValue());
        for(String field:List.of("native_handled","threshold_applied","event_closed","conversion_applied","new_date_observed","physical_save_confirmed"))assertFalse(n.get(field).booleanValue(),field);
    }
}

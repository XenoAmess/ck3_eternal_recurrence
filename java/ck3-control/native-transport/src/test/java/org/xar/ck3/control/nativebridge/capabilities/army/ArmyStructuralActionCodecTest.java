package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual shared argument and original-evidence serde. DATA cannot mint an Ack or submission permit. */
final class ArmyStructuralActionCodecTest {
    private static RawJson json(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static ExactRef ref(String name){return new ExactRef("software-original-"+name,1,"a".repeat(64));}
    @Test void everyTypedSelectorRoundTripsAndNativeRequestIsOnlyTheCentralCoordinatorInput() {
        for(String step:List.of("halt-army-0","split-army-half-2147483647","merge-armies-0-with-2147483647")) {
            var call=ArmyStructuralActionsTest.call(step);assertEquals(call,ArmyStructuralActionCodec.decode(ArmyStructuralActionCodec.encode(call)));
            assertEquals(new org.xar.ck3.control.application.action.NativeRequest(step,java.util.Optional.of(call.capability()),json("{}")),ArmyStructuralActionCodec.request(call));
        }
    }
    @Test void argumentsRejectMissingNullAliasesExtraFieldsAndEqualButWrongJsonTypes() {
        String schema=ArmyStructuralActionCodec.SCHEMA;
        for(String value:List.of("{}","null","[]","{\"schema\":\""+schema+"\"}",
                "{\"schema\":\""+schema+"\",\"step\":null}","{\"schema\":\""+schema+"\",\"step\":true}",
                "{\"schema\":\""+schema+"\",\"step\":1.0}","{\"schema\":\""+schema+"\",\"step\":\"halt-army-00\"}",
                "{\"schema\":\""+schema+"\",\"step\":\"halt-army-0\",\"alias\":0}"))
            assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decode(json(value)),value);
    }
    @Test void originalPendingBasisHasOneStrictVersionAndExactRequiredCustodyReferences() {
        var original=new ArmyStructuralActionCodec.PendingBasis("b".repeat(64),"original-native-request",ref("before-native"),ref("before-driver"),ref("after-native"),ref("after-driver"),ref("material"));
        RawJson encoded=ArmyStructuralActionCodec.encode(original);assertEquals(original,ArmyStructuralActionCodec.decodeBasis(encoded));
        var complete=StrictJson.object(StrictJson.parse(encoded.bytes()),java.util.Set.of("schema","command_body_sha256","request_id","before_native","before_driver","after_native","after_driver","material"));
        for(String required:List.of("schema","command_body_sha256","request_id","before_native","before_driver","after_native","after_driver","material")) {
            var missing=complete.deepCopy();missing.remove(required);assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decodeBasis(new RawJson(StrictJson.canonical(missing))));
            var nil=complete.deepCopy();nil.putNull(required);assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decodeBasis(new RawJson(StrictJson.canonical(nil))));
        }
        var drift=complete.deepCopy();drift.put("schema","xar.java.army-structural-pending-originals/v0");
        assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decodeBasis(new RawJson(StrictJson.canonical(drift))));
        var alias=complete.deepCopy();alias.put("beforeNative","alias");assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decodeBasis(new RawJson(StrictJson.canonical(alias))));
        var wrong=complete.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("before_native")).put("bytes",true);
        assertThrows(IllegalArgumentException.class,()->ArmyStructuralActionCodec.decodeBasis(new RawJson(StrictJson.canonical(wrong))));
    }
    @Test void haltUnknownDataHasNoAfterMaterialAndCannotProbeGuardPacketsOrMintAnEffect() {
        var context=ArmyStructuralActionsTest.context();var call=ArmyStructuralActionsTest.call("halt-army-0");
        var command=new org.xar.ck3.control.application.action.ActionCommand("software-halt-no-dispatch",context.before(),context.source(),context.sessionId(),call.operation(),
                DriverJson.object(ArmyStructuralActionCodec.encode(call).bytes(),org.xar.ck3.control.application.action.ActionCommand.MAX_ARGUMENT_BYTES),ArmyStructuralEffects.expected(context.before(),context.source(),call),
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),context.deadline());
        var receipt=new org.xar.ck3.control.application.action.ActionReceipt(1,1,command,org.xar.ck3.control.application.action.ActionCodec.bodySha256(command),
                new org.xar.ck3.control.application.action.ActionState.Unknown(java.util.Optional.empty(),java.util.Optional.empty(),"software DATA only, no native attempt or Root authority",List.of(ref("native-packet"))));
        var type=org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class;
        var archive=type.cast(java.lang.reflect.Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},
                (proxy,method,arguments)->{throw new AssertionError("halt without after-material must not probe original archive packets: "+method.getName());}));
        assertTrue(ArmyStructuralEffects.pendingMaterial(receipt,archive,(basis,actualArchive)->{throw new AssertionError("no Root frame may be invented");}).isEmpty());
        assertEquals(org.xar.ck3.control.application.action.ActionReceipt.Outcome.UNRESOLVED,receipt.outcome());assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
    }
}

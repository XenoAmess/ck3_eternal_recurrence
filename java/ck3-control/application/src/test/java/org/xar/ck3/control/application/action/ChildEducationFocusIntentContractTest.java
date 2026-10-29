package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.family.ChildEducationFocusIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual intent/ActionCommand serialization and canonical refusal. These DATA records carry no Root/native authority. */
final class ChildEducationFocusIntentContractTest {
    @Test void fiveKeysAndHighNativeIdentityRoundtripThroughTheRealCommandCodec(){
        for(var target:ChildEducationFocusIntent.FocusKey.values()){
            var intent=new ChildEducationFocusIntent(0xFE000001L,target,Optional.empty());
            assertEquals(intent,ChildEducationFocusIntent.fromJson(intent.toJson()));
            var template=ActionCoordinatorTest.command("focus-codec-"+target.wire(),ChildEducationFocusIntent.STEP);
            var command=new ActionCommand(template.actionId(),template.before(),template.source(),template.sessionId(),
                    new OperationKey(ChildEducationFocusIntent.STEP),intent.toJson(),intent.expected(template.before(),template.source()),template.claims(),template.deadline());
            var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
            assertEquals(command,decoded);assertEquals(ActionCodec.bodySha256(command),ActionCodec.bodySha256(decoded));
            assertEquals(intent.values(),decoded.expected().values());
        }
    }
    @Test void missingWrongTypeAndLegacyQueryAliasesAreNotCanonicalIntent(){
        var intent=new ChildEducationFocusIntent(7,ChildEducationFocusIntent.FocusKey.EDUCATION_LEARNING,Optional.empty());
        var source=(com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNode(intent.toJson());
        for(var changed:List.of(source.deepCopy().put("child_full_id",false),source.deepCopy().put("child_full_id",7.0),
                source.deepCopy().put("child_full_id",0),source.deepCopy().put("child_full_id",0xFFFF_FFFFL),
                source.deepCopy().put("target_key","education_prowess"),source.deepCopy().put("target_key","EDUCATION_LEARNING"),
                source.deepCopy().put("query",true),source.deepCopy().put("schema","child-education-focus-private-12004-v1"))){
            var encoded=DriverJson.object(StrictJson.canonical(changed),DriverJson.MAX_NATIVE_BYTES);
            assertThrows(IllegalArgumentException.class,()->ChildEducationFocusIntent.fromJson(encoded));
        }
        var missing=source.deepCopy();missing.remove("planning_proof");
        assertThrows(IllegalArgumentException.class,()->ChildEducationFocusIntent.fromJson(DriverJson.object(StrictJson.canonical(missing),DriverJson.MAX_NATIVE_BYTES)));
    }
    @Test void sameSemAckDataCannotBeFocusAppliedAndCanonicalUnknownCannotResubmit(){
        var template=ActionCoordinatorTest.command("focus-unknown",ChildEducationFocusIntent.STEP);
        var intent=new ChildEducationFocusIntent(7,ChildEducationFocusIntent.FocusKey.EDUCATION_MARTIAL,Optional.empty());
        var command=new ActionCommand(template.actionId(),template.before(),template.source(),template.sessionId(),template.operation(),
                intent.toJson(),intent.expected(template.before(),template.source()),template.claims(),template.deadline());
        var attempt=new ActionState.Attempt("original-focus-request",ActionCoordinatorTest.NOW,ActionCoordinatorTest.guard(command,ActionCoordinatorTest.NOW),
                new NativeRequest(ChildEducationFocusIntent.STEP,Optional.empty(),new RawJson(new byte[]{'{','}'})));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.empty(),new RawJson(new byte[]{'{','}'}),new byte[]{1});
        var sameSem=new ActionState.EffectObservation(command.before(),command.source(),command.sessionId(),ChildEducationFocusIntent.OBSERVER_SCHEMA,
                intent.values(),"different-data-read",ActionCoordinatorTest.NOW.plusSeconds(1),ActionCoordinatorTest.AFTER);
        assertThrows(IllegalArgumentException.class,()->ActionEffects.validate(command,attempt,ack,new ActionState.Applied(sameSem)));
        var unknown=new NativeActionPort.Unknown(attempt.requestId(),"original response unavailable",new byte[0],Optional.empty());
        var pending=new ActionReceipt(1,3,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.of(attempt),Optional.of(unknown),"retained original focus",List.of()));
        assertThrows(IllegalArgumentException.class,()->ActionTransitions.validate(Optional.of(pending),command,pending.bodySha256(),new ActionState.Submitting(attempt)));
        assertTrue(pending.applied().isEmpty());assertFalse(pending.eligibleAdvance());
    }
}

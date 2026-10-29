package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.action.family.FamilyMarriageSendExpectation;
import org.xar.ck3.control.application.effects.family.FamilySendObservation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.MarriageArrangePublicCodec;
import org.xar.ck3.control.service.mcp.MarriageChoicesPublicCodec;

/** Shared core DATA fixture -> canonical receipt serde -> public presentation. No writer/private proof is constructed. */
public final class MarriageArrangePublicCodecTest {
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PublicBindings.Arguments args(String value){return new PublicBindings.Value(raw(value));}
    public static ActionCommand commandData() {
        var original=FamilySendCoreContractTest.vector().command();var intent=new RulerMarriageIntent("29829-8",29829,8,Optional.empty());
        return new ActionCommand(original.actionId(),original.before(),original.source(),original.sessionId(),new OperationKey(intent.step()),
                intent.toJson(),FamilyMarriageSendExpectation.expected(original.before(),original.source(),29829,8),original.claims(),original.deadline());
    }
    public static ActionReceipt unknownData() {
        var command=commandData();return new ActionReceipt(1,4,command,ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(),Optional.empty(),"DATA pending, never replay",List.of()));
    }
    @Test void exactChoiceAndOptionalRevisionKeepMissingNullAndFullWidthValueThroughSerde() {
        for(String original:List.of("{\"choice_id\":\"7-8\"}","{\"choice_id\":\"7-8\",\"expected_revision\":null}",
                "{\"choice_id\":\"7-8\",\"expected_revision\":0}","{\"choice_id\":\"7-8\",\"expected_revision\":9007199254740991}",
                "{\"choice_id\":\"7-8\",\"expected_revision\":\"18446744073709551615\"}")) {
            var value=MarriageArrangePublicCodec.decode(args(original));
            assertEquals(value,MarriageArrangePublicCodec.decode(new PublicBindings.Value(MarriageArrangePublicCodec.encodeRequest(value))));
            assertEquals("arrange-marriage-7-8",value.step());
        }
        assertInstanceOf(MarriageChoicesPublicCodec.MissingRevision.class,MarriageArrangePublicCodec.decode(args("{\"choice_id\":\"7-8\"}")).revision().expectedRevision());
        assertInstanceOf(MarriageChoicesPublicCodec.NullRevision.class,MarriageArrangePublicCodec.decode(args("{\"choice_id\":\"7-8\",\"expected_revision\":null}")).revision().expectedRevision());
        var zero=MarriageArrangePublicCodec.decode(args("{\"choice_id\":\"7-8\",\"expected_revision\":0}"));
        assertThrows(IllegalArgumentException.class,()->zero.revision().requireCurrent(BigInteger.ONE));
    }
    @Test void wrongMissingNullBooleanFloatingUnsafeAndExtraArgumentsFailBeforeAnyCurrentReader() {
        for(String invalid:List.of("null","[]","{}","{\"choice_id\":null}","{\"choice_id\":true}","{\"choice_id\":7}",
                "{\"choice_id\":\"wrong\"}","{\"choice_id\":\"7-8\",\"extra\":0}","{\"choice_id\":\"7-8\",\"expected_revision\":true}",
                "{\"choice_id\":\"7-8\",\"expected_revision\":1.0}","{\"choice_id\":\"7-8\",\"expected_revision\":9007199254740992}",
                "{\"choice_id\":\"7-8\",\"expected_revision\":\"01\"}","{\"choice_id\":\"7-8\",\"expected_revision\":\"18446744073709551616\"}"))
            assertThrows(IllegalArgumentException.class,()->MarriageArrangePublicCodec.decode(args(invalid)),invalid);
        assertThrows(IllegalArgumentException.class,()->MarriageArrangePublicCodec.decode(new PublicBindings.Missing()));
        assertThrows(IllegalArgumentException.class,()->MarriageArrangePublicCodec.decode(new PublicBindings.Null()));
    }
    private record SendData(ActionReceipt receipt,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,FamilySendObservation observation) { }
    private static SendData sendData() {
        var shared=FamilySendCoreContractTest.vector();var command=commandData();var old=shared.observation();
        var prepared=new NativeRequest(command.operation().value(),Optional.empty(),shared.attempt().preparedRequest().additionalFields(),shared.attempt().preparedRequest().preparationEvidence());
        var attempt=new ActionState.Attempt(shared.attempt().requestId(),shared.attempt().submittedAt(),ActionCoordinatorTest.guard(command,shared.attempt().submittedAt()),prepared);
        var ack=shared.dispatch();
        var observation=new FamilySendObservation(old.profile(),command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),old.originalDispatchRef(),old.preparedRequestRef(),
                old.beforeFrame(),old.afterFrame(),command.before(),command.before(),command.source(),command.sessionId(),old.beforeStorage(),old.afterStorage(),old.completePreparation(),
                old.nativePendingFullId(),old.definitionStableHash(),FamilySendObservation.sendOnlyValues(FamilySendObservation.Profile.MARRIAGE,29829,8,old.nativePendingFullId()));
        var receipt=new ActionReceipt(1,4,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.FamilySendConfirmed(observation)));
        return new SendData(receipt,attempt,ack,observation);
    }
    private static ActionPorts.OutcomeArchive dataArchive(SendData value) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                (proxy,method,args)->switch(method.getName()) {
                    case "referenceOf" -> {assertEquals(value.ack(),args[0]);yield value.observation().originalDispatchRef();}
                    case "requestReferenceOf" -> {assertEquals(value.attempt().preparedRequest(),args[0]);yield value.observation().preparedRequestRef();}
                    case "load" -> {assertEquals(value.observation().originalDispatchRef(),args[0]);yield value.ack();}
                    case "loadRequest" -> {assertEquals(value.observation().preparedRequestRef(),args[0]);yield value.attempt().preparedRequest();}
                    case "readReferenceOf" -> {
                        if(value.observation().beforeStorage().equals(args[0]))yield value.observation().completePreparation().getFirst();
                        assertEquals(value.observation().afterStorage(),args[0]);yield new ExactRef("D:/family-send-data/after-read",1,"1".repeat(64));
                    }
                    case "loadRead" -> {
                        if(value.observation().completePreparation().getFirst().equals(args[0]))yield value.observation().beforeStorage();
                        assertEquals(new ExactRef("D:/family-send-data/after-read",1,"1".repeat(64)),args[0]);yield value.observation().afterStorage();
                    }
                    default -> throw new AssertionError("DATA fixture supplies no authority or writer: "+method.getName());
                });
    }
    @Test void sharedCanonicalSendDataSurvivesReceiptSerdeThenPublicEncoderWithoutAppliedOrRelationshipCredit() {
        var value=sendData();var archive=dataArchive(value);var bytes=ActionReceiptCodec.encodeReceipt(value.receipt(),archive);
        var restored=ActionReceiptCodec.decodeReceipt(bytes,archive);assertEquals(value.receipt(),restored);
        var reply=new MarriageArrangePublicCodec.Reply(restored,true);var row=StrictJson.parse(MarriageArrangePublicCodec.encode(reply).bytes());
        assertEquals("send_confirmed",row.get("status").textValue());assertTrue(row.get("send_confirmed").booleanValue());
        assertEquals("proposal_submitted",row.path("marriage_action").get("status").textValue());assertFalse(row.get("relationship_confirmed").booleanValue());
        assertFalse(row.get("eligible_advance").booleanValue());assertTrue(row.get("accepted").isNull());assertTrue(row.get("reconciliation").booleanValue());
        assertTrue(row.path("marriage_choice").get("played_character_id").isIntegralNumber());assertEquals(29829,row.path("marriage_choice").get("played_character_id").intValue());
        assertTrue(restored.applied().isEmpty());assertEquals(restored.command().before(),value.observation().after());
    }
    @Test void ackAcceptedAndUnknownRemainUnknownAndErrorAckCannotClaimAccepted() {
        var value=sendData();var command=value.receipt().command();
        for(boolean nativeOk:List.of(true,false)) {
            var ack=new NativeActionPort.AckReceived(value.ack().requestId(),nativeOk,Optional.of(raw("{\"accepted\":true}")),value.ack().originalFrame(),value.ack().originalPacket());
            for(ActionState state:List.of(new ActionState.AckReceived(value.attempt(),ack),new ActionState.Unknown(Optional.of(value.attempt()),Optional.of(ack),"DATA uncertain",List.of()))) {
                var receipt=new ActionReceipt(1,4,command,ActionCodec.bodySha256(command),state);
                var row=StrictJson.parse(MarriageArrangePublicCodec.encode(new MarriageArrangePublicCodec.Reply(receipt,false)).bytes());
                assertEquals("unknown",row.path("marriage_action").get("status").textValue());assertFalse(row.get("send_confirmed").booleanValue());
                assertFalse(row.get("relationship_confirmed").booleanValue());assertFalse(row.get("eligible_advance").booleanValue());
                assertTrue(row.path("marriage_action").get("submitted_date_raw").isNull());
                assertEquals(nativeOk,row.get("native_ack_ok").booleanValue());if(nativeOk)assertTrue(row.get("accepted").booleanValue());else assertTrue(row.get("accepted").isNull());
            }
        }
        var absent=StrictJson.parse(MarriageArrangePublicCodec.encode(new MarriageArrangePublicCodec.Reply(unknownData(),false)).bytes());
        assertTrue(absent.get("accepted").isNull());assertTrue(absent.get("native_ack_ok").isNull());assertTrue(absent.path("marriage_action").get("submitted_date_raw").isNull());
        var unknown=unknownData();assertThrows(IllegalArgumentException.class,()->ActionTransitions.validate(Optional.of(unknown),unknown.command(),unknown.bodySha256(),
                new ActionState.Submitting(value.attempt())),"public presentation supplies no UNKNOWN replay transition");
    }
}

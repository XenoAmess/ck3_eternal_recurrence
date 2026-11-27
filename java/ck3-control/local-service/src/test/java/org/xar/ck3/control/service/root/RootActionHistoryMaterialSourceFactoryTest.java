package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.ObservationProvenance;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalOnly;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.CanonicalReason;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Evidence;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.EvidenceKind;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Legacy;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.Recording;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.NativeEventPostconditionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedInteger;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.CurrentFull111EventOption;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Material policy cases for originals already verified by the action's archived replay. */
class RootActionHistoryMaterialSourceFactoryTest {
    @Test void returnedOriginalDoesNotBecomeAnAppliedOrAcceptedAlias(){
        // These are actual original execute_step result shapes: no accepted field for mercenary results,
        // and the gift compatible result can retain its query step rather than the submitting operation.
        Obj mercenaries=new Obj(Map.of("status",new Text("hired"),"mercenary_company_id",number(9)));
        assertEquals(Recording.RETURNED,record("hire-mercenary-company-9",mercenaries));
        Obj gift=new Obj(Map.of("step",new Text("query-faction-member-gift-v1"),"status",new Text("observed")));
        assertEquals(Recording.RETURNED,record("send-faction-gift-9",gift));
        Obj submitted=new Obj(Map.of("marriage_result",new Obj(Map.of("status",new Text("proposal_submitted")))));
        assertEquals(Recording.RETURNED,record("arrange-marriage-707-809",submitted));
        assertEquals(Recording.RETURNED,record("enforce-demands-9",new Obj(Map.of("accepted",new Bool(false),"status",new Text("pending")))));
    }
    @Test void sourceBoundOverviewAndOriginalExceptionalReturnsUseTheirActualAcceptedField(){
        Obj rejected=new Obj(Map.of("accepted",new Bool(false)));
        assertEquals(Recording.ACCEPTED_RETURN,record("query-war-declared-overview-v1",rejected));
        assertEquals(Recording.ACCEPTED_RETURN,record("close-war-declared-overview-v1",rejected));
        Obj moved=new Obj(Map.of("accepted",new Bool(false),"status",new Text("observed_after_native_error"),"native_ack_verified",new Bool(false)));
        assertEquals(Recording.ACCEPTED_RETURN,record("move-army-0-to-42",moved));
        assertEquals(Recording.RETURNED,record("move-army-0-to-42",moved.with("native_ack_verified",new Bool(true))));
        assertEquals(Recording.RETURNED,record("move-army-00-to-42",moved));
        assertEquals(Recording.RETURNED,record("move-army-0-to-2147483648",moved));
        List<String> operations=List.of("query-route-contact-horizon-v1-0-to-42-h-2-8-9","query-war-termination-options-9","query-battle-control-snapshot-v1-0");
        List<String> schemas=List.of("xar.route-contact-readonly-unavailable.v1","xar.war-termination-readonly-unavailable/v1","xar.battle-control-readonly-unavailable.v1");
        for(int index=0;index<operations.size();index++){
            Obj unavailable=new Obj(Map.of("schema",new Text(schemas.get(index)),"status",new Text("unavailable"),"accepted",new Bool(false)));
            assertEquals(Recording.ACCEPTED_RETURN,record(operations.get(index),unavailable));
            assertEquals(Recording.RETURNED,record(operations.get(index),unavailable.with("status",new Text("available"))));
            assertEquals(Recording.RETURNED,record("unrelated-operation",unavailable));
        }
        assertThrows(IllegalArgumentException.class,()->record("close-war-declared-overview-v1",new Obj(Map.of("accepted",number(1)))));
    }
    @Test void samplingSetOriginalRecorderUsesTypedAcceptedRatherThanReturnedSuccess(){
        for(String step:List.of("enable-army-observer-research-sampling-v1","disable-army-observer-research-sampling-v1")) {
            assertEquals(Recording.ACCEPTED_RETURN,record(step,new Obj(Map.of("accepted",new Bool(true)))));
            assertEquals(Recording.ACCEPTED_RETURN,record(step,new Obj(Map.of("accepted",new Bool(false),"status",new Text("incomplete")))));
            assertThrows(IllegalArgumentException.class,()->record(step,new Obj(Map.of("accepted",number(1)))));
        }
    }
    @Test void originalPolicyRolesCannotBeSubstitutedOrSilentlyRebased(){
        var driver=ref("native_driver.py",1658471,"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603");
        var overview=ref("war_declared_overview_contract.py",11073,"86ebfb0fc5ba6a0150f28c8ac4aeceb3c65116b03d0f5175a99fc9659377ece0");
        var war=ref("war_contract.py",241556,"b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937");
        var battle=ref("battle_control_contract.py",91388,"2a5509214b8c0187bb0799a4fc10728d7ea7b7954a525af977d768de0528c3de");
        assertEquals(List.of(driver,overview,war,battle,RootFamilySendRecordingMaterial.originalContract(driver),RootActionHistoryMaterialSourceFactory.samplingOriginal(driver),RootActionHistoryMaterialSourceFactory.guiServiceOriginal(driver),RootActionHistoryMaterialSourceFactory.guiCameraOriginal(driver),RootActionHistoryMaterialSourceFactory.pilgrimageOriginal(driver),RootActionHistoryMaterialSourceFactory.closeOriginal(driver),RootActionHistoryMaterialSourceFactory.giftOriginal(driver)),new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(driver,overview,war,battle).originals());
        assertThrows(IllegalArgumentException.class,()->new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(overview,driver,war,battle));
        assertThrows(IllegalArgumentException.class,()->new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(ref("native_driver.py",1658471,"0".repeat(64)),overview,war,battle));
    }

    @Test void full111StockSelectionKeepsOriginalsAndCountsAsVisibleGameplay() throws Exception {
        String operation = CurrentFull111EventOption.Action.SELECT.step();
        var receipt = selection(operation, RootFull111EventOptionEffects.SCHEMA);
        var original = full111Result(operation);
        var result = ref("effect-result.json", 1, "1".repeat(64));
        var producer = ref("effect-producer.java", 1, "2".repeat(64));
        var queue = ref("queue-ack.bin", 1, "3".repeat(64));
        var originals = new LinkedHashSet<>(List.of(new Evidence(EvidenceKind.MATERIAL, queue), new Evidence(EvidenceKind.MATERIAL, result)));
        var producers = new LinkedHashSet<>(List.of(producer));

        var material = RootActionHistoryMaterialSourceFactory.recordNativeResult(receipt, result, original, originals, producers);
        assertEquals(new CanonicalOnly(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER, List.copyOf(originals), List.of(producer)), material);
        assertTrue(receipt.visibleGameplay());
        assertFalse(receipt.eligibleAdvance());

        var legacy = selection("select-event-option-1", NativeEventPostconditionPort.EVENT_SCHEMA);
        var legacyOriginal = new RawJson(DriverJson.encode(new Obj(Map.of("selected_option_index", number(0)))));
        var legacyMaterial = assertInstanceOf(Legacy.class,
                RootActionHistoryMaterialSourceFactory.recordNativeResult(legacy, result, legacyOriginal, originals, producers));
        assertEquals(Recording.RETURNED, legacyMaterial.recording());
    }

    @Test void full111StockSelectionRejectsOldOrDetachedResultMaterial() throws Exception {
        String operation = CurrentFull111EventOption.Action.SELECT.step();
        var receipt = selection(operation, RootFull111EventOptionEffects.SCHEMA);
        var result = ref("effect-result.json", 1, "1".repeat(64));
        var original = full111Result(operation);
        var originals = new LinkedHashSet<>(List.of(new Evidence(EvidenceKind.MATERIAL, result)));
        var producers = new LinkedHashSet<>(List.of(ref("effect-producer.java", 1, "2".repeat(64))));
        var legacyObserver = selection(operation, NativeEventPostconditionPort.EVENT_SCHEMA);
        assertThrows(IllegalArgumentException.class,
                () -> RootActionHistoryMaterialSourceFactory.recordNativeResult(legacyObserver, result, original, originals, producers));
        var targetPresent = new RawJson(DriverJson.encode(DriverJson.object(original.bytes(), DriverJson.MAX_NATIVE_BYTES)
                .with("event_queue_absent", new Bool(false))));
        assertThrows(IllegalArgumentException.class,
                () -> RootActionHistoryMaterialSourceFactory.recordNativeResult(receipt, result, targetPresent, originals, producers));
        assertThrows(IllegalArgumentException.class,
                () -> RootActionHistoryMaterialSourceFactory.recordNativeResult(receipt, result, original, new LinkedHashSet<>(), producers));
    }

    @Test void full111ActualZeroWriteRetainsItsPreparedPacketAndCannotClaimAnEffect() throws Exception {
        try (var resource = getClass().getResourceAsStream("/org/xar/ck3/control/application/session/source56-named-zero-dispatch.json.gz");
             var compressed = new java.util.zip.GZIPInputStream(resource)) {
            var fixture = StrictJson.parse(compressed.readAllBytes(), 1024 * 1024);
            var originals = fixture.get("materials");
            java.util.function.Function<ExactRef, byte[]> bytes = ref -> {
                var raw = java.util.Base64.getDecoder().decode(originals.get(ref.sha256()).textValue());
                assertEquals(ref.bytes(), raw.length);
                assertEquals(ref.sha256(), ActionCodec.sha256(raw));
                return raw;
            };
            var codec = new org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec((ref, maximum) -> bytes.apply(ref));
            var archive = (org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive) java.lang.reflect.Proxy.newProxyInstance(
                    getClass().getClassLoader(),
                    new Class<?>[]{org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class},
                    (proxy, method, args) -> switch (method.getName()) {
                        case "loadReceipt" -> org.xar.ck3.control.application.action.ActionReceiptCodec.decodeReceipt(
                                bytes.apply((ExactRef) args[0]), (org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive) proxy);
                        case "loadRequest" -> codec.decodePreparedRequestData((ExactRef) args[0]);
                        case "load" -> codec.decodeDispatchData((ExactRef) args[0]);
                        default -> throw new AssertionError("unexpected original reader " + method);
                    });
            var reference = ExactRef.fromJson(fixture.get("events").get(4).get("details").get("receipt_ref"));
            var receipt = org.xar.ck3.control.application.action.ActionRecordCodec.decode(bytes.apply(reference), archive).receipt();
            var zero = assertInstanceOf(ActionState.RejectedBeforeDispatch.class, receipt.state());
            var prepared = zero.attempt().preparedRequest();
            RootActionHistoryMaterialSourceFactory.requireFull111ZeroDispatch(receipt, zero, prepared);
            assertFalse(receipt.visibleGameplay());
            assertFalse(receipt.eligibleAdvance());
            assertTrue(receipt.applied().isEmpty());
            var detached = new NativeRequest(prepared.step(), prepared.requiredCapability(), prepared.additionalFields());
            assertThrows(IllegalArgumentException.class,
                    () -> RootActionHistoryMaterialSourceFactory.requireFull111ZeroDispatch(receipt, zero, detached));
        }
    }

    private static RawJson full111Result(String operation) {
        return new RawJson(DriverJson.encode(new Obj(Map.of("schema", new Text(RootFull111EventOptionEffects.RESULT_SCHEMA),
                "step", new Text(operation), "progress_status", new Text("postcondition"), "old_event_instance_id", number(7),
                "recipient_character_id", number(-16777215), "event_definition_key", new Text("bookmark.1070"),
                "selected_native_option_index", number(4), "event_queue_absent", new Bool(true),
                "active_event", new Obj(Map.of("event_instance_id", number(8)))))));
    }

    private static ActionReceipt selection(String step, String observerSchema) throws Exception {
        Instant start = Instant.parse("2026-11-27T04:00:00Z");
        Instant deadline = start.plusSeconds(30);
        String session = "software-session";
        var game = new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE));
        var before = selectionFrame(game, 12);
        var after = selectionFrame(game, 13);
        var renderer = ref("renderer.bin", 1, "4".repeat(64));
        var frame = ref("after.bin", 1, "5".repeat(64));
        var source = new G2Source(before.machineId(), start.toString(), "a".repeat(64), renderer);
        var operation = new OperationKey(step);
        var fields = DriverJson.object(StrictJson.canonical(renderer.toJson()), DriverJson.MAX_NATIVE_BYTES);
        var args = new Obj(Map.of("renderer_original", fields, "instance_id", number(7),
                "recipient_character_id", number(-16777215), "definition_key", new Text("bookmark.1070"), "authored_option_index", number(4)));
        List<ExpectedValue> values = List.of(new ExpectedInteger(new FieldKey("event_instance_id"), BigInteger.valueOf(7)),
                new ExpectedInteger(new FieldKey("recipient_character_id"), BigInteger.valueOf(-16777215)),
                new ExpectedText(new FieldKey("event_definition_key"), "bookmark.1070"),
                new ExpectedInteger(new FieldKey("authored_option_index"), BigInteger.valueOf(4)),
                new ExpectedBoolean(new FieldKey("event_queue_absent"), true),
                new ExpectedText(new FieldKey("connection_generation_decimal"), "1"));
        var expected = new ExpectedPostcondition(1, before, source, observerSchema, values);
        var claims = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
        var command = new ActionCommand("software-event-7", before, source, session, operation, args, expected, claims, deadline);
        var guard = new GuardEvidence(before, source, session, BigInteger.ONE, operation, renderer, renderer, "test", start, deadline);
        var request = new NativeRequest(step, Optional.empty(), new RawJson(DriverJson.encode(new Obj(Map.of()))));
        var attempt = new ActionState.Attempt("select-7", start, guard, request);
        var ack = StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", attempt.requestId()).put("ok", true);
        ack.putObject("result");
        var ackBytes = StrictJson.canonical(ack);
        var dispatched = new AckReceived(attempt.requestId(), true, Optional.of(new RawJson(new byte[]{'{', '}'})),
                new RawJson(ackBytes), NativeWire.packet(ackBytes));
        var observation = new ActionState.EffectObservation(after, source, session, observerSchema, values,
                new ObservationProvenance.Query("queue-7"), start.plusSeconds(1), frame, List.of(renderer));
        return new ActionReceipt(1, 2, command, ActionCodec.bodySha256(command),
                new ActionState.Settled(attempt, dispatched, new ActionState.Applied(observation)));
    }

    private static ObservationIdentity selectionFrame(GameGeneration game, long revision) {
        var frame = new Frame(BigInteger.valueOf(-16777215), BigInteger.valueOf(revision), BigInteger.valueOf(53144328));
        return new ObservationIdentity("software-history", game, new ProposalFrame(frame, "native:" + revision, BigInteger.ONE, "software"), 1);
    }
    private static Recording record(String step,Obj result){return RootActionHistoryMaterialSourceFactory.recording(new OperationKey(step),result);}
    private static IntegerValue number(long number){return new IntegerValue(java.math.BigInteger.valueOf(number));}
    private static ExactRef ref(String name,long bytes,String sha){return new ExactRef("D:/source-data-only/"+name,bytes,sha);}
}

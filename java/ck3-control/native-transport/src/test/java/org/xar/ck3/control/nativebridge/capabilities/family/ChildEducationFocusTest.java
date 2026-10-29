package org.xar.ck3.control.nativebridge.capabilities.family;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.ChildEducationFocus.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Closed actual query input plus synthetic pending/post cases checked against the original production parser. */
final class ChildEducationFocusTest {
    private static final String FIXTURE = "ck3_autonomous_player/tests/unit/fixtures/lifestyle_after_succession_4106_4107_v1.json";
    private static final List<Pin> PINS = List.of(
            new Pin(FIXTURE, 2702, "75f01d2699f1306c8f2b8c9b93edfb8f773b32020a19258831e8cbf21563b425"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/child_education_focus_private_v1.py", 19253, "8a97b27c594128ffe38e011431af00928172b4d842671b798981390fc198a247"),
            new Pin("ck3_autonomous_player/native_bridge/src/child_education_focus_private_12004.cpp", 21060, "b6f10c36a15c5260fe7c5c39210e25a08b0ea3ab1edc03ffc096eb6941c8fb83"),
            new Pin("ck3_autonomous_player/native_bridge/include/xar_bridge/child_education_focus_receipt_v1.hpp", 3939, "2e5d6efb77ea51a0233f9f464537fb1d808d9e61816aed521cef3fb1cc08a2c3"));
    private record Pin(String path, long bytes, String sha256) { }
    private static final Frame PRE = new Frame("native:53", "synthetic-episode", BigInteger.valueOf(53), 53220000, 101);
    private static final Frame POST = new Frame("native:54", "synthetic-episode", BigInteger.valueOf(54), 53220000, 101);
    private static final Selection SELECTED = new Selection(202, Key.EDUCATION_STEWARDSHIP);

    @Test void closedActualUnavailableLegalityRetainsIndependentlyPresentCurrentFocus() throws Exception {
        verifyPins(); ObjectNode fixture = actual(); Context context = ChildEducationFocus.decodeContext(fixture.get("source_context"));
        ObjectNode nativeResult = nativeQuery(fixture); Selection selected = new Selection(40526, Key.EDUCATION_STEWARDSHIP);
        Query query = ChildEducationFocus.decodeQuery(raw(nativeResult), context.frame(), selected);
        assertEquals(QueryStatus.UNAVAILABLE, query.status()); assertTrue(query.nativeLegal().isEmpty());
        assertEquals(Presence.PRESENT, query.focus().presence()); assertEquals("education_intrigue", query.focus().key().orElseThrow());
        assertEquals(fixture, OpportunityJson.toNode(ChildEducationFocusQueries.project(query, context, fixture.get("request_id").textValue(), Optional.empty())));
        assertEquals(query, ChildEducationFocus.decodeQuery(query.original(), context.frame(), selected)); verifyPins();
    }
    @Test void originalPythonParserAndOriginalRequestProducerAcceptSameClosedActualInput() throws Exception {
        verifyPins(); Path root = repository();
        String script = """
                import json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.child_education_focus_private_v1 import parse_child_education_focus_private_v1,_request
                value=json.loads((root/'ck3_autonomous_player/tests/unit/fixtures/lifestyle_after_succession_4106_4107_v1.json').read_text(encoding='utf-8'))['education_query']
                result={key:value[key] for key in ('schema','kind','status','unavailable_reason','source_frame','child_full_id','target_key','native_legal','current_focus')}
                response={'type':'command_result','protocol_version':1,'request_id':value['request_id'],'ok':True,'result':result}
                parsed=parse_child_education_focus_private_v1(response,expected_request_id=value['request_id'],kind='query',expected_frame=value['source_frame'],child_full_id=value['child_full_id'],target_key=value['target_key'])
                packet={**_request(value['source_context'],value['child_full_id'],value['target_key']),'type':'execute_step','protocol_version':1,'request_id':'synthetic-query-id','step':'private-query-child-education-focus-v1'}
                print(json.dumps({'parsed':parsed,'request':packet},sort_keys=True,separators=(',',':')))
                """;
        JsonNode original = python(script, root.toString()); ObjectNode actual = actual(); Context context = ChildEducationFocus.decodeContext(actual.get("source_context"));
        assertEquals(nativeQuery(actual), original.get("parsed"));
        var request = ChildEducationFocusQueries.nativeRequest(new OperationKey(ChildEducationFocus.QUERY_STEP), context, new Selection(40526, Key.EDUCATION_STEWARDSHIP), Optional.empty());
        byte[] packet = NativeWire.execute("synthetic-query-id", request.step(), context.frame().nativeRevision(), request.additionalFields().bytes());
        assertEquals(original.get("request"), NativeWire.parse(java.util.Arrays.copyOfRange(packet, 4, packet.length))); verifyPins();
    }
    @Test void syntheticUnknownPendingCanOnlyAcquireCreditFromOriginalAcceptedLaterPost() {
        Pending pending = ChildEducationFocus.decodePending(raw(pending(true)));
        assertEquals(PendingStatus.ACTION_STATE_UNKNOWN, pending.status()); assertTrue(pending.accepted().isEmpty()); assertTrue(pending.nativeCommandSubmitted().isEmpty());
        ObjectNode nativeResult = receipt(); Receipt result = ChildEducationFocus.decodeReceipt(raw(nativeResult), POST, pending);
        assertTrue(result.observedApplied()); assertEquals(SubmitStatus.SUBMITTED_VERIFICATION_PENDING, result.submission().status());
        var projection = ChildEducationFocusQueries.project(result, new Context(POST, BigInteger.valueOf(56)), "synthetic-receipt-id", Optional.of(pending));
        assertEquals("synthetic-action-id", OpportunityJson.text(projection.get("action_request_id"), "action_request_id"));
        assertTrue(OpportunityJson.bool(projection.get("observed_applied"), "observed_applied"));
        assertEquals(pending.original(), ChildEducationFocus.verifyPending(pending));
    }
    @Test void syntheticReceiptParsesThroughOriginalPythonProductionConsumer() throws Exception {
        verifyPins(); ObjectNode nativeResult = receipt(), pending = pending(true);
        ObjectNode input = StrictJson.object(); input.set("result", nativeResult); input.set("pending", pending); input.set("post", ChildEducationFocus.encodeFrame(POST));
        String script = """
                import json,pathlib,sys
                root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
                from xar_autoplayer.bridge.child_education_focus_private_v1 import parse_child_education_focus_private_v1
                value=json.loads(sys.argv[2]); pending=value['pending'];result=value['result']
                response={'type':'command_result','protocol_version':1,'request_id':'synthetic-receipt-id','ok':True,'result':result}
                parsed=parse_child_education_focus_private_v1(response,expected_request_id='synthetic-receipt-id',kind='receipt',expected_frame=value['post'],child_full_id=pending['child_full_id'],target_key=pending['requested_focus_key'],expected_submission=pending)
                print(json.dumps(parsed,sort_keys=True,separators=(',',':')))
                """;
        JsonNode original = python(script, repository().toString(), new String(StrictJson.canonical(input), StandardCharsets.UTF_8));
        assertEquals(nativeResult, original); assertTrue(ChildEducationFocus.decodeReceipt(raw(nativeResult), POST, ChildEducationFocus.decodePending(raw(pending))).observedApplied()); verifyPins();
    }
    @Test void queueAckSameFrameWrongKeyAndUnpublishedPostNeverBecomeApplied() {
        Pending pending = ChildEducationFocus.decodePending(raw(pending(false)));
        ObjectNode same = receipt(); ((ObjectNode) same.path("post_observation")).set("source_frame", ChildEducationFocus.encodeFrame(PRE));
        assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodeReceipt(raw(same), PRE, pending));
        ObjectNode unpublished = receipt(); ((ObjectNode) unpublished.path("post_observation")).put("independently_published_after_submission", false); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodeReceipt(raw(unpublished), POST, pending));
        ObjectNode key = receipt(); ((ObjectNode) key.path("post_observation").path("current_focus")).put("key", "education_intrigue"); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodeReceipt(raw(key), POST, pending));
        ObjectNode notAccepted = receipt(); ((ObjectNode) notAccepted.path("submission")).put("status", "submit_unknown").put("accepted", false); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodeReceipt(raw(notAccepted), POST, pending));
        ObjectNode awaiting = receipt().put("status", "verification_pending").put("observed_applied", false); awaiting.putNull("post_observation"); assertFalse(ChildEducationFocus.decodeReceipt(raw(awaiting), POST, pending).observedApplied());
    }
    @Test void wrongTypeFieldSourceAndUnknownDispatchMutationAreRefused() {
        ObjectNode n = pending(true); ObjectNode numericBool = n.deepCopy().put("accepted", 1); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(numericBool)));
        ObjectNode dispatchedUnknown = n.deepCopy().put("native_command_submitted", true); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(dispatchedUnknown)));
        ObjectNode mismatched = n.deepCopy(); ((ObjectNode) mismatched.path("source_context")).put("exe_sha256", FamilyObligations.Build.ORIGINAL2.sha256()); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(mismatched)));
        ObjectNode missing = n.deepCopy(); missing.remove("pre_frame"); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(missing)));
        ObjectNode floatId = n.deepCopy().put("child_full_id", 202.0); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(floatId)));
        ObjectNode extra = n.deepCopy().put("assume_applied", true); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocus.decodePending(raw(extra)));
        ObjectNode fields = StrictJson.object().put("child_full_id", 202).put("target_key", "education_stewardship").put("expected_revision", 56);
        assertEquals(SELECTED, ChildEducationFocusQueries.queryArguments(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)), "args")).selection());
        fields.put("expected_revision", true); assertThrows(IllegalArgumentException.class, () -> ChildEducationFocusQueries.queryArguments(OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)), "args")));
    }
    private static ObjectNode actual() throws Exception { return (ObjectNode) StrictJson.parse(Files.readAllBytes(repository().resolve(FIXTURE))).get("education_query"); }
    private static ObjectNode nativeQuery(ObjectNode publicValue) { ObjectNode n = publicValue.deepCopy(); n.remove(List.of("request_id", "source_public_revision", "source_context")); return n; }
    private static ObjectNode focus() { ObjectNode n = StrictJson.object().put("available", true).put("presence", "present").put("key", SELECTED.target().wire()); n.putNull("unavailable_reason"); return n; }
    private static ObjectNode submission() {
        ObjectNode n = StrictJson.object().put("status", "submitted_verification_pending").put("action_request_id", "synthetic-action-id").put("accepted", true).put("child_full_id", SELECTED.child()).put("requested_focus_key", SELECTED.target().wire());
        n.putNull("unavailable_reason"); n.set("pre_frame", ChildEducationFocus.encodeFrame(PRE)); return n;
    }
    private static ObjectNode pending(boolean unknown) {
        ObjectNode n = submission().put("schema", ChildEducationFocus.SCHEMA).put("kind", "submit").put("request_id", "synthetic-action-id").put("source_public_revision", 55);
        n.set("source_context", ChildEducationFocus.encodeContext(new Context(PRE, BigInteger.valueOf(55))));
        if (unknown) n.put("status", "action_state_unknown").putNull("accepted").putNull("native_command_submitted"); else n.put("native_command_submitted", true); return n;
    }
    private static ObjectNode receipt() {
        ObjectNode n = StrictJson.object().put("schema", ChildEducationFocus.SCHEMA).put("kind", "receipt").put("status", "observed_applied").put("observed_applied", true); n.putNull("unavailable_reason"); n.set("submission", submission());
        ObjectNode post = StrictJson.object().put("action_request_id", "synthetic-action-id").put("independently_published_after_submission", true).put("child_full_id", SELECTED.child()); post.set("source_frame", ChildEducationFocus.encodeFrame(POST)); post.set("current_focus", focus()); n.set("post_observation", post); return n;
    }
    private static RawJson raw(JsonNode node) { return new RawJson(StrictJson.canonical(node)); }
    private static JsonNode python(String script, String... arguments) throws Exception {
        var command = new java.util.ArrayList<String>(); command.add(required("xar.python")); command.add("-B"); command.add("-c"); command.add(script); command.addAll(List.of(arguments));
        ProcessBuilder builder = new ProcessBuilder(command); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.redirectErrorStream(true); Process process = builder.start();
        if (!process.waitFor(30, TimeUnit.SECONDS)) { process.destroyForcibly(); throw new AssertionError("original production child-focus parser timed out"); }
        byte[] output = process.getInputStream().readNBytes(65_537); assertEquals(0, process.exitValue(), new String(output, StandardCharsets.UTF_8)); assertTrue(output.length <= 65_536); return StrictJson.parse(output);
    }
    private static void verifyPins() throws Exception { for (Pin pin : PINS) { byte[] body = Files.readAllBytes(repository().resolve(pin.path())); assertEquals(pin.bytes(), body.length, pin.path()); assertEquals(pin.sha256(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)), pin.path()); } }
    private static Path repository() { return Path.of(required("xar.repository.root")).toAbsolutePath().normalize(); }
    private static String required(String key) { String value = System.getProperty(key); assertNotNull(value, "required CI property: " + key); assertFalse(value.isBlank(), "required CI property: " + key); return value; }
}

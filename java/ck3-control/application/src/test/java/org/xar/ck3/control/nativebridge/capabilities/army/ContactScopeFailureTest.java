package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;

/** Original two-query errors remain typed DATA; none of these fixtures grants a current lease or Native qualification. */
final class ContactScopeFailureTest {
    @Test void publicStaleChecksKeepTheTwoOriginalProfilesAndExactUnsignedRevisions() {
        BigInteger expected = new BigInteger("18446744073709551615"), current = expected.subtract(BigInteger.ONE);
        for (ContactScopeObservation.Query query : queries()) {
            ContactScopeFailure.requireExpectedRevision(query, current, current);
            ContactScopeFailure failure = assertThrows(ContactScopeFailure.class,
                    () -> ContactScopeFailure.requireExpectedRevision(query, expected, current));
            assertSame(query, failure.query());
            assertEquals(ContactScopeFailure.Kind.PRE_SUBMISSION_REVISION_MISMATCH, failure.kind());
            assertEquals(query instanceof ContactScopeObservation.Projected ? "projected-contact source revision is stale"
                    : "native gameplay revision mismatch: expected " + expected + ", current " + current, failure.getMessage());
            assertTrue(failure.unavailable().isEmpty()); assertTrue(failure.original().isEmpty());
        }
    }

    @Test void actualIoAndUnclassifiedNativeOriginalsStayDifferentWithoutTimeoutInference() {
        for (ContactScopeObservation.Query query : queries()) {
            IOException original = new IOException("actual current Root observation is unavailable");
            ContactScopeFailure io = ContactScopeFailure.fromIo(query, original);
            assertSame(original, io.getCause()); assertSame(query, io.query());
            assertEquals(ContactScopeFailure.Kind.BRIDGE_UNAVAILABLE, io.kind()); assertEquals(original.getMessage(), io.getMessage());
            var unknown = new NativeActionPort.Unknown("q", "actual transport write interrupted", new byte[]{1}, Optional.empty());
            var unavailable = unavailable(unknown);
            var failure = ContactScopeFailure.from(query, unavailable);
            assertSame(unavailable, failure.unavailable().orElseThrow()); assertSame(unknown, failure.original().orElseThrow());
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, failure.kind());
            assertEquals(unknown.reason(), failure.getMessage()); assertFalse(failure.getMessage().contains("timed out"));
            assertEquals(unavailable.reason(), failure.sourceReason());
            var absent = new PlanningReadResult.Unavailable<ContactScopeObservation>("actual guard returned unavailable", Optional.empty());
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, ContactScopeFailure.from(query, absent).kind());
        }
    }

    @Test void onlyBoundActualFalseTopAndItsExactContactRequestCanClaimOriginalNativeRejection() {
        for (ContactScopeObservation.Query query : queries()) {
            ObjectNode request = request(query), top = top();
            var ack = ack(request, top);
            var unavailable = unavailable(ack);
            ContactScopeFailure failure = ContactScopeFailure.from(query, unavailable);
            assertEquals(ContactScopeFailure.Kind.NATIVE_COMMAND_REJECTED, failure.kind());
            assertEquals("native gameplay step failed: original native refusal", failure.getMessage());
            assertSame(ack, failure.original().orElseThrow()); assertSame(unavailable, failure.unavailable().orElseThrow());
            for (String bad : List.of("query", "request", "protocol_bool", "revision_float", "ok_integer", "packet", "typed")) {
                ObjectNode changedRequest = request.deepCopy(), changedTop = top.deepCopy();
                switch (bad) {
                    case "query" -> changedRequest.put("step", "query-unrelated-v1");
                    case "request" -> changedTop.put("request_id", "other");
                    case "protocol_bool" -> changedTop.put("protocol_version", true);
                    case "revision_float" -> changedRequest.put("expected_revision", 1.0);
                    case "ok_integer" -> changedTop.put("ok", 0);
                    case "typed" -> changedTop.putObject("typed_query_failure_v1").put("reason", "domain profile required");
                    case "packet" -> { }
                    default -> throw new AssertionError(bad);
                }
                var changed = ack(changedRequest, changedTop);
                if (bad.equals("packet")) {
                    byte[] damaged = changed.originalPacket(); damaged[damaged.length - 1] ^= 1;
                    changed = new NativeActionPort.AckReceived("q", false, Optional.empty(), changed.originalFrame(), damaged, changed.outbound());
                }
                var rejected = ContactScopeFailure.from(query, unavailable(changed));
                assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, rejected.kind(), bad);
                assertSame(changed, rejected.original().orElseThrow(), bad);
            }
        }
    }

    @Test void onlyActualResponseDeadlineCauseGetsOriginalTimeoutWhileOtherUnknownsKeepTheirCause() {
        for (ContactScopeObservation.Query query : queries()) {
            byte[] outbound = packet(request(query).toString().getBytes(StandardCharsets.UTF_8));
            var timedOut = new NativeActionPort.Unknown("q", "opaque actual provider diagnostic", outbound, Optional.empty(),
                    Optional.of(cause(NativeActionPort.FailureKind.DEADLINE_EXPIRED, NativeActionPort.FailureStage.RESPONSE_WAIT)));
            var unavailable = unavailable(timedOut);
            var failure = ContactScopeFailure.from(query, unavailable);
            assertEquals(ContactScopeFailure.Kind.BRIDGE_UNAVAILABLE, failure.kind());
            assertEquals("native command_result timed out for gameplay step " + query.step(), failure.getMessage());
            assertSame(timedOut, failure.original().orElseThrow()); assertSame(unavailable, failure.unavailable().orElseThrow());
            assertEquals("actual unavailable read source reason", failure.sourceReason());
            for (NativeActionPort.FailureKind kind : NativeActionPort.FailureKind.values()) {
                if (kind == NativeActionPort.FailureKind.DEADLINE_EXPIRED) continue;
                var original = new NativeActionPort.Unknown("q", "source reason has timed out text without timeout proof", outbound, Optional.empty(),
                        Optional.of(cause(kind, NativeActionPort.FailureStage.RESPONSE_WAIT)));
                var unclassified = ContactScopeFailure.from(query, unavailable(original));
                assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, unclassified.kind(), kind.name());
                assertEquals(original.reason(), unclassified.getMessage()); assertSame(original, unclassified.original().orElseThrow());
            }
            var writeDeadline = new NativeActionPort.Unknown("q", "actual write deadline", outbound, Optional.empty(),
                    Optional.of(cause(NativeActionPort.FailureKind.DEADLINE_EXPIRED, NativeActionPort.FailureStage.WRITE)));
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, ContactScopeFailure.from(query, unavailable(writeDeadline)).kind());
            ObjectNode other = request(query).put("step", "query-unrelated-v1");
            var wrongQuery = new NativeActionPort.Unknown("q", "actual foreign response deadline", packet(other.toString().getBytes(StandardCharsets.UTF_8)),
                    Optional.empty(), timedOut.failureCause());
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, ContactScopeFailure.from(query, unavailable(wrongQuery)).kind());
        }
    }

    @Test void realOriginalBothContactPrimitivesAndServiceStaleMatchWithoutDispatchReplay() throws Exception {
        ObjectNode originals = originalFaults();
        for (ContactScopeObservation.Query query : queries()) {
            ObjectNode row = (ObjectNode) originals.get(query instanceof ContactScopeObservation.Projected ? "projected" : "actual");
            ObjectNode refusal = (ObjectNode) row.get("refusal");
            assertEquals(1, refusal.get("requests").size());
            var ack = ack((ObjectNode) refusal.get("requests").get(0), (ObjectNode) refusal.get("top"));
            var failure = ContactScopeFailure.from(query, unavailable(ack));
            assertEquals("_NativeCommandRejectedError", refusal.get("type").textValue());
            assertEquals(refusal.get("message").textValue(), failure.getMessage());
            ObjectNode timeout = (ObjectNode) row.get("timeout");
            assertEquals("BridgeUnavailableError", timeout.get("type").textValue(), "Contact uses the ordinary original timeout class");
            assertEquals("native command_result timed out for gameplay step " + query.step(), timeout.get("message").textValue());
            assertEquals(1, timeout.get("requests").size(), "actual original unknown result is never submitted twice");
            ObjectNode originalRequest = (ObjectNode) timeout.get("requests").get(0);
            var timedOut = new NativeActionPort.Unknown(originalRequest.get("request_id").textValue(), "actual provider opaque deadline diagnostic",
                    packet(originalRequest.toString().getBytes(StandardCharsets.UTF_8)), Optional.empty(),
                    Optional.of(cause(NativeActionPort.FailureKind.DEADLINE_EXPIRED, NativeActionPort.FailureStage.RESPONSE_WAIT)));
            var javaTimeout = ContactScopeFailure.from(query, unavailable(timedOut));
            assertEquals(ContactScopeFailure.Kind.BRIDGE_UNAVAILABLE, javaTimeout.kind());
            assertEquals(timeout.get("message").textValue(), javaTimeout.getMessage());
            ObjectNode stale = (ObjectNode) row.get("stale");
            var staleFailure = assertThrows(ContactScopeFailure.class, () -> ContactScopeFailure.requireExpectedRevision(query,
                    stale.get("expected").bigIntegerValue(), stale.get("current").bigIntegerValue()));
            assertEquals("PreSubmissionRevisionMismatchError", stale.get("type").textValue());
            assertEquals(stale.get("message").textValue(), staleFailure.getMessage()); assertEquals(0, stale.get("requests").size());
        }
    }

    private static List<ContactScopeObservation.Query> queries() {
        return List.of(new ContactScopeObservation.Projected(new ProjectedContactPolicy.QueryKey(0, 31, 30)),
                new ContactScopeObservation.Actual(new ActualContactModel.Query(0, 31)));
    }
    private static PlanningReadResult.Unavailable<ContactScopeObservation> unavailable(NativeActionPort.DispatchOutcome original) {
        return new PlanningReadResult.Unavailable<>("actual unavailable read source reason", Optional.of(original));
    }
    private static ObjectNode request(ContactScopeObservation.Query query) {
        return StrictJson.object().put("type", "execute_step").put("protocol_version", 1).put("request_id", "q")
                .put("step", query.step()).put("expected_revision", new BigInteger("18446744073709551615"));
    }
    private static ObjectNode top() {
        return StrictJson.object().put("type", "command_result").put("protocol_version", 1).put("request_id", "q").put("ok", false).put("error", "original native refusal");
    }
    private static NativeActionPort.AckReceived ack(ObjectNode request, ObjectNode top) {
        String requestId = request.path("request_id").textValue();
        byte[] body = top.toString().getBytes(StandardCharsets.UTF_8);
        return new NativeActionPort.AckReceived(requestId, false, Optional.empty(), new RawJson(body), packet(body),
                Optional.of(new NativeActionPort.OutboundPacket(requestId, packet(request.toString().getBytes(StandardCharsets.UTF_8)))));
    }
    private static byte[] packet(byte[] body) { return ByteBuffer.allocate(body.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array(); }
    private static NativeActionPort.FailureCause cause(NativeActionPort.FailureKind kind, NativeActionPort.FailureStage stage) {
        Optional<NativeActionPort.OriginalException> original = kind == NativeActionPort.FailureKind.FRAME_BUDGET_EXHAUSTED
                ? Optional.empty() : Optional.of(NativeActionPort.OriginalException.from(new IOException("controlled actual exception diagnostic")));
        Optional<NativeActionPort.DeadlineObservation> deadline = kind == NativeActionPort.FailureKind.DEADLINE_EXPIRED
                ? Optional.of(new NativeActionPort.DeadlineObservation(Instant.parse("2030-01-01T00:00:00Z"), Instant.parse("2030-01-01T00:00:01Z"), false))
                : Optional.empty();
        return new NativeActionPort.FailureCause(kind, stage, original, Optional.empty(), deadline);
    }

    private static ObjectNode originalFaults() throws Exception {
        Path root = required("xar.repository.root"), python = required("xar.python"); verify(root);
        String code = """
import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'ck3_autonomous_player'/'tests'/'unit'),str(root/'ck3_autonomous_player'/'src')]
from test_native_bridge_driver import FakeEndpoint,_hello,_snapshot
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.projected_contact_contract import query_projected_contact_scope_v1_step,QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY
from xar_autoplayer.bridge.actual_contact_contract import query_actual_contact_scope_step,QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY
rows={}
for name,step,cap in [('projected',query_projected_contact_scope_v1_step(0,31,30),QUERY_PROJECTED_CONTACT_SCOPE_V1_CAPABILITY),
                      ('actual',query_actual_contact_scope_step(0,31),QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY)]:
 row={}
 for mode in ('refusal','timeout','stale'):
  endpoint=FakeEndpoint();driver=NativeHeadlessGameplayDriver(endpoint.pipe_name,endpoint=endpoint,state_dir=None,command_timeout_seconds=0.001)
  hello=_hello('game.state.snapshot',cap)
  hello.update(bridge_version='0.1.0.4',expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256,connection_generation=23)
  endpoint.publish(hello);endpoint.publish(_snapshot(40,played_character={'character_id':707,'alive':True}))
  before=driver.take_snapshot();endpoint.frames.clear();received=[]
  def send(request):
   if mode=='refusal':
    top={'type':'command_result','protocol_version':1,'request_id':request['request_id'],'ok':False,'error':'原生 Contact refusal'}
    received.append(top);endpoint.publish(top)
  endpoint.send_hook=send;current=before['revision'];expected=current+1 if mode=='stale' else current
  try:
   if mode=='stale' and name=='projected':
    service=SimpleNamespace(snapshot=lambda:before)
    GameplayBridgeService.query_projected_contact_scope_v1(service,0,31,30,expected_revision=expected)
   else:driver._execute_primitive_step(step,expected_revision=expected,required_capability=cap)
   raise RuntimeError('actual original fault path unexpectedly returned')
  except Exception as error:
   value={'type':type(error).__name__,'message':str(error),'requests':endpoint.frames,'expected':expected,'current':current}
   if received:value['top']=received[0]
   row[mode]=value
  finally:driver.close()
 rows[name]=row
print(json.dumps(rows,ensure_ascii=False,allow_nan=False))
""";
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", code, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); Process process = builder.start();
        FutureTask<byte[]> out = new FutureTask<>(() -> process.getInputStream().readNBytes(65_537));
        FutureTask<byte[]> err = new FutureTask<>(() -> process.getErrorStream().readNBytes(16_385));
        Thread.ofVirtual().start(out); Thread.ofVirtual().start(err); process.getOutputStream().close();
        try {
            if (!process.waitFor(40, TimeUnit.SECONDS)) throw new IllegalStateException("original Contact fault producer timed out");
            byte[] output = out.get(5, TimeUnit.SECONDS), errors = err.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || output.length > 65_536 || errors.length > 16_384)
                throw new IllegalStateException("actual original Contact fault producer failed: " + new String(errors, StandardCharsets.UTF_8));
            verify(root); JsonNode value = StrictJson.parse(output); assertInstanceOf(ObjectNode.class, value); return (ObjectNode) value;
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS); } }
    }
    private static Path required(String property) throws Exception {
        String value = System.getProperty(property); if (value == null || value.isBlank()) throw new IllegalStateException("required actual original source property missing: " + property);
        Path path = Path.of(value); if (!path.isAbsolute()) throw new IllegalArgumentException("absolute actual source path required"); return path.toRealPath();
    }
    private static void verify(Path root) throws Exception {
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
            {"ck3_autonomous_player/tests/unit/test_native_bridge_driver.py", "4cf26ef6804ba46b7e8d1f3ef5aeaffafab136e7ee4f0b3a45462906dcdc1f99"}
        };
        for (String[] pin : pins) { Path source = root.resolve(pin[0]).toRealPath(); assertTrue(source.startsWith(root));
            assertEquals(pin[1], java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))), "original Contact producer source drift"); }
    }
}

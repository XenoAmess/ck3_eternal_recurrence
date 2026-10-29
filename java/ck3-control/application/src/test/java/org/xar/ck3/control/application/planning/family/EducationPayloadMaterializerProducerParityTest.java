package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Original Python producer -> strict Java request -> shared review -> full materialization projection. */
final class EducationPayloadMaterializerProducerParityTest {
    @Test void completeOriginalMaterializationAndFreshTokenFrameBindingMatch() throws Exception {
        Obj capture = original(); assertEquals(t("xar.java.education-materializer-original/v1"), capture.get("schema"));
        assertEquals(3, array(capture.get("cases")).size()); int available = 0;
        for (Value value : array(capture.get("cases"))) {
            Obj sample = object(value), query = object(sample.get("query")), snapshot = object(sample.get("snapshot"));
            if (sample.get("result") == Nil.INSTANCE) {
                Obj intent = object(sample.get("intent"));
                assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.prepareAndMaterialize("ordinary-parity", query, snapshot,
                        integer(intent.get("recipient_id")).longValueExact(), integer(intent.get("child_full_id")).longValueExact(), integer(intent.get("guardian_full_id")).longValueExact(),
                        array(intent.get("requested_option_keys")).stream().map(FamilyJson::text).toList()));
                continue;
            }
            available++; var request = EducationPayloadMaterializer.readRequest(object(sample.get("request")));
            var actual = EducationPayloadMaterializer.materialize(request, query, snapshot);
            assertEquals(sample.get("result"), actual.projection());
            assertEquals(actual.projection(), decodeDomain(bytes(actual.projection())), "complete JSON type-domain roundtrip");
            assertFalse(yes(actual.projection().get("dispatch_ready"))); assertFalse(yes(actual.projection().get("material_result")));
            assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.materialize(new EducationPayloadMaterializer.Request(request.requestId(),
                    "0".repeat(64), request.snapshotId(), request.publicRevision(), request.nativeRevision(), request.recipient(), request.child(), request.guardian(), request.optionKeys()), query, snapshot));
            assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.materialize(request, query,
                    snapshot.with("revision", new IntegerValue(request.publicRevision().add(java.math.BigInteger.ONE)))));
        }
        assertTrue(available > 0, "actual retained corpus must exercise materialization rather than only rejections");
    }
    @Test void reviewedRequestBoundaryRejectsExactTypeAndFieldDrift() {
        Obj request = obj("schema", t(EducationPayloadMaterializer.REQUEST_SCHEMA), "request_id", t("ordinary-boundary"), "review_token", t("a".repeat(64)),
                "expected_snapshot_id", t("native:23"), "expected_revision", n(31), "expected_native_revision", n(23), "recipient_id", n(1),
                "child_full_id", n(1), "guardian_full_id", n(2), "requested_option_keys", rows(java.util.List.of()));
        assertEquals(request, EducationPayloadMaterializer.readRequest(request).toJson());
        assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.readRequest(request.with("child_full_id", new Bool(true))));
        assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.readRequest(request.with("expected_revision", new DecimalValue("31.0"))));
        assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.readRequest(request.with("requested_option_keys", Nil.INSTANCE)));
        assertThrows(IllegalArgumentException.class, () -> EducationPayloadMaterializer.readRequest(request.with("extra", n(1))));
    }
    private static Obj original() throws Exception {
        Path repository = Path.of(required("xar.repository.root")).toRealPath(), python = Path.of(required("xar.python")).toRealPath();
        assertTrue(repository.isAbsolute() && Files.isRegularFile(python), "actual original repository/interpreter binding required");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-I", "-u", "-", repository.toString());
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("PYTHONUTF8", "1");
        Process process = builder.start();
        try (var workers = Executors.newVirtualThreadPerTaskExecutor()) {
            var out = workers.submit(() -> read(process.getInputStream(), 2 << 20));
            var err = workers.submit(() -> read(process.getErrorStream(), 16 << 10));
            try (var input = process.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS); throw new IllegalStateException("original materializer timed out; NOT EXECUTED"); }
            byte[] raw = out.get(10, TimeUnit.SECONDS), error = err.get(10, TimeUnit.SECONDS);
            assertEquals(0, process.exitValue(), new String(error, StandardCharsets.UTF_8)); assertEquals(0, error.length);
            return decodeDomain(raw);
        } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(10, TimeUnit.SECONDS); } }
    }
    private static byte[] read(java.io.InputStream stream, int maximum) throws IOException {
        byte[] raw = stream.readNBytes(maximum + 1); if (raw.length > maximum) throw new IOException("bounded original producer output"); return raw;
    }
    private static String required(String property) {
        String value = System.getProperty(property); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: required " + property); return value;
    }
    private static final String SCRIPT = """
import sys,json,pathlib,hashlib
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
names=['ck3_autonomous_player/src/xar_autoplayer/bridge/education_payload_materializer_private_v1.py','ck3_autonomous_player/tests/fixtures/family_guardian_p43_completed_projection_v1.json']
expected=[(12006,'75afb2ca71bf156975e4bc19b08bb1c03f283b39b2547ee070664f2df22bf60e'),(152325,'329d2d7ad78b9e0122ec5c55cf2fc9f63dff1da77891387a5133403140a569db')]
before={name:(root/name).read_bytes() for name in names}
for name,(size,sha) in zip(names,expected):
 raw=before[name]
 if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError('original input drift: '+name)
from xar_autoplayer.bridge.education_payload_materializer_private_v1 import prepare_education_payload_review_v1,materialize_reviewed_education_payload_v1,REQUEST_SCHEMA
cases=[]
for sample in json.loads(before[names[1]])['rows']:
 frame=sample['planning_source_frame'];query=sample['family_education_observations'][0]['request_attempts'][0]['query'];native=query['character_interaction_ordinary_context'];roles=native['effective_roles']
 snapshot={**frame,'played_character':{'character_id':frame['actor_character_id'],'alive':True},'paused':True,'map_ready':True,'active_wars':[],'active_event':None,'pending_character_interaction':None,'one_life_terminal_reason':None,'diagnostics':{'connected':True,'bridge_pid':frame['bridge_pid'],'connection_generation':frame['connection_generation'],'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':native['executable_sha256'],'ck3_build_match':True,'game_adapter_id':'ck3-1.20.0.4-msvc-x64','pid':frame['bridge_pid']}}}
 keys=list(dict.fromkeys(row['canonical_flag_key'] for row in native['education_option_rows']['rows'] if row['ordinal_selected']))
 intent={'recipient_id':native['recipient_id'],'child_full_id':roles['secondary_recipient_id'],'guardian_full_id':roles['secondary_actor_id'],'requested_option_keys':keys}
 review=prepare_education_payload_review_v1(query,snapshot,expected_revision=frame['revision'],**intent)
 request=None;result=None
 if review['status']=='available':
  request={'schema':REQUEST_SCHEMA,'request_id':'ordinary-parity','review_token':review['review_token'],'expected_snapshot_id':query['queried_snapshot_id'],'expected_revision':frame['revision'],'expected_native_revision':query['queried_native_revision'],**intent}
  result=materialize_reviewed_education_payload_v1(request,query,snapshot)
 cases.append({'snapshot':snapshot,'query':query,'intent':intent,'request':request,'result':result})
for name,raw in before.items():
 if (root/name).read_bytes()!=raw:raise RuntimeError('original input changed during capture')
sys.stdout.buffer.write((json.dumps({'schema':'xar.java.education-materializer-original/v1','cases':cases},ensure_ascii=False,separators=(',',':'),allow_nan=False)+chr(10)).encode('utf-8'))
""";
}

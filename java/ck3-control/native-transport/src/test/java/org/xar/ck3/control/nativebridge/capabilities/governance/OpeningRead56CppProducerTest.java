package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads.OpeningReadProfile;

/** Cold reads of separately pinned C++ originals. No wrapper, owner ticket or live authority is manufactured. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.opening56.cases.path",matches=".+")
final class OpeningRead56CppProducerTest {
    private static byte[] original(ExactRef ref)throws Exception {
        byte[] raw=Files.readAllBytes(Path.of(ref.path()));assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));return raw;
    }
    private static ObjectNode cases()throws Exception {
        var ref=new ExactRef(System.getProperty("xar.opening56.cases.path"),Long.parseLong(System.getProperty("xar.opening56.cases.bytes")),System.getProperty("xar.opening56.cases.sha256"));
        return StrictJson.object(StrictJson.parse(original(ref)),Set.of("schema","dll","data","route_refusals"));
    }
    private static OpeningReadProfile profile(ObjectNode cases) {
        var dll=ExactRef.fromJson(cases.get("dll"));
        return OpeningReadProfile.selectQualified(OpeningReadProfile.VERSION,OpeningReadProfile.EXECUTABLE,dll).orElseThrow();
    }
    private static OpeningReadProfile.Frame independentFull(ExactRef ref)throws Exception {
        var frame=StrictJson.object(StrictJson.parse(original(ref)),Set.of("type","protocol_version","snapshot_id","revision","read_request_id","state"));
        assertEquals("state_snapshot",StrictJson.text(frame.get("type")));assertEquals(1,StrictJson.integer(frame.get("protocol_version"),1,1));
        var state=CouncilCodec.object(frame.get("state"));assertEquals("ck3_1210_full_state_v1",StrictJson.text(state.get("schema")));
        assertEquals(OpeningReadProfile.ADAPTER,StrictJson.text(state.get("adapter_id")));assertEquals(OpeningReadProfile.VERSION,StrictJson.text(state.get("game_version")));
        assertEquals(OpeningReadProfile.EXECUTABLE,StrictJson.text(state.get("executable_sha256")));
        StrictJson.trueValue(state.get("paused"));StrictJson.trueValue(state.get("map_ready"));
        var actor=CouncilCodec.object(state.get("played_character"));StrictJson.trueValue(actor.get("alive"));
        assertEquals(OpeningReadProfile.ADAPTER,StrictJson.text(actor.get("adapter_id")));assertEquals(OpeningReadProfile.EXECUTABLE,StrictJson.text(actor.get("executable_sha256")));
        var expected=new OpeningReadProfile.Frame(frame.get("revision").bigIntegerValue(),state.get("date_raw").bigIntegerValue(),actor.get("character_id").bigIntegerValue());
        assertEquals(expected.snapshotId(),StrictJson.text(frame.get("snapshot_id")));return expected;
    }
    @Test void actualCppDataStaysBoundToIndependentFullAndKeepsOfflineOrigin()throws Exception {
        var index=cases();var profile=profile(index);int availableScope=0,availableCurrent=0,unavailable=0;
        for(var item:index.get("data")) {
            var row=StrictJson.object(item,Set.of("kind","full","data","command","request","request_id","status"));
            var kind=OpeningReadProfile.Kind.valueOf(StrictJson.text(row.get("kind")));
            var request=StrictJson.object(StrictJson.parse(original(ExactRef.fromJson(row.get("request")))),Set.of("type","protocol_version","request_id","step","expected_revision"));
            assertEquals("execute_step",StrictJson.text(request.get("type")));assertEquals(1,StrictJson.integer(request.get("protocol_version"),1,1));
            assertEquals(kind.step(),StrictJson.text(request.get("step")));assertEquals(StrictJson.text(row.get("request_id")),StrictJson.text(request.get("request_id")));
            RawJson raw=new RawJson(original(ExactRef.fromJson(row.get("data"))));
            var data=profile.decodeData(kind,raw,independentFull(ExactRef.fromJson(row.get("full"))));
            assertEquals(independentFull(ExactRef.fromJson(row.get("full"))).nativeRevision(),request.get("expected_revision").bigIntegerValue());
            assertArrayEquals(raw.bytes(),data.original().bytes());assertEquals(StrictJson.text(row.get("status")).equals("available"),data.available());
            var command=StrictJson.object(StrictJson.parse(original(ExactRef.fromJson(row.get("command")))),Set.of("type","protocol_version","request_id","ok","result"));
            assertEquals("command_result",StrictJson.text(command.get("type")));assertEquals(1,StrictJson.integer(command.get("protocol_version"),1,1));
            assertEquals(StrictJson.text(row.get("request_id")),StrictJson.text(command.get("request_id")));StrictJson.trueValue(command.get("ok"));
            assertEquals(StrictJson.parse(raw.bytes()),command.get("result"));
            assertThrows(IllegalArgumentException.class,data::requireApplicationMainOrigin);
            assertFalse(data.origin().mainOwnerObserved());
            if(data.available()) {
                assertEquals(OpeningReadProfile.SourceKind.OFFLINE_FIXTURE,data.origin().kind());
                if(kind==OpeningReadProfile.Kind.SCOPE){availableScope++;assertTrue(data.government().isPresent());}
                else{availableCurrent++;assertTrue(data.progress().orElseThrow().present());}
            }else{unavailable++;assertTrue(data.frame().isEmpty());assertTrue(data.government().isEmpty());assertTrue(data.progress().isEmpty());assertTrue(data.unavailableReason().isPresent());}
        }
        assertTrue(availableScope>0&&availableCurrent>0&&unavailable>0,"actual producer positive scope/current and typed unavailable originals required");
    }
    @Test void actualRouteRefusalsNeverBecomeTypedAvailability()throws Exception {
        var index=cases();int count=0;
        for(var item:index.get("route_refusals")) {
            var row=StrictJson.object(item,Set.of("command","request_id"));
            var command=StrictJson.object(StrictJson.parse(original(ExactRef.fromJson(row.get("command")))),Set.of("type","protocol_version","request_id","ok","error"));
            assertEquals("command_result",StrictJson.text(command.get("type")));assertEquals(1,StrictJson.integer(command.get("protocol_version"),1,1));
            assertEquals(StrictJson.text(row.get("request_id")),StrictJson.text(command.get("request_id")));assertFalse(CouncilCodec.bool(command.get("ok")));
            assertFalse(command.has("result"));assertNotNull(command.get("error"));count++;
        }
        assertTrue(count>0,"real C++ route refusal originals required");
    }
}

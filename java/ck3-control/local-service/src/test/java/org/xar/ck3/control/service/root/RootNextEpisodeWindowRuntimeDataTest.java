package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Real helper DATA producer -> persisted codecs/reducer. No authority, Stage, SAVE or Game is minted here. */
final class RootNextEpisodeWindowRuntimeDataTest {
    @TempDir Path temporary;

    @Test void actualDescriptorProducerPersistsAllOriginalSourcesAndFullWidthIdentity()throws Exception {
        var lifecycle=pin("00000008.json","original-lifecycle");
        var driver=ref("adopted-driver.json","complete-adopted-driver");
        var semantic=ref("opening-semantic.json","actual-semantic");
        var input=data(lifecycle,driver,List.of(semantic));
        var descriptor=RootNextEpisodeWindowRuntime.describeBegin(input);
        Path file=temporary.resolve("begin.json");Files.write(file,ContinuityJson.canonical(descriptor.toJson()));
        var replay=EpisodeWindow.Begin.fromJson(ContinuityJson.parseObject(Files.readAllBytes(file),65536));
        assertEquals(descriptor,replay);assertEquals(descriptor.request().identity(),EpisodeWindow.begin(replay.request()).request().identity());
        assertEquals(List.of(semantic,lifecycle.reference(),driver),replay.request().evidence());
        var committed=new EpisodeWindow.CommittedBegin(replay,9,replay.request().identity(),"c".repeat(64),pin("00000009.json","actual-begin-data"));
        Path proof=temporary.resolve("committed-begin.json");Files.write(proof,ContinuityJson.canonical(committed.toJson()));
        var roundtrip=EpisodeWindow.CommittedBegin.fromJson(ContinuityJson.parseObject(Files.readAllBytes(proof),65536));
        assertEquals(committed,roundtrip);
        assertEquals("134055108000000017",roundtrip.begin().after().toJson().path("game").path("creation_filetime").textValue());
        assertEquals("18446744073709551615",roundtrip.eventPin().identity().fileIdDecimal());
        assertEquals("134055108000000019",roundtrip.eventPin().identity().creationFiletimeDecimal());
    }

    @Test void helperProducedDescriptorRunsWholeReducerWithoutErasingUnknownPendingOrInventingCycles()throws Exception {
        var descriptor=RootNextEpisodeWindowRuntime.describeBegin(data(pin("00000008.json","lifecycle"),ref("driver.json","driver"),List.of()));
        var before=state();var waiting=EpisodeWindow.reduce(before,descriptor.request());
        assertEquals(ContinuityState.Status.AWAITING_FIRST_SAVE,waiting.status());
        assertEquals(before.origin(),waiting.origin());assertEquals(before.settledCycles(),waiting.settledCycles());
        assertEquals(before.toJson().get("UNKNOWN"),waiting.toJson().get("UNKNOWN"));
        assertTrue(waiting.toJson().has("pending_cycle"));assertTrue(waiting.toJson().get("pending_cycle").isNull());
        var committed=new EpisodeWindow.CommittedBegin(descriptor,9,descriptor.request().identity(),"c".repeat(64),pin("00000009.json","begin"));
        var pair=ref("pair.json","pair-data-only");
        var baseline=new EpisodeWindow.Baseline(committed,"actual-save-id-data",pair,pair.sha256(),ref("save.json","receipt-data-only"),"d".repeat(64),descriptor.after());
        Path packet=temporary.resolve("baseline.json");Files.write(packet,ContinuityJson.canonical(baseline.toJson()));
        var replay=EpisodeWindow.Baseline.fromJson(ContinuityJson.parseObject(Files.readAllBytes(packet),65536));
        var active=EpisodeWindow.reduce(waiting,replay.request());
        assertEquals(8,active.origin().windowId());assertEquals(500,active.origin().startDateRaw());assertEquals(0,active.settledCycles());
        for(String retained:List.of("UNKNOWN","NEXT","pending_cycle","unknown_requests","empty_collection"))
            assertEquals(before.toJson().get(retained),active.toJson().get(retained),retained);
        assertEquals(pair,EpisodeWindow.requireActive(active).baseline().orElseThrow().pairRef());
        assertFalse(active.toJson().has("completed_cycle_proof"));
    }

    @Test void eventSelectionRejectsMissingWrongSequenceAndAmbiguousPhysicalSources() {
        var actual=pin("00000008.json","original");
        assertSame(actual,RootNextEpisodeWindowRuntime.eventPin(List.of(actual),8));
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.eventPin(List.of(actual),9));
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.eventPin(List.of(),8));
        var duplicate=pin("another-directory/00000008.json","different-physical-source");
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.eventPin(List.of(actual,duplicate),8));
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.describeBegin(data(pin("00000007.json","wrong-event"),ref("driver.json","driver"),List.of())));
    }

    @Test void actualProducerRejectsAnotherEpochGameAndDuplicateEvidenceBeforeAnyAuthorityExists() {
        var input=data(pin("00000008.json","lifecycle"),ref("driver.json","driver"),List.of());
        var sameGame=new EpisodeWindow.Identity(input.after().machineId(),input.before().game(),input.after().sessionId(),input.after().episodeRunId(),
                input.after().epoch(),input.after().actorId(),input.after().dateRaw());
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.describeBegin(new RootNextEpisodeWindowRuntime.DescriptorData(
                input.before(),sameGame,input.oldWindowId(),input.parentActionId(),input.lifecycleSequence(),input.lifecycleIdentity(),input.lifecycleEvent(),input.adoptedDriver(),List.of())));
        var reusedPid=identity(41,"134055108000000017","new","new-episode",8,74,500);
        var distinct=RootNextEpisodeWindowRuntime.describeBegin(new RootNextEpisodeWindowRuntime.DescriptorData(input.before(),reusedPid,
                input.oldWindowId(),input.parentActionId(),input.lifecycleSequence(),input.lifecycleIdentity(),input.lifecycleEvent(),input.adoptedDriver(),List.of()));
        assertEquals(distinct.before().game().pid(),distinct.after().game().pid());
        assertNotEquals(distinct.before().game(),distinct.after().game(),"PID reuse retains the exact distinct process birth; PID alone is never Game identity");
        var skippedEpoch=new EpisodeWindow.Identity(input.after().machineId(),input.after().game(),input.after().sessionId(),input.after().episodeRunId(),
                10,input.after().actorId(),input.after().dateRaw());
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.describeBegin(new RootNextEpisodeWindowRuntime.DescriptorData(
                input.before(),skippedEpoch,input.oldWindowId(),input.parentActionId(),input.lifecycleSequence(),input.lifecycleIdentity(),input.lifecycleEvent(),input.adoptedDriver(),List.of())));
        var source=ref("source.json","same-original");
        assertThrows(IllegalArgumentException.class,()->RootNextEpisodeWindowRuntime.describeBegin(data(input.lifecycleEvent(),input.adoptedDriver(),List.of(source,source))));
    }

    @Test void persistedDescriptorAndPinRejectMissingNullBooleanFloatAndNumericIdentity()throws Exception {
        var descriptor=RootNextEpisodeWindowRuntime.describeBegin(data(pin("00000008.json","lifecycle"),ref("driver.json","driver"),List.of()));
        for(var wrong:List.of(StrictJson.object().put("x",true).get("x"),StrictJson.object().put("x",8.0).get("x"),StrictJson.object().putNull("x").get("x"))){
            var encoded=descriptor.toJson();encoded.set("old_window_id",wrong);
            assertThrows(IllegalArgumentException.class,()->EpisodeWindow.Begin.fromJson(encoded));
        }
        var missing=descriptor.toJson();missing.remove("lifecycle_event_ref");
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.Begin.fromJson(missing));
        var committed=new EpisodeWindow.CommittedBegin(descriptor,9,descriptor.request().identity(),"c".repeat(64),pin("00000009.json","begin"));
        var numeric=committed.toJson();((ObjectNode)numeric.path("event_pin").path("identity")).put("file_id_decimal",123);
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.CommittedBegin.fromJson(numeric));
        var invalid=committed.toJson();((ObjectNode)invalid.path("event_pin").path("identity")).remove("creation_filetime_decimal");
        assertThrows(IllegalArgumentException.class,()->EpisodeWindow.CommittedBegin.fromJson(invalid));
    }

    private static RootNextEpisodeWindowRuntime.DescriptorData data(WriterContracts.Pin lifecycle,ExactRef driver,List<ExactRef> evidence){
        return new RootNextEpisodeWindowRuntime.DescriptorData(identity(41,"134055108000000016","old","old-episode",7,73,1000),
                identity(42,"134055108000000017","new","new-episode",8,74,500),7,"original-next-parent",8,"a".repeat(64),lifecycle,driver,evidence);
    }
    private static EpisodeWindow.Identity identity(long pid,String birth,String session,String episode,long epoch,long actor,long date){
        var row=StrictJson.object();row.put("pid",pid);row.put("creation_filetime",birth);
        return new EpisodeWindow.Identity("fixture-machine",GameGeneration.fromJson(row),session,episode,epoch,actor,date);
    }
    private static ContinuityState state(){
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id","fixture-machine");row.put("sequence",8);
        row.put("window_id",7);row.put("status","running");row.put("target_days",10);row.put("start_date_raw",1000);row.put("target_date_raw",1240);
        row.put("last_settled_date_raw",1024);row.put("last_settled_cycles",1);row.putObject("UNKNOWN").put("original-request","UNKNOWN");
        row.putNull("pending_cycle");row.putObject("NEXT").put("original-next","pending");row.putNull("unknown_requests");row.putArray("empty_collection");
        return ContinuityState.fromJson(row,"fixture-machine");
    }
    private static WriterContracts.Pin pin(String path,String content){
        var ref=ref(path,content);return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("123","18446744073709551615","134055108000000019","2026-10-23T22:55:00Z",ref.bytes()));
    }
    private static ExactRef ref(String path,String body){
        byte[] bytes=body.getBytes(StandardCharsets.UTF_8);return new ExactRef("fixture/"+path,bytes.length,
                org.xar.ck3.control.application.driver.DriverJson.sha256(bytes));
    }
}

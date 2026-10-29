package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.ritecreation.RiteCreationDomainState;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract.EpisodeScope;
import org.xar.ck3.control.application.ritecreation.RiteCreationState;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Real bounded Core/writer/archive DATA. No Game, private fresh proof, Native action or import custody. */
final class RootRiteRetainedBodyReloadTest {
    @TempDir Path directory;

    private ExactRef file(String name,String value)throws IOException {
        Path target=directory.resolve(name);byte[] raw=value.getBytes(StandardCharsets.UTF_8);
        Files.write(target,raw);return new ExactRef(target.toString(),raw.length,ActionCodec.sha256(raw));
    }
    private RootApplicationConfiguration configuration(ExactRef writer)throws IOException {
        String machine=WindowsJobProcess.currentMachineId();
        ObjectNode initial=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",machine)
                .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958)
                .put("target_years",30).put("calendar_year_days",365.25).put("start_date_raw",1000)
                .put("target_date_raw",1000+10958*24).put("last_settled_date_raw",1000).put("last_settled_cycles",1)
                .put("manual_repair_count",1).put("automatic_recovery_count",0).put("binding_lineage_count",0);
        initial.putObject("game_binding").put("pid",121).put("creation_date","2026-10-23T01:00:00Z");
        initial.putNull("latest_binding");initial.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);
        initial.put("NEXT",11559);
        byte[] raw=ContinuityJson.canonical(initial);Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json");
        Path anchor=directory.resolve("anchor.json");Files.write(snapshot,raw);Files.write(anchor,raw);
        Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);
        Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        return new RootApplicationConfiguration(machine,HostMode.HTTP,Instant.now().plusSeconds(3600),
                file("launch-data.json","{\"fixture\":\"no Game launch\"}"),
                new WriterContracts.Layout(snapshot,new ExactRef(anchor.toString(),raw.length,ActionCodec.sha256(raw)),machine),
                List.of(writer),Files.createDirectory(directory.resolve("archive")),16L<<20);
    }

    @Test void retainedActualBodySurvivesProducerReloadWithoutRewriteAndStillRejectsChangedPayload()throws Exception {
        assertTrue(com.sun.jna.Platform.isWindows(),"actual Windows lock and immutable file identity required");
        ExactRef writer=file("writer-source.txt","unchanged canonical writer fixture");
        ExactRef sourceA=file("rite-source-A.txt","Rite business source A");
        ExactRef sourceB=file("rite-source-B.txt","Rite business source B");
        var configuration=configuration(writer);var first=new RootRiteCreationDomain(List.of(sourceA));
        var expected=new RiteCreationDomainState(RiteCreationState.initialize(RiteCreationState.State.empty(),
                new RiteCreationState.Basis(RiteCreationState.Initialization.FRESH,
                        new EpisodeScope("software-retained-episode"),73,List.of(writer))),Optional.empty());
        var storage=StorageWriteGuardTestSupport.create(configuration.ledger());
        try(var original=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(first.registration()),Optional.empty(),storage)) {
            first.bindCore(original);
            DomainBodies.BodyRef retained=original.writer().locked(same->{
                var body=first.publishFull(same,new RawJson("{\"kind\":\"software_rite_retained_body\"}".getBytes(StandardCharsets.UTF_8)),
                        List.of(sourceA),(actual,previous)->{assertTrue(previous.isEmpty());return expected;});
                assertEquals(expected,first.fullState(same));return body;
            });
            assertEquals(List.of(sourceA),retained.producerSources());
            byte[] snapshot=Files.readAllBytes(configuration.ledger().snapshot());
            byte[] payload=Files.readAllBytes(Path.of(retained.payload().path()));
            var reloaded=new RootRiteCreationDomain(List.of(sourceB));
            assertNotEquals(first.registration().producerSources(),reloaded.registration().producerSources());
            try(var current=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(reloaded.registration()),Optional.empty(),storage)) {
                reloaded.bindCore(current);
                current.writer().locked(same->{
                    assertEquals(expected,reloaded.fullState(same),"current code must read the same retained business body produced by A");
                    var available=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.RITE_CREATION));
                    assertEquals(retained,available.reference(),"old producer metadata and native payload identity remain historical data");
                    assertArrayEquals(expected.encode().bytes(),available.canonicalBody());return null;
                });
                assertArrayEquals(snapshot,Files.readAllBytes(configuration.ledger().snapshot()),"reload read cannot re-import or rewrite the canonical body");
                assertArrayEquals(payload,Files.readAllBytes(Path.of(retained.payload().path())));
                assertFalse(Files.exists(configuration.ledger().event(2)),"reload creates no replacement domain import");
                byte[] changed=payload.clone();changed[0]^=1;Files.write(Path.of(retained.payload().path()),changed);
                current.writer().locked(same->{assertThrows(IOException.class,()->reloaded.fullState(same));return null;});
                assertArrayEquals(snapshot,Files.readAllBytes(configuration.ledger().snapshot()));
                assertArrayEquals(changed,Files.readAllBytes(Path.of(retained.payload().path())),"failed read never repairs or replaces changed payload");
            }
        }
    }
}

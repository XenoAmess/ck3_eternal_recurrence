package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.ZoneOffset;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.contracts.StrictJson;

/** Original Python software fixture -> actual Full/Known -> shared original-only replay and journal basis.
 * No ManagedGame/current Root/private token is fabricated. The public Root callback requires whole-Root
 * integration independently; these tests exercise its actual DATA producers and durable consumers. */
final class RootIncidentPendingUiFrameTest {
    @TempDir Path temporary;
    @BeforeAll static void originalInputs()throws Exception{PendingUiEventPreparationTest.originalProducers();}

    @Test void actualSuccessorFrameReplaysIntoObservedJournalBeforeCaptureAndColdReopen()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("pending-journal"),16*1024*1024)){
            disk.writer.locked(same->{
                var archive=disk.archive.withSession(same);var fixture=new PendingUiEventPreparationTest.Inputs(disk,archive,same);
                var actual=fixture.event(true);String head=same.head().digest();
                var rebuilt=RootIncidentRuntime.replayPendingUiOriginal(actual,new DriverFrameEvidenceLoader(new DriverObservationAssembler()),archive);
                assertEquals(actual.frame(),rebuilt);
                var basis=RootIncidentRuntime.originalObservationBasis(rebuilt);var retained=archive.preserveMaterial(basis);
                var binding=new EpisodeIncidentJournal.Binding(rebuilt.identity(),rebuilt.source(),rebuilt.sessionId());
                var configured=configuration(disk.directory,actual,Optional.of(fixture.trusted));
                var journal=EpisodeIncidentJournal.initializeObserved(configured,binding,retained);
                assertEquals(Optional.of(retained),journal.originalObservationBasis());
                assertEquals(actual.frame().identity().frame().episodeRunId(),journal.origin().before().frame().episodeRunId());
                assertEquals(actual.known().driver().session().actorId(),journal.origin().before().frame().identity().player());
                var prepared=fixture.eventPreparation(actual,fixture.eventContext(true),1,"pending-journal-choice");
                var restored=ActionCodec.decodeCommand(ActionCodec.encodeCommand(prepared.command()));assertEquals(prepared.command(),restored);
                assertEquals(prepared.command().operation().value(),EventActionPreparation.prepare(restored).step());
                var ticket=journal.before(restored).orElseThrow();assertTrue(ticket.before().bytes()>0);
                var scan=journal.scan(binding);assertEquals(1,scan.incompleteAfter());assertTrue(scan.batch().isPresent());
                var reopened=EpisodeIncidentJournal.open(configured,binding,journal.episodeReference());
                assertEquals(retained,reopened.originalObservationBasis().orElseThrow());assertEquals(1,reopened.scan(binding).incompleteAfter());
                var original=StrictJson.parse(archive.loadMaterial(retained).bytes(),1<<20);
                assertEquals("xar.java.incident-observation-original/v1",original.path("schema").textValue());
                assertEquals(rebuilt.sessionId(),original.path("session_id").textValue());
                assertEquals(head,same.head().digest(),"journal side evidence must not change the canonical continuity head");
                return null;
            });
        }
    }

    @Test void pendingReplayRejectsAnotherFrameChangedFullBindingAndForeignOriginalDriver()throws Exception {
        try(var disk=new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("pending-negative"),16*1024*1024)){
            disk.writer.locked(same->{
                var archive=disk.archive.withSession(same);var fixture=new PendingUiEventPreparationTest.Inputs(disk,archive,same);
                var actual=fixture.event(true);var later=fixture.next(actual);String head=same.head().digest();
                assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.replayPendingUiOriginal(actual,(basis,source)->later.frame(),archive));
                var frame=actual.frame();var changed=new DriverObservationAssembler.Complete(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),
                        frame.semantic(),frame.originalEvidence(),frame.observedAt(),frame.fullBindingSha256().equals("0".repeat(64))?"1".repeat(64):"0".repeat(64));
                assertThrows(IllegalArgumentException.class,()->RootIncidentRuntime.replayPendingUiOriginal(actual,(basis,source)->changed,archive));
                Path foreign=Files.write(disk.directory.resolve("foreign-driver.json"),actual.known().driver().encode());var calls=new AtomicInteger();
                var crossed=new PendingUiEvent.Current(actual.originalParent(),actual.full(),actual.known(),actual.frame(),EpisodeIncidentJournal.measure(foreign),
                        actual.originalHistoryBasis(),actual.canonicalPublication(),actual.canonicalDomain(),actual.qualifiedCause(),actual.bridgeCapabilities());
                assertThrows(RuntimeException.class,()->RootIncidentRuntime.replayPendingUiOriginal(crossed,(basis,source)->{calls.incrementAndGet();return frame;},archive));
                assertEquals(0,calls.get(),"foreign identical-byte Driver reference must fail before frame replay");
                assertEquals(frame,RootIncidentRuntime.replayPendingUiOriginal(actual,new DriverFrameEvidenceLoader(new DriverObservationAssembler()),archive));
                assertEquals(head,same.head().digest());return null;
            });
        }
    }

    private static EpisodeIncidentJournal.Configuration configuration(Path root,PendingUiEvent.Current actual,
            Optional<org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext> trusted)throws IOException {
        Path incidents=Files.createDirectory(root.resolve("incidents")),scans=Files.createDirectory(root.resolve("scans"));
        return new EpisodeIncidentJournal.Configuration(incidents,scans,Clock.fixed(actual.frame().observedAt(),ZoneOffset.UTC),
                size->{if(size<0||size>(1<<20))throw new IOException("finite software journal output");},trusted);
    }
}

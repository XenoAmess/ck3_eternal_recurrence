package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordingFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;

/** Real finite ledger I/O observations; no Game state or runtime recovery is inferred. */
final class HistoricalHeadSessionReuse165Test {
    @TempDir Path root;

    private WriterFixture history(String name,int count) throws Exception {
        var fixture=new WriterFixture(root.resolve(name));
        fixture.writer.locked(same->{
            for(int index=1;index<=count;index++)
                same.commit(same.preview(WriterFixture.settled("event-"+index,1000+24L*index,1L+index)));
            return null;
        });
        return fixture;
    }

    @Test void repeatedHistoricalHeadsDoNotReopenUnrequestedEvents() throws Exception {
        var fixture=history("io",4);
        byte[] snapshot=Files.readAllBytes(fixture.layout.snapshot());
        Path recording=root.resolve("historical-head-reads.jfr");
        long[] elapsed={0};
        fixture.writer.locked(same->{
            var edge=same.readHistoricalTransition(LedgerFiles.read(fixture.layout.event(1),ContinuityJson.LEDGER_MAX_BYTES).pin());
            String digest=ContinuityJson.digest(edge.after().toJson());
            var original=same.requireHistoricalHead(1,digest);
            try(var events=new Recording()) {
                events.setToDisk(true);
                events.enable("jdk.FileRead").withThreshold(Duration.ZERO).withStackTrace();
                events.start();
                long started=System.nanoTime();
                for(int count=0;count<3;count++) {
                    var again=same.requireHistoricalHead(1,digest);
                    assertEquals(original.state().toJson(),again.state().toJson());
                    assertEquals(original.documents(),again.documents());
                }
                elapsed[0]=System.nanoTime()-started;
                events.stop();events.dump(recording);
            }
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalHead(1,"0".repeat(64)));
            assertThrows(IllegalArgumentException.class,()->same.requireHistoricalHead(5,digest));
            return null;
        });
        long reads=0,bytes=0,unrequested=0;var details=new ArrayList<String>();
        try(var events=new RecordingFile(recording)) {
            while(events.hasMoreEvents()) {
                var event=events.readEvent();
                if(!event.getEventType().getName().equals("jdk.FileRead"))continue;
                String supplied=event.getString("path");if(supplied==null)continue;
                Path actual=Path.of(supplied).toAbsolutePath().normalize();
                if(!actual.startsWith(fixture.layout.snapshot().getParent()))continue;
                reads++;bytes+=Math.max(0,event.getLong("bytesRead"));
                for(int index=2;index<=4;index++)if(actual.equals(fixture.layout.event(index)))unrequested++;
                details.add(actual.getFileName().toString());
            }
        }
        System.out.println("HIST165_IO reads="+reads+" bytes="+bytes+" unrequested_event_reads="+unrequested
                +" repetitions=3 elapsed_nanos="+elapsed[0]+" recording="+recording+" paths="+details);
        assertTrue(reads>0,"the recording must observe actual residual ledger reads");
        assertEquals(0,unrequested,"same locked historical proof must not reopen unrelated event bodies");
        assertArrayEquals(snapshot,Files.readAllBytes(fixture.layout.snapshot()));
        assertFalse(Files.exists(fixture.layout.event(5)));
    }

    @Test void firstProofOfNewSessionRejectsCorruptionOutsideRequestedEvent() throws Exception {
        var fixture=history("session-boundary",2);String[] digest={null};
        ContinuityStorePort.Session[] escaped={null};
        fixture.writer.locked(same->{
            escaped[0]=same;digest[0]=same.head().digest();same.requireHistoricalHead(2,digest[0]);return null;
        });
        assertThrows(IllegalArgumentException.class,()->escaped[0].requireHistoricalHead(2,digest[0]));
        // The cached store still has the same snapshot. This older event is not the requested target.
        Files.writeString(fixture.layout.event(1),"changed original event");
        fixture.writer.locked(same->{assertThrows(IOException.class,()->same.requireHistoricalHead(2,digest[0]));return null;});
    }

    @Test void commitReplacesProofAndForeignWriterCannotBorrowSession() throws Exception {
        var fixture=history("commit",1);var foreign=history("foreign",1);
        fixture.writer.locked(same->{
            String first=same.head().digest();var before=same.requireHistoricalHead(1,first);
            assertThrows(IOException.class,()->foreign.writer.requireSession(same));
            var second=same.commit(same.preview(WriterFixture.settled("second",1048,3)));
            var ancestor=same.requireHistoricalHead(1,first);
            assertEquals(before.state().toJson(),ancestor.state().toJson());
            assertTrue(ancestor.documents().stream().anyMatch(pin->Path.of(pin.reference().path()).equals(fixture.layout.event(2))));
            assertEquals(2,same.requireHistoricalHead(2,ContinuityJson.digest(second.head().toJson())).state().sequence());
            // Same-session target reads remain physical and exact even after proof reuse.
            Files.writeString(fixture.layout.event(1),"changed requested original");
            assertThrows(IOException.class,()->same.requireHistoricalHead(1,first));
            return null;
        });
    }

    @Test void historicalDomainPayloadRemainsAnExactReadOnEveryCall() throws Exception {
        var fixture=new WriterFixture(root.resolve("domain"));Path archive=root.resolve("domain/archive");Files.createDirectory(archive);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(archive,fixture.layout.lock(),4_194_304),fixture.storage);
        var source=LedgerFiles.read(fixture.source,65_536).pin().reference();
        var registration=new DomainBodies.Registration(DomainBodies.Slot.LIFE,"fixture.life/v1",65_536,List.of(source),
                (before,previous,request,raw)->ContinuityJson.digest(ContinuityJson.parseObject(raw,65_536)));
        var authority=new TransitionAuthority() {
            @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalWindowReducer.reduce(before,request);}
        };
        var writer=new ContinuityWriter(fixture.layout,List.of(source),authority,Clock.systemUTC(),
                new ContinuityWriter.Extensions(List.of(registration),Optional.of(artifacts),Optional.empty()),fixture.storage);
        Path body=root.resolve("domain/original-body.json");Files.writeString(body,"{\"schema\":\"fixture.life/v1\",\"pending\":null}");
        var request=new DomainBodies.ImportRequest(DomainBodies.Slot.LIFE,"fixture.life/v1",LedgerFiles.read(body,65_536).pin().reference(),
                ContinuityJson.canonical(org.xar.ck3.control.contracts.StrictJson.object().put("input",1)),List.of(source),"domain-one");
        var receipt=writer.commitImport(writer.previewImport(request));
        writer.locked(same->{
            String digest=ContinuityJson.digest(receipt.head().toJson());var first=same.requireHistoricalHead(1,digest);
            var retained=DomainBodies.reference(first.state(),DomainBodies.Slot.LIFE).orElseThrow();
            Files.writeString(Path.of(retained.payload().path()),"{}");
            assertThrows(IOException.class,()->same.requireHistoricalHead(1,digest));return null;
        });
    }
}

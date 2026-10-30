package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;

/** Real sole-writer historical reads, with no new authority or persistence repair. */
final class HistoricalTransitionBatchTest {
    @TempDir Path root;
    private static Pin eventPin(WriterFixture fixture,long sequence)throws IOException {
        return LedgerFiles.read(fixture.layout.event(sequence),ContinuityJson.LEDGER_MAX_BYTES).pin();
    }
    @Test void batchUsesActualEdgesAndSeesLaterCommitWithoutRepairingMissingIndex()throws Exception {
        var fixture=new WriterFixture(root.resolve("actual-batch"));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("one",1024,2)));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("two",1048,3)));
        Pin first=eventPin(fixture,1),second=eventPin(fixture,2);
        fixture.writer.locked(same->{
            var edges=same.readHistoricalTransitions(List.of(second,first));
            assertEquals(List.of(2L,1L),edges.stream().map(HistoricalTransition::sequence).toList());
            for(var edge:edges){
                var old=same.readHistoricalTransition(edge.eventPin());
                assertEquals(old.sequence(),edge.sequence());assertEquals(old.kind(),edge.kind());
                assertEquals(old.eventIdentity(),edge.eventIdentity());assertEquals(old.eventPin(),edge.eventPin());
                assertArrayEquals(old.details(),edge.details());
                assertArrayEquals(old.before().canonicalBytes(),edge.before().canonicalBytes());
                assertArrayEquals(old.after().canonicalBytes(),edge.after().canonicalBytes());
            }
            assertEquals(ContinuityJson.digest(edges.get(1).after().toJson()),ContinuityJson.digest(edges.get(0).before().toJson()));
            assertArrayEquals(ContinuityJson.canonical(WriterFixture.state().get("pending_cycle")),
                    ContinuityJson.canonical(edges.get(0).after().toJson().get("pending_cycle")));
            var committed=same.commit(same.preview(WriterFixture.settled("three",1072,4)));
            assertEquals(3,committed.head().sequence());
            var current=same.readHistoricalTransitions(List.of(first,eventPin(fixture,3)));
            assertEquals(List.of(1L,3L),current.stream().map(HistoricalTransition::sequence).toList());
            assertEquals(same.head().digest(),ContinuityJson.digest(current.get(1).after().toJson()));
            return null;
        });
        Path index=fixture.layout.sourceIndex(WriterFixture.settled("three",1072,4).sourceKey());
        Files.delete(index);
        byte[] before=Files.readAllBytes(fixture.layout.snapshot());
        fixture.writer.locked(same->{
            assertEquals(3,same.readHistoricalTransitions(List.of(eventPin(fixture,3))).getFirst().sequence());
            assertFalse(same.head().indexRepairs().isEmpty());return null;
        });
        assertFalse(Files.exists(index));assertFalse(Files.exists(fixture.layout.event(4)));
        assertArrayEquals(before,Files.readAllBytes(fixture.layout.snapshot()));
    }
    @Test void batchRejectsCopiedAndReplacedOriginalEventPins()throws Exception {
        var fixture=new WriterFixture(root.resolve("foreign-pin"));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("one",1024,2)));
        Pin original=eventPin(fixture,1);
        Path copy=root.resolve("copied-event.json");Files.copy(fixture.layout.event(1),copy);
        Pin copied=LedgerFiles.read(copy,ContinuityJson.LEDGER_MAX_BYTES).pin();
        fixture.writer.locked(same->{
            same.readHistoricalTransitions(List.of(original));
            assertThrows(IOException.class,()->same.readHistoricalTransitions(List.of(copied)));
            Path replacement=root.resolve("replacement-event.json");Files.copy(fixture.layout.event(1),replacement);
            Files.move(replacement,fixture.layout.event(1),StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,()->same.readHistoricalTransitions(List.of(original)));
            assertEquals(1,same.readHistoricalTransitions(List.of(eventPin(fixture,1))).getFirst().sequence());
            return null;
        });
        fixture.writer.locked(same->{
            assertEquals(1,same.readHistoricalTransitions(List.of(eventPin(fixture,1))).getFirst().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(2)));
    }

    @Test void repeatedRequestedEdgesKeepCallerOrderAndDetachedDetails() throws Exception {
        var fixture=new WriterFixture(root.resolve("repeated-batch"));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("one",1024,2)));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("two",1048,3)));
        Pin first=eventPin(fixture,1),second=eventPin(fixture,2);
        fixture.writer.locked(same->{
            var edges=same.readHistoricalTransitions(List.of(second,first,second));
            assertEquals(List.of(2L,1L,2L),edges.stream().map(HistoricalTransition::sequence).toList());
            assertArrayEquals(edges.get(0).details(),edges.get(2).details());
            assertArrayEquals(edges.get(0).before().canonicalBytes(),edges.get(2).before().canonicalBytes());
            assertArrayEquals(edges.get(1).after().canonicalBytes(),edges.get(0).before().canonicalBytes());
            byte[] exposed=edges.get(0).details();exposed[0]='!';
            assertArrayEquals(edges.get(0).details(),edges.get(2).details());
            assertEquals(1,same.readHistoricalTransitions(List.of(first)).getFirst().sequence());
            return null;
        });
        assertFalse(Files.exists(fixture.layout.event(3)));
    }
}

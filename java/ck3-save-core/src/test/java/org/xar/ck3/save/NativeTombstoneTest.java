package org.xar.ck3.save;

import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.save.SaveContracts.*;

final class NativeTombstoneTest {
    private static final Selection EMPTY = new Selection(List.of(), List.of(), false, false, List.of());
    private static StreamingTable table(List<NativeId> selected, int count, long bytes) {
        return new StreamingTable(List.of("stories", "active"), "story_cycle", selected, count, 1024, bytes, true);
    }
    private static SaveStream parser(String body, StreamingTable table, StreamingTableSink sink) {
        return new SaveStream(new StringReader("stories={active={"+body+"}}"), EMPTY, table, sink);
    }
    private static StreamingTableSink sink() {
        return new StreamingTableSink() {
            public void discriminator(NativeId id,String type) { }
            public void record(StreamedRecord record) { }
        };
    }
    @Test void canonicalNoneHasSeparateBoundedEvidenceAndNeverARecordCallback() throws Exception {
        List<NativeTombstone> slots=new ArrayList<>();List<StreamedRecord> records=new ArrayList<>();
        var p=parser("1={story_cycle=finance}1288=none",table(List.of(new NativeId("1")),2,1024),new StreamingTableSink(){
            public void discriminator(NativeId id,String type) { }
            public void record(StreamedRecord record){records.add(record);}
            public void tombstone(NativeTombstone slot){slots.add(slot);}
        });p.read();var o=p.streamingObservation();
        assertEquals(1,o.records());assertEquals(1,o.selectedRecords());assertEquals(2,o.observedSlots());
        assertEquals(List.of(new NativeId("1")),records.stream().map(StreamedRecord::id).toList());
        assertEquals(List.of(new NativeId("1288")),slots.stream().map(NativeTombstone::id).toList());
        assertEquals(slots,o.tombstones());assertEquals(FilePins.sha256("1288 = none".getBytes(java.nio.charset.StandardCharsets.UTF_8)),slots.getFirst().canonicalTokenSha256());
        assertEquals(o,SaveJson.read(SaveJson.write(o),StreamingObservation.class));
    }
    @Test void arbitraryScalarQuotedNoneNoncanonicalIdAndMalformedBlockStillReject() {
        for(String body:List.of("1=0","1=yes","1=\"none\"","\"1\"=none","01=none","-1=none","18446744073709551616=none","1={}","1={story_cycle={bad=yes}}"))
            assertThrows(IOException.class,()->parser(body,table(List.of(),10,1024),sink()).read(),body);
    }
    @Test void duplicateIdsCannotCrossBlockAndTombstoneForms() {
        for(String body:List.of("1=none 1=none","1={story_cycle=finance}1=none","1=none 1={story_cycle=finance}"))
            assertThrows(IOException.class,()->parser(body,table(List.of(),10,1024),sink()).read(),body);
    }
    @Test void selectedTombstoneIsNotAnExistingSelectedRecord() {
        assertThrows(IOException.class,()->parser("1288=none",table(List.of(new NativeId("1288")),2,1024),sink()).read());
    }
    @Test void tombstonesConsumeOriginalIdentityAndStreamedByteBudgets() {
        assertThrows(IOException.class,()->parser("1=none 2=none",table(List.of(),1,1024),sink()).read());
        assertThrows(IOException.class,()->parser("1={story_cycle=finance}2=none",table(List.of(),1,1024),sink()).read());
        assertThrows(IOException.class,()->parser("1=none 2=none",table(List.of(),2,11),sink()).read());
    }
    @Test void tableTombstoneNeverWaivesRemainderOfStreamValidation() {
        var p=new SaveStream(new StringReader("stories={active={1288=none}}bad={"),EMPTY,table(List.of(),2,1024),sink());
        assertThrows(IOException.class,p::read);assertThrows(IllegalStateException.class,p::streamingObservation);
    }
}

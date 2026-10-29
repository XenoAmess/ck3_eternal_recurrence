package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual source pins -> original reducer preview -> sole DATA codec -> same writer commit.
 * Source and active-window originals are software persistence fixtures; no Game or Native capacity is granted.
 */
final class ConfiguredWriterSourceClosureTest {
    @TempDir Path temporary;
    private static TransitionAuthority reducer() {
        return new TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalWindowReducer.reduce(before,request);}
        };
    }
    @Test void fullConfiguredClosureIncludingLargeSourceRoundtripsAndCommitsWithoutTruncation()throws Exception {
        var fixture=new WriterFixture(temporary.resolve("ledger"));Path originals=Files.createDirectory(temporary.resolve("source-originals"));
        var sources=new ArrayList<ExactRef>();Path last=null;
        for(int index=0;index<MAXIMUM_CONFIGURED_SOURCES;index++) {
            Path source=originals.resolve(String.format(java.util.Locale.ROOT,"source-%03d.java",index));
            byte[] body=index==0?new byte[ContinuityJson.TRANSPORT_MAX_BYTES+1]:new byte[]{(byte)(index&127),1};
            Files.write(source,body,StandardOpenOption.CREATE_NEW);sources.add(LedgerFiles.read(source,MAX_PIN_BYTES).pin().reference());last=source;
        }
        var writer=new ContinuityWriter(fixture.layout,List.copyOf(sources),reducer(),fixture.storage);
        var prepared=writer.preview(WriterFixture.settled("full-writer-sources",1024,2));
        assertEquals(MAXIMUM_CONFIGURED_SOURCES,prepared.sources().size());
        assertEquals(sources,prepared.sources().stream().map(Pin::reference).toList());
        byte[] encoded=WriterTransactionCodec.encodePrepared(prepared);
        var decoded=WriterTransactionCodec.decodePrepared(encoded,WriterFixture.MACHINE);
        assertArrayEquals(encoded,WriterTransactionCodec.encodePrepared(decoded));assertEquals(prepared.sources(),decoded.sources());
        var receipt=writer.commit(decoded);assertEquals(Disposition.COMMITTED,receipt.disposition());
        var reopened=WriterTransactionCodec.decodeReceipt(WriterTransactionCodec.encodeReceipt(receipt),WriterFixture.MACHINE);
        assertEquals(receipt.eventIdentity(),reopened.eventIdentity());assertEquals(1,reopened.head().sequence());
        writer.locked(same->{assertEquals(sources,same.captureSources().stream().map(Pin::reference).toList());return null;});
        var changed=writer.preview(WriterFixture.settled("last-source-drift",1048,3));
        Files.writeString(last,"changed final actual source original");
        assertThrows(IOException.class,()->writer.commit(changed));
        writer.locked(same->{assertEquals(1,same.head().state().sequence());return null;});
    }
    @Test void configuredAndSerializedSourceCountAboveSharedBoundRejectsBeforeMutation()throws Exception {
        var fixture=new WriterFixture(temporary.resolve("bounds"));var reference=LedgerFiles.read(fixture.source,4096).pin().reference();
        List<ExactRef> tooMany=java.util.Collections.nCopies(MAXIMUM_CONFIGURED_SOURCES+1,reference);
        assertThrows(IllegalArgumentException.class,()->new ContinuityWriter(fixture.layout,tooMany,reducer(),fixture.storage));
        var actual=fixture.writer.preview(WriterFixture.settled("actual-one-source",1024,2));
        var encoded=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(WriterTransactionCodec.encodePrepared(actual),WriterTransactionCodec.MAXIMUM_BYTES);
        var rows=encoded.putArray("sources");for(int index=0;index<=MAXIMUM_CONFIGURED_SOURCES;index++)rows.add(actual.sources().getFirst().toJson());
        byte[] excessive=encoded.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->WriterTransactionCodec.decodePrepared(excessive,WriterFixture.MACHINE));
        fixture.writer.locked(same->{assertEquals(0,same.head().state().sequence());return null;});
    }
}

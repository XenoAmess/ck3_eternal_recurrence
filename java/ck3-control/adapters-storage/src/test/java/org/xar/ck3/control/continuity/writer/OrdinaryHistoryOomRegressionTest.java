package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.FileTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.StrictJson;

/** Real physical warm/cold writer and compact projection; no private Batch/Managed or Game qualification. */
final class OrdinaryHistoryOomRegressionTest {
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static final int LONG_EDGES=128;
    private static final int PAYLOAD_BYTES=112*1024;
    private static final int SMALL_EDGES=12;
    @TempDir Path root;

    private record Summary(int count,long sequenceSum,long lastSequence,long lastDate,long lastCycles) { }

    /** Uses the existing WriterFixture's actual baseline/reducer, not a fabricated Session or Root issuer. */
    private static ObjectNode initial(int payloadBytes) {
        ObjectNode row=StrictJson.object();
        row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);
        row.put("sequence",0);row.put("window_id",1);row.put("status","running");
        row.put("target_days",10958);row.put("target_years",30);row.put("calendar_year_days",365.25);
        row.put("start_date_raw",1000);row.put("target_date_raw",1000+10958*24);
        row.put("last_settled_date_raw",1000);row.put("last_settled_cycles",1);
        row.put("manual_repair_count",1);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);
        row.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");
        row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);
        row.put("NEXT",11559);
        row.put("opaque_fixture_payload","x".repeat(payloadBytes));
        return row;
    }
    private static Request settled(int sequence) {
        ObjectNode details=StrictJson.object();details.put("machine_id",MACHINE);
        details.put("evidence_id","bounded-history-event-"+sequence);details.put("source","original-actual-pair");
        details.put("date_raw",1000L+24L*sequence);details.put("completed_cycles",1L+sequence);
        return new Request("settled_batch",ContinuityJson.canonical(details),List.of());
    }
    private static final class Fixture implements AutoCloseable {
        final Layout layout;final ContinuityWriter writer;final StorageWriteGuardTestSupport storage;
        final List<org.xar.ck3.control.contracts.ExactRef> sources;
        final TransitionAuthority authority;
        Fixture(Path supplied,int payloadBytes)throws IOException {
            Path directory=supplied.toAbsolutePath().normalize();Files.createDirectory(directory);
            Path snapshot=directory.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=directory.resolve("anchor.json");
            byte[] seed=ContinuityState.fromJson(initial(payloadBytes),MACHINE).canonicalBytes();
            Files.write(snapshot,seed);Files.write(anchor,seed);
            Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);
            Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path source=directory.resolve("reviewed-source.txt");Files.writeString(source,"literal OriginalWindowReducer DATA fixture");
            layout=new Layout(snapshot,LedgerFiles.read(anchor,ContinuityJson.LEDGER_MAX_BYTES).pin().reference(),MACHINE);
            storage=StorageWriteGuardTestSupport.create(directory,layout.lock(),256L*1024*1024);
            sources=List.of(LedgerFiles.read(source,65536).pin().reference());
            authority=new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before,Request request) {
                    return ContinuityJson.digest(request.detailsObject());
                }
                @Override public ContinuityState reduce(ContinuityState before,Request request) {
                    return OriginalWindowReducer.reduce(before,request);
                }
            };
            writer=reopen();
        }
        ContinuityWriter reopen()throws IOException {return new ContinuityWriter(layout,sources,authority,storage);}
        @Override public void close()throws IOException {storage.close();}
        Pin pin(long sequence)throws IOException {return LedgerFiles.read(layout.event(sequence),ContinuityJson.LEDGER_MAX_BYTES).pin();}
        List<Pin> build(ContinuityStorePort.Session same,int count)throws IOException {
            var pins=new ArrayList<Pin>(count);
            // Real guarded commits keep the actual store's clean incremental Head warm.
            // A preseeded cold open would exercise a separate all-document Head projector.
            for(int sequence=1;sequence<=count;sequence++) {
                Request request=settled(sequence);Prepared prepared=same.preview(request);
                Receipt receipt=same.commit(prepared);
                assertEquals(Disposition.COMMITTED,receipt.disposition());
                assertEquals(sequence,receipt.head().sequence());
                assertTrue(Files.isRegularFile(layout.sourceIndex(request.sourceKey())));
                pins.add(pin(sequence));
            }
            return List.copyOf(pins);
        }
    }
    private static Summary consume(List<HistoricalTransition> edges,int payloadBytes) {
        long sum=0,lastSequence=0,lastDate=0,lastCycles=0;String preceding=null;
        for(int index=0;index<edges.size();index++) {
            HistoricalTransition edge=edges.get(index);long sequence=index+1L;
            assertEquals(sequence,edge.sequence());assertEquals("settled_batch",edge.kind());
            assertEquals(sequence-1,edge.before().sequence());assertEquals(sequence,edge.after().sequence());
            assertEquals(settled(index+1).identity(),edge.eventIdentity());
            assertArrayEquals(settled(index+1).details(),edge.details());
            if(preceding!=null)assertEquals(preceding,ContinuityJson.digest(edge.before().toJson()));
            ObjectNode after=edge.after().toJson();
            assertEquals(payloadBytes,after.path("opaque_fixture_payload").textValue().length());
            assertEquals(edge.eventIdentity(),after.path("last_event_identity").textValue());
            lastDate=after.path("last_settled_date_raw").longValue();lastCycles=after.path("last_settled_cycles").longValue();
            assertEquals(1000L+24L*sequence,lastDate);assertEquals(sequence+1,lastCycles);
            preceding=ContinuityJson.digest(after);sum+=sequence;lastSequence=sequence;
        }
        return new Summary(edges.size(),sum,lastSequence,lastDate,lastCycles);
    }
    private static void restore(Path path,byte[] raw,FileTime modified)throws IOException {
        Files.write(path,raw);Files.setLastModifiedTime(path,modified);
    }

    @Test void realWriterProjectsLongFullStatesUnderFixedSmallHeapAndClosesItsView()throws Exception {
        assertTrue(Runtime.getRuntime().maxMemory()<=64L*1024*1024,"this regression requires Native's fixed <=64MiB RUN heap");
        try(var fixture=new Fixture(root.resolve("long-history"),PAYLOAD_BYTES)) {
            List<Pin> pins=fixture.writer.locked(same->{
                List<Pin> builtPins=fixture.build(same,LONG_EDGES);
                Head before=same.head();String digest=before.digest();
                var callbacks=new AtomicInteger();var escaped=new AtomicReference<List<HistoricalTransition>>();
                Summary result=same.withHistoricalTransitions(builtPins,edges->{
                    assertEquals(1,callbacks.incrementAndGet());escaped.set(edges);
                    return consume(edges,PAYLOAD_BYTES);
                });
                assertEquals(new Summary(LONG_EDGES,LONG_EDGES*(LONG_EDGES+1L)/2,LONG_EDGES,
                        1000L+24L*LONG_EDGES,LONG_EDGES+1L),result);
                assertEquals(1,callbacks.get());assertEquals(digest,same.head().digest());
                assertThrows(UncheckedIOException.class,()->escaped.get().get(0));
                assertThrows(UncheckedIOException.class,()->escaped.get().size());escaped.set(null);
                assertFalse(Files.exists(fixture.layout.event(LONG_EDGES+1L)));
                return builtPins;
            });
            // A different actual Writer/Store forces the canonical cold-head producer too.
            // This needs the separately qualified cold Store/History candidate, not only the new warm API.
            ContinuityWriter cold=fixture.reopen();
            cold.locked(same->{
                Head before=same.head();String digest=before.digest();var callbacks=new AtomicInteger();
                Summary result=same.withHistoricalTransitions(pins,edges->{
                    assertEquals(1,callbacks.incrementAndGet());return consume(edges,PAYLOAD_BYTES);
                });
                assertEquals(new Summary(LONG_EDGES,LONG_EDGES*(LONG_EDGES+1L)/2,LONG_EDGES,
                        1000L+24L*LONG_EDGES,LONG_EDGES+1L),result);
                assertEquals(1,callbacks.get());assertEquals(digest,same.head().digest());
                assertFalse(Files.exists(fixture.layout.event(LONG_EDGES+1L)));
                System.out.println("SOFTWARE_BOUNDED_HISTORY edges="+LONG_EDGES+" state_payload_bytes="+PAYLOAD_BYTES
                        +" requested_payload_bytes="+(LONG_EDGES*(long)PAYLOAD_BYTES)+" max_heap="+Runtime.getRuntime().maxMemory()
                        +" warm_callbacks=1 cold_callbacks=1 no_read_writes=true");
                return null;
            });
        }
    }

    @Test void latePhysicalFailuresCaughtReadsAndChangedHeadCannotGrantAProjection()throws Exception {
        for(String mode:List.of("requested","unrequested","caught-restored","identity","head","absence","primary")) {
            try(var fixture=new Fixture(root.resolve(mode),0)) {
                fixture.writer.locked(same->{
                    List<Pin> pins=fixture.build(same,SMALL_EDGES);
                    Head before=same.head();String digest=before.digest();byte[] snapshot=Files.readAllBytes(fixture.layout.snapshot());
                    Path target=fixture.layout.event(SMALL_EDGES);byte[] raw=Files.readAllBytes(target);
                    FileTime modified=Files.getLastModifiedTime(target);FileIdentity identity=LedgerFiles.identity(target);
                    var calls=new AtomicInteger();var fired=new AtomicInteger();
                    var delivered=new AtomicReference<String>();var caught=new AtomicReference<IOException>();
                    var escaped=new AtomicReference<List<HistoricalTransition>>();
                    IOException primary=new IOException("actual projection consumer primary");
                    List<Pin> requested=List.of("unrequested","head","absence","primary").contains(mode)?List.of(pins.getFirst()):pins;
                    IOException failure;
                    try {
                        failure=assertThrows(IOException.class,()->delivered.set(same.withHistoricalTransitions(requested,edges->{
                            assertEquals(1,calls.incrementAndGet());escaped.set(edges);
                            assertEquals(1,edges.getFirst().sequence());
                            if(mode.equals("head")) {
                                Prepared next=same.preview(settled(SMALL_EDGES+1));
                                assertEquals(Disposition.COMMITTED,same.commit(next).disposition());fired.incrementAndGet();
                            } else if(mode.equals("absence")) {
                                Files.write(fixture.layout.event(SMALL_EDGES+1L),new byte[]{'{','}'});fired.incrementAndGet();
                            } else if(mode.equals("identity")) {
                                Path replacement=target.resolveSibling("equal-byte-replacement.json");
                                Files.copy(target,replacement);Files.setLastModifiedTime(replacement,modified);
                                Files.move(replacement,target,StandardCopyOption.REPLACE_EXISTING);
                                assertArrayEquals(raw,Files.readAllBytes(target));
                                assertNotEquals(identity.fileIdDecimal(),LedgerFiles.identity(target).fileIdDecimal());fired.incrementAndGet();
                            } else {
                                byte[] corrupt=raw.clone();corrupt[corrupt.length-1]^=1;
                                Files.write(target,corrupt);fired.incrementAndGet();
                                if(mode.equals("caught-restored")) {
                                    UncheckedIOException read=assertThrows(UncheckedIOException.class,()->edges.get(SMALL_EDGES-1));
                                    caught.set(read.getCause());restore(target,raw,modified);
                                    assertEquals(identity,LedgerFiles.identity(target),"all physical pins restored; sticky failure must still reject");
                                }
                                if(mode.equals("primary"))throw primary;
                            }
                            return "must-not-escape";
                        })));
                    } finally {
                        if(mode.equals("absence"))Files.deleteIfExists(fixture.layout.event(SMALL_EDGES+1L));
                        else if(!mode.equals("identity")&&!mode.equals("head"))restore(target,raw,modified);
                    }
                    assertNull(delivered.get());assertEquals(1,calls.get());assertEquals(1,fired.get());
                    assertThrows(UncheckedIOException.class,()->escaped.get().get(0));escaped.set(null);
                    if(mode.equals("caught-restored"))assertSame(caught.get(),failure,"caught original remains sticky after exact restoration");
                    if(mode.equals("primary")) {
                        assertSame(primary,failure);assertTrue(failure.getSuppressed().length>0,"late physical fence remains attached to original primary");
                    }
                    if(mode.equals("head")) {
                        assertEquals(SMALL_EDGES+1,same.head().state().sequence());assertNotEquals(digest,same.head().digest());
                        List<Pin> fresh=new ArrayList<>(pins);fresh.add(fixture.pin(SMALL_EDGES+1));
                        Integer count=same.withHistoricalTransitions(fresh,List::size);assertEquals(SMALL_EDGES+1,count.intValue());
                        assertFalse(Files.exists(fixture.layout.event(SMALL_EDGES+2L)));
                    } else {
                        assertArrayEquals(snapshot,Files.readAllBytes(fixture.layout.snapshot()));
                        assertFalse(Files.exists(fixture.layout.event(SMALL_EDGES+1L)));
                        if(!mode.equals("identity")) {
                            assertEquals(digest,same.head().digest());
                            Integer count=same.withHistoricalTransitions(pins,List::size);assertEquals(SMALL_EDGES,count.intValue());
                        }
                    }
                    System.out.println("SOFTWARE_HISTORY_FENCE mode="+mode+" callbacks=1 fault_fired=true result_delivered=false");
                    return null;
                });
            }
        }
    }
}

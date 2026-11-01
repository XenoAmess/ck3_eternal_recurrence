package org.xar.ck3.control.continuity.writer;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Real owned-temp Session/NoWrites/CAS-scope composition. No Game or Saved issuer is fabricated. */
final class ReadOnlyHistoricalScope258Test {
    @TempDir Path temp;
    private static final byte[] ORIGINAL="{\"retained\":true}".getBytes(StandardCharsets.UTF_8);
    private static final ActionPorts.HistoricalReadLimits LIMITS=new ActionPorts.HistoricalReadLimits(8,16_384,16);
    private static final TransitionAuthority NEVER=new TransitionAuthority() {
        @Override public String revalidate(ContinuityState before,Request request){throw new AssertionError("no preview");}
        @Override public ContinuityState reduce(ContinuityState before,Request request){throw new AssertionError("no commit");}
    };
    private static ObjectNode state() {
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");
        row.put("machine_id","scope258-owned-temp");row.put("sequence",0);row.put("window_id",1);
        row.put("status","running");row.put("target_days",10958);row.put("target_years",30);
        row.put("calendar_year_days",365.25);row.put("start_date_raw",1000);row.put("target_date_raw",263992);
        row.put("last_settled_date_raw",1000);row.put("last_settled_cycles",1);row.put("manual_repair_count",1);
        row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);
        var game=row.putObject("game_binding");game.put("pid",123);game.put("creation_date","2026-10-23T01:00:00Z");
        row.putNull("latest_binding");row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);
        row.put("NEXT",11559);return row;
    }
    private static final class Fixture implements AutoCloseable {
        final Path root;final Layout layout;final ExactRef source;final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore.Config config;final ContinuityWriter writer;final NativeOutcomeArchive archive;
        Fixture(Path root)throws IOException {
            this.root=root;Files.createDirectory(root);byte[] state=ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"),state,StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"),state,StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0],StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));
            var original=root.resolve("source.txt");Files.writeString(original,"reviewed owned-temp source",StandardOpenOption.CREATE_NEW);
            source=LedgerFiles.read(original,1024).pin().reference();
            layout=new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),LedgerFiles.read(root.resolve("anchor.json"),65536).pin().reference(),"scope258-owned-temp");
            storage=StorageWriteGuardTestSupport.create(layout);config=new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),8<<20);
            var store=new ImmutableArtifactStore(config,storage);
            writer=new ContinuityWriter(layout,List.of(source),NEVER,Clock.systemUTC(),
                    new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),storage);
            archive=new NativeOutcomeArchive(store,writer);
        }
        @Override public void close()throws IOException {storage.close();}
    }
    private static final class Reader implements AutoCloseable {
        final StorageWriteGuard noWrites=StorageWriteGuard.noWrites();
        final ContinuityWriter writer;final NativeOutcomeArchive archive;
        Reader(Fixture source)throws IOException {
            var store=ImmutableArtifactStore.readOnlyExisting(source.config,noWrites);
            writer=ContinuityWriter.readOnlyExisting(source.layout,List.of(source.source),NEVER,Clock.systemUTC(),
                    new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),noWrites);
            archive=new NativeOutcomeArchive(store,writer);
        }
        @Override public void close()throws IOException {noWrites.close();}
    }
    private static long leaves(Path root)throws IOException {try(var paths=Files.list(root)){return paths.count();}}
    private static boolean causedBy(Throwable failure,Throwable original) {
        for(int depth=0;failure!=null&&depth<32;depth++,failure=failure.getCause())if(failure==original)return true;
        return false;
    }
    private static void restored(Fixture caller,ContinuityStorePort.Session outer,String digest)throws IOException {
        caller.writer.requireSession(outer);assertSame(outer,caller.writer.borrowedSession());
        assertEquals(digest,outer.head().digest());
    }
    @Test void actualReadonlyInnerScopeClosesBeforeExactOuterResumes()throws IOException {
        try(var source=new Fixture(temp.resolve("old"));var caller=new Fixture(temp.resolve("new"));var reader=new Reader(source)) {
            ExactRef ref=source.writer.locked(same->source.archive.preserveArtifact(same,ORIGINAL,1024));
            assertArrayEquals(ORIGINAL,source.writer.locked(same->source.archive.readArtifact(same,ref,1024)));
            byte[] before=Files.readAllBytes(source.layout.snapshot());long inventory=leaves(source.root.resolve("artifacts"));
            var escaped=new AtomicReference<ContinuityStorePort.Session>();
            caller.writer.locked(outer->{
                String digest=outer.head().digest();
                reader.writer.readOnlyFrom(outer,old->{
                    escaped.set(old);reader.writer.requireSession(old);assertSame(old,reader.writer.borrowedSession());
                    assertThrows(ContractViolationException.class,outer::head);
                    reader.archive.inHistoricalReadScope(old,LIMITS,bound->{
                        assertArrayEquals(ORIGINAL,reader.archive.readArtifact(old,ref,1024));
                        byte[] detached=reader.archive.readArtifact(old,ref,1024);detached[0]=0;
                        assertArrayEquals(ORIGINAL,reader.archive.readArtifact(old,ref,1024));
                        return null;
                    });
                    reader.writer.requireSession(old);assertNotNull(old.head());return null;
                });
                restored(caller,outer,digest);assertThrows(ContractViolationException.class,escaped.get()::head);
                byte[] next=reader.writer.readOnlyFrom(outer,old->{
                    assertNotSame(escaped.get(),old);
                    return reader.archive.inHistoricalReadScope(old,LIMITS,bound->reader.archive.readArtifact(old,ref,1024));
                });
                assertArrayEquals(ORIGINAL,next);
                restored(caller,outer,digest);
                ExactRef own=caller.archive.preserveArtifact(outer,"new".getBytes(StandardCharsets.UTF_8),1024);
                assertArrayEquals("new".getBytes(StandardCharsets.UTF_8),caller.archive.readArtifact(outer,own,1024));
                return null;
            });
            assertArrayEquals(before,Files.readAllBytes(source.layout.snapshot()));assertEquals(inventory,leaves(source.root.resolve("artifacts")));
        }
    }
    @Test void caughtForbiddenPublicationStillFailsScopeAndRestoresOuter()throws IOException {
        try(var source=new Fixture(temp.resolve("old-failure"));var caller=new Fixture(temp.resolve("new-failure"));var reader=new Reader(source)) {
            ExactRef ref=source.writer.locked(same->source.archive.preserveArtifact(same,ORIGINAL,1024));
            assertArrayEquals(ORIGINAL,source.writer.locked(same->source.archive.readArtifact(same,ref,1024)));
            byte[] before=Files.readAllBytes(source.layout.snapshot());long inventory=leaves(source.root.resolve("artifacts"));
            var caught=new AtomicReference<IOException>();
            caller.writer.locked(outer->{
                String digest=outer.head().digest();
                IOException poisoned=assertThrows(IOException.class,()->reader.writer.readOnlyFrom(outer,old->
                        reader.archive.inHistoricalReadScope(old,LIMITS,bound->{
                            assertArrayEquals(ORIGINAL,reader.archive.readArtifact(old,ref,1024));
                            caught.set(assertThrows(IOException.class,()->reader.archive.preserveArtifact(old,"forbidden".getBytes(StandardCharsets.UTF_8),1024)));
                            return null;
                        })));
                assertNotNull(caught.get());assertTrue(causedBy(poisoned,caught.get()));
                restored(caller,outer,digest);
                byte[] recovered=reader.writer.readOnlyFrom(outer,old->reader.archive.inHistoricalReadScope(old,LIMITS,
                        bound->reader.archive.readArtifact(old,ref,1024)));
                assertArrayEquals(ORIGINAL,recovered);restored(caller,outer,digest);return null;
            });
            assertArrayEquals(before,Files.readAllBytes(source.layout.snapshot()));assertEquals(inventory,leaves(source.root.resolve("artifacts")));
        }
    }
}

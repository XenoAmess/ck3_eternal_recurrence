package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Store/writer persistence regression only. No Entry, Game or runtime capacity authority is invented. */
final class FreshGenesisWriterInitializationTest {
    @TempDir Path root;
    private record Fixture(FreshContinuityGenesis.Plan plan,ExactRef request,InitialLayout paths,
            StorageWriteGuardTestSupport storage,ExactRef source) { }
    private Fixture fixture(String name)throws IOException {
        Path directory=Files.createDirectory(root.resolve(name));
        var paths=new InitialLayout(directory.resolve("ROOT-CONTINUITY-WINDOW.json"),directory.resolve("anchor.json"),WriterFixture.MACHINE);
        // The existing finite test allocation owner requires an actual empty original lock, like the Root bootstrap guard.
        Files.createFile(paths.lock());
        var plan=new FreshContinuityGenesis.Plan(WriterFixture.MACHINE,1,OriginalWindowReducer.TARGET_DAYS);
        Path request=directory.resolve("initial-request.json");Files.write(request,FreshContinuityGenesis.encode(plan));
        Path source=directory.resolve("actual-reviewed-source.txt");Files.writeString(source,"software persistence fixture only");
        var storage=StorageWriteGuardTestSupport.create(directory,paths.lock(),4L<<20);
        return new Fixture(plan,LedgerFiles.read(request,4096).pin().reference(),paths,storage,
                LedgerFiles.read(source,4096).pin().reference());
    }
    private ContinuityWriter writer(Fixture fixture,Layout actual)throws IOException {
        return new ContinuityWriter(actual,List.of(fixture.source()),new TransitionAuthority(){
            @Override public String revalidate(ContinuityState before,Request request){return request.identity();}
            @Override public ContinuityState reduce(ContinuityState before,Request request){return OriginalWindowReducer.reduce(before,request);}
        },fixture.storage());
    }
    @Test void actualCreateNewStoreAndSameWriterReadPreEntryWithoutDateGameOrCredit()throws Exception {
        var fixture=fixture("new-store");assertFalse(Files.exists(fixture.paths().anchor()));assertFalse(Files.exists(fixture.paths().snapshot()));
        var actual=ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),fixture.storage());
        var queried=ContinuityWriter.readFreshInitialization(fixture.plan(),fixture.request(),fixture.paths());
        assertEquals(actual.layout(),queried.layout());assertEquals(actual.anchor(),queried.anchor());assertEquals(actual.snapshot(),queried.snapshot());
        assertEquals(LedgerFiles.read(fixture.paths().lock(),1).pin(),actual.lock());assertEquals(actual.lock(),queried.lock());
        assertEquals(fixture.paths().anchor().toString(),actual.layout().anchor().path());
        assertEquals(actual.anchor().reference(),actual.layout().anchor());
        assertEquals(actual.anchor().reference().sha256(),actual.snapshot().reference().sha256());
        assertNotEquals(actual.anchor().identity().fileIdDecimal(),actual.snapshot().identity().fileIdDecimal());
        var writer=writer(fixture,actual.layout());
        writer.locked(same->{
            writer.requireSession(same);var state=same.head().state();
            assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY,state.status());assertEquals(0,state.sequence());
            assertEquals(0,state.settledCycles());assertTrue(state.initializedOrigin().isEmpty());
            assertThrows(IllegalArgumentException.class,state::origin);assertThrows(IllegalArgumentException.class,state::settledDateRaw);
            var row=state.toJson();assertFalse(row.has("game_binding"));assertTrue(row.get("start_date_raw").isNull());
            assertTrue(row.get("last_settled_date_raw").isNull());assertFalse(row.has("pending_cycle"));
            assertArrayEquals(state.canonicalBytes(),ContinuityState.fromJson(row,WriterFixture.MACHINE).canonicalBytes());
            var details=StrictJson.object();details.put("evidence_id","cannot-credit-pre-entry");details.put("source","software-query");
            details.put("date_raw",24);details.put("completed_cycles",1);
            assertThrows(IllegalArgumentException.class,()->same.preview(new Request("settled_batch",ContinuityJson.canonical(details),List.of())));
            assertEquals(0,same.head().state().sequence());return null;
        });
        try(var events=Files.list(fixture.paths().events())){assertEquals(0,events.count());}
        byte[] anchor=Files.readAllBytes(fixture.paths().anchor());
        assertThrows(IOException.class,()->ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),fixture.storage()));
        assertArrayEquals(anchor,Files.readAllBytes(fixture.paths().anchor()));
    }
    @Test void changedOriginalAndWrongTypedPlanAreRejectedBeforeCanonicalOutputs()throws Exception {
        var fixture=fixture("changed-request");
        Files.writeString(Path.of(fixture.request().path()),"{}");
        assertThrows(IOException.class,()->ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),fixture.storage()));
        assertFalse(Files.exists(fixture.paths().anchor()));assertFalse(Files.exists(fixture.paths().snapshot()));
        for(int variant=0;variant<4;variant++) {
            var row=StrictJson.object(StrictJson.parse(FreshContinuityGenesis.encode(fixture.plan())),
                    java.util.Set.of("schema","machine_id","planned_window_id","target_days"));
            switch(variant){case 0->row.remove("target_days");case 1->row.putNull("target_days");
                case 2->row.put("target_days",true);case 3->row.put("planned_window_id",1.0);default->throw new AssertionError();}
            byte[] body=row.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class,()->FreshContinuityGenesis.decode(body));
        }
    }
    /** Persistence DATA only; the local-service test must separately use a genuine START/Received/Driver producer. */
    @Test void observedEntryUsesOriginalWriterAndReopensItsExactBusinessOriginWithoutSaveOrCycleCredit()throws Exception {
        var fixture=fixture("observed-entry");
        var initialized=ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),fixture.storage());
        var authority=new TransitionAuthority(){
            @Override public String revalidate(ContinuityState state,Request request){return request.identity();}
            @Override public ContinuityState reduce(ContinuityState state,Request request){return org.xar.ck3.control.continuity.ObservedGameplayEntry.reduce(state,request,false);}
        };
        var writer=new ContinuityWriter(initialized.layout(),List.of(fixture.source()),authority,fixture.storage());
        var game=org.xar.ck3.control.contracts.GameGeneration.fromJson(StrictJson.object().put("pid",73).put("creation_filetime","9007199254740993"));
        var details=new org.xar.ck3.control.continuity.ObservedGameplayEntry.Details(WriterFixture.MACHINE,"software-session","software-episode","software-frame",game,
                2,53144328,73,java.math.BigInteger.ONE,new java.math.BigInteger("9007199254740993"),
                fixture.source(),fixture.source(),fixture.source(),fixture.source(),fixture.source());
        var receipt=writer.locked(same->{
            var prepared=same.preview(details.request());var result=same.commit(prepared);same.requireCommitted(prepared,result);return result;
        });
        assertEquals(Disposition.COMMITTED,receipt.disposition());assertEquals(1,receipt.head().sequence());
        assertEquals(0,receipt.head().settledCycles());assertEquals(53144328,receipt.head().origin().startDateRaw());
        assertEquals(game,org.xar.ck3.control.contracts.GameGeneration.fromJson(receipt.head().toJson().get("game_binding")));
        var reopened=writer.locked(same->same.head().state());
        assertArrayEquals(receipt.head().canonicalBytes(),reopened.canonicalBytes());
        assertEquals("software-episode",reopened.toJson().path("latest_binding").path("episode_run_id").textValue());
        assertFalse(reopened.toJson().has(ORDINARY_SAVED_CYCLE_FIELD));
        writer.locked(same->{assertEquals(Disposition.ALREADY_COMMITTED,same.commit(same.preview(details.request())).disposition());return null;});
        assertTrue(Files.isRegularFile(initialized.layout().event(1)));assertFalse(Files.exists(initialized.layout().event(2)));
    }
    @Test void failedInitialSnapshotKeepsRealPartialAnchorAndNeverReplacesIt()throws Exception {
        var fixture=fixture("partial");
        StorageWriteGuard failure=new StorageWriteGuard(){
            @Override public void requireInitialization(Path lock,List<Path> roots)throws IOException {fixture.storage().requireInitialization(lock,roots);}
            @Override public <T>T write(WritePlan plan,PhysicalWrite<T> io)throws IOException {
                if(plan.mutations().size()==1&&plan.mutations().getFirst() instanceof FileRename rename
                        &&rename.target().equals(fixture.paths().snapshot()))throw new IOException("injected lost initial snapshot publication");
                return fixture.storage().write(plan,io);
            }
            @Override public void close()throws IOException {fixture.storage().close();}
        };
        assertThrows(IOException.class,()->ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),failure));
        assertTrue(Files.exists(fixture.paths().anchor()));assertFalse(Files.exists(fixture.paths().snapshot()));
        byte[] retained=Files.readAllBytes(fixture.paths().anchor());
        assertThrows(IOException.class,()->ContinuityWriter.initializeFresh(fixture.plan(),fixture.request(),fixture.paths(),failure));
        assertArrayEquals(retained,Files.readAllBytes(fixture.paths().anchor()));
        assertThrows(IOException.class,()->ContinuityWriter.readFreshInitialization(fixture.plan(),fixture.request(),fixture.paths()));
        var anchor=LedgerFiles.read(fixture.paths().anchor(),65536).pin().reference();
        assertThrows(IOException.class,()->new ContinuityStore(new Layout(fixture.paths().snapshot(),anchor,WriterFixture.MACHINE)).head());
    }
}

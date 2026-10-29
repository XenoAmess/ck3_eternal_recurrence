package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.Platform;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual temporary canonical writer/Windows lock tests. Fixture authorities confer no native or Game qualification. */
final class DriverReadHistoryWriterTest {
    @TempDir Path root;
    private static List<ExactRef> sources(WriterFixture fixture) throws IOException {
        return List.of(LedgerFiles.read(fixture.source,65_536).pin().reference());
    }
    private static TransitionAuthority originalAuthority(){
        return new TransitionAuthority(){
            @Override public String revalidate(ContinuityState state,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState state,Request request){return OriginalWindowReducer.reduce(state,request);}
        };
    }
    @Test void activeScopeIsExactAndForeignScopeIsAnErrorRatherThanAbsence() throws Exception {
        assertTrue(Platform.isWindows());WriterFixture fixture=new WriterFixture(root.resolve("scope"));
        ContinuityWriter foreign=new ContinuityWriter(fixture.layout, sources(fixture), originalAuthority(), StorageWriteGuardTestSupport.forLayout(fixture.layout));
        assertTrue(fixture.writer.activeSession().isEmpty());assertTrue(foreign.activeSession().isEmpty());
        ContinuityStorePort.Session[] escaped=new ContinuityStorePort.Session[1];
        fixture.writer.locked(session->{
            escaped[0]=session;
            assertSame(session,fixture.writer.activeSession().orElseThrow());
            assertSame(session,fixture.writer.borrowedSession());
            assertThrows(IOException.class,foreign::activeSession);
            assertThrows(IOException.class,foreign::borrowedSession);
            assertThrows(IOException.class,()->foreign.locked(other->{throw new AssertionError("nested writer callback must never run");}));
            ExecutorService executor=Executors.newSingleThreadExecutor();
            try {
                try {
                    assertTrue(executor.submit(()->fixture.writer.activeSession().isEmpty()).get(5,TimeUnit.SECONDS));
                    assertTrue(executor.submit(()->{
                        try{fixture.writer.borrowedSession();return false;}catch(IOException unavailable){return true;}
                    }).get(5,TimeUnit.SECONDS));
                } finally {executor.shutdownNow();assertTrue(executor.awaitTermination(5,TimeUnit.SECONDS));}
            }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("cross-thread writer scope probe interrupted",interrupted);}
            catch(ExecutionException|TimeoutException failure){throw new IOException("cross-thread writer scope probe failed",failure);}
            return null;
        });
        assertTrue(fixture.writer.activeSession().isEmpty());
        assertThrows(ContractViolationException.class,()->escaped[0].head());
        assertThrows(IOException.class,()->fixture.writer.locked(session->{throw new IOException("actual callback failure");}));
        assertTrue(fixture.writer.activeSession().isEmpty());
        assertTrue(foreign.activeSession().isEmpty());
        foreign.locked(session->{assertSame(session,foreign.activeSession().orElseThrow());return null;});
        assertTrue(foreign.activeSession().isEmpty());
    }
    @Test void exactHistoricalStatesAreReadFromTheActualFiniteChainAfterLaterCommitsWithoutWrites() throws Exception {
        assertTrue(Platform.isWindows());WriterFixture fixture=new WriterFixture(root.resolve("historical"));
        Head anchor=fixture.writer.locked(ContinuityStorePort.Session::head);
        Receipt first=fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("first",1024,2)));
        fixture.writer.commit(fixture.writer.preview(WriterFixture.settled("second",1048,3)));
        byte[] snapshot=Files.readAllBytes(fixture.layout.snapshot()),event1=Files.readAllBytes(fixture.layout.event(1)),event2=Files.readAllBytes(fixture.layout.event(2));
        Path missingIndex=fixture.layout.sourceIndex(WriterFixture.settled("first",1024,2).sourceKey());
        Files.delete(missingIndex);
        ContinuityWriter reader=new ContinuityWriter(fixture.layout, sources(fixture), new TransitionAuthority(){
            @Override public String revalidate(ContinuityState state,Request request){throw new AssertionError("historical proof cannot invoke an authority");}
            @Override public ContinuityState reduce(ContinuityState state,Request request){throw new AssertionError("historical proof cannot replay a reducer");}
        }, StorageWriteGuardTestSupport.forLayout(fixture.layout));
        reader.locked(session->{
            ContinuityState old=session.requireHistoricalState(0,anchor.digest());
            assertTrue(ContinuityJson.same(anchor.state().toJson(),old.toJson()));
            String firstDigest=ContinuityJson.digest(first.head().toJson());
            ContinuityState retained=session.requireHistoricalState(1,firstDigest);
            assertTrue(ContinuityJson.same(first.head().toJson(),retained.toJson()));
            Head current=session.head();
            assertTrue(ContinuityJson.same(current.state().toJson(),session.requireHistoricalState(2,current.digest()).toJson()));
            assertThrows(IOException.class,()->session.requireHistoricalState(1,current.digest()));
            assertThrows(IOException.class,()->session.requireHistoricalState(3,current.digest()));
            assertThrows(IOException.class,()->session.requireHistoricalState(-1,anchor.digest()));
            assertThrows(IOException.class,()->session.requireHistoricalState(0,"A".repeat(64)));
            assertThrows(IOException.class,()->session.requireHistoricalState(0,null));
            return null;
        });
        assertArrayEquals(snapshot,Files.readAllBytes(fixture.layout.snapshot()));
        assertArrayEquals(event1,Files.readAllBytes(fixture.layout.event(1)));assertArrayEquals(event2,Files.readAllBytes(fixture.layout.event(2)));
        assertFalse(Files.exists(fixture.layout.event(3)));assertFalse(Files.exists(missingIndex),"historical proof cannot repair an index");
        Files.writeString(fixture.layout.event(1),"{\"changed\":true}");
        assertThrows(IOException.class,()->reader.locked(session->session.requireHistoricalState(0,anchor.digest())));
    }
    /** Private immutable source fixture; the production typed Driver proof is application-owner code. */
    private record ReadProof(Pin query,Pin before,Pin after,long beforeVersion,long afterVersion) {
        ReadProof {Objects.requireNonNull(query);Objects.requireNonNull(before);Objects.requireNonNull(after);assertEquals(beforeVersion+1,afterVersion);}
        List<Pin> originals(){return List.of(query,before,after);}
    }
    private record Fixture(WriterFixture files,Layout layout,ReadProof proof) { }
    private Fixture factualFixture(String name) throws Exception {
        WriterFixture files=new WriterFixture(root.resolve(name));
        ObjectNode initial=WriterFixture.state();initial.putNull("fixture_unrelated_null");
        Files.write(files.layout.snapshot(),ContinuityJson.canonical(initial));Files.write(Path.of(files.layout.anchor().path()),ContinuityJson.canonical(initial));
        Layout layout=new Layout(files.layout.snapshot(),LedgerFiles.read(Path.of(files.layout.anchor().path()),65_536).pin().reference(),WriterFixture.MACHINE);
        Path query=layout.snapshot().resolveSibling("fixture-original-query.json"),before=layout.snapshot().resolveSibling("fixture-before-driver.json"),after=layout.snapshot().resolveSibling("fixture-after-driver.json");
        Files.writeString(query,"{\"schema\":\"fixture.read-query/v1\",\"request_id\":77,\"accepted\":true}");
        Files.writeString(before,"{\"schema\":\"fixture.driver/v1\",\"version\":0}");
        Files.writeString(after,"{\"schema\":\"fixture.driver/v1\",\"version\":1}");
        ReadProof proof=new ReadProof(LedgerFiles.read(query,65_536).pin(),LedgerFiles.read(before,65_536).pin(),LedgerFiles.read(after,65_536).pin(),0,1);
        return new Fixture(files,layout,proof);
    }
    private static TransitionAuthority factualAuthority(ReadProof proof,AtomicInteger checks,Consumer<ObjectNode> mutation){
        return new TransitionAuthority(){
            @Override public String revalidate(ContinuityState state,Request request){throw new AssertionError("factual source authority requires the actual captured Head");}
            @Override public String revalidate(Head head,Request request) throws IOException {
                checks.incrementAndGet();
                if(!DRIVER_READ_HISTORY_KIND.equals(request.kind()))throw new IOException("fixture is not another event authority");
                ObjectNode details=request.detailsObject();
                if(!StrictJson.text(details.get("expected_head")).equals(head.digest()))throw new IOException("actual original Head changed");
                if(StrictJson.integer(details.get("before_version"),0,Long.MAX_VALUE)!=proof.beforeVersion()
                        || StrictJson.integer(details.get("after_version"),0,Long.MAX_VALUE)!=proof.afterVersion())throw new IOException("actual private proof version differs");
                for(Pin pin:proof.originals())LedgerFiles.verify(pin);
                if(!request.evidence().equals(proof.originals().stream().map(Pin::reference).toList()))throw new IOException("original query/full Driver proof closure differs");
                return ContinuityJson.digest(details);
            }
            @Override public ContinuityState reduce(ContinuityState state,Request request){
                ObjectNode next=state.toJson();ObjectNode registry=next.putObject(DRIVER_READ_HISTORY_FIELD);
                registry.put("schema","fixture.driver-read-registry/v1");registry.put("version",proof.afterVersion());
                registry.put("before_driver_sha256",proof.before().reference().sha256());registry.put("after_driver_sha256",proof.after().reference().sha256());
                registry.put("original_query_sha256",proof.query().reference().sha256());
                mutation.accept(next);
                return ContinuityState.fromJson(next,state.machineId());
            }
        };
    }
    private static Request request(ContinuityWriter writer,ReadProof proof,String evidence) throws IOException {
        Head head=writer.locked(ContinuityStorePort.Session::head);
        ObjectNode details=StrictJson.object();details.put("evidence_id",evidence);details.put("source","actual-temp-originals-kernel-fixture");
        details.put("expected_head",head.digest());details.put("before_version",proof.beforeVersion());details.put("after_version",proof.afterVersion());
        return new Request(DRIVER_READ_HISTORY_KIND,ContinuityJson.canonical(details),proof.originals().stream().map(Pin::reference).toList());
    }
    @Test void factualHistoryCommitUsesHeadRevalidationAndOnlyItsRegistryChanges() throws Exception {
        assertTrue(Platform.isWindows());Fixture fixture=factualFixture("factual");AtomicInteger checks=new AtomicInteger();
        ContinuityWriter writer=new ContinuityWriter(fixture.layout(), sources(fixture.files()), factualAuthority(fixture.proof(),checks,row->{}), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        Request request=request(writer,fixture.proof(),"fixture-factual-read");
        Prepared prepared=writer.preview(request);assertEquals(1,checks.get());
        Receipt receipt=writer.commit(prepared);assertEquals(2,checks.get());assertEquals(Disposition.COMMITTED,receipt.disposition());
        assertEquals(1,receipt.head().sequence());assertEquals(1000,receipt.head().settledDateRaw());assertEquals(1,receipt.head().settledCycles());
        ObjectNode before=prepared.predecessor().state().toJson(),after=receipt.head().toJson();
        Set<String> keys=new HashSet<>();before.fieldNames().forEachRemaining(keys::add);after.fieldNames().forEachRemaining(keys::add);
        keys.removeAll(Set.of("sequence","last_event_identity",DRIVER_READ_HISTORY_FIELD));
        for(String key:keys){assertEquals(before.has(key),after.has(key),key);assertEquals(before.get(key),after.get(key),key);}
        assertTrue(after.path(DRIVER_READ_HISTORY_FIELD).isObject());
        byte[] committed=Files.readAllBytes(fixture.layout().snapshot());
        Receipt duplicate=writer.commit(prepared);assertEquals(Disposition.ALREADY_COMMITTED,duplicate.disposition());assertEquals(2,checks.get());
        assertArrayEquals(committed,Files.readAllBytes(fixture.layout().snapshot()));assertFalse(Files.exists(fixture.layout().event(2)));
    }
    @Test void historyKindCannotRemoveChangeOrAddAnyOtherFieldIncludingNullAndProgress() throws Exception {
        assertTrue(Platform.isWindows());Fixture fixture=factualFixture("overreach");
        List<Consumer<ObjectNode>> mutations=List.of(
            row->row.remove("fixture_unrelated_null"),
            row->row.put("fixture_unrelated_null","invented"),
            row->row.putNull("fixture_new_unrelated"),
            row->row.put("last_settled_date_raw",1001),
            row->row.put("last_settled_cycles",2),
            row->row.put("NEXT",11560),
            row->row.putObject("pending_cycle").put("stage","cleared"),
            row->row.remove(DRIVER_READ_HISTORY_FIELD),
            row->row.putNull(DRIVER_READ_HISTORY_FIELD)
        );
        for(int i=0;i<mutations.size();i++){
            ContinuityWriter writer=new ContinuityWriter(fixture.layout(), sources(fixture.files()), factualAuthority(fixture.proof(),new AtomicInteger(),mutations.get(i)), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
            Request input=request(writer,fixture.proof(),"overreach-"+i);
            assertThrows(ContractViolationException.class,()->writer.preview(input));
        }
        assertFalse(Files.exists(fixture.layout().event(1)));
    }
    @Test void anotherKindCannotClearTheHistoryAndChangedOriginalCannotAcquirePublication() throws Exception {
        assertTrue(Platform.isWindows());Fixture fixture=factualFixture("unrelated");
        ContinuityWriter writer=new ContinuityWriter(fixture.layout(), sources(fixture.files()), factualAuthority(fixture.proof(),new AtomicInteger(),row->{}), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        writer.commit(writer.preview(request(writer,fixture.proof(),"genuine-fixture-read")));
        for(Consumer<ObjectNode> mutation:List.<Consumer<ObjectNode>>of(
                row->row.remove(DRIVER_READ_HISTORY_FIELD),row->row.putNull(DRIVER_READ_HISTORY_FIELD),
                row->row.putObject(DRIVER_READ_HISTORY_FIELD).put("version",999))){
            ContinuityWriter wrong=new ContinuityWriter(fixture.layout(), sources(fixture.files()), new TransitionAuthority(){
                @Override public String revalidate(ContinuityState state,Request request){return ContinuityJson.digest(request.detailsObject());}
                @Override public ContinuityState reduce(ContinuityState state,Request request){ObjectNode next=state.toJson();mutation.accept(next);return ContinuityState.fromJson(next,state.machineId());}
            }, StorageWriteGuardTestSupport.forLayout(fixture.layout()));
            ObjectNode details=StrictJson.object();details.put("evidence_id","foreign");details.put("source","fixture-different-kind");
            Request other=new Request("fixture.other_kind",ContinuityJson.canonical(details),List.of());
            assertThrows(ContractViolationException.class,()->wrong.preview(other));
        }
        Fixture changed=factualFixture("changed-source");
        ContinuityWriter guarded=new ContinuityWriter(changed.layout(), sources(changed.files()), factualAuthority(changed.proof(),new AtomicInteger(),row->{}), StorageWriteGuardTestSupport.forLayout(changed.layout()));
        Prepared pending=guarded.preview(request(guarded,changed.proof(),"changed-original"));
        Files.writeString(Path.of(changed.proof().after().reference().path()),"{\"schema\":\"fixture.driver/v1\",\"version\":2}");
        assertThrows(IOException.class,()->guarded.commit(pending));assertFalse(Files.exists(changed.layout().event(1)));
    }

    @Test void rollbackPlansRetainFactualDriverHistoryAndRejectARewrittenHistoricalRegistry() throws Exception {
        assertTrue(Platform.isWindows());Fixture fixture=factualFixture("rollback-history");
        ContinuityWriter ordinary=new ContinuityWriter(fixture.layout(), sources(fixture.files()), originalAuthority(), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        ordinary.commit(ordinary.preview(WriterFixture.settled("completed-tail",1024,2)));
        ContinuityWriter writer=new ContinuityWriter(fixture.layout(), sources(fixture.files()), factualAuthority(fixture.proof(),new AtomicInteger(),row->{}), StorageWriteGuardTestSupport.forLayout(fixture.layout()));
        writer.commit(writer.preview(request(writer,fixture.proof(),"read-before-rollback")));
        Head before=writer.locked(ContinuityStorePort.Session::head);
        ObjectNode basis=StrictJson.object();basis.put("machine_id",WriterFixture.MACHINE);basis.put("completed_cycles",1);
        ObjectNode origin=basis.putObject("origin");
        for(String field:List.of("start_date_raw","target_date_raw","target_days"))origin.set(field,before.state().toJson().get(field));
        basis.putObject("frame").put("date_raw",1000);
        basis.putObject("refs").set("settled_full_response",fixture.proof().query().reference().toJson());
        ObjectNode frame=StrictJson.object();frame.put("date_raw",1024);
        // This constructs only a pure rollback plan for guard verification; no recovery eligibility or commit is granted.
        RollbackPair.Evidence evidence=new RollbackPair.Evidence(fixture.proof().query().reference(),ContinuityJson.canonical(basis),
                ContinuityJson.canonical(frame),2,fixture.proof().originals(),ContinuityJson.digest(basis));
        RollbackPair.Plan plan=RollbackPair.plan(before,evidence);
        ObjectNode original=before.state().toJson();
        for(RollbackPair.EventPlan event:List.of(plan.first(),plan.second()))
            assertEquals(original.get(DRIVER_READ_HISTORY_FIELD),event.reduced().toJson().get(DRIVER_READ_HISTORY_FIELD));
        ObjectNode reduced=plan.second().reduced().toJson();reduced.remove(DRIVER_READ_HISTORY_FIELD);
        ContinuityState forgedReduced=ContinuityState.fromJson(reduced,WriterFixture.MACHINE);
        ObjectNode committed=reduced.deepCopy();committed.put("sequence",before.state().sequence()+2);committed.put("last_event_identity",plan.second().request().identity());
        RollbackPair.EventPlan changed=new RollbackPair.EventPlan(plan.second().request(),forgedReduced,ContinuityState.fromJson(committed,WriterFixture.MACHINE));
        RollbackPair.Plan forged=new RollbackPair.Plan(plan.originalHead(),plan.evidence(),plan.first(),changed,plan.transactionId());
        assertThrows(ContractViolationException.class,()->RollbackPair.validate(forged));
        assertFalse(Files.exists(fixture.layout().event(before.state().sequence()+1)));
    }
}

package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import static org.xar.ck3.control.application.planning.family.FamilyPorts.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real sole writer/archive/FS seam; the read and Bridge edges are explicit software fixtures.
 * No installed Root/Native private permission, SEND, live marriage or gameplay authority is created. */
final class FamilyMaterialStoreWarmTransitionTest {
    private static final List<Slot> SLOTS=List.of(Slot.FAMILY,Slot.CHILD_MATRILINEAL,Slot.DEFAULT_MARRIAGE);
    private static final BridgeIdentity BRIDGE=new BridgeIdentity(55,"created");
    @TempDir Path temporary;
    private static Obj original()throws IOException {
        try(var input=FamilyMaterialStoreWarmTransitionTest.class.getResourceAsStream("/family/original-warm-material.json")) {
            assertNotNull(input,"unchanged original Python producer capture required");
            Obj captured=decode(input.readAllBytes());
            assertEquals(n(1),captured.get("test_count"));assertTrue(array(captured.get("errors")).isEmpty());assertTrue(array(captured.get("failures")).isEmpty());
            return object(array(captured.get("cases")).getFirst());
        }
    }
    private static ExactRef reference(Path path)throws IOException {
        var source=SharedSourceFiles.observe(path).source();return new ExactRef(source.path(),source.bytes(),source.sha256());
    }
    private static byte[] canonical(Obj value) {return ContinuityJson.canonical(OpportunityJson.toNode(value),ContinuityJson.DOMAIN_MAX_BYTES);}
    private static Obj empty(Slot slot) {return obj("schema",t(FamilyDomainSource.schema(slot)),"pending",Nil.INSTANCE,"resolved",Nil.INSTANCE);}
    private static byte[] initialState(String machine) {
        var state=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",machine)
                .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30)
                .put("calendar_year_days",365.25).put("start_date_raw",53215920).put("target_date_raw",53478912)
                .put("last_settled_date_raw",53215920).put("last_settled_cycles",1).put("manual_repair_count",1)
                .put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",11559);
        state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-25T20:00:00Z");state.putNull("latest_binding");
        state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);
        return ContinuityJson.canonical(state);
    }
    private static final class Fixture implements AutoCloseable {
        final Path root;final String machine;final ExactRef source;final ContinuityWriter writer;final NativeOutcomeArchive archive;
        final ImmutableArtifactStore artifacts;final FamilyMaterialStore store;final Reads reads;final FamilyDomainSource.CurrentBridge bridge;
        final PlanningRequest request;final Obj capture;final StorageWriteGuardTestSupport storage;
        final List<Query> calls=new ArrayList<>();final AtomicInteger replays=new AtomicInteger();
        final Map<Query,ObservedRead> originals=new EnumMap<>(Query.class);
        Fixture(Path root,Obj capture,boolean reopen)throws IOException {
            this.root=root;this.capture=capture;machine=WindowsJobProcess.currentMachineId();
            Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json"),lock=root.resolve("ROOT-CONTINUITY-WINDOW.lock");
            Path producer=root.resolve("software-family-source.txt");
            if(!reopen) {
                Files.createDirectory(root);Files.write(snapshot,initialState(machine));Files.write(anchor,initialState(machine));Files.createFile(lock);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.writeString(producer,"actual finite software Family writer source");
            }
            source=reference(producer);request=request(capture,machine,source);
            storage=StorageWriteGuardTestSupport.create(root,lock,32L<<20);
            artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),lock,16L<<20),storage);
            var writerRef=new AtomicReference<ContinuityWriter>();var storeRef=new AtomicReference<FamilyMaterialStore>();
            var archiveRef=new AtomicReference<NativeOutcomeArchive>();
            bridge=new FamilyDomainSource.CurrentBridge() {
                @Override public Optional<FamilyDomainSource.BridgeObservation> observe(PlanningRequest actual) {
                    assertEquals(request.before(),actual.before());return Optional.of(new FamilyDomainSource.BridgeObservation(BRIDGE,source));
                }
                @Override public boolean verifyRetained(PlanningReadReceipt read,FamilyDomainSource.BridgeObservation observed) {
                    // Explicit software Bridge seam, never the private RootFamilyBridge issuer.
                    return observed.equals(new FamilyDomainSource.BridgeObservation(BRIDGE,source))
                            && read.request().before().equals(request.before())&&read.request().source().equals(request.source())
                            && read.request().sessionId().equals(request.sessionId());
                }
            };
            var projected=new EnumMap<Query,ProjectedSource>(Query.class);
            for(Query query:List.of(Query.CURRENT_RELATION,Query.FAMILY_ALLIANCE))projected.put(query,new ProjectedSource() {
                @Override public ProjectedRead read(PlanningRequest actual,Obj arguments) {
                    assertEquals(request,actual);calls.add(query);
                    Obj result=query==Query.CURRENT_RELATION?object(capture.get("relation")):
                            obj("alliance_status",t("allied"),"played_has_recipient_alliance",new Bool(true),"recipient_has_played_alliance",new Bool(true),
                                    "relationship_status",t("marriage"),"native_revision",n(7));
                    ObservedRead original=observed(query,arguments,result,"software-family-read-"+calls.size(),archiveRef.get());
                    originals.put(query,original);return new ProjectedRead(arguments,new PlanningReadResult.Known<>(result,original.receipt(),original.originalReceipt()));
                }
                @Override public Obj decode(PlanningReadReceipt receipt) {
                    assertEquals(query.operation(),receipt.request().operation());assertEquals("software-family-contract:"+query,receipt.contractId());
                    return FamilyJson.decode(receipt.original().originalResultToken().orElseThrow().bytes());
                }
            });
            reads=new Reads(Map.of(),projected);
            var registrations=new ArrayList<DomainBodies.Registration>();
            for(Slot slot:SLOTS)registrations.add(new DomainBodies.Registration(slot,FamilyDomainSource.schema(slot),ContinuityJson.DOMAIN_MAX_BYTES,List.of(source),
                    (head,previous,input,body)-> {
                        if("software-family-original-fixture/v1".equals(text(FamilyJson.decode(input.producerInput()).get("schema")))) {
                            assertTrue(previous.isEmpty());assertArrayEquals(canonical(seed(slot)),body);
                            return ActionCodec.sha256(body);
                        }
                        replays.incrementAndGet();
                        return storeRef.get().registration(slot,List.of(source)).verifier().verify(head,previous,input,body);
                    }));
            writer=new ContinuityWriter(new Layout(snapshot,reference(anchor),machine),List.of(source),new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor,Request transition) {return ContinuityJson.digest(transition.detailsObject());}
                @Override public ContinuityState reduce(ContinuityState predecessor,Request transition) {return OriginalWindowReducer.reduce(predecessor,transition);}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(registrations,Optional.of(artifacts),Optional.empty()),storage);
            writerRef.set(writer);archive=new NativeOutcomeArchive(artifacts,writer);archiveRef.set(archive);
            store=new FamilyMaterialStore(()->writerRef.get().borrowedSession(),artifacts,archive,bridge,reads);storeRef.set(store);
            if(!reopen)writer.locked(same-> {
                for(Slot slot:SLOTS) {
                    var body=artifacts.publish(canonical(seed(slot)),ContinuityJson.DOMAIN_MAX_BYTES);
                    var input=new DomainBodies.ImportRequest(slot,FamilyDomainSource.schema(slot),body.reference(),
                            canonical(obj("schema",t("software-family-original-fixture/v1"))),List.of(source),"original-"+slot);
                    same.commitImport(same.previewImport(input));
                }
                return null;
            });
        }
        Obj seed(Slot slot) {return slot==Slot.FAMILY?object(capture.get("before")):empty(slot);}
        ObservedRead observed(Query query,Obj arguments,Obj result,String id,NativeOutcomeArchive target) {
            try {
                var read=new PlanningReadRequest(request.before(),request.source(),request.sessionId(),query.operation(),arguments,request.deadline());
                byte[] packet=NativeWire.packet(bytes(obj("type",t("command_result"),"protocol_version",n(1),"request_id",t(id),"ok",new Bool(true),"result",result)));
                var decoded=(NativeWire.CommandResult)NativeWire.decode(packet);
                var ack=new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),Optional.of(new RawJson(decoded.result().token().orElseThrow().value())),
                        new RawJson(decoded.payload().value()),decoded.packet().value());
                var evidence=new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,query.operation(),source,source,"software-family-read-authority",Instant.now(),request.deadline());
                var guard=new PlanningReadGuard(evidence,true,true,true,"d".repeat(64));
                var receipt=new PlanningReadReceipt(read,"software-family-contract:"+query,id,guard,guard,ack);
                ExactRef original=target.withSession(writer.borrowedSession()).preserveRead(receipt);
                assertEquals(receipt,target.withSession(writer.borrowedSession()).loadRead(original));
                return new ObservedRead(result,receipt,original);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        FamilyOrdinaryPolicy policy() {
            return new FamilyOrdinaryPolicy(source,new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest actual) {throw new AssertionError("only explicit software projected read seams installed");}
            },reads,new FamilyDomainSource(writer::borrowedSession,bridge),(r,operation,arguments,plan)->{throw new AssertionError("a material read cannot prepare SEND");},store,
                    new Settings(true,false,false,false,Optional.empty()));
        }
        Obj family(ContinuityStorePort.Session same)throws IOException {return FamilyDomainSource.validate(Slot.FAMILY,assertInstanceOf(DomainBodies.Available.class,same.readDomain(Slot.FAMILY)).canonicalBody());}
        @Override public void close()throws IOException {storage.close();}
    }
    private static PlanningRequest request(Obj capture,String machine,ExactRef sourceRef) {
        var source=new G2Source(machine,Instant.now().toString(),"software-family-material-store",sourceRef);
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101),BigInteger.valueOf(7),BigInteger.valueOf(53215920)),"native:7",BigInteger.valueOf(8),"robert-test");
        var before=new ObservationIdentity(machine,new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        Obj snapshot=object(capture.get("snapshot")).with("revision",n(8)).with("snapshot_id",t("native:7")).with("player_armies",rows(List.of()));
        return new PlanningRequest(before,source,"software-warm-session",Instant.now().plusSeconds(120),new PlanningObservation(snapshot,List.of(),Set.of(new OperationKey("life-advance")),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
    }
    private static OrdinaryPolicy.Draft baseline(PlanningRequest request) {
        var expected=new ExpectedPostcondition(org.xar.ck3.control.g2.planning.ProposalLifecycle.POSTCONDITION_VERSION,request.before(),request.source(),"software-family-existing-action/v1",List.of(new ExpectedBoolean(new FieldKey("retained_software_turn"),true)));
        var command=new ActionCommand("existing-life",request.before(),request.source(),request.sessionId(),new OperationKey("life-advance"),obj(),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
        return new OrdinaryPolicy.Draft("one-life-turn-v1","peace_growth","retain original software turn",OrdinaryPolicy.Kind.ORDINARY,Optional.of(command),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),obj("selected_step",t("life-advance")));
    }
    @Test void actualOrdinaryPolicyImportsWarmMaterialAndFreshAllianceThroughOneWriterAndColdFilesystem()throws Exception {
        Obj capture=original();Path root=temporary.resolve("writer");byte[] committed;
        try(var f=new Fixture(root,capture,false)) {
            f.writer.locked(same->{
                var policy=f.policy();long sequence=same.head().state().sequence();
                assertInstanceOf(OrdinaryPolicy.Refresh.class,policy.evaluate(f.request,baseline(f.request)));
                assertEquals(object(capture.get("after")),f.family(same));assertEquals(sequence+1,same.head().state().sequence());
                assertNull(object(f.family(same).get("resolved")).get("alliance_result"));assertTrue(f.replays.get()>=2,"preview and commit must rerun the real registration");
                assertEquals(List.of(Query.CURRENT_RELATION),f.calls);
                assertInstanceOf(OrdinaryPolicy.Refresh.class,policy.evaluate(f.request,baseline(f.request)));
                assertEquals(List.of(Query.CURRENT_RELATION,Query.CURRENT_RELATION,Query.FAMILY_ALLIANCE),f.calls);
                Obj resolved=object(f.family(same).get("resolved"));assertEquals(t("marriage"),resolved.get("status"));
                assertEquals(t("marriage"),object(resolved.get("alliance_result")).get("relationship_status"));
                assertEquals(object(object(capture.get("before")).get("resolved")).get("source_pending"),resolved.get("source_pending"));
                assertEquals(sequence+2,same.head().state().sequence());return null;
            });
            committed=f.writer.locked(same->canonical(f.family(same)));
        }
        try(var cold=new Fixture(root,capture,true)) {
            cold.writer.locked(same->{assertArrayEquals(committed,canonical(cold.family(same)));assertEquals(5,same.head().state().sequence());return null;});
        }
    }
    @Test void forgedObservedValueCannotOverrideTheRealArchivedDecoderOrChangeTheCanonicalHead()throws Exception {
        Obj capture=original();
        try(var f=new Fixture(temporary.resolve("writer"),capture,false)) {
            f.writer.locked(same->{
                Obj args=obj("expected_native_revision",n(7));
                Obj originalRelation=object(capture.get("relation")).with("primary_spouse_character_id",n(400));
                ObservedRead actual=f.observed(Query.CURRENT_RELATION,args,originalRelation,"forged-value",f.archive);
                String before=same.head().digest();
                assertFalse(f.store.consume(f.request,Query.CURRENT_RELATION,args,new ObservedRead(object(capture.get("relation")),actual.receipt(),actual.originalReceipt())));
                assertEquals(before,same.head().digest());assertEquals(object(capture.get("before")),f.family(same));return null;
            });
        }
    }
    @Test void receiptOperationCannotBeRelabeledAsAWarmReadAndFailedImportLeavesPendingMaterial()throws Exception {
        Obj capture=original();
        try(var f=new Fixture(temporary.resolve("writer"),capture,false)) {
            f.writer.locked(same->{
                Obj args=obj("expected_native_revision",n(7));var actual=f.observed(Query.FAMILY_ALLIANCE,args,object(capture.get("relation")),"wrong-operation",f.archive);
                String before=same.head().digest();assertFalse(f.store.consume(f.request,Query.CURRENT_RELATION,args,actual));
                assertEquals(before,same.head().digest());assertEquals(object(capture.get("before")),f.family(same));return null;
            });
        }
    }
    @Test void corruptedArchivedReceiptIsRejectedBeforeAnotherCanonicalImport()throws Exception {
        Obj capture=original();
        try(var f=new Fixture(temporary.resolve("writer"),capture,false)) {
            f.writer.locked(same->{
                Obj args=obj("expected_native_revision",n(7));var actual=f.observed(Query.CURRENT_RELATION,args,object(capture.get("relation")),"mutated-receipt",f.archive);
                String before=same.head().digest();Files.writeString(Path.of(actual.originalReceipt().path()),"{\"corrupt\":true}");
                assertThrows(UncheckedIOException.class,()->f.store.consume(f.request,Query.CURRENT_RELATION,args,actual));
                assertEquals(before,same.head().digest());assertEquals(object(capture.get("before")),f.family(same));return null;
            });
        }
    }
}

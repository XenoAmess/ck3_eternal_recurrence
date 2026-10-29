package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.military.WarDeclarationContinuity;
import org.xar.ck3.control.application.planning.warentry.PeacetimeWarEntryPlanner;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Original golden TOP -> full Driver/canonical action -> ordinary snapshot -> cold DATA replay.
 * The storage boundary is in memory; no native readiness, submit, Game or real SAVE is manufactured.
 */
final class DriverDeclarationContinuityStateTest {
    private static final Instant DEADLINE=Instant.parse("2030-01-01T00:00:00Z");
    private static final String ID="909-17-0",STEP="declare-war-"+ID;
    private static Obj obj(ObjectNode n){return DriverJson.object(StrictJson.canonical(n),DriverJson.MAX_NATIVE_BYTES);}
    private static ObjectNode objectNode(com.fasterxml.jackson.databind.JsonNode value){return assertInstanceOf(ObjectNode.class,value);}
    private static ObjectNode node(Value value){return objectNode(toNode(value));}
    private static byte[] packet(ObjectNode n){byte[] bytes=StrictJson.canonical(n);return ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();}
    private record Observed(NativeObservationPort.ObservedFrame nativeFrame,Known known,Complete frame) { }
    private static final class Fixture {
        final Archive archive=new Archive();final ObjectNode donor;
        final WriterContracts.Head initial=head(0,Optional.empty());
        final AtomicReference<WriterContracts.Head> current=new AtomicReference<>(initial);
        final ContinuityStorePort.Session same;
        final NativeRecordedEvidenceVerifier verifier;
        final Observed before;final Known initialized;
        Fixture()throws Exception {
            try(var input=DriverDeclarationContinuityStateTest.class.getResourceAsStream("/declarationcontinuity/original-coalition-base.json")){
                assertNotNull(input);var resource=objectNode(StrictJson.parse(input.readAllBytes()));
                assertEquals("7b90bd8ca10faea6d70d687f803ebc2883ebb55c74820cc6104132d2dd42b703",resource.path("source_sha256").textValue());
                donor=objectNode(resource.get("base")).deepCopy();
            }
            same=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{
                if(method.getName().equals("head"))return current.get();
                if(method.getName().equals("requireHistoricalState")){
                    assertEquals(initial.state().sequence(),args[0]);assertEquals(initial.digest(),args[1]);return initial.state();
                }
                throw new AssertionError("declaration DATA may not write or query another session: "+method.getName());
            });
            archive.bind(same);
            verifier=new NativeRecordedEvidenceVerifier(archive,()->same,(session,ref,maximum)->{
                assertSame(same,session);byte[] bytes=archive.nativeFrames.containsKey(ref)?archive.loadNativeFrame(ref):archive.loadMaterial(ref).bytes();
                assertTrue(bytes.length<=maximum);return bytes;
            },new DriverFrameEvidenceLoader(new DriverObservationAssembler()),List.of());
            before=observe(new Obj(Map.of()),9,2,false);
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=archive.preserveMaterial(new RawJson("{\"scope\":\"software-canonical-declaration\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(before.frame(),before.known(),configuration,presentation,policy,archive);
            initialized=with(before.known(),produced.auxiliary());
        }
        Observed observe(Obj auxiliary,int nativeRevision,int publicRevision,boolean match) {
            ObjectNode state=objectNode(StrictJson.parse(DriverObservationAssemblerTest.STATE.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            ObjectNode diagnostic=state.putObject("diagnostics").put("bridge_pid",42).put("connection_generation",5);
            diagnostic.set("hello",donor.path("snapshot").path("diagnostics").path("hello").deepCopy());objectNode(diagnostic.get("hello")).put("pid",42);
            state.set("declarable_wars",donor.path("snapshot").path("declarable_wars").deepCopy());
            if(match)state.putArray("active_wars").addObject().put("war_id",8).put("player_side","attacker")
                    .put("player_is_primary_war_leader",true).put("primary_opponent_character_id",909).putArray("targeted_title_ids").add(91);
            ObjectNode top=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","snapshot-"+nativeRevision).put("revision",nativeRevision);top.set("state",state);
            var actual=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine",DriverStateAssemblerTest.game(),BigInteger.valueOf(5),"held-session"),
                    "snapshot-"+nativeRevision,BigInteger.valueOf(nativeRevision),new RawJson(StrictJson.canonical(state)),packet(top),Instant.parse("2026-10-23T16:00:00Z").plusSeconds(nativeRevision));
            Known legacy=DriverStateAssemblerTest.known();var driver=new DriverStateSnapshot.Complete(legacy.driver().session(),List.of(),legacy.driver().lastCheckpoint(),legacy.driver().rollbackWarFailure(),
                    legacy.driver().managedRestoreTransaction(),legacy.driver().successionExpectation(),legacy.driver().successionLifecycle(),legacy.driver().campaignGoal(),legacy.driver().rollbackWarFailures());
            var full=archive.preserveMaterial(new RawJson(driver.encode()));var stamp=new DriverSnapshotFacts.Stamp(3,7,legacy.stamp().game(),driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
            Known bare=new Known(driver,stamp,full,List.of(),auxiliary,Optional.empty(),Optional.empty());
            var fields=new java.util.LinkedHashMap<>(auxiliary.members());fields.put("backend_id",new Text("native-headless"));fields.put("source",new Text("injected-dll-named-pipe"));fields.put("diagnostics",obj(diagnostic));
            RawJson manifest=DriverObservationEvidenceReader.encode(bare,actual,BigInteger.valueOf(publicRevision),1,DriverStateAssemblerTest.source(),new Obj(fields),full);
            ExactRef ref=archive.preserveMaterial(manifest);var facts=DriverObservationEvidenceReader.decode(ref,manifest,new RawJson(driver.encode()),actual);
            var known=new Known(driver,stamp,full,List.of(),auxiliary,Optional.empty(),Optional.of(facts));
            var frame=assertInstanceOf(Complete.class,new DriverObservationAssembler().assemble(actual,facts,archive.preserveNativeFrame(actual)));return new Observed(actual,known,frame);
        }
        GuardEvidence guard(OperationKey operation) {
            Complete frame=before.frame();var known=before.known();
            var semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
            var stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
            var hello=archive.retainPacket(packet(StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42).put("connection_generation",5)));
            var heartbeat=archive.retainPacket(packet(StrictJson.object().put("type","heartbeat").put("protocol_version",1).put("pid",42).put("sequence",0).put("monotonic_ms",0)));
            Obj capabilities=new Obj(Map.of());var cap=archive.preserveMaterial(new RawJson(DriverJson.encode(capabilities)));
            var unqualified=archive.preserveMaterial(new RawJson("{\"scope\":\"unqualified-software-data\"}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            var evidence=new SessionPorts.SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,known.originalHistoryBasis(),frame.observedAt());
            var lease=new ReadinessAuthority.LeaseSnapshot(frame,known,capabilities,evidence,Set.of(),Set.of(),hello,heartbeat,DEADLINE,unqualified);
            var basis=RootGuardEvidence.preserve(lease,operation,"software-source-only",cap,archive,initial);
            return new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),operation,frame.originalEvidence(),hello,"software-source-only",frame.observedAt(),DEADLINE,List.of(basis));
        }
        PlanningReadReceipt read(String requestId,String operation,Obj arguments,ObjectNode top) {
            top.put("request_id",requestId);ObjectNode result=objectNode(top.get("result"));var key=new OperationKey(operation);
            var request=new PlanningReadRequest(before.frame().identity(),before.frame().source(),before.frame().sessionId(),key,arguments,DEADLINE);
            var binding=guard(key);var held=new PlanningReadGuard(binding,true,true,true,before.frame().fullBindingSha256());
            var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(new RawJson(StrictJson.canonical(result))),new RawJson(StrictJson.canonical(top)),packet(top));archive.preserve(ack);
            var read=new PlanningReadReceipt(request,"software-original-"+operation,requestId,held,held,ack);archive.preserveRead(read);return read;
        }
        ActionCommand command() {
            var revision=new ArmyCalls.Revision(new ArmyTypes.Present<>(before.frame().identity().frame().revision()));
            var declarationCall=new ArmyCalls.Declaration(PublicMethod.DECLARE_WAR,revision,ID);
            ObjectNode choices=StrictJson.object().put("type","command_result").put("protocol_version",1).put("ok",true);
            ObjectNode result=choices.putObject("result").put("step","query-declarable-wars").put("accepted",true).put("status","available").put("query_sequence",12);
            result.set("declarable_wars",donor.path("snapshot").path("declarable_wars").deepCopy());
            var first=read("original-declarations","query-declarable-wars",DriverJson.object(ArmyCallCodec.encode(new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,revision)).bytes(),32768),choices);
            ObjectNode coalition=objectNode(donor.get("frame")).deepCopy();ObjectNode domain=objectNode(coalition.path("result").get("prewar_force_coalition_coverage_v2"));
            domain.put("actor_character_id",73).put("native_revision",9).put("public_revision",2).put("date_raw",53144328);
            objectNode(domain.get("final_cb_roles")).put("primary_attacker_character_id",73);objectNode(domain.path("owner_forces").get(0)).put("owner_character_id",73);
            var second=read("original-final-roles","query-prewar-force-coalition-coverage-v2",DriverJson.object(ArmyCallCodec.encode(new ArmyCalls.Declaration(PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V2,revision,ID)).bytes(),32768),coalition);
            var args=new ArmyOrdinaryActionArguments(ArmyOrdinaryActionArguments.Kind.DECLARE_WAR,ArmyCallCodec.encode(declarationCall),List.of(archive.readReferenceOf(first),archive.readReferenceOf(second)));
            var operation=new OperationKey(STEP);var expected=NativeArmyWarWindowEffects.expected(before.frame().identity(),before.frame().source(),operation,args.raw());
            return new ActionCommand("original-declaration",before.frame().identity(),before.frame().source(),before.frame().sessionId(),operation,args.encode(),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),DEADLINE);
        }
        ActionState.Attempt attempt(ActionCommand command) {
            var prepared=new NativeRequest(STEP,Optional.empty(),new RawJson(new byte[]{'{','}'}));archive.preserveRequest(prepared);
            return new ActionState.Attempt("original-native-declaration",before.frame().observedAt(),guard(command.operation()),prepared);
        }
        NativeActionPort.AckReceived ack(ActionState.Attempt attempt,boolean nativeOk,boolean accepted) {
            ObjectNode top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",attempt.requestId()).put("ok",nativeOk);
            Optional<RawJson> token=Optional.empty();if(nativeOk){var result=top.putObject("result").put("step",STEP).put("accepted",accepted);token=Optional.of(new RawJson(StrictJson.canonical(result)));}else top.put("error","original native refusal");
            var ack=new NativeActionPort.AckReceived(attempt.requestId(),nativeOk,token,new RawJson(StrictJson.canonical(top)),packet(top));archive.preserve(ack);return ack;
        }
        ActionReceipt retain(ActionCommand command,ActionState state) {
            var intent=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());archive.preserveReceipt(intent);
            var first=archive.preserveRecord(new ActionRecord(intent,Optional.empty()));
            if(state instanceof ActionState.IntentDurable){current.set(head(1,Optional.of(first)));return intent;}
            var receipt=new ActionReceipt(1,2,command,ActionCodec.bodySha256(command),state);archive.preserveReceipt(receipt);
            current.set(head(2,Optional.of(archive.preserveRecord(new ActionRecord(receipt,Optional.of(first))))));return receipt;
        }
        Obj publish(Observed observed) throws IOException {
            return archive.borrowed(same,bound -> {
                var canonical=ContinuityActionJournal.receipts(current.get().state(),bound);
                var persistent=DriverPersistentPlanningState.declarationContinuity(same,observed.frame(),observed.known(),canonical,verifier,bound);
                var produced=DriverCapabilityStateProducer.observePersistentPlanning(observed.frame(),observed.known(),persistent,bound);
                var repository=new DriverFactsRepository(observed.known());repository.locked(known->{repository.publishCapabilityInputs(observed.known().stamp(),produced.expectedAuxiliarySha256(),produced);return null;});
                return repository.locked(known->assertInstanceOf(Known.class,known).auxiliary());
            });
        }
    }
    @Test void acceptedWithoutWarPublishesToOrdinaryThenColdReplayContinuesTheSameTicket() throws Exception {
        var f=new Fixture();var command=f.command();var attempt=f.attempt(command);var ack=f.ack(attempt,true,true);
        f.retain(command,new ActionState.Unknown(Optional.of(attempt),Optional.of(ack),"accepted awaiting unique war",List.of(f.before.frame().originalEvidence())));
        var current=f.observe(f.initialized.auxiliary(),10,3,false);Obj auxiliary=f.publish(current);
        var joined=f.observe(auxiliary,10,3,false);Obj record=object(joined.frame().semantic().get(DriverDeclarationContinuityState.KEY),"original declaration");
        assertEquals(new Text("declaration_submitted"),record.get("status"));assertEquals(new Text(attempt.requestId()),record.get("request_id"));assertEquals(new Bool(false),record.get("in_flight"));
        Obj history=new Obj(Map.of("command",new Text(STEP),"ok",new Bool(true),"index",new IntegerValue(BigInteger.ONE)));
        Obj plan=PeacetimeWarEntryPlanner.select(joined.frame().semantic(),List.of(history),Set.of("life-advance")).orElseThrow();
        assertEquals(new Text("native_war_declaration_pending"),plan.get("phase"));assertEquals(new Text("life-advance"),plan.get("selected_step"));
        var semantic=f.archive.preserveMaterial(new RawJson(DriverJson.encode(joined.frame().semantic())));var stamp=f.archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(joined.frame(),joined.known())));
        var evidence=new SessionPorts.SemanticEvidence(joined.frame().identity(),semantic,joined.frame().originalEvidence(),stamp,joined.known().originalHistoryBasis(),joined.frame().observedAt());
        var recovered=f.archive.inSession(f.same,bound -> new RestoreCapabilityAdoption(bound).replay(f.same,evidence,joined.known().driver()));
        assertEquals(auxiliary,recovered.ownerAuxiliary());DriverPersistentPlanningState.replay(recovered.ownerAuxiliary(),f.archive);
        var following=f.observe(recovered.ownerAuxiliary(),11,4,true);Obj completed=f.publish(following);
        var started=WarDeclarationContinuity.decode(DriverJson.encode(completed.get(DriverDeclarationContinuityState.KEY)));
        assertEquals(attempt.requestId(),started.origin().requestId());assertEquals(WarDeclarationContinuity.Status.WAR_STARTED,started.status());assertEquals(8,started.warId().orElseThrow());
        assertFalse(((Bool)WarDeclarationContinuity.json(started).get("request_retried")).value());assertFalse(ContinuityActionJournal.receipts(f.current.get().state(),f.archive).getFirst().settled());
    }
    @Test void unknownWithMatchingWarDoesNotInventAckAndTamperedOrDetachedSourcesFail() throws Exception {
        var f=new Fixture();var command=f.command();var attempt=f.attempt(command);
        f.retain(command,new ActionState.Unknown(Optional.of(attempt),Optional.empty(),"original response unknown",List.of(f.before.frame().originalEvidence())));
        var current=f.observe(f.initialized.auxiliary(),10,3,true);Obj auxiliary=f.publish(current);
        var record=WarDeclarationContinuity.decode(DriverJson.encode(auxiliary.get(DriverDeclarationContinuityState.KEY)));
        assertEquals(WarDeclarationContinuity.Status.SUBMISSION_UNKNOWN,record.status());assertFalse(record.postconditionVerified());assertFalse(record.inFlight());
        var view=current.frame().semantic().with(DriverDeclarationContinuityState.KEY,auxiliary.get(DriverDeclarationContinuityState.KEY));
        assertEquals(Nil.INSTANCE,PeacetimeWarEntryPlanner.select(view,List.of(),Set.of("life-advance")).orElseThrow().get("selected_step"));
        Obj forged=auxiliary.with(DriverDeclarationContinuityState.KEY,WarDeclarationContinuity.json(record).with("native_response",new Text("accepted")));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(forged,f.archive));
        assertThrows(IllegalArgumentException.class,()->f.archive.borrowed(f.same,bound -> DriverPersistentPlanningState.declarationContinuity(f.same,current.frame(),current.known(),List.of(),f.verifier,bound)));
        var original=DriverObservationEvidenceReader.reference(auxiliary.get(DriverDeclarationContinuityState.SOURCE));f.archive.materials.put(original,new RawJson(new byte[]{'{','}'}));
        assertThrows(IllegalArgumentException.class,()->DriverPersistentPlanningState.replay(auxiliary,f.archive));
    }
    @Test void submittingRejectedAndPreGuardIntentKeepTheirDistinctCanonicalMeanings() throws Exception {
        for(int variant=0;variant<5;variant++){
            var f=new Fixture();var command=f.command();var attempt=f.attempt(command);ActionState state;
            if(variant==0)state=new ActionState.Submitting(attempt);
            else if(variant==1)state=new ActionState.Unknown(Optional.of(attempt),Optional.of(f.ack(attempt,false,false)),"native refused",List.of());
            else if(variant==2)state=new ActionState.Unknown(Optional.of(attempt),Optional.of(f.ack(attempt,true,false)),"native accepted=false",List.of());
            else if(variant==3){var outcome=new NativeActionPort.RejectedBeforeDispatch(attempt.requestId(),new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"actual local primitive rejection",Optional.empty()));f.archive.preserve(outcome);state=new ActionState.RejectedBeforeDispatch(attempt,outcome);}
            else state=new ActionState.IntentDurable();
            f.retain(command,state);Obj auxiliary=f.publish(f.observe(f.initialized.auxiliary(),10,3,false));DriverPersistentPlanningState.replay(auxiliary,f.archive);
            if(variant==4){assertEquals(Nil.INSTANCE,auxiliary.get(DriverDeclarationContinuityState.KEY));continue;}
            var record=WarDeclarationContinuity.decode(DriverJson.encode(auxiliary.get(DriverDeclarationContinuityState.KEY)));
            assertEquals(variant==0?WarDeclarationContinuity.Status.SUBMISSION_UNKNOWN:variant==3?WarDeclarationContinuity.Status.NOT_SUBMITTED:WarDeclarationContinuity.Status.NATIVE_REJECTED,record.status());
            assertEquals(variant==0,record.inFlight());assertEquals(attempt.requestId(),record.origin().requestId());
        }
    }
    private static Known with(Known current,Obj auxiliary){return new Known(current.driver(),current.stamp(),current.originalHistoryBasis(),current.actionRows(),auxiliary,current.loop(),current.observation());}
    private static WriterContracts.Head head(long sequence,Optional<ExactRef> record){
        var state=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id","test-machine").put("sequence",sequence).put("window_id",1).put("status","running")
                .put("target_days",10).put("start_date_raw",53144328).put("target_date_raw",53144568).put("last_settled_date_raw",53144328).put("last_settled_cycles",0);state.putObject("UNKNOWN");
        record.ifPresent(ref->state.set(ContinuityActionJournal.STATE_FIELD,ref.toJson()));return new WriterContracts.Head(ContinuityState.fromJson(state,"test-machine"),List.of(),List.of(),List.of(),false);
    }

    @Test void archiveBorrowerMustOwnTheActiveSameHeadScopeAndCannotEscapeIt() throws Exception {
        var f=new Fixture();var bytes=new RawJson("{\"original\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var ref=f.archive.preserveMaterial(bytes);var escaped=new AtomicReference<ActionPorts.OutcomeArchive>();
        assertThrows(IllegalArgumentException.class,()->f.archive.withSession(f.same));
        f.archive.inSession(f.same,bound -> {
            assertEquals(bytes,bound.loadMaterial(ref));escaped.set(bound);
            assertThrows(IllegalArgumentException.class,()->f.archive.withSession(DriverCapabilityStateProducerTest.nullSession()));
            return null;
        });
        assertThrows(IllegalArgumentException.class,()->escaped.get().loadMaterial(ref));
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private ContinuityStorePort.Session owner;
        private Thread ownerThread;
        private WriterContracts.Head scopeHead;
        private int activeDepth;
        void bind(ContinuityStorePort.Session original) {
            StrictJson.require(owner==null,"fixture archive owner already bound");
            owner=java.util.Objects.requireNonNull(original);ownerThread=Thread.currentThread();
        }
        private WriterContracts.Head actualHead() {
            try { return owner.head(); } catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
        private void requireScope(ContinuityStorePort.Session borrowed) {
            StrictJson.require(owner==borrowed && ownerThread==Thread.currentThread() && activeDepth>0
                    && scopeHead==actualHead(),"fixture archive requires its actual same-thread borrowed head scope");
        }
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session borrowed) {
            requireScope(borrowed);
            return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                    (proxy,method,args)->{
                        requireScope(borrowed);
                        try { return method.invoke(this,args); }
                        catch(java.lang.reflect.InvocationTargetException failure) { throw failure.getCause(); }
                    });
        }
        @FunctionalInterface private interface BorrowedWork<T> { T apply(ActionPorts.OutcomeArchive bound) throws IOException; }
        <T>T borrowed(ContinuityStorePort.Session borrowed,BorrowedWork<T> work) throws IOException {
            try { return inSession(borrowed,bound -> {
                try { return work.apply(bound); } catch(IOException failure) { throw new java.io.UncheckedIOException(failure); }
            }); } catch(java.io.UncheckedIOException failure) { throw failure.getCause(); }
        }
        @Override public <T>T inSession(ContinuityStorePort.Session borrowed,java.util.function.Function<ActionPorts.OutcomeArchive,T> work) {
            StrictJson.require(owner==borrowed && ownerThread==Thread.currentThread(),"foreign fixture archive borrower/thread");
            var previous=scopeHead;var head=actualHead();if(activeDepth>0)requireScope(borrowed);
            scopeHead=head;activeDepth++;
            try { return work.apply(withSession(borrowed)); }
            finally {
                boolean unchanged=actualHead()==head;activeDepth--;scopeHead=previous;
                StrictJson.require(unchanged,"read-only fixture reducer changed the borrowed canonical head");
            }
        }
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,byte[]> nativeFrames=new HashMap<>();
        final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();final Map<ExactRef,NativeRequest> requests=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        final Map<ExactRef,ActionReceipt> receipts=new HashMap<>();final Map<ExactRef,ActionRecord> records=new HashMap<>();
        private static ExactRef ref(String kind,byte[] bytes){return new ExactRef("D:/test-memory/declaration/"+kind+"/"+DriverJson.sha256(bytes),bytes.length,DriverJson.sha256(bytes));}
        private static byte[] dispatchBytes(NativeActionPort.DispatchOutcome value){return value instanceof NativeActionPort.AckReceived ack?ack.originalPacket():value instanceof NativeActionPort.Unknown unknown?unknown.originalRequestPacket():((NativeActionPort.RejectedBeforeDispatch)value).proof().reason().getBytes(java.nio.charset.StandardCharsets.UTF_8);}
        private static byte[] requestBytes(NativeRequest value){return StrictJson.canonical(StrictJson.object().put("step",value.step()).put("capability",value.requiredCapability().orElse("")).put("fields",DriverJson.sha256(value.additionalFields().bytes())));}
        private static byte[] readBytes(PlanningReadReceipt value){return StrictJson.canonical(StrictJson.object().put("id",value.requestId()).put("contract",value.contractId()).put("frame",value.before().originalBindingSha256()).put("outcome",DriverJson.sha256(value.original().originalPacket())));}
        private static <T>T get(Map<ExactRef,T> values,ExactRef ref){T value=values.get(ref);if(value==null)throw new IllegalArgumentException("original archive entry absent: "+ref.path());return value;}
        private static <T>ExactRef known(Map<ExactRef,T> values,ExactRef ref,T value){require(value.equals(get(values,ref)),"original archive object changed");return ref;}
        private static void require(boolean condition,String reason){StrictJson.require(condition,reason);}
        @Override public ExactRef preserveMaterial(RawJson value){var ref=ref("material",value.bytes());materials.putIfAbsent(ref,value);return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){return get(materials,ref);}
        @Override public RawJson loadFullMaterial(ExactRef ref){var value=loadMaterial(ref);require(value.bytes().length==ref.bytes()&&DriverJson.sha256(value.bytes()).equals(ref.sha256()),"original full material changed");return value;}
        @Override public ExactRef materialReferenceOf(RawJson value){return known(materials,ref("material",value.bytes()),value);}
        ExactRef retainPacket(byte[] value){var ref=ref("packet",value);nativeFrames.putIfAbsent(ref,value.clone());return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){var ref=ref("native",value.originalPacket());nativeFrames.putIfAbsent(ref,value.originalPacket());return ref;}
        @Override public byte[] loadNativeFrame(ExactRef ref){return get(nativeFrames,ref).clone();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){var ref=ref("outcome",dispatchBytes(value));outcomes.putIfAbsent(ref,value);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return get(outcomes,ref);}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return known(outcomes,ref("outcome",dispatchBytes(value)),value);}
        @Override public ExactRef preserveRequest(NativeRequest value){var ref=ref("request",requestBytes(value));requests.putIfAbsent(ref,value);return ref;}
        @Override public NativeRequest loadRequest(ExactRef ref){return get(requests,ref);}
        @Override public ExactRef requestReferenceOf(NativeRequest value){return known(requests,ref("request",requestBytes(value)),value);}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){var ref=ref("read",readBytes(value));reads.putIfAbsent(ref,value);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return get(reads,ref);}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){return known(reads,ref("read",readBytes(value)),value);}
        @Override public ExactRef preserveReceipt(ActionReceipt value){var ref=ref("receipt",ActionReceiptCodec.encodeReceipt(value,this));receipts.putIfAbsent(ref,value);return ref;}
        @Override public ActionReceipt loadReceipt(ExactRef ref){return get(receipts,ref);}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){return known(receipts,ref("receipt",ActionReceiptCodec.encodeReceipt(value,this)),value);}
        @Override public ExactRef preserveRecord(ActionRecord value){var ref=ref("record",ActionRecordCodec.encode(value,this));records.putIfAbsent(ref,value);return ref;}
        @Override public ActionRecord loadRecord(ExactRef ref){return get(records,ref);}
        @Override public ExactRef recordReferenceOf(ActionRecord value){return known(records,ref("record",ActionRecordCodec.encode(value,this)),value);}
    }
}

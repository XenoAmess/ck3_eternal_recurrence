package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Original captured Python data -> real typed family/decoder -> archived replay/history -> public64.
 * The framed transport below is software test data and grants no Game, source or native qualification. */
final class ContactScopeReadProducerTest {
    private static final ExactRef SOURCE=new ExactRef("software-contact-read-definition",1,"a".repeat(64));
    private static final Instant OBSERVED=Instant.parse("2026-10-24T00:00:00Z"),DEADLINE=OBSERVED.plusSeconds(60);
    @Test void projectedAndActualOriginalBodiesReachTheirIdenticalFamiliesHistoryAndPublicConsumers()throws Exception {
        for(boolean projected:List.of(true,false)) {
            Fixture fixture=fixture(projected);Held held=new Held(fixture.snapshot());
            var producer=new ContactScopeReads(SOURCE,SOURCE,held,held.archive,held::load,()->held.session);
            var catalog=new RootReadContractCatalog(List.of(),producer.families());
            var selection=ContactScopeReads.Selection.current(fixture.query(),held.complete,DEADLINE);
            held.last=producer.contract(catalog,selection);
            held.result=nativeResult(selection,fixture.scope());
            assertEquals(projected,held.result.has("backend_id"));
            if(projected) {
                ObjectNode missingBackend=held.result.deepCopy();missingBackend.remove("backend_id");
                assertThrows(IllegalArgumentException.class,()->ContactScopeReads.normalize(selection,missingBackend));
            }
            List<String> invalidBackends=projected?List.of("null","true","1","1.0","\"\"","\"   \"")
                    :List.of("null","true","1","1.0","\"\"","\"   \"","\"native-headless\"","\"unexpected-backend\"");
            for(String token:invalidBackends) {
                ObjectNode malformed=held.result.deepCopy();
                malformed.set("backend_id",parse(("{\"value\":"+token+"}").getBytes(StandardCharsets.UTF_8)).get("value"));
                assertThrows(IllegalArgumentException.class,()->ContactScopeReads.normalize(selection,malformed),token);
            }
            PlanningReadResult<ContactScopeObservation> actual=producer.collect(held.session,catalog,selection);
            assertTrue(actual instanceof PlanningReadResult.Known<ContactScopeObservation>);
            var known=(PlanningReadResult.Known<ContactScopeObservation>)actual;
            assertEquals(projected,known.value().backendId().isPresent());
            if(projected)assertEquals("native-headless",known.value().backendId().orElseThrow());
            Optional<String> invalidBackend=projected?Optional.empty():Optional.of("native-headless");
            assertThrows(IllegalArgumentException.class,()->new ContactScopeObservation(known.value().query(),known.value().scope(),
                    known.value().querySequence(),invalidBackend,known.value().capture()));
            assertEquals(fixture.scope(),parse(bytes(known.value().scope().nativeJson())));assertEquals(1,held.nativeCalls);
            assertSame(held.last,catalog.contracts().getFirst());assertTrue(held.last.hasPureReplay());
            assertEquals(known.value(),held.last.replay(known.receipt()));assertEquals(1,held.nativeCalls,"archived replay must not dispatch");
            var response=ContactScopePublicCodec.capture(fixture.query(),actual);
            RawJson wire=ContactScopePublicCodec.encode(response);assertEquals(response,ContactScopePublicCodec.decode(wire));
            RawJson originalWire=ContactScopePublicCodec.encodeOriginal(known.value());
            assertEquals(known.value(),ContactScopePublicCodec.decodeOriginal(originalWire));
            ObjectNode generic=parse(originalWire.bytes()),dedicated=parse(wire.bytes());
            assertFalse(generic.has("original_read_receipt"));dedicated.remove("original_read_receipt");assertEquals(generic,dedicated);
            assertEquals(projected,generic.has("backend_id"));assertEquals(projected,dedicated.has("backend_id"));
            ObjectNode publicObject=parse(wire.bytes());assertTrue(publicObject.get("queried_revision").isTextual());
            assertTrue(publicObject.get("query_sequence").isTextual());
            ObjectNode scope=object(publicObject.get(projected?"projected_contact_scope":"actual_contact_scope"));
            assertTrue(scope.get("snapshot_revision").isTextual());assertTrue(scope.get("subject_army_id").isIntegralNumber());
            assertTrue(DriverReadHistoryRowProducer.shouldRecord(known));
            var candidate=DriverReadHistoryRowProducer.prepare(held.archive,catalog,held.last,known,1);
            assertEquals(known.value().normalizedResult(),candidate.row().result());
            assertEquals(candidate.row(),DriverReadHistoryRowProducer.decode(candidate.row().encode()));
            assertEquals(known,DriverReadHistoryRowProducer.replayCanonical(held.archive,catalog,held.last,candidate.row()));
            assertSame(candidate,DriverReadHistoryRowProducer.replay(held.archive,catalog,held.last,known,candidate));
            assertEquals(projected?"PROJECTED_CONTACT_SCOPE":"ACTUAL_CONTACT_SCOPE",candidate.provenance().kind().name());
            Obj row=candidate.row().toJson();Obj result=candidate.row().result();
            assertEquals(projected,result.members().containsKey("backend_id"));
            for(String field:List.of("queried_episode_run_id","queried_connection_generation","step")) {
                Obj changed=row.with("result",result.with(field,new OpportunityJson.Text("wrong")));
                assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(changed)));
            }
            Obj provenance=OpportunityJson.object(row.get(DriverReadHistoryRowProducer.SOURCE_FIELD),"source");
            Obj wrongKind=row.with(DriverReadHistoryRowProducer.SOURCE_FIELD,provenance.with("kind",new OpportunityJson.Text(projected?"ACTUAL_CONTACT_SCOPE":"PROJECTED_CONTACT_SCOPE")));
            assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(wrongKind)));
            String payload=projected?"projected_contact_scope":"actual_contact_scope";
            Obj originalScope=OpportunityJson.object(result.get(payload),"scope");
            for(OpportunityJson.Value wrongRevision:List.of(new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("1.0"))) {
                Obj changed=row.with("result",result.with(payload,originalScope.with("snapshot_revision",wrongRevision)));
                assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(changed)));
            }
            var missing=new java.util.LinkedHashMap<>(originalScope.members());missing.remove("snapshot_revision");
            assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(row.with("result",result.with(payload,new Obj(missing))))));
            var renewed=new PlanningReadRequest(selection.context().before(),selection.context().source(),selection.context().sessionId(),held.last.operation(),known.receipt().request().arguments(),DEADLINE.plusSeconds(30));
            held.last.requireCanonicalReuse(known.receipt(),known.value(),renewed,selection.snapshot());
            Obj drifted=selection.snapshot().with("command_history",new OpportunityJson.Arr(List.of(new OpportunityJson.Text("new-row"))));
            held.last.requireCanonicalReuse(known.receipt(),known.value(),renewed,drifted);
            Obj nativeDrift=selection.snapshot().with("player_armies",new OpportunityJson.Arr(List.of()));
            assertThrows(IllegalArgumentException.class,()->held.last.requireCanonicalReuse(known.receipt(),known.value(),renewed,nativeDrift));
            assertEquals(1,held.nativeCalls);
        }
    }
    @Test void public64RetainsValuesAboveJsSafeAndFullUint64WithoutChangingIds()throws Exception {
        Fixture f=fixture(true);Obj semantic=f.snapshot().with("native_revision",new OpportunityJson.IntegerValue(new BigInteger("18446744073709551615")))
                .with("revision",new OpportunityJson.IntegerValue(new BigInteger("9007199254740993")));
        Held held=new Held(semantic);var selected=ContactScopeReads.Selection.current(f.query(),held.complete,DEADLINE);
        ObjectNode body=f.scope().deepCopy();body.put("snapshot_revision",selected.context().nativeRevision());
        ObjectNode result=nativeResult(selected,body).put("query_sequence",new BigInteger("18446744073709551615"));
        var observation=ContactScopeReads.normalize(selected,result);
        var available=new ContactScopePublicCodec.Available(observation,SOURCE);RawJson encoded=ContactScopePublicCodec.encode(available);
        ObjectNode n=parse(encoded.bytes());assertEquals("9007199254740993",n.get("queried_revision").textValue());
        assertEquals("18446744073709551615",n.get("query_sequence").textValue());assertEquals(available,ContactScopePublicCodec.decode(encoded));
        ObjectNode original=parse(ContactScopePublicCodec.encodeOriginal(observation).bytes());
        assertEquals("9007199254740993",original.get("queried_revision").textValue());
        assertEquals("18446744073709551615",original.get("snapshot_revision").textValue());
        assertEquals(observation,ContactScopePublicCodec.decodeOriginal(new RawJson(bytes(original))));
        n.put("query_sequence",true);assertThrows(IllegalArgumentException.class,()->ContactScopePublicCodec.decode(new RawJson(bytes(n))));
    }
    @Test void wrongSubjectFrameRawTokenAndScopeAreRejectedBeforeTheyBecomePublicResults()throws Exception {
        Fixture f=fixture(true);Held held=new Held(f.snapshot());var selected=ContactScopeReads.Selection.current(f.query(),held.complete,DEADLINE);
        var producer=new ContactScopeReads(SOURCE,SOURCE,held,held.archive,held::load,()->held.session);var catalog=new RootReadContractCatalog(List.of(),producer.families());
        for(String field:List.of("query_sequence","snapshot_revision")) {
            ObjectNode malformed=nativeResult(selected,f.scope());malformed.put(field,true);held.result=malformed;
            assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,catalog,selected));
        }
        held.result=nativeResult(selected,f.scope());held.corruptToken=true;
        assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,catalog,selected));held.corruptToken=false;
        held.result=nativeResult(selected,f.scope());held.frameDrift=true;
        assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,catalog,selected));held.frameDrift=false;
        ObjectNode incomplete=f.scope().deepCopy();incomplete.remove("transition_kind");held.result=nativeResult(selected,incomplete);
        assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,catalog,selected));
        ObjectNode wrong=f.scope().deepCopy();wrong.put("subject_owner_character_id",1);held.result=nativeResult(selected,wrong);
        assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,catalog,selected));
        var army=object(OpportunityJson.toNode(f.snapshot())).deepCopy();object(army.withArray("player_armies").get(0)).put("controllable",false);
        assertThrows(IllegalArgumentException.class,()->new ContactScopeReads.Selection(f.query(),selected.context(),DriverJson.object(bytes(army),DriverJson.MAX_NATIVE_BYTES),held.complete.connectionGeneration()));
        var other=new RootReadContractCatalog(List.of(),List.of());
        assertThrows(IllegalArgumentException.class,()->producer.collect(held.session,other,selected));
    }
    @Test void actualRequiresCurrentProvinceAndNativeUnavailabilityRemainsADataResult()throws Exception {
        Fixture f=fixture(false);Held held=new Held(f.snapshot());
        var wrong=new ContactScopeObservation.Actual(new ActualContactModel.Query(f.query().subject(),f.query().target()+1));
        assertThrows(IllegalArgumentException.class,()->ContactScopeReads.Selection.current(wrong,held.complete,DEADLINE));
        var producer=new ContactScopeReads(SOURCE,SOURCE,held,held.archive,held::load,()->held.session);
        var catalog=new RootReadContractCatalog(List.of(),producer.families());held.unavailable=true;
        var actual=producer.collect(held.session,catalog,ContactScopeReads.Selection.current(f.query(),held.complete,DEADLINE));
        var response=ContactScopePublicCodec.capture(f.query(),actual);assertTrue(response instanceof ContactScopePublicCodec.Unavailable);
        assertEquals(response,ContactScopePublicCodec.decode(ContactScopePublicCodec.encode(response)));assertEquals(0,held.nativeCalls);
    }
    private record Fixture(ContactScopeObservation.Query query,Obj snapshot,ObjectNode scope) { }
    /** Existing captured-original software producer, reused by independent serializer consumers; not a live source grant. */
    static PlanningReadResult.Known<ContactScopeObservation> producedOriginalRead(boolean projected)throws Exception {
        Fixture fixture=fixture(projected);Held held=new Held(fixture.snapshot());
        var producer=new ContactScopeReads(SOURCE,SOURCE,held,held.archive,held::load,()->held.session);
        var catalog=new RootReadContractCatalog(List.of(),producer.families());
        var selection=ContactScopeReads.Selection.current(fixture.query(),held.complete,DEADLINE);
        held.last=producer.contract(catalog,selection);held.result=nativeResult(selection,fixture.scope());
        var actual=producer.collect(held.session,catalog,selection);assertEquals(1,held.nativeCalls);
        if(actual instanceof PlanningReadResult.Known<ContactScopeObservation> known)return known;
        throw new AssertionError(actual);
    }
    private static Fixture fixture(boolean projected)throws Exception {
        String root=System.getProperty("xar.repository.root");assertNotNull(root,"the existing complete CI step must supply its actual original repository");
        Path java=Path.of(root,"java","ck3-control");
        if(projected) {
            var golden=parse(Files.readAllBytes(java.resolve("military-policy/src/test/resources/projectedcontact/producer-golden-v1.json")));
            var row=object(golden.withArray("cases").get(0));var input=object(row.get("input"));
            var scope=object(object(row.get("expected")).get("projection"));
            var query=new ContactScopeObservation.Projected(new ProjectedContactPolicy.QueryKey(i32(scope.get("subject_army_id")),i32(scope.get("target_province_id")),i32(scope.get("incoming_entry_province_id"))));
            return new Fixture(query,DriverJson.object(bytes(object(input.get("snapshot"))),DriverJson.MAX_NATIVE_BYTES),scope);
        }
        var golden=parse(Files.readAllBytes(java.resolve("wave2-military/src/test/resources/actualcontact/producer-golden-v1.json")));
        ObjectNode scope=object(object(object(golden.get("bases")).get("new_attacker")).get("scope"));
        var q=new ActualContactModel.Query(i32(scope.get("subject_army_id")),i32(scope.get("target_province_id")));
        ObjectNode snapshot=empty().put("snapshot_id","software-actual-contact-frame").put("episode_run_id","software-contact-episode")
                .put("revision",7).put("native_revision",integer(scope.get("snapshot_revision"))).put("date_raw",i32(scope.get("date_raw"))).put("paused",true);
        snapshot.putObject("diagnostics").put("connection_generation",3);
        snapshot.putArray("player_armies").add(empty().put("army_id",q.subjectArmyId()).put("current_province_id",q.targetProvinceId())
                .put("controllable",true).put("owner_character_id",i32(scope.get("subject_owner_character_id"))));
        return new Fixture(new ContactScopeObservation.Actual(q),DriverJson.object(bytes(snapshot),DriverJson.MAX_NATIVE_BYTES),scope);
    }
    private static ObjectNode nativeResult(ContactScopeReads.Selection selection,ObjectNode body) {
        ObjectNode result=empty().put("step",selection.query().step()).put("accepted",true).put("status","available").put("query_sequence",1)
                .put("snapshot_revision",selection.context().nativeRevision());
        if(selection.query() instanceof ContactScopeObservation.Projected) result.put("backend_id","native-headless");
        result.set(selection.query() instanceof ContactScopeObservation.Projected?"projected_contact_scope":"actual_contact_scope",body);return result;
    }
    private static final class Held implements PlanningReadPort {
        final Map<ExactRef,RawJson> materials=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> receipts=new HashMap<>();
        final ContinuityStorePort.Session session;final ActionPorts.OutcomeArchive archive;
        final ExactRef nativeFrame,driverFacts,hello;final Complete complete;ReadContract<ContactScopeObservation> last;
        ObjectNode result;int nativeCalls,frameLoads;boolean corruptToken,frameDrift,unavailable;
        Held(Obj semantic) {
            semantic=semantic.with("map_ready",new OpportunityJson.Bool(true)).with("played_character",new Obj(Map.of("character_id",new OpportunityJson.IntegerValue(BigInteger.valueOf(73)),"alive",new OpportunityJson.Bool(true))));
            if(!semantic.members().containsKey("active_wars"))semantic=semantic.with("active_wars",new OpportunityJson.Arr(List.of()));
            session=(ContinuityStorePort.Session)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ContinuityStorePort.Session.class},(proxy,method,args)->{throw new AssertionError("software decoder cannot mutate writer: "+method.getName());});
            archive=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->switch(method.getName()) {
                case "withSession" -> {assertSame(session,args[0]);yield proxy;}
                case "loadMaterial" -> materials.get((ExactRef)args[0]);
                case "loadFullMaterial" -> RawJson.fullMaterial(materials.get((ExactRef)args[0]).bytes());
                case "preserveMaterial" -> material((RawJson)args[0]);
                case "materialReferenceOf" -> reference((RawJson)args[0]);
                case "loadRead" -> receipts.get((ExactRef)args[0]);
                case "readReferenceOf" -> receipts.entrySet().stream().filter(e->e.getValue().equals(args[0])).map(Map.Entry::getKey).findFirst().orElseThrow();
                default -> throw new AssertionError("unexpected decoder archive operation: "+method.getName());
            });
            nativeFrame=material(new RawJson(DriverJson.encode(semantic)));driverFacts=material(new RawJson("{\"software_original\":true}".getBytes(StandardCharsets.UTF_8)));
            hello=material(new RawJson("{\"software_capabilities\":true}".getBytes(StandardCharsets.UTF_8)));
            int owner=OpportunityJson.integer(OpportunityJson.object(OpportunityJson.array(semantic.get("player_armies"),"armies").getFirst(),"subject").get("owner_character_id"),"owner").intValueExact();
            var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(owner),OpportunityJson.integer(semantic.get("native_revision"),"native"),OpportunityJson.integer(semantic.get("date_raw"),"date")),
                    OpportunityJson.text(semantic.get("snapshot_id"),"snapshot"),OpportunityJson.integer(semantic.get("revision"),"revision"),OpportunityJson.text(semantic.get("episode_run_id"),"episode"));
            var identity=new ObservationIdentity("software-contact-machine",new GameGeneration(123,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
            complete=new Complete(identity,new G2Source(identity.machineId(),OBSERVED.toString(),"software-fixture-only",SOURCE),"software-contact-session",BigInteger.valueOf(3),semantic,nativeFrame,OBSERVED,"a".repeat(64));
        }
        ExactRef reference(RawJson raw){return new ExactRef("software-material-"+DriverJson.sha256(raw.bytes()),raw.bytes().length,DriverJson.sha256(raw.bytes()));}
        ExactRef material(RawJson raw){ExactRef ref=reference(raw);materials.put(ref,raw);return ref;}
        Complete load(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive same) {
            assertEquals(nativeFrame,basis.nativeFrame());assertEquals(driverFacts,basis.driverFacts());assertSame(archive,same);frameLoads++;
            if(frameDrift&&frameLoads%2==0)return new Complete(complete.identity(),complete.source(),complete.sessionId(),complete.connectionGeneration(),complete.semantic(),complete.originalEvidence(),complete.observedAt(),"b".repeat(64));
            return complete;
        }
        GuardEvidence guard(OperationKey operation) {
            ObjectNode basis=empty().put("schema",RootGuardEvidence.SCHEMA).put("operation",operation.value()).put("authority_id","software-contact-authority");
            basis.set("native_frame",nativeFrame.toJson());basis.set("driver_facts",driverFacts.toJson());basis.set("semantic",nativeFrame.toJson());
            for(String field:List.of("driver_stamp","original_driver","capabilities","hello","heartbeat","source_qualification"))basis.set(field,hello.toJson());
            basis.putObject("writer_point").put("sequence",0).put("digest","a".repeat(64));
            return new GuardEvidence(complete.identity(),complete.source(),complete.sessionId(),complete.connectionGeneration(),operation,nativeFrame,hello,"software-contact-authority",OBSERVED,DEADLINE,List.of(material(new RawJson(bytes(basis)))));
        }
        @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){return read(session,contract,request);}
        @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request) {
            assertSame(session,same);
            if(unavailable)return new PlanningReadResult.Unavailable<>("actual advertised/source/native read unavailable",Optional.empty());
            // The generic service transports T; the test retains the typed Contact contract without an unchecked cast.
            String id="software-contact-query-"+(++nativeCalls);contract.prepare(request,id);
            ObjectNode packet=empty().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);packet.set("result",result);
            byte[] frame=bytes(packet);byte[] wire=ByteBuffer.allocate(frame.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(frame.length).put(frame).array();
            ObjectNode token=result.deepCopy();if(corruptToken)token.put("query_sequence",9);
            var ack=new NativeActionPort.AckReceived(id,true,Optional.of(new RawJson(bytes(token))),new RawJson(frame),wire);
            var guard=new PlanningReadGuard(guard(request.operation()),true,true,true,"a".repeat(64));
            var receipt=new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
            ExactRef ref=material(new RawJson(emptyReceipt(id)));receipts.put(ref,receipt);
            return new PlanningReadResult.Known<>(contract.decode(receipt),receipt,ref);
        }
        private static byte[] emptyReceipt(String id){return bytes(empty().put("software_original_read_id",id));}
    }
}

package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.HashSet;
import java.util.EnumMap;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Identity;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.m6.M6SourceProducer;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

import java.util.ArrayList;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.m6.G2M6Contracts.Episode;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.m6.SwayLifecycle;

/** Mandatory new NS80 actual current4 public packets; notification does not establish an end cause. */
final class SwayCurrent4SignedInvalidationReadTest {
    private static final ExactRef SOURCE=new ExactRef("software:actual-current4-invalidation-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-30T00:00:00Z");
    private static final List<String> OUTCOMES=List.of("message_enqueue_observed","render_observed","material_effect_observed","native_end_cause_observed","native_terminal_state_observed");

    @Test void actualNineSignedCurrent4PacketsPassPublicEncodePrepareTypedDecodeReplayAndReadback() throws Exception {
        var reads=new SwayRootReads(new SwayRootReads.Sources(SOURCE,SOURCE,SOURCE),true);var catalog=new RootReadContractCatalog(List.of(),reads.families());reads.attach(catalog);
        List<String> failures=new ArrayList<>();Set<String> branches=new HashSet<>();Set<String> roles=new HashSet<>();int count=0;
        for(JsonNode packet:originals()) {
            JsonNode raw=body(packet,null);var subject=subject(raw);
            try {
                var publicInput=new SwayPublicCodec.InvalidationRequest(binding(packet,raw).before().frame().revision(),subject.targetCharacterId(),subject.schemeInstanceId(),raw.get("after_sequence").bigIntegerValue());
                assertEquals(publicInput,SwayPublicCodec.decodeInvalidation(SwayPublicCodec.encodeInvalidationRequest(publicInput)));
                var query=new SwayObservationReads.InvalidationQuery(subject,publicInput.afterSequence());
                var contract=reads.invalidation(query);assertSame(contract,reads.invalidation(query));assertTrue(catalog.containsIdentity(contract));
                var request=request(contract,SwayObservationReads.arguments(query),packet,raw);
                JsonNode prepared=StrictJson.parse(contract.prepare(request,requestId(packet)).additionalFields().bytes());
                assertEquals(subject.actorCharacterId(),prepared.get("actor_character_id").longValue());assertEquals(subject.targetCharacterId(),prepared.get("target_character_id").longValue());assertEquals(subject.schemeInstanceId(),prepared.get("scheme_instance_id").longValue());
                assertEquals(query.afterSequence(),prepared.get("after_sequence").bigIntegerValue());assertFalse(prepared.has("action_id"));
                var receipt=receipt(contract,request,packet);var plane=contract.decode(receipt);assertArrayEquals(plane.normalized().bytes(),contract.replay(receipt).normalized().bytes());
                JsonNode normalized=StrictJson.parse(plane.normalized().bytes());for(var field:raw.properties())assertEquals(field.getValue(),normalized.get(field.getKey()),field.getKey());
                assertEquals("1.20.0.4",normalized.get("exact_ck3_build").textValue());
                JsonNode result=StrictJson.parse(SwayPublicCodec.publicNormalized(plane).bytes());assertEquals(packet.path("result").get("snapshot_revision").bigIntegerValue().toString(),result.get("snapshot_revision").textValue());
                assertEquals(raw.at("/records/0/sequence").bigIntegerValue().toString(),result.at("/records/0/sequence").textValue());
                assertEquals(raw.at("/records/0/source_branch"),result.at("/records/0/source_branch"));assertEquals(raw.at("/records/0/authored_reason_key"),result.at("/records/0/authored_reason_key"));
                for(String field:OUTCOMES){assertFalse(result.get(field).booleanValue(),field);assertFalse(result.at("/records/0/"+field).booleanValue(),field);}
                assertFalse(result.has("action_id"));assertFalse(result.has("cause_relation"));assertFalse(result.has("sway_terminal_sources_12004"));
                branches.add(raw.at("/records/0/source_branch").textValue());roles.add(subject.actorCharacterId()+"/"+subject.targetCharacterId());
            }catch(IllegalArgumentException failure){failures.add(requestId(packet)+": "+failure.getMessage());}
            count++;
        }
        assertEquals(9,count);assertEquals(List.of(),failures,"actual current4 notification public consumer rejected Native original");
        assertEquals(Set.of("target_dead_notification_source","opaque_existing_stock_notification_source","out_of_range_notification_source"),branches);
        assertEquals(Set.of("-2/0","0/2147483647","-2147483648/2147483647"),roles);
    }
    @Test void current4NotificationSourcePairCursorAndFiveOutcomesRemainStrict() throws Exception {
        JsonNode original=originals().get(0);
        for(String defect:List.of("exe","version","actor","fullID","generation","bool-sequence","float-sequence","cursor","missing","null","unknown-branch","scope","join","command","frame")) {
            ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode result=(ObjectNode)changed.get("result"),body=(ObjectNode)body(changed,null),row=(ObjectNode)body.at("/records/0");
            switch(defect){
                case "exe"->result.put("executable_sha256","0".repeat(64));case "version"->result.put("build_version","1.20.0.3");case "actor"->row.put("actor_character_id",29830);
                case "fullID"->row.put("scheme_instance_id",134217987);case "generation"->row.put("scheme_instance_generation",9);case "bool-sequence"->row.put("sequence",true);case "float-sequence"->row.put("sequence",1.0);case "cursor"->row.put("sequence",0);
                case "missing"->body.remove("session_records_only");case "null"->body.putNull("observer_attached");case "unknown-branch"->row.put("source_branch","cause_from_notification");case "scope"->row.put("root_scope_kind",9);case "join"->row.put("exact_scope_join_ready",false);case "command"->row.put("authored_command","send_notification");case "frame"->result.put("snapshot_revision",7102);default->throw new AssertionError(defect);
            }
            assertThrows(IllegalArgumentException.class,()->decode(original,changed,true),defect);
        }
        for(String field:OUTCOMES)for(boolean root:List.of(true,false)) {
            ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode selected=root?(ObjectNode)body(changed,null):(ObjectNode)body(changed,null).at("/records/0");selected.put(field,true);
            assertThrows(IllegalArgumentException.class,()->decode(original,changed,true),field);
        }
    }
    @Test void canonicalInvalidationRolesAreOnlyAdmittedByActual4Source() throws Exception {
        JsonNode original=originals().get(0);JsonNode raw=body(original,null);var subject=subject(raw);var query=new SwayObservationReads.InvalidationQuery(subject,BigInteger.ZERO);
        var enabled=SwayObservationReads.invalidationContract(SOURCE,query,true);var request=request(enabled,SwayObservationReads.arguments(query),original,raw);
        var disabled=SwayObservationReads.invalidationContract(SOURCE,query,false);
        assertThrows(IllegalArgumentException.class,()->disabled.prepare(request(disabled,SwayObservationReads.arguments(query),original,raw),requestId(original)));
        for(JsonNode packet:originals()) {
            JsonNode body=body(packet,null);var actual=new SwayObservationReads.InvalidationQuery(subject(body),body.get("after_sequence").bigIntegerValue());var contract=SwayObservationReads.invalidationContract(SOURCE,actual,true);
            for(String legacy:List.of("1.20.0.2","1.20.0.3")) {
                var current=request(contract,SwayObservationReads.arguments(actual),packet,body);
                var old=new PlanningReadRequest(current.before(),new G2Source(current.before().machineId(),NOW.toString(),legacy,SOURCE),current.sessionId(),current.operation(),current.arguments(),current.deadline());
                var prepared=assertThrows(IllegalArgumentException.class,()->contract.prepare(old,requestId(packet)));
                assertEquals("current native Sway entry requires positive int32 character",prepared.getMessage());
                var decoded=assertThrows(IllegalArgumentException.class,()->contract.decode(receipt(contract,old,packet)));
                assertEquals(prepared.getMessage(),decoded.getMessage());
            }
        }
        for(String bad:List.of("-1","-2147483649","2147483648","4294967294","true","0.0","\"0\"","null")) {
            ObjectNode args=StrictJson.object();args.put("expected_revision","1");args.set("target_character_id",StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8)));args.put("scheme_instance_id",subject.schemeInstanceId());args.put("after_sequence","0");
            assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeInvalidation(new RawJson(StrictJson.canonical(args))),bad);
            for(String field:List.of("actor_character_id","target_character_id"))for(boolean root:List.of(true,false)) {
                ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode selected=root?(ObjectNode)body(changed,null):(ObjectNode)body(changed,null).at("/records/0");selected.set(field,StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->decode(original,changed,true),field+":"+bad);
            }
        }
        for(String field:List.of("actor_character_id","target_character_id")) {
            ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode row=(ObjectNode)body(changed,null).at("/records/0");row.put(field,row.get(field).intValue()^0x0100_0000);
            assertThrows(IllegalArgumentException.class,()->decode(original,changed,true),"same low24slot different full role generation "+field);
        }
        var unknown=new PlanningReadRequest(request.before(),new G2Source(request.before().machineId(),NOW.toString(),"1.20.0.5",SOURCE),request.sessionId(),request.operation(),request.arguments(),request.deadline());
        assertThrows(IllegalArgumentException.class,()->enabled.prepare(unknown,"unknown-version"));
        for(long value:new long[]{Integer.MIN_VALUE,-2,0}) {
            assertThrows(IllegalArgumentException.class,()->new SwayObservationReads.JournalQuery(SwayObservationReads.Kind.EXECUTION,new NativeSubject(value,7,1,0),BigInteger.ZERO));
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.currentCharacter(value));
        }
    }
    private static SwayObservationReads.InvalidationPlane decode(JsonNode expected,JsonNode actual,boolean enabled) {
        JsonNode raw=body(expected,null);var query=new SwayObservationReads.InvalidationQuery(subject(raw),raw.get("after_sequence").bigIntegerValue());var contract=SwayObservationReads.invalidationContract(SOURCE,query,enabled);
        return contract.decode(receipt(contract,request(contract,SwayObservationReads.arguments(query),expected,raw),actual));
    }
    private static JsonNode originals() throws Exception {
        try (var stream = SwayCurrent4SignedInvalidationReadTest.class.getResourceAsStream("/sway/m6-native-current4-signed-invalidation.json")) {
            assertNotNull(stream, "mandatory actual Native serializer packets, never cloud-authored positives");
            JsonNode rows = StrictJson.parse(stream.readAllBytes(), SwayNativeWire.MAX); assertTrue(rows.isArray()); assertEquals(9,rows.size()); return rows;
        }
    }
    private static SwayObservationReads.Kind kind(JsonNode packet) { return SwayObservationReads.Kind.TERMINATION; }
    private static JsonNode body(JsonNode packet, SwayObservationReads.Kind kind) { return packet.path("result").get("sway_completion_invalidation_reason"); }
    private static String requestId(JsonNode packet) { return packet.get("request_id").textValue(); }
    private static NativeSubject subject(JsonNode body) { long instance = body.get("scheme_instance_id").longValue(); return new NativeSubject(NativeCharacterId.fromJson(body.get("actor_character_id")).value(), NativeCharacterId.fromJson(body.get("target_character_id")).value(), instance, (int)(instance >>> 24)); }
    private static Identity identity(NativeSubject subject) { return new Identity("software-native-terminal-original", subject.actorCharacterId(), subject.targetCharacterId(), subject.schemeInstanceId(), subject.schemeInstanceGeneration()); }
    private static SwayNativeWire.Binding binding(JsonNode packet, JsonNode body) {
        JsonNode envelope = packet.get("result"); JsonNode revision = body.has("snapshot_revision") ? body.get("snapshot_revision") : envelope.get("snapshot_revision"); JsonNode date = body.has("date_raw") ? body.get("date_raw") : envelope.get("date_raw");
        var id = new JointBudgetSelector.Frame(BigInteger.valueOf(subject(body).actorCharacterId()), revision.bigIntegerValue(), date.bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(id, "software-native-terminal-snapshot", revision.bigIntegerValue().add(BigInteger.ONE), "software-native-current4-invalidation-episode");
        var observed = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000074"))), frame, 1);
        return new SwayNativeWire.Binding(observed, "software-native-terminal-session", BigInteger.ONE, "software-native-terminal-authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    private static PlanningReadRequest request(ReadContract<?> contract, org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj args, JsonNode packet, JsonNode body) {
        var binding = binding(packet, body); return new PlanningReadRequest(binding.before(), new G2Source(binding.before().machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE), binding.sessionId(), contract.operation(), args, NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt receipt(ReadContract<?> contract, PlanningReadRequest request, JsonNode packet) {
        var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, contract.operation(), SOURCE, SOURCE, "software-native-terminal-authority", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64)); byte[] bytes = StrictJson.canonical(packet, SwayNativeWire.MAX);
        byte[] framed = ByteBuffer.allocate(bytes.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack = new NativeActionPort.AckReceived(requestId(packet), true, Optional.of(new RawJson(StrictJson.canonical(packet.get("result"), SwayNativeWire.MAX))), new RawJson(bytes), framed);
        return new PlanningReadReceipt(request, contract.contractId(), requestId(packet), guard, guard, ack);
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(StrictJson.canonical(value, SwayNativeWire.MAX)); }
}

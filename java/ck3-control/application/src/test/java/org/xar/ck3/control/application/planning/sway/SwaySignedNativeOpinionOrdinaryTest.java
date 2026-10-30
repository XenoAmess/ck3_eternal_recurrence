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

/** Actual independent Native fixtures are compared by values, never promoted to same-Game gain. */
final class SwaySignedNativeOpinionOrdinaryTest {
    private static final ExactRef SOURCE = new ExactRef("software:actual-native-terminal-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-30T00:00:00Z");
    private static final SwayObservationReads.Kind OPINION = SwayObservationReads.Kind.OPINION;
    private static final SwayObservationReads.Kind COMPLETION = SwayObservationReads.Kind.COMPLETION;

    @Test void actualMatchingPublicDecodedOpinionAndCompletionReachOrdinaryValidation() throws Exception {
        List<String> failures=new ArrayList<>(); int count=0;
        for (JsonNode packet:originals()) {
            JsonNode raw=body(packet,OPINION);JsonNode completion=matchingCompletion(raw);
            var id=identity(subject(completion.get("result").get("sway_completion")));
            var queried=binding(packet,raw).before();var inputs=inputs(opinion(packet),completion(completion,id));
            try {
                M6TerminalSourceComposition.validateInputs(inputs,id,queried);
                var episode=new Episode(id,Optional.empty(),Optional.empty(),Optional.empty(),ProjectionJson.object("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8),SwayNativeWire.MAX));
                var state=SwayLifecycle.empty(id,queried);
                var absent=assertThrows(IllegalArgumentException.class,()->SwayLifecycle.observe(state,episode,inputs,queried));
                assertEquals("JSON string required",absent.getMessage());
                assertTrue(java.util.Arrays.stream(absent.getStackTrace()).anyMatch(frame->frame.getClassName().equals(M6TerminalSourceComposition.class.getName())&&frame.getMethodName().equals("original")));
                assertTrue(state.material().isEmpty()&&state.firstGain().isEmpty()&&state.latest().isEmpty());
            } catch (IllegalArgumentException failure) { failures.add(raw.get("actor_character_id")+"/"+raw.get("target_character_id")+": "+failure.getMessage()); }
            count++;
        }
        assertEquals(3,count);assertEquals(List.of(),failures,"actual Native opinion normalized plane rejected in ordinary ingress");
    }
    @Test void ordinaryOpinionRetainsCanonicalTypesPairAndQueryFrame() throws Exception {
        JsonNode packet=originals().get(0);JsonNode raw=body(packet,OPINION);JsonNode nativeCompletion=matchingCompletion(raw);
        var id=identity(subject(nativeCompletion.get("result").get("sway_completion")));var queried=binding(packet,raw).before();
        ObjectNode normalized=(ObjectNode)StrictJson.parse(opinion(packet).bytes());
        for(String bad:List.of("-1","-2147483649","2147483648","4294967294","true","0.0","\"0\"","null")) {
            for(String field:List.of("actor_character_id","target_character_id")) {
                ObjectNode changed=normalized.deepCopy();changed.set(field,StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->M6TerminalSourceComposition.validateInputs(inputs(projection(changed),null),id,queried),field+":"+bad);
            }
        }
        ObjectNode crossed=normalized.deepCopy();crossed.put("target_character_id",1);
        assertThrows(IllegalArgumentException.class,()->M6TerminalSourceComposition.validateInputs(inputs(projection(crossed),null),id,queried));
        ObjectNode wrongStamp=normalized.deepCopy();wrongStamp.put("date_raw",raw.get("date_raw").intValue()+1);
        assertThrows(IllegalArgumentException.class,()->M6TerminalSourceComposition.validateInputs(inputs(projection(wrongStamp),null),id,queried));
    }
    private static JsonNode matchingCompletion(JsonNode opinion) throws Exception {
        try(var stream=SwaySignedNativeOpinionOrdinaryTest.class.getResourceAsStream("/sway/m6-native-signed-terminal.json")) {
            assertNotNull(stream);for(JsonNode packet:StrictJson.parse(stream.readAllBytes(),SwayNativeWire.MAX)) {
                JsonNode body=packet.path("result").get("sway_completion");if(body==null||body.get("native_status_raw").intValue()!=0)continue;
                boolean same=true;for(String key:List.of("actor_character_id","target_character_id","snapshot_revision","date_raw"))same&=body.get(key).equals(opinion.get(key));
                if(same)return packet;
            }
        } throw new AssertionError("no actual Native completion with exact same pair/revision/date values");
    }
    private static ProjectionJson opinion(JsonNode packet) {
        JsonNode raw=body(packet,OPINION);var actors=new SwayObservationReads.Actors(NativeCharacterId.fromJson(raw.get("actor_character_id")).value(),NativeCharacterId.fromJson(raw.get("target_character_id")).value());
        var query=new SwayObservationReads.DirectQuery(OPINION,new SwayObservationReads.OpinionSubject(actors));var contract=SwayObservationReads.directContract(SOURCE,query);
        return contract.decode(receipt(contract,request(contract,SwayObservationReads.arguments(query),packet,raw),packet)).normalized();
    }
    private static ProjectionJson completion(JsonNode packet,Identity id) {
        JsonNode raw=packet.path("result").get("sway_completion");var query=SwayObservationReads.Query.current(COMPLETION,id);var contract=SwayObservationReads.contract(SOURCE,query);
        return contract.decode(receipt(contract,request(contract,SwayObservationReads.arguments(query),packet,raw),packet)).normalized();
    }
    private static M6TerminalSourceComposition.Inputs inputs(ProjectionJson opinion,ProjectionJson completion) { return new M6TerminalSourceComposition.Inputs(Optional.ofNullable(completion),Optional.empty(),Optional.empty(),Optional.of(opinion)); }
    private static ProjectionJson projection(JsonNode value) {return ProjectionJson.object(StrictJson.canonical(value,SwayNativeWire.MAX),SwayNativeWire.MAX);}
    private static JsonNode originals() throws Exception {
        try (var stream = SwaySignedNativeOpinionOrdinaryTest.class.getResourceAsStream("/sway/m6-native-mailbox-opinion.json")) {
            assertNotNull(stream, "mandatory actual Native serializer packets, never cloud-authored positives");
            JsonNode rows = StrictJson.parse(stream.readAllBytes(), SwayNativeWire.MAX); assertTrue(rows.isArray()); assertEquals(3, rows.size()); return rows;
        }
    }
    private static SwayObservationReads.Kind kind(JsonNode packet) { return OPINION; }
    private static JsonNode body(JsonNode packet, SwayObservationReads.Kind kind) { return packet.path("result").get("sway_outcome_opinion"); }
    private static String requestId(JsonNode packet) { return packet.get("request_id").textValue(); }
    private static NativeSubject subject(JsonNode body) { long instance = body.get("scheme_instance_id").longValue(); return new NativeSubject(NativeCharacterId.fromJson(body.get("actor_character_id")).value(), NativeCharacterId.fromJson(body.get("target_character_id")).value(), instance, (int)(instance >>> 24)); }
    private static Identity identity(NativeSubject subject) { return new Identity("software-native-terminal-original", subject.actorCharacterId(), subject.targetCharacterId(), subject.schemeInstanceId(), subject.schemeInstanceGeneration()); }
    private static SwayNativeWire.Binding binding(JsonNode packet, JsonNode body) {
        JsonNode envelope = packet.get("result"); JsonNode revision = body.has("snapshot_revision") ? body.get("snapshot_revision") : envelope.get("snapshot_revision"); JsonNode date = body.has("date_raw") ? body.get("date_raw") : envelope.get("date_raw");
        var id = new JointBudgetSelector.Frame(BigInteger.valueOf(NativeCharacterId.fromJson(body.get("actor_character_id")).value()), revision.bigIntegerValue(), date.bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(id, "software-native-terminal-snapshot", BigInteger.valueOf(9), "software-native-terminal-episode");
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

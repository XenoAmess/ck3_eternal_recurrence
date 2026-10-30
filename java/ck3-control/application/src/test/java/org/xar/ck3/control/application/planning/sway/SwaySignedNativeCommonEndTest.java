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

/** Mandatory actual Native CommonEnd public packets. No Game or cause qualification. */
public final class SwaySignedNativeCommonEndTest {
    private static final ExactRef SOURCE=new ExactRef("software:actual-native-common-source",1,"a".repeat(64));
    private static final Instant NOW=Instant.parse("2026-10-30T00:00:00Z");
    private static final SwayObservationReads.Kind COMPLETION=SwayObservationReads.Kind.COMPLETION;
    private static final SwayObservationReads.Kind TERMINATION=SwayObservationReads.Kind.TERMINATION;

    @Test void actualCommonPacketsSurvivePublicDecodeOrdinaryValidationAndPublicOutput() throws Exception {
        List<String> failures=new ArrayList<>();Set<Integer> incomingDl=new HashSet<>();int count=0;
        for(JsonNode packet:originals()) {
            JsonNode raw=body(packet,TERMINATION);var subject=subject(raw);var id=identity(subject);
            try {
                var plane=decode(packet,packet);JsonNode normalized=StrictJson.parse(plane.normalized().bytes());
                assertEquals(raw.get("common_native_end"),normalized.get("common_native_end"));
                var inputs=new M6TerminalSourceComposition.Inputs(Optional.empty(),Optional.empty(),Optional.of(plane.normalized()),Optional.empty());
                M6TerminalSourceComposition.validateInputs(inputs,id,binding(packet,raw).before());
                JsonNode result=StrictJson.parse(SwayPublicCodec.publicNormalized(plane).bytes());
                JsonNode publicCommon=result.get("common_native_end"),nativeCommon=raw.get("common_native_end");
                assertEquals(nativeCommon.get("actor_character_id"),publicCommon.get("actor_character_id"));
                assertEquals(nativeCommon.get("target_character_id"),publicCommon.get("target_character_id"));
                assertEquals(nativeCommon.get("observer_session_identity").bigIntegerValue().toString(),publicCommon.get("observer_session_identity").textValue());
                for(String frame:List.of("entry","returned"))assertEquals(nativeCommon.at("/records/0/"+frame),publicCommon.at("/records/0/"+frame));
                assertEquals(nativeCommon.at("/records/0/incoming_dl_raw_u8"),publicCommon.at("/records/0/incoming_dl_raw_u8"));
                JsonNode record=raw.at("/common_native_end/records/0");
                assertEquals(1,raw.at("/common_native_end/records").size());assertFalse(record.has("cause_relation"));
                assertFalse(record.get("incoming_return_address_observed").booleanValue());assertTrue(record.get("caller_return_rva").isNull());
                assertFalse(record.at("/entry/core_frame_observed").booleanValue());assertTrue(record.at("/entry/core_frame").isNull());
                assertEquals(Integer.toUnsignedLong(Math.toIntExact(subject.actorCharacterId())),record.at("/entry/owner_character_full_id_raw_u32").longValue());
                assertEquals(Integer.toUnsignedLong(Math.toIntExact(subject.targetCharacterId())),record.at("/entry/target_character_full_id_raw_u32").longValue());
                assertEquals(0xffff_ffffL,record.at("/returned/owner_character_full_id_raw_u32").longValue());
                incomingDl.add(record.get("incoming_dl_raw_u8").intValue());
            } catch(IllegalArgumentException failure) {failures.add(subject.actorCharacterId()+"/"+subject.targetCharacterId()+": "+failure.getMessage());}
            count++;
        }
        assertEquals(5,count);assertEquals(List.of(),failures,"actual CommonEnd public packets rejected by existing consumer");
        assertEquals(Set.of(0,2,255,127,1),incomingDl,"raw DL byte must not become boolean");
    }
    @Test void commonCanonicalRootRawBitsAndUnobservedFieldsStayStrict() throws Exception {
        JsonNode original=originals().get(0);
        for(String bad:List.of("-1","2147483648","4294967294","true","0.0","\"0\"","null")) {
            for(String field:List.of("actor_character_id","target_character_id")) {
                ObjectNode changed=((ObjectNode)original).deepCopy();((ObjectNode)body(changed,TERMINATION).get("common_native_end")).set(field,StrictJson.parse(bad.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->decode(original,changed),field+":"+bad);
            }
        }
        for(String field:List.of("owner_character_full_id_raw_u32","target_character_full_id_raw_u32")) {
            ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode entry=(ObjectNode)body(changed,TERMINATION).at("/common_native_end/records/0/entry");entry.put(field,entry.get(field).longValue()^0x0100_0000L);
            assertThrows(IllegalArgumentException.class,()->decode(original,changed),"same slot other generation "+field);
            ObjectNode signed=((ObjectNode)original).deepCopy();((ObjectNode)body(signed,TERMINATION).at("/common_native_end/records/0/entry")).put(field,-2);
            assertThrows(IllegalArgumentException.class,()->decode(original,signed),"raw field must stay unsigned "+field);
        }
        ObjectNode absent=((ObjectNode)original).deepCopy();((ObjectNode)body(absent,TERMINATION).at("/common_native_end/records/0/entry")).remove("core_frame");
        assertThrows(IllegalArgumentException.class,()->decode(original,absent));
        ObjectNode booleanDl=((ObjectNode)original).deepCopy();((ObjectNode)body(booleanDl,TERMINATION).at("/common_native_end/records/0")).put("incoming_dl_raw_u8",true);
        assertThrows(IllegalArgumentException.class,()->decode(original,booleanDl));
    }
    public static SwayObservationReads.JournalPlane decode(JsonNode expected,JsonNode actual) {
        JsonNode raw=body(expected,TERMINATION);var query=new SwayObservationReads.JournalQuery(TERMINATION,subject(raw),raw.get("after_sequence").bigIntegerValue());var contract=SwayObservationReads.journalContract(SOURCE,query);
        return contract.decode(receipt(contract,request(contract,SwayObservationReads.arguments(query),expected,raw),actual));
    }
    private static JsonNode originals() throws Exception {
        try (var stream = SwaySignedNativeCommonEndTest.class.getResourceAsStream("/sway/m6-native-common-end.json")) {
            assertNotNull(stream, "mandatory actual Native serializer packets, never cloud-authored positives");
            JsonNode rows = StrictJson.parse(stream.readAllBytes(), SwayNativeWire.MAX); assertTrue(rows.isArray()); assertEquals(5,rows.size()); return rows;
        }
    }
    private static SwayObservationReads.Kind kind(JsonNode packet) { return packet.path("result").has("sway_completion") ? COMPLETION : TERMINATION; }
    private static JsonNode body(JsonNode packet, SwayObservationReads.Kind kind) { return packet.path("result").get(kind == COMPLETION ? "sway_completion" : "sway_completion_termination"); }
    private static String requestId(JsonNode packet) { return packet.get("request_id").textValue(); }
    private static NativeSubject subject(JsonNode body) { long instance = body.get("scheme_instance_id").longValue(); return new NativeSubject(NativeCharacterId.fromJson(body.get("actor_character_id")).value(), NativeCharacterId.fromJson(body.get("target_character_id")).value(), instance, (int)(instance >>> 24)); }
    private static Identity identity(NativeSubject subject) { return new Identity("software-native-terminal-original", subject.actorCharacterId(), subject.targetCharacterId(), subject.schemeInstanceId(), subject.schemeInstanceGeneration()); }
    private static SwayNativeWire.Binding binding(JsonNode packet, JsonNode body) {
        JsonNode envelope = packet.get("result"); JsonNode revision = body.has("snapshot_revision") ? body.get("snapshot_revision") : envelope.get("snapshot_revision"); JsonNode date = body.has("date_raw") ? body.get("date_raw") : envelope.get("date_raw");
        var id = new JointBudgetSelector.Frame(BigInteger.valueOf(subject(body).actorCharacterId()), revision.bigIntegerValue(), date.bigIntegerValue());
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

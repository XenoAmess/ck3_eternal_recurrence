package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts.NativeSubject;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual seeded-world Native Stop packets. Java guard/config DATA are software seams.
 * No original Start, genuine Finish preparation, canonical writer or Cancel execution is claimed. */
final class SwayActualNativeStopPacketTest {
    private static final Instant NOW=Instant.parse("2026-10-30T00:00:00Z");
    private static final ExactRef SOURCE=new ExactRef("software-owned-stop-source-data",1,"a".repeat(64));

    @Test void actualNativeStopAcknowledgementsRemainPendingForBothCanonicalRoleDirections() throws Exception {
        List<String> failures=new ArrayList<>();int cases=0;
        for(var row:originals()) {
            byte[] raw=wire(row,"stop.response");var outer=parse(raw);var body=outer.at("/result/sway_stop");
            try {
                var ack=SwayNativeWire.stopAck(raw,text(outer,"request_id"),binding(body),text(body,"action_id"),role(body,"target_character_id"),number(body,"scheme_instance_id"),Math.toIntExact(number(body,"scheme_instance_generation")));
                assertEquals(role(body,"actor_character_id"),ack.actor());assertEquals(role(body,"target_character_id"),ack.target());
                assertEquals(0,ack.fullId());assertEquals(0,ack.generation());assertFalse(ack.terminalObserved());
                assertEquals(body,parse(ack.body().bytes()));assertFalse(body.get("postcondition_verified").booleanValue());
                assertFalse(body.get("terminal_cause_observed").booleanValue());assertEquals("unknown",text(body,"terminal_cause"));
            } catch(IllegalArgumentException rejected) {failures.add(row.get("case").textValue()+": "+rejected.getMessage());}
            cases++;
        }
        assertEquals(2,cases);assertEquals(List.of(),failures,"actual Native signed Stop ACK consumer");
    }

    @Test void actualNativeStopRequestFieldsRoundTripThePublicFinishValueContract() throws Exception {
        List<String> failures=new ArrayList<>();int cases=0;
        for(var row:originals()) {
            var actual=parse(wire(row,"stop.request"));
            try {
                var request=new SwaySelectedFinish.Request(actual.get("expected_revision").bigIntegerValue(),role(actual,"target_character_id"),number(actual,"scheme_instance_id"),Math.toIntExact(number(actual,"scheme_instance_generation")));
                var original=SwayPublicCodec.encodeFinishRequest(request);var decoded=SwayPublicCodec.decodeFinish(original);
                assertEquals(request,decoded);assertEquals(role(actual,"target_character_id"),decoded.targetCharacterId());
                assertEquals(0,decoded.schemeInstanceId());assertEquals(0,decoded.schemeInstanceGeneration());
            } catch(IllegalArgumentException rejected) {failures.add(row.get("case").textValue()+": "+rejected.getMessage());}
            cases++;
        }
        assertEquals(2,cases);assertEquals(List.of(),failures,"Java public Finish contract for actual Native request fields, not genuine Finish admission");
    }

    @Test void independentNativeCompletionReadsPreserveActivePendingAndUnattributedControlledTerminal() throws Exception {
        int reads=0;
        for(var row:originals()) for(String stage:List.of("current.response","pending.response","terminal.response")) {
            byte[] raw=wire(row,stage);var outer=parse(raw);var body=outer.at("/result/sway_completion");var binding=binding(body);
            var subject=new NativeSubject(role(body,"actor_character_id"),role(body,"target_character_id"),number(body,"scheme_instance_id"),Math.toIntExact(number(body,"scheme_instance_generation")));
            var query=new SwayObservationReads.DirectQuery(SwayObservationReads.Kind.COMPLETION,new SwayObservationReads.CompletionSubject(subject));
            var inputs=new SwayPublicCodec.DirectRequest(SwayObservationReads.Kind.COMPLETION,BigInteger.valueOf(9),subject.targetCharacterId(),java.util.OptionalLong.of(subject.schemeInstanceId()));
            assertEquals(inputs,SwayPublicCodec.decodeDirect(inputs.kind(),SwayPublicCodec.encodeDirectRequest(inputs)));
            var definition=SwayObservationReads.directContract(SOURCE,query);var fields=StrictJson.object();fields.put("target_character_id",subject.targetCharacterId());fields.put("scheme_instance_id",subject.schemeInstanceId());
            var request=new PlanningReadRequest(binding.before(),new G2Source(binding.before().machineId(),NOW.toString(),SwayNativeWire.BUILD,SOURCE),binding.sessionId(),definition.operation(),OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)),"actual subject DATA"),NOW.plusSeconds(30));
            var prepared=definition.prepare(request,text(outer,"request_id"));assertEquals(definition.operation().value(),prepared.step());
            var evidence=new GuardEvidence(binding.before(),request.source(),request.sessionId(),binding.connectionGeneration(),definition.operation(),SOURCE,SOURCE,binding.authorityId(),NOW,NOW.plusSeconds(30));
            var guard=new PlanningReadGuard(evidence,true,true,true,"b".repeat(64));
            var nativeAck=new NativeActionPort.AckReceived(text(outer,"request_id"),true,Optional.of(new RawJson(StrictJson.canonical(outer.get("result")))),new RawJson(raw),NativeWire.packet(raw));
            var receipt=new PlanningReadReceipt(request,definition.contractId(),text(outer,"request_id"),guard,guard,nativeAck);
            var plane=definition.decode(receipt);var normalized=parse(plane.normalized().bytes());
            assertEquals(subject.actorCharacterId(),normalized.get("actor_character_id").longValue());assertEquals(subject.targetCharacterId(),normalized.get("target_character_id").longValue());
            var read=normalized;assertEquals(body.get("native_owner_raw"),read.get("native_owner_raw"));
            assertEquals(stage.equals("terminal.response"),read.get("native_terminal_state_observed").booleanValue());
            assertFalse(read.get("terminal_cause_observed").booleanValue());assertEquals("unknown",text(read,"terminal_cause"));
            var publicValue=parse(SwayPublicCodec.publicNormalized(new SwayObservationReads.DirectBatch(plane,Optional.empty())).bytes());assertEquals(normalized.get("actor_character_id"),publicValue.get("actor_character_id"));reads++;
        }
        assertEquals(6,reads);
    }

    @Test void actualNativeRedStopsAndMutatedInvalidRolesCannotBroadenOtherDomains() throws Exception {
        for(var row:originals()) {
            var outer=parse(wire(row,"stop.response"));var body=outer.at("/result/sway_stop");var binding=binding(body);
            long target=role(body,"target_character_id");String action=text(body,"action_id");
            for(String redRole:List.of("wrong-generation.response","ended-stop.response")) {
                byte[] red=wire(row,redRole);var packet=parse(red);assertFalse(packet.get("ok").booleanValue());
                assertThrows(IllegalArgumentException.class,()->SwayNativeWire.stopAck(red,text(packet,"request_id"),binding,action,target,0,0));
            }
            var actual=parse(wire(row,"stop.request"));
            var request=new SwaySelectedFinish.Request(actual.get("expected_revision").bigIntegerValue(),target,0,0);
            for(String invalid:List.of("-1","2147483648","4294967294","true","0.0","\"0\"","null")) {
                JsonNode token=parse(invalid.getBytes(StandardCharsets.UTF_8));
                for(String field:List.of("actor_character_id","target_character_id")) {
                    var altered=outer.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)altered.at("/result/sway_stop")).set(field,token);
                    assertThrows(IllegalArgumentException.class,()->SwayNativeWire.stopAck(StrictJson.canonical(altered),text(outer,"request_id"),binding,action,target,0,0));
                }
                var publicArgs=(com.fasterxml.jackson.databind.node.ObjectNode)parse(SwayPublicCodec.encodeFinishRequest(request).bytes());publicArgs.set("target_character_id",token);
                assertThrows(IllegalArgumentException.class,()->SwayPublicCodec.decodeFinish(new RawJson(StrictJson.canonical(publicArgs))));
            }
            assertThrows(IllegalArgumentException.class,()->new SwaySelectedFinish.Request(BigInteger.valueOf(7),target,0,1));
            assertThrows(IllegalArgumentException.class,()->new SwaySelectedFinish.Request(BigInteger.valueOf(7),target,0xffff_ffffL,255));
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.currentCharacter(binding.actor()));
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.character(binding.actor()));
            var subject=new NativeSubject(binding.actor(),target,0,0);
            assertThrows(IllegalArgumentException.class,()->new SwayObservationReads.JournalQuery(SwayObservationReads.Kind.EXECUTION,subject,BigInteger.ZERO));
        }
    }

    private static SwayNativeWire.Binding binding(JsonNode source) {
        var identity=new JointBudgetSelector.Frame(BigInteger.valueOf(role(source,"actor_character_id")),source.get("snapshot_revision").bigIntegerValue(),source.get("date_raw").bigIntegerValue());
        var frame=new JointBudgetSelector.ProposalFrame(identity,"software-owned-stop-snapshot",BigInteger.valueOf(9),"software-owned-stop-episode");
        var observed=new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",new GameGeneration(73,new PythonOnlyUInt64(BigInteger.ONE)),frame,1);
        return new SwayNativeWire.Binding(observed,"software-owned-stop-session",BigInteger.ONE,"software-owned-stop-authority",SwayNativeWire.BUILD,SwayNativeWire.EXE);
    }
    private static JsonNode originals() throws Exception {try(var in=SwayActualNativeStopPacketTest.class.getResourceAsStream("/sway/m6-native-stop-public-originals.json")){assertNotNull(in,"mandatory actual Native Stop originals, no invented positives");var rows=parse(in.readAllBytes());assertEquals(2,rows.size());return rows;}}
    private static byte[] wire(JsonNode row,String key) {var value=row.path("wires").get(key);assertNotNull(value);byte[] raw=value.get("original_utf8").textValue().getBytes(StandardCharsets.UTF_8);assertEquals(value.get("sha256").textValue(),ActionCodec.sha256(raw));return raw;}
    private static JsonNode parse(byte[] raw) {return StrictJson.parse(raw,SwayNativeWire.MAX);}
    private static String text(JsonNode row,String key) {return StrictJson.text(row.get(key));}
    private static long number(JsonNode row,String key) {return StrictJson.integer(row.get(key),0,0xffff_fffeL);}
    private static int role(JsonNode row,String key) {return NativeCharacterId.fromJson(row.get(key)).value();}

@Test void actualStopPreparationPreservesSignedRolesAndRejectsBoundaryDrift() throws Exception {
    List<String> failures = new ArrayList<>();
    int cases = 0;
    for (var row : originals()) {
        byte[] rawReq = wire(row, "stop.request");
        JsonNode req = parse(rawReq);
        byte[] rawResp = wire(row, "stop.response");
        JsonNode resp = parse(rawResp);
        JsonNode body = resp.at("/result/sway_stop");

        long actor = role(req, "actor_character_id");
        long target = role(req, "target_character_id");
        String actionId = text(body, "action_id");
        String originalActionId = "sway-software-parser-original";
        long instanceId = number(body, "scheme_instance_id");
        int generation = Math.toIntExact(number(body, "scheme_instance_generation"));

        var binding = SwayActualNativeStopPacketTest.binding(body);
        var observed = binding.before();
        var source = new G2Source(observed.machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE);
        var claims = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(BigInteger.valueOf(actor), BigInteger.valueOf(target)), Set.of());
        var expected = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1, observed, source, "software-stop-observer", List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("sway.action_id"), actionId)));

        com.fasterxml.jackson.databind.node.ObjectNode args = StrictJson.object();
        args.put("schema", SwayNativeBindings.STOP_ARGUMENTS);
        args.put("original_action_id", originalActionId);
        args.put("target_character_id", target);
        args.put("scheme_instance_id", instanceId);
        args.put("scheme_instance_generation", generation);
        args.set("original_target_read", SOURCE.toJson());
        args.set("completion_read", SOURCE.toJson());
        args.set("opinion_read", SOURCE.toJson());

        var command = new ActionCommand(actionId, observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(args)), "software-stop-args"), expected, claims, NOW);

        try {
            var prepared = SwayNativeBindings.stopPreparation().prepare(command);
            assertEquals(SwayNativeWire.STOP, prepared.step());
            var fields = StrictJson.parse(prepared.additionalFields().bytes(), SwayNativeWire.MAX);
            assertEquals(actor, NativeCharacterId.fromJson(fields.get("actor_character_id")).value());
            assertEquals(target, NativeCharacterId.fromJson(fields.get("target_character_id")).value());
            assertEquals(actionId, text(fields, "action_id"));
            assertEquals(instanceId, number(fields, "scheme_instance_id"));
            assertEquals(generation, Math.toIntExact(number(fields, "scheme_instance_generation")));
            JsonNode retained = StrictJson.parse(OpportunityJson.encode(command.arguments()));
            for (String field : List.of("original_target_read", "completion_read", "opinion_read"))
                assertEquals(SOURCE, ExactRef.fromJson(retained.get(field)), "software command retains its declared original ref");
        } catch (IllegalArgumentException e) {
            failures.add(row.get("case").textValue() + ": " + e.getMessage());
        }
        cases++;
    }
    assertEquals(2, cases);
    assertEquals(List.of(), failures, "actual Stop preparation preserves signed roles");

    var row = originals().get(0);
    var req = parse(wire(row, "stop.request"));
    var resp = parse(wire(row, "stop.response"));
    var body = resp.at("/result/sway_stop");
    var binding = SwayActualNativeStopPacketTest.binding(body);
    var observed = binding.before();
    var source = new G2Source(observed.machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE);
    var claims = new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(BigInteger.valueOf(role(req, "actor_character_id")), BigInteger.valueOf(role(req, "target_character_id"))), Set.of());
    var expected = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1, observed, source, "software-stop-observer", List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("sway.action_id"), text(body, "action_id"))));

    com.fasterxml.jackson.databind.node.ObjectNode baseArgs = StrictJson.object();
    baseArgs.put("schema", SwayNativeBindings.STOP_ARGUMENTS);
    baseArgs.put("original_action_id", "sway-software-parser-original");
    baseArgs.put("target_character_id", role(req, "target_character_id"));
    baseArgs.put("scheme_instance_id", number(body, "scheme_instance_id"));
    baseArgs.put("scheme_instance_generation", Math.toIntExact(number(body, "scheme_instance_generation")));
    baseArgs.set("original_target_read", SOURCE.toJson());
    baseArgs.set("completion_read", SOURCE.toJson());
    baseArgs.set("opinion_read", SOURCE.toJson());

    var validCommand = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(baseArgs)), "software-stop-args"), expected, claims, NOW);

    // Public roles remain exact signed int32 except the -1 absence sentinel.
    for (String invalid : List.of("-1", "2147483648", "4294967294", "true", "0.0", "\"0\"", "null")) {
        var invalidArgs = baseArgs.deepCopy();
        invalidArgs.set("target_character_id", parse(invalid.getBytes(StandardCharsets.UTF_8)));
        if (invalid.equals("0.0")) {
            assertThrows(IllegalArgumentException.class, () -> StrictJson.canonical(invalidArgs),
                    "fractional JSON is rejected during canonical command construction before preparation");
            continue;
        }
        var invalidCommand = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(invalidArgs)), "software-stop-args"), expected, claims, NOW);
        assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(invalidCommand), invalid);
    }

    // Negative: actor == target
    var mutated = baseArgs.deepCopy();
    mutated.put("target_character_id", role(req, "actor_character_id"));
    var sameActorTarget = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(sameActorTarget));

    // Negative: invalid schema
    mutated = baseArgs.deepCopy();
    mutated.put("schema", "bad-schema");
    var badSchema = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(badSchema));

    // Negative: invalid action id
    var badAction = new ActionCommand("invalid-id", observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(baseArgs)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(badAction));

    // Negative: invalid original action id
    mutated = baseArgs.deepCopy();
    mutated.put("original_action_id", "invalid-id");
    var badOriginal = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(badOriginal));

    // Negative: invalid instance/generation relation
    mutated = baseArgs.deepCopy();
    mutated.put("scheme_instance_id", 0L);
    mutated.put("scheme_instance_generation", 1);
    var badInstance = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(badInstance));

    // Negative: missing read ref
    mutated = baseArgs.deepCopy();
    mutated.remove("completion_read");
    var missingRef = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(missingRef));

    // Negative: zero-byte read ref
    mutated = baseArgs.deepCopy();
    mutated.set("completion_read", new ExactRef("path", 0, "a".repeat(64)).toJson());
    var zeroRef = new ActionCommand(text(body, "action_id"), observed, source, "software-stop-session", new OperationKey(SwayNativeWire.STOP),
            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(mutated)), "software-stop-args"), expected, claims, NOW);
    assertThrows(IllegalArgumentException.class, () -> SwayNativeBindings.stopPreparation().prepare(zeroRef));
}
}

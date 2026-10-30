package org.xar.ck3.control.application.planning.sway;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.sway.SwayFormalState.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m6.G2M6Contracts;
import org.xar.ck3.control.g2.m6.M6TerminalSourceComposition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual owned-world Native public route. Java custody metadata is a test seam, not Game evidence. */
final class SwayCurrent4PublicActionRouteTest {
    private static final ExactRef SOURCE = new ExactRef("software:actual-current4-public-sway-source", 1, "a".repeat(64));
    private static final Instant NOW = Instant.parse("2026-10-30T00:00:00Z");
    private static final String EPISODE = "software-native-current4-action-episode";

    @Test void actualQueryPassesPublicTargetPrepareDecodeQuoteAndStartArgumentRoundTrip() throws Exception {
        byte[] original = wire("query"); JsonNode packet = parse(original), body = packet.at("/result/active_scheme_sway");
        long target = NativeCharacterId.fromJson(body.get("target_character_id")).value();
        var publicTarget = new SwayDriverCodec.TargetRequest(binding().before().frame().revision(), target);
        assertEquals(publicTarget, SwayDriverCodec.decodeTarget(SwayDriverCodec.encode(publicTarget)));
        var reads = new SwayRootReads(new SwayRootReads.Sources(SOURCE, SOURCE, SOURCE));
        var catalog = new RootReadContractCatalog(List.of(), reads.families()); reads.attach(catalog);
        var contract = reads.target(target); var request = request(contract, targetArguments(target));
        assertTrue(catalog.containsIdentity(contract)); assertEquals(contract.operation().value(), contract.prepare(request, requestId(packet)).step());
        var receipt = guarded(contract, request, original); var value = contract.decode(receipt);
        var replay=assertThrows(IllegalStateException.class,()->contract.replay(receipt));
        assertEquals("this exact read contract has no explicitly installed pure replay decoder",replay.getMessage());
        assertEquals(-2, value.binding().actor()); assertEquals(0, value.target());
        var ref = new ExactRef("software:actual-native-query-original", original.length, ActionCodec.sha256(original));
        var quote = SwayDriverCodec.quote(receipt, value, ref);
        var startArgs = StrictJson.object(); startArgs.set("readback", parse(quote.bytes())); startArgs.put("action_id", actionId());
        var start = SwayDriverCodec.decodeStart(raw(startArgs));
        assertEquals(start, SwayDriverCodec.decodeStart(SwayDriverCodec.encode(start)));
        assertEquals(ref, start.readback().originalRead()); assertEquals(target, start.readback().targetCharacterId());
        var receiptInput = new SwayDriverCodec.ReceiptRequest(publicTarget.expectedRevision(), target, actionId(), value.captureEpoch());
        assertEquals(receiptInput, SwayDriverCodec.decodeReceipt(SwayDriverCodec.encode(receiptInput)));
        var commandFields=StrictJson.object();commandFields.put("schema",SwayNativeBindings.PUBLIC_START_ARGUMENTS);commandFields.put("target_character_id",target);commandFields.set("original_target_read",ref.toJson());
        var expected=new ExpectedPostcondition(1,request.before(),request.source(),SwayActionLifecycle.START_OBSERVER,List.of(new ExpectedBoolean(new FieldKey("sway.exact_active_observed"),true)));
        var command=new ActionCommand(actionId(),request.before(),request.source(),request.sessionId(),new OperationKey(SwayNativeWire.START+target),
                OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(commandFields)),"actual Native public Start source"),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),NOW.plusSeconds(30));
        var archive=new ReadOnlyArchive(ref,receipt);var prepared=SwayNativeBindings.startPreparation(archive).prepare(command);
        assertEquals(command.operation().value(),prepared.step());JsonNode fields=parse(prepared.additionalFields().bytes());
        assertEquals(value.captureEpoch(),fields.get("expected_capture_epoch").bigIntegerValue());assertEquals(value.containerGeneration(),fields.get("expected_container_generation").bigIntegerValue());
        byte[] submit=wire("submit");var dispatch=ack(submit);var attempt=new ActionState.Attempt(requestId(parse(submit)),NOW,receipt.before().binding(),prepared);
        var actual=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.AckReceived(attempt,dispatch));
        JsonNode publicAck=parse(SwayDriverCodec.startResult(actual,archive).bytes());assertEquals("submitted_verification_pending",publicAck.get("stage").textValue());
        assertFalse(publicAck.get("canonical_postcondition_verified").booleanValue());assertFalse(publicAck.get("eligible_advance").booleanValue());
        assertEquals(-2,publicAck.get("actor_character_id").longValue());assertEquals(0,publicAck.get("target_character_id").longValue());
    }

    @Test void actualAckAndZeroReceiptNeedIndependentLaterPublicQueryBeforeResolutionAndPersistence() throws Exception {
        Ledger resolved = resolved(); var episode = resolved.resolved().orElseThrow();
        assertEquals(-2, episode.identity().actorCharacterId()); assertEquals(0, episode.identity().targetCharacterId());
        assertEquals(0, episode.identity().schemeInstanceId()); assertEquals(0, episode.identity().schemeInstanceGeneration());
        assertTrue(episode.nativeReceipt().isPresent()); assertTrue(resolved.pending().isEmpty());
        byte[] encoded = SwayFormalCodec.encode(resolved);
        assertArrayEquals(encoded, SwayFormalCodec.encode(SwayFormalCodec.decode(encoded)));
        var original = SwayFormalCodec.originalResolved(episode);
        assertEquals("applied", original.get("status").textValue()); assertEquals(0, original.at("/native_receipt/scheme_instance_id").longValue());
        assertFalse(original.has("terminal_cause_observed") && original.get("terminal_cause_observed").booleanValue());
    }

    @Test void actualNativeReceiptPreservesFullSchemeZeroAndUnsafeContainerGeneration() throws Exception {
        byte[] response=wire("receipt");JsonNode packet=parse(response),body=packet.at("/result/active_scheme_sway_formal");
        var receipt=SwayNativeWire.receipt(response,requestId(packet),binding(),actionId(),0,BigInteger.valueOf(4));
        assertEquals(0,receipt.fullId());assertEquals(0,receipt.generation());
        assertEquals(new BigInteger("15189419816273770301"),receipt.postContainerGeneration());
        assertEquals(body.get("post_container_generation").bigIntegerValue(),receipt.postContainerGeneration());
        var reads=new SwayRootReads(new SwayRootReads.Sources(SOURCE,SOURCE,SOURCE));var catalog=new RootReadContractCatalog(List.of(),reads.families());reads.attach(catalog);
        var contract=reads.receipt(0,actionId(),BigInteger.valueOf(4));var arguments=StrictJson.object();arguments.put("action_id",actionId());
        var request=request(contract,OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(arguments)),"actual Native original receipt"));
        assertEquals(actionId(),parse(contract.prepare(request,requestId(packet)).additionalFields().bytes()).get("action_id").textValue());
        var guarded=guarded(contract,request,response);assertEquals(receipt,contract.decode(guarded));
        var reference=new ExactRef("software:actual-native-receipt-original",response.length,ActionCodec.sha256(response));
        JsonNode presented=parse(SwayDriverCodec.receipt(guarded,receipt,reference).bytes());
        assertEquals("15189419816273770301",presented.get("post_container_generation").textValue());assertEquals(0,presented.get("scheme_instance_id").longValue());
        assertEquals(reference,ExactRef.fromJson(presented.get("java_original_receipt_read")));
    }

    @Test void actualResolvedStartReachesOrdinaryCopiedSourceCompositionWithoutInventingTerminalPlanes() throws Exception {
        var episode = resolved().resolved().orElseThrow(); var original = SwayFormalCodec.originalResolved(episode);
        var copied = new G2M6Contracts.Episode(episode.identity(), Optional.empty(), Optional.empty(), Optional.empty(),
                ProjectionJson.object(StrictJson.canonical(original, SwayNativeWire.MAX), SwayNativeWire.MAX));
        var result = M6TerminalSourceComposition.compose(copied, M6TerminalSourceComposition.Inputs.unqueried());
        assertEquals(episode.identity(), result.identity()); assertTrue(result.current().isEmpty()); assertTrue(result.cause().isEmpty());
        assertFalse(result.actionAuthorized()); assertFalse(result.ledgerCommitted()); assertFalse(result.requestRetried());
    }

    @Test void actualRouteStillRejectsRoleAliasesWrongFullGenerationAndLegacySourceBroadening() throws Exception {
        byte[] query=wire("query");JsonNode original=parse(query);
        for(String bad:List.of("-1","-2147483649","2147483648","4294967294","4294967295","true","0.0","\"0\"","null")) {
            for(String field:List.of("actor_character_id","target_character_id")) {
                ObjectNode changed=((ObjectNode)original).deepCopy();((ObjectNode)changed.at("/result/active_scheme_sway")).set(field,parse(bad.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class,()->SwayNativeWire.target(StrictJson.canonical(changed),requestId(original),binding(),0),field+":"+bad);
            }
            ObjectNode publicArgs=StrictJson.object();publicArgs.put("expected_revision","9");publicArgs.set("target_character_id",parse(bad.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->SwayDriverCodec.decodeTarget(raw(publicArgs)),bad);
        }
        for(String field:List.of("actor_character_id","target_character_id")) {
            ObjectNode changed=((ObjectNode)original).deepCopy();ObjectNode body=(ObjectNode)changed.at("/result/active_scheme_sway");body.put(field,body.get(field).intValue()^0x0100_0000);
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.target(StrictJson.canonical(changed),requestId(original),binding(),0),"same slot different generation "+field);
        }
        byte[] receipt=wire("receipt");JsonNode originalReceipt=parse(receipt);
        for(String bad:List.of("-1","4294967295","true","0.0","\"0\"","null")) {
            ObjectNode changed=((ObjectNode)originalReceipt).deepCopy();((ObjectNode)changed.at("/result/active_scheme_sway_formal")).set("scheme_instance_id",parse(bad.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.receipt(StrictJson.canonical(changed),requestId(originalReceipt),binding(),actionId(),0,BigInteger.valueOf(4)),bad);
        }
        ObjectNode changed=((ObjectNode)originalReceipt).deepCopy();((ObjectNode)changed.at("/result/active_scheme_sway_formal")).put("scheme_instance_generation",1);
        assertThrows(IllegalArgumentException.class,()->SwayNativeWire.receipt(StrictJson.canonical(changed),requestId(originalReceipt),binding(),actionId(),0,BigInteger.valueOf(4)));
        for(long role:new long[]{Integer.MIN_VALUE,-2,0}) {
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.character(role),"historical import character domain");
            assertThrows(IllegalArgumentException.class,()->SwayNativeWire.currentCharacter(role),"unmigrated Stop entry");
        }
        var episode=resolved().resolved().orElseThrow();var legacy=SwayFormalCodec.originalResolved(episode);
        var legacyReceipt=(ObjectNode)legacy.get("native_receipt");legacyReceipt.put("exact_ck3_build","1.20.0.3");legacyReceipt.put("exe_sha256","94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
        var copied=new G2M6Contracts.Episode(episode.identity(),Optional.empty(),Optional.empty(),Optional.empty(),ProjectionJson.object(StrictJson.canonical(legacy),SwayNativeWire.MAX));
        var rejected=assertThrows(IllegalArgumentException.class,()->M6TerminalSourceComposition.compose(copied,M6TerminalSourceComposition.Inputs.unqueried()));
        assertEquals("integer outside contract range",rejected.getMessage(),"legacy source retains its prior role ingress domain");
    }

    private static Ledger resolved() throws Exception {
        byte[] query = wire("query"); var read = SwayNativeWire.target(query, requestId(parse(query)), binding(), 0);
        byte[] submit = wire("submit"); var ack = SwayNativeWire.startAck(submit, requestId(parse(submit)), actionId(), read);
        assertFalse(ack.applied());
        var seed = new Ledger(binding().before().machineId(), EPISODE, Optional.empty(), Optional.empty(), List.of(), Optional.empty(), SOURCE);
        var pending = reduce(seed, new StartIntent(actionId(), read, MandatoryContext.CLEAR, StartAdmission.PUBLIC_NATIVE_FINAL));
        pending = reduce(pending, new StartAcknowledged(ack)); assertTrue(pending.resolved().isEmpty());
        byte[] response = wire("receipt"); var receipt = SwayNativeWire.receipt(response, requestId(parse(response)), binding(), actionId(), 0, read.captureEpoch());
        assertEquals(0, receipt.fullId()); assertEquals(0, receipt.generation());
        pending = reduce(pending, new ReceiptRetained(receipt)); assertTrue(pending.resolved().isEmpty());
        byte[] post = wire("post-query"); var independent = SwayNativeWire.target(post, requestId(parse(post)), binding(), 0);
        assertTrue(independent.captureEpoch().compareTo(receipt.postCaptureEpoch()) > 0);
        assertEquals(1, independent.instances().size()); assertEquals(0, independent.instances().get(0).fullId());
        return reduce(pending, new Recovered(independent));
    }

    private static String actionId() throws Exception { return parse(wire("submit")).at("/result/active_scheme_sway_formal/action_id").textValue(); }
    private static SwayNativeWire.Binding binding() throws Exception {
        JsonNode body = parse(wire("query")).at("/result/active_scheme_sway");
        var id = new JointBudgetSelector.Frame(body.get("actor_character_id").bigIntegerValue(), body.get("snapshot_revision").bigIntegerValue(), body.get("date_raw").bigIntegerValue());
        var frame = new JointBudgetSelector.ProposalFrame(id, "software-native-action-snapshot", BigInteger.valueOf(9), EPISODE);
        var observation = new ObservationIdentity("xenoamess-full-tower-eb9d2c1186", new GameGeneration(73, new PythonOnlyUInt64(new BigInteger("134370000000000074"))), frame, 1);
        return new SwayNativeWire.Binding(observation, "software-native-action-session", BigInteger.ONE, "software-native-action-authority", SwayNativeWire.BUILD, SwayNativeWire.EXE);
    }
    private static PlanningReadRequest request(ReadContract<?> contract, OpportunityJson.Obj arguments) throws Exception {
        var binding = binding(); return new PlanningReadRequest(binding.before(), new G2Source(binding.before().machineId(), NOW.toString(), SwayNativeWire.BUILD, SOURCE), binding.sessionId(), contract.operation(), arguments, NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt guarded(ReadContract<?> contract, PlanningReadRequest request, byte[] original) {
        var evidence = new GuardEvidence(request.before(), request.source(), request.sessionId(), BigInteger.ONE, contract.operation(), SOURCE, SOURCE, "software-native-action-authority", NOW, NOW.plusSeconds(30));
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64)); JsonNode packet = parse(original);
        return new PlanningReadReceipt(request, contract.contractId(), requestId(packet), guard, guard, ack(original));
    }
    private static NativeActionPort.AckReceived ack(byte[] original) {
        JsonNode packet=parse(original);byte[] framed=ByteBuffer.allocate(original.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(original.length).put(original).array();
        return new NativeActionPort.AckReceived(requestId(packet),true,Optional.of(raw((ObjectNode)packet.get("result"))),new RawJson(original),framed);
    }
    private static OpportunityJson.Obj targetArguments(long target) { var row=StrictJson.object();row.put("target_character_id",target);return (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(row)); }
    private static byte[] wire(String role) throws Exception {
        try (var in = SwayCurrent4PublicActionRouteTest.class.getResourceAsStream("/sway/m6-native-current4-action-route.json")) {
            assertNotNull(in, "mandatory actual Native action route bytes, never cloud-authored positives"); JsonNode rows = parse(in.readAllBytes());
            assertTrue(rows.isArray()); assertEquals(4, rows.size());
            for (JsonNode row : rows) if (role.equals(row.get("role").textValue())) {
                byte[] bytes = row.get("original_utf8").textValue().getBytes(StandardCharsets.UTF_8); assertEquals(row.get("sha256").textValue(), ActionCodec.sha256(bytes)); return bytes;
            }
            throw new AssertionError("missing actual Native wire role " + role);
        }
    }
    private static JsonNode parse(byte[] bytes) { return StrictJson.parse(bytes, SwayNativeWire.MAX); }
    private static String requestId(JsonNode packet) { return packet.get("request_id").textValue(); }
    private static RawJson raw(ObjectNode row) { return new RawJson(StrictJson.canonical(row, SwayNativeWire.MAX)); }
    /** Only the original read is installed; every unrelated archive request fails. */
    private static final class ReadOnlyArchive implements ActionPorts.OutcomeArchive {
        private final ExactRef reference;private final PlanningReadReceipt original;
        ReadOnlyArchive(ExactRef reference,PlanningReadReceipt original){this.reference=reference;this.original=original;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){assertEquals(reference,ref);return original;}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt read){assertEquals(original,read);return reference;}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw new AssertionError();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw new AssertionError();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw new AssertionError();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw new AssertionError();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw new AssertionError();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw new AssertionError();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw new AssertionError();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw new AssertionError();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw new AssertionError();}
        @Override public ExactRef preserveMaterial(RawJson value){throw new AssertionError();}
        @Override public RawJson loadMaterial(ExactRef ref){throw new AssertionError();}
        @Override public ExactRef materialReferenceOf(RawJson value){throw new AssertionError();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw new AssertionError();}
        @Override public byte[] loadNativeFrame(ExactRef ref){throw new AssertionError();}
    }
}

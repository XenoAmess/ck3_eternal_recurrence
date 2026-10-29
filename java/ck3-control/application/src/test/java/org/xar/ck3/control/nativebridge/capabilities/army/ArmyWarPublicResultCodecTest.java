package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real retained Python producers -> full Java native receipt -> exact public shape -> durable JSON. No Game qualification. */
public final class ArmyWarPublicResultCodecTest {
    private static final BigInteger U64 = new BigInteger("18446744073709551615");
    private static ObjectNode captured;

    @Test void actualDeclarationWhitePeaceAndOccupationProducersRetainTheirDifferentPublicShapes() throws Exception {
        for (JsonNode vector : vectors().path("cases")) {
            ObjectNode snapshot = (ObjectNode) vector.path("snapshot");
            Context context = context(snapshot);
            PublicMethod method = switch (vector.path("kind").asText()) {
                case "declarations" -> PublicMethod.QUERY_DECLARABLE_WARS;
                case "white" -> PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS;
                case "occupation" -> PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1;
                default -> throw new AssertionError("unexpected original producer kind");
            };
            ArmyCalls.Call call = method == PublicMethod.QUERY_DECLARABLE_WARS
                    ? new ArmyCalls.Frame(method, new ArmyCalls.Revision(new Present<>(BigInteger.TWO)))
                    : new ArmyCalls.War(method, new ArmyCalls.Revision(new Present<>(BigInteger.TWO)), BigInteger.valueOf(77));
            var scope = new ArmyWarReadCodec.Scope(call, context, immutable(snapshot), Optional.empty());
            var receipt = receipt(scope, (ObjectNode) vector.path("native"));
            var actual = ArmyWarReadCodec.decode(scope, receipt);
            byte[] originalBytes = receipt.original().originalFrame().bytes().clone();
            RawJson wire = ArmyWarPublicResultCodec.encode(scope, receipt, actual, Optional.empty());
            Obj restored = ArmyPublicWire.decodeExactSourceBound(wire, context);
            assertEquals(immutable((ObjectNode) vector.path("expected")), restored);
            if(method==PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS||method==PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1) {
                var driver=ArmyWarOriginalResultCodec.encode(scope,receipt,actual);ObjectNode expectedDriver=(ObjectNode)vector.path("driver_result");
                assertEquals(immutable(expectedDriver),DriverJson.object(driver.bytes(),DriverJson.MAX_NATIVE_BYTES));
                assertFalse(ArmyJson.parse(driver.bytes()).has("war_id"),"Driver result keeps its distinct original shape");
            }
            assertEquals(wire, ArmyPublicWire.encodeExactSourceBound(restored, context));
            assertEquals(actual, ArmyWarReadCodec.decode(scope, receipt));
            assertArrayEquals(originalBytes, receipt.original().originalFrame().bytes());
            ObjectNode encoded = ArmyJson.parse(wire.bytes());
            assertEquals(U64.toString(), encoded.path("query_sequence").textValue());
            assertFalse(encoded.has("queried_date_raw"));
            assertEquals(method != PublicMethod.QUERY_DECLARABLE_WARS, encoded.has("queried_revision"));
            assertFalse(encoded.has("public_wire_schema")); assertFalse(encoded.has("integer_paths"));
        }
    }

    @Test void fullOriginalReceiptRejectsChangedPublicValueRequestAndCurrentWarRecipient() throws Exception {
        ObjectNode vector = (ObjectNode) vectors().path("cases").get(1);
        ObjectNode snapshot = (ObjectNode) vector.path("snapshot");
        var call = new ArmyCalls.War(PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS,
                new ArmyCalls.Revision(new Present<>(BigInteger.TWO)), BigInteger.valueOf(77));
        var scope = new ArmyWarReadCodec.Scope(call, context(snapshot), immutable(snapshot), Optional.empty());
        var receipt = receipt(scope, (ObjectNode) vector.path("native"));
        var value = (ArmyWarReadCodec.WhitePeace) ArmyWarReadCodec.decode(scope, receipt);
        var material = (ObjectNode) OpportunityJson.toNode(value.normalizedResult());
        material.put("queried_revision", 99);
        var forged = new ArmyWarReadCodec.WhitePeace(value.war(), value.actor(), value.recipient(),
                value.present(), value.pendingInteraction(), immutable(material));
        assertThrows(IllegalArgumentException.class, () -> ArmyWarPublicResultCodec.encode(scope, receipt, forged, Optional.empty()));
        ObjectNode changed = snapshot.deepCopy();
        ((ObjectNode) changed.path("active_wars").get(0)).put("primary_opponent_character_id", 303);
        var crossed = new ArmyWarReadCodec.Scope(call, scope.context(), immutable(changed), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ArmyWarPublicResultCodec.encode(crossed, receipt, value, Optional.empty()));
        var wrong = new ArmyCalls.War(call.method(), call.revision(), BigInteger.valueOf(78));
        var wrongScope = new ArmyWarReadCodec.Scope(wrong, scope.context(), immutable(snapshot), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> ArmyWarPublicResultCodec.encode(wrongScope, receipt, value, Optional.empty()));
    }

    @Test void occupationMetadataCannotBorrowAnotherConnectionOrEpisode() throws Exception {
        ObjectNode vector = (ObjectNode) vectors().path("cases").get(2);
        ObjectNode snapshot = (ObjectNode) vector.path("snapshot");
        var call = new ArmyCalls.War(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,
                new ArmyCalls.Revision(new Present<>(BigInteger.TWO)), BigInteger.valueOf(77));
        var scope = new ArmyWarReadCodec.Scope(call, context(snapshot), immutable(snapshot), Optional.empty());
        for (ObjectNode changed : List.of(((ObjectNode) vector.path("native")).deepCopy().put("queried_connection_generation", 2),
                ((ObjectNode) vector.path("native")).deepCopy().put("queried_episode_run_id", "different-episode"))) {
            var original = receipt(scope, changed);
            assertThrows(IllegalArgumentException.class, () -> ArmyWarPublicResultCodec.encode(scope, original,
                    ArmyWarReadCodec.decode(scope, original), Optional.empty()));
        }
    }

    @Test void originalCombatDerivedIntegersAndCopiedMemoryKindsRoundTripWithoutPrecisionLoss() {
        ObjectNode raw = ArmyJson.empty();
        ObjectNode ring = raw.putObject("knight_stat_consumption_projection_v1").put("overwritten_events", U64);
        ObjectNode event = ring.putArray("events").addObject().put("sequence", U64).put("linked_character_identity", U64)
                .put("projected_effectiveness_raw", BigInteger.valueOf(Long.MIN_VALUE));
        event.putArray("modifier_raw").add(BigInteger.valueOf(Long.MAX_VALUE)).addNull();
        ObjectNode context = event.putArray("consumed_contexts").addObject().put("context_identity", U64).put("operand_raw", BigInteger.valueOf(Long.MIN_VALUE));
        context.putObject("consumed_pc").put("identity", U64);
        context.putObject("preparation_capture_at_consumption").put("character_identity", "0xabcdef").putObject("pre_six_aggregate").putObject("pc").put("identity", "0x123456");
        ObjectNode transfer = context.putObject("installed_transfer_lineage").putObject("capture_at_consumption").putArray("records").addObject();
        transfer.putObject("stage").put("model_a_identity", U64);
        transfer.putObject("physical_postimage").putArray("ordered_payload_raw64").add(U64);
        event.putObject("preparation_stage_join").putArray("owned_capture_compositions").addObject().put("model_identity", "0xfedcba");
        event.putObject("installed_transfer_pc_stage_join").putArray("property_inputs").addObject().put("preparation_pc_identity", U64);
        ObjectNode special = raw.putObject("current_special_knight_initial_value");
        BigInteger sum = BigInteger.ONE.shiftLeft(90).negate();
        special.putObject("ready_member_contributions_by_role").putObject("attacker").put("ready_member_damage_raw_sum", sum);
        special.putArray("members_in_query_order").addObject().putObject("calculation_ledger").putObject("selected_source")
                .putObject("observation").putArray("operand_raw").add(BigInteger.valueOf(Long.MIN_VALUE)).addNull();
        raw.putObject("loaded_playset_proof").putObject("managed_session").put("native_session_generation", U64);
        Context source = context(snapshot()); RawJson encoded = ArmyPublicWire.encodeExactSourceBound(immutable(raw), source);
        assertEquals(immutable(raw), ArmyPublicWire.decodeExactSourceBound(encoded, source));
        assertEquals(U64.toString(), ArmyJson.parse(encoded.bytes()).path("knight_stat_consumption_projection_v1").path("events").get(0).path("linked_character_identity").textValue());
        assertEquals(sum.toString(), ArmyJson.parse(encoded.bytes()).path("current_special_knight_initial_value").path("ready_member_contributions_by_role").path("attacker").path("ready_member_damage_raw_sum").textValue());
        ObjectNode wrong = raw.deepCopy(); ((ObjectNode) wrong.path("knight_stat_consumption_projection_v1")).put("overwritten_events", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(immutable(wrong), source));
        ObjectNode tooWide = raw.deepCopy(); ((ObjectNode) tooWide.path("knight_stat_consumption_projection_v1").path("events").get(0)).put("projected_effectiveness_raw", U64);
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(immutable(tooWide), source));
        ObjectNode noncanonical = ArmyJson.parse(encoded.bytes());
        ((ObjectNode) noncanonical.path("current_special_knight_initial_value").path("ready_member_contributions_by_role").path("attacker")).put("ready_member_damage_raw_sum", "-0");
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(noncanonical)), source));
    }

    @Test void existingMetadataMustBeCompleteIntegerTypedAndBoundBeforeProjection() {
        Context context = context(snapshot());
        ObjectNode raw = ArmyJson.empty().put("query_sequence", U64).put("date_raw", 77).put("flag", false).putNull("unknown");
        raw.putArray("values").add(0).add(1); raw.put("opaque", "001");
        RawJson noMeta = ArmyPublicWire.encodeExactSourceBound(immutable(raw), context);
        assertEquals(immutable(raw), ArmyPublicWire.decodeExactSourceBound(noMeta, context));
        assertFalse(ArmyJson.parse(noMeta.bytes()).has("queried_revision"));
        ObjectNode bound = raw.deepCopy().put("queried_snapshot_id", "native:3").put("queried_revision", 2).put("queried_native_revision", 3);
        RawJson encoded = ArmyPublicWire.encodeExactSourceBound(immutable(bound), context);
        assertEquals(immutable(bound), ArmyPublicWire.decodeExactSourceBound(encoded, context));
        assertTrue(ArmyJson.parse(encoded.bytes()).path("date_raw").isIntegralNumber());
        assertFalse(ArmyJson.parse(encoded.bytes()).has("missing"));
        for (ObjectNode invalid : List.of(
                raw.deepCopy().put("queried_revision", 2),
                bound.deepCopy().put("queried_revision", true),
                bound.deepCopy().put("queried_native_revision", 3.0),
                bound.deepCopy().put("queried_revision", "2"),
                bound.deepCopy().put("queried_snapshot_id", "other"),
                bound.deepCopy().put("queried_revision", 4),
                raw.deepCopy().put("undeclared", U64))) {
            assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encodeExactSourceBound(immutable(invalid), context));
        }
        for (String invalid : List.of("02", "+2", "-0", "2.0")) {
            ObjectNode changed = ArmyJson.parse(encoded.bytes()).put("queried_revision", invalid);
            assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(changed)), context));
        }
        ObjectNode wrongType = ArmyJson.parse(encoded.bytes()).put("query_sequence", 18446744073709551615.0);
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decodeExactSourceBound(new RawJson(ArmyJson.bytes(wrongType)), context));
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.encode(immutable(bound), context), "Army13 source metadata collision contract remains strict");
    }

    @Test void actualWarEntryPublicCharacterKeyHasOneContractAndRejectsTheOldWrongProvinceKey() {
        ObjectNode args = ArmyJson.empty().put("expected_revision", U64.toString()); args.putArray("target_character_ids").add(808);
        var value = (ArmyCalls.WarEntry) ArmyCallCodec.decode(PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS, new RawJson(ArmyJson.bytes(args)));
        assertEquals(List.of(new PositiveId(808)), value.targets());
        assertEquals(args, ArmyJson.parse(ArmyCallCodec.encode(value).bytes()));
        ObjectNode wrong = args.deepCopy(); wrong.set("target_province_ids", wrong.remove("target_character_ids"));
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(value.method(), new RawJson(ArmyJson.bytes(wrong))));
        ObjectNode doubled = args.deepCopy(); doubled.withArray("target_character_ids").add(809);
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(value.method(), new RawJson(ArmyJson.bytes(doubled))));
        ObjectNode bool = args.deepCopy(); bool.withArray("target_character_ids").set(0, ArmyJson.empty().booleanNode(true));
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(value.method(), new RawJson(ArmyJson.bytes(bool))));
    }

    @Test void currentKnightNativeRevisionUsesCanonicalUint64AndNeverAnUnsafeNumericRoundTrip() {
        ObjectNode args = ArmyJson.empty().put("subject_public_cunit_id", 0).put("character_id", 1).put("regiment_id", 2)
                .put("expected_played_character_id", 101).put("expected_war_id", 0).put("expected_native_carmy_id", 3)
                .put("expected_combat_id", 4).put("expected_province_id", 5).put("expected_date_raw", 77)
                .put("expected_revision", U64.toString()).put("expected_native_revision", U64.toString()).put("expected_snapshot_id", "native:" + U64);
        var call = ArmyCallCodec.decode(PublicMethod.QUERY_CURRENT_BATTLE_KNIGHT_V1, new RawJson(ArmyJson.bytes(args)));
        assertEquals(args, ArmyJson.parse(ArmyCallCodec.encode(call).bytes()));
        assertEquals(call, ArmyCallCodec.decode(call.method(), ArmyCallCodec.encode(call)));
        for (JsonNode invalid : List.of(ArmyJson.empty().numberNode(U64), ArmyJson.empty().booleanNode(true),
                ArmyJson.empty().textNode("01"), ArmyJson.empty().textNode("18446744073709551616"), ArmyJson.empty().numberNode(1.0))) {
            ObjectNode changed = args.deepCopy(); changed.set("expected_native_revision", invalid);
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(call.method(), new RawJson(ArmyJson.bytes(changed))));
        }
        ObjectNode safe = args.deepCopy().put("expected_native_revision", 7).put("expected_snapshot_id", "native:7");
        assertEquals("7", ArmyJson.parse(ArmyCallCodec.encode(ArmyCallCodec.decode(call.method(), new RawJson(ArmyJson.bytes(safe)))).bytes()).path("expected_native_revision").textValue());
    }

    /** Software original-packet DATA only; transport parsing and authority remain in native-transport. */
    private static byte[] originalPacketData(RawJson payload) {
        byte[] original = payload.bytes();
        return ByteBuffer.allocate(Integer.BYTES + original.length).order(ByteOrder.LITTLE_ENDIAN)
                .putInt(original.length).put(original).array();
    }

    private static PlanningReadReceipt receipt(ArmyWarReadCodec.Scope scope, ObjectNode result) {
        Context context = scope.context(); OperationKey operation = new OperationKey(result.path("step").textValue());
        var args = DriverJson.object(ArmyCallCodec.encode(scope.call()).bytes(), DriverJson.MAX_NATIVE_BYTES);
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), operation, args, context.deadline());
        var evidence = new GuardEvidence(context.before(), context.source(), context.sessionId(), BigInteger.ONE, operation,
                context.source().sourceRef(), context.source().sourceRef(), "synthetic-public-wire-only", Instant.parse("2026-10-24T00:00:00Z"), context.deadline());
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
        ObjectNode top = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", "original-public-war").put("ok", true); top.set("result", result);
        RawJson packet = new RawJson(ArmyJson.bytes(top));
        var ack = new NativeActionPort.AckReceived("original-public-war", true, Optional.of(new RawJson(ArmyJson.bytes(result))), packet, originalPacketData(packet));
        return new PlanningReadReceipt(request, "synthetic-original-no-read-authority", "original-public-war", guard, guard, ack);
    }
    private static ObjectNode snapshot() {
        ObjectNode n = ArmyJson.empty().put("snapshot_id", "native:3").put("revision", 2).put("native_revision", 3).put("date_raw", 77)
                .put("paused", true).put("map_ready", true).put("episode_run_id", "public-war-fixture");
        n.putObject("played_character").put("character_id", 101).put("alive", true);
        n.putObject("diagnostics").put("connection_generation", 1).put("bridge_pid", 42);
        n.putArray("active_wars").addObject().put("war_id", 77).put("primary_opponent_character_id", 202);
        return n;
    }
    private static Context context(ObjectNode snapshot) {
        var sourceRef = new ExactRef("synthetic-public-producer-no-game", 1, "a".repeat(64));
        var source = new G2Source("synthetic-protocol-test", "2026-10-24T00:00:00Z", "1.20.0.4", sourceRef);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), snapshot.path("native_revision").bigIntegerValue(), BigInteger.valueOf(77)),
                snapshot.path("snapshot_id").textValue(), BigInteger.TWO, "public-war-fixture");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1),
                source, "public-war-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static Obj immutable(ObjectNode n) { return DriverJson.object(ArmyJson.bytes(n), DriverJson.MAX_NATIVE_BYTES); }

    /** Actual Python producer vectors exposed only from the application test artifact. DATA cannot issue authority. */
    public record OriginalPublicVector(ArmyWarReadCodec.Scope scope,PlanningReadReceipt receipt,
            ArmyWarReadCodec.Observation observed,Obj expectedPublic) { }
    public static List<OriginalPublicVector> originalPublicVectors()throws Exception {
        var actual=new java.util.ArrayList<OriginalPublicVector>();
        for(JsonNode vector:vectors().path("cases")) {
            ObjectNode snapshot=(ObjectNode)vector.path("snapshot");Context context=context(snapshot);
            PublicMethod method=switch(vector.path("kind").asText()) {case "declarations"->PublicMethod.QUERY_DECLARABLE_WARS;case "white"->PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS;case "occupation"->PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1;default->throw new AssertionError("closed original vector kind");};
            ArmyCalls.Call call=method==PublicMethod.QUERY_DECLARABLE_WARS?new ArmyCalls.Frame(method,new ArmyCalls.Revision(new Present<>(BigInteger.TWO))):new ArmyCalls.War(method,new ArmyCalls.Revision(new Present<>(BigInteger.TWO)),BigInteger.valueOf(77));
            var scope=new ArmyWarReadCodec.Scope(call,context,immutable(snapshot),Optional.empty());var original=receipt(scope,(ObjectNode)vector.path("native"));
            actual.add(new OriginalPublicVector(scope,original,ArmyWarReadCodec.decode(scope,original),immutable((ObjectNode)vector.path("expected"))));
        }
        return List.copyOf(actual);
    }

    private static synchronized ObjectNode vectors() throws Exception {
        if (captured != null) return captured.deepCopy();
        verifyOriginals();
        captured = BattleOriginalOracle.call("""
                import copy,json,sys,threading
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                from test_declaration_contract import _declaration
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as Driver
                from xar_autoplayer.bridge.service import GameplayBridgeService as Service
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='public-war-fixture',played_character=dict(character_id=101,alive=True),diagnostics=dict(connection_generation=1,bridge_pid=42),active_wars=[dict(war_id=77,primary_opponent_character_id=202)])
                class Source:
                    _declaration_result_binding=staticmethod(Driver._declaration_result_binding)
                    def __init__(self,native):self.native=native;self._driver_state_lock=threading.Lock()
                    def take_snapshot_without_native_command_history(self):return copy.deepcopy(snapshot)
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(snapshot)
                    def _execute_primitive_step(self,*a,**kw):return {**copy.deepcopy(self.native),'backend_id':'native-headless'}
                class Public:
                    _execute_typed_war_step=Service._execute_typed_war_step
                    def __init__(self,result):self.result=result
                    def capabilities(self):return dict(action_steps=[self.result['step']])
                    def snapshot(self,**kw):return copy.deepcopy(snapshot)
                    def execute_step(self,*a,**kw):return copy.deepcopy(self.result)
                    def _strategy_state_dir(self):return None
                    def _observed_planning_source_frame(self,*a):return dict(status='incomplete')
                native=dict(step='query-declarable-wars',accepted=True,status='available',query_sequence=2**64-1,declarable_wars=[_declaration()])
                d=Source(native)
                published=Driver._publish_declarable_war_result(d,{**native,'backend_id':'native-headless'},Driver._declaration_result_binding(snapshot))
                expected=Service.query_declarable_wars(Public(published),expected_revision=2)
                cases=[dict(kind='declarations',snapshot=snapshot,native=native,expected=expected)]
                white=dict(schema_version=1,war_id=77,actor_character_id=101,recipient_character_id=202,state='exact_absent',present=False,pending_interaction_id=-1)
                native=dict(step='query-outbound-war-white-peace-status-v1-77',accepted=True,status='available',query_sequence=2**64-1,outbound_war_white_peace_status=white)
                published=Driver._execute_outbound_war_white_peace_status_query(Source(native),native['step'],starting=snapshot,selected_revision=2,war_id=77)
                expected=Service.query_outbound_war_white_peace_status(Public(published),77,expected_revision=2)
                cases.append(dict(kind='white',snapshot=snapshot,native=native,expected=expected,driver_result=published))
                from xar_autoplayer.bridge.version_identity import CK3_12004
                snapshot=copy.deepcopy(snapshot);snapshot['active_wars'][0]['player_side']='attacker'
                domain=dict(schema='xar.ck3.war-occupation-targets.v1',schema_version=1,available=True,collection_complete=True,status='available',snapshot_revision=3,date_raw=77,war_id=77,actor_character_id=101,primary_attacker_character_id=101,primary_defender_character_id=202,player_side='attacker',game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,unavailable_reason=None,side_counts=[dict(territory_side=side,eligible=0,occupied=0,native_candidate_count=0,collection_complete=True) for side in ('attacker','defender')],rows=[])
                native=dict(step='query-war-occupation-targets-v1-77',accepted=True,status='available',query_sequence=2**64-1,war_occupation_targets_v1=domain)
                published=Driver._execute_war_occupation_targets_v1_query(Source(native),native['step'],expected_revision=2)
                expected=Service.query_war_occupation_targets_v1(Public(published),77,expected_revision=2)
                cases.append(dict(kind='occupation',snapshot=snapshot,native=native,expected=expected,driver_result=published))
                snapshot=copy.deepcopy(snapshot);snapshot.pop('episode_run_id');snapshot['diagnostics'].pop('connection_generation')
                published=Driver._execute_war_occupation_targets_v1_query(Source(native),native['step'],expected_revision=2)
                expected=Service.query_war_occupation_targets_v1(Public(published),77,expected_revision=2)
                cases.append(dict(kind='occupation',snapshot=snapshot,native=native,expected=expected,driver_result=published))
                print(json.dumps(dict(cases=cases),allow_nan=False))
                """, ArmyJson.empty());
        verifyOriginals(); return captured.deepCopy();
    }
    private static void verifyOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        if (configured == null || configured.isBlank()) throw new IllegalStateException("actual retained producer source root required");
        Path root = Path.of(configured).toRealPath();
        for (String[] pin : new String[][] {
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py","b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"},
                {"ck3_autonomous_player/tests/unit/test_declaration_contract.py","3595ee51b6d52bf34f8de0753ad1fd0a4fe84840fbdc2deee071e698c6db1512"}}) {
            Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "original producer changed");
        }
    }
}



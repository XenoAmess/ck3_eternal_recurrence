package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
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
import org.xar.ck3.control.wave2.military.declarationcontract.DeclarationContract;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Synthetic callbacks pass through the real old transport/normalizers and the complete Java receipt consumer. No game qualification. */
final class HolyWarReadMigrationTest {
    private static ObjectNode captured;
    @Test void originalPrivateTransportFeedsFullReceiptAndLosslessPublicAndColdConsumers() throws Exception {
        for (JsonNode vector : vectors().path("cases")) {
            var scope = scope((ObjectNode) vector.path("snapshot")); var receipt = receipt(scope, (ObjectNode) vector.path("wire"));
            var value = (ArmyWarReadCodec.HolyContext) ArmyWarReadCodec.decode(scope, receipt);
            assertEquals(vector.path("expected"), ArmyJson.parse(ArmyWarReadCodec.encode(value).bytes()));
            assertEquals(value, ArmyWarReadCodec.decode(scope, receipt));
            var wire = ArmyWarPublicResultCodec.encode(scope, receipt, value, Optional.empty());
            assertEquals(value.normalizedResult(), ArmyPublicWire.decodeExactSourceBound(wire, scope.context()));
            assertEquals(org.xar.ck3.control.wave2.military.holycost.HolyCostObservation.TotalCost.UNKNOWN, value.value().totalCost());
            assertTrue(value.defenderJoin().isPresent());
            assertEquals(vector.path("wire"), ArmyJson.parse(receipt.original().originalFrame().bytes()));
        }
    }
    @Test void fullSiblingCannotBorrowReceiverOrFrameOrInventAJoinScore() throws Exception {
        ObjectNode vector = (ObjectNode) vectors().path("cases").get(0); var scope = scope((ObjectNode) vector.path("snapshot"));
        for (String field : List.of("primary_attacker_character_id", "native_revision", "joiner_count")) {
            ObjectNode wire = vector.path("wire").deepCopy(); ObjectNode join = (ObjectNode) wire.path("result").path(HolyWarDefenderJoinCodec.DOMAIN);
            join.put(field, join.path(field).bigIntegerValue().add(BigInteger.ONE));
            assertThrows(IllegalArgumentException.class, () -> ArmyWarReadCodec.decode(scope, receipt(scope, wire)), field);
        }
        ObjectNode guessed = vector.path("wire").deepCopy(); ((ObjectNode) guessed.path("result").path(HolyWarDefenderJoinCodec.DOMAIN)).put("is_final_join_score", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarReadCodec.decode(scope, receipt(scope, guessed)));
        ObjectNode loose = vector.path("wire").deepCopy(); ((ObjectNode) loose.path("result").path(HolyWarDefenderJoinCodec.DOMAIN)).put("capture_epoch", true);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarReadCodec.decode(scope, receipt(scope, loose)));
        ObjectNode falsePrivate = vector.path("wire").deepCopy(); ((ObjectNode) falsePrivate.path("result")).put("private_build", false);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarReadCodec.decode(scope, receipt(scope, falsePrivate)));
        ObjectNode crossed = vector.path("snapshot").deepCopy(); crossed.put("date_raw", crossed.path("date_raw").intValue() + 1);
        var crossedScope = scope(crossed);
        assertThrows(IllegalArgumentException.class, () -> ArmyWarReadCodec.decode(crossedScope, receipt(crossedScope, (ObjectNode) vector.path("wire"))));
    }
    private static ArmyWarReadCodec.Scope scope(ObjectNode snapshot) {
        var ref = new ExactRef("synthetic-holy-original-transport-fixture", 1, "a".repeat(64));
        var source = new G2Source("synthetic-test-no-native-qualification", "2026-10-24T00:00:00Z", snapshot.path("diagnostics").path("hello").path("expected_ck3_version").textValue(), ref);
        var nativeRevision = snapshot.path("native_revision").bigIntegerValue();
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(), nativeRevision,
                snapshot.path("date_raw").bigIntegerValue()), snapshot.path("snapshot_id").textValue(), snapshot.path("revision").bigIntegerValue(), "synthetic-holy-episode");
        var context = new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source,
                "synthetic-holy-session", Instant.parse("2026-10-24T00:01:00Z"));
        var selected = DeclarationContract.normalize(snapshot.path("declarable_wars")).getFirst();
        var call = new ArmyCalls.Declaration(PublicMethod.QUERY_PLAYER_ORDINARY_HOLY_WAR_DECLARATION_CONTEXT_PRIVATE_V1,
                new ArmyCalls.Revision(new Present<>(snapshot.path("revision").bigIntegerValue())), selected.declarationId());
        return new ArmyWarReadCodec.Scope(call, context, DriverJson.object(ArmyJson.bytes(snapshot), DriverJson.MAX_NATIVE_BYTES), Optional.of(selected));
    }
    private static PlanningReadReceipt receipt(ArmyWarReadCodec.Scope scope, ObjectNode original) throws Exception {
        var c = scope.context(); var operation = new OperationKey("query-player-ordinary-holy-war-declaration-context-v1");
        var args = OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(scope.call()).bytes()), "actual typed query arguments");
        var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), operation, args, c.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(c.before(), c.source(), c.sessionId(), BigInteger.ONE, operation, c.source().sourceRef(), c.source().sourceRef(),
                "synthetic-holy-source", Instant.parse("2026-10-24T00:00:00Z"), c.deadline()), true, true, true, "b".repeat(64));
        RawJson full = new RawJson(ArmyJson.bytes(original)); String id = original.path("request_id").textValue();
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(ArmyJson.bytes(original.path("result")))), full, ArmyOriginalPacketFixture.packet(full));
        return new PlanningReadReceipt(request, "synthetic-original-holy-contract", id, guard, guard, ack);
    }
    private static synchronized ObjectNode vectors() throws Exception {
        if (captured != null) return captured.deepCopy(); verifyOriginals();
        captured = BattleOriginalOracle.call("""
                import json,sys,copy
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'))
                from test_player_ordinary_holy_war_declaration_context_12004_whole_wire import ACTOR,TARGET,ADDITIONAL,TITLE_IDS,FRAME,CB_COSTS_RAW
                from xar_autoplayer.bridge.version_identity import CK3_12003,CK3_12004
                from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_observation import RESOURCE_KEYS
                from xar_autoplayer.bridge.player_ordinary_holy_war_declaration_context_private_transport import query_player_ordinary_holy_war_declaration_context_private_v1
                cases=[]
                for build,mode in [(CK3_12004,'ready'),(CK3_12003,'ready'),(CK3_12004,'faith_failure'),(CK3_12004,'fallback'),(CK3_12004,'disabled')]:
                    selected=dict(target_character_id=TARGET,casus_belli_index=0,casus_belli_key='religious_war',configuration_index=0,claimant_character_id=-1,target_title_ids=TITLE_IDS)
                    identity=str(TARGET)+'-0-0'
                    snapshot=dict(snapshot_id='native:17',revision=4,native_revision=17,date_raw=FRAME['date_raw'],paused=True,map_ready=True,played_character=dict(character_id=ACTOR,alive=True),declarable_wars=[dict(selected,declaration_id=identity)],diagnostics=dict(hello=dict(expected_ck3_version=build.game_version,expected_ck3_sha256=build.executable_sha256)))
                    context=dict(schema='player_ordinary_holy_war_declaration_context_v1',read_only=True,game_version=build.game_version,executable_sha256=build.executable_sha256,available=True,unavailable_reason=None,capture_epoch=1007,public_revision=4,native_revision=17,date_raw=FRAME['date_raw'],played_character_id=ACTOR,declaration_id=identity,selected_declaration=selected,context_actor_character_id=ACTOR,context_recipient_character_id=TARGET,context_additional_role_character_id=ADDITIONAL,context_claimant_character_id=-1,recipient_uses_native_fallback=False,additional_role_uses_native_fallback=(mode=='fallback'),claimant_uses_native_fallback=True,final_can_send=False,cb_cost=dict(available=True,unavailable_reason=None,resource_keys=list(RESOURCE_KEYS),resource_costs_raw=CB_COSTS_RAW,raw_scale=100000),generic_interaction_cost_raw=None,total_declaration_cost_raw=None,total_cost_ready=False)
                    ready=mode!='fallback';faith=mode!='faith_failure';enabled=mode!='disabled'
                    join=dict(schema=('ck3_12004_' if build==CK3_12004 else 'ck3_12003_')+'holy_war_defender_join_inputs_v1',read_only=True,available=ready,unavailable_reason=None if ready else 'native_role_fallback',capture_epoch=1007,native_revision=17,public_revision=4,date_raw=FRAME['date_raw'],played_character_id=ACTOR,declaration_id=identity,selected_declaration=selected,primary_attacker_character_id=ADDITIONAL,primary_defender_character_id=TARGET,primary_defender_faith_available=True,primary_defender_faith_unavailable_reason=None,primary_defender_rite_id=5,primary_defender_faith_id=6,cb_flags_raw=(1<<15) if enabled else 0,defender_faith_can_join=enabled,native_joiner_set_observed=ready,joiner_count=1 if ready and enabled else 0,joiners=[],raw_scale=100000,unit='fervor_points',is_final_join_score=False)
                    if ready and enabled:join['joiners']=[dict(character_id=0xffffffff,row_faith_available=faith,row_fervor_available=faith,unavailable_reason=None if faith else 'faith_unavailable',rite_id=5 if faith else None,faith_id=6 if faith else None,faith_fervor_raw=-1 if faith else None,matches_primary_defender_faith=True if faith else None)]
                    result=dict(step='query-player-ordinary-holy-war-declaration-context-v1',accepted=True,private_build=True,read_only=True,advertised=False,backend_id=build.backend_id('player-ordinary-holy-war-declaration-context-v1'),game_version=build.game_version,executable_sha256=build.executable_sha256,domain_key='player_ordinary_holy_war_declaration_context_v1',snapshot_revision=17,public_revision=4,date_raw=FRAME['date_raw'],status='observed',player_ordinary_holy_war_declaration_context=context,player_holy_war_defender_join_inputs=join)
                    class Driver:
                        allow_private_player_ordinary_holy_war_declaration_context_query=True
                        def __init__(self):self.endpoint=self;self.state=self;self.sent=[];self.wire=None
                        def take_snapshot(self):return copy.deepcopy(snapshot)
                        def send(self,request):self.sent.append(copy.deepcopy(request))
                        def wait_for_command_result(self,request_id,timeout):
                            self.wire=dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,result=copy.deepcopy(result));return copy.deepcopy(self.wire)
                    driver=Driver();expected=query_player_ordinary_holy_war_declaration_context_private_v1(driver,expected_revision=4,declaration_id=identity)
                    if len(driver.sent)!=1:raise RuntimeError('original query did not send exactly once')
                    cases.append(dict(snapshot=snapshot,wire=driver.wire,expected=expected))
                print(json.dumps({'cases':cases},allow_nan=False))
                """, ArmyJson.empty());
        verifyOriginals(); return captured.deepCopy();
    }
    private static void verifyOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if (configured == null || configured.isBlank()) throw new IllegalStateException("original root required");
        Path root = Path.of(configured).toRealPath();
        String[][] pins = {
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_war_defender_join_inputs.py","3e899728b3afd21e0013da8bba0a244e7401be40704b052c12f6ee2177340e38"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_transport.py","a1e1f1fa1cb18019ee6aa8062595b41187d4daf576060d405a777287c44f553e"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/player_ordinary_holy_war_declaration_context_private_observation.py","ca36df8e0a0914508ed3e3b6d3436d1e4eb935896006b3d96966b18d31e2e8e2"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/g2_private_query_transport.py","02db15ca2b070f814df06cad10da2bb9b4c8e2e1aec621f9228a5ab12f971315"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py","fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"},
            {"ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py","9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"},
            {"ck3_autonomous_player/tests/test_player_ordinary_holy_war_declaration_context_12004_whole_wire.py","3deb7743b88741bae36b9119a1624913c21298080837f9299662c5f6521aa42f"}};
        for (String[] pin : pins) { Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "original private query source drift"); }
    }
}

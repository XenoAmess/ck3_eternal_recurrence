package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
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

/** Actual retained original V1 validators -> full Java receipt/domain consumer. Synthetic source values grant no canonical-history or Game qualification. */
final class PrewarPartialMigrationTest {
    @Test void originalIndependentTopAndFullPartialDomainAgreeIncludingZeroAndSignedNativeHandles() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> new PrewarPartialCodec.IndependentSource(new UInt64(BigInteger.ZERO), UInt64.positive(BigInteger.ONE), new PositiveId(202), new PositiveId(303)));
        verifyOriginals(); ObjectNode captured = BattleOriginalOracle.call("""
                import json,copy
                from xar_autoplayer.bridge.version_identity import CK3_12004
                from xar_autoplayer.bridge.prewar_force_coalition_contract import normalize_prewar_force_coalition_v1
                from xar_autoplayer.bridge.prewar_force_coalition_transport import validate_prewar_force_coalition_execution_receipt
                selected=dict(target_character_id=202,casus_belli_index=0,casus_belli_key='claim_cb',configuration_index=-1,claimant_character_id=-1,target_title_ids=[0,17])
                declaration=dict(selected,declaration_id='202-0--1');expected=dict(declaration,effective_target_character_id=303)
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='partial-fixture',played_character=dict(character_id=101,alive=True),declarable_wars=[declaration],diagnostics=dict(connection_generation=1,hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))
                def allies(owner,ids):return dict(owner_character_id=owner,available=True,unavailable_reason=None,collection_complete=True,ally_character_ids=ids,unresolved_source_character_ids=[],dead_source_character_ids=[])
                def force(owner,armies,available,unraised,legal):
                    return dict(owner_character_id=owner,raised_available=available,raised_unavailable_reason=None if available else 'incomplete',raised_armies=armies,raised_current_soldiers=sum(a['current_soldiers'] for a in armies) if available else None,raised_maximum_soldiers=sum(a['maximum_soldiers'] for a in armies) if available else None,unraised_available=unraised is not None,unraised_unavailable_reason=None if unraised is not None else 'unread',unraised_soldiers=unraised,native_raise_legal=legal)
                forces=[force(101,[dict(army_id=0,current_soldiers=0,maximum_soldiers=0)],True,0,True),force(303,[dict(army_id=1,current_soldiers=50,maximum_soldiers=100)],True,40,False),force(-2147483648,[dict(army_id=2,current_soldiers=None,maximum_soldiers=30)],False,None,None),force(0,None,False,None,None)]
                domain=dict(schema_version=1,status='available_partial',read_only=True,game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,capture_epoch=7,native_revision=3,public_revision=2,date_raw=77,actor_character_id=101,declaration_id='202-0--1',selected_declaration=selected,effective_target_character_id=303,ticket=9,query_sequence=9,current_allies=[allies(101,[-2147483648]),allies(303,[0])],owner_forces=forces,actor_ready_unraised_lower_soldiers=0,enemy_upper_soldiers=None,enemy_force_coverage_complete=False,complete_initial_participants_ready=False,automatic_declaration_enabled=False)
                result=dict(step='query-prewar-force-coalition-coverage-v1',accepted=True,status='available_partial',private_build=True,read_only=True,advertised=False,domain_key='prewar_force_coalition_coverage',prewar_force_coalition_coverage=domain)
                top=dict(type='command_result',protocol_version=1,request_id='partial-original',ok=True,execution_receipt=dict(ticket=9,query_sequence=9,capture_epoch=7),result=result)
                cases=[]
                def add(name,edit=None):
                    packet=copy.deepcopy(top);frame=copy.deepcopy(snapshot)
                    if edit:edit(packet,frame)
                    try:
                        receipt,result=validate_prewar_force_coalition_execution_receipt(packet,expected_request_id='partial-original')
                        value=normalize_prewar_force_coalition_v1(result['prewar_force_coalition_coverage'],snapshot=frame,expected_declaration=expected,expected_request_binding=receipt)
                        answer=dict(accepted=True,domain=value)
                    except ValueError:answer=dict(accepted=False)
                    cases.append(dict(name=name,top=packet,snapshot=frame,expected=answer))
                add('zero-public-unit-and-zero-native-ally-full-signed-generation')
                add('canonical-sha-case',lambda p,s:p['result']['prewar_force_coalition_coverage'].__setitem__('executable_sha256',CK3_12004.executable_sha256.lower()))
                add('domain-ticket-cannot-bind-itself',lambda p,s:p['result']['prewar_force_coalition_coverage'].__setitem__('ticket',10))
                add('receipt-ticket-query-mismatch',lambda p,s:p['execution_receipt'].__setitem__('query_sequence',10))
                add('wrong-effective-target',lambda p,s:p['result']['prewar_force_coalition_coverage'].__setitem__('effective_target_character_id',404))
                add('duplicate-public-unit-cross-owners',lambda p,s:p['result']['prewar_force_coalition_coverage']['owner_forces'][1]['raised_armies'][0].__setitem__('army_id',0))
                add('absent-native-character-id',lambda p,s:p['result']['prewar_force_coalition_coverage']['current_allies'][0]['ally_character_ids'].__setitem__(0,-1))
                add('invented-enemy-upper',lambda p,s:p['result']['prewar_force_coalition_coverage'].__setitem__('enemy_upper_soldiers',0))
                add('invented-declaration-authority',lambda p,s:p['result']['prewar_force_coalition_coverage'].__setitem__('automatic_declaration_enabled',True))
                add('actor-ready-lower-without-raise-legality',lambda p,s:p['result']['prewar_force_coalition_coverage']['owner_forces'][0].__setitem__('native_raise_legal',False))
                add('bool-soldier-count',lambda p,s:p['result']['prewar_force_coalition_coverage']['owner_forces'][0]['raised_armies'][0].__setitem__('current_soldiers',True))
                add('float-frame',lambda p,s:s.__setitem__('revision',2.0))
                add('partial-raised-aggregate',lambda p,s:p['result']['prewar_force_coalition_coverage']['owner_forces'][2].__setitem__('raised_current_soldiers',0))
                add('incomplete-owner-set',lambda p,s:p['result']['prewar_force_coalition_coverage']['owner_forces'].pop())
                add('missing-domain-field',lambda p,s:p['result']['prewar_force_coalition_coverage'].pop('enemy_upper_soldiers'))
                add('unadvertised-private-shape',lambda p,s:p['result'].__setitem__('advertised',True))
                print(json.dumps({'cases':cases},allow_nan=False))
                """, ArmyJson.empty()); verifyOriginals();
        int accepted = 0;
        for (JsonNode vector : captured.path("cases")) {
            ObjectNode snapshot = (ObjectNode) vector.path("snapshot"), top = (ObjectNode) vector.path("top");
            if (!vector.path("expected").path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> consume(snapshot, top), vector.path("name").textValue()); continue;
            }
            var observed = consume(snapshot, top); sameJson(vector.path("expected").path("domain"), PrewarPartialCodec.encode(observed.value()));
            assertFalse(observed.value().automaticDeclarationEnabled()); assertFalse(observed.value().completeInitialParticipantsReady());
            assertEquals(0, observed.value().forces().getFirst().raisedArmies().orElseThrow().getFirst().army().value());
            assertTrue(observed.value().forces().getLast().raisedArmies().isEmpty());
            assertEquals(observed, consume(snapshot, top)); var publicWire = ArmyPublicWire.encodeExactSourceBound(observed.normalizedResult(), context(snapshot));
            assertEquals(observed.normalizedResult(), ArmyPublicWire.decodeExactSourceBound(publicWire, context(snapshot))); accepted++;
        }
        assertEquals(2, accepted); assertEquals(16, captured.path("cases").size());
    }
    private static ArmyWarReadCodec.CoalitionV1 consume(ObjectNode snapshot, ObjectNode top) throws Exception {
        var c = context(snapshot); var choice = DeclarationContract.normalize(snapshot.path("declarable_wars")).getFirst();
        var call = new ArmyCalls.Declaration(PublicMethod.QUERY_PREWAR_FORCE_COALITION_COVERAGE_V1, new ArmyCalls.Revision(new Present<>(BigInteger.TWO)), choice.declarationId());
        var source = new PrewarPartialCodec.IndependentSource(UInt64.positive(BigInteger.valueOf(5)), UInt64.positive(BigInteger.valueOf(6)), new PositiveId(202), new PositiveId(303));
        var scope = new ArmyWarReadCodec.Scope(call, c, DriverJson.object(ArmyJson.bytes(snapshot), DriverJson.MAX_NATIVE_BYTES), Optional.of(choice), Optional.of(source));
        var operation = new OperationKey(PrewarPartialCodec.STEP); var args = OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(call).bytes()), "partial original arguments");
        var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), operation, args, c.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(c.before(), c.source(), c.sessionId(), BigInteger.ONE, operation, c.source().sourceRef(), c.source().sourceRef(), "synthetic-partial", Instant.parse("2026-10-24T00:00:00Z"), c.deadline()), true, true, true, "b".repeat(64));
        RawJson original = new RawJson(ArmyJson.bytes(top)); var ack = new NativeActionPort.AckReceived("partial-original", true, Optional.of(new RawJson(ArmyJson.bytes(top.path("result")))), original, ArmyOriginalPacketFixture.packet(original));
        var receipt = new PlanningReadReceipt(request, "synthetic-partial-no-history-qualification", "partial-original", guard, guard, ack);
        var observed = (ArmyWarReadCodec.CoalitionV1) ArmyWarReadCodec.decode(scope, receipt);
        var publicWire = ArmyWarPublicResultCodec.encode(scope,receipt,observed,Optional.of(source.declarationQuerySequence()));
        assertEquals(observed.normalizedResult(),ArmyPublicWire.decodeExactSourceBound(publicWire,c));
        return observed;
    }
    private static Context context(ObjectNode snapshot) {
        var ref = new ExactRef("synthetic-partial-no-game-source", 1, "a".repeat(64)); var source = new G2Source("synthetic-test-no-game", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), BigInteger.valueOf(3), BigInteger.valueOf(77)), "native:3", BigInteger.TWO, "partial-fixture");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "partial-fixture-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static void sameJson(JsonNode expected, JsonNode actual) { assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8)); }
    private static void verifyOriginals() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if (configured == null || configured.isBlank()) throw new IllegalStateException("actual original root required");
        Path root = Path.of(configured).toRealPath();
        for (String[] pin : new String[][] {
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_contract.py","0895ccaa64bbaec908e843bb15604d14da46f051276070ac5379f490c27e1eac"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_transport.py","28ffe1bc6cd9f8042417e16c97bb7c76fe812d5d1386f9015909010eb7203299"}}) {
            Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "actual V1 source drift");
        }
    }
}

package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.FactionAlertReadService.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.FactionReadReplay;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.wave2.finance.factionalerts.FactionAlertModel;

/** Actual Character14 Core/reader/projector/serializer/WriteFrame originals through installed-family
 * preparation/decode, pure archive replay and public projection. Context/guards are explicit DATA;
 * this test supplies no real writer permit, native read invocation, Game or action authority. */
final class FactionAlertNativeCharacterContractTest {
    private static final ExactRef REF=new ExactRef("D:/fixture/faction-character14.java",1,"a".repeat(64));
    private static final G2Source SOURCE=new G2Source("xenoamess-full-tower-eb9d2c1186","2026-10-30T17:50:00Z","1.20.0.4",REF);
    private static final Instant DEADLINE=Instant.parse("2099-01-01T00:00:00Z");
    private static byte[] resource(String name)throws Exception {
        try(var input=FactionAlertNativeCharacterContractTest.class.getResourceAsStream("/factionalerts/character-native90/"+name+"/public-alerts-whole.json.packet.bin")){assertNotNull(input,name);return input.readAllBytes();}
    }
    private static ObservationIdentity before(BigInteger actor) {
        var identity=new JointBudgetSelector.Frame(actor,BigInteger.ONE,BigInteger.valueOf(53175816));
        return new ObservationIdentity(SOURCE.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(identity,"character14-native",BigInteger.ONE,"character14-episode"),1);
    }
    private static Context context(ObservationIdentity before) {
        return new Context(before,SOURCE,"character14-session",DEADLINE,new SameFrameWars(before,new RawJson("[]".getBytes(java.nio.charset.StandardCharsets.UTF_8))),"native-headless");
    }
    private static FactionReadReplay.Context replayContext(ObservationIdentity before) {
        return new FactionReadReplay.Context(before,SOURCE,"character14-session",DEADLINE,new RawJson("[]".getBytes(java.nio.charset.StandardCharsets.UTF_8)),"native-headless");
    }
    @ParameterizedTest
    @ValueSource(strings={"actor-zero","actor-min","leader-zero","leader-min","member-zero","member-min","mixed-members"})
    void actualNativeCharacterPacketUsesInstalledContractArchiveAndPublicProjection(String name)throws Exception {
        byte[] original=resource("candidate-"+name);var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(original));assertArrayEquals(original,wire.packet().value());
        RawJson full=new RawJson(wire.payload().value()),token=new RawJson(wire.result().token().orElseThrow().value());JsonNode frame=StrictJson.parse(token.bytes()).get("player_faction_alerts");
        var held=before(frame.get("player_character_id").bigIntegerValue());var selected=new Selection(new Query(BigInteger.ONE),context(held));
        Contracts owner=new Contracts(REF,REF);var catalog=new RootReadContractCatalog(List.of(),owner.families());var issued=owner.issue(catalog,selected);var request=request(selected);
        assertSame(issued,owner.issue(catalog,selected));assertEquals("{}",new String(issued.prepare(request,wire.requestId()).additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
        var binding=new GuardEvidence(held,SOURCE,selected.context().sessionId(),BigInteger.ONE,new OperationKey(STEP),REF,REF,"explicit-software-guard",DEADLINE.minusSeconds(30),DEADLINE);
        var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var ack=new NativeActionPort.AckReceived(wire.requestId(),wire.nativeOk(),Optional.of(token),full,original);
        var receipt=new PlanningReadReceipt(request,issued.contractId(),wire.requestId(),guard,guard,ack);
        Observation decoded=issued.decode(receipt);assertEquals(decoded,issued.replay(receipt));assertEquals(decoded,decodeArchivedOriginal(receipt,selected.context().wars(),"native-headless"));
        assertEquals(decoded.frame(),FactionReadReplay.replayArchived(receipt,selected.context().wars().activeWars(),"native-headless").frame());
        assertArrayEquals(token.bytes(),decoded.originalResult().bytes());assertArrayEquals(original,receipt.original().originalPacket());
        var available=assertInstanceOf(FactionAlertModel.Available.class,decoded.frame());assertEquals(frame.get("player_character_id").intValue(),available.playerCharacterId());assertEquals(1,available.targetingFactionCount());
        var row=available.targetingFactions().getFirst();JsonNode nativeRow=frame.get("targeting_factions").get(0);
        assertEquals(nativeRow.get("target_character_id").intValue(),row.targetCharacterId());
        JsonNode leader=nativeRow.get("leader_character_id");assertEquals(leader.isNull()?Optional.empty():Optional.of(leader.intValue()),row.leaderCharacterId());
        List<Integer> members=new ArrayList<>();nativeRow.get("character_member_ids").forEach(value->members.add(value.intValue()));assertEquals(members,row.characterMemberIds());
        if(name.equals("mixed-members"))assertEquals(List.of(Integer.MIN_VALUE,-16777214,3),members);
        RawJson publicValue=encodePublic(selected,decoded);var restored=decodePublic(selected,publicValue);assertEquals(decoded.frame(),restored.frame());assertEquals(decoded.normalizedAlert(),restored.normalizedAlert());
        JsonNode publicFrame=StrictJson.parse(publicValue.bytes()).get("player_faction_alerts");assertEquals(frame.get("player_character_id"),publicFrame.get("player_character_id"));
        assertEquals(nativeRow.get("character_member_ids"),publicFrame.get("targeting_factions").get(0).get("character_member_ids"));
        assertEquals(decoded.frame(),decodePublic(selected,encodePublic(selected,decodeToken(selected,token))).frame());
        assertEquals(available.playerCharacterId(),replayContext(held).player());
    }
    @ParameterizedTest
    @ValueSource(strings={"-1","2147483648","4294967294","4294967295","-2147483649"})
    void installedAndArchivedActorContextsRejectSentinelAndUnsignedAliases(String value) {
        BigInteger actor=new BigInteger(value);
        RuntimeException installed=assertThrows(RuntimeException.class,()->context(before(actor)));
        RuntimeException archived=assertThrows(RuntimeException.class,()->replayContext(before(actor)));
        assertTrue(installed instanceof IllegalArgumentException||installed instanceof ArithmeticException);
        assertTrue(archived instanceof IllegalArgumentException||archived instanceof ArithmeticException);
    }
    @ParameterizedTest
    @ValueSource(strings={"actor-zero","actor-min"})
    void actualNativeActorPacketReachesLowerArchiveProducerIndependently(String name)throws Exception {
        byte[] packet=resource("candidate-"+name);var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        RawJson token=new RawJson(wire.result().token().orElseThrow().value());JsonNode frame=StrictJson.parse(token.bytes()).get("player_faction_alerts");
        var archived=replayContext(before(frame.get("player_character_id").bigIntegerValue()));
        var observed=FactionReadReplay.decodeOriginal(archived,BigInteger.ONE,wire.requestId(),new RawJson(wire.payload().value()),token);
        assertEquals(frame.get("player_character_id").intValue(),assertInstanceOf(FactionAlertModel.Available.class,observed.frame()).playerCharacterId());
        assertArrayEquals(token.bytes(),observed.originalResult().bytes());
    }
    @ParameterizedTest
    @ValueSource(strings={"stale-recipient-zero","stale-recipient-min","absent-actor","duplicate-member","stale-actor-zero","stale-actor-min","absent-member"})
    void actualNativeRefusalPacketsRemainUnavailable(String name)throws Exception {
        var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(resource("control-"+name)));
        var selected=new Selection(new Query(BigInteger.ONE),context(before(BigInteger.valueOf(50331649))));
        var observed=decodeOriginal(selected,wire.requestId(),new RawJson(wire.payload().value()),new RawJson(wire.result().token().orElseThrow().value()));
        var unavailable=assertInstanceOf(FactionAlertModel.Unavailable.class,observed.frame());assertTrue(unavailable.readiness().allFalse());
        assertEquals(observed.frame(),decodePublic(selected,encodePublic(selected,observed)).frame());
    }
    @ParameterizedTest
    @ValueSource(strings={"true","0.0","-2147483648.0","\"0\"","null"})
    void typedOriginalDecoderRejectsNonIntegerActorTokens(String value)throws Exception {
        byte[] packet=resource("candidate-leader-zero");var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        byte[] original=wire.result().token().orElseThrow().value();JsonNode nativeFrame=StrictJson.parse(original).get("player_faction_alerts");var selected=new Selection(new Query(BigInteger.ONE),context(before(nativeFrame.get("player_character_id").bigIntegerValue())));
        String text=new String(original,java.nio.charset.StandardCharsets.UTF_8),field="\"player_character_id\":"+nativeFrame.get("player_character_id").bigIntegerValue();
        assertTrue(text.contains(field));String changed=text.replace(field,"\"player_character_id\":"+value);
        assertThrows(IllegalArgumentException.class,()->decodeToken(selected,new RawJson(changed.getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    @Test void publicProjectionPreservesExactSourceBindingAndIntegerDateGuards()throws Exception {
        var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(resource("candidate-leader-zero")));
        var token=new RawJson(wire.result().token().orElseThrow().value());
        var actor=StrictJson.parse(token.bytes()).get("player_faction_alerts").get("player_character_id").bigIntegerValue();
        var selected=new Selection(new Query(BigInteger.ONE),context(before(actor)));
        var encoded=encodePublic(selected,decodeToken(selected,token));
        String original=new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8);
        JsonNode publicValue=StrictJson.parse(encoded.bytes());int rejected=0;
        for(String section:List.of("source","binding")) {
            JsonNode actual=publicValue.get(section);
            String sectionText=new String(StrictJson.canonical(actual),java.nio.charset.StandardCharsets.UTF_8);
            String exact="\""+section+"\":"+sectionText;assertTrue(original.contains(exact));
            String date="\"date_raw\":53175816";assertTrue(sectionText.contains(date));
            for(String malformed:List.of("53175816.0","5.3175816e7","true","false","\"53175816\"","null","53175817")) {
                String mutated=original.replace(exact,"\""+section+"\":"+sectionText.replace(date,"\"date_raw\":"+malformed));
                assertThrows(IllegalArgumentException.class,()->decodePublic(selected,new RawJson(mutated.getBytes(java.nio.charset.StandardCharsets.UTF_8))),section+" date="+malformed);rejected++;
            }
            var names=new ArrayList<String>();actual.fieldNames().forEachRemaining(names::add);
            for(String field:names) {
                var changed=(com.fasterxml.jackson.databind.node.ObjectNode)actual.deepCopy();changed.remove(field);
                String mutated=original.replace(exact,"\""+section+"\":"+new String(StrictJson.canonical(changed),java.nio.charset.StandardCharsets.UTF_8));
                assertThrows(IllegalArgumentException.class,()->decodePublic(selected,new RawJson(mutated.getBytes(java.nio.charset.StandardCharsets.UTF_8))),section+" missing "+field);rejected++;
                changed=(com.fasterxml.jackson.databind.node.ObjectNode)actual.deepCopy();changed.put(field,"wrong-original-value");
                String wrong=original.replace(exact,"\""+section+"\":"+new String(StrictJson.canonical(changed),java.nio.charset.StandardCharsets.UTF_8));
                assertThrows(IllegalArgumentException.class,()->decodePublic(selected,new RawJson(wrong.getBytes(java.nio.charset.StandardCharsets.UTF_8))),section+" changed "+field);rejected++;
            }
            var extra=(com.fasterxml.jackson.databind.node.ObjectNode)actual.deepCopy();extra.put("unexpected",true);
            String extraField=original.replace(exact,"\""+section+"\":"+new String(StrictJson.canonical(extra),java.nio.charset.StandardCharsets.UTF_8));
            assertThrows(IllegalArgumentException.class,()->decodePublic(selected,new RawJson(extraField.getBytes(java.nio.charset.StandardCharsets.UTF_8))),section+" extra field");rejected++;
        }
        assertEquals(38,rejected);
    }
    @Test void issuedContractAndArchivedReadRetainCompleteSelectionAndTransportGuards()throws Exception {
        byte[] original=resource("candidate-leader-zero");var wire=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(original));RawJson token=new RawJson(wire.result().token().orElseThrow().value()),full=new RawJson(wire.payload().value());
        var actor=StrictJson.parse(token.bytes()).get("player_faction_alerts").get("player_character_id").bigIntegerValue();var held=before(actor);var selected=new Selection(new Query(BigInteger.ONE),context(held));var owner=new Contracts(REF,REF);var catalog=new RootReadContractCatalog(List.of(),owner.families());var issued=owner.issue(catalog,selected);
        assertThrows(IllegalArgumentException.class,()->owner.issue(new RootReadContractCatalog(List.of(),List.of()),selected));
        assertThrows(QueryFailure.class,()->new Selection(new Query(BigInteger.TWO),selected.context()));
        var binding=new GuardEvidence(held,SOURCE,selected.context().sessionId(),BigInteger.ONE,new OperationKey(STEP),REF,REF,"explicit-software-guard",DEADLINE.minusSeconds(30),DEADLINE);var guard=new PlanningReadGuard(binding,true,true,true,"b".repeat(64));
        var ack=new NativeActionPort.AckReceived(wire.requestId(),true,Optional.of(token),full,original);var receipt=new PlanningReadReceipt(request(selected),issued.contractId(),wire.requestId(),guard,guard,ack);
        byte[] changed=original.clone();changed[0]^=1;var badAck=new NativeActionPort.AckReceived(wire.requestId(),true,Optional.of(token),full,changed);var badPacket=new PlanningReadReceipt(receipt.request(),receipt.contractId(),receipt.requestId(),guard,guard,badAck);
        assertThrows(IllegalArgumentException.class,()->issued.replay(badPacket));
        var badContract=new PlanningReadReceipt(receipt.request(),receipt.contractId()+"-other",receipt.requestId(),guard,guard,ack);assertThrows(IllegalArgumentException.class,()->decodeArchivedOriginal(badContract,selected.context().wars(),"native-headless"));
        assertThrows(IllegalArgumentException.class,()->decodeOriginal(selected,"other-request",full,token));
        assertArrayEquals(original,receipt.original().originalPacket());
    }
    @ParameterizedTest
    @ValueSource(strings={"leader-zero","leader-min","leader-zero-war-zero"})
    void surrenderImpactPreservesNestedRefusalAndCharacterBoundaries(String name) throws Exception {
        actualNativeCharacterPacketUsesInstalledContractArchiveAndPublicProjection("surrender-" + name);
        byte[] original = resource("candidate-surrender-" + name);
        var wire = assertInstanceOf(NativeWire.CommandResult.class, NativeWire.decode(original));
        RawJson token = new RawJson(wire.result().token().orElseThrow().value());
        JsonNode nativeFrame = StrictJson.parse(token.bytes()).get("player_faction_alerts");
        var selected = new Selection(new Query(BigInteger.ONE), context(before(BigInteger.valueOf(50331649))));
        var observed = decodeToken(selected, token);
        var available = assertInstanceOf(FactionAlertModel.Available.class, observed.frame());
        var row = available.targetingFactions().getFirst();
        var impact = row.surrenderImpact().orElseThrow();
        var nativeRow = nativeFrame.get("targeting_factions").get(0);
        var nativeImpact = nativeRow.get("surrender_impact");

        if (name.equals("leader-min")) {
            assertEquals(Integer.MIN_VALUE, row.leaderCharacterId().orElseThrow());
            assertEquals(List.of(Integer.MIN_VALUE), row.characterMemberIds());
        } else {
            assertEquals(0, row.leaderCharacterId().orElseThrow());
            assertEquals(List.of(0), row.characterMemberIds());
        }

        if (name.equals("leader-zero-war-zero")) {
            assertEquals(FactionAlertModel.Status.UNAVAILABLE, impact.status());
            assertEquals("surrender_branch_predicates_unavailable", impact.unavailableReason().orElseThrow().value());
            assertFalse(impact.ordinaryBranchTitleSetsReady());
            assertFalse(impact.countyLossComplete());
            assertFalse(impact.kingdomOutcomeComplete());
            assertTrue(impact.leaderAtWarWithTarget().isEmpty());
            assertEquals(FactionAlertModel.Status.UNAVAILABLE.wire(), nativeImpact.get("status").textValue());
            assertEquals("surrender_branch_predicates_unavailable", nativeImpact.get("unavailable_reason").textValue());
            assertFalse(nativeImpact.get("ordinary_branch_title_sets_ready").booleanValue());
            assertFalse(nativeImpact.get("county_loss_complete").booleanValue());
            assertFalse(nativeImpact.get("kingdom_outcome_complete").booleanValue());
            assertTrue(nativeImpact.get("leader_at_war_with_target").isNull());
        } else {
            assertEquals(FactionAlertModel.Status.AVAILABLE, impact.status());
            assertTrue(impact.unavailableReason().isEmpty());
            assertTrue(impact.ordinaryBranchTitleSetsReady());
            assertTrue(impact.countyLossComplete());
            assertFalse(impact.kingdomOutcomeComplete());
            assertEquals(Boolean.FALSE, impact.leaderAtWarWithTarget().orElseThrow());
            assertEquals(FactionAlertModel.Status.AVAILABLE.wire(), nativeImpact.get("status").textValue());
            assertTrue(nativeImpact.get("unavailable_reason").isNull());
            assertTrue(nativeImpact.get("ordinary_branch_title_sets_ready").booleanValue());
            assertTrue(nativeImpact.get("county_loss_complete").booleanValue());
            assertFalse(nativeImpact.get("kingdom_outcome_complete").booleanValue());
            assertFalse(nativeImpact.get("leader_at_war_with_target").booleanValue());
        }

        assertTrue(impact.playerSubrealmCountyTitleIds().isEmpty());
        assertTrue(impact.memberCounties().isEmpty());
        assertTrue(impact.seizedCounties().isEmpty());
        assertTrue(impact.seizedDuchies().isEmpty());
        assertTrue(impact.playerDirectTitleLossIds().isEmpty());
        assertTrue(impact.playerRemainingDirectCountyTitleIds().isEmpty());
        assertTrue(impact.kingdoms().isEmpty());

        RawJson publicValue = encodePublic(selected, observed);
        var restored = decodePublic(selected, publicValue);
        assertEquals(observed.frame(), restored.frame());
        assertEquals(observed.normalizedAlert(), restored.normalizedAlert());

        JsonNode publicFrame = StrictJson.parse(publicValue.bytes()).get("player_faction_alerts");
        var publicImpact = publicFrame.get("targeting_factions").get(0).get("surrender_impact");
        assertEquals(nativeImpact.get("status"), publicImpact.get("status"));
        assertEquals(nativeImpact.get("unavailable_reason"), publicImpact.get("unavailable_reason"));
        assertEquals(nativeImpact.get("ordinary_branch_title_sets_ready"), publicImpact.get("ordinary_branch_title_sets_ready"));
        assertEquals(nativeImpact.get("county_loss_complete"), publicImpact.get("county_loss_complete"));
        assertEquals(nativeImpact.get("kingdom_outcome_complete"), publicImpact.get("kingdom_outcome_complete"));
        assertEquals(nativeImpact.get("leader_at_war_with_target"), publicImpact.get("leader_at_war_with_target"));
        assertEquals(nativeImpact.get("player_subrealm_county_title_ids"), publicImpact.get("player_subrealm_county_title_ids"));
        assertEquals(nativeImpact.get("member_counties"), publicImpact.get("member_counties"));
        assertEquals(nativeImpact.get("seized_counties"), publicImpact.get("seized_counties"));
        assertEquals(nativeImpact.get("seized_duchies"), publicImpact.get("seized_duchies"));
        assertEquals(nativeImpact.get("player_direct_title_loss_ids"), publicImpact.get("player_direct_title_loss_ids"));
        assertEquals(nativeImpact.get("player_remaining_direct_county_title_ids"), publicImpact.get("player_remaining_direct_county_title_ids"));
        assertEquals(nativeImpact.get("kingdoms"), publicImpact.get("kingdoms"));
    }
}

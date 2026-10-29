package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual public decoder and native request consumers agree on original token, count and identity domains. */
final class ArmyRetreatBoundaryTest {
    @Test void originalUrlSafeTokenAndSignedCombatReachTheActualTypedOrderConsumer() {
        String token = "_Z-0123456789012345678901234567890";
        String original = "{\"expected_revision\":9,\"selected_public_cunit_id\":0,\"expected_combat_id\":-2147483648,\"expected_side_index\":1,\"expected_scope\":\"owner_subset\",\"target_province_id\":2700,\"candidate_token\":\"" + token + "\"}";
        var call = (ArmyCalls.RetreatOrder) ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, json(original));
        assertEquals(token, call.token()); assertEquals(Integer.MIN_VALUE, call.combat().value()); assertEquals(0, call.selected().value());
        assertEquals(call, ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, ArmyCallCodec.encode(call)));
        for (String invalid : List.of("a".repeat(31), "a".repeat(129), "a".repeat(31) + "+")) assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, json(original.replace(token, invalid))));
        assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1, json(original.replace("-2147483648", "-1"))));
    }
    @Test void nativeTerminalCharactersRemainPositiveWhilePublicUnitZeroAndCombatHighBitRemainValid() {
        var none = new ArmyRequests.Terminal(Optional.of(new FullId(Integer.MIN_VALUE)), Optional.of(new PublicUnitId(0)), Optional.of(new UInt64(new BigInteger("18446744073709551615"))), List.of(new FullId(1)));
        assertEquals("query-battle-terminal-transition-v1--2147483648-0-18446744073709551615:characters:1", ArmySteps.terminal(none));
        for (int invalid : List.of(0, -2, Integer.MIN_VALUE)) assertThrows(IllegalArgumentException.class, () -> new ArmyRequests.Terminal(Optional.empty(), Optional.empty(), Optional.empty(), List.of(new FullId(invalid))));
    }
    @Test void full64PublicRevisionAndTerminalCursorUseCanonicalDecimalTextWithoutRoundedNumberFallback() {
        String original = "{\"prior_combat_id\":-2147483648,\"subject_public_cunit_id\":0,\"expected_revision\":\"18446744073709551615\",\"after_terminal_sequence\":\"18446744073709551615\"}";
        var call = (ArmyCalls.Terminal) ArmyCallCodec.decode(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, json(original));
        assertEquals(new BigInteger("18446744073709551615"), call.revision().requireCurrent(new BigInteger("18446744073709551615")));
        assertEquals(call, ArmyCallCodec.decode(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, ArmyCallCodec.encode(call)));
        assertTrue(ArmyJson.parse(ArmyCallCodec.encode(call).bytes()).get("expected_revision").isTextual());
        for (String invalid : List.of("18446744073709551615", "18446744073709551615.0", "true", "\"018446744073709551615\"", "\"18446744073709551616\""))
            assertThrows(IllegalArgumentException.class, () -> ArmyCallCodec.decode(PublicMethod.QUERY_BATTLE_TERMINAL_TRANSITION_V1, json(original.replace("\"expected_revision\":\"18446744073709551615\"", "\"expected_revision\":" + invalid))));
    }
    @Test void observedMapEntryBindsCurrentPausedOwnerWithoutRequiringASecondStartOrStaleReadIds() {
        var game=new org.xar.ck3.control.contracts.GameGeneration(42,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE));
        var entry=new org.xar.ck3.control.continuity.ObservedGameplayEntry.Details("synthetic-retreat","session","episode","native:3",
                game,9,77,101,BigInteger.valueOf(3),BigInteger.ONE,
                new org.xar.ck3.control.continuity.ObservedGameplayEntry.Origin.CurrentMap(),
                entryRef("read"),entryRef("native"),entryRef("driver"),entryRef("facts"));
        var current=observedFrame(entry,5,10,2,true);
        ArmyRetreatDomain.requireObservedCurrentFrame(entry,current);
        assertFalse(entry.toJson().has("start_ack"));
        assertEquals(4,entry.evidence().size());
        assertEquals(entry,org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(entry.toJson()));
        for(String field:List.of("player_character_id","date_raw","revision","native_revision","connection_generation")) {
            var wrong=entry.toJson();var frame=(com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("frame");
            if(field.equals("connection_generation"))frame.put(field,"3");
            else if(field.equals("revision"))frame.put(field,11);
            else if(field.equals("native_revision"))frame.put(field,6);
            else frame.put(field,999);
            var altered=org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(wrong);
            assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(altered,current),field);
        }
        var wrongEpisode=entry.toJson();wrongEpisode.put("episode_id","foreign");
        wrongEpisode.put("evidence_id","observed-gameplay-entry:session:foreign");
        var anotherEpisode=org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(wrongEpisode);
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(anotherEpisode,current));
        var wrongGame=entry.toJson();((com.fasterxml.jackson.databind.node.ObjectNode)wrongGame.get("game")).put("creation_filetime","2");
        var anotherGame=org.xar.ck3.control.continuity.ObservedGameplayEntry.decode(wrongGame);
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(anotherGame,current));
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(entry,observedFrame(entry,5,10,2,false)));
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(entry,observedFrame(entry,2,10,2,true)));
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.requireObservedCurrentFrame(entry,observedFrame(entry,5,8,2,true)));
    }
    @Test void observedRetreatSelectsTheStoredSemanticReferenceFromKnownOriginalData() throws Exception {
        var game=new org.xar.ck3.control.contracts.GameGeneration(42,new org.xar.ck3.control.contracts.PythonOnlyUInt64(BigInteger.ONE));
        var entry=new org.xar.ck3.control.continuity.ObservedGameplayEntry.Details("synthetic-retreat","session","episode","native:3",
                game,9,77,101,BigInteger.valueOf(3),BigInteger.ONE,
                new org.xar.ck3.control.continuity.ObservedGameplayEntry.Origin.CurrentMap(),
                entryRef("read"),entryRef("native"),entryRef("driver"),entryRef("known-original"));
        var semantic=entryRef("semantic-manifest");
        var known=org.xar.ck3.control.contracts.StrictJson.object().put("schema",org.xar.ck3.control.application.driver.DriverSnapshotFacts.ORIGINAL_SCHEMA);
        for(String field:List.of("driver","stamp","original_history_basis","auxiliary","loop"))known.putNull(field);
        known.putArray("action_rows");known.set("observation",semantic.toJson());
        var actual=RawJson.fullMaterial(org.xar.ck3.control.contracts.StrictJson.canonical(known));
        var archive=metadataSelectionArchive(entry.driverFacts(),actual);
        assertEquals(semantic,ArmyRetreatDomain.observedSemanticOriginal(entry,archive));
        assertNotEquals(entry.driverFacts(),ArmyRetreatDomain.observedSemanticOriginal(entry,archive));
        known.putNull("observation");
        var missing=metadataSelectionArchive(entry.driverFacts(),RawJson.fullMaterial(org.xar.ck3.control.contracts.StrictJson.canonical(known)));
        assertThrows(java.io.IOException.class,()->ArmyRetreatDomain.observedSemanticOriginal(entry,missing));
        known.put("schema",org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.SCHEMA);
        var wrong=metadataSelectionArchive(entry.driverFacts(),RawJson.fullMaterial(org.xar.ck3.control.contracts.StrictJson.canonical(known)));
        assertThrows(IllegalArgumentException.class,()->ArmyRetreatDomain.observedSemanticOriginal(entry,wrong));
    }
    /** A read-only metadata selector port; it cannot mint a frame, native result or import. */
    private static org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive metadataSelectionArchive(
            org.xar.ck3.control.contracts.ExactRef expected,RawJson original) {
        return org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class.cast(java.lang.reflect.Proxy.newProxyInstance(
                ArmyRetreatBoundaryTest.class.getClassLoader(),new Class<?>[]{org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive.class},
                (proxy,method,args)->{
                    if(method.getName().equals("loadFullMaterial")) {assertEquals(expected,args[0]);return original;}
                    throw new AssertionError("metadata selection cannot call "+method.getName());
                }));
    }
    private static org.xar.ck3.control.contracts.ExactRef entryRef(String name) {
        return new org.xar.ck3.control.contracts.ExactRef("D:/typed-retreat/"+name+".bin",1,"a".repeat(64));
    }
    private static org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete observedFrame(
            org.xar.ck3.control.continuity.ObservedGameplayEntry.Details entry,long nativeRevision,long publicRevision,long connection,boolean paused) {
        var source=new org.xar.ck3.control.g2.common.G2Source(entry.machineId(),"2026-10-28T00:00:00Z","SYNTHETIC-RETREAT",entryRef("implementation"));
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(entry.actorId()),BigInteger.valueOf(nativeRevision),BigInteger.valueOf(entry.dateRaw())),
                "native:"+nativeRevision,BigInteger.valueOf(publicRevision),entry.episodeId());
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(entry.machineId(),entry.game(),frame,1);
        var semantic=new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of(
                "paused",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(paused),
                "map_ready",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true)));
        return new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(identity,source,entry.sessionId(),
                BigInteger.valueOf(connection),semantic,entryRef("current-frame"),java.time.Instant.parse("2026-10-28T00:00:00Z"),"b".repeat(64));
    }
    private static RawJson json(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
}

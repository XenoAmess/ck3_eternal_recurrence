package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** Original current Python producers generated the checked-in golden bytes; this test executes Java consumers. */
final class RegistryProducerTest {
    private static Binding binding() { return new Binding("registry-fixture-1",BigInteger.valueOf(9),BigInteger.valueOf(7),168,BigInteger.valueOf(9)); }
    private static Source source() { return new Source("game.command.query-campaign-root-context-v1",BigInteger.valueOf(4),"1.20.0.4",RegistryJson.EXE); }
    private static AvailableRoot root() {
        Title primary = new Title(10,3,"duchy");
        return new AvailableRoot(binding(),source(),29829,true,primary,400,null,29829,true,List.of(5),List.of(9),
                List.of(new Related(5,Relation.DIRECT_LANDED_VASSAL,new Title(22,2,"county"),600,29829,29829),
                        new Related(9,Relation.ADJACENT_EXTERNAL_PROVINCE_HOLDER,new Title(33,2,"county"),700,null,9)),
                new Government("feudal_government",List.of("feudal"),1),new Fixed(10000,100000),new Fixed(250000,100000),
                2,4,1,new Council(Status.UNAVAILABLE,"standard_landed_non_nomadic_core_v1",29829,List.of(),false,
                        "actual4_council_position_key_source_unavailable"),List.of(111),
                List.of(new PartitionRow(primary,111,400,true,false,null),new PartitionRow(new Title(11,2,"county"),222,500,false,false,null)));
    }
    private record Event(String key) { }
    private record Interaction(String key) { }
    private static Snapshot<Event,Interaction> snapshot(Presence<Event> event, Presence<Interaction> interaction,
            Presence<List<War>> wars) {
        return new Snapshot<>(binding(),true,29829,true,Component.available(100),Component.available(new Fixed(2000000,100000)),
                event,interaction,wars,"native-headless");
    }
    private static RawJson golden(String name) throws java.io.IOException {
        String resource = "/registry/" + name + ".json";
        try (java.io.InputStream input = RegistryProducerTest.class.getResourceAsStream(resource)) {
            if (input == null) throw new java.io.IOException("Required original producer resource missing from the actual test classpath: " + resource);
            byte[] body = input.readNBytes(RawJson.MAXIMUM_BYTES + 1);
            if (body.length > RawJson.MAXIMUM_BYTES) throw new java.io.IOException("Original producer resource exceeds its exact JSON bound: " + resource);
            return new RawJson(body);
        }
    }
    @Test void actualEntityProducerGoldenAndRoundTrip() throws Exception {
        EntityDirectory.Result value = EntityDirectory.build(root(),new EntityDirectory.Request(Relation.ANY,null,2));
        RawJson encoded = RegistryWire.encodeDirectory(value);
        assertEquals(RegistryJson.object(golden("directory")),RegistryJson.object(encoded));
        assertEquals(RegistryJson.object(encoded),RegistryJson.object(RegistryJson.encode(RegistryJson.object(encoded))));
        assertEquals(9,value.nextAfterCharacterId()); assertEquals(3,value.totalMatchingCount());
        assertEquals(List.of(29829),EntityDirectory.build(root(),new EntityDirectory.Request(Relation.SELF,9,50)).entities().stream().map(EntityDirectory.Entity::characterId).toList());
    }
    @Test void actualBundleProducerGoldenPreservesPartialReadinessAndGeography() throws Exception {
        Snapshot<Event,Interaction> snapshot = snapshot(new NullValue<>(),new NullValue<>(),
                new Present<>(List.of(new War(77,Side.DEFENDER,9,BigInteger.valueOf(-12)))));
        TurnBundle.Result<Event,Interaction> value = TurnBundle.build(snapshot,root());
        RawJson encoded = RegistryWire.encodeBundle(value);
        assertEquals(RegistryJson.object(golden("bundle")),RegistryJson.object(encoded));
        assertEquals(RegistryJson.object(encoded),RegistryJson.object(RegistryJson.encode(RegistryJson.object(encoded))));
        assertFalse(value.readiness().ready()); assertFalse(value.readiness().realmCouncilReady());
        assertEquals(List.of(11),value.realmState().value().territory().directCountiesToOtherTitleHeirs().value());
        assertEquals(Status.UNAVAILABLE,value.realmState().value().territory().successionRealmCountyLoss().status());
        assertEquals(Status.PARTIAL,value.rulerState().value().vitals().status());
    }
    @Test void absenceNullAndUnavailableRootKeepDistinctReadiness() {
        var missing = TurnBundle.build(snapshot(new Missing<>(),new NullValue<>(),new Missing<>()),root());
        assertFalse(missing.readiness().eventPendingReady()); assertFalse(missing.readiness().warSummaryReady());
        assertEquals(Status.UNAVAILABLE,missing.pendingState().value().pendingCharacterInteraction().status());
        var noEvent = TurnBundle.build(snapshot(new NullValue<>(),new NullValue<>(),new Present<>(List.of())),root());
        assertTrue(noEvent.readiness().eventPendingReady()); assertEquals(Status.NOT_APPLICABLE,noEvent.pendingState().value().activeEvent().status());
        var unavailable = EntityDirectory.build(new UnavailableRoot(binding(),source(),"map_not_ready"),new EntityDirectory.Request(Relation.ANY,null,50));
        assertEquals(Status.UNAVAILABLE,unavailable.status()); assertFalse(unavailable.readiness().ready()); assertEquals(List.of(),unavailable.entities());
    }
    @Test void typedInventoryRejectsUnknownRetiredAndMissingActualBindings() {
        PublicRoutes routes = new PublicRoutes();
        assertEquals(240,routes.inventory().size());
        assertEquals(PublicRoutes.Status.RETIRED,routes.describe(PublicMethod.PLAN_NONWAR_TURN).status());
        assertThrows(IllegalArgumentException.class,() -> PublicMethod.exact("query-any-arbitrary-dll-step"));
        assertThrows(IllegalArgumentException.class,() -> routes.freeze(List.of(PublicMethod.PLAN_TURN)));
        assertThrows(NullPointerException.class,() -> new RegistryDelegates(null,null,null,null,null,null));
        assertThrows(IllegalArgumentException.class,() -> new EntityDirectory.Request(Relation.ANY,null,0));
        assertThrows(IllegalArgumentException.class,() -> new Binding("s",BigInteger.ONE,BigInteger.ONE,1,BigInteger.TWO));
    }
    @Test void coreRejectsMissingFieldsWrongIntegerTypesDuplicateKeysAndCompleteSnapshotClaim() {
        String unavailable = "{\"schema\":\"ck3_12004_core_frame_v1\",\"game_version\":\"1.20.0.4\",\"executable_sha256\":\"" + RegistryJson.EXE
                + "\",\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\",\"backend\":\"ck3-1.20.0.4-native-headless-main-thread\",\"status\":\"unavailable\","
                + "\"complete_snapshot\":false,\"core_available\":false,\"application_main_observed\":false,\"unavailable_reason\":\"map_not_ready\","
                + "\"excluded_snapshot_families\":[\"treasury\",\"domain\",\"military\",\"campaign\"],\"date_raw\":null,\"speed\":null,\"paused\":null,"
                + "\"local_player_id\":null,\"map_ready\":null,\"has_played_character\":null,\"played_character_id\":null,\"played_character_alive\":null}";
        assertInstanceOf(CoreFrame.Unavailable.class,CoreFrame.decode(raw(unavailable)));
        assertThrows(IllegalArgumentException.class,() -> CoreFrame.decode(raw(unavailable.replace("\"speed\":null,",""))));
        assertThrows(IllegalArgumentException.class,() -> CoreFrame.decode(raw(unavailable.replace("\"complete_snapshot\":false","\"complete_snapshot\":true"))));
        assertThrows(IllegalArgumentException.class,() -> CoreFrame.decode(raw(unavailable.replace("\"core_available\":false","\"core_available\":0"))));
        assertThrows(IllegalArgumentException.class,() -> raw("{\"id\":1,\"id\":2}"));
        assertThrows(IllegalArgumentException.class,() -> CoreFrame.decode(raw(unavailable.replace("\"date_raw\":null","\"date_raw\":false"))));
    }
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
}


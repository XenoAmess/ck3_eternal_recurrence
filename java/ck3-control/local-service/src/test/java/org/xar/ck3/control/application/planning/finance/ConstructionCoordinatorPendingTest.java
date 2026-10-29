package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RequestIds;
import org.xar.ck3.control.contracts.ExactRef;

final class ConstructionCoordinatorPendingTest {
    private static final String DIGEST = "a".repeat(64);
    @Test void theCoordinatorAndNativeRequestIdentitiesRemainDistinctAcrossThePersistentRoundTrip() {
        Obj legacy = original(); Obj actual = legacy.with("status", new Text("java_intent_prepared"))
                .with("coordinator_action_id", new Text("actual-coordinator-action"))
                .with("coordinator_body_sha256", new Text(DIGEST))
                .with("action_request_id", new Text(RequestIds.forActionBody(DIGEST)));
        var decoded = ConstructionLedgerCodec.intent(object(parse(encode(actual)), "persistent pending"));
        assertEquals(Optional.of("actual-coordinator-action"), decoded.coordinatorActionId());
        assertEquals(RequestIds.forActionBody(DIGEST), decoded.identity().actionRequestId());
        assertNotEquals(decoded.coordinatorActionId().orElseThrow(), decoded.identity().actionRequestId());
        for (Value wrong : List.of(new Bool(true), new Text("other-native-request")))
            assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.intent(actual.with("action_request_id", wrong)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionLedgerCodec.intent(legacy.with("status", new Text("java_intent_prepared"))));
        assertTrue(ConstructionLedgerCodec.intent(legacy).coordinatorActionId().isEmpty());
    }
    @Test void anUnboundDomainRegistryCannotGrantQualificationOrPublishEvenAShapedBody() {
        ExactRef source = new ExactRef("C:/source.java", 1, "b".repeat(64));
        var prepared = ConstructionDomainLifecycle.prepare(List.of(source), source);
        assertThrows(java.io.IOException.class, () -> prepared.verify((org.xar.ck3.control.continuity.writer.WriterContracts.Head) null,
                Optional.empty(), null, new byte[]{'{','}'}));
        assertEquals(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.CONSTRUCTION, prepared.registration().slot());
    }
    @Test void freshConstructionBodyUsesTheWritersCanonicalBytesWithoutChangingJsonTypes() {
        Obj body = object(parse("""
                {"schema":"xar.ck3.construction_formal_pending_v1","pending":null,"applied":null,"applied_prior":[],
                 "java_fresh_initialization_v2":{"original_basis":{"bytes":4969,"path":"D:/actual-basis.bin","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
                 "episode_run_id":"actual-episode","actor_character_id":31254}}
                """.getBytes(StandardCharsets.UTF_8)), "fresh construction body");
        byte[] inserted = encode(body);
        byte[] writer = org.xar.ck3.control.continuity.ContinuityJson.canonical(
                org.xar.ck3.control.continuity.ContinuityJson.parseObject(inserted, ConstructionDomainLifecycle.MAX_BYTES),
                ConstructionDomainLifecycle.MAX_BYTES);
        assertFalse(java.util.Arrays.equals(inserted, writer), "the former producer order differs from the committed reader order");
        byte[] published = ConstructionDomainLifecycle.Prepared.canonicalBody(body);
        assertArrayEquals(writer, published);
        assertEquals(body, object(parse(published), "canonical construction body"));
        Obj audit = object(body.get("java_fresh_initialization_v2"), "fresh audit");
        Obj changed = body.with("java_fresh_initialization_v2", audit.with("actor_character_id", new Bool(true)));
        assertFalse(java.util.Arrays.equals(published, ConstructionDomainLifecycle.Prepared.canonicalBody(changed)));
        java.util.Map<String, Value> withoutPending = new java.util.LinkedHashMap<>(body.members());
        withoutPending.remove("pending");
        assertFalse(java.util.Arrays.equals(published, ConstructionDomainLifecycle.Prepared.canonicalBody(new Obj(withoutPending))));
        Obj firstOrder = body.with("applied_prior", new Arr(List.of(new Text("first"), new Text("second"))));
        Obj secondOrder = body.with("applied_prior", new Arr(List.of(new Text("second"), new Text("first"))));
        assertFalse(java.util.Arrays.equals(ConstructionDomainLifecycle.Prepared.canonicalBody(firstOrder),
                ConstructionDomainLifecycle.Prepared.canonicalBody(secondOrder)));
    }
    static Obj original() {
        String raw = "{\"action_request_id\":\"legacy-native-request\",\"episode_run_id\":\"episode\",\"actor_character_id\":1,\"pre_native_revision\":2,\"pre_date_raw\":100,\"pre_proof_epoch\":3,\"source_bridge_pid\":42,\"source_bridge_creation_date\":\"legacy-process\",\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0,\"gold_before_raw\":100,\"stock_gold_cost_raw\":25}}";
        return object(parse(raw.getBytes(StandardCharsets.UTF_8)), "original pending");
    }
}

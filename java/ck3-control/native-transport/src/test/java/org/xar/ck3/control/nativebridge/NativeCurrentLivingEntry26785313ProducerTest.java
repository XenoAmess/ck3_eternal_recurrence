package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.NativeCurrentLivingInventory26785313ProducerTest.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Original C++ software DATA and actual production factory, never actual Game or new native frames. */
class NativeCurrentLivingEntry26785313ProducerTest {
    private static byte[] raw(String name) throws Exception {
        return switch (name) {
            case "original-entry-confirm_manage.body.json" -> original("entry", name, 782, "daeef2a967cabad956dfebea50cbcbe24a9951a9cf978187cca37bb6909bb37e");
            case "original-entry-open_detail.body.json" -> original("entry", name, 776, "a1dd34bcf0466f044ef03bd8416e05749a8a44e902e1a1abcd62380b2a4711b0");
            case "original-entry-open_inventory.body.json" -> original("entry", name, 782, "f4583fe45cccdd7c5d969e30e456121052c42418e9281b9bba959c4286278e26");
            case "original-entry-open_manage_detail.body.json" -> original("entry", name, 790, "4bc5263292a02bbb011b0a21e109cff10772d1e6805d3039cc34015bd5709de8");
            case "original-entry-open_manage_list.body.json" -> original("entry", name, 786, "4bda0da70e1791014d9b0b109f27a75b086f3676e79a439bff21f98070d0924f");
            case "original-entry-query_detail_entry.body.json" -> original("entry", name, 752, "524b598d85bbdef847f91f438ff3a0e62fb907a96cc185ed1824c46590b0ab80");
            case "original-entry-query_inventory_entry.body.json" -> original("entry", name, 758, "64f3c97633c0b4c4456e021e6e7955bef60376de114bbb0864a6fef34e52324d");
            case "original-entry-query_manage.body.json" -> original("entry", name, 740, "e999872d23f1cedcba176c31176a1e6c11f535645421ea9eef055f7c372c7b61");
            case "response-entry-dispatched.body.json" -> original("entry", name, 1271, "b0c61c605576a8c77a4734f5dafd8fb89b9a3270be88e2efb613645693d916ec");
            case "response-entry-query-0.body.json" -> original("entry", name, 1659, "f8947386099f2141c33996a11feae2bc46987d0502de268b5d7bd7de3b3904f4");
            case "response-entry-query-1.body.json" -> original("entry", name, 1276, "84f199b98c0a4e359161972abfa429fe1b216a0db8fe0f3cb1826d23a584fb06");
            case "response-entry-query-2.body.json" -> original("entry", name, 1270, "03a935cb76d022f9b2b836717c5f105ae07c3a7174781c6cae41921eebcef342");
            case "response-entry-unknown.body.json" -> original("entry", name, 999, "dad29fab9a52a39add8efdba7d0943ce576b99e88b5fc33ae4e4d1eb16b8416d");
            default -> throw new IllegalArgumentException("Unknown original resource: " + name);
        };
    }
    private static CurrentLivingEntryResult frame(String name) throws Exception {
        byte[] original = raw(name); var frame = CurrentLivingEntryResult.decode(result(original));
        assertEquals(frame, CurrentLivingEntryResult.decode(frame.encode()));
        responseIdentity(original, frame.encode(), frame.successful());
        return frame;
    }
    private static void requestFactory(String actionWire, CurrentLivingEntry.Action action) throws Exception {
        var original = StrictJson.object(envelope(raw("original-entry-" + actionWire + ".body.json")),
                Set.of("type", "protocol_version", "request_id", "step", "actor", "target", "arguments", "deadline_unix_ms"));
        var args = StrictJson.object(original.get("arguments"), Set.of("living_entry"));
        var claim = StrictJson.object(args.get("living_entry"), Set.of("schema", "game_version", "executable_sha256",
                "adapter_id", "backend", "action", "expected_core", "provider_generation", "query_sequence"));
        assertEquals(actionWire, action.wire()); assertEquals(actionWire, claim.get("action").textValue());
        assertTrue(claim.get("provider_generation").isIntegralNumber()); assertTrue(claim.get("query_sequence").isIntegralNumber());
        BigInteger provider = claim.get("provider_generation").bigIntegerValue(), query = claim.get("query_sequence").bigIntegerValue();
        assertEquals(action.queryOnly() ? BigInteger.ZERO : MAX_U64, provider);
        assertEquals(action.queryOnly() ? BigInteger.ZERO : MAX_U64, query);
        var request = CurrentLivingEntry.request(core(claim), action, provider, query);
        assertEquals(CurrentLivingEntry.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "living_entry"));
        assertEquals(9, fields.get("living_entry").size()); assertTrue(fields.get("arguments").isEmpty());
        // Exercise the actual production strict8 encoder. A hand-built test envelope would conceal production regressions.
        byte[] packet = NativeGameTransport.currentLivingFixedEntryUiPacket(original.get("request_id").textValue(), request,
                original.get("deadline_unix_ms").bigIntegerValue());
        factory("entry", original, request, packet);
    }

    @Test void originalManageQueryKeepsCompleteModelNullableConfirmAndObservedSelection() throws Exception {
        var frame = frame("response-entry-query-0.body.json"); assertEquals(CurrentLivingEntry.Action.QUERY_MANAGE, frame.action());
        var manage = frame.source().orElseThrow().manage().orElseThrow(); assertTrue(manage.completeModelCensus()); assertTrue(manage.ownerBound());
        assertEquals(1, manage.groupsCount().orElseThrow().intValue()); assertEquals(1, manage.totalModelRows().orElseThrow().intValue());
        assertTrue(manage.listVisible()); assertFalse(manage.detailFound()); assertTrue(manage.nativeCanConfirm().isEmpty());
        assertFalse(manage.confirmAdmissible()); assertFalse(manage.confirmTooltipObserved()); assertTrue(manage.confirmTooltip().isEmpty());
        assertEquals(1, manage.rows().size()); assertEquals("xalw_manage_decision", manage.rows().get(0).decisionKey());
        assertTrue(manage.rows().get(0).canOpenDetail()); assertFalse(manage.rows().get(0).isSelected());
    }
    @Test void originalInventoryEntryQueryCanObserveKnownClosedWithoutClaimingAnOpen() throws Exception {
        var frame = frame("response-entry-query-1.body.json"); assertEquals(CurrentLivingEntry.Action.QUERY_INVENTORY_ENTRY, frame.action());
        var view = frame.source().orElseThrow().inventory().orElseThrow(); assertEquals(0L, view.expectedPayloadFullId());
        assertFalse(view.windowFound()); assertFalse(view.visible()); assertFalse(view.payloadBound()); assertFalse(view.blockedByVisibleModal());
        assertTrue(view.openAdmissible()); assertFalse(frame.effectAttempted()); assertEquals(BigInteger.ZERO, frame.claimSequence());
    }
    @Test void originalDetailEntryQueryRetainsARealClosedTargetWithoutAnAppliedDetail() throws Exception {
        var frame = frame("response-entry-query-2.body.json"); assertEquals(CurrentLivingEntry.Action.QUERY_DETAIL_ENTRY, frame.action());
        var view = frame.source().orElseThrow().detail().orElseThrow(); assertEquals(0L, view.expectedPayloadFullId());
        assertFalse(view.windowFound()); assertFalse(view.visible()); assertFalse(view.payloadBound()); assertTrue(view.openAdmissible());
        assertFalse(frame.nativeReturned()); assertFalse(frame.effectAttempted());
    }
    @Test void originalOpenInventoryDispatchIsImmutableBeforeSourceAndNotAnOpenedPoststate() throws Exception {
        var frame = frame("response-entry-dispatched.body.json"); assertEquals(CurrentLivingEntry.Action.OPEN_INVENTORY, frame.action());
        assertEquals(CurrentLivingEntryResult.Status.DISPATCHED, frame.status()); assertTrue(frame.effectAttempted());
        assertTrue(frame.nativeReturned()); assertTrue(frame.cleanupKnown()); assertFalse(frame.nativeHandled());
        assertEquals(BigInteger.valueOf(7), frame.claimSequence());
        assertEquals(frame("response-entry-query-1.body.json").source(), frame.source());
        assertFalse(frame.source().orElseThrow().inventory().orElseThrow().windowFound());
    }
    @Test void originalEntryUnknownKeepsPrivateClaimDiagnosticAndSourceNull() throws Exception {
        var frame = frame("response-entry-unknown.body.json"); assertEquals(CurrentLivingEntryResult.Status.INDETERMINATE, frame.status());
        assertFalse(frame.cleanupKnown()); assertTrue(frame.source().isEmpty()); assertTrue(frame.effectAttempted()); assertFalse(frame.nativeReturned());
        assertEquals(BigInteger.ONE, frame.providerGeneration()); assertEquals(BigInteger.TWO, frame.querySequence());
        assertEquals(BigInteger.valueOf(7), frame.claimSequence()); assertFalse(frame.unavailableReason().orElseThrow().isEmpty());
    }

    @Test void originalFactoryConfirmManage() throws Exception { requestFactory("confirm_manage", CurrentLivingEntry.Action.CONFIRM_MANAGE); }

    @Test void originalFactoryOpenDetail() throws Exception { requestFactory("open_detail", CurrentLivingEntry.Action.OPEN_DETAIL); }

    @Test void originalFactoryOpenInventory() throws Exception { requestFactory("open_inventory", CurrentLivingEntry.Action.OPEN_INVENTORY); }

    @Test void originalFactoryOpenManageDetail() throws Exception { requestFactory("open_manage_detail", CurrentLivingEntry.Action.OPEN_MANAGE_DETAIL); }

    @Test void originalFactoryOpenManageList() throws Exception { requestFactory("open_manage_list", CurrentLivingEntry.Action.OPEN_MANAGE_LIST); }

    @Test void originalFactoryQueryDetailEntry() throws Exception { requestFactory("query_detail_entry", CurrentLivingEntry.Action.QUERY_DETAIL_ENTRY); }

    @Test void originalFactoryQueryInventoryEntry() throws Exception { requestFactory("query_inventory_entry", CurrentLivingEntry.Action.QUERY_INVENTORY_ENTRY); }

    @Test void originalFactoryQueryManage() throws Exception { requestFactory("query_manage", CurrentLivingEntry.Action.QUERY_MANAGE); }
}

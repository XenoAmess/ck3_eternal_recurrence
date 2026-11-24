package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.NativeCurrentLivingInventory26785313ProducerTest.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Untouched C++ software DATA. Dispatch retains beforeSource; it is no applied/closed proof. */
class NativeCurrentLivingUi26785313ProducerTest {
    private static byte[] raw(String name) throws Exception {
        return switch (name) {
            case "original-ui-cancel_review.body.json" -> original("ui", name, 766, "58e315d4cfffb68b5a31e142025d0deff3678194584a579ab7de704bee89b063");
            case "original-ui-close_management.body.json" -> original("ui", name, 772, "d4e4f3145770b4612def8422541f3f4e74b7129f7c6c3ac42100e33f646c72d6");
            case "original-ui-confirm_review.body.json" -> original("ui", name, 768, "12a489e45d30b9707bbb4d8fbb6a02f546642c1290818318ceca2d2c3d2031e6");
            case "original-ui-equip_target.body.json" -> original("ui", name, 763, "a4dfdcaf14bd756527ae0d99db78e54551481b6af865213b2432c67efd1698c9");
            case "original-ui-feed_common.body.json" -> original("ui", name, 761, "b00c1f542a80151225d8bdf8d7f76f3ee3237055dd768a62c783f348333eef0d");
            case "original-ui-feed_famed.body.json" -> original("ui", name, 759, "edf777445cad81113d9895664cd386b6b59026c52ba4b69f8a1dda1004f82164");
            case "original-ui-feed_illustrious.body.json" -> original("ui", name, 772, "f50eefb2a0f141ee20d70a8a325f1f01604c746602cd7fd4df2aebc922f20100");
            case "original-ui-feed_masterwork.body.json" -> original("ui", name, 769, "e683484108e643b68bf955184066dd1adb52bc1edd039185cb3a08eeb97ee185");
            case "original-ui-open_tutorial.body.json" -> original("ui", name, 765, "493204a2dcd547e133b356087d17e3cf15b3f994ee7070bc904a9e022ee8542e");
            case "original-ui-query_detail.body.json" -> original("ui", name, 726, "8edc463bf2212e0d47476be29feec47ed5421569955259173d67953bb5316db3");
            case "original-ui-query_events.body.json" -> original("ui", name, 725, "b72489a159afa7100c1e796911d259a98af29a377847f338a66c42369c9ded89");
            case "original-ui-query_weapon.body.json" -> original("ui", name, 725, "581afb4ab5e921338fed0899ae5e76720eac3f4ebe17f708cf782d9e8ae0af13");
            case "original-ui-select_weapon.body.json" -> original("ui", name, 765, "2334e08e23dc0f3745fe7828dfb52e9c3db30c99fd9cf7fa707939d9691061e5");
            case "original-ui-unequip_target.body.json" -> original("ui", name, 767, "070385107b2bb5b0d5d85f55a81a04b1b9aa90f3cab92b3cdef2996a30c9ef55");
            case "response-ui-dispatched.body.json" -> original("ui", name, 3296, "55a9ef14ff9ef256a8fb5696ac37ad17a985c7479df3e0806f17bcbc4fd2ecf7");
            case "response-ui-query-0.body.json" -> original("ui", name, 1366, "1566bba463d56cc9646cecbd248ea1a8c7396a4fabd0fd1bb67326ff35d71792");
            case "response-ui-query-1.body.json" -> original("ui", name, 3290, "0688aef95f8240f5b3c2cec0b7066f35bbe0681f813687be46f82ab6683b0abb");
            case "response-ui-query-2.body.json" -> original("ui", name, 1288, "ec0af46d8cbee458c8e2ce7d55d69a1d9e5a4df634342be48c6d855f40674aa3");
            case "response-ui-unknown.body.json" -> original("ui", name, 992, "1e5a5deeb6afe15ea940a0e64c9c8389a36a095acb5e26ed0caca227e13ca329");
            default -> throw new IllegalArgumentException("Unknown original resource: " + name);
        };
    }
    private static CurrentLivingUiResult frame(String name) throws Exception {
        byte[] original = raw(name); var frame = CurrentLivingUiResult.decode(result(original));
        assertEquals(frame, CurrentLivingUiResult.decode(frame.encode()));
        responseIdentity(original, frame.encode(), frame.successful());
        return frame;
    }
    private static void requestFactory(String actionWire, CurrentLivingUi.Action action) throws Exception {
        var original = StrictJson.object(envelope(raw("original-ui-" + actionWire + ".body.json")),
                Set.of("type", "protocol_version", "request_id", "step", "actor", "target", "arguments", "deadline_unix_ms"));
        var args = StrictJson.object(original.get("arguments"), Set.of("living_ui"));
        var claim = StrictJson.object(args.get("living_ui"), Set.of("schema", "game_version", "executable_sha256",
                "adapter_id", "backend", "action", "expected_core", "provider_generation", "query_sequence"));
        assertEquals(actionWire, action.wire()); assertEquals(actionWire, claim.get("action").textValue());
        assertTrue(claim.get("provider_generation").isIntegralNumber()); assertTrue(claim.get("query_sequence").isIntegralNumber());
        BigInteger provider = claim.get("provider_generation").bigIntegerValue(), query = claim.get("query_sequence").bigIntegerValue();
        assertEquals(action.queryOnly() ? BigInteger.ZERO : MAX_U64, provider);
        assertEquals(action.queryOnly() ? BigInteger.ZERO : MAX_U64, query);
        var request = CurrentLivingUi.request(core(claim), action, provider, query);
        assertEquals(CurrentLivingUi.CAPABILITY, request.requiredCapability().orElseThrow());
        var fields = StrictJson.object(NativeWire.parse(request.additionalFields().bytes()), Set.of("arguments", "living_ui"));
        assertEquals(9, fields.get("living_ui").size()); assertTrue(fields.get("arguments").isEmpty());
        // Exercise the actual production strict8 encoder. A hand-built test envelope would conceal production regressions.
        byte[] packet = NativeGameTransport.currentLivingFixedEntryUiPacket(original.get("request_id").textValue(), request,
                original.get("deadline_unix_ms").bigIntegerValue());
        factory("ui", original, request, packet);
    }

    @Test void originalWeaponQueryPreservesActualSelectionAndFalseEquipmentData() throws Exception {
        var frame = frame("response-ui-query-0.body.json"); assertEquals(CurrentLivingUi.Action.QUERY_WEAPON, frame.action());
        var source = frame.source().orElseThrow(); var weapon = source.weapon().orElseThrow();
        assertEquals(0L, source.actorFullId()); assertEquals(0L, weapon.targetFullId()); assertTrue(weapon.weaponArtifactFullId().isEmpty());
        assertTrue(weapon.nativeSlotAvailable().orElseThrow()); assertTrue(weapon.nativeCanHold().orElseThrow());
        assertTrue(weapon.selectAdmissible()); assertFalse(weapon.equipAdmissible()); assertFalse(weapon.unequipAdmissible());
        assertFalse(weapon.targetEquipped()); assertFalse(weapon.weaponSelected()); assertFalse(frame.effectAttempted());
    }
    @Test void originalEventsQueryPreservesEmbeddedNulAndOnlyTheActualManagementCloseRow() throws Exception {
        var frame = frame("response-ui-query-1.body.json"); assertEquals(CurrentLivingUi.Action.QUERY_EVENTS, frame.action());
        var source = frame.source().orElseThrow(); var events = source.events().orElseThrow();
        assertTrue(events.censusComplete()); assertTrue(events.completeBindings()); assertEquals(1, events.namedRootCount());
        var event = events.events().get(0); assertEquals("xalw.10", event.definitionKey()); assertEquals(17, event.instanceId());
        assertEquals("A" + (char) 0 + "B", event.description()); assertEquals(10, event.options().size());
        assertEquals(10, event.authoredOptionCount()); assertEquals(0, event.recipientCharacterId());
        var binding = events.bindings().get(0); assertEquals(0L, binding.target().artifactFullId().orElseThrow().longValue());
        assertTrue(binding.targetOwned()); assertFalse(binding.materialRequired()); assertTrue(binding.material().artifactFullId().isEmpty());
        assertEquals(1, events.fixedActions().size()); var close = events.fixedActions().get(0);
        assertEquals(CurrentLivingUi.Action.CLOSE_MANAGEMENT, close.action()); assertEquals(9, close.authoredOptionIndex());
        assertTrue(close.admissible()); assertTrue(source.actionAdmissible(CurrentLivingUi.Action.CLOSE_MANAGEMENT));
    }
    @Test void originalDetailQueryPreservesObservedEmptyRichtextNulAndControls() throws Exception {
        var frame = frame("response-ui-query-2.body.json"); assertEquals(CurrentLivingUi.Action.QUERY_DETAIL, frame.action());
        var detail = frame.source().orElseThrow().detail().orElseThrow(); assertEquals(0L, detail.targetFullId());
        assertTrue(detail.targetBound()); assertEquals("A" + (char) 0 + "B\n\t", detail.modifierEffectsText().orElseThrow());
        assertEquals("#P XalwEffects#!", detail.customEffectsText().orElseThrow()); assertEquals("", detail.descriptionText().orElseThrow());
    }
    @Test void originalCloseDispatchRetainsBeforeEventRatherThanClaimingInstanceAbsence() throws Exception {
        var frame = frame("response-ui-dispatched.body.json"); assertEquals(CurrentLivingUi.Action.CLOSE_MANAGEMENT, frame.action());
        assertEquals(CurrentLivingUiResult.Status.DISPATCHED, frame.status()); assertTrue(frame.effectAttempted());
        assertTrue(frame.nativeReturned()); assertTrue(frame.cleanupKnown()); assertFalse(frame.nativeHandled());
        assertEquals(BigInteger.valueOf(7), frame.claimSequence());
        assertEquals(frame("response-ui-query-1.body.json").source(), frame.source());
        assertEquals(17, frame.source().orElseThrow().events().orElseThrow().events().get(0).instanceId());
    }
    @Test void originalUiUnknownPreservesSpentIdentityAndEnteredButNotReturnedEffect() throws Exception {
        var frame = frame("response-ui-unknown.body.json"); assertEquals(CurrentLivingUiResult.Status.INDETERMINATE, frame.status());
        assertFalse(frame.cleanupKnown()); assertTrue(frame.source().isEmpty()); assertTrue(frame.effectAttempted()); assertFalse(frame.nativeReturned());
        assertEquals(BigInteger.ONE, frame.providerGeneration()); assertEquals(BigInteger.TWO, frame.querySequence());
        assertEquals(BigInteger.valueOf(7), frame.claimSequence()); assertFalse(frame.unavailableReason().orElseThrow().isEmpty());
    }

    @Test void originalFactoryCancelReview() throws Exception { requestFactory("cancel_review", CurrentLivingUi.Action.CANCEL_REVIEW); }

    @Test void originalFactoryCloseManagement() throws Exception { requestFactory("close_management", CurrentLivingUi.Action.CLOSE_MANAGEMENT); }

    @Test void originalFactoryConfirmReview() throws Exception { requestFactory("confirm_review", CurrentLivingUi.Action.CONFIRM_REVIEW); }

    @Test void originalFactoryEquipTarget() throws Exception { requestFactory("equip_target", CurrentLivingUi.Action.EQUIP_TARGET); }

    @Test void originalFactoryFeedCommon() throws Exception { requestFactory("feed_common", CurrentLivingUi.Action.FEED_COMMON); }

    @Test void originalFactoryFeedFamed() throws Exception { requestFactory("feed_famed", CurrentLivingUi.Action.FEED_FAMED); }

    @Test void originalFactoryFeedIllustrious() throws Exception { requestFactory("feed_illustrious", CurrentLivingUi.Action.FEED_ILLUSTRIOUS); }

    @Test void originalFactoryFeedMasterwork() throws Exception { requestFactory("feed_masterwork", CurrentLivingUi.Action.FEED_MASTERWORK); }

    @Test void originalFactoryOpenTutorial() throws Exception { requestFactory("open_tutorial", CurrentLivingUi.Action.OPEN_TUTORIAL); }

    @Test void originalFactoryQueryDetail() throws Exception { requestFactory("query_detail", CurrentLivingUi.Action.QUERY_DETAIL); }

    @Test void originalFactoryQueryEvents() throws Exception { requestFactory("query_events", CurrentLivingUi.Action.QUERY_EVENTS); }

    @Test void originalFactoryQueryWeapon() throws Exception { requestFactory("query_weapon", CurrentLivingUi.Action.QUERY_WEAPON); }

    @Test void originalFactorySelectWeapon() throws Exception { requestFactory("select_weapon", CurrentLivingUi.Action.SELECT_WEAPON); }

    @Test void originalFactoryUnequipTarget() throws Exception { requestFactory("unequip_target", CurrentLivingUi.Action.UNEQUIP_TARGET); }
}

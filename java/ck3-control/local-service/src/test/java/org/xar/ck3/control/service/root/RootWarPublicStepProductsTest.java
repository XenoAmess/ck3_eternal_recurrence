package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionTitleSelectorReads;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original parsers feed the actual shared DTO and serde consumers; no Managed Root is fabricated. */
final class RootWarPublicStepProductsTest {
    private static final ArmyCalls.Revision REV=new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(7)));
    private static OperationKey step(String value){return new OperationKey(value);}
    @Test void titleSelectorsKeepUnsignedTitleAndOrderedClaimsDomainsAndUseTheirSingleSerde(){
        for(String original:List.of("query-title-own-laws-v1-0","query-title-own-laws-v1-4294967294",
                "query-title-holder-v1-0","query-title-holder-v1-2147483647",InteractionTitleSelectorReads.operation(new InteractionTitleSelectorReads.ClaimsSelector(List.of(
                        new org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Int32Id(Integer.MAX_VALUE),
                        new org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Int32Id(0),
                        new org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Int32Id(4)))).value())){
            var value=RootWarPublicStepProducts.titleSelector(step(original)).orElseThrow();
            assertEquals(step(original),InteractionTitleSelectorReads.operation(value));
            assertEquals(value,InteractionTitleSelectorReads.decodeSelector(InteractionTitleSelectorReads.encodeSelector(value)));
            assertEquals(RootWarPublicStepProducts.ReadKind.TITLE,RootWarPublicStepProducts.readKind(step(original)).orElseThrow());
        }
        for(String invalid:List.of("query-title-own-laws-v1-4294967295","query-title-own-laws-v1--1",
                "query-title-own-laws-v1-01","query-title-holder-v1-2147483648","query-title-holder-v1-01",
                "query-player-claims-v1-1:1","query-player-claims-v1-1:","query-player-claims-v1-1:01",
                "query-player-claims-v1-2147483648"))
            assertTrue(RootWarPublicStepProducts.titleSelector(step(invalid)).isEmpty(),invalid);
        assertThrows(IllegalArgumentException.class,()->step("query-player-claims-v1-2,1"));
        assertThrows(IllegalArgumentException.class,()->step("query-player-claims-v1-١"));
    }
    @Test void warReadSelectionReachesTheSolePublicCodecWithoutInventedAliases(){
        for(String original:List.of("query-war-occupation-targets-v1-0","query-war-occupation-targets-v1-2147483647",
                "query-war-termination-options-9","query-war-termination-terms-v1-9","query-outbound-war-white-peace-status-v1-9")){
            ArmyCalls.War call=RootWarPublicStepProducts.warCall(step(original),REV).orElseThrow();
            assertEquals(call,ArmyCallCodec.decode(call.method(),ArmyCallCodec.encode(call)));
            assertEquals(RootWarPublicStepProducts.ReadKind.WAR,RootWarPublicStepProducts.readKind(step(original)).orElseThrow());
            String json=new String(ArmyCallCodec.encode(call).bytes(),StandardCharsets.UTF_8);
            for(String invalid:List.of(json.replace("\"expected_revision\":\"7\"","\"expected_revision\":true"),
                    json.replace("\"expected_revision\":\"7\"","\"expected_revision\":7.0")))
                if(!invalid.equals(json))assertThrows(IllegalArgumentException.class,()->ArmyCallCodec.decode(call.method(),new RawJson(invalid.getBytes(StandardCharsets.UTF_8))));
        }
        for(String invalid:List.of("query-war-termination-options-0","query-war-termination-options-01",
                "query-war-termination-terms-9","query-outbound-war-white-peace-status-9","query-war-occupation-targets-v1-2147483648"))
            assertTrue(RootWarPublicStepProducts.warCall(step(invalid),REV).isEmpty(),invalid);
    }
    @Test void retreatTokensRetainSignedCombatPublicZeroAndExactRevisionThroughActualOrderCodec(){
        String token="_Z-0123456789012345678901234567890";
        String original="order-active-combat-retreat-v1-0-revision-7-combat--2147483648-side-1-scope-owner_subset-to-2700-token-"+token;
        ArmyCalls.RetreatOrder call=RootWarPublicStepProducts.retreatOrder(step(original),REV).orElseThrow();
        assertEquals(0,call.selected().value());assertEquals(Integer.MIN_VALUE,call.combat().value());
        assertEquals(call,ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1,ArmyCallCodec.encode(call)));
        assertEquals(original,ArmyRetreatPreview.orderStep(call.selected(),BigInteger.valueOf(7),call.combat(),1,call.scope(),call.target(),token));
        assertTrue(RootWarPublicStepProducts.retreatOrder(step(original.replace("revision-7","revision-8")),REV).isEmpty());
        for(String invalid:List.of(original.replace("combat--2147483648","combat--1"),original.replace(token,"a".repeat(31)),
                original.replace("scope-owner_subset","scope-side_wide"),original.replace("-to-2700","-to-0"),original.replace(token,"a".repeat(129))))
            assertTrue(RootWarPublicStepProducts.retreatOrder(step(invalid),REV).isEmpty(),invalid);
        String extendedStep=original+"-extra";
        var extended=RootWarPublicStepProducts.retreatOrder(step(extendedStep),REV).orElseThrow();
        assertEquals(token+"-extra",extended.token());
        assertEquals(extended,ArmyCallCodec.decode(PublicMethod.ORDER_ACTIVE_COMBAT_RETREAT_V1,ArmyCallCodec.encode(extended)));
        assertEquals(extendedStep,ArmyRetreatPreview.orderStep(extended.selected(),BigInteger.valueOf(7),extended.combat(),1,extended.scope(),extended.target(),extended.token()));
        ArmyCalls.RetreatPreview preview=RootWarPublicStepProducts.retreatPreview(step("preview-active-combat-retreat-v1-0-to-2700"),REV).orElseThrow();
        assertEquals(preview,ArmyCallCodec.decode(preview.method(),ArmyCallCodec.encode(preview)));
    }
    @Test void parsedOpaqueTokensStillRequireTheExactDurablePreviewAfterSerde(){
        String token="_Z-0123456789012345678901234567890";
        String prefix="order-active-combat-retreat-v1-0-revision-7-combat--2147483648-side-1-scope-owner_subset-to-2700-token-";
        var source=new ActiveRetreatProposal.SourceFrame("native:7",BigInteger.valueOf(7),BigInteger.valueOf(7),BigInteger.valueOf(100),"software-token-episode",BigInteger.ONE);
        // Pure DATA: the actual reducer and order validator grant no current Native or submission authority.
        var node=StrictJson.object().put("contract_stage",ArmyRetreatTokens.STAGE).put("status","available").put("action_ready",true)
                .put("selected_public_cunit_id",0).put("selected_native_carmy_id",1).put("selected_owner_character_id",9)
                .put("combat_id",Integer.MIN_VALUE).put("combat_province_id",1).put("side_index",1).put("side_scope","owner_subset").put("target_province_id",2700);
        node.set("source_binding",OpportunityJson.toNode(source.json()));
        node.putArray("affected_public_cunit_ids_in_stored_order").add(0);node.putArray("unaffected_same_side_public_cunit_ids_in_stored_order").add(2);
        var control=node.putObject("battle_control_snapshot");
        for(String field:List.of("combat_id","combat_province_id","selected_public_cunit_id","selected_native_carmy_id","selected_owner_character_id",
                "side_index","side_scope","affected_public_cunit_ids_in_stored_order","unaffected_same_side_public_cunit_ids_in_stored_order"))
            control.set(field,node.get(field).deepCopy());
        var target=node.putObject("target_preview").put("status","available");target.putArray("route_province_ids").add(2700);
        for(String retained:List.of(token,token+"-extra")){
            target.put("candidate_token",retained).put("order_step",prefix+retained);
            var preview=DriverJson.object(StrictJson.canonical(node),DriverJson.MAX_NATIVE_BYTES);
            var started=ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartPreview(source));
            var stored=ActiveRetreatState.reduce(started,new ActiveRetreatState.FinishPreview(source,preview));
            var restored=ActiveRetreatState.decode(DriverJson.object(DriverJson.encode(ActiveRetreatState.encode(stored)),DriverJson.MAX_NATIVE_BYTES));
            assertEquals(stored,restored);
            var matching=RootWarPublicStepProducts.retreatOrder(step(prefix+retained),REV).orElseThrow();
            assertEquals(retained,ArmyRetreatOrders.order(restored,matching).arguments().candidateToken());
            var changed=RootWarPublicStepProducts.retreatOrder(step(prefix+(retained.equals(token)?token+"-extra":token)),REV).orElseThrow();
            var failure=assertThrows(IllegalArgumentException.class,()->ArmyRetreatOrders.order(restored,changed));
            assertEquals("retreat order differs from the sole original preview binding",failure.getMessage());
        }
    }
    @Test void completeOrderedRouteScopeUsesTheActualSelectionLiteralAndCannotCaptureAdvances(){
        var preview=RootWarPublicStepProducts.route(step("preview-move-army-0-to-2")).orElseThrow();
        assertEquals("preview-move-army-0-to-2",preview.step());
        var horizon=RootWarPublicStepProducts.route(step("query-route-contact-horizon-v1-0-to-2-h-2-1-3")).orElseThrow();
        assertEquals(List.of(1,3),horizon.hostiles());assertEquals("query-route-contact-horizon-v1-0-to-2-h-2-1-3",horizon.step());
        for(String invalid:List.of("query-route-contact-horizon-v1-0-to-2-h-1-1-3","query-route-contact-horizon-v1-0-to-2-h-2-3-1",
                "query-route-contact-horizon-v1-0-to-2-h-2-1-1","query-route-contact-horizon-v1-0-to-2-h-1-0",
                "query-route-contact-horizon-v1-0-to-0-h-1-1","advance-route-contact-horizon-v1-0-to-2-h-1-1"))
            assertTrue(RootWarPublicStepProducts.route(step(invalid)).isEmpty(),invalid);
    }
    @Test void explicitDisabledPreviewIsMatchedWithoutAReadyOrInventedPublicMcpName(){
        assertTrue(RootWarPublicStepProducts.disabledExit(step("query-war-termination-exit-terms-v2-9")));
        assertFalse(RootWarPublicStepProducts.disabledExit(step("query-war-termination-exit-terms-v2-0")));
        assertFalse(RootWarPublicStepProducts.disabledExit(step("ck3_query_war_termination_exit_terms")));
        assertEquals(RootWarPublicStepProducts.ReadKind.DISABLED_EXIT_PREVIEW,
                RootWarPublicStepProducts.readKind(step("query-war-termination-exit-terms-v2-9")).orElseThrow());
    }
    @Test void ordinaryOtherOwnersAreExcludedAndH2743RemainsAReadWithItsOriginalBeforeFrameContract(){
        for(String unrelated:List.of("raise-troops-default","disband-army-0","halt-army-0","split-army-half-0","merge-armies-0-with-1",
                "assign-army-commander-v1-army-0-to-character-1","hire-mercenary-v1","hire-holy-order-v1",
                "accept-pending-character-interaction","save-checkpoint","query-battle-transition-v1-9","advance-route-window"))
            assertTrue(RootWarPublicStepProducts.readKind(step(unrelated)).isEmpty(),unrelated);
        assertEquals(RootWarPublicStepProducts.ReadKind.SPECIAL,
                RootWarPublicStepProducts.readKind(step(ArmySpecialWarReads.H2743)).orElseThrow());
        var failure = assertThrows(PublicServiceFailure.class, () -> new PublicPlanningCodec.ExecuteRequest(step(ArmySpecialWarReads.H2743),
                new PublicPlanningCodec.RevisionValue(BigInteger.valueOf(7)), new PublicPlanningCodec.FrameMissing()));
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE, failure.kind());
        assertEquals("H2743 read-only query requires an explicit before-frame claim", failure.getMessage());
        var directed=RootWarPublicStepProducts.closedCall(step("query-raiktor-actual-truce-expiry-v1-9"),REV).orElseThrow();
        assertInstanceOf(ArmyCalls.Truce.class,directed);assertEquals(directed,ArmyCallCodec.decode(directed.method(),ArmyCallCodec.encode(directed)));
    }
    @Test void sevenWarActionsUseTheExistingExactTypedCallProducerAndNeverCaptureOtherArmyOwners(){
        for(String original:List.of("move-army-0-to-2","start-assault-2","stop-assault-2","declare-war-1-0--1",
                "enforce-demands-0","offer-white-peace-9","surrender-war-9")){
            ArmyCalls.Call call=RootWarPublicStepProducts.ordinaryCall(step(original),BigInteger.valueOf(7)).orElseThrow();
            assertEquals(call,ArmyCallCodec.decode(call.method(),ArmyCallCodec.encode(call)));
            assertEquals(BigInteger.valueOf(7),call.revision().requireCurrent(BigInteger.valueOf(7)));
            assertTrue(RootWarPublicStepProducts.readKind(step(original)).isEmpty(),"a typed action cannot become a READ");
        }
        for(String unrelated:List.of("raise-troops-default","disband-army-0","halt-army-0","split-army-half-0",
                "merge-armies-0-with-1","close-war-declared-overview-v1","close-war-results-window-v1",
                "hire-mercenary-v1","hire-holy-order-v1","move-army-0-to-0","move-army-00-to-2",
                "start-assault-0","stop-assault-0","declare-war-01-0--1","surrender-war-0","offer-white-peace-0"))
            assertTrue(RootWarPublicStepProducts.ordinaryCall(step(unrelated),BigInteger.valueOf(7)).isEmpty(),unrelated);
    }
    @Test void mercenaryReadUsesTheOriginalSixFieldM5ProducerBeforeAnyReadAndRetainsExact64BitSource(){
        String original="{\"played_character\":{\"character_id\":9},\"native_revision\":18446744073709551615,\"date_raw\":0,"
                +"\"snapshot_id\":\"native:18446744073709551615\",\"revision\":18446744073709551615,\"episode_run_id\":\"actual-test-episode\"}";
        var snapshot=DriverJson.object(original.getBytes(StandardCharsets.UTF_8),65536);
        var source=RootWarPublicStepProducts.mercenarySourceFrame(snapshot);
        assertEquals(java.util.Set.of("played_character_id","native_revision","date_raw","snapshot_id","revision","episode_run_id"),source.members().keySet());
        assertEquals(new BigInteger("18446744073709551615"),OpportunityJson.integer(source.get("native_revision"),"native_revision"));
        assertEquals(source,OpportunityJson.parse(DriverJson.encode(source)));
        for(String invalid:List.of(original.replace("\"native_revision\":18446744073709551615","\"native_revision\":true"),
                original.replace("\"revision\":18446744073709551615","\"revision\":0"),original.replace("\"snapshot_id\":\"native:18446744073709551615\"","\"snapshot_id\":null")))
            assertThrows(IllegalArgumentException.class,()->RootWarPublicStepProducts.mercenarySourceFrame(DriverJson.object(invalid.getBytes(StandardCharsets.UTF_8),65536)));
        assertEquals(RootWarPublicStepProducts.ReadKind.MERCENARY,RootWarPublicStepProducts.readKind(step("query-player-mercenary-context-v1")).orElseThrow());
    }
}

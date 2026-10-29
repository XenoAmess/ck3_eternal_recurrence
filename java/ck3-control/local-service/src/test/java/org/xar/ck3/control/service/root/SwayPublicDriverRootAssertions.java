package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.Optional;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.*;

/** The complete Root fixture supplies actual Context/Inputs/catalog/physical source; this helper cannot mint any of them. */
public final class SwayPublicDriverRootAssertions {
    private SwayPublicDriverRootAssertions() { }
    private record Snapshot(GameGeneration game,JsonNode wholeJournal,Optional<ActionReceipt> action) { }
    /** Positive fixture must arrange a legal empty slot on the original paused frame and an unused caller action ID. */
    public static RawJson targetStartRetryActualAndAssert(RootPublicHandlerProductsFactory.Context actual,PublicMcpDirectory sameActualDirectory,SwayDriverCodec.TargetRequest target,String callerActionId)throws Exception {
        var initial=snapshot(actual,callerActionId);assertTrue(initial.action().isEmpty());
        var quote=business(invoke(sameActualDirectory,"ck3_query_active_scheme_sway_target_private_v1",SwayDriverCodec.encode(target)));
        var afterQuery=snapshot(actual,callerActionId);assertEquals(initial.game(),afterQuery.game());assertEquals(initial.wholeJournal(),afterQuery.wholeJournal());
        var args=StrictJson.object();args.set("readback",StrictJson.parse(quote.bytes(),SwayNativeWire.MAX));args.put("action_id",callerActionId);var request=SwayDriverCodec.decodeStart(new RawJson(StrictJson.canonical(args,SwayNativeWire.MAX)));
        var first=business(invoke(sameActualDirectory,"ck3_start_active_scheme_sway_private_v1",SwayDriverCodec.encode(request)));var committed=snapshot(actual,callerActionId);var original=committed.action().orElseThrow();
        actual.withCurrent(root->{var catalog=actual.installed(root);var sway=catalog.remainingDomains().sway();var binding=sway.retainedArchived(original).orElseThrow();assertSame(catalog.context().bindings().actualArchivedVerifier(original.command().operation()).orElseThrow(),binding);assertTrue(sway.historyProducerSources().contains(binding.definitionSource()));return null;});
        assertEquals(callerActionId,original.command().actionId());assertEquals(SwayNativeWire.START+target.targetCharacterId(),original.command().operation().value());assertFalse(original.eligibleAdvance());
        assertEquals(SwayNativeBindings.PUBLIC_START_ARGUMENTS,StrictJson.text(StrictJson.parse(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(original.command().arguments())).get("schema")));
        var retry=business(invoke(sameActualDirectory,"ck3_start_active_scheme_sway_private_v1",SwayDriverCodec.encode(request)));var after=snapshot(actual,callerActionId);var same=after.action().orElseThrow();
        assertEquals(initial.game(),after.game());assertEquals(original.bodySha256(),same.bodySha256());assertEquals(original.command(),same.command());assertEquals(ActionTransitions.attempt(original.state()),ActionTransitions.attempt(same.state()),"same caller action ID may only retain/reconcile its original durable attempt");
        assertEquals(callerActionId,StrictJson.text(StrictJson.parse(first.bytes()).get("action_id")));assertEquals(callerActionId,StrictJson.text(StrictJson.parse(retry.bytes()).get("action_id")));return retry;
    }
    /** Actual restored source is mandatory. An observed restored instance cannot rewrite the old canonical UNKNOWN. */
    public static RawJson coldActualAndAssert(RootPublicHandlerProductsFactory.Context actual,PublicMcpDirectory sameActualDirectory,SwayDriverCodec.StartRequest retained)throws Exception {
        var before=snapshot(actual,retained.actionId());assertTrue(before.action().isPresent());var old=before.action().orElseThrow();assertNotEquals(before.game(),old.command().before().game());
        var result=business(invoke(sameActualDirectory,"ck3_start_active_scheme_sway_private_v1",SwayDriverCodec.encode(retained)));var after=snapshot(actual,retained.actionId());
        assertEquals(before.game(),after.game());assertEquals(before.wholeJournal(),after.wholeJournal());assertEquals(old,after.action().orElseThrow());assertFalse(StrictJson.parse(result.bytes()).get("postcondition_verified").booleanValue());return result;
    }
    private static Snapshot snapshot(RootPublicHandlerProductsFactory.Context actual,String actionId)throws Exception {
        return actual.withCurrent(root->{var context=actual.installed(root).context();return context.withSession(same->new Snapshot(root.identity().game(),same.head().state().toJson().get(ContinuityActionJournal.STATE_FIELD),ContinuityActionJournal.lookup(same.head().state(),actionId,context.archive().withSession(same))));});
    }
    private static PublicMcpDirectory.CallResult invoke(PublicMcpDirectory actual,String name,RawJson args)throws Exception {return actual.invoke(new PublicMcpDirectory.ToolCall(name,new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(args)),Optional.empty(),new McpCancellation()));}
    private static RawJson business(PublicMcpDirectory.CallResult result){var row=StrictJson.parse(result.bytes(),SwayNativeWire.MAX);assertFalse(row.get("isError").booleanValue());assertTrue(row.get("structuredContent").isObject());return new RawJson(StrictJson.canonical(row.get("structuredContent"),SwayNativeWire.MAX));}
}

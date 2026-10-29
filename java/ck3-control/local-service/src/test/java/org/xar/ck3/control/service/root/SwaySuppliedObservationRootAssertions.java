package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.planning.sway.SwayObservationReads;
import org.xar.ck3.control.application.planning.sway.SwayPublicCodec;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;

/** Whole Root fixture supplies the genuine Context/current installed catalog and frozen registry; no alternate Core issuer. */
public final class SwaySuppliedObservationRootAssertions {
    private SwaySuppliedObservationRootAssertions() { }
    private record Snapshot(GameGeneration game,JsonNode actionJournal) { }
    public static RawJson invokeActualAndAssert(RootPublicHandlerProductsFactory.Context actual,PublicBindings sameFrozenRegistry,SwayPublicCodec.DirectRequest request)throws Exception {
        var before=snapshot(actual);var method=request.kind()==SwayObservationReads.Kind.COMPLETION?PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_COMPLETION_PRIVATE_V1:PublicMethod.QUERY_ACTIVE_SCHEME_SWAY_OUTCOME_OPINION_PRIVATE_V1;
        assertTrue(sameFrozenRegistry.frozen());var route=sameFrozenRegistry.lookup(method).orElseThrow();var result=route.invoke(PublicBindings.present(SwayPublicCodec.encodeDirectRequest(request)));var row=StrictJson.parse(result.bytes(),1<<20);
        assertEquals(request.kind()==SwayObservationReads.Kind.COMPLETION?"xar.ck3.sway_completion.v1":"xar.ck3.sway-outcome-opinion-v1",StrictJson.text(row.get("schema")));
        assertEquals(request.targetCharacterId(),row.get("target_character_id").longValue());assertFalse(row.has("action_id"));
        var after=snapshot(actual);assertEquals(before.game(),after.game());assertEquals(before.actionJournal(),after.actionJournal(),"pure actual observation must preserve every canonical action including UNKNOWN");return result;
    }
    private static Snapshot snapshot(RootPublicHandlerProductsFactory.Context actual)throws Exception {
        return actual.withCurrent(root->{var current=actual.installed(root).context();return current.withSession(same->new Snapshot(root.identity().game(),same.head().state().toJson().get(ContinuityActionJournal.STATE_FIELD)));});
    }
}

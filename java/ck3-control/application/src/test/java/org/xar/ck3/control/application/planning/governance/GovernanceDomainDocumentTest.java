package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceDomainDocument.*;

/** Explicit synthetic state vectors. No private fresh-entry, native result or writer capability is constructed. */
final class GovernanceDomainDocumentTest {
    private static ObjectNode pendingCouncil() {
        var row=StrictJson.object().put("stage","submission_unresolved").put("episode_run_id","original-episode").put("action_request_id","step-1-original").put("candidate_character_id",16777232)
                .put("pre_native_revision",new BigInteger("18446744073709551615")).put("pre_date_raw",53169072);row.putObject("source_query");row.putObject("source_decision");row.set("request",StrictJson.object().put("request_id","step-1-original").put("position_key","councillor_steward").put("candidate_character_id",16777232)
                .put("expected_snapshot_id","native:18446744073709551615").put("expected_public_revision",new BigInteger("18446744073709551615")).put("expected_native_revision",new BigInteger("18446744073709551615")).put("expected_date_raw",53169072).put("expected_owner_character_id",16777217).put("expected_has_incumbent",false).put("expected_incumbent_character_id",-1));row.putNull("action_ack");return row;
    }
    private static ObjectNode pendingCrown() {
        var row=StrictJson.object().put("stage","receipt_pending").put("episode_run_id","original-episode").put("action_id","step-2-original").put("actor_character_id",4278190081L).put("law_key","crown_authority_1").put("pre_native_revision",7).put("pre_date_raw",53169072);
        row.putObject("readback");row.putObject("choice");row.putObject("budgets");row.set("source_context",StrictJson.object().put("bridge_pid",123).put("episode_run_id","original-episode"));row.putObject("ack");return row;
    }
    @Test void onlyExplicitInitialBodiesRoundTripAsClearAndMissingOrNullBodyIsRejected() {
        for(Domain domain:Domain.values()) {var state=initial(domain);assertEquals(state,decode(domain,encode(state)));assertTrue(state.pending().isEmpty());}
        assertThrows(IllegalArgumentException.class,()->decode(Domain.COUNCIL,"{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class,()->decode(Domain.CROWN,"null".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var row=StrictJson.parse(encode(initial(Domain.CROWN)));((ObjectNode)row).remove("pending");assertThrows(IllegalArgumentException.class,()->decode(Domain.CROWN,StrictJson.canonical(row)));
    }
    @Test void originalPendingRoundTripRetainsUnsignedRevisionAndNeverPromotesUnknownToResult() {
        var pending=raw(pendingCouncil());var state=pending(initial(Domain.COUNCIL),pending);var restored=decode(Domain.COUNCIL,encode(state));assertEquals(state,restored);
        assertEquals("18446744073709551615",object(restored.pending().orElseThrow().original()).get("pre_native_revision").asText());assertTrue(restored.latest().isEmpty());
        var wrong=pendingCouncil();wrong.put("candidate_character_id",true);assertThrows(IllegalArgumentException.class,()->decodePending(Domain.COUNCIL,raw(wrong)));
        var floating=pendingCouncil();floating.put("pre_native_revision",7.0);assertThrows(IllegalArgumentException.class,()->decodePending(Domain.COUNCIL,raw(floating)));
        var unknown=pendingCouncil().put("stage","unknown-retry");assertThrows(IllegalArgumentException.class,()->decodePending(Domain.COUNCIL,raw(unknown)));
    }
    @Test void crownPendingAndResultPreserveTheExistingM7RetryOriginalWithoutReinterpretingIt() {
        var retry=raw(StrictJson.object().put("observed_date_raw",53169072).put("retry_date_raw",53177832).put("law_key","crown_authority_2"));
        var before=new Document(Domain.CROWN,Optional.empty(),Optional.empty(),Optional.of(retry));var pending=pending(before,raw(pendingCrown()));
        assertEquals(pending,decode(Domain.CROWN,encode(pending)));var resolved=raw(StrictJson.object().put("status","cold_current_law_observed").put("material_result",false).putNull("native_receipt"));
        var after=result(pending,Optional.of(resolved));assertEquals(Optional.of(retry),after.retry());assertTrue(after.pending().isEmpty());assertFalse(object(after.latest().orElseThrow()).get("material_result").booleanValue());
        var wrong=pendingCrown();wrong.remove("source_context");assertThrows(IllegalArgumentException.class,()->decodePending(Domain.CROWN,raw(wrong)));
        var changed=pendingCrown();changed.put("actor_character_id",true);assertThrows(IllegalArgumentException.class,()->decodePending(Domain.CROWN,raw(changed)));
    }
    private static ObjectNode root(int current) {
        var row=StrictJson.object().put("snapshot_revision",9).put("date_raw",53169096);var seat=row.putObject("council").putArray("positions").addObject().put("position_key","councillor_steward").put("incumbent_character_id",16777232).put("task_key","task_collect_taxes").put("task_type","finite").put("frozen",false);seat.putNull("target");
        var progress=seat.putObject("progress").put("kind","finite");progress.set("current",StrictJson.object().put("raw",current).put("scale",1000));progress.set("maximum",StrictJson.object().put("raw",10000).put("scale",1000));return row;
    }
    @Test void followingJobProgressUsesOriginalFixedPointValuesAndNeverClaimsYieldOrEta() {
        var before=StrictJson.object().put("post_date_raw",53169072);before.set("independent_position",seat(root(2000),"councillor_steward").orElseThrow());
        var observed=jobProgress(root(3500),"original-episode","councillor_steward",Optional.of(raw(before)));
        assertEquals(6500,observed.get("remaining_progress").get("raw").intValue());assertEquals(1500,observed.get("following_comparison").get("progress_change").get("raw").intValue());assertEquals(24,observed.get("following_comparison").get("elapsed_game_hours").intValue());
        assertEquals("not_observed",observed.get("effect_attribution").textValue());assertFalse(observed.has("eta"));assertFalse(observed.has("yield"));
        var wrong=root(3500);((ObjectNode)wrong.get("council").get("positions").get(0).get("progress").get("maximum")).put("scale",1);assertThrows(IllegalArgumentException.class,()->jobProgress(wrong,"original-episode","councillor_steward",Optional.empty()));
    }
    @Test void typedPendingMetadataCannotDisagreeWithTheRetainedOriginalRecord() {
        var row=pendingCouncil();var mismatched=new Pending(Domain.COUNCIL,Stage.RECEIPT_PENDING,"another-episode","another-id",raw(row));
        assertThrows(IllegalArgumentException.class,()->new Document(Domain.COUNCIL,Optional.of(mismatched),Optional.empty(),Optional.empty()));
    }
}

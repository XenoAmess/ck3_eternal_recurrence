package org.xar.ck3.control.service.mcp;

import java.math.BigInteger;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Regression for the actual original provenance _positive(maximum=0xFFFFFFFF) contract;
 * the old Root decoder wrongly narrowed its candidate to signed int31. */
final class ActivityPublicScalarBoundsTest {
    private static PublicMcpDirectory.Arguments arguments(com.fasterxml.jackson.databind.JsonNode value) {
        return new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,Optional.of(new RawJson(StrictJson.canonical(value))));
    }
    @Test void provenanceKeepsOriginalUint32RevisionAndCandidateWhileOtherSubjectIdsStayInt31() {
        var row=StrictJson.object().put("expected_revision","4294967295").put("authored_rule_key","activity_invite_rule_vassals").put("candidate_character_id",new BigInteger("4294967295"));
        var request=RootMcpActivityReads.decode(Query.GUEST_RULE_PROVENANCE,arguments(row));
        assertEquals(new BigInteger("4294967295"),request.expectedRevision());
        assertEquals(new OpportunityJson.IntegerValue(new BigInteger("4294967295")),request.arguments().get("candidate_character_id"));
        assertTrue(StrictJson.parse(RootMcpActivityReads.encodeRequest(request).bytes()).get("candidate_character_id").isIntegralNumber());
        var highRevision=row.deepCopy().put("expected_revision","4294967296");
        assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.decode(Query.GUEST_RULE_PROVENANCE,arguments(highRevision))).kind());
        var highCandidate=row.deepCopy().put("candidate_character_id",new BigInteger("4294967296"));
        assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.decode(Query.GUEST_RULE_PROVENANCE,arguments(highCandidate)));
        var ordered=row.deepCopy().put("authored_rule_key","invalid_rule").put("expected_revision","0");
        assertEquals("authored_rule_key must be a bounded feast invitation rule",assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.decode(Query.GUEST_RULE_PROVENANCE,arguments(ordered))).getMessage());
        var opinion=StrictJson.object().put("expected_revision","18446744073709551615").put("guest_character_id",Integer.MAX_VALUE);
        assertEquals(new BigInteger("18446744073709551615"),RootMcpActivityReads.decode(Query.GUEST_OPINION,arguments(opinion)).expectedRevision());
        opinion.put("guest_character_id",new BigInteger("2147483648"));
        assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.decode(Query.GUEST_OPINION,arguments(opinion)));
    }
}

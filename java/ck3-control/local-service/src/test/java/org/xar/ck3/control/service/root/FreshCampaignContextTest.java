package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Typed DATA roundtrip only; no Game or private adoption authority is manufactured. */
final class FreshCampaignContextTest {
    private static ObservationIdentity identity() {
        var game=new GameGeneration(171676,new PythonOnlyUInt64(new BigInteger("134376899432680684")));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(31254),
                new BigInteger("18446744073709551615"),BigInteger.valueOf(53144328)),
                "fresh-context-observation",new BigInteger("18446744073709551615"),"observed-campaign");
        return new ObservationIdentity("xenoamess-full-tower-eb9d2c1186",game,frame,1);
    }
    @Test void actualFiletimeAndFullIntegerTokensRoundtripExactly()throws Exception {
        var original=identity();var row=FreshCampaignContext.encodeObservation(original);
        assertEquals("134376899432680684",row.path("game").path("creation_filetime").textValue());
        var bytes=StrictJson.canonical(row,ContinuityJson.DOMAIN_MAX_BYTES);
        var parsed=StrictJson.parse(bytes,ContinuityJson.DOMAIN_MAX_BYTES);
        assertTrue(parsed.path("frame").path("revision").isIntegralNumber());
        assertEquals(original.frame().revision(),parsed.path("frame").path("revision").bigIntegerValue());
        assertEquals(original,FreshCampaignContext.decodeObservation(parsed));
    }
    @Test void filetimeWrongJsonTypesAndNoncanonicalStringsStayRejected() {
        for(String invalid:new String[]{"134376899432680684","1.0","true","null","\"0134376899432680684\"","\"18446744073709551616\""}) {
            var row=FreshCampaignContext.encodeObservation(identity());
            ((com.fasterxml.jackson.databind.node.ObjectNode)row.get("game")).set("creation_filetime",StrictJson.parse(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class,()->FreshCampaignContext.decodeObservation(row));
        }
    }
    @Test void originalMapperFailureIsReproducedAndGlobalLedgerRangeStaysIntact() {
        var old=ControlBuild.strictMapper().valueToTree(identity());
        assertThrows(IllegalArgumentException.class,()->ContinuityJson.canonical(old));
        var unsafe=StrictJson.object().put("value",new BigInteger("9007199254740992"));
        assertThrows(IllegalArgumentException.class,()->ContinuityJson.canonical(unsafe));
    }
}

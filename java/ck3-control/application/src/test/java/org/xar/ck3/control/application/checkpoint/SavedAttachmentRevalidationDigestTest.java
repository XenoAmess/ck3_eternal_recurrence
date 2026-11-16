package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure proof DATA only; this test creates no private material, writer Session or restored role. */
final class SavedAttachmentRevalidationDigestTest {
    private static ObjectNode proof(int retainedBytes) {
        var row=StrictJson.object();
        var previous=StrictJson.object();
        previous.put("retained_history","h".repeat(retainedBytes));
        row.set("previous",previous);
        for(String field:new String[]{"pair","details","basis","game","opening","progress"}) {
            var document=StrictJson.object();document.put("original",field);row.set(field,document);
        }
        return row;
    }

    @Test void boundedLedgerAndDocumentsUseTheAggregateProofDomain() throws Exception {
        // Same seven-field proof shape as the real consumer; previous alone exceeds 64 KiB.
        var row=proof(100_051);
        assertDoesNotThrow(()->ContinuityJson.canonical(row.get("previous"),ContinuityJson.LEDGER_MAX_BYTES));
        for(String field:new String[]{"pair","details","basis","game","opening","progress"})
            assertDoesNotThrow(()->ContinuityJson.canonical(row.get(field),ContinuityJson.DOCUMENT_MAX_BYTES));
        assertThrows(ContractViolationException.class,()->ContinuityJson.digest(row));
        byte[] canonical=ContinuityJson.canonical(row,ContinuityJson.DOMAIN_MAX_BYTES);
        String expected=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical));
        assertEquals(expected,SavedAttachmentAuthority.revalidationDigest(row));
        var changed=row.deepCopy();((ObjectNode)changed.get("progress")).put("changed",true);
        assertNotEquals(expected,SavedAttachmentAuthority.revalidationDigest(changed));
    }

    @Test void existingSmallProofDigestIsByteCompatible() {
        var row=proof(32);
        assertEquals(ContinuityJson.digest(row),SavedAttachmentAuthority.revalidationDigest(row));
    }

    @Test void aggregateDomainAndOriginalChildLimitsRemainFinite() {
        assertThrows(ContractViolationException.class,
                ()->SavedAttachmentAuthority.revalidationDigest(proof(ContinuityJson.DOMAIN_MAX_BYTES)));
        var previous=proof(ContinuityJson.DOCUMENT_MAX_BYTES).get("previous");
        assertThrows(ContractViolationException.class,
                ()->ContinuityJson.canonical(previous,ContinuityJson.DOCUMENT_MAX_BYTES));
        var oversizedLedger=proof(ContinuityJson.LEDGER_MAX_BYTES).get("previous");
        assertThrows(ContractViolationException.class,
                ()->ContinuityJson.canonical(oversizedLedger,ContinuityJson.LEDGER_MAX_BYTES));
    }
}

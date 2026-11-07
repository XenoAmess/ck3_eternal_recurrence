package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Header selection only: no owner descriptor, custody, source proof, private Root or runtime permission is manufactured. */
final class OriginalSavedRecoveryRoute101Test {
    @Test void originalRecoveryUsesOnlyItsExactSchemaAndPreservesTheThreeExistingModes() {
        ObjectNode row=StrictJson.object();
        for(String field:java.util.List.of("machineId","sourceRuntimeConfiguration","newRuntimeConfiguration","sourceConfirmation","checkpointPair","ownerDirectory"))row.putNull(field);
        String[] schemas={"xar.java-loaded-saved-resume-request/v1","xar.java-loaded-saved-preentry-request/v1","xar.java-loaded-saved-passive-observer-request/v1","xar.java-loaded-saved-original-recovery-request/v1"};
        for(int i=0;i<schemas.length;i++){row.put("schema",schemas[i]);assertEquals(i,RootLoadedSavedResumeMain250.requestMode(row));}
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(row));
        row.put("schema",schemas[0]);assertFalse(RootLoadedSavedResumeMain250.preentryRequest(row));
        row.put("schema",schemas[1]);assertTrue(RootLoadedSavedResumeMain250.preentryRequest(row));
        row.put("schema",schemas[2]);assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(row));
        row.put("schema",schemas[3]);row.put("fallback",true);assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(row));row.remove("fallback");
        row.remove("ownerDirectory");assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(row));row.putNull("ownerDirectory");
        row.put("schema","xar.java-loaded-saved-original-recovery-request/v2");assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(row));
    }
}

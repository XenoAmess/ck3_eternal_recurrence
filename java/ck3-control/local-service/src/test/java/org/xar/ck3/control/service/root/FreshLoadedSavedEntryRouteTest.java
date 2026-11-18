package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Request and filesystem eligibility only; no source, Game, custody or admission is minted. */
final class FreshLoadedSavedEntryRouteTest {
    @TempDir Path directory;

    @Test void freshEntryRequiresItsExplicitSchemaAndKeepsExistingRoutes() {
        var row=StrictJson.object().put("schema","xar.java-loaded-saved-fresh-entry-request/v1")
                .put("machineId","unissued-request-data").put("ownerDirectory","unissued-owner");
        var ref=new ExactRef("unissued-request-data.json",2,"0".repeat(64));
        for(String key:new String[]{"sourceRuntimeConfiguration","newRuntimeConfiguration","sourceConfirmation","checkpointPair"})
            row.set(key,ref.toJson());
        assertEquals(4,RootLoadedSavedResumeMain250.requestMode(row));
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.preentryRequest(row));
        var reread=StrictJson.parse(StrictJson.canonical(row),1<<20);
        assertEquals(4,RootLoadedSavedResumeMain250.requestMode(reread));
        for(String schema:new String[]{"xar.java-loaded-saved-fresh-entry-request/v2","fresh", ""}) {
            var bad=row.deepCopy().put("schema",schema);
            assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(bad));
        }
        var extra=row.deepCopy().put("entry_mode","FRESH");
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(extra));
        var missing=row.deepCopy();missing.remove("sourceConfirmation");
        assertThrows(IllegalArgumentException.class,()->RootLoadedSavedResumeMain250.requestMode(missing));
        row.put("schema","xar.java-loaded-saved-preentry-request/v1");
        assertEquals(1,RootLoadedSavedResumeMain250.requestMode(row));
        assertTrue(RootLoadedSavedResumeMain250.preentryRequest(row));
        row.put("schema","xar.java-loaded-saved-resume-request/v1");
        assertEquals(0,RootLoadedSavedResumeMain250.requestMode(row));
        row.put("schema","xar.java-loaded-saved-original-recovery-request/v1");
        assertEquals(3,RootLoadedSavedResumeMain250.requestMode(row));
    }

    @Test void absentFreshRootCannotBeInferredFromTheExistingPreentryRequest()throws Exception {
        Path root=directory.resolve("business-root");
        RootLoadedSavedResumeMain250.requireBusinessRoot(4,root);
        assertFalse(Files.exists(root));
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requireBusinessRoot(1,root));
        assertFalse(Files.exists(root));
        Files.createDirectory(root);
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requireBusinessRoot(4,root));
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requireBusinessRoot(1,root));
        try(var files=Files.list(root)){assertEquals(0,files.count());}
    }

    @Test void aCompleteExistingPreentryStoreCannotBeOverwrittenByFreshEntry()throws Exception {
        Path root=Files.createDirectory(directory.resolve("retained"));
        Path continuity=Files.createDirectory(root.resolve("continuity"));
        byte[] snapshot="retained-snapshot-data".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        byte[] anchor="retained-anchor-data".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(continuity.resolve("continuity.json"),snapshot);
        Files.write(continuity.resolve("genesis-anchor.json"),anchor);
        Files.createDirectory(continuity.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        RootLoadedSavedResumeMain250.requireBusinessRoot(1,root);
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requireBusinessRoot(4,root));
        assertArrayEquals(snapshot,Files.readAllBytes(continuity.resolve("continuity.json")));
        assertArrayEquals(anchor,Files.readAllBytes(continuity.resolve("genesis-anchor.json")));
        Path occupied=directory.resolve("occupied-file");Files.writeString(occupied,"retained");
        assertThrows(IOException.class,()->RootLoadedSavedResumeMain250.requireBusinessRoot(4,occupied));
        assertEquals("retained",Files.readString(occupied));
    }
}

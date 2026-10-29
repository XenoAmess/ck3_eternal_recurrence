package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
class RootNextCheckpointPathTest {
    @TempDir Path directory;
    @Test void nextSaveIsAnIdentityBoundDirectProfileChildEligibleForSavedReplacementLocation()throws IOException {
        Path profile=directory.resolve("profile"),saves=profile.resolve("save games");
        Path first=RootNextEpisodeAssemblyInputs.canonicalSaveTarget(profile,saves,"next-"+"1".repeat(64));
        Path second=RootNextEpisodeAssemblyInputs.canonicalSaveTarget(profile,saves,"next-"+"2".repeat(64));
        assertEquals(saves,first.getParent());assertEquals("xar_checkpoint.ck3",first.getFileName().toString());assertEquals(first,second);
        assertThrows(IOException.class,()->RootNextEpisodeAssemblyInputs.canonicalSaveTarget(profile,saves.resolve("episodes"),"next-"+"1".repeat(64)));
        assertThrows(IOException.class,()->RootNextEpisodeAssemblyInputs.canonicalSaveTarget(profile,saves,"../old-pair"));
    }
    /** A genuine whole-Root SAVE fixture supplies its actual canonical command; no mock command grants readiness. */
    public static org.xar.ck3.control.application.checkpoint.CheckpointRequest assertActualConsumer(
            org.xar.ck3.control.application.action.ActionCommand actualSave,Path actualProfile,Path actualSaveGames,
            String physicalToken,String actualLineage)throws IOException {
        Path produced=RootNextEpisodeAssemblyInputs.canonicalSaveTarget(actualProfile,actualSaveGames,physicalToken);
        return new org.xar.ck3.control.application.checkpoint.CheckpointRequest(actualSave,produced,actualLineage,java.util.Optional.empty());
    }
}

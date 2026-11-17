package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** The actual plan publication read-set includes the explicit NoMods settings original. */
final class RootNativeSettingsSeedInputsTest {
    @TempDir Path temporary;
    @Test void exactSettingsSeedBecomesARealPublicationWitnessAndDetectsIdentityReplacement()throws Exception{
        Path source=temporary.resolve("settings.txt");Files.writeString(source,"save_on_exit=no"+System.lineSeparator());
        var ref=FileRef.measure(source);var profile=NativeLaunchPlan.PreparedProfile.vanilla(ref);
        var witnesses=RootNativeLaunchPlanInputs.profileWitnesses(profile);
        assertEquals(1,witnesses.size());assertEquals(ref,witnesses.getFirst().source());
        SharedSourceFiles.assertUnchanged(witnesses.getFirst());
        Path replacement=temporary.resolve("replacement.txt");Files.write(replacement,Files.readAllBytes(source));
        Files.delete(source);Files.move(replacement,source);
        assertEquals(ref,FileRef.measure(source));
        assertThrows(IOException.class,()->SharedSourceFiles.assertUnchanged(witnesses.getFirst()));
    }
    @Test void changedOrMissingSeedCannotAcquirePublicationWitness()throws Exception{
        Path source=temporary.resolve("settings.txt");Files.writeString(source,"original");
        var profile=NativeLaunchPlan.PreparedProfile.vanilla(FileRef.measure(source));
        Files.writeString(source,"tampered");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.profileWitnesses(profile));
        Files.delete(source);
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.profileWitnesses(profile));
    }
    @Test void unchangedLegacyVanillaHasNoInventedProfileInput()throws Exception{
        assertTrue(RootNativeLaunchPlanInputs.profileWitnesses(NativeLaunchPlan.PreparedProfile.vanilla()).isEmpty());
    }
}

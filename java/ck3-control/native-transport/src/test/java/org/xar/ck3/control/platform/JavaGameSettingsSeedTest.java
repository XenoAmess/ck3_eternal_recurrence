package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;

/** Real isolated filesystem preparation only: no Game, Steam, process or user profile. */
final class JavaGameSettingsSeedTest {
    @TempDir Path temporary;
    private FileRef seed()throws IOException{
        Path source=temporary.resolve("declared-settings.txt");
        Files.writeString(source,String.join(System.lineSeparator(),"promt_for_tutorial=no","prompt_for_china_tutorial=no","prompt_for_ruler_designer=no","save_on_exit=no",""),StandardCharsets.UTF_8);
        return FileRef.measure(source);
    }
    @Test void declaredOriginalIsCopiedExactlyAndMatchingDestinationIsNeverReplaced()throws Exception{
        var seed=seed();var original=SharedSourceFiles.observe(Path.of(seed.path()));
        var profile=Files.createDirectory(temporary.resolve("isolated-profile"));
        Files.writeString(profile.resolve("dlc_load.json"),"{\"enabled_mods\":[\"mod/old.mod\"],\"disabled_dlcs\":[\"dlc/one\"]}");
        var declared=NativeLaunchPlan.PreparedProfile.vanilla(seed);
        JavaGameLifecycle.prepareNoModsProfile(declared,profile);
        Path target=profile.resolve("pdx_settings.txt");var copied=SharedSourceFiles.observe(target);
        assertEquals(seed.bytes(),copied.source().bytes());assertEquals(seed.sha256(),copied.source().sha256());
        assertArrayEquals(Files.readAllBytes(Path.of(seed.path())),Files.readAllBytes(target));
        assertNotEquals(original.nativeFile().identityKey(),copied.nativeFile().identityKey());
        JavaGameLifecycle.prepareNoModsProfile(declared,profile);
        SharedSourceFiles.assertUnchanged(copied);SharedSourceFiles.assertUnchanged(original);
        var selection=StrictJson.parse(Files.readAllBytes(profile.resolve("dlc_load.json")));
        assertTrue(selection.path("enabled_mods").isEmpty());assertEquals("dlc/one",selection.path("disabled_dlcs").get(0).textValue());
        try(var files=Files.list(profile)){
            assertEquals(List.of("dlc_load.json","pdx_settings.txt"),files.map(x->x.getFileName().toString()).sorted().toList());
        }
    }
    @Test void tamperedOriginalRejectsBeforeCreatingProfileOrConfiguration()throws Exception{
        var seed=seed();var declared=NativeLaunchPlan.PreparedProfile.vanilla(seed);
        Files.writeString(Path.of(seed.path()),"changed");Path profile=temporary.resolve("absent-profile");
        assertThrows(IOException.class,()->JavaGameLifecycle.prepareNoModsProfile(declared,profile));
        assertFalse(Files.exists(profile));
    }
    @Test void conflictingDestinationIsPreservedAndNoDlcSelectionIsWritten()throws Exception{
        var seed=seed();Path profile=Files.createDirectory(temporary.resolve("conflicting-profile"));
        Path target=profile.resolve("pdx_settings.txt");Files.writeString(target,"original different settings");
        var before=SharedSourceFiles.observe(target);
        assertThrows(IOException.class,()->JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(seed),profile));
        SharedSourceFiles.assertUnchanged(before);assertFalse(Files.exists(profile.resolve("dlc_load.json")));
        try(var files=Files.list(profile)){assertEquals(1,files.count());}
    }
    @Test void legacyVanillaDoesNotCreateOrAlterSettings()throws Exception{
        Path profile=Files.createDirectory(temporary.resolve("legacy-profile"));
        Path settings=profile.resolve("pdx_settings.txt");Files.writeString(settings,"user-selected original");
        var before=SharedSourceFiles.observe(settings);
        JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),profile);
        SharedSourceFiles.assertUnchanged(before);
        Path absent=temporary.resolve("new-legacy-profile");
        JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),absent);
        assertFalse(Files.exists(absent.resolve("pdx_settings.txt")));
    }
}

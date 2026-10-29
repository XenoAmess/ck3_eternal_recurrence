package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.StrictJson;

/** Ordinary isolated profile files only; no CK3, Steam, Native endpoint or worker is started. */
final class JavaGameProfileTest {
    @TempDir Path temporary;

    @Test void noModsCreatesBothEmptySelectionsForANewProfile()throws Exception{
        Path profile=temporary.resolve("new-profile");
        JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),profile);
        assertEquals(StrictJson.parse("{\"disabled_dlcs\":[],\"enabled_mods\":[]}".getBytes(StandardCharsets.UTF_8)),
                StrictJson.parse(Files.readAllBytes(profile.resolve("dlc_load.json"))));
        assertOnlyConfiguration(profile);
    }

    @Test void reusedProfileRemovesOldModsAndPreservesDlcAndOtherUserValues()throws Exception{
        Path profile=Files.createDirectory(temporary.resolve("reused-profile"));
        Path configuration=profile.resolve("dlc_load.json");
        String before="""
                {"enabled_mods":["mod/old.mod","mod/helper.mod"],"disabled_dlcs":["dlc/dlc001","dlc/dlc002"],
                 "custom":{"decimal":1.234567890123456789,"nullable":null,"flags":[true,false]},"label":"original"}
                """;
        Files.writeString(configuration,before,StandardCharsets.UTF_8);
        var expected=StrictJson.parse(before.getBytes(StandardCharsets.UTF_8));
        ((com.fasterxml.jackson.databind.node.ObjectNode)expected).putArray("enabled_mods");
        JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),profile);
        assertEquals(expected,StrictJson.parse(Files.readAllBytes(configuration)));
        JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),profile);
        assertEquals(expected,StrictJson.parse(Files.readAllBytes(configuration)));
        assertOnlyConfiguration(profile);
    }

    @Test void explicitProfilesKeepTheirOriginalSelectionAndDoNotCreateMissingDirectories()throws Exception{
        Path manifest=temporary.resolve("manifest.json");Files.writeString(manifest,"{}",StandardCharsets.UTF_8);
        var explicit=NativeLaunchPlan.PreparedProfile.explicit(ControlBuild.FileRef.measure(manifest),
                ProfileKind.SAVED_VANILLA,List.of(),List.of());
        Path profile=Files.createDirectory(temporary.resolve("explicit-profile"));
        Path configuration=profile.resolve("dlc_load.json");
        byte[] original="{ \"enabled_mods\": [\"mod/explicit.mod\"], \"disabled_dlcs\": [] }".getBytes(StandardCharsets.UTF_8);
        Files.write(configuration,original);
        JavaGameLifecycle.prepareNoModsProfile(explicit,profile);
        assertArrayEquals(original,Files.readAllBytes(configuration));
        Path missing=temporary.resolve("unused-profile");
        JavaGameLifecycle.prepareNoModsProfile(explicit,missing);
        assertFalse(Files.exists(missing));assertOnlyConfiguration(profile);
    }

    @Test void malformedOrNonobjectConfigurationIsNotOverwrittenOrSilentlyAccepted()throws Exception{
        for(String original:List.of("not json","[]","null","{\"enabled_mods\":[],\"enabled_mods\":[\"mod/old.mod\"]}")){
            Path profile=Files.createTempDirectory(temporary,"invalid-");
            Path configuration=profile.resolve("dlc_load.json");Files.writeString(configuration,original,StandardCharsets.UTF_8);
            assertThrows(IOException.class,()->JavaGameLifecycle.prepareNoModsProfile(NativeLaunchPlan.PreparedProfile.vanilla(),profile));
            assertEquals(original,Files.readString(configuration,StandardCharsets.UTF_8));assertOnlyConfiguration(profile);
        }
    }

    private static void assertOnlyConfiguration(Path profile)throws IOException{
        try(var files=Files.list(profile)){
            assertEquals(List.of("dlc_load.json"),files.map(path->path.getFileName().toString()).sorted().toList());
        }
    }
}

package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Physical input DATA producer regression. These files are not a CK3 SAVE, Started or admitted launch. */
final class InitialEpisodeSavedPolicyContractTest {
    @TempDir Path root;
    private record Inputs(ControlBuild.FileRef environment,ControlBuild.FileRef save) { }
    private Inputs inputs()throws Exception {
        Path profile=root.resolve("profile");Files.createDirectories(profile.resolve("save games"));
        Path save=profile.resolve("save games/original.ck3");Files.writeString(save,"source-data-only",StandardOpenOption.CREATE_NEW);
        var env=StrictJson.object().put("environment_sha256","e".repeat(64)).put("state_dir",root.toString()).put("profile_dir",profile.toString());
        env.putObject("rules").putArray("profile");env.putObject("load_profile").putArray("enabled_mods").add("mod/explicit-product.mod");
        Path file=root.resolve("environment-data.json");Files.write(file,StrictJson.canonical(env),StandardOpenOption.CREATE_NEW);
        return new Inputs(ControlBuild.FileRef.measure(file),ControlBuild.FileRef.measure(save));
    }
    @Test void soleSavedProducerBindsOriginalEnvironmentAndSaveWithoutInventingLifecycleOrModAbsence()throws Exception {
        var in=inputs();byte[] bytes=InitialEpisodePolicy.produceSaved(in.environment(),in.save()).bytes();
        var value=StrictJson.object(StrictJson.parse(bytes,1<<20),java.util.Set.of("schema","environment_manifest","episode_projection","succession_lifecycle","saved_game"));
        assertEquals(InitialEpisodePolicy.SAVED_SCHEMA,value.get("schema").textValue());assertEquals("native_campaign",value.get("episode_projection").textValue());
        assertTrue(value.get("succession_lifecycle").isNull());assertEquals(new ExactRef(in.save().path(),in.save().bytes(),in.save().sha256()),ExactRef.fromJson(value.get("saved_game")));
        assertEquals(new ExactRef(in.environment().path(),in.environment().bytes(),in.environment().sha256()),ExactRef.fromJson(value.get("environment_manifest")));
        assertArrayEquals(bytes,InitialEpisodePolicy.produceSaved(in.environment(),in.save()).bytes());
        assertFalse(new String(bytes,java.nio.charset.StandardCharsets.UTF_8).contains("xar_off"));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.produce(in.environment(),InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT));
    }
    @Test void sourceChangesAndSaveOutsideTheActualProfileAreRejected()throws Exception {
        var in=inputs();Path foreign=root.resolve("foreign.ck3");Files.writeString(foreign,"foreign",StandardOpenOption.CREATE_NEW);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.produceSaved(in.environment(),ControlBuild.FileRef.measure(foreign)));
        Files.writeString(Path.of(in.save().path()),"changed-source",StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(java.io.IOException.class,()->InitialEpisodePolicy.produceSaved(in.environment(),in.save()));
    }
}

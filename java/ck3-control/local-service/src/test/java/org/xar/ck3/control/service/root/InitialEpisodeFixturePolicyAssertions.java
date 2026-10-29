package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;

/** Consumes the real private PreparedFixture produced by its existing disk-input suite.
 * The historical minimal ENV DATA fixture does not qualify a launch, Game, source or live observation. */
public final class InitialEpisodeFixturePolicyAssertions {
    private InitialEpisodeFixturePolicyAssertions(){ }
    public static void assertPreparedInventoryRoundTrip(PreparedFixture same,Path outputDirectory)throws Exception {
        same.verifySources();Files.createDirectories(outputDirectory);
        var manifest=StrictJson.object();manifest.put("environment_sha256","e".repeat(64));
        manifest.put("state_dir",same.stateDir().toString());manifest.put("profile_dir",same.profileDirectory().toString());
        manifest.putObject("rules").putArray("profile");manifest.putObject("verified_mod_absence");
        var mods=ControlBuild.FileRef.measure(same.profileDirectory().resolve("dlc_load.json"));
        byte[] dlc=Files.readAllBytes(Path.of(mods.path()));
        if(dlc.length>=3&&(dlc[0]&255)==239&&(dlc[1]&255)==187&&(dlc[2]&255)==191)dlc=java.util.Arrays.copyOfRange(dlc,3,dlc.length);
        var load=manifest.putObject("load_profile");load.set("enabled_mods",StrictJson.parse(dlc,1<<20).get("enabled_mods"));load.put("dlc_load_sha256",mods.sha256());
        assertFalse(load.get("enabled_mods").isEmpty());
        Path env=outputDirectory.resolve("fixture-environment-data.json");Files.write(env,StrictJson.canonical(manifest),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        var actual=ControlBuild.FileRef.measure(env);
        RootProfileBootstrapFixturePolicyAssertions.assertActualProducer(actual,same,outputDirectory.resolve("bootstrap-policy"));
        byte[] original=InitialEpisodePolicy.produceFixture(actual,same).bytes();
        Path policy=outputDirectory.resolve("fixture-projection.json");Files.write(policy,original,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);var measured=ControlBuild.FileRef.measure(policy);
        var accepted=InitialEpisodePolicy.readExactFixture(new ExactRef(measured.path(),measured.bytes(),measured.sha256()),actual,same);
        assertSame(same,accepted.explicitFixture().orElseThrow());accepted.requireFixtureProjection(same);accepted.verify();
        assertEquals(InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_FIXTURE,accepted.kind());assertEquals("null",new String(accepted.lifecycle().bytes(),java.nio.charset.StandardCharsets.UTF_8));
        assertTrue(accepted.evidenceClosure().containsAll(same.inputClosure()));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.produce(actual,InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,InitialEpisodePolicy.FreshPact.ORDINARY_NO_PACT));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.readExact(accepted.source(),actual));
        manifest.put("profile_dir",outputDirectory.toString());Path wrong=outputDirectory.resolve("wrong-profile.json");Files.write(wrong,StrictJson.canonical(manifest),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.produceFixture(ControlBuild.FileRef.measure(wrong),same));
        var changed=StrictJson.object(StrictJson.parse(original,1<<20),java.util.Set.of("schema","environment_manifest","episode_projection","succession_lifecycle","fixture_policy","input_closure","mounted_relative_paths"));
        changed.putObject("succession_lifecycle").put("lifecycle","ordinary_campaign_succession");Path altered=outputDirectory.resolve("false-lifecycle.json");Files.write(altered,StrictJson.canonical(changed,1<<20),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);var alteredRef=ControlBuild.FileRef.measure(altered);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.readExactFixture(new ExactRef(alteredRef.path(),alteredRef.bytes(),alteredRef.sha256()),actual,same));
        org.xar.ck3.control.build.ProfileEnvironmentDomainContractTest.assertActualFixture(same,outputDirectory.resolve("explicit-environment"));
    }
}

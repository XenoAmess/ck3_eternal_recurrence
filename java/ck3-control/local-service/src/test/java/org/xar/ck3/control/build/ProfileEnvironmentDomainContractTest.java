package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.NativeRunProfileManifest.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;
import org.xar.ck3.control.service.root.RootFrozenRunProfile;

/** Real profile derivation/codec and consumer domain checks on owned software files.
 * Unqualified build inputs cannot issue a launch, FrozenRunProfile or Game authority. */
public final class ProfileEnvironmentDomainContractTest {
    @TempDir Path root;
    private record Inputs(ExplicitRequest request,List<FileRef> runtime) { }
    private static FileRef write(Path path,String bytes)throws IOException {
        Files.createDirectories(path.getParent());Files.writeString(path,bytes,StandardOpenOption.CREATE_NEW);return FileRef.measure(path);
    }
    private static Inputs inputs(Path output,Path state,ExplicitSource source)throws Exception {
        Files.createDirectories(output);Path game=Files.createDirectories(output.resolve("game"));Files.createDirectories(game.resolve("game/dlc"));
        var exe=write(game.resolve("binaries/ck3.exe"),"software data never executed");var rules=write(game.resolve("rules.txt"),"source data only");
        var launcher=write(game.resolve("launcher/launcher-settings.json"),"{\"rawVersion\":\"software\",\"version\":\"software\",\"distPlatform\":\"steam\"}");
        var build=write(output.resolve("unqualified-build.json"),"{}");var runtime=new ArrayList<FileRef>();
        for(int n=0;n<6;n++)runtime.add(write(output.resolve("runtime"+n+".jar"),"unqualified runtime data "+n));
        var request=new ExplicitRequest(EXPLICIT_REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(3600).toString(),
                state.toString(),output.toString(),build,exe,rules,launcher,false,source);
        return new Inputs(request,List.copyOf(runtime));
    }
    private static ExplicitManifest derive(Inputs inputs)throws Exception {
        return NativeRunProfileProducer.finishExplicit(NativeRunProfileProducer.deriveExplicit(inputs.request(),inputs.runtime()),Clock.systemUTC());
    }
    private static FileRef persist(Path output,ProfileEnvironment actual)throws Exception {
        var path=output.resolve("environment.json");Files.write(path,encodeEnvironment(actual),StandardOpenOption.CREATE_NEW);var original=FileRef.measure(path);
        assertEquals(actual,decodeEnvironment(encodeEnvironment(actual)));assertEquals(actual,readEnvironmentOriginal(original));return original;
    }
    @Test void bothSavedPhysicalProducerDomainsReachTheActualFrozenAndPolicyConsumers()throws Exception {
        for(int products:List.of(0,2)) {
            Path output=Files.createDirectory(root.resolve("saved-"+products)),state=Files.createDirectory(output.resolve("state"));
            Path profile=Files.createDirectory(state.resolve("profile"));var mapper=ControlBuild.strictMapper();
            var load=mapper.createObjectNode();var enabled=load.putArray("enabled_mods");var files=new ArrayList<FileRef>();
            for(int n=products-1;n>=0;n--) {
                Path product=profile.resolve("mod-content/product"+n);String descriptor="mod/product"+n+".mod";enabled.add(descriptor);
                files.add(write(profile.resolve(descriptor),"name=\"product\"\npath=\""+product.toString().replace((char)92,'/')+"\"\n"));
                files.add(write(product.resolve("descriptor.mod"),"name=\"software\"\n"));files.add(write(product.resolve("script.txt"),"software product"));
            }
            Files.write(profile.resolve("dlc_load.json"),mapper.writeValueAsBytes(load),StandardOpenOption.CREATE_NEW);
            write(profile.resolve("pdx_settings.txt"),"software prelaunch settings");
            var inventory=mapper.createObjectNode().put("schema",products==0?"ck3-saved-campaign-vanilla-profile-v1":"ck3-saved-campaign-product-only-profile-v1").put("profile_path",profile.toString());
            inventory.set("enabled_mods",enabled.deepCopy());var rows=inventory.putArray("product_files");
            for(var file:files)rows.addObject().put("path",file.path()).put("bytes",file.bytes()).put("sha256",file.sha256());
            Path source=output.resolve("inventory.json");Files.write(source,mapper.writeValueAsBytes(inventory),StandardOpenOption.CREATE_NEW);
            var input=inputs(output,state,new SavedSource(products==0?SavedKind.VANILLA:SavedKind.PRODUCT_ONLY,FileRef.measure(source)));
            var actual=derive(input);var original=persist(output,actual);InitialEpisodePolicy.requireSavedProfileDomain(readEnvironmentOriginal(original));
            RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.EnabledNativeCampaign(state),readEnvironmentOriginal(original));
            assertEquals(products,actual.productionRoots().size());
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.Enabled(state),actual));
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.DisabledFreshRobert(),actual));
            var dummy=new ExactRef(original.path(),original.bytes(),original.sha256());
            assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.DisabledFreshFixture(dummy),actual));
            var save=write(profile.resolve("save games/original.ck3"),"software source data only");
            assertThrows(IOException.class,()->InitialEpisodePolicy.produceSaved(original,save));
            Files.writeString(profile.resolve("pdx_settings.txt"),"mutable postlaunch software data",StandardOpenOption.TRUNCATE_EXISTING);
            assertEquals(actual,readEnvironmentOriginal(original));InitialEpisodePolicy.requireSavedProfileDomain(readEnvironmentOriginal(original));
        }
    }
    /** Called by both real private PreparedFixture disk-producer cases in the persistent suite. */
    public static void assertActualFixture(PreparedFixture same,Path output)throws Exception {
        same.verifySources();Files.createDirectories(output);
        var source=new FixtureSource(new FileRef(same.policySource().path(),same.policySource().bytes(),same.policySource().sha256()),
                same.inputClosure().stream().map(ref->new FileRef(ref.path(),ref.bytes(),ref.sha256())).toList(),
                new java.util.TreeSet<>(same.mountedInventory().mountedRelativePaths()).stream().toList());
        var input=inputs(output,same.stateDir(),source);var actual=derive(input);var original=persist(output,actual);
        InitialEpisodePolicy.requireFixtureProfileDomain(readEnvironmentOriginal(original),same);
        RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.DisabledFreshFixture(same.policySource()),readEnvironmentOriginal(original));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.requireSavedProfileDomain(actual));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.EnabledNativeCampaign(same.stateDir()),actual));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.DisabledFreshRobert(),actual));
        assertThrows(IllegalArgumentException.class,()->RootFrozenRunProfile.requireEnvironmentDomain(new RootFrozenRunProfile.Enabled(same.stateDir()),actual));
        var profile=(FreshFixtureProfile)actual.profile();
        var badInputs=new ArrayList<>(profile.immutableInputs());badInputs.removeIf(file->file.equals(profile.loadProfile().dlcLoad()));
        var badSource=new FixtureSource(profile.policySource(),badInputs,profile.mountedRelativePaths());
        var request=actual.request();var wrongRequest=new ExplicitRequest(request.schema(),request.machineId(),request.reviewAtUtc(),request.stateDir(),
                request.sourceWorkingDirectory(),request.qualifiedToolsBuild(),request.gameExecutable(),request.vanillaRules(),request.launcherSettings(),request.debugMode(),badSource);
        var badProfile=new FreshFixtureProfile(profile.policySource(),badInputs,profile.mountedRelativePaths(),profile.loadProfile(),profile.mountedMods(),profile.custody());
        var wrong=sealExplicit(new ExplicitManifest(actual.schema(),actual.formatVersion(),actual.machineId(),actual.observedAtUtc(),actual.stateDir(),actual.profileDir(),
                actual.game(),wrongRequest,badProfile,actual.profileAssets(),actual.dlc(),actual.originals(),actual.producerToolsBuild(),actual.producerRuntime(),actual.environmentSha256()));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.requireFixtureProfileDomain(wrong,same));
        // Software receipts remain unqualified: public prelaunch generation must still reject them.
        assertThrows(IOException.class,()->InitialEpisodePolicy.produceFixture(original,same));same.verifySources();
    }
}

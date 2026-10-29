package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Historical ENV/SAVE DATA exercises the real byte producer and request codec without claiming a Game. */
final class RootProfileBootstrapSavedPolicyTest {
    @TempDir Path root;
    @Test void actualSavedByteProducerReachesTheExistingQuoteAndStrictRequestCodec()throws IOException {
        Path profile=root.resolve("profile"),state=root.resolve("state");Files.createDirectories(profile.resolve("save games"));Files.createDirectories(state);
        var env=StrictJson.object();env.put("environment_sha256","e".repeat(64));env.put("state_dir",state.toString());env.put("profile_dir",profile.toString());
        env.putObject("rules").putArray("profile");env.putObject("verified_mod_absence");
        var load=env.putObject("load_profile");load.putArray("enabled_mods");load.put("dlc_load_sha256","d".repeat(64));
        Path envPath=root.resolve("environment-data.json"),savePath=profile.resolve("save games/original.ck3");
        Files.write(envPath,StrictJson.canonical(env),StandardOpenOption.CREATE_NEW);Files.write(savePath,new byte[]{1,2,3},StandardOpenOption.CREATE_NEW);
        FileRef actualEnv=FileRef.measure(envPath),actualSave=FileRef.measure(savePath);Path target=root.resolve("saved-policy.json");
        byte[] produced=InitialEpisodePolicy.produceSaved(actualEnv,actualSave).bytes();
        var quote=RootProfileBootstrapInputs.initialSavedNativePolicy(actualEnv,actualSave,target).quote();
        assertEquals(1,quote.size());assertEquals(produced.length,quote.getFirst().bytes());assertEquals(DriverJson.sha256(produced),quote.getFirst().sha256());
        Files.write(target,produced,StandardOpenOption.CREATE_NEW);var wire=StrictJson.parse(Files.readAllBytes(target),1<<20);
        assertEquals(InitialEpisodePolicy.SAVED_SCHEMA,wire.get("schema").textValue());assertEquals("native_campaign",wire.get("episode_projection").textValue());
        assertTrue(wire.get("succession_lifecycle").isNull());assertEquals(new ExactRef(actualSave.path(),actualSave.bytes(),actualSave.sha256()),ExactRef.fromJson(wire.get("saved_game")));
        var request=new RootProfileBootstrapCommand.SavedNativePolicyRequest("xar.java-root-initial-saved-native-policy-bootstrap/v1",
                WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(300).toString(),actualEnv,actualSave,
                new ExactRef(root.resolve("native-plan-data.json").toString(),1,"a".repeat(64)),target.toString());
        var mapper=ControlBuild.strictMapper();byte[] encoded=mapper.writeValueAsBytes(request);
        assertEquals(request,mapper.readValue(encoded,RootProfileBootstrapCommand.SavedNativePolicyRequest.class));
        ObjectNode missing=mapper.readValue(encoded,ObjectNode.class);missing.remove("actual_save");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missing),RootProfileBootstrapCommand.SavedNativePolicyRequest.class));
        ObjectNode wrong=mapper.readValue(encoded,ObjectNode.class);((ObjectNode)wrong.get("actual_save")).put("bytes",true);
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(wrong),RootProfileBootstrapCommand.SavedNativePolicyRequest.class));
        ObjectNode alias=mapper.readValue(encoded,ObjectNode.class);alias.put("schema","xar.java-root-initial-fixture-policy-bootstrap/v1");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(alias),RootProfileBootstrapCommand.SavedNativePolicyRequest.class));
        Path crossed=root.resolve("crossed.ck3");Files.write(crossed,new byte[]{1,2,3},StandardOpenOption.CREATE_NEW);
        assertThrows(IllegalArgumentException.class,()->RootProfileBootstrapInputs.initialSavedNativePolicy(actualEnv,FileRef.measure(crossed),root.resolve("crossed-policy.json")));
    }
}

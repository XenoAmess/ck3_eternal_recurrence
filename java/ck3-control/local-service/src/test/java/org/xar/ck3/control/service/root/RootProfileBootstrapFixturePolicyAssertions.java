package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.PreparedFixture;

/** Called by both real PreparedFixture inventory cases. Persisted bytes are test DATA, never an admitted write or Game. */
public final class RootProfileBootstrapFixturePolicyAssertions {
    private RootProfileBootstrapFixturePolicyAssertions(){ }
    public static void assertActualProducer(FileRef actualEnvironment,PreparedFixture same,Path outputRoot)throws IOException {
        same.verifySources();Files.createDirectories(outputRoot);
        Path target=outputRoot.resolve("bootstrap-initial-fixture-policy.json");
        byte[] bytes=InitialEpisodePolicy.produceFixture(actualEnvironment,same).bytes();
        var actual=RootProfileBootstrapInputs.initialFixturePolicy(actualEnvironment,same,target);
        var expected=new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.INITIAL_POLICY,
                target.getFileName().toString(),bytes.length,DriverJson.sha256(bytes));
        assertEquals(List.of(expected),actual.quote());
        Files.write(target,bytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        var written=FileRef.measure(target);
        var decoded=InitialEpisodePolicy.readExactFixture(new ExactRef(written.path(),written.bytes(),written.sha256()),actualEnvironment,same);
        decoded.verify();assertArrayEquals(bytes,InitialEpisodePolicy.produceFixture(actualEnvironment,same).bytes());
        var value=StrictJson.parse(bytes,1<<20);
        assertEquals("native_campaign",value.get("episode_projection").textValue());
        assertTrue(value.has("succession_lifecycle")&&value.get("succession_lifecycle").isNull());
        assertEquals(same.policySource(),ExactRef.fromJson(value.get("fixture_policy")));

        var request=new RootProfileBootstrapCommand.FixturePolicyRequest("xar.java-root-initial-fixture-policy-bootstrap/v1",
                WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(300).toString(),actualEnvironment,
                same.policySource(),same.stateDir().toString(),same.profileDirectory().toString(),target.toString());
        var mapper=ControlBuild.strictMapper();byte[] encoded=mapper.writeValueAsBytes(request);
        assertEquals(request,mapper.readValue(encoded,RootProfileBootstrapCommand.FixturePolicyRequest.class));
        ObjectNode missing=mapper.readValue(encoded,ObjectNode.class);missing.remove("fixture_policy");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missing),RootProfileBootstrapCommand.FixturePolicyRequest.class));
        ObjectNode booleanSize=mapper.readValue(encoded,ObjectNode.class);((ObjectNode)booleanSize.get("fixture_policy")).put("bytes",true);
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(booleanSize),RootProfileBootstrapCommand.FixturePolicyRequest.class));
        ObjectNode ordinary=mapper.readValue(encoded,ObjectNode.class);ordinary.put("schema","xar.java-root-initial-policy-bootstrap/v1");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(ordinary),RootProfileBootstrapCommand.FixturePolicyRequest.class));
        same.verifySources();actualEnvironment.verify();
    }
}

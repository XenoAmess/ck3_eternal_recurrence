package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Request DATA roundtrips issue no creator, Started, Prepared or canonical cold authority. */
final class RootSavedNativeCoordinatorTest {
    @TempDir Path root;
    @Test void actualCliDecoderKeepsOrdinaryAndRequiresACompleteExplicitSavedSource() {
        String startup=root.resolve("startup.json").toString(),saved=root.resolve("saved-route.json").toString(),sha="a".repeat(64);
        assertTrue(RootSavedNativeCoordinator.arguments(new String[]{startup,"1",sha}).savedRoute().isEmpty());
        var actual=RootSavedNativeCoordinator.arguments(new String[]{startup,"1",sha,saved,"2",sha});
        assertEquals(new FileRef(startup,1,sha),actual.startup());assertEquals(new FileRef(saved,2,sha),actual.savedRoute().orElseThrow());
        assertThrows(IllegalArgumentException.class,()->RootSavedNativeCoordinator.arguments(new String[]{startup,"1",sha,saved}));
        assertThrows(IllegalArgumentException.class,()->RootSavedNativeCoordinator.arguments(new String[]{startup,"01",sha}));
        assertThrows(IllegalArgumentException.class,()->RootSavedNativeCoordinator.arguments(new String[]{startup,"1",sha,saved,"true",sha}));
    }
    @Test void explicitSavedRequestRejectsMissingPairWrongIdentityTypeAndFixtureAlias()throws IOException {
        var request=new RootSavedNativeCoordinator.Request(RootSavedNativeCoordinator.SCHEMA,WindowsJobProcess.currentMachineId(),
                Instant.now().plusSeconds(300).toString(),new FileRef(root.resolve("startup.json").toString(),1,"a".repeat(64)),
                new FileRef(root.resolve("pair.json").toString(),1,"b".repeat(64)),root.resolve("cold-evidence").toString());
        var mapper=ControlBuild.strictMapper();byte[] bytes=mapper.writeValueAsBytes(request);
        assertEquals(request,mapper.readValue(bytes,RootSavedNativeCoordinator.Request.class));
        ObjectNode missing=mapper.readValue(bytes,ObjectNode.class);missing.remove("checkpoint_pair");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(missing),RootSavedNativeCoordinator.Request.class));
        ObjectNode wrong=mapper.readValue(bytes,ObjectNode.class);((ObjectNode)wrong.get("checkpoint_pair")).put("bytes",true);
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(wrong),RootSavedNativeCoordinator.Request.class));
        ObjectNode fixture=mapper.readValue(bytes,ObjectNode.class);fixture.put("schema","xar.java-root-initial-fixture-policy-bootstrap/v1");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(fixture),RootSavedNativeCoordinator.Request.class));
        ObjectNode extra=mapper.readValue(bytes,ObjectNode.class);extra.putObject("started");
        assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(extra),RootSavedNativeCoordinator.Request.class));
    }
}

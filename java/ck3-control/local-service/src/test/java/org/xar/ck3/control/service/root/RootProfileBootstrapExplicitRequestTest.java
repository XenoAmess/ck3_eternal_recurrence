package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.WindowsJobProcess;

/** The production CLI request and sole producer's explicit source domain remain separate from ordinary PROFILE. */
final class RootProfileBootstrapExplicitRequestTest {
    @TempDir Path root;
    @Test void persistedBootstrapRequestRejectsMissingWrongTypeAliasAndWrongTarget()throws Exception {
        Path producer=root.resolve("producer-request.json");Files.writeString(producer,"{}",StandardOpenOption.CREATE_NEW);
        var request=new RootProfileBootstrapCommand.ExplicitProfileRequest("xar.java-root-explicit-profile-bootstrap/v1",
                WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(300).toString(),FileRef.measure(producer),
                root.resolve("env-output").resolve(NativeRunProfileProducer.ENVIRONMENT_NAME).toString());
        var mapper=ControlBuild.strictMapper();Path source=root.resolve("bootstrap-request.json");
        Files.write(source,mapper.writeValueAsBytes(request),StandardOpenOption.CREATE_NEW);
        byte[] wire=Files.readAllBytes(source);
        assertEquals(request,mapper.readValue(wire,RootProfileBootstrapCommand.ExplicitProfileRequest.class));
        for(String field:List.of("producer_request","environment_target","review_at_utc")){
            var invalid=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);invalid.remove(field);
            assertThrows(IOException.class,()->mapper.readValue(mapper.writeValueAsBytes(invalid),RootProfileBootstrapCommand.ExplicitProfileRequest.class));
        }
        var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);
        ((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("producer_request")).put("bytes",true);
        byte[] wrongScalar=mapper.writeValueAsBytes(wrong);
        assertThrows(IOException.class,()->mapper.readValue(wrongScalar,RootProfileBootstrapCommand.ExplicitProfileRequest.class));
        var oldSchema=(com.fasterxml.jackson.databind.node.ObjectNode)mapper.readTree(wire);oldSchema.put("schema","xar.java-root-profile-bootstrap/v1");
        byte[] alias=mapper.writeValueAsBytes(oldSchema);
        assertThrows(IOException.class,()->mapper.readValue(alias,RootProfileBootstrapCommand.ExplicitProfileRequest.class));
        assertThrows(IllegalArgumentException.class,()->new RootProfileBootstrapCommand.ExplicitProfileRequest(request.schema(),request.machineId(),
                request.reviewAtUtc(),request.producerRequest(),root.resolve("ordinary-default.json").toString()));
    }
    @Test void explicitSourceModeAndOutputRootsAreCheckedBeforeAnyQualifiedProducerOrWrite()throws Exception {
        Path data=root.resolve("source.json");Files.writeString(data,"{}",StandardOpenOption.CREATE_NEW);FileRef original=FileRef.measure(data);
        var saved=request(new NativeRunProfileManifest.SavedSource(NativeRunProfileManifest.SavedKind.VANILLA,original));
        var fixture=request(new NativeRunProfileManifest.FixtureSource(original,List.of(original),List.of("mod/exact.mod")));
        RootProfileBootstrapCommand.requireExplicitMode(RootProfileBootstrapCommand.Mode.EXPLICIT_SAVED_PROFILE,saved);
        RootProfileBootstrapCommand.requireExplicitMode(RootProfileBootstrapCommand.Mode.EXPLICIT_FIXTURE_PROFILE,fixture);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.requireExplicitMode(RootProfileBootstrapCommand.Mode.EXPLICIT_SAVED_PROFILE,fixture));
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.requireExplicitMode(RootProfileBootstrapCommand.Mode.EXPLICIT_FIXTURE_PROFILE,saved));
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.requireExplicitMode(RootProfileBootstrapCommand.Mode.PROFILE,saved));
        assertThrows(IOException.class,()->RootProfileBootstrapInputs.requireExplicitEnvironmentTarget(saved,List.of(),
                saved.profile().resolve(NativeRunProfileProducer.ENVIRONMENT_NAME)));
        assertThrows(IOException.class,()->NativeRunProfileProducer.prepareSaved(saved,java.time.Clock.systemUTC()));
        assertFalse(Files.exists(root.resolve("state")));
    }
    private NativeRunProfileManifest.ExplicitRequest request(NativeRunProfileManifest.ExplicitSource source)throws IOException {
        FileRef original=FileRef.measure(root.resolve("source.json"));
        return new NativeRunProfileManifest.ExplicitRequest(NativeRunProfileManifest.EXPLICIT_REQUEST_SCHEMA,
                WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(600).toString(),root.resolve("state").toString(),root.toString(),
                original,original,original,original,false,source);
    }
}


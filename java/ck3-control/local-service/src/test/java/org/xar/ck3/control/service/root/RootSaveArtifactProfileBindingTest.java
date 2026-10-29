package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.platform.*;
import org.xar.ck3.control.service.mcp.McpCancellation;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;

/** Genuine independent configuration producers and real read-only profile consumer; no Game. */
final class RootSaveArtifactProfileBindingTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef data(String name)throws IOException {
        Path file=temporary.resolve(name);Files.writeString(file,"software launch configuration DATA "+name);
        return ControlBuild.FileRef.measure(file);
    }
    @Test void independentAcceptedMetadataCannotRejectTheSameActualProfileOrPermitAnotherDirectory()throws Exception {
        Path profile=Files.createDirectory(temporary.resolve("profile"));
        var review=new LaunchSourceBinding.Review(null,null,data("configured-game.exe"),data("configured-bridge.dll"),
                data("configured-injector.exe"),null,null,List.of());
        Instant expired=Instant.parse("2000-01-01T00:00:00Z");
        var configuration=new NativeLaunchPlanCodec.Configuration("software-request","software-session",review,
                profile,temporary.resolve("state"),temporary.resolve("evidence"),"\\\\.\\pipe\\save-profile-software",
                "software-bridge","software-adapter",new NativeLaunchPlan.NewGame(),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,1L<<20,expired,
                Duration.ofSeconds(1),Duration.ofSeconds(1),new SteamOfflineProbe.Plan("software-machine",data("steam.exe"),expired),
                NativeLaunchPlan.PreparedProfile.vanilla(),128);
        var json=NativeLaunchPlanCodec.toJson(configuration);
        var first=NativeLaunchPlanCodec.fromJson(json).accept();
        var second=NativeLaunchPlanCodec.fromJson(json.deepCopy()).accept();
        assertNotSame(first,second);assertNotSame(first.sources(),second.sources());
        assertNotSame(first.preparedProfile(),second.preparedProfile());
        assertEquals(first.preparedProfile(),second.preparedProfile());
        var implementation=new RootOrdinaryImplementationMetadata().implementation(RootSaveArtifactPublicProducts.class);
        var prepared=RootSaveArtifactPublicProducts.prepare(first,Clock.systemUTC(),VanillaEventCatalog.load().textRules(),implementation);
        prepared.requireSamePlan(second);
        var binding=RootSaveArtifactPublicProducts.binding(implementation,prepared::inspect);
        var arguments=new Arguments(Presence.VALUE,Optional.of(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8))));
        var request=binding.decoder().decode(new ToolCall(RootSaveArtifactPublicProducts.NAME,arguments,Optional.empty(),new McpCancellation()));
        var result=binding.encoder().encode(binding.actual().invoke(request));
        var envelope=ControlBuild.strictMapper().readTree(result.bytes());
        assertFalse(envelope.path("isError").booleanValue());
        assertEquals(0,envelope.path("structuredContent").path("artifact_count").intValue());
        Path other=Files.createDirectory(temporary.resolve("other-profile"));
        var wrong=json.deepCopy();wrong.put("profile_directory",other.toString());
        var wrongPlan=NativeLaunchPlanCodec.fromJson(wrong).accept();
        assertThrows(IOException.class,()->prepared.requireSamePlan(wrongPlan));
        Files.move(profile,temporary.resolve("retained-original-profile"));Files.createDirectory(profile);
        assertThrows(IOException.class,()->prepared.requireSamePlan(second));
    }
}

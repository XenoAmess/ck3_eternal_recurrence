package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
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
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Explicit metadata only. Missing genuine Native/profile originals never count as a successful publication. */
final class RootNativeLaunchPlanCommandTest {
    @TempDir Path directory;
    private FileRef source(String name){return new FileRef(directory.resolve(name).toString(),1,"a".repeat(64));}
    private RootNativeLaunchPlanInputs.Invocation invocation(boolean saved,RootNativeLaunchPlanInputs.Mode mode) {
        Instant until=Instant.now().plusSeconds(300);
        var review=new LaunchSourceBinding.Review("software-fixture",until,source("ck3.exe"),source("xar_ck3_bridge.dll"),source("xar_ck3_bridge_injector.exe"),
                new NativeLaunchEvidence.Inputs(source("native-env.json"),source("native-build.json"),source("native-register.json")),
                directory,List.of(source("deployment.jar")));
        NativeLaunchPlan.Load load=saved?new NativeLaunchPlan.SavedGame("original",source("original.ck3")):new NativeLaunchPlan.NewGame();
        NativeLaunchPlan.PreparedProfile prepared=saved
                ?NativeLaunchPlan.PreparedProfile.explicit(source("saved-env.json"),ProfileKind.SAVED_VANILLA,List.of(),List.of(source("saved-settings.txt")))
                :new NativeLaunchPlan.PreparedProfile(source("fresh-env.json"),directory.resolve("production"),"mod/xar_autoplayer.mod",
                        List.of(source("fresh-settings.txt")),List.of(source("production/descriptor.mod")));
        var data=new NativeLaunchPlanCodec.Configuration("explicit-plan","explicit-session",review,directory.resolve("profile"),
                directory.resolve("state"),directory.resolve("evidence"),"\\\\.\\pipe\\explicit-plan","explicit-bridge","explicit-adapter",
                load,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),8L<<30,128L<<20,until,
                Duration.ofSeconds(10),Duration.ofMinutes(2),new SteamOfflineProbe.Plan("software-fixture",source("steam.exe"),until),prepared,128);
        return new RootNativeLaunchPlanInputs.Invocation(mode,
                new RootNativeLaunchPlanInputs.Request(data,directory.resolve(RootNativeLaunchPlanInputs.FILE_NAME),until.minusSeconds(1)),
                mode==RootNativeLaunchPlanInputs.Mode.QUOTE?Optional.empty():Optional.of(source("binding.json")));
    }
    @Test void bothLoadAndProfileBranchesReachTheExistingCodecAndExactRequestReader()throws IOException {
        for(boolean saved:new boolean[]{false,true}) {
            var actual=invocation(saved,RootNativeLaunchPlanInputs.Mode.QUOTE);byte[] raw=RootNativeLaunchPlanInputs.encodeInvocation(actual);
            assertEquals(actual,RootNativeLaunchPlanInputs.decodeInvocation(raw));
            Path input=directory.resolve(saved?"saved-inputs.json":"fresh-inputs.json");Files.write(input,raw);
            assertEquals(actual,RootNativeLaunchPlanInputs.readInvocation(FileRef.measure(input)));
            assertFalse(Files.exists(actual.request().target()));
            var decoded=StrictJson.object(StrictJson.parse(raw),java.util.Set.of("schema","mode","configuration","target","review_at_utc","binding_ref"));
            assertArrayEquals(StrictJson.canonical(NativeLaunchPlanCodec.toJson(actual.request().configuration()),NativeLaunchPlanCodec.MAXIMUM_BYTES),
                    StrictJson.canonical(decoded.get("configuration"),NativeLaunchPlanCodec.MAXIMUM_BYTES));
            assertTrue(decoded.get("binding_ref").isNull());
        }
        var create=invocation(true,RootNativeLaunchPlanInputs.Mode.CREATE_NEW);
        assertEquals(create,RootNativeLaunchPlanInputs.decodeInvocation(RootNativeLaunchPlanInputs.encodeInvocation(create)));
    }
    @Test void missingNullAndWrongModeBindingsRetainTheirDistinctContract()throws IOException {
        var quote=invocation(false,RootNativeLaunchPlanInputs.Mode.QUOTE);
        ObjectNode good=assertInstanceOf(ObjectNode.class,StrictJson.parse(RootNativeLaunchPlanInputs.encodeInvocation(quote)));
        var missing=good.deepCopy();missing.remove("binding_ref");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(StrictJson.canonical(missing)));
        var createWithoutBinding=good.deepCopy();createWithoutBinding.put("mode","CREATE_NEW");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(StrictJson.canonical(createWithoutBinding)));
        var quotedBinding=assertInstanceOf(ObjectNode.class,StrictJson.parse(RootNativeLaunchPlanInputs.encodeInvocation(invocation(false,RootNativeLaunchPlanInputs.Mode.CREATE_NEW))));
        quotedBinding.put("mode","QUOTE");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(StrictJson.canonical(quotedBinding)));
    }
    @Test void wrongNestedTypesAndExtraFieldsFailThroughTheSoleConfigurationBoundary()throws IOException {
        var base=assertInstanceOf(ObjectNode.class,StrictJson.parse(RootNativeLaunchPlanInputs.encodeInvocation(invocation(true,RootNativeLaunchPlanInputs.Mode.QUOTE))));
        String original=new String(StrictJson.canonical(base,RootNativeLaunchPlanInputs.MAXIMUM_INVOCATION_BYTES),java.nio.charset.StandardCharsets.UTF_8);
        String originalField="\"game_memory_bytes\":8589934592";
        assertTrue(original.contains(originalField));
        assertEquals(original.indexOf(originalField),original.lastIndexOf(originalField));
        for(String token:List.of("true","1.0","\"1\"","null")) {
            // Inject exact original token bytes. A JsonNode parse/serialize round trip can normalize 1.0 to 1.
            String field="\"game_memory_bytes\":"+token;
            byte[] raw=original.replace(originalField,field).getBytes(java.nio.charset.StandardCharsets.UTF_8);
            String actual=new String(raw,java.nio.charset.StandardCharsets.UTF_8);
            assertTrue(actual.contains(field),token);
            assertFalse(StrictJson.parse(raw,RootNativeLaunchPlanInputs.MAXIMUM_INVOCATION_BYTES).path("configuration").path("game_memory_bytes").isIntegralNumber(),token);
            // The managed test stdout retains the exact invalid original so attribution can be checked later.
            System.out.println("M3_NATIVE_PLAN_RAW_REJECT_CASE "+token+" "+actual);
            assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(raw),token);
        }
        var extra=base.deepCopy();extra.put("ready",true);
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(StrictJson.canonical(extra)));
        var missing=base.deepCopy();assertInstanceOf(ObjectNode.class,missing.get("configuration")).remove("review");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.decodeInvocation(StrictJson.canonical(missing)));
    }
    @Test void executeStillCallsActualProducerAndRefusesMissingOriginalsBeforeAnyOutput()throws IOException {
        for(boolean saved:new boolean[]{false,true}) {
            var actual=invocation(saved,RootNativeLaunchPlanInputs.Mode.QUOTE);
            assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.execute(actual,Clock.systemUTC()));
            assertFalse(Files.exists(actual.request().target()));
        }
        assertThrows(IllegalArgumentException.class,()->RootNativeLaunchPlanInputs.main(new String[]{"missing","01","a".repeat(64)}));
        assertThrows(IllegalArgumentException.class,()->RootNativeLaunchPlanInputs.main(new String[]{"missing","1"}));
    }
    @Test void ordinaryQuoteFrameUsesTheActualIndependentIssuerContract()throws IOException {
        var actual=invocation(false,RootNativeLaunchPlanInputs.Mode.QUOTE);
        var output=new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,
                RootNativeLaunchPlanInputs.FILE_NAME,3,"a".repeat(64));
        byte[] body=RootNativeLaunchPlanInputs.quoteFrame(actual.request(),output);
        byte[] frame=java.util.Arrays.copyOf(body,body.length+1);frame[body.length]='\n';
        var quote=RootBootstrapProtocol.line(frame,RootBootstrapProtocol.Quote.class);
        assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,quote);
        assertEquals("NATIVE_LAUNCH_PLAN",quote.phase());
        assertEquals(actual.request().configuration().review().machineId(),quote.machineId());
        assertEquals(actual.request().reviewAt().toString(),quote.reviewAtUtc());
        assertEquals(actual.request().target().getParent().toString(),quote.assetRoot());
        assertEquals(List.of(output),quote.outputs());
        assertEquals(List.of(),quote.outputDirectories());assertEquals(List.of(),quote.retainedInputs());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",quote.authority());
        assertFalse(Files.exists(actual.request().target()));
    }

    @Test void v4NoModsQuoteAndPrepareUseEffectiveMachineWithoutOutput() throws IOException {
        var until = Instant.now().plusSeconds(300);
        var review = new LaunchSourceBinding.Review(null, until, source("ck3.exe"), source("bridge.dll"), source("injector.exe"),
                new NativeLaunchEvidence.Inputs(source("native-env.json"), source("native-build.json"), source("native-register.json")),
                directory, List.of(source("deployment.jar")));
        var profile = NativeLaunchPlan.PreparedProfile.vanilla();
        var v4Config = new NativeLaunchPlanCodec.Configuration("v4-req", "v4-sess", review, directory.resolve("profile"),
                directory.resolve("state"), directory.resolve("evidence"), "\\\\.\\pipe\\v4", "v4-bridge", "v4-adapter",
                new NativeLaunchPlan.NewGame(), false, NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of(),
                8L<<30, 128L<<20, until, Duration.ofSeconds(10), Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("steam-machine", source("steam.exe"), until), profile, 128);
        var request = new RootNativeLaunchPlanInputs.Request(v4Config, directory.resolve(RootNativeLaunchPlanInputs.FILE_NAME), until.minusSeconds(1));
        var invocation = new RootNativeLaunchPlanInputs.Invocation(RootNativeLaunchPlanInputs.Mode.QUOTE, request, Optional.empty());
        
        var prepared = RootNativeLaunchPlanInputs.prepare(request, Clock.systemUTC());
        assertFalse(Files.exists(request.target()));
        
        var output = prepared.quote();
        byte[] body = RootNativeLaunchPlanInputs.quoteFrame(request, output);
        byte[] frame = java.util.Arrays.copyOf(body, body.length+1); frame[body.length]='\n';
        var quote = RootBootstrapProtocol.line(frame, RootBootstrapProtocol.Quote.class);
        assertEquals("steam-machine", quote.machineId());
        
        var execBytes = RootNativeLaunchPlanInputs.execute(invocation, Clock.systemUTC());
        var execJson = StrictJson.parse(execBytes);
        assertEquals("steam-machine", execJson.path("machine_id").asText());
    }

    @Test void v4NoModsPastHistoricalReviewStillPrepares() throws IOException {
        var until = Instant.now().plusSeconds(300);
        var pastReview = Instant.now().minusSeconds(3600);
        var review = new LaunchSourceBinding.Review("software-fixture", pastReview, source("ck3.exe"), source("bridge.dll"), source("injector.exe"),
                new NativeLaunchEvidence.Inputs(source("native-env.json"), source("native-build.json"), source("native-register.json")),
                directory, List.of(source("deployment.jar")));
        var profile = NativeLaunchPlan.PreparedProfile.vanilla();
        var v4Config = new NativeLaunchPlanCodec.Configuration("v4-past", "v4-sess", review, directory.resolve("profile"),
                directory.resolve("state"), directory.resolve("evidence"), "\\\\.\\pipe\\v4", "v4-bridge", "v4-adapter",
                new NativeLaunchPlan.NewGame(), false, NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of(),
                8L<<30, 128L<<20, until, Duration.ofSeconds(10), Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("steam-machine", source("steam.exe"), until), profile, 128);
        var request = new RootNativeLaunchPlanInputs.Request(v4Config, directory.resolve(RootNativeLaunchPlanInputs.FILE_NAME), until.minusSeconds(1));
        var invocation = new RootNativeLaunchPlanInputs.Invocation(RootNativeLaunchPlanInputs.Mode.QUOTE, request, Optional.empty());
        
        var prepared = RootNativeLaunchPlanInputs.prepare(request, Clock.systemUTC());
        assertFalse(Files.exists(request.target()));
        byte[] body = RootNativeLaunchPlanInputs.quoteFrame(request, prepared.quote());
        byte[] frame = java.util.Arrays.copyOf(body, body.length+1); frame[body.length]='\n';
        var quote = RootBootstrapProtocol.line(frame, RootBootstrapProtocol.Quote.class);
        assertEquals("software-fixture", quote.machineId());
    }

    @Test void v4NoModsDebugModeStillPrepares() throws IOException {
        var until = Instant.now().plusSeconds(300);
        var review = new LaunchSourceBinding.Review("software-fixture", until, source("ck3.exe"), source("bridge.dll"), source("injector.exe"),
                new NativeLaunchEvidence.Inputs(source("native-env.json"), source("native-build.json"), source("native-register.json")),
                directory, List.of(source("deployment.jar")));
        var profile = NativeLaunchPlan.PreparedProfile.vanilla();
        var v4Config = new NativeLaunchPlanCodec.Configuration("v4-debug", "v4-sess", review, directory.resolve("profile"),
                directory.resolve("state"), directory.resolve("evidence"), "\\\\.\\pipe\\v4", "v4-bridge", "v4-adapter",
                new NativeLaunchPlan.NewGame(), true, NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of(),
                8L<<30, 128L<<20, until, Duration.ofSeconds(10), Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("steam-machine", source("steam.exe"), until), profile, 128);
        var request = new RootNativeLaunchPlanInputs.Request(v4Config, directory.resolve(RootNativeLaunchPlanInputs.FILE_NAME), until.minusSeconds(1));
        var invocation = new RootNativeLaunchPlanInputs.Invocation(RootNativeLaunchPlanInputs.Mode.QUOTE, request, Optional.empty());
        
        assertNotNull(RootNativeLaunchPlanInputs.prepare(request, Clock.systemUTC()));
        assertEquals("software-fixture", StrictJson.parse(RootNativeLaunchPlanInputs.execute(invocation, Clock.systemUTC())).path("machine_id").asText());
        assertFalse(Files.exists(request.target()));
    }

    @Test void v4SavedGameNoModsPrepareAndQuote() throws IOException {
        var review = new LaunchSourceBinding.Review(null, null, source("ck3.exe"), source("bridge.dll"), source("injector.exe"),
                null, null, List.of());
        var profile = NativeLaunchPlan.PreparedProfile.vanilla();
        var v4Config = new NativeLaunchPlanCodec.Configuration("v4-saved", "v4-sess", review, directory.resolve("profile"),
                directory.resolve("state"), directory.resolve("evidence"), "\\\\.\\pipe\\v4", "v4-bridge", "v4-adapter",
                new NativeLaunchPlan.SavedGame("save", source("save.ck3")), false, NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of(),
                8L<<30, 128L<<20, Instant.now().plusSeconds(300), Duration.ofSeconds(10), Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("steam-machine", source("steam.exe"), Instant.now().plusSeconds(300)), profile, 128);
        var request = new RootNativeLaunchPlanInputs.Request(v4Config, directory.resolve(RootNativeLaunchPlanInputs.FILE_NAME), Instant.now().plusSeconds(100));
        var invocation = new RootNativeLaunchPlanInputs.Invocation(RootNativeLaunchPlanInputs.Mode.QUOTE, request, Optional.empty());
        
        var prepared = RootNativeLaunchPlanInputs.prepare(request, Clock.systemUTC());
        assertFalse(Files.exists(request.target()));
        
        var output = prepared.quote();
        byte[] body = RootNativeLaunchPlanInputs.quoteFrame(request, output);
        byte[] frame = java.util.Arrays.copyOf(body, body.length+1); frame[body.length]='\n';
        var quote = RootBootstrapProtocol.line(frame, RootBootstrapProtocol.Quote.class);
        assertEquals("steam-machine", quote.machineId());
    }
}

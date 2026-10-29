package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Actual startup-file selection and no-write quote; this is not runtime or Game qualification. */
public final class RootFiniteFirstLiveRequestProducerTest {
    @TempDir Path temporary;
    private static final Instant NOW=Instant.parse("2026-10-26T00:00:00Z");
    private static final Clock CLOCK=Clock.fixed(NOW,ZoneOffset.UTC);
    private FileRef original(String name,String contents)throws IOException {
        Path target=temporary.resolve(name);Files.writeString(target,contents);return SharedSourceFiles.observe(target).source();
    }
    private RootStartupConfiguration startup()throws IOException {
        String machine=WindowsJobProcess.currentMachineId();var source=original("original-source.txt","controlled source original");
        return new RootStartupConfiguration(machine,NOW.plusSeconds(600),original("application.json","{}"),original("runtime.json","{}"),
                "software-finite-input",new G2Source(machine,NOW.toString(),"software-input-fixture",
                        new ExactRef(source.path(),source.bytes(),source.sha256())),new RootStartupConfiguration.FreshRobert("fresh-robert"),
                new RootStartupConfiguration.CheckpointPaths(temporary.resolve("driver.json"),temporary.resolve("checkpoint"),
                        temporary.resolve("attachments"),"lineage",temporary.resolve("robert.ck3")),
                new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(25),true),Duration.ofSeconds(30),
                List.of(new BatchLimits("batch-first",5,Duration.ofMinutes(2),Duration.ofSeconds(20),Duration.ofMillis(100),1)),
                temporary.resolve("receipts"));
    }
    private RootFiniteFirstLiveRequest finite(FileRef startup) {
        return new RootFiniteFirstLiveRequest("finite-input-test",WindowsJobProcess.currentMachineId(),NOW,NOW.plusSeconds(300),
                new RootStartupInputsProducer.Request(startup,Duration.ofSeconds(1)),1,Duration.ofSeconds(30));
    }
    @Test public void realStartupOriginalFeedsTypedQuoteWithoutCreatingTheFiniteRequest()throws Exception {
        byte[] startupBytes=StrictJson.canonical(startup().toJson(),RootStartupConfiguration.MAXIMUM_BYTES);
        Path input=temporary.resolve("startup.json");Files.write(input,startupBytes);FileRef selected=SharedSourceFiles.observe(input).source();
        var request=new RootFiniteFirstLiveRequestProducer.Request(RootJavaBootstrapInputs.Mode.QUOTE,null,
                temporary.resolve("finite-request.json"),finite(selected));
        var decoded=RootFiniteFirstLiveRequestProducer.decode(RootFiniteFirstLiveRequestProducer.encode(request));
        assertEquals(request,decoded);
        var prepared=RootFiniteFirstLiveRequestProducer.prepare(decoded,CLOCK);
        assertEquals(RootBootstrapOutputContract.Kind.FINITE_FIRST_LIVE_REQUEST,prepared.quote().getFirst().kind());
        assertEquals(request.finite().encode().length,prepared.expected().bytes());
        assertEquals(org.xar.ck3.control.application.driver.DriverJson.sha256(request.finite().encode()),prepared.expected().sha256());
        assertFalse(Files.exists(request.target()));
        assertThrows(IOException.class,()->prepared.createNew(CLOCK));
        assertFalse(Files.exists(request.target()));
    }
    @Test public void missingActualStartupCannotBePricedOrPublished()throws Exception {
        var missing=new FileRef(temporary.resolve("missing-startup.json").toString(),2,"a".repeat(64));
        var request=new RootFiniteFirstLiveRequestProducer.Request(RootJavaBootstrapInputs.Mode.QUOTE,null,
                temporary.resolve("finite-request.json"),finite(missing));
        assertThrows(IOException.class,()->RootFiniteFirstLiveRequestProducer.prepare(request,CLOCK));
        assertFalse(Files.exists(request.target()));
    }
}

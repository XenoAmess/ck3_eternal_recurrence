package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.build.ManualBuildCapacityReleaseProducer.*;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;

final class ManualPreparationExceptionSerializationTest {
    @TempDir Path temporary;

    @Test void actualRejectedProducerKeepsItsLivePinButJavaExceptionSerializationCannotRestoreEvidence()throws Exception {
        Path base=Files.createDirectory(temporary.resolve("software-case")).toRealPath();
        Path source=Files.createDirectory(base.resolve("source")),work=Files.createDirectory(base.resolve("work"));
        Path policy=base.resolve("policy.json"),issuerSource=base.resolve("software-issuer.txt");
        Files.writeString(policy,"{\"schema\":\"xar-storage-retention-policy-v1\"}");
        Files.writeString(issuerSource,"software fixture only; no financial or Maven authority");
        var config=new ControlBuild.Config(source,work,base.resolve("rejected-manual.json"),"software-serialization-case",
                "software-writer",null,base,"3.10.0",10,ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,ControlBuild.SourceLimitProfile.STANDARD_8_MIB);
        Instant observed=Instant.parse("2026-10-24T00:00:00Z");
        var issuer=new IssuerDomain("software-owner","software-issuer",FileRef.measure(issuerSource),"fixture-only","no execution");
        var request=new Request(config,"software-machine",observed,observed.plusSeconds(60),issuer,FileRef.measure(policy),
                List.of(source),new Parts(1000000,1000000,1000000,1000000,1000000,1000000),
                List.of(new Volume(base,100000000,80000000,1000000,2000000,3000000,4000000,5000000,100000000)),new Memory(128000000,64000000));
        // Source-only approved root deliberately omits work: this is the real producer and actual reader rejection.
        var failure=assertThrows(PreparationRejectedException.class,()->ManualBuildCapacityReleaseProducer.prepare(request,
                Clock.fixed(observed.plusSeconds(10),ZoneOffset.UTC)));
        FileRef live=failure.retainedCandidate();live.verify();
        assertEquals(config.capacityRelease().toString(),live.path());
        byte[] candidate=Files.readAllBytes(config.capacityRelease());
        var bytes=new ByteArrayOutputStream();
        try(var output=new ObjectOutputStream(bytes)){output.writeObject(failure);}
        final PreparationRejectedException restored;
        try(var input=new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()))) {
            restored=assertInstanceOf(PreparationRejectedException.class,input.readObject());
        }
        assertEquals(failure.getMessage(),restored.getMessage());assertNotNull(restored.getCause());
        assertThrows(IllegalStateException.class,restored::retainedCandidate);
        assertSame(live,failure.retainedCandidate());live.verify();
        assertArrayEquals(candidate,Files.readAllBytes(config.capacityRelease()));
        // Recovery reacquires the actual file's existing pure3 contract; no FileRef is inferred from the exception message.
        assertEquals(live,FileRef.measure(config.capacityRelease()));
    }
}

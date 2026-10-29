package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Independent typed persisted forecast reader. Reuses the original price producer; grants no live assembly authority. */
public final class SdkSharedQuoteReader {
    private SdkSharedQuoteReader() { }
    public record Readback(String schema, String machineId, FileRef forecastRef, FileRef requestRef,
            long sharedSourceAllocationUpperBytes, long artifactSourceGateIncrementBytes, boolean metadataRecomputed,
            boolean actualSharedViewsQualified, boolean executionAuthorized) {
        public Readback {
            if (!"xar.sdk-source-cost-cold-read/v1".equals(schema) || machineId == null || !metadataRecomputed
                    || actualSharedViewsQualified || executionAuthorized) throw new IllegalArgumentException("Forecast metadata readback only");
        }
    }
    public static Readback read(FileRef forecastRef) throws IOException {
        if (forecastRef.bytes() < 1 || forecastRef.bytes() > 32768) throw new IOException("Finite exact forecast required");
        forecastRef.verify();
        var mapper = ControlBuild.strictMapper();
        var recorded = mapper.readValue(Files.readAllBytes(Path.of(forecastRef.path())), SdkSharedQuoteProducer.Forecast.class);
        FileRef requestRef = recorded.requestRef();
        if (requestRef.bytes() < 1 || requestRef.bytes() > 65536) throw new IOException("Finite exact forecast request required");
        requestRef.verify();
        var request = mapper.readValue(Files.readAllBytes(Path.of(requestRef.path())), SdkSharedQuoteProducer.Request.class);
        var actual = SdkSharedQuoteProducer.forecast(requestRef, request);
        if (!recorded.equals(actual)) throw new IOException("Persisted forecast differs from the same pinned metadata and original price algorithm");
        forecastRef.verify(); requestRef.verify();
        return new Readback("xar.sdk-source-cost-cold-read/v1", recorded.machineId(), forecastRef, requestRef,
                recorded.sharedSourceAllocationUpperBytes(), recorded.artifactSourceGateIncrementBytes(), true, false, false);
    }
    public static void main(String[] args) throws IOException {
        if (args.length != 3 || !args[1].matches("[1-9][0-9]{0,8}"))
            throw new IllegalArgumentException("FORECAST_PATH EXACT_BYTES SHA256 required");
        System.out.println(ControlBuild.strictMapper().writeValueAsString(read(new FileRef(args[0], Long.parseLong(args[1]), args[2]))));
    }
}


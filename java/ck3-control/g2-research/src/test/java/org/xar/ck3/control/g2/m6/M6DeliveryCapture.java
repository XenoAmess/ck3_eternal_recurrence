package org.xar.ck3.control.g2.m6;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** One finite capture of the new actual Java producer/domain/wire path for the host test. */
public final class M6DeliveryCapture {
    private static final String ORIGINAL_SHA = "edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580";
    private M6DeliveryCapture() { }

    public record CaptureReceipt(String schema, @JsonProperty("machine_id") String machineId,
            @JsonProperty("observed_at_utc") String observedAtUtc, ExactRef originalLedger, ExactRef ordinaryStart,
            ExactRef packet,
            ExactRef request, ExactRef expectedResult, ExactRef expectedResponse, boolean gameStarted,
            boolean ledgerCommitted, boolean wholeM6Complete) { }

    public static void main(String[] arguments) throws IOException, NoSuchAlgorithmException {
        if (arguments.length != 4) { throw new IllegalArgumentException("exact original ledger, exact original ordinary AUTO, new output directory and machine ID required"); }
        Path input = Path.of(arguments[0]).toRealPath();
        byte[] original = Files.readAllBytes(input);
        StrictJson.require(original.length == 21864 && sha(original).equals(ORIGINAL_SHA), "the exact original closed M6 ledger is required");
        Path autoInput = Path.of(arguments[1]).toRealPath();
        byte[] ordinary = Files.readAllBytes(autoInput);
        StrictJson.require(ordinary.length == 87990 && sha(ordinary).equals(
                "44defd2b790131659d9dbd617b755b98d9d36820789bbc5e8248274152c93c24"), "exact original ordinary AUTO48 required");
        String observed = Instant.now().toString();
        byte[] packet = M6SourceProducer.encodeEvidencePacket(original, ref(input, original), ordinary,
                ref(autoInput, ordinary), new M6SourceProducer.OrdinaryStartBinding(31254, "native-31254-6271ac8cd441", 214568));
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        Files.createDirectories(output);
        Path packetFile = output.resolve("M6.payload.json");
        Files.write(packetFile, packet, StandardOpenOption.CREATE_NEW);
        G2Source source = new G2Source(arguments[3], observed, M6SourceProducer.BUILD, ref(packetFile, packet));
        G2Request request = new G2Request("m6-original-host", Milestone.M6, source,
                ProjectionJson.object(packet, M6SourceProducer.MAX_BYTES));
        StrictJson.require(java.util.Arrays.equals(packet, G2Wire.decodeRequest(G2Wire.encodeRequest(request)).payload().bytes()),
                "compact evidence packet transport changed its exact source bytes");
        var response = new M6Research().evaluate(G2Wire.decodeRequest(G2Wire.encodeRequest(request)));
        byte[] resultBytes = response.result().bytes();
        StrictJson.require(!StrictJson.parse(resultBytes).get("whole_m6_complete").booleanValue(), "original ledger cannot complete M6");
        byte[] responseBytes = G2Wire.encodeResponse(response);
        StrictJson.require(java.util.Arrays.equals(G2Wire.decodeResponse(responseBytes).result().bytes(), resultBytes), "host result wire roundtrip differs");
        Path requestFile = output.resolve("M6.request.json");
        Path resultFile = output.resolve("M6.expected-result.json");
        Path responseFile = output.resolve("M6.expected-response.json");
        byte[] requestBytes = G2Wire.encodeRequest(request);
        Files.write(requestFile, requestBytes, StandardOpenOption.CREATE_NEW);
        Files.write(resultFile, resultBytes, StandardOpenOption.CREATE_NEW);
        Files.write(responseFile, responseBytes, StandardOpenOption.CREATE_NEW);
        CaptureReceipt receipt = new CaptureReceipt("xar.g2.m6.actual-host-capture/v1", arguments[3], observed,
                ref(input, original), ref(autoInput, ordinary), ref(packetFile, packet),
                ref(requestFile, requestBytes), ref(resultFile, resultBytes), ref(responseFile, responseBytes),
                false, false, false);
        Files.write(output.resolve("M6-CAPTURE-ACTUAL01.json"), new ObjectMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(receipt),
                StandardOpenOption.CREATE_NEW);
    }

    private static ExactRef ref(Path path, byte[] raw) throws NoSuchAlgorithmException {
        return new ExactRef(path.toString(), raw.length, sha(raw));
    }
    private static String sha(byte[] raw) throws NoSuchAlgorithmException {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}

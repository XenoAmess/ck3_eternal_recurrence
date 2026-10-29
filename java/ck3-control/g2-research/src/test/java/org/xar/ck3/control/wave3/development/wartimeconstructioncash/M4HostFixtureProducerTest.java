package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.m4.M4Research;
import static org.junit.jupiter.api.Assertions.*;

/** Uses the actual shared producer/domain path; optional export is consumed by the common host suite. */
public final class M4HostFixtureProducerTest {
    private record Artifact(String name, byte[] utf8) { }

    @Test public void actualOriginalProducerDomainAndMalformedQuoteSupplyHostArtifacts() throws Exception {
        G2Source source = originalSource();
        M4HostFixtureProducer.Fixture fixture = M4HostFixtureProducer.produce(source);
        byte[] request = fixture.requestUtf8(), expected = fixture.expectedResultUtf8();
        byte[] response = fixture.responseUtf8(), refused = fixture.refusedRequestUtf8();
        assertEquals(source, G2Wire.decodeRequest(request).source());
        assertEquals(source, G2Wire.decodeResponse(response).source());
        assertArrayEquals(expected, G2Wire.decodeResponse(response).result().bytes());
        assertArrayEquals(expected, new M4Research().evaluate(G2Wire.decodeRequest(request)).result().bytes());
        assertThrows(IllegalArgumentException.class,
                () -> new M4Research().evaluate(G2Wire.decodeRequest(refused)));
        assertEquals(source, G2Wire.decodeRequest(refused).source());

        String outputValue = System.getProperty("xar.m4.hostFixtureOutput");
        if (outputValue == null) return;
        assertNotEquals("synthetic-test-machine", source.machineId(), "export requires the observed execution machine");
        String rootValue = System.getProperty("xar.m4.hostFixtureRoot");
        assertNotNull(rootValue, "the admitted build root must be explicit");
        Path root = Path.of(rootValue).toRealPath();
        Path output = Path.of(outputValue).toAbsolutePath().normalize();
        assertTrue(output.startsWith(root) && !output.equals(root), "output must stay inside the admitted root");
        assertTrue(Files.notExists(output, LinkOption.NOFOLLOW_LINKS), "fresh artifact output must not already exist");
        assertEquals(output.getParent(), output.getParent().toRealPath(), "artifact parent must be an existing real run directory");
        Files.createDirectory(output);
        assertEquals(output, output.toRealPath(), "output cannot traverse a link or alias");
        List<Artifact> artifacts = List.of(new Artifact("M4.request.json", request),
                new Artifact("M4.expected-result.json", expected), new Artifact("M4.response.json", response),
                new Artifact("M4.refused-request.json", refused));
        ObjectNode pins = StrictJson.object();
        pins.put("schema", "xar.g2-m4-host-fixture-pins.v1");
        pins.put("machine_id", source.machineId());
        pins.put("observed_at_utc", source.observedAtUtc());
        pins.put("synthetic", true);
        pins.put("exact_build", source.exactBuild());
        pins.put("scope", "Actual original31 corpus -> typed producer -> G2Wire -> M4Research; no live frame, native query, wallet, project or game qualification.");
        ObjectNode sourcePin = pins.putObject("source_ref");
        sourcePin.put("path", source.sourceRef().path());
        sourcePin.put("bytes", source.sourceRef().bytes());
        sourcePin.put("sha256", source.sourceRef().sha256());
        var refs = pins.putArray("artifacts");
        for (Artifact artifact : artifacts) {
            Path file = output.resolve(artifact.name());
            Files.write(file, artifact.utf8(), StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            byte[] readback = Files.readAllBytes(file);
            assertArrayEquals(artifact.utf8(), readback);
            ObjectNode ref = refs.addObject();
            ref.put("path", file.toString());
            ref.put("bytes", readback.length);
            ref.put("sha256", sha256(readback));
        }
        // Verify the exported files themselves through the common wire/domain, not just the in-memory values.
        assertArrayEquals(Files.readAllBytes(output.resolve("M4.expected-result.json")), new M4Research()
                .evaluate(G2Wire.decodeRequest(Files.readAllBytes(output.resolve("M4.request.json")))).result().bytes());
        assertArrayEquals(Files.readAllBytes(output.resolve("M4.expected-result.json")), G2Wire.decodeResponse(
                Files.readAllBytes(output.resolve("M4.response.json"))).result().bytes());
        assertThrows(IllegalArgumentException.class, () -> new M4Research().evaluate(
                G2Wire.decodeRequest(Files.readAllBytes(output.resolve("M4.refused-request.json")))));
        byte[] pinBytes = M4OriginalCorpus.wire(pins);
        Path pinFile = output.resolve("M4.fixture-pins.json");
        Files.write(pinFile, pinBytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        assertArrayEquals(pinBytes, Files.readAllBytes(pinFile));
    }

    @Test public void changedOriginalCorpusDigestCannotProduceAnAcceptedHostFixture() throws Exception {
        G2Source source = originalSource();
        ExactRef changed = new ExactRef(source.sourceRef().path(), source.sourceRef().bytes(), "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> M4HostFixtureProducer.produce(
                new G2Source(source.machineId(), source.observedAtUtc(), source.exactBuild(), changed)));
    }

    @Test public void changedOriginalCorpusLengthCannotProduceAnAcceptedHostFixture() throws Exception {
        G2Source source = originalSource();
        ExactRef changed = new ExactRef(source.sourceRef().path(), source.sourceRef().bytes() + 1,
                source.sourceRef().sha256());
        assertThrows(IllegalArgumentException.class, () -> M4HostFixtureProducer.produce(
                new G2Source(source.machineId(), source.observedAtUtc(), source.exactBuild(), changed)));
    }

    private static G2Source originalSource() throws Exception {
        URL resource = M4HostFixtureProducerTest.class.getResource("/m4producer/wartime-original02.json.gz");
        assertNotNull(resource, "the actual original31 corpus is required");
        Path corpus = Path.of(resource.toURI()).toRealPath();
        byte[] original = Files.readAllBytes(corpus);
        assertEquals(6379, original.length);
        assertEquals(M4HostFixtureProducer.ORIGINAL_SHA256, sha256(original));
        return new G2Source(System.getProperty("xar.m4.fixture.machineId", "synthetic-test-machine"),
                Instant.now().toString(), "synthetic-original31-corpus-not-live",
                new ExactRef(corpus.toString(), original.length, sha256(original)));
    }

    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }
}

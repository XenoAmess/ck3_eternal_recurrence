package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.build.SharedSourceFiles;

/** DATA and actual file continuity only: no ManagedGameSession or source qualification is constructed. */
final class RootArchivedNativeSourceReaderTest {
    @TempDir Path temporary;
    private static final String MACHINE = "software-data-machine";
    private static final String SESSION = "software-data-session";
    private static final List<String> ROLES = List.of("bridge_dll", "game_executable", "injector",
            "java_runtime", "launcher_settings", "native_source");

    private record Fixture(ObjectNode epoch, byte[] epochBytes, NativeSourceProofDocument proof) { }

    @Test void actualProducerCodecFeedsReaderAndCompleteEpochWithoutLiveGuard() throws IOException {
        Fixture fixture = fixture();
        byte[] produced = NativeSourceProofCodec.encode(fixture.proof());
        var decoded = RootArchivedNativeSourceReader.readData(reference("proof.json", produced), produced);
        assertEquals(fixture.proof(), decoded);
        var epoch = RootArchivedNativeSourceReader.readEpochData(decoded.sourceEpochManifest(), fixture.epochBytes(), decoded);
        assertEquals(MACHINE, epoch.machineId());
        assertEquals(6, epoch.inputs().size());
        assertEquals("340282366920938463463374607431768211455", decoded.liveWitnesses().getFirst().nativeFile().fileIdDecimal());
        assertEquals("18446744073709551615", decoded.liveWitnesses().getFirst().nativeFile().creationFiletimeDecimal());
    }

    @Test void legacyV2CannotAcquireHistoricalWitnessesFromMatchingContent() throws IOException {
        byte[] v3 = NativeSourceProofCodec.encode(fixture().proof());
        byte[] legacy = new String(v3, StandardCharsets.UTF_8)
                .replace(NativeSourceProofDocument.SCHEMA, "xar.java-root-native-source-proof/v2")
                .getBytes(StandardCharsets.UTF_8);
        assertThrows(IOException.class, () -> RootArchivedNativeSourceReader.readData(reference("v2.json", legacy), legacy));
    }

    @Test void epochCannotBorrowMissingPhysicalWitnessEvenWithSameReferenceHash() {
        Fixture fixture = fixture();
        var selected = fixture.proof().liveWitnesses().stream()
                .filter(witness -> !witness.source().path().endsWith("bridge_dll.bin")).toList();
        NativeSourceProofDocument incomplete = copy(fixture.proof(), fixture.proof().sourceEpochManifest(),
                List.of(fixture.proof().gameExecutable()), selected);
        assertThrows(ContractViolationException.class, () -> RootArchivedNativeSourceReader.readEpochData(
                incomplete.sourceEpochManifest(), fixture.epochBytes(), incomplete));
    }

    @Test void epochDecoderRejectsWrongMachineUnknownRoleOrderAndUnknownFields() {
        Fixture fixture = fixture();
        ObjectNode wrongMachine = fixture.epoch().deepCopy().put("machine_id", "another-machine");
        rejectEpoch(fixture, wrongMachine);
        ObjectNode unknownRole = fixture.epoch().deepCopy();
        ((ObjectNode) unknownRole.withArray("inputs").get(0)).put("role", "reconstructed_runtime");
        rejectEpoch(fixture, unknownRole);
        ObjectNode duplicate = fixture.epoch().deepCopy();
        duplicate.withArray("inputs").add(duplicate.withArray("inputs").get(0).deepCopy());
        rejectEpoch(fixture, duplicate);
        ObjectNode extra = fixture.epoch().deepCopy().put("live_guard_passed", true);
        rejectEpoch(fixture, extra);
    }

    @Test void sourceAndEpochExactReferencesRemainRequiredBeforeDecoding() throws IOException {
        Fixture fixture = fixture();
        byte[] produced = NativeSourceProofCodec.encode(fixture.proof());
        ExactRef unrelated = new ExactRef("D:/software-data/other.json", produced.length, "0".repeat(64));
        assertThrows(ContractViolationException.class, () -> RootArchivedNativeSourceReader.readData(unrelated, produced));
        ExactRef old = fixture.proof().sourceEpochManifest();
        ExactRef another = new ExactRef(old.path(), old.bytes(), "0".repeat(64));
        assertThrows(ContractViolationException.class, () -> RootArchivedNativeSourceReader.readEpochData(
                another, fixture.epochBytes(), fixture.proof()));
    }

    @Test void sourceReaderUsesStrictWitnessWireRatherThanJsonNumericCoercions() throws IOException {
        byte[] produced = NativeSourceProofCodec.encode(fixture().proof());
        for (String invalid : List.of("true", "1.0", "1", "null")) {
            String input = new String(produced, StandardCharsets.UTF_8)
                    .replace("\"file_id_decimal\":\"340282366920938463463374607431768211455\"",
                            "\"file_id_decimal\":" + invalid);
            byte[] changed = input.getBytes(StandardCharsets.UTF_8);
            assertThrows(IOException.class, () -> RootArchivedNativeSourceReader.readData(reference("malformed.json", changed), changed));
        }
    }

    @Test void sameBytesInAReplacementFileCannotRecoverTheOriginalNativeIdentity() throws IOException {
        Path original = temporary.resolve("actual-source.bin").toAbsolutePath();
        byte[] content = "actual physical witness continuity".getBytes(StandardCharsets.UTF_8);
        Files.write(original, content);
        SharedSourceFiles.Witness actual = SharedSourceFiles.observe(original);
        ExactRef source = new ExactRef(actual.source().path(), actual.source().bytes(), actual.source().sha256());
        SourceWitness witness = RootNativeSourceProofProducer.persistWitnesses(List.of(actual)).getFirst();
        Fixture template = fixture();
        NativeSourceProofDocument proof = new NativeSourceProofDocument(MACHINE, SESSION, template.proof().observedAtUtc(),
                template.proof().mode(), source, template.proof().source(), template.proof().ownerSourceEpoch(),
                template.proof().sourceEpochManifest(), source, List.of(source), List.of(witness));
        byte[] produced = NativeSourceProofCodec.encode(proof);
        NativeSourceProofDocument decoded = RootArchivedNativeSourceReader.readData(reference("physical-proof.json", produced), produced);
        RootArchivedNativeSourceReader.requireOriginalFiles(decoded);
        Path replacement = temporary.resolve("private-replacement.bin").toAbsolutePath();
        Files.write(replacement, content);
        Files.move(replacement, original, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        assertEquals(source.sha256(), SharedSourceFiles.observe(original).source().sha256());
        RootArchivedNativeSourceReader.requireOriginalFiles(decoded);
    }

    private static void rejectEpoch(Fixture fixture, ObjectNode changed) {
        byte[] raw = StrictJson.canonical(changed);
        ExactRef ref = reference("epoch.json", raw);
        NativeSourceProofDocument updated = copy(fixture.proof(), ref,
                fixture.proof().completeEvidenceClosure(), fixture.proof().liveWitnesses());
        assertThrows(IllegalArgumentException.class, () -> RootArchivedNativeSourceReader.readEpochData(ref, raw, updated));
    }

    private static Fixture fixture() {
        List<ExactRef> sources = new ArrayList<>();
        ObjectNode epoch = StrictJson.object().put("schema", "xar.java-root-source-epoch/v1").put("machine_id", MACHINE);
        var inputs = epoch.putArray("inputs");
        for (String role : ROLES) {
            ExactRef source = reference(role + ".bin", role.getBytes(StandardCharsets.UTF_8)); sources.add(source);
            ObjectNode row = inputs.addObject().put("role", role); row.set("source", source.toJson());
        }
        byte[] epochBytes = StrictJson.canonical(epoch);
        ExactRef epochRef = reference("epoch.json", epochBytes);
        ExactRef host = reference("host.json", "host".getBytes(StandardCharsets.UTF_8));
        List<SourceWitness> witnesses = new ArrayList<>();
        for (ExactRef source : sources) witnesses.add(witness(source));
        witnesses.add(witness(host));
        witnesses.sort(Comparator.comparing(value -> value.source().path()));
        var proof = new NativeSourceProofDocument(MACHINE, SESSION, "2026-10-24T18:00:00Z",
                NativeSourceProofDocument.Mode.HTTP, host, reference("origin.json", new byte[] {1}), epochRef.sha256(),
                epochRef, sources.get(1), sources, witnesses);
        return new Fixture(epoch, epochBytes, proof);
    }

    private static SourceWitness witness(ExactRef source) {
        String name = source.path().substring(source.path().lastIndexOf('/') + 1);
        int index = ROLES.indexOf(name.replace(".bin", ""));
        if (index < 0) index = ROLES.size();
        BigInteger id = new BigInteger("340282366920938463463374607431768211455").subtract(BigInteger.valueOf(index));
        String legacy = String.format("%016x", id.and(new BigInteger("18446744073709551615")).longValue());
        return new SourceWitness(source, new NativeSourceFileIdentity("18446744073709551615",
                id.toString(), "4294967295", legacy,
                "18446744073709551615", "18446744073709551614", "18446744073709551613",
                source.bytes(), 4096, 1));
    }

    private static ExactRef reference(String name, byte[] bytes) {
        return new ExactRef("d:/software-data/" + name, bytes.length, DriverJson.sha256(bytes));
    }

    private static NativeSourceProofDocument copy(NativeSourceProofDocument original, ExactRef epoch,
            List<ExactRef> closure, List<SourceWitness> witnesses) {
        return new NativeSourceProofDocument(original.machineId(), original.sessionId(), original.observedAtUtc(),
                original.mode(), original.hostConfiguration(), original.source(), epoch.sha256(), epoch,
                original.gameExecutable(), closure, witnesses);
    }
}

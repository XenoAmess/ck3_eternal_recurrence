package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;

/** Source DATA has its own exact physical reader; all Driver/effect artifacts retain the canonical archive domain. */
final class RootOriginalArtifacts {
    private RootOriginalArtifacts() { }
    static byte[] read(ContinuityWriter writer, NativeOutcomeArchive archive, ContinuityStorePort.Session borrowed,
            ExactRef reference, int maximum, ExactRef originalSourceData) throws IOException {
        writer.requireSession(borrowed);
        int supported = Math.min(maximum, ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
        if (supported < 1 || reference.bytes() > supported) throw new IOException("original artifact exceeds the actual immutable/source byte boundary");
        if (!reference.equals(originalSourceData)) return archive.readArtifact(borrowed, reference, supported);
        // This branch admits only the caller's single exact G2 source DATA reference. It grants no executable-source qualification.
        WriterContracts.Pin pin = borrowed.capturePin(originalSourceData, supported);
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(originalSourceData.path()))) { bytes = input.readNBytes(supported + 1); }
        if (bytes.length != originalSourceData.bytes() || !sha(bytes).equals(originalSourceData.sha256()))
            throw new IOException("original G2 source DATA bytes changed during its dedicated read");
        borrowed.verifyPin(pin); return bytes;
    }
    /** Only the lifecycle issuer's private actual replacement may identify external managed launch/hello/lifecycle originals. */
    static byte[] readNext(ContinuityWriter writer, NativeOutcomeArchive archive, ContinuityStorePort.Session borrowed,
            ExactRef reference, int maximum, ExactRef originalSourceData,
            org.xar.ck3.control.application.lifecycle.LifecycleComposites.NextEpisodeAdoption actual,
            org.xar.ck3.control.application.driver.DriverCapabilityRuntime candidate,
            org.xar.ck3.control.application.driver.DriverStateAssembler sameAuthority) throws IOException {
        writer.requireSession(borrowed); candidate.requireNextCandidate(borrowed, actual, sameAuthority);
        var replacement = actual.replacement();
        if (!java.util.List.of(replacement.launchEvidence(), replacement.helloEvidence(), replacement.lifecycleEvidence()).contains(reference))
            return read(writer, archive, borrowed, reference, maximum, originalSourceData);
        int supported = Math.min(maximum, WriterContracts.MAX_PIN_BYTES);
        if (supported < 1 || reference.bytes() > supported) throw new IOException("managed replacement original exceeds its qualified physical pin lane");
        WriterContracts.Pin pin = borrowed.capturePin(reference, supported);
        byte[] bytes = borrowed.readPinned(pin, supported); borrowed.verifyPin(pin);
        candidate.requireNextCandidate(borrowed, actual, sameAuthority); return bytes;
    }
    private static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}

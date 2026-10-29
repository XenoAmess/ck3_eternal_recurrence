package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity;
import org.xar.ck3.control.application.readiness.NativeSourceFileIdentity.SourceWitness;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.NativeProof;
import org.xar.ck3.control.contracts.ExactRef;

/** Persists only the actual witnesses acquired by the sole physical source authority. */
final class RootNativeSourceProofProducer {
    private RootNativeSourceProofProducer() { }

    static NativeSourceProofDocument document(SessionIdentity identity, String observedAtUtc,
            NativeProof proof, FileRef hostConfiguration, ExactRef source, ExactRef epochManifest,
            List<SharedSourceFiles.Witness> actualLiveWitnesses) throws IOException {
        Objects.requireNonNull(identity); Objects.requireNonNull(proof);
        if (!identity.machineId().equals(proof.machineId()))
            throw new IOException("actual source proof machine differs from original transport");
        try {
            return new NativeSourceProofDocument(identity.machineId(), identity.sessionId(), observedAtUtc,
                    mode(proof.mode()), exact(hostConfiguration), source,
                    epochManifest.sha256(), epochManifest, exact(proof.expected().gameExecutable()),
                    proof.completeEvidenceClosure().stream().map(RootNativeSourceProofProducer::exact).toList(),
                    persistWitnesses(actualLiveWitnesses));
        } catch (IllegalArgumentException error) {
            throw new IOException("actual source witnesses do not close the original proof", error);
        }
    }

    /** Exhaustive shared-mode join; an added HostMode requires an explicit producer migration. */
    private static NativeSourceProofDocument.Mode mode(HostMode actual) {
        return switch (actual) {
            case HTTP -> NativeSourceProofDocument.Mode.HTTP;
            case MCP_STDIO -> NativeSourceProofDocument.Mode.MCP_STDIO;
            case COMPLETE_MIGRATION -> NativeSourceProofDocument.Mode.COMPLETE_MIGRATION;
        };
    }

    /** DATA conversion never reobserves a path or synthesizes identity from a content hash. */
    static List<SourceWitness> persistWitnesses(List<SharedSourceFiles.Witness> originals) throws IOException {
        LinkedHashMap<String, SourceWitness> retained = new LinkedHashMap<>();
        for (SharedSourceFiles.Witness original : List.copyOf(originals)) {
            SharedSourceFiles.NativeFile physical = original.nativeFile();
            SourceWitness current;
            try {
                current = new SourceWitness(exact(original.source()), new NativeSourceFileIdentity(
                        physical.volumeSerialDecimal(), physical.fileIdDecimal(), physical.legacyVolumeSerialDecimal(),
                        physical.legacyFileIdHex(), physical.creationFiletimeDecimal(), physical.lastWriteFiletimeDecimal(),
                        physical.changeFiletimeDecimal(), physical.logicalBytes(), physical.allocatedBytes(), physical.linkCount()));
            } catch (IllegalArgumentException error) {
                throw new IOException("original native witness is outside its durable contract", error);
            }
            String path = NativeSourceProofDocument.pathKey(current.source().path());
            SourceWitness previous = retained.putIfAbsent(path, current);
            if (previous != null && !previous.sameImmutableFile(current))
                throw new IOException("actual native witness path has conflicting original identity or content");
        }
        if (retained.isEmpty()) throw new IOException("actual live Witnesses absent; old v2 proof cannot acquire them");
        return List.copyOf(retained.values());
    }

    private static ExactRef exact(FileRef source) { return new ExactRef(source.path(), source.bytes(), source.sha256()); }
}

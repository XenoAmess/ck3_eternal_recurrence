package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Publishes only the exact typed SDK publication request DATA.
 * Historical issuer cards, census, capacity, binding/declaration files and machine/date freshness do not gate this DATA.
 * The outputBindingRef is passive historical DATA and is not opened or treated as authority. */
public final class RootRuntimeDefinitionsPublicationRequestProducer {
    public static final int MAXIMUM_BYTES = RootRuntimeDefinitionsPublisher.MAXIMUM_REQUEST_BYTES;
    private RootRuntimeDefinitionsPublicationRequestProducer() { }

    /** Pure unique-codec preparation. A retained Request is DATA, never a proof of its configured inputs. */
    public static Prepared prepare(RootRuntimeDefinitionsPublisher.Request actualRequest) throws IOException {
        Objects.requireNonNull(actualRequest, "actual typed publication Request is required; no default configuration");
        byte[] bytes = RootRuntimeDefinitionsPublisher.encodeRequest(actualRequest);
        require(bytes.length > 0 && bytes.length <= MAXIMUM_BYTES && bytes.length <= (1 << 20),
                "publication request exceeds the original bootstrap 1MiB leaf bound");
        require(actualRequest.equals(RootRuntimeDefinitionsPublisher.decodeRequest(bytes)),
                "sole SDK publication request roundtrip changed");
        return new Prepared(actualRequest, bytes);
    }

    public static final class Prepared {
        private final RootRuntimeDefinitionsPublisher.Request request;
        private final byte[] bytes;
        private Prepared(RootRuntimeDefinitionsPublisher.Request request, byte[] bytes) {
            this.request = request; this.bytes = bytes.clone();
        }
        public RootRuntimeDefinitionsPublisher.Request request() { return request; }
        public byte[] bytes() { return bytes.clone(); }
        public RootBootstrapOutputContract.Output quote(Path target) {
            normalized(target);
            return new RootBootstrapOutputContract.Output(
                    RootBootstrapOutputContract.Kind.RUNTIME_DEFINITIONS_PUBLICATION_REQUEST,
                    target.getFileName().toString(), bytes.length, DriverJson.sha256(bytes));
        }

        /** Compatibility entrypoint: delegates to direct publish, ignoring the FileRef authority. */
        public Published publish(FileRef actualRequestOutputBinding, Path target, Clock clock) throws IOException {
            return publish(target, clock);
        }

        /** Direct publish: validates target, writes CREATE_NEW, reads back, decodes, returns witness. */
        public Published publish(Path target, Clock clock) throws IOException {
            Objects.requireNonNull(clock);
            normalized(target);
            
            // Reject target aliasing request.target or the passive request.outputBindingRef path
            require(!target.equals(Path.of(request.target())), "request target aliases its own Definitions target");
            require(!target.equals(Path.of(request.outputBindingRef().path())), "request target aliases passive outputBindingRef");
            
            // Write only CREATE_NEW
            Files.write(target, bytes, java.nio.file.StandardOpenOption.CREATE_NEW);
            
            // Bounded-read exact bytes and decode with unique existing codec
            var physical = new FileRef(target.toString(), bytes.length, DriverJson.sha256(bytes));
            byte[] actual = readBounded(physical);
            require(Arrays.equals(bytes, actual), "published request differs from the exact SDK typed producer");
            require(request.equals(RootRuntimeDefinitionsPublisher.decodeRequest(actual)), "sole-codec roundtrip changed");
            
            // Return the actual emitted original/witness for reporting
            var witness = SharedSourceFiles.observe(target);
            require(witness.source().equals(physical), "emitted request report differs from its actual bytes");
            return new Published(this, physical, witness);
        }
    }

    /** Actual CREATE_NEW/readback DATA and its one publication-time report; this is not runtime permission. */
    public static final class Published {
        private final Prepared prepared;
        private final FileRef original;
        private final SharedSourceFiles.Witness witness;
        private Published(Prepared prepared, FileRef original, SharedSourceFiles.Witness witness) {
            this.prepared = prepared; this.original = original; this.witness = witness;
        }
        public FileRef original() { return original; }
        public SharedSourceFiles.Witness actualWitness() { return witness; }
        
        /** Bounded-read/decode its own actual DATA and compare with prepared Request, without native identity or historical card checks. */
        public RootRuntimeDefinitionsPublisher.Request readExact(Clock clock) throws IOException {
            Objects.requireNonNull(clock);
            byte[] actual = readBounded(original);
            var decoded = RootRuntimeDefinitionsPublisher.decodeRequest(actual);
            require(prepared.request.equals(decoded), "actual publication request changed its retained SDK value");
            return decoded;
        }
        
        /** Definitions execution remains its separate existing consumer. */
        public RootRuntimeDefinitionsPublisher.Published execute(Clock clock) throws IOException {
            readExact(clock);
            var result = RootRuntimeDefinitionsPublisher.execute(original, clock);
            return result;
        }
    }

    private static byte[] readBounded(FileRef reference) throws IOException {
        Objects.requireNonNull(reference);
        require(reference.bytes() > 0 && reference.bytes() <= MAXIMUM_BYTES, "bounded nonempty request DATA required");
        try (var input = Files.newInputStream(Path.of(reference.path()))) {
            byte[] bytes = input.readNBytes(Math.addExact(MAXIMUM_BYTES, 1));
            require(bytes.length == reference.bytes() && bytes.length <= MAXIMUM_BYTES
                    && DriverJson.sha256(bytes).equalsIgnoreCase(reference.sha256()), "publication request DATA changed");
            return bytes;
        }
    }

    private static void normalized(Path target) {
        Objects.requireNonNull(target);
        if (!target.isAbsolute() || !target.equals(target.normalize()) || target.getParent() == null || target.getFileName() == null)
            throw new IllegalArgumentException("exact absolute normalized file target required");
    }
    private static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}
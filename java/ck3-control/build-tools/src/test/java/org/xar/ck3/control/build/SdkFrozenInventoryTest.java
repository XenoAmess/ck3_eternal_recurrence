package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.LinkOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.FileTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SdkSourceAssembly.*;

/** Actual filesystem inventory/reuse guards; no SDK import or runtime qualification. */
final class SdkFrozenInventoryTest {
    @TempDir Path temporary;
    private record Fixture(Path root, Path source, SharedSourceFiles.Witness original, Request request) {
        Map<String, SharedSourceFiles.Witness> witnesses() { return Map.of("source.py", original); }
    }
    private Fixture fixture() throws IOException {
        Path root = Files.createDirectory(temporary.resolve("sdk"));
        Path source = Files.writeString(root.resolve("source.py"), "original source\n");
        Path producer = Files.writeString(temporary.resolve("producer.py"), "fixture producer\n");
        String sdk = "ck3_autonomous_player/src", producerName = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
        var request = new Request(SdkSourceAssembly.REQUEST_SCHEMA, "fixture-machine", temporary.toString(), "1".repeat(40), temporary.toString(), temporary.resolve("new-graph").toString(),
                root.toString(), sdk, List.of(".", sdk), List.of(temporary.toString()),
                List.of(new ProtectedRoot(ProtectedRole.FROZEN_SDK, root.toString()), new ProtectedRoot(ProtectedRole.FROZEN_HOST, temporary.resolve("host").toString()), new ProtectedRoot(ProtectedRole.FROZEN_RUNTIME, temporary.resolve("runtime").toString())),
                List.of(new Source(sdk + "/source.py", SourceRole.SDK_SOURCE, InputOrigin.CURRENT_CANONICAL, FileRef.measure(source), List.of()), new Source(producerName, SourceRole.PRODUCER, InputOrigin.CURRENT_CANONICAL, FileRef.measure(producer), List.of())),
                List.of(new ImportRoute("sdk_source", sdk + "/source.py", ImportSourceLocation.FRESH_GRAPH, true)),
                List.of(new Deployment("fixture", FileRef.measure(producer), ControlBuild.TargetKind.SERVICE_FAST_JAR)),
                new ProducerReuse(producerName, "tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1", "compose_v1", "tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", "validate_current_saved_cold_owner_v1"), 1 << 20);
        return new Fixture(root, source, SharedSourceFiles.observe(source), request);
    }
    @Test void declaredCachesAreExcludedByBothInventoryAndFrozenReuseAndRemainUntouched() throws Exception {
        Fixture f = fixture(); var before = SdkSourceAssembly.completeSdkInventory(f.request());
        List<SharedSourceFiles.Witness> caches = new ArrayList<>();
        for (Path parent : List.of(f.root(), f.root().resolve("nested"))) {
            for (String name : List.of("__pycache__", ".mypy_cache", ".pytest_cache")) {
                Path cache = Files.createDirectories(parent.resolve(name));
                caches.add(SharedSourceFiles.observe(Files.writeString(cache.resolve("opaque.pyc"), "existing cache\n")));
                caches.add(SharedSourceFiles.observe(Files.writeString(cache.resolve("ordinary.py"), "cache directory data\n")));
            }
        }
        var mapper = ControlBuild.strictMapper();
        Request roundTripRequest = mapper.readValue(mapper.writeValueAsBytes(f.request()), Request.class);
        SdkInventory roundTripInventory = mapper.readValue(mapper.writeValueAsBytes(before), SdkInventory.class);
        assertEquals(before, roundTripInventory);
        assertEquals(before, SdkSourceAssembly.completeSdkInventory(f.request()));
        assertEquals(before, SdkSourceAssembly.completeSdkInventory(roundTripRequest));
        SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses());
        for (SharedSourceFiles.Witness cache : caches) {
            SharedSourceFiles.assertUnchanged(cache);
            assertEquals(cache.nativeFile(), SharedSourceFiles.nativeFile(Path.of(cache.source().path())));
        }
        SharedSourceFiles.assertUnchanged(f.original());
    }
    @Test void anExtraOrdinarySourceRemainsRejectedByBothConsumers() throws Exception {
        Fixture f = fixture();
        for (Path extra : List.of(f.root().resolve("extra.py"), f.root().resolve("__pycache__-ordinary/source.py"))) {
            Files.createDirectories(extra.getParent()); Files.writeString(extra, "unrecorded\n");
            assertThrows(IOException.class, () -> SdkSourceAssembly.completeSdkInventory(f.request()));
            assertThrows(IOException.class, () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses()));
            Files.delete(extra);
        }
        SharedSourceFiles.assertUnchanged(f.original());
    }
    @Test void missingOriginalSourceRemainsRejected() throws Exception {
        Fixture f = fixture(); Files.delete(f.source());
        assertThrows(IOException.class, () -> SdkSourceAssembly.completeSdkInventory(f.request()));
        assertThrows(IOException.class, () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses()));
    }
    @Test void contentDriftAndSameBytesAtANewNativeIdentityRemainRejected() throws Exception {
        Fixture f = fixture(); Files.writeString(f.source(), "changed source\n");
        assertThrows(IOException.class, () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses()));
        Files.move(f.source(), temporary.resolve("retired.py")); Files.writeString(f.source(), "original source\n");
        var replacement = SharedSourceFiles.observe(f.source());
        assertEquals(f.original().source().sha256(), replacement.source().sha256());
        assertNotEquals(f.original().nativeFile().identityKey(), replacement.nativeFile().identityKey());
        assertEquals(1, SdkSourceAssembly.completeSdkInventory(f.request()).originalFiles());
        assertThrows(IOException.class, () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses()));
    }
    @Test void compiledCacheSuffixesOutsideDeclaredDirectoriesRemainRejected() throws Exception {
        Fixture f = fixture();
        for (String suffix : List.of("pyc", "pyo")) {
            Path extra = Files.writeString(f.root().resolve("extra." + suffix), "unrecorded\n");
            assertThrows(IOException.class, () -> SdkSourceAssembly.completeSdkInventory(f.request()));
            assertThrows(IOException.class, () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses()));
            Files.delete(extra);
        }
    }
    @Test void syntheticNonordinaryMetadataInsideAnExcludedCacheRemainsRejectedByBothConsumers() throws Exception {
        Fixture f = fixture(); SdkInventory before = SdkSourceAssembly.completeSdkInventory(f.request());
        Path cache = Files.createDirectory(f.root().resolve("__pycache__"));
        Path rejected = Files.createDirectory(cache.resolve("redirect"));
        assertEquals(before, SdkSourceAssembly.completeSdkInventory(f.request()));
        SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses());
        for (boolean symbolic : List.of(false, true)) {
            AtomicInteger rejectedObservations = new AtomicInteger();
            SdkSourceAssembly.SourceEntryMetadata metadata = path -> {
                BasicFileAttributes actual = Files.readAttributes(path, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
                if (!path.equals(rejected)) return actual;
                assertTrue(actual.isDirectory()); assertFalse(actual.isSymbolicLink()); assertFalse(actual.isOther());
                // The real outer inventory runs during each injected observation and still sees only ordinary entries.
                ControlBuild.mutableInventoryBytes(temporary, ignored -> {});
                rejectedObservations.incrementAndGet();
                return new NonordinaryMetadata(actual, symbolic);
            };
            IOException inventory = assertThrows(IOException.class,
                    () -> SdkSourceAssembly.completeSdkInventory(f.request(), metadata));
            IOException reuse = assertThrows(IOException.class,
                    () -> SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses(), metadata));
            assertEquals("ordinary non-reparse SDK source entry required", inventory.getMessage());
            assertEquals(inventory.getMessage(), reuse.getMessage());
            assertEquals(2, rejectedObservations.get(), "both complete consumers must inspect the excluded entry");
            assertEquals(before, SdkSourceAssembly.completeSdkInventory(f.request()));
            SdkSourceAssembly.requireCurrentFrozenSources(f.root(), f.witnesses());
            SharedSourceFiles.assertUnchanged(f.original());
        }
    }
    private record NonordinaryMetadata(BasicFileAttributes original, boolean symbolic) implements BasicFileAttributes {
        @Override public FileTime lastModifiedTime() { return original.lastModifiedTime(); }
        @Override public FileTime lastAccessTime() { return original.lastAccessTime(); }
        @Override public FileTime creationTime() { return original.creationTime(); }
        @Override public boolean isRegularFile() { return false; }
        @Override public boolean isDirectory() { return false; }
        @Override public boolean isSymbolicLink() { return symbolic; }
        @Override public boolean isOther() { return !symbolic; }
        @Override public long size() { return original.size(); }
        @Override public Object fileKey() { return original.fileKey(); }
    }
}

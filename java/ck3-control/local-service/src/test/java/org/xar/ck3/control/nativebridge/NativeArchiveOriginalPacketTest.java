package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual shared archive reader; HELLO custody never becomes native/source qualification. */
final class NativeArchiveOriginalPacketTest {
    @TempDir Path root;
    @Test void ownedHelloAndSnapshotReadUnderActualSameWriterWithoutNativeRequest() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("roles"),false)){
            fixture.ready();var guard=fixture.lastNestedRead.get().before().binding();int writes=fixture.nativeReadWrites();byte[] ledger=fixture.ledgerBytes();
            fixture.writer.locked(session->fixture.archive.inSession(session,archive->{
                assertInstanceOf(NativeWire.Hello.class,assertDoesNotThrow(()->NativeWire.decode(archive.readOriginalPacket(guard.capabilityEvidence()))));
                assertInstanceOf(NativeWire.Snapshot.class,assertDoesNotThrow(()->NativeWire.decode(archive.readOriginalPacket(guard.nativeEvidence()))));return null;}));
            assertThrows(UncheckedIOException.class,()->fixture.archive.loadNativeFrame(guard.capabilityEvidence()));
            ExactRef json=fixture.archive.preserveMaterial(new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(UncheckedIOException.class,()->fixture.archive.readOriginalPacket(json));assertEquals(writes,fixture.nativeReadWrites());assertArrayEquals(ledger,fixture.ledgerBytes());
        }
    }
    @Test void sameBytesAtForeignLocatorAndChangedOwnedPacketRefuseWithoutRepair() throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("integrity"),false)){
            fixture.ready();var ref=fixture.lastNestedRead.get().before().binding().capabilityEvidence();Path copy=fixture.root.resolve("hello-copy.bin");Files.copy(Path.of(ref.path()),copy);
            var alias=new ExactRef(copy.toAbsolutePath().toString(),ref.bytes(),ref.sha256());
            assertThrows(UncheckedIOException.class,()->fixture.archive.readOriginalPacket(alias));
            byte[] damaged={0,0,0,0};Files.write(Path.of(ref.path()),damaged);
            assertThrows(UncheckedIOException.class,()->fixture.archive.readOriginalPacket(ref));assertArrayEquals(damaged,Files.readAllBytes(Path.of(ref.path())));assertEquals(0,fixture.nativeActionWrites());
        }
    }
}

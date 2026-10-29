package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.advance.FullAdvanceFrameFixture;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.nativebridge.NativeSnapshotWaitReceiverFixture;

/** Actual software endpoint/NGT/sole Held projection and real archive replay. These DATA samples grant no Root authority. */
final class HeldSampledSnapshotTest {
    @TempDir Path root;
    @Test void heldSampleRetainsActualPortPacketAndOldObservationTimeWithoutANativeReadOrQuery()throws Exception {
        try(var receiver=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState());
                var foreign=new NativeSnapshotWaitReceiverFixture(WaitForChangeDriverFixture.fullState())) {
            var accepted=receiver.transport().observe(Instant.now().plusSeconds(5));
            var held=WaitForChangeDriverFixture.receiver(receiver.transport(),Map.of(BigInteger.valueOf(7),BigInteger.valueOf(2)));
            int reads=receiver.actualReadCalls(),writes=receiver.actualWriteCalls();Instant began=Instant.now();
            var sampled=held.sampleCurrentFull(Instant.now().plusSeconds(5));
            sampled.sample().requirePort(receiver.transport());
            assertThrows(IOException.class,()->sampled.sample().requirePort(foreign.transport()));
            assertSame(sampled.sample().frame(),sampled.full().actual());
            assertEquals(accepted.observedAt(),sampled.full().actual().observedAt());
            assertEquals(ActionCodec.sha256(accepted.originalPacket()),sampled.full().originalEvidence().sha256());
            assertFalse(sampled.sample().startedAt().isBefore(began));
            assertFalse(sampled.sample().completedAt().isBefore(sampled.sample().startedAt()));
            assertEquals(reads,receiver.actualReadCalls());assertEquals(writes,receiver.actualWriteCalls());
            receiver.failActualSource("actual sampling source guard failed");
            assertThrows(IOException.class,()->held.sampleCurrentFull(Instant.now().plusSeconds(5)));
            assertEquals(writes,receiver.actualWriteCalls());
        }
    }
    @Test void fullLoaderReusesTheSameRetainedNativeDriverReaderAndStrictOrdinaryProjection()throws Exception {
        try(var produced=new FullAdvanceFrameFixture(root.resolve("full-loader"))) {
            byte[] ledger=produced.actual.ledgerBytes();int writes=produced.actual.nativeActionWrites();
            produced.actual.writer.locked(same->{
            var archive=produced.actual.archive.withSession(same);
            var evidence=produced.frame.semantic().get("java_driver_facts_evidence");
            var ref=org.xar.ck3.control.contracts.ExactRef.fromJson(DriverJson.toNode(evidence));
            var basis=new NativeEffectEvidence.FrameBasis(produced.frame.originalEvidence(),ref);
            var loader=new DriverFrameEvidenceLoader(produced.actual.physicalInputs().observationAssembler());
            var full=loader.loadFull(basis,archive);var ordinary=loader.load(basis,archive);
            assertEquals(produced.complete.identity(),ordinary.identity());
            assertEquals(produced.complete.semantic(),ordinary.semantic());
            assertEquals(produced.frame.originalEvidence(),full.originalEvidence());
            assertArrayEquals(full.actual().originalPacket(),archive.loadNativeFrame(basis.nativeFrame()));
            return null;
            });
            assertArrayEquals(ledger,produced.actual.ledgerBytes());assertEquals(writes,produced.actual.nativeActionWrites());
        }
    }
}

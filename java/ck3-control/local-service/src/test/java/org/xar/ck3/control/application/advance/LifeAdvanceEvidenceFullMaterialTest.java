package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Actual software packet/facts/assembler plus the same physical archive. No action, canonical
 * receipt, Ready or current Root is minted. Wide-number DATA below deliberately has no Native frame qualification.
 */
final class LifeAdvanceEvidenceFullMaterialTest {
    @TempDir Path root;
    private static long files(Path directory)throws IOException {
        try(var entries=Files.walk(directory)){return entries.filter(Files::isRegularFile).count();}
    }
    @Test void actualFullFrameProducerArchiveAndIndependentFrameReaderPreserveCompleteSemanticData()throws Exception {
        try(var fixture=new FullAdvanceFrameFixture(root.resolve("actual-full-frame"))) {
            byte[] original=DriverJson.encode(fixture.frame.semantic());
            assertTrue(original.length>128*1024);assertTrue(original.length<=RawJson.MAXIMUM_BYTES);
            // Strings of131KiB do not exceed the ordinary64MiB byte limit or4300-digit integer limit.
            // This case proves complete real frame/role roundtrip, not an ordinary-number rejection.
            byte[] ledger=fixture.actual.ledgerBytes();int actions=fixture.actual.nativeActionWrites(),packets=fixture.actual.nativePacketReads();
            fixture.actual.writer.locked(same->{
                var archive=fixture.actual.archive.withSession(same);
                var recorded=LifeAdvanceEvidence.preserveFrame(fixture.frame,archive);
                assertArrayEquals(original,archive.loadFullMaterial(recorded.semantic()).bytes());
                assertArrayEquals(original,archive.loadMaterial(recorded.semantic()).bytes());
                long retained=files(fixture.actual.root);
                assertEquals(fixture.frame.semantic(),LifeAdvanceEvidence.originalSemantic(recorded,archive));
                var independentlyRebuilt=new LifeAdvanceRootReplay(fixture.actual.frameLoader()).rebuild(fixture.command,recorded,archive);
                assertEquals(fixture.frame,independentlyRebuilt);assertEquals(retained,files(fixture.actual.root));
                return null;
            });
            assertArrayEquals(ledger,fixture.actual.ledgerBytes());assertEquals(actions,fixture.actual.nativeActionWrites());
            assertEquals(packets,fixture.actual.nativePacketReads());
        }
    }
    @Test void explicitLargeDerivedIntegerMaterialDoesNotBecomeANativeOrQualifiedSemanticFrame()throws Exception {
        try(var fixture=new FullAdvanceFrameFixture(root.resolve("wide-data-only"))) {
            var wide=new Obj(Map.of("unregistered_derived_integer",new IntegerValue(new BigInteger("9".repeat(5000)))));
            byte[] bytes=DriverJson.encode(wide);
            assertThrows(IllegalArgumentException.class,()->new RawJson(bytes));
            byte[] ledger=fixture.actual.ledgerBytes();int actions=fixture.actual.nativeActionWrites(),packets=fixture.actual.nativePacketReads();
            fixture.actual.writer.locked(same->{
                var archive=fixture.actual.archive.withSession(same);
                var actualRecord=LifeAdvanceEvidence.preserveFrame(fixture.frame,archive);
                var data=archive.preserveMaterial(RawJson.fullMaterial(bytes));
                var unregistered=new LifeAdvanceEvidence.FrameRecord(actualRecord.identity(),actualRecord.provenance(),actualRecord.observedAt(),
                        actualRecord.nativeFrame(),actualRecord.driverFacts(),data);
                long retained=files(fixture.actual.root);
                assertEquals(wide,LifeAdvanceEvidence.originalSemantic(unregistered,archive));
                assertThrows(RuntimeException.class,()->archive.loadMaterial(data));
                assertThrows(IllegalArgumentException.class,()->archive.loadFullMaterial(data).requireProtocolBound());
                // The real independent loader reconstructs the original frame, not these caller-shaped DATA.
                // readRecorded's existing complete-semantic equality guard remains mandatory for qualification.
                var independentlyRebuilt=new LifeAdvanceRootReplay(fixture.actual.frameLoader()).rebuild(fixture.command,unregistered,archive);
                assertEquals(fixture.frame,independentlyRebuilt);assertNotEquals(wide,independentlyRebuilt.semantic());
                assertEquals(retained,files(fixture.actual.root));return null;
            });
            assertArrayEquals(ledger,fixture.actual.ledgerBytes());assertEquals(actions,fixture.actual.nativeActionWrites());
            assertEquals(packets,fixture.actual.nativePacketReads());
        }
    }
}

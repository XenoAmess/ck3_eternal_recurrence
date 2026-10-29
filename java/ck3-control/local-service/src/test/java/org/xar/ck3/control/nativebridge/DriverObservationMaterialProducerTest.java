package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software frame/Driver -> complete manifest DATA. No public Complete or private Root admission. */
class DriverObservationMaterialProducerTest {
    @TempDir Path directory;
    @Test void actualSoftwareFrameAndDriverEncodeArchiveAndDecodeFullManifestOpaqueMaterial()throws Exception{
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("manifest-material"),false)){
            fixture.command("original-observation");
            var known=fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state()));
            var actual=fixture.physicalInputs().transport().observe(Instant.now().plusSeconds(20));
            var prior=known.observation().orElseThrow();
            // These are explicitly DATA material extensions, not a claim about the current Game SEM.
            var semantic=prior.originalSemanticFields().with("opaque_material_progress",new OpportunityJson.IntegerValue(new BigInteger("9".repeat(70000))))
                    .with("opaque_material_zero",new OpportunityJson.DecimalValue("-0.0")).with("opaque_material_ratio",new OpportunityJson.DecimalValue("1.0"));
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);var driver=RawJson.fullMaterial(known.driver().encode());
                var driverRef=archive.preserveMaterial(driver);
                var encoded=DriverObservationEvidenceReader.encode(known,actual,prior.publicRevision(),prior.observationVersion(),prior.source(),semantic,driverRef);
                assertThrows(IllegalArgumentException.class,()->new RawJson(encoded.bytes()));
                var manifestRef=archive.preserveMaterial(encoded);var reopened=archive.loadFullMaterial(manifestRef);
                var decoded=DriverObservationEvidenceReader.decode(manifestRef,reopened,archive.loadFullMaterial(driverRef),actual);
                assertEquals(known.driver(),decoded.driver());assertEquals(semantic,decoded.originalSemanticFields());
                assertEquals(decoded,DriverObservationEvidenceReader.decode(manifestRef,reopened,archive.loadFullMaterial(driverRef),actual));
                assertArrayEquals(encoded.bytes(),reopened.bytes());
                return null;
            });
        }
    }
}

package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Exact full roles traverse actual packet/facts producer, filesystem archive and original frame loader. */
final class AdvanceFullMaterialTest {
    @TempDir Path root;
    @Test void explicitDriverMaterialRoleRetainsWideDerivedIntegersWithoutWideningNativeTokens()throws Exception {
        try(var actual=new org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture(root.resolve("driver-data-role"),false)) {
            byte[] body=("{\"driver_only_derived_integer\":"+"9".repeat(5000)+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class,()->new RawJson(body));
            var full=RawJson.fullMaterial(body);int writes=actual.nativeActionWrites();byte[] head=actual.ledgerBytes();
            actual.writer.locked(same->{var archive=actual.archive.withSession(same);var reference=archive.preserveMaterial(full);
                assertArrayEquals(body,archive.loadFullMaterial(reference).bytes());
                assertThrows(IllegalArgumentException.class,()->archive.loadMaterial(reference));return null;
            });
            assertEquals(writes,actual.nativeActionWrites());assertArrayEquals(head,actual.ledgerBytes());
        }
    }
    @Test void actualLargeNativeFactsManifestUsesFullMaterialButThePrimitiveBasisRemainsSmall()throws Exception {
        try(var fixture=new FullAdvanceFrameFixture(root.resolve("large-native-original"))) {
            int writes=fixture.actual.nativeActionWrites(),reads=fixture.actual.nativePacketReads();byte[] head=fixture.actual.ledgerBytes();
            fixture.actual.writer.locked(same->{
                var archive=fixture.actual.archive.withSession(same);
                var manifest=ExactRef.fromJson(OpportunityJson.toNode(fixture.frame.semantic().get("java_driver_facts_evidence")));
                assertTrue(manifest.bytes()>131072 && manifest.bytes()<=RawJson.MAXIMUM_BYTES);
                assertArrayEquals(archive.loadMaterial(manifest).bytes(),archive.loadFullMaterial(manifest).bytes(),"large byte count alone does not change the ordinary numeric-token domain");
                assertEquals(manifest.bytes(),archive.loadFullMaterial(manifest).bytes().length);
                var basis=AdvancePrimitiveEvidence.preserve(fixture.command,fixture.frame,archive);
                assertTrue(basis.bytes()<RawJson.MAXIMUM_BYTES);
                var small=StrictJson.parse(archive.loadMaterial(basis).bytes());
                assertEquals(manifest,ExactRef.fromJson(small.get("driver_facts")));
                var retained=new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(small.get("native_frame")),manifest);
                var restored=fixture.actual.frameLoader().load(retained,archive);
                assertEquals(fixture.complete.identity(),restored.identity());assertEquals(fixture.complete.fullBindingSha256(),restored.fullBindingSha256());
                assertEquals(fixture.complete.semantic(),restored.semantic());return null;
            });
            assertArrayEquals(head,fixture.actual.ledgerBytes());assertEquals(writes,fixture.actual.nativeActionWrites());assertEquals(reads,fixture.actual.nativePacketReads());
        }
    }
}

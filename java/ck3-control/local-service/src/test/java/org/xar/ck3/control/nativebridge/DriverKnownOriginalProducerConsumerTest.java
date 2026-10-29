package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.math.BigInteger;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software Driver owner -> original Known material -> sole decoder. No physical Root/cold permission. */
public final class DriverKnownOriginalProducerConsumerTest {
    @TempDir Path directory;
    private record StoredKnown(ExactRef original,RawJson expected,DriverSnapshotFacts.Known data) { }
    private static ExactRef ref(String name){return new ExactRef("data/"+name,1,DriverJson.sha256(name.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}
    @Test public void actualProducerSevenSlotsRoundTripRequiresItsOriginalObservationReplay()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("known-original"),false)) {
            fixture.command("observed-before");
            fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->{
                var known=(DriverSnapshotFacts.Known)frozen.state();var wire=DriverSnapshotFacts.encodeKnownOriginal(known);
                assertEquals(known.observation().map(DriverObservationFacts::semanticFactsEvidence),DriverSnapshotFacts.observationOriginalReference(wire));
                var decoded=DriverSnapshotFacts.decodeKnownOriginal(wire,known.observation());
                assertArrayEquals(known.driver().encode(),decoded.driver().encode());assertEquals(known.stamp(),decoded.stamp());
                assertEquals(known.originalHistoryBasis(),decoded.originalHistoryBasis());assertEquals(known.actionRows(),decoded.actionRows());
                assertEquals(known.auxiliary(),decoded.auxiliary());assertEquals(known.loop(),decoded.loop());
                assertArrayEquals(wire.bytes(),DriverSnapshotFacts.encodeKnownOriginal(decoded).bytes());
                if(known.observation().isPresent())assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(wire,Optional.empty()));
                return null;
            }));
        }
    }
    @Test public void mixedCoverageLoopAndOpaqueTokensAreCompleteDataRatherThanAnEmptyFallback()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("known-data"),false)) {
            fixture.command("observed-before");
            fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->{
                var actual=(DriverSnapshotFacts.Known)frozen.state();var base=actual.driver();
                long ordinal=base.commandHistory().size()+1L;
                var row=new DriverStateSnapshot.HistoryEntry(ordinal,new DriverStateSnapshot.Value(("{\"index\":"+ordinal+",\"command\":\"data\",\"opaque\":-0.0,\"ratio\":1.0,\"progress\":"+"9".repeat(70000)+"}").getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                var history=new ArrayList<>(base.commandHistory());history.add(row);
                var driver=new DriverStateSnapshot.Complete(base.session(),history,base.lastCheckpoint(),base.rollbackWarFailure(),base.managedRestoreTransaction(),
                        base.successionExpectation(),base.successionLifecycle(),base.campaignGoal(),base.rollbackWarFailures());
                var stamp=new DriverSnapshotFacts.Stamp(actual.stamp().driverVersion(),actual.stamp().episodeEpoch(),actual.stamp().game(),actual.stamp().episodeRunId(),DriverJson.sha256(driver.encode()));
                var rows=List.of(new DriverSnapshotFacts.ActionRow("legacy","a".repeat(64),1,new DriverSnapshotFacts.LegacyHistoryRow(ordinal,ref("row"))),
                        new DriverSnapshotFacts.ActionRow("canonical","b".repeat(64),2,new DriverSnapshotFacts.CanonicalOnly(ref("canonical"))));
                var aux=actual.auxiliary().with("opaque",new OpportunityJson.DecimalValue("1e999")).with("zero",new OpportunityJson.DecimalValue("-0.0"));
                var loop=new DriverSnapshotFacts.LoopWitness("batch",3,actual.stamp().episodeEpoch(),true,2,false,ref("loop"));
                var data=new DriverSnapshotFacts.Known(driver,stamp,actual.originalHistoryBasis(),rows,aux,Optional.of(loop),Optional.empty());
                var encoded=DriverSnapshotFacts.encodeKnownOriginal(data);var decoded=DriverSnapshotFacts.decodeKnownOriginal(encoded,Optional.empty());
                assertThrows(IllegalArgumentException.class,()->new RawJson(encoded.bytes()));
                var reread=DriverSnapshotFacts.originalKnownJson(encoded.bytes());assertEquals(encoded,reread);
                assertArrayEquals(driver.encode(),decoded.driver().encode());
                assertTrue(DriverSnapshotFacts.observationOriginalReference(encoded).isEmpty());
                assertEquals(rows,decoded.actionRows());assertEquals(loop,decoded.loop().orElseThrow());assertEquals(aux,decoded.auxiliary());
                assertTrue(decoded.actionRows().get(1).coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly);
                assertThrows(IllegalStateException.class,()->decoded.actionRows().get(1).historyIndex());
                assertArrayEquals(encoded.bytes(),DriverSnapshotFacts.encodeKnownOriginal(decoded).bytes());return null;
            }));
        }
    }
    @Test public void absentNullWrongTypeAndObservationInjectionRejectWithoutManufacturingKnown()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("known-invalid"),false)) {
            fixture.command("observed-before");
            fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->{
                var known=(DriverSnapshotFacts.Known)frozen.state();var valid=DriverJson.object(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES);
                for(String key:List.of("driver","stamp","original_history_basis","action_rows","auxiliary","loop","observation")) {
                    var missing=new LinkedHashMap<String,OpportunityJson.Value>(valid.members());missing.remove(key);
                    assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(new RawJson(DriverJson.encode(new OpportunityJson.Obj(missing))),known.observation()));
                }
                var stamp=OpportunityJson.object(valid.get("stamp"),"stamp");
                for(var bad:List.<OpportunityJson.Value>of(new OpportunityJson.Bool(true),new OpportunityJson.DecimalValue("1.0"),new OpportunityJson.Text("1"))) {
                    var invalid=valid.with("stamp",stamp.with("driver_version",bad));
                    assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(new RawJson(DriverJson.encode(invalid)),known.observation()));
                }
                var nullAux=valid.with("auxiliary",OpportunityJson.Nil.INSTANCE);
                assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(new RawJson(DriverJson.encode(nullAux)),known.observation()));
                if(known.observation().isPresent()) {
                    var absent=valid.with("observation",OpportunityJson.Nil.INSTANCE);
                    assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(new RawJson(DriverJson.encode(absent)),known.observation()));
                    var wrong=valid.with("observation",DriverObservationEvidenceReader.reference(ref("other-manifest")));
                    assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(new RawJson(DriverJson.encode(wrong)),known.observation()));
                }
                return null;
            }));
        }
    }
    @Test public void actualKnownOwnerToOriginalArchiveAndFreshReadRetainsLargeMaterialAndObservationPresence()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("known-material-archive"),false)) {
            fixture.command("observed-before");
            StoredKnown retained=fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->{
                var actual=(DriverSnapshotFacts.Known)frozen.state();
                var auxiliary=actual.auxiliary().with("contract_progress",new OpportunityJson.IntegerValue(new BigInteger("9".repeat(70000))))
                        .with("opaque_zero",new OpportunityJson.DecimalValue("-0.0")).with("opaque_ratio",new OpportunityJson.DecimalValue("1.0"))
                        .with("opaque_exponent",new OpportunityJson.DecimalValue("1e999"));
                // This is complete DATA derived from the real owner; it creates no Root/cold admission.
                var data=new DriverSnapshotFacts.Known(actual.driver(),actual.stamp(),actual.originalHistoryBasis(),actual.actionRows(),auxiliary,actual.loop(),actual.observation());
                var encoded=DriverSnapshotFacts.encodeKnownOriginal(data);
                assertEquals(actual.observation().map(DriverObservationFacts::semanticFactsEvidence),DriverSnapshotFacts.observationOriginalReference(encoded));
                var archive=fixture.archive.withSession(same);return new StoredKnown(archive.preserveMaterial(encoded),encoded,data);
            }));
            fixture.writer.locked(same->{
                var archive=fixture.archive.withSession(same);var material=archive.loadFullMaterial(retained.original());
                assertEquals(retained.expected(),material);assertEquals(retained.original(),archive.materialReferenceOf(material));
                assertThrows(IllegalArgumentException.class,()->archive.loadMaterial(retained.original()));
                var raw=DriverSnapshotFacts.originalKnownJson(material.bytes());
                var decoded=DriverSnapshotFacts.decodeKnownOriginal(raw,retained.data().observation());
                assertArrayEquals(retained.data().driver().encode(),decoded.driver().encode());assertEquals(retained.data().stamp(),decoded.stamp());
                assertEquals(retained.data().auxiliary(),decoded.auxiliary());assertEquals(retained.data().actionRows(),decoded.actionRows());
                assertEquals(retained.data().loop(),decoded.loop());assertEquals(retained.data().observation(),decoded.observation());
                assertArrayEquals(raw.bytes(),DriverSnapshotFacts.encodeKnownOriginal(decoded).bytes());
                if(retained.data().observation().isPresent())assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.decodeKnownOriginal(raw,Optional.empty()));
                var invalid=DriverJson.object(raw.bytes(),DriverSnapshotFacts.MAX_ORIGINAL_BYTES).with("schema",new OpportunityJson.Text("unknown"));
                assertThrows(IllegalArgumentException.class,()->DriverSnapshotFacts.originalKnownJson(DriverJson.encode(invalid)));
                return null;
            });
        }
    }
}

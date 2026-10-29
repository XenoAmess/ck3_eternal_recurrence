package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original framed software DATA -> sole observation producer -> both actual lifecycle settlement consumers.
 * This does not create a Managed process, NEXT authority, first-SAVE proof or restoration permission. */
public final class LifecycleSettlementObservationTest {
    @TempDir Path temporary;
    private LifecycleObservationPort.Snapshot snapshot(String suffix,long version)throws Exception {
        Path root=java.nio.file.Files.createDirectories(temporary.resolve(suffix));
        var f=new LifecycleBusinessFixture(root);
        var raw=(com.fasterxml.jackson.databind.node.ObjectNode)DriverJson.toNormalizedNode(
                DriverObservationAssembler.originalNativeState(f.snapshot.actual()));
        raw.putNull("active_event");raw.putNull("pending_character_interaction");
        var settlement=DeathSettlementTest.ready(false,10,10);
        BigInteger scale=BigInteger.TEN.pow(20);
        settlement.putObject("final_score").put("raw",scale.add(BigInteger.ONE)).put("scale",scale);
        settlement.putObject("score_before_reject").put("raw",-1).put("scale",BigInteger.TEN.pow(400));
        raw.set("one_life_settlement",settlement);
        byte[] state=DriverJson.encode(DriverJson.fromNormalizedNode(raw));
        var envelope=new OpportunityJson.Obj(Map.of("type",new OpportunityJson.Text("state_snapshot"),
                "protocol_version",new OpportunityJson.IntegerValue(BigInteger.ONE),
                "snapshot_id",new OpportunityJson.Text(f.snapshot.actual().snapshotId()),
                "revision",new OpportunityJson.IntegerValue(f.snapshot.actual().nativeRevision()),
                "state",DriverJson.object(state,DriverJson.MAX_NATIVE_BYTES)));
        byte[] payload=DriverJson.encode(envelope);
        byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var actual=new NativeObservationPort.ObservedFrame(f.snapshot.actual().session(),f.snapshot.actual().snapshotId(),
                f.snapshot.actual().nativeRevision(),new RawJson(state),packet,f.snapshot.actual().observedAt());
        var nativeRef=f.files.createNew(root.resolve("settlement-original-native.bin"),packet).reference();
        var known=f.snapshot.facts();
        // These are real original producer inputs; the projector alone derives normalized v3 SEM.
        var extras=new OpportunityJson.Obj(Map.of());
        var wire=DriverObservationEvidenceReader.encode(known,actual,BigInteger.ONE,version,f.snapshot.source(),extras,known.originalHistoryBasis());
        var manifest=f.files.createNew(root.resolve("settlement-observation-manifest.json"),wire.bytes()).reference();
        var facts=DriverObservationEvidenceReader.decode(manifest,wire,new RawJson(known.driver().encode()),actual);
        var projected=new DriverObservationAssembler().projectFull(actual,facts,nativeRef);
        var observed=new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),known.actionRows(),
                known.auxiliary(),known.loop(),Optional.of(facts));
        return new LifecycleObservationPort.Snapshot(actual,f.snapshot.source(),projected.semantic(),observed,nativeRef);
    }
    @Test void actualVersionThreeProducerKeepsRoundedRatioFloatAndNegativeZeroThroughConsumer()throws Exception {
        var actual=snapshot("canonical",DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION);
        var ready=LifecycleComposites.settlementFromSnapshot(actual).orElseThrow();
        assertTrue(ready.scoreJson().isFloatingPointNumber());assertEquals(1.0,ready.scoreJson().doubleValue());
        assertEquals(Double.doubleToRawLongBits(-0.0),
                Double.doubleToRawLongBits(ready.normalizedJson().get("score_before_reject").doubleValue()));
        assertArrayEquals(ready.normalized(),DeathSettlement.fromNormalized(
                DriverJson.toNormalizedNode(actual.semantic().get("one_life_settlement"))).orElseThrow().normalized());
        assertEquals(3,actual.facts().observation().orElseThrow().observationVersion());
    }
    @Test void originalVersionOneAndTwoUseActualRawPacketWithoutRelabellingTheirFacts()throws Exception {
        for(long version:new long[]{DriverObservationAssembler.LEGACY_OBSERVATION_VERSION,DriverObservationAssembler.WAR_ARMY_OBSERVATION_VERSION}){
            var actual=snapshot("historical-"+version,version);
            var ready=LifecycleComposites.settlementFromSnapshot(actual).orElseThrow();
            assertEquals(version,actual.facts().observation().orElseThrow().observationVersion());
            assertInstanceOf(OpportunityJson.Obj.class,actual.semantic().get("one_life_settlement"));
            var raw=OpportunityJson.object(actual.semantic().get("one_life_settlement"),"original legacy settlement");
            assertInstanceOf(OpportunityJson.Obj.class,raw.get("final_score"),"legacy fixed object must remain original DATA");
            assertTrue(ready.scoreJson().isFloatingPointNumber());assertEquals(1.0,ready.scoreJson().doubleValue());
            assertEquals(Double.doubleToRawLongBits(-0.0),
                    Double.doubleToRawLongBits(ready.normalizedJson().get("score_before_reject").doubleValue()));
        }
    }
    @Test void normalizedSemanticMutationCannotBorrowTheOriginalObservationVersion()throws Exception {
        var actual=snapshot("semantic-drift",DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION);
        var fields=new LinkedHashMap<String,OpportunityJson.Value>(actual.semantic().members());
        fields.put("one_life_settlement",OpportunityJson.Nil.INSTANCE);
        var tampered=new LifecycleObservationPort.Snapshot(actual.actual(),actual.source(),new OpportunityJson.Obj(fields),
                actual.facts(),actual.originalEvidence());
        assertThrows(IllegalArgumentException.class,()->LifecycleComposites.settlementFromSnapshot(tampered));
    }
    @Test void missingActualObservationVersionCannotBeGuessedFromAnEvidenceReference()throws Exception {
        var actual=snapshot("missing-version",DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION);
        var known=actual.facts();
        var missing=new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),known.actionRows(),
                known.auxiliary(),known.loop(),Optional.empty());
        var unversioned=new LifecycleObservationPort.Snapshot(actual.actual(),actual.source(),actual.semantic(),missing,actual.originalEvidence());
        assertThrows(IOException.class,()->LifecycleComposites.settlementFromSnapshot(unversioned));
    }
}

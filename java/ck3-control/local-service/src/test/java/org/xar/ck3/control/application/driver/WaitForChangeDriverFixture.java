package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software transport at the real typed wait boundary; original packets still pass the actual Driver assembler. */
public final class WaitForChangeDriverFixture {
    private WaitForChangeDriverFixture() { }
    public record Frame(NativeObservationPort.ObservedFrame actual,DriverObservationFacts facts,ExactRef original,boolean elapsed) { }
    public record Deadlines(Instant waitUntil,Instant captureUntil) { }
    public record Scenario(HeldDriverObservationPort held,AtomicInteger waits,AtomicInteger currentSnapshots,AtomicInteger genericObservations,
            AtomicInteger facts,AtomicInteger evidence,List<Deadlines> receivedDeadlines) { }

    public static Frame frame(int nativeRevision,BigInteger publicRevision,boolean elapsed) {
        var base=DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);
        byte[] state=DriverStateAssemblerTest.bytes(DriverObservationAssemblerTest.STATE.strip());
        byte[] json=DriverStateAssemblerTest.bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"wait-"+nativeRevision
                +"\",\"revision\":"+nativeRevision+",\"state\":"+DriverObservationAssemblerTest.STATE+"}");
        byte[] packet=ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        var actual=new NativeObservationPort.ObservedFrame(base.session(),"wait-"+nativeRevision,BigInteger.valueOf(nativeRevision),
                new RawJson(state),packet,base.observedAt());
        var facts=DriverObservationAssemblerTest.facts(actual);
        var supplied=new DriverObservationFacts(facts.driver(),facts.driverVersion(),facts.episodeEpoch(),actual.session(),actual.snapshotId(),
                actual.nativeRevision(),facts.nativeStateSha256(),publicRevision,facts.observationVersion(),facts.source(),facts.originalSemanticFields(),facts.semanticFactsEvidence());
        return new Frame(actual,supplied,DriverStateAssemblerTest.ref(packet),elapsed);
    }
    public static Scenario sequence(Frame... frames){return scenario(List.of(frames),null,null);}
    public static Scenario unavailable(IOException failure){return scenario(List.of(),failure,null);}
    public static Scenario interrupted(InterruptedException failure){return scenario(List.of(),null,failure);}
    public static byte[] fullState(){return DriverStateAssemblerTest.bytes(DriverObservationAssemblerTest.STATE);}
    /** The same actual NGT used by the shared software Win32 endpoint; no typed wait outcome is manufactured here. */
    public static HeldDriverObservationPort receiver(NativeGameTransport actualTransport,Map<BigInteger,BigInteger> publicRevisions) {
        Map<BigInteger,BigInteger> revisions=Map.copyOf(publicRevisions);
        return new HeldDriverObservationPort(actualTransport,actual->{
            BigInteger publicRevision=java.util.Objects.requireNonNull(revisions.get(actual.nativeRevision()),"explicit actual fixture public revision mapping required");
            var template=new RawJson(DriverStateAssemblerTest.bytes(DriverStateAssemblerTest.WIRE));
            var driver=PublicDataJson.object(template);driver.put("pipe_name",actualTransport.pipeName());
            byte[] originalDriver=PublicDataJson.encodePreservingDecimals(driver,template).bytes();
            ExactRef driverRef=DriverStateAssemblerTest.ref(originalDriver);
            var known=DriverFactsRepository.imported(driverRef,originalDriver,3,7,actual.session().game(),new OpportunityJson.Obj(Map.of()));
            var source=new G2Source(actual.session().machineId(),"2026-10-24T00:00:00Z","actual-wait-receiver-software-fixture",
                    DriverStateAssemblerTest.ref(DriverStateAssemblerTest.bytes("explicit actual receiver test source")));
            var manifest=DriverObservationEvidenceReader.encode(known,actual,publicRevision,1,source,new OpportunityJson.Obj(Map.of()),driverRef);
            return new DriverObservationFacts.Known(new DriverObservationFacts(known.driver(),known.stamp().driverVersion(),known.stamp().episodeEpoch(),
                    actual.session(),actual.snapshotId(),actual.nativeRevision(),DriverJson.sha256(actual.state().bytes()),publicRevision,1,source,
                    new OpportunityJson.Obj(Map.of()),DriverStateAssemblerTest.ref(manifest.bytes())));
        },actual->DriverStateAssemblerTest.ref(actual.originalPacket()),new DriverObservationAssembler(),8);
    }
    private static Scenario scenario(List<Frame> frames,IOException failure,InterruptedException interrupt) {
        List<Frame> originals=frames.isEmpty()?List.of(frame(8,BigInteger.valueOf(2),false)):frames;
        var remaining=new ArrayDeque<>(frames);
        if(!remaining.isEmpty()&&!remaining.getFirst().elapsed())remaining.removeFirst();
        var waits=new AtomicInteger();var currents=new AtomicInteger();var observations=new AtomicInteger();
        var facts=new AtomicInteger();var evidence=new AtomicInteger();var deadlines=new ArrayList<Deadlines>();
        NativeSnapshotWaitPort transport=new NativeSnapshotWaitPort() {
            @Override public NativeObservationPort.ObservedFrame observe(Instant deadline) {
                observations.incrementAndGet();throw new AssertionError("WAIT must not call another observation producer");
            }
            @Override public NativeObservationPort.ObservedFrame currentSnapshot(Instant captureUntil) {
                currents.incrementAndGet();return originals.getFirst().actual();
            }
            @Override public WaitResult waitForSnapshot(Instant waitUntil,Instant captureUntil)throws IOException,InterruptedException {
                waits.incrementAndGet();deadlines.add(new Deadlines(waitUntil,captureUntil));
                if(failure!=null)throw failure;if(interrupt!=null)throw interrupt;
                if(remaining.isEmpty())throw new IOException("actual fixture packet stream ended without a typed timeout result");
                Frame frame=remaining.removeFirst();return frame.elapsed()?new Elapsed(frame.actual()):new Received(frame.actual());
            }
        };
        var held=new HeldDriverObservationPort(transport,actual->{
            facts.incrementAndGet();Frame frame=originals.stream().filter(value->value.actual()==actual).findFirst().orElseThrow();
            return new DriverObservationFacts.Known(frame.facts());
        },actual->{
            evidence.incrementAndGet();return originals.stream().filter(value->value.actual()==actual).findFirst().orElseThrow().original();
        },new DriverObservationAssembler(),8);
        return new Scenario(held,waits,currents,observations,facts,evidence,deadlines);
    }
}

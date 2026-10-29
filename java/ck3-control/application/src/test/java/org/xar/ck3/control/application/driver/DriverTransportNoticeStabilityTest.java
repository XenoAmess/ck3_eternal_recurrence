package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class DriverTransportNoticeStabilityTest {
    private record Actual(DriverObservationFacts facts,NativeObservationPort.ObservedFrame nativeFrame,Obj manifest) { }
    @Test void CompleteArchivedProducerRetainsBusinessAndUnknownNoticeFieldsWhileOnlyProvenOuterFreshnessMayDiffer() {
        var f=DriverCapabilityStateProducerTest.fresh();Obj raw=DriverJson.object(f.actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        var before=observed(f,raw,diagnostics(f,heartbeat(f,1,2,"same"),"ping-1"));
        var later=observed(f,raw,diagnostics(f,heartbeat(f,3,4,"same"),"ping-2"));
        assertNotEquals(before.facts().originalSemanticFields(),later.facts().originalSemanticFields());
        assertEquals(DriverTransportNoticeStability.originalFields(before.facts(),before.nativeFrame()),DriverTransportNoticeStability.originalFields(later.facts(),later.nativeFrame()));
        var beforeFrame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(before.nativeFrame(),before.facts(),f.archive().preserveNativeFrame(before.nativeFrame())));
        var laterFrame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(later.nativeFrame(),later.facts(),f.archive().preserveNativeFrame(later.nativeFrame())));
        var firstManifest=DriverTransportNoticeStability.manifest(before.manifest(),before.facts(),before.nativeFrame());
        var nextManifest=DriverTransportNoticeStability.manifest(later.manifest(),later.facts(),later.nativeFrame());
        assertEquals(firstManifest,nextManifest);
        assertEquals(DriverTransportNoticeStability.semantic(beforeFrame,before.facts(),before.nativeFrame(),firstManifest),
                DriverTransportNoticeStability.semantic(laterFrame,later.facts(),later.nativeFrame(),nextManifest));
        Obj normalized=object(DriverTransportNoticeStability.originalFields(before.facts(),before.nativeFrame()).get("diagnostics"),"diagnostics");
        Obj retained=object(normalized.get("last_heartbeat"),"last_heartbeat");
        assertFalse(retained.members().containsKey("sequence"));assertFalse(retained.members().containsKey("monotonic_ms"));
        assertEquals(new Text("same"),retained.get("command_entry_trace_v1"));
        assertEquals(new IntegerValue(BigInteger.valueOf(99)),object(retained.get("unknown_future_business"),"unknown_future_business").get("monotonic_ms"));
        var business=observed(f,raw,diagnostics(f,heartbeat(f,3,4,"changed"),"ping-2"));
        assertNotEquals(DriverTransportNoticeStability.originalFields(later.facts(),later.nativeFrame()),DriverTransportNoticeStability.originalFields(business.facts(),business.nativeFrame()));
    }
    @Test void NativeOwnedSameNameKeysAndErrorSnapshotDiagnosticsStayEntirelyStrict() {
        var f=DriverCapabilityStateProducerTest.fresh();Obj raw=DriverJson.object(f.actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        Obj one=heartbeat(f,1,2,"same"),two=heartbeat(f,2,3,"same");
        Obj nativeOne=raw.with("diagnostics",object(raw.get("diagnostics"),"diagnostics").with("last_heartbeat",one));
        Obj nativeTwo=raw.with("diagnostics",object(raw.get("diagnostics"),"diagnostics").with("last_heartbeat",two));
        var first=observed(f,nativeOne,diagnostics(f,one,"ping-1"));var second=observed(f,nativeTwo,diagnostics(f,two,"ping-2"));
        Obj retained=object(DriverTransportNoticeStability.originalFields(first.facts(),first.nativeFrame()).get("diagnostics"),"diagnostics");
        assertEquals(one,retained.get("last_heartbeat"));
        assertNotEquals(DriverTransportNoticeStability.originalFields(first.facts(),first.nativeFrame()),DriverTransportNoticeStability.originalFields(second.facts(),second.nativeFrame()));
        Obj baseline=diagnostics(f,one,"ping-1").with("last_error",new Obj(Map.of("request_id",new Text("error-1"))))
                .with("last_snapshot_publish_diagnostic",new Obj(Map.of("elapsed_ms",new IntegerValue(BigInteger.ONE),"status",new Text("published"))));
        var before=observed(f,raw,baseline);var error=observed(f,raw,baseline.with("last_error",new Obj(Map.of("request_id",new Text("error-2")))));
        var snapshot=observed(f,raw,baseline.with("last_snapshot_publish_diagnostic",new Obj(Map.of("elapsed_ms",new IntegerValue(BigInteger.TWO),"status",new Text("published")))));
        assertNotEquals(DriverTransportNoticeStability.originalFields(before.facts(),before.nativeFrame()),DriverTransportNoticeStability.originalFields(error.facts(),error.nativeFrame()));
        assertNotEquals(DriverTransportNoticeStability.originalFields(before.facts(),before.nativeFrame()),DriverTransportNoticeStability.originalFields(snapshot.facts(),snapshot.nativeFrame()));
    }
    @Test void WrongTypeProtocolGameOrNonIntegerFreshnessCannotBecomeAStableWrapper() {
        var f=DriverCapabilityStateProducerTest.fresh();Obj raw=DriverJson.object(f.actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        for(Obj invalid:new Obj[]{heartbeat(f,1,2,"same").with("type",new Text("unknown")),heartbeat(f,1,2,"same").with("protocol_version",new Bool(true)),
                heartbeat(f,1,2,"same").with("pid",new IntegerValue(BigInteger.ZERO)),heartbeat(f,1,2,"same").with("sequence",new Bool(true))}) {
            var actual=observed(f,raw,diagnostics(f,invalid,"ping-1"));
            assertThrows(IllegalArgumentException.class,()->DriverTransportNoticeStability.originalFields(actual.facts(),actual.nativeFrame()));
        }
    }
    private static Obj heartbeat(DriverCapabilityStateProducerTest.Fixture f,long sequence,long time,String business) {
        return new Obj(Map.of("type",new Text("heartbeat"),"protocol_version",new IntegerValue(BigInteger.ONE),"pid",new IntegerValue(BigInteger.valueOf(f.actual().session().game().pid())),
                "sequence",new IntegerValue(BigInteger.valueOf(sequence)),"monotonic_ms",new IntegerValue(BigInteger.valueOf(time)),"command_entry_trace_v1",new Text(business),
                "unknown_future_business",new Obj(Map.of("monotonic_ms",new IntegerValue(BigInteger.valueOf(99))))));
    }
    private static Obj diagnostics(DriverCapabilityStateProducerTest.Fixture f,Obj heartbeat,String request) {
        var fields=new LinkedHashMap<>(object(f.current().observation().orElseThrow().originalSemanticFields().get("diagnostics"),"diagnostics").members());
        fields.put("last_heartbeat",heartbeat);fields.put("last_pong",new Obj(Map.of("type",new Text("pong"),"protocol_version",new IntegerValue(BigInteger.ONE),
                "pid",new IntegerValue(BigInteger.valueOf(f.actual().session().game().pid())),"request_id",new Text(request))));return new Obj(fields);
    }
    private static Actual observed(DriverCapabilityStateProducerTest.Fixture f,Obj raw,Obj diagnostics) {
        byte[] state=DriverJson.encode(raw);byte[] packet=ByteBuffer.allocate(state.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(state.length).put(state).array();
        var actual=new NativeObservationPort.ObservedFrame(f.actual().session(),f.actual().snapshotId(),f.actual().nativeRevision(),new RawJson(state),packet,f.actual().observedAt());
        var fields=new LinkedHashMap<>(f.current().observation().orElseThrow().originalSemanticFields().members());fields.put("diagnostics",diagnostics);
        RawJson manifest=DriverObservationEvidenceReader.encode(f.current(),actual,BigInteger.TWO,1,f.frame().source(),new Obj(fields),f.current().originalHistoryBasis());
        var ref=f.archive().preserveMaterial(manifest);
        var facts=DriverObservationEvidenceReader.decode(ref,manifest,new RawJson(f.current().driver().encode()),actual);
        return new Actual(facts,actual,DriverJson.object(manifest.bytes(),DriverJson.MAX_NATIVE_BYTES));
    }
}

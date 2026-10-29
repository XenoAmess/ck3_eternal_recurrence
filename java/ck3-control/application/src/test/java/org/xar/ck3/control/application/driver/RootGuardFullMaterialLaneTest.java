package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual Driver/manifest/assembler/guard codecs, on software original DATA. No Root lease or writer authority. */
final class RootGuardFullMaterialLaneTest {
    private static final OperationKey OPERATION=new OperationKey("query-full-guard-software-data");
    private static final String AUTHORITY="software-codec-only";
    @Test void realFullDriverManifestAndSemanticProducerReachGuardConsumerAndColdReconstruction() {
        Fixture f=fixture();ExactRef basis=preserve(f);GuardEvidence guard=guard(f,basis);
        Set<ExactRef> full=Set.of(f.manifest,f.semantic.semantic(),f.semantic.originalDriver());
        for(ExactRef original:full)assertThrows(IllegalArgumentException.class,()->f.archive.loadMaterial(original));
        f.archive.ordinaryReads.clear();f.archive.fullReads.clear();
        assertEquals(new NativeEffectEvidence.FrameBasis(f.frame.originalEvidence(),f.manifest),RootGuardEvidence.frameBasis(guard,f.archive));
        assertEquals(f.originals.sourceQualification(),RootGuardEvidence.sourceQualification(guard,f.archive));
        assertEquals(new RootGuardEvidence.OriginalDriverSource(f.semantic.originalDriver(),f.semantic.driverStamp()),RootGuardEvidence.originalDriverSource(guard,f.archive));
        assertEquals(new RootGuardEvidence.WriterPoint(f.head.state().sequence(),f.head.digest()),RootGuardEvidence.writerPoint(guard,f.archive));
        assertEquals(f.frame,RootGuardEvidence.loadFrame(guard,f.archive,RootGuardFullMaterialLaneTest::rebuild));
        assertTrue(f.archive.fullReads.containsAll(full));assertFalse(f.archive.fullReads.contains(basis));
        for(ExactRef metadata:List.of(f.semantic.driverStamp(),f.originals.capabilities(),f.originals.sourceQualification().orElseThrow())) {
            assertTrue(f.archive.ordinaryReads.contains(metadata));assertFalse(f.archive.fullReads.contains(metadata));
        }
        for(ExactRef original:full)assertFalse(f.archive.ordinaryReads.contains(original));
        int writes=f.archive.writes;Archive cold=f.archive.cold();
        var replayed=RootGuardEvidence.loadFrame(guard,cold,RootGuardFullMaterialLaneTest::rebuild);
        assertEquals(f.frame,replayed);assertEquals(0,cold.writes);assertEquals(writes,f.archive.writes);
        assertEquals(f.frame.semantic(),DriverJson.object(cold.loadFullMaterial(f.semantic.semantic()).bytes(),DriverJson.MAX_NATIVE_BYTES));
        assertEquals(70000,OpportunityJson.integer(f.frame.semantic().get("full_original_progress"),"full original progress").toString().length());
    }
    @Test void namedMetadataAndOuterBasisKeepOrdinaryLimitsWithoutSizeOrParserFallback() {
        Fixture f=fixture();ExactRef basis=preserve(f);byte[] wide=("{\"metadata_counter\":"+"9".repeat(70000)+"}").getBytes(StandardCharsets.UTF_8);
        ExactRef extra=f.archive.preserveMaterial(RawJson.fullMaterial(wide));
        for(String role:List.of("driver_stamp","capabilities","source_qualification")) {
            ObjectNode changed=body(f.archive,basis);changed.set(role,extra.toJson());ExactRef altered=f.archive.preserveMaterial(new RawJson(StrictJson.canonical(changed)));
            f.archive.fullReads.clear();
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(guard(f,altered),f.archive));
            assertFalse(f.archive.fullReads.contains(extra),"ordinary named metadata must not fall back to full material");
        }
        ObjectNode original=body(f.archive,basis);String text=new String(StrictJson.canonical(original),StandardCharsets.UTF_8);
        byte[] oversizedBasis=(text.substring(0,text.length()-1)+",\"unregistered_counter\":"+"9".repeat(70000)+"}").getBytes(StandardCharsets.UTF_8);
        ExactRef wideBasis=f.archive.preserveMaterial(RawJson.fullMaterial(oversizedBasis));f.archive.fullReads.clear();
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(guard(f,wideBasis),f.archive));assertFalse(f.archive.fullReads.contains(wideBasis));
        assertThrows(IllegalArgumentException.class,()->new RawJson(wide));
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(wide).requireProtocolBound());
    }
    @Test void corruptOrDifferentFullSemanticCannotAcquireTheOriginalFrameBinding() {
        Fixture f=fixture();ExactRef basis=preserve(f);
        Obj changed=f.frame.semantic().with("full_original_progress",new IntegerValue(new BigInteger("8".repeat(70000))));
        ExactRef replacement=f.archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(changed)));
        ObjectNode manifest=body(f.archive,basis);manifest.set("semantic",replacement.toJson());ExactRef altered=f.archive.preserveMaterial(new RawJson(StrictJson.canonical(manifest)));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.loadFrame(guard(f,altered),f.archive,RootGuardFullMaterialLaneTest::rebuild));
        Archive corrupted=f.archive.cold();corrupted.values.put(f.semantic.originalDriver(),"{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(guard(f,basis),corrupted));
        assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(("{\"counter\":"+"9".repeat(70000)+",\"counter\":0}").getBytes(StandardCharsets.UTF_8)));
        Archive absent=f.archive.cold();absent.values.remove(f.manifest);
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(guard(f,basis),absent));
    }
    @Test void unavailableFullReaderDoesNotUseTheOrdinaryReaderAsAnAuthoritySubstitute() {
        Fixture f=fixture();ExactRef basis=preserve(f);Archive unavailable=f.archive.cold();unavailable.fullAvailable=false;
        assertThrows(UnsupportedOperationException.class,()->RootGuardEvidence.frameBasis(guard(f,basis),unavailable));
        assertFalse(unavailable.ordinaryReads.contains(f.manifest));assertEquals(0,unavailable.writes);
    }
    @Test void historicalV2StillLoadsDataAndV3HistoryPointAndAuthorityGuardsStayStrict() {
        Fixture f=fixture();ExactRef basis=preserve(f);ObjectNode legacy=body(f.archive,basis);
        legacy.put("schema","xar.java.root-guard-original-basis/v2");legacy.remove("writer_point");ExactRef old=f.archive.preserveMaterial(new RawJson(StrictJson.canonical(legacy)));
        assertEquals(f.frame,RootGuardEvidence.loadFrame(guard(f,old),f.archive,RootGuardFullMaterialLaneTest::rebuild));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.writerPoint(guard(f,old),f.archive));
        ObjectNode wrong=body(f.archive,basis);((ObjectNode)wrong.get("writer_point")).put("sequence",true);
        ExactRef bad=f.archive.preserveMaterial(new RawJson(StrictJson.canonical(wrong)));assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.writerPoint(guard(f,bad),f.archive));
        var g=guard(f,basis);var foreign=new GuardEvidence(g.origin(),g.source(),g.sessionId(),g.connectionGeneration(),g.operation(),g.nativeEvidence(),g.capabilityEvidence(),"foreign-authority",g.observedAt(),g.validUntil(),g.supportingEvidence());
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(foreign,f.archive));
        ExactRef child=f.archive.preserveMaterial(new RawJson("{\"schema\":\"unknown-derived-child\"}".getBytes(StandardCharsets.UTF_8)));
        var derived=new GuardEvidence(g.origin(),g.source(),g.sessionId(),g.connectionGeneration(),g.operation(),g.nativeEvidence(),g.capabilityEvidence(),g.authorityId(),g.observedAt(),g.validUntil(),List.of(basis,child));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(derived,f.archive));assertFalse(f.archive.fullReads.contains(child));
    }

    private record Fixture(Archive archive,DriverObservationAssembler.Complete frame,SemanticEvidence semantic,
            RootGuardEvidence.PhysicalReadOriginals originals,WriterContracts.Head head,ExactRef manifest){ }
    private static Fixture fixture() {
        Archive archive=new Archive();var base=DriverStateAssemblerTest.known();var driver=base.driver();var history=new ArrayList<>(driver.commandHistory());
        history.add(new DriverStateSnapshot.HistoryEntry(history.size()+1L,new DriverStateSnapshot.Value(("{\"index\":3,\"command\":\"original-progress-data\",\"progress\":"+"9".repeat(70000)+",\"opaque_zero\":-0.0,\"ratio\":1.0}").getBytes(StandardCharsets.UTF_8))));
        var full=new DriverStateSnapshot.Complete(driver.session(),history,driver.lastCheckpoint(),driver.rollbackWarFailure(),driver.managedRestoreTransaction(),driver.successionExpectation(),driver.successionLifecycle(),driver.campaignGoal(),driver.rollbackWarFailures());
        var stamp=new DriverSnapshotFacts.Stamp(base.stamp().driverVersion(),base.stamp().episodeEpoch(),base.stamp().game(),base.stamp().episodeRunId(),DriverJson.sha256(full.encode()));
        var known=new DriverSnapshotFacts.Known(full,stamp,base.originalHistoryBasis(),base.actionRows(),base.auxiliary(),base.loop(),Optional.empty());
        var actual=DriverObservationAssemblerTest.actual(DriverObservationAssemblerTest.STATE);ExactRef nativeRef=archive.nativeFrame(actual);
        ExactRef fullDriver=archive.preserveMaterial(RawJson.fullMaterial(full.encode()));
        Obj extras=new Obj(Map.of("full_original_progress",new IntegerValue(new BigInteger("9".repeat(70000)))));
        RawJson encodedManifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.TWO,1,DriverStateAssemblerTest.source(),extras,fullDriver);
        ExactRef manifest=archive.preserveMaterial(encodedManifest);
        DriverObservationFacts facts=DriverObservationEvidenceReader.decode(manifest,encodedManifest,archive.loadFullMaterial(fullDriver),actual);
        var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,nativeRef));
        ExactRef semanticRef=archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(frame.semantic())));
        Obj knownValue=DriverJson.object(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),DriverJson.MAX_NATIVE_BYTES);
        ExactRef stampRef=archive.preserveMaterial(new RawJson(DriverJson.encode(OpportunityJson.object(knownValue.get("stamp"),"actual stamp codec"))));
        var semantic=new SemanticEvidence(frame.identity(),semanticRef,nativeRef,stampRef,fullDriver,actual.observedAt());
        var originals=new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,small(archive,"hello"),small(archive,"heartbeat"),small(archive,"source-qualification"),small(archive,"capabilities"));
        ObjectNode state=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",frame.identity().machineId()).put("sequence",3).put("window_id",1)
                .put("status","running").put("start_date_raw",100).put("target_days",1).put("target_date_raw",124).put("last_settled_cycles",0).put("last_settled_date_raw",100);
        var head=new WriterContracts.Head(ContinuityState.fromJson(state,frame.identity().machineId()),List.of(),List.of(),List.of(),false);
        return new Fixture(archive,frame,semantic,originals,head,manifest);
    }
    private static DriverObservationAssembler.Complete rebuild(NativeEffectEvidence.FrameBasis basis,ActionPorts.OutcomeArchive archive) {
        RawJson manifest=archive.loadFullMaterial(basis.driverFacts());
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(basis.driverFacts(),manifest,archive.loadNativeFrame(basis.nativeFrame()));
        ExactRef driver=DriverObservationEvidenceReader.currentDriverReference(basis.driverFacts(),manifest);
        DriverObservationFacts facts=DriverObservationEvidenceReader.decode(basis.driverFacts(),manifest,archive.loadFullMaterial(driver),nativeFrame);
        return assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,basis.nativeFrame()));
    }
    private static ExactRef preserve(Fixture f){return RootGuardEvidence.preservePhysicalRead(f.originals,OPERATION,AUTHORITY,f.archive,f.head);}
    private static GuardEvidence guard(Fixture f,ExactRef basis){return new GuardEvidence(f.frame.identity(),f.frame.source(),f.frame.sessionId(),f.frame.connectionGeneration(),OPERATION,f.frame.originalEvidence(),f.originals.hello(),AUTHORITY,f.frame.observedAt(),f.frame.observedAt().plusSeconds(30),List.of(basis));}
    private static ObjectNode body(Archive archive,ExactRef basis){
        var value=StrictJson.parse(archive.loadMaterial(basis).bytes());
        if(value instanceof ObjectNode object)return object;
        throw new IllegalArgumentException("original material basis JSON object required");
    }
    private static ExactRef small(Archive archive,String role){return archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("software_role",role))));}

    /** Only bytes survive a cold reopen; the caller must choose the explicit original role each time. */
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Map<ExactRef,byte[]> values=new HashMap<>(),nativeFrames=new HashMap<>();
        private final Set<ExactRef> ordinaryReads=new LinkedHashSet<>(),fullReads=new LinkedHashSet<>();
        private int writes;private boolean fullAvailable=true;
        private ExactRef ref(String role,byte[] bytes){return new ExactRef("software-guard-full/"+role+"/"+DriverJson.sha256(bytes),bytes.length,DriverJson.sha256(bytes));}
        private Archive cold(){var copy=new Archive();values.forEach((ref,bytes)->copy.values.put(ref,bytes.clone()));nativeFrames.forEach((ref,bytes)->copy.nativeFrames.put(ref,bytes.clone()));return copy;}
        private byte[] bytes(ExactRef ref){byte[] bytes=values.get(ref);if(bytes==null)throw new IllegalArgumentException("original material missing");return bytes.clone();}
        private ExactRef nativeFrame(NativeObservationPort.ObservedFrame original){ExactRef ref=ref("native",original.originalPacket());nativeFrames.put(ref,original.originalPacket());return ref;}
        @Override public ExactRef preserveMaterial(RawJson original){ExactRef ref=ref("material",original.bytes());values.putIfAbsent(ref,original.bytes());writes++;return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){ordinaryReads.add(ref);return new RawJson(bytes(ref));}
        @Override public RawJson loadFullMaterial(ExactRef ref){if(!fullAvailable)throw new UnsupportedOperationException("full material capability unavailable");fullReads.add(ref);return RawJson.fullMaterial(bytes(ref));}
        @Override public ExactRef materialReferenceOf(RawJson raw){ExactRef ref=ref("material",raw.bytes());if(!java.util.Arrays.equals(raw.bytes(),values.get(ref)))throw new IllegalArgumentException("original material not retained");return ref;}
        @Override public byte[] loadNativeFrame(ExactRef ref){byte[] bytes=nativeFrames.get(ref);if(bytes==null)throw new IllegalArgumentException("original native frame missing");return bytes.clone();}
        private UnsupportedOperationException unavailable(){return new UnsupportedOperationException("DATA-only archive has no Native/Root/Session/writer authority");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original){throw unavailable();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original){throw unavailable();}
        @Override public ExactRef preserveRequest(NativeRequest original){throw unavailable();}
        @Override public NativeRequest loadRequest(ExactRef original){throw unavailable();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original){throw unavailable();}
        @Override public ExactRef requestReferenceOf(NativeRequest original){throw unavailable();}
        @Override public ExactRef preserveRead(PlanningReadReceipt original){throw unavailable();}
        @Override public PlanningReadReceipt loadRead(ExactRef original){throw unavailable();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original){throw unavailable();}
        @Override public ExactRef preserveRecord(ActionRecord original){throw unavailable();}
        @Override public ActionRecord loadRecord(ExactRef original){throw unavailable();}
        @Override public ExactRef recordReferenceOf(ActionRecord original){throw unavailable();}
        @Override public ExactRef preserveReceipt(ActionReceipt original){throw unavailable();}
        @Override public ActionReceipt loadReceipt(ExactRef original){throw unavailable();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt original){throw unavailable();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original){throw unavailable();}
    }
}

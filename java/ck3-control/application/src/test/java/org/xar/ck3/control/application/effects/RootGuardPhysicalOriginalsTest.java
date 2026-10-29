package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.ParentProof;
import org.xar.ck3.control.application.effects.control.ControlSequenceObservation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Sole physical DATA producer -> existing v3 strict readers. No LeaseSnapshot, source, writer or Ready authority is synthesized. */
final class RootGuardPhysicalOriginalsTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final class Materials implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> values=new HashMap<>();boolean corruptPublishedDigest;
        @Override public ExactRef preserveMaterial(RawJson raw){var ref=new ExactRef(java.nio.file.Path.of(System.getProperty("java.io.tmpdir"),"xar-physical-guard-data",values.size()+".json").toAbsolutePath().toString(),raw.bytes().length,corruptPublishedDigest?"0".repeat(64):ActionCodec.sha256(raw.bytes()));values.put(ref,raw);return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){return java.util.Objects.requireNonNull(values.get(ref));}
        @Override public RawJson loadFullMaterial(ExactRef ref){return RawJson.fullMaterial(java.util.Objects.requireNonNull(values.get(ref)).bytes());}
        @Override public ExactRef materialReferenceOf(RawJson raw){return values.entrySet().stream().filter(row->row.getValue().equals(raw)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        @Override public byte[] loadNativeFrame(ExactRef ref){return loadMaterial(ref).bytes();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original){throw new IllegalStateException("software DATA archive has no preserve authority");}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original){throw new IllegalStateException("software DATA archive has no load authority");}
        @Override public ExactRef preserveRequest(NativeRequest original){throw new IllegalStateException("software DATA archive has no preserveRequest authority");}
        @Override public NativeRequest loadRequest(ExactRef original){throw new IllegalStateException("software DATA archive has no loadRequest authority");}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original){throw new IllegalStateException("software DATA archive has no referenceOf authority");}
        @Override public ExactRef requestReferenceOf(NativeRequest original){throw new IllegalStateException("software DATA archive has no requestReferenceOf authority");}
        @Override public ExactRef preserveRead(PlanningReadReceipt original){throw new IllegalStateException("software DATA archive has no preserveRead authority");}
        @Override public PlanningReadReceipt loadRead(ExactRef original){throw new IllegalStateException("software DATA archive has no loadRead authority");}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original){throw new IllegalStateException("software DATA archive has no readReferenceOf authority");}
        @Override public ExactRef preserveRecord(ActionRecord original){throw new IllegalStateException("software DATA archive has no preserveRecord authority");}
        @Override public ActionRecord loadRecord(ExactRef original){throw new IllegalStateException("software DATA archive has no loadRecord authority");}
        @Override public ExactRef recordReferenceOf(ActionRecord original){throw new IllegalStateException("software DATA archive has no recordReferenceOf authority");}
        @Override public ExactRef preserveReceipt(ActionReceipt original){throw new IllegalStateException("software DATA archive has no preserveReceipt authority");}
        @Override public ActionReceipt loadReceipt(ExactRef original){throw new IllegalStateException("software DATA archive has no loadReceipt authority");}
        @Override public ExactRef receiptReferenceOf(ActionReceipt original){throw new IllegalStateException("software DATA archive has no receiptReferenceOf authority");}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original){throw new IllegalStateException("software DATA archive has no preserveNativeFrame authority");}
    }

    private record Fixture(Materials archive,Complete frame,SemanticEvidence semantic,RootGuardEvidence.PhysicalReadOriginals originals,WriterContracts.Head head){}
    private static ExactRef material(Materials archive,String name){return archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("software_role",name))));}
    private static WriterContracts.Head head(String machine){
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",machine).put("sequence",3).put("window_id",1)
                .put("status","running").put("start_date_raw",100).put("target_days",1).put("target_date_raw",124)
                .put("last_settled_cycles",0).put("last_settled_date_raw",100);
        return new WriterContracts.Head(ContinuityState.fromJson(row,machine),List.of(),List.of(),List.of(),false);
    }
    private static Fixture fixture(){return fixture(0,0);}
    private static Fixture fixture(int historyBytes,int fullDepth){
        var archive=new Materials();var nativeRef=material(archive,"native");var driver=material(archive,"driver-facts");var sourceRef=material(archive,"source");
        var source=new G2Source("synthetic-physical-machine",NOW.toString(),"1.20.0.4",sourceRef);
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var state=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(19),BigInteger.valueOf(53),BigInteger.valueOf(100)),
                "native:53",BigInteger.valueOf(55),"synthetic-physical-episode");
        var identity=new ObservationIdentity(source.machineId(),game,state,1);var row=StrictJson.object().put("software_only",true);row.set("java_driver_facts_evidence",driver.toJson());
        if(historyBytes>0)row.put("retained_driver_history","x".repeat(historyBytes));
        var nested=row;for(int i=0;i<fullDepth;i++)nested=nested.putObject("nested_original");
        nested.put("kind","software-full-data-only");
        var value=DriverJson.object(DriverJson.encodeNode(row),DriverJson.MAX_NATIVE_BYTES);
        var frame=new Complete(identity,source,"synthetic-physical-session",BigInteger.TWO,value,nativeRef,NOW,"a".repeat(64));
        var semantic=new SemanticEvidence(identity,archive.preserveMaterial(new RawJson(DriverJson.encode(value))),nativeRef,material(archive,"stamp"),material(archive,"full-driver"),NOW);
        var originals=new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,material(archive,"hello"),material(archive,"heartbeat"),material(archive,"source-qualification"),material(archive,"capabilities"));
        return new Fixture(archive,frame,semantic,originals,head(source.machineId()));
    }
    private static GuardEvidence guard(Fixture f,ExactRef basis){
        return new GuardEvidence(f.frame().identity(),f.frame().source(),f.frame().sessionId(),f.frame().connectionGeneration(),
                new OperationKey("query-actual-physical-domain"),f.frame().originalEvidence(),f.originals().hello(),"physical-data-authority",NOW,NOW.plusSeconds(30),List.of(basis));
    }
    private static ExactRef preserve(Fixture f){
        return RootGuardEvidence.preservePhysicalRead(f.originals(),new OperationKey("query-actual-physical-domain"),"physical-data-authority",f.archive(),f.head());
    }
    @Test void solePhysicalProducerRoundtripsThroughExistingFrameSourceDriverAndWriterPointReaders(){
        var f=fixture();var basis=preserve(f);var guard=guard(f,basis);
        assertEquals(RootGuardEvidence.SCHEMA,StrictJson.parse(f.archive().loadMaterial(basis).bytes()).get("schema").textValue());
        assertEquals(NativeEffectEvidence.basis(f.frame()),RootGuardEvidence.frameBasis(guard,f.archive()));
        assertEquals(f.originals().sourceQualification(),RootGuardEvidence.sourceQualification(guard,f.archive()));
        assertEquals(new RootGuardEvidence.OriginalDriverSource(f.semantic().originalDriver(),f.semantic().driverStamp()),RootGuardEvidence.originalDriverSource(guard,f.archive()));
        assertEquals(new RootGuardEvidence.WriterPoint(f.head().state().sequence(),f.head().digest()),RootGuardEvidence.writerPoint(guard,f.archive()));
        // This returns fixture DATA only after requiring the exact original pair. Actual callers provide the sole real DriverFrameEvidenceLoader.
        var replayed=RootGuardEvidence.loadFrame(guard,f.archive(),(original,archive)->{
            assertEquals(NativeEffectEvidence.basis(f.frame()),original);assertSame(f.archive(),archive);return f.frame();
        });
        assertEquals(f.frame(),replayed);
    }
    @Test void absentSourceQualificationRemainsNullAndReplaysTheActualFrameWithoutAProofRead(){
        var f=fixture();
        var absent=new RootGuardEvidence.PhysicalReadOriginals(f.frame(),f.semantic(),f.originals().hello(),
                f.originals().heartbeat(),java.util.Optional.empty(),f.originals().capabilities());
        f.archive().values.remove(f.originals().sourceQualification().orElseThrow());
        var ref=RootGuardEvidence.preservePhysicalRead(absent,new OperationKey("query-actual-physical-domain"),
                "physical-data-authority",f.archive(),f.head());
        var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(f.archive().loadMaterial(ref).bytes());
        assertTrue(row.has("source_qualification")&&row.get("source_qualification").isNull());
        assertTrue(RootGuardEvidence.sourceQualification(guard(f,ref),f.archive()).isEmpty());
        assertEquals(f.frame(),RootGuardEvidence.loadFrame(guard(f,ref),f.archive(),(pair,archive)->f.frame()));
        row.remove("source_qualification");
        var missing=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(row)));
        assertTrue(RootGuardEvidence.sourceQualification(guard(f,missing),f.archive()).isEmpty());
        assertEquals(f.frame(),RootGuardEvidence.loadFrame(guard(f,missing),f.archive(),(pair,archive)->f.frame()));
        for(var invalid:List.of(StrictJson.parse("true".getBytes(java.nio.charset.StandardCharsets.UTF_8)),
                StrictJson.parse("[]".getBytes(java.nio.charset.StandardCharsets.UTF_8)),StrictJson.object())) {
            row.set("source_qualification",invalid);
            var wrong=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(row)));
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.sourceQualification(guard(f,wrong),f.archive()));
        }
    }
    @Test void differentNativePacketOrObservedTimeCannotBeMixedIntoTheTypedOriginals(){
        var f=fixture();var different=material(f.archive(),"another-native");
        var packet=new SemanticEvidence(f.frame().identity(),f.semantic().semantic(),different,f.semantic().driverStamp(),f.semantic().originalDriver(),NOW);
        var time=new SemanticEvidence(f.frame().identity(),f.semantic().semantic(),f.semantic().originalNativePacket(),f.semantic().driverStamp(),f.semantic().originalDriver(),NOW.plusNanos(1));
        for(var invalid:List.of(packet,time))assertThrows(IllegalArgumentException.class,()->new RootGuardEvidence.PhysicalReadOriginals(f.frame(),invalid,
                f.originals().hello(),f.originals().heartbeat(),f.originals().sourceQualification(),f.originals().capabilities()));
    }
    @Test void physicalDataCannotBorrowAnotherFrameIdentityOrWriterMachine(){
        var f=fixture();var before=f.frame().identity();var current=before.frame();
        var otherFrame=new JointBudgetSelector.ProposalFrame(current.identity(),"native:54",current.revision(),current.episodeRunId());
        var other=new ObservationIdentity(before.machineId(),before.game(),otherFrame,before.observationVersion());
        var wrong=new SemanticEvidence(other,f.semantic().semantic(),f.semantic().originalNativePacket(),f.semantic().driverStamp(),f.semantic().originalDriver(),NOW);
        assertThrows(IllegalArgumentException.class,()->new RootGuardEvidence.PhysicalReadOriginals(f.frame(),wrong,f.originals().hello(),f.originals().heartbeat(),f.originals().sourceQualification(),f.originals().capabilities()));
        int beforeWrites=f.archive().values.size();
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.preservePhysicalRead(f.originals(),new OperationKey("query-actual-physical-domain"),"physical-data-authority",f.archive(),head("foreign-machine")));
        assertEquals(beforeWrites,f.archive().values.size());
    }
    @Test void immutablePublisherDigestIsCheckedBeforeAReferenceCanEscape(){
        var f=fixture();f.archive().corruptPublishedDigest=true;
        assertThrows(IllegalArgumentException.class,()->preserve(f));
    }
    @Test void exactV3DecoderRejectsChangedBasisBytesAndWrongWriterPointScalarType(){
        var f=fixture();var ref=preserve(f);var raw=f.archive().loadMaterial(ref);
        f.archive().values.put(ref,new RawJson(new byte[]{'{','}'}));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(guard(f,ref),f.archive()));
        var changed=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(raw.bytes());
        ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("writer_point")).put("sequence",true);
        var malformed=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(changed)));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.writerPoint(guard(f,malformed),f.archive()));
    }
    @Test void nonemptyRoleAndActualRebuiltFullFrameGuardsRemainRequired(){
        var f=fixture();var empty=new ExactRef(f.originals().hello().path(),0,f.originals().hello().sha256());
        assertThrows(IllegalArgumentException.class,()->new RootGuardEvidence.PhysicalReadOriginals(f.frame(),f.semantic(),empty,f.originals().heartbeat(),f.originals().sourceQualification(),f.originals().capabilities()));
        var otherSource=new G2Source(f.frame().source().machineId(),f.frame().source().observedAtUtc(),"1.20.0.4",material(f.archive(),"foreign-source"));
        var wrong=new Complete(f.frame().identity(),otherSource,f.frame().sessionId(),f.frame().connectionGeneration(),f.frame().semantic(),f.frame().originalEvidence(),NOW,f.frame().fullBindingSha256());
        var ref=preserve(f);assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.loadFrame(guard(f,ref),f.archive(),(basis,archive)->wrong));
    }

    @Test void fullSemAboveRequestAndReceiptBudgetsUsesTheSoleFullDriverDataLane(){
        for(int bytes:List.of(131073,1048577)){
            var f=fixture(bytes,0);byte[] full=DriverJson.encode(f.frame().semantic());
            assertTrue(full.length>bytes);
            if(bytes>1048576)assertThrows(IllegalArgumentException.class,()->StrictJson.parse(full,1048576));
            // This is the real pre-fix parser and its original request guard remains strict.
            assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(full));
            assertDoesNotThrow(()->RootGuardChecks.requireSemanticOriginal(f.frame(),f.archive().loadMaterial(f.semantic().semantic())));
            var basis=preserve(f);
            assertEquals(f.frame(),RootGuardEvidence.loadFrame(guard(f,basis),f.archive(),(actual,archive)->{
                assertEquals(NativeEffectEvidence.basis(f.frame()),actual);assertSame(f.archive(),archive);return f.frame();
            }));
        }
    }
    @Test void fullSemAboveRequestDepthRetainsTheExistingDriverDepthInsteadOfBroadeningRequests(){
        var f=fixture(0,40);byte[] full=DriverJson.encode(f.frame().semantic());
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(full));
        assertDoesNotThrow(()->RootGuardChecks.requireSemanticOriginal(f.frame(),f.archive().loadMaterial(f.semantic().semantic())));
        var basis=preserve(f);assertEquals(f.frame(),RootGuardEvidence.loadFrame(guard(f,basis),f.archive(),(actual,archive)->f.frame()));
    }
    @Test void fullSemStillRejectsDuplicateFieldsAndDifferentOriginalSemanticContent(){
        var f=fixture(1048577,0);var basis=preserve(f);
        for(String invalid:List.of("{\"retained_driver_history\":\""+ "x".repeat(1048577)+"\",\"retained_driver_history\":0}",
                "{\"different_retained_driver_history\":\""+ "x".repeat(1048577)+"\"}")){
            var content=f.archive().preserveMaterial(new RawJson(invalid.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            var manifest=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(f.archive().loadMaterial(basis).bytes());
            manifest.set("semantic",content.toJson());var changed=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(manifest)));
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.loadFrame(guard(f,changed),f.archive(),(actual,archive)->f.frame()));
        }
    }
    private record ParentData(Fixture fixture,ActionCommand parent,ParentProof proof,GuardEvidence guard,ExactRef basis,ExactRef proofRef) { }
    private static ParentData publicParentData(){
        var f=fixture();var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,f.frame().identity(),f.frame().source(),
                ControlSequenceObservation.OBSERVER,ControlSequenceObservation.expected());
        var parent=new ActionCommand("software-public-pause-parent",f.frame().identity(),f.frame().source(),f.frame().sessionId(),ControlSequenceObservation.OPERATION,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()),expected,
                new JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),NOW.plusSeconds(30));
        var runtime=material(f.archive(),"software-parent-runtime-source");var product=material(f.archive(),"software-parent-product-source");
        var caller=new RawJson(StrictJson.canonical(StrictJson.object().put("step","pause-map").put("software_original_call",true)));
        var proof=new ParentProof(parent,caller,f.frame().originalEvidence(),NativeEffectEvidence.basis(f.frame()).driverFacts(),runtime,product,List.of(runtime,product),f.head().state().sequence(),f.head().digest());
        var proofRef=f.archive().preserveMaterial(new RawJson(proof.encode()));
        var basis=RootGuardEvidence.preservePhysicalRead(f.originals(),parent.operation(),"software-parent-data-authority",f.archive(),f.head());
        var guard=new GuardEvidence(parent.before(),parent.source(),parent.sessionId(),f.frame().connectionGeneration(),parent.operation(),f.frame().originalEvidence(),f.originals().hello(),
                "software-parent-data-authority",NOW,NOW.plusSeconds(30),List.of(basis,proofRef));
        return new ParentData(f,parent,proof,guard,basis,proofRef);
    }
    private static GuardEvidence parentLocator(ParentData data,ExactRef proof){var g=data.guard();return new GuardEvidence(g.origin(),g.source(),g.sessionId(),g.connectionGeneration(),g.operation(),g.nativeEvidence(),g.capabilityEvidence(),g.authorityId(),g.observedAt(),g.validUntil(),List.of(data.basis(),proof));}
    @Test void typedPublicParentLocatorAndNamedSemReplayAsDataWithoutGrantingAPrivateSource(){
        var data=publicParentData();var f=data.fixture();int files=f.archive().values.size();
        assertEquals(data.proof(),ParentProof.decode(f.archive().loadMaterial(data.proofRef()).bytes()));
        assertEquals(NativeEffectEvidence.basis(f.frame()),RootGuardEvidence.frameBasis(data.guard(),f.archive()));
        assertEquals(f.semantic().semantic(),RootGuardEvidence.semanticReference(data.guard(),f.archive()));
        assertEquals(f.frame(),RootGuardEvidence.loadFrame(data.guard(),f.archive(),(pair,archive)->f.frame()));
        assertEquals(files,f.archive().values.size());
        // Materials supplies no Session, Source, Lease or archived callback. These are DATA assertions only;
        // the mandatory installed PublicPauseAuthority/Kernel callback must independently qualify a real parent.
    }
    @Test void publicParentRejectsFullDriverInManifestRoleAndDifferentOriginalWriterPoint(){
        var data=publicParentData();var f=data.fixture();var p=data.proof();
        for(var wrong:List.of(new ParentProof(p.parent(),p.originalCaller(),p.beforeNative(),f.semantic().originalDriver(),p.runtimeSource(),p.productSource(),p.sourceClosure(),p.writerSequence(),p.writerDigest()),
                new ParentProof(p.parent(),p.originalCaller(),p.beforeNative(),p.beforeDriver(),p.runtimeSource(),p.productSource(),p.sourceClosure(),p.writerSequence()+1,p.writerDigest()))){
            var ref=f.archive().preserveMaterial(new RawJson(wrong.encode()));
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(parentLocator(data,ref),f.archive()));
        }
    }
    @Test void publicParentRejectsTamperedCallerBodyUnknownLocatorAndForeignRootGuard(){
        var data=publicParentData();var f=data.fixture();
        var bad=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(data.proof().encode());bad.put("original_caller_sha256","f".repeat(64));
        var caller=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(bad)));assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.semanticReference(parentLocator(data,caller),f.archive()));
        var unknown=f.archive().preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("schema","xar.java.public-pause-parent-call-proof/v999"))));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(parentLocator(data,unknown),f.archive()));
        var g=data.guard();var foreign=new GuardEvidence(g.origin(),g.source(),"another-session",g.connectionGeneration(),g.operation(),g.nativeEvidence(),g.capabilityEvidence(),g.authorityId(),g.observedAt(),g.validUntil(),g.supportingEvidence());
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(foreign,f.archive()));
    }
}

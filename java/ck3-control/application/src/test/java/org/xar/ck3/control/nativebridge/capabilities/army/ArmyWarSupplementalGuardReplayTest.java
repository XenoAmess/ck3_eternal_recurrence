package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual new family -> sole physical guard DATA serializer/readers -> two loaded snapshots -> existing Adapter.
 * The strict stored-pair FrameLoader is software DATA, not the real DriverFrameEvidenceLoader or a Root lease.
 * No transport custody, writer Session, Native permission or current Root is fabricated. */
final class ArmyWarSupplementalGuardReplayTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T10:30:00Z");
    private static final String AUTHORITY="supplemental-software-original-data";
    private static final ExactRef SOURCE=new ExactRef("software-supplemental-guard-definition",1,"a".repeat(64));
    private record Fixture(DataArchive archive,ArmyWarSupplementalReads reads,RootReadContractCatalog catalog,
            Selection selection,PlanningReadReceipt receipt,Complete before,Complete after,
            List<NativeEffectEvidence.FrameBasis> loaded,ObjectNode expected){ }

    @Test void realFamilyLoadsBothOriginalGuardSlotsBeforeBaselineAndPreservesCanonicalReplay()throws Exception{
        Fixture f=fixture(false);Observation observation=f.reads.replay(f.catalog,f.selection,f.receipt);
        assertInstanceOf(DefenderBaseline.class,observation);assertEquals(f.expected,ArmyWarSupplementalReadCodec.object(observation.normalizedResult()));
        assertEquals(List.of(NativeEffectEvidence.basis(f.before),NativeEffectEvidence.basis(f.after)),f.loaded);
        assertNotEquals(NativeEffectEvidence.basis(f.before),NativeEffectEvidence.basis(f.after),"test originals independently name before and after slots");
        var reference=f.archive.preserveRead(f.receipt);assertEquals(observation,f.reads.replayArchived(f.catalog,f.selection,reference,f.archive));
        assertEquals(4,f.loaded.size());assertEquals(NativeEffectEvidence.basis(f.after),f.loaded.get(3));
        RawJson wire=ArmyWarSupplementalReadCodec.fullDriverResult(observation);
        assertEquals(wire,new RawJson(DriverJson.encode(DriverJson.object(wire.bytes(),ArmyWarSupplementalReadCodec.MAX_BYTES))));
        assertTrue(ArmyWarSupplementalReadCodec.object(wire).path("defender_de_jure_exit_terms_v1").path("directed_truce").isNull());
        assertEquals(f.receipt.original().originalResultToken().orElseThrow(),observation.nativeResult());
    }
    @Test void independentlyLoadedChangedAfterWarAndMissingAfterBasisCannotUseBeforeAsFallback()throws Exception{
        Fixture changed=fixture(true);assertThrows(RuntimeException.class,()->changed.reads.replay(changed.catalog,changed.selection,changed.receipt));
        assertEquals(List.of(NativeEffectEvidence.basis(changed.before),NativeEffectEvidence.basis(changed.after)),changed.loaded);
        Fixture missing=fixture(false);missing.archive.materials.remove(NativeEffectEvidence.basis(missing.after).driverFacts());
        assertThrows(RuntimeException.class,()->missing.reads.replay(missing.catalog,missing.selection,missing.receipt));
        assertTrue(missing.loaded.size()<2,"missing actual after basis must not silently reuse before");
    }
    private Fixture fixture(boolean changedWar)throws Exception{
        ObjectNode corpus=ArmyWarSupplementalOriginalInputs.capture(temporary);ObjectNode row=null;
        for(var value:corpus.get("cases"))if(value.path("name").textValue().equals("original-driver-baseline")){row=(ObjectNode)value;break;}
        assertNotNull(row);DataArchive archive=new DataArchive();OperationKey operation=new OperationKey(row.path("raw").path("step").textValue());
        Selection seed=ArmyWarSupplementalReadTest.selected((ObjectNode)row.get("before"),operation);
        Complete before=frame(seed,(ObjectNode)row.get("before"),archive,"before",AT);
        ObjectNode afterSnapshot=((ObjectNode)row.get("after")).deepCopy();if(changedWar)((ObjectNode)afterSnapshot.path("active_wars").get(0)).putArray("targeted_title_ids").add(999);
        Complete after=frame(seed,afterSnapshot,archive,"after",AT.plusSeconds(1));
        var old=seed.original();var observed=old.observations();var original=new org.xar.ck3.control.application.planning.PlanningRequest(old.before(),old.source(),old.sessionId(),old.deadline(),
                new org.xar.ck3.control.application.planning.PlanningObservation(before.semantic(),observed.history(),observed.actionSteps(),observed.bridgeCapabilities(),observed.battleSpeedReadiness(),observed.actionFacts(),observed.campaignGoal(),observed.crossRunPlan(),observed.initialLifestyleFocusRequired()));
        Selection selected=new Selection(original,operation);var loaded=new ArrayList<NativeEffectEvidence.FrameBasis>();
        Map<NativeEffectEvidence.FrameBasis,Complete> stored=Map.of(NativeEffectEvidence.basis(before),before,NativeEffectEvidence.basis(after),after);
        NativeEffectEvidence.FrameLoader frameLoader=(basis,same)->{
            assertSame(archive,same);assertNotNull(same.loadFullMaterial(basis.driverFacts()));assertTrue(same.loadNativeFrame(basis.nativeFrame()).length>0);
            Complete actual=stored.get(basis);if(actual==null)throw new IllegalArgumentException("unregistered actual original DATA pair");loaded.add(basis);return actual;
        };
        var noQuery=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("guard DATA replay cannot query Native");}};
        var reads=new ArmyWarSupplementalReads(new Sources(SOURCE,SOURCE,SOURCE,SOURCE),noQuery,()->archive,frameLoader,
                (s,r)->{assertEquals(selected,s);assertEquals(operation,r.request().operation());});
        var catalog=new RootReadContractCatalog(List.of(),reads.families());var issued=reads.issue(catalog,selected);
        GuardEvidence first=guard(before,operation,archive,"before"),last=guard(after,operation,archive,"after");
        var guardBefore=new PlanningReadGuard(first,true,true,true,"b".repeat(64));var guardAfter=new PlanningReadGuard(last,true,true,true,"b".repeat(64));
        var raw=ArmyWarSupplementalReadCodec.json(row.get("raw"));String requestId="software-defender-original";
        var top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",requestId).put("ok",true);top.set("result",row.get("raw"));RawJson full=ArmyWarSupplementalReadCodec.json(top);
        var ack=new NativeActionPort.AckReceived(requestId,true,Optional.of(raw),full,full.bytes());
        var receipt=new PlanningReadReceipt(issued.request(),issued.contract().contractId(),requestId,guardBefore,guardAfter,ack);
        return new Fixture(archive,reads,catalog,selected,receipt,before,after,loaded,(ObjectNode)row.get("expected"));
    }
    private static Complete frame(Selection selected,ObjectNode snapshot,DataArchive archive,String slot,Instant observed){
        ExactRef nativeFrame=archive.material("native-"+slot),driver=archive.material("driver-facts-"+slot);
        ObjectNode value=snapshot.deepCopy();value.set("java_driver_facts_evidence",driver.toJson());OpportunityJson.Obj semantic=DriverJson.object(ArmyWarSupplementalReadCodec.json(value).bytes(),DriverJson.MAX_NATIVE_BYTES);
        return new Complete(selected.original().before(),selected.original().source(),selected.original().sessionId(),BigInteger.ONE,semantic,nativeFrame,observed,"c".repeat(64));
    }
    private static GuardEvidence guard(Complete actual,OperationKey operation,DataArchive archive,String slot){
        var semantic=new SemanticEvidence(actual.identity(),archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(actual.semantic()))),actual.originalEvidence(),archive.material("stamp-"+slot),archive.material("full-driver-"+slot),actual.observedAt());
        var originals=new RootGuardEvidence.PhysicalReadOriginals(actual,semantic,archive.material("hello-"+slot),archive.material("heartbeat-"+slot),archive.material("source-qualification-"+slot),archive.material("capabilities-"+slot));
        var row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",actual.identity().machineId()).put("sequence",3).put("window_id",1).put("status","running")
                .put("start_date_raw",100).put("target_days",1).put("target_date_raw",124).put("last_settled_cycles",0).put("last_settled_date_raw",100);
        var head=new WriterContracts.Head(ContinuityState.fromJson(row,actual.identity().machineId()),List.of(),List.of(),List.of(),false);
        ExactRef basis=RootGuardEvidence.preservePhysicalRead(originals,operation,AUTHORITY,archive,head);
        return new GuardEvidence(actual.identity(),actual.source(),actual.sessionId(),actual.connectionGeneration(),operation,actual.originalEvidence(),originals.hello(),AUTHORITY,actual.observedAt(),AT.plusSeconds(60),List.of(basis));
    }
    /** Immutable bytes and original receipt objects only; no canonical writer/native/permission implementation. */
    private static final class DataArchive implements ActionPorts.OutcomeArchive{
        private final Map<ExactRef,byte[]> materials=new HashMap<>();private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        private ExactRef exact(String role,byte[] value){return new ExactRef("software-supplemental-data/"+role+"/"+materials.size(),value.length,ActionCodec.sha256(value));}
        private ExactRef material(String role){return preserveMaterial(ArmyWarSupplementalReadCodec.json(StrictJson.object().put("software_role",role)));}
        @Override public ExactRef preserveMaterial(RawJson raw){var ref=exact("material",raw.bytes());materials.put(ref,raw.bytes());return ref;}
        @Override public RawJson loadMaterial(ExactRef ref){return new RawJson(java.util.Objects.requireNonNull(materials.get(ref),"actual original material absent"));}
        @Override public RawJson loadFullMaterial(ExactRef ref){return RawJson.fullMaterial(java.util.Objects.requireNonNull(materials.get(ref),"actual original full material absent"));}
        @Override public ExactRef materialReferenceOf(RawJson raw){return materials.entrySet().stream().filter(e->java.util.Arrays.equals(e.getValue(),raw.bytes())).map(Map.Entry::getKey).findFirst().orElseThrow();}
        @Override public byte[] loadNativeFrame(ExactRef ref){return java.util.Objects.requireNonNull(materials.get(ref),"native original absent").clone();}
        @Override public ExactRef preserveRead(PlanningReadReceipt receipt){preserve(receipt.original());ExactRef ref=material("read-object-"+reads.size());reads.put(ref,receipt);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return java.util.Objects.requireNonNull(reads.get(ref));}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt receipt){return reads.entrySet().stream().filter(e->e.getValue().equals(receipt)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original){ExactRef ref=material("outcome-object-"+outcomes.size());outcomes.put(ref,original);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return java.util.Objects.requireNonNull(outcomes.get(ref));}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original){return outcomes.entrySet().stream().filter(e->e.getValue().equals(original)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        private UnsupportedOperationException unavailable(){return new UnsupportedOperationException("software DATA archive has no native/Root/writer/Session authority");}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unavailable();}
        @Override public NativeRequest loadRequest(ExactRef value){throw unavailable();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unavailable();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unavailable();}
        @Override public ActionRecord loadRecord(ExactRef value){throw unavailable();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unavailable();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unavailable();}
        @Override public ActionReceipt loadReceipt(ExactRef value){throw unavailable();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unavailable();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unavailable();}
    }
}

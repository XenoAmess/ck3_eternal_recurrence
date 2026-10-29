package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDerivedAdmissionEvidence;

/** Root basis and closed locator DATA only. No history/derived-child/source/native qualification is manufactured. */
final class RootGuardDerivedLocatorTest {
    private static final Instant NOW=Instant.parse("2026-10-24T00:00:00Z");
    private static final class Materials implements ActionPorts.OutcomeArchive {
        final Map<ExactRef,RawJson> values=new HashMap<>();
        @Override public ExactRef preserveMaterial(RawJson raw){var ref=new ExactRef("synthetic/"+values.size(),raw.bytes().length,ActionCodec.sha256(raw.bytes()));values.put(ref,raw);return ref;}
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
    private record Fixture(Materials archive,GuardEvidence guard,ExactRef nativeRef,ExactRef driverRef,ExactRef proofRef){}
    private static ExactRef material(Materials archive,String name){return archive.preserveMaterial(new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(StrictJson.object().put("software_role",name))));}
    private static Fixture fixture(boolean wrongNative,boolean wrongDriver){
        var archive=new Materials();var nativeRef=material(archive,"native");var driverRef=material(archive,"driver");var hello=material(archive,"hello");
        var row=StrictJson.object().put("schema",RootGuardEvidence.SCHEMA).put("operation","life-advance").put("authority_id","synthetic-derived");
        row.set("native_frame",nativeRef.toJson());row.set("driver_facts",driverRef.toJson());row.set("hello",hello.toJson());
        for(var name:List.of("semantic","driver_stamp","original_driver","capabilities","heartbeat","source_qualification"))row.set(name,material(archive,name).toJson());
        row.putObject("writer_point").put("sequence",0).put("digest","a".repeat(64));var basis=archive.preserveMaterial(new RawJson(StrictJson.canonical(row)));
        var leaf=material(archive,"typed-locator-input");var proof=new RootDerivedChildEvidence(0,"a".repeat(64),"timeline-handler",leaf,"b".repeat(64),"c".repeat(64),1,
                nativeRef,driverRef,wrongNative?leaf:nativeRef,wrongDriver?leaf:driverRef,leaf,leaf,leaf,leaf,leaf,leaf,List.of());
        var proofRef=archive.preserveMaterial(proof.encode());var source=new G2Source("synthetic-derived-machine",NOW.toString(),"1.20.0.4",leaf);
        var game=new GameGeneration(991,new PythonOnlyUInt64(new BigInteger("133700000000000001")));
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(19),BigInteger.valueOf(53),BigInteger.valueOf(100)),"native:53",BigInteger.valueOf(55),"synthetic-derived-episode");
        var identity=new ObservationIdentity(source.machineId(),game,frame,1);
        var guard=new GuardEvidence(identity,source,"synthetic-derived-session",BigInteger.TWO,new OperationKey("life-advance"),nativeRef,hello,"synthetic-derived",NOW,NOW.plusSeconds(30),List.of(basis,proofRef));
        return new Fixture(archive,guard,nativeRef,driverRef,proofRef);
    }
    @Test void exactRootLocatorCanReadItsNamedBasisWithoutMintingHistoricalAuthority(){
        var fixture=fixture(false,false);var actual=RootGuardEvidence.frameBasis(fixture.guard(),fixture.archive());
        assertEquals(fixture.nativeRef(),actual.nativeFrame());assertEquals(fixture.driverRef(),actual.driverFacts());
        assertEquals(new RootGuardEvidence.WriterPoint(0,"a".repeat(64)),RootGuardEvidence.writerPoint(fixture.guard(),fixture.archive()));
        assertEquals(RootDerivedChildEvidence.decode(fixture.archive().loadMaterial(fixture.proofRef())),
                RootDerivedChildEvidence.requireGuard(fixture.guard(),fixture.archive()));
    }
    @Test void rootLocatorCannotReplaceEitherActualBeforeNativeOrDriver(){
        for(var fixture:List.of(fixture(true,false),fixture(false,true)))
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(fixture.guard(),fixture.archive()));
    }
    @Test void unknownOrArmySchemaCannotBeAnAliasForRootDerivedFields(){
        for(var schema:List.of("xar.java.root-derived-child-admission/v0",ArmyDerivedAdmissionEvidence.SCHEMA)){
            var fixture=fixture(false,false);var value=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(fixture.archive().loadMaterial(fixture.proofRef()).bytes());
            value.put("schema",schema);var ref=fixture.archive().preserveMaterial(new RawJson(StrictJson.canonical(value)));var previous=fixture.guard();
            var changed=new GuardEvidence(previous.origin(),previous.source(),previous.sessionId(),previous.connectionGeneration(),previous.operation(),previous.nativeEvidence(),previous.capabilityEvidence(),previous.authorityId(),previous.observedAt(),previous.validUntil(),List.of(previous.supportingEvidence().getFirst(),ref));
            assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(changed,fixture.archive()));
        }
    }
    @Test void originalLocatorDigestAndClosedFieldContractRemainStrict(){
        var fixture=fixture(false,false);fixture.archive().values.put(fixture.proofRef(),new RawJson(new byte[]{'{','}'}));
        assertThrows(IllegalArgumentException.class,()->RootGuardEvidence.frameBasis(fixture.guard(),fixture.archive()));
        var second=fixture(false,false);var raw=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(second.archive().loadMaterial(second.proofRef()).bytes());
        raw.put("before_driver_alias",true);var invalid=new RawJson(StrictJson.canonical(raw));
        assertThrows(IllegalArgumentException.class,()->RootDerivedChildEvidence.decode(invalid));
    }
}


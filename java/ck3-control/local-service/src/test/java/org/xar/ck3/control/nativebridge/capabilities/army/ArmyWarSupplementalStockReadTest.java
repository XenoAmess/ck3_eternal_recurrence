package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReadCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.army.H2743StockPredicateAdmission;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootH2743StockPredicateAdmission;
import org.xar.ck3.control.service.root.StockConsumerOriginalInputs;

/** Actual original source verifier/software seal -> original full transport response -> real held
 * file DATA verifier -> shared stock normalizer/family/two original guard slots/public serde.
 * Injected Work and packet ports are software DATA only. They are not Root's private source issuer,
 * a physical DriverFrameEvidenceLoader, current Game, Native custody or an executable permit. */
final class ArmyWarSupplementalStockReadTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T12:00:00Z");
    private static final ExactRef JAVA=new ExactRef("software-stock-source-definition",1,"a".repeat(64));
    private static final RootH2743StockPredicateAdmission.Limits LIMITS=new RootH2743StockPredicateAdmission.Limits(128,8388608,1048576,8388608);
    private record Inputs(StockConsumerOriginalInputs.Vector original,H2743StockPredicateAdmission.VerifiedData data,Selection selected){ }
    private Inputs inputs(String name)throws Exception{
        var original=StockConsumerOriginalInputs.capture(temporary.resolve(name));
        var data=RootH2743StockPredicateAdmission.verifyDataOnly(original.input(),LIMITS);
        assertEquals(object(original.expectedSource()),object(data.sourceReceipt()));
        var selected=ArmyWarSupplementalReadTest.selected(object(original.before()),new OperationKey(object(original.nativeResult()).path("step").textValue()));
        return new Inputs(original,data,selected);
    }
    private static DefenderStock normalize(Inputs inputs,RawJson raw,RawJson after){return ArmyWarSupplementalStockCodec.normalize(inputs.selected(),raw,inputs.original().before(),after,inputs.data());}

    @Test void originalCompleteTransportAndVerifiedSourceReachTheSoleFormatterAndSerde()throws Exception{
        Inputs i=inputs("full-original");var actual=normalize(i,i.original().nativeResult(),i.original().after());
        assertEquals(object(i.original().expectedResult()),object(actual.normalizedResult()));assertEquals(BigInteger.valueOf(9),actual.actualMailboxSequence());
        assertEquals(i.original().nativeResult(),actual.nativeResult());
        var copied=H2743StockPredicateAdmission.decodeData(H2743StockPredicateAdmission.encodeData(i.data()));
        assertEquals(object(actual.normalizedResult()),object(ArmyWarSupplementalStockCodec.normalize(i.selected(),i.original().nativeResult(),i.original().before(),i.original().after(),copied).normalizedResult()));
        RawJson wire=ArmyWarSupplementalReadCodec.fullDriverResult(actual);ObjectNode output=object(wire);
        assertEquals("4",output.path("queried_revision").textValue());assertEquals("3",output.path("queried_native_revision").textValue());assertEquals("1",output.path("queried_connection_generation").textValue());
        assertEquals("native-29829-2bc2d599f7f9",output.path("queried_episode_run_id").textValue());
        JsonNode body=output.get("defender_de_jure_exit_terms_v1"),proof=body.get("h2743_stock_predicate_evidence_v1");
        assertEquals(17,proof.size());assertEquals("3",proof.path("native_revision").textValue());assertEquals("8",proof.path("pump_epoch").textValue());assertEquals("9",proof.path("mailbox_sequence").textValue());
        assertTrue(proof.path("application_main_thread_id").isIntegralNumber());assertEquals(77,proof.path("application_main_thread_id").intValue());
        assertTrue(body.path("truce_inputs_v1").path("short").path("value").booleanValue());assertFalse(body.path("truce_inputs_v1").path("long").path("value").booleanValue());
        assertFalse(body.path("material_complete").booleanValue());assertTrue(body.path("directed_truce").isNull());assertTrue(body.path("recommended_outcome").isNull());assertTrue(body.path("action_literal").isNull());
        assertFalse(output.has("public_wire_schema"));assertFalse(output.has("integer_paths"));assertFalse(output.has("stockEnabled"));
        assertEquals(wire,json(DriverJson.toNode(DriverJson.object(wire.bytes(),MAX_BYTES))));
        ObjectNode wide=object(i.original().nativeResult());var wideProof=(ObjectNode)wide.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1");
        wideProof.put("pump_epoch",StrictJson.UINT64_MAX).put("mailbox_sequence",StrictJson.UINT64_MAX).put("application_main_thread_id",new BigInteger("4294967295"));
        ObjectNode wideWire=object(ArmyWarSupplementalReadCodec.fullDriverResult(normalize(i,json(wide),i.original().after())));
        assertEquals(StrictJson.UINT64_MAX.toString(),wideWire.path("defender_de_jure_exit_terms_v1").path("h2743_stock_predicate_evidence_v1").path("mailbox_sequence").textValue());
        assertTrue(wideWire.path("defender_de_jure_exit_terms_v1").path("h2743_stock_predicate_evidence_v1").path("application_main_thread_id").isIntegralNumber());
    }

    @Test void exactSeventeenFieldEvidenceAndPredicateTypesRejectMissingNullBoolAndFloat()throws Exception{
        Inputs i=inputs("malformed");ObjectNode raw=object(i.original().nativeResult()),body=(ObjectNode)raw.get("defender_de_jure_exit_terms_v1"),evidence=(ObjectNode)body.get("h2743_stock_predicate_evidence_v1");
        var names=new ArrayList<String>();evidence.fieldNames().forEachRemaining(names::add);
        for(String field:names){ObjectNode bad=raw.deepCopy();((ObjectNode)bad.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1")).remove(field);assertThrows(RuntimeException.class,()->normalize(i,json(bad),i.original().after()),field);}
        for(String field:List.of("native_revision","date_raw","actor_character_id","war_id","attacker_character_id","defender_character_id","application_main_thread_id","pump_epoch","mailbox_sequence","executor_invocations")){
            for(JsonNode wrong:List.of(StrictJson.object().put("x",true).get("x"),StrictJson.object().put("x",1.0).get("x"),StrictJson.object().putNull("x").get("x"))){
                ObjectNode bad=raw.deepCopy();((ObjectNode)bad.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1")).set(field,wrong);assertThrows(RuntimeException.class,()->normalize(i,json(bad),i.original().after()),field);
            }
        }
        for(String field:List.of("paused","map_ready","same_frame_stable","stock_double_sample_stable","stock_parties_bound","material_complete")){
            ObjectNode bad=raw.deepCopy();((ObjectNode)bad.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1")).put(field,1);assertThrows(RuntimeException.class,()->normalize(i,json(bad),i.original().after()),field);
        }
        for(String field:List.of("short","long","border_raid_pair")){
            ObjectNode bad=raw.deepCopy();((ObjectNode)bad.path("defender_de_jure_exit_terms_v1").path("truce_inputs_v1").get(field)).put("status","unavailable").putNull("value").put("unavailable_reason","stock_condition_reader_unavailable");
            assertThrows(RuntimeException.class,()->normalize(i,json(bad),i.original().after()));
        }
        ObjectNode extra=raw.deepCopy();((ObjectNode)extra.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1")).put("eighteenth_field",1);assertThrows(RuntimeException.class,()->normalize(i,json(extra),i.original().after()));
        for(String field:List.of("paused","map_ready","same_frame_stable","stock_double_sample_stable","stock_parties_bound","material_complete")){
            ObjectNode bad=raw.deepCopy();((ObjectNode)bad.path("defender_de_jure_exit_terms_v1").get("h2743_stock_predicate_evidence_v1")).put(field,field.equals("material_complete"));assertThrows(RuntimeException.class,()->normalize(i,json(bad),i.original().after()),field);
        }
    }

    @Test void originalFixedFrameDuplicateNumericTargetAndSourceProfileCannotBeLaundered()throws Exception{
        Inputs i=inputs("scope-errors");
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","connection_generation")){
            ObjectNode after=object(i.original().after());
            switch(field){case "snapshot_id","episode_run_id"->after.put(field,"foreign");case "connection_generation"->((ObjectNode)after.get("diagnostics")).put(field,2);default->after.put(field,999);}
            assertThrows(RuntimeException.class,()->normalize(i,i.original().nativeResult(),json(after)),field);
        }
        ObjectNode duplicated=object(i.original().after());ObjectNode floatTarget=((ObjectNode)duplicated.path("active_wars").get(0)).deepCopy().put("war_id",16777231.0);((com.fasterxml.jackson.databind.node.ArrayNode)duplicated.get("active_wars")).add(floatTarget);
        assertThrows(RuntimeException.class,()->normalize(i,i.original().nativeResult(),json(duplicated)),"original matching treats equal float as a duplicate then rejects");
        ObjectNode missingStorage=object(i.original().nativeResult());((ObjectNode)missingStorage.get("defender_de_jure_exit_terms_v1")).remove("border_raid_storage_candidate_v1");assertThrows(RuntimeException.class,()->normalize(i,json(missingStorage),i.original().after()));
        var historical=new H2743StockPredicateAdmission.VerifiedData(H2743StockPredicateAdmission.Profile.HISTORICAL_BASELINE,i.data().sourceReceipt(),i.data().completeFiles());
        assertThrows(RuntimeException.class,()->ArmyWarSupplementalStockCodec.normalize(i.selected(),i.original().nativeResult(),i.original().before(),i.original().after(),historical));
        assertThrows(RuntimeException.class,()->ArmyWarSupplementalReadCodec.normalizeBaseline(i.selected(),i.original().nativeResult(),i.original().before(),i.original().after()),"stock wire never enters the historical unadmitted path");
    }

    @Test void actualFamilyCallsLiveWorkOnceAndArchiveReplayNeverReopensLivePermission()throws Exception{
        Inputs i=inputs("family");DataArchive archive=new DataArchive();Complete before=frame(i.selected(),object(i.original().before()),archive,"before",AT),after=frame(i.selected(),object(i.original().after()),archive,"after",AT.plusSeconds(1));
        var old=i.selected().original();var o=old.observations();var selected=new Selection(new PlanningRequest(old.before(),old.source(),old.sessionId(),old.deadline(),new PlanningObservation(before.semantic(),o.history(),o.actionSteps(),o.bridgeCapabilities(),o.battleSpeedReadiness(),o.actionFacts(),o.campaignGoal(),o.crossRunPlan(),o.initialLifestyleFocusRequired())),i.selected().operation());
        Map<NativeEffectEvidence.FrameBasis,Complete> stored=Map.of(NativeEffectEvidence.basis(before),before,NativeEffectEvidence.basis(after),after);
        var modes=new ArrayList<DecodeMode>();var liveCalls=new AtomicInteger();var archiveCalls=new AtomicInteger();
        // A spy for callback selection only. It does not recreate the private mailbox reducer.
        StockAdmissionPort softwareOnly=(s,r,b,a,mode,work)->{assertEquals(before,b);assertEquals(after,a);modes.add(mode);var value=work.normalize(i.data());if(mode==DecodeMode.LIVE)liveCalls.incrementAndGet();else archiveCalls.incrementAndGet();return value;};
        PlanningReadPort never=new PlanningReadPort(){public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("DATA test cannot query Native");}};
        NativeEffectEvidence.FrameLoader loader=(basis,same)->{assertSame(archive,same);same.loadFullMaterial(basis.driverFacts());same.loadNativeFrame(basis.nativeFrame());return java.util.Objects.requireNonNull(stored.get(basis));};
        var facts=new StockSources(JAVA,file(i.original().input().pairPath()),file(i.original().input().pinsPath()),i.original().input().nativeSourceCheckout());
        var sources=new Sources(JAVA,JAVA,JAVA,JAVA,Optional.of(facts));
        var reads=new ArmyWarSupplementalReads(sources,never,()->archive,loader,(s,r)->assertEquals(selected,s),softwareOnly);
        var catalog=new RootReadContractCatalog(List.of(),reads.families());var issued=reads.issue(catalog,selected);
        var first=new PlanningReadGuard(guard(before,selected.operation(),archive,"before"),true,true,true,"b".repeat(64));var second=new PlanningReadGuard(guard(after,selected.operation(),archive,"after"),true,true,true,"b".repeat(64));
        ObjectNode top=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id","stock-software-original").put("ok",true);top.set("result",object(i.original().nativeResult()));RawJson full=json(top);
        var ack=new NativeActionPort.AckReceived("stock-software-original",true,Optional.of(i.original().nativeResult()),full,full.bytes());
        var receipt=new PlanningReadReceipt(issued.request(),issued.contract().contractId(),ack.requestId(),first,second,ack);
        var live=assertInstanceOf(DefenderStock.class,issued.contract().decode(receipt));assertEquals(object(i.original().expectedResult()),object(live.normalizedResult()));assertEquals(BigInteger.valueOf(9),live.actualMailboxSequence());
        ExactRef ref=archive.preserveRead(receipt);assertEquals(live,reads.replayArchived(catalog,selected,ref,archive));assertEquals(live,reads.replayArchived(catalog,selected,ref,archive));assertEquals(1,liveCalls.get());assertEquals(2,archiveCalls.get());
        assertEquals(List.of(DecodeMode.LIVE,DecodeMode.ARCHIVED,DecodeMode.ARCHIVED),modes);
        var noAdmission=new ArmyWarSupplementalReads(sources,never,()->archive,loader,(s,r)->{ });var noCatalog=new RootReadContractCatalog(List.of(),noAdmission.families());assertThrows(RuntimeException.class,()->noAdmission.replay(noCatalog,selected,receipt));
        var otherFacts=new StockSources(JAVA,new ExactRef(facts.pair().path(),facts.pair().bytes(),"f".repeat(64)),facts.pins(),facts.nativeSourceCheckout());
        var changed=new ArmyWarSupplementalReads(new Sources(JAVA,JAVA,JAVA,JAVA,Optional.of(otherFacts)),never,()->archive,loader,(s,r)->{ },softwareOnly);var changedCatalog=new RootReadContractCatalog(List.of(),changed.families());
        assertNotEquals(issued.contract().contractId(),changed.issue(changedCatalog,selected).contract().contractId());assertThrows(RuntimeException.class,()->changed.replayArchived(changedCatalog,selected,ref,archive));
        var moved=new StockSources(JAVA,facts.pair(),facts.pins(),facts.nativeSourceCheckout().resolveSibling("other-checkout"));
        var movedReads=new ArmyWarSupplementalReads(new Sources(JAVA,JAVA,JAVA,JAVA,Optional.of(moved)),never,()->archive,loader,(s,r)->{ },softwareOnly);var movedCatalog=new RootReadContractCatalog(List.of(),movedReads.families());var movedIssued=movedReads.issue(movedCatalog,selected);
        assertNotEquals(issued.contract().contractId(),movedIssued.contract().contractId());
        var relabelledData=new PlanningReadReceipt(movedIssued.request(),movedIssued.contract().contractId(),receipt.requestId(),first,second,ack);
        assertThrows(RuntimeException.class,()->movedIssued.contract().replay(relabelledData),"DATA relabelling cannot replace original source checkout");
    }
    private static ExactRef file(Path path)throws Exception{byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,DriverJson.sha256(bytes));}
    private static Complete frame(Selection selected,ObjectNode raw,DataArchive archive,String slot,Instant at){
        ExactRef nativeFrame=archive.material("native-"+slot),driver=archive.material("driver-"+slot);ObjectNode semantic=raw.deepCopy();semantic.set("java_driver_facts_evidence",driver.toJson());
        return new Complete(selected.original().before(),selected.original().source(),selected.original().sessionId(),BigInteger.ONE,DriverJson.object(json(semantic).bytes(),MAX_BYTES),nativeFrame,at,"c".repeat(64));
    }
    private static GuardEvidence guard(Complete frame,OperationKey step,DataArchive archive,String slot){
        var semantic=new SemanticEvidence(frame.identity(),archive.preserveMaterial(RawJson.fullMaterial(DriverJson.encode(frame.semantic()))),frame.originalEvidence(),archive.material("stamp-"+slot),archive.material("full-driver-"+slot),frame.observedAt());
        var originals=new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,archive.material("hello-"+slot),archive.material("heartbeat-"+slot),archive.material("qualification-"+slot),archive.material("capabilities-"+slot));
        ObjectNode row=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",frame.identity().machineId()).put("sequence",3).put("window_id",1).put("status","running").put("start_date_raw",100).put("target_days",1).put("target_date_raw",124).put("last_settled_cycles",0).put("last_settled_date_raw",100);
        var head=new WriterContracts.Head(ContinuityState.fromJson(row,frame.identity().machineId()),List.of(),List.of(),List.of(),false);
        ExactRef basis=RootGuardEvidence.preservePhysicalRead(originals,step,"stock-software-original-data",archive,head);
        return new GuardEvidence(frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration(),step,frame.originalEvidence(),originals.hello(),"stock-software-original-data",frame.observedAt(),AT.plusSeconds(60),List.of(basis));
    }
    private static final class DataArchive implements ActionPorts.OutcomeArchive{
        final Map<ExactRef,byte[]> materials=new HashMap<>();final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        ExactRef material(String role){return preserveMaterial(json(StrictJson.object().put("software_role",role)));}
        public ExactRef preserveMaterial(RawJson raw){var ref=new ExactRef("software-stock-data/"+materials.size(),raw.bytes().length,ActionCodec.sha256(raw.bytes()));materials.put(ref,raw.bytes());return ref;}
        public RawJson loadMaterial(ExactRef ref){return new RawJson(java.util.Objects.requireNonNull(materials.get(ref)));}public RawJson loadFullMaterial(ExactRef ref){return RawJson.fullMaterial(java.util.Objects.requireNonNull(materials.get(ref)));}
        public ExactRef materialReferenceOf(RawJson value){return materials.entrySet().stream().filter(e->java.util.Arrays.equals(e.getValue(),value.bytes())).map(Map.Entry::getKey).findFirst().orElseThrow();}public byte[] loadNativeFrame(ExactRef ref){return java.util.Objects.requireNonNull(materials.get(ref)).clone();}
        public ExactRef preserveRead(PlanningReadReceipt value){preserve(value.original());ExactRef ref=material("read-"+reads.size());reads.put(ref,value);return ref;}public PlanningReadReceipt loadRead(ExactRef ref){return java.util.Objects.requireNonNull(reads.get(ref));}public ExactRef readReferenceOf(PlanningReadReceipt value){return reads.entrySet().stream().filter(e->e.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        public ExactRef preserve(NativeActionPort.DispatchOutcome value){ExactRef ref=material("outcome-"+outcomes.size());outcomes.put(ref,value);return ref;}public NativeActionPort.DispatchOutcome load(ExactRef ref){return java.util.Objects.requireNonNull(outcomes.get(ref));}public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return outcomes.entrySet().stream().filter(e->e.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow();}
        private UnsupportedOperationException unavailable(){return new UnsupportedOperationException("DATA fixture has no Root/writer/native authority");}
        public ExactRef preserveRequest(NativeRequest value){throw unavailable();}public NativeRequest loadRequest(ExactRef value){throw unavailable();}public ExactRef requestReferenceOf(NativeRequest value){throw unavailable();}public ExactRef preserveRecord(ActionRecord value){throw unavailable();}public ActionRecord loadRecord(ExactRef value){throw unavailable();}public ExactRef recordReferenceOf(ActionRecord value){throw unavailable();}public ExactRef preserveReceipt(ActionReceipt value){throw unavailable();}public ActionReceipt loadReceipt(ExactRef value){throw unavailable();}public ExactRef receiptReferenceOf(ActionReceipt value){throw unavailable();}public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unavailable();}
    }
}

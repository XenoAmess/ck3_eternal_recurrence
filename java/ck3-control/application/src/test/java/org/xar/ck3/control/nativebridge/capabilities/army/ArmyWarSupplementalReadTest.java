package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyWarSupplementalReads.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Original Python whole results -> sole Java normalizers/family -> explicit public wire.
 * APP never imports the NT parser. Actual NativeWire packet-verifier and Root guard replay integration
 * are required by the NPI owner; these synthetic originals cannot supply Game/Root permission. */
final class ArmyWarSupplementalReadTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T10:30:00Z"),DEADLINE=AT.plusSeconds(60);
    private static final ExactRef REF=new ExactRef("software-supplemental-war-source-no-native-qualification",1,"a".repeat(64));
    private static final Sources SOURCES=new Sources(REF,REF,REF,REF);
    private static final PlanningReadPort NO_READ=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("pure decoder must not query Native");}};

    @Test void originalNormalizerAndExactDriverMethodProduceAllTwelveFullResponses()throws Exception{
        ObjectNode corpus=ArmyWarSupplementalOriginalInputs.capture(temporary);assertEquals(12,corpus.path("cases").size());
        for(JsonNode v:corpus.get("cases")){
            ObjectNode row=(ObjectNode)v;var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));
            Observation result=normalized(selected,row);assertEquals(row.get("expected"),node(result.normalizedResult()),row.path("name").textValue());
            RawJson publicResult=ArmyWarSupplementalReadCodec.fullDriverResult(result);assertEquals(publicResult,serde(publicResult));
            var publicNode=node(publicResult);assertTrue(publicNode.path("query_sequence").isTextual());assertFalse(publicNode.has("supplemental_war_wire_encoding"));
            assertEquals(fieldNames((ObjectNode)row.get("expected")),fieldNames(publicNode));
            if(result instanceof LocalSiege){assertFalse(publicNode.has("queried_revision"));assertEquals(8,publicNode.size());}
            else{assertEquals("baseline_only",publicNode.path("status").textValue());assertTrue(publicNode.path("queried_revision").isTextual());assertFalse(publicNode.path("defender_de_jure_exit_terms_v1").path("material_complete").booleanValue());assertTrue(publicNode.path("defender_de_jure_exit_terms_v1").path("action_literal").isNull());}
            assertTrue(node(result.nativeResult()).path("query_sequence").isIntegralNumber(),"public encoding must not rewrite native originals");
        }
    }
    @Test void activeSiegeOptionalAbsentNullZeroAndRepeatedNativeOccurrencesStayDistinct()throws Exception{
        var corpus=ArmyWarSupplementalOriginalInputs.capture(temporary);ObjectNode absent=null,nil=null,zero=null,members=null;
        for(JsonNode row:corpus.get("cases"))switch(row.path("name").textValue()){
            case "software-optional-work-missing"->absent=(ObjectNode)row.get("raw");case "software-optional-work-null"->nil=(ObjectNode)row.get("raw");case "software-optional-work-zero"->zero=(ObjectNode)row.get("raw");case "original-membership-repetitions-zero"->members=(ObjectNode)row.get("raw");default->{}}
        assertNotNull(absent);assertNotNull(nil);assertNotNull(zero);assertNotNull(members);
        LocalSiege a=local(absent),n=local(nil),z=local(zero);String path="eligible_regiment_siege_work";
        assertFalse(node(a.normalizedResult()).path("province_state").path("active_siege").has(path));
        assertTrue(node(n.normalizedResult()).path("province_state").path("active_siege").get(path).isNull());
        assertEquals(BigInteger.ZERO,node(z.normalizedResult()).path("province_state").path("active_siege").path(path).path("raw").bigIntegerValue());
        var occurrences=node(local(members).normalizedResult()).path("province_state").path("active_siege").path("province_unit_occurrences");
        assertEquals(5,occurrences.size());assertEquals(0,occurrences.get(0).path("public_unit_id").intValue());
        assertEquals(occurrences.get(1).get("qualified_regiment_ids"),occurrences.get(3).get("qualified_regiment_ids"));
        assertEquals(occurrences.get(1).get("qualified_regiment_ids").get(0),occurrences.get(1).get("qualified_regiment_ids").get(1));
    }
    @Test void installedLocalFamilyDelegatesActualTypedReceiptAndInjectedPacketVerifierOnce()throws Exception{
        var row=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0);var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));
        var calls=new AtomicInteger();var packets=new AtomicInteger();
        PlanningReadPort port=new PlanningReadPort(){
            @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("same-writer overload required");}
            @Override public <T>PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){
                calls.incrementAndGet();assertEquals(selected.original().before(),request.before());var primitive=contract.prepare(request,"software-query");
                assertEquals(selected.operation().value(),primitive.step());assertEquals(nativeArguments(),primitive.additionalFields());assertTrue(primitive.preparationEvidence().isEmpty());
                var original=receipt(contract,request,(ObjectNode)row.get("raw"));return new PlanningReadResult.Known<>(contract.decode(original),original,REF);
            }};
        var reads=reads(port,(s,r)->{assertEquals(selected,s);assertEquals(s.operation(),r.request().operation());packets.incrementAndGet();});
        var catalog=new RootReadContractCatalog(List.of(),reads.families());var response=reads.collect(null,catalog,selected);
        if(!(response instanceof PlanningReadResult.Known<Observation> actual))throw new AssertionError("actual injected read must retain a typed Known");
        assertEquals(1,calls.get());assertEquals(1,packets.get());assertInstanceOf(LocalSiege.class,actual.value());
        Observation value=actual.value();assertEquals(row.get("expected"),node(value.normalizedResult()));assertEquals(ArmyWarSupplementalReadCodec.fullDriverResult(value),serde(ArmyWarSupplementalReadCodec.fullDriverResult(value)));
        var issued=reads.issue(catalog,selected);assertEquals(value,reads.replay(catalog,selected,receipt(issued.contract(),issued.request(),(ObjectNode)row.get("raw"))));assertEquals(1,calls.get(),"archived DATA replay must never query again");
    }
    @Test void unavailableAndOriginalUnknownReturnOnceWithoutReplacementReadOrInventedResult()throws Exception{
        var row=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0);var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));var sends=new AtomicInteger();
        var originalUnknown=new NativeActionPort.Unknown("software-query","no complete native reply",new byte[]{1},Optional.empty());
        PlanningReadPort port=new PlanningReadPort(){@Override public <T>PlanningReadResult<T> read(ReadContract<T> c,PlanningReadRequest r){throw new AssertionError();}
            @Override public <T>PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ReadContract<T> c,PlanningReadRequest r){sends.incrementAndGet();return new PlanningReadResult.Unavailable<>("actual native capability/read unavailable",Optional.of(originalUnknown));}};
        var reads=reads(port,(s,r)->{throw new AssertionError("UNKNOWN is not a complete packet");});var response=reads.collect(null,new RootReadContractCatalog(List.of(),reads.families()),selected);
        if(!(response instanceof PlanningReadResult.Unavailable<Observation> actual))throw new AssertionError("UNKNOWN cannot become Known");
        assertEquals(originalUnknown,actual.original().orElseThrow());assertEquals(1,sends.get());
    }
    @Test void nativeFrameBoolMissingRangeAndInventedOccupationOrSiegeCannotBecomeNormalized()throws Exception{
        ObjectNode raw=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0).get("raw");
        for(String mutation:List.of("sequence-bool","revision-float","date-bool","missing","extra","province-bool","occupation","siege","status")){
            ObjectNode bad=raw.deepCopy(),state=(ObjectNode)bad.get("province_state");switch(mutation){
                case "sequence-bool"->bad.put("query_sequence",true);case "revision-float"->bad.put("snapshot_revision",4.0);case "date-bool"->bad.put("date_raw",true);case "missing"->bad.remove("province_state");case "extra"->bad.put("queried_revision",7);
                case "province-bool"->state.put("province_id",true);case "occupation"->{state.put("occupation_observable",false).put("is_occupied",true);}case "siege"->{state.put("siege_observable",false);state.putObject("active_siege");}case "status"->bad.put("status","partial");default->throw new AssertionError();}
            assertThrows(RuntimeException.class,()->localWithFrame(bad,4,53219928),mutation);
        }
    }
    @Test void nestedSiegeStrictTypesFractionsPhasesAndEligibilityAreNotInferred()throws Exception{
        var cases=ArmyWarSupplementalOriginalInputs.capture(temporary).get("cases");ObjectNode raw=null;for(JsonNode row:cases)if(row.path("name").textValue().equals("original-membership-repetitions-zero"))raw=(ObjectNode)row.get("raw");assertNotNull(raw);
        for(String mutation:List.of("negative-fixed","fraction","scale-float","phase-bool","enum-range","unobservable-assault","occurrence-order","excluded-consumes","unresolved-consumes")){
            ObjectNode bad=raw.deepCopy(),siege=(ObjectNode)bad.path("province_state").get("active_siege");switch(mutation){
                case "negative-fixed"->((ObjectNode)siege.get("current_work")).put("raw",-1);case "fraction"->((ObjectNode)siege.get("progress_fraction")).put("raw",100001);case "scale-float"->((ObjectNode)siege.get("current_work")).put("scale",100000.0);case "phase-bool"->siege.put("phase_counter",true);case "enum-range"->siege.put("prepared_selected_phase_event_enum",6);case "unobservable-assault"->siege.put("breach_level",1);
                case "occurrence-order"->((ObjectNode)siege.path("province_unit_occurrences").get(0)).put("occurrence_index",1);
                case "excluded-consumes"->((ObjectNode)siege.path("province_unit_occurrences").get(2)).putArray("qualified_regiment_ids").add(1);
                case "unresolved-consumes"->((ObjectNode)siege.path("province_unit_occurrences").get(4)).putArray("qualified_regiment_ids");default->throw new AssertionError();}
            assertThrows(RuntimeException.class,()->local(bad),mutation);
        }
    }
    @Test void originalBaselineAdapterRejectsChangedActualAfterWarConnectionAndMaterialLaundering()throws Exception{
        var rows=ArmyWarSupplementalOriginalInputs.capture(temporary).get("cases");ObjectNode row=null;for(JsonNode r:rows)if(r.path("kind").textValue().equals("baseline")){row=(ObjectNode)r;break;}assertNotNull(row);
        var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));RawJson before=json(row.get("before")),raw=json(row.get("raw"));
        for(String mutation:List.of("war","connection","episode","unpaused")){
            ObjectNode after=((ObjectNode)row.get("after")).deepCopy();switch(mutation){case "war"->((ObjectNode)after.path("active_wars").get(0)).putArray("targeted_title_ids").add(999);case "connection"->((ObjectNode)after.get("diagnostics")).put("connection_generation",2);case "episode"->after.put("episode_run_id","foreign");case "unpaused"->after.put("paused",false);default->throw new AssertionError();}
            assertThrows(RuntimeException.class,()->ArmyWarSupplementalReadCodec.normalizeBaseline(selected,raw,before,json(after)),mutation);
        }
        ObjectNode admitted=((ObjectNode)row.get("raw")).deepCopy();((ObjectNode)admitted.get("defender_de_jure_exit_terms_v1")).putObject("h2743_stock_predicate_evidence_v1");
        assertThrows(RuntimeException.class,()->ArmyWarSupplementalReadCodec.normalizeBaseline(selected,json(admitted),before,before),"admitted stock cannot be laundered as historical baseline");
        ObjectNode invented=((ObjectNode)row.get("raw")).deepCopy();((ObjectNode)invented.get("defender_de_jure_exit_terms_v1")).put("material_complete",true);
        assertThrows(RuntimeException.class,()->ArmyWarSupplementalReadCodec.normalizeBaseline(selected,json(invented),before,before));
    }
    @Test void sourcesAndSemanticDigestBindFiniteFamilyIdentityWithoutArchiveMaterialAlias()throws Exception{
        var row=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0);var snapshot=((ObjectNode)row.get("before")).deepCopy();snapshot.put("unchanged_other_semantic","x".repeat(70_000));
        var selected=selected(snapshot,new OperationKey(row.path("raw").path("step").textValue()));var one=reads(NO_READ,(s,r)->{throw new AssertionError();});var a=one.issue(new RootReadContractCatalog(List.of(),one.families()),selected);
        assertTrue(DriverJson.encode(a.request().arguments()).length<65_536);assertTrue(a.contract().prepare(a.request(),"source-test").preparationEvidence().isEmpty());
        var otherSources=new Sources(REF,REF,new ExactRef("different-current-native-source",1,"b".repeat(64)),REF);var two=new ArmyWarSupplementalReads(otherSources,NO_READ,()->{throw new AssertionError();},(basis,archive)->{throw new AssertionError();},(s,r)->{throw new AssertionError();});
        assertNotEquals(a.contract().contractId(),two.issue(new RootReadContractCatalog(List.of(),two.families()),selected).contract().contractId());
        for(String step:List.of("query-province-local-siege-v1-0","query-province-local-siege-v1-02610","query-province-local-siege-v1-2147483648","query-defender-de-jure-exit-terms-v1-0","query-war-termination-options-1"))assertFalse(supports(new OperationKey(step)));
    }
    @Test void wrongHeldGuardSessionAndNativePacketVerifierFailureCannotBePromotedToKnown()throws Exception{
        var row=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0);var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));var verified=new AtomicInteger();
        var reads=reads(NO_READ,(s,r)->verified.incrementAndGet());var catalog=new RootReadContractCatalog(List.of(),reads.families());var issued=reads.issue(catalog,selected);var original=receipt(issued.contract(),issued.request(),(ObjectNode)row.get("raw"));
        var wrong=new PlanningReadGuard(original.after().binding(),true,false,true,original.after().originalBindingSha256());
        assertThrows(RuntimeException.class,()->issued.contract().replay(new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),wrong,original.original())));assertEquals(0,verified.get());
        var r=original.request();var other=new PlanningReadRequest(r.before(),r.source(),"foreign-session",r.operation(),r.arguments(),r.deadline());
        assertThrows(RuntimeException.class,()->issued.contract().replay(new PlanningReadReceipt(other,original.contractId(),original.requestId(),original.before(),original.after(),original.original())));
        var denied=reads(NO_READ,(s,receipt)->{throw new IllegalArgumentException("actual native packet/chronology rejected");});var deniedCatalog=new RootReadContractCatalog(List.of(),denied.families());var deniedIssue=denied.issue(deniedCatalog,selected);
        assertThrows(IllegalArgumentException.class,()->deniedIssue.contract().replay(receipt(deniedIssue.contract(),deniedIssue.request(),(ObjectNode)row.get("raw"))));
    }
    @Test void liveDecoderRetainsExactNativeTokenBytesInsteadOfReencodingItsValidatedTree()throws Exception{
        var row=(ObjectNode)ArmyWarSupplementalOriginalInputs.capture(temporary).path("cases").get(0);var selected=selected((ObjectNode)row.get("before"),new OperationKey(row.path("raw").path("step").textValue()));
        var reads=reads(NO_READ,(s,r)->{ });var catalog=new RootReadContractCatalog(List.of(),reads.families());var issued=reads.issue(catalog,selected);
        var original=receipt(issued.contract(),issued.request(),(ObjectNode)row.get("raw"));var old=original.original();
        var token=new RawJson(("  "+new String(old.originalResultToken().orElseThrow().bytes(),java.nio.charset.StandardCharsets.UTF_8)+"  ").getBytes(java.nio.charset.StandardCharsets.UTF_8));
        var ack=new NativeActionPort.AckReceived(old.requestId(),old.nativeOk(),Optional.of(token),old.originalFrame(),old.originalPacket());
        var retained=new PlanningReadReceipt(original.request(),original.contractId(),original.requestId(),original.before(),original.after(),ack);
        Observation observed=issued.contract().decode(retained);assertEquals(token,observed.nativeResult());
        assertArrayEquals(token.bytes(),observed.nativeResult().bytes());assertEquals(row.get("expected"),node(observed.normalizedResult()));
        assertEquals(ArmyWarSupplementalReadCodec.fullDriverResult(observed),serde(ArmyWarSupplementalReadCodec.fullDriverResult(observed)));
    }

    public static Selection selected(ObjectNode snapshot,OperationKey operation){
        var identity=new ObservationIdentity("software-supplemental-no-game",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(),snapshot.path("native_revision").bigIntegerValue(),snapshot.path("date_raw").bigIntegerValue()),snapshot.path("snapshot_id").textValue(),snapshot.path("revision").bigIntegerValue(),snapshot.path("episode_run_id").textValue()),1);
        var source=new G2Source(identity.machineId(),AT.toString(),"SOFTWARE-NOT-NATIVE-QUALIFIED",REF);
        return new Selection(new PlanningRequest(identity,source,"software-supplemental-session",DEADLINE,new PlanningObservation(DriverJson.object(json(snapshot).bytes(),DriverJson.MAX_NATIVE_BYTES),List.of(),Set.of(),Set.of(capability(kind(operation))),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false)),operation);
    }
    private static Observation normalized(Selection selected,ObjectNode row){return row.path("kind").textValue().equals("local")?ArmyWarSupplementalReadCodec.normalizeLocalSiege(selected,json(row.get("raw"))):ArmyWarSupplementalReadCodec.normalizeBaseline(selected,json(row.get("raw")),json(row.get("before")),json(row.get("after")));}
    private static LocalSiege local(ObjectNode raw){return localWithFrame(raw,raw.path("snapshot_revision").bigIntegerValue(),raw.path("date_raw").bigIntegerValue());}
    private static LocalSiege localWithFrame(ObjectNode raw,long revision,long date){return localWithFrame(raw,BigInteger.valueOf(revision),BigInteger.valueOf(date));}
    private static LocalSiege localWithFrame(ObjectNode raw,BigInteger revision,BigInteger date){var snapshot=StrictJson.object().put("snapshot_id","software:"+revision).put("revision",7).put("native_revision",revision).put("date_raw",date).put("episode_run_id","software-supplemental").put("paused",true).put("map_ready",true);snapshot.putObject("played_character").put("character_id",29829).put("alive",true);return ArmyWarSupplementalReadCodec.normalizeLocalSiege(selected(snapshot,new OperationKey(raw.path("step").textValue())),json(raw));}
    private static ArmyWarSupplementalReads reads(PlanningReadPort port,OriginalPacketVerifier packets){return new ArmyWarSupplementalReads(SOURCES,port,()->{throw new AssertionError("local query cannot request a fake original frame archive");},(basis,archive)->{throw new AssertionError("local query cannot fabricate defender frames");},packets);}
    static PlanningReadReceipt receipt(ReadContract<?> contract,PlanningReadRequest request,ObjectNode raw){
        String id="software-query";var frame=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);frame.set("result",raw);
        // Synthetic packet bytes are deliberately not presented as a successful real NT parser fixture.
        var ack=new NativeActionPort.AckReceived(id,true,Optional.of(json(raw)),json(frame),json(frame).bytes());
        var guard=new PlanningReadGuard(new GuardEvidence(request.before(),request.source(),request.sessionId(),BigInteger.ONE,request.operation(),REF,REF,"software-supplemental-only",AT,DEADLINE),true,true,true,"c".repeat(64));
        return new PlanningReadReceipt(request,contract.contractId(),id,guard,guard,ack);
    }
    private static java.util.Set<String> fieldNames(ObjectNode node){var names=new java.util.HashSet<String>();node.fieldNames().forEachRemaining(names::add);return Set.copyOf(names);}
    private static ObjectNode node(RawJson raw){return ArmyWarSupplementalReadCodec.object(raw);}
    private static RawJson json(JsonNode node){return ArmyWarSupplementalReadCodec.json(node);}
    private static RawJson serde(RawJson raw){return new RawJson(DriverJson.encode(DriverJson.object(raw.bytes(),ArmyWarSupplementalReadCodec.MAX_BYTES)));}
}

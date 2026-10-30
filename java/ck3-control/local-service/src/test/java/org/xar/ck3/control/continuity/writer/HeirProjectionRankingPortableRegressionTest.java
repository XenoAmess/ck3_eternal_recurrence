package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.wave3.governance.heirranking.HeirCandidateRankingConsumerPort;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyHeirNativeProjection;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageProjectionQueries;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyRootBinding;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Build;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.service.root.RootFamilyCampaignRead;
import org.xar.ck3.control.wave3.governance.heirintake.HeirCandidateIntakeConsumerPort;

/** Relocated worker102 original producer topology; software DATA only, no live admission or qualification. */
final class HeirProjectionRankingPortableRegressionTest {
    @TempDir Path temporary;
    private static final String LEGALITY="c7c50b93ad3089aa31fe5f99382cab6545691c5b4b4a4e5f6209d63164ead320";
    private static final String ROOT="b4cd1df8ce36691aac1fa850d7bc375904d5ca2016a5211acb67ff1b303227a6";

    private Actual actual()throws Exception {
        var retained=PortableHeirRanking102Fixture.materialize(temporary);
        ExactRef legalityRef=retained.legality(),rootRef=retained.root(),projectionRef=retained.projection();
        var codec=new NativeArchiveDataCodec(HeirProjectionRankingPortableRegressionTest::exact);
        PlanningReadReceipt legalityReceipt=codec.decodeRead(legalityRef),rootReceipt=codec.decodeRead(rootRef),projectionReceipt=codec.decodeRead(projectionRef);
        assertEquals(legalityReceipt.request().before(),rootReceipt.request().before());
        assertEquals(legalityReceipt.request().before(),projectionReceipt.request().before());
        var frame=RootGuardEvidence.loadFrame(legalityReceipt.before().binding(),originals(),
                new DriverFrameEvidenceLoader(new DriverObservationAssembler()));
        var context=new RootInteractionContextProjection(Build.CROZIER4).project(frame,legalityReceipt.request().deadline());
        var definitions=new FinanceReadContracts(query->new FinanceReadContracts.Registration(rootRef,
                new FinanceReadContracts.Permission(Optional.empty(),query.operation().value(),
                        org.xar.ck3.control.application.action.ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                        org.xar.ck3.control.application.action.ReadContract.WireProfile.EXECUTE_STEP)));
        var rootPacket=definitions.decodeOriginal(FinanceReadContracts.Query.ROOT,rootReceipt,frame.semantic());
        var rootKnown=new PlanningReadResult.Known<>(RootFamilyCampaignRead.project(rootPacket.result(),rootReceipt),rootReceipt,rootRef);
        FamilyRootBinding.Originals roots=ref->{assertEquals(rootRef,ref);return rootKnown;};
        Obj legality=FamilyHeirNativeProjection.project(legalityReceipt,roots);
        var exclusions=new Arr(List.of());
        var intake=HeirCandidateIntakeConsumerPort.evaluate(OpportunityJson.encode(obj(
                "legal_rows",legality.get("native_legal_candidates"),"rejected_candidate_ids",exclusions)));
        List<BigInteger> ids=intake.nextRichCandidateIds().orElseThrow();
        var history=new FamilyMarriageProjectionQueries.Originals(){
            @Override public PlanningReadReceipt load(ExactRef ref){assertEquals(legalityRef,ref);return legalityReceipt;}
            @Override public ExactRef referenceOf(PlanningReadReceipt actual){assertSame(legalityReceipt,actual);return legalityRef;}
        };
        // Constructor context is archive-only; admission deliberately cannot authorize any request.
        var queries=new FamilyMarriageProjectionQueries(legalityReceipt.request().source().sourceRef(),history,roots,
                request->{throw new AssertionError("archive-only test must never grant Native admission");});
        Obj projection=queries.project(projectionReceipt);
        assertEquals(new Text("available"),projection.get("status"));
        assertEquals(new IntegerValue(BigInteger.valueOf(56)),projection.get("native_revision"));
        assertEquals(new IntegerValue(BigInteger.valueOf(61)),projection.get("queried_revision"));
        List<Value> rows=OpportunityJson.array(projection.get("rows"),"actual rich rows");
        assertEquals(5,rows.size());
        for(int i=0;i<rows.size();i++) {
            Obj row=OpportunityJson.object(rows.get(i),"actual rich candidate");
            assertEquals(new IntegerValue(ids.get(i)),row.get("candidate_character_id"));
            assertEquals(new IntegerValue(BigInteger.valueOf(31254)),row.get("actor_character_id"));
            assertEquals(new IntegerValue(BigInteger.valueOf(40526)),row.get("heir_character_id"));
            assertInstanceOf(IntegerValue.class,row.get("recipient_character_id"));
            assertInstanceOf(Bool.class,row.get("complete_can_send"));
        }
        Obj ranking=obj("legality",legality,"projection",projection,"rejected_candidate_ids",exclusions);
        byte[] raw=OpportunityJson.encode(ranking);
        assertTrue(raw.length>65536);
        String trace=System.getProperty("xar.heir102.trace");
        if(trace!=null) {
            Path directory=Path.of(trace);Files.createDirectories(directory);
            var document=StrictJson.object();var inputs=document.putArray("inputs");long count=0;
            for(var original:LOADED.entrySet()) {inputs.addObject().set("ref",original.getKey().toJson());count+=original.getValue().length;}
            document.put("bytes",count);Files.write(directory.resolve("TRACE.json"),FullJsonTree.encode(document,FullJsonTree.MAXIMUM_BYTES));
        }
        return new Actual(raw,projectionReceipt,queries,ids);
    }
    private record Actual(byte[] ranking,PlanningReadReceipt projection,FamilyMarriageProjectionQueries queries,List<BigInteger> ids) { }
    private static final java.util.Map<ExactRef,byte[]> LOADED=new LinkedHashMap<>();

    @Test void actualNativeReadAndProjectionReachTheRealLargeRankingConsumer()throws Exception {
        var original=actual();byte[] before=original.ranking().clone();
        var decoded=HeirCandidateRankingConsumerPort.decode(original.ranking());
        assertTrue(decoded.available());assertEquals(833,decoded.legalRows().size());assertEquals(5,decoded.rows().size());
        assertArrayEquals(original.ranking(),decoded.sourceJson());
        var evaluated=HeirCandidateRankingConsumerPort.evaluate(decoded);
        var reasons=StrictJson.parse(evaluated.rejectionReasons());assertEquals(5,reasons.size());
        for(int index=0;index<5;index++)assertEquals(original.ids().get(index),reasons.get(index).get("candidate_character_id").bigIntegerValue());
        var choices=StrictJson.parse(evaluated.choices());
        for(var choice:choices)assertTrue(original.ids().contains(choice.get("candidate_character_id").bigIntegerValue()));
        assertArrayEquals(evaluated.choices(),HeirCandidateRankingConsumerPort.rank(original.ranking()));
        assertArrayEquals(evaluated.rejectionReasons(),HeirCandidateRankingConsumerPort.diagnose(original.ranking()));
        assertArrayEquals(before,original.ranking());
        System.out.println("PASS actual102 full original ACK/ROOT/legality/projection -> Ranking bytes="+original.ranking().length+" legal833/rich5 reasons5 choices="+choices.size());
    }

    @Test void largeRankingStillRejectsTypedFieldsAndExplainsChangedOwner()throws Exception {
        var original=actual();
        var input=ObjectNode.class.cast(FullJsonTree.parse(original.ranking(),FullJsonTree.MAXIMUM_BYTES));
        for(var wrong:List.of(StrictJson.object().put("value",true).get("value"),StrictJson.object().put("value","40408").get("value"),StrictJson.object().put("value",40408.0).get("value"))) {
            var changed=input.deepCopy();ObjectNode.class.cast(changed.get("projection").get("rows").get(0)).set("candidate_character_id",wrong);
            assertThrows(IllegalArgumentException.class,()->HeirCandidateRankingConsumerPort.evaluate(FullJsonTree.encode(changed,FullJsonTree.MAXIMUM_BYTES)));
        }
        var extra=input.deepCopy();extra.put("qualified",true);
        assertThrows(IllegalArgumentException.class,()->HeirCandidateRankingConsumerPort.evaluate(FullJsonTree.encode(extra,FullJsonTree.MAXIMUM_BYTES)));
        var owner=input.deepCopy();ObjectNode.class.cast(owner.get("projection").get("rows").get(0)).put("actor_character_id",31255);
        var changedOwner=HeirCandidateRankingConsumerPort.evaluate(FullJsonTree.encode(owner,FullJsonTree.MAXIMUM_BYTES));
        var reasons=StrictJson.parse(changedOwner.rejectionReasons()).get(0).get("rejection_reasons");
        assertTrue(java.util.stream.StreamSupport.stream(reasons.spliterator(),false).anyMatch(value->"actor_identity_mismatch".equals(value.textValue())));
        assertTrue(java.util.stream.StreamSupport.stream(StrictJson.parse(changedOwner.choices()).spliterator(),false).noneMatch(value->original.ids().getFirst().equals(value.get("candidate_character_id").bigIntegerValue())));
        var nativeResult=ObjectNode.class.cast(FullJsonTree.parse(original.projection().original().originalResultToken().orElseThrow().bytes(),FullJsonTree.MAXIMUM_BYTES));
        ObjectNode.class.cast(nativeResult.get("rows").get(0)).put("actor_character_id",31255);
        var binding=original.queries().decode(original.projection()).binding();
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageValue.decode(new RawJson(FullJsonTree.encode(nativeResult,FullJsonTree.MAXIMUM_BYTES)),binding));
    }

    private static Obj obj(Object...pairs){var m=new LinkedHashMap<String,Value>();for(int i=0;i<pairs.length;i+=2)m.put((String)pairs[i],(Value)pairs[i+1]);return new Obj(m);}
    private static Obj ref(ExactRef ref){return obj("path",new Text(ref.path()),"bytes",new IntegerValue(BigInteger.valueOf(ref.bytes())),"sha256",new Text(ref.sha256()));}
    private static byte[] exact(ExactRef ref,int maximum)throws IOException {
        byte[] raw=Files.readAllBytes(Path.of(ref.path()));
        StrictJson.require(raw.length==ref.bytes()&&raw.length<=maximum&&DriverJson.sha256(raw).equals(ref.sha256()),"actual102 original bytes/SHA differs");
        LOADED.put(ref,raw);
        String trace=System.getProperty("xar.heir102.trace");
        if(trace!=null) {Path directory=Path.of(trace).resolve("raw");Files.createDirectories(directory);Files.write(directory.resolve(ref.sha256()+".bin"),raw);}
        return raw;
    }
    private static ActionPorts.OutcomeArchive originals(){
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(HeirProjectionRankingPortableRegressionTest.class.getClassLoader(),new Class<?>[]{ActionPorts.OutcomeArchive.class},
                (proxy,method,args)->switch(method.getName()){
                    case "loadNativeFrame","readOriginalPacket"->exact((ExactRef)args[0],WriterContracts.MAX_PIN_BYTES);
                    case "loadMaterial"->new RawJson(exact((ExactRef)args[0],RawJson.MAXIMUM_BYTES));
                    case "loadFullMaterial"->RawJson.fullMaterial(exact((ExactRef)args[0],WriterContracts.MAX_PIN_BYTES));
                    default->throw new AssertionError("archive-only test refuses "+method.getName());
                });
    }
}

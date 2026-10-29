package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.lossallocation.ObservedLossRequests;
import org.xar.ck3.control.wave2.military.monthlycaller.ArmyMonthlyCaller;

final class LossAllocationProductionTest {
    @Test void completeStageMatchesEveryOriginalProducerAndPreservesNormalizedInput()throws Exception{
        JsonNode golden=golden();assertTrue(golden.get("cases").size()>=15);
        for(JsonNode sample:golden.get("cases")){
            JsonNode input=sample.get("input");byte[] before=StrictJson.canonical(input,StrictJson.EXPLICIT_MAX_BYTES);
            var actual=ArmyStrengthsLossAllocation.projectRow(input);
            assertArrayEquals(StrictJson.canonical(sample.get("expected"),StrictJson.EXPLICIT_MAX_BYTES),
                StrictJson.canonical(ArmyStrengthsLossAllocation.encodeArmy(actual),StrictJson.EXPLICIT_MAX_BYTES),sample.get("id").textValue());
            assertArrayEquals(before,StrictJson.canonical(input,StrictJson.EXPLICIT_MAX_BYTES),"same query inputs remain unchanged");
            assertFalse(ArmyStrengthsLossAllocation.encodeArmy(actual).get("applied_loss_ready").booleanValue());
        }
    }
    @Test void actualReadonlyStagesDoNotBorrowDerivedPhysicalWrites()throws Exception{
        var missing=ArmyStrengthsLossAllocation.projectRow(sample("missing_real_post_supply_stage").get("input"));
        assertFalse(missing.observed().ready());assertTrue(missing.observed().missing().contains("post_supply_current_soldiers"));
        var overflow=ArmyStrengthsLossAllocation.projectRow(sample("missing_real_post_preferred_stage").get("input"));
        assertEquals(3,overflow.observed().passes().size());assertEquals(List.of("siege_raid_residual_stage_inputs"),overflow.observed().missing());
        var zero=ArmyStrengthsLossAllocation.projectRow(sample("observed_zero_quantity_order").get("input"));
        assertEquals(List.of(0,1,1),zero.observed().passes().get(2).requests().stream().map(ObservedLossRequests.Request::requestedSoldiers).toList());
    }
    @Test void low32MultiplyAndSignedDivisionKeepNativeTruncation(){
        var pass=ObservedLossRequests.requests(50000,new ObservedLossRequests.StageInputs(100000,List.of(new ObservedLossRequests.Eligible(9,50000),new ObservedLossRequests.Eligible(3,50000))),ObservedLossRequests.Phase.SIEGE_RAID_PREFERRED);
        assertEquals(List.of(-1794967296,-897517296),pass.requests().stream().map(ObservedLossRequests.Request::multiplySigned32).toList());
        assertEquals(List.of(-17949,-17950),pass.requests().stream().map(ObservedLossRequests.Request::requestedSoldiers).toList());
        assertEquals(85899,pass.remainingBudget());assertEquals(0,pass.overflow());
    }
    @Test void publicWideSchemaEncodingPreservesNativeNumbersAndZeroIdentity()throws Exception{
        var value=ArmyStrengthsLossAllocation.projectRow(sample("domain_signed64_wrap_clamp").get("input"));
        var collection=new ArmyStrengthsLossAllocation.Allocation(List.of(value));
        JsonNode nativeJson=ArmyStrengthsCodec.parseValue(ArmyStrengthsLossAllocation.encode(collection));
        JsonNode publicJson=ArmyStrengthsCodec.parseValue(ArmyStrengthsLossAllocation.encodePublicV2(collection));
        assertEquals(0,publicJson.get(0).get("army_id").intValue());
        String field="same_input_conditional_current_helper_domain_updates_v1";
        assertTrue(nativeJson.get(0).get(field).get("record_projections").get(0).get("conditional_domain_value_48_before_raw64").isIntegralNumber());
        assertEquals(Long.toString(Long.MAX_VALUE-1),publicJson.get(0).get(field).get("record_projections").get(0).get("conditional_domain_value_48_before_raw64").textValue());
        assertEquals(0,nativeJson.get(0).get(field).get("record_projections").get(0).get("conditional_domain_value_48_after_raw64").longValue());
        assertEquals("0",publicJson.get(0).get(field).get("record_projections").get(0).get("conditional_domain_value_48_after_raw64").textValue());
        assertArrayEquals(ArmyStrengthsLossAllocation.encode(collection).bytes(),ArmyStrengthsLossAllocation.encode(collection).bytes());
    }
    @Test void sharedCallerParserRejectsWrongTypeMissingAndExtraAndRoundtrips()throws Exception{
        JsonNode raw=sample("ordered_counter_aliases").get("input").get("monthly_caller_effect_inputs_v1");
        var value=ArmyMonthlyCaller.decodeInputs(raw);assertEquals(value,ArmyMonthlyCaller.decodeInputs(StrictJson.parse(StrictJson.canonical(ArmyMonthlyCaller.encodeInputs(value)))));
        ObjectNode wrong=raw.deepCopy();wrong.put("current_date_storage_raw64",true);assertThrows(IllegalArgumentException.class,()->ArmyMonthlyCaller.decodeInputs(wrong));
        ObjectNode missing=raw.deepCopy();missing.remove("army_byte_22_raw");assertThrows(IllegalArgumentException.class,()->ArmyMonthlyCaller.decodeInputs(missing));
        ObjectNode extra=raw.deepCopy();extra.put("unexpected",0);assertThrows(IllegalArgumentException.class,()->ArmyMonthlyCaller.decodeInputs(extra));
        assertNull(ArmyMonthlyCaller.decodeInputs(StrictJson.parse("null".getBytes(StandardCharsets.UTF_8))));
    }
    @Test void internalFullDataRefreshNodeDoesNotUseTheSmallerExternalSelectorEnvelope(){
        var contributions=new java.util.ArrayList<org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.Contribution>();
        for(int i=0;i<4096;i++)contributions.add(new org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.Contribution(i,110,i%7,1,1,1));
        var refresh=new org.xar.ck3.control.wave2.military.armyselector.RaisedRegimentRefresh.Result(10,true,4096,4096,false,true,List.of(),contributions);
        assertThrows(IllegalArgumentException.class,()->org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec.encodeRefresh(refresh));
        assertEquals(4096,org.xar.ck3.control.wave2.military.armyselector.ArmySelectorCodec.refreshNode(refresh).get("record_contributions").size());
        var writer=new org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.WriterResult(org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.WriterStatus.AVAILABLE,10,false,refresh,List.of(),List.of(),List.of(),0L,0L,null);
        assertEquals(4096,org.xar.ck3.control.wave2.military.losssequence.LossSequenceCodec.writerNode(writer).get("conditional_raised_regiment_refresh").get("record_contributions").size());
        var associated=new org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection.Result(org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection.Status.AVAILABLE,true,true,false,List.of(),List.of(refresh),List.of(new org.xar.ck3.control.wave2.military.losssequence.LossSequenceModel.FinalRegiment(10,4096,4096)),List.of(),List.of());
        assertEquals(4096,org.xar.ck3.control.wave3.military.landcontext.AssociatedRefillProjection.encode(associated).get("regiment_refreshes").get(0).get("record_contributions").size());
    }
    @Test void installerHasOneTypedStageAndPartialPipelineCannotBecomeProduction(@TempDir Path temporary)throws Exception{
        Path source=temporary.resolve("actual-source.java");byte[] bytes="source-bound-test".getBytes(StandardCharsets.UTF_8);Files.write(source,bytes);
        var ref=new ExactRef(source.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        var pipeline=new ArmyStrengthsPipeline();var families=new ArmyStrengthsFamilies.Registry();
        ArmyStrengthsLossAllocation.install(families,pipeline,ref);
        assertEquals(List.of(ArmyStrengthsPipeline.Stage.LOSS_ALLOCATION_REQUESTS_V1),pipeline.coverage().installed());
        assertThrows(IllegalArgumentException.class,()->ArmyStrengthsLossAllocation.install(families,pipeline,ref));
        pipeline.freeze();assertThrows(IllegalArgumentException.class,pipeline::requireComplete);
    }
    private static JsonNode sample(String id)throws Exception{for(JsonNode value:golden().get("cases"))if(id.equals(value.get("id").textValue()))return value;throw new AssertionError("missing original case "+id);}
    private static JsonNode golden()throws Exception{
        String configured=System.getProperty("xar.lossallocation.golden");if(configured==null||configured.isBlank())configured=System.getenv("XAR_LOSS_ALLOCATION_GOLDEN");
        assertNotNull(configured,"complete original producer capture is required; no skip or synthesized expected output");
        JsonNode node=StrictJson.parse(Files.readAllBytes(Path.of(configured)),StrictJson.EXPLICIT_MAX_BYTES);
        assertEquals("xar.loss-allocation.complete-original-golden/v1",node.get("schema").textValue());assertTrue(node.get("original_test_count").intValue()>0);assertEquals(0,node.get("original_skipped").intValue());
        assertFalse(node.get("machine_id").textValue().isBlank());assertNotEquals("unknown",node.get("machine_id").textValue());OffsetDateTime.parse(node.get("observed_at_utc").textValue());
        String repository=System.getProperty("xar.repo");if(repository==null||repository.isBlank())repository=System.getenv("XAR_REPO_ROOT");
        assertNotNull(repository,"original source root required");Path repo=Path.of(repository).toRealPath();
        for(JsonNode ref:node.get("source_refs")){Path source=repo.resolve(ref.get("path").textValue()).normalize();assertTrue(source.startsWith(repo));byte[] data=Files.readAllBytes(source);assertEquals(ref.get("bytes").longValue(),data.length);assertEquals(ref.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data)),source.toString());}
        return node;
    }
}

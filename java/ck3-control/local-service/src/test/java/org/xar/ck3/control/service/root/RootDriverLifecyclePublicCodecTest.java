package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;
import static org.xar.ck3.control.service.root.RootDriverLifecyclePublicCodec.*;

/** Typed public input/output DATA only; no Root/M3/native token is manufactured by these fixtures. */
final class RootDriverLifecyclePublicCodecTest {
    private static RawJson raw(String value){return new RawJson(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static PublicBindings.Value value(String input){return new PublicBindings.Value(raw(input));}
    private static final BigInteger HIGH=new BigInteger("18446744073709551615");
    /** Actual private pure runtime producer -> original material serde -> public report; software DATA only. */
    @Test void actualRuntimeEndingBindingRetainsPlayerIdentityThroughCloseReport()throws Exception {
        var cases=(org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr)originalCases().get("cases");
        var row=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(cases.items().get(1),"POST_ADVANCE_UNCONFIRMED original case");
        var source=(SubmittedClose)material(row);
        assertEquals(row.get("expected"),DriverJson.object(projectClose(source).bytes(),RawJson.MAXIMUM_BYTES));
        var semantic=DriverJson.object(source.endingSnapshot().bytes(),RawJson.MAXIMUM_BYTES);
        var producer=RootPendingUiRuntime.class.getDeclaredMethod("rawBinding",org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj.class,String.class,BigInteger.class,BigInteger.class);
        producer.setAccessible(true);
        var ending=(RawJson)producer.invoke(null,semantic,"actual-runtime-ending-binding",HIGH,HIGH.subtract(BigInteger.ONE));
        var binding=DriverJson.object(ending.bytes(),RawJson.MAXIMUM_BYTES);
        assertNotEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,binding.get("played_character_id"));
        assertNotEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,binding.get("played_character_alive"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(BigInteger.valueOf(35465)),binding.get("played_character_id"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true),binding.get("played_character_alive"));
        assertThrows(IllegalArgumentException.class,()->new SubmittedClose(ClosePhase.POST_ADVANCE_UNCONFIRMED,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),ending,source.lifeResult(),source.failure()));
        var actual=new SubmittedClose(ClosePhase.POST_ADVANCE_UNCONFIRMED,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),new EndingBinding(ending),source.lifeResult(),source.failure());
        for(var invalid:java.util.List.of(binding.with("played_character_id",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true)),binding.with("played_character_alive",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(BigInteger.ONE)),binding.with("played_character",semantic.get("played_character"))))assertThrows(IllegalArgumentException.class,()->new EndingBinding(json(invalid)));
        assertThrows(IllegalArgumentException.class,()->new EndingBinding(source.endingSnapshot()));
        var absentPlayed=new java.util.LinkedHashMap<>(semantic.members());absentPlayed.remove("played_character");
        for(var nested:java.util.List.of(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(absentPlayed),semantic.with("played_character",org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE))){
            var unavailable=new SubmittedClose(ClosePhase.POST_ADVANCE_UNCONFIRMED,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),json(nested),source.lifeResult(),source.failure());
            var after=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(DriverJson.object(projectClose(unavailable).bytes(),RawJson.MAXIMUM_BYTES).get("post_advance_snapshot"),"unavailable nested player");
            assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,after.get("played_character_id"));
            assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE,after.get("played_character_alive"));
        }
        var archived=encodeMaterial(actual);var replay=decodeMaterial(archived);assertArrayEquals(archived.bytes(),encodeMaterial(replay).bytes());
        for(var input:java.util.List.of(actual,replay)){
            var report=DriverJson.object(projectClose(input).bytes(),RawJson.MAXIMUM_BYTES);
            var after=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(report.get("post_advance_snapshot"),"actual ending binding in public report");
            assertEquals(binding.get("played_character_id"),after.get("played_character_id"));
            assertEquals(binding.get("played_character_alive"),after.get("played_character_alive"));
            assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(HIGH),after.get("revision"));
            assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(HIGH.subtract(BigInteger.ONE)),after.get("native_revision"));
        }
        // A genuine software Life result and its very same ending Frame enter the actual public codecs.
        var life=producedLifeMaterial(source.startingDateRaw());var endpoint=life.ending();
        var publicEnding=(RawJson)producer.invoke(null,endpoint.semantic(),endpoint.identity().frame().snapshotId(),endpoint.identity().frame().revision(),endpoint.identity().frame().identity().nativeRevision());
        var publicMaterial=new SubmittedClose(ClosePhase.POST_ADVANCE_UNCONFIRMED,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),new EndingBinding(publicEnding),Optional.of(life.original()),source.failure());
        var publicReport=encodeCloseMaterial(publicMaterial);
        assertArrayEquals(publicReport.bytes(),encodeCloseData(decodeCloseData(publicReport)).bytes());
        var publicRow=PublicDataJson.object(publicReport);var publicAfter=publicRow.get("post_advance_snapshot");
        assertEquals("post_advance_unconfirmed",publicRow.get("status").textValue());assertFalse(publicRow.get("material_result_verified").booleanValue());
        assertEquals(HIGH.toString(),publicRow.get("ending_revision").textValue());assertEquals(HIGH.toString(),publicRow.get("ending_native_revision").textValue());
        assertEquals(HIGH.toString(),publicAfter.get("revision").textValue());assertEquals(HIGH.toString(),publicAfter.get("native_revision").textValue());
        assertEquals(BigInteger.valueOf(35465),publicAfter.get("played_character_id").bigIntegerValue());assertTrue(publicAfter.get("played_character_alive").booleanValue());
        assertEquals(endpoint.identity().frame().episodeRunId(),publicAfter.get("episode_run_id").textValue());
        assertEquals(endpoint.identity().frame().identity().dateRaw(),publicAfter.get("date_raw").bigIntegerValue());
        assertEquals(HIGH.subtract(BigInteger.ONE).toString(),publicRow.get("life_advance_result").get("starting_revision").textValue());
        assertTrue(new String(publicReport.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("-0.0"));
    }
    @Test void threeOriginalInputsShareRevisionCodecAndPreserveMissingNull(){
        assertTrue(resume(new PublicBindings.Missing()).original().expectedRevision() instanceof LifecyclePublicCodec.MissingRevision);
        assertTrue(resume(value("{\"expected_revision\":null}")).original().expectedRevision() instanceof LifecyclePublicCodec.NullRevision);
        var query=query(value("{\"expected_revision\":\"18446744073709551615\"}"));assertEquals(HIGH,query.expectedRevision());assertEquals(query,query(encode(query)));
        var close=close(value("{\"expected_revision\":\"18446744073709551615\",\"expected_played_character_id\":23,\"expected_episode_run_id\":\"new-run\"}"));assertEquals(HIGH,close.expectedRevision());assertEquals(close,close(encode(close)));
    }
    @Test void requiredInputsRejectNullMissingBooleanFloatAndUnexpectedCloseFlags(){
        for(var wrong:new PublicBindings.Arguments[]{new PublicBindings.Missing(),new PublicBindings.Null(),value("{}"),value("{\"expected_revision\":null}"),value("{\"expected_revision\":true}"),value("{\"expected_revision\":1.0}"),value("{\"expected_revision\":1}"),value("{\"expected_revision\":\"01\"}")})assertThrows(IllegalArgumentException.class,()->query(wrong));
        assertThrows(IllegalArgumentException.class,()->resume(value("{\"allow_close\":true}")));
        assertThrows(IllegalArgumentException.class,()->close(value("{\"expected_revision\":\"1\",\"expected_played_character_id\":true,\"expected_episode_run_id\":\"new\"}")));
        assertThrows(IllegalArgumentException.class,()->close(value("{\"expected_revision\":\"1\",\"expected_played_character_id\":3.0,\"expected_episode_run_id\":\"new\"}")));
    }
    @Test void publicViewRoundtripRetainsOriginalDecimalTokensAndUnknownNoReplay(){
        var reference=new ExactRef("D:/synthetic-public-ui/actual-original-receipt",3,"a".repeat(64));
        var snapshot=raw("{\"revision\":\"18446744073709551615\",\"one_life_settlement\":{\"final_score\":-0.0,\"inherited_partial_score\":1.0},\"nullable\":null}");
        var original=new View(Status.UI_UNRESOLVED,true,false,false,snapshot,Optional.empty(),Optional.of(new CloseResult(ActionReceipt.Outcome.UNRESOLVED,"original",reference,false,Optional.empty())),"synthetic-public-machine",Instant.parse("2026-10-24T06:00:00Z"));
        var encoded=encode(original);var decoded=decodeView(encoded);assertEquals(original.status(),decoded.status());assertEquals(original.close(),decoded.close());assertEquals(DriverJson.object(snapshot.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(decoded.snapshot().bytes(),RawJson.MAXIMUM_BYTES));
        assertArrayEquals(encoded.bytes(),encode(decoded).bytes());assertEquals(ActionReceipt.Outcome.UNRESOLVED,decoded.close().orElseThrow().outcome());assertFalse(decoded.actionSubmitted());
        var wrong=PublicDataJson.object(encoded);wrong.put("date_advanced",true);assertThrows(IllegalArgumentException.class,()->decodeView(PublicDataJson.encode(wrong)));
        var replay=PublicDataJson.object(encoded);((com.fasterxml.jackson.databind.node.ObjectNode)replay.get("close_result")).put("replay_authorized",true);assertThrows(IllegalArgumentException.class,()->decodeView(PublicDataJson.encode(replay)));
    }
    @Test void reconciliationPublicWirePreservesUnknownConfirmedDateAndBlockedSelectionOriginals(){
        var unknown=new ExactRef("pure-ui/original-unknown",5,"a".repeat(64));var confirmed=new ExactRef("pure-ui/actual-confirmed",7,"b".repeat(64));var proof=new ExactRef("pure-ui/same-original-action",9,"c".repeat(64));var date=new ExactRef("pure-ui/actual-life-date",11,"d".repeat(64));var diagnosis=new ExactRef("pure-ui/retained-event-diagnosis",13,"e".repeat(64));
        var reconciliation=new org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.ReadOnlyReconciliation(unknown,confirmed,proof,Optional.of(confirmed),Optional.of(date));
        var close=new CloseResult(ActionReceipt.Outcome.UNRESOLVED,"original-close",unknown,true,Optional.of(date),Optional.of(reconciliation));
        var actual=new View(Status.CLEAR,true,false,false,raw("{\"one_life_settlement\":{\"final_score\":-0.0,\"inherited_partial_score\":1.0}}"),Optional.empty(),Optional.of(close),"pure-ui",Instant.parse("2026-10-24T07:00:00Z"),Optional.of(diagnosis));
        var encoded=encode(actual);var decoded=decodeView(encoded);assertEquals(actual.close(),decoded.close());assertEquals(actual.eventDiagnosis(),decoded.eventDiagnosis());assertArrayEquals(encoded.bytes(),encode(decoded).bytes());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED,decoded.close().orElseThrow().outcome());assertEquals(unknown,decoded.close().orElseThrow().canonicalReceipt());assertEquals(confirmed,decoded.close().orElseThrow().reconciliation().orElseThrow().confirmedReceipt());
        var wire=PublicDataJson.object(encoded);((com.fasterxml.jackson.databind.node.ObjectNode)wire.get("close_result").get("read_only_reconciliation")).set("original_unknown_receipt",confirmed.toJson());assertThrows(IllegalArgumentException.class,()->decodeView(PublicDataJson.encode(wire)));
    }
    @Test void publicTimelineDataKeepsFullWidthCountersWithoutRecreatingNativeQueryAuthority(){
        var row=PublicDataJson.object(raw("{\"step\":\"query-current-timeline-blocker-context-v1\",\"accepted\":true,\"status\":\"unavailable\",\"query_sequence\":\"18446744073709551615\",\"observation_revision\":\"18446744073709551615\",\"snapshot_revision\":\"18446744073709551615\",\"current_timeline_blocker_context\":{\"status\":\"unavailable\",\"snapshot_revision\":\"18446744073709551615\",\"retained_native_context\":null},\"private_build\":true,\"read_only\":true,\"advertised\":false,\"backend_id\":\"native-headless\",\"machine_id\":\"pure-public-ui\",\"observed_at_utc\":\"2026-10-24T07:00:00Z\"}"));
        var original=PublicDataJson.encode(row);var actual=decodeTimelineData(original);assertEquals(HIGH,actual.querySequence());assertEquals(HIGH,actual.snapshotRevision());assertArrayEquals(original.bytes(),encodeTimelineData(actual).bytes());
        var numeric=row.deepCopy();numeric.put("query_sequence",HIGH);assertThrows(IllegalArgumentException.class,()->decodeTimelineData(PublicDataJson.encode(numeric)));
        var malformed=row.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)malformed.get("current_timeline_blocker_context")).put("snapshot_revision","1");assertThrows(IllegalArgumentException.class,()->decodeTimelineData(PublicDataJson.encode(malformed)));
        var missing=row.deepCopy();missing.remove("read_only");assertThrows(IllegalArgumentException.class,()->decodeTimelineData(PublicDataJson.encode(missing)));
    }
    @Test void originalPythonProducerReportsReachTypedCarrierAndExactInternalSerde()throws Exception {
        var corpus=originalCases();
        for(var item:((org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr)corpus.get("cases")).items()){
            var row=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(item,"case");var material=material(row);
            assertEquals(row.get("expected"),DriverJson.object(projectClose(material).bytes(),RawJson.MAXIMUM_BYTES));
            var restored=decodeMaterial(encodeMaterial(material));assertEquals(material,restored);
            assertArrayEquals(projectClose(material).bytes(),projectClose(restored).bytes());
            // The original Python oracle deliberately supplies a minimal Life mapping to its permissive helper.
            // It is valid numeric-oracle DATA, but is not a migrated Life21 schema and must not pass that owner parser.
            if(material instanceof SubmittedClose submitted&&submitted.lifeResult().isPresent())assertThrows(IllegalArgumentException.class,()->encodeCloseMaterial(material));
            else if(material instanceof ReclaimClose reclaim)actualReclaimPublicRoundtrip(reclaim);
            else{RawJson publicClose=encodeCloseMaterial(material);assertArrayEquals(publicClose.bytes(),encodeCloseData(decodeCloseData(publicClose)).bytes());}
            RawJson actualQuery=material instanceof SubmittedClose submitted?submitted.initialQuery():((ReclaimClose)material).initialQuery();
            RawJson publicQuery=encodeTimelineOriginal(actualQuery);
            assertEquals(DriverJson.object(actualQuery.bytes(),RawJson.MAXIMUM_BYTES),DriverJson.object(decodeTimelineOriginal(publicQuery).bytes(),RawJson.MAXIMUM_BYTES));
            assertArrayEquals(publicQuery.bytes(),encodeTimelineOriginal(decodeTimelineOriginal(publicQuery)).bytes());
        }
    }
    @Test void actualClosePublicConsumerUsesFullReportAndCanonicalKnownUint64Roles()throws Exception {
        var row=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(((org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr)originalCases().get("cases")).items().getFirst(),"case");
        var source=(SubmittedClose)material(row);var ack=PublicDataJson.object(source.submissionAck());ack.put("snapshot_revision",HIGH);ack.put("action_observation_revision",HIGH.subtract(BigInteger.TWO));
        var initial=PublicDataJson.object(source.initialQuery());initial.put("snapshot_revision",HIGH);((com.fasterxml.jackson.databind.node.ObjectNode)initial.get("current_timeline_blocker_context")).put("snapshot_revision",HIGH);initial.put("query_sequence",HIGH.subtract(BigInteger.TWO));initial.put("observation_revision",HIGH.subtract(BigInteger.valueOf(3)));
        var actual=new SubmittedClose(ClosePhase.SUBMITTED_UNCONFIRMED,PublicDataJson.encode(ack),PublicDataJson.encode(initial),java.util.List.of(),source.startingDateRaw(),raw("{\"revision\":18446744073709551615,\"native_revision\":18446744073709551615,\"date_raw\":"+source.startingDateRaw()+",\"score\":-0.0}"),Optional.empty(),Optional.of("actual bounded post observation unavailable"));
        var view=view(actual,false);var report=RootDriverLifecyclePublicSupplier.closeResponse(view);var data=decodeCloseData(report);assertArrayEquals(report.bytes(),encodeCloseData(data).bytes());
        var publicRow=PublicDataJson.object(report);assertEquals(HIGH.toString(),publicRow.get("snapshot_revision").textValue());assertEquals(HIGH.toString(),publicRow.get("ending_native_revision").textValue());assertTrue(publicRow.get("submission_ack").get("action_observation_revision").isTextual());
        assertFalse(publicRow.has("canonical_receipt"));assertTrue(publicRow.has("post_query_attempts"));assertTrue(publicRow.get("life_advance_result").isNull());
        for(var wrong:java.util.List.of(raw("{\"schema\":\"xar.java.original-close-material/v1\",\"kind\":true}"),raw("{\"schema\":\"xar.java.original-close-material/v1\",\"kind\":\"UNKNOWN\"}")))assertThrows(IllegalArgumentException.class,()->decodeMaterial(wrong));
        for(String value:java.util.List.of("true","1.0","\"01\"","\"18446744073709551616\"","1")){
            String changed=new String(report.bytes(),java.nio.charset.StandardCharsets.UTF_8).replaceFirst("\\\"snapshot_revision\\\":\\\"18446744073709551615\\\"","\"snapshot_revision\":"+value);
            assertThrows(IllegalArgumentException.class,()->decodeCloseData(raw(changed)));
        }
        var noMaterial=new View(view.status(),view.pending(),false,false,view.snapshot(),view.transition(),view.close(),view.machineId(),view.observedAtUtc());
        assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->RootDriverLifecyclePublicSupplier.closeResponse(noMaterial));
    }
    @Test void lifeEmbeddingPreservesOriginalDecimalTokenAndUsesOwningLifeFormatter()throws Exception {
        var row=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(((org.xar.ck3.control.planning.opportunity.OpportunityJson.Arr)originalCases().get("cases")).items().getFirst(),"case");var source=(SubmittedClose)material(row);
        var life=producedLife(source.startingDateRaw());
        for(var phase:java.util.List.of(ClosePhase.MATERIALLY_VERIFIED,ClosePhase.POST_ADVANCE_UNCONFIRMED)){
            var actual=new SubmittedClose(phase,source.submissionAck(),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),raw("{\"revision\":18446744073709551615,\"native_revision\":18446744073709551615,\"date_raw\":"+(source.startingDateRaw()+24)+"}"),Optional.of(life),phase==ClosePhase.MATERIALLY_VERIFIED?Optional.empty():Optional.of("bounded post-query unavailable"));
            var report=RootDriverLifecyclePublicSupplier.closeResponse(view(actual,phase==ClosePhase.MATERIALLY_VERIFIED));
            assertTrue(new String(report.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("-0.0"));
            assertArrayEquals(report.bytes(),encodeCloseData(decodeCloseData(report)).bytes());
        }
        var bad=PublicDataJson.object(source.submissionAck());bad.put("close_invocations",true);assertThrows(IllegalArgumentException.class,()->new SubmittedClose(source.phase(),PublicDataJson.encode(bad),source.initialQuery(),source.postAttempts(),source.startingDateRaw(),source.endingSnapshot(),source.lifeResult(),source.failure()));
    }
    /** Actual AdvanceResult.json production consumer on complete typed software DATA; no Root or day qualification. */
    private record LifeMaterial(RawJson original,org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame ending) { }
    private static RawJson producedLife(int date){return producedLifeMaterial(date).original();}
    private static LifeMaterial producedLifeMaterial(int date){
        var now=Instant.parse("2026-10-24T08:00:00Z");
        var source=new org.xar.ck3.control.g2.common.G2Source("pure-life-producer-data",now.toString(),"software-only",
                new ExactRef("pure-life-producer-DATA/source",1,"a".repeat(64)));
        var starting=lifeFrame(source,"pure-life-before",HIGH.subtract(BigInteger.ONE),date,1,now);
        var ending=lifeFrame(source,"pure-life-after",HIGH,date+24,2,now);
        var plan=new org.xar.ck3.control.application.advance.AdvancePlan(BigInteger.valueOf(date),BigInteger.valueOf(date+24),1,1,"pure-result-DATA",true,
                org.xar.ck3.control.application.advance.AdvancePlan.ClockMode.POLLED,Optional.empty());
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,starting.identity(),source,
                org.xar.ck3.control.application.advance.AdvancePlan.OBSERVER,plan.expected());
        var command=new ActionCommand("pure-life-result-DATA",starting.identity(),source,"pure-life-session",new OperationKey("life-advance"),
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()).with(org.xar.ck3.control.application.advance.AdvancePlan.KEY,plan.json()),expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),now.plusSeconds(30));
        var diagnostics=new org.xar.ck3.control.application.advance.AdvanceClock.Diagnostics(BigInteger.valueOf(date),BigInteger.valueOf(date+24),1,1,1,"pure-result-DATA",
                org.xar.ck3.control.application.advance.AdvanceClock.ProgressStatus.POSTCONDITION,Optional.empty(),Optional.empty(),false,java.util.List.of(),0L,Optional.empty());
        var result=new org.xar.ck3.control.application.advance.AdvanceResult(command,plan,starting,
                new org.xar.ck3.control.application.advance.AdvanceClock.Outcome(ending,diagnostics),java.util.List.of());
        return new LifeMaterial(new RawJson(DriverJson.encode(result.json())),ending);
    }
    private static org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame lifeFrame(
            org.xar.ck3.control.g2.common.G2Source source,String id,BigInteger revision,int date,long sequence,Instant now){
        var proposal=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(35465),revision,BigInteger.valueOf(date)),id,revision,"pure-life-episode");
        var identity=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(source.machineId(),new GameGeneration(4242,new PythonOnlyUInt64(BigInteger.ONE)),proposal,sequence);
        var semantic=DriverJson.object(raw("{\"snapshot_id\":\""+id+"\",\"revision\":"+revision+",\"native_revision\":"+revision+",\"date_raw\":"+date+",\"episode_run_id\":\"pure-life-episode\",\"played_character\":{\"character_id\":35465,\"alive\":true},\"paused\":true,\"map_ready\":true,\"speed\":1,\"active_wars\":[{\"war_id\":1,\"player_relative_war_score\":-0.0}],\"player_armies\":[],\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"diagnostics\":{}}").bytes(),RawJson.MAXIMUM_BYTES);
        byte[] original=DriverJson.encode(semantic);var reference=new ExactRef("pure-life-producer-DATA/"+id,original.length,ActionCodec.sha256(original));
        return new org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame(identity,source,"pure-life-session",semantic,"pure-query-"+id,now,reference);
    }
    private static View view(CloseMaterial material,boolean completed){
        var reference=new ExactRef("pure-report-data/canonical",3,"a".repeat(64));var date=completed?Optional.of(new ExactRef("pure-report-data/date",5,"b".repeat(64))):Optional.<ExactRef>empty();
        var base=new View(Status.UI_UNRESOLVED,true,false,false,raw("{\"revision\":\"1\"}"),Optional.empty(),Optional.of(new CloseResult(completed?ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT:ActionReceipt.Outcome.UNRESOLVED,"actual-data",reference,completed,date)),"data-only",Instant.parse("2026-10-24T08:00:00Z"));return withCloseMaterial(base,material);
    }
    /** Current fixture inputs travel through actual Driver import, Native framing and manifest/assembler producers. */
    private static RawJson producedReclaimSnapshot(RawJson original) throws Exception {
        var before=DriverJson.object(original.bytes(),RawJson.MAXIMUM_BYTES);
        var wire=DriverJson.object(fixtureInput("DriverStateAssemblerTest","WIRE"),RawJson.MAXIMUM_BYTES);
        var campaign=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(wire.get("campaign_goal"),"campaign");
        var anchor=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(campaign.get("anchor"),"anchor");
        var lifecycle=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(wire.get("succession_lifecycle"),"lifecycle");
        var current=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(lifecycle.get("current"),"current");
        wire=wire.with("episode_character_id",before.get("episode_character_id")).with("episode_run_id",before.get("episode_run_id"))
                .with("campaign_goal",campaign.with("anchor",anchor.with("character_id",before.get("episode_character_id"))))
                .with("succession_lifecycle",lifecycle.with("current",current.with("episode",before.get("episode_run_id"))));
        var state=DriverJson.object(fixtureInput("DriverObservationAssemblerTest","STATE"),RawJson.MAXIMUM_BYTES);
        for(String key:java.util.List.of("paused","map_ready","date_raw","played_character","active_event","pending_character_interaction","one_life_terminal_reason"))state=state.with(key,before.get(key));
        var game=new GameGeneration(org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(wire.get("bridge_pid"),"pid").longValueExact(),
                new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        byte[] driverBytes=DriverJson.encode(wire);
        var known=DriverFactsRepository.imported(reclaimReference("driver-input.json",driverBytes),driverBytes,3,7,game,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()));
        String snapshot=org.xar.ck3.control.planning.opportunity.OpportunityJson.text(before.get("snapshot_id"),"snapshot_id");
        BigInteger revision=org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(before.get("revision"),"revision"),nativeRevision=org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(before.get("native_revision"),"native_revision");
        byte[] stateBytes=DriverJson.encode(state);
        byte[] envelope=DriverJson.encode(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of(
                "protocol_version",new org.xar.ck3.control.planning.opportunity.OpportunityJson.IntegerValue(BigInteger.ONE),
                "type",new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("state_snapshot"),
                "snapshot_id",before.get("snapshot_id"),"revision",before.get("native_revision"),"state",state)));
        byte[] packet=java.nio.ByteBuffer.allocate(envelope.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(envelope.length).put(envelope).array();
        var observed=Instant.parse("2026-10-24T04:00:00Z");
        var session=new NativeObservationPort.TransportSession("pure-reclaim-data",game,BigInteger.valueOf(5),"pure-reclaim-session");
        var nativeFrame=new NativeObservationPort.ObservedFrame(session,snapshot,nativeRevision,new RawJson(stateBytes),packet,observed);
        var driver=new RawJson(known.driver().encode());
        var source=new org.xar.ck3.control.g2.common.G2Source(session.machineId(),observed.toString(),"pure-reclaim-data",reclaimReference("source.json",driverBytes));
        var manifest=DriverObservationEvidenceReader.encode(known,nativeFrame,revision,2,source,
                new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),reclaimReference("complete-driver.json",driver.bytes()));
        var facts=DriverObservationEvidenceReader.decode(reclaimReference("facts.json",manifest.bytes()),manifest,driver,nativeFrame);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,reclaimReference("native.bin",packet)));
        for(String key:java.util.List.of("snapshot_id","revision","native_revision","date_raw","paused","map_ready","episode_character_id","episode_run_id","played_character"))assertEquals(before.get(key),complete.semantic().get(key),key);
        return RawJson.fullMaterial(DriverJson.encode(complete.semantic()));
    }
    private static byte[] fixtureInput(String owner,String field) throws Exception {
        var root=java.nio.file.Path.of(System.getProperty("xar.repository.root"));
        String source=java.nio.file.Files.readString(root.resolve("java/ck3-control/application/src/test/java/org/xar/ck3/control/application/driver/"+owner+".java"),java.nio.charset.StandardCharsets.UTF_8);
        String marker="static final String "+field+"=\"\"\"";int start=source.indexOf(marker);
        assertTrue(start>=0&&source.indexOf(marker,start+marker.length())<0,"unique current input fixture required");start+=marker.length();
        int end=source.indexOf("\"\"\"",start);assertTrue(end>start,"complete current input fixture required");
        return source.substring(start,end).strip().getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }
    private static ExactRef reclaimReference(String name,byte[] bytes){
        return new ExactRef(java.nio.file.Path.of(System.getProperty("java.io.tmpdir"),"pure-reclaim-data",name).toAbsolutePath().toString(),bytes.length,DriverJson.sha256(bytes));
    }
    private static void actualReclaimPublicRoundtrip(ReclaimClose source) throws Exception {
        var failure=assertThrows(IllegalArgumentException.class,()->encodeCloseMaterial(source));
        assertEquals("format_version must be an integer token",failure.getMessage());
        byte[] requestBefore=source.originalRequest().bytes(),frameBefore=source.originalCommandResult().bytes();
        var snapshot=producedReclaimSnapshot(source.preSubmissionSnapshot());
        var actual=new ReclaimClose(source.originalRequest(),source.originalCommandResult(),snapshot,source.initialQuery(),source.retainedSubmissionAck(),source.retainedAckValidationError());
        RawJson publicClose=encodeCloseMaterial(actual);assertArrayEquals(publicClose.bytes(),encodeCloseData(decodeCloseData(publicClose)).bytes());
        var numeric=DriverJson.object(projectClose(actual).bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(DriverJson.object(requestBefore,RawJson.MAXIMUM_BYTES),numeric.get("native_request_frame"));
        assertEquals(DriverJson.object(frameBefore,RawJson.MAXIMUM_BYTES),numeric.get("native_command_result_frame"));
        var report=PublicDataJson.object(publicClose);assertFalse(report.get("ok").booleanValue());assertFalse(report.get("material_result_verified").booleanValue());assertFalse(report.get("business_material_verified").booleanValue());
        assertEquals(source.retainedSubmissionAck().isPresent()?"submitted_unconfirmed":"submission_unknown",report.get("status").textValue());
        var before=PublicDataJson.object(source.preSubmissionSnapshot());var full=report.get("actual_pre_submission_snapshot");
        assertEquals(before.get("played_character"),full.get("played_character"));assertEquals(before.get("date_raw"),full.get("date_raw"));assertEquals(before.get("episode_run_id"),full.get("episode_run_id"));
        assertEquals(before.get("revision").bigIntegerValue().toString(),full.get("revision").textValue());assertEquals(before.get("native_revision").bigIntegerValue().toString(),full.get("native_revision").textValue());
        var request=PublicDataJson.object(source.originalRequest());assertEquals(request.get("expected_revision").bigIntegerValue().toString(),report.get("native_request_frame").get("expected_revision").textValue());
        assertEquals(DriverJson.object(frameBefore,RawJson.MAXIMUM_BYTES),org.xar.ck3.control.planning.opportunity.OpportunityJson.object(DriverJson.object(publicClose.bytes(),RawJson.MAXIMUM_BYTES).get("native_command_result_frame"),"original RED"));
        assertArrayEquals(requestBefore,source.originalRequest().bytes());assertArrayEquals(frameBefore,source.originalCommandResult().bytes());
    }
    private static RawJson json(org.xar.ck3.control.planning.opportunity.OpportunityJson.Value value){return new RawJson(DriverJson.encode(value));}
    private static CloseMaterial material(org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj row){
        var data=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(row.get("input"),"input");
        if(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text("RECLAIM").equals(row.get("kind")))return new ReclaimClose(json(data.get("request")),json(data.get("frame")),json(data.get("snapshot")),json(data.get("initial")),data.get("ack")==org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(json(data.get("ack"))),data.get("error")==org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(data.get("error"),"error")));
        var attempts=new java.util.ArrayList<PostQueryAttempt>();for(var value:org.xar.ck3.control.planning.opportunity.OpportunityJson.array(data.get("attempts"),"attempts")){
            var attempt=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(value,"attempt");attempts.add(new PostQueryAttempt(org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(attempt.get("attempt"),"ordinal").intValueExact(),Optional.of(json(attempt.get("query"))),Optional.empty(),Optional.of(json(attempt.get("binding")))));
        }
        return new SubmittedClose(ClosePhase.valueOf(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(row.get("phase"),"phase")),json(data.get("ack")),json(data.get("initial")),attempts,org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(data.get("date"),"date").intValueExact(),json(data.get("snapshot")),data.get("life")==org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(json(data.get("life"))),data.get("failure")==org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE?Optional.empty():Optional.of(org.xar.ck3.control.planning.opportunity.OpportunityJson.text(data.get("failure"),"failure")));
    }
    private static org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj originalCases()throws Exception {
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");assertNotNull(python,"NOT_RUN_REQUIRED_ORIGINAL_CLOSE_PYTHON");assertNotNull(repository,"NOT_RUN_REQUIRED_ORIGINAL_CLOSE_REPOSITORY");
        var base=java.nio.file.Path.of(repository);var source=org.xar.ck3.control.build.SharedSourceFiles.observe(base.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/death_succession_modal_private_transport.py"));var fixture=org.xar.ck3.control.build.SharedSourceFiles.observe(base.resolve("ck3_autonomous_player/tests/unit/test_death_succession_modal_private_transport.py"));
        assertEquals(22301,source.source().bytes());assertEquals("135187b16c0d857c65f53ec24634a45b111219d0e6ac2dd0cf17ab0838726cd2",source.source().sha256());assertEquals(13489,fixture.source().bytes());assertEquals("96db174a3a27eb44005b388729474039d932f48ef55f8e181de42166edcbecf3",fixture.source().sha256());
        String oracle="""
                import ast,copy,json,pathlib,sys,uuid,time
                from collections.abc import Mapping
                root=pathlib.Path(sys.argv[1]);p=root/'ck3_autonomous_player/src/xar_autoplayer/bridge/death_succession_modal_private_transport.py'
                f=root/'ck3_autonomous_player/tests/unit/test_death_succession_modal_private_transport.py'
                tree=ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p));fixture=ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f))
                ns={'copy':copy,'Mapping':Mapping,'uuid':uuid,'time':time,'json':json,'BridgeUnavailableError':type('BridgeUnavailableError',(RuntimeError,),{}),'UnsupportedStepError':type('UnsupportedStepError',(RuntimeError,),{})}
                ns.update(CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP='continue-death-succession-modal-v1',QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP='query-current-timeline-blocker-context-v1',POST_CLOSE_QUERY_LIMIT=8)
                selected=[n for n in fixture.body if isinstance(n,ast.Assign) or isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_snapshot','_timeline','_Endpoint','_State','_Driver')]
                exec(compile(ast.Module(body=selected,type_ignores=[]),str(f),'exec'),ns)
                selected=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
                exec(compile(ast.Module(body=selected,type_ignores=[]),str(p),'exec'),ns)
                e=ns['_Endpoint']();s=ns['_State'](e)
                e.send({'step':ns['QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP'],'request_id':'initial'});initial=s.wait_for_command_result('initial',1)['result']
                e.send({'step':ns['CONTINUE_DEATH_SUCCESSION_MODAL_V1_STEP'],'request_id':'close'});ack=s.wait_for_command_result('close',1)['result']
                e.send({'step':ns['QUERY_CURRENT_TIMELINE_BLOCKER_CONTEXT_V1_STEP'],'request_id':'post'});post=s.wait_for_command_result('post',1)['result']
                before=ns['_snapshot']();after=copy.deepcopy(before);after.update(revision=10,native_revision=78,date_raw=ns['DATE_RAW']+4)
                attempts=[{'attempt':1,'query':post,'error':None,'binding':ns['_post_query_binding'](before)}];life={'step':'life-advance','accepted':True,'original_decimal':-0.0};cases=[]
                for phase in ('SUBMITTED_UNCONFIRMED','POST_ADVANCE_UNCONFIRMED','MATERIALLY_VERIFIED'):
                    failure=None if phase=='MATERIALLY_VERIFIED' else 'retained actual observation failure'
                    data={'ack':ack,'initial':initial,'attempts':attempts,'date':ns['DATE_RAW'],'snapshot':after,'life':None if phase=='SUBMITTED_UNCONFIRMED' else life,'failure':failure}
                    if phase=='SUBMITTED_UNCONFIRMED':expected=ns['_submitted_unconfirmed_result'](ack=ack,initial=initial,post_attempts=attempts,date_raw=ns['DATE_RAW'],snapshot=after,failure=failure)
                    elif phase=='POST_ADVANCE_UNCONFIRMED':expected=ns['_post_advance_unconfirmed_result'](ack=ack,initial=initial,post_attempts=attempts,date_raw=ns['DATE_RAW'],snapshot=after,life_result=life,failure=failure)
                    else:
                        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='continue_death_succession_modal_private_v1');node=fn.body[-1].value
                        env=dict(ns,ack=ack,initial=initial,post_attempts=attempts,post=post,post_observation_revision=post['observation_revision'],life_result=life,date_raw=ns['DATE_RAW'],final_date=after['date_raw'],after_advance=after)
                        expected=eval(compile(ast.Expression(node),str(p),'eval'),env)
                    cases.append({'kind':'SUBMITTED','phase':phase,'input':data,'expected':expected})
                for invalid in (False,True):
                    d=ns['_Driver']();captured={}
                    def wait(request_id,timeout):
                        request=copy.deepcopy(d.endpoint.request);inner={'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,'result':ack}
                        detail={'stage':'reclaim','status':'submitted_unconfirmed','material_result_verified':False,'business_material_verified':False,'reclaim_result_enum':True if invalid else 1,'submitted_ack_frame_exact_json':json.dumps(inner)}
                        frame={'type':'command_result','protocol_version':1,'request_id':request_id,'ok':False,'error':'native reclaim failed','death_succession_close_failure_v1':detail};captured.update(request=request,frame=frame);return frame
                    d.state.wait_for_command_result=wait;ns['query_current_timeline_blocker_context_private_v1']=lambda *args,**kwargs:copy.deepcopy(initial)
                    result=ns['continue_death_succession_modal_private_v1'](d,expected_revision=ns['PUBLIC_REVISION'],expected_played_character_id=ns['CHARACTER_ID'],expected_episode_run_id=ns['EPISODE_RUN_ID'])
                    data=dict(captured,snapshot=before,initial=initial,ack=None if invalid else ack,error=result.get('retained_ack_validation_error'))
                    cases.append({'kind':'RECLAIM','input':data,'expected':result})
                print(json.dumps({'cases':cases},allow_nan=False))
                """;
        var child=new ProcessBuilder(python,"-c",oracle,repository).redirectErrorStream(true).start();
        try(var readers=java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()){
            var output=readers.submit(()->child.getInputStream().readNBytes(131073));
            try{
                if(!child.waitFor(30,java.util.concurrent.TimeUnit.SECONDS)){child.destroyForcibly();fail("original Close oracle timed out");}
                byte[] bytes=output.get(5,java.util.concurrent.TimeUnit.SECONDS);assertTrue(bytes.length<=131072);
                assertEquals(0,child.exitValue(),new String(bytes,java.nio.charset.StandardCharsets.UTF_8));return DriverJson.object(bytes,131072);
            }finally{child.destroyForcibly();child.getInputStream().close();output.cancel(true);org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(source);org.xar.ck3.control.build.SharedSourceFiles.assertUnchanged(fixture);}
        }
    }
}

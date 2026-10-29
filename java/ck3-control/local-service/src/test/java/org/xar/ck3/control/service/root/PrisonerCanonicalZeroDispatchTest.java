package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.prisoners.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerNativeQueries;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.prisoners.releasepreview.*;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.*;

/** Actual software collector/guard/coordinator/writer/archive to domain verifier/reducer; no managed Root or live Game qualification. */
final class PrisonerCanonicalZeroDispatchTest {
    @TempDir Path temporary;
    @Test void actualIntentBarrierZeroWriteCanResolveOnlyItsCanonicalUnsubmittedPending()throws Exception {
        for(var family:PrisonerPlanningPorts.Family.values()){
            var operation=family==PrisonerPlanningPorts.Family.RELEASE?PrisonerOrdinaryPolicy12004.RELEASE:PrisonerOrdinaryPolicy12004.RANSOM;
            var queries=new AtomicReference<PrisonerNativeQueries>();var preparation=new AtomicReference<PrisonerActionBinding12004>();
            var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(CachedSuccession12004.EXE_SHA256.toLowerCase(java.util.Locale.ROOT),"prisoner-zero-software",
                    source->{var actual=new PrisonerNativeQueries(source,(ordinal,request,args)->{});queries.set(actual);return List.of(actual.contract(0));},
                    request->collection(request.step()),Optional.of("1.20.0.4@sha256:"+CachedSuccession12004.EXE_SHA256),Set.of(PrisonerNativeQueries.PERMISSION));
            var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"controlled-prisoner-action",
                    (command,attempt,dispatch)->{throw new AssertionError("zero dispatch has no native poststate");},
                    ()->{throw new AssertionError("the actual central intent barrier must prevent every native action write");},Optional.empty(),
                    Optional.of(source->new NativePrivateActionPermission(operation,"controlled-prisoner-software",source,
                            request->StrictJson.require(request.requiredCapability().isEmpty(),"exact private primitive required"),
                            (config,hello,guard,request)->source)),true,
                    Optional.of(command->preparation.get().prepare(command)));
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve(family.name()),false,reads,List.of(action))){
                var original=fixture.command("read-basis-"+family);var contract=queries.get().contract(0);
                var result=fixture.reads.read(contract,new PlanningReadRequest(original.before(),original.source(),original.sessionId(),contract.operation(),
                        PrisonerNativeQueries.arguments(new PrisonerOptionIntent.Unconditional(),java.util.OptionalLong.empty()),Instant.now().plusSeconds(20)));
                if(!(result instanceof PlanningReadResult.Known<RawJson> read))throw new AssertionError("actual software prisoner query must be available");
                var actualKnown=new PlanningReadResult.Known<>(contract.replay(read.receipt()),read.receipt(),read.originalReceipt());
                var current=fixture.command("zero-"+family);
                fixture.writer.locked(same->{
                    var archived=fixture.archive.withSession(same);var binding=new PrisonerActionBinding12004(archived,new PrisonerPlanningPorts.Queries(queries.get().contracts(),Map.of()));preparation.set(binding);
                    var wallet=StrictJson.object();wallet.putObject("played_character_gold").put("raw",100_000_000).put("scale",100_000);
                    var command=binding.bindPublic(current.actionId(),current.before(),current.source(),current.sessionId(),current.deadline(),
                            OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(wallet)),"actual software wallet DATA"),actualKnown,actualKnown.value(),303,operation);
                    // Audit DATA body only. Live v2 preview/commit requires the real installed Core and remains a separate whole-Root check.
                    var clear=new RawJson((family==PrisonerPlanningPorts.Family.RELEASE?"{\"pending\":null,\"resolved\":null}":"{\"schema\":\"xar.ck3.prisoner-ransom-formal.v1\",\"pending\":null,\"resolved\":null}").getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    var pending=PrisonerLedgerReducer12004.prepare(family,clear,command,binding.selected(command));
                    fixture.stopAtIntentBarrier.set(4);
                    var stopped=assertThrows(ReadPublicationRequiredException.class,()->fixture.coordinator.execute(same,command));
                    var receipt=stopped.zeroDispatchReceipt().orElseThrow();var zero=assertInstanceOf(ActionState.RejectedBeforeDispatch.class,receipt.state());
                    assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.dispatch().proof().stage());assertEquals(0,zero.dispatch().proof().requestBytesWritten());
                    assertEquals(binding.prepare(command),zero.attempt().preparedRequest());assertEquals(0,fixture.nativeActionWrites());
                    assertEquals(receipt,ContinuityActionJournal.lookup(same.head().state(),command.actionId(),archived).orElseThrow());
                    PrisonerLegacyBinding12004.verifyOriginal(same.head(),archived,binding,family,pending,receipt);
                    assertEquals(2,PrisonerLegacyBinding12004.originalLineage(same.head(),archived,receipt).size());
                    var material=PrisonerLedgerReducer12004.zeroMaterial(receipt);var resolved=PrisonerLedgerReducer12004.resolve(family,pending,receipt,material);
                    var body=StrictJson.parse(resolved.bytes());assertTrue(body.get("pending").isNull());assertEquals("rejected_before_dispatch",body.path("resolved").get("status").textValue());
                    for(String flag:List.of("material_result","postcondition_verified","payment_observed","freedom_observed","relationship_effect_verified","game_advanced"))assertFalse(body.path("resolved").get(flag).booleanValue());
                    assertFalse(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());assertEquals(body,StrictJson.parse(new RawJson(StrictJson.canonical(body)).bytes()));
                    var forged=new ActionReceipt(receipt.version(),receipt.sequence()+1,receipt.command(),receipt.bodySha256(),receipt.state());
                    assertThrows(IllegalArgumentException.class,()->PrisonerLegacyBinding12004.verifyOriginal(same.head(),archived,binding,family,pending,forged));
                    var unknown=new ActionReceipt(receipt.version(),receipt.sequence(),receipt.command(),receipt.bodySha256(),new ActionState.Unknown(Optional.of(zero.attempt()),Optional.empty(),"DATA only unresolved outcome",List.of()));
                    assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.resolve(family,pending,unknown,material));
                    var legacy=StrictJson.parse(pending.bytes());var legacyPending=(com.fasterxml.jackson.databind.node.ObjectNode)legacy.get("pending");
                    var retainedAck=legacyPending.putObject("action_ack").put("status","submitted_verification_pending").put("material_result",false).put("request_id",zero.attempt().requestId());
                    for(String key:List.of("pre_native_revision","pre_date_raw","player_character_id","prisoner_character_id"))retainedAck.set(key,legacyPending.get(key));
                    for(String key:family==PrisonerPlanningPorts.Family.RELEASE?List.of("release_query_sequence","release_option_mask_bits"):List.of("payer_character_id","quoted_gold_raw","selected_option"))retainedAck.set(key,legacyPending.get(key));
                    var legacyBody=new RawJson(StrictJson.canonical(legacy));
                    assertThrows(IllegalArgumentException.class,()->PrisonerLegacyBinding12004.verifyOriginal(same.head(),archived,binding,family,legacyBody,receipt));
                    assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.resolve(family,legacyBody,receipt,material));
                    var altered=StrictJson.parse(material.bytes());((com.fasterxml.jackson.databind.node.ObjectNode)altered).put("payment_observed",true);
                    assertThrows(IllegalArgumentException.class,()->PrisonerLedgerReducer12004.resolve(family,pending,receipt,new RawJson(StrictJson.canonical(altered))));
                    long sequence=same.head().state().sequence();assertEquals(receipt,fixture.coordinator.execute(same,command));assertEquals(sequence,same.head().state().sequence());
                    assertEquals(0,fixture.nativeActionWrites());return null;
                });
            }
        }
    }
    private static RawJson collection(String step){
        var payload=StrictJson.object().put("step",step).put("accepted",true).put("status","available").put("query_sequence",11).put("observation_revision",12)
                .put("snapshot_revision",1).put("private_build",true).put("read_only",true).put("advertised",false).put("backend_id","native-headless");
        var value=payload.putObject("player_prisoner_collection").put("schema","player-prisoner-collection-private-v1").put("schema_version",6).put("snapshot_revision",1)
                .put("status","available").putNull("unavailable_reason").put("date_raw",ActionWriterIntegrationFixture.INITIAL_DATE_RAW).put("played_character_id",73).put("total_count",1).put("returned_count",1)
                .put("collection_complete",true).put("played_house_id",17).put("played_dynasty_id",17).put("played_dread_raw",0);
        var row=value.putArray("prisoners").addObject().put("source_ordinal",0).put("prisoner_character_id",303).put("collection_owner_character_id",73).put("jailer_character_id",73)
                .put("custody_relation_verified",true).put("house_id",17).put("dynasty_id",17).put("same_house",true).put("same_dynasty",true).put("is_child_of_played_character",true).put("primary_title_tier_raw",6);
        var frame=new FrameBinding(BigInteger.ONE,ActionWriterIntegrationFixture.INITIAL_DATE_RAW,73,303);
        row.set("unconditional_release_preview",ReleasePreviewCodec12003.toNode(new ReleasePreview12003.Available(frame,BigInteger.valueOf(12),new Definition(123,1),true,
                new Costs(java.util.Arrays.stream(Resource.values()).map(resource->new CostEntry(resource,0)).toList()))));
        row.set("ransom_quote_preview",org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.quoteJson(new org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.AvailableQuote(
                frame,BigInteger.valueOf(12),404,org.xar.ck3.control.g2.m6.prisonerransom.PrisonerVanillaResearch.Option.GOLD,30_000_000,0,0)));
        return new RawJson(StrictJson.canonical(payload));
    }
}

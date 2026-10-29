package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsService;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.service.mcp.*;
import static org.junit.jupiter.api.Assertions.*;

/** Software boundary regressions using the actual registered decoder/normalizer/encoder; no constructed private Root. */
final class RootArtifactsPublicProductsTest {
    @TempDir Path temporary;
    private static final String SHA="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final ExactRef SOURCE=new ExactRef("software:artifact-source",1,"a".repeat(64));
    @Test void actualOriginalSdkDescriptorsContainEveryExactArtifactNameAndOnlyReadProductsAreClaimed()throws Exception {
        Set<String> original=RootOriginalPublicTestInputs.tools().stream().map(PublicMcpDirectory.ToolDescriptor::name).collect(Collectors.toSet());
        Set<String> all=java.util.Arrays.stream(Method.values()).map(Method::originalName).collect(Collectors.toSet());
        assertEquals(18,all.size());assertTrue(original.containsAll(all));
        var bindings=RootArtifactsPublicProducts.readBindings(SOURCE,request->{throw new AssertionError("descriptor inspection performs no native operation");});
        assertEquals(10,bindings.size());
        assertEquals(java.util.Arrays.stream(Method.values()).filter(Method::readOnly).map(Method::originalName).collect(Collectors.toSet()),
                bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(Collectors.toSet()));
        assertTrue(bindings.stream().allMatch(b->b.kind()==PublicMcpBindings.Kind.DRIVER_DIRECT&&b.target().implementationSource().equals(SOURCE)));
        assertTrue(bindings.stream().noneMatch(b->b.name().equals(Method.OPEN.originalName())||b.name().equals(Method.PERSONAL_SUBMIT.originalName())));
        assertEquals(18,RootArtifactsPublicProducts.missingAll("actual source join absent").size());
    }
    @Test void namedSdkRouteDecodesActualUint64AndRunsTheUniqueOriginalKnightNormalizerThenMcpEncoder()throws Exception {
        AtomicInteger calls=new AtomicInteger();
        var bindings=RootArtifactsPublicProducts.readBindings(SOURCE,request->{
            calls.incrementAndGet();assertInstanceOf(CharacterRead.class,request);
            assertEquals(new BigInteger("18446744073709551615"),request.expectedRevision());
            NativeFrame actual=frame(request.expectedRevision());
            return ArtifactsCodec.normalize(request,actual,new NativeEnvelope("original-knight-read",knightPacket(),actual));
        });
        var binding=bindings.stream().filter(b->b.name().equals(Method.KNIGHT.originalName())).findFirst().orElseThrow();
        var response=invoke(binding,raw("{\"expected_revision\":\"18446744073709551615\",\"character_id\":42}"));
        var output=StrictJson.parse(response.bytes()).get("structuredContent");
        assertNotNull(output);assertFalse(output.get("available").booleanValue());
        assertTrue(output.get("knight_effectiveness_raw").isNull());
        assertTrue(output.get("actual_knight_effectiveness_breakdown").isNull());
        assertEquals("unavailable",output.get("callback_provenance").textValue());assertEquals(1,calls.get());
        assertFalse(output.path("business_outcome_observed").asBoolean(false));
    }
    @Test void missingNullWrongTypesUnsafeNumericU64AndUnknownFieldsNeverReachTheActualRuntime()throws Exception {
        AtomicInteger calls=new AtomicInteger();
        var bindings=RootArtifactsPublicProducts.readBindings(SOURCE,request->{calls.incrementAndGet();throw new AssertionError("malformed request reached runtime");});
        for(var binding:bindings) {
            assertThrows(IllegalArgumentException.class,()->binding.decoder().decode(call(binding.name(),PublicMcpDirectory.Presence.MISSING,Optional.empty())));
            assertThrows(IllegalArgumentException.class,()->binding.decoder().decode(call(binding.name(),PublicMcpDirectory.Presence.NULL,Optional.of(raw("null")))));
            for(String input:new String[]{"{}","[]","{\"expected_revision\":true}","{\"expected_revision\":7.0}",
                    "{\"expected_revision\":9007199254740992}","{\"expected_revision\":\"18446744073709551616\"}",
                    "{\"expected_revision\":7,\"unknown\":0}"})
                assertThrows(IllegalArgumentException.class,()->invoke(binding,raw(input)));
        }
        assertEquals(0,calls.get());
    }
    @Test void originalTargetFrameAndUnavailableShapeAreNotReplacedByAStandardEffectivenessFallback() {
        var request=new CharacterRead(BigInteger.valueOf(7),42);var frame=frame(BigInteger.valueOf(7));
        var valid=ArtifactsCodec.normalize(request,frame,new NativeEnvelope("original-knight-read",knightPacket(),frame));
        assertFalse(valid.facts().available());assertFalse(valid.facts().independentDesiredObserved());
        assertTrue(valid.facts().actualIntentSequence().isEmpty());
        ObjectNode foreign=knightPacket();((ObjectNode)foreign.get("result").get("character_knight_effectiveness_v1")).put("character_id",43);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,frame,new NativeEnvelope("original-knight-read",foreign,frame)));
        ObjectNode invented=knightPacket();((ObjectNode)invented.get("result").get("character_knight_effectiveness_v1")).put("knight_effectiveness_raw",100000);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,frame,new NativeEnvelope("original-knight-read",invented,frame)));
        var exposed=valid.payload().original();exposed.put("unavailable_reason","changed-copy");
        assertNotEquals("changed-copy",valid.payload().original().get("unavailable_reason").textValue());
    }
    @Test void dataFrameCannotRelabelAnotherGameBirthAsTheSameOriginalOwner() {
        var before=frame(BigInteger.valueOf(7));
        var another=new NativeFrame(before.publicRevision(),before.nativeRevision(),before.dateRaw(),before.actorCharacterId(),before.gamePid(),
                before.gameCreationFiletime().subtract(BigInteger.ONE),before.connectionGeneration(),before.episodeRunId(),SHA,true,true,true);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(new CharacterRead(BigInteger.valueOf(7),42),before,
                new NativeEnvelope("original-knight-read",knightPacket(),another)));
    }
    @Test void allEighteenOriginalTypedRequestsRoundTripWithoutAliasesOrLossOfMissingAndNull() {
        var r=BigInteger.valueOf(7);var missing=new PublicUnsigned64.Missing();var nil=new PublicUnsigned64.NullValue();
        List<Request> requests=List.of(new RevisionRequest(Method.CLOSE,r),new Enshrine(r,7,8,0,true,"b".repeat(64),missing),
                new RevisionRequest(Method.OPEN,r),new CharacterRead(r,42),new SkillRead(r,42,Skill.MARTIAL),
                new PersonalPost(r,8,BigInteger.valueOf(17)),new ArtifactRead(r,8),new RelicPair(Method.RELIC_ACTION_CONTEXT,r,7,8),
                new RelicSite(r,7),new RelicPermissions(r,7,missing),new InventoryPost(Method.CLOSE_POST,r,BigInteger.valueOf(17)),
                new RevisionRequest(Method.CLOSE_QUERY,r),new InventoryPost(Method.OPEN_POST,r,BigInteger.valueOf(17)),
                new Remove(r,7,8,true,"b".repeat(64)),new RelicPair(Method.SELECT_RELIC,r,7,8),new CreationSelection(BigInteger.ZERO,8,true),
                new RelicSlot(r,7,0,true),new PersonalSubmit(r,8,true,0,missing,true));
        assertEquals(Set.of(Method.values()),requests.stream().map(Request::method).collect(Collectors.toSet()));
        for(Request request:requests)assertEquals(request,ArtifactsCodec.decode(request.method().originalName(),ArtifactsCodec.encode(request)));
        var absent=new RelicPermissions(r,7,missing);var explicitNull=new RelicPermissions(r,7,nil);
        assertFalse(ArtifactsCodec.encode(absent).has("artifact_id"));assertTrue(ArtifactsCodec.encode(explicitNull).get("artifact_id").isNull());
        assertEquals(explicitNull,ArtifactsCodec.decode(explicitNull.method().originalName(),ArtifactsCodec.encode(explicitNull)));
        assertNotEquals(absent,explicitNull);
        var fields=ArtifactsCodec.nativeFields(requests.get(17),frame(r),Optional.empty());
        assertTrue(fields.get("policy_positive").booleanValue());assertTrue(fields.get("expected_replacing_empty").booleanValue());
        assertFalse(fields.has("expected_replacing_artifact_id"));assertFalse(fields.has("expected_snapshot_revision"));
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.nativeFields(new PersonalSubmit(r,8,true,0,missing,false),frame(r),Optional.empty()));
        var creation=ArtifactsCodec.nativeFields(new CreationSelection(r,8,true),frame(r),Optional.empty());
        assertTrue(creation.get("selected").booleanValue());assertFalse(creation.has("holy_site_creation_selected"));
        var relic=ArtifactsCodec.nativeFields(new RelicPair(Method.SELECT_RELIC,r,7,8),frame(r),Optional.empty());
        assertTrue(relic.has("expected_date_raw"));assertTrue(relic.has("expected_player_character_id"));
        assertFalse(relic.has("expected_game_pid"));
    }
    @Test void sameFiniteNativeGrammarRejectsUnexpectedFieldsBoolAndUnsafeFullIdBeforePermissionUse() {
        var fields=ArtifactsCodec.nativeFields(new CharacterRead(BigInteger.valueOf(7),42),frame(BigInteger.valueOf(7)),Optional.empty());
        ArtifactsService.validatePrivateFields(Method.KNIGHT,fields);
        fields.put("character_id",true);assertThrows(IllegalArgumentException.class,()->ArtifactsService.validatePrivateFields(Method.KNIGHT,fields));
        fields.put("character_id",4294967295L);assertThrows(IllegalArgumentException.class,()->ArtifactsService.validatePrivateFields(Method.KNIGHT,fields));
        fields.put("character_id",42).put("unreviewed",true);assertThrows(IllegalArgumentException.class,()->ArtifactsService.validatePrivateFields(Method.KNIGHT,fields));
    }
    @Test void positiveOriginalKnightEnvelopePreservesExactValuesAndRejectsRoleAndTypeChanges() {
        var request=new CharacterRead(BigInteger.valueOf(7),42);var current=frame(request.expectedRevision());var packet=knightPacket();
        var env=(ObjectNode)packet.get("result");env.put("status","available");var body=(ObjectNode)env.get(request.method().resultKey());
        body.put("available",true).putNull("unavailable_reason");body.put("two_pass_stable",true).put("own_actor_context_verified",true)
                .put("callback_provenance","exact4_native").put("rite_id",1).put("faith_id",2).put("knight_effectiveness_raw",123456)
                .put("actual_knight_effectiveness_breakdown","actual authored original-format callback text");
        var reply=ArtifactsCodec.normalize(request,current,new NativeEnvelope("original-knight-read",packet,current));
        assertTrue(reply.facts().available());assertEquals(123456,ArtifactsCodec.encode(reply).get("knight_effectiveness_raw").longValue());
        env.put("read_only",false);assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,current,new NativeEnvelope("original-knight-read",packet,current)));
        env.put("read_only",true);body.put("knight_effectiveness_raw",123456.0);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,current,new NativeEnvelope("original-knight-read",packet,current)));
    }
    @Test void originalInventoryOuterObservedAndBodyStatusSurviveWithIndependentPostCause() {
        var current=frame(BigInteger.valueOf(7));var request=new InventoryPost(Method.CLOSE_POST,current.publicRevision(),BigInteger.valueOf(17));
        var packet=inventoryPacket();var reply=ArtifactsCodec.normalize(request,current,new NativeEnvelope("inventory-close-post",packet,current));
        assertTrue(reply.facts().onceIntentConsumed());assertTrue(reply.facts().independentDesiredObserved());
        assertFalse(reply.facts().needsRecovery());assertEquals("inventory_window_closed_observed",ArtifactsCodec.encode(reply).get("status").textValue());
        var body=(ObjectNode)packet.get("result").get("player_inventory_window_close");
        ((ObjectNode)body.get("after")).put("capture_epoch",10);((ObjectNode)body.get("current")).put("capture_epoch",10);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,current,new NativeEnvelope("inventory-close-post",packet,current)));
        body.put("desired_window_observed",true).put("read_only",false);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,current,new NativeEnvelope("inventory-close-post",packet,current)));
    }
    @Test void frozenOriginalRelicPacketRunsRecognitionAndRarityInsteadOfOnlyUnavailableBranches()throws Exception {
        String repository=System.getProperty("xar.repository.root");
        assertNotNull(repository,"NOT_RUN_REQUIRED: actual Root-bound repository path must be supplied");
        Path repositoryRoot=Path.of(repository);assertTrue(repositoryRoot.isAbsolute(),"actual repository root must be absolute");
        Path location=repositoryRoot.resolve("ck3_autonomous_player/tests/fixtures/holy_site_relic_rarity/context-integration.json");
        byte[] raw=Files.readAllBytes(location);assertEquals(6706,raw.length);
        assertEquals("1a863e1a1baaa538cec35162d01c100e3c6034f5879bae9a11689f5401c4c9d1",
                java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        var packet=(ObjectNode)StrictJson.parse(raw);var result=(ObjectNode)packet.get("result");
        var original=(ObjectNode)result.get("player_holy_site_relic_context");
        var current=new NativeFrame(BigInteger.valueOf(7),BigInteger.valueOf(9),BigInteger.valueOf(42),13,123,
                BigInteger.valueOf(55),BigInteger.valueOf(2),"frozen-owned-fixture-not-live",SHA,true,true,true);
        var request=new RelicSite(current.publicRevision(),7);
        var reply=ArtifactsCodec.normalize(request,current,new NativeEnvelope(packet.get("request_id").textValue(),packet,current));
        var output=ArtifactsCodec.encode(reply);assertTrue(reply.facts().available());
        assertEquals(original.get("recognition_matrix"),output.get("recognition_matrix"));
        assertEquals(original.get("cached_world_state"),output.get("cached_world_state"));
        assertEquals(original.get("evaluation_context"),output.get("evaluation_context"));
        assertEquals(0,output.get("rarity_decomposition").get("projected_sum").intValue());
        assertEquals("inventory_count_zero",output.get("rarity_decomposition").get("slots").get(0).get("reason").textValue());
        original.put("requested_holy_site_id",8);
        assertThrows(IllegalArgumentException.class,()->ArtifactsCodec.normalize(request,current,new NativeEnvelope(packet.get("request_id").textValue(),packet,current)));
    }
    @Test void actualFiniteDeclarationAddsOnlyItsFiveOriginalNavNamesAndCannotDeclareTheOtherThreeActions() {
        var mutable=new java.util.HashSet<>(Set.of(Method.SELECT_RELIC,Method.RELIC_SLOT,Method.ENSHRINE,Method.REMOVE,Method.CREATION_SELECTION));
        Set<Method> frozen=RootArtifactsPublicProducts.requireFiniteActions(mutable);mutable.clear();assertEquals(5,frozen.size());
        var bindings=RootArtifactsPublicProducts.actionBindings(SOURCE,frozen,request->{throw new AssertionError("descriptor inspection does not invoke Root");});
        assertEquals(frozen.stream().map(Method::originalName).collect(Collectors.toSet()),bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(Collectors.toSet()));
        assertTrue(bindings.stream().allMatch(b->b.kind()==PublicMcpBindings.Kind.DRIVER_DIRECT));
        assertEquals(Set.of(Method.PERSONAL_SUBMIT),RootArtifactsPublicProducts.requireFiniteActions(Set.of(Method.PERSONAL_SUBMIT)));
        assertEquals(Set.of(Method.OPEN,Method.CLOSE),RootArtifactsPublicProducts.requireFiniteActions(Set.of(Method.OPEN,Method.CLOSE)));
        assertThrows(IllegalArgumentException.class,()->RootArtifactsPublicProducts.requireFiniteActions(Set.of(Method.KNIGHT)));
        assertTrue(RootArtifactsPublicProducts.actionBindings(SOURCE,Set.of(),request->{throw new AssertionError();}).isEmpty());
    }
    @Test void namedFiniteSelectorConsumesUniqueNativeNormalizerAndMcpSerdeWithoutGrantingGameplaySuccess()throws Exception {
        AtomicInteger calls=new AtomicInteger();
        var bindings=RootArtifactsPublicProducts.actionBindings(SOURCE,Set.of(Method.SELECT_RELIC),request->{
            calls.incrementAndGet();assertInstanceOf(RelicPair.class,request);var current=frame(request.expectedRevision());
            return ArtifactsCodec.normalize(request,current,new NativeEnvelope("authored-finite-selector",selectorPacket(),current));
        });
        var binding=bindings.getFirst();
        var encoded=invoke(binding,raw("{\"expected_revision\":\"7\",\"holy_site_id\":7,\"artifact_id\":8}"));
        var output=StrictJson.parse(encoded.bytes()).get("structuredContent");var action=output.get("holy_site_relic_action");
        assertEquals("already_in_requested_state_verification_pending",action.get("status").textValue());
        assertTrue(action.get("selection_postcondition_observed").booleanValue());assertFalse(action.get("native_dispatch_attempted").booleanValue());
        assertFalse(action.get("business_outcome_observed").booleanValue());assertFalse(action.get("gameplay_command_may_have_been_queued").booleanValue());
        assertEquals(1,calls.get());
        for(String invalid:List.of("{\"expected_revision\":7,\"holy_site_id\":7,\"artifact_id\":true}",
                "{\"expected_revision\":7,\"holy_site_id\":7,\"artifact_id\":8.0}",
                "{\"expected_revision\":7,\"holy_site_id\":7,\"artifact_id\":4294967295}",
                "{\"expected_revision\":7,\"holy_site_id\":7,\"artifact_id\":8,\"private_permission\":true}"))
            assertThrows(IllegalArgumentException.class,()->invoke(binding,raw(invalid)));
        assertEquals(1,calls.get());
    }
    @Test void finiteSelectorNativeBodyCannotInventBusinessSuccessAtTheRegisteredPublicBoundary() {
        var packet=selectorPacket();((ObjectNode)packet.get("result").get("holy_site_relic_action")).put("business_outcome_observed",true);
        var bindings=RootArtifactsPublicProducts.actionBindings(SOURCE,Set.of(Method.SELECT_RELIC),request->{
            var current=frame(request.expectedRevision());return ArtifactsCodec.normalize(request,current,
                    new NativeEnvelope("authored-finite-selector",packet,current));
        });
        assertThrows(IllegalArgumentException.class,()->invoke(bindings.getFirst(),raw("{\"expected_revision\":7,\"holy_site_id\":7,\"artifact_id\":8}")));
    }
    @Test void actualCanonicalUnknownAndOriginalAckProjectRealPublicReferencesWithoutClearingReplay()throws Exception {
        var nativeBody=new AtomicReference<ObjectNode>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("navigate-ingame-ui-v1"),
                "game.command.navigate-ingame-ui-v1",(command,attempt,dispatch)->new ActionPorts.Pending(
                "controlled independent selection read not yet available",List.of(attempt.guard().nativeEvidence())),()->{},
                ()->new RawJson(StrictJson.canonical(nativeBody.get())));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("artifact-public-original"),false,scenario)) {
            var command=fixture.command("artifact-public-original");var point=command.before().frame().identity();
            var body=(ObjectNode)selectorPacket().get("result");body.put("native_revision",point.nativeRevision())
                    .put("date_raw",point.dateRaw()).put("played_character_id",point.player());nativeBody.set(body);
            var receipt=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,receipt.state());
            fixture.writer.locked(same->fixture.archive.inSession(same,archive->{try {
                var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();var ack=receipt.ack().orElseThrow();
                var original=RootGuardEvidence.loadFrame(attempt.guard(),archive,fixture.frameLoader());
                var actual=ArtifactsService.actualFrame(original);var query=new RelicPair(Method.SELECT_RELIC,actual.publicRevision(),7,8);
                var normalized=ArtifactsCodec.normalize(query,actual,new NativeEnvelope(ack.requestId(),StrictJson.parse(ack.originalFrame().bytes()),actual));
                var receiptRef=archive.receiptReferenceOf(receipt);var ackRef=archive.referenceOf(ack);
                var parsed=NativeUiParsedReturn.encode(ack.outbound().orElseThrow().originalPacket(),ack.originalPacket(),original.semantic());
                var parsedRef=fixture.archive.preserveArtifact(same,parsed.bytes(),NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);
                byte[] preserved=fixture.archive.readArtifact(same,parsedRef,NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES);assertArrayEquals(parsed.bytes(),preserved);
                var parsedBody=OpportunityJson.toNode(NativeUiParsedReturn.decode(preserved));
                assertEquals(NativeUiParsedReturn.SCHEMA,parsedBody.get("schema").textValue());
                assertEquals("unvalidated",parsedBody.get("validation_state").textValue());assertFalse(parsedBody.get("wire_bytes_preserved").booleanValue());
                assertEquals(OpportunityJson.toNode(original.semantic()),parsedBody.get("actual_pre_submission_snapshot"));
                assertEquals(ack.requestId(),parsedBody.get("request").get("request_id").textValue());
                assertEquals(StrictJson.parse(ack.originalFrame().bytes()),parsedBody.get("original_parsed_command_result"));
                assertThrows(IllegalArgumentException.class,()->new ArtifactsService.ActionPublication(original,receipt,receiptRef,ackRef,ackRef));
                var projected=ArtifactsService.publishAction(normalized,new ArtifactsService.ActionPublication(original,receipt,receiptRef,ackRef,parsedRef));
                var output=ArtifactsCodec.encode(projected);
                assertEquals(original.identity().frame().snapshotId(),output.get("queried_snapshot_id").textValue());
                assertEquals(original.identity().frame().revision().toString(),output.get("queried_revision").textValue());
                assertEquals(original.connectionGeneration().toString(),output.get("queried_connection_generation").textValue());
                assertEquals(receiptRef.path(),output.get("consumed_intent_receipt").textValue());
                assertTrue(output.get("native_ui_raw_return_receipt").isObject());
                assertEquals(NativeUiParsedReturn.reference(parsedRef),output.get("native_ui_raw_return_receipt"));
                assertEquals("unvalidated",output.get("native_ui_raw_return_receipt").get("validation_state").textValue());
                assertNotEquals(output.get("native_ui_raw_return_receipt").get("path").textValue(),ackRef.path());
                assertEquals(receiptRef.toJson(),output.get("java_canonical_action_receipt"));
                assertEquals(ackRef.toJson(),output.get("java_original_native_ack"));
                assertTrue(output.get("identical_intent_replay_blocked").booleanValue());
                assertFalse(output.get("automatic_retry").booleanValue());assertFalse(output.get("business_outcome_observed").booleanValue());
                var serialized=PublicMcpDirectory.CallResult.fromBusinessJson(new RawJson(StrictJson.canonical(output)));
                assertEquals(output,StrictJson.parse(serialized.bytes()).get("structuredContent"));
                assertFalse(receipt.settled());return null;
            }catch(java.io.IOException failure){throw new java.io.UncheckedIOException(failure);}}));
            assertEquals(1,fixture.nativeActionWrites());
        }
    }
    @Test void threePrivateOriginalNamesUseTheActualTypedPublicDecoderBeforeAnyProducerInvocation() {
        var privateMethods=Set.of(Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT);AtomicInteger calls=new AtomicInteger();
        var bindings=RootArtifactsPublicProducts.actionBindings(SOURCE,privateMethods,request->{
            calls.incrementAndGet();throw new AssertionError("invalid public DTO must not invoke private Root/native products");
        });
        assertEquals(privateMethods.stream().map(Method::originalName).collect(Collectors.toSet()),
                bindings.stream().map(McpExecutableDirectory.DirectBinding::name).collect(Collectors.toSet()));
        for(var binding:bindings)assertThrows(IllegalArgumentException.class,()->invoke(binding,raw("{\"expected_revision\":true}")));
        assertEquals(0,calls.get());
        assertThrows(IllegalArgumentException.class,()->RootArtifactsPublicProducts.requireFiniteActions(Set.of(Method.OPEN_POST)));
        assertThrows(IllegalArgumentException.class,()->RootArtifactsPublicProducts.requireFiniteActions(Set.of(Method.PERSONAL_POST)));
    }
    /** Authored original-format selector DTO only; the numbers and flags grant no native or private Root qualification. */
    private static ObjectNode selectorPacket() {
        ObjectNode selection=StrictJson.object().put("available",true).put("artifact_id",8).putNull("slot_index").put("unavailable_reason","");
        selection.putArray("slot_artifact_ids").add(8);
        ObjectNode action=StrictJson.object().put("available",true).put("status","already_in_requested_state_verification_pending")
                .put("loaded_source_pins_verified",true).put("native_dispatch_attempted",false).put("dispatch_invoked",false)
                .put("verification_pending",true).put("already_in_requested_state",true).put("selection_postcondition_observed",true)
                .put("original_button_enabled_observed",false).putNull("original_button_enabled");
        action.put("actual_button_presentation_observed",false).put("button_child_path","").put("frozen_preview_verified",false)
                .put("gameplay_command_may_have_been_queued",false).put("business_outcome_observed",false).put("action_ready",false).put("unavailable_reason","");
        action.set("before",selection);action.set("after",selection.deepCopy());
        ObjectNode result=StrictJson.object().put("schema","ck3-ingame-ui-window-v1").put("step","navigate-ingame-ui-v1")
                .put("game_version","1.20.0.4").put("executable_sha256",SHA).put("backend_id","native-headless")
                .put("native_backend_id","ck3-1.20.0.4-native-ingame-ui-v1").put("native_revision",20).put("date_raw",24)
                .put("played_character_id",99).put("paused",true).put("window_kind","holy_site").put("window_name","holy_site_window")
                .put("requested_subject_id",7).put("current_subject_id",7).put("accepted",true).put("available",true)
                .put("status","already_in_requested_state_verification_pending").put("native_dispatch_attempted",false)
                .put("dispatch_invoked",false).put("verification_pending",true).put("unavailable_reason","")
                .put("window_exists",true).put("effective_visible",true).put("enabled",true).put("subject_id_available",true)
                .put("application_owner_thread_verified",true).put("gui_owner_binding_verified",true).put("thread_id",1)
                .put("pump_epoch",1).put("gui_context_address",1).put("gui_owner_address",1).put("rng_owner_is_ui_admission_gate",false);
        result.set("holy_site_relic_action",action);result.set("modal_admission",StrictJson.object().put("attempted",true)
                .put("header_read",true).put("receivers_verified",true).put("effective_visible_count",0));
        ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1)
                .put("request_id","authored-finite-selector").put("ok",true);packet.set("result",result);return packet;
    }
    /** Authored translation of tests/test_player_inventory_window_close_private_transport.py:view/body, not live evidence. */
    private static ObjectNode inventoryPacket() {
        ObjectNode before=inventoryView(10,false),after=inventoryView(12,true);
        ObjectNode body=StrictJson.object().put("schema","ck3_12004_player_inventory_window_close_v1").put("game_version","1.20.0.4")
                .put("executable_sha256",SHA).put("operation","post").put("read_only",true).put("available",true).putNull("unavailable_reason");
        body.put("loaded_code_pins_verified",true).put("loaded_gui_sources_verified",true).put("intent_sequence",17)
                .put("intent_found",true).put("once_intent_consumed",true).put("invoked",true).put("call_returned",true)
                .put("needs_recovery",false).put("desired_window_observed",true).put("status","inventory_window_closed_observed");
        body.set("current",after.deepCopy());body.set("before",before);body.set("after",after);
        for(String key:List.of("artifact_equipped_observed","actor_aggregate_observed","personal_net_effect_attributed","business_outcome_observed","automatic_retry"))body.put(key,false);
        ObjectNode env=StrictJson.object().put("step",Method.CLOSE_POST.step()).put("accepted",true).put("private_build",true)
                .put("read_only",true).put("advertised",false).put("game_version","1.20.0.4").put("executable_sha256",SHA)
                .put("backend_id","ck3-1.20.0.4-native-player-inventory-window-close-v1-private").put("domain_key",Method.CLOSE_POST.domain())
                .put("snapshot_revision",20).put("date_raw",24).put("game_pid",123).put("connection_generation",2).put("status","observed");
        env.set("player_inventory_window_close",body);ObjectNode packet=StrictJson.object().put("type","command_result")
                .put("protocol_version",1).put("request_id","inventory-close-post").put("ok",true);packet.set("result",env);return packet;
    }
    private static ObjectNode inventoryView(int epoch,boolean hidden) {
        return StrictJson.object().put("available",true).put("native_revision",20).put("capture_epoch",epoch).put("date_raw",24)
                .put("game_pid",123).put("connection_generation",2).put("played_character_id",99).put("selected_character_id",99)
                .put("window_present",true).put("root_present",true).put("native_visible",!hidden).put("effective_visible",!hidden).put("current_player_selected",true);
    }
    private static NativeFrame frame(BigInteger revision) {
        return new NativeFrame(revision,BigInteger.valueOf(20),BigInteger.valueOf(24),99,123,
                new BigInteger("18446744073709551615"),BigInteger.valueOf(2),"actual-software-episode",SHA,true,true,true);
    }
    private static ObjectNode knightPacket() {
        ObjectNode body=StrictJson.object().put("schema","ck3_12004_character_knight_effectiveness_v1")
                .put("available",false).put("unavailable_reason","actual actor context unavailable")
                .put("read_only",true).put("snapshot_revision",20).put("date_raw",24)
                .put("played_character_id",99).put("character_id",42).put("raw_scale",100000)
                .put("two_pass_stable",false).put("own_actor_context_verified",false).put("callback_provenance","unavailable")
                .put("modifier_cache_refreshed",false).put("cache_generation_time_known",false)
                .put("site_attribution_observed",false).put("gameplay_command_submitted",false)
                .put("raw_pointer_fields_persisted",false).put("script_cache_rng_effects","unknown")
                .put("game_version","1.20.0.4").put("executable_sha256",SHA);
        for(String name:java.util.List.of("rite_id","faith_id","knight_effectiveness_raw",
                "actual_knight_effectiveness_breakdown","selected_site_contribution_raw"))body.putNull(name);
        ObjectNode result=StrictJson.object().put("step","query-character-knight-effectiveness-v1-private")
                .put("accepted",true).put("private_build",true).put("read_only",true).put("advertised",false)
                .put("backend_id","native-headless").put("domain_key","character_knight_effectiveness_v1")
                .put("game_pid",123).put("connection_generation",2).put("snapshot_revision",20).put("date_raw",24)
                .put("game_version","1.20.0.4").put("executable_sha256",SHA).put("status","unavailable");
        result.set("character_knight_effectiveness_v1",body);
        ObjectNode packet=StrictJson.object().put("type","command_result").put("protocol_version",1)
                .put("request_id","original-knight-read").put("ok",true);packet.set("result",result);return packet;
    }
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static PublicMcpDirectory.ToolCall call(String name,PublicMcpDirectory.Presence presence,Optional<RawJson> args) {
        return new PublicMcpDirectory.ToolCall(name,new PublicMcpDirectory.Arguments(presence,args),Optional.empty(),new McpCancellation());
    }
    private static <Q,R>PublicMcpDirectory.CallResult invoke(McpExecutableDirectory.DirectBinding<Q,R> binding,RawJson input)throws Exception {
        return binding.encoder().encode(binding.actual().invoke(binding.decoder().decode(call(binding.name(),PublicMcpDirectory.Presence.VALUE,Optional.of(input)))));
    }
}

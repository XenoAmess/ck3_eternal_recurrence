package org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts.ArtifactsContract.*;

/** Original finite artifact operations. All I/O is issued by the installed Root contracts/coordinator. */
public final class ArtifactsService {
    @FunctionalInterface public interface FrameSource { NativeFrame require(Complete actual) throws IOException; }
    @FunctionalInterface public interface InventorySource { String require(Complete actual) throws IOException; }
    public record Sources(ExactRef definition,ExactRef decoder,Map<Method,ExactRef> nativeProducers,
            List<ExactRef> completeProducerClosure,Set<Method> enabled,FrameSource frames,
            InventorySource inventory,NativePrivateActionPermission.QualificationVerifier actualQualification) {
        /** Ordinary execution metadata does not replace the actual native frame and qualification ports. */
        public static Sources ordinary(ExactRef definition,ExactRef decoder,Map<Method,ExactRef> nativeProducers,
                List<ExactRef> completeProducerClosure,Set<Method> enabled,FrameSource frames,
                InventorySource inventory,NativePrivateActionPermission.QualificationVerifier actualQualification) {
            return new Sources(definition,decoder,nativeProducers,completeProducerClosure,enabled,frames,inventory,actualQualification);
        }
        public Sources {
            Objects.requireNonNull(definition);Objects.requireNonNull(decoder);
            nativeProducers=Map.copyOf(nativeProducers);completeProducerClosure=List.copyOf(completeProducerClosure);
            enabled=Set.copyOf(enabled);Objects.requireNonNull(frames);Objects.requireNonNull(inventory);Objects.requireNonNull(actualQualification);
            need(definition.bytes()>0&&decoder.bytes()>0&&!completeProducerClosure.isEmpty()
                    &&completeProducerClosure.size()<=64,"actual complete artifact producer/decoder closure required");
            for(Method method:enabled)need(nativeProducers.containsKey(method)&&nativeProducers.get(method).bytes()>0,
                    "enabled artifact operation has no actual original native producer: "+method.originalName());
        }
        public List<ExactRef> allSources(){
            var result=new java.util.LinkedHashSet<ExactRef>(completeProducerClosure);
            result.add(definition);result.add(decoder);result.addAll(nativeProducers.values());return List.copyOf(result);
        }
    }
    public record Selection(Complete captured,NativeFrame frame,Request query,Optional<String> sourceInventory,Instant deadline) {
        public Selection {
            Objects.requireNonNull(captured);Objects.requireNonNull(frame);Objects.requireNonNull(query);
            Objects.requireNonNull(sourceInventory);Objects.requireNonNull(deadline);
            need(frame.publicRevision().equals(query.expectedRevision()),"artifact public revision differs from actual captured frame");
            sourceInventory.ifPresent(value->need(value.matches("[0-9a-f]{64}"),"actual managed inventory SHA required"));
        }
    }
    private final NativeGameTransport transport;
    private final Sources sources;
    private final EnumMap<Method,RootReadContractCatalog.Family<Selection,Reply>> families=new EnumMap<>(Method.class);
    public ArtifactsService(NativeGameTransport transport,Sources sources) {
        this.transport=Objects.requireNonNull(transport);this.sources=Objects.requireNonNull(sources);
        for(Method method:sources.enabled())if(method.readOnly())families.put(method,family(method));
    }
    public Sources sources(){return sources;}
    public boolean enabled(Method method){return sources.enabled().contains(method);}
    public List<RootReadContractCatalog.Family<?,?>> readFamilies(){
        var result=new ArrayList<RootReadContractCatalog.Family<?,?>>();
        result.addAll(families.values());if(internalInventorySource().isPresent())result.add(internalInventoryFamily());return List.copyOf(result);
    }
    public Selection select(Complete actual,Request request,Instant deadline)throws IOException {
        requireEnabled(request.method());NativeFrame frame=sources.frames().require(actual);
        need(frame.equals(actualFrame(actual)),"artifact frame source differs from the complete physical/semantic current frame");
        need(frame.publicRevision().equals(actual.identity().frame().revision())
                &&frame.nativeRevision().equals(actual.identity().frame().identity().nativeRevision())
                &&frame.dateRaw().equals(actual.identity().frame().identity().dateRaw())
                &&BigIntegerValue(frame.actorCharacterId()).equals(actual.identity().frame().identity().player())
                &&frame.gamePid()==actual.identity().game().pid()
                &&frame.gameCreationFiletime().equals(actual.identity().game().creationFiletime().value()),
                "artifact data frame differs from complete actual physical Root identity");
        need(frame.paused()&&frame.mapReady()&&frame.alive()
                &&frame.executableSha256().equals(EXECUTABLE_SHA256),"artifact operation requires actual current living paused exact .4 frame");
        Optional<String> inventory=inventory(request.method())?Optional.of(sources.inventory().require(actual)):Optional.empty();
        return new Selection(actual,frame,request,inventory,deadline);
    }
    public ReadContract<Reply> issue(RootReadContractCatalog catalog,Selection selection) {
        need(selection.query().method().readOnly(),"actions are not read contracts");
        return catalog.issue(Objects.requireNonNull(families.get(selection.query().method()),"enabled original artifact family absent"),selection);
    }
    public PlanningReadRequest request(Selection selection) {
        Complete actual=selection.captured();
        return new PlanningReadRequest(actual.identity(),actual.source(),actual.sessionId(),
                operation(selection.query().method()),obj(key(selection)),selection.deadline());
    }
    public NativeRequest prepare(Selection selection,String actualProtocolRequestId) {
        StrictJson.text(actualProtocolRequestId);requireEnabled(selection.query().method());
        try {
            requireHeld(selection);
            ObjectNode fields=ArtifactsCodec.nativeFields(selection.query(),selection.frame(),selection.sourceInventory());
            if(!selection.query().method().readOnly()&&!navigation(selection.query().method()))
                fields.put("expected_snapshot_revision",selection.frame().nativeRevision());
            return new NativeRequest(selection.query().method().step(),navigation(selection.query().method())
                    ?Optional.of("game.command.navigate-ingame-ui-v1"):Optional.empty(),
                    raw(fields));
        }catch(IOException unavailable){throw new UncheckedIOException("artifact original producer/frame admission unavailable",unavailable);}
    }
    public Reply decodeRead(Selection selection,PlanningReadReceipt receipt) {
        need(selection.query().method().readOnly(),"cannot decode an artifact action as a read");
        requireRead(selection,receipt);
        requireWire(selection,receipt.original(),receipt.requestId());
        Reply normalized=ArtifactsCodec.normalize(selection.query(),selection.frame(),
                new NativeEnvelope(receipt.requestId(),StrictJson.parse(receipt.original().originalFrame().bytes()),selection.frame()));
        return publicRead(normalized,selection,receipt);
    }
    /** Called only with the actual canonical attempt guard and independently captured current after-frame. */
    public Reply decodeAction(Selection selection,ActionState.Attempt actualAttempt,NativeActionPort.AckReceived actualAck,
            NativeFrame independentlyObservedAfter)throws IOException {
        need(!selection.query().method().readOnly(),"query cannot consume an action ACK");
        need(actualAttempt.requestId().equals(actualAck.requestId()),"artifact actual attempt/request correlation differs");
        actualAck.custody().orElseThrow(()->new IllegalArgumentException("original artifact native custody absent"))
                .verify(actualAck,actualAttempt.guard());
        need(actualAttempt.guard().observed().equals(selection.captured().identity())
                &&actualAttempt.guard().source().equals(selection.captured().source())
                &&actualAttempt.guard().sessionId().equals(selection.captured().sessionId()),
                "artifact attempt belongs to another original Root/frame/source/session");
        requireWire(selection,actualAck,actualAttempt.requestId());
        return ArtifactsCodec.normalize(selection.query(),selection.frame(),
                new NativeEnvelope(actualAttempt.requestId(),StrictJson.parse(actualAck.originalFrame().bytes()),independentlyObservedAfter));
    }
    /** Actual same-writer receipt, ACK and preserved parsed-return wrapper references. DATA only: this projection grants no authority. */
    public record ActionPublication(Complete original,ActionReceipt receipt,ExactRef receiptReference,ExactRef acknowledgementReference,ExactRef parsedReturnReference) {
        public ActionPublication {
            Objects.requireNonNull(original);Objects.requireNonNull(receipt);Objects.requireNonNull(receiptReference);Objects.requireNonNull(acknowledgementReference);Objects.requireNonNull(parsedReturnReference);
            need(receiptReference.bytes()>0&&acknowledgementReference.bytes()>0&&parsedReturnReference.bytes()>0,"actual canonical receipt, ACK and parsed-return references required");
            need(!parsedReturnReference.path().equals(acknowledgementReference.path()),"parsed-return wrapper cannot identify the canonical ACK artifact");
        }
    }
    /** Pure public projection: actual canonical files are identified explicitly; no legacy Python receipt path is invented. */
    public static Reply publishAction(Reply normalized,ActionPublication actual) {
        Objects.requireNonNull(normalized);Objects.requireNonNull(actual);Method method=normalized.method();
        need(navigation(method),"only the five actual finite Nav products use this public action projection");
        Complete original=actual.original();ActionReceipt receipt=actual.receipt();
        need(receipt.command().before().equals(original.identity())&&receipt.command().source().equals(original.source())
                &&receipt.command().sessionId().equals(original.sessionId())&&receipt.command().operation().equals(operation(method)),
                "public artifact projection crossed its original canonical command/frame/source/session");
        var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IllegalArgumentException("canonical INTENT has no original native attempt"));
        need(attempt.guard().observed().equals(original.identity())&&attempt.guard().source().equals(original.source())
                &&attempt.guard().sessionId().equals(original.sessionId()),"public artifact projection changed its original actual guard");
        var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->new IllegalArgumentException("canonical attempt has no original dispatch"));
        need(dispatch instanceof NativeActionPort.AckReceived,"unknown native dispatch cannot manufacture a public result");
        var ack=(NativeActionPort.AckReceived)dispatch;
        need(ack.nativeOk()&&ack.requestId().equals(attempt.requestId())&&ack.originalResultToken().isPresent(),"actual correlated successful native ACK required");
        ObjectNode body=normalized.payload().original();
        need(body.equals(node(ack.originalResultToken().orElseThrow())),"public artifact projection differs from its actual original normalized native body");
        var frame=original.identity().frame();
        body.put("exact_ck3_build",VERSION).put("exe_sha256",EXECUTABLE_SHA256)
                .put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision().toString())
                .put("queried_native_revision",frame.identity().nativeRevision().toString())
                .put("queried_connection_generation",original.connectionGeneration().toString()).put("episode_run_id",frame.episodeRunId());
        body.set("native_ui_raw_return_receipt",NativeUiParsedReturn.reference(actual.parsedReturnReference()));
        body.set("java_original_native_ack",actual.acknowledgementReference().toJson());
        body.set("java_canonical_action_receipt",actual.receiptReference().toJson());
        if(method.kind()==Kind.RELIC_ACTION)body.put("automatic_retry",false).put("business_outcome_observed",false)
                .put("action_ready",false).put("consumed_intent_receipt",actual.receiptReference().path())
                .put("identical_intent_replay_blocked",!receipt.settled());
        var payload=new NativePayload(body);
        if(normalized instanceof RelicActionReply)return new RelicActionReply(method,normalized.facts(),payload);
        if(normalized instanceof CreationSelectionReply)return new CreationSelectionReply(method,normalized.facts(),payload);
        throw new IllegalArgumentException("finite Nav result has another immutable reply kind");
    }
    /** Actual private original outcome references. DATA projection only; it creates no dispatch/effect authority. */
    public record PrivateActionPublication(Complete original,Complete observedAfter,ActionReceipt receipt,ExactRef receiptReference,
            ExactRef acknowledgementReference,boolean clientReplayBlocked) {
        public PrivateActionPublication {
            Objects.requireNonNull(original);Objects.requireNonNull(observedAfter);Objects.requireNonNull(receipt);Objects.requireNonNull(receiptReference);Objects.requireNonNull(acknowledgementReference);
            need(receiptReference.bytes()>0&&acknowledgementReference.bytes()>0,"actual private canonical receipt/ACK references required");
        }
    }
    /** Preserve the exact private normalizer body and original client latch; no Nav parsed-return field is fabricated. */
    public static Reply publishPrivateAction(Reply normalized,PrivateActionPublication actual) {
        Objects.requireNonNull(normalized);Objects.requireNonNull(actual);Method method=normalized.method();
        need(Set.of(Method.OPEN,Method.CLOSE,Method.PERSONAL_SUBMIT).contains(method),"only three exact private artifact actions may use this projection");
        Complete original=actual.original();ActionReceipt receipt=actual.receipt();
        need(receipt.command().before().equals(original.identity())&&receipt.command().source().equals(original.source())
                &&receipt.command().sessionId().equals(original.sessionId())&&receipt.command().operation().equals(operation(method)),
                "private artifact public projection crossed its actual canonical operation/frame/source/session");
        var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IllegalArgumentException("private canonical action has no actual attempt"));
        need(attempt.guard().observed().equals(original.identity())&&attempt.guard().source().equals(original.source())
                &&attempt.guard().sessionId().equals(original.sessionId()),"private artifact projection changed its original guard");
        var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow(()->new IllegalArgumentException("private canonical action has no actual dispatch"));
        need(dispatch instanceof NativeActionPort.AckReceived,"private UNKNOWN dispatch cannot manufacture a public native body");
        var ack=(NativeActionPort.AckReceived)dispatch;
        need(ack.nativeOk()&&ack.requestId().equals(attempt.requestId())&&ack.originalResultToken().isPresent(),"actual correlated private ACK required");
        ObjectNode envelope=node(ack.originalResultToken().orElseThrow());
        need(envelope.has("step")&&envelope.get("step").isTextual()&&envelope.get("step").textValue().equals(method.step())
                &&envelope.has("domain_key")&&envelope.get("domain_key").isTextual()&&envelope.get("domain_key").textValue().equals(method.domain()),
                "private artifact ACK has another original step/domain");
        if(!(envelope.get(method.resultKey()) instanceof ObjectNode originalBody))
            throw new IllegalArgumentException("private artifact ACK result body is not an object");
        ObjectNode expected=originalBody.deepCopy();
        expected.set("backend_id",envelope.get("backend_id"));expected.put("domain_key",method.domain()).put("advertised",false)
                .put("snapshot_revision",original.identity().frame().identity().nativeRevision());
        ObjectNode body=normalized.payload().original();
        need(body.equals(expected),"private public projection differs from its unique original normalizer body");
        NativeFrame before=actualFrame(original),after=actualFrame(actual.observedAfter());
        need(original.identity().machineId().equals(actual.observedAfter().identity().machineId())
                &&original.source().equals(actual.observedAfter().source())&&original.sessionId().equals(actual.observedAfter().sessionId())
                &&before.gamePid()==after.gamePid()&&before.gameCreationFiletime().equals(after.gameCreationFiletime())
                &&before.actorCharacterId()==after.actorCharacterId()&&before.episodeRunId().equals(after.episodeRunId())
                &&before.connectionGeneration().equals(after.connectionGeneration())&&before.executableSha256().equals(after.executableSha256())
                &&after.publicRevision().compareTo(before.publicRevision())>=0&&after.nativeRevision().compareTo(before.nativeRevision())>=0
                &&after.dateRaw().compareTo(before.dateRaw())>=0&&after.paused()&&after.mapReady()&&after.alive(),
                "private original post snapshot crossed actual process/player/source/session/generation or moved backwards");
        need(actual.clientReplayBlocked()==!receipt.settled(),"private client latch differs from actual canonical unresolved state");
        var frame=original.identity().frame();
        body.put("exact_ck3_build",VERSION).put("exe_sha256",EXECUTABLE_SHA256)
                .put("queried_snapshot_id",frame.snapshotId()).put("queried_revision",frame.revision().toString())
                .put("queried_native_revision",frame.identity().nativeRevision().toString())
                .put("queried_connection_generation",original.connectionGeneration().toString()).put("episode_run_id",frame.episodeRunId())
                .put("client_replay_blocked",actual.clientReplayBlocked()).put("post_snapshot_id",actual.observedAfter().identity().frame().snapshotId());
        if(method==Method.OPEN||method==Method.CLOSE) {
            try {
                var outgoing=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(()->new IllegalArgumentException("actual original inventory request absent")).originalPacket());
                need(outgoing.requestId().equals(attempt.requestId())&&outgoing.step().equals(method.step()),"inventory source digest belongs to another original request");
                var sent=node(new RawJson(outgoing.normalizedAdditionalFields().value()));var digest=sent.get("source_inventory_sha256");
                need(digest!=null&&digest.isTextual()&&digest.textValue().matches("[0-9a-f]{64}"),"actual original managed inventory digest absent");
                body.put("client_source_inventory_sha256",digest.textValue());
            }catch(IOException invalid){throw new UncheckedIOException("actual original inventory request is invalid",invalid);}
        }
        body.set("java_original_native_ack",actual.acknowledgementReference().toJson());
        body.set("java_canonical_action_receipt",actual.receiptReference().toJson());
        var payload=new NativePayload(body);
        if(normalized instanceof PersonalActionReply)return new PersonalActionReply(method,normalized.facts(),payload);
        if(normalized instanceof InventoryReply)return new InventoryReply(method,normalized.facts(),payload);
        throw new IllegalArgumentException("private artifact normalizer has another reply kind");
    }
    public List<NativePrivateActionPermission> privatePermissions() {
        return privatePermissions(sources);
    }
    public static List<NativePrivateActionPermission> privatePermissions(Sources sources) {
        var result=new ArrayList<NativePrivateActionPermission>();
        for(Method method:sources.enabled())if(!navigation(method))
            result.add(new NativePrivateActionPermission(operation(method),permission(method),sources.nativeProducers().get(method),
                    request->{
                        need(request.step().equals(method.step())&&request.requiredCapability().isEmpty(),"exact artifact private operation required");
                        ObjectNode fields=node(request.additionalFields());
                        validatePrivateFields(method,fields);
                        need(!fields.has("request_id")&&!fields.has("type")&&!fields.has("protocol_version")
                                &&!fields.has("expected_revision"),"artifact cannot override sole native protocol");
                    },sources.actualQualification()));
        if(sources.enabled().contains(Method.OPEN)||sources.enabled().contains(Method.OPEN_POST)) {
            Method original=sources.enabled().contains(Method.OPEN)?Method.OPEN:Method.OPEN_POST;
            result.add(new NativePrivateActionPermission(new OperationKey(INVENTORY_QUERY),"allow_private_player_inventory_window_open",
                    sources.nativeProducers().get(original),request->{
                        need(request.step().equals(INVENTORY_QUERY)&&request.requiredCapability().isEmpty(),"original internal inventory QUERY step required");
                        ObjectNode fields=node(request.additionalFields());
                        var expected=java.util.Set.of("expected_date_raw","expected_actor_character_id","expected_game_pid","expected_connection_generation","source_inventory_sha256");
                        java.util.HashSet<String> actual=new java.util.HashSet<>();fields.fieldNames().forEachRemaining(actual::add);
                        need(actual.equals(expected),"internal inventory exact native fields required");
                        need(fields.get("source_inventory_sha256").isTextual()&&fields.get("source_inventory_sha256").textValue().matches("[a-f0-9]{64}"),"internal inventory actual source SHA absent");
                        for(String field:List.of("expected_date_raw","expected_actor_character_id","expected_game_pid","expected_connection_generation"))
                            need(fields.get(field).isIntegralNumber(),"internal inventory exact native numeric field required");
                    },sources.actualQualification()));
        }
        return List.copyOf(result);
    }
    /** The sole GUI owner includes this verifier in its pre-Core finite selector descriptor. */
    public NativePrivateActionPermission.QualificationVerifier navigationQualification(){return sources.actualQualification();}
    /** Finite original private-field grammar, also consumed by permission admission; it grants no qualification. */
    public static void validatePrivateFields(Method method,ObjectNode fields) {
        need(!navigation(method),"navigation belongs to the sole GUI finite selector owner");
        var expected=new java.util.HashSet<String>();
        if(method.kind()!=Kind.RELIC_CONTEXT&&method.kind()!=Kind.RELIC_PERMISSIONS&&method.kind()!=Kind.RELIC_ACTION_CONTEXT)
            expected.addAll(List.of("expected_date_raw","expected_actor_character_id","expected_game_pid","expected_connection_generation"));
        switch(method.kind()) {
            case PERSONAL_ITEM->expected.add("artifact_id");
            case PERSONAL_ACTION->{expected.add("artifact_id");if(method==Method.PERSONAL_POST)expected.add("expected_intent_sequence");else{
                expected.addAll(List.of("desired_equipped","expected_slot_index","policy_positive","expected_replacing_empty","expected_snapshot_revision"));
                if(fields.has("expected_replacing_artifact_id"))expected.add("expected_replacing_artifact_id");}}
            case INVENTORY_OPEN,INVENTORY_CLOSE->{expected.add("source_inventory_sha256");if(method.operation().equals("post"))expected.add("expected_intent_sequence");
                if(!method.readOnly())expected.add("expected_snapshot_revision");}
            case KNIGHT->expected.add("character_id");
            case SKILLS->expected.addAll(List.of("character_id","skill_key","skill_enum"));
            case RELIC_CONTEXT->expected.add("holy_site_id");
            case RELIC_PERMISSIONS->{expected.add("holy_site_id");if(fields.has("artifact_id"))expected.add("artifact_id");}
            case RELIC_ACTION_CONTEXT->expected.addAll(List.of("holy_site_id","artifact_id"));
            default->throw new IllegalArgumentException("not an original private artifact family");
        }
        var actual=new java.util.HashSet<String>();fields.fieldNames().forEachRemaining(actual::add);
        need(actual.equals(expected),"original private artifact fields differ from the finite family schema");
        for(String field:expected) {
            var token=fields.get(field);
            if(List.of("desired_equipped","policy_positive","expected_replacing_empty").contains(field))need(token.isBoolean(),"exact native Boolean required: "+field);
            else if(field.equals("source_inventory_sha256"))need(token.isTextual()&&token.textValue().matches("[0-9a-f]{64}"),"exact managed inventory SHA required");
            else if(field.equals("skill_key"))need(token.isTextual()&&java.util.Arrays.stream(Skill.values()).anyMatch(s->s.key().equals(token.textValue())),"exact native skill key required");
            else {
                need(token.isIntegralNumber(),"exact native integer required: "+field);var n=token.bigIntegerValue();
                java.math.BigInteger lo=java.math.BigInteger.ZERO,hi=org.xar.ck3.control.contracts.PublicUnsigned64.MAXIMUM;
                if(field.equals("expected_date_raw")){lo=java.math.BigInteger.valueOf(Integer.MIN_VALUE);hi=java.math.BigInteger.valueOf(Integer.MAX_VALUE);}
                else if(field.endsWith("artifact_id")||field.equals("holy_site_id")||field.equals("character_id")){hi=java.math.BigInteger.valueOf(0xfffffffeL);}
                else if(field.equals("expected_actor_character_id")){lo=java.math.BigInteger.ONE;hi=java.math.BigInteger.valueOf(0xfffffffeL);}
                else if(field.equals("expected_game_pid")){lo=java.math.BigInteger.ONE;hi=java.math.BigInteger.valueOf(0xffffffffL);}
                else if(field.equals("expected_slot_index"))hi=java.math.BigInteger.valueOf(63);
                else if(field.equals("skill_enum"))hi=java.math.BigInteger.valueOf(5);
                else lo=java.math.BigInteger.ONE;
                need(n.compareTo(lo)>=0&&n.compareTo(hi)<=0,"native artifact integer outside its exact range: "+field);
            }
        }
        if(method==Method.PERSONAL_SUBMIT)need(fields.get("policy_positive").booleanValue()
                &&fields.get("expected_replacing_empty").booleanValue()==!fields.has("expected_replacing_artifact_id"),"actual personal policy/replacement mismatch");
        if(method==Method.SKILLS)need(Skill.exact(fields.get("skill_key").textValue()).ordinal()==fields.get("skill_enum").intValue(),"native skill enum/key mismatch");
    }
    public void validateNative(Method method,NativeRequest request)throws IOException {
        requireEnabled(method);need(request.step().equals(method.step())&&request.requiredCapability().equals(navigation(method)
                ?Optional.of("game.command.navigate-ingame-ui-v1"):Optional.empty()),
                "artifact native request changed exact original step/private authority");
        ObjectNode fields=node(request.additionalFields());
        if(!navigation(method))validatePrivateFields(method,fields);
        need(!fields.has("expected_revision")&&!fields.has("request_id")&&!fields.has("type")
                &&!fields.has("protocol_version"),"artifact fields cannot override the sole native protocol owner");
    }
    public static OperationKey operation(Method method){return new OperationKey(method.step());}
    public static boolean navigation(Method method){return method.kind()==Kind.RELIC_ACTION||method==Method.CREATION_SELECTION;}
    public static boolean inventory(Method method){return method.kind()==Kind.INVENTORY_OPEN||method.kind()==Kind.INVENTORY_CLOSE;}
    public static String permission(Method method) {
        return switch(method.kind()) {
            case PERSONAL_ITEM->"allow_private_player_artifact_personal_use_query";
            case PERSONAL_ACTION->"allow_private_player_artifact_personal_use_actions";
            case INVENTORY_OPEN->"allow_private_player_inventory_window_open";
            case INVENTORY_CLOSE->"allow_private_player_inventory_window_close";
            case KNIGHT->"allow_private_character_knight_effectiveness_query";
            case SKILLS->"allow_private_character_skill_effects_query";
            case RELIC_CONTEXT->"allow_private_player_holy_site_relic_context_query";
            case RELIC_PERMISSIONS->"allow_private_player_holy_site_relic_permissions_query";
            case RELIC_ACTION_CONTEXT->"allow_private_player_holy_site_relic_action_context_query";
            case RELIC_ACTION->"allow_private_holy_site_relic_actions";
            case CREATION_SELECTION->"game.command.navigate-ingame-ui-v1";
        };
    }
    private RootReadContractCatalog.Family<Selection,Reply> family(Method method) {
        return new RootReadContractCatalog.Family<>("original-artifacts-"+method.name().toLowerCase(java.util.Locale.ROOT)+"/v1",
                Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.definition(),sources.decoder(),
                ArtifactsService::key,s->operation(method),selection->{
                    need(selection.query().method()==method,"artifact family changed exact original method");
                    return new ReadContract<>("original-artifact-read-"+ActionCodec.sha256(key(selection).bytes()),operation(method),
                            Optional.empty(),permission(method),ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                            ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,sources.nativeProducers().get(method),
                            (request,id)->{need(request.equals(request(selection)),"artifact original read request/arguments changed");return prepare(selection,id);},
                            receipt->decodeRead(selection,receipt),receipt->decodeRead(selection,receipt));
                });
    }
    private void requireRead(Selection selection,PlanningReadReceipt receipt) {
        need(receipt.request().equals(request(selection))&&receipt.original().nativeOk(),"artifact original read request or ACK differs");
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.binding().observed().equals(selection.captured().identity())
                    &&guard.binding().source().equals(selection.captured().source())
                    &&guard.binding().sessionId().equals(selection.captured().sessionId())
                    &&guard.paused()&&guard.mapReady()&&guard.playerAlive(),"artifact original read crossed actual guard/source/session");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"artifact complete semantic binding drift");
    }
    /** Public projection consumes the same validated original receipt; no snapshot identifier is invented by the codec. */
    private static Reply publicRead(Reply reply,Selection selection,PlanningReadReceipt receipt) {
        var body=reply.payload().original();
        publicMetadata(body,receipt,inventory(reply.method())?selection.sourceInventory():Optional.empty(),
                inventory(reply.method())||reply.method().kind()==Kind.PERSONAL_ACTION);
        var payload=new NativePayload(body);var m=reply.method();var facts=reply.facts();
        return switch(reply) {
            case PersonalItemReply ignored->new PersonalItemReply(m,facts,payload);
            case PersonalActionReply ignored->new PersonalActionReply(m,facts,payload);
            case InventoryReply ignored->new InventoryReply(m,facts,payload);
            case KnightReply ignored->new KnightReply(m,facts,payload);
            case SkillsReply ignored->new SkillsReply(m,facts,payload);
            case RelicContextReply ignored->new RelicContextReply(m,facts,payload);
            case RelicPermissionsReply ignored->new RelicPermissionsReply(m,facts,payload);
            case RelicActionContextReply ignored->new RelicActionContextReply(m,facts,payload);
            case RelicActionReply ignored->throw new IllegalArgumentException("navigation is not a private read");
            case CreationSelectionReply ignored->throw new IllegalArgumentException("creation selection is not a private read");
        };
    }
    private static void publicMetadata(ObjectNode body,PlanningReadReceipt receipt,Optional<String> inventorySha,boolean includePost) {
        var original=receipt.request().before().frame();
        body.put("exact_ck3_build",VERSION).put("exe_sha256",EXECUTABLE_SHA256)
                .put("queried_snapshot_id",original.snapshotId()).put("queried_revision",original.revision().toString())
                .put("queried_native_revision",original.identity().nativeRevision().toString());
        if(includePost)
            body.put("post_snapshot_id",receipt.after().binding().observed().frame().snapshotId());
        inventorySha.ifPresent(value->body.put("client_source_inventory_sha256",value));
    }
    private void requireWire(Selection selection,NativeActionPort.AckReceived ack,String id) {
        try {
            var sent=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(()->new IllegalArgumentException("original artifact outgoing packet absent")).originalPacket());
            need(sent.requestId().equals(id)&&ack.requestId().equals(id)&&sent.step().equals(selection.query().method().step())
                    &&sent.expectedRevision().equals(Optional.of(selection.frame().nativeRevision()))
                    &&(navigation(selection.query().method())||sent.expectedSnapshotRevision().equals(Optional.of(selection.frame().nativeRevision()))),
                    "artifact original outgoing ID/step/native revision differs");
            need(node(new RawJson(sent.normalizedAdditionalFields().value())).equals(
                    ArtifactsCodec.nativeFields(selection.query(),selection.frame(),selection.sourceInventory())),
                    "artifact actual outgoing fields differ from exact typed original request");
            var decoded=NativeWire.decode(ack.originalPacket());
            need(decoded instanceof NativeWire.CommandResult,"artifact complete actual command_result absent");
            var packet=(NativeWire.CommandResult)decoded;
            need(packet.nativeOk()&&ack.nativeOk()&&packet.requestId().equals(id)
                    &&packet.result().presence()==NativeWire.Presence.VALUE
                    &&java.util.Arrays.equals(packet.payload().value(),ack.originalFrame().bytes())
                    &&java.util.Arrays.equals(packet.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),
                    "artifact original packet/result-token custody differs");
        }catch(IOException unavailable){throw new UncheckedIOException("artifact original wire evidence unavailable",unavailable);}
    }
    private void requireHeld(Selection selection)throws IOException {
        var hello=transport.originalHello();var frame=selection.frame();var held=transport.latestObservedSnapshot()
                .orElseThrow(()->new IOException("actual artifact held native snapshot absent"));
        need(hello.pid()==frame.gamePid()&&hello.connectionGeneration().equals(frame.connectionGeneration())
                &&hello.gameSha256().equals(EXECUTABLE_SHA256)&&hello.buildMatch()
                &&held.session().game().equals(selection.captured().identity().game())
                &&held.session().connectionGeneration().equals(frame.connectionGeneration())
                &&held.nativeRevision().equals(frame.nativeRevision())
                &&held.snapshotId().equals(selection.captured().identity().frame().snapshotId()),
                "artifact actual held physical/native frame/build changed");
        ObjectNode state=node(held.state());need(state.path("paused").isBoolean()&&state.path("paused").booleanValue()
                &&state.path("map_ready").isBoolean()&&state.path("map_ready").booleanValue()
                &&state.path("played_character").path("alive").isBoolean()
                &&state.path("played_character").path("alive").booleanValue(),"artifact held living paused map unavailable");
    }
    private void requireEnabled(Method method){need(enabled(method),"original artifact permission disabled: "+permission(method));}
    private static RawJson key(Selection selection) {
        var n=ArtifactsCodec.encode(selection.query());n.put("actual_full_binding_sha256",selection.captured().fullBindingSha256());
        n.set("original_frame_evidence",selection.captured().originalEvidence().toJson());
        n.put("actual_game_birth",selection.frame().gameCreationFiletime().toString());
        n.put("actual_connection_generation",selection.frame().connectionGeneration().toString());
        if(selection.sourceInventory().isPresent())n.put("source_inventory_sha256",selection.sourceInventory().orElseThrow());else n.putNull("source_inventory_sha256");
        return raw(n);
    }

    public static NativeFrame actualFrame(Complete actual) {
        Objects.requireNonNull(actual);
        var actor=actual.identity().frame().identity().player();
        need(actor.signum()>0&&actor.compareTo(java.math.BigInteger.valueOf(Integer.MAX_VALUE))<=0,
                "ART15 requires a positive public int32 actor; signed high-bit actors need the separately typed native-family successor");
        var semantic=actual.semantic();var player=OpportunityJson.object(semantic.get("played_character"),"actual played actor");
        return new NativeFrame(actual.identity().frame().revision(),actual.identity().frame().identity().nativeRevision(),
                actual.identity().frame().identity().dateRaw(),actor.longValueExact(),
                actual.identity().game().pid(),actual.identity().game().creationFiletime().value(),actual.connectionGeneration(),
                actual.identity().frame().episodeRunId(),EXECUTABLE_SHA256,
                OpportunityJson.bool(semantic.get("paused"),"actual paused"),
                OpportunityJson.bool(semantic.get("map_ready"),"actual map"),
                OpportunityJson.bool(player.get("alive"),"actual living played actor"));
    }
    public record InventorySelection(Complete captured,NativeFrame frame,String sourceInventory,Instant deadline) {
        public InventorySelection {Objects.requireNonNull(captured);Objects.requireNonNull(frame);Objects.requireNonNull(deadline);
            need(sourceInventory!=null&&sourceInventory.matches("[0-9a-f]{64}"),"actual managed inventory source required");}
    }
    public static final class InventoryResult {
        private final ObjectNode body;
        private InventoryResult(ObjectNode actual){body=actual.deepCopy();}
        public ObjectNode original(){return body.deepCopy();}
    }
    public InventorySelection inventorySelection(Complete actual,Instant deadline)throws IOException {
        need(internalInventorySource().isPresent(),"original inventory-open QUERY permission/source unavailable");
        NativeFrame frame=sources.frames().require(actual);
        need(frame.equals(actualFrame(actual)),"internal inventory query lost actual complete physical frame");
        return new InventorySelection(actual,frame,sources.inventory().require(actual),deadline);
    }
    private Optional<ExactRef> internalInventorySource(){
        for(Method method:List.of(Method.OPEN,Method.OPEN_POST))if(sources.enabled().contains(method))
            return Optional.of(sources.nativeProducers().get(method));
        return Optional.empty();
    }
    private static final String INVENTORY_QUERY="query-player-inventory-window-v1-private";
    private RootReadContractCatalog.Family<InventorySelection,InventoryResult> inventoryFamily;
    public synchronized RootReadContractCatalog.Family<InventorySelection,InventoryResult> internalInventoryFamily(){
        if(inventoryFamily==null) {
            ExactRef source=internalInventorySource().orElseThrow(()->new IllegalStateException("actual original inventory QUERY source absent"));
            inventoryFamily=new RootReadContractCatalog.Family<>("original-inventory-window-query/v1",InventorySelection.class,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.definition(),sources.decoder(),
                    ArtifactsService::inventoryKey,s->new OperationKey(INVENTORY_QUERY),s->new ReadContract<>(
                    "original-inventory-query-"+ActionCodec.sha256(inventoryKey(s).bytes()),new OperationKey(INVENTORY_QUERY),
                    Optional.empty(),"allow_private_player_inventory_window_open",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                    ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->{
                        need(request.equals(inventoryRequest(s)),"original internal inventory query changed");
                        try{requireHeld(new Selection(s.captured(),s.frame(),new RevisionRequest(Method.OPEN,s.frame().publicRevision()),Optional.of(s.sourceInventory()),s.deadline()));}
                        catch(IOException failure){throw new UncheckedIOException(failure);}
                        return new NativeRequest(INVENTORY_QUERY,Optional.empty(),raw(inventoryFields(s)));
                    },receipt->inventoryDecode(s,receipt),receipt->inventoryDecode(s,receipt)));
        }return inventoryFamily;
    }
    public PlanningReadRequest inventoryRequest(InventorySelection s) {
        return new PlanningReadRequest(s.captured().identity(),s.captured().source(),s.captured().sessionId(),
                new OperationKey(INVENTORY_QUERY),obj(inventoryKey(s)),s.deadline());
    }
    public ReadContract<InventoryResult> inventoryContract(RootReadContractCatalog actual,InventorySelection s){
        return actual.issue(internalInventoryFamily(),s);
    }
    private InventoryResult inventoryDecode(InventorySelection s,PlanningReadReceipt receipt) {
        need(receipt.request().equals(inventoryRequest(s))&&receipt.original().nativeOk(),"original internal inventory query/ACK differs");
        for(var guard:List.of(receipt.before(),receipt.after()))
            need(guard.binding().observed().equals(s.captured().identity())&&guard.binding().source().equals(s.captured().source())
                    &&guard.binding().sessionId().equals(s.captured().sessionId())&&guard.paused()&&guard.mapReady()&&guard.playerAlive(),
                    "internal inventory actual guard/source/session drift");
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"internal inventory semantic drift");
        try{
            var outgoing=NativeWire.decodeExecuteRequest(receipt.original().outbound().orElseThrow().originalPacket());
            need(outgoing.step().equals(INVENTORY_QUERY)&&outgoing.requestId().equals(receipt.requestId())
                    &&outgoing.expectedRevision().equals(Optional.of(s.frame().nativeRevision()))
                    &&outgoing.expectedSnapshotRevision().equals(Optional.of(s.frame().nativeRevision()))
                    &&node(new RawJson(outgoing.normalizedAdditionalFields().value())).equals(inventoryFields(s)),
                    "internal inventory original outgoing request differs");
            var nativePacket=NativeWire.decode(receipt.original().originalPacket());
            need(nativePacket instanceof NativeWire.CommandResult,"actual internal inventory command_result absent");
            var packet=(NativeWire.CommandResult)nativePacket;
            need(packet.nativeOk()&&packet.requestId().equals(receipt.requestId())
                    &&packet.result().presence()==NativeWire.Presence.VALUE
                    &&java.util.Arrays.equals(packet.payload().value(),receipt.original().originalFrame().bytes())
                    &&java.util.Arrays.equals(packet.result().token().orElseThrow().value(),receipt.original().originalResultToken().orElseThrow().bytes()),
                    "internal inventory complete packet/token custody drift");
        }catch(IOException failure){throw new UncheckedIOException(failure);}
        var normalized=ArtifactsCodec.normalizeInventoryQuery(s.frame(),
                new NativeEnvelope(receipt.requestId(),StrictJson.parse(receipt.original().originalFrame().bytes()),s.frame()));
        publicMetadata(normalized,receipt,Optional.of(s.sourceInventory()),true);return new InventoryResult(normalized);
    }
    private static ObjectNode inventoryFields(InventorySelection s){
        return StrictJson.object().put("expected_date_raw",s.frame().dateRaw())
                .put("expected_actor_character_id",s.frame().actorCharacterId()).put("expected_game_pid",s.frame().gamePid())
                .put("expected_connection_generation",s.frame().connectionGeneration()).put("source_inventory_sha256",s.sourceInventory());
    }
    private static RawJson inventoryKey(InventorySelection s){
        var n=StrictJson.object().put("schema","xar.original-inventory-query-selection/v1")
                .put("actual_full_binding_sha256",s.captured().fullBindingSha256())
                .put("source_inventory_sha256",s.sourceInventory());n.set("original_frame_evidence",s.captured().originalEvidence().toJson());return raw(n);
    }

    private static java.math.BigInteger BigIntegerValue(long value){return java.math.BigInteger.valueOf(value);}
    private static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
    private static OpportunityJson.Obj obj(RawJson value){return OpportunityJson.object(OpportunityJson.parse(value.bytes()),"closed artifact arguments");}
    private static ObjectNode node(RawJson value){
        var parsed=StrictJson.parse(value.bytes());
        if(parsed instanceof ObjectNode actual)return actual;
        throw new IllegalArgumentException("artifact native boundary requires an exact JSON object");
    }
    private static void need(boolean condition,String message){StrictJson.require(condition,message);}
}

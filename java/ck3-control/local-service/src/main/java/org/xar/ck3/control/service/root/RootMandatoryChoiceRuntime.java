package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryEvidenceLookup;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceCodec;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Existing Native mandatory-choice mailbox on the sole Root read/action/archive path.
 * Token ACK, an independently observed receiver transition and gameplay material remain distinct. */
public final class RootMandatoryChoiceRuntime {
    public static final String QUERY="query-mandatory-choice-v1", SELECT="select-mandatory-choice-v1";
    public static final String CAPABILITY="game.state.native-mandatory-choice-window-v1";
    public static final String SCHEMA="xar.ck3.native-mandatory-choice-postcondition/v1";
    private static final String CONTRACT="native/mandatory-choice-v1";
    private static final String HINT_SOURCE="application_main_pump_observed_modal_receiver";
    private final RootRuntimeContext context;
    private final ExactRef source;
    private final NativeEffectSnapshots snapshots;
    private final Knowledge knowledge;
    private final NativeEventEffects.ObservedAfter incidents;
    public record Knowledge(EventSourceReadContext sources, ExactRef backend) {
        public Knowledge { Objects.requireNonNull(sources); Objects.requireNonNull(backend); }
    }
    private final ReadContract<EventPolicies.ReadPublication> query;

    RootMandatoryChoiceRuntime(RootRuntimeContext context,ExactRef source,EventWindowRead.Admission admission,
            EventSourceReadContext sources, RootIncidentRuntime incidents) {
        this.context=Objects.requireNonNull(context);this.source=Objects.requireNonNull(source);
        Objects.requireNonNull(incidents).requireContext(context); this.incidents=incidents;
        var backend=context.game().launchPlan().sources().review().bridgeDll();
        knowledge=new Knowledge(Objects.requireNonNull(sources),new ExactRef(backend.path(),backend.bytes(),backend.sha256()));
        snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader());
        query=contract(source,admission);
    }
    public ReadContract<EventPolicies.ReadPublication> query(){return query;}
    /** The original native endpoint consumes this exact owner frame, including the separate public revision. */
    static ReadContract<EventPolicies.ReadPublication> contract(ExactRef source,EventWindowRead.Admission admission) {
        Objects.requireNonNull(source);Objects.requireNonNull(admission);
        return new ReadContract<>(CONTRACT,new OperationKey(QUERY),Optional.of(CAPABILITY),CAPABILITY,
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                (request,id)->{admission.verify(request);ObjectNode frame=frame(request);requirePresentHint(node(request.arguments()));
                    var fields=objectNode();fields.set("mandatory_choice_frame_binding",frame);
                    return new NativeRequest(QUERY,Optional.of(CAPABILITY),raw(fields));},
                RootMandatoryChoiceRuntime::decodeQuery,RootMandatoryChoiceRuntime::decodeQuery);
    }
    static EventPolicies.ReadPublication decodeQuery(PlanningReadReceipt receipt) {
        StrictJson.require(CONTRACT.equals(receipt.contractId())&&QUERY.equals(receipt.request().operation().value()),"mandatory query original contract differs");
        ObjectNode expected=frame(receipt.request());
        for(var guard:List.of(receipt.before(),receipt.after())) {
            StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP&&guard.paused()&&guard.mapReady()&&guard.playerAlive(),
                    "mandatory query lost its living paused-map read guards");
            NativeWire.Frame parsed;
            try{parsed=NativeWire.decode(original(guard.binding().capabilityEvidence()));}
            catch(IOException failure){throw new UncheckedIOException("mandatory query HELLO unavailable",failure);}
            StrictJson.require(parsed instanceof NativeWire.Hello,"mandatory query requires its actual HELLO");
            var hello=(NativeWire.Hello)parsed;
            StrictJson.require(hello.pid()==receipt.request().before().game().pid()&&hello.connectionGeneration().equals(guard.binding().connectionGeneration())
                    &&hello.buildMatch()&&hello.adapterStatus().equals("ready")&&hello.capabilities().contains(CAPABILITY)
                    &&hello.gameSha256().equalsIgnoreCase("98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"),
                    "mandatory query process/connection/executable/capability differs");
        }
        ObjectNode fields=objectNode();fields.set("mandatory_choice_frame_binding",expected);
        ObjectNode result=originalResult(receipt.original(),QUERY,raw(fields));
        objectNode(result,Set.of("step","accepted","status","owner_verified","queried_snapshot_id","queried_revision",
                "queried_native_revision","unavailable_reason","mandatory_choice"));
        bool(result.get("accepted"));bool(result.get("owner_verified"));StrictJson.text(result.get("status"));
        for(String key:List.of("snapshot_id","revision","native_revision"))
            StrictJson.require(Objects.equals(result.get("queried_"+key),expected.get(key)),"mandatory query source frame differs: "+key);
        JsonNode window=result.get("mandatory_choice");
        if(bool(result.get("accepted"))) {
            StrictJson.require("available".equals(StrictJson.text(result.get("status")))&&bool(result.get("owner_verified")),
                    "available mandatory query lacks its actual owning-thread observation");
            var decoded=MandatoryChoiceCodec.decode(StrictJson.canonical(window));
            StrictJson.require(decoded.frame().original().json().equals(MandatoryChoiceCodec.decodeFrame(StrictJson.canonical(expected)).original().json()),
                    "mandatory query changed the exact native/public owner frame");
        } else StrictJson.require(window!=null&&window.isNull()&&"unavailable".equals(StrictJson.text(result.get("status"))),
                "unavailable mandatory query cannot publish a usable window");
        return new EventPolicies.ReadPublication(object(result),Optional.empty());
    }
    OrdinaryCorePolicy.Prepared prepare(PlanningRequest actual,Obj plan) {
        StrictJson.require(actual.before().game().equals(context.game().generation())&&actual.source().equals(context.source())
                &&actual.sessionId().equals(context.game().sessionId()),"mandatory selection crossed the installed physical Root");
        return prepare(actual,plan,context.archive(),knowledge);
    }
    /** Same ordinary adapter consumes its source-reviewed Root facts, without a legacy Python launch layout. */
    static OrdinaryCorePolicy.Prepared prepare(PlanningRequest actual,Obj plan,ActionPorts.OutcomeArchive archive,Knowledge knowledge) {
        Objects.requireNonNull(knowledge);
        plan=plan.with("mandatory_backend_source",object(knowledge.backend().toJson()));
        var selected=selection(actual,plan,archive);
        Optional<org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument> known=
                new UiRecoveryEvidenceLookup(knowledge.sources()).lookupRoot(node(plan).path("unknown_mandatory_choice_v1").get("native_window"),
                        BigInteger.valueOf(actual.before().game().pid()),knowledge.backend());
        if(known.isPresent()) {
            Obj fact=object(StrictJson.parse(known.orElseThrow().json().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            Obj capture=OpportunityJson.object(plan.get("unknown_mandatory_choice_v1"),"actual mandatory capture");
            plan=plan.with("known_ui_recovery_source",fact).with("unknown_mandatory_choice_v1",capture.with("known_ui_recovery_source",fact));
        }
        return prepare(actual,plan,archive);
    }
    static OrdinaryCorePolicy.Prepared prepare(PlanningRequest actual,Obj plan,ActionPorts.OutcomeArchive archive) {
        var selection=selection(actual,plan,archive);
        var values=expectedValues(selection);
        var expected=new ExpectedPostcondition(1,actual.before(),actual.source(),SCHEMA,values);
        String id=ActionIds.forDecision(actual.sessionId(),actual.before(),"mandatory:"+DriverJson.sha256(OpportunityJson.encode(plan)));
        var claims=new Claims(Set.of(),Set.of(),Set.of(actual.before().frame().identity().player()),Set.of("foreground-window"));
        return new OrdinaryCorePolicy.Prepared(new ActionCommand(id,actual.before(),actual.source(),actual.sessionId(),
                new OperationKey(SELECT),plan,expected,claims,actual.deadline()));
    }
    private record Selection(String queryId,String token,String windowId,String instanceId,String choiceId,ObjectNode frame,ExactRef originalRead,RawJson nativeWindow) { }
    private static Selection selection(PlanningRequest actual,Obj plan,ActionPorts.OutcomeArchive archive) {
        var selected=selection(plan);
        StrictJson.require(selected.frame().equals(frame(new PlanningReadRequest(actual.before(),actual.source(),actual.sessionId(),
                new OperationKey(QUERY),actual.observations().snapshot(),actual.deadline()))),"mandatory token belongs to another actual owner frame");
        String current=requirePresentHint(node(actual.observations().snapshot()));
        StrictJson.require(current.equals(selected.instanceId()),"mandatory token is not the actual current exclusive receiver");
        requireOriginalQuery(selected,actual.before(),actual.source(),actual.sessionId(),archive);
        return selected;
    }
    private static Selection selection(Obj plan) {
        ObjectNode retained=node(plan);
        StrictJson.require(SELECT.equals(StrictJson.text(retained.get("selected_step"))),"original mandatory selection step required");
        ObjectNode capture=objectNode(retained.get("unknown_mandatory_choice_v1"));
        ObjectNode window=objectNode(capture.get("native_window")),chosen=objectNode(capture.get("selection"));
        var decoded=MandatoryChoiceCodec.decode(StrictJson.canonical(window));
        StrictJson.require(decoded.choicesComplete()&&decoded.blockingProof().isPresent(),"complete source-bound blocking catalogue required");
        ObjectNode frame=objectNode(capture.get("frame_binding"));
        StrictJson.require(Objects.equals(frame,window.get("frame_binding")),"mandatory capture frame differs from native window");
        String query=StrictJson.text(chosen.get("query_id")),token=StrictJson.text(chosen.get("action_token"));
        String windowId=StrictJson.text(window.get("window_id")),instance=StrictJson.text(window.get("window_instance_id")),choice=StrictJson.text(chosen.get("choice_id"));
        StrictJson.require(Objects.equals(chosen.get("query_id"),window.get("query_id"))&&Objects.equals(chosen.get("window_instance_id"),window.get("window_instance_id")),
                "mandatory selected token changed native query/window identity");
        var recommendation=org.xar.ck3.control.events.mandatorychoice.MandatoryChoicePolicy.selectUnknownMandatory(decoded,Optional.of(decoded.frame()));
        StrictJson.require(recommendation.selectedChoice().isPresent(),"original mandatory selected row is not legal");
        ObjectNode verified=objectNode(StrictJson.parse(MandatoryChoiceCodec.encodeDecision(recommendation)));
        StrictJson.require(Objects.equals(verified.get("selected_choice_id"),chosen.get("choice_id"))&&Objects.equals(verified.get("action_token"),chosen.get("action_token")),
                "mandatory action must preserve the actual first native choice and token");
        ExactRef read=ExactRef.fromJson(retained.get("mandatory_choice_original_read"));
        return new Selection(query,token,windowId,instance,choice,frame,read,raw(window));
    }
    private static void requireOriginalQuery(Selection selected,ObservationIdentity before,org.xar.ck3.control.g2.common.G2Source source,
            String session,ActionPorts.OutcomeArchive archive) {
        PlanningReadReceipt receipt=archive.loadRead(selected.originalRead());
        StrictJson.require(archive.readReferenceOf(receipt).equals(selected.originalRead())&&receipt.request().before().equals(before)
                &&receipt.request().source().equals(source)&&receipt.request().sessionId().equals(session),"mandatory token lost its exact original query receipt");
        NativeRecordedEvidenceVerifier.requireRead(receipt,archive);
        ObjectNode result=node(decodeQuery(receipt).result()),window=objectNode(result.get("mandatory_choice"));
        StrictJson.require(raw(window).equals(selected.nativeWindow()),"mandatory retained catalogue differs from its actual original query");
        StrictJson.require(selected.queryId().equals(StrictJson.text(window.get("query_id")))
                &&selected.instanceId().equals(StrictJson.text(window.get("window_instance_id"))),"mandatory token/query original differs");
        var decoded=MandatoryChoiceCodec.decode(StrictJson.canonical(window));
        boolean present=decoded.choices().stream().filter(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice.class::isInstance)
                .map(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.NativeChoice.class::cast)
                .anyMatch(row->row.actionToken().hasValue()&&row.actionToken().value().equals(selected.token()));
        StrictJson.require(present,"mandatory token was not produced by the actual original query");
    }
    private NativeRequest prepare(ActionCommand command) { return prepareRequest(command,context.archive()); }
    static NativeRequest prepareRequest(ActionCommand command,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(command.operation().value().equals(SELECT)&&command.expected().observerSchema().equals(SCHEMA),"mandatory operation/schema differs");
        Selection selected=selection(command.arguments());
        StrictJson.require(command.expected().values().equals(expectedValues(selected))&&command.expected().before().equals(command.before())
                &&command.expected().source().equals(command.source()),"mandatory retained expected values differ");
        requireOriginalQuery(selected,command.before(),command.source(),command.sessionId(),archive);
        return request(selected);
    }
    private static NativeRequest request(Selection selected) {
        ObjectNode choice=objectNode().put("query_id",selected.queryId()).put("action_token",selected.token()).put("window_instance_id",selected.instanceId());
        choice.set("frame_binding",selected.frame());ObjectNode fields=objectNode();fields.set("mandatory_choice_selection",choice);
        return new NativeRequest(SELECT,Optional.of(CAPABILITY),raw(fields));
    }
    RootExecutableBindings.ActionBinding action() {
        return new RootExecutableBindings.ActionBinding(new NativeEffectRegistry.Binding(new OperationKey(SELECT),source,this::prepare,this::observe),
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(CAPABILITY),source);
    }
    private NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempted,NativeActionPort.DispatchOutcome dispatch) {
        return observe(command,attempted,dispatch,snapshots,context.archive(),incidents);
    }
    static NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempted,NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots snapshots,ActionPorts.OutcomeArchive archive) {
        return observe(command,attempted,dispatch,snapshots,archive,(original,attempt,pair,projected)->{ });
    }
    static NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempted,NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots snapshots,ActionPorts.OutcomeArchive archive,NativeEventEffects.ObservedAfter incidents) {
        Selection selected=selection(command.arguments());requireOriginalQuery(selected,command.before(),command.source(),command.sessionId(),archive);
        var pair=snapshots.read(command,attempted);var projected=project(command,attempted,dispatch,pair);
        if(!(projected.result() instanceof ActionPorts.EffectObserved))return projected;
        ExactRef basis=snapshots.evidence(command,attempted,pair,List.of(archive.loadRead(selected.originalRead())),projected.compatibleResult().orElseThrow());
        projected=NativeEffectSnapshots.withEvidence(projected,List.of(basis));
        incidents.record(command,attempted,pair,projected);return projected;
    }
    NativeRecordedEvidenceVerifier.Binding archived() { return archived(source,context.frameLoader()); }
    static NativeRecordedEvidenceVerifier.Binding archived(ExactRef source,NativeEffectEvidence.FrameLoader frames) {
        return new NativeRecordedEvidenceVerifier.Binding(new OperationKey(SELECT),source,(head,receipt,archive)->{
            var original=NativeEffectEvidence.load(receipt,archive,frames);
            Selection selected=selection(receipt.command().arguments());requireOriginalQuery(selected,receipt.command().before(),receipt.command().source(),receipt.command().sessionId(),archive);
            StrictJson.require(original.independentReads().equals(List.of(archive.loadRead(selected.originalRead()))),"mandatory archive lost its sole actual catalogue read");
            var settled=(ActionState.Settled)receipt.state();
            var replayed=project(receipt.command(),settled.attempt(),settled.dispatch(),original.frames());
            replayed=NativeEffectSnapshots.withEvidence(replayed,((ActionState.Applied)settled.settlement()).observation().supportingEvidence());
            NativeEffectEvidence.requireSame(settled.settlement(),replayed,original.compatibleResult());
        });
    }
    static NativeEffectRegistry.Projected project(ActionCommand command,ActionState.Attempt attempted,NativeActionPort.DispatchOutcome dispatch,
            NativeEffectSnapshots.Pair pair) {
        Selection selected=selection(command.arguments());
        StrictJson.require(pair.before().identity().equals(command.before())&&pair.before().source().equals(command.source())
                &&pair.before().sessionId().equals(command.sessionId())&&SCHEMA.equals(command.expected().observerSchema()),"mandatory effect original frame/source differs");
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))
            return NativeEffectRegistry.Projected.pending("mandatory original outcome is unknown; never resubmit its token",List.of(pair.after().originalEvidence()));
        ObjectNode original=originalResult(ack,SELECT,request(selected).additionalFields());
        ObjectNode post=objectNode(original.get("mandatory_choice_postcondition"));
        boolean nativeAdvanced=bool(original.get("accepted"))&&bool(original.get("owner_verified"))
                &&bool(post.get("verified"))&&bool(post.get("old_window_no_longer_blocking"))
                &&selected.windowId().equals(StrictJson.text(post.get("old_window_id")))
                &&selected.instanceId().equals(StrictJson.text(post.get("old_instance")))
                &&selected.choiceId().equals(StrictJson.text(post.get("selected_choice_id")))
                &&"fresh_native_modal_receiver_vector_no_old_widget_dereference".equals(StrictJson.text(post.get("source")));
        Optional<String> after=observedHint(node(pair.after().semantic()));
        if(!nativeAdvanced||after.isEmpty()||after.orElseThrow().equals(selected.instanceId()))
            return NativeEffectRegistry.Projected.pending("actual original receiver transition and independent later hint are not both verified",List.of(pair.after().originalEvidence()));
        ObjectNode compatible=original.deepCopy();compatible.put("progress_status","postcondition").put("material_effects_verified",false);
        compatible.put("snapshot_id",pair.after().identity().frame().snapshotId()).put("revision",pair.after().identity().frame().revision());
        compatible.set("independent_modal_hint",node(pair.after().semantic()).get("top_exclusive_modal_choice_hint"));
        var projected=NativeEffectSnapshots.observed(command,attempted,pair.after(),SCHEMA,expectedValues(selected),NativeEffectSnapshots.publication(pair.after()),raw(compatible),List.of());
        return projected;
    }
    private static List<ExpectedValue> expectedValues(Selection selected) {
        return List.of(new ExpectedText(new FieldKey("old_window_instance_id"),selected.instanceId()),
                new ExpectedText(new FieldKey("selected_choice_id"),selected.choiceId()),
                new ExpectedBoolean(new FieldKey("old_window_no_longer_blocking"),true));
    }
    private static ObjectNode frame(PlanningReadRequest request) {
        ObjectNode snapshot=node(request.arguments()),frame=objectNode();var identity=request.before().frame();
        ObjectNode diagnostics=objectNode(snapshot.get("diagnostics")),player=objectNode(snapshot.get("played_character"));
        frame.set("game_pid",diagnostics.get("bridge_pid"));frame.set("connection_generation",diagnostics.get("connection_generation"));
        for(String key:List.of("revision","native_revision","date_raw","episode_run_id","snapshot_id"))frame.set(key,snapshot.get(key));
        frame.set("actor_character_id",player.get("character_id"));var decoded=MandatoryChoiceCodec.decodeFrame(StrictJson.canonical(frame));
        StrictJson.require(decoded.gamePid()==request.before().game().pid()&&decoded.revision().equals(identity.revision())
                &&decoded.nativeRevision().equals(identity.identity().nativeRevision())&&decoded.dateRaw().equals(identity.identity().dateRaw())
                &&decoded.actorCharacterId().equals(identity.identity().player())&&decoded.episodeRunId().equals(identity.episodeRunId())
                &&decoded.snapshotId().equals(identity.snapshotId()),"mandatory actual snapshot differs from its original observation identity");
        return frame;
    }
    private static String requirePresentHint(ObjectNode snapshot) {
        Optional<String> observed=observedHint(snapshot);
        StrictJson.require(observed.isPresent()&&!observed.orElseThrow().isEmpty(),"actual qualified top exclusive native receiver required");
        return observed.orElseThrow();
    }
    private static Optional<String> observedHint(ObjectNode snapshot) {
        JsonNode raw=snapshot.get("top_exclusive_modal_choice_hint");if(!(raw instanceof ObjectNode hint))return Optional.empty();
        if(!hint.path("owner_verified").isBoolean()||!hint.path("owner_verified").booleanValue()
                ||!HINT_SOURCE.equals(hint.path("source").asText())||!hint.path("max_observation_age_ms").isIntegralNumber()
                ||!BigInteger.valueOf(2000).equals(hint.path("max_observation_age_ms").bigIntegerValue()))return Optional.empty();
        if("absent".equals(hint.path("status").asText())&&hint.path("opaque_root_id").isNull())return Optional.of("");
        if("present".equals(hint.path("status").asText())&&hint.path("opaque_root_id").isTextual()&&!hint.path("opaque_root_id").textValue().isBlank())
            return Optional.of(hint.path("opaque_root_id").textValue());
        return Optional.empty();
    }
    private static ObjectNode originalResult(NativeActionPort.AckReceived ack,String step,RawJson fields) {
        try {
            StrictJson.require(ack.nativeOk()&&ack.originalResultToken().isPresent(),"mandatory original successful outer packet required");
            var decoded=NativeWire.decode(ack.originalPacket());
            StrictJson.require(decoded instanceof NativeWire.CommandResult,"mandatory actual original return packet required");
            var returned=(NativeWire.CommandResult)decoded;
            StrictJson.require(returned.nativeOk()&&returned.requestId().equals(ack.requestId())
                    &&Arrays.equals(returned.payload().value(),ack.originalFrame().bytes())
                    &&returned.result().token().isPresent()
                    &&Arrays.equals(returned.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"mandatory packet/payload/result identity differs");
            var sent=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow(()->new IllegalArgumentException("mandatory original outbound packet missing")).originalPacket());
            StrictJson.require(sent.requestId().equals(ack.requestId())&&sent.step().equals(step)
                    &&StrictJson.parse(sent.normalizedAdditionalFields().value()).equals(StrictJson.parse(fields.bytes())),"mandatory original request step/fields differs");
            ObjectNode sentFields=objectNode(StrictJson.parse(fields.bytes()));
            JsonNode bound=QUERY.equals(step)?sentFields.get("mandatory_choice_frame_binding"):sentFields.path("mandatory_choice_selection").get("frame_binding");
            StrictJson.require(bound!=null&&sent.expectedRevision().filter(value->value.equals(bound.path("native_revision").bigIntegerValue())).isPresent(),
                    "mandatory outbound actual expected native revision differs");
            ObjectNode result=objectNode(StrictJson.parse(ack.originalResultToken().orElseThrow().bytes()));
            StrictJson.require(step.equals(StrictJson.text(result.get("step"))),"mandatory original result step differs");return result;
        } catch(IOException failure){throw new UncheckedIOException("mandatory original Native wire unavailable",failure);}
    }
    private static byte[] original(ExactRef ref)throws IOException {
        var witness=SharedSourceFiles.observe(Path.of(ref.path()));
        StrictJson.require(witness.source().bytes()==ref.bytes()&&witness.source().sha256().equals(ref.sha256()),"mandatory source original changed");
        byte[] raw=Files.readAllBytes(Path.of(ref.path()));StrictJson.require(raw.length==ref.bytes()&&ActionCodec.sha256(raw).equals(ref.sha256()),"mandatory original bytes/SHA differ");SharedSourceFiles.assertUnchanged(witness);return raw;
    }
    private static boolean bool(JsonNode value){StrictJson.require(value!=null&&value.isBoolean(),"actual mandatory boolean token required");return value.booleanValue();}
    private static ObjectNode objectNode(){return StrictJson.object();}
    private static ObjectNode objectNode(JsonNode value){StrictJson.require(value instanceof ObjectNode,"actual mandatory JSON object required");return (ObjectNode)value;}
    private static ObjectNode objectNode(JsonNode value,Set<String> fields){return StrictJson.object(value,fields);}
    private static ObjectNode node(OpportunityJson.Value value){return objectNode(StrictJson.parse(OpportunityJson.encode(value)));}
    private static Obj object(JsonNode value){return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(value)),"mandatory original object");}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
}

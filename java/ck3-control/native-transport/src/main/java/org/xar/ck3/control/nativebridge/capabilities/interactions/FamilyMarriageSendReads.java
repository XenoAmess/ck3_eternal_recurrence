package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.family.FamilyMarriageIntent;
import org.xar.ck3.control.application.action.ordinary.RulerMarriageIntent;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.family.FamilyNativePreparation;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** One actual outgoing query with two narrowly installed origins. No pending document is invented for preparation. */
public final class FamilyMarriageSendReads {
    public static final String STEP="query-family-marriage-send-outgoing-v1-private";
    public static final String PERMISSION="allow_private_family_marriage_send_outgoing_query";
    public static final String ARGUMENT_SCHEMA="xar.java.family-marriage-outgoing-read/v2";
    public static final String WIRE_SCHEMA="ck3-family-marriage-outgoing-query-12004-v2";
    public static final String PREPARED_SCHEMA="ck3-marriage-materialized-send-context-12004-v2";
    public enum Scope { ACTION_PREPARATION, POST_SUBMISSION }
    public enum Route { FIRST_HEIR, FULFILL_BETROTHAL, CHILD_MATRILINEAL, CHILD_DEFAULT, RULER }
    public record Sender(Route route,long actor,long subject,long candidate,OptionalLong recipient,
            boolean requestMatrilineal,boolean requireMatrilinealOff) {
        public Sender {Objects.requireNonNull(route);Objects.requireNonNull(recipient);character(actor);character(subject);character(candidate);
            need(subject!=candidate,"distinct actual marriage pair required");recipient.ifPresent(FamilyMarriageSendReads::character);
            need(!(requestMatrilineal&&requireMatrilinealOff),"contradictory requested native option");}
    }
    /** Actual fresh original locators. Its constructor provides DATA only; Root's unique source owner verifies all originals. */
    public record FreshBasis(ExactRef snapshot,ExactRef bridge,List<ExactRef> reads) {
        public FreshBasis {original(snapshot);original(bridge);reads=List.copyOf(reads);need(!reads.isEmpty()&&reads.size()<=32&&new java.util.HashSet<>(reads).size()==reads.size(),"actual distinct fresh legality/root originals required");reads.forEach(FamilyMarriageSendReads::original);}
        public static FreshBasis from(FamilyNativePreparation.VerifiedBasis actual,List<ExactRef> freshReads) {
            return new FreshBasis(actual.snapshotEvidence(),actual.bridgeEvidence(),freshReads);
        }
    }
    public record Arguments(Scope scope,String actionId,String bodySha256,String attemptRequestId,Obj senderIntent,
            Optional<FreshBasis> freshBasis,Optional<ExactRef> beforeRead,OptionalLong senderCharacterId) {
        public Arguments {Objects.requireNonNull(scope);StrictJson.text(actionId);need(bodySha256!=null&&bodySha256.matches("[a-f0-9]{64}"),"exact immutable command body hash required");
            StrictJson.text(attemptRequestId);Objects.requireNonNull(senderIntent);Objects.requireNonNull(freshBasis);Objects.requireNonNull(beforeRead);Objects.requireNonNull(senderCharacterId);
            need((scope==Scope.ACTION_PREPARATION)==freshBasis.isPresent() && (scope==Scope.POST_SUBMISSION)==beforeRead.isPresent(),"preparation originals and post-submission baseline have different closed scopes");beforeRead.ifPresent(FamilyMarriageSendReads::original);need((scope==Scope.POST_SUBMISSION)==senderCharacterId.isPresent(),"only actual post query carries the retained materialized sender filter");senderCharacterId.ifPresent(FamilyMarriageSendReads::character);}
    }
    public sealed interface Materialized permits Prepared,NotPrepared { }
    public record Prepared(long definitionHash,FamilyOutgoingCodec.Roles roles,List<FamilyOutgoingCodec.OptionRow> options,
            boolean canSend,boolean matrilineal,boolean grandWedding,Optional<Boolean> effectiveMatrilineal) implements Materialized {
        public Prepared {u32(definitionHash);Objects.requireNonNull(roles);options=List.copyOf(options);need(options.size()<=4096,"complete materialized bank required");
            Objects.requireNonNull(effectiveMatrilineal);
            for(int i=0;i<options.size();i++)need(options.get(i).ordinal()==i,"materialized authored bank order differs");}
    }
    public record NotPrepared(String reason) implements Materialized {public NotPrepared {StrictJson.text(reason);}}
    public record Observation(Scope scope,Frame frame,Optional<Materialized> prepared,FamilyOutgoingCodec.Snapshot outgoing) {
        public Observation {Objects.requireNonNull(scope);Objects.requireNonNull(frame);Objects.requireNonNull(prepared);Objects.requireNonNull(outgoing);
            need(outgoing.profile()==FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE&&outgoing.frame().equals(frame),"same actual marriage storage frame required");
            need((scope==Scope.ACTION_PREPARATION)==prepared.isPresent(),"only actual before preparation contains a native local context");}
    }
    /** Must use real same-writer ActionCommandScope + fresh source originals, or the canonical unresolved read scope. */
    public interface Authority {
        void verifyCurrent(PlanningReadRequest actual,Arguments arguments);
        void verifyOriginal(PlanningReadReceipt original,Arguments arguments);
    }
    private final ReadContract<Observation> preparation,observation;
    private final Authority authority;
    public FamilyMarriageSendReads(ExactRef actualNativeProducer,Authority actualAuthority) {
        original(actualNativeProducer);authority=Objects.requireNonNull(actualAuthority);
        preparation=contract(actualNativeProducer,Scope.ACTION_PREPARATION,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        observation=contract(actualNativeProducer,Scope.POST_SUBMISSION,ReadContract.GuardMode.RECONCILIATION_OBSERVATION);
    }
    public ReadContract<Observation> preparationContract(){return preparation;}
    public ReadContract<Observation> observationContract(){return observation;}
    public List<ReadContract<Observation>> contracts(){return List.of(preparation,observation);}
    private static String contractId(Scope scope) {
        return "family:marriage-send-outgoing:"+scope.name().toLowerCase(java.util.Locale.ROOT)+"/v2";
    }
    private ReadContract<Observation> contract(ExactRef source,Scope scope,ReadContract.GuardMode guard) {
        return new ReadContract<>(contractId(scope),
                new OperationKey(STEP),Optional.empty(),PERMISSION,ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP,guard,source,(request,requestId)->{
                    Arguments args=arguments(request.arguments());need(args.scope()==scope,"read contract changed narrow preparation/observation scope");
                    requireOrigin(request,args);authority.verifyCurrent(request,args);
                    return new NativeRequest(STEP,Optional.empty(),nativeFields(args));
                },receipt->decode(receipt,scope),receipt->decode(receipt,scope));
    }
    public static Sender sender(ActionCommand command) {
        need(command.origin() instanceof CommandOrigin.Gameplay,"original marriage send must retain its real gameplay origin");
        Sender sender=sender(command.arguments(),command.operation().value());
        need(sender.actor()==command.before().frame().identity().player().longValueExact(),"sender differs from original played actor");return sender;
    }
    public static Sender sender(Obj original,String step) {
        JsonNode node=DriverJson.toNode(original);String schema=StrictJson.text(node.get("schema"));
        if(schema.equals(FamilyMarriageIntent.SCHEMA)) {
            var value=FamilyMarriageIntent.fromJson(original);need(value.step().equals(step),"private family sender changed actual primitive");
            Route route=Route.valueOf(value.route().name());
            // The original first-heir and fulfillment submissions preserve their
            // default context bank. Only the two child routes invoke the setter.
            return new Sender(route,value.actorId(),value.subjectId(),value.candidateId(),OptionalLong.of(value.recipientId()),
                    route==Route.CHILD_MATRILINEAL,route==Route.CHILD_DEFAULT);
        }
        var value=RulerMarriageIntent.fromJson(original);need(value.step().equals(step),"ruler sender changed actual canonical pair step");
        return new Sender(Route.RULER,value.actorId(),value.actorId(),value.candidateId(),OptionalLong.empty(),false,false);
    }
    public static Obj preparationArguments(ActionCommand command,String requestId,FreshBasis actualOriginals) {
        sender(command);return encode(new Arguments(Scope.ACTION_PREPARATION,command.actionId(),ActionCodec.bodySha256(command),requestId,
                command.arguments(),Optional.of(actualOriginals),Optional.empty(),OptionalLong.empty()));
    }
    public static Obj observationArguments(ActionCommand command,ActionState.Attempt attempt,ExactRef actualBeforeRead,long actualMaterializedSender) {
        sender(command);return encode(new Arguments(Scope.POST_SUBMISSION,command.actionId(),ActionCodec.bodySha256(command),attempt.requestId(),
                command.arguments(),Optional.empty(),Optional.of(actualBeforeRead),OptionalLong.of(actualMaterializedSender)));
    }
    public static Obj encode(Arguments a) {
        var n=StrictJson.object().put("schema",ARGUMENT_SCHEMA).put("scope",a.scope().name()).put("action_id",a.actionId())
                .put("command_body_sha256",a.bodySha256()).put("attempt_request_id",a.attemptRequestId());n.set("sender_intent",DriverJson.toNode(a.senderIntent()));
        if(a.freshBasis().isPresent()) {var b=a.freshBasis().orElseThrow();var value=n.putObject("fresh_basis");value.set("snapshot",b.snapshot().toJson());value.set("bridge",b.bridge().toJson());
            var refs=value.putArray("reads");b.reads().forEach(ref->refs.add(ref.toJson()));}else n.putNull("fresh_basis");
        if(a.beforeRead().isPresent())n.set("before_read",a.beforeRead().orElseThrow().toJson());else n.putNull("before_read");
        if(a.senderCharacterId().isPresent())n.put("sender_character_id",a.senderCharacterId().getAsLong());else n.putNull("sender_character_id");return app(n);
    }
    public static Arguments arguments(Obj original) {
        JsonNode n=DriverJson.toNode(original);StrictJson.object(n,Set.of("schema","scope","action_id","command_body_sha256","attempt_request_id","sender_intent","fresh_basis","before_read","sender_character_id"));
        text(n,"schema",ARGUMENT_SCHEMA);Scope scope=Scope.valueOf(StrictJson.text(n.get("scope")));Optional<FreshBasis> basis=Optional.empty();
        JsonNode b=n.get("fresh_basis");
        if(!b.isNull()) {StrictJson.object(b,Set.of("snapshot","bridge","reads"));JsonNode reads=b.get("reads");need(reads.isArray()&&!reads.isEmpty()&&reads.size()<=32,"actual fresh read original list required");
            var refs=new java.util.ArrayList<ExactRef>();for(JsonNode ref:reads)refs.add(ExactRef.fromJson(ref));basis=Optional.of(new FreshBasis(ExactRef.fromJson(b.get("snapshot")),ExactRef.fromJson(b.get("bridge")),refs));}
        JsonNode intent=n.get("sender_intent");need(intent.isObject(),"actual original sender intent required");
        return new Arguments(scope,StrictJson.text(n.get("action_id")),StrictJson.text(n.get("command_body_sha256")),StrictJson.text(n.get("attempt_request_id")),
                app(intent),basis,n.get("before_read").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(n.get("before_read"))),n.get("sender_character_id").isNull()?OptionalLong.empty():OptionalLong.of(StrictJson.integer(n.get("sender_character_id"),1,0xFFFF_FFFEL)));
    }
    public static RawJson nativeFields(Arguments a) {
        String step=sourceStep(a.senderIntent());
        Sender sender=sender(a.senderIntent(),step);
        var n=StrictJson.object().put("read_scope",a.scope().name()).put("source_action_step",step).put("actor_character_id",sender.actor())
                .put("subject_character_id",sender.subject()).put("candidate_character_id",sender.candidate())
                .put("request_matrilineal_option",sender.requestMatrilineal()).put("require_matrilineal_option_off",sender.requireMatrilinealOff());
        if(sender.recipient().isPresent())n.put("expected_recipient_character_id",sender.recipient().getAsLong());else n.putNull("expected_recipient_character_id");
        if(a.senderCharacterId().isPresent())n.put("sender_character_id",a.senderCharacterId().getAsLong());else n.putNull("sender_character_id");
        return new RawJson(DriverJson.encode(app(n)));
    }
    private static String sourceStep(Obj intent) {
        return StrictJson.text(DriverJson.toNode(intent).get("schema")).equals(FamilyMarriageIntent.SCHEMA)
                ?FamilyMarriageIntent.fromJson(intent).step():RulerMarriageIntent.fromJson(intent).step();
    }
    private Observation decode(PlanningReadReceipt receipt,Scope scope) {
        Arguments args=arguments(receipt.request().arguments());need(args.scope()==scope,"original outgoing narrow scope changed");requireOrigin(receipt.request(),args);
        authority.verifyOriginal(receipt,args);return decodeOriginal(receipt,scope);
    }
    /** Pure domain replay after the unique Root authority has qualified its actual original source. */
    private static Observation decodeOriginal(PlanningReadReceipt receipt,Scope scope) {
        Arguments args=arguments(receipt.request().arguments());need(args.scope()==scope,"original outgoing narrow scope changed");requireOrigin(receipt.request(),args);
        need(receipt.contractId().equals(contractId(scope)),"original outgoing receipt is not the fixed installed narrow contract");requirePacket(receipt);
        var request=receipt.request();ObservationIdentity identity=identity(request);
        for(var guard:List.of(receipt.before(),receipt.after())) {
            need(guard.guardMode()==(scope==Scope.ACTION_PREPARATION?ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP:ReadContract.GuardMode.RECONCILIATION_OBSERVATION),"actual outgoing guard profile differs");
            need(request.origin().acceptsGuard(guard.binding().origin())
                &&guard.binding().source().equals(request.source())&&guard.binding().sessionId().equals(request.sessionId())&&guard.binding().operation().equals(request.operation())
                ,"actual outgoing read changed guarded origin/frame/source");
            if(scope==Scope.ACTION_PREPARATION)need(guard.paused()&&guard.mapReady()&&guard.playerAlive(),"actual preparation requires qualified ordinary controls");
        }
        need(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),"actual outgoing read crossed its full native/Driver binding");
        JsonNode n=DriverJson.toNode(DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES));
        return decodePayload(n,scope,frame(identity,BigInteger.ONE),args.senderCharacterId(),sender(args.senderIntent(),sourceStep(args.senderIntent())).route());
    }
    /** One strict complete wire boundary, shared by installed replay and retained sender extraction. DATA only. */
    static Observation decodePayload(JsonNode n,Scope scope,Frame originalFrame,OptionalLong senderFilter,Route route) {
        Objects.requireNonNull(scope);Objects.requireNonNull(originalFrame);Objects.requireNonNull(senderFilter);Objects.requireNonNull(route);
        need((scope==Scope.POST_SUBMISSION)==senderFilter.isPresent(),"only post-submission has its original materialized sender filter");
        senderFilter.ifPresent(FamilyMarriageSendReads::character);
        StrictJson.object(n,Set.of("schema","step","accepted","status","private_build","read_only","advertised","backend_id","query_sequence","snapshot_revision","date_raw","played_character_id","read_scope","prepared_context",FamilyOutgoingCodec.GROUP));
        text(n,"schema",WIRE_SCHEMA);text(n,"step",STEP);yes(n,"accepted");yes(n,"private_build");yes(n,"read_only");no(n,"advertised");text(n,"backend_id","native-headless");text(n,"read_scope",scope.name());
        StrictJson.integer(n.get("snapshot_revision"),originalFrame.revision(),originalFrame.revision());
        StrictJson.integer(n.get("date_raw"),originalFrame.date(),originalFrame.date());
        StrictJson.integer(n.get("played_character_id"),originalFrame.actor(),originalFrame.actor());
        Frame frame=new Frame(originalFrame.revision(),originalFrame.date(),originalFrame.actor(),originalFrame.build(),
                StrictJson.integer(n.get("query_sequence"),BigInteger.ONE,StrictJson.UINT64_MAX));
        var storage=FamilyOutgoingCodec.decodeGroup(n.get(FamilyOutgoingCodec.GROUP),frame,FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE);
        text(n,"status",storage.complete()?"available":"unavailable");
        JsonNode prepared=n.get("prepared_context");Optional<Materialized> material=Optional.empty();
        if(scope==Scope.ACTION_PREPARATION)material=Optional.of(prepared(prepared));else need(prepared.isNull(),"after observation must not fabricate a fresh canSend context");
        if(material.orElse(null) instanceof Prepared p)need((route==Route.RULER)==p.effectiveMatrilineal().isEmpty(),"actual public/default-context and private/final-terms effective lineality scopes differ");
        if(material.orElse(null) instanceof Prepared p && storage.complete())need(p.definitionHash()==storage.definitionHash().orElseThrow()&&p.roles().actor()==storage.senderCharacterId().orElseThrow(),"prepared/source storage definition or actual materialized sender differs");
        if(scope==Scope.POST_SUBMISSION&&storage.complete())need(storage.senderCharacterId().orElseThrow()==senderFilter.orElseThrow(),"actual storage sender differs from retained before filter");
        return new Observation(scope,frame,material,storage);
    }
    public static Materialized prepared(JsonNode n) {
        StrictJson.object(n,Set.of("schema","status","source","read_only","send_invoked","command_constructed","role_arity","sixth_role_id",
                "definition_stable_hash","interaction_key","complete_can_send","matrilineal_option_selected","grand_wedding_option_selected","effective_matrilineal_if_accepted","effective_roles","selected_option_rows","copy_passes","unavailable_reason"));
        text(n,"schema",PREPARED_SCHEMA);text(n,"source","original_native_marriage_context_builder");
        yes(n,"read_only");no(n,"send_invoked");no(n,"command_constructed");text(n,"interaction_key",FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE.interactionKey());
        need(n.get("sixth_role_id").isNull(),"actual unsupported sixth role cannot be hidden");
        boolean available=StrictJson.text(n.get("status")).equals("available");
        if(!available) {
            text(n,"status","unavailable");
            for(String key:List.of("role_arity","definition_stable_hash","complete_can_send","matrilineal_option_selected","grand_wedding_option_selected","effective_matrilineal_if_accepted","effective_roles"))need(n.get(key).isNull(),"unavailable local context invented native material");
            need(n.get("selected_option_rows").isArray()&&n.get("selected_option_rows").isEmpty(),"unavailable local options must be explicit empty");StrictJson.integer(n.get("copy_passes"),0,0);
            return new NotPrepared(StrictJson.text(n.get("unavailable_reason")));
        }
        StrictJson.integer(n.get("role_arity"),5,5);StrictJson.integer(n.get("copy_passes"),2,2);need(n.get("unavailable_reason").isNull(),"available native local context retains an unavailable reason");
        return new Prepared(StrictJson.integer(n.get("definition_stable_hash"),0,0xFFFF_FFFFL),FamilyOutgoingCodec.roles(n.get("effective_roles")),
                FamilyOutgoingCodec.options(n.get("selected_option_rows")),bool(n.get("complete_can_send")),bool(n.get("matrilineal_option_selected")),bool(n.get("grand_wedding_option_selected")),
                n.get("effective_matrilineal_if_accepted").isNull()?Optional.empty():Optional.of(bool(n.get("effective_matrilineal_if_accepted"))));
    }
    private static void requireOrigin(PlanningReadRequest request,Arguments a) {
        need(request.operation().value().equals(STEP),"actual registered outgoing operation required");
        if(a.scope()==Scope.ACTION_PREPARATION)need(request.origin() instanceof CommandOrigin.Gameplay,"before preparation requires actual qualified gameplay origin");
        else {
            var pending=request.origin().requireReconciliation().pending();
            need(pending.actionId().equals(a.actionId())&&pending.bodySha256().equals(a.bodySha256())&&pending.requestId().equals(a.attemptRequestId()),"after observation differs from its actual canonical unresolved primitive");
        }
    }
    private static void requirePacket(PlanningReadReceipt read) {
        need(read.original().nativeOk()&&!read.requestId().equals(arguments(read.request().arguments()).attemptRequestId()),"independent actual successful outgoing query required");
        var custody=read.original().custody().orElseThrow(()->new IllegalArgumentException("actual query request chronology required"));custody.verify(read);
        try {
            var decoded=NativeWire.decode(read.original().originalPacket());need(decoded instanceof NativeWire.CommandResult,"actual outgoing response packet type differs");var result=(NativeWire.CommandResult)decoded;
            need(result.requestId().equals(read.requestId())&&result.nativeOk()&&java.util.Arrays.equals(result.payload().value(),read.original().originalFrame().bytes())
                    &&result.result().token().map(NativeWire.Bytes::value).map(RawJson::new).equals(read.original().originalResultToken()),"actual outgoing response envelope/token differs");
            var outgoing=NativeWire.decodeExecuteRequest(read.original().outbound().orElseThrow().originalPacket());
            need(outgoing.requestId().equals(read.requestId())&&outgoing.step().equals(STEP)&&outgoing.expectedRevision().equals(Optional.of(identity(read.request()).frame().identity().nativeRevision()))
                    &&outgoing.expectedSnapshotRevision().isEmpty()&&StrictJson.parse(outgoing.normalizedAdditionalFields().value()).equals(StrictJson.parse(nativeFields(arguments(read.request().arguments())).bytes())),"actual outgoing request packet differs from source-qualified native fields");
        } catch(IOException failure){throw new UncheckedIOException("original outgoing native query packet unreadable",failure);}
    }
    /** The entire original wire/guards/storage is replayed; Root independently verifies actual source and canonical custody. */
    public static long materializedSender(PlanningReadReceipt before) {
        Observation original=decodeOriginal(before,Scope.ACTION_PREPARATION);
        need(original.outgoing().complete(),"original complete before outgoing storage unavailable");
        Materialized value=original.prepared().orElseThrow();need(value instanceof Prepared,"original native materialized sender unavailable");
        return ((Prepared)value).roles().actor();
    }
    public static ObservationIdentity identity(PlanningReadRequest request) {
        return request.origin() instanceof CommandOrigin.Gameplay?request.before():request.origin().requireReconciliation().factual();
    }
    public static Frame frame(ObservationIdentity identity,BigInteger sequence) {
        return new Frame(identity.frame().identity().nativeRevision(),identity.frame().identity().dateRaw(),identity.frame().identity().player(),Build.CROZIER4,sequence);
    }
    private static Obj app(JsonNode n){return DriverJson.object(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    private static boolean bool(JsonNode n){need(n!=null&&n.isBoolean(),"actual JSON boolean required");return n.booleanValue();}
    private static void yes(JsonNode n,String key){need(bool(n.get(key)),"actual true required: "+key);}
    private static void no(JsonNode n,String key){need(!bool(n.get(key)),"actual false required: "+key);}
    private static void text(JsonNode n,String key,String value){need(value.equals(StrictJson.text(n.get(key))),"actual outgoing field differs: "+key);}
    private static void original(ExactRef r){Objects.requireNonNull(r);need(r.bytes()>0,"nonempty actual original required");}
    private static void character(long value){need(value>0&&value<0xFFFF_FFFFL,"full native character ID required");}
    private static void u32(long value){need(value>=0&&value<=0xFFFF_FFFFL,"full native uint32 required");}
    private static void need(boolean condition,String message){StrictJson.require(condition,message);}
}


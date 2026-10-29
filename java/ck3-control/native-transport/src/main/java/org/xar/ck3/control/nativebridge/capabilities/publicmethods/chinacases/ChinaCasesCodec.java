package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.HexFormat;
import java.nio.charset.StandardCharsets;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.util.Locale;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesActions.ScoreboardAction;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesFacade;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.Frame;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.IncidentProfile;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases.ChinaCasesContract.*;
import static org.xar.ck3.control.contracts.PublicUnsigned64.Minimum.*;
import static org.xar.ck3.control.contracts.PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL;

/** Strict public JSON boundary; native numeric originals are never rewritten in retained receipts. */
public final class ChinaCasesCodec {
    private ChinaCasesCodec() { }
    private static final String OLD_VERSION="1.19.0.6";
    private static final String OLD_EXE="2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
    private static final ObjectMapper JSON=new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(RawJson.MAXIMUM_BYTES).maxNumberLength(4300).maxNestingDepth(1000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    public static ReadRequest decodeRead(Method method,ObjectNode input) {
        StrictJson.require(method.readOnly(),"query method required");
        Set<String> required=new HashSet<>(Set.of("request_nonce"));
        Set<String> optional=new HashSet<>();
        if(method==Method.AI_OWNED) optional.add("expected_revision"); else required.add("expected_revision");
        switch(method) {
            case CASE -> { required.add("case_kind"); optional.add("subject_character_id"); optional.add("owner_character_id"); }
            case AI_OWNED -> { required.add("owner_character_id"); required.add("subject_character_id"); }
            case RESULT,PIP -> required.add("owner_character_id");
            case PROJECTS -> { required.add("owner_character_id"); optional.add("subject_character_id"); }
            case INCIDENT -> { required.add("owner_character_id"); required.add("profile"); }
            default -> { }
        }
        fields(input,required,optional);
        if(method==Method.CASE) require(text(input.get("case_kind")).equals("zhongguo.b1.performance"),"case_kind is not allowlisted");
        var expected=PublicUnsigned64.read(input,"expected_revision",ZERO,SAFE_INTEGER_OR_DECIMAL);
        Optional<IncidentProfile> profile=Optional.empty();
        if(method==Method.INCIDENT) {
            String token=text(input.get("profile")); require(Set.of("x","y","z").contains(token),"profile must be x, y or z");
            profile=Optional.of(IncidentProfile.valueOf(token.toUpperCase(Locale.ROOT)));
        }
        return new ReadRequest(method,text(input.get("request_nonce")),expected,optionalCharacter(input,"owner_character_id"),optionalCharacter(input,"subject_character_id"),profile);
    }
    public static ObjectNode encodeReadRequest(ReadRequest request) {
        ObjectNode n=StrictJson.object(); n.put("request_nonce",request.requestNonce());
        putExpected(n,request.expectedRevision());
        request.ownerCharacterId().ifPresent(id->n.put("owner_character_id",id)); request.subjectCharacterId().ifPresent(id->n.put("subject_character_id",id));
        request.profile().ifPresent(profile->n.put("profile",profile.name().toLowerCase(Locale.ROOT)));
        if(request.method()==Method.CASE)n.put("case_kind","zhongguo.b1.performance"); return n;
    }
    private static void putExpected(ObjectNode n,PublicUnsigned64.Field field) {
        if(field instanceof PublicUnsigned64.Value value)n.put("expected_revision",PublicUnsigned64.canonical(value.value(),ZERO));
        else if(field instanceof PublicUnsigned64.NullValue)n.putNull("expected_revision");
    }
    public static ActionRequest decodeAction(ObjectNode n) {
        StrictJson.object(n,Set.of("request_nonce","action","expected_revision","expected_native_revision","expected_connection_generation",
                "expected_player_character_id","expected_provider_session_id","expected_observation_sequence","expected_observed_state_revision",
                "expected_tree_fingerprint_v1","expected_semantic_fingerprint_v1","expected_window_instance_pointer","expected_target_instance_pointer","expected_target_vtable_pointer"));
        String action=text(n.get("action")); ScoreboardAction selected=null;
        for(ScoreboardAction candidate:ScoreboardAction.values())if(candidate.wire().equals(action))selected=candidate;
        require(selected!=null,"action is not allowlisted");
        return new ActionRequest(text(n.get("request_nonce")),selected,publicInteger(n,"expected_revision",ZERO),publicInteger(n,"expected_native_revision",ONE),
                publicInteger(n,"expected_connection_generation",ONE),characterToken(n.get("expected_player_character_id")),text(n.get("expected_provider_session_id")),
                publicInteger(n,"expected_observation_sequence",ONE),publicInteger(n,"expected_observed_state_revision",ONE),text(n.get("expected_tree_fingerprint_v1")),
                text(n.get("expected_semantic_fingerprint_v1")),text(n.get("expected_window_instance_pointer")),text(n.get("expected_target_instance_pointer")),text(n.get("expected_target_vtable_pointer")));
    }
    public static ObjectNode encodeActionRequest(ActionRequest r) {
        ObjectNode n=StrictJson.object(); n.put("request_nonce",r.requestNonce());n.put("action",r.action().wire());
        n.put("expected_revision",PublicUnsigned64.canonical(r.expectedRevision(),ZERO));n.put("expected_native_revision",PublicUnsigned64.canonical(r.expectedNativeRevision(),ONE));
        n.put("expected_connection_generation",PublicUnsigned64.canonical(r.expectedConnectionGeneration(),ONE));n.put("expected_player_character_id",r.expectedPlayerCharacterId());
        n.put("expected_provider_session_id",r.expectedProviderSessionId());n.put("expected_observation_sequence",PublicUnsigned64.canonical(r.expectedObservationSequence(),ONE));
        n.put("expected_observed_state_revision",PublicUnsigned64.canonical(r.expectedObservedStateRevision(),ONE));n.put("expected_tree_fingerprint_v1",r.expectedTreeFingerprintV1());
        n.put("expected_semantic_fingerprint_v1",r.expectedSemanticFingerprintV1());n.put("expected_window_instance_pointer",r.expectedWindowInstancePointer());
        n.put("expected_target_instance_pointer",r.expectedTargetInstancePointer());n.put("expected_target_vtable_pointer",r.expectedTargetVtablePointer()); return n;
    }
    public static Frame decodeOriginal(Method method,PlanningReadReceipt receipt) {
        return switch(method) {
            case B1 -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeB1Frame(receipt);
            case CASE -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeCaseFrame(receipt);
            case AI_OWNED -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeAiOwnedFrame(receipt);
            case RESULT -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeResultFrame(receipt);
            case PIP -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodePipFrame(receipt);
            case PROMOTION -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodePromotionFrame(receipt);
            case AF5 -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeAf5Frame(receipt);
            case PROJECTS -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeProjectsFrame(receipt);
            case INCIDENT -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeIncidentFrame(receipt);
            case SCOREBOARD -> org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.decodeScoreboardFrame(receipt);
            case ACTIVATE_SCOREBOARD -> throw new IllegalArgumentException("activation is not a frame decoder");
        };
    }
    static ChinaCasesService.ReadResponse render(ReadRequest request,ChinaCasesService.Context context,PlanningReadReceipt receipt,Frame original) {
        require(decodeOriginal(request.method(),receipt).equals(original),"original family projection changed");
        ObjectNode envelope=parse(receipt.original().originalResultToken().orElseThrow());
        ObjectNode payload=object(envelope.get(request.method().payload())).deepCopy();
        var c=context.query(); var frame=c.before().frame(); var id=frame.identity();
        String version=OLD_VERSION,exe=OLD_EXE;
        ObjectNode provenance=payload.get("provenance") instanceof ObjectNode p?p:null;
        if(provenance!=null && provenance.has("game_version")) { version=text(provenance.get("game_version"));exe=text(provenance.get("executable_sha256")); }
        require(version.equals(context.gameVersion()) && exe.equalsIgnoreCase(context.executableSha256()),"actual hello build differs from original China contract provenance");
        ObjectNode build=StrictJson.object();build.put("version",version);build.put("exe_sha256",exe);payload.set("build",build);
        String backend=text(envelope.get("backend_id")); BigInteger sequence=org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.querySequence(receipt,request.method().family());
        ObjectNode source=source(c,backend); ObjectNode binding=sourceBinding(c);binding.put("request_nonce",request.requestNonce());
        binding.put("expected_revision",ChinaCasesService.requireExpected(request,c));
        if(request.method()==Method.B1) {
            if(!(original instanceof org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.B1Frame b1))throw new IllegalArgumentException("B1 original frame required");
            var derived=ChinaCasesService.deriveB1(b1);
            payload.set("invariants",encodeB1Invariants(derived.invariants()));var anomalies=JSON.createArrayNode();derived.anomalies().forEach(a->anomalies.add(a.wire()));payload.set("anomalies",anomalies);
            payload.put("query_sequence",sequence);payload.set("bridge_source",source);binding.remove(java.util.List.of("snapshot_id","revision","native_revision","connection_generation","date_raw","paused","player_character_id"));
            binding.put("manager_character_id",id.player());
        } else {
            source.put("bridge_version",context.bridgeVersion());source.put("game_adapter_id",context.gameAdapterId());
            if(Set.of(Method.CASE,Method.AI_OWNED,Method.RESULT,Method.PIP,Method.INCIDENT,Method.SCOREBOARD).contains(request.method()))
                source.put("consumer_id",text(object(payload.get("provenance")).get("consumer_id")));
            if(request.method()==Method.SCOREBOARD)source.put("query_sequence",sequence);
            payload.set("source",source);
            switch(request.method()) {
                case CASE -> { binding.put("subject_character_id",request.subjectCharacterId().orElse(id.player().intValueExact())); putActualOwner(binding,payload,"case"); }
                case AI_OWNED -> { binding.put("subject_character_id",request.subjectCharacterId().orElseThrow());binding.put("owner_character_id",request.ownerCharacterId().orElseThrow()); }
                case RESULT -> { binding.put("subject_character_id",id.player());putActualOwner(binding,payload,"case"); }
                case PIP -> { binding.put("subject_character_id",id.player());putActualOwner(binding,payload,"gate"); }
                case INCIDENT -> { binding.put("subject_character_id",id.player());binding.put("profile",request.profile().orElseThrow().name().toLowerCase(Locale.ROOT));putActualOwner(binding,payload,"probe"); }
                case PROMOTION,AF5 -> { payload.put("source_backend_id","native-headless");binding.set("subject_character_id",payload.get("subject_character_id"));binding.put("owner_character_id",id.player()); }
                case PROJECTS -> { payload.put("source_backend_id","native-headless");binding.put("subject_character_id",request.subjectCharacterId().orElse(id.player().intValueExact()));binding.put("owner_character_id",request.ownerCharacterId().orElseThrow()); }
                default -> { }
            }
        }
        payload.set("binding",binding);publicReadIntegers(payload);return new ChinaCasesService.ReadResponse(request.method(),raw(payload));
    }
    private static void putActualOwner(ObjectNode binding,ObjectNode payload,String group) {
        if(text(payload.get("status")).equals("unavailable")){binding.putNull("owner_character_id");return;}
        ObjectNode owner=object(object(payload.get(group)).get("owner_character_id"));
        require(text(owner.get("status")).equals("available"),"available China frame lacks its actual owner");
        binding.put("owner_character_id",characterToken(owner.get("value")));
    }
    private static ObjectNode source(ChinaCasesFacade.Context c,String backend) { ObjectNode source=sourceBinding(c);source.put("backend_id",backend);return source; }
    private static ObjectNode sourceBinding(ChinaCasesFacade.Context c) {
        var f=c.before().frame();ObjectNode n=StrictJson.object();n.put("snapshot_id",f.snapshotId());n.put("revision",f.revision());n.put("native_revision",f.identity().nativeRevision());
        n.put("connection_generation",c.connectionGeneration());n.put("date_raw",f.identity().dateRaw());n.put("paused",true);n.put("player_character_id",f.identity().player());return n;
    }
    public static ObjectNode encodeReadResult(ChinaCasesService.ReadResponse response) { return parse(response.publicJson()); }
    public static ObjectNode encodeB1Invariants(ChinaCasesService.B1Invariants value) {
        ObjectNode n=StrictJson.object();optionalBoolean(n,"active_matches_state",value.activeMatchesState());optionalBoolean(n,"counts_nonnegative",value.countsNonnegative());
        optionalBoolean(n,"processing_within_roster",value.processingWithinRoster());optionalBoolean(n,"quota_target_conserved",value.quotaTargetConserved());
        optionalBoolean(n,"quota_recount_conserved",value.quotaRecountConserved());optionalBoolean(n,"quota_target_matches_recount",value.quotaTargetMatchesRecount());optionalBoolean(n,"closed_state_coherent",value.closedStateCoherent());return n;
    }
    private static void optionalBoolean(ObjectNode n,String key,Optional<Boolean> value) { if(value.isPresent())n.put(key,value.get());else n.putNull(key); }
    /** Validate roundtrip against the actual retained original, without treating public JSON as a fresh read. */
    public static ChinaCasesService.ReadResponse decodeReadResult(ReadRequest request,ChinaCasesService.Context context,PlanningReadReceipt receipt,RawJson publicJson) {
        var expected=render(request,context,receipt,decodeOriginal(request.method(),receipt));
        require(parse(expected.publicJson()).equals(parse(publicJson)),"public China response differs from its exact original rendering");return new ChinaCasesService.ReadResponse(request.method(),publicJson);
    }

    /** One original transport result. It never proves the scoreboard changed or turns an ACK into PASS. */
    public static RawJson validateActionResult(ActionRequest request,ChinaCasesFacade.Context before,RawJson nativeResult,boolean productionAdvertised) {
        require(before.before().frame().revision().equals(request.expectedRevision())
                && before.before().frame().identity().nativeRevision().equals(request.expectedNativeRevision())
                && before.connectionGeneration().equals(request.expectedConnectionGeneration())
                && before.before().frame().identity().player().equals(BigInteger.valueOf(request.expectedPlayerCharacterId())),"scoreboard source binding is stale");
        ObjectNode n=parse(nativeResult);StrictJson.object(n,Set.of("step","accepted","status","request_nonce","action","action_sequence","snapshot_revision","rejection_reason","action_ack","production_capability_advertised","backend_id"));
        require(text(n.get("step")).equals("activate-zhongguo-scoreboard-v1") && text(n.get("request_nonce")).equals(request.requestNonce()) && text(n.get("action")).equals(request.action().wire()),"scoreboard native action binding drift");
        nativeUnsigned(n.get("action_sequence"),ONE);require(nativeUnsigned(n.get("snapshot_revision"),ONE).equals(request.expectedNativeRevision()),"scoreboard native revision drift");
        StrictJson.text(text(n.get("backend_id")));boolean advertised=bool(n.get("production_capability_advertised"));require(advertised==productionAdvertised,"scoreboard actual capability mirror drift");
        if(!bool(n.get("accepted"))) {
            require(text(n.get("status")).equals("unavailable") && n.get("action_ack").isNull() && !advertised,"scoreboard rejection is malformed");StrictJson.text(text(n.get("rejection_reason")));
        } else {
            require(text(n.get("status")).equals("acknowledged_verification_pending") && n.get("rejection_reason").isNull(),"scoreboard ACK must remain pending");
            validateAck(request,before,object(n.get("action_ack")));
        }
        return nativeResult;
    }
    private static void validateAck(ActionRequest r,ChinaCasesFacade.Context before,ObjectNode a) {
        StrictJson.object(a,Set.of("schema_version","status","accepted","capability","step","request_nonce","action","source","target","expected_postcondition","native_handled","postcondition_verified","provenance"));
        require(integer(a.get("schema_version")).equals(BigInteger.ONE) && text(a.get("status")).equals("acknowledged_verification_pending") && bool(a.get("accepted"))
                && text(a.get("capability")).equals("game.command.activate-zhongguo-scoreboard-v1") && text(a.get("step")).equals("activate-zhongguo-scoreboard-v1")
                && text(a.get("request_nonce")).equals(r.requestNonce()) && text(a.get("action")).equals(r.action().wire()) && !bool(a.get("postcondition_verified")),"scoreboard ACK identity drift");
        bool(a.get("native_handled")); // The original ACK accepts either boolean, never a truthy scalar.
        ObjectNode s=StrictJson.object(a.get("source"),Set.of("revision","native_revision","connection_generation","date_raw","player_character_id","provider_session_id","observation_sequence","observed_state_revision","tree_fingerprint_v1","semantic_fingerprint_v1","window_instance_pointer"));
        require(nativeUnsigned(s.get("revision"),ZERO).equals(r.expectedRevision()) && nativeUnsigned(s.get("native_revision"),ONE).equals(r.expectedNativeRevision())
                && nativeUnsigned(s.get("connection_generation"),ONE).equals(r.expectedConnectionGeneration()) && characterToken(s.get("player_character_id"))==r.expectedPlayerCharacterId()
                && integer(s.get("date_raw")).equals(before.before().frame().identity().dateRaw()) && text(s.get("provider_session_id")).equals(r.expectedProviderSessionId())
                && nativeUnsigned(s.get("observation_sequence"),ONE).equals(r.expectedObservationSequence()) && nativeUnsigned(s.get("observed_state_revision"),ONE).equals(r.expectedObservedStateRevision())
                && text(s.get("tree_fingerprint_v1")).equals(r.expectedTreeFingerprintV1()) && text(s.get("semantic_fingerprint_v1")).equals(r.expectedSemanticFingerprintV1())
                && text(s.get("window_instance_pointer")).equals(r.expectedWindowInstancePointer()),"scoreboard ACK source differs from request");
        ObjectNode t=StrictJson.object(a.get("target"),Set.of("stable_identity","runtime_name","instance_pointer","vtable_pointer"));
        String target=text(t.get("stable_identity"));String action=r.action().wire();String tab;
        if(action.startsWith("switch-")) {tab=action.substring(7);require(target.equals("zg361_scoreboard_tab_"+tab),"scoreboard switch target drift");}
        else if(action.equals("close")){tab=null;require(target.equals("zg361_scoreboard_header_close"),"scoreboard close target drift");}
        else {require(Set.of("zg361_scoreboard_entry_managed","zg361_scoreboard_entry_received","zg361_scoreboard_entry_system").contains(target),"scoreboard open target drift");tab=target.substring("zg361_scoreboard_entry_".length());}
        require(text(t.get("runtime_name")).equals(target) && text(t.get("instance_pointer")).equals(r.expectedTargetInstancePointer()) && text(t.get("vtable_pointer")).equals(r.expectedTargetVtablePointer()),"scoreboard ACK exact target changed");
        ObjectNode p=StrictJson.object(a.get("expected_postcondition"),Set.of("requires_independent_query","minimum_observation_sequence","minimum_observed_state_revision","expected_provider_session_id","expected_tree_fingerprint_v1","modal_effective_visible","active_tab","list_view_required","expected_window_instance_pointer"));
        require(bool(p.get("requires_independent_query")) && integer(p.get("minimum_observation_sequence")).equals(r.expectedObservationSequence().add(BigInteger.ONE))
                && integer(p.get("minimum_observed_state_revision")).equals(r.expectedObservedStateRevision().add(BigInteger.ONE)) && text(p.get("expected_provider_session_id")).equals(r.expectedProviderSessionId())
                && text(p.get("expected_tree_fingerprint_v1")).equals(r.expectedTreeFingerprintV1()) && text(p.get("expected_window_instance_pointer")).equals(r.expectedWindowInstancePointer())
                && (tab==null?p.get("active_tab").isNull():text(p.get("active_tab")).equals(tab)),"scoreboard ACK independent postcondition drift");
        bool(p.get("modal_effective_visible"));bool(p.get("list_view_required"));
        ObjectNode provenance=StrictJson.object(a.get("provenance"),Set.of("game_version","executable_sha256","backend_id","consumer_id","allowlist_id","contract_stage"));
        require(text(provenance.get("game_version")).equals(OLD_VERSION) && text(provenance.get("executable_sha256")).equals(OLD_EXE)
                && text(provenance.get("backend_id")).equals("ck3-1.19.0.6-native-zhongguo-scoreboard-action-v1")
                && text(provenance.get("consumer_id")).equals("xar-autoplayer-zhongguo-scoreboard-action-v1")
                && text(provenance.get("allowlist_id")).equals("zg361-scoreboard-named-widget-action-v1")
                && text(provenance.get("contract_stage")).equals("exact_dispatch_ack_provider_revision_live_unverified"),"scoreboard ACK provenance drift");
    }
    public static ObjectNode encodeActionResult(ActionRequest request,ChinaCasesFacade.Context before,RawJson validatedOriginal) {
        ObjectNode n=parse(validatedOriginal);validateActionResult(request,before,validatedOriginal,bool(n.get("production_capability_advertised")));
        n.put("queried_snapshot_id",before.before().frame().snapshotId());n.put("queried_revision",request.expectedRevision());n.put("queried_native_revision",request.expectedNativeRevision());n.put("queried_connection_generation",request.expectedConnectionGeneration());
        for(String field:Set.of("action_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation"))decimal(n,field);
        if(n.get("action_ack") instanceof ObjectNode a) { ObjectNode source=object(a.get("source"));for(String field:Set.of("revision","native_revision","connection_generation","observation_sequence","observed_state_revision"))decimal(source,field);
            ObjectNode post=object(a.get("expected_postcondition"));for(String field:Set.of("minimum_observation_sequence","minimum_observed_state_revision"))decimal(post,field); }
        return n;
    }

    /** Exact original encoded Cases10 EXECUTE grammar. Selection is DATA, never Native permission. */
    private record Execution(Method method,OpportunityJson.Obj arguments) { }
    public static Optional<Method> executionMethod(OperationKey encoded) {
        return execution(encoded).map(Execution::method);
    }
    public static OpportunityJson.Obj executionArguments(OperationKey encoded,BigInteger actualConnectionGeneration) {
        PublicUnsigned64.canonical(actualConnectionGeneration,ONE);
        Execution selected=execution(encoded).orElseThrow(()->new IllegalArgumentException("unknown or malformed Cases EXECUTE step"));
        return selected.method()==Method.SCOREBOARD
            ?selected.arguments().with("expected_connection_generation",new OpportunityJson.IntegerValue(actualConnectionGeneration))
            :selected.arguments();
    }
    public static OperationKey executionStep(Method method,PlanningReadReceipt original) {
        Objects.requireNonNull(method);Objects.requireNonNull(original);
        require(method.readOnly()&&original.request().operation().value().equals(method.family().step()),"Cases logical operation drift");
        decodeOriginal(method,original);
        ObjectNode args=object(OpportunityJson.toNode(original.request().arguments()));
        String nonce=text(args.get("request_nonce"));ChinaCasesContract.nonce(nonce);
        String encodedNonce=HexFormat.of().formatHex(nonce.getBytes(StandardCharsets.US_ASCII));
        String tail=switch(method) {
            case CASE -> "b1-"+integer(args.get("subject_character_id"))+"-"+integer(args.get("owner_character_id"))+"-"+encodedNonce;
            case AI_OWNED,PROJECTS -> integer(args.get("owner_character_id"))+"-"+integer(args.get("subject_character_id"))+"-"+encodedNonce;
            case RESULT,PIP,PROMOTION,AF5 -> integer(args.get("owner_character_id"))+"-"+encodedNonce;
            case INCIDENT -> integer(args.get("owner_character_id"))+"-"+text(args.get("profile"))+"-"+encodedNonce;
            case B1 -> encodedNonce;
            case SCOREBOARD -> nonce;
            case ACTIVATE_SCOREBOARD -> throw new IllegalArgumentException("scoreboard activation is not a read");
        };
        OperationKey encoded=new OperationKey(method.family().step()+"-"+tail);
        require(executionArguments(encoded,original.before().binding().connectionGeneration()).equals(original.request().arguments()),
            "Cases original arguments do not equal the canonical encoded EXECUTE command");
        return encoded;
    }

    /** The original driver result has seven Native fields plus four queried-frame fields.
     * No MCP build/source/binding additions and no public-number rewriting enter archives/history. */
    public static RawJson encodeNumericExecutionResult(Method method,PlanningReadReceipt original) {
        Objects.requireNonNull(method);Objects.requireNonNull(original);
        Frame decoded=decodeOriginal(method,original);
        require(original.request().operation().value().equals(method.family().step()),"Cases original operation drift");
        ObjectNode envelope=parse(original.original().originalResultToken().orElseThrow()).deepCopy();
        if(method==Method.B1) {
            require(decoded instanceof org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.B1Frame,"B1 original required");
            var derived=ChinaCasesService.deriveB1((org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.B1Frame)decoded);
            ObjectNode payload=object(envelope.get(method.payload()));
            payload.set("invariants",encodeB1Invariants(derived.invariants()));
            var anomalies=JSON.createArrayNode();derived.anomalies().forEach(value->anomalies.add(value.wire()));
            payload.set("anomalies",anomalies);
        }
        var before=original.request().before().frame();
        envelope.put("queried_snapshot_id",before.snapshotId());envelope.put("queried_revision",before.revision());
        envelope.put("queried_native_revision",before.identity().nativeRevision());
        envelope.put("queried_connection_generation",original.before().binding().connectionGeneration());
        return raw(envelope);
    }
    /** Narrow public projection of that SAME numeric original report; no recursive integer conversion. */
    public static RawJson encodeExecutionResult(Method method,PlanningReadReceipt original) {
        ObjectNode result=parse(encodeNumericExecutionResult(method,original));
        publicReadIntegers(object(result.get(method.payload())));
        for(String field:Set.of("query_sequence","snapshot_revision","queried_revision","queried_native_revision","queried_connection_generation"))
            decimal(result,field);
        return raw(result);
    }

    private static Optional<Execution> execution(OperationKey encoded) {
        Objects.requireNonNull(encoded);
        for(Method method:Method.values()) {
            if(!method.readOnly())continue;
            String prefix=method.family().step()+"-";
            if(!encoded.value().startsWith(prefix))continue;
            try {
                String tail=encoded.value().substring(prefix.length());
                ObjectNode args=StrictJson.object();
                String[] parts=tail.split("-",-1);String nonce;
                switch(method) {
                    case SCOREBOARD -> {nonce=tail;ChinaCasesContract.nonce(nonce);}
                    case B1 -> {require(parts.length==1,"B1 tail");nonce=decodeNonce(parts[0]);}
                    case CASE -> {
                        require(parts.length==4&&parts[0].equals("b1"),"case tail");
                        args.put("case_kind","zhongguo.b1.performance");
                        args.put("subject_character_id",stepInteger(parts[1],false,true));
                        args.put("owner_character_id",stepInteger(parts[2],true,true));nonce=decodeNonce(parts[3]);
                    }
                    case AI_OWNED,PROJECTS -> {
                        require(parts.length==3,"owner/subject tail");boolean bounded=method==Method.AI_OWNED;
                        BigInteger owner=stepInteger(parts[0],false,bounded),subject=stepInteger(parts[1],false,bounded);
                        require(!owner.equals(subject),"owner and subject must differ");
                        args.put("owner_character_id",owner);args.put("subject_character_id",subject);nonce=decodeNonce(parts[2]);
                    }
                    case RESULT,PIP,PROMOTION,AF5 -> {
                        require(parts.length==2,"owner tail");
                        args.put("owner_character_id",stepInteger(parts[0],false,method==Method.RESULT||method==Method.PIP));
                        nonce=decodeNonce(parts[1]);
                    }
                    case INCIDENT -> {
                        require(parts.length==3&&Set.of("x","y","z").contains(parts[1]),"incident tail");
                        args.put("owner_character_id",stepInteger(parts[0],false,true));args.put("profile",parts[1]);nonce=decodeNonce(parts[2]);
                    }
                    case ACTIVATE_SCOREBOARD -> throw new IllegalArgumentException("action is not read");
                    default -> throw new IllegalStateException("unhandled exact Cases method");
                }
                args.put("request_nonce",nonce);
                return Optional.of(new Execution(method,OpportunityJson.object(OpportunityJson.parse(raw(args).bytes()),"Cases execution arguments")));
            } catch(IllegalArgumentException malformed) { return Optional.empty(); }
        }
        return Optional.empty();
    }
    private static BigInteger stepInteger(String value,boolean zero,boolean int32) {
        require(value!=null&&value.length()<=4300&&value.matches("0|[1-9][0-9]*"),"canonical decimal Cases ID required");
        BigInteger parsed=new BigInteger(value);
        require(parsed.signum()>0||zero&&parsed.signum()==0,"positive Cases ID required");
        if(int32)require(parsed.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"Cases ID exceeds original signed int32");
        return parsed;
    }
    private static String decodeNonce(String hex) {
        require(hex!=null&&!hex.isEmpty()&&hex.length()<=128&&(hex.length()&1)==0&&hex.matches("[0-9a-f]+"),"canonical lowercase nonce hex required");
        String nonce=new String(HexFormat.of().parseHex(hex),StandardCharsets.US_ASCII);ChinaCasesContract.nonce(nonce);
        require(HexFormat.of().formatHex(nonce.getBytes(StandardCharsets.US_ASCII)).equals(hex),"nonce ASCII roundtrip drift");
        return nonce;
    }

    private static void publicReadIntegers(ObjectNode n) {
        for(String key:Set.of("snapshot_revision","query_sequence","observation_sequence","observed_state_revision"))if(n.has(key))decimal(n,key);
        for(String group:Set.of("source","bridge_source","binding"))if(n.get(group) instanceof ObjectNode o)
            for(String field:Set.of("revision","native_revision","connection_generation","expected_revision","query_sequence"))if(o.has(field))decimal(o,field);
    }
    private static void decimal(ObjectNode n,String field) { n.put(field,PublicUnsigned64.canonical(integer(n.get(field)),ZERO)); }
    private static BigInteger publicInteger(ObjectNode n,String key,PublicUnsigned64.Minimum min) { return PublicUnsigned64.parse(n.get(key),min,SAFE_INTEGER_OR_DECIMAL); }
    private static BigInteger nativeUnsigned(JsonNode n,PublicUnsigned64.Minimum min) { BigInteger value=integer(n);PublicUnsigned64.canonical(value,min);return value; }
    private static OptionalInt optionalCharacter(ObjectNode n,String key) { return !n.has(key)||n.get(key).isNull()?OptionalInt.empty():OptionalInt.of(characterToken(n.get(key))); }
    private static int characterToken(JsonNode n) { BigInteger value=integer(n);require(value.signum()>0 && value.compareTo(BigInteger.valueOf(Integer.MAX_VALUE))<=0,"character ID must be a positive int32");return value.intValueExact(); }
    private static void fields(ObjectNode n,Set<String> required,Set<String> optional) { Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);Set<String> allowed=new HashSet<>(required);allowed.addAll(optional);require(actual.containsAll(required) && allowed.containsAll(actual),"unexpected or missing public China method arguments"); }
    private static ObjectNode object(JsonNode n) { require(n instanceof ObjectNode,"JSON object required");return (ObjectNode)n; }
    private static String text(JsonNode n) { require(n!=null && n.isTextual(),"exact string required");return n.textValue(); }
    private static boolean bool(JsonNode n) { require(n!=null && n.isBoolean(),"exact boolean required");return n.booleanValue(); }
    private static BigInteger integer(JsonNode n) { require(n!=null && n.isIntegralNumber(),"exact integer token required; bool/float/text refused in native originals");return n.bigIntegerValue(); }
    private static void require(boolean condition,String message) { StrictJson.require(condition,message); }
    private static ObjectNode parse(RawJson raw) {
        try { JsonNode n=JSON.readTree(raw.bytes());return object(n); }
        catch(IOException e){throw new IllegalArgumentException("invalid original China JSON",e);}
    }
    private static RawJson raw(ObjectNode n) { try{return new RawJson(JSON.writeValueAsBytes(n));}catch(IOException e){throw new IllegalArgumentException("China JSON encoding failed",e);} }
}

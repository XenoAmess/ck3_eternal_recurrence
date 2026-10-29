package org.xar.ck3.control.service.mcp;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.normalexit.NormalExitProtocol;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** Sole strict public-V2 normal-exit conversion. Validated DATA is never a retained-handle/source permission. */
public final class NormalExitPublicCodec {
    private static final BigInteger U32=new BigInteger("4294967295"),SAFE=BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER);
    public enum ObserveArguments { MISSING,OBJECT }
    public record Query(BigInteger expectedRevision){public Query{positive(expectedRevision);}}
    public record Request(Action action,BigInteger expectedRevision,String contextSignature){
        public Request{Objects.requireNonNull(action);require(action!=Action.QUERY_CONTEXT,"query is not a public mutation");positive(expectedRevision);sha(contextSignature);}
    }
    public enum Kind {
        CONTEXT("ck3-normal-exit-context-result-v1","ck3-normal-exit-context-result-v2"),
        REQUEST("ck3-normal-exit-request-result-v1","ck3-normal-exit-request-result-v2"),
        OBSERVATION("ck3-normal-exit-process-observation-result-v1","ck3-normal-exit-process-observation-result-v2");
        final String memory,wire;Kind(String memory,String wire){this.memory=memory;this.wire=wire;}
        static Kind memory(String schema){for(Kind k:values())if(k.memory.equals(schema))return k;throw new IllegalArgumentException("known normal-exit V1 memory schema required");}
        static Kind wire(String schema){for(Kind k:values())if(k.wire.equals(schema))return k;throw new IllegalArgumentException("public normal-exit V2 schema required");}
    }
    public static final class Result {
        private final Kind kind;private final Action action;private final BigInteger publicRevision,creationFiletime;private final RawJson memory;
        private Result(Kind kind,Action action,BigInteger revision,BigInteger creation,RawJson memory){this.kind=kind;this.action=action;publicRevision=revision;creationFiletime=creation;this.memory=memory;}
        public Kind kind(){return kind;}public Action action(){return action;}public BigInteger publicRevision(){return publicRevision;}
        public BigInteger creationFiletime(){return creationFiletime;}public RawJson memory(){return memory;}
    }
    private NormalExitPublicCodec(){ }
    public static ObserveArguments decodeObserve(PublicBindings.Arguments arguments){
        Objects.requireNonNull(arguments);if(arguments instanceof PublicBindings.Missing)return ObserveArguments.MISSING;
        exact(arguments(arguments),Set.of());return ObserveArguments.OBJECT;
    }
    public static PublicBindings.Arguments encodeObserve(ObserveArguments value){Objects.requireNonNull(value);return value==ObserveArguments.MISSING?new PublicBindings.Missing():PublicBindings.present(raw(StrictJson.object()));}
    public static Query decodeQuery(PublicBindings.Arguments arguments){ObjectNode row=arguments(arguments);exact(row,Set.of("expected_revision"));return new Query(decimal(row.get("expected_revision"),BigInteger.ONE));}
    public static Request decodeRequest(PublicBindings.Arguments arguments){ObjectNode row=arguments(arguments);exact(row,Set.of("action","expected_revision","expected_exit_context_signature"));
        return new Request(Action.parse(text(row,"action")),decimal(row.get("expected_revision"),BigInteger.ONE),text(row,"expected_exit_context_signature"));}
    public static RawJson encodeQuery(Query request){return raw(StrictJson.object().put("expected_revision",request.expectedRevision().toString()));}
    public static RawJson encodeRequest(Request request){return raw(StrictJson.object().put("action",request.action().wire()).put("expected_revision",request.expectedRevision().toString()).put("expected_exit_context_signature",request.contextSignature()));}
    private static ObjectNode arguments(PublicBindings.Arguments arguments){require(arguments instanceof PublicBindings.Value,"closed normal-exit object required; null/missing not accepted here");return obj(StrictJson.parse(((PublicBindings.Value)arguments).original().bytes(),65536));}
    private static final Set<String> TOP=Set.of("schema","action","status","public_revision","native_observation","exit_context_signature","source_inventory_sha256",
            "process_creation_filetime_100ns","claim_consumed","retry_authorized","orderly_exit_verified","autosave_verified","process_observation","process_preconfirm_pin",
            "driver_dispatch_receipt_observed_monotonic_ns","receipt_clock_meaning","snapshot_after_required","reason","observer_retained","confirmation_observed","exit_autosave_disabled_observed",
            "process_exit_observed","typed_normal_exit_observed","exit_code","request_id","claim_path","uses_desktop_input","uses_ocr","native_submission_count","observer_close_receipt_path","observer_close_receipt_error","receipt_path");
    private static final Set<String> COMMON=Set.of("schema","status","public_revision","native_observation","process_creation_filetime_100ns","source_inventory_sha256","claim_consumed","retry_authorized","autosave_verified");
    private static final Set<String> PIN=Set.of("pid","creation_filetime_100ns","retained_handle_token","wait_result","verified_monotonic_ns","observation_clock_domain");
    private static final Set<String> PROCESS=Set.of("pid","creation_filetime_100ns","retained_handle_token","wait_result","wait_state","exit_code","process_identity_verified","process_exit_observed",
            "observed_monotonic_ns","timeout_ms","observation_deadline_reached","observation_clock_domain","errors");
    public static Result fromMemory(RawJson actual){
        ObjectNode row=obj(StrictJson.parse(Objects.requireNonNull(actual).bytes()));Set<String> keys=keys(row);require(TOP.containsAll(keys)&&keys.containsAll(COMMON),"closed public exit memory fields differ");
        if(row.has("reason"))require(row.get("reason").isNull()||row.get("reason").isTextual(),"normal-exit reason must be nullable original text");
        Kind kind=Kind.memory(text(row,"schema"));Action action=kind==Kind.CONTEXT?Action.QUERY_CONTEXT:Action.parse(text(row,"action"));
        BigInteger revision=integer(row,"public_revision",BigInteger.ONE,StrictJson.UINT64_MAX),creation=integer(row,"process_creation_filetime_100ns",BigInteger.ONE,StrictJson.UINT64_MAX);sha(text(row,"source_inventory_sha256"));
        require(!bool(row,"retry_authorized")&&!bool(row,"autosave_verified"),"exit result cannot grant replay/save integrity");
        for(String flag:List.of("uses_desktop_input","uses_ocr","orderly_exit_verified"))if(row.has(flag))require(!bool(row,flag),"unsupported public exit assertion: "+flag);
        if(row.has("native_submission_count"))integer(row,"native_submission_count",BigInteger.ZERO,BigInteger.ONE);
        if(row.hasNonNull("exit_code"))integer(row,"exit_code",BigInteger.ZERO,U32);
        if(kind==Kind.CONTEXT){require(!bool(row,"claim_consumed")&&!bool(row,"orderly_exit_verified"),"context query cannot claim or prove orderly exit");text(row,"exit_context_signature");}
        else {
            require(action!=Action.QUERY_CONTEXT&&bool(row,"claim_consumed"),"request needs an actually consumed mutation phase");
            for(String field:List.of("process_exit_observed","typed_normal_exit_observed"))bool(row,field);
            for(String field:List.of("request_id","claim_path"))text(row,field);
            for(String field:List.of("uses_desktop_input","uses_ocr"))require(!bool(row,field),"desktop input/OCR forbidden");
            integer(row,"native_submission_count",BigInteger.ZERO,kind==Kind.OBSERVATION?BigInteger.ZERO:BigInteger.ONE);
            if(action!=Action.CONFIRM_DESKTOP)require(!bool(row,"process_exit_observed")&&!bool(row,"typed_normal_exit_observed"),"preparation cannot establish process exit");
        }
        Optional<RetainedIdentity> pin=Optional.empty();
        if(action==Action.CONFIRM_DESKTOP){require(!bool(row,"snapshot_after_required"),"terminal result cannot require a final snapshot");ObjectNode p=obj(row.get("process_preconfirm_pin"));exact(p,PIN);
            integer(p,"wait_result",BigInteger.ZERO,U32);integer(p,"verified_monotonic_ns",BigInteger.ZERO,StrictJson.UINT64_MAX);clock(p);
            pin=Optional.of(identity(p));require(pin.orElseThrow().creationFiletime().equals(creation),"result changed original process birth");}
        Optional<Observation> nativeObservation=Optional.empty();JsonNode nativeValue=row.get("native_observation");
        if(!nativeValue.isNull()){ObjectNode n=obj(nativeValue);BigInteger pid=pin.isPresent()?pin.orElseThrow().pid():integer(n,"game_pid",BigInteger.ONE,U32);
            Binding binding=new Binding(integer(n,"native_revision",BigInteger.ONE,StrictJson.UINT64_MAX),integer(n,"played_character_id",BigInteger.ONE,new BigInteger("2147483647")),pid,
                    integer(n,"connection_generation",BigInteger.ONE,StrictJson.UINT64_MAX),creation,text(row,"source_inventory_sha256"));nativeObservation=Optional.of(decodeObservation(n,binding,action));}
        if(action==Action.QUERY_CONTEXT){Observation n=nativeObservation.orElseThrow(()->new IllegalArgumentException("query needs its actual native observation"));
            require(text(row,"exit_context_signature").equals(n.contextSignature()),"query replaced original context signature");}
        if(action!=Action.CONFIRM_DESKTOP){String status=nativeObservation.map(n->n.status().wire()).orElse("dispatch_unknown_claimed");require(status.equals(text(row,"status")),"public/native status differ");}
        else {
            ObjectNode p=obj(row.get("process_observation"));exact(p,PROCESS);var errors=new ArrayList<String>();JsonNode es=p.get("errors");require(es!=null&&es.isArray(),"process errors array required");for(JsonNode e:es){require(e.isTextual(),"process error text required");errors.add(e.textValue());}
            String state=text(p,"wait_state");WaitState wait=switch(state){case "signaled"->WaitState.SIGNALED;case "timeout"->WaitState.TIMEOUT;case "failed"->WaitState.FAILED;default->throw new IllegalArgumentException("known process wait state required");};clock(p);
            OptionalLong code=p.hasNonNull("exit_code")?OptionalLong.of(integer(p,"exit_code",BigInteger.ZERO,U32).longValueExact()):OptionalLong.empty();require(p.has("exit_code"),"process exit_code nullable field required");
            ProcessObservation process=new ProcessObservation(identity(p),integer(p,"wait_result",BigInteger.ZERO,U32).longValueExact(),wait,code,bool(p,"process_identity_verified"),bool(p,"process_exit_observed"),
                    integer(p,"observed_monotonic_ns",BigInteger.ZERO,StrictJson.UINT64_MAX),integer(p,"timeout_ms",BigInteger.ZERO,BigInteger.valueOf(5000)).intValueExact(),bool(p,"observation_deadline_reached"),text(p,"observation_clock_domain"),errors);
            require(row.has("driver_dispatch_receipt_observed_monotonic_ns"),"receipt time nullable field required");Optional<BigInteger> receipt=row.hasNonNull("driver_dispatch_receipt_observed_monotonic_ns")
                    ?Optional.of(integer(row,"driver_dispatch_receipt_observed_monotonic_ns",BigInteger.ZERO,StrictJson.UINT64_MAX)):Optional.empty();
            ObjectNode facts=NormalExitProtocol.classify(nativeObservation,process,receipt,pin.orElseThrow()).json();for(String key:keys(facts)){
                JsonNode expected=facts.get(key),actualField=row.get(key);
                require(expected.isIntegralNumber()?actualField!=null&&actualField.isIntegralNumber()&&expected.bigIntegerValue().equals(actualField.bigIntegerValue()):expected.equals(actualField),
                        "terminal result differs from original same-handle facts: "+key);
            }
            if(kind==Kind.OBSERVATION){require(action==Action.CONFIRM_DESKTOP,"observer is only for original confirmation");bool(row,"observer_retained");}
        }
        if(kind==Kind.OBSERVATION)require(action==Action.CONFIRM_DESKTOP,"observer requires original confirmation");
        ObjectNode wire=transform(row,true);safeJson(wire);return new Result(kind,action,revision,creation,raw(row));
    }
    public static RawJson encode(Result actual){Objects.requireNonNull(actual);ObjectNode memory=obj(StrictJson.parse(actual.memory.bytes()));ObjectNode wire=transform(memory,true);wire.put("schema",actual.kind.wire);safeJson(wire);return raw(wire);}
    public static Result decode(RawJson publicWire,Optional<BigInteger> expectedCreation){
        Objects.requireNonNull(expectedCreation);ObjectNode wire=obj(StrictJson.parse(publicWire.bytes()));safeJson(wire);Kind kind=Kind.wire(text(wire,"schema"));wire.put("schema",kind.memory);
        Result actual=fromMemory(raw(transform(wire,false)));expectedCreation.ifPresent(value->{positive(value);require(value.equals(actual.creationFiletime()),"public result belongs to another process birth");});return actual;
    }
    private static ObjectNode transform(ObjectNode original,boolean encode){
        ObjectNode row=original.deepCopy();role(row,"public_revision",encode,BigInteger.ONE,false);role(row,"process_creation_filetime_100ns",encode,BigInteger.ONE,false);
        if(row.hasNonNull("native_observation")){ObjectNode n=obj(row.get("native_observation"));require((encode?NormalExitProtocol.NATIVE_SCHEMA:"ck3-normal-exit-map-v2").equals(text(n,"schema")),"native schema/wire representation differs");n.put("schema",encode?"ck3-normal-exit-map-v2":NormalExitProtocol.NATIVE_SCHEMA);
            for(String k:List.of("native_revision","connection_generation","process_creation_filetime_100ns"))role(n,k,encode,BigInteger.ONE,false);role(n,"pump_epoch",encode,BigInteger.ZERO,false);
            JsonNode targets=n.get("targets");require(targets!=null&&targets.isArray(),"native targets required");for(JsonNode t:targets)role(obj(t),"target_vtable_rva",encode,BigInteger.ZERO,false);}
        if(row.has("driver_dispatch_receipt_observed_monotonic_ns"))role(row,"driver_dispatch_receipt_observed_monotonic_ns",encode,BigInteger.ZERO,true);
        for(String name:List.of("process_preconfirm_pin","process_observation"))if(row.has(name)){ObjectNode p=obj(row.get(name));role(p,"creation_filetime_100ns",encode,BigInteger.ONE,false);role(p,name.equals("process_preconfirm_pin")?"verified_monotonic_ns":"observed_monotonic_ns",encode,BigInteger.ZERO,false);}
        return row;
    }
    private static void role(ObjectNode row,String key,boolean encode,BigInteger min,boolean nullable){require(row.has(key),"missing uint64 role: "+key);if(nullable&&row.get(key).isNull())return;
        if(encode)row.put(key,integer(row,key,min,StrictJson.UINT64_MAX).toString());else row.put(key,decimal(row.get(key),min));}
    private static BigInteger decimal(JsonNode value,BigInteger min){require(value!=null&&value.isTextual(),"canonical uint64 STRING required");BigInteger result=new BigInteger(new CrossJsDecimalUInt64(value.textValue()).decimal());require(result.compareTo(min)>=0,"public uint64 role below minimum");return result;}
    private static RetainedIdentity identity(ObjectNode row){return new RetainedIdentity(integer(row,"pid",BigInteger.ONE,U32),integer(row,"creation_filetime_100ns",BigInteger.ONE,StrictJson.UINT64_MAX),text(row,"retained_handle_token"));}
    private static void clock(ObjectNode row){require("driver_monotonic_v1".equals(text(row,"observation_clock_domain")),"foreign process clock domain");}
    private static Set<String> keys(ObjectNode row){var result=new java.util.HashSet<String>();row.fieldNames().forEachRemaining(result::add);return Set.copyOf(result);}
    private static void safeJson(JsonNode value){require(value!=null,"missing JSON value");if(value.isIntegralNumber()){BigInteger n=value.bigIntegerValue();require(n.compareTo(SAFE.negate())>=0&&n.compareTo(SAFE)<=0,"unlisted JSON number exceeds safe integer domain");}
        else if(value.isArray()||value.isObject())value.forEach(NormalExitPublicCodec::safeJson);else require(value.isTextual()||value.isBoolean()||value.isNull(),"float/non-JSON normal-exit value forbidden");}
    private static void positive(BigInteger value){require(value!=null&&value.signum()>0&&value.compareTo(StrictJson.UINT64_MAX)<=0,"positive uint64 public revision required");}
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
}

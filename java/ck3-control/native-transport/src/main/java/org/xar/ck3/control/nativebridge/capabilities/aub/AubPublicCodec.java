package org.xar.ck3.control.nativebridge.capabilities.aub;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;

/** Sole AUB public projection. Original numeric native tokens and archived packets remain unchanged. */
public final class AubPublicCodec {
    private AubPublicCodec() { }
    public enum Operation { BUSINESS, OPTIONS, SELECT, CONFIRM }
    private static final BigInteger SAFE=new BigInteger("9007199254740991");
    private static final BigInteger U32=new BigInteger("4294967295"),I32=BigInteger.valueOf(Integer.MAX_VALUE),I32_MIN=BigInteger.valueOf(Integer.MIN_VALUE);
    private static final Set<String> METADATA=Set.of("episode_run_id","queried_revision","uses_mouse","uses_keyboard","uses_ocr","full_product_acceptance_credit");
    private static final Set<String> RESULT=Set.of("later_actual_observation","independent_postcondition_verified","action_request_id","canonical_action_id","canonical_claim_authority","native_ack");
    public static RawJson business(AubBusinessStateRead.State value) {
        Objects.requireNonNull(value);
        try {
            var checked=AubBusinessStateRead.decodeMaterial(value.original(),value.before(),value.connectionGeneration());
            need(checked.flags().equals(value.flags())&&checked.detail().equals(value.detail()),"AUB typed business disagrees with its original token");
            ObjectNode row=object(value.original());stamp(row,value.before(),value.connectionGeneration());metadata(row,value.before());
            return output(Operation.BUSINESS,row);
        } catch(IOException invalid) {throw new UncheckedIOException("original AUB business public projection unavailable",invalid);}
    }
    public static RawJson options(Options value) {
        Objects.requireNonNull(value);
        try {
            var checked=AubOperations.options(value.original(),value.before(),value.connectionGeneration());
            need(checked.policy().equals(value.policy()),"AUB typed policy disagrees with its original token");
            ObjectNode row=object(value.original());optionsNative(row,value.before(),value.connectionGeneration());metadata(row,value.before());
            return output(Operation.OPTIONS,row);
        } catch(IOException invalid) {throw new UncheckedIOException("original AUB options public projection unavailable",invalid);}
    }
    public static RawJson select(Select mutation,RawJson original,ObservationIdentity before,BigInteger generation,
            Options later,String requestId,String actionId)throws IOException {
        Objects.requireNonNull(mutation);AubOperations.nativeMutation(original,mutation,before,generation);
        need(later.policy().selected().equals(java.util.Optional.of(mutation.desired())),"independent selected policy differs");
        ObjectNode nativeAck=object(original);optionsNative(nativeAck,before,generation);
        ObjectNode row=nativeAck.deepCopy();metadata(row,before);result(row,nativeAck,object(options(later)),requestId,actionId);
        return output(Operation.SELECT,row);
    }
    public static RawJson confirm(Confirm mutation,RawJson original,ObservationIdentity before,BigInteger generation,
            AubBusinessStateRead.State later,String requestId,String actionId)throws IOException {
        Objects.requireNonNull(mutation);AubOperations.nativeMutation(original,mutation,before,generation);
        need(AubOperations.confirmed(later,mutation.expected()),"independent AUB Confirm postcondition differs");
        ObjectNode nativeAck=object(original);confirmNative(nativeAck,before,generation);
        ObjectNode row=nativeAck.deepCopy();metadata(row,before);result(row,nativeAck,object(business(later)),requestId,actionId);
        return output(Operation.CONFIRM,row);
    }
    /** Public JSON boundary validates fixed role paths and canonical output decimals, including nested ACKs. */
    public static RawJson readPublic(Operation operation,RawJson actual)throws IOException {
        ObjectNode row=object(Objects.requireNonNull(actual));validate(Objects.requireNonNull(operation),row);
        return raw(row);
    }
    private static void optionsNative(ObjectNode row,ObservationIdentity before,BigInteger generation)throws IOException {
        stamp(row,before,generation);stamp(child(row,"before_actual_model"),before,generation);stamp(child(row,"after_actual_model"),before,generation);
    }
    private static void confirmNative(ObjectNode row,ObservationIdentity before,BigInteger generation)throws IOException {
        stamp(child(row,"before_actual_model"),before,generation);stamp(child(row,"state_before"),before,generation);stamp(child(row,"state_after"),before,generation);
    }
    private static void stamp(ObjectNode row,ObservationIdentity before,BigInteger generation)throws IOException {
        BigInteger revision=NativeWire.integer(row.get("native_revision"),BigInteger.ONE,NativeWire.UINT64_MAX);
        BigInteger connection=NativeWire.integer(row.get("connection_generation"),BigInteger.ONE,NativeWire.UINT64_MAX);
        need(revision.equals(before.frame().identity().nativeRevision())&&connection.equals(generation),"public projection crossed native identity");
        row.put("native_revision",revision.toString());row.put("connection_generation",connection.toString());
    }
    private static void metadata(ObjectNode row,ObservationIdentity before) {
        BigInteger revision=before.frame().revision();need(revision.signum()>=0&&revision.compareTo(NativeWire.UINT64_MAX)<=0,"public revision outside uint64");
        row.put("episode_run_id",before.frame().episodeRunId());row.put("queried_revision",revision.toString());
        for(String key:List.of("uses_mouse","uses_keyboard","uses_ocr","full_product_acceptance_credit"))row.put(key,false);
    }
    private static void result(ObjectNode row,ObjectNode nativeAck,ObjectNode later,String requestId,String actionId) {
        need(requestId!=null&&!requestId.isEmpty()&&actionId!=null&&!actionId.isEmpty(),"actual action request and canonical claim identity required");
        row.set("later_actual_observation",later);row.put("independent_postcondition_verified",true);row.put("action_request_id",requestId);
        row.put("canonical_action_id",actionId);row.put("canonical_claim_authority","same-writer-action-intent");row.set("native_ack",nativeAck);
    }
    private static RawJson output(Operation operation,ObjectNode row)throws IOException {validate(operation,row);return raw(row);}
    private static void validate(Operation operation,ObjectNode row)throws IOException {
        exact(row,fields(operation),true,operation==Operation.SELECT||operation==Operation.CONFIRM);
        metadataPublic(row);
        switch(operation) {
            case BUSINESS -> businessPublic(row);
            case OPTIONS -> optionsPublic(row,AubOperations.QUERY);
            case SELECT -> {
                optionsPublic(row,AubOperations.SELECT);ObjectNode ack=child(row,"native_ack");exact(ack,AubOperations.SELECT_FIELDS,false,false);optionsPublic(ack,AubOperations.SELECT);
                ObjectNode later=child(row,"later_actual_observation");exact(later,AubOperations.OPTIONS_FIELDS,true,false);metadataPublic(later);optionsPublic(later,AubOperations.QUERY);resultPublic(row);
            }
            case CONFIRM -> {
                confirmPublic(row);ObjectNode ack=child(row,"native_ack");exact(ack,AubOperations.CONFIRM_FIELDS,false,false);confirmPublic(ack);
                ObjectNode later=child(row,"later_actual_observation");exact(later,AubBusinessStateRead.RESULT_FIELDS,true,false);metadataPublic(later);businessPublic(later);resultPublic(row);
            }
        }
        safeNumbers(row);
        material(operation,row);
    }
    /** Reuse the sole native DATA decoders after reversing only declared public roles.
     * No synthetic ObservationIdentity, archive, guard or permission is created here. */
    private static void material(Operation operation,ObjectNode row)throws IOException {
        ObjectNode nativeRow=nativeBody(operation,row);
        switch(operation) {
            case BUSINESS -> AubBusinessStateRead.material(raw(nativeRow));
            case OPTIONS -> AubOperations.optionsMaterial(raw(nativeRow));
            case SELECT -> {
                Select mutation=new Select(key(nativeRow,"expected_selected_key"),key(nativeRow,"desired_key"));
                var actual=AubOperations.mutationMaterial(raw(nativeRow),mutation);
                need(nativeRow.equals(nativeBody(Operation.SELECT,child(row,"native_ack"))),"public AUB result differs from original ACK DATA");
                var later=AubOperations.optionsMaterial(raw(nativeBody(Operation.OPTIONS,child(row,"later_actual_observation"))));
                need(actual.stamp().sameOwner(later.stamp())&&later.policy().selected().equals(java.util.Optional.of(mutation.desired())),"independent public AUB selection DATA differs");
                sameEpisode(row);
            }
            case CONFIRM -> {
                Confirm mutation=new Confirm(key(nativeRow,"selected_key"));var actual=AubOperations.mutationMaterial(raw(nativeRow),mutation);
                need(nativeRow.equals(nativeBody(Operation.CONFIRM,child(row,"native_ack"))),"public AUB Confirm differs from original ACK DATA");
                var later=AubBusinessStateRead.material(raw(nativeBody(Operation.BUSINESS,child(row,"later_actual_observation"))));
                need(actual.stamp().sameOwner(later.stamp())&&AubOperations.confirmed(later,mutation.expected()),"independent public AUB Confirm DATA differs");
                sameEpisode(row);
            }
        }
    }
    private static ObjectNode nativeBody(Operation operation,ObjectNode row)throws IOException {
        ObjectNode copy=row.deepCopy();METADATA.forEach(copy::remove);RESULT.forEach(copy::remove);
        switch(operation) {
            case BUSINESS -> numericStamp(copy);
            case OPTIONS,SELECT -> {numericStamp(copy);numericStamp(child(copy,"before_actual_model"));numericStamp(child(copy,"after_actual_model"));}
            case CONFIRM -> {numericStamp(child(copy,"before_actual_model"));numericStamp(child(copy,"state_before"));numericStamp(child(copy,"state_after"));}
        }
        return copy;
    }
    private static void numericStamp(ObjectNode row) {
        BigInteger revision=decimal(row,"native_revision",BigInteger.ONE),generation=decimal(row,"connection_generation",BigInteger.ONE);
        row.put("native_revision",revision);row.put("connection_generation",generation);
    }
    private static PolicyKey key(ObjectNode row,String name) {
        need(row.path(name).isTextual(),"AUB semantic key text required");return PolicyKey.parse(row.get(name).textValue());
    }
    private static void sameEpisode(ObjectNode row)throws IOException {
        need(row.get("episode_run_id").equals(child(row,"later_actual_observation").get("episode_run_id")),"public AUB later DATA changed episode");
    }
    private static void businessPublic(ObjectNode row)throws IOException {schema(row,"ck3-aub-business-state-v1",AubBusinessStateRead.STEP);stampPublic(row);}
    private static void optionsPublic(ObjectNode row,String step)throws IOException {
        schema(row,"ck3-aub-policy-options-v1",step);stampPublic(row);
        detailPublic(child(row,"before_actual_model"));detailPublic(child(row,"after_actual_model"));
        ObjectNode policy=child(row,step.equals(AubOperations.QUERY)?"policy":"before_policy");policyPublic(policy);
        if(step.equals(AubOperations.SELECT))policyPublic(child(row,"after_policy"));
    }
    private static void confirmPublic(ObjectNode row)throws IOException {
        schema(row,"ck3-aub-confirm-v1",AubOperations.CONFIRM);detailPublic(child(row,"before_actual_model"));
        for(String key:List.of("state_before","state_after")) {ObjectNode state=child(row,key);exact(state,AubBusinessStateRead.RESULT_FIELDS,false,false);businessPublic(state);}
    }
    private static void detailPublic(ObjectNode row)throws IOException {
        schema(row,"ck3-ingame-decision-item-v1","query-ingame-decision-item-v1");stampPublic(row);
        bounded(row,"row_context_reference_key",BigInteger.ZERO,U32);bounded(row,"detail_actor_reference_key",BigInteger.ONE,I32);
        bounded(row,"group_count",BigInteger.ZERO,BigInteger.valueOf(64));bounded(row,"row_count",BigInteger.ZERO,BigInteger.valueOf(2048));bounded(row,"matching_row_count",BigInteger.ONE,BigInteger.ONE);
    }
    private static void policyPublic(ObjectNode row)throws IOException {bounded(row,"played_character_id",BigInteger.ONE,I32);bounded(row,"selected_index",BigInteger.valueOf(-1),BigInteger.valueOf(5));}
    private static void stampPublic(ObjectNode row)throws IOException {
        decimal(row,"native_revision",BigInteger.ONE);decimal(row,"connection_generation",BigInteger.ONE);
        bounded(row,"game_pid",BigInteger.ONE,U32);bounded(row,"played_character_id",BigInteger.ONE,I32);bounded(row,"date_raw",I32_MIN,I32);
    }
    private static void metadataPublic(ObjectNode row) {
        decimal(row,"queried_revision",BigInteger.ZERO);need(row.path("episode_run_id").isTextual()&&!row.get("episode_run_id").textValue().isEmpty(),"public episode required");
        for(String key:List.of("uses_mouse","uses_keyboard","uses_ocr","full_product_acceptance_credit"))need(row.path(key).isBoolean()&&!row.get(key).booleanValue(),"AUB public flags cannot grant UI/product credit");
    }
    private static void resultPublic(ObjectNode row) {
        need(row.path("independent_postcondition_verified").isBoolean()&&row.get("independent_postcondition_verified").booleanValue(),"independent result proof flag required");
        for(String key:List.of("action_request_id","canonical_action_id"))need(row.path(key).isTextual()&&!row.get(key).textValue().isEmpty(),"actual AUB action identity required");
        need(row.path("canonical_claim_authority").asText().equals("same-writer-action-intent"),"actual canonical claim authority required");
    }
    private static void schema(ObjectNode row,String schema,String step) {need(row.path("schema").asText().equals(schema)&&row.path("step").asText().equals(step),"exact public AUB operation schema required");}
    private static BigInteger decimal(ObjectNode row,String key,BigInteger minimum) {
        JsonNode token=row.get(key);need(token!=null&&token.isTextual()&&token.textValue().length()<=20&&token.textValue().matches("0|[1-9][0-9]*"),"canonical uint64 decimal string required: "+key);
        BigInteger value=new BigInteger(token.textValue());need(value.compareTo(minimum)>=0&&value.compareTo(NativeWire.UINT64_MAX)<=0,"public uint64 outside range: "+key);return value;
    }
    private static void bounded(ObjectNode row,String key,BigInteger minimum,BigInteger maximum)throws IOException {NativeWire.integer(row.get(key),minimum,maximum);}
    private static void safeNumbers(JsonNode value) {
        if(value.isNumber())need(value.isIntegralNumber()&&value.bigIntegerValue().abs().compareTo(SAFE)<=0,"unconverted or unsafe public numeric role");
        if(value.isContainerNode())for(JsonNode child:value)safeNumbers(child);
    }
    private static Set<String> fields(Operation operation) {
        return switch(operation) {
            case BUSINESS -> AubBusinessStateRead.RESULT_FIELDS;
            case OPTIONS -> AubOperations.OPTIONS_FIELDS;
            case SELECT -> AubOperations.SELECT_FIELDS;
            case CONFIRM -> AubOperations.CONFIRM_FIELDS;
        };
    }
    private static void exact(ObjectNode row,Set<String> nativeFields,boolean metadata,boolean outcome) {
        Set<String> expected=new HashSet<>(nativeFields);if(metadata)expected.addAll(METADATA);if(outcome)expected.addAll(RESULT);
        if(row.has("backend_id")) {expected.add("backend_id");need(row.path("backend_id").asText().equals("native-headless"),"AUB backend changed");}
        Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);need(actual.equals(expected),"exact AUB public field contract differs");
    }
    private static ObjectNode child(ObjectNode row,String key)throws IOException {return NativeWire.object(row.get(key));}
    private static ObjectNode object(RawJson raw)throws IOException {return NativeWire.object(NativeWire.parse(raw.bytes()));}
    private static RawJson raw(ObjectNode row) {return new RawJson(row.toString().getBytes(StandardCharsets.UTF_8));}
    private static void need(boolean condition,String message) {if(!condition)throw new IllegalArgumentException(message);}
}

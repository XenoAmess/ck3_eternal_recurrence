package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact resident letter observation. The reviewed mapping admits no configurable option. */
public record CurrentLetterSource(int residentCount,boolean letterFound,boolean namedRootBound,boolean windowVisible,
        boolean windowEnabled,Optional<Integer> instanceId,Optional<Integer> recipientCharacterId,Optional<String> definitionKey,
        Optional<String> opening,Optional<String> description,List<Option> options,boolean knownReplyAdmissible) {
    public record Option(int authoredOptionIndex,boolean nativeCanSelect,String text,String disabledReason,Optional<String> sourceBoundOptionKey) {
        public Option {Objects.requireNonNull(sourceBoundOptionKey);bounded(text,16384);bounded(disabledReason,16384);
            StrictJson.require(authoredOptionIndex>=0&&authoredOptionIndex<64,"Actual authored option index outside bounded DATA domain");}
    }
    public CurrentLetterSource {
        Objects.requireNonNull(instanceId);Objects.requireNonNull(recipientCharacterId);Objects.requireNonNull(definitionKey);
        Objects.requireNonNull(opening);Objects.requireNonNull(description);options=List.copyOf(options);
        StrictJson.require(residentCount>=0&&residentCount<=32&&options.size()<=64,"Bounded actual resident source required");
        if(!letterFound) StrictJson.require(!namedRootBound&&!windowVisible&&!windowEnabled&&instanceId.isEmpty()&&recipientCharacterId.isEmpty()
                &&definitionKey.isEmpty()&&opening.isEmpty()&&description.isEmpty()&&options.isEmpty()&&!knownReplyAdmissible,"No-letter source must preserve exact null roles");
        else {
            StrictJson.require(namedRootBound&&instanceId.filter(n->n>0).isPresent()&&recipientCharacterId.filter(n->n!=-1).isPresent()
                    &&definitionKey.filter(s->!s.isEmpty()).isPresent()&&opening.isPresent()&&description.isPresent(),"Actual found-letter source incomplete");
            bounded(definitionKey.orElseThrow(),256);bounded(opening.orElseThrow(),16384);bounded(description.orElseThrow(),16384);
            var indices=new HashSet<Integer>();for(var option:options) {
                StrictJson.require(indices.add(option.authoredOptionIndex()),"Duplicate authored letter option index");
                if(option.sourceBoundOptionKey().isPresent())StrictJson.require(CurrentLetter.KNOWN_DEFINITION.equals(definitionKey.orElseThrow())
                        &&options.size()==1&&option.authoredOptionIndex()==0&&CurrentLetter.KNOWN_OPTION.equals(option.sourceBoundOptionKey().orElseThrow()),"Unreviewed letter option-key mapping");
            }
            if(knownReplyAdmissible)StrictJson.require(CurrentLetter.KNOWN_DEFINITION.equals(definitionKey.orElseThrow())&&windowVisible&&windowEnabled
                    &&options.size()==1&&options.getFirst().authoredOptionIndex()==0&&options.getFirst().nativeCanSelect()
                    &&options.getFirst().sourceBoundOptionKey().filter(CurrentLetter.KNOWN_OPTION::equals).isPresent()&&!options.getFirst().text().isEmpty(),"Fixed known reply source incomplete");
        }
    }
    static CurrentLetterSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","resident_count","letter_found","named_root_bound","window_visible","window_enabled","instance_id","recipient_character_id","definition_key","opening","description","options","known_reply_admissible"));
        if(!NativeWire.text(r.get("schema")).equals(CurrentLetter.SOURCE_SCHEMA))throw new IOException("Exact current letter source schema required");
        if(!r.get("options").isArray()||r.get("options").size()>64)throw new IOException("Bounded actual letter options required");
        var options=new ArrayList<Option>();for(var n:r.get("options")) {
            var o=StrictJson.object(n,Set.of("authored_option_index","native_can_select","text","disabled_reason","source_bound_option_key"));
            options.add(new Option(i32(o.get("authored_option_index")),bool(o,"native_can_select"),cachedText(o.get("text")),cachedText(o.get("disabled_reason")),text(o.get("source_bound_option_key"))));
        }
        return new CurrentLetterSource(i32(r.get("resident_count")),bool(r,"letter_found"),bool(r,"named_root_bound"),bool(r,"window_visible"),bool(r,"window_enabled"),
                integer(r.get("instance_id")),integer(r.get("recipient_character_id")),text(r.get("definition_key")),text(r.get("opening")),text(r.get("description")),options,bool(r,"known_reply_admissible"));
    }
    ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentLetter.SOURCE_SCHEMA).put("resident_count",residentCount).put("letter_found",letterFound)
                .put("named_root_bound",namedRootBound).put("window_visible",windowVisible).put("window_enabled",windowEnabled).put("known_reply_admissible",knownReplyAdmissible);
        putInt(r,"instance_id",instanceId);putInt(r,"recipient_character_id",recipientCharacterId);putText(r,"definition_key",definitionKey);putText(r,"opening",opening);putText(r,"description",description);
        var a=r.putArray("options");for(var o:options){var n=a.addObject().put("authored_option_index",o.authoredOptionIndex()).put("native_can_select",o.nativeCanSelect()).put("text",o.text()).put("disabled_reason",o.disabledReason());putText(n,"source_bound_option_key",o.sourceBoundOptionKey());}return r;
    }
    private static void putInt(ObjectNode r,String k,Optional<Integer> v){if(v.isPresent())r.put(k,v.orElseThrow());else r.putNull(k);}
    private static void putText(ObjectNode r,String k,Optional<String> v){if(v.isPresent())r.put(k,v.orElseThrow());else r.putNull(k);}
    private static Optional<Integer> integer(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(i32(n));}
    private static Optional<String> text(JsonNode n)throws IOException{return n.isNull()?Optional.empty():Optional.of(cachedText(n));}
    private static String cachedText(JsonNode n)throws IOException {if(n==null||!n.isTextual())throw new IOException("Actual cached JSON string required");return n.textValue();}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException {var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual letter bool required: "+k);return n.booleanValue();}
    private static void bounded(String s,int max){Objects.requireNonNull(s);StrictJson.require(s.getBytes(StandardCharsets.UTF_8).length<=max,"Bounded actual cached letter string required");}
}

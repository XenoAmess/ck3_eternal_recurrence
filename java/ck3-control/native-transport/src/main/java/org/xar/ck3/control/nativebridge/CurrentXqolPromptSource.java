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

/** Complete prompt census. A missing fixed event does not assert that other event windows are absent. */
public record CurrentXqolPromptSource(int residentCount,int namedRootCount,boolean censusComplete,
        Optional<Integer> authoredOptionCount,Optional<Event> event,boolean confirmAdmissible,boolean cancelAdmissible) {
    public record Event(int residentCount,boolean eventFound,boolean namedRootBound,boolean windowVisible,boolean windowEnabled,
            int instanceId,int recipientCharacterId,String definitionKey,String opening,String description,List<CurrentLetterSource.Option> options) {
        public Event {
            options=List.copyOf(options);bounded(opening);bounded(description);
            StrictJson.require(residentCount>=0&&residentCount<=32&&eventFound&&namedRootBound&&instanceId>0&&recipientCharacterId!=-1
                    &&CurrentXqolPrompt.KNOWN_DEFINITION.equals(definitionKey)&&options.size()<=2,"Exact known material prompt event required");
            var seen=new HashSet<Integer>();for(var o:options){
                StrictJson.require(o.authoredOptionIndex()<=1&&seen.add(o.authoredOptionIndex()),"Duplicate or unknown prompt authored option");
                String key=o.authoredOptionIndex()==0?CurrentXqolPrompt.CONFIRM_OPTION:CurrentXqolPrompt.CANCEL_OPTION;
                StrictJson.require(o.sourceBoundOptionKey().filter(key::equals).isPresent(),"Exact reviewed authored prompt option mapping required");
            }
        }
        public boolean admits(CurrentXqolPrompt.Action action) {
            if(action==CurrentXqolPrompt.Action.QUERY_PROMPT)return false;
            int authored=action==CurrentXqolPrompt.Action.CONFIRM_CONVERSION?0:1;
            return windowVisible&&windowEnabled&&options.stream().anyMatch(o->o.authoredOptionIndex()==authored&&o.nativeCanSelect());
        }
    }
    public CurrentXqolPromptSource {
        Objects.requireNonNull(authoredOptionCount);Objects.requireNonNull(event);
        StrictJson.require(residentCount>=0&&residentCount<=32&&namedRootCount>=0&&namedRootCount<=32&&censusComplete,"Complete bounded actual prompt census required");
        if(event.isEmpty())StrictJson.require(authoredOptionCount.isEmpty()&&!confirmAdmissible&&!cancelAdmissible,"Absent known prompt retains null authored count and no action authority");
        else {
            var e=event.orElseThrow();StrictJson.require(namedRootCount>=1&&e.residentCount()==residentCount&&authoredOptionCount.filter(n->n==2).isPresent(),"Known prompt census/count differs");
            StrictJson.require(confirmAdmissible==e.admits(CurrentXqolPrompt.Action.CONFIRM_CONVERSION)&&cancelAdmissible==e.admits(CurrentXqolPrompt.Action.CANCEL_CONVERSION),"Actual prompt NativeCan/admission differs");
        }
    }
    public boolean admits(CurrentXqolPrompt.Action action){return switch(action){case QUERY_PROMPT->false;case CONFIRM_CONVERSION->confirmAdmissible;case CANCEL_CONVERSION->cancelAdmissible;};}
    static CurrentXqolPromptSource decode(JsonNode node)throws IOException {
        var r=StrictJson.object(node,Set.of("schema","resident_count","named_root_count","census_complete","authored_option_count","event","confirm_admissible","cancel_admissible"));
        require(r,"schema",CurrentXqolPrompt.SOURCE_SCHEMA);Optional<Event> event=Optional.empty();
        if(!r.get("event").isNull()) {
            var e=StrictJson.object(r.get("event"),Set.of("schema","resident_count","event_found","named_root_bound","window_visible","window_enabled","instance_id","recipient_character_id","definition_key","opening","description","options","known_definition_verified"));
            require(e,"schema",CurrentXqolPrompt.EVENT_SCHEMA);if(!bool(e,"known_definition_verified"))throw new IOException("Known prompt definition not verified");
            if(!e.get("options").isArray()||e.get("options").size()>2)throw new IOException("Bounded actual prompt options required");
            var options=new ArrayList<CurrentLetterSource.Option>();for(var n:e.get("options")) {
                var o=StrictJson.object(n,Set.of("authored_option_index","native_can_select","text","disabled_reason","source_bound_option_key"));
                options.add(new CurrentLetterSource.Option(i32(o.get("authored_option_index")),bool(o,"native_can_select"),cached(o.get("text")),cached(o.get("disabled_reason")),o.get("source_bound_option_key").isNull()?Optional.empty():Optional.of(cached(o.get("source_bound_option_key")))));
            }
            event=Optional.of(new Event(i32(e.get("resident_count")),bool(e,"event_found"),bool(e,"named_root_bound"),bool(e,"window_visible"),bool(e,"window_enabled"),i32(e.get("instance_id")),i32(e.get("recipient_character_id")),cached(e.get("definition_key")),cached(e.get("opening")),cached(e.get("description")),options));
        }
        return new CurrentXqolPromptSource(i32(r.get("resident_count")),i32(r.get("named_root_count")),bool(r,"census_complete"),r.get("authored_option_count").isNull()?Optional.empty():Optional.of(i32(r.get("authored_option_count"))),event,bool(r,"confirm_admissible"),bool(r,"cancel_admissible"));
    }
    ObjectNode encode() {
        var r=StrictJson.object().put("schema",CurrentXqolPrompt.SOURCE_SCHEMA).put("resident_count",residentCount).put("named_root_count",namedRootCount).put("census_complete",censusComplete).put("confirm_admissible",confirmAdmissible).put("cancel_admissible",cancelAdmissible);
        if(authoredOptionCount.isPresent())r.put("authored_option_count",authoredOptionCount.orElseThrow());else r.putNull("authored_option_count");
        if(event.isEmpty())r.putNull("event");else {
            var e=event.orElseThrow();var n=r.putObject("event").put("schema",CurrentXqolPrompt.EVENT_SCHEMA).put("resident_count",e.residentCount()).put("event_found",e.eventFound()).put("named_root_bound",e.namedRootBound()).put("window_visible",e.windowVisible()).put("window_enabled",e.windowEnabled()).put("instance_id",e.instanceId()).put("recipient_character_id",e.recipientCharacterId()).put("definition_key",e.definitionKey()).put("opening",e.opening()).put("description",e.description()).put("known_definition_verified",true);
            var a=n.putArray("options");for(var o:e.options()){var v=a.addObject().put("authored_option_index",o.authoredOptionIndex()).put("native_can_select",o.nativeCanSelect()).put("text",o.text()).put("disabled_reason",o.disabledReason());if(o.sourceBoundOptionKey().isPresent())v.put("source_bound_option_key",o.sourceBoundOptionKey().orElseThrow());else v.putNull("source_bound_option_key");}
        }return r;
    }
    private static String cached(JsonNode n)throws IOException{if(n==null||!n.isTextual())throw new IOException("Actual cached prompt string required");return n.textValue();}
    private static void bounded(String s){Objects.requireNonNull(s);StrictJson.require(s.getBytes(StandardCharsets.UTF_8).length<=16384,"Bounded cached prompt string required");}
    private static int i32(JsonNode n)throws IOException{return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static boolean bool(ObjectNode r,String k)throws IOException{var n=r.get(k);if(n==null||!n.isBoolean())throw new IOException("Actual prompt bool required: "+k);return n.booleanValue();}
    private static void require(ObjectNode r,String k,String expected)throws IOException{if(!cached(r.get(k)).equals(expected))throw new IOException("Exact prompt identity required: "+k);}
}

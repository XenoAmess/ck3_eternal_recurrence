package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-valued knowledge compiled from all original producers. No current Game or Python runtime is consulted. */
public final class ReligionHolyKnowledge {
    public static final String BUILD="1.20.0.4",RESOURCE="/org/xar/ck3/control/religion/holy-site-planning-v1.json";
    public static final long RESOURCE_BYTES=349224;
    public static final String RESOURCE_SHA256="a50636b62e64d54c601272e8cf0ad4131ea7abc0f07e108cd9f5961fa869387e";
    private ReligionHolyKnowledge() { }
    public enum Action {
        ADOPT,CREATE,PROMOTE,DEMOTE,ABANDON,ENSHRINE_RELIC,REMOVE_RELIC;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static Action parse(String value){for(Action action:values())if(action.wire().equals(value))return action;throw new IllegalArgumentException("unsupported holy-site planning action");}
    }
    private static final class Holder { private static final Compiled SOURCE=load(); }
    public static RawJson query(Action action,String requestedBuild){return Holder.SOURCE.query(action,requestedBuild);}
    public static List<ExactRef> originalSources(){return Holder.SOURCE.originalSources();}
    private static Compiled load(){try(var stream=ReligionHolyKnowledge.class.getResourceAsStream(RESOURCE)){if(stream==null)throw new IOException("complete compiled holy-site planning source resource missing");return decode(stream.readNBytes((int)RESOURCE_BYTES+1));}catch(IOException missing){throw new UncheckedIOException(missing);}}
    /** Exact source-resource decoder, also used by packaging/parity regressions. It grants no current eligibility. */
    public static Compiled decode(byte[] original){
        StrictJson.require(original!=null&&original.length==RESOURCE_BYTES&&ActionCodec.sha256(original).equals(RESOURCE_SHA256),"complete immutable holy-site planning source pack changed");
        ObjectNode root=ReligionCodec.object(new RawJson(original));shape(root,Set.of("schema","actions","blocks","unsupported_template","original_sources"));equal(root,"schema","xar.java.holy-source-knowledge-pack/v1");
        ObjectNode actions=object(root.get("actions")),blocks=object(root.get("blocks"));var expected=new HashSet<String>();for(Action action:Action.values())expected.add(action.wire());shape(actions,expected);
        for(var fields=blocks.properties().iterator();fields.hasNext();){var field=fields.next();StrictJson.require(field.getKey().matches("[0-9a-f]{64}")&&field.getValue().isContainerNode(),"closed compiled source block identity required");}
        var values=new EnumMap<Action,RawJson>(Action.class);
        for(Action action:Action.values()){ObjectNode value=object(expand(actions.get(action.wire()),blocks,new HashSet<>(),0));requireStatic(value,action);equal(value,"requested_build",BUILD);equal(value,"status","available");equal(value,"qualification","source_reviewed_static");values.put(action,ReligionCodec.raw(value));}
        ObjectNode unsupported=object(root.get("unsupported_template"));requireStatic(unsupported,Action.ADOPT);equal(unsupported,"status","unavailable");equal(unsupported,"qualification","unsupported_build");StrictJson.require(unsupported.get("knowledge").isNull(),"unsupported build cannot acquire reviewed knowledge");
        JsonNode refs=root.get("original_sources");StrictJson.require(refs.isArray()&&refs.size()==10,"complete original static knowledge producer closure required");var sources=new ArrayList<ExactRef>();for(JsonNode source:refs)sources.add(ExactRef.fromJson(source));StrictJson.require(sources.stream().map(ExactRef::path).distinct().count()==sources.size(),"original static source roster repeats a file");
        return new Compiled(values,ReligionCodec.raw(unsupported),sources);
    }
    public static final class Compiled {
        private final EnumMap<Action,RawJson> actions;private final RawJson unsupported;private final List<ExactRef> originalSources;
        private Compiled(EnumMap<Action,RawJson> actions,RawJson unsupported,List<ExactRef> sources){this.actions=new EnumMap<>(actions);this.unsupported=unsupported;originalSources=List.copyOf(sources);}
        public List<ExactRef> originalSources(){return originalSources;}
        public RawJson query(Action action,String requestedBuild){
            java.util.Objects.requireNonNull(action);StrictJson.require(requestedBuild!=null&&!requestedBuild.isEmpty(),"ck3_build must be a nonempty exact version");
            if(requestedBuild.equals(BUILD))return actions.get(action);
            ObjectNode result=ReligionCodec.object(unsupported);result.put("action",action.wire()).put("requested_build",requestedBuild);return ReligionCodec.raw(result);
        }
    }
    private static JsonNode expand(JsonNode source,ObjectNode blocks,Set<String> active,int depth){
        StrictJson.require(source!=null&&depth<=128,"bounded complete static-source expansion required");
        if(source instanceof ObjectNode object){
            if(object.has("$knowledge_ref")){shape(object,Set.of("$knowledge_ref"));String key=StrictJson.text(object.get("$knowledge_ref"));StrictJson.require(key.matches("[0-9a-f]{64}")&&active.add(key)&&blocks.has(key),"missing or cyclic static-source block");JsonNode expanded=expand(blocks.get(key),blocks,active,depth+1);active.remove(key);return expanded;}
            ObjectNode result=StrictJson.object();for(var fields=object.properties().iterator();fields.hasNext();){var field=fields.next();result.set(field.getKey(),expand(field.getValue(),blocks,active,depth+1));}return result;
        }
        if(source.isArray()){var result=StrictJson.object().putArray("values");for(JsonNode value:source)result.add(expand(value,blocks,active,depth+1));return result;}
        return source.deepCopy();
    }
    private static void requireStatic(ObjectNode value,Action action){equal(value,"schema","xar.ck3.holy-site-planning-knowledge.v1");equal(value,"action",action.wire());equal(value,"supported_build",BUILD);for(String field:List.of("read_only"))StrictJson.require(value.path(field).isBoolean()&&value.get(field).booleanValue(),"source knowledge lost readonly contract");for(String field:List.of("requires_ck3","executes_action","state_observed","action_ready"))StrictJson.require(value.path(field).isBoolean()&&!value.get(field).booleanValue(),"static source knowledge cannot grant observed state, action or readiness");StrictJson.require(value.has("native_legality")&&value.get("native_legality").isNull(),"static source knowledge cannot invent native eligibility");}
    private static ObjectNode object(JsonNode value){StrictJson.require(value instanceof ObjectNode,"compiled source object required");return (ObjectNode)value;}
    private static void shape(ObjectNode value,Set<String> expected){var names=new HashSet<String>();value.fieldNames().forEachRemaining(names::add);StrictJson.require(names.equals(expected),"compiled source fields changed");}
    private static void equal(ObjectNode value,String field,String expected){StrictJson.require(value.has(field)&&value.get(field).isTextual()&&value.get(field).textValue().equals(expected),"compiled source field changed: "+field);}
}

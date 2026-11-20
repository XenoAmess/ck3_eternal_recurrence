package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Response-local tree DATA only. Node indices are neither addresses nor reusable activation tokens. */
public sealed interface GuiWindowFrame permits GuiWindowFrame.Partial, GuiWindowFrame.Unavailable {
    String STEP="query-scripted-gui-window-v1", SCHEMA="ck3.scripted_gui_window.v1", REQUEST_SCHEMA="ck3.scripted_gui_window_request.v1";
    String BACKEND=GuiRootIndexFrame.BACKEND;
    ExactCk3Build BUILD=GuiRootIndexFrame.BUILD;
    int MAXIMUM_BYTES=2*1024*1024, MAXIMUM_NODES=4096, MAXIMUM_DEPTH=64, MAXIMUM_NAME_BYTES=192, MAXIMUM_TOTAL_NAME_BYTES=131072;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status",
            "tree_source_available","window_available","application_main_observed","source_abi_pins_verified","addresses_redacted",
            "complete_snapshot","complete_gui_tree","complete_window_tree","native_findtop_semantics_verified","activation_available","control_actions_available",
            "core_frame","requested_window","top_level","window","owner_witness","unavailable_reason");
    CoreFrame coreFrame();
    default ExactCk3Build build(){return BUILD;}
    default boolean windowAvailable(){return this instanceof Partial p&&p.window().isPresent();}
    static String windowName(String value){RegistryJson.require(value!=null&&value.matches("[A-Za-z0-9._-]{1,96}"),"explicit bounded ASCII window name required");return value;}
    static String nodeName(String value){
        RegistryJson.require(value!=null&&value.indexOf(0)<0,"observed widget name cannot contain NUL");
        for(int i=0;i<value.length();i++) {
            char c=value.charAt(i);
            if(Character.isHighSurrogate(c)){RegistryJson.require(i+1<value.length()&&Character.isLowSurrogate(value.charAt(i+1)),"valid UTF-8 name required");i++;}
            else RegistryJson.require(!Character.isLowSurrogate(c),"valid UTF-8 name required");
        }
        RegistryJson.require(value.getBytes(StandardCharsets.UTF_8).length<=MAXIMUM_NAME_BYTES,"widget name exceeds192 UTF-8 bytes");return value;
    }
    record TopLevel(String name,boolean visible,boolean enabled){public TopLevel{nodeName(name);}}
    record Node(int nodeId,OptionalInt parentId,int siblingIndex,int depth,String name,int childCount,boolean visible,boolean enabled){
        public Node{
            Objects.requireNonNull(parentId);nodeName(name);
            RegistryJson.require(nodeId>=0&&nodeId<MAXIMUM_NODES&&siblingIndex>=0&&siblingIndex<MAXIMUM_NODES
                    &&depth>=0&&depth<=MAXIMUM_DEPTH&&childCount>=0&&childCount<=MAXIMUM_NODES,"bounded response-local node indices/counts required");
            RegistryJson.require(parentId.isEmpty()?nodeId==0&&depth==0:nodeId>0&&parentId.getAsInt()>=0&&parentId.getAsInt()<nodeId,"root null or preceding parent required");
        }
    }
    record Window(List<Node> nodes){
        public Window{
            nodes=List.copyOf(nodes);RegistryJson.require(!nodes.isEmpty()&&nodes.size()<=MAXIMUM_NODES,"bounded complete window nodes required");
            int[] children=new int[nodes.size()];
            for(int i=0;i<nodes.size();i++) {
                var n=nodes.get(i);RegistryJson.require(n.nodeId()==i,"canonical contiguous response-local IDs required");
                if(i==0)RegistryJson.require(n.parentId().isEmpty()&&n.depth()==0,"first node is the root");
                else {
                    int parent=n.parentId().orElseThrow();var p=nodes.get(parent);
                    RegistryJson.require(n.depth()==p.depth()+1&&n.siblingIndex()==children[parent]++,"parent depth and exact child order required");
                    RegistryJson.require((!n.visible()||p.visible())&&(!n.enabled()||p.enabled()),"child flags cannot escape ancestor flags");
                }
            }
            for(int i=0;i<nodes.size();i++)RegistryJson.require(children[i]==nodes.get(i).childCount(),"complete child_count must equal actual children");
        }
    }
    record Partial(CoreFrame.Partial coreFrame,String requestedWindow,List<TopLevel> topLevel,Optional<Window> window,
            GuiRootIndexFrame.OwnerWitness ownerWitness)implements GuiWindowFrame {
        public Partial{
            GuiRootIndexFrame.requireExpectedCore(coreFrame);windowName(requestedWindow);topLevel=List.copyOf(topLevel);
            Objects.requireNonNull(window);Objects.requireNonNull(ownerWitness);RegistryJson.require(topLevel.size()<=MAXIMUM_NODES,"bounded top-level inventory required");
            int match=-1,count=0;long bytes=0;
            for(int i=0;i<topLevel.size();i++){var t=topLevel.get(i);bytes+=t.name().getBytes(StandardCharsets.UTF_8).length;if(t.name().equals(requestedWindow)){match=i;count++;}}
            RegistryJson.require(count==(window.isPresent()?1:0),"window must correspond to exactly one named top-level entry");
            if(window.isPresent()) {
                var nodes=window.orElseThrow().nodes();var first=nodes.getFirst();var top=topLevel.get(match);
                RegistryJson.require(first.name().equals(requestedWindow)&&first.siblingIndex()==match&&first.visible()==top.visible()&&first.enabled()==top.enabled(),"window root differs from its exact top-level occurrence");
                for(int i=1;i<nodes.size();i++)bytes+=nodes.get(i).name().getBytes(StandardCharsets.UTF_8).length;
            }
            // The unexported global-root name is not asserted; all exported names remain bounded.
            RegistryJson.require(bytes<=MAXIMUM_TOTAL_NAME_BYTES,"observed name budget exceeded");
        }
    }
    record Unavailable(CoreFrame.Unavailable coreFrame,String reason)implements GuiWindowFrame {
        public Unavailable{Objects.requireNonNull(coreFrame);RegistryJson.require(coreFrame.build()==BUILD&&reason!=null&&!reason.isEmpty()&&reason.equals(coreFrame.reason()),"atomic unavailable Core/window reason required");}
    }
    static GuiWindowFrame decode(RawJson raw){
        RegistryJson.require(raw.bytes().length<=MAXIMUM_BYTES,"bounded window response required");var row=RegistryJson.object(raw);RegistryJson.keys(row,FIELDS);
        RegistryJson.require(STEP.equals(RegistryJson.text(row.get("step")))&&SCHEMA.equals(RegistryJson.text(row.get("schema")))
                &&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&BUILD.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),"exact window source tuple required");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted"))&&!RegistryJson.bool(row.get("complete_snapshot"))
                &&!RegistryJson.bool(row.get("complete_gui_tree"))&&!RegistryJson.bool(row.get("native_findtop_semantics_verified"))
                &&!RegistryJson.bool(row.get("activation_available"))&&!RegistryJson.bool(row.get("control_actions_available")),"read-only tree cannot grant addresses, native FindTop semantics or actions");
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));RegistryJson.require(core.build()==BUILD,"nested Core exact source mismatch");
        boolean available=RegistryJson.bool(row.get("tree_source_available")),found=RegistryJson.bool(row.get("window_available"));
        boolean main=RegistryJson.bool(row.get("application_main_observed")),pins=RegistryJson.bool(row.get("source_abi_pins_verified")),complete=RegistryJson.bool(row.get("complete_window_tree"));
        if(!available){
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status")))&&!found&&!pins&&!complete&&core instanceof CoreFrame.Unavailable
                    &&row.get("requested_window").isNull()&&row.get("top_level").isNull()&&row.get("window").isNull()&&row.get("owner_witness").isNull(),"unavailable window must preserve explicit nulls");
            var absent=(CoreFrame.Unavailable)core;RegistryJson.require(main==absent.applicationMainObserved(),"window main-owner flag differs from Core");return new Unavailable(absent,RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status")))&&main&&pins&&core instanceof CoreFrame.Partial&&complete==found&&row.get("unavailable_reason").isNull(),"partial tree evidence required");
        var top=new ArrayList<TopLevel>();for(var n:array(row.get("top_level"))){var t=RegistryJson.object(n);RegistryJson.keys(t,Set.of("name","visible","enabled"));top.add(new TopLevel(name(t.get("name")),RegistryJson.bool(t.get("visible")),RegistryJson.bool(t.get("enabled"))));}
        Optional<Window> window;
        if(!found){RegistryJson.require(row.get("window").isNull(),"missing named window must remain null");window=Optional.empty();}
        else{
            var w=RegistryJson.object(row.get("window"));RegistryJson.keys(w,Set.of("nodes"));var nodes=new ArrayList<Node>();
            for(var n:array(w.get("nodes"))){var t=RegistryJson.object(n);RegistryJson.keys(t,Set.of("node_id","parent_id","sibling_index","depth","name","child_count","visible","enabled"));
                nodes.add(new Node(id(t.get("node_id")),t.get("parent_id").isNull()?OptionalInt.empty():OptionalInt.of(id(t.get("parent_id"))),RegistryJson.int32(t.get("sibling_index")),RegistryJson.int32(t.get("depth")),name(t.get("name")),RegistryJson.int32(t.get("child_count")),RegistryJson.bool(t.get("visible")),RegistryJson.bool(t.get("enabled"))));}
            window=Optional.of(new Window(nodes));
        }
        var owner=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(owner,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
        return new Partial((CoreFrame.Partial)core,RegistryJson.text(row.get("requested_window")),top,window,new GuiRootIndexFrame.OwnerWitness(witness(owner.get("connection_generation")),witness(owner.get("ticket_sequence")),witness(owner.get("pump_epoch")),RegistryJson.integer(owner.get("thread_id"),java.math.BigInteger.ONE,java.math.BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
    }
    private static List<JsonNode> array(JsonNode node){RegistryJson.require(node!=null&&node.isArray()&&node.size()<=MAXIMUM_NODES,"bounded node array required");var list=new ArrayList<JsonNode>();node.forEach(list::add);return list;}
    private static String name(JsonNode node){RegistryJson.require(node!=null&&node.isTextual(),"actual widget-name string required");return nodeName(node.textValue());}
    private static int id(JsonNode node){String token=RegistryJson.text(node);RegistryJson.require(token.matches("0|[1-9][0-9]{0,3}"),"canonical decimal response-local index string required");int value=Integer.parseInt(token);RegistryJson.require(value<MAXIMUM_NODES,"node index exceeds bound");return value;}
    private static java.math.BigInteger witness(JsonNode node){String token=RegistryJson.text(node);RegistryJson.require(token.matches("[1-9][0-9]{0,19}"),"canonical uint64 witness string required");var value=new java.math.BigInteger(token);RegistryJson.require(value.compareTo(RegistryJson.U64)<=0,"uint64 witness overflow");return value;}
}

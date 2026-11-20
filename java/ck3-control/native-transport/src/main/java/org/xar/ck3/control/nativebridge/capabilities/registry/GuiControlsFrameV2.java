package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Current pre-action control DATA. Even a submitted callback is not a post-state or SAVE receipt. */
public record GuiControlsFrameV2(Operation operation,Status status,CoreFrame coreFrame,Window window,
        boolean coreBeforeVerified,boolean sourceAbiPinsVerified,boolean riteSourceVerified,OptionalLong sourceRiteId,
        boolean queryAvailable,Optional<BigInteger> queryGeneration,Optional<GuiRootIndexFrame.OwnerWitness> ownerWitness,
        Optional<List<Widget>> widgets,boolean effectAttempted,boolean nativeHandled,boolean verificationPending,Optional<String> unavailableReason) {
    public static final String QUERY_STEP="query-scripted-widget-controls-v2",ACTIVATE_STEP="activate-scripted-widget-control-v2";
    public static final String SCHEMA="ck3.scripted_widget_controls.v2",REQUEST_SCHEMA="ck3.scripted_widget_controls_request.v2",BACKEND=GuiRootIndexFrame.BACKEND;
    public static final String QUERY_CAPABILITY="game.query.scripted-widget-controls.v2",ACTIVATE_CAPABILITY="game.command.activate-scripted-widget-control.v2";
    public static final ExactCk3Build BUILD=GuiRootIndexFrame.BUILD;
    public static final int MAXIMUM_ROWS=2048,MAXIMUM_BYTES=2*1024*1024;
    public ExactCk3Build build(){return BUILD;}
    public static final Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status","query_available","application_main_observed","core_before_verified","source_abi_pins_verified","addresses_redacted","complete_snapshot","full_snapshot_before_verified","complete_gui_tree","effect_attempted","native_handled","verification_pending","effect_confirmed","physical_save_confirmed","core_frame","window_name","rite_source_verified","source_rite_id","query_generation","owner_witness","widgets","unavailable_reason");
    public enum Operation { QUERY,ACTIVATE;
        public String step(){return this==QUERY?QUERY_STEP:ACTIVATE_STEP;}
        public static Operation step(String value){if(QUERY_STEP.equals(value))return QUERY;if(ACTIVATE_STEP.equals(value))return ACTIVATE;throw new IllegalArgumentException("fixed current controls step required");}
    }
    public enum Window { FAITH("faith_window"),RITE("rite_creation_window"),HUD_LAYER("hud_layer"),WINDOWS_LAYER("windows_layer");
        private final String wire;Window(String value){wire=value;}public String wire(){return wire;}
        public boolean navigationRoot(){return this==HUD_LAYER||this==WINDOWS_LAYER;}
        public String navigationRuntimeName(){return switch(this){case HUD_LAYER->"faith_button";case WINDOWS_LAYER->"edit_rite";default->throw new IllegalStateException("Only fixed navigation roots have a literal selector");};}
        public static Window wire(String value){for(var w:values())if(w.wire.equals(value))return w;throw new IllegalArgumentException("Only the four exact current control roots are supported");}
    }
    public enum Status { AVAILABLE,SUBMITTED,EXPIRED,STALE_CORE,STALE_GUI,DISABLED,INDETERMINATE,UNAVAILABLE;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static Status wire(String value){for(var s:values())if(s.wire().equals(value))return s;throw new IllegalArgumentException("fixed controls result status required");}
    }
    public record Widget(BigInteger widgetId,String runtimeName,String childPath,boolean effectiveVisible,boolean enabled,boolean nativeCallbackAdmissible){
        public Widget{positive64(widgetId);GuiWindowFrame.nodeName(runtimeName);path(childPath);RegistryJson.require(!nativeCallbackAdmissible||effectiveVisible&&enabled,"admissible callback must remain visible and enabled");}
    }
    public GuiControlsFrameV2 {
        Objects.requireNonNull(operation);Objects.requireNonNull(status);Objects.requireNonNull(coreFrame);Objects.requireNonNull(window);Objects.requireNonNull(sourceRiteId);
        Objects.requireNonNull(queryGeneration);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(widgets);Objects.requireNonNull(unavailableReason);
        RegistryJson.require(coreFrame.build()==BUILD&&coreBeforeVerified==(coreFrame instanceof CoreFrame.Partial)&&ownerWitness.isPresent()==coreBeforeVerified,"Core-before/witness must remain atomic, not a post-action claim");
        if(coreBeforeVerified)requireCore((CoreFrame.Partial)coreFrame);
        RegistryJson.require(!sourceAbiPinsVerified||coreBeforeVerified,"ABI source proof needs the actual pre-action Core");
        RegistryJson.require(riteSourceVerified==sourceRiteId.isPresent()&&(!riteSourceVerified||window==Window.RITE&&coreBeforeVerified),"Rite source cannot be borrowed by a Faith query");
        sourceRiteId.ifPresent(RiteDraftCostsFrameV2::sourceRiteId);queryGeneration.ifPresent(GuiControlsFrameV2::positive64);
        RegistryJson.require(operation!=Operation.ACTIVATE||window==Window.RITE||window.navigationRoot(),"Only Rite or fixed navigation roots support activation");
        RegistryJson.require(!nativeHandled||effectAttempted,"native_handled requires a real attempted callback");
        RegistryJson.require(!effectAttempted||operation==Operation.ACTIVATE&&verificationPending,"attempted effects remain verification-pending");
        if(operation==Operation.QUERY)RegistryJson.require(!effectAttempted&&!nativeHandled&&!verificationPending,"readonly query cannot attempt a callback");
        RegistryJson.require(widgets.isPresent()==queryAvailable,"widgets are present only for a real available query");
        if(queryAvailable){
            RegistryJson.require(operation==Operation.QUERY&&status==Status.AVAILABLE&&coreBeforeVerified&&sourceAbiPinsVerified&&queryGeneration.isPresent()
                    &&(window!=Window.RITE||riteSourceVerified),"available query needs original source/generation");
            var rows=List.copyOf(widgets.orElseThrow());RegistryJson.require(!rows.isEmpty()&&rows.size()<=MAXIMUM_ROWS,"bounded nonempty actual controls required");
            var paths=new HashSet<String>();long nameBytes=0;
            for(int i=0;i<rows.size();i++){var row=rows.get(i);RegistryJson.require(row.widgetId().equals(BigInteger.valueOf(i+1L))&&paths.add(row.childPath()),"response-local widgets require exact unique row identities/paths");
                RegistryJson.require(!row.nativeCallbackAdmissible()||window==Window.RITE||window.navigationRoot()&&row.runtimeName().equals(window.navigationRuntimeName()),"Only Rite or the fixed navigation literal may carry Native callback admission");nameBytes+=row.runtimeName().getBytes(java.nio.charset.StandardCharsets.UTF_8).length;}
            RegistryJson.require(nameBytes<=131072,"current controls name budget exceeded");widgets=Optional.of(rows);
        }else if(operation==Operation.QUERY)RegistryJson.require(queryGeneration.isEmpty(),"unavailable query retains null generation");
        if(status==Status.SUBMITTED)RegistryJson.require(operation==Operation.ACTIVATE&&coreBeforeVerified&&(window==Window.RITE?riteSourceVerified:window.navigationRoot()&&sourceAbiPinsVerified)&&effectAttempted&&verificationPending&&queryGeneration.isPresent(),"submitted is a pending original callback, not completion");
        boolean reasonAbsent=queryAvailable||coreBeforeVerified&&status==Status.SUBMITTED;
        RegistryJson.require(unavailableReason.isEmpty()==reasonAbsent,"exact null/unavailable reason rule required");unavailableReason.ifPresent(value->RegistryJson.require(!value.isEmpty(),"nonempty rejection reason required"));
    }
    public static void requireCore(CoreFrame.Partial frame){GuiRootIndexFrame.requireExpectedCore(frame);RegistryJson.require(frame.prefix().playedCharacterId()!=0,"controls require a nonzero original played character");}
    public static BigInteger positive64(BigInteger value){Objects.requireNonNull(value);RegistryJson.require(value.signum()>0&&value.compareTo(RegistryJson.U64)<=0,"positive exact uint64 required");return value;}
    static BigInteger uint64String(JsonNode node){String text=RegistryJson.text(node);RegistryJson.require(text.matches("[1-9][0-9]{0,19}"),"canonical positive uint64 string required");return positive64(new BigInteger(text));}
    private static String path(String value){RegistryJson.require(value!=null&&value.length()<=319,"bounded response-local child path required");if(!value.isEmpty()){String[] parts=value.split("/",-1);RegistryJson.require(parts.length<=64,"bounded control path depth required");for(String part:parts)RegistryJson.require(part.matches("0|[1-9][0-9]{0,3}")&&Integer.parseInt(part)<4096,"canonical child index required");}return value;}
    public static GuiControlsFrameV2 decode(RawJson raw){
        RegistryJson.require(raw.bytes().length<=MAXIMUM_BYTES,"bounded current controls frame required");var row=RegistryJson.object(raw);RegistryJson.keys(row,FIELDS);
        RegistryJson.require(SCHEMA.equals(RegistryJson.text(row.get("schema")))&&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))&&BUILD.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),"exact current controls source tuple required");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted")),"controls cannot expose addresses");for(String key:Set.of("complete_snapshot","full_snapshot_before_verified","complete_gui_tree","effect_confirmed","physical_save_confirmed"))RegistryJson.require(!RegistryJson.bool(row.get(key)),"current controls cannot claim Full/effect/save: "+key);
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));boolean main=core instanceof CoreFrame.Partial||((CoreFrame.Unavailable)core).applicationMainObserved();RegistryJson.require(main==RegistryJson.bool(row.get("application_main_observed")),"actual main-owner flag differs from Core");
        Optional<GuiRootIndexFrame.OwnerWitness> witness=Optional.empty();if(!row.get("owner_witness").isNull()){var w=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(w,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));witness=Optional.of(new GuiRootIndexFrame.OwnerWitness(uint64String(w.get("connection_generation")),uint64String(w.get("ticket_sequence")),uint64String(w.get("pump_epoch")),RegistryJson.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
        Optional<List<Widget>> widgets=Optional.empty();if(!row.get("widgets").isNull()){var value=row.get("widgets");RegistryJson.require(value.isArray()&&value.size()<=MAXIMUM_ROWS,"bounded controls rows required");var rows=new ArrayList<Widget>();for(var n:value){var w=RegistryJson.object(n);RegistryJson.keys(w,Set.of("widget_id","runtime_name","child_path","effective_visible","enabled","native_callback_admissible"));RegistryJson.require(w.get("runtime_name").isTextual()&&w.get("child_path").isTextual(),"actual names/path strings required");rows.add(new Widget(uint64String(w.get("widget_id")),w.get("runtime_name").textValue(),w.get("child_path").textValue(),RegistryJson.bool(w.get("effective_visible")),RegistryJson.bool(w.get("enabled")),RegistryJson.bool(w.get("native_callback_admissible"))));}widgets=Optional.of(rows);}
        return new GuiControlsFrameV2(Operation.step(RegistryJson.text(row.get("step"))),Status.wire(RegistryJson.text(row.get("status"))),core,Window.wire(RegistryJson.text(row.get("window_name"))),RegistryJson.bool(row.get("core_before_verified")),RegistryJson.bool(row.get("source_abi_pins_verified")),RegistryJson.bool(row.get("rite_source_verified")),row.get("source_rite_id").isNull()?OptionalLong.empty():OptionalLong.of(RegistryJson.integer(row.get("source_rite_id"),BigInteger.ZERO,BigInteger.valueOf(0xffff_fffeL)).longValueExact()),RegistryJson.bool(row.get("query_available")),row.get("query_generation").isNull()?Optional.empty():Optional.of(uint64String(row.get("query_generation"))),witness,widgets,RegistryJson.bool(row.get("effect_attempted")),RegistryJson.bool(row.get("native_handled")),RegistryJson.bool(row.get("verification_pending")),row.get("unavailable_reason").isNull()?Optional.empty():Optional.of(RegistryJson.text(row.get("unavailable_reason"))));
    }
}

package org.xar.ck3.control.build;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/** Fixed native Lobby layout observation. Decoding grants no loaded/source or selection authority. */
public final class FrontendLobbyCallbackObservation {
    private FrontendLobbyCallbackObservation() { }
    public static final String SCOPE = "lobby_random_callback";
    public static final String STEP = "inspect-gui-window-tree-v1";
    public static final String EXE_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final long IMAGE = 0x61C5000L, THUNK = 0x3AA30E0L, EXPRESSION = 0x3A9F960L;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public enum Receiver { UNKNOWN, ABSENT, PRESENT }
    public enum UnavailableKind { NATIVE_ERROR, ROOT_UNAVAILABLE }
    public sealed interface Reply permits Observed, Unavailable { }
    public record Chain(int index, long typeId, long kindRaw, long targetRva, boolean userDataPresent) { }
    public record Expression(long finalTypeId, long finalKindRaw, long finalTargetRva,
            boolean finalUserDataPresent, long receiverTypeId, int receiverFlagRaw, List<Chain> chain) {
        public Expression { chain = List.copyOf(chain); }
    }
    public record Indirect(long targetRva, Receiver receiver, Optional<Expression> expression) { }
    public record Callback(int index, long vtableRva, long slot2Rva, Optional<Indirect> indirect) {
        public Receiver receiver() { return indirect.map(Indirect::receiver).orElse(Receiver.UNKNOWN); }
    }
    public record Observed(String requestId, String group, List<Callback> callbacks) implements Reply {
        public Observed { callbacks = List.copyOf(callbacks); }
        public boolean selectedIdentityProven() { return false; }
        public boolean eligibilityProven() { return false; }
        public boolean drawCompletionProven() { return false; }
        public boolean callbackAbiQualified() { return false; }
    }
    public record Unavailable(String requestId, UnavailableKind kind, Optional<String> nativeError) implements Reply { }

    /** Argument payload for the existing admitted native read, never caller pointers/names/limits. */
    public static String arguments() {
        return "{\"expected_revision\":0,\"window_kind\":\"lobby_random_callback\"}";
    }
    public static Reply decode(byte[] originalFrame, String expectedRequestId) throws IOException {
        require(originalFrame != null && originalFrame.length > 0 && originalFrame.length <= 1048576, "bounded original frame required");
        require(expectedRequestId != null && !expectedRequestId.isBlank(), "actual request identity required");
        JsonNode frame = JSON.readTree(originalFrame);
        boolean ok = bool(field(frame, "ok"));
        exact(frame, ok ? Set.of("type","protocol_version","request_id","ok","result")
                : Set.of("type","protocol_version","request_id","ok","error"));
        require(text(field(frame,"type")).equals("command_result") && integer(field(frame,"protocol_version"),1)==1
                && text(field(frame,"request_id")).equals(expectedRequestId), "native response crossed protocol/request");
        if (!ok) return new Unavailable(expectedRequestId, UnavailableKind.NATIVE_ERROR,
                Optional.of(text(field(frame,"error"))));
        JsonNode result = field(frame,"result");
        boolean available = bool(field(result,"root_available"));
        var fields = new HashSet<>(Set.of("step","accepted","status","scope_root_name","root_available","truncated","widget_count","widgets"));
        if (available) fields.add("callback_binding_source_12004");
        exact(result,fields);
        require(text(field(result,"step")).equals(STEP) && bool(field(result,"accepted"))
                && text(field(result,"scope_root_name")).equals(SCOPE) && !bool(field(result,"truncated")),
                "fixed untruncated native callback scope required");
        JsonNode widgets = field(result,"widgets");
        require(widgets.isArray(), "widget array required");
        if (!available) {
            require(text(field(result,"status")).equals("unavailable") && integer(field(result,"widget_count"),0)==0
                    && widgets.isEmpty(), "unavailable native read carried partial callbacks");
            return new Unavailable(expectedRequestId,UnavailableKind.ROOT_UNAVAILABLE,Optional.empty());
        }
        require(text(field(result,"status")).equals("available") && integer(field(result,"widget_count"),1)==1
                && widgets.size()==1, "exact fixed leaf required");
        source(field(result,"callback_binding_source_12004"));
        JsonNode widget = widgets.get(0);
        exact(widget,Set.of("runtime_name","child_path","depth","child_count","vtable_rva","effective_visible","enabled","standard_click_binding_12004"));
        require(text(field(widget,"runtime_name")).isEmpty() && text(field(widget,"child_path")).isEmpty()
                && integer(field(widget,"depth"),0)==0 && integer(field(widget,"child_count"),0)==0
                && bool(field(widget,"effective_visible")) && bool(field(widget,"enabled")), "fixed visible random button leaf required");
        rva(field(widget,"vtable_rva"),false);
        JsonNode binding = field(widget,"standard_click_binding_12004");
        exact(binding,Set.of("button_base_slot13","group","callbacks"));
        String group = text(field(binding,"group"));
        require(bool(field(binding,"button_base_slot13")) && Set.of("primary","fallback").contains(group), "actual standard click group required");
        JsonNode rows = field(binding,"callbacks");
        require(rows.isArray() && !rows.isEmpty() && rows.size()<=256, "bounded nonempty callbacks required");
        List<Callback> callbacks = new ArrayList<>();
        for (int i=0;i<rows.size();i++) {
            JsonNode row=rows.get(i);
            long slot=rva(field(row,"callback_slot2_rva"),false);
            var keys = new HashSet<>(Set.of("index","callback_vtable_rva","callback_slot2_rva"));
            if (slot==THUNK) keys.add("indirect_target_3aa30e0");
            exact(row,keys);
            require(integer(field(row,"index"),255)==i, "callback index drift");
            long table=rva(field(row,"callback_vtable_rva"),false);
            require(table<=IMAGE-24, "callback vtable truncated");
            Optional<Indirect> indirect=Optional.empty();
            if (slot==THUNK) {
                JsonNode item=field(row,"indirect_target_3aa30e0");
                long target=rva(field(item,"native_target_8_rva"),false);
                var innerKeys=new HashSet<>(Set.of("native_target_8_rva","receiver_f0_present"));
                if (target==EXPRESSION) innerKeys.add("expression_3a9f960");
                exact(item,innerKeys);
                indirect=Optional.of(new Indirect(target,bool(field(item,"receiver_f0_present")) ? Receiver.PRESENT : Receiver.ABSENT,
                        target==EXPRESSION ? Optional.of(expression(field(item,"expression_3a9f960"))) : Optional.empty()));
            }
            callbacks.add(new Callback(i,table,slot,indirect));
        }
        return new Observed(expectedRequestId,group,callbacks);
    }
    private static Expression expression(JsonNode value) {
        exact(value,Set.of("chain_count_24_raw","final_type_id_30","final_kind_34_raw","final_target_38_rva","final_user_data_40_present",
                "receiver_type_id_48","receiver_flag_4c_raw","chain_calls"));
        int count=(int)integer(field(value,"chain_count_24_raw"),16);
        JsonNode calls=field(value,"chain_calls"); require(calls.isArray() && calls.size()==count,"complete bounded expression chain required");
        List<Chain> chain=new ArrayList<>();
        for(int i=0;i<count;i++) {
            JsonNode call=calls.get(i); exact(call,Set.of("index","type_id_0","kind_4_raw","native_target_8_rva","user_data_10_present"));
            require(integer(field(call,"index"),15)==i,"expression chain index drift");
            chain.add(new Chain(i,integer(field(call,"type_id_0"),0xffffffffL),integer(field(call,"kind_4_raw"),0xffffffffL),
                    rva(field(call,"native_target_8_rva"),false),bool(field(call,"user_data_10_present"))));
        }
        long kind=integer(field(value,"final_kind_34_raw"),0xffffffffL), target=rva(field(value,"final_target_38_rva"),true);
        require((kind==3 || kind==4) ? target!=0 : target==0,"final target role differs");
        return new Expression(integer(field(value,"final_type_id_30"),0xffffffffL),kind,target,
                bool(field(value,"final_user_data_40_present")),integer(field(value,"receiver_type_id_48"),0xffffffffL),
                (int)integer(field(value,"receiver_flag_4c_raw"),255),chain);
    }
    private static void source(JsonNode source) {
        exact(source,Set.of("executable_sha256","button_base_slot13_rva","group_dispatch_rva","input_modifier",
                "indirect_target_thunk_rva","indirect_target_thunk_bytes_sha256","expression_target_bridge_rva",
                "expression_builder_rva","expression_eval_rva","expression_layout_bytes_sha256"));
        require(text(field(source,"executable_sha256")).equals(EXE_SHA)
                && integer(field(source,"button_base_slot13_rva"),IMAGE)==0x3AA0D20L
                && integer(field(source,"group_dispatch_rva"),IMAGE)==0x3A9FA30L
                && integer(field(source,"input_modifier"),0)==0
                && integer(field(source,"indirect_target_thunk_rva"),IMAGE)==THUNK
                && text(field(source,"indirect_target_thunk_bytes_sha256")).equals("7a37683abfa5cb9317164e719bc14ba7cc067f79fee8e086267a11d8b18f3563")
                && integer(field(source,"expression_target_bridge_rva"),IMAGE)==EXPRESSION
                && integer(field(source,"expression_builder_rva"),IMAGE)==0x3AC38C0L
                && integer(field(source,"expression_eval_rva"),IMAGE)==0x3E4C090L
                && text(field(source,"expression_layout_bytes_sha256")).equals("7412efd136e722993b71a8810f5d585347cde53104ba0a107551eb324ff18963"),"actual .4 callback source pins required");
    }
    private static JsonNode field(JsonNode value,String name) {
        require(value!=null && value.isObject() && value.has(name),"missing native field "+name); return value.get(name);
    }
    private static void exact(JsonNode value,Set<String> fields) {
        require(value!=null && value.isObject(),"native object required");
        Set<String> actual=new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(fields),"native fields differ");
    }
    private static String text(JsonNode value) { require(value.isTextual(),"native text required"); return value.textValue(); }
    private static boolean bool(JsonNode value) { require(value.isBoolean(),"native bool required"); return value.booleanValue(); }
    private static long integer(JsonNode value,long maximum) {
        require(value.isIntegralNumber() && value.canConvertToLong() && value.longValue()>=0 && value.longValue()<=maximum,
                "native bounded integer required"); return value.longValue();
    }
    private static long rva(JsonNode value,boolean zero) { long result=integer(value,IMAGE-1); require(zero || result>0,"nonzero native RVA required"); return result; }
    private static void require(boolean condition,String reason) { if(!condition)throw new IllegalArgumentException(reason); }
}

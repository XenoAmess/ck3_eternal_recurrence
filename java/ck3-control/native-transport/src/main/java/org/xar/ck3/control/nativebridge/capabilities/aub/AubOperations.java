package org.xar.ck3.control.nativebridge.capabilities.aub;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The original exact .3 AUB operation family. No Native write or writer authority is created here. */
public final class AubOperations {
    private static final Set<String> DETAIL_FIELDS=Set.of("schema","step","read_only","game_version","executable_sha256","native_revision","connection_generation","game_pid","played_character_id","date_raw",
            "group_count","row_count","matching_row_count","row_context_reference_key","detail_actor_reference_key","available","owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified",
            "decisions_tree_complete","decisions_root_visible","row_owner_verified","row_scope_reference_available","detail_tree_complete","detail_root_visible","detail_definition_available","detail_definition_matches_target",
            "detail_actor_binding_verified","row_widget_datacontext_verified","action_qualified","decision_key","detail_decision_key","unavailable_reason");
    static final Set<String> OPTIONS_FIELDS=Set.of("schema","step","read_only","game_version","executable_sha256","native_revision","connection_generation","game_pid","played_character_id","date_raw",
                "tooltip_available","enabled_available","rendered_down_available","production_confirmed","before_actual_model","after_actual_model","unavailable_reason","policy");
    static final Set<String> SELECT_FIELDS=Set.of("schema","step","read_only","game_version","executable_sha256","native_revision","connection_generation","game_pid","played_character_id","date_raw",
                    "tooltip_available","enabled_available","rendered_down_available","production_confirmed","before_actual_model","after_actual_model","unavailable_reason","before_policy","after_policy",
                    "expected_selected_key","desired_key","already_selected","dispatch_invoked","native_call_completed","postcondition_verified","verification_pending");
    static final Set<String> CONFIRM_FIELDS=Set.of("schema","step","read_only","game_version","executable_sha256","selected_key","target_child_path","receiver_qualified","selected_policy_revalidated",
                "dispatch_attempted","dispatch_invoked","native_handled","postcondition_verified","verification_pending","before_actual_model","state_before","state_after","actual_policy_before","unavailable_reason","product_acceptance_proven");
    public static final String QUERY = "query-aub-policy-options-v1";
    public static final String SELECT = "select-aub-policy-option-v1";
    public static final String CONFIRM = "confirm-aub-policy-v1";
    public static final String OBSERVER = "java.aub.original-independent-postcondition.v1";
    private static final BigInteger U32 = new BigInteger("4294967295");
    private AubOperations() { }
    public enum PolicyKey {
        TREASURY_PAUSE("aub_policy_treasury_only_pause_choice"), TREASURY_CONTINUE("aub_policy_treasury_only_continue_choice"),
        PERSONAL_PAUSE("aub_policy_personal_only_pause_choice"), PERSONAL_CONTINUE("aub_policy_personal_only_continue_choice"),
        TREASURY_FIRST_PAUSE("aub_policy_treasury_first_pause_choice"), TREASURY_FIRST_CONTINUE("aub_policy_treasury_first_continue_choice");
        private final String wire;
        PolicyKey(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static PolicyKey parse(String value) {
            for (PolicyKey key : values()) if (key.wire.equals(value)) return key;
            throw new IllegalArgumentException("unknown fixed AUB policy key");
        }
    }
    public sealed interface Mutation permits Select, Confirm { PolicyKey expected(); String step(); }
    public record Select(PolicyKey expected, PolicyKey desired) implements Mutation {
        public Select { Objects.requireNonNull(expected); Objects.requireNonNull(desired); }
        @Override public String step() { return SELECT; }
    }
    public record Confirm(PolicyKey expected) implements Mutation {
        public Confirm { Objects.requireNonNull(expected); }
        @Override public String step() { return CONFIRM; }
    }
    public record Entry(PolicyKey key, boolean selected) { public Entry { Objects.requireNonNull(key); } }
    public record Policy(List<Entry> entries, Optional<PolicyKey> selected, int selectedIndex) {
        public Policy {
            entries = List.copyOf(entries); Objects.requireNonNull(selected);
            need(entries.size() == 6 && entries.stream().map(Entry::key).distinct().count() == 6, "complete unique six-policy entries required");
            int observed = -1;
            for (int index=0; index<entries.size(); index++) if(entries.get(index).selected()) { need(observed == -1,"multiple actual selected policies"); observed=index; }
            need(observed == selectedIndex && selected.equals(observed < 0 ? Optional.empty() : Optional.of(entries.get(observed).key())), "actual selected index/key/entries differ");
        }
    }
    public record Options(ObservationIdentity before, BigInteger connectionGeneration, Policy policy, RawJson original) {
        public Options { Objects.requireNonNull(before); Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(policy); Objects.requireNonNull(original); }
    }
    public record SelectedDetail(int groupCount, int rowCount, BigInteger actor) {
        public SelectedDetail { Objects.requireNonNull(actor); need(groupCount>=0&&groupCount<=64&&rowCount>=0&&rowCount<=2048,"bounded actual decision rows required"); }
    }
    public record NativeMutation(Mutation mutation, boolean nativeVerified, RawJson original) {
        public NativeMutation { Objects.requireNonNull(mutation); Objects.requireNonNull(original); }
    }
    public record Sources(ExactRef businessDefinition, ExactRef policyDefinition, ExactRef decoder) {
        public Sources { for(ExactRef ref:List.of(businessDefinition,policyDefinition,decoder)) need(ref.bytes()>0,"original complete AUB source closure required"); }
        public List<ExactRef> refs() { return List.of(businessDefinition,policyDefinition,decoder); }
    }
    public static String capability(String step) { need(Set.of(QUERY,SELECT,CONFIRM,AubBusinessStateRead.STEP).contains(step),"fixed AUB operation required"); return "game.command."+step; }
    public static final class Registration {
        private final AubBusinessStateRead.Registration business;
        private final ReadContract<Options> options;
        private final NativeGameTransport transport;
        private final Sources sources;
        public Registration(NativeGameTransport actualTransport, ActionPorts.OutcomeArchive actualArchive, Sources actualSources) {
            transport=Objects.requireNonNull(actualTransport); sources=Objects.requireNonNull(actualSources);
            business=new AubBusinessStateRead.Registration(actualTransport,actualArchive,sources.businessDefinition());
            options=new ReadContract<>("java.aub.original-policy-options.v1",new OperationKey(QUERY),Optional.of(capability(QUERY)),capability(QUERY),
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    sources.policyDefinition(),(request,id)->business.prepareFixed(request,QUERY,capability(QUERY)),this::decodeOptions,this::decodeOptions);
        }
        public AubBusinessStateRead.Registration business() { return business; }
        public ReadContract<Options> options() { return options; }
        public Sources sources() { return sources; }
        public Options decodeOptions(PlanningReadReceipt receipt) {
            try {
                need(receipt.request().operation().equals(options.operation())&&receipt.original().nativeOk(),"original successful AUB options query required");
                business.verifyReadWire(receipt,QUERY);
                business.validateOriginals(receipt.request().before(),receipt.before().binding(),capability(QUERY));
                business.validateOriginals(receipt.request().before(),receipt.after().binding(),capability(QUERY));
                return AubOperations.options(receipt.original().originalResultToken().orElseThrow(),receipt.request().before(),receipt.before().binding().connectionGeneration());
            } catch(IOException failure) { throw new UncheckedIOException("actual archived AUB options unavailable",failure); }
        }
        public AubBusinessStateRead.State decodeBusiness(PlanningReadReceipt receipt) {
            try {
                need(receipt.request().operation().equals(business.contract().operation())&&receipt.original().nativeOk(),"original successful AUB business query required");
                business.verifyReadWire(receipt,AubBusinessStateRead.STEP);
                business.validateOriginals(receipt.request().before(),receipt.before().binding()); business.validateOriginals(receipt.request().before(),receipt.after().binding());
                return AubBusinessStateRead.decodeMaterial(receipt.original().originalResultToken().orElseThrow(),receipt.request().before(),receipt.before().binding().connectionGeneration());
            } catch(IOException failure) { throw new UncheckedIOException("actual archived AUB business state unavailable",failure); }
        }
        public NativeRequest prepare(ActionCommand command, Mutation mutation, BigInteger generation) {
            try {
                need(command.operation().value().equals(mutation.step()),"AUB typed mutation changed operation");
                var held=transport.latestObservedSnapshot().orElseThrow(()->new IOException("actual AUB held snapshot unavailable"));
                need(held.session().sessionId().equals(command.sessionId())&&held.session().connectionGeneration().equals(generation),"AUB mutation changed actual session/generation");
                AubBusinessStateRead.validateFrame(command.before(),generation,(NativeWire.Snapshot)NativeWire.decode(held.originalPacket()),transport.originalHello(),capability(mutation.step()));
                need(transport.originalHello().capabilities().contains(capability(QUERY)),"AUB independent original policy observer capability absent");
                if(mutation instanceof Confirm)need(transport.originalHello().capabilities().contains(AubBusinessStateRead.CAPABILITY),"AUB independent original business observer capability absent");
                ObjectNode row=StrictJson.object();row.put("expected_player_character_id",command.before().frame().identity().player());row.put("expected_game_pid",command.before().game().pid());
                row.put("expected_connection_generation",generation);row.put("expected_selected_key",mutation.expected().wire());
                if(mutation instanceof Select select)row.put("desired_key",select.desired().wire());
                return new NativeRequest(mutation.step(),Optional.of(capability(mutation.step())),raw(row));
            } catch(IOException failure) { throw new UncheckedIOException("actual AUB mutation preparation unavailable",failure); }
        }
    }
    record OptionsMaterial(AubNativeStamp stamp,Policy policy) { OptionsMaterial {Objects.requireNonNull(stamp);Objects.requireNonNull(policy);} }
    record MutationMaterial(AubNativeStamp stamp,NativeMutation value) { MutationMaterial {Objects.requireNonNull(stamp);Objects.requireNonNull(value);} }
    public static Options options(RawJson original, ObservationIdentity before, BigInteger generation) throws IOException {
        OptionsMaterial value=optionsMaterial(original);need(value.stamp().equals(AubNativeStamp.expected(before,generation)),"AUB policy stamps differ from actual observation");
        return new Options(before,generation,value.policy(),original);
    }
    static OptionsMaterial optionsMaterial(RawJson original)throws IOException {
        ObjectNode row=object(original);AubNativeStamp stamp=AubNativeStamp.read(row);outer(row,QUERY,true,stamp);
        exactOptionalBackend(row,OPTIONS_FIELDS);selectedDetail(row.get("before_actual_model"),stamp);selectedDetail(row.get("after_actual_model"),stamp);
        return new OptionsMaterial(stamp,policy(row.get("policy"),stamp));
    }
    public static NativeMutation nativeMutation(RawJson original,Mutation mutation,ObservationIdentity before,BigInteger generation) throws IOException {
        MutationMaterial value=mutationMaterial(original,mutation);need(value.stamp().equals(AubNativeStamp.expected(before,generation)),"AUB mutation stamps differ from actual observation");
        return value.value();
    }
    static MutationMaterial mutationMaterial(RawJson original,Mutation mutation) throws IOException {
        ObjectNode row=object(original);AubNativeStamp stamp=AubNativeStamp.read(mutation instanceof Select?row:NativeWire.object(row.get("state_before")));
        if(mutation instanceof Select select) {
            outer(row,SELECT,false,stamp);
            exactOptionalBackend(row,SELECT_FIELDS);
            selectedDetail(row.get("before_actual_model"),stamp);selectedDetail(row.get("after_actual_model"),stamp);
            Policy first=policy(row.get("before_policy"),stamp),last=policy(row.get("after_policy"),stamp);
            need(first.selected().equals(Optional.of(select.expected()))&&last.selected().equals(Optional.of(select.desired()))&&text(row,"expected_selected_key").equals(select.expected().wire())
                    &&text(row,"desired_key").equals(select.desired().wire()),"AUB actual policy transition differs");
            need(first.entries().stream().map(Entry::key).toList().equals(last.entries().stream().map(Entry::key).toList()),"AUB actual policy entry order changed");
            boolean same=select.expected()==select.desired();need(bool(row,"already_selected")==same&&bool(row,"dispatch_invoked")==!same&&bool(row,"native_call_completed")==!same,"AUB native select dispatch disposition differs");
            need(bool(row,"postcondition_verified")&&!bool(row,"verification_pending"),"AUB native select result unresolved; never retry");
            return new MutationMaterial(stamp,new NativeMutation(mutation,true,original));
        }
        Confirm confirm=(Confirm)mutation;
        build(row); exactOptionalBackend(row,CONFIRM_FIELDS);
        need(text(row,"schema").equals("ck3-aub-confirm-v1")&&text(row,"step").equals(CONFIRM)&&!bool(row,"read_only")&&text(row,"selected_key").equals(confirm.expected().wire())
                &&!text(row,"target_child_path").isEmpty()&&text(row,"unavailable_reason").isEmpty()&&!bool(row,"product_acceptance_proven"),"actual AUB Confirm unavailable or changed source");
        for(String key:List.of("receiver_qualified","selected_policy_revalidated","dispatch_attempted","dispatch_invoked"))need(bool(row,key),"AUB Confirm native receiver/dispatch proof absent");
        bool(row,"native_handled"); selectedDetail(row.get("before_actual_model"),stamp);
        var stateBefore=AubBusinessStateRead.material(raw(NativeWire.object(row.get("state_before"))));
        var stateAfter=AubBusinessStateRead.material(raw(NativeWire.object(row.get("state_after"))));
        need(stamp.equals(stateBefore.stamp())&&stamp.equals(stateAfter.stamp()),"AUB Confirm business DATA stamps differ");
        need(!stateBefore.flags().get(0).present()&&stateBefore.detail().effectivelyVisible(),"AUB Confirm requires original disabled visible detail");
        ObjectNode p=NativeWire.object(row.get("actual_policy_before"));exact(p,Set.of("ready","selected_key","entries"));
        need(bool(p,"ready")&&text(p,"selected_key").equals(confirm.expected().wire()),"AUB Confirm actual selected policy differs");
        List<Entry> entries=entries(p.get("entries"));need(entries.stream().filter(Entry::selected).map(Entry::key).toList().equals(List.of(confirm.expected())),"AUB Confirm selected entry differs");
        boolean observed=confirmed(stateAfter,confirm.expected()); boolean verified=bool(row,"postcondition_verified");
        need(verified==observed&&bool(row,"verification_pending")==!verified,"AUB Confirm actual flags/closure differ from native disposition");
        return new MutationMaterial(stamp,new NativeMutation(mutation,verified,original));
    }
    public static boolean confirmed(AubBusinessStateRead.State state,PolicyKey key) {return confirmed(state.flags(),state.detail(),key);}
    static boolean confirmed(AubBusinessStateRead.Material state,PolicyKey key) {return confirmed(state.flags(),state.detail(),key);}
    private static boolean confirmed(List<AubBusinessStateRead.Flag> flags,AubBusinessStateRead.DetailCensus detail,PolicyKey key) {
        int choice=key.ordinal();List<Boolean> expected=List.of(true,choice<2,choice>=2&&choice<4,choice%2==0);
        return !detail.effectivelyVisible()&&java.util.stream.IntStream.range(0,4).allMatch(index->flags.get(index).present()==expected.get(index));
    }
    public static List<ExpectedValue> actual(Mutation mutation,Optional<Policy> selection,Optional<AubBusinessStateRead.State> business) {
        if(mutation instanceof Select select) {
            Policy selected=selection.orElseThrow();need(selected.selected().equals(Optional.of(select.desired())),"independent later AUB policy differs");
            return List.of(new ExpectedText(new FieldKey("aub_selected_key"),selected.selected().orElseThrow().wire()),new ExpectedBoolean(new FieldKey("aub_independent_postcondition"),true));
        }
        need(confirmed(business.orElseThrow(),mutation.expected()),"independent later AUB flags/closure unverified");
        return List.of(new ExpectedText(new FieldKey("aub_confirmed_policy"),mutation.expected().wire()),new ExpectedBoolean(new FieldKey("aub_independent_postcondition"),true));
    }
    public static List<ExpectedValue> expected(Mutation mutation) {
        return List.of(new ExpectedText(new FieldKey(mutation instanceof Select?"aub_selected_key":"aub_confirmed_policy"),mutation instanceof Select select?select.desired().wire():mutation.expected().wire()),
                new ExpectedBoolean(new FieldKey("aub_independent_postcondition"),true));
    }
    public static RawJson publicOptions(Options value) { return AubPublicCodec.options(value); }
    private static void outer(ObjectNode row,String step,boolean readOnly,AubNativeStamp stamp)throws IOException {
        build(row);need(text(row,"schema").equals("ck3-aub-policy-options-v1")&&text(row,"step").equals(step)&&bool(row,"read_only")==readOnly&&text(row,"unavailable_reason").isEmpty(),"actual AUB policy operation unavailable");
        stamp.require(row);for(String key:List.of("tooltip_available","enabled_available","rendered_down_available","production_confirmed"))need(!bool(row,key),"AUB operation cannot grant unsupported product/UI proof");
    }
    private static Policy policy(JsonNode node,AubNativeStamp stamp)throws IOException {
        ObjectNode row=NativeWire.object(node);exact(row,Set.of("ready","unavailable_reason","played_character_id","decision_key","selected_key","selected_index","entries"));
        need(bool(row,"ready")&&text(row,"unavailable_reason").isEmpty()&&text(row,"decision_key").equals("enable_auto_build")&&number(row,"played_character_id",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).equals(stamp.actor()),"actual AUB policy owner/readiness differs");
        String selected=text(row,"selected_key");return new Policy(entries(row.get("entries")),selected.isEmpty()?Optional.empty():Optional.of(PolicyKey.parse(selected)),number(row,"selected_index",BigInteger.valueOf(-1),BigInteger.valueOf(5)).intValueExact());
    }
    private static List<Entry> entries(JsonNode node)throws IOException {
        need(node!=null&&node.isArray()&&node.size()==6,"complete six actual AUB entries required");var entries=new ArrayList<Entry>();
        for(JsonNode value:node){ObjectNode row=NativeWire.object(value);exact(row,Set.of("value_key","selected"));entries.add(new Entry(PolicyKey.parse(text(row,"value_key")),bool(row,"selected")));}
        need(entries.stream().map(Entry::key).distinct().count()==6,"duplicate/missing native AUB policy entry");return List.copyOf(entries);
    }
    private static SelectedDetail selectedDetail(JsonNode node,AubNativeStamp stamp)throws IOException {
        ObjectNode row=NativeWire.object(node);build(row);need(text(row,"schema").equals("ck3-ingame-decision-item-v1")&&text(row,"step").equals("query-ingame-decision-item-v1")&&bool(row,"read_only")&&bool(row,"available"),"actual selected AUB detail unavailable");
        exactOptionalBackend(row,DETAIL_FIELDS);need(text(row,"unavailable_reason").isEmpty(),"AUB successful detail cannot contain failed-query diagnostics");
        stamp.require(row);need(!row.has("selected_terms"),"exact .3 AUB cannot claim .4 selected terms");
        for(String key:List.of("row_widget_datacontext_verified","action_qualified"))need(!bool(row,key),"detail observation cannot qualify UI action");
        for(String key:List.of("owner_thread_verified","frame_verified","source_abi_pins_verified","gui_owner_binding_verified","decisions_tree_complete","decisions_root_visible","row_owner_verified",
                "detail_root_visible","detail_tree_complete","detail_definition_available","detail_definition_matches_target","detail_actor_binding_verified"))need(bool(row,key),"actual selected AUB detail proof absent: "+key);
        bool(row,"row_scope_reference_available");need(text(row,"decision_key").equals("enable_auto_build")&&text(row,"detail_decision_key").equals("enable_auto_build")&&number(row,"matching_row_count",BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE),"selected AUB detail target/uniqueness changed");
        number(row,"row_context_reference_key",BigInteger.ZERO,U32);BigInteger actor=number(row,"detail_actor_reference_key",BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE));need(actor.equals(stamp.actor()),"selected AUB detail changed actual actor");
        return new SelectedDetail(number(row,"group_count",BigInteger.ZERO,BigInteger.valueOf(64)).intValueExact(),number(row,"row_count",BigInteger.ZERO,BigInteger.valueOf(2048)).intValueExact(),actor);
    }
    private static void build(ObjectNode row) { need(text(row,"game_version").equals(AubBusinessStateRead.GAME_VERSION)&&text(row,"executable_sha256").equalsIgnoreCase(AubBusinessStateRead.GAME_SHA256),"AUB requires exact original .3 producer");if(row.has("backend_id"))need(text(row,"backend_id").equals("native-headless"),"AUB backend changed"); }
    private static void exactOptionalBackend(ObjectNode row,Set<String> base) { Set<String> expected=new HashSet<>(base);if(row.has("backend_id"))expected.add("backend_id");exact(row,expected); }
    private static void exact(ObjectNode row,Set<String> expected) { var keys=new HashSet<String>();row.fieldNames().forEachRemaining(keys::add);need(keys.equals(expected),"AUB exact native fields differ"); }
    private static ObjectNode object(RawJson raw)throws IOException { return NativeWire.object(NativeWire.parse(raw.bytes())); }
    private static RawJson raw(ObjectNode row) { return new RawJson(row.toString().getBytes(StandardCharsets.UTF_8)); }
    private static String text(ObjectNode row,String key) { JsonNode value=row.get(key);need(value!=null&&value.isTextual(),"AUB text field required: "+key);return value.textValue(); }
    private static boolean bool(ObjectNode row,String key) { JsonNode value=row.get(key);need(value!=null&&value.isBoolean(),"AUB boolean field required: "+key);return value.booleanValue(); }
    private static BigInteger number(ObjectNode row,String key,BigInteger min,BigInteger max)throws IOException { return NativeWire.integer(row.get(key),min,max); }
    private static void need(boolean condition,String detail) { StrictJson.require(condition,detail); }
}

package org.xar.ck3.control.nativebridge.capabilities.normalexit;

import static org.xar.ck3.control.contracts.StrictJson.require;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Closed production wire/data rules migrated from normal_exit_contract_v1.
 * These values do not grant a source inventory, retained handle, claim or submission authority.
 */
public final class NormalExitProtocol {
    public static final String STEP="normal-exit-map-v1", NATIVE_SCHEMA="ck3-normal-exit-map-v1";
    private static final BigInteger U32=new BigInteger("4294967295"), PLAYER=new BigInteger("2147483647");
    private static final ObjectMapper WIRE=new ObjectMapper();
    private NormalExitProtocol() { }
    public enum Action {
        QUERY_CONTEXT("query_context"),PREPARE_CONFIRMATION("prepare_confirmation"),CONTINUE_PREPARATION("continue_preparation"),
        DISABLE_EXIT_AUTOSAVE("disable_exit_autosave"),CONFIRM_DESKTOP("confirm_desktop");
        private final String wire;Action(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Action parse(String value){for(Action item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("closed normal-exit action required");}
    }
    public enum Status {
        UNAVAILABLE("unavailable"),CONTEXT_OBSERVED("context_observed"),CONFIRMATION_OBSERVED("confirmation_observed"),
        DISPATCH_PENDING("dispatch_pending"),DISPATCH_UNKNOWN_CLAIMED("dispatch_unknown_claimed"),AUTOSAVE_DISABLED("autosave_disabled");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Status parse(String value){for(Status item:values())if(item.wire.equals(value))return item;throw new IllegalArgumentException("unknown native normal-exit status");}
    }
    public record Binding(BigInteger nativeRevision,BigInteger playerId,BigInteger gamePid,BigInteger connectionGeneration,
            BigInteger creationFiletime,String sourceInventorySha256) {
        public Binding {positive(nativeRevision,StrictJson.UINT64_MAX);positive(playerId,PLAYER);positive(gamePid,U32);
            positive(connectionGeneration,StrictJson.UINT64_MAX);positive(creationFiletime,StrictJson.UINT64_MAX);sha(sourceInventorySha256);}
    }
    public record Request(String requestId,Action action,Binding binding,String nonce,Optional<String> contextSignature) {
        public Request {ascii(requestId);ascii(nonce);Objects.requireNonNull(action);Objects.requireNonNull(binding);Objects.requireNonNull(contextSignature);
            require((action==Action.QUERY_CONTEXT)==contextSignature.isEmpty(),"query omits signature; mutation requires it");contextSignature.ifPresent(NormalExitProtocol::sha);}
    }
    /** Same insertion order and integer JSON domain as the original Python production encoder. */
    public static byte[] payload(Request request) {
        Objects.requireNonNull(request);Binding b=request.binding();ObjectNode row=StrictJson.object();
        row.put("type","execute_step").put("protocol_version",1).put("request_id",request.requestId()).put("step",STEP).put("action",request.action().wire());
        row.put("expected_revision",b.nativeRevision()).put("expected_player_character_id",b.playerId()).put("expected_game_pid",b.gamePid())
                .put("expected_connection_generation",b.connectionGeneration()).put("expected_process_creation_filetime_100ns",b.creationFiletime())
                .put("source_inventory_sha256",b.sourceInventorySha256()).put("request_nonce",request.nonce());
        request.contextSignature().ifPresent(value->row.put("expected_exit_context_signature",value));
        try{return WIRE.writeValueAsBytes(row);}catch(IOException invalid){throw new IllegalArgumentException("normal-exit wire serialization failed",invalid);}
    }
    public static byte[] packet(Request request)throws IOException{return NativeWire.packet(payload(request));}
    public static Request decodeRequest(byte[] payload) {
        ObjectNode row=obj(StrictJson.parse(payload,65536));
        Set<String> fields=Set.of("type","protocol_version","request_id","step","action","expected_revision","expected_player_character_id",
                "expected_game_pid","expected_connection_generation","expected_process_creation_filetime_100ns","source_inventory_sha256","request_nonce");
        exact(row,with(fields,row.has("expected_exit_context_signature")?"expected_exit_context_signature":null));
        require("execute_step".equals(text(row,"type"))&&STEP.equals(text(row,"step")),"normal-exit wire identity differs");
        require(integer(row,"protocol_version",BigInteger.ONE,BigInteger.ONE).equals(BigInteger.ONE),"protocol1 required");
        return new Request(text(row,"request_id"),Action.parse(text(row,"action")),new Binding(integer(row,"expected_revision",BigInteger.ONE,StrictJson.UINT64_MAX),
                integer(row,"expected_player_character_id",BigInteger.ONE,PLAYER),integer(row,"expected_game_pid",BigInteger.ONE,U32),
                integer(row,"expected_connection_generation",BigInteger.ONE,StrictJson.UINT64_MAX),integer(row,"expected_process_creation_filetime_100ns",BigInteger.ONE,StrictJson.UINT64_MAX),
                text(row,"source_inventory_sha256")),text(row,"request_nonce"),row.has("expected_exit_context_signature")?Optional.of(text(row,"expected_exit_context_signature")):Optional.empty());
    }
    public record Proof(boolean exactBuild,boolean owner,boolean processIdentity,boolean sourceAbiPins,boolean stockFiles,boolean loadedSource,boolean frame) {
        public boolean complete(){return exactBuild&&owner&&processIdentity&&sourceAbiPins&&stockFiles&&loadedSource&&frame;}
    }
    public record Target(boolean readComplete,boolean rootExists,boolean rootVisible,boolean targetExists,boolean targetVisible,
            boolean targetEnabled,boolean uniqueTarget,boolean dispatchAdmitted,BigInteger vtableRva) {
        public Target {uint(vtableRva,StrictJson.UINT64_MAX);}
        public boolean complete(){return readComplete&&rootExists&&rootVisible&&targetExists&&targetVisible&&targetEnabled&&uniqueTarget&&dispatchAdmitted;}
    }
    public record Dispatch(boolean claimLatched,boolean invoked,boolean nativeHandled,boolean postReadComplete,boolean postconditionObserved) { }
    public record Autosave(boolean stateAvailable,boolean controlVisible,boolean controlEnabled,boolean shouldSave,
            boolean disableClaimed,boolean invoked,boolean postconditionObserved) { }
    public record Observation(Binding binding,Action action,Status status,BigInteger pumpEpoch,Proof proof,boolean contextSignatureVerified,
            boolean confirmationVisible,boolean orderlyExitVerified,boolean autosaveVerified,String contextSignature,String reason,
            List<Target> targets,List<Dispatch> dispatches,List<Boolean> stageConsumed,Optional<Autosave> exitAutosave) {
        public Observation {
            Objects.requireNonNull(binding);Objects.requireNonNull(action);Objects.requireNonNull(status);uint(pumpEpoch,StrictJson.UINT64_MAX);Objects.requireNonNull(proof);
            Objects.requireNonNull(contextSignature);Objects.requireNonNull(reason);targets=List.copyOf(targets);dispatches=List.copyOf(dispatches);stageConsumed=List.copyOf(stageConsumed);Objects.requireNonNull(exitAutosave);
            require(targets.size()==3&&dispatches.size()==3&&stageConsumed.size()==3,"three fixed exit stages required");
            require(!orderlyExitVerified&&!autosaveVerified,"native ACK cannot prove orderly exit or save integrity");
            if(status!=Status.UNAVAILABLE){
                if(status==Status.DISPATCH_UNKNOWN_CLAIMED){
                    if(!contextSignature.isEmpty())sha(contextSignature);
                } else {
                    sha(contextSignature);
                    require(proof.complete()&&pumpEpoch.signum()>0,"available exit lacks actual owner/source/frame proofs");
                }
            } else if(!contextSignature.isEmpty())sha(contextSignature);
            if(action==Action.QUERY_CONTEXT){require(dispatches.stream().noneMatch(value->value.claimLatched()||value.invoked()),"query cannot claim or dispatch");
                exitAutosave.ifPresent(value->require(!value.invoked()&&!value.postconditionObserved(),"query cannot toggle autosave"));}
            if(action!=Action.QUERY_CONTEXT&&status!=Status.UNAVAILABLE)require(contextSignatureVerified,"mutation requires verified backend context signature");
            if(action==Action.DISABLE_EXIT_AUTOSAVE)require(exitAutosave.isPresent()&&dispatches.stream().noneMatch(value->value.claimLatched()||value.invoked()),"autosave disable requires its provider and cannot dispatch exit stages");
            if(status==Status.AUTOSAVE_DISABLED){require(action==Action.DISABLE_EXIT_AUTOSAVE&&exitAutosave.isPresent(),"autosave disable identity/provider required");Autosave a=exitAutosave.orElseThrow();require(confirmationVisible
                    &&a.stateAvailable()&&a.controlVisible()&&a.controlEnabled()&&a.postconditionObserved()&&!a.shouldSave(),"autosave false not observed");}
            if(action==Action.CONTINUE_PREPARATION){require(!dispatches.get(0).claimLatched()&&!dispatches.get(0).invoked()&&!dispatches.get(2).claimLatched()&&!dispatches.get(2).invoked(),"continuation cannot dispatch stages0/2");
                if(status!=Status.UNAVAILABLE)require(stageConsumed.get(0)&&!stageConsumed.get(2)&&(!dispatches.get(1).claimLatched()||stageConsumed.get(1)),"continuation lacks actual remaining stage");}
            if(status==Status.CONFIRMATION_OBSERVED)require((action==Action.PREPARE_CONFIRMATION||action==Action.CONTINUE_PREPARATION)&&confirmationVisible&&targets.get(2).complete(),"official confirmation not observed");
        }
        public boolean continuePreparationReady(){return action==Action.QUERY_CONTEXT&&status==Status.CONTEXT_OBSERVED&&!confirmationVisible&&proof.complete()&&pumpEpoch.signum()>0
                &&stageConsumed.equals(List.of(true,false,false))&&targets.stream().allMatch(Target::readComplete)&&!targets.get(2).rootVisible()&&targets.get(1).complete()&&targets.get(1).vtableRva().signum()>0;}
    }
    private static final Set<String> OBS_FIELDS=Set.of("schema","step","action","status","native_revision","connection_generation","game_pid","played_character_id",
            "process_creation_filetime_100ns","pump_epoch","exact_build_verified","owner_verified","process_identity_verified","source_abi_pins_verified","stock_files_verified",
            "loaded_source_binding_verified","frame_verified","context_signature_verified","confirmation_visible","orderly_exit_verified","autosave_verified","exit_context_signature","reason","targets","dispatches","stage_consumed");
    public static Observation decodeObservation(JsonNode value,Binding expected,Action action) {
        ObjectNode row=obj(value);exact(row,with(OBS_FIELDS,row.has("exit_autosave")?"exit_autosave":null));
        require(NATIVE_SCHEMA.equals(text(row,"schema"))&&STEP.equals(text(row,"step"))&&action.wire().equals(text(row,"action")),"native normal-exit identity differs");
        require(integer(row,"native_revision",BigInteger.ONE,StrictJson.UINT64_MAX).equals(expected.nativeRevision())&&integer(row,"connection_generation",BigInteger.ONE,StrictJson.UINT64_MAX).equals(expected.connectionGeneration())
                &&integer(row,"game_pid",BigInteger.ONE,U32).equals(expected.gamePid())&&integer(row,"played_character_id",BigInteger.ONE,PLAYER).equals(expected.playerId())
                &&integer(row,"process_creation_filetime_100ns",BigInteger.ONE,StrictJson.UINT64_MAX).equals(expected.creationFiletime()),"native exit crossed its submission binding");
        var targets=new ArrayList<Target>();for(JsonNode n:three(row,"targets")){ObjectNode t=obj(n);exact(t,Set.of("read_complete","root_exists","root_visible","target_exists","target_visible","target_enabled","unique_target","dispatch_admitted","target_vtable_rva"));
            targets.add(new Target(bool(t,"read_complete"),bool(t,"root_exists"),bool(t,"root_visible"),bool(t,"target_exists"),bool(t,"target_visible"),bool(t,"target_enabled"),bool(t,"unique_target"),bool(t,"dispatch_admitted"),integer(t,"target_vtable_rva",BigInteger.ZERO,StrictJson.UINT64_MAX)));}
        var dispatches=new ArrayList<Dispatch>();for(JsonNode n:three(row,"dispatches")){ObjectNode t=obj(n);exact(t,Set.of("claim_latched","dispatch_invoked","native_handled","post_read_complete","postcondition_observed"));
            dispatches.add(new Dispatch(bool(t,"claim_latched"),bool(t,"dispatch_invoked"),bool(t,"native_handled"),bool(t,"post_read_complete"),bool(t,"postcondition_observed")));}
        var stages=new ArrayList<Boolean>();for(JsonNode n:three(row,"stage_consumed")){require(n.isBoolean(),"actual stage boolean required");stages.add(n.booleanValue());}
        Optional<Autosave> autosave=Optional.empty();if(row.has("exit_autosave")){ObjectNode a=obj(row.get("exit_autosave"));exact(a,Set.of("state_available","control_visible","control_enabled","should_save","disable_claimed","dispatch_invoked","postcondition_observed"));
            autosave=Optional.of(new Autosave(bool(a,"state_available"),bool(a,"control_visible"),bool(a,"control_enabled"),bool(a,"should_save"),bool(a,"disable_claimed"),bool(a,"dispatch_invoked"),bool(a,"postcondition_observed")));}
        return new Observation(expected,action,Status.parse(text(row,"status")),integer(row,"pump_epoch",BigInteger.ZERO,StrictJson.UINT64_MAX),
                new Proof(bool(row,"exact_build_verified"),bool(row,"owner_verified"),bool(row,"process_identity_verified"),bool(row,"source_abi_pins_verified"),bool(row,"stock_files_verified"),bool(row,"loaded_source_binding_verified"),bool(row,"frame_verified")),
                bool(row,"context_signature_verified"),bool(row,"confirmation_visible"),bool(row,"orderly_exit_verified"),bool(row,"autosave_verified"),text(row,"exit_context_signature"),text(row,"reason"),targets,dispatches,stages,autosave);
    }
    public static ObjectNode observationJson(Observation value) {
        ObjectNode r=StrictJson.object();Binding b=value.binding();Proof p=value.proof();r.put("schema",NATIVE_SCHEMA).put("step",STEP).put("action",value.action().wire()).put("status",value.status().wire());
        r.put("native_revision",b.nativeRevision()).put("connection_generation",b.connectionGeneration()).put("game_pid",b.gamePid()).put("played_character_id",b.playerId()).put("process_creation_filetime_100ns",b.creationFiletime()).put("pump_epoch",value.pumpEpoch());
        r.put("exact_build_verified",p.exactBuild()).put("owner_verified",p.owner()).put("process_identity_verified",p.processIdentity()).put("source_abi_pins_verified",p.sourceAbiPins()).put("stock_files_verified",p.stockFiles()).put("loaded_source_binding_verified",p.loadedSource()).put("frame_verified",p.frame());
        r.put("context_signature_verified",value.contextSignatureVerified()).put("confirmation_visible",value.confirmationVisible()).put("orderly_exit_verified",value.orderlyExitVerified()).put("autosave_verified",value.autosaveVerified()).put("exit_context_signature",value.contextSignature()).put("reason",value.reason());
        var ts=r.putArray("targets");for(Target t:value.targets())ts.addObject().put("read_complete",t.readComplete()).put("root_exists",t.rootExists()).put("root_visible",t.rootVisible()).put("target_exists",t.targetExists()).put("target_visible",t.targetVisible()).put("target_enabled",t.targetEnabled()).put("unique_target",t.uniqueTarget()).put("dispatch_admitted",t.dispatchAdmitted()).put("target_vtable_rva",t.vtableRva());
        var ds=r.putArray("dispatches");for(Dispatch d:value.dispatches())ds.addObject().put("claim_latched",d.claimLatched()).put("dispatch_invoked",d.invoked()).put("native_handled",d.nativeHandled()).put("post_read_complete",d.postReadComplete()).put("postcondition_observed",d.postconditionObserved());
        var ss=r.putArray("stage_consumed");value.stageConsumed().forEach(ss::add);value.exitAutosave().ifPresent(a->r.putObject("exit_autosave").put("state_available",a.stateAvailable()).put("control_visible",a.controlVisible()).put("control_enabled",a.controlEnabled()).put("should_save",a.shouldSave()).put("disable_claimed",a.disableClaimed()).put("dispatch_invoked",a.invoked()).put("postcondition_observed",a.postconditionObserved()));return r;
    }
    public record RetainedIdentity(BigInteger pid,BigInteger creationFiletime,String handleToken) {
        public RetainedIdentity {positive(pid,U32);positive(creationFiletime,StrictJson.UINT64_MAX);require(handleToken!=null&&!handleToken.isEmpty(),"retained original handle token required");}
    }
    public enum WaitState { SIGNALED,TIMEOUT,FAILED }
    public record ProcessObservation(RetainedIdentity identity,long waitResult,WaitState waitState,OptionalLong exitCode,boolean identityVerified,
            boolean exitObserved,BigInteger observedMonotonicNs,int timeoutMs,boolean deadlineReached,String clockDomain,List<String> errors) {
        public ProcessObservation {Objects.requireNonNull(identity);require(waitResult>=0&&waitResult<=0xffff_ffffL,"DWORD wait required");Objects.requireNonNull(waitState);Objects.requireNonNull(exitCode);
            exitCode.ifPresent(value->require(value>=0&&value<=0xffff_ffffL,"DWORD exit code required"));uint(observedMonotonicNs,StrictJson.UINT64_MAX);require(timeoutMs>=0&&timeoutMs<=5000,"bounded observation wait required");
            require(switch(waitState){case SIGNALED -> waitResult==0;case TIMEOUT -> waitResult==258;case FAILED -> waitResult!=0&&waitResult!=258;},"process wait state differs from its actual DWORD");
            require(exitObserved==(identityVerified&&waitState==WaitState.SIGNALED&&waitResult==0&&exitCode.isPresent()),"process exit observation differs from actual identity/signal/code facts");
            require("driver_monotonic_v1".equals(clockDomain),"original driver clock domain required");errors=List.copyOf(errors);errors.forEach(Objects::requireNonNull);}
    }
    public enum FactStatus { DISPATCH_UNKNOWN_CLAIMED,ORIGINAL_RETAINED_HANDLE_IDENTITY_MISMATCH,PROCESS_EXIT_OBSERVED_ZERO,PROCESS_EXIT_OBSERVED_NONZERO,DISPATCH_PENDING,OBSERVATION_FAILED_UNKNOWN;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}}
    public record Facts(FactStatus status,boolean processExitObserved,OptionalLong exitCode,boolean typedNormalExitObserved) {
        public Facts {Objects.requireNonNull(status);Objects.requireNonNull(exitCode);}
        public ObjectNode json(){ObjectNode r=StrictJson.object();r.put("claim_consumed",true).put("retry_authorized",false).put("process_exit_observed",processExitObserved).put("typed_normal_exit_observed",typedNormalExitObserved).put("autosave_verified",false).put("status",status.wire());if(exitCode.isPresent())r.put("exit_code",exitCode.getAsLong());else r.putNull("exit_code");return r;}
    }
    /** Classification consumes DATA observations, never opens/reopens a process or grants a retry. */
    public static Facts classify(Optional<Observation> nativeObservation,ProcessObservation process,Optional<BigInteger> receiptObservedNs,RetainedIdentity expected) {
        Objects.requireNonNull(nativeObservation);Objects.requireNonNull(process);Objects.requireNonNull(receiptObservedNs);Objects.requireNonNull(expected);receiptObservedNs.ifPresent(value->uint(value,StrictJson.UINT64_MAX));
        if(!process.identity().equals(expected)||!process.identityVerified())return new Facts(FactStatus.ORIGINAL_RETAINED_HANDLE_IDENTITY_MISMATCH,false,OptionalLong.empty(),false);
        boolean qualified=nativeObservation.filter(n->n.action()==Action.CONFIRM_DESKTOP&&n.status()==Status.DISPATCH_PENDING&&n.proof().complete()&&n.contextSignatureVerified()
                &&n.dispatches().get(2).claimLatched()&&n.dispatches().get(2).invoked()&&n.dispatches().get(2).nativeHandled()
                &&n.binding().gamePid().equals(expected.pid())&&n.binding().creationFiletime().equals(expected.creationFiletime())).isPresent()
                &&receiptObservedNs.isPresent()&&process.observedMonotonicNs().compareTo(receiptObservedNs.orElseThrow())>=0;
        if(process.waitState()==WaitState.SIGNALED&&process.waitResult()==0&&process.exitCode().isPresent()){long code=process.exitCode().getAsLong();return new Facts(code==0?FactStatus.PROCESS_EXIT_OBSERVED_ZERO:FactStatus.PROCESS_EXIT_OBSERVED_NONZERO,true,OptionalLong.of(code),qualified&&code==0);}
        return new Facts(qualified?(process.waitState()==WaitState.TIMEOUT?FactStatus.DISPATCH_PENDING:FactStatus.OBSERVATION_FAILED_UNKNOWN):FactStatus.DISPATCH_UNKNOWN_CLAIMED,false,OptionalLong.empty(),false);
    }
    public static ObjectNode obj(JsonNode value){require(value instanceof ObjectNode,"closed JSON object required");return (ObjectNode)value;}
    public static void exact(ObjectNode value,Set<String> fields){StrictJson.object(value,fields);}
    public static String text(ObjectNode row,String key){JsonNode n=row.get(key);require(n!=null&&n.isTextual(),"text required: "+key);return n.textValue();}
    public static boolean bool(ObjectNode row,String key){JsonNode n=row.get(key);require(n!=null&&n.isBoolean(),"boolean required: "+key);return n.booleanValue();}
    public static BigInteger integer(ObjectNode row,String key,BigInteger min,BigInteger max){return StrictJson.integer(row.get(key),min,max);}
    private static JsonNode three(ObjectNode row,String key){JsonNode n=row.get(key);require(n!=null&&n.isArray()&&n.size()==3,"three fixed entries required: "+key);return n;}
    private static Set<String> with(Set<String> fields,String optional){if(optional==null)return fields;var result=new java.util.HashSet<>(fields);result.add(optional);return Set.copyOf(result);}
    public static void sha(String value){require(value!=null&&value.matches("[0-9a-f]{64}"),"64 lowercase SHA256 required");}
    private static void ascii(String value){require(value!=null&&value.matches("[A-Za-z0-9_.:-]{1,128}"),"closed ASCII request identity required");}
    private static void positive(BigInteger value,BigInteger maximum){require(value!=null&&value.signum()>0&&value.compareTo(maximum)<=0,"positive exact bounded integer required");}
    private static void uint(BigInteger value,BigInteger maximum){require(value!=null&&value.signum()>=0&&value.compareTo(maximum)<=0,"exact bounded unsigned integer required");}
}

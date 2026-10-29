package org.xar.ck3.control.nativebridge.capabilities.diagnostics;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.application.driver.RejectedSnapshotPublicEncoding;

/** One strict wire codec for the original complete native-driver diagnostic branch. */
public final class BridgeDiagnosticsCodec {
    private BridgeDiagnosticsCodec() { }
    private static final BigInteger MAX_SAFE=BigInteger.valueOf(9007199254740991L);
    private static final String REJECTED_COUNT="rejected_state_snapshot_count",LAST_REJECTED="last_rejected_state_snapshot",
            PUBLISH_COUNT="snapshot_publish_diagnostic_count",TRANSPORT_REFUSAL="transport_refusal";
    private static final Set<String> NATIVE_OWNED=Set.of(REJECTED_COUNT,LAST_REJECTED,PUBLISH_COUNT,TRANSPORT_REFUSAL);
    private static final Set<String> FIELDS=Set.of("protocol_version","pipe_name","connected","connection_generation","bridge_pid",
            "bridge_version","hello","last_heartbeat","private_observers","last_pong","last_error",
            "top_exclusive_modal_choice_hint_observation","semantic_state_available","rejected_state_snapshot_count",
            "last_rejected_state_snapshot","snapshot_publish_diagnostic_count","last_snapshot_publish_diagnostic",
            "transport_fatal_error","transport_refusal","pending_declaration_query","frontend_start_campaign_root_query");
    public static BridgeDiagnostics.Request decodeRequest(PublicBindings.Arguments arguments) {
        java.util.Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Value value) {
            Obj object=DriverJson.object(value.original().bytes(),RawJson.MAXIMUM_BYTES);
            StrictJson.require(object.members().isEmpty(),"bridge diagnostics accepts no public arguments");
        }
        return new BridgeDiagnostics.Request();
    }
    /** Original internal JSON numbers are restored only for explicitly proved public decimal roles. */
    public static RawJson encode(BridgeDiagnostics.Report report) {
        Obj original=internal(report);var fields=new LinkedHashMap<>(original.members());
        decimal(fields,"connection_generation");decimal(fields,"rejected_state_snapshot_count");decimal(fields,"snapshot_publish_diagnostic_count");
        for(String key:List.of("hello","last_heartbeat","last_pong","last_error","last_snapshot_publish_diagnostic")) {
            Value value=fields.get(key);if(value instanceof Obj object) {
                var nested=new LinkedHashMap<>(object.members());if(nested.containsKey("connection_generation"))decimal(nested,"connection_generation");
                fields.put(key,new Obj(nested));
            }
        }
        pendingBinding(fields,true);frontendFields(fields,true);
        Obj publicValue=new Obj(fields);
        publicValue=RejectedSnapshotPublicEncoding.toPublic(publicValue);
        safeNumbers(publicValue);return new RawJson(DriverJson.encode(publicValue));
    }
    /** Strict public reader returns the original JSON type domain, without guessing arbitrary identity field names. */
    public static Obj decodePublic(RawJson encoded) {
        Obj value=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);StrictJson.require(value.members().keySet().equals(FIELDS),"exact complete diagnostic fields required");
        safeNumbers(value);
        var fields=new LinkedHashMap<>(value.members());
        restoreIntegerRole(fields,"connection_generation",true);restoreIntegerRole(fields,"rejected_state_snapshot_count",false);restoreIntegerRole(fields,"snapshot_publish_diagnostic_count",false);
        for(String key:List.of("hello","last_heartbeat","last_pong","last_error","last_snapshot_publish_diagnostic")) {
            Value item=fields.get(key);if(item instanceof Obj object) {
                var nested=new LinkedHashMap<>(object.members());if(nested.containsKey("connection_generation"))restoreIntegerRole(nested,"connection_generation",true);fields.put(key,new Obj(nested));
            }
        }
        pendingBinding(fields,false);frontendFields(fields,false);
        Obj restored=RejectedSnapshotPublicEncoding.fromPublic(new Obj(fields));validate(restored);return restored;
    }
    public static Obj internal(BridgeDiagnostics.Report report) {
        java.util.Objects.requireNonNull(report);var actual=report.received();var original=actual.original();var supplement=report.supplement();
        try {StrictJson.require(actual.equals(BridgeDiagnosticsCapture.capture(actual.pipeName(),original,actual.retainedSnapshot())),"diagnostic fields differ from their original received producer");}
        catch(java.io.IOException invalid){throw new IllegalArgumentException("diagnostic original packet is invalid",invalid);}
        NativeTransportDiagnostics.Production accounting;
        try {accounting=BridgeDiagnostics.requireNativeProduction(actual);}
        catch(BridgeDiagnostics.MissingInputs missing){throw new IllegalArgumentException("actual original Native diagnostic producer is incomplete",missing);}
        var hello=original.originalHello();var fields=new LinkedHashMap<String,Value>();
        fields.put("protocol_version",new IntegerValue(BigInteger.ONE));fields.put("pipe_name",new Text(actual.pipeName()));
        fields.put("connected",new Bool(original.receivedState()==NativeGameTransport.ReceivedState.HELLO_VERIFIED));
        fields.put("connection_generation",original.session().<Value>map(s->new IntegerValue(s.connectionGeneration())).orElse(Nil.INSTANCE));
        fields.put("bridge_pid",hello.<Value>map(h->new IntegerValue(BigInteger.valueOf(h.original().pid()))).orElse(Nil.INSTANCE));
        fields.put("bridge_version",hello.<Value>map(h->new Text(h.original().bridgeVersion())).orElse(Nil.INSTANCE));
        fields.put("hello",nullable(actual.hello()));fields.put("last_heartbeat",nullable(actual.heartbeat()));
        fields.put("last_pong",nullable(actual.pong()));fields.put("last_error",nullable(actual.error()));
        fields.put("last_snapshot_publish_diagnostic",nullable(actual.snapshotPublishDiagnostic()));
        var observers=new LinkedHashMap<String,Value>();var privateValues=actual.privateObservers();
        privateValues.trucePreview().ifPresent(v->observers.put("g2_truce_preview_entry_observer_v1",v));
        privateValues.vfsMount().ifPresent(v->observers.put("vfs_mount_lifecycle_observer_v1",v));
        privateValues.physfsMountedData().ifPresent(v->observers.put("physfs_mounted_data_observer_v1",v));
        fields.put("private_observers",new Obj(observers));fields.put("top_exclusive_modal_choice_hint_observation",nullable(actual.modalChoiceHint()));
        fields.put("semantic_state_available",new Bool(report.semanticStateAvailable()));
        fields.putAll(nativeProductionFields(accounting).members());
        fields.put("transport_fatal_error",original.terminalFailure().<Value>map(Text::new).orElse(Nil.INSTANCE));
        fields.put("pending_declaration_query",nullable(supplement.pendingDeclarationQuery()));
        fields.put("frontend_start_campaign_root_query",nullable(supplement.frontendStartCampaignRootQuery()));
        Obj result=new Obj(fields);validate(result);return result;
    }
    /** Sole live Driver/public native diagnostic formatter. Missing adopter observation omits refusal; it is never null. */
    public static Obj nativeProductionFields(NativeTransportDiagnostics.Production actual) {
        java.util.Objects.requireNonNull(actual);var fields=new LinkedHashMap<String,Value>();
        fields.put(REJECTED_COUNT,new IntegerValue(actual.rejectedSnapshotCount()));
        fields.put(LAST_REJECTED,actual.lastRejectedSnapshot().<Value>map(BridgeDiagnosticsCodec::rejected).orElse(Nil.INSTANCE));
        fields.put(PUBLISH_COUNT,new IntegerValue(actual.snapshotPublishDiagnosticCount()));
        if(actual.adoption() instanceof NativeTransportDiagnostics.Observed observed)
            fields.put(TRANSPORT_REFUSAL,observed.refusal().<Value>map(BridgeDiagnosticsCodec::refusal).orElse(Nil.INSTANCE));
        return new Obj(fields);
    }
    /** Clear these retained auxiliary fields before consuming the current optional native production. */
    public static Set<String> nativeOwnedFields(){return NATIVE_OWNED;}
    private static void validate(Obj value) {
        StrictJson.require(value.members().keySet().equals(FIELDS),"exact original native-driver diagnostic fields required");
        StrictJson.require(integer(value.get("protocol_version"),"protocol_version").equals(BigInteger.ONE),"original Native protocol v1 required");
        text(value.get("pipe_name"),"pipe_name");bool(value.get("connected"),"connected");bool(value.get("semantic_state_available"),"semantic_state_available");
        for(String key:List.of("connection_generation","rejected_state_snapshot_count","snapshot_publish_diagnostic_count")) {
            Value item=value.get(key);if(key.equals("connection_generation")&&item==Nil.INSTANCE)continue;
            BigInteger count=integer(item,key);StrictJson.require(count.signum()>=0&&count.bitLength()<=64,"exact uint64 diagnostic field required: "+key);
        }
        Value pid=value.get("bridge_pid");if(pid!=Nil.INSTANCE){BigInteger id=integer(pid,"bridge_pid");StrictJson.require(id.signum()>0&&id.compareTo(MAX_SAFE)<=0,"safe actual bridge PID required");}
        for(String key:List.of("bridge_version","transport_fatal_error"))if(value.get(key)!=Nil.INSTANCE)text(value.get(key),key);
        for(String key:List.of("hello","last_heartbeat","last_pong","last_error","last_snapshot_publish_diagnostic","last_rejected_state_snapshot",
                "top_exclusive_modal_choice_hint_observation","transport_refusal","pending_declaration_query","frontend_start_campaign_root_query"))
            if(value.get(key)!=Nil.INSTANCE)object(value.get(key),key);
        Obj observers=object(value.get("private_observers"),"private_observers");
        StrictJson.require(Set.of("g2_truce_preview_entry_observer_v1","vfs_mount_lifecycle_observer_v1","physfs_mounted_data_observer_v1").containsAll(observers.members().keySet()),"unproved private diagnostic observer role");
        observers.members().forEach((key,item)->object(item,key));
        if(integer(value.get("rejected_state_snapshot_count"),"rejections").signum()==0)StrictJson.require(value.get("last_rejected_state_snapshot")==Nil.INSTANCE,"zero count cannot have an original rejection");
        if(value.get("last_rejected_state_snapshot") instanceof Obj rejected) {
            StrictJson.require(rejected.members().keySet().equals(Set.of("snapshot_id","revision","date_raw","speed","paused","map_ready","error_type","error")),"exact original rejected-snapshot diagnostic fields required");
            text(rejected.get("error_type"),"error_type");StrictJson.require(rejected.get("error") instanceof Text,"actual rejected-snapshot error must retain its original text");
        }
        if(value.get("transport_refusal") instanceof Obj refusal) {
            StrictJson.require(refusal.members().keySet().equals(Set.of("schema","exception_type","stage","reason","message","attempted_bridge_pid"))
                    &&new Text("native-bridge-adoption-refusal-v1").equals(refusal.get("schema"))&&new Text("hello_adoption").equals(refusal.get("stage")),"exact original adoption-refusal fields required");
            text(refusal.get("exception_type"),"exception_type");StrictJson.require(refusal.get("message") instanceof Text,"original adoption refusal message must be text");
            StrictJson.require(Set.of("invalid_driver_journal","active_driver_journal_requires_consolidation","legacy_lifecycle_incompatible","persisted_lifecycle_mismatch").contains(text(refusal.get("reason"),"reason")),"unproved adoption refusal reason");
            BigInteger attempted=integer(refusal.get("attempted_bridge_pid"),"attempted_bridge_pid");StrictJson.require(attempted.signum()>0&&attempted.compareTo(MAX_SAFE)<=0,"safe attempted adoption PID required");
        }
        if(integer(value.get("snapshot_publish_diagnostic_count"),"publications").signum()==0)StrictJson.require(value.get("last_snapshot_publish_diagnostic")==Nil.INSTANCE,"zero count cannot have an original publish diagnostic");
        if(value.get("hello") instanceof Obj hello) {
            StrictJson.require(integer(hello.get("protocol_version"),"hello.protocol_version").equals(BigInteger.ONE)
                    &&java.util.Objects.equals(hello.get("pid"),value.get("bridge_pid"))
                    &&java.util.Objects.equals(hello.get("bridge_version"),value.get("bridge_version"))
                    &&java.util.Objects.equals(hello.get("connection_generation"),value.get("connection_generation")),"complete diagnostic HELLO/top identity differs");
        } else StrictJson.require(!bool(value.get("connected"),"connected")&&value.get("bridge_pid")==Nil.INSTANCE
                &&value.get("bridge_version")==Nil.INSTANCE&&value.get("connection_generation")==Nil.INSTANCE,"connected diagnostic identity requires the actual original HELLO");
        if(value.get("pending_declaration_query") instanceof Obj pending) {
            StrictJson.require(pending.members().keySet().equals(Set.of("request_id","step","status","binding","timeout_seconds"))
                    &&new Text("query-declarable-wars").equals(pending.get("step"))&&new Text("pending").equals(pending.get("status")),"exact original pending declaration metadata required");
            text(pending.get("request_id"),"pending.request_id");Obj binding=object(pending.get("binding"),"pending.binding");
            StrictJson.require(binding.members().keySet().equals(Set.of("snapshot_id","revision","native_revision","episode_run_id","date_raw","paused","map_ready","player_character_id","bridge_pid","connection_generation")),"exact original pending declaration binding fields required");
            text(binding.get("snapshot_id"),"pending.snapshot_id");text(binding.get("episode_run_id"),"pending.episode_run_id");
            bool(binding.get("paused"),"pending.paused");bool(binding.get("map_ready"),"pending.map_ready");
            for(String key:List.of("revision","native_revision","connection_generation")) {
                BigInteger actual=integer(binding.get(key),"pending."+key);StrictJson.require(actual.signum()>0&&(key.equals("revision")||actual.bitLength()<=64),"exact positive pending revision/generation required");
            }
            for(String key:List.of("date_raw","player_character_id","bridge_pid")) {
                BigInteger actual=integer(binding.get(key),"pending."+key);StrictJson.require((key.equals("date_raw")?actual.signum()>=0:actual.signum()>0)&&actual.compareTo(MAX_SAFE)<=0,"exact safe pending identity/date required");
            }
            StrictJson.require(java.util.Objects.equals(binding.get("bridge_pid"),value.get("bridge_pid"))
                    &&java.util.Objects.equals(binding.get("connection_generation"),value.get("connection_generation")),"pending declaration metadata crossed actual diagnostic transport identity");
            Value duration=pending.get("timeout_seconds");StrictJson.require(duration instanceof IntegerValue whole&&whole.value().signum()>0
                    ||duration instanceof DecimalValue decimal&&new java.math.BigDecimal(decimal.token()).signum()>0,"actual positive pending timeout seconds required; no boolean/float conversion");
        }
        if(value.get("frontend_start_campaign_root_query") instanceof Obj frontend) {
            String status=text(frontend.get("status"),"frontend.status");
            StrictJson.require(Set.of("prepared_not_submitted","native_result_received","query_failed",
                    "native_result_pending_at_deadline","campaign_root_frame_verified").contains(status),"exact original Start query diagnostic status required");
            var keys=new java.util.HashSet<>(Set.of("native_request_id","status","deadline_monotonic","initial_remaining_seconds",
                    "snapshot_id","native_revision","date_raw","original_request_replayed"));
            boolean received=status.equals("native_result_received")||status.equals("campaign_root_frame_verified");
            boolean failed=status.equals("query_failed")||status.equals("native_result_pending_at_deadline");
            if(received)keys.addAll(Set.of("native_result_status","native_query_sequence"));
            if(failed)keys.add("error");
            StrictJson.require(frontend.members().keySet().equals(keys),"exact original Start query diagnostic state fields required");
            text(frontend.get("native_request_id"),"frontend.native_request_id");text(frontend.get("snapshot_id"),"frontend.snapshot_id");
            StrictJson.require(frontend.get("deadline_monotonic") instanceof DecimalValue
                    &&frontend.get("initial_remaining_seconds") instanceof DecimalValue remaining&&new java.math.BigDecimal(remaining.token()).signum()>0,
                    "actual exact decimal Start deadline/remaining seconds required");
            BigInteger revision=integer(frontend.get("native_revision"),"frontend.native_revision");
            StrictJson.require(revision.signum()>0&&revision.bitLength()<=64,"actual uint64 Start native revision required");
            BigInteger date=integer(frontend.get("date_raw"),"frontend.date_raw");
            StrictJson.require(date.signum()>=0&&date.compareTo(MAX_SAFE)<=0,"actual safe Start date required");
            StrictJson.require(new Bool(false).equals(frontend.get("original_request_replayed")),"Start query diagnostics never grant replay");
            if(received) {
                Value resultStatus=frontend.get("native_result_status"),sequence=frontend.get("native_query_sequence");
                StrictJson.require(resultStatus==Nil.INSTANCE||resultStatus instanceof Text,"original Start result status must retain text/null");
                StrictJson.require(sequence==Nil.INSTANCE||sequence instanceof IntegerValue actual&&actual.value().signum()>0&&actual.value().bitLength()<=64,
                        "malformed Start result sequence remains original evidence; it cannot qualify a complete typed Report");
            }
            if(failed)StrictJson.require(frontend.get("error") instanceof Text,"actual Start failure error text required");
        }
        var derived=new LinkedHashMap<String,Value>();
        if(value.get("last_heartbeat") instanceof Obj heartbeat) {
            if(heartbeat.members().containsKey("connection_generation"))StrictJson.require(java.util.Objects.equals(heartbeat.get("connection_generation"),value.get("connection_generation")),"diagnostic heartbeat crossed connection generation");
            for(String key:List.of("g2_truce_preview_entry_observer_v1","vfs_mount_lifecycle_observer_v1","physfs_mounted_data_observer_v1"))if(heartbeat.get(key) instanceof Obj item)derived.put(key,item);
        }
        StrictJson.require(observers.equals(new Obj(derived)),"private diagnostic observers differ from the original received heartbeat");
    }
    private static Value nullable(Optional<Obj> value){return value.<Value>map(v->v).orElse(Nil.INSTANCE);}
    private static Obj rejected(NativeTransportDiagnostics.RejectedSnapshot rejected) {
        try {
            var original=rejected.original().fields();return new Obj(Map.of("snapshot_id",field(original.snapshotId()),"revision",field(original.revision()),
                    "date_raw",field(original.dateRaw()),"speed",field(original.speed()),"paused",field(original.paused()),"map_ready",field(original.mapReady()),
                    "error_type",new Text(rejected.errorType()),"error",new Text(rejected.error())));
        }catch(java.io.IOException invalid){throw new IllegalArgumentException("actual original rejected snapshot is invalid",invalid);}
    }
    private static Value field(NativeWire.Field field) {
        return field.presence()==NativeWire.Presence.VALUE?DriverJson.fromNode(StrictJson.parse(field.token().orElseThrow().value())):Nil.INSTANCE;
    }
    private static Obj refusal(NativeTransportDiagnostics.AdoptionRefusal actual) {
        return new Obj(Map.of("schema",new Text("native-bridge-adoption-refusal-v1"),"exception_type",new Text(actual.exceptionType()),
                "stage",new Text(actual.stage()),"reason",new Text(actual.reason().wire()),"message",new Text(actual.message()),
                "attempted_bridge_pid",new IntegerValue(BigInteger.valueOf(actual.session().game().pid()))));
    }
    private static void decimal(Map<String,Value> fields,String key){Value value=fields.get(key);if(value!=Nil.INSTANCE){BigInteger number=integer(value,key);StrictJson.require(number.signum()>=0&&number.bitLength()<=64,"uint64 role required: "+key);fields.put(key,new Text(number.toString()));}}
    private static void restoreIntegerRole(Map<String,Value> fields,String key,boolean nullable){Value value=fields.get(key);if(nullable&&value==Nil.INSTANCE)return;String text=text(value,key);StrictJson.require(text.matches("0|[1-9][0-9]*")&&text.length()<=20,"canonical uint64 decimal required: "+key);BigInteger integer=new BigInteger(text);StrictJson.require(integer.bitLength()<=64,"uint64 decimal overflow: "+key);fields.put(key,new IntegerValue(integer));}
    private static void pendingBinding(Map<String,Value> fields,boolean encode) {
        if(fields.get("pending_declaration_query")==Nil.INSTANCE)return;
        Obj pending=object(fields.get("pending_declaration_query"),"pending_declaration_query");var binding=new LinkedHashMap<>(object(pending.get("binding"),"pending.binding").members());
        for(String key:List.of("revision","native_revision","connection_generation")) {
            Value raw=binding.get(key);BigInteger actual;
            if(encode)actual=integer(raw,"pending."+key);
            else {String decimal=text(raw,"pending."+key);StrictJson.require(decimal.matches("[1-9][0-9]*")&&decimal.length()<=4300,"canonical positive pending decimal identity required");actual=new BigInteger(decimal);}
            StrictJson.require(actual.signum()>0&&(key.equals("revision")||actual.bitLength()<=64),"pending identity decimal range differs");
            binding.put(key,encode?new Text(actual.toString()):new IntegerValue(actual));
        }
        fields.put("pending_declaration_query",pending.with("binding",new Obj(binding)));
    }
    private static void frontendFields(Map<String,Value> fields,boolean encode) {
        if(fields.get("frontend_start_campaign_root_query")==Nil.INSTANCE)return;
        Obj original=object(fields.get("frontend_start_campaign_root_query"),"frontend_start_campaign_root_query");
        var frontend=new LinkedHashMap<>(original.members());
        for(String key:List.of("native_revision","native_query_sequence")) {
            if(!frontend.containsKey(key)||frontend.get(key)==Nil.INSTANCE)continue;
            Value raw=frontend.get(key);BigInteger actual;
            if(encode)actual=integer(raw,"frontend."+key);
            else {
                String decimal=text(raw,"frontend."+key);
                StrictJson.require(decimal.matches("[1-9][0-9]*")&&decimal.length()<=20,"canonical positive Start uint64 decimal required");
                actual=new BigInteger(decimal);
            }
            StrictJson.require(actual.signum()>0&&actual.bitLength()<=64,"Start uint64 diagnostic identity overflow");
            frontend.put(key,encode?new Text(actual.toString()):new IntegerValue(actual));
        }
        // snapshot_id is an opaque shared String. Decimal seconds retain their original exact number tokens.
        fields.put("frontend_start_campaign_root_query",new Obj(frontend));
    }
    private static void safeNumbers(Value value) {
        if(value instanceof IntegerValue integer)StrictJson.require(integer.value().abs().compareTo(MAX_SAFE)<=0,"unproved unsafe public diagnostic integer role; original report unavailable");
        else if(value instanceof Obj object)object.members().values().forEach(BridgeDiagnosticsCodec::safeNumbers);
        else if(value instanceof Arr array)array.items().forEach(BridgeDiagnosticsCodec::safeNumbers);
    }
}

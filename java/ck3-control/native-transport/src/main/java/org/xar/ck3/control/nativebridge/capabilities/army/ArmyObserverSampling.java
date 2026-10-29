package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Exact .4 nine-family observer control. Retained capture state is not an Army effect or a gameplay result. */
public final class ArmyObserverSampling {
    private ArmyObserverSampling() { }
    public static final String QUERY="query-army-observer-research-sampling-v1",ENABLE="enable-army-observer-research-sampling-v1",DISABLE="disable-army-observer-research-sampling-v1";
    public static final String CAPABILITY=ArmyStrengths.CAPABILITY,OBSERVER="java.army.observer-sampling.independent.v1";
    public enum Family { ALL,NATURAL_PHASE,REGULAR_CORE,DAILY_ASSAULT_PREPARATION,ASSAULT_PLACEMENT,ASSAULT_CONSUMER,ASSAULT_GROUP_RELEASE,GATHERING,CLEANUP,PRE_DATE_PREFIX;
        public String wire(){return name().toLowerCase(Locale.ROOT);} public List<Family> selected(){return this==ALL?Arrays.stream(values()).filter(f->f!=ALL).toList():List.of(this);}
        public static Family parse(String text){return Arrays.stream(values()).filter(f->f.wire().equals(text)).findFirst().orElseThrow(()->new IllegalArgumentException("unknown observer family"));}
    }
    public record Selection(Family family,Optional<List<Integer>> subjects) {
        public Selection {Objects.requireNonNull(family);Objects.requireNonNull(subjects);subjects=subjects.map(List::copyOf);subjects.ifPresent(ids->require(family==Family.REGULAR_CORE&&ids.size()>=1&&ids.size()<=64&&new HashSet<>(ids).size()==ids.size()&&ids.stream().allMatch(id->id!=null&&id!=-1),"regular_core unique signed32 subjects required"));}
        public Selection query(){return new Selection(family,Optional.empty());}
    }
    public enum CaptureStatus { UNAVAILABLE,ENABLED,BUSY,DISABLED,CLEAR_PENDING;
        public String wire(){return name().toLowerCase(Locale.ROOT);} public static CaptureStatus parse(String text){return Arrays.stream(values()).filter(v->v.wire().equals(text)).findFirst().orElseThrow(()->new IllegalArgumentException("invalid observer capture status"));}
    }
    public enum CaptureReadiness { UNAVAILABLE,OFF,INFLIGHT,AWAITING_SAMPLE,RETAINED_OBSERVATION;
        public String wire(){return name().toLowerCase(Locale.ROOT);} public static CaptureReadiness parse(String text){return Arrays.stream(values()).filter(v->v.wire().equals(text)).findFirst().orElseThrow(()->new IllegalArgumentException("invalid observer capture readiness"));}
    }
    public record Row(Family family,boolean installed,boolean available,boolean enabled,boolean busy,boolean clearCompleted,
            BigInteger epoch,BigInteger activeCaptures,BigInteger retainedRecords,BigInteger qualifiedRecords,CaptureStatus status,CaptureReadiness readiness) {
        public Row {
            Objects.requireNonNull(family);require(family!=Family.ALL,"actual family row required");
            for(var n:List.of(epoch,activeCaptures,retainedRecords,qualifiedRecords))require(n.signum()>=0&&n.bitLength()<=64,"observer counter must be uint64");
            require(qualifiedRecords.compareTo(retainedRecords)<=0&&busy==(activeCaptures.signum()>0),"observer retained/busy contradiction");
            require(!clearCompleted||!enabled&&!busy&&retainedRecords.signum()==0,"observer clear contradicts retained state");
            boolean a=installed&&available;String s=!a?"unavailable":enabled?"enabled":busy?"busy":clearCompleted?"disabled":"clear_pending";
            String r=!a?"unavailable":!enabled?"off":busy?"inflight":qualifiedRecords.signum()==0?"awaiting_sample":"retained_observation";
            require(status!=null&&readiness!=null&&s.equals(status.wire())&&r.equals(readiness.wire()),"observer status/readiness contradict actual counters");
        }
        public boolean satisfies(boolean enable){return installed&&available&&(enable?enabled:!enabled&&!busy&&clearCompleted);}
    }
    public record Result(String step,boolean accepted,Selection selection,List<Row> rows,RawJson original) {
        public Result {require(Set.of(QUERY,ENABLE,DISABLE).contains(step),"fixed observer operation required");Objects.requireNonNull(selection);rows=List.copyOf(rows);Objects.requireNonNull(original);require(rows.stream().map(Row::family).toList().equals(selection.family().selected()),"selected observer family order differs");}
    }
    public static NativeRequest request(String step,Selection selection){require(Set.of(QUERY,ENABLE,DISABLE).contains(step),"fixed observer step required");require(selection.subjects().isEmpty()||step.equals(ENABLE),"scope only for enable regular_core");return new NativeRequest(step,Optional.of(CAPABILITY),fields(selection));}
    public static RawJson fields(Selection selection){var n=ArmyJson.empty().put("observer_family",selection.family().wire());selection.subjects().ifPresent(ids->{var a=n.putArray("regular_core_full_carmy_ids");ids.forEach(a::add);});return new RawJson(ArmyJson.bytes(n));}
    public static Selection selection(OpportunityJson.Obj args){return selection(ArmyJson.parse(OpportunityJson.encode(args)));}
    public static Selection selection(ObjectNode row){Set<String> keys=new HashSet<>();row.fieldNames().forEachRemaining(keys::add);require(keys.equals(Set.of("observer_family"))||keys.equals(Set.of("observer_family","regular_core_full_carmy_ids")),"exact observer request fields required");Family f=Family.parse(text(row,"observer_family"));Optional<List<Integer>> ids=Optional.empty();if(row.has("regular_core_full_carmy_ids")){JsonNode a=row.get("regular_core_full_carmy_ids");require(a.isArray(),"actual subject array required");var list=new ArrayList<Integer>();a.forEach(v->{require(v.isIntegralNumber()&&v.canConvertToInt(),"subject must be signed32 integer");list.add(v.intValue());});ids=Optional.of(list);}return new Selection(f,ids);}
    public static Result decode(RawJson original,String step,Selection selected){
        ObjectNode root=ArmyJson.parse(original.bytes());Set<String> keys=new HashSet<>();root.fieldNames().forEachRemaining(keys::add);
        require(keys.equals(Set.of("step","accepted","status","army_observer_research_sampling_v1")),"exact original native observer envelope required");
        require(text(root,"step").equals(step),"observer original step changed");boolean accepted=bool(root,"accepted");
        ObjectNode rows=object(root.get("army_observer_research_sampling_v1"));var wanted=new HashSet<String>();selected.family().selected().forEach(f->wanted.add(f.wire()));exact(rows,wanted);var output=new ArrayList<Row>();
        for(Family family:selected.family().selected()){
            ObjectNode row=object(rows.get(family.wire()));exact(row,Set.of("installed","available","capture_enabled","busy","clear_completed","epoch","active_captures","retained_records","qualified_records","status","readiness"));
            output.add(new Row(family,bool(row,"installed"),bool(row,"available"),bool(row,"capture_enabled"),bool(row,"busy"),bool(row,"clear_completed"),uint(row,"epoch"),uint(row,"active_captures"),uint(row,"retained_records"),uint(row,"qualified_records"),CaptureStatus.parse(text(row,"status")),CaptureReadiness.parse(text(row,"readiness"))));
        }
        boolean all=step.equals(QUERY)||output.stream().allMatch(r->r.satisfies(step.equals(ENABLE)));
        require(accepted==all||step.equals(ENABLE)&&selected.subjects().isPresent()&&!accepted,"observer aggregate accepted contradicts actual rows");
        require(text(root,"status").equals(accepted?"completed":"incomplete"),"observer aggregate status differs");return new Result(step,accepted,selected,output,original);
    }
    public static Result verifyRead(PlanningReadReceipt receipt,Selection selection,ActionPorts.OutcomeArchive archive){
        try {
            require(receipt.request().operation().value().equals(QUERY)&&selection(receipt.request().arguments()).equals(selection.query()),"observer read arguments changed");
            verifyAck(receipt.original(),QUERY,selection.query(),receipt.request().before());
            for(GuardEvidence guard:List.of(receipt.before().binding(),receipt.after().binding())){
                var snapshot=NativeWire.decode(original(archive,guard.nativeEvidence()));var hello=NativeWire.decode(original(archive,guard.capabilityEvidence()));
                require(snapshot instanceof NativeWire.Snapshot&&hello instanceof NativeWire.Hello,"actual observer snapshot/HELLO originals required");
                validate(receipt.request().before(),guard.connectionGeneration(),(NativeWire.Snapshot)snapshot,(NativeWire.Hello)hello);
            }
            sameFrame(receipt.request().before(),receipt.before().binding().observed());sameFrame(receipt.request().before(),receipt.after().binding().observed());
            return decode(receipt.original().originalResultToken().orElseThrow(),QUERY,selection.query());
        }catch(IOException failure){throw new java.io.UncheckedIOException("actual observer original unavailable",failure);}
    }
    public static void verifyAck(NativeActionPort.AckReceived ack,String step,Selection selection,ObservationIdentity before)throws IOException {
        var decoded=NativeWire.decode(ack.originalPacket());require(decoded instanceof NativeWire.CommandResult,"actual observer ACK original required");var frame=(NativeWire.CommandResult)decoded;
        require(ack.nativeOk()&&frame.nativeOk()&&frame.requestId().equals(ack.requestId())&&Arrays.equals(frame.payload().value(),ack.originalFrame().bytes())
                &&frame.result().presence()==NativeWire.Presence.VALUE&&Arrays.equals(frame.result().token().orElseThrow().value(),ack.originalResultToken().orElseThrow().bytes()),"observer ACK packet/token/request mismatch");
        var outbound=NativeWire.decodeExecuteRequest(ack.outbound().orElseThrow().originalPacket());
        require(outbound.requestId().equals(ack.requestId())&&outbound.step().equals(step)&&outbound.expectedRevision().equals(Optional.of(before.frame().identity().nativeRevision()))
                &&NativeWire.parse(outbound.normalizedAdditionalFields().value()).equals(NativeWire.parse(fields(selection).bytes())),"observer actual outbound operation/revision/fields differ");
        decode(ack.originalResultToken().orElseThrow(),step,selection);
    }
    /** Pure interpretation of the actual original incomplete ACK; it never changes or settles canonical UNKNOWN. */
    public static Result incompleteOriginal(ActionCommand command,ActionState.Attempt attempted,NativeActionPort.AckReceived ack)throws IOException {
        Selection selected=selection(command.arguments());
        require(attempted.guard().source().equals(command.source())&&attempted.guard().observed().equals(command.before())
                &&attempted.guard().operation().equals(command.operation())&&attempted.guard().sessionId().equals(command.sessionId())
                &&attempted.preparedRequest().equals(request(command.operation().value(),selected)),"incomplete observer return changed its canonical original guard/request");
        require(attempted.requestId().equals(ack.requestId()),"incomplete observer ACK request differs from the actual canonical attempt");
        ack.custody().orElseThrow().verify(ack,attempted.guard());verifyAck(ack,command.operation().value(),selected,command.before());
        Result original=decode(ack.originalResultToken().orElseThrow(),command.operation().value(),selected);
        require(!original.accepted(),"an unverified successful observer ACK cannot be returned as a completed control");return original;
    }
    public static void validate(ObservationIdentity before,BigInteger generation,NativeWire.Snapshot snapshot,NativeWire.Hello hello)throws IOException {
        require(hello.pid()==before.game().pid()&&hello.connectionGeneration().equals(generation)&&hello.capabilities().contains(CAPABILITY)
                &&hello.buildMatch()&&hello.gameSha256().equalsIgnoreCase("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"),"observer requires actual exact .4 HELLO identity/capability");
        byte[] h=hello.packet().value();ObjectNode raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(h,4,h.length)));require(text(raw,"expected_ck3_version").equals("1.20.0.4"),"observer requires exact .4 version");
        require(snapshot.snapshotId().equals(before.frame().snapshotId())&&snapshot.revision().equals(before.frame().identity().nativeRevision()),"observer original native snapshot differs");
        ObjectNode state=ArmyJson.parse(snapshot.state().value());require(bool(state,"paused")&&bool(state,"map_ready"),"observer requires paused map");
        ObjectNode actor=object(state.get("played_character"));require(bool(actor,"alive")&&NativeWire.integer(actor.get("character_id"),BigInteger.ONE,BigInteger.valueOf(Integer.MAX_VALUE)).equals(before.frame().identity().player())
                &&NativeWire.integer(state.get("date_raw"),BigInteger.ZERO,NativeWire.UINT64_MAX).equals(before.frame().identity().dateRaw()),"observer living player/date differs");
    }
    private static byte[] original(ActionPorts.OutcomeArchive archive,ExactRef ref)throws IOException {byte[] bytes=archive.readOriginalPacket(ref);var id=NativeRequestChronology.PacketIdentity.of(bytes);require(id.bytes()==ref.bytes()&&id.sha256().equals(ref.sha256()),"observer archive original changed");return bytes;}
    public static void sameFrame(ObservationIdentity first,ObservationIdentity second){require(first.equals(second),"observer control crossed its exact paused public/native frame");}
    public static List<ExpectedValue> expected(boolean enable,Family family){return List.of(new ExpectedText(new FieldKey("observer_family"),family.wire()),new ExpectedBoolean(new FieldKey("observer_capture_enabled"),enable),new ExpectedBoolean(new FieldKey("observer_independent_verified"),true));}
    public static List<ExpectedValue> actual(boolean enable,Result queried){require(queried.step().equals(QUERY)&&queried.accepted()&&queried.rows().stream().allMatch(r->r.satisfies(enable)),"independent observer gate postcondition unresolved");return expected(enable,queried.selection().family());}
    /** Full internal Driver result; original numeric token domains remain exact for canonical history. */
    public static RawJson driverResult(Result result,ObservationIdentity before,BigInteger generation){
        Result checked=decode(result.original(),result.step(),result.selection());require(checked.rows().equals(result.rows())&&checked.accepted()==result.accepted(),"observer typed result differs from actual original");
        var out=ArmyJson.parse(result.original().bytes());out.put("backend_id","native-headless");out.put("observer_family",result.selection().family().wire());
        out.put("queried_snapshot_id",before.frame().snapshotId()).put("queried_revision",before.frame().revision()).put("queried_native_revision",before.frame().identity().nativeRevision()).put("queried_date_raw",before.frame().identity().dateRaw()).put("queried_connection_generation",generation).put("queried_episode_run_id",before.frame().episodeRunId()).put("queried_player_character_id",before.frame().identity().player());
        return new RawJson(ArmyJson.bytes(out));
    }
    /** Public roles convert only their declared uint64 counters/identities; internal history retains numbers. */
    public static RawJson publicResult(Result result,ObservationIdentity before,BigInteger generation){
        var out=ArmyJson.parse(driverResult(result,before,generation).bytes());
        ObjectNode rows=object(out.get("army_observer_research_sampling_v1"));
        for(Row row:result.rows()){ObjectNode n=object(rows.get(row.family().wire()));n.put("epoch",row.epoch().toString()).put("active_captures",row.activeCaptures().toString()).put("retained_records",row.retainedRecords().toString()).put("qualified_records",row.qualifiedRecords().toString());}
        for(String role:List.of("queried_revision","queried_native_revision","queried_date_raw","queried_connection_generation")){BigInteger n=uint(out,role);out.put(role,n.toString());}
        return new RawJson(ArmyJson.bytes(out));
    }
    private static ObjectNode object(JsonNode n){require(n!=null&&n.isObject(),"observer object required");return (ObjectNode)n;}
    private static void exact(ObjectNode n,Set<String> keys){Set<String> actual=new HashSet<>();n.fieldNames().forEachRemaining(actual::add);require(actual.equals(keys),"observer fields differ");}
    private static String text(ObjectNode n,String k){var v=n.get(k);require(v!=null&&v.isTextual(),"observer text required: "+k);return v.textValue();}
    private static boolean bool(ObjectNode n,String k){var v=n.get(k);require(v!=null&&v.isBoolean(),"observer boolean required: "+k);return v.booleanValue();}
    private static BigInteger uint(ObjectNode n,String k){var v=n.get(k);require(v!=null&&v.isIntegralNumber()&&v.bigIntegerValue().signum()>=0&&v.bigIntegerValue().bitLength()<=64,"observer uint64 required: "+k);return v.bigIntegerValue();}
}

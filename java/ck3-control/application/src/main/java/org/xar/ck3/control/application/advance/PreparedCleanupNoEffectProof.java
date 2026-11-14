package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Event-time DATA for the distinct prepared fifth child's observed NoEffect.
 * No method proves NoDispatch, acknowledges CANCEL, claims IDLE, completes the
 * parent or issues a world capability. Actual Root must independently accept the
 * exact exited sender, loaded backend/serial worker and canonical current prefix. */
public final class PreparedCleanupNoEffectProof {
    public static final String SCHEMA="xar.life-prepared-cleanup-no-effect/v1";
    private static final int MAXIMUM=64*1024;
    private static final Set<String> FIELDS=Set.of("schema","original_parent","original_children","preparation","authorization",
            "old_sender_start","old_sender_exit","serial_barrier","accepted_observation","fresh_status","fresh_snapshot_ack",
            "fresh_frame","snapshot_received","issued_at_utc","observation_deadline_utc");
    private PreparedCleanupNoEffectProof() { }
    public static class Originals {
        private final ExactRef proofReference,parentReference,oldSenderStart,oldSenderExit,serialBarrier,acceptedObservation;
        private final ActionReceipt parentReceipt;
        private final List<ActionReceipt> children;
        private final List<ExactRef> childReferences;
        private final PreparedCleanupEvidence.Prepared prepared;
        private final ClockStatusRead.Observation freshStatus;
        private final NativeActionPort.AckReceived freshSnapshotAck;
        private final NativeObservationPort.ObservedFrame freshFrame;
        private final NativeRequestChronology.Event snapshotReceived;
        private final Instant issuedAt,observationDeadline,oldSenderExitedAt;
        private Originals(ExactRef proof,ExactRef parentRef,ActionReceipt parent,List<ActionReceipt> children,List<ExactRef> childRefs,
                PreparedCleanupEvidence.Prepared prepared,ExactRef senderStart,ExactRef senderExit,ExactRef barrier,ExactRef accepted,
                ClockStatusRead.Observation status,NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame,
                NativeRequestChronology.Event received,Instant issuedAt,Instant deadline,Instant exitedAt) {
            proofReference=proof;parentReference=parentRef;parentReceipt=parent;this.children=List.copyOf(children);childReferences=List.copyOf(childRefs);
            this.prepared=prepared;oldSenderStart=senderStart;oldSenderExit=senderExit;serialBarrier=barrier;acceptedObservation=accepted;
            freshStatus=status;freshSnapshotAck=ack;freshFrame=frame;snapshotReceived=received;this.issuedAt=issuedAt;observationDeadline=deadline;oldSenderExitedAt=exitedAt;
        }
        public ExactRef proofReference(){return proofReference;} public ExactRef parentReference(){return parentReference;}
        public ActionReceipt parentReceipt(){return parentReceipt;} public List<ActionReceipt> children(){return children;}
        public List<ExactRef> childReferences(){return childReferences;} public ActionReceipt child5(){return children.getLast();}
        public ExactRef child5Reference(){return childReferences.getLast();} public PreparedCleanupAction originalPreparedState(){return (PreparedCleanupAction)child5().state();}
        public PreparedCleanupEvidence.Prepared prepared(){return prepared;} public ExactRef preparationReference(){return prepared.reference();}
        public ExactRef authorizationReference(){return prepared.authorizationReference();} public ExactRef oldSenderStart(){return oldSenderStart;}
        public ExactRef oldSenderExit(){return oldSenderExit;} public ExactRef serialBarrier(){return serialBarrier;}
        public ExactRef acceptedObservation(){return acceptedObservation;} public ClockStatusRead.Observation freshStatus(){return freshStatus;}
        public NativeActionPort.AckReceived freshSnapshotAck(){return freshSnapshotAck;} public NativeObservationPort.ObservedFrame freshFrame(){return freshFrame;}
        public NativeRequestChronology.Event snapshotReceived(){return snapshotReceived;} public Instant issuedAt(){return issuedAt;}
        public Instant observationDeadline(){return observationDeadline;} public Instant oldSenderExitedAt(){return oldSenderExitedAt;}
        public String backendDllSha256(){return prepared.aProof().backendDllSha256();}
    }
    public static final class Verified extends Originals {
        private Verified(Originals d,PreparedCleanupEvidence.Prepared full) {
            super(d.proofReference(),d.parentReference(),d.parentReceipt(),d.children(),d.childReferences(),full,d.oldSenderStart(),
                    d.oldSenderExit(),d.serialBarrier(),d.acceptedObservation(),d.freshStatus(),d.freshSnapshotAck(),d.freshFrame(),
                    d.snapshotReceived(),d.issuedAt(),d.observationDeadline(),d.oldSenderExitedAt());
        }
    }
    /** Historical import uses original event time; it never refreshes a READ or command deadline. */
    public static ExactRef preserve(ActionReceipt parent,List<ActionReceipt> children,ExactRef oldSenderStart,ExactRef oldSenderExit,
            ExactRef serialBarrier,ExactRef acceptedObservation,ClockStatusRead.Observation status,NativeActionPort.AckReceived ack,
            NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received,Instant issuedAt,Instant deadline,
            ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Objects.requireNonNull(frames);require(children.size()==5&&children.getLast().state() instanceof PreparedCleanupAction,"prepared NoEffect needs its exact original fifth state");
        var state=(PreparedCleanupAction)children.getLast().state();var prepared=PreparedCleanupEvidence.loadPreparedOriginals(state.preparationReference(),archive);
        var row=StrictJson.object();row.put("schema",SCHEMA);row.set("original_parent",archive.receiptReferenceOf(parent).toJson());
        var refs=row.putArray("original_children");for(var child:children)refs.add(archive.receiptReferenceOf(child).toJson());
        row.set("preparation",prepared.reference().toJson());row.set("authorization",prepared.authorizationReference().toJson());
        row.set("old_sender_start",oldSenderStart.toJson());row.set("old_sender_exit",oldSenderExit.toJson());
        row.set("serial_barrier",serialBarrier.toJson());row.set("accepted_observation",acceptedObservation.toJson());
        row.set("fresh_status",archive.preserveRead(status.receipt()).toJson());row.set("fresh_snapshot_ack",archive.referenceOf(ack).toJson());
        var f=row.putObject("fresh_frame");f.set("native_frame",archive.preserveNativeFrame(frame).toJson());f.set("state_material",archive.preserveMaterial(frame.state()).toJson());
        f.put("snapshot_id",frame.snapshotId());f.put("native_revision",frame.nativeRevision().toString());f.put("observed_at_utc",frame.observedAt().toString());
        var e=row.putObject("snapshot_received");e.put("order",received.order().toString());e.put("observed_at_utc",received.observedAt().toString());
        row.put("issued_at_utc",issuedAt.toString());row.put("observation_deadline_utc",deadline.toString());
        byte[] bytes=StrictJson.canonical(row);require(bytes.length<=MAXIMUM,"prepared NoEffect proof exceeds bounded material cap");
        var reference=archive.preserveMaterial(new RawJson(bytes));var loaded=load(reference,archive,frames);
        require(loaded.parentReceipt().equals(parent)&&loaded.children().equals(children)&&loaded.freshStatus().equals(status)
                &&loaded.freshSnapshotAck().equals(ack)&&Arrays.equals(loaded.freshFrame().originalPacket(),frame.originalPacket())
                &&Arrays.equals(loaded.freshFrame().state().bytes(),frame.state().bytes())&&loaded.snapshotReceived().equals(received),
                "prepared NoEffect preserved originals differ from producer inputs");return reference;
    }
    public static ExactRef preserveArchivedOriginals(ActionReceipt parent,List<ActionReceipt> children,ExactRef oldSenderStart,ExactRef oldSenderExit,
            ExactRef serialBarrier,ExactRef acceptedObservation,ClockStatusRead.Observation status,NativeActionPort.AckReceived ack,
            NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received,Instant issuedAt,Instant deadline,
            ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        return preserve(parent,children,oldSenderStart,oldSenderExit,serialBarrier,acceptedObservation,status,ack,frame,received,issuedAt,deadline,archive,frames);
    }
    public static Verified load(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Objects.requireNonNull(frames);var data=loadOriginals(reference,archive);
        var full=PreparedCleanupEvidence.loadPrepared(data.preparationReference(),archive,frames);
        require(full.reference().equals(data.preparationReference())&&full.command().equals(data.prepared().command())
                &&full.authorizationReference().equals(data.authorizationReference())&&full.preparationNonce().equals(data.prepared().preparationNonce()),
                "prepared NoEffect full authorization changed its durable preparation");return new Verified(data,full);
    }
    public static Originals loadOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var row=material(reference,archive,MAXIMUM);require(row.members().keySet().equals(FIELDS)&&new Text(SCHEMA).equals(row.get("schema")),"prepared NoEffect schema or fields differ");
        var parentRef=exact(row.get("original_parent"));var parent=receipt(parentRef,archive);
        var children=new ArrayList<ActionReceipt>();var refs=new ArrayList<ExactRef>();
        for(var value:array(row.get("original_children"),"original_children")){var ref=exact(value);refs.add(ref);children.add(receipt(ref,archive));}
        require(children.size()==5&&refs.stream().distinct().count()==5&&children.getLast().state() instanceof PreparedCleanupAction,
                "prepared NoEffect needs its original five distinct receipt references");
        var state=(PreparedCleanupAction)children.getLast().state();
        require(!state.terminal()&&(state.phase()==PreparedCleanupAction.Phase.PREPARED||state.phase()==PreparedCleanupAction.Phase.UNKNOWN)
                &&state.preparationReference().equals(exact(row.get("preparation"))),"prepared NoEffect cannot replace an already terminal fifth child");
        var prepared=PreparedCleanupEvidence.loadPreparedOriginals(state.preparationReference(),archive);
        require(prepared.authorizationReference().equals(exact(row.get("authorization"))),"prepared NoEffect changed the old authorization");
        requirePrefix(parent,children,refs,prepared);
        var statusRef=exact(row.get("fresh_status"));var read=archive.loadRead(statusRef);
        require(archive.readReferenceOf(read).equals(statusRef),"prepared NoEffect Status original reference differs");
        var status=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
        status.requirePhysicalParent(parent.command());NativeRecordedEvidenceVerifier.requireRead(read,archive);read.original().custody().orElseThrow().verify(read);
        var ackRef=exact(row.get("fresh_snapshot_ack"));var outcome=archive.load(ackRef);
        require(outcome instanceof NativeActionPort.AckReceived&&archive.referenceOf(outcome).equals(ackRef),"prepared NoEffect full READ ACK original differs");
        var ack=(NativeActionPort.AckReceived)outcome;
        var f=object(row.get("fresh_frame"),"fresh_frame");require(f.members().keySet().equals(Set.of("native_frame","state_material","snapshot_id","native_revision","observed_at_utc")),"prepared NoEffect raw frame fields differ");
        var nativeRef=exact(f.get("native_frame"));byte[] packet=archive.loadNativeFrame(nativeRef);exactBytes(nativeRef,packet);
        var stateRef=exact(f.get("state_material"));var rawState=archive.loadFullMaterial(stateRef);exactBytes(stateRef,rawState.bytes());
        var query=read.original().custody().orElseThrow();var frame=new NativeObservationPort.ObservedFrame(query.session(),text(f.get("snapshot_id"),"snapshot_id"),
                positiveDecimal(f.get("native_revision"),"native_revision"),rawState,packet,instant(f.get("observed_at_utc"),"observed_at_utc"));
        var e=object(row.get("snapshot_received"),"snapshot_received");require(e.members().keySet().equals(Set.of("order","observed_at_utc")),"prepared NoEffect snapshot receive fields differ");
        var received=new NativeRequestChronology.Event(positiveDecimal(e.get("order"),"order"),instant(e.get("observed_at_utc"),"observed_at_utc"));
        var startRef=exact(row.get("old_sender_start"));var exitRef=exact(row.get("old_sender_exit"));var barrierRef=exact(row.get("serial_barrier"));
        var acceptanceRef=exact(row.get("accepted_observation"));var began=material(startRef,archive,MAXIMUM);var ended=material(exitRef,archive,MAXIMUM);
        var barrier=material(barrierRef,archive,MAXIMUM);Instant exitedAt=verifySender(began,ended,barrier,startRef,exitRef,parent,prepared);
        Instant issuedAt=instant(row.get("issued_at_utc"),"issued_at_utc"),deadline=instant(row.get("observation_deadline_utc"),"observation_deadline_utc");
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(2)))&&!issuedAt.isBefore(exitedAt)
                &&!query.writeEntered().observedAt().isBefore(issuedAt)&&query.writeEntered().observedAt().isBefore(read.request().deadline())
                &&!query.responseReceived().observedAt().isAfter(read.request().deadline())&&!read.request().deadline().isAfter(deadline),
                "prepared NoEffect observation is not the finite new post-exit read window");
        var oldIds=new java.util.HashSet<String>();oldIds.add(RequestIds.forCommand(parent.command()));oldIds.add(prepared.nativeRequestId());
        for(var child:children){oldIds.add(RequestIds.forCommand(child.command()));ActionTransitions.attempt(child.state()).ifPresent(a->oldIds.add(a.requestId()));ActionTransitions.dispatch(child.state()).ifPresent(d->oldIds.add(d.requestId()));}
        oldIds.add(prepared.aProof().freshStatus().receipt().requestId());oldIds.add(prepared.aProof().freshSnapshotAck().requestId());
        require(!oldIds.contains(read.requestId())&&!query.writeEntered().observedAt().isBefore(exitedAt)
                &&query.session().connectionGeneration().compareTo(prepared.aProof().freshFrame().session().connectionGeneration())>0,
                "prepared NoEffect Status reused an old request or connection");
        verifyFresh(prepared.aProof().original(),status,ack,frame,received,deadline,oldIds);
        verifyAccepted(material(acceptanceRef,archive,MAXIMUM),status,ack,frame);
        return new Originals(reference,parentRef,parent,children,refs,prepared,startRef,exitRef,barrierRef,acceptanceRef,status,ack,frame,received,issuedAt,deadline,exitedAt);
    }
    private static void requirePrefix(ActionReceipt parent,List<ActionReceipt> children,List<ExactRef> refs,PreparedCleanupEvidence.Prepared prepared) {
        require(parent.state() instanceof ActionState.CompositeUnknown&&parent.command().equals(prepared.parentReceipt().command())
                &&parent.bodySha256().equals(prepared.parentReceipt().bodySha256())&&parent.bodySha256().equals(ActionCodec.bodySha256(parent.command())),
                "prepared NoEffect changed the exact original UNKNOWN parent command/body");
        var current=((ActionState.CompositeUnknown)parent.state()).execution();var old=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();
        require(current.handlerId().equals(old.handlerId())&&current.handlerId().equals(LifeAdvanceComposite.HANDLER)&&current.startedAt().equals(old.startedAt())
                &&current.guard().equals(old.guard())&&current.children().size()==5&&current.children().subList(0,4).equals(old.children())
                &&children.subList(0,4).equals(prepared.children())&&refs.subList(0,4).equals(prepared.childReferences())
                &&children.subList(0,4).stream().allMatch(ActionReceipt::settled),"prepared NoEffect changed original four children or parent guard/deadline");
        for(int i=0;i<5;i++){var child=children.get(i);var binding=current.children().get(i);
            require(binding.actionId().equals(child.command().actionId())&&binding.bodySha256().equals(child.bodySha256())
                    &&child.bodySha256().equals(ActionCodec.bodySha256(child.command())),"prepared NoEffect child ordinal/body changed");}
        var fifth=children.getLast();require(fifth.command().equals(prepared.command())&&fifth.sequence()>parent.sequence()
                &&children.subList(0,4).stream().allMatch(c->c.sequence()<parent.sequence())
                &&fifth.command().actionId().equals(ActionIds.child(parent.command().actionId(),5,fifth.command().operation()))
                &&!fifth.settled(),"prepared NoEffect fifth receipt is not the original unresolved reserved prepared command");
        require(parent.command().origin() instanceof CommandOrigin.Gameplay&&parent.command().source().equals(prepared.command().source())
                &&parent.command().sessionId().equals(prepared.command().sessionId()),"prepared NoEffect parent/source/session differs");
    }
    private static Instant verifySender(Obj start,Obj end,Obj barrier,ExactRef startRef,ExactRef endRef,
            ActionReceipt parent,PreparedCleanupEvidence.Prepared prepared) {
        require(new Text("native-post-B-oldsender-barrier-reuse/v1").equals(barrier.get("schema")),"prepared NoEffect needs the distinct accepted post-B barrier role");
        require(sameContent(exact(barrier.get("new_sender_start")),startRef)&&sameContent(exact(barrier.get("new_sender_end")),endRef)
                &&sameContent(exact(barrier.get("accepted_machine_proof")),prepared.aProof().serialBarrier()),"prepared NoEffect barrier changed its exact sender/machine proof originals");
        var tool=object(start.get("tool"),"tool");var after=object(end.get("tool_after"),"tool_after");var sender=object(barrier.get("new_sender"),"new_sender");
        var pid=integer(tool.get("pid"),"pid");var birth=positiveDecimal(tool.get("birth"),"birth");var exit=integer(end.get("exit_code"),"exit_code");
        require(pid.signum()>0&&pid.equals(integer(end.get("tool_pid"),"tool_pid"))&&pid.equals(integer(after.get("pid"),"pid"))
                &&pid.equals(integer(sender.get("pid"),"pid"))&&birth.equals(positiveDecimal(sender.get("birth"),"birth"))
                &&BigInteger.valueOf(259).equals(integer(tool.get("exit"),"exit"))&&!BigInteger.valueOf(259).equals(exit)
                &&exit.equals(integer(after.get("Popen_exit_code"),"Popen_exit_code"))&&new Text("RETURNED").equals(end.get("status")),
                "prepared NoEffect sender lacks exact started identity and positive process exit");
        Instant began=instant(start.get("at_utc"),"at_utc"),ended=instant(end.get("at_utc"),"at_utc");
        require(!ended.isBefore(began)&&ended.equals(instant(sender.get("exited_at"),"exited_at")),"prepared NoEffect sender exit event differs");
        var game=parent.command().before().game();boolean found=false;
        for(var value:array(end.get("Game_keeper_after"),"Game_keeper_after")){var item=object(value,"process");
            if(BigInteger.valueOf(game.pid()).equals(integer(item.get("pid"),"pid"))){require(game.creationFiletime().value().equals(positiveDecimal(item.get("birth"),"birth"))
                    &&BigInteger.valueOf(259).equals(integer(item.get("exit"),"exit")),"prepared NoEffect changed actual retained Game identity");found=true;}}
        require(found&&barrier.get("same_Game_keeper_positive").equals(end.get("Game_keeper_after")),"prepared NoEffect barrier lost its same Game/keeper observations");
        return ended;
    }
    private static void verifyAccepted(Obj accepted,ClockStatusRead.Observation status,NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame) {
        require(new Text("xar.root-independent-post-B-noeffect-observation/v1").equals(accepted.get("schema")),"prepared NoEffect lacks the distinct actual post-B observation acceptance");
        var current=object(accepted.get("current_observation"),"current_observation");var game=object(current.get("game"),"game");
        require(new Text(status.receipt().requestId()).equals(current.get("status_request_id"))&&new Text(ack.requestId()).equals(current.get("fresh_request_id"))
                &&integer(current.get("native_revision"),"native_revision").equals(frame.nativeRevision())
                &&BigInteger.valueOf(frame.session().game().pid()).equals(integer(game.get("pid"),"pid"))
                &&frame.session().game().creationFiletime().value().equals(positiveDecimal(game.get("creation_filetime"),"creation_filetime"))
                &&instant(current.get("status_response_at"),"status_response_at").equals(status.receipt().original().custody().orElseThrow().responseReceived().observedAt())
                &&instant(current.get("fresh_snapshot_at"),"fresh_snapshot_at").equals(frame.observedAt()),"prepared NoEffect accepted observation was for another request/Game/frame");
        var named=array(accepted.get("actual_named_files_reopened"),"actual_named_files_reopened");
        require(namedPacket(named,status.receipt().original().originalPacket())&&namedPacket(named,ack.originalPacket())
                &&namedPacket(named,ack.outbound().orElseThrow().originalPacket())&&namedPacket(named,frame.originalPacket()),
                "prepared NoEffect changed the actual accepted Status/full-state wire originals");
        require(!instant(accepted.get("at_utc"),"at_utc").isBefore(ack.custody().orElseThrow().responseReceived().observedAt()),
                "prepared NoEffect acceptance predates its actual observations");
    }
    private static boolean namedPacket(List<Value> named,byte[] bytes) {
        for(var item:named){var ref=exact(item);if(ref.bytes()==bytes.length&&ref.sha256().equals(ActionCodec.sha256(bytes)))return true;}return false;
    }
    /** Archive closure only; full old authorization frames and private installed-source qualification remain mandatory above. */
    public static Originals verifyArchivedState(ActionReceipt terminal,ExactRef proofReference,PreparedCleanupAction originalPreparedState,
            ActionPorts.OutcomeArchive archive) {
        var data=loadOriginals(proofReference,archive);
        require(terminal.state() instanceof ActionState.PreparedCleanupNoEffectConfirmed,"prepared NoEffect archived role has another state type");
        var state=(ActionState.PreparedCleanupNoEffectConfirmed)terminal.state();
        require(state.proofReference().equals(proofReference)&&state.originalPreparedState().equals(originalPreparedState)
                &&data.originalPreparedState().equals(originalPreparedState)&&terminal.command().equals(data.child5().command())
                &&terminal.bodySha256().equals(data.child5().bodySha256())&&terminal.sequence()>data.child5().sequence()
                &&terminal.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT&&!terminal.visibleGameplay()&&!terminal.eligibleAdvance()
                &&terminal.ack().isEmpty()&&terminal.applied().isEmpty(),"prepared NoEffect terminal changed the original complete prepared state/command/body or invented ACK/credit");
        return data;
    }
    private static void verifyFresh(LifePostResumePauseCleanupProof.Original original,ClockStatusRead.Observation status,
            NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received,
            Instant deadline,Set<String> oldIds) {
        var query=status.receipt().original().custody().orElseThrow();var fresh=ack.custody().orElseThrow();fresh.verify(ack);
        require(ack.nativeOk()&&!ack.requestId().equals(query.requestId())&&!oldIds.contains(ack.requestId())
                &&fresh.session().equals(query.session())&&fresh.session().equals(frame.session())
                &&fresh.custodyEpoch().equals(query.custodyEpoch()),"prepared NoEffect independent full READ crossed its original held connection or request ID");
        require(fresh.writeEntered().order().compareTo(query.responseReceived().order())>0
                &&!fresh.writeEntered().observedAt().isBefore(query.responseReceived().observedAt())
                &&received.order().compareTo(fresh.writeCompleted().order())>0&&received.order().compareTo(fresh.responseReceived().order())<0
                &&!received.observedAt().isBefore(fresh.writeCompleted().observedAt())
                &&!received.observedAt().isAfter(fresh.responseReceived().observedAt())&&received.observedAt().equals(frame.observedAt())
                &&!fresh.responseReceived().observedAt().isAfter(deadline),"prepared NoEffect full state was not actually received after Status and between its own write and ACK");
        Obj outbound=packet(ack.outbound().orElseThrow().originalPacket());
        require(outbound.members().keySet().equals(Set.of("type","protocol_version","request_id","step","expected_revision"))
                &&new Text("execute_step").equals(outbound.get("type"))&&BigInteger.ONE.equals(integer(outbound.get("protocol_version"),"protocol_version"))
                &&new Text(ack.requestId()).equals(outbound.get("request_id"))
                &&new Text("query-fresh-full-state-v1").equals(outbound.get("step"))
                &&BigInteger.ZERO.equals(integer(outbound.get("expected_revision"),"expected_revision")),"prepared NoEffect full-state original outbound differs from the fixed read-only protocol");
        Obj wireAck=packet(ack.originalPacket());
        require(wireAck.members().keySet().equals(Set.of("type","protocol_version","request_id","ok","result"))
                &&new Text("command_result").equals(wireAck.get("type"))&&BigInteger.ONE.equals(integer(wireAck.get("protocol_version"),"protocol_version"))
                &&new Text(ack.requestId()).equals(wireAck.get("request_id"))&&new Bool(true).equals(wireAck.get("ok"))
                &&wireAck.equals(DriverJson.object(ack.originalFrame().bytes(),RawJson.MAXIMUM_BYTES)),"prepared NoEffect full-state framed ACK differs from its original");
        Obj result=object(wireAck.get("result"),"result");
        require(result.members().keySet().equals(Set.of("schema","request_id","snapshot_id","revision"))
                &&new Text("xar.native.fresh-full-state-read/v1").equals(result.get("schema"))
                &&new Text(ack.requestId()).equals(result.get("request_id"))&&new Text(frame.snapshotId()).equals(result.get("snapshot_id"))
                &&frame.nativeRevision().equals(integer(result.get("revision"),"revision"))
                &&result.equals(DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES)),
                "prepared NoEffect full-state result does not bind this independent raw packet");
        Obj raw=packet(frame.originalPacket());
        require(raw.members().keySet().equals(Set.of("type","protocol_version","snapshot_id","revision","state","read_request_id"))
                &&new Text("state_snapshot").equals(raw.get("type"))&&BigInteger.ONE.equals(integer(raw.get("protocol_version"),"protocol_version"))
                &&new Text(frame.snapshotId()).equals(raw.get("snapshot_id"))&&frame.nativeRevision().equals(integer(raw.get("revision"),"revision"))
                &&new Text(ack.requestId()).equals(raw.get("read_request_id")),"prepared NoEffect raw frame is not this read's independently received complete snapshot");
        Obj state=object(raw.get("state"),"state"),player=object(state.get("played_character"),"played_character");
        require(state.equals(DriverJson.object(frame.state().bytes(),RawJson.MAXIMUM_BYTES))&&new Bool(true).equals(state.get("paused"))
                &&new Bool(true).equals(state.get("map_ready"))&&new Bool(true).equals(player.get("alive")),"prepared NoEffect raw frame is not complete/paused/map-ready/alive");
        var pause=ActionEffects.observation(original.pause()).orElseThrow();var date=integer(state.get("date_raw"),"date_raw");
        require(date.equals(pause.after().frame().identity().dateRaw())&&integer(player.get("character_id"),"character_id").equals(pause.after().frame().identity().player())
                &&frame.session().game().equals(pause.after().game())&&frame.session().machineId().equals(pause.after().machineId())
                &&frame.nativeRevision().compareTo(status.physicalIdentity().orElseThrow().nativeRevision())>=0,
                "prepared NoEffect full frame crossed the original owner/Game/partial paused date");
        var delta=date.subtract(original.plan().startingDateRaw());var actual=status.status();AdvanceClock.requireSameSlot(original.originalArm(),actual);
        require(delta.signum()>0&&delta.mod(AdvancePlan.DAY).signum()==0&&date.compareTo(original.plan().targetDateRaw())<0
                &&actual.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED&&!actual.abnormal()&&!actual.terminalObserved()
                &&actual.completedDailyTicks()==delta.divide(AdvancePlan.DAY).longValueExact()&&actual.lastObservedDateRaw()==date.longValueExact()
                &&actual.triggerDateRaw()==0&&actual.intermediatePauseCount()==0&&actual.triggerFlags()==0&&actual.triggerReasons().isEmpty()
                &&actual.signedDateDeltaFromTargetRaw()==0&&actual.overshootDays()==-1&&!actual.pauseWrapperCalled()&&!actual.pauseObserved(),
                "prepared NoEffect Status does not retain the exact original nonterminal ARMED partial slot");
    }
    private static void exactBytes(ExactRef reference,byte[] bytes) {
        require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"prepared NoEffect original exact bytes changed");
    }
    private static ExactRef exact(Value value){return ExactRef.fromJson(toNode(object(value,"exact reference")));}
    private static Instant instant(Value value,String key){return Instant.parse(StrictJson.utc(text(value,key)));}
    private static BigInteger positiveDecimal(Value value,String key) {
        String decimal=text(value,key);require(decimal.matches("[1-9][0-9]*"),"prepared NoEffect canonical positive decimal required: "+key);
        var number=new BigInteger(decimal);require(number.compareTo(StrictJson.UINT64_MAX)<=0,"prepared NoEffect uint64 exceeded: "+key);return number;
    }
    private static Obj packet(byte[] bytes) {
        require(bytes.length>=5&&bytes.length<=RawJson.MAXIMUM_BYTES+4,"prepared NoEffect framed native packet size differs");
        int length=ByteBuffer.wrap(bytes,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        require(length==bytes.length-4,"prepared NoEffect native frame length prefix differs");
        return DriverJson.object(Arrays.copyOfRange(bytes,4,bytes.length),RawJson.MAXIMUM_BYTES);
    }
    private static boolean sameContent(ExactRef left,ExactRef right){return left.bytes()==right.bytes()&&left.sha256().equals(right.sha256());}
    private static ActionReceipt receipt(ExactRef reference,ActionPorts.OutcomeArchive archive){var value=archive.loadReceipt(reference);require(archive.receiptReferenceOf(value).equals(reference),"prepared NoEffect receipt original reference differs");return value;}
    private static Obj material(ExactRef reference,ActionPorts.OutcomeArchive archive,int maximum){require(reference.bytes()>0&&reference.bytes()<=maximum,"prepared NoEffect bounded material required");byte[] bytes=archive.loadMaterial(reference).bytes();exactBytes(reference,bytes);return DriverJson.object(bytes,maximum);}
}

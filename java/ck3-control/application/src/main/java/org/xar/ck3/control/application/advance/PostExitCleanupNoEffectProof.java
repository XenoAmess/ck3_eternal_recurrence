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

/** Archived DATA for one post-exit observed NoEffect. No method issues a Native permit,
 * proves NoDispatch, acknowledges CANCEL, completes a parent or qualifies a loaded DLL.
 * The installed source must separately accept the exact backend/OS originals and
 * revalidate canonical current parent/child membership under the actual writer lock. */
public final class PostExitCleanupNoEffectProof {
    public static final String SCHEMA="xar.life-post-exit-cleanup-no-effect/v1";
    private static final int MAXIMUM=64*1024;
    private static final Set<String> FIELDS=Set.of("schema","original_parent","original_children","authorization",
            "old_sender_exit","serial_barrier","fresh_status","fresh_snapshot_ack","fresh_frame",
            "snapshot_received","issued_at_utc","observation_deadline_utc");
    private static final Set<String> AUTH_FIELDS=Set.of("schema","original_parent","original_children",
            "armed_read","before_cancel","issued_at_utc","deadline_utc");
    private PostExitCleanupNoEffectProof() { }

    /** Structural/event-time originals only. This is not an installed-source witness. */
    public static class Originals {
        private final ExactRef proofReference,parentReference,authorizationReference,oldSenderExit,serialBarrier,child4Reference;
        private final List<ExactRef> childReferences;
        private final ActionReceipt parentReceipt;
        private final List<ActionReceipt> children;
        private final LifePostResumePauseCleanupProof.Original original;
        private final ClockStatusRead.Observation freshStatus;
        private final NativeActionPort.AckReceived freshSnapshotAck;
        private final NativeObservationPort.ObservedFrame freshFrame;
        private final NativeRequestChronology.Event snapshotReceived;
        private final Instant issuedAt,observationDeadline,oldSenderExitedAt;
        private final String backendDllSha256;
        private Originals(ExactRef proofReference,ExactRef parentReference,List<ExactRef> childReferences,
                ActionReceipt parentReceipt,List<ActionReceipt> children,ExactRef authorizationReference,
                ExactRef oldSenderExit,ExactRef serialBarrier,LifePostResumePauseCleanupProof.Original original,
                ClockStatusRead.Observation freshStatus,NativeActionPort.AckReceived freshSnapshotAck,
                NativeObservationPort.ObservedFrame freshFrame,NativeRequestChronology.Event snapshotReceived,
                Instant issuedAt,Instant observationDeadline,Instant oldSenderExitedAt,String backendDllSha256) {
            this.proofReference=proofReference;this.parentReference=parentReference;this.childReferences=List.copyOf(childReferences);
            this.child4Reference=this.childReferences.getLast();this.parentReceipt=parentReceipt;this.children=List.copyOf(children);
            this.authorizationReference=authorizationReference;this.oldSenderExit=oldSenderExit;this.serialBarrier=serialBarrier;
            this.original=original;this.freshStatus=freshStatus;this.freshSnapshotAck=freshSnapshotAck;this.freshFrame=freshFrame;
            this.snapshotReceived=snapshotReceived;this.issuedAt=issuedAt;this.observationDeadline=observationDeadline;
            this.oldSenderExitedAt=oldSenderExitedAt;this.backendDllSha256=backendDllSha256;
        }
        public ExactRef proofReference(){return proofReference;} public ExactRef parentReference(){return parentReference;}
        public ExactRef child4Reference(){return child4Reference;} public List<ExactRef> childReferences(){return childReferences;}
        public ActionReceipt parentReceipt(){return parentReceipt;} public List<ActionReceipt> children(){return children;}
        public ActionReceipt child4(){return children.getLast();} public ExactRef authorizationReference(){return authorizationReference;}
        public ExactRef oldSenderExit(){return oldSenderExit;} public ExactRef serialBarrier(){return serialBarrier;}
        public LifePostResumePauseCleanupProof.Original original(){return original;}
        public ClockStatusRead.Observation freshStatus(){return freshStatus;}
        public NativeActionPort.AckReceived freshSnapshotAck(){return freshSnapshotAck;}
        public NativeObservationPort.ObservedFrame freshFrame(){return freshFrame;}
        public NativeRequestChronology.Event snapshotReceived(){return snapshotReceived;}
        public Instant issuedAt(){return issuedAt;} public Instant observationDeadline(){return observationDeadline;}
        public Instant oldSenderExitedAt(){return oldSenderExitedAt;} public String backendDllSha256(){return backendDllSha256;}
    }
    /** Adds genuine archived old authorization/frame reconstruction; still no source or current-writer authority. */
    public static final class Verified extends Originals {
        private final LifePostResumePauseCleanupEvidence.Authorization authorization;
        private Verified(Originals data,LifePostResumePauseCleanupEvidence.Authorization authorization) {
            super(data.proofReference(),data.parentReference(),data.childReferences(),data.parentReceipt(),data.children(),
                    data.authorizationReference(),data.oldSenderExit(),data.serialBarrier(),data.original(),data.freshStatus(),
                    data.freshSnapshotAck(),data.freshFrame(),data.snapshotReceived(),data.issuedAt(),data.observationDeadline(),
                    data.oldSenderExitedAt(),data.backendDllSha256());this.authorization=authorization;
        }
        public LifePostResumePauseCleanupEvidence.Authorization authorization(){return authorization;}
    }

    public static ExactRef preserve(ActionReceipt parent,List<ActionReceipt> children,ExactRef authorization,
            ExactRef oldSenderExit,ExactRef serialBarrier,ClockStatusRead.Observation status,
            NativeActionPort.AckReceived freshSnapshotAck,NativeObservationPort.ObservedFrame freshFrame,
            NativeRequestChronology.Event snapshotReceived,Instant issuedAt,Instant observationDeadline,Instant actualNow,
            ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Objects.requireNonNull(actualNow);require(!actualNow.isBefore(issuedAt)&&actualNow.isBefore(observationDeadline),
                "post-exit observation producer has no current finite read window");
        require(!freshFrame.observedAt().isAfter(actualNow),"post-exit producer cannot preserve a future frame");
        return preserveArchivedOriginals(parent,children,authorization,oldSenderExit,serialBarrier,status,
                freshSnapshotAck,freshFrame,snapshotReceived,issuedAt,observationDeadline,archive,frames);
    }
    /** Historical original import only. The private installed source must accept the exact runtime/OS pins;
     * an expired READ window is never relabelled as a current observation or control permission. */
    public static ExactRef preserveArchivedOriginals(ActionReceipt parent,List<ActionReceipt> children,ExactRef authorization,
            ExactRef oldSenderExit,ExactRef serialBarrier,ClockStatusRead.Observation status,
            NativeActionPort.AckReceived freshSnapshotAck,NativeObservationPort.ObservedFrame freshFrame,
            NativeRequestChronology.Event snapshotReceived,Instant issuedAt,Instant observationDeadline,
            ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var row=StrictJson.object();row.put("schema",SCHEMA);row.set("original_parent",archive.receiptReferenceOf(parent).toJson());
        var refs=row.putArray("original_children");for(var child:children)refs.add(archive.receiptReferenceOf(child).toJson());
        row.set("authorization",authorization.toJson());row.set("old_sender_exit",oldSenderExit.toJson());
        row.set("serial_barrier",serialBarrier.toJson());row.set("fresh_status",archive.preserveRead(status.receipt()).toJson());
        row.set("fresh_snapshot_ack",archive.referenceOf(freshSnapshotAck).toJson());
        var frame=row.putObject("fresh_frame");frame.set("native_frame",archive.preserveNativeFrame(freshFrame).toJson());
        frame.set("state_material",archive.preserveMaterial(freshFrame.state()).toJson());
        frame.put("snapshot_id",freshFrame.snapshotId());frame.put("native_revision",freshFrame.nativeRevision().toString());
        frame.put("observed_at_utc",freshFrame.observedAt().toString());
        var received=row.putObject("snapshot_received");received.put("order",snapshotReceived.order().toString());
        received.put("observed_at_utc",snapshotReceived.observedAt().toString());
        row.put("issued_at_utc",issuedAt.toString());row.put("observation_deadline_utc",observationDeadline.toString());
        byte[] bytes=StrictJson.canonical(row);require(bytes.length<=MAXIMUM,"post-exit proof exceeds its material cap");
        var reference=archive.preserveMaterial(new RawJson(bytes));var verified=load(reference,archive,frames);
        require(verified.parentReceipt().equals(parent)&&verified.children().equals(children)
                &&verified.freshStatus().equals(status)&&verified.freshSnapshotAck().equals(freshSnapshotAck)
                &&verified.freshFrame().session().equals(freshFrame.session())
                &&Arrays.equals(verified.freshFrame().originalPacket(),freshFrame.originalPacket())
                &&verified.snapshotReceived().equals(snapshotReceived),"post-exit preserved originals differ from actual producer inputs");
        return reference;
    }
    public static Verified load(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var data=loadOriginals(reference,archive);
        var authorization=LifePostResumePauseCleanupEvidence.loadAuthorization(data.authorizationReference(),archive,frames);
        require(authorization.original().equals(data.original()),"post-exit semantic authorization differs from original DATA prefix");
        return new Verified(data,authorization);
    }
    /** No clock.now or Game query: historical replay uses the retained response/frame event times. */
    public static Originals loadOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        Obj row=material(reference,archive,MAXIMUM);
        require(row.members().keySet().equals(FIELDS)&&new Text(SCHEMA).equals(row.get("schema")),"post-exit proof schema or fields differ");
        ExactRef parentRef=exact(row.get("original_parent")),authorizationRef=exact(row.get("authorization"));
        ActionReceipt parent=receipt(parentRef,archive);var childRefs=new ArrayList<ExactRef>();var children=new ArrayList<ActionReceipt>();
        for(var value:array(row.get("original_children"),"original_children")) {var ref=exact(value);childRefs.add(ref);children.add(receipt(ref,archive));}
        require(children.size()==4&&childRefs.stream().distinct().count()==4&&childRefs.stream().noneMatch(parentRef::equals),
                "post-exit proof requires all four distinct original children");
        require(parent.state() instanceof ActionState.CompositeUnknown,"post-exit subject parent must remain its original UNKNOWN");
        var unknown=(ActionState.CompositeUnknown)parent.state();var cursor=unknown.execution();var child4=children.getLast();
        require(child4.state() instanceof ActionState.Unknown&&cursor.children().size()==4
                &&unknown.reason().startsWith(LifePostResumePauseCleanupEvidence.CURSOR_PREFIX)
                &&!unknown.evidence().isEmpty()&&unknown.evidence().getLast().equals(authorizationRef),
                "post-exit proof requires exact original cleanup UNKNOWN4 and its durable authorization");
        for(int i=0;i<4;i++) {var bound=cursor.children().get(i);var child=children.get(i);
            require(bound.actionId().equals(child.command().actionId())&&bound.bodySha256().equals(child.bodySha256()),
                    "post-exit original child ordinal/body differs");}
        Obj auth=material(authorizationRef,archive,MAXIMUM);
        require(auth.members().keySet().equals(AUTH_FIELDS)&&new Text(LifePostResumePauseCleanupEvidence.AUTHORIZATION_SCHEMA).equals(auth.get("schema")),
                "post-exit original authorization schema or fields differ");
        var originalParent=receipt(exact(auth.get("original_parent")),archive);var prefix=new ArrayList<ActionReceipt>();
        for(var value:array(auth.get("original_children"),"original_children"))prefix.add(receipt(exact(value),archive));
        require(prefix.size()==3&&children.subList(0,3).equals(prefix)&&parent.command().equals(originalParent.command())
                &&parent.bodySha256().equals(originalParent.bodySha256()),"post-exit changed original parent or first three receipts");
        var original=LifePostResumePauseCleanupProof.original(originalParent,prefix);
        var originalExecution=((ActionState.CompositeUnknown)originalParent.state()).execution();
        require(cursor.handlerId().equals(originalExecution.handlerId())&&cursor.startedAt().equals(originalExecution.startedAt())
                &&cursor.guard().equals(originalExecution.guard())&&cursor.children().subList(0,3).equals(originalExecution.children())
                &&child4.sequence()>originalParent.sequence()&&parent.sequence()>child4.sequence(),"post-exit execution or canonical original ordering differs");
        var before=LifeAdvanceEvidence.decodeFrame(object(auth.get("before_cancel"),"before_cancel"),false);
        reopenFrameOriginals(before,archive);
        Instant ownDeadline=instant(auth.get("deadline_utc"),"deadline_utc");
        var operation=new OperationKey(ClockStatusRead.CANCEL_PREFIX+original.originalArm().generation().decimal());
        var args=new Obj(java.util.Map.of());var command=new ActionCommand(ActionIds.child(parent.command().actionId(),4,operation),
                before.identity(),parent.command().source(),parent.command().sessionId(),operation,args,
                AdvancePrimitives.expected(before.identity(),parent.command().source(),operation,args),parent.command().claims(),ownDeadline);
        require(child4.command().equals(command)&&child4.bodySha256().equals(ActionCodec.bodySha256(command)),"post-exit child4 is not the immutable authorized exact CANCEL");
        var authReadRef=exact(auth.get("armed_read"));var authRead=archive.loadRead(authReadRef);
        require(archive.readReferenceOf(authRead).equals(authReadRef),"post-exit original authorization Status reference differs");
        NativeRecordedEvidenceVerifier.requireRead(authRead,archive);authRead.original().custody().orElseThrow().verify(authRead);
        var statusRef=exact(row.get("fresh_status"));var read=archive.loadRead(statusRef);
        require(archive.readReferenceOf(read).equals(statusRef)&&!statusRef.equals(authReadRef),"post-exit Status is not its distinct complete original read");
        var status=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
        status.requirePhysicalParent(parent.command());NativeRecordedEvidenceVerifier.requireRead(read,archive);
        var custody=LifeSentinelCancellationProof.physical(parent.command(),read);custody.verify(read);
        var oldCustody=authRead.original().custody().orElseThrow();
        require(custody.session().machineId().equals(oldCustody.session().machineId())
                &&custody.session().game().equals(oldCustody.session().game())&&custody.session().sessionId().equals(oldCustody.session().sessionId())
                &&custody.session().connectionGeneration().compareTo(oldCustody.session().connectionGeneration())>0
                &&!custody.custodyEpoch().equals(oldCustody.custodyEpoch()),"post-exit Status is not a new connection of the exact original Game/session");
        var ids=new java.util.HashSet<String>();ids.add(RequestIds.forCommand(parent.command()));ids.add(authRead.requestId());
        for(var child:children){ids.add(RequestIds.forCommand(child.command()));ActionTransitions.attempt(child.state()).ifPresent(a->ids.add(a.requestId()));}
        require(!ids.contains(read.requestId()),"post-exit Status reused an original parent/child/native request ID");
        ExactRef exitRef=exact(row.get("old_sender_exit")),barrierRef=exact(row.get("serial_barrier"));
        Instant exitedAt=oldExit(material(exitRef,archive,MAXIMUM),parent);
        Obj barrier=material(barrierRef,archive,MAXIMUM);String dll=barrier(barrier,exitRef);
        Instant issuedAt=instant(row.get("issued_at_utc"),"issued_at_utc"),deadline=instant(row.get("observation_deadline_utc"),"observation_deadline_utc");
        require(issuedAt.isBefore(deadline)&&!deadline.isAfter(issuedAt.plus(Duration.ofMinutes(2)))
                &&child4.command().deadline().isBefore(exitedAt)&&!issuedAt.isBefore(exitedAt)
                &&!custody.writeEntered().observedAt().isBefore(issuedAt)&&!read.request().deadline().isAfter(deadline)
                &&!custody.responseReceived().observedAt().isAfter(read.request().deadline()),"post-exit Status escaped the new finite post-release observation window");
        var loadedAck=archive.load(exact(row.get("fresh_snapshot_ack")));
        require(loadedAck instanceof NativeActionPort.AckReceived,"post-exit full-state original is not an ACK");
        var freshAck=(NativeActionPort.AckReceived)loadedAck;
        require(archive.referenceOf(freshAck).equals(exact(row.get("fresh_snapshot_ack"))),"post-exit full-state ACK original reference differs");
        Obj frame=object(row.get("fresh_frame"),"fresh_frame");
        require(frame.members().keySet().equals(Set.of("native_frame","state_material","snapshot_id","native_revision","observed_at_utc")),"post-exit frame fields differ");
        byte[] packet=archive.loadNativeFrame(exact(frame.get("native_frame")));exactBytes(exact(frame.get("native_frame")),packet);
        Obj snapshot=packet(packet);Obj state=object(snapshot.get("state"),"state");
        var stateReference=exact(frame.get("state_material"));
        RawJson originalState=archive.loadFullMaterial(stateReference);exactBytes(stateReference,originalState.bytes());
        require(state.equals(DriverJson.object(originalState.bytes(),RawJson.MAXIMUM_BYTES)),
                "post-exit original state material differs from its complete raw native packet");
        var observed=new NativeObservationPort.ObservedFrame(custody.session(),text(frame.get("snapshot_id"),"snapshot_id"),
                positiveDecimal(frame.get("native_revision"),"native_revision"),originalState,packet,
                instant(frame.get("observed_at_utc"),"observed_at_utc"));
        Obj event=object(row.get("snapshot_received"),"snapshot_received");
        require(event.members().keySet().equals(Set.of("order","observed_at_utc")),"post-exit snapshot event fields differ");
        var received=new NativeRequestChronology.Event(positiveDecimal(event.get("order"),"order"),instant(event.get("observed_at_utc"),"observed_at_utc"));
        verifyFresh(original,status,freshAck,observed,received,deadline,ids);
        return new Originals(reference,parentRef,childRefs,parent,children,authorizationRef,exitRef,barrierRef,original,status,freshAck,
                observed,received,issuedAt,deadline,exitedAt,dll);
    }

    private static void verifyFresh(LifePostResumePauseCleanupProof.Original original,ClockStatusRead.Observation status,
            NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received,
            Instant deadline,Set<String> oldIds) {
        var query=status.receipt().original().custody().orElseThrow();var fresh=ack.custody().orElseThrow();fresh.verify(ack);
        require(ack.nativeOk()&&!ack.requestId().equals(query.requestId())&&!oldIds.contains(ack.requestId())
                &&fresh.session().equals(query.session())&&fresh.session().equals(frame.session())
                &&fresh.custodyEpoch().equals(query.custodyEpoch()),"post-exit independent full READ crossed its original held connection or request ID");
        require(fresh.writeEntered().order().compareTo(query.responseReceived().order())>0
                &&!fresh.writeEntered().observedAt().isBefore(query.responseReceived().observedAt())
                &&received.order().compareTo(fresh.writeCompleted().order())>0&&received.order().compareTo(fresh.responseReceived().order())<0
                &&!received.observedAt().isBefore(fresh.writeCompleted().observedAt())
                &&!received.observedAt().isAfter(fresh.responseReceived().observedAt())&&received.observedAt().equals(frame.observedAt())
                &&!fresh.responseReceived().observedAt().isAfter(deadline),"post-exit full state was not actually received after Status and between its own write and ACK");
        Obj outbound=packet(ack.outbound().orElseThrow().originalPacket());
        require(outbound.members().keySet().equals(Set.of("type","protocol_version","request_id","step","expected_revision"))
                &&new Text("execute_step").equals(outbound.get("type"))&&BigInteger.ONE.equals(integer(outbound.get("protocol_version"),"protocol_version"))
                &&new Text(ack.requestId()).equals(outbound.get("request_id"))
                &&new Text("query-fresh-full-state-v1").equals(outbound.get("step"))
                &&BigInteger.ZERO.equals(integer(outbound.get("expected_revision"),"expected_revision")),"post-exit full-state original outbound differs from the fixed read-only protocol");
        Obj wireAck=packet(ack.originalPacket());
        require(wireAck.members().keySet().equals(Set.of("type","protocol_version","request_id","ok","result"))
                &&new Text("command_result").equals(wireAck.get("type"))&&BigInteger.ONE.equals(integer(wireAck.get("protocol_version"),"protocol_version"))
                &&new Text(ack.requestId()).equals(wireAck.get("request_id"))&&new Bool(true).equals(wireAck.get("ok"))
                &&wireAck.equals(DriverJson.object(ack.originalFrame().bytes(),RawJson.MAXIMUM_BYTES)),"post-exit full-state framed ACK differs from its original");
        Obj result=object(wireAck.get("result"),"result");
        require(result.members().keySet().equals(Set.of("schema","request_id","snapshot_id","revision"))
                &&new Text("xar.native.fresh-full-state-read/v1").equals(result.get("schema"))
                &&new Text(ack.requestId()).equals(result.get("request_id"))&&new Text(frame.snapshotId()).equals(result.get("snapshot_id"))
                &&frame.nativeRevision().equals(integer(result.get("revision"),"revision"))
                &&result.equals(DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES)),
                "post-exit full-state result does not bind this independent raw packet");
        Obj raw=packet(frame.originalPacket());
        require(raw.members().keySet().equals(Set.of("type","protocol_version","snapshot_id","revision","state","read_request_id"))
                &&new Text("state_snapshot").equals(raw.get("type"))&&BigInteger.ONE.equals(integer(raw.get("protocol_version"),"protocol_version"))
                &&new Text(frame.snapshotId()).equals(raw.get("snapshot_id"))&&frame.nativeRevision().equals(integer(raw.get("revision"),"revision"))
                &&new Text(ack.requestId()).equals(raw.get("read_request_id")),"post-exit raw frame is not this read's independently received complete snapshot");
        Obj state=object(raw.get("state"),"state"),player=object(state.get("played_character"),"played_character");
        require(state.equals(DriverJson.object(frame.state().bytes(),RawJson.MAXIMUM_BYTES))&&new Bool(true).equals(state.get("paused"))
                &&new Bool(true).equals(state.get("map_ready"))&&new Bool(true).equals(player.get("alive")),"post-exit raw frame is not complete/paused/map-ready/alive");
        var pause=ActionEffects.observation(original.pause()).orElseThrow();var date=integer(state.get("date_raw"),"date_raw");
        require(date.equals(pause.after().frame().identity().dateRaw())&&integer(player.get("character_id"),"character_id").equals(pause.after().frame().identity().player())
                &&frame.session().game().equals(pause.after().game())&&frame.session().machineId().equals(pause.after().machineId())
                &&frame.nativeRevision().compareTo(status.physicalIdentity().orElseThrow().nativeRevision())>=0,
                "post-exit full frame crossed the original owner/Game/partial paused date");
        var delta=date.subtract(original.plan().startingDateRaw());var actual=status.status();AdvanceClock.requireSameSlot(original.originalArm(),actual);
        require(delta.signum()>0&&delta.mod(AdvancePlan.DAY).signum()==0&&date.compareTo(original.plan().targetDateRaw())<0
                &&actual.state()==org.xar.ck3.control.reconciliation.LateOutcome.State.ARMED&&!actual.abnormal()&&!actual.terminalObserved()
                &&actual.completedDailyTicks()==delta.divide(AdvancePlan.DAY).longValueExact()&&actual.lastObservedDateRaw()==date.longValueExact()
                &&actual.triggerDateRaw()==0&&actual.intermediatePauseCount()==0&&actual.triggerFlags()==0&&actual.triggerReasons().isEmpty()
                &&actual.signedDateDeltaFromTargetRaw()==0&&actual.overshootDays()==-1&&!actual.pauseWrapperCalled()&&!actual.pauseObserved(),
                "post-exit Status does not retain the exact original nonterminal ARMED partial slot");
    }

    private static Instant oldExit(Obj row,ActionReceipt parent) {
        var processes=object(row.get("processes"),"processes");var host=object(processes.get("oldHost"),"oldHost");
        var before=object(host.get("before"),"before");var after=object(host.get("after"),"after");
        require(integer(before.get("pid"),"pid").signum()>0&&before.get("pid").equals(after.get("pid"))
                &&positiveDecimal(before.get("birth"),"birth").equals(positiveDecimal(after.get("birth"),"birth"))
                &&BigInteger.valueOf(259).equals(integer(before.get("exit"),"exit"))
                &&!BigInteger.valueOf(259).equals(integer(after.get("exit"),"exit")),"post-exit original does not contain exact exited old sender identity");
        var game=object(processes.get("Game"),"Game");var gameBefore=object(game.get("before"),"before");var gameAfter=object(game.get("after"),"after");
        require(gameBefore.equals(gameAfter)&&BigInteger.valueOf(parent.command().before().game().pid()).equals(integer(gameAfter.get("pid"),"pid"))
                &&parent.command().before().game().creationFiletime().value().equals(positiveDecimal(gameAfter.get("birth"),"birth"))
                &&BigInteger.valueOf(259).equals(integer(gameAfter.get("exit"),"exit")),"post-exit original crossed the exact retained Game identity");
        var keeper=object(processes.get("keeper"),"keeper");var keeperBefore=object(keeper.get("before"),"before");var keeperAfter=object(keeper.get("after"),"after");
        require(keeperBefore.equals(keeperAfter)&&integer(keeperAfter.get("pid"),"pid").signum()>0
                &&positiveDecimal(keeperAfter.get("birth"),"birth").signum()>0&&BigInteger.valueOf(259).equals(integer(keeperAfter.get("exit"),"exit")),
                "post-exit original changed its retained keeper identity");
        Instant begin=instant(row.get("began_at_utc"),"began_at_utc"),end=instant(row.get("ended_at_utc"),"ended_at_utc");
        require(!end.isBefore(begin),"post-exit original OS release time regressed");return end;
    }
    private static String barrier(Obj row,ExactRef exitReference) {
        require(new Text("native.C81.post-old-sender-exit-status-serial-barrier-conditional-qualification/v1").equals(row.get("schema"))
                &&new Text("CONDITIONAL_TRANSPORT_EXECUTION_BARRIER_QUALIFIED; ACTUAL_NO_EFFECT_NOT_HELD").equals(row.get("decision")),
                "post-exit needs its accepted serial-barrier qualification schema, not a caller boolean");
        var dll=exact(row.get("exact_DLL"));require(dll.bytes()>0,"post-exit barrier lacks exact DLL metadata");
        var sender=object(row.get("old_Java_future_sender_barrier"),"old_Java_future_sender_barrier");
        var exit=exact(sender.get("actual"));require(exit.bytes()==exitReference.bytes()&&exit.sha256().equals(exitReference.sha256()),
                "post-exit barrier was qualified against another old sender release original");
        var serial=object(row.get("single_worker_connection_barrier"),"single_worker_connection_barrier");
        for(String name:List.of("original_target_match","original_serial_proof","actual_WorkerTail"))require(exact(serial.get(name)).bytes()>0,"post-exit barrier omitted original code proof reference");
        require(exact(object(row.get("Status_accessor"),"Status_accessor").get("actual_bytes")).bytes()>0,
                "post-exit barrier omitted exact Status accessor bytes");
        // This reads metadata and exact retained qualification bytes only. Installed Root must
        // independently accept these pins and same loaded backend/worker/lifecycle semantics.
        return dll.sha256();
    }
    /** Shared original-closure check; it grants no current source authority or terminal-state type. */
    public static Originals verifyArchivedState(ActionReceipt terminal,ExactRef proofReference,
            java.util.Optional<ActionState.Attempt> retainedAttempt,
            java.util.Optional<NativeActionPort.DispatchOutcome> retainedDispatch,ActionPorts.OutcomeArchive archive) {
        var data=loadOriginals(proofReference,archive);var unknown=(ActionState.Unknown)data.child4().state();
        require(terminal.outcome()==ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT
                &&terminal.command().equals(data.child4().command())&&terminal.bodySha256().equals(data.child4().bodySha256())
                &&terminal.sequence()>data.child4().sequence()&&unknown.attempt().equals(retainedAttempt)&&unknown.dispatch().equals(retainedDispatch),
                "post-exit terminal changed the original UNKNOWN command/body/optional Attempt or dispatch");
        return data;
    }
    private static void reopenFrameOriginals(LifeAdvanceEvidence.FrameRecord frame,ActionPorts.OutcomeArchive archive) {
        byte[] packet=archive.loadNativeFrame(frame.nativeFrame());exactBytes(frame.nativeFrame(),packet);
        byte[] facts=archive.loadFullMaterial(frame.driverFacts()).bytes();exactBytes(frame.driverFacts(),facts);
        byte[] semantic=archive.loadFullMaterial(frame.semantic()).bytes();exactBytes(frame.semantic(),semantic);
        Obj data=DriverJson.object(semantic,RawJson.MAXIMUM_BYTES);
        require(exact(data.get("java_driver_facts_evidence")).equals(frame.driverFacts()),
                "post-exit authorization frame substituted its original Driver facts manifest");
    }
    private static ActionReceipt receipt(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        var value=archive.loadReceipt(reference);require(archive.receiptReferenceOf(value).equals(reference),"post-exit receipt original reference differs");return value;
    }
    private static Obj material(ExactRef reference,ActionPorts.OutcomeArchive archive,int maximum) {
        require(reference.bytes()>0&&reference.bytes()<=maximum,"post-exit original material size is outside its role");
        byte[] bytes=archive.loadMaterial(reference).bytes();exactBytes(reference,bytes);return DriverJson.object(bytes,maximum);
    }
    private static void exactBytes(ExactRef reference,byte[] bytes) {
        require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"post-exit original exact bytes changed");
    }
    private static ExactRef exact(Value value){return ExactRef.fromJson(toNode(object(value,"exact reference")));}
    private static Instant instant(Value value,String key){return Instant.parse(StrictJson.utc(text(value,key)));}
    private static BigInteger positiveDecimal(Value value,String key) {
        String decimal=text(value,key);require(decimal.matches("[1-9][0-9]*"),"post-exit canonical positive decimal required: "+key);
        var number=new BigInteger(decimal);require(number.compareTo(StrictJson.UINT64_MAX)<=0,"post-exit uint64 exceeded: "+key);return number;
    }
    private static Obj packet(byte[] bytes) {
        require(bytes.length>=5&&bytes.length<=RawJson.MAXIMUM_BYTES+4,"post-exit framed native packet size differs");
        int length=ByteBuffer.wrap(bytes,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
        require(length==bytes.length-4,"post-exit native frame length prefix differs");
        return DriverJson.object(Arrays.copyOfRange(bytes,4,bytes.length),RawJson.MAXIMUM_BYTES);
    }
}

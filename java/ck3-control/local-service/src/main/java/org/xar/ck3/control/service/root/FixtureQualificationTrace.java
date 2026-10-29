package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.readiness.ReadinessArchive;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Durable original qualification replay; decoding rows is never a live scope or entry permit. */
public final class FixtureQualificationTrace {
    public static final String SCHEMA="xar.java.fixture-qualification-trace/v1";
    private final RootRuntimeContext context;
    private final PreparedFixture fixture;
    private final FixtureStartSubmission submission;
    private final ArrayList<ObjectNode> rows=new ArrayList<>();
    public FixtureQualificationTrace(RootRuntimeContext context,PreparedFixture fixture,FixtureStartSubmission submission) {
        this.context=java.util.Objects.requireNonNull(context);this.fixture=java.util.Objects.requireNonNull(fixture);this.submission=java.util.Objects.requireNonNull(submission);
    }
    public FixtureQualificationLogs.Observation preserveLogs(Session same,FixtureQualificationLogs.Observation observed)throws IOException {
        context.writer().requireSession(same);if(!observed.exists())return observed;
        ExactRef source=observed.source().orElseThrow();byte[] raw=Files.readAllBytes(Path.of(source.path()));
        StrictJson.require(raw.length==source.bytes()&&DriverJson.sha256(raw).equals(source.sha256()),"fixture original logs changed before immutable archive");
        ExactRef retained=context.archive().preserveArtifact(same,raw,64*1024*1024);
        return new FixtureQualificationLogs.Observation(true,Optional.of(retained),observed.matches());
    }
    public void owner(SemanticEvidence actual,ExactRef sourceQualification,FixtureQualificationLogs.Observation logs,boolean eventAllowed,NativeFreshSnapshotPort.Received originalRead) {
        ObjectNode n=sample("owner",actual,Optional.of(sourceQualification),logs,eventAllowed,originalRead);append(n);
    }
    public void owner(SemanticEvidence actual,Optional<ExactRef> sourceQualification,FixtureQualificationLogs.Observation logs,boolean eventAllowed,NativeFreshSnapshotPort.Received originalRead) {
        ObjectNode n=sample("owner",actual,sourceQualification,logs,eventAllowed,originalRead);append(n);
    }
    public void business(SemanticEvidence actual,ExactRef sourceQualification,FixtureQualificationLogs.Observation logs,boolean eventAllowed,PlanningReadReceipt root,NativeFreshSnapshotPort.Received originalRead) {
        var same=borrowed();ObjectNode n=sample("business",actual,Optional.of(sourceQualification),logs,eventAllowed,originalRead);n.set("root",context.archive().withSession(same).readReferenceOf(root).toJson());append(n);
    }
    public void business(SemanticEvidence actual,Optional<ExactRef> sourceQualification,FixtureQualificationLogs.Observation logs,boolean eventAllowed,PlanningReadReceipt root,NativeFreshSnapshotPort.Received originalRead) {
        var same=borrowed();ObjectNode n=sample("business",actual,sourceQualification,logs,eventAllowed,originalRead);n.set("root",context.archive().withSession(same).readReferenceOf(root).toJson());append(n);
    }
    public void event(SemanticEvidence before,SemanticEvidence after,PlanningReadReceipt original,
            FixtureStartupHandler.Decision decision,Optional<ActionReceipt> submitted,NativeFreshSnapshotPort.Received independentAfter) {
        var archive=context.archive().withSession(borrowed());ObjectNode n=StrictJson.object().put("kind","event");
        n.set("before",OrdinaryCycleTransitions.semanticToJson(before));n.set("after",OrdinaryCycleTransitions.semanticToJson(after));
        n.set("read",archive.readReferenceOf(original).toJson());n.set("decision",DriverJson.toNode(FixtureStartupHandler.encodeDecision(decision)));
        n.set("independent_after",fresh(after,independentAfter));
        n.set("child",submitted.<JsonNode>map(value->archive.receiptReferenceOf(value).toJson()).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));
        if(!rows.isEmpty()&&StrictJson.text(rows.getLast().get("kind")).equals("event_pending")) {
            StrictJson.require(submitted.isPresent()&&StrictJson.text(rows.getLast().get("child_action_id")).equals(submitted.orElseThrow().command().actionId()),"startup continuation changed its original reserved child");rows.set(rows.size()-1,n);
        }else append(n);
    }
    public void pendingEvent(SemanticEvidence before,PlanningReadReceipt original,FixtureStartupHandler.Decision decision,ActionCommand exactChild) {
        var archive=context.archive().withSession(borrowed());ObjectNode n=StrictJson.object().put("kind","event_pending").put("child_action_id",exactChild.actionId()).put("child_body_sha256",ActionCodec.bodySha256(exactChild));
        n.set("before",OrdinaryCycleTransitions.semanticToJson(before));n.set("read",archive.readReferenceOf(original).toJson());n.set("decision",DriverJson.toNode(FixtureStartupHandler.encodeDecision(decision)));append(n);
    }
    private void append(ObjectNode n){StrictJson.require(rows.size()<4096,"fixture original qualification trace exceeds finite bound");rows.add(n);}
    private ObjectNode sample(String kind,SemanticEvidence actual,Optional<ExactRef> sourceQualification,FixtureQualificationLogs.Observation logs,boolean allow,NativeFreshSnapshotPort.Received read) {
        ObjectNode n=StrictJson.object().put("kind",kind).put("event_allowed",allow);n.set("semantic",OrdinaryCycleTransitions.semanticToJson(actual));
        n.set("source_qualification",ExactRef.optionalToJson(sourceQualification));
        n.set("independent_read",fresh(actual,read));
        n.set("log",logs.source().<JsonNode>map(ExactRef::toJson).orElse(com.fasterxml.jackson.databind.node.NullNode.instance));return n;
    }
    private ObjectNode fresh(SemanticEvidence actual,NativeFreshSnapshotPort.Received read) {
        StrictJson.require(read.originalFrame().observedAt().equals(actual.observedAt()),"fixture sample is not this actual independent READ frame");
        ObjectNode row=StrictJson.object().put("snapshot_order",new CrossJsDecimalUInt64(read.snapshotReceived().order().toString()).decimal()).put("snapshot_observed_at",read.snapshotReceived().observedAt().toString());
        row.set("acknowledgement",context.archive().withSession(borrowed()).preserve(read.acknowledgement()).toJson());return row;
    }
    public ExactRef preserve(Session same,ActionCommand parent)throws IOException {
        context.writer().requireSession(same);ObjectNode n=StrictJson.object().put("schema",SCHEMA).put("parent_action_id",parent.actionId()).put("parent_body_sha256",ActionCodec.bodySha256(parent));
        n.set("policy",fixture.policySource().toJson());n.set("submission",submission.toJson());var array=n.putArray("rows");rows.forEach(array::add);
        return context.archive().withSession(same).preserveMaterial(new RawJson(StrictJson.canonical(n,16*1024*1024)));
    }
    public static void verify(RootRuntimeContext context,Session same,PreparedFixture fixture,ActionCommand parent,
            FixtureBusinessEvidence original)throws IOException {
        context.writer().requireSession(same);var archive=context.archive().withSession(same);original.validateParent(parent);
        ObjectNode trace=StrictJson.object(StrictJson.parse(archive.loadFullMaterial(original.qualification()).bytes(),16*1024*1024),
                Set.of("schema","parent_action_id","parent_body_sha256","policy","submission","rows"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(trace.get("schema")))&&parent.actionId().equals(StrictJson.text(trace.get("parent_action_id")))
                &&ActionCodec.bodySha256(parent).equals(StrictJson.text(trace.get("parent_body_sha256")))&&fixture.policySource().equals(ExactRef.fromJson(trace.get("policy"))),"fixture qualification changed exact parent/policy");
        var submission=FixtureStartSubmission.fromJson(trace.get("submission"));var reducer=new FixtureBusinessQualification(fixture,submission);
        StrictJson.require(java.util.Arrays.equals(StrictJson.canonical(StrictJson.parse(submission.acknowledgement().bytes())),StrictJson.canonical(StrictJson.parse(FixtureFrontendProducer.ack(original.originalStart()).bytes()))),"fixture qualifier substituted original Start ACK");
        JsonNode rows=trace.get("rows");StrictJson.require(rows.isArray()&&rows.size()>0&&rows.size()<=4096,"complete finite fixture observations required");
        SemanticEvidence finalSemantic=null;PlanningReadReceipt finalRoot=null;OpportunityJson.Value preserved=null;boolean observedScenario=false;
        FixtureBusinessQualification.Owner previousOwner=null,currentOwner=null;
        for(JsonNode input:rows) {
            String kind=StrictJson.text(input.get("kind"));
            if(kind.equals("event")) {
                ObjectNode row=StrictJson.object(input,Set.of("kind","before","after","read","decision","child","independent_after"));
                var before=OrdinaryCycleTransitions.semanticFromJson(row.get("before"));var after=OrdinaryCycleTransitions.semanticFromJson(row.get("after"));
                var beforeData=semantic(context,same,before);var afterData=semantic(context,same,after);
                var read=archive.loadRead(ExactRef.fromJson(row.get("read")));NativeRecordedEvidenceVerifier.requireRead(read,archive);
                verifyFresh(context,same,after,row.get("independent_after"),read.original());
                var installedWindow=context.frontend().fixtureCatalog().remainingDomains().events().eventWindowContract();
                StrictJson.require(read.contractId().equals(installedWindow.contractId())&&read.request().operation().equals(installedWindow.operation())
                        &&read.request().before().equals(before.frame())&&read.request().source().equals(parent.source())
                        &&read.request().sessionId().equals(parent.sessionId()),"startup event read changed actual installed contract/admitted owner/frame");
                var decision=FixtureStartupHandler.decodeDecision(DriverJson.object(StrictJson.canonical(row.get("decision"),65536),65536));
                if(decision instanceof FixtureStartupHandler.ObserveOnly) {
                    StrictJson.require(row.get("child").isNull()&&fixture.policy().kind()==FrontendFixturePolicy.Kind.SCENARIO
                            &&beforeData.get("active_event").equals(afterData.get("active_event")),"scenario observe-only cannot select or change original event");
                    var window=DriverJson.object(read.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
                    FixtureStartupObservation.validatePresentation(fixture,submission,java.util.Objects.requireNonNull(previousOwner),java.util.Objects.requireNonNull(currentOwner),beforeData,window,afterData);
                    preserved=beforeData.get("active_event");observedScenario=true;
                } else {
                    StrictJson.require(!row.get("child").isNull(),"startup selection omitted its actual canonical child");
                    ActionReceipt child=archive.loadReceipt(ExactRef.fromJson(row.get("child")));StrictJson.require(child.settled(),"startup event action remains unknown; no qualification");
                    var canonical=ContinuityActionJournal.lookup(same.head().state(),child.command().actionId(),archive).orElseThrow();
                    StrictJson.require(canonical.equals(child),"startup qualification changed canonical child history");
                    var source=OpportunityJson.object(child.command().arguments().get("fixture_startup_event_source"),"actual startup child source");
                    StrictJson.require(new OpportunityJson.Text(parent.actionId()).equals(source.get("original_parent_action_id"))
                            &&fixture.policySource().equals(ExactRef.fromJson(DriverJson.toNode(source.get("policy_source"))))
                            &&archive.readReferenceOf(read).equals(ExactRef.fromJson(DriverJson.toNode(source.get("original_read"))))
                            &&FixtureStartupHandler.encodeDecision(decision).equals(child.command().arguments().get("fixture_startup_handler_decision")),
                            "startup qualification changed the canonical child's original parent/read/handler decision");
                    context.bindings().actualArchivedVerifier(child.command().operation()).orElseThrow().verifier().verify(same.head(),child,archive);
                    var event=OpportunityJson.object(beforeData.get("active_event"),"active_event");var afterEvent=afterData.get("active_event");
                    StrictJson.require(!(afterEvent instanceof OpportunityJson.Obj obj&&event.get("instance_id").equals(obj.get("instance_id"))),"original startup event instance still present");
                    if(decision instanceof FixtureStartupHandler.SelectDisplayedOption selected) {
                        var log=selected.proof().actualLog();byte[] bytes=context.archive().readArtifact(same,log,64*1024*1024);
                        StrictJson.require(log.sha256().equals(DriverJson.sha256(bytes)),"external handler actual log evidence changed");
                        var configured=context.frontend().startupCase().orElseThrow();configured.verifySources();
                        var window=DriverJson.object(read.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
                        configured.verifyOriginal(bytes,beforeData,window,selected);
                    }
                }
                continue;
            }
            ObjectNode row=StrictJson.object(input,kind.equals("owner")?Set.of("kind","event_allowed","semantic","independent_read","log"):Set.of("kind","event_allowed","semantic","independent_read","log","root"),Set.of("source_qualification"));
            StrictJson.require(kind.equals("owner")||kind.equals("business"),"unknown fixture qualification row kind");
            var evidence=OrdinaryCycleTransitions.semanticFromJson(row.get("semantic"));var data=semantic(context,same,evidence);
            var anchor=kind.equals("owner")?original.originalStart().ack().orElseThrow():archive.loadRead(ExactRef.fromJson(row.get("root"))).original();
            verifyFresh(context,same,evidence,row.get("independent_read"),anchor);
            ExactRef.optionalFromJson(row.get("source_qualification"));
            StrictJson.require(row.get("event_allowed").isBoolean(),"exact nullable-event policy boolean required");boolean allow=row.get("event_allowed").booleanValue();
            if(observedScenario)StrictJson.require(preserved.equals(data.get("active_event")),"scenario startup event changed before final qualification");
            var logs=logs(context,same,fixture,row.get("log"));
            if(kind.equals("owner")){previousOwner=currentOwner;currentOwner=reducer.observeOwner(data,logs,allow).owner().orElse(null);}
            else {
                StrictJson.require(allow==observedScenario,"whole-root cannot admit an unverified active startup event");
                StrictJson.require(fixture.policy().kind()!=FrontendFixturePolicy.Kind.SCENARIO||observedScenario,"scenario whole-root query preceded actual observe-only target event");
                var root=archive.loadRead(ExactRef.fromJson(row.get("root")));NativeRecordedEvidenceVerifier.requireRead(root,archive);
                reducer.observeBusiness(data,FixtureGameplayRoot.publication(root,fixture,data),logs,allow);finalSemantic=evidence;finalRoot=root;
            }
        }
        StrictJson.require(reducer.decision().fixtureTargetIdentityProven()&&original.finalSemantic().equals(finalSemantic)
                &&original.campaignRootRead().equals(finalRoot),"actual logs/owner/event/root/actor/pump reducer did not reproduce final fixture qualification");
    }
    private static FixtureQualificationLogs.Observation logs(RootRuntimeContext context,Session same,PreparedFixture fixture,JsonNode row)throws IOException {
        if(row.isNull())return new FixtureQualificationLogs.Observation(false,Optional.empty(),List.of());ExactRef ref=ExactRef.fromJson(row);
        byte[] raw=context.archive().readArtifact(same,ref,64*1024*1024);
        return FixtureQualificationLogs.fromOriginal(ref,raw,fixture.policy());
    }
    private static OpportunityJson.Obj semantic(RootRuntimeContext context,Session same,SemanticEvidence evidence)throws IOException {
        context.semanticVerifier().verify(same,new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(evidence.frame().machineId(),evidence.frame().game(),context.game().sessionId()),evidence);
        return DriverJson.object(context.archive().readArtifact(same,evidence.semantic(),ReadinessArchive.Role.SEMANTIC.maximumBytes()),ReadinessArchive.Role.SEMANTIC.maximumBytes());
    }
    private static void verifyFresh(RootRuntimeContext context,Session same,SemanticEvidence evidence,JsonNode input,NativeActionPort.AckReceived anchor)throws IOException {
        ObjectNode row=StrictJson.object(input,Set.of("snapshot_order","snapshot_observed_at","acknowledgement"));var dispatch=context.archive().withSession(same).load(ExactRef.fromJson(row.get("acknowledgement")));
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"fixture fresh sample omitted original ACK custody");var ack=(NativeActionPort.AckReceived)dispatch;
        byte[] packet=context.archive().readArtifact(same,evidence.originalNativePacket(),ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());var nativeData=NativeWire.decode(packet);
        StrictJson.require(nativeData instanceof NativeWire.Snapshot,"actual fixture native state packet missing");var snapshot=(NativeWire.Snapshot)nativeData;
        var actual=new NativeObservationPort.ObservedFrame(ack.custody().orElseThrow().session(),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,evidence.observedAt());
        var received=new NativeRequestChronology.Event(new java.math.BigInteger(new CrossJsDecimalUInt64(StrictJson.text(row.get("snapshot_order"))).decimal()),java.time.Instant.parse(StrictJson.text(row.get("snapshot_observed_at"))));
        NativeFreshSnapshotPort.verifyAfterOriginal(anchor,ack,actual,received);
    }
    private Session borrowed(){try{return context.writer().borrowedSession();}catch(IOException e){throw new java.io.UncheckedIOException(e);}}
}

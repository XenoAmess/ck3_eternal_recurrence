package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.advance.PreparedCleanupParentEvidence.Originals;
import org.xar.ck3.control.application.advance.PreparedCleanupParentEvidence.Loaded;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Independent six-child successor parent basis. Raw volatile post-ACK capture must already
 * be complete and the actual historical scope closed before any preserve call.
 * Live projection uses the identical SDK afterFrame object through the real Driver
 * producer; readback is historical DATA only and cannot mint a receiver/Guard/Ready. */
public final class PreparedCleanupSuccessorParentEvidence {
    public static final String SCHEMA="xar.life-prepared-cleanup-parent/v2";
    private static final int MAXIMUM=64*1024;
    private static final Set<String> FIELDS=Set.of("schema","parent_body_sha256","original_parent","preparation","capture",
            "children","starting","ending","progress_status");
    private PreparedCleanupSuccessorParentEvidence() { }
    /** No child execution/query or receiver capability construction. Actual Root supplies both genuine projected frames. */
    public static ExactRef preserve(ActionCommand parent,CompositeExecution currentExecution,List<ActionReceipt> children,
            ExactRef preparationReference,ExactRef captureReference,AdvanceObservationPort.Frame starting,
            AdvanceObservationPort.Frame ending,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var prepared=PreparedCleanupSuccessorEvidence.loadPrepared(preparationReference,archive,Objects.requireNonNull(frames));
        require(PreparedCleanupSuccessorEvidence.isSuccessor(prepared),"successor parent needs its strict six-child preparation");
        require(parent.equals(prepared.parentReceipt().command()),"prepared parent producer changed its immutable original command");
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("parent_body_sha256",ActionCodec.bodySha256(parent));
        row.set("original_parent",prepared.parentReference().toJson());row.set("preparation",preparationReference.toJson());row.set("capture",captureReference.toJson());
        var refs=row.putArray("children");for(var child:children)refs.add(archive.receiptReferenceOf(child).toJson());
        row.set("starting",toNode(LifeAdvanceEvidence.frame(LifeAdvanceEvidence.preserveFrame(starting,archive))));
        row.set("ending",toNode(LifeAdvanceEvidence.frame(LifeAdvanceEvidence.preserveFrame(ending,archive))));
        row.put("progress_status",AdvanceResult.progressStatus(AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS));
        byte[] bytes=StrictJson.canonical(row);require(bytes.length<=MAXIMUM,"prepared parent basis exceeds its unchanged bounded material cap");
        var reference=archive.preserveMaterial(new RawJson(bytes));var loaded=load(reference,archive,frames);
        require(loaded.originals().execution().equals(currentExecution)&&loaded.originals().children().equals(children)
                &&loaded.starting().equals(starting)&&loaded.ending().equals(ending),"prepared parent basis canonical original roundtrip differs");
        return reference;
    }
    /** Full physical raw and original material closure, without a fabricated FrameVerifier or live Native token. */
    public static Originals loadOriginals(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        Obj row=material(reference,archive);require(row.members().keySet().equals(FIELDS)&&new Text(SCHEMA).equals(row.get("schema")),
                "prepared parent basis schema or fields differ");
        var prepared=PreparedCleanupSuccessorEvidence.loadPreparedOriginals(exact(row.get("preparation")),archive);
        require(PreparedCleanupSuccessorEvidence.isSuccessor(prepared),"successor parent requires its distinct C5 NoEffect prefix");
        require(exact(row.get("original_parent")).equals(prepared.parentReference())
                &&new Text(ActionCodec.bodySha256(prepared.parentReceipt().command())).equals(row.get("parent_body_sha256"))
                &&new Text(AdvanceResult.progressStatus(AdvanceClock.ProgressStatus.WALL_TIMEOUT_WITH_DATE_PROGRESS)).equals(row.get("progress_status")),
                "prepared parent basis changed immutable parent or partial-progress policy");
        var captureRef=exact(row.get("capture"));var capture=PreparedCleanupEvidence.loadPostAckCapturedOriginals(captureRef,archive);
        Obj captureBody=material(captureRef,archive);var lateRef=exact(captureBody.get("late_binding"));
        var references=new ArrayList<ExactRef>();var children=new ArrayList<ActionReceipt>();
        for(var value:array(row.get("children"),"children")){var ref=exact(value);var child=archive.loadReceipt(ref);
            require(archive.receiptReferenceOf(child).equals(ref),"prepared parent child original reference differs");references.add(ref);children.add(child);}
        var previous=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();
        var execution=new CompositeExecution(previous.handlerId(),previous.startedAt(),previous.guard(),children.stream()
                .map(child->new CompositeExecution.Child(child.command().actionId(),child.bodySha256())).toList());
        var starting=LifeAdvanceEvidence.decodeFrame(object(row.get("starting"),"starting"),false);
        var ending=LifeAdvanceEvidence.decodeFrame(object(row.get("ending"),"ending"),false);
        reopen(starting,archive);reopen(ending,archive);
        var result=new Originals(reference,prepared,captureRef,lateRef,capture,children,references,execution,starting,ending);
        PreparedCleanupSuccessorParentProof.requirePrefix(result,archive);return result;
    }

    public static Loaded load(ExactRef reference,ActionPorts.OutcomeArchive archive,LifeAdvanceEvidence.BoundFrameVerifier frames) {
        Objects.requireNonNull(frames);var raw=loadOriginals(reference,archive);
        var prepared=PreparedCleanupSuccessorEvidence.loadPrepared(raw.prepared().reference(),archive,frames);
        var capture=PreparedCleanupEvidence.loadPostAckCaptured(raw.captureReference(),archive,frames);
        var originals=new Originals(raw.reference(),prepared,raw.captureReference(),raw.lateBindingReference(),capture,raw.children(),raw.childReferences(),
                raw.execution(),raw.starting(),raw.ending());var parent=prepared.parentReceipt().command();
        var starting=LifeAdvanceEvidence.restore(parent,raw.starting(),archive,frames);
        var ending=LifeAdvanceEvidence.restore(parent,raw.ending(),archive,frames);
        var result=new Loaded(originals,starting,ending);PreparedCleanupSuccessorParentProof.requireFrames(result,archive,frames);return result;
    }
    /** Strict parent consumer; does not create a planning READ, replace a guard or query Game. */
    public static LifeAdvanceEvidence.Recorded readRecorded(ActionReceipt actualParent,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var reference=referenceOf(actualParent);var loaded=load(reference,archive,frames);
        PreparedCleanupSuccessorParentProof.verifyReceipt(actualParent,loaded,archive,frames);
        return new LifeAdvanceEvidence.Recorded(loaded.originals().starting(),loaded.originals().ending(),Optional.empty());
    }
    /** Producer-side exact old observation algorithm, using complete actual six-child originals and projected ending frame. */
    public static ActionState.EffectObservation verifyEffect(ActionReceipt originalParent,List<ActionReceipt> actualChildren,
            AdvanceObservationPort.Frame completeEnding,ExactRef basisReference,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        var loaded=load(basisReference,archive,frames);
        require(originalParent.command().equals(loaded.originals().prepared().parentReceipt().command())
                &&originalParent.bodySha256().equals(loaded.originals().prepared().parentReceipt().bodySha256())
                &&actualChildren.equals(loaded.originals().children())&&completeEnding.equals(loaded.ending()),
                "prepared parent effect substituted its immutable command/actual children/strict ending frame");
        return PreparedCleanupSuccessorParentProof.expectedEffect(originalParent.command(),completeEnding,basisReference);
    }
    public static ExactRef referenceOf(ActionReceipt parent) {
        require(parent.state() instanceof ActionState.CompositeSettled,"prepared parent basis requires an actual composite terminal");
        var settlement=((ActionState.CompositeSettled)parent.state()).settlement();require(settlement instanceof ActionState.Applied,
                "prepared parent basis is not a fabricated NoEffect/zero-day control terminal");
        var effect=((ActionState.Applied)settlement).observation();require(effect.observerSchema().equals(AdvancePlan.OBSERVER)
                &&effect.supportingEvidence().size()==1,"prepared parent basis requires its one complete original Life material");return effect.supportingEvidence().getFirst();
    }
    public static boolean isSchema(Obj material){return new Text(SCHEMA).equals(material.get("schema"));}
    private static void reopen(LifeAdvanceEvidence.FrameRecord value,ActionPorts.OutcomeArchive archive) {
        byte[] nativeBytes=archive.loadNativeFrame(value.nativeFrame());exactBytes(value.nativeFrame(),nativeBytes);
        byte[] facts=archive.loadFullMaterial(value.driverFacts()).bytes();exactBytes(value.driverFacts(),facts);
        byte[] semantic=archive.loadFullMaterial(value.semantic()).bytes();exactBytes(value.semantic(),semantic);
        var object=DriverJson.object(semantic,RawJson.MAXIMUM_BYTES);require(exact(object.get("java_driver_facts_evidence")).equals(value.driverFacts()),
                "prepared parent frame substituted its exact original Driver facts manifest");
    }
    private static Obj material(ExactRef reference,ActionPorts.OutcomeArchive archive) {
        require(reference.bytes()>0&&reference.bytes()<=MAXIMUM,"prepared parent bounded material reference required");
        byte[] bytes=archive.loadMaterial(reference).bytes();exactBytes(reference,bytes);return DriverJson.object(bytes,MAXIMUM);
    }
    private static void exactBytes(ExactRef reference,byte[] bytes){require(reference.bytes()==bytes.length&&reference.sha256().equals(ActionCodec.sha256(bytes)),"prepared parent original material changed");}
    private static ExactRef exact(Value value){return ExactRef.fromJson(toNode(object(value,"exact reference")));}
}

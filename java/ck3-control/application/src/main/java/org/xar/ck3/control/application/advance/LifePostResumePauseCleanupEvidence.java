package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable original DATA for the separate post-resume-paused protocol; it never grants a current permit. */
public final class LifePostResumePauseCleanupEvidence {
    public static final String CURSOR_PREFIX="xar.life-post-resume-paused-cancel/v1: ";
    public static final String AUTHORIZATION_SCHEMA="xar.life-post-resume-pause-authorization/v1";
    public static final String TERMINAL_SCHEMA="xar.life-post-resume-pause-cleanup/v1";
    private static final Set<String> AUTHORIZATION_FIELDS=Set.of("schema","original_parent","original_children",
            "armed_read","before_cancel","issued_at_utc","deadline_utc");
    private LifePostResumePauseCleanupEvidence() { }

    public record Authorization(ExactRef reference,LifePostResumePauseCleanupProof.Original original,
            ExactRef parentReference,List<ExactRef> childReferences,ClockStatusRead.Observation armedStatus,
            AdvanceObservationPort.Frame beforeCancel,Instant issuedAt,Instant deadline) {
        public Authorization { childReferences=List.copyOf(childReferences); }
    }

    public static ExactRef preserveAuthorization(ActionReceipt originalParent,List<ActionReceipt> originalChildren,
            ClockStatusRead.Observation armedStatus,AdvanceObservationPort.Frame beforeCancel,
            Instant issuedAt,Instant ownDeadline,Instant actualNow,ActionPorts.OutcomeArchive archive) {
        var original=LifePostResumePauseCleanupProof.original(originalParent,originalChildren);
        LifePostResumePauseCleanupProof.requireFreshArmedPaused(original,armedStatus,beforeCancel,issuedAt,ownDeadline,actualNow);
        var body=StrictJson.object();body.put("schema",AUTHORIZATION_SCHEMA);
        body.set("original_parent",archive.receiptReferenceOf(originalParent).toJson());
        var children=body.putArray("original_children");
        for(var child:originalChildren)children.add(archive.receiptReferenceOf(child).toJson());
        body.set("armed_read",archive.preserveRead(armedStatus.receipt()).toJson());
        body.set("before_cancel",toNode(LifeAdvanceEvidence.frame(LifeAdvanceEvidence.preserveFrame(beforeCancel,archive))));
        body.put("issued_at_utc",issuedAt.toString());body.put("deadline_utc",ownDeadline.toString());
        return archive.preserveMaterial(new RawJson(StrictJson.canonical(body)));
    }

    public static Authorization loadAuthorization(ExactRef reference,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames) {
        return loadAuthorization(reference,archive,new LifeAdvanceRootReplay(frames));
    }

    public static Authorization loadAuthorization(ExactRef reference,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames) {
        byte[] bytes=archive.loadMaterial(reference).bytes();
        require(bytes.length==reference.bytes()&&ActionCodec.sha256(bytes).equals(reference.sha256()),
                "post-resume cleanup authorization changed its complete original bytes");
        Obj body=DriverJson.object(bytes,64*1024);
        require(body.members().keySet().equals(AUTHORIZATION_FIELDS)&&new Text(AUTHORIZATION_SCHEMA).equals(body.get("schema")),
                "post-resume cleanup authorization fields or schema differ");
        var parentReference=exact(body.get("original_parent"));var parent=archive.loadReceipt(parentReference);
        require(archive.receiptReferenceOf(parent).equals(parentReference),"cleanup original parent reference differs");
        var childReferences=new ArrayList<ExactRef>();var children=new ArrayList<ActionReceipt>();
        for(var value:array(body.get("original_children"),"original_children")) {
            var ref=exact(value);var child=archive.loadReceipt(ref);
            require(archive.receiptReferenceOf(child).equals(ref),"cleanup original child reference differs");
            childReferences.add(ref);children.add(child);
        }
        require(childReferences.size()>=3&&childReferences.size()<=5&&childReferences.stream().distinct().count()==childReferences.size()
                &&childReferences.stream().noneMatch(parentReference::equals),"cleanup original references are not distinct and finite");
        var original=LifePostResumePauseCleanupProof.original(parent,children);
        var armedReference=exact(body.get("armed_read"));var read=archive.loadRead(armedReference);
        require(archive.readReferenceOf(read).equals(armedReference),"cleanup original armed Status reference differs");
        var armedStatus=new ClockStatusRead.Observation(ClockStatusRead.decode(read.original()),read,archive.referenceOf(read.original()));
        var frame=LifeAdvanceEvidence.decodeFrame(object(body.get("before_cancel"),"before_cancel"),false);
        var beforeCancel=LifeAdvanceEvidence.restore(parent.command(),frame,archive,frames);
        Instant issuedAt=Instant.parse(text(body.get("issued_at_utc"),"issued_at_utc"));
        Instant deadline=Instant.parse(text(body.get("deadline_utc"),"deadline_utc"));
        // Historical replay uses the actual receipt/frame event; the live issuer separately checks its real clock.
        LifePostResumePauseCleanupProof.requireFreshArmedPaused(original,armedStatus,beforeCancel,issuedAt,deadline,beforeCancel.observedAt());
        return new Authorization(reference,original,parentReference,childReferences,armedStatus,beforeCancel,issuedAt,deadline);
    }

    public static ExactRef preserveTerminal(ExactRef authorization,ExactRef completeLifeBasis,ActionPorts.OutcomeArchive archive) {
        require(authorization.bytes()>0&&completeLifeBasis.bytes()>0&&!authorization.equals(completeLifeBasis),
                "cleanup terminal requires its distinct actual authorization and complete Life basis");
        var body=StrictJson.object();body.put("schema",TERMINAL_SCHEMA);
        body.set("authorization",authorization.toJson());body.set("basis",completeLifeBasis.toJson());
        return archive.preserveMaterial(new RawJson(StrictJson.canonical(body)));
    }

    public static ExactRef authorizationFromParent(ActionReceipt successor,ActionPorts.OutcomeArchive archive) {
        require(successor.state() instanceof ActionState.CompositeUnknown unknown&&unknown.reason().startsWith(CURSOR_PREFIX),
                "cleanup authorization requires its explicitly marked current UNKNOWN successor");
        var evidence=((ActionState.CompositeUnknown)successor.state()).evidence();
        require(!evidence.isEmpty(),"cleanup successor has no durable source authorization original");
        // The new continuation/source appends this exact reference last, preserving every older evidence entry.
        // Older entries include binary Native originals; they are neither scanned nor treated as JSON role candidates.
        var reference=evidence.getLast();require(reference.bytes()>0&&reference.bytes()<=64*1024,
                "cleanup authorization original must be finite and nonempty");
        byte[] bytes=archive.loadMaterial(reference).bytes();
        require(bytes.length==reference.bytes()&&ActionCodec.sha256(bytes).equals(reference.sha256()),
                "cleanup successor authorization original changed");
        Obj body=DriverJson.object(bytes,64*1024);
        require(body.members().keySet().equals(AUTHORIZATION_FIELDS)&&new Text(AUTHORIZATION_SCHEMA).equals(body.get("schema")),
                "cleanup successor lacks its exact source authorization schema");
        return reference;
    }

    static ExactRef exact(Value value) { return ExactRef.fromJson(toNode(object(value,"exact reference"))); }
}

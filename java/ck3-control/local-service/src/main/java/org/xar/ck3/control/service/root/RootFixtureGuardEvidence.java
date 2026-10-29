package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** One codec for original fixture-derived guard ancestry; historical verification grants no live scope. */
final class RootFixtureGuardEvidence {
    static final String SCHEMA="xar.java.fixture-derived-guard/v1";
    private static final Set<String> FIELDS=Set.of("schema","parent_action_id","parent_body_sha256","handler_id",
            "parent_receipt","start_receipt","child_action_id","child_body_sha256","ordinal","fixture");
    private RootFixtureGuardEvidence(){}
    static ExactRef preserve(Session same,ActionChildPlanningScope.FixtureCursor cursor,ActionCommand parent,
            ActionCommand child,String handler,FixturePlan plan,ActionPorts.OutcomeArchive originals)throws IOException {
        var start=cursor.recordedChildren().stream().filter(row->row.command().operation().equals(plan.kind().startOperation())).findFirst().orElseThrow();
        var row=StrictJson.object().put("schema",SCHEMA).put("parent_action_id",parent.actionId())
                .put("parent_body_sha256",ActionCodec.bodySha256(parent)).put("handler_id",handler)
                .put("child_action_id",child.actionId()).put("child_body_sha256",ActionCodec.bodySha256(child))
                .put("ordinal",cursor.execution().children().size());
        row.set("parent_receipt",originals.receiptReferenceOf(cursor.parent()).toJson());
        row.set("start_receipt",originals.receiptReferenceOf(start).toJson());row.set("fixture",plan.encode());
        ExactRef proof=originals.preserveMaterial(new RawJson(org.xar.ck3.control.continuity.ContinuityJson.canonical(row)));
        same.verifyPin(same.capturePin(proof,WriterContracts.MAX_PIN_BYTES));return proof;
    }
    static boolean matches(GuardEvidence guard,ActionPorts.OutcomeArchive originals) {
        if(guard.supportingEvidence().isEmpty())return false;
        try {var row=DriverJson.toNode(DriverJson.object(originals.loadMaterial(guard.supportingEvidence().getLast()).bytes(),DriverJson.MAX_NATIVE_BYTES));
            return row.isObject()&&row.has("schema")&&SCHEMA.equals(StrictJson.text(row.get("schema")));
        } catch(RuntimeException unavailable){return false;}
    }
    static void verify(WriterContracts.Head head,ActionReceipt child,GuardEvidence guard,ActionPorts.OutcomeArchive originals,Session same)throws IOException {
        StrictJson.require(!guard.supportingEvidence().isEmpty(),"fixture derived guard has no original ancestry");
        ExactRef proof=guard.supportingEvidence().getLast();same.verifyPin(same.capturePin(proof,WriterContracts.MAX_PIN_BYTES));
        var row=StrictJson.object(DriverJson.toNode(DriverJson.object(originals.loadMaterial(proof).bytes(),DriverJson.MAX_NATIVE_BYTES)),FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact fixture derived guard schema required");
        String parentId=StrictJson.text(row.get("parent_action_id"));var parent=ContinuityActionJournal.lookup(head.state(),parentId,originals).orElseThrow();
        var originalParent=originals.loadReceipt(ExactRef.fromJson(row.get("parent_receipt")));
        ContinuityActionJournal.requireHistoricalReceipt(head.state(),originalParent,originals);
        var plan=FixturePlan.decode(row.get("fixture"));
        StrictJson.require(FixturePlan.requireParent(parent.command()).equals(plan)
                &&parent.bodySha256().equals(StrictJson.text(row.get("parent_body_sha256")))
                &&originalParent.bodySha256().equals(parent.bodySha256())
                &&child.command().actionId().equals(StrictJson.text(row.get("child_action_id")))
                &&child.bodySha256().equals(StrictJson.text(row.get("child_body_sha256")))
                &&child.command().source().equals(parent.command().source())
                &&child.command().sessionId().equals(parent.command().sessionId()),"fixture derived original parent/child/source changed");
        CompositeExecution execution;
        if(parent.state() instanceof ActionState.CompositeRunning value)execution=value.execution();
        else if(parent.state() instanceof ActionState.CompositeUnknown value)execution=value.execution();
        else if(parent.state() instanceof ActionState.CompositeSettled value)execution=value.execution();
        else throw new IllegalArgumentException("fixture ancestry has no canonical composite execution");
        int ordinal=Math.toIntExact(StrictJson.integer(row.get("ordinal"),1,4096));
        StrictJson.require(execution.handlerId().equals(StrictJson.text(row.get("handler_id")))&&ordinal<=execution.children().size(),
                "fixture derived original handler or child ordinal changed");
        var reserved=execution.children().get(ordinal-1);
        StrictJson.require(reserved.actionId().equals(child.command().actionId())&&reserved.bodySha256().equals(child.bodySha256())
                &&child.command().actionId().equals(ActionIds.child(parentId,ordinal,child.command().operation())),
                "fixture derived guard is not this canonical reserved child");
        var start=originals.loadReceipt(ExactRef.fromJson(row.get("start_receipt")));
        var canonicalStart=ContinuityActionJournal.lookup(head.state(),start.command().actionId(),originals).orElseThrow();
        StrictJson.require(start.equals(canonicalStart)&&start.state() instanceof ActionState.Settled settled
                &&settled.settlement() instanceof ActionState.FixtureStarted,"fixture lost its actual canonical physically settled Start");
        var first=((ActionState.FixtureStarted)((ActionState.Settled)start.state()).settlement()).observation();
        StrictJson.require(first.fixture().equals(plan)&&start.command().operation().equals(plan.kind().startOperation())
                &&guard.source().equals(child.command().source())&&guard.sessionId().equals(child.command().sessionId())
                &&guard.operation().equals(child.command().operation())&&child.command().origin().acceptsGuard(guard.origin()),
                "fixture derived guard changed its first map, original operation or origin");
        for(var ref:List.of(plan.policySource(),plan.claim(),plan.producerSource(),child.command().source().sourceRef()))
            same.verifyPin(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
    }
}


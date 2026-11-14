package org.xar.ck3.control.application.advance;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.StrictJson;

/** Full archive role for the new five-child cursor. The cheap header predicate
 * only selects a read-only route; it never issues a token, frame or permit. */
public final class PreparedCleanupCursor {
    private PreparedCleanupCursor(){}
    public static boolean marked(ActionReceipt receipt){
        return receipt.state() instanceof ActionState.CompositeUnknown unknown
                &&(unknown.reason().startsWith(PreparedCleanupEvidence.CURSOR_PREFIX)||unknown.reason().startsWith(PreparedCleanupSuccessorEvidence.CURSOR_PREFIX));
    }
    public static PreparedCleanupEvidence.Prepared load(ActionReceipt parent,ActionPorts.OutcomeArchive archive,
            LifeAdvanceEvidence.BoundFrameVerifier frames){
        StrictJson.require(marked(parent),"prepared cleanup requires its explicit independent cursor marker");
        var unknown=(ActionState.CompositeUnknown)parent.state();
        StrictJson.require(!unknown.evidence().isEmpty(),"prepared cursor has no durable preparation reference");
        var prepared=PreparedCleanupEvidence.loadPrepared(unknown.evidence().getLast(),archive,frames);
        if(PreparedCleanupSuccessorEvidence.isSuccessor(prepared)){requireSuccessor(parent,prepared);return prepared;}
        StrictJson.require(unknown.reason().startsWith(PreparedCleanupEvidence.CURSOR_PREFIX),"original prepared cursor may not borrow a successor marker");
        var before=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();var current=unknown.execution();
        StrictJson.require(parent.command().equals(prepared.parentReceipt().command())&&parent.bodySha256().equals(prepared.parentReceipt().bodySha256())
                &&current.handlerId().equals(before.handlerId())&&current.startedAt().equals(before.startedAt())&&current.guard().equals(before.guard())
                &&current.children().size()==5&&current.children().subList(0,4).equals(before.children())
                &&current.children().getLast().equals(new CompositeExecution.Child(prepared.command().actionId(),ActionCodec.bodySha256(prepared.command()))),
                "prepared cursor changed its immutable parent/four originals or distinct fifth command");
        var originalEvidence=new java.util.ArrayList<>(((ActionState.CompositeUnknown)prepared.parentReceipt().state()).evidence());
        originalEvidence.removeIf(prepared.reference()::equals);originalEvidence.add(prepared.reference());
        StrictJson.require(unknown.evidence().equals(originalEvidence),"prepared cursor erased/reordered its original authorization or preparation");
        return prepared;
    }
    private static void requireSuccessor(ActionReceipt parent,PreparedCleanupEvidence.Prepared prepared){
        var unknown=(ActionState.CompositeUnknown)parent.state();var current=unknown.execution();
        var before=((ActionState.CompositeUnknown)prepared.parentReceipt().state()).execution();
        StrictJson.require(unknown.reason().startsWith(PreparedCleanupSuccessorEvidence.CURSOR_PREFIX)
                &&parent.command().equals(prepared.parentReceipt().command())&&parent.bodySha256().equals(prepared.parentReceipt().bodySha256())
                &&current.handlerId().equals(before.handlerId())&&current.startedAt().equals(before.startedAt())&&current.guard().equals(before.guard())
                &&current.children().size()==6&&before.children().size()==5&&current.children().subList(0,5).equals(before.children())
                &&current.children().getLast().equals(new CompositeExecution.Child(prepared.command().actionId(),ActionCodec.bodySha256(prepared.command()))),
                "prepared successor cursor changed the complete five-child prefix or distinct sixth command");
        var evidence=new java.util.ArrayList<>(((ActionState.CompositeUnknown)prepared.parentReceipt().state()).evidence());
        evidence.removeIf(prepared.reference()::equals);evidence.add(prepared.reference());
        StrictJson.require(unknown.evidence().equals(evidence),"prepared successor cursor erased/reordered original authorization/preparation evidence");
    }
    public static boolean currentChildren(PreparedCleanupEvidence.Prepared prepared,List<ActionReceipt> actions){
        for(var expected:prepared.children()){
            var found=actions.stream().filter(value->value.command().actionId().equals(expected.command().actionId())).toList();
            if(found.size()!=1||!found.getFirst().equals(expected))return false;
        }
        return true;
    }
}

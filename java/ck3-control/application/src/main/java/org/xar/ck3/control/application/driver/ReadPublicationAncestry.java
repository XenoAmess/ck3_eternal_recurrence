package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Only actual never-written action descendants may intervene before publishing an already observed pure read. */
final class ReadPublicationAncestry {
    private ReadPublicationAncestry() { }
    static WriterContracts.Head require(ContinuityStorePort.Session same,WriterContracts.Head original,
            ActionJournal.Snapshot baseline,ActionJournal.Snapshot current,ActionPorts.OutcomeArchive archive) throws IOException {
        WriterContracts.Head actual=same.head();
        if(actual.digest().equals(original.digest()))return actual;
        var old=same.requireHistoricalState(original.state().sequence(),original.digest());
        StrictJson.require(ContinuityJson.same(old.toJson(),original.state().toJson()),"original read head is not this exact canonical ancestor");
        var before=old.toJson();var after=actual.state().toJson();var fields=new LinkedHashSet<String>();
        before.fieldNames().forEachRemaining(fields::add);after.fieldNames().forEachRemaining(fields::add);
        for(String field:fields)if(!List.of("sequence","last_event_identity",WriterContracts.ACTION_LIFECYCLE_FIELD).contains(field))
            StrictJson.require(Objects.equals(before.get(field),after.get(field)),"read descendant changed unrelated canonical field: "+field);
        Optional<ExactRef> stop=reference(before.get(WriterContracts.ACTION_LIFECYCLE_FIELD));
        Optional<ExactRef> cursor=reference(after.get(WriterContracts.ACTION_LIFECYCLE_FIELD));
        List<ActionReceipt> additions=new ArrayList<>();var seen=new HashSet<ExactRef>();
        while(!cursor.equals(stop)) {
            StrictJson.require(cursor.isPresent()&&seen.add(cursor.orElseThrow())&&additions.size()<512,"finite exact action ancestor chain required");
            ActionRecord record=archive.loadRecord(cursor.orElseThrow());ActionReceipt receipt=record.receipt();
            StrictJson.require(receipt.sequence()>old.sequence()&&receipt.sequence()<=actual.state().sequence(),"intervening action escaped actual canonical sequence");
            StrictJson.require(receipt.bodySha256().equals(ActionCodec.bodySha256(receipt.command())),"intervening canonical action body digest differs");
            StrictJson.require(receipt.state() instanceof ActionState.IntentDurable||receipt.state() instanceof ActionState.CompositeRunning
                    ||receipt.state() instanceof ActionState.CompositeUnknown||zero(receipt),"intervening action may have written Native; read publication cannot rebase");
            additions.add(receipt);cursor=record.previous();
        }
        StrictJson.require(additions.size()==Math.subtractExact(actual.state().sequence(),old.sequence())
                &&current.ledgerSequence()==actual.state().sequence()&&current.headSha256().equals(actual.digest()),"unrelated canonical event intervened before read publication");
        Map<String,ActionReceipt> oldActions=new HashMap<>(),latest=new HashMap<>();
        baseline.actions().forEach(row -> oldActions.put(row.command().actionId(),row));
        current.actions().forEach(row -> latest.put(row.command().actionId(),row));
        var changed=new HashSet<String>();additions.forEach(row -> changed.add(row.command().actionId()));
        for(String id:changed) {
            ActionReceipt row=latest.get(id);StrictJson.require(row!=null,"actual changed action absent from canonical snapshot");
            for(ActionReceipt intermediate:additions)if(intermediate.command().actionId().equals(id))
                StrictJson.require(intermediate.bodySha256().equals(row.bodySha256()),"intervening action body changed");
            if(zero(row))continue;
            StrictJson.require(row.state() instanceof ActionState.CompositeUnknown,"intervening unresolved action has no actual zero-write settlement");
            var execution=((ActionState.CompositeUnknown)row.state()).execution();
            StrictJson.require(!execution.children().isEmpty(),"intervening composite has no actual registered zero-write child");
            for(var child:execution.children()) {
                ActionReceipt actualChild=latest.get(child.actionId());
                StrictJson.require(actualChild!=null&&actualChild.bodySha256().equals(child.bodySha256()),"intervening composite child differs from canonical body");
                if(changed.contains(child.actionId()))StrictJson.require(zero(actualChild),"intervening composite child may have written Native");
                else StrictJson.require(oldActions.containsKey(child.actionId())&&oldActions.get(child.actionId()).equals(actualChild)
                        &&actualChild.settled(),"old composite child changed after original read");
            }
        }
        return actual;
    }
    private static boolean zero(ActionReceipt actual) {
        if(!(actual.state() instanceof ActionState.RejectedBeforeDispatch rejected))return false;
        var proof=rejected.dispatch().proof();
        return actual.outcome()==ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH
                &&proof.stage()==NativeActionPort.ZeroDispatchStage.BEFORE_WRITE&&proof.requestBytesWritten()==0
                &&rejected.attempt().requestId().equals(rejected.dispatch().requestId())
                &&rejected.attempt().requestId().equals(RequestIds.forCommand(actual.command()))
                &&NativeStepDiscriminator.matchesRequest(actual.command().operation(),ExecutableStepBindings.Kind.ACTION,rejected.attempt().preparedRequest());
    }
    private static Optional<ExactRef> reference(com.fasterxml.jackson.databind.JsonNode value) {
        if(value==null)return Optional.empty();StrictJson.require(!value.isNull(),"actual action head cannot be null");
        return Optional.of(ExactRef.fromJson(value));
    }
}

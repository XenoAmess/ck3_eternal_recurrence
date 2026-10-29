package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Integration assertions requiring the real installed Root provider. No fixture, Known, ACK or private publication is manufactured. */
public final class RootOperatorPublicationAssertions {
    private RootOperatorPublicationAssertions(){ }
    private record Captured(DriverSnapshotFacts.Known known,List<ActionReceipt> actions,
            List<org.xar.ck3.control.continuity.EpisodeWindow.OperatorRebind> operatorLineage){ }
    /** Execute only with the actual qualified .6 input and exact installed same-Core publisher; unsupported inputs must fail. */
    public static RawJson requireActualSwitch(RootRuntimeContext context,RootSetPlayedCharacterRuntime.Installed installed,
            OperatorPlayerSwitch.Request request,Instant deadline,DriverActionHistoryPublisher actualPublisher) throws IOException,InterruptedException {
        context.requireCurrent(deadline);var root=context.core().sessionAccess().current();
        require(root==context.actions()&&root.ownedBy(context.core())&&root.driver()==context.adopted(),
                "operator assertions require the actual current same-Core Root and adopted Driver");
        actualPublisher.requireOwner(root.driver().authority(),context.core().journal(),context.archive());
        Captured before=capture(context);Set<String> oldIds=before.actions().stream().map(row->row.command().actionId()).collect(java.util.stream.Collectors.toSet());
        RawJson actualPublic=installed.runtime().execute(root,request,deadline);
        Captured after=capture(context);
        var fresh=after.actions().stream().filter(row->!oldIds.contains(row.command().actionId())).toList();
        require(fresh.size()==1,"one explicit operator invocation must retain one actual canonical action, without a replacement coordinator/child");
        var actual=fresh.getFirst();require(actual.state() instanceof ActionState.Settled,"actual operator action did not settle");
        var settled=(ActionState.Settled)actual.state();require(settled.settlement() instanceof ActionState.OperatorRebound,"actual operator identity settlement missing");
        var completion=((ActionState.OperatorRebound)settled.settlement()).observation();
        require(completion.request().equals(request),"actual operator completion changed the original public request");
        boolean changed=!before.known().driver().session().actorId().equals(java.math.BigInteger.valueOf(request.characterId()));
        require(completion.rebindPerformed()==changed&&after.known().stamp().driverVersion()==Math.addExact(before.known().stamp().driverVersion(),changed?1:0),
                "operator introduced an extra history version or lost its one actual identity CAS");
        require(after.operatorLineage().size()==Math.addExact(before.operatorLineage().size(),changed?1:0),"operator created an extra/missing identity Window event");
        require(after.operatorLineage().subList(0,before.operatorLineage().size()).equals(before.operatorLineage()),"operator rewrote its original identity lineage");
        var expected=DriverOperatorRebindProjection.propose(before.known(),request);
        require(Arrays.equals(expected.driver().encode(),after.known().driver().encode())&&expected.auxiliary().equals(after.known().auxiliary()),
                "actual operator changed another complete Driver/auxiliary slot");
        require(after.known().stamp().episodeEpoch()==before.known().stamp().episodeEpoch()
                &&after.known().stamp().game().equals(before.known().stamp().game())
                &&after.known().stamp().episodeRunId().equals(before.known().stamp().episodeRunId()),"operator changed Game/run/epoch");
        require(after.known().driver().session().actorId().equals(java.math.BigInteger.valueOf(request.characterId())),"actual Driver retained the old actor");
        require(after.known().actionRows().equals(before.known().actionRows()),"an interface without the original recorder invented an ActionRow");
        require(after.known().driver().commandHistory().size()==before.known().driver().commandHistory().size(),"operator invented Python history");
        for(int i=0;i<before.known().driver().commandHistory().size();i++)require(Arrays.equals(before.known().driver().commandHistory().get(i).originalRow().json(),
                after.known().driver().commandHistory().get(i).originalRow().json()),"operator rewrote original historical result bytes");
        context.writer().locked(same->{
            String head=same.head().digest();var originals=context.archive().withSession(same);
            DriverActionHistoryCodec.verifyOperator(same,actual,originals);
            DriverOperatorRebindOriginals.requireCoveredBy(same,actual,originals,after.known().driver(),after.known().stamp().driverVersion(),
                    after.known().stamp().episodeEpoch(),after.known().stamp().game(),context.adopted().session().sessionId());
            var disposition=actualPublisher.completed(same,actual);
            require(disposition instanceof DriverActionHistoryPublisher.Unchanged unchanged
                    &&unchanged.reason()==DriverActionHistoryPublisher.Reason.OPERATOR_CANONICAL_RECEIPT_VERIFIED,
                    "operator history completion used the ordinary publication path");
            require(same.head().digest().equals(head),"operator readonly completion appended another canonical event");
            root.driver().authority().withFrozenFacts(same,frozen->{
                require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual post-operator full Driver missing");
                var current=(DriverSnapshotFacts.Known)frozen.state();require(current.stamp().equals(after.known().stamp())
                        &&Arrays.equals(current.driver().encode(),after.known().driver().encode())&&current.auxiliary().equals(after.known().auxiliary())
                        &&current.actionRows().equals(after.known().actionRows()),"readonly operator verification changed actual Driver state");return null;
            });
            var publicRow=DriverJson.object(actualPublic.bytes(),DriverJson.MAX_NATIVE_BYTES);
            OperatorPlayerSwitch.requireRebound(request,completion.episodeRunId(),DriverJson.toNode(DriverJson.object(
                    originals.loadFullMaterial(completion.originals().reboundNative()).bytes(),DriverJson.MAX_NATIVE_BYTES)));
            require(new OpportunityJson.Bool(changed).equals(publicRow.get("episode_rebind_performed")),"public result lost the original rebind distinction");
            require(Arrays.equals(OperatorPlayerSwitch.decodeCompletion(completion.encode()).encode(),completion.encode()),"typed operator receipt completion changed in serde");
            require(same.head().digest().equals(head),"operator serialization/archive replay changed the writer");return null;
        });
        return actualPublic;
    }
    private static Captured capture(RootRuntimeContext context) throws IOException {
        return context.writer().locked(same->rootCapture(context,same));
    }
    private static Captured rootCapture(RootRuntimeContext context,org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same) throws IOException {
        return context.adopted().authority().withFrozenFacts(same,frozen->{
            require(frozen.state() instanceof DriverSnapshotFacts.Known,"actual original Root Driver unavailable");
            return new Captured((DriverSnapshotFacts.Known)frozen.state(),frozen.actions().actions(),
                    org.xar.ck3.control.continuity.EpisodeWindow.operatorLineage(same.head().state()));
        });
    }
    private static void require(boolean condition,String message){if(!condition)throw new AssertionError(message);}
}

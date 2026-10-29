package org.xar.ck3.control.application.action;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Observed fixture qualification DATA before Entry commits. It cannot settle its parent by itself. */
public record FixtureBusinessEvidence(String parentActionId,String parentBodySha256,FixturePlan fixture,
        ActionReceipt originalStart,SemanticEvidence finalSemantic,PlanningReadReceipt campaignRootRead,
        ExactRef qualification,List<ExactRef> supportingEvidence) {
    public static final String SCHEMA="xar.java.fixture-business-evidence/v1";
    public FixtureBusinessEvidence {
        StrictJson.text(parentActionId);StrictJson.require(parentBodySha256!=null&&parentBodySha256.matches("[0-9a-f]{64}"),"fixture exact parent body required");
        Objects.requireNonNull(fixture);Objects.requireNonNull(originalStart);Objects.requireNonNull(finalSemantic);
        Objects.requireNonNull(campaignRootRead);Objects.requireNonNull(qualification);supportingEvidence=List.copyOf(supportingEvidence);
        StrictJson.require(qualification.bytes()>0&&supportingEvidence.size()<=64&&supportingEvidence.stream().distinct().count()==supportingEvidence.size()
                &&supportingEvidence.stream().allMatch(ref->ref.bytes()>0),"finite original fixture qualification closure required");
        StrictJson.require(originalStart.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.FixtureStarted,
                "fixture business evidence requires its canonical physically settled original Start child");
        var started=(ActionState.FixtureStarted)((ActionState.Settled)originalStart.state()).settlement();var first=started.observation();
        StrictJson.require(((ActionState.Settled)originalStart.state()).dispatch() instanceof NativeActionPort.AckReceived ack&&ack.nativeOk(),
                "fixture business evidence requires its retained successful Start ACK");
        StrictJson.require(first.fixture().equals(fixture)&&originalStart.command().source().equals(campaignRootRead.request().source())
                &&originalStart.command().sessionId().equals(campaignRootRead.request().sessionId())
                &&campaignRootRead.request().origin() instanceof CommandOrigin.Gameplay
                &&campaignRootRead.request().before().equals(finalSemantic.frame())
                &&campaignRootRead.before().binding().origin() instanceof CommandOrigin.Gameplay
                &&campaignRootRead.after().binding().origin() instanceof CommandOrigin.Gameplay
                &&campaignRootRead.before().binding().observed().equals(finalSemantic.frame())
                &&campaignRootRead.after().binding().observed().equals(finalSemantic.frame())
                &&campaignRootRead.original().nativeOk()&&campaignRootRead.request().operation().value().equals("query-campaign-root-context-v1")
                &&first.gameplaySession().machineId().equals(finalSemantic.frame().machineId())&&first.gameplaySession().game().equals(finalSemantic.frame().game())
                &&!finalSemantic.observedAt().isBefore(first.firstMap().observedAt()),"fixture final root/SEM crossed its actual first map or source/session");
        NativeRequestChronology.requireSampledAfter(campaignRootRead,((ActionState.Settled)originalStart.state()).attempt(),
                (NativeActionPort.AckReceived)((ActionState.Settled)originalStart.state()).dispatch());
    }
    public void validateParent(ActionCommand parent){
        StrictJson.require(parent.actionId().equals(parentActionId)&&ActionCodec.bodySha256(parent).equals(parentBodySha256)
                &&FixturePlan.requireParent(parent).equals(fixture)&&originalStart.command().source().equals(parent.source())
                &&originalStart.command().sessionId().equals(parent.sessionId())
                &&originalStart.command().origin().requireFrontend().sameSession(parent.origin().requireFrontend()),
                "fixture qualification changed its exact original parent/source/branch");
    }
    public void validateChildren(CompositeExecution execution,List<ActionReceipt> canonical){
        long starts=canonical.stream().filter(value->value.command().operation().equals(fixture.kind().startOperation())).count();
        StrictJson.require(starts==1&&canonical.contains(originalStart)&&canonical.size()==execution.children().size(),
                "fixture business proof substituted or omitted its unique canonical Start/child history");
    }
    public List<ExactRef> references(){
        var refs=new ArrayList<>(finalSemantic.references());refs.add(qualification);refs.addAll(supportingEvidence);
        refs.addAll(List.of(fixture.policySource(),fixture.claim(),fixture.producerSource()));return refs.stream().distinct().toList();
    }
}

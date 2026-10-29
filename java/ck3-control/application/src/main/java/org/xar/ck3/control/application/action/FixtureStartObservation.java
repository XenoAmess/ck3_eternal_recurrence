package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Real first-map and independent paused owner-pump originals. No campaign-root or gameplay entry is implied. */
public record FixtureStartObservation(FixturePlan fixture,FrontendIdentity before,G2Source source,
        SessionIdentity gameplaySession,BigInteger connectionGeneration,SemanticEvidence firstMap,String fullBindingSha256,
        ExactRef originalHello,ExactRef firstHeartbeat,ExactRef lastHeartbeat,java.util.Optional<ExactRef> sourceQualification,
        NativeActionPort.AckReceived independentRead,NativeRequestChronology.Event snapshotReceived) {
    public static final String SCHEMA="xar.java.fixture-first-map-observation/v1";
    public FixtureStartObservation {
        Objects.requireNonNull(fixture);Objects.requireNonNull(before);Objects.requireNonNull(source);Objects.requireNonNull(gameplaySession);
        FrontendFrame.positive(connectionGeneration);Objects.requireNonNull(firstMap);Objects.requireNonNull(originalHello);
        Objects.requireNonNull(firstHeartbeat);Objects.requireNonNull(lastHeartbeat);Objects.requireNonNull(sourceQualification);
        Objects.requireNonNull(independentRead);Objects.requireNonNull(snapshotReceived);
        var readCustody=independentRead.custody().orElseThrow(()->new IllegalArgumentException("fixture independent READ has no actual custody"));readCustody.verify(independentRead);
        StrictJson.require(independentRead.nativeOk()&&snapshotReceived.order().compareTo(readCustody.writeCompleted().order())>0
                &&snapshotReceived.order().compareTo(readCustody.responseReceived().order())<0
                &&snapshotReceived.observedAt().equals(firstMap.observedAt()),"fixture first-map READ snapshot is outside its actual write/ACK interval");
        StrictJson.require(fullBindingSha256!=null&&fullBindingSha256.matches("[0-9a-f]{64}"),"actual first-map full Native/Driver binding required");
        StrictJson.require(before.machineId().equals(source.machineId())&&before.machineId().equals(gameplaySession.machineId())
                &&before.game().equals(gameplaySession.game())&&before.frontendSessionId().equals(gameplaySession.sessionId())
                &&before.connectionGeneration().equals(connectionGeneration)&&before.machineId().equals(firstMap.frame().machineId())
                &&before.game().equals(firstMap.frame().game()),"fixture first map crossed its original held Game/source/session/connection");
        StrictJson.require(!firstHeartbeat.equals(lastHeartbeat)&&java.util.stream.Stream.concat(List.of(originalHello,firstHeartbeat,lastHeartbeat).stream(),sourceQualification.stream()).toList()
                .stream().allMatch(ref->ref.bytes()>0),"actual independent first/last paused owner heartbeats and nonempty supplied metadata required");
    }
    public FixtureStartObservation(FixturePlan fixture,FrontendIdentity before,G2Source source,
            SessionIdentity gameplaySession,BigInteger connectionGeneration,SemanticEvidence firstMap,String fullBindingSha256,
            ExactRef originalHello,ExactRef firstHeartbeat,ExactRef lastHeartbeat,ExactRef sourceQualification,
            NativeActionPort.AckReceived independentRead,NativeRequestChronology.Event snapshotReceived) {
        this(fixture,before,source,gameplaySession,connectionGeneration,firstMap,fullBindingSha256,originalHello,firstHeartbeat,
                lastHeartbeat,java.util.Optional.of(sourceQualification),independentRead,snapshotReceived);
    }
    public static FixtureStartObservation from(FixturePlan fixture,FrontendIdentity before,Complete actual,SemanticEvidence semantic,
            ExactRef hello,ExactRef firstHeartbeat,ExactRef lastHeartbeat,ExactRef sourceQualification,
            NativeActionPort.AckReceived independentRead,NativeRequestChronology.Event snapshotReceived){
        return from(fixture,before,actual,semantic,hello,firstHeartbeat,lastHeartbeat,java.util.Optional.of(sourceQualification),independentRead,snapshotReceived);
    }
    public static FixtureStartObservation from(FixturePlan fixture,FrontendIdentity before,Complete actual,SemanticEvidence semantic,
            ExactRef hello,ExactRef firstHeartbeat,ExactRef lastHeartbeat,java.util.Optional<ExactRef> sourceQualification,
            NativeActionPort.AckReceived independentRead,NativeRequestChronology.Event snapshotReceived){
        StrictJson.require(actual.identity().equals(semantic.frame())&&actual.originalEvidence().equals(semantic.originalNativePacket())
                &&actual.observedAt().equals(semantic.observedAt()),"fixture first-map semantic differs from its actual complete Driver frame");
        return new FixtureStartObservation(fixture,before,actual.source(),new SessionIdentity(actual.identity().machineId(),actual.identity().game(),actual.sessionId()),
                actual.connectionGeneration(),semantic,actual.fullBindingSha256(),hello,firstHeartbeat,lastHeartbeat,sourceQualification,independentRead,snapshotReceived);
    }
    public List<ExactRef> references(){
        var refs=new ArrayList<>(firstMap.references());refs.addAll(List.of(originalHello,firstHeartbeat,lastHeartbeat,
                fixture.policySource(),fixture.claim(),fixture.producerSource()));sourceQualification.ifPresent(refs::add);return refs.stream().distinct().toList();
    }
    public void validate(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        fixture.requireStart(command);var expected=command.expectation().requireFrontend();
        StrictJson.require(before.equals(command.origin().requireFrontend())&&before.sameSession(attempt.guard().origin().requireFrontend())
                &&source.equals(command.source())&&source.equals(expected.source())&&gameplaySession.sessionId().equals(command.sessionId())
                &&fixture.expectedStart(before,source).equals(expected),"fixture first-map proof changed its original Start/expectation/source");
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived ack&&ack.nativeOk()&&ack.requestId().equals(attempt.requestId()),
                "fixture first-map proof requires the exact successful original Start ACK");
        var ack=(NativeActionPort.AckReceived)dispatch;var custody=ack.custody().orElseThrow();custody.verify(ack,attempt.guard());
        var readCustody=independentRead.custody().orElseThrow();readCustody.verify(independentRead);
        StrictJson.require(independentRead.nativeOk()&&!independentRead.requestId().equals(attempt.requestId())
                &&readCustody.session().equals(custody.session())&&readCustody.custodyEpoch().equals(custody.custodyEpoch())
                &&readCustody.writeEntered().order().compareTo(custody.responseReceived().order())>0
                &&snapshotReceived.order().compareTo(readCustody.writeCompleted().order())>0
                &&snapshotReceived.order().compareTo(readCustody.responseReceived().order())<0
                &&snapshotReceived.observedAt().equals(firstMap.observedAt()),
                "fixture first map requires the independent actual READ after its original Start ACK");
        StrictJson.require(!firstMap.observedAt().isBefore(custody.responseReceived().observedAt())
                &&!firstMap.originalNativePacket().equals(attempt.guard().nativeEvidence())
                &&custody.session().machineId().equals(firstMap.frame().machineId())&&custody.session().game().equals(firstMap.frame().game())
                &&custody.session().sessionId().equals(gameplaySession.sessionId())&&custody.session().connectionGeneration().equals(connectionGeneration),
                "fixture Start needs actual independent post-ACK first-map originals, never an old frame or ACK projection");
    }
}

package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;

/** Original .4 submit-only ACK normalizer. Native final_terms.payment_status is an admission enum, never a payment receipt. */
public final class HireMercenaryAck {
    private static final String EXE="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public enum Status { SUBMITTED, ALREADY_HIRED, REJECTED, UNAVAILABLE }
    public record Observation(Status status,BigInteger companyId,Optional<BigInteger> actor,boolean commandSubmitted,
            boolean verificationPending,NativeMercenaryMarket.Terms terms,Obj original) {
        public Observation { Objects.requireNonNull(status);Objects.requireNonNull(companyId);Objects.requireNonNull(actor);Objects.requireNonNull(terms);Objects.requireNonNull(original); }
        public boolean knownRejectedWithoutSubmission() { return status==Status.REJECTED&&!commandSubmitted&&!verificationPending; }
        public boolean employmentVerified() { return false; }
        public boolean paymentVerified() { return false; }
        public boolean availableArmyVerified() { return false; }
    }
    private HireMercenaryAck() { }
    public static Observation decode(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,Complete actualBefore) {
        require(command.operation().equals(OrdinaryFinancePolicies.MERCENARY)&&command.before().equals(actualBefore.identity())
                &&command.source().equals(actualBefore.source())&&command.sessionId().equals(actualBefore.sessionId())
                &&attempt.requestId().equals(ack.requestId()),"mercenary ACK crossed original command/request/native source");
        byte[] packet=ack.originalPacket(),payload=ack.originalFrame().bytes();
        require(packet.length>=5&&java.nio.ByteBuffer.wrap(packet,0,4).order(java.nio.ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4
                &&java.util.Arrays.equals(java.util.Arrays.copyOfRange(packet,4,packet.length),payload),"original mercenary ACK LE packet differs from full frame");
        Obj full=org.xar.ck3.control.application.driver.DriverJson.object(ack.originalFrame().bytes(),RawJson.MAXIMUM_BYTES);
        require(new Text("command_result").equals(full.get("type"))&&new IntegerValue(BigInteger.ONE).equals(full.get("protocol_version"))
                &&new Text(attempt.requestId()).equals(full.get("request_id"))&&new Bool(true).equals(full.get("ok"))&&ack.nativeOk(),"original mercenary ACK transport envelope mismatch");
        Obj result=object(full.get("result"),"original mercenary result");
        require(ack.originalResultToken().isPresent()&&result.equals(org.xar.ck3.control.application.driver.DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),RawJson.MAXIMUM_BYTES)),"mercenary ACK original frame/token differ");
        return decodeNativeResult(result,actualBefore.semantic(),org.xar.ck3.control.application.effects.NativeFinanceEffects.company(command.arguments()));
    }
    /** Pure producer parity boundary; a decoded value grants no native submission or material settlement authority. */
    public static Observation decodeNativeResult(Obj value,Obj snapshot,BigInteger expectedCompany) {
        require(new Text(OrdinaryFinancePolicies.MERCENARY.value()).equals(value.get("step"))&&new Text("1.20.0.4").equals(value.get("game_version"))
                &&new Text(EXE).equals(value.get("executable_sha256"))&&new Bool(false).equals(value.get("read_only")),"mercenary native ACK build/route mismatch");
        Obj hello=object(object(snapshot.get("diagnostics"),"actual diagnostics").get("hello"),"actual native hello");
        Value version=hello.get("expected_ck3_version")!=null?hello.get("expected_ck3_version"):hello.get("game_version");
        Value executable=hello.get("expected_ck3_sha256")!=null?hello.get("expected_ck3_sha256"):hello.get("executable_sha256");
        require(value.get("game_version").equals(version)&&value.get("executable_sha256").equals(executable),"mercenary ACK differs from actual current native snapshot build");
        BigInteger sequence=integer(value.get("command_sequence"),"actual command sequence");require(sequence.signum()>0&&sequence.bitLength()<=64,"positive native command sequence required");
        require(Objects.equals(value.get("snapshot_revision"),snapshot.get("native_revision"))&&Objects.equals(value.get("date_raw"),snapshot.get("date_raw")),"mercenary ACK differs from actual submission frame");
        integer(value.get("snapshot_revision"),"actual native revision");integer(value.get("date_raw"),"actual native date");
        Obj action=object(value.get("mercenary_hire"),"actual mercenary action");require(new Text("ck3_12004_mercenary_hire_action_v1").equals(action.get("schema")),"actual mercenary ACK schema required");
        String wire=text(action.get("status"),"mercenary status");Status status=switch(wire) { case "submitted"->Status.SUBMITTED;case "already_hired"->Status.ALREADY_HIRED;case "rejected"->Status.REJECTED;case "unavailable"->Status.UNAVAILABLE;default->throw new IllegalArgumentException("unrecognized mercenary submit status"); };
        boolean accepted=status==Status.SUBMITTED||status==Status.ALREADY_HIRED;
        require(new Bool(accepted).equals(value.get("accepted"))&&new Text(status==Status.SUBMITTED?"submitted_verification_pending":wire).equals(value.get("status"))
                &&Objects.equals(action.get("snapshot_revision"),value.get("snapshot_revision"))&&Objects.equals(action.get("date_raw"),value.get("date_raw")),"mercenary submit status/frame mirrors differ");
        BigInteger company=integer(action.get("company_id"),"full CompanyID");require(company.signum()>=0&&company.compareTo(new BigInteger("4294967295"))<0&&company.equals(expectedCompany),"mercenary ACK full company differs");
        require(new IntegerValue(BigInteger.ONE).equals(action.get("native_hire_mode")),"native mercenary mode differs");
        BigInteger player=integer(object(snapshot.get("played_character"),"actual player").get("character_id"),"player");
        Value actorValue=action.get("actor_character_id");Optional<BigInteger> actor=actorValue==Nil.INSTANCE?Optional.empty():Optional.of(integer(actorValue,"actual mercenary actor"));
        require(actor.isEmpty()||actor.orElseThrow().equals(player),"mercenary ACK actor differs");require(!accepted||actor.isPresent(),"accepted mercenary ACK lacks actual player");
        for(String key:List.of("company_resolved","native_command_validation_observable","command_submitted","verification_pending"))bool(action.get(key),key);
        Value employer=action.get("prior_employer_character_id");if(employer!=Nil.INSTANCE) { BigInteger id=integer(employer,"prior employer");require(id.signum()>=0&&id.compareTo(new BigInteger("4294967295"))<0,"prior employer domain differs"); }
        boolean observable=bool(action.get("native_command_validation_observable"),"native validation sampling");
        require(observable?action.get("native_command_valid") instanceof Bool:action.get("native_command_valid")==Nil.INSTANCE,"native command validity is not observed");
        Value reason=action.get("unavailable_reason");require(reason==Nil.INSTANCE||reason instanceof Text&&!((Text)reason).value().isEmpty(),"mercenary unavailable reason missing/invalid");
        require(new Bool(false).equals(action.get("after_state_observed")),"submit ACK cannot supply its own independent poststate");
        return new Observation(status,company,actor,bool(action.get("command_submitted"),"native submit marker"),bool(action.get("verification_pending"),"native pending marker"),
                NativeMercenaryMarket.decodeTerms(object(action.get("final_terms"),"actual original final terms")),value);
    }
}

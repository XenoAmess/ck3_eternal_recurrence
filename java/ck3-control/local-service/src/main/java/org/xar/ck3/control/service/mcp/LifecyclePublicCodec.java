package org.xar.ck3.control.service.mcp;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.LifecyclePublicResultCodec;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.lifecycle.DeathSettlement;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeOneLifeSettlement;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public DATA contracts. They cannot mint a terminal scope, original action or replacement authority. */
public final class LifecyclePublicCodec {
    private LifecyclePublicCodec() { }
    public static final String SETTLEMENT_CAPABILITY="game.state.xar-one-life-settlement";
    private static final BigInteger MAX_UINT64=BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    public enum ArgumentPresence { MISSING,NULL,OBJECT }
    public sealed interface RevisionExpectation permits MissingRevision,NullRevision,ExactRevision { }
    public record MissingRevision() implements RevisionExpectation { }
    public record NullRevision() implements RevisionExpectation { }
    public record ExactRevision(BigInteger value) implements RevisionExpectation {
        public ExactRevision {Objects.requireNonNull(value);require(value.signum()>=0&&value.compareTo(MAX_UINT64)<=0,"public revision must be exact uint64");}
    }
    public record NoArguments(ArgumentPresence presence) {public NoArguments {Objects.requireNonNull(presence);}}
    public record Request(ArgumentPresence presence,RevisionExpectation expectedRevision) {
        public Request {Objects.requireNonNull(presence);Objects.requireNonNull(expectedRevision);
            require(presence==ArgumentPresence.OBJECT||expectedRevision instanceof MissingRevision,"absent/null arguments cannot contain a revision field");}
        /** Missing and explicit null have the same Python default, while the decoded request retains both states. */
        public Optional<BigInteger> expected() {return expectedRevision instanceof ExactRevision exact?Optional.of(exact.value()):Optional.empty();}
    }
    public enum InspectionStatus {
        NOT_TERMINAL("not_terminal"),UNAVAILABLE("settlement_unavailable"),READY("ready"),SOURCE_MISMATCH("source_mismatch"),PENDING("pending");
        private final String wire;InspectionStatus(String wire){this.wire=wire;}public String wire(){return wire;}
    }
    public sealed interface SettlementField permits MissingSettlement,NullSettlement,PendingSettlement,ReadySettlement { }
    public record MissingSettlement() implements SettlementField { }
    public record NullSettlement() implements SettlementField { }
    public record PendingSettlement(Optional<BigInteger> commitSerial) implements SettlementField {
        public PendingSettlement {commitSerial=Objects.requireNonNull(commitSerial);commitSerial.ifPresent(value->require(value.signum()>=0,"nonnegative original pending commit_serial required"));}
    }
    public record ReadySettlement(DeathSettlement.Ready actual) implements SettlementField {public ReadySettlement {Objects.requireNonNull(actual);}}
    public sealed interface Payload permits Inspection,Applied,Unconfirmed { }
    public record Inspection(InspectionStatus status,boolean supported,boolean terminal,Optional<String> terminalReason,
            BigInteger episodeCharacterId,SettlementField settlement,String snapshotId,BigInteger revision,
            Optional<String> backendId,String machineId,Instant observedAtUtc) implements Payload {
        public Inspection {
            Objects.requireNonNull(status);terminalReason=Objects.requireNonNull(terminalReason);Objects.requireNonNull(episodeCharacterId);
            Objects.requireNonNull(settlement);StrictJson.text(snapshotId);Objects.requireNonNull(revision);backendId=Objects.requireNonNull(backendId);
            StrictJson.text(machineId);Objects.requireNonNull(observedAtUtc);require(episodeCharacterId.signum()>=0&&revision.signum()>=0,"original observation identities must be nonnegative integers");
            require(!machineId.isBlank()&&(terminalReason.isEmpty()||terminal),"actual machine and consistent terminal reason required");
            require(status==LifecyclePublicCodec.status(supported,terminal,episodeCharacterId,settlement),"inspection status differs from its actual settlement/episode binding");
        }
    }
    public record Applied(Kind kind,RawJson originalResult,String machineId,Instant sourceObservedAtUtc) implements Payload {
        public Applied {Objects.requireNonNull(kind);Objects.requireNonNull(originalResult);StrictJson.text(machineId);Objects.requireNonNull(sourceObservedAtUtc);
            require(!machineId.isBlank()&&(kind==Kind.DEATH||kind==Kind.NEXT_EPISODE),"actual machine and original one-life public operation required");validateBusiness(kind,object(originalResult));}
    }
    public record Unconfirmed(LifecycleExpectedPostcondition.Operation operation,ActionReceipt.Outcome outcome,boolean settled,
            String actionId,String actionBodySha256,ExactRef originalReceipt,String machineId,Instant sourceObservedAtUtc) implements Payload {
        public Unconfirmed {Objects.requireNonNull(operation);Objects.requireNonNull(outcome);StrictJson.text(actionId);Objects.requireNonNull(originalReceipt);
            require(operation==LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL||operation==LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,"one-life operation required");
            require(actionBodySha256!=null&&actionBodySha256.matches("[0-9a-f]{64}")&&originalReceipt.bytes()>0,"actual canonical original receipt/body required");
            StrictJson.text(machineId);require(!machineId.isBlank(),"actual machine required");Objects.requireNonNull(sourceObservedAtUtc);}
    }
    public static NoArguments decodeNoArguments(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)return new NoArguments(ArgumentPresence.MISSING);
        if(arguments instanceof PublicBindings.Null)return new NoArguments(ArgumentPresence.NULL);
        ObjectNode row=object(((PublicBindings.Value)arguments).original());fields(row,Set.of());return new NoArguments(ArgumentPresence.OBJECT);
    }
    public static Request decodeRequest(PublicBindings.Arguments arguments) {
        Objects.requireNonNull(arguments);
        if(arguments instanceof PublicBindings.Missing)return new Request(ArgumentPresence.MISSING,new MissingRevision());
        if(arguments instanceof PublicBindings.Null)return new Request(ArgumentPresence.NULL,new MissingRevision());
        ObjectNode row=object(((PublicBindings.Value)arguments).original());fields(row,Set.of("expected_revision"));JsonNode value=row.get("expected_revision");
        RevisionExpectation expected;
        if(value==null)expected=new MissingRevision();else if(value.isNull())expected=new NullRevision();else {
            require(value.isTextual()&&value.textValue().length()<=20&&value.textValue().matches("0|[1-9][0-9]*"),"expected_revision requires a canonical uint64 decimal string or explicit null");
            expected=new ExactRevision(new BigInteger(value.textValue()));
        }
        return new Request(ArgumentPresence.OBJECT,expected);
    }
    public static PublicBindings.Arguments encodeRequest(Request request) {
        Objects.requireNonNull(request);
        if(request.presence()==ArgumentPresence.MISSING)return new PublicBindings.Missing();
        if(request.presence()==ArgumentPresence.NULL)return new PublicBindings.Null();
        ObjectNode row=StrictJson.object();
        if(request.expectedRevision() instanceof NullRevision)row.putNull("expected_revision");
        else if(request.expectedRevision() instanceof ExactRevision exact)row.put("expected_revision",exact.value().toString());
        return new PublicBindings.Value(raw(row));
    }
    public static Inspection inspect(OpportunityJson.Obj actualSemantic,Set<String> originalBridgeCapabilities,String machineId,Instant actualObservedAtUtc) {
        Objects.requireNonNull(actualSemantic);originalBridgeCapabilities=Set.copyOf(originalBridgeCapabilities);
        ObjectNode row=object(new RawJson(DriverJson.encode(actualSemantic)));
        Optional<String> reason=optionalText(row.get("one_life_terminal_reason"));
        JsonNode flag=row.get("one_life_terminal");require(flag==null||flag.isNull()||flag.isBoolean(),"original one_life_terminal must be bool, null or missing");
        boolean terminal=flag!=null&&flag.isBoolean()&&flag.booleanValue()||reason.isPresent();
        BigInteger actor=integer(row.get("episode_character_id"),"episode_character_id");
        SettlementField settlement=settlement(actualSemantic);boolean supported=originalBridgeCapabilities.contains(SETTLEMENT_CAPABILITY);
        return new Inspection(status(supported,terminal,actor,settlement),supported,terminal,reason,actor,settlement,
                StrictJson.text(row.get("snapshot_id")),integer(row.get("revision"),"revision"),optionalText(row.get("backend_id")),machineId,actualObservedAtUtc);
    }
    private static InspectionStatus status(boolean supported,boolean terminal,BigInteger actor,SettlementField settlement) {
        if(!terminal)return InspectionStatus.NOT_TERMINAL;if(!supported)return InspectionStatus.UNAVAILABLE;
        if(settlement instanceof ReadySettlement ready)return ready.actual().sourceCharacterId().equals(actor)?InspectionStatus.READY:InspectionStatus.SOURCE_MISMATCH;
        return InspectionStatus.PENDING;
    }
    /** Input is the actual normalized SEM/public field, never a fresh native scalar. Preserve its original decimal tokens. */
    private static SettlementField settlement(OpportunityJson.Obj actual) {
        if(!actual.members().containsKey(NativeOneLifeSettlement.KEY))return new MissingSettlement();
        var original=actual.get(NativeOneLifeSettlement.KEY);
        if(original instanceof OpportunityJson.Nil)return new NullSettlement();
        var parsed=NativeOneLifeSettlement.decodeNormalized(DriverJson.encode(original),RawJson.MAXIMUM_BYTES);
        if(parsed instanceof NativeOneLifeSettlement.Pending pending)return new PendingSettlement(pending.commitSerial());
        require(parsed instanceof NativeOneLifeSettlement.Ready,"actual normalized settlement state required");
        return new ReadySettlement(DeathSettlement.fromNormalized(NativeOneLifeSettlement.encode(parsed)).orElseThrow());
    }
    /** A real Root action callback supplies its canonical receipt and same-writer archive, including after actual NEXT retirement. */
    public static Payload present(LifecycleExpectedPostcondition.Operation expected,ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(expected);Objects.requireNonNull(actual);Objects.requireNonNull(archive);
        require(expected==LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL||expected==LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,"one-life public operation required");
        require(actual.command().operation().equals(expected.key())&&actual.command().origin() instanceof CommandOrigin.LifecycleTerminal,"public lifecycle result crossed its original terminal operation");
        ExactRef receipt=archive.receiptReferenceOf(actual);require(archive.loadReceipt(receipt).equals(actual),"public lifecycle result must retain its exact canonical receipt");
        var origin=actual.command().lifecycleBefore();
        if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&actual.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied) {
            var proof=applied.proof();proof.validateParent(actual.command());Kind kind=expected==LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL?Kind.DEATH:Kind.NEXT_EPISODE;
            require(proof.kind()==kind,"original lifecycle proof kind differs from selected public operation");
            return new Applied(kind,new RawJson(proof.encodedResult()),origin.machineId(),origin.observedAt());
        }
        return new Unconfirmed(expected,actual.outcome(),actual.settled(),actual.command().actionId(),actual.bodySha256(),receipt,origin.machineId(),origin.observedAt());
    }
    /** Original generic EXECUTE projection; it never grants a terminal scope or retry authority. */
    public static RawJson presentStep(LifecycleExpectedPostcondition.Operation expected,ActionReceipt actual,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(expected);Objects.requireNonNull(actual);Objects.requireNonNull(archive);
        if(expected==LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL||expected==LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE)
            return encode(present(expected,actual,archive));
        require(expected==LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,"exact original lifecycle EXECUTE operation required");
        require(actual.command().operation().equals(expected.key())&&actual.command().origin() instanceof CommandOrigin.LifecycleTerminal,
                "natural public result crossed its actual terminal parent operation");
        ExactRef reference=archive.receiptReferenceOf(actual);require(archive.loadReceipt(reference).equals(actual),"natural public result lost its actual original canonical receipt");
        var origin=actual.command().lifecycleBefore();
        if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&actual.state() instanceof ActionState.CompositeSettled settled
                &&settled.settlement() instanceof ActionState.LifecycleApplied applied){
            var proof=applied.proof();proof.validateParent(actual.command());require(proof.kind()==Kind.CONTINUE_SUCCESSOR,"natural public result has another lifecycle proof kind");
            RawJson projection=LifecyclePublicResultCodec.encode(Kind.CONTINUE_SUCCESSOR,new RawJson(proof.encodedResult()));var row=object(projection);
            sameOrPut(row,"machine_id",origin.machineId());sameOrPut(row,"source_observed_at_utc",origin.observedAt().toString());
            return PublicDataJson.encodePreservingDecimals(row,projection);
        }
        // A canonical consumed parent without its original business proof remains unconfirmed DATA.
        // No caller-supplied ACK, reconciliation or DTO can turn this branch into "continued".
        var row=StrictJson.object().put("step",expected.key().value()).put("status",actual.settled()?"public_result_unavailable":"action_state_unknown")
                .put("canonical_outcome",actual.outcome().name()).put("action_id",actual.command().actionId()).put("action_body_sha256",actual.bodySha256())
                .put("never_replay",true).put("material_result_available",false).put("machine_id",origin.machineId()).put("source_observed_at_utc",origin.observedAt().toString());
        row.set("original_receipt",reference.toJson());return raw(row);
    }
    public static RawJson encode(Payload payload) {
        Objects.requireNonNull(payload);ObjectNode row;
        if(payload instanceof Inspection value) {
            row=StrictJson.object().put("status",value.status().wire()).put("supported",value.supported()).put("terminal",value.terminal());
            if(value.terminalReason().isPresent())row.put("terminal_reason",value.terminalReason().orElseThrow());else row.putNull("terminal_reason");
            row.put("episode_character_id",value.episodeCharacterId());row.set("one_life_settlement",settlementJson(value.settlement()));
            row.put("continue_as_heir_after_death",false).put("heir_gameplay_actions",0).put("snapshot_id",value.snapshotId()).put("revision",value.revision());
            if(value.backendId().isPresent())row.put("backend_id",value.backendId().orElseThrow());else row.putNull("backend_id");
            row.put("machine_id",value.machineId()).put("observed_at_utc",value.observedAtUtc().toString());
            return LifecyclePublicResultCodec.encodeSettlementInspection(raw(row));
        }
        if(payload instanceof Applied value) {
            RawJson originalProjection=LifecyclePublicResultCodec.encode(value.kind(),value.originalResult());row=object(originalProjection);
            sameOrPut(row,"machine_id",value.machineId());sameOrPut(row,"source_observed_at_utc",value.sourceObservedAtUtc().toString());
            return PublicDataJson.encodePreservingDecimals(row,originalProjection);
        }
        Unconfirmed value=(Unconfirmed)payload;
        row=StrictJson.object().put("step",value.operation().key().value()).put("status",value.settled()?"public_result_unavailable":"action_state_unknown")
                .put("canonical_outcome",value.outcome().name()).put("action_id",value.actionId()).put("action_body_sha256",value.actionBodySha256())
                .put("never_replay",true).put("material_result_available",false).put("machine_id",value.machineId()).put("source_observed_at_utc",value.sourceObservedAtUtc().toString());
        row.set("original_receipt",value.originalReceipt().toJson());return raw(row);
    }
    /** Public roundtrip uses the same sole revision-role codec; score and counters keep their original JSON number types. */
    public static Inspection decodeInspection(RawJson publicResult) {
        RawJson normalized=LifecyclePublicResultCodec.decodeSettlementInspection(Objects.requireNonNull(publicResult));
        ObjectNode row=object(normalized);
        var normalizedSemantic=DriverJson.object(normalized.bytes(),RawJson.MAXIMUM_BYTES);
        Set<String> names=Set.of("status","supported","terminal","terminal_reason","episode_character_id","one_life_settlement",
                "continue_as_heir_after_death","heir_gameplay_actions","snapshot_id","revision","backend_id","machine_id","observed_at_utc");
        StrictJson.object(row,names);require(row.path("continue_as_heir_after_death").isBoolean()&&!row.get("continue_as_heir_after_death").booleanValue()
                &&BigInteger.ZERO.equals(integer(row.get("heir_gameplay_actions"),"heir_gameplay_actions")),"inspection cannot claim heir gameplay");
        InspectionStatus status=null;String wire=StrictJson.text(row.get("status"));for(InspectionStatus value:InspectionStatus.values())if(value.wire().equals(wire))status=value;
        require(status!=null,"unknown one-life inspection status");
        return new Inspection(status,booleanValue(row.get("supported")),booleanValue(row.get("terminal")),optionalText(row.get("terminal_reason")),
                integer(row.get("episode_character_id"),"episode_character_id"),settlement(normalizedSemantic),StrictJson.text(row.get("snapshot_id")),
                integer(row.get("revision"),"revision"),optionalText(row.get("backend_id")),StrictJson.text(row.get("machine_id")),Instant.parse(StrictJson.text(row.get("observed_at_utc"))));
    }
    private static JsonNode settlementJson(SettlementField field) {
        if(field instanceof ReadySettlement ready)return ready.actual().normalizedJson();
        if(field instanceof PendingSettlement pending)return NativeOneLifeSettlement.encode(new NativeOneLifeSettlement.Pending(pending.commitSerial()));
        return StrictJson.object().nullNode();
    }
    private static void validateBusiness(Kind kind,ObjectNode row) {
        if(kind==Kind.DEATH) {
            require(row.path("terminal").isBoolean()&&row.get("terminal").booleanValue()&&row.path("continue_as_heir_after_death").isBoolean()&&!row.get("continue_as_heir_after_death").booleanValue()
                    &&BigInteger.ZERO.equals(integer(row.get("heir_gameplay_actions"),"heir_gameplay_actions")),"actual one-life terminal violates its no-heir contract");
            String disposition=StrictJson.text(row.get("settlement_status"));require(Set.of("complete","settlement_unavailable").contains(disposition),"known actual settlement disposition required");
            if(!disposition.equals("settlement_unavailable")){require(row.path("score").isNumber(),"actual normalized death score must remain a JSON number");DeathSettlement.fixedScore(row.get("score"));}
        } else require(row.path("status").isTextual()&&row.get("status").textValue().equals("started")&&row.path("lifecycle_intent").isTextual()&&row.get("lifecycle_intent").textValue().equals("new_episode")
                &&row.path("episode_run_id").isTextual()&&!row.get("episode_run_id").textValue().isBlank()&&row.get("cross_run_plan_used") instanceof ObjectNode,"actual next-episode result lacks its original new-run/plan material");
    }
    private static BigInteger integer(JsonNode value,String name) {require(value!=null&&value.isIntegralNumber()&&value.bigIntegerValue().signum()>=0,name+" requires a nonnegative integer, never bool/float");return value.bigIntegerValue();}
    private static boolean booleanValue(JsonNode value) {require(value!=null&&value.isBoolean(),"actual JSON boolean required");return value.booleanValue();}
    private static Optional<String> optionalText(JsonNode value) {return value==null||value.isNull()?Optional.empty():Optional.of(StrictJson.text(value));}
    private static ObjectNode object(RawJson original) {return PublicDataJson.object(original);}
    private static void fields(ObjectNode row,Set<String> allowed) {Set<String> actual=new HashSet<>();row.fieldNames().forEachRemaining(actual::add);require(allowed.containsAll(actual),"unknown public lifecycle arguments");}
    private static RawJson raw(ObjectNode row) {return PublicDataJson.encode(row);}
    private static void sameOrPut(ObjectNode row,String key,String value) {if(row.has(key))require(row.get(key).isTextual()&&row.get(key).textValue().equals(value),"actual lifecycle public provenance field conflicts");else row.put(key,value);}
}

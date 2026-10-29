package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;

/** The original nine explicit driver-tool arguments. Public tokens confer no native qualification. */
public final class DriverGovernancePublicInput {
    private DriverGovernancePublicInput() { }
    public record Revision(BigInteger expectedRevision) {
        public Revision { positive(expectedRevision); }
    }
    public record CouncilQuery(BigInteger expectedRevision,CouncilModels.Position position) {
        public CouncilQuery { positive(expectedRevision);Objects.requireNonNull(position); }
    }
    public sealed interface RequestedActionId permits MissingActionId,NullActionId,ActionId { }
    public record MissingActionId() implements RequestedActionId { }
    public record NullActionId() implements RequestedActionId { }
    public record ActionId(String value) implements RequestedActionId {
        public ActionId { Objects.requireNonNull(value); }
    }
    public record CouncilAssign(RawJson query,int candidateCharacterId,BigInteger expectedRevision,RequestedActionId actionId) {
        public CouncilAssign { object(query);StrictJson.require(candidateCharacterId>0,"positive int31 candidate required");positive(expectedRevision);Objects.requireNonNull(actionId); }
    }
    public record CouncilReceipt(RawJson pending,BigInteger expectedRevision) {
        public CouncilReceipt { object(pending);positive(expectedRevision); }
    }
    public record Budget(CrownAuthorityPolicy.Currency currency,BigInteger raw) {
        public Budget { Objects.requireNonNull(currency);Objects.requireNonNull(raw);StrictJson.require(raw.signum()>=0&&raw.compareTo(BigInteger.valueOf(Long.MAX_VALUE))<=0,"nonnegative signed64 caller budget required"); }
    }
    public record CrownEnact(RawJson readback,String lawKey,List<Budget> budgets,String actionId) {
        public CrownEnact {
            object(readback);validateLawKey(lawKey);
            budgets=List.copyOf(budgets).stream().sorted(java.util.Comparator.comparing(value->value.currency().wire())).toList();var currencies=new HashSet<CrownAuthorityPolicy.Currency>();
            for(var budget:budgets)StrictJson.require(currencies.add(budget.currency()),"duplicate caller currency limit");nativeId(actionId);
        }
    }
    public record CrownReceipt(BigInteger expectedRevision,String submittedRequestId) {
        public CrownReceipt { positive(expectedRevision);nativeId(submittedRequestId); }
    }
    /** Original Python uses action_request_id or generatedDefault: empty string is preserved publicly but selects the default. */
    public static java.util.Optional<String> explicitCouncilId(RequestedActionId value) {
        Objects.requireNonNull(value);return value instanceof ActionId id&&!id.value().isEmpty()?java.util.Optional.of(id.value()):java.util.Optional.empty();
    }
    private static void positive(BigInteger value) { PublicUnsigned64.canonical(value,PublicUnsigned64.Minimum.ONE); }
    static void validateLawKey(String value) {StrictJson.require(value!=null&&value.startsWith("crown_authority_")&&value.length()<=95,"explicit crown-authority law key required");}
    static void nativeId(String value) {
        StrictJson.require(value!=null&&!value.isEmpty()&&value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=63,"nonempty native request identity within 63 UTF-8 bytes required");
    }
    private static void object(RawJson value) { Objects.requireNonNull(value);StrictJson.require(StrictJson.parse(value.bytes()).isObject(),"original named object required"); }
}

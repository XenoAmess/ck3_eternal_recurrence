package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import static org.xar.ck3.control.service.root.DriverGovernancePublicInput.*;

/** Single named-object input contract for the nine original private driver tools. */
public final class DriverGovernancePublicCodec {
    private DriverGovernancePublicCodec() { }
    public static Revision revision(RawJson original) {
        var node=exact(original,Set.of("expected_revision"),Set.of());return new Revision(revision(node));
    }
    public static CouncilQuery council(RawJson original) {
        var node=exact(original,Set.of("expected_revision"),Set.of("position_key"));
        var position=node.has("position_key")?CouncilModels.Position.exact(CouncilCodec.text(node,"position_key")):CouncilModels.Position.STEWARD;
        return new CouncilQuery(revision(node),position);
    }
    public static CouncilAssign assign(RawJson original) {
        var node=exact(original,Set.of("query","candidate_character_id","expected_revision"),Set.of("action_request_id"));
        RequestedActionId id=!node.has("action_request_id")?new MissingActionId():node.get("action_request_id").isNull()?new NullActionId():new ActionId(StrictJson.text(node.get("action_request_id")));
        return new CouncilAssign(object(node.get("query")),CouncilCodec.id(node.get("candidate_character_id")),revision(node),id);
    }
    public static CouncilReceipt councilReceipt(RawJson original) {
        var node=exact(original,Set.of("pending","expected_revision"),Set.of());return new CouncilReceipt(object(node.get("pending")),revision(node));
    }
    public static CrownEnact enact(RawJson original) {
        var node=exact(original,Set.of("readback","law_key","budgets","action_id"),Set.of());
        String law=CouncilCodec.text(node,"law_key");try {DriverGovernancePublicInput.validateLawKey(law);}catch(IllegalArgumentException rejected){throw valueError("law_key must identify a crown-authority candidate");}
        var amounts=CouncilCodec.object(node.get("budgets"));var budgets=new ArrayList<Budget>();
        amounts.properties().forEach(entry->{
            CrownAuthorityPolicy.Currency currency;try {currency=currency(entry.getKey());}catch(IllegalArgumentException rejected){throw valueError("budgets must contain supported nonnegative raw currency limits");}
            var value=budget(entry.getValue());
            budgets.add(new Budget(currency,value));
        });
        String action=CouncilCodec.text(node,"action_id");try {DriverGovernancePublicInput.nativeId(action);}catch(IllegalArgumentException rejected){throw valueError("action_id must be nonempty and fit the native request ID");}
        return new CrownEnact(object(node.get("readback")),law,budgets,action);
    }
    public static CrownReceipt crownReceipt(RawJson original) {
        var node=exact(original,Set.of("expected_revision","submitted_request_id"),Set.of());return new CrownReceipt(revision(node),CouncilCodec.text(node,"submitted_request_id"));
    }
    public static RawJson encode(Revision value) {return raw(StrictJson.object().put("expected_revision",value.expectedRevision().toString()));}
    public static RawJson encode(CouncilQuery value) {return raw(StrictJson.object().put("expected_revision",value.expectedRevision().toString()).put("position_key",value.position().key()));}
    public static RawJson encode(CouncilAssign value) {
        var node=StrictJson.object().put("candidate_character_id",value.candidateCharacterId()).put("expected_revision",value.expectedRevision().toString());node.set("query",StrictJson.parse(value.query().bytes()));
        if(value.actionId() instanceof ActionId id)node.put("action_request_id",id.value());else if(value.actionId() instanceof NullActionId)node.putNull("action_request_id");return raw(node);
    }
    public static RawJson encode(CouncilReceipt value) {var node=StrictJson.object().put("expected_revision",value.expectedRevision().toString());node.set("pending",StrictJson.parse(value.pending().bytes()));return raw(node);}
    public static RawJson encode(CrownEnact value) {
        var node=StrictJson.object().put("law_key",value.lawKey()).put("action_id",value.actionId());node.set("readback",StrictJson.parse(value.readback().bytes()));var budgets=node.putObject("budgets");
        for(var amount:value.budgets())budgets.put(amount.currency().wire(),amount.raw().toString());return raw(node);
    }
    public static RawJson encode(CrownReceipt value) {return raw(StrictJson.object().put("expected_revision",value.expectedRevision().toString()).put("submitted_request_id",value.submittedRequestId()));}
    private static BigInteger budget(JsonNode token) {
        BigInteger value;
        if(token.isTextual()) {StrictJson.require(token.textValue().matches("0|-?[1-9][0-9]{0,18}"),"canonical signed64 budget representation required");value=new BigInteger(token.textValue());}
        else {StrictJson.require(token.isIntegralNumber()&&token.bigIntegerValue().abs().compareTo(PublicUnsigned64.MAXIMUM_SAFE_NUMBER)<=0,"safe integral public budget representation required");value=token.bigIntegerValue();}
        if(value.signum()<0||value.compareTo(BigInteger.valueOf(Long.MAX_VALUE))>0)throw valueError("budgets must contain supported nonnegative raw currency limits");return value;
    }
    private static org.xar.ck3.control.service.mcp.PublicServiceFailure valueError(String message) {
        return new org.xar.ck3.control.service.mcp.PublicServiceFailure(org.xar.ck3.control.service.mcp.PublicServiceFailure.Kind.exact("ValueError"),message,java.util.Optional.empty());
    }
    private static BigInteger revision(ObjectNode node) {return PublicUnsigned64.parse(node.get("expected_revision"),PublicUnsigned64.Minimum.ONE,PublicUnsigned64.NumericInput.SAFE_INTEGER_OR_DECIMAL);}
    private static CrownAuthorityPolicy.Currency currency(String key) {
        for(var value:CrownAuthorityPolicy.Currency.values())if(value.wire().equals(key))return value;throw new IllegalArgumentException("unknown caller currency budget");
    }
    private static RawJson object(JsonNode value) {CouncilCodec.object(value);return raw(value);}
    private static RawJson raw(JsonNode value) {return new RawJson(StrictJson.canonical(value));}
    private static ObjectNode exact(RawJson value,Set<String> required,Set<String> optional) {
        var node=CouncilCodec.object(StrictJson.parse(value.bytes()));var actual=new HashSet<String>();node.fieldNames().forEachRemaining(actual::add);
        StrictJson.require(actual.containsAll(required),"missing private governance tool fields");actual.removeAll(required);StrictJson.require(optional.containsAll(actual),"unknown private governance tool field");return node;
    }
}

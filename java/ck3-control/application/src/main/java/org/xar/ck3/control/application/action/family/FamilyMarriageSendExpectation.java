package org.xar.ck3.control.application.action.family;

import java.math.BigInteger;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;

/**
 * Immutable pre-submission subset for an outgoing marriage request. The native
 * pending ID is unknown before submission and never belongs in this expectation.
 * The dedicated observer must additionally validate its closed send-only actual
 * values, including pending ID and explicit false gameplay/advance/checkpoint
 * flags. ProposalLifecycle.compare matches this subset; it grants no settlement.
 */
public final class FamilyMarriageSendExpectation {
    public static final String SCHEMA="xar.java.family-marriage-send-observation/v1";
    private FamilyMarriageSendExpectation() { }
    public static ExpectedPostcondition expected(ObservationIdentity before,G2Source source,long subject,long candidate) {
        return new ExpectedPostcondition(1,before,source,SCHEMA,values(subject,candidate));
    }
    public static List<ExpectedValue> values(long subject,long candidate) {
        StrictJson.require(subject>0&&subject<0xFFFF_FFFFL&&candidate>0&&candidate<0xFFFF_FFFFL&&subject!=candidate,"distinct full native marriage pair required");
        return List.of(new ExpectedInteger(new FieldKey("subject_full_id"),BigInteger.valueOf(subject)),
                new ExpectedInteger(new FieldKey("candidate_full_id"),BigInteger.valueOf(candidate)),
                new ExpectedBoolean(new FieldKey("outbound_request_effect_observed"),true),
                new ExpectedBoolean(new FieldKey("marriage_relation_verified"),false),
                new ExpectedBoolean(new FieldKey("alliance_verified"),false),
                new ExpectedBoolean(new FieldKey("fees_verified"),false));
    }
}

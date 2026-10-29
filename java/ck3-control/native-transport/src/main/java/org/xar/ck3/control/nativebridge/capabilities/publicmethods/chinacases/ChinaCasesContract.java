package org.xar.ck3.control.nativebridge.capabilities.publicmethods.chinacases;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesActions;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesCodec.Family;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.IncidentProfile;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.Nonce;
import org.xar.ck3.control.nativebridge.capabilities.china_cases.ChinaCasesModel.CharacterId;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original public argument contract. These are DATA values, never read/submit authority. */
public final class ChinaCasesContract {
    private ChinaCasesContract() { }
    public enum Method {
        ACTIVATE_SCOREBOARD("ck3_activate_zhongguo_scoreboard_v1", null, null),
        AI_OWNED("ck3_query_zhongguo_ai_owned_case_snapshot_v1", Family.AIOWNED, "zhongguo_ai_owned_case_snapshot"),
        B1("ck3_query_zhongguo_b1_cycle_snapshot_v1", Family.B1, "zhongguo_b1_cycle_snapshot"),
        PIP("ck3_query_zhongguo_b2_pip_snapshot_v1", Family.PIP, "zhongguo_b2_pip_snapshot"),
        CASE("ck3_query_zhongguo_case_snapshot_v1", Family.CASE, "zhongguo_case_snapshot"),
        AF5("ck3_query_zhongguo_compensation_af5_snapshot_v1", Family.AF5, "zhongguo_compensation_af5_snapshot"),
        INCIDENT("ck3_query_zhongguo_incident_snapshot_v1", Family.INCIDENT, "zhongguo_incident_snapshot"),
        PROJECTS("ck3_query_zhongguo_projects_metrics_postcondition_v1", Family.PROJECTS, "zhongguo_projects_metrics_postcondition"),
        PROMOTION("ck3_query_zhongguo_promotion_compensation_postcondition_v1", Family.PROMOTION, "zhongguo_promotion_compensation_postcondition"),
        RESULT("ck3_query_zhongguo_result_case_snapshot_v1", Family.RESULT, "zhongguo_result_case_snapshot"),
        SCOREBOARD("ck3_query_zhongguo_scoreboard_state_v1", Family.SCOREBOARD, "zhongguo_scoreboard_state");
        private final String publicName;
        private final Family family;
        private final String payload;
        Method(String publicName, Family family, String payload) { this.publicName=publicName; this.family=family; this.payload=payload; }
        public String publicName() { return publicName; }
        public boolean readOnly() { return family!=null; }
        public Family family() { StrictJson.require(readOnly(), "scoreboard activation is not a read"); return family; }
        public String payload() { StrictJson.require(readOnly(), "scoreboard activation has no query payload"); return payload; }
    }
    public sealed interface Request permits ReadRequest, ActionRequest { Method method(); String requestNonce(); }
    public record ReadRequest(Method method, String requestNonce, PublicUnsigned64.Field expectedRevision,
            OptionalInt ownerCharacterId, OptionalInt subjectCharacterId, Optional<IncidentProfile> profile) implements Request {
        public ReadRequest {
            Objects.requireNonNull(method); StrictJson.require(method.readOnly(), "query method required"); nonce(requestNonce);
            Objects.requireNonNull(expectedRevision); Objects.requireNonNull(ownerCharacterId); Objects.requireNonNull(subjectCharacterId); profile=Objects.requireNonNull(profile);
            if (method!=Method.AI_OWNED) StrictJson.require(expectedRevision instanceof PublicUnsigned64.Value, "expected_revision is required and nonnull");
            ownerCharacterId.ifPresent(ChinaCasesContract::character); subjectCharacterId.ifPresent(ChinaCasesContract::character);
            boolean ownerRequired=switch(method) { case AI_OWNED,RESULT,PIP,PROJECTS,INCIDENT -> true; default -> false; };
            boolean ownerAllowed=ownerRequired || method==Method.CASE;
            StrictJson.require(ownerAllowed || ownerCharacterId.isEmpty(), "owner_character_id is not a parameter of this method");
            StrictJson.require(!ownerRequired || ownerCharacterId.isPresent(), "owner_character_id is required");
            StrictJson.require(method==Method.CASE || method==Method.AI_OWNED || method==Method.PROJECTS || subjectCharacterId.isEmpty(), "subject_character_id is not a parameter of this method");
            StrictJson.require(method!=Method.AI_OWNED || subjectCharacterId.isPresent(), "subject_character_id is required");
            StrictJson.require((method==Method.INCIDENT)==profile.isPresent(), "profile is required only by the incident query");
        }
        public Nonce nativeNonce() { return new Nonce(requestNonce); }
        public Optional<CharacterId> owner() { return ownerCharacterId.isPresent()?Optional.of(new CharacterId(ownerCharacterId.getAsInt())):Optional.empty(); }
        public Optional<CharacterId> subject() { return subjectCharacterId.isPresent()?Optional.of(new CharacterId(subjectCharacterId.getAsInt())):Optional.empty(); }
    }
    /** Exact original MCP request. Wire-only expected_public_revision is produced in nativeArguments(). */
    public record ActionRequest(String requestNonce, ChinaCasesActions.ScoreboardAction action,
            BigInteger expectedRevision, BigInteger expectedNativeRevision, BigInteger expectedConnectionGeneration,
            int expectedPlayerCharacterId, String expectedProviderSessionId, BigInteger expectedObservationSequence,
            BigInteger expectedObservedStateRevision, String expectedTreeFingerprintV1, String expectedSemanticFingerprintV1,
            String expectedWindowInstancePointer, String expectedTargetInstancePointer, String expectedTargetVtablePointer) implements Request {
        public ActionRequest {
            nonce(requestNonce); Objects.requireNonNull(action);
            PublicUnsigned64.canonical(expectedRevision,PublicUnsigned64.Minimum.ZERO);
            PublicUnsigned64.canonical(expectedNativeRevision,PublicUnsigned64.Minimum.ONE);
            PublicUnsigned64.canonical(expectedConnectionGeneration,PublicUnsigned64.Minimum.ONE);
            PublicUnsigned64.canonical(expectedObservationSequence,PublicUnsigned64.Minimum.ONE);
            PublicUnsigned64.canonical(expectedObservedStateRevision,PublicUnsigned64.Minimum.ONE);
            character(expectedPlayerCharacterId);
            StrictJson.require(expectedProviderSessionId!=null && expectedProviderSessionId.matches("[0-9A-F]{32}"),"expected_provider_session_id requires 32 uppercase hexadecimal digits");
            fingerprint(expectedTreeFingerprintV1); fingerprint(expectedSemanticFingerprintV1);
            pointer(expectedWindowInstancePointer); pointer(expectedTargetInstancePointer); pointer(expectedTargetVtablePointer);
        }
        @Override public Method method() { return Method.ACTIVATE_SCOREBOARD; }
        public ChinaCasesActions.ScoreboardRequest nativeRequest() {
            return new ChinaCasesActions.ScoreboardRequest(new Nonce(requestNonce),action,expectedRevision,expectedNativeRevision,
                    expectedConnectionGeneration,new CharacterId(expectedPlayerCharacterId),
                    new ChinaCasesActions.ProviderBinding(expectedProviderSessionId,expectedObservationSequence,expectedObservedStateRevision,
                            expectedTreeFingerprintV1,expectedSemanticFingerprintV1),
                    new ChinaCasesActions.Pointer(expectedWindowInstancePointer),new ChinaCasesActions.Pointer(expectedTargetInstancePointer),
                    new ChinaCasesActions.Pointer(expectedTargetVtablePointer));
        }
        public OpportunityJson.Obj nativeArguments() { return nativeRequest().arguments(); }
        public OpportunityJson.Obj arguments() { return nativeArguments(); }
    }
    static void nonce(String value) { StrictJson.require(value!=null && value.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"),"request_nonce is invalid"); }
    static void character(int value) { StrictJson.require(value>0,"character ID must be a positive int32"); }
    static void pointer(String value) { StrictJson.require(value!=null && value.matches("0x[0-9A-F]+"),"uppercase hexadecimal pointer required"); }
    static void fingerprint(String value) { StrictJson.require(value!=null && value.matches("[0-9A-F]{64}"),"64 uppercase hexadecimal fingerprint required"); }
}

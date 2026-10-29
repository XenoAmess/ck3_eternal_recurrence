package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.OptionalLong;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Complete original first-heir legal enumeration. The bound heir remains a title heir. */
public final class FamilyHeirLegality {
    public static final String STEP="query-observed-first-heir-marriage-legality-v1";
    public static final String SCHEMA="xar.ck3.observed-first-heir-marriage-legality.v1";
    private FamilyHeirLegality() { }
    /** Data binding only; the query installer must verify the retained original root receipt on its held session. */
    public record Binding(Context context, BigInteger rootQuerySequence,
                          OptionalLong observedFirstHeir, ExactRef originalCampaignRoot) {
        public Binding {
            Objects.requireNonNull(context); Objects.requireNonNull(observedFirstHeir); Objects.requireNonNull(originalCampaignRoot);
            range(rootQuerySequence,BigInteger.ONE,U64);
            need(observedFirstHeir.isEmpty() || (observedFirstHeir.getAsLong()>0 && observedFirstHeir.getAsLong()<=Integer.MAX_VALUE),
                    "public campaign-root title heir outside native int32 domain");
            need((context.build()==Build.CROZIER3 || context.build()==Build.CROZIER4) &&
                    context.source().exactBuild().equals(context.build().version()),
                    "family legal decoder requires its exact3/4 source; runtime admission separately requires current4");
        }
    }
    public record Observation(Binding binding, BigInteger querySequence, Availability availability,
                              List<HeirMarriageCandidate> candidates, MarriageDiagnostics diagnostics,
                              int subjectRoleMismatches, RawJson original) {
        public Observation {
            Objects.requireNonNull(binding); Objects.requireNonNull(availability); Objects.requireNonNull(diagnostics);
            Objects.requireNonNull(original); range(querySequence,BigInteger.ONE,U64); candidates=List.copyOf(candidates);
            need(subjectRoleMismatches>=0,"negative family subject-role mismatch count");
            if(availability.available()) need(binding.observedFirstHeir().isPresent() && diagnostics.complete(),
                    "available family legal enumeration lacks its actual heir or complete storage traversal");
            else need(candidates.isEmpty(),"unavailable family legal enumeration invented candidates");
        }
        public List<HeirMarriageCandidate> nativeLegalCandidates() {
            return candidates.stream().filter(HeirMarriageCandidate::nativeLegal).toList();
        }
    }
    public static Observation decode(RawJson raw, Binding binding) {
        JsonNode n=parse(raw);
        closed(n,"step","accepted","private_build","read_only","advertised","status","query_sequence",
                "subject_source","subject_character_id","unavailable_reason","family_candidates",
                "arrange_marriage_diagnostics","family_subject_role_mismatches");
        eq(n,"step",STEP); yes(n,"accepted"); yes(n,"private_build"); yes(n,"read_only"); no(n,"advertised");
        eq(n,"subject_source","public_campaign_root_primary_first_heir");
        eq(n,"subject_character_id",BigInteger.valueOf(binding.observedFirstHeir().orElse(-1)));
        String status=text(n,"status"); need(status.equals("available") || status.equals("unavailable"),"family legal status differs");
        boolean available=status.equals("available");
        Availability availability=new Availability(available,available?nullableText(n,"unavailable_reason"):reason(n,"unavailable_reason"));
        List<HeirMarriageCandidate> candidates=list(n,"family_candidates",65536,row->candidate(row,binding));
        unique(candidates.stream().map(HeirMarriageCandidate::character).toList(),65536);
        if(!candidates.isEmpty()) {
            HeirMarriageCandidate first=candidates.getFirst();
            for(HeirMarriageCandidate row:candidates)
                need(Objects.equals(row.heirAdultMeasure(),first.heirAdultMeasure()) &&
                        Objects.equals(row.playerDynasty(),first.playerDynasty()) && Objects.equals(row.heirDynasty(),first.heirDynasty()),
                        "native heir ranking operands changed between enumerated rows");
        }
        return new Observation(binding,positive64(n,"query_sequence"),availability,candidates,
                MarriageDiagnostics.decode(field(n,"arrange_marriage_diagnostics")),
                integer(n,"family_subject_role_mismatches",0,Integer.MAX_VALUE),raw);
    }
    /** Exact original Python public DTO, including the distinct unavailable variant. */
    public static OpportunityJson.Obj project(Observation observation) {
        verifyOriginal(observation); Binding binding=observation.binding();
        ObjectNode nativeValue=parse(observation.original());
        ObjectNode out=F.objectNode().put("schema",SCHEMA).put("schema_version",1)
                .put("exact_ck3_build",binding.context().build().version()).put("exe_sha256",binding.context().build().sha256())
                .put("read_only",true).put("advertised",false).put("status",observation.availability().available()?"available":"unavailable")
                .put("native_revision",binding.context().revision()).put("root_query_sequence",binding.rootQuerySequence());
        if(binding.observedFirstHeir().isPresent()) out.put("observed_first_heir_character_id",binding.observedFirstHeir().getAsLong());
        else out.putNull("observed_first_heir_character_id");
        if(!observation.availability().available()) out.put("unavailable_reason",observation.availability().reason());
        else {
            out.put("query_sequence",observation.querySequence());
            out.set("candidates",nativeValue.get("family_candidates"));
            var legal=out.putArray("native_legal_candidates");
            for(JsonNode row:nativeValue.get("family_candidates")) if(bool(row,"recipient_answer_allows_send")) legal.add(row);
            out.set("diagnostics",nativeValue.get("arrange_marriage_diagnostics"));
            out.put("family_subject_role_mismatches",observation.subjectRoleMismatches());
        }
        return InteractionArguments.app(out);
    }
    public static RawJson verifyOriginal(Observation value) {
        need(decode(value.original(),value.binding()).equals(value),"family legality differs from retained original native packet");
        return value.original();
    }
    private static HeirMarriageCandidate candidate(JsonNode row,Binding binding) {
        need(binding.observedFirstHeir().isPresent(),"candidate row without observed actual title heir");
        return FamilyMarriageCandidateCodec.decodeCompleteCandidate(row,binding.context(),Math.toIntExact(binding.observedFirstHeir().getAsLong()));
    }
}

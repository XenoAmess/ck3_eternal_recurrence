package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.CampaignCadenceCodec;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedCountyMembership;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipCodec;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipInput;
import org.xar.ck3.control.wave2.planning.savedcountymembership.SavedMembershipResult;
import org.xar.ck3.control.wave3.planning.realmmembership.RealmMembershipFeedback;

/**
 * M1 application boundary over the shared production projections. Inputs are the
 * original producer JSON contracts, with no synthesized frame, SAVE or query.
 */
public final class M1ProducerApi {
    private M1ProducerApi() { }

    /** Retains the original geography mapping and founding scope for comparison. */
    public record SavedProjection(SavedMembershipInput input, SavedMembershipResult result) {
        public SavedProjection {
            Objects.requireNonNull(input, "original saved membership input required");
            Objects.requireNonNull(result, "shared membership result required");
            StrictJson.require(input.sourceRef().equals(result.sourceRef())
                    && input.actor().equals(result.actor())
                    && input.house().equals(result.house())
                    && input.dynasty().equals(result.dynasty()), "saved producer/result source scope differs");
        }

        public byte[] wireJson() { return SavedMembershipCodec.encode(result); }
    }

    /** An absent exact slot stays explicit null; it is not an empty observation. */
    public record MonthlyProjection(CampaignCadenceCodec.Candidate request,
            Optional<MonthlyObservation> observation) {
        public MonthlyProjection {
            Objects.requireNonNull(request, "original monthly candidate request required");
            Objects.requireNonNull(observation, "explicit exact-slot presence required");
        }

        public byte[] wireJson() {
            JsonNode result = observation.<JsonNode>map(MonthlyObservation::toJson).orElse(NullNode.instance);
            return StrictJson.canonical(result);
        }
    }

    /** The source SAVE projection has already been obtained; this method does no I/O. */
    public static SavedProjection savedMembership(byte[] originalInputJson) {
        SavedMembershipInput input = SavedMembershipCodec.decode(originalInputJson);
        return new SavedProjection(input, SavedCountyMembership.audit(input));
    }

    /** Keeps the original complete/unavailable branch and all original source frames. */
    public static RealmMembershipFeedback.Result realmFeedback(byte[] originalInputJson) {
        return RealmMembershipFeedback.project(originalInputJson);
    }

    /** Accepts only the existing exact-slot producer operation, never another cadence action. */
    public static MonthlyProjection monthlyObservation(byte[] originalInputJson) {
        CampaignCadenceCodec.Request decoded = CampaignCadenceCodec.decode(originalInputJson);
        StrictJson.require(decoded instanceof CampaignCadenceCodec.Candidate,
                "M1 monthly projection requires ordinary_sample_candidate");
        CampaignCadenceCodec.Candidate request = (CampaignCadenceCodec.Candidate) decoded;
        Optional<MonthlyObservation> observation = MonthlyObservation.fromExistingFrame(request.snapshot(),
                request.startDate(), request.machineId(), request.observedAtUtc(), request.campaignAnchor(), request.months());
        return new MonthlyProjection(request, observation);
    }
}

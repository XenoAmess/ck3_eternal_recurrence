package org.xar.ck3.control.wave3.governance.betrothalvalue;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.ValueFields.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalProposals;

/** Pure original fixed-pair selection; source string matching never grants live runtime qualification. */
public final class BetrothalValuePolicy {
    public static final String RELATION_SCHEMA = "xar.ck3.current-first-heir-relationship.v1";
    private BetrothalValuePolicy() { }

    public static BigInteger pausedActor(Snapshot snapshot) {
        PlayedCharacter played = snapshot.played();
        if (!Boolean.TRUE.equals(snapshot.paused()) || !Boolean.TRUE.equals(snapshot.mapReady()) || played == null
                || !Boolean.TRUE.equals(played.alive()) || !positive(played.characterId()) || !positive(snapshot.nativeRevision())
                || snapshot.dateRaw() == null || snapshot.episodeRunId() == null) { return null; }
        return played.characterId();
    }

    public static Choice evaluate(EvaluationInput input) {
        Snapshot snapshot = input.snapshot(); Relationship relation = input.relationship();
        BigInteger actor = pausedActor(snapshot);
        if (actor == null || !RELATION_SCHEMA.equals(relation.schema()) || !readbackMatches(snapshot, relation)
                || !Objects.equals(relation.nativeRevision(), snapshot.nativeRevision())
                || !Boolean.TRUE.equals(relation.readOnly()) || !Boolean.FALSE.equals(relation.advertised())) {
            throw new ProjectionDomainRejection("betrothal fulfillment observation crossed its formal frame");
        }
        List<Reason> reasons = new ArrayList<>();
        if (!"available".equals(relation.status()) || !Boolean.TRUE.equals(relation.bilateralVerified())) { reasons.add(Reason.CURRENT_PAIR_UNAVAILABLE); }
        if (!positive(relation.heir()) || !positive(relation.partner())) { reasons.add(Reason.NO_CURRENT_BILATERAL_BETROTHAL); }
        if (relation.primarySpouse() != null || relation.spouses().presence() != Presence.VALUE || !relation.spouses().value().isEmpty()) {
            reasons.add(Reason.CURRENT_HEIR_ALREADY_MARRIED);
        }
        ValidatedActionability value = CurrentPairActionabilityValidator.validate(relation.actionability(),
                new Roles(actor, relation.heir(), relation.partner(), null, null));
        if (value.status() != NativeStatus.AVAILABLE) { reasons.add(Reason.CURRENT_PAIR_VALUE_UNKNOWN); }
        if (!Boolean.TRUE.equals(value.adult().ready())) { reasons.add(Reason.ACTUAL_PAIR_NOT_READY); }
        if (!Boolean.TRUE.equals(value.legality().completeCanSend())) { reasons.add(Reason.NATIVE_FINAL_CAN_SEND_NOT_TRUE); }
        BigInteger answer = value.recipient().answerStatusRaw();
        if (!value.recipient().ready() || answer == null || answer.signum() < 0 || answer.compareTo(BigInteger.ONE) > 0
                || !positive(value.recipient().acceptanceRaw())) { reasons.add(Reason.NATIVE_RECIPIENT_NOT_POSITIVE); }
        if (!"marriage".equals(value.projection().predictedOutcomeIfAccepted())) { reasons.add(Reason.NATIVE_OUTCOME_NOT_MARRIAGE); }
        GenericCosts costs = value.projection().costs();
        if (costs == null || costs.amounts().values().stream().anyMatch(amount -> !BigInteger.ZERO.equals(amount.value()))) {
            reasons.add(Reason.NONZERO_OR_UNKNOWN_SEND_COST_REQUIRES_JOINT_BUDGET);
        }
        boolean selected = reasons.isEmpty();
        Relation projected = relation.proposalProjection();
        ResourceProposal resource = BetrothalProposals.build(new BuildInput(projected, snapshot.proposalFrame(), selected,
                reasons.stream().map(Reason::wire).toList()));
        return new Choice(selected ? ChoiceStatus.SELECTED : ChoiceStatus.HELD, reasons, relation.heir(), relation.partner(),
                value, projected.descendants(), projected.descendantsSummary(), resource);
    }

    /** Exact hello content is parsed here; absent legacy hello preserves only the original archival branch. */
    public static ExactBuild nativeBuild(Snapshot snapshot) {
        WireValue diagnostics = get(snapshot.original(), "diagnostics");
        WireValue hello = diagnostics instanceof ObjectValue object ? get(object, "hello") : NullValue.INSTANCE;
        if (!(hello instanceof ObjectValue object)) { return ExactBuild.CK3_11906; }
        WireValue versionValue = object.values().containsKey("expected_ck3_version") ? get(object, "expected_ck3_version") : get(object, "game_version");
        WireValue shaValue = object.values().containsKey("expected_ck3_sha256") ? get(object, "expected_ck3_sha256") : get(object, "executable_sha256");
        String version = nullableText(versionValue), sha = nullableText(shaValue);
        for (ExactBuild build : ExactBuild.values()) {
            if (build.version().equals(version) && sha != null && build.sha256().equals(sha.toUpperCase(Locale.ROOT))) { return build; }
        }
        throw new ProjectionDomainRejection("private nonwar source lacks a frozen exact native build");
    }

    public static boolean readbackMatches(Snapshot snapshot, Relationship readback) {
        ExactBuild build = nativeBuild(snapshot);
        if (!build.version().equals(readback.exactBuild())) { return false; }
        String sha = readback.executableSha256();
        return build == ExactBuild.CK3_11906 && sha == null || sha != null && build.sha256().equals(sha.toUpperCase(Locale.ROOT));
    }

    public static ObjectValue provenance(Snapshot snapshot) {
        ExactBuild build = nativeBuild(snapshot);
        return new ObjectValue(build == ExactBuild.CK3_11906
                ? Map.of("exact_ck3_build", new TextValue(build.version()))
                : Map.of("exact_ck3_build", new TextValue(build.version()), "exe_sha256", new TextValue(build.sha256())));
    }
}

package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Typed original restore metadata. This data alone grants no private Root or saved-pair admission. */
public record ConstructionRestoreProvenance(ExactRef restoreBasis, ExactRef savedMaterial, ExactRef savedBody,
        long savedHeadSequence, String savedHeadSha256, String savedEpisodeRunId, BigInteger savedActorCharacterId,
        GameGeneration replacementGame, String replacementSessionId) {
    private static final Set<String> FIELDS = Set.of("restore_basis", "saved_material", "saved_body", "saved_head_sequence",
            "saved_head_sha256", "saved_episode_run_id", "saved_actor_character_id", "replacement_game", "replacement_session_id");
    public ConstructionRestoreProvenance {
        for (ExactRef source : java.util.List.of(restoreBasis, savedMaterial, savedBody)) {
            Objects.requireNonNull(source); StrictJson.require(source.bytes() > 0, "nonempty original restore source required");
        }
        StrictJson.require(savedHeadSequence >= 0 && savedHeadSequence <= StrictJson.MAX_SAFE_INTEGER,
                "safe exact original saved head sequence required");
        StrictJson.require(savedHeadSha256 != null && savedHeadSha256.matches("[0-9a-f]{64}"), "original saved head SHA-256 required");
        StrictJson.text(savedEpisodeRunId); StrictJson.text(replacementSessionId);
        StrictJson.require(savedActorCharacterId != null && savedActorCharacterId.signum() > 0
                && savedActorCharacterId.compareTo(BigInteger.valueOf(StrictJson.MAX_SAFE_INTEGER)) <= 0,
                "positive safe exact saved actor required");
        Objects.requireNonNull(replacementGame);
    }
    public Obj toJson() {
        return obj("restore_basis", ref(restoreBasis), "saved_material", ref(savedMaterial), "saved_body", ref(savedBody),
                "saved_head_sequence", new IntegerValue(BigInteger.valueOf(savedHeadSequence)), "saved_head_sha256", new Text(savedHeadSha256),
                "saved_episode_run_id", new Text(savedEpisodeRunId), "saved_actor_character_id", new IntegerValue(savedActorCharacterId),
                "replacement_game", object(parse(StrictJson.canonical(replacementGame.toJson())), "actual replacement Game"),
                "replacement_session_id", new Text(replacementSessionId));
    }
    public static ConstructionRestoreProvenance decode(Obj original) {
        Objects.requireNonNull(original);
        StrictJson.require(original.members().keySet().equals(FIELDS), "complete exact construction restoration provenance required");
        return new ConstructionRestoreProvenance(ref(original.get("restore_basis")), ref(original.get("saved_material")),
                ref(original.get("saved_body")), integer(original.get("saved_head_sequence"), "saved head sequence").longValueExact(),
                text(original.get("saved_head_sha256"), "saved head SHA-256"), text(original.get("saved_episode_run_id"), "saved episode"),
                integer(original.get("saved_actor_character_id"), "saved actor"),
                GameGeneration.fromJson(StrictJson.parse(encode(object(original.get("replacement_game"), "replacement Game")))),
                text(original.get("replacement_session_id"), "replacement session"));
    }
    private static Obj ref(ExactRef value) { return object(parse(StrictJson.canonical(value.toJson())), "actual original reference"); }
    private static ExactRef ref(Value value) { return ExactRef.fromJson(StrictJson.parse(encode(object(value, "original reference")))); }
}

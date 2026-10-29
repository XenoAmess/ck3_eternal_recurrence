package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Projection from the same single protected Driver read used by the original SDK validator. */
public record ColdRestoreDriverLineage(long bridgePid, long episodeCharacterId, String episodeRunId,
        ObjectNode successionLifecycle) {
    public ColdRestoreDriverLineage {
        StrictJson.safe(bridgePid,1); StrictJson.require(bridgePid<=0xffff_ffffL,"actual uint32 Windows Game PID"); StrictJson.safe(episodeCharacterId,1); StrictJson.text(episodeRunId);
        successionLifecycle = StrictJson.object(successionLifecycle,Set.of("schema","lifecycle","xar_enabled",
                "pact_contract","source","environment_sha256")).deepCopy();
        StrictJson.require("xar.ck3.succession-lifecycle-binding/v1".equals(StrictJson.text(successionLifecycle.get("schema"))),"original lifecycle schema");
        for (String field:Set.of("lifecycle","pact_contract","source")) { StrictJson.text(successionLifecycle.get(field)); }
        StrictJson.require(successionLifecycle.get("xar_enabled").isNull() || (successionLifecycle.get("xar_enabled").isTextual() && Set.of("xar_on","xar_off").contains(successionLifecycle.get("xar_enabled").textValue())),"original nullable text XAR lifecycle field");
        StrictJson.require(StrictJson.text(successionLifecycle.get("environment_sha256")).matches("[0-9a-f]{64}"),"semantic environment digest");
    }
    @Override public ObjectNode successionLifecycle() { return successionLifecycle.deepCopy(); }
    static ColdRestoreDriverLineage decode(ObjectNode value) {
        StrictJson.object(value,Set.of("schema","format_version","bridge_pid","episode_character_id","episode_run_id","succession_lifecycle"));
        StrictJson.require("xar.original-sdk-cold-restore-lineage/v1".equals(StrictJson.text(value.get("schema"))),"cold restore lineage schema");
        StrictJson.integer(value.get("format_version"),2,2);
        return new ColdRestoreDriverLineage(StrictJson.integer(value.get("bridge_pid"),1,0xffff_ffffL),
                StrictJson.integer(value.get("episode_character_id"),1,StrictJson.MAX_SAFE_INTEGER),
                StrictJson.text(value.get("episode_run_id")),StrictJson.object(value.get("succession_lifecycle"),Set.of("schema","lifecycle","xar_enabled","pact_contract","source","environment_sha256")));
    }
    public ObjectNode toJson() {
        var value=StrictJson.object(); value.put("schema","xar.original-sdk-cold-restore-lineage/v1");
        value.put("format_version",2); value.put("bridge_pid",bridgePid); value.put("episode_character_id",episodeCharacterId);
        value.put("episode_run_id",episodeRunId); value.set("succession_lifecycle",successionLifecycle()); return value;
    }
}

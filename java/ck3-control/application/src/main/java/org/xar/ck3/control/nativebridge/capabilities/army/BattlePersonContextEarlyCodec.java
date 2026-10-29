package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;

/** The six assigned exact source-input leaves; remaining leaves have other unique owners. */
final class BattlePersonContextEarlyCodec {
    private BattlePersonContextEarlyCodec() { }
    static JsonNode normalize(BattlePersonExternalCodec.Leaf leaf,JsonNode raw,String field) {
        return switch(leaf) {
            case TRAIT_STAGE_291D460 -> BattleTraitStageCodec.normalize(raw,field);
            case ABSENT_RECIPIENT_INPUTS -> BattleRecipientInputsCodec.absent(raw,field);
            case HELPER_2922070 -> Battle2922070Codec.normalize(raw,field);
            case CONFERENCE_24B1D00 -> BattleConferenceCodec.normalize(raw,field);
            case UNCACHED_RECIPIENT_INPUTS -> BattleRecipientInputsCodec.uncached(raw,field);
            case PROVIDER_BUCKET_291C5B2 -> BattleProviderBucketCodec.normalize(raw,field);
            default -> throw bad(field,"leaf belongs to another source owner: "+leaf);
        };
    }
    static ObjectNode traitGroup(JsonNode raw,String field,ObjectNode normalizedSelectorsStage) {
        return BattleTraitStageCodec.group(raw,field,normalizedSelectorsStage);
    }
    static ObjectNode traitKeyset(JsonNode raw,String field,int index) {
        return BattleTraitStageCodec.keyset(raw,field,index);
    }
}

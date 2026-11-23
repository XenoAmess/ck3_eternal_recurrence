package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete physical own-law DATA, not effective/realm inheritance or a D5 execute-time heir witness. */
public record CurrentRmtmTitleQuerySource(int actorId,long fullTitleId,Optional<CharacterRef> holder,Optional<CharacterRef> engineCurrentHeir,
        int nativeLawCount,List<Law> physicalOwnLaws,int engineSuccessorCount,boolean sampledTwice) {
    public record CharacterRef(long fullId,boolean alive){public CharacterRef{CurrentRmtmTitleQuery.requireFullId(fullId);}}
    public record Law(long nativeDefinitionId,String key){public Law{CurrentRmtmTitleQuery.requireFullId(nativeDefinitionId);Objects.requireNonNull(key);
        StrictJson.require(key.length()>=1&&key.length()<=256&&key.matches("[A-Za-z0-9_.:-]+"),"Actual ASCII law key required");}}
    public CurrentRmtmTitleQuerySource {
        StrictJson.require(actorId!=-1,"Packed actor sentinel invalid");CurrentRmtmTitleQuery.requireFullId(fullTitleId);Objects.requireNonNull(holder);Objects.requireNonNull(engineCurrentHeir);
        physicalOwnLaws=List.copyOf(physicalOwnLaws);StrictJson.require(sampledTwice,"Available title Source requires two actual samples");
        StrictJson.require(nativeLawCount>=0&&nativeLawCount<=64&&nativeLawCount==physicalOwnLaws.size(),"Complete physical law count differs");
        StrictJson.require(engineSuccessorCount>=0&&engineSuccessorCount<=4096&&(engineSuccessorCount==0)==engineCurrentHeir.isEmpty(),"Exact successor-count/current-heir nullable roles differ");
        var ids=new HashSet<Long>();var keys=new HashSet<String>();for(var law:physicalOwnLaws)StrictJson.require(ids.add(law.nativeDefinitionId())&&keys.add(law.key()),"Duplicate physical law ID/key");
    }
    private static Optional<CharacterRef> character(JsonNode n)throws IOException{if(n.isNull())return Optional.empty();var row=StrictJson.object(n,Set.of("full_id","alive"));return Optional.of(new CharacterRef(CurrentRmtmTitleQuery.fullId(row.get("full_id")),CurrentRmtmTitleQuery.bool(row,"alive")));}
    public static CurrentRmtmTitleQuerySource decode(JsonNode node)throws IOException{
        try{var n=StrictJson.object(node,Set.of("schema","actor_id","full_title_id","holder","engine_current_heir","native_law_count","physical_own_laws","engine_successor_count","sampled_twice"));
            CurrentRmtmTitleQuery.identity(n,"schema",CurrentRmtmTitleQuery.SOURCE_SCHEMA);var values=n.get("physical_own_laws");if(!values.isArray()||values.size()>64)throw new IOException("Bounded complete physical own-law array required");
            var laws=new ArrayList<Law>();for(var value:values){var row=StrictJson.object(value,Set.of("native_definition_id","key"));laws.add(new Law(CurrentRmtmTitleQuery.fullId(row.get("native_definition_id")),NativeWire.text(row.get("key"))));}
            return new CurrentRmtmTitleQuerySource(CurrentRmtmTitleQuery.i32(n.get("actor_id")),CurrentRmtmTitleQuery.fullId(n.get("full_title_id")),character(n.get("holder")),character(n.get("engine_current_heir")),
                    NativeWire.integer(n.get("native_law_count"),BigInteger.ZERO,BigInteger.valueOf(64)).intValueExact(),laws,
                    NativeWire.integer(n.get("engine_successor_count"),BigInteger.ZERO,BigInteger.valueOf(4096)).intValueExact(),CurrentRmtmTitleQuery.bool(n,"sampled_twice"));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact RMTM physical title Source",invalid);}
    }
    private static void character(ObjectNode n,String key,Optional<CharacterRef> value){if(value.isEmpty())n.putNull(key);else{var actual=value.orElseThrow();n.putObject(key).put("full_id",actual.fullId()).put("alive",actual.alive());}}
    public ObjectNode encode(){var n=StrictJson.object().put("schema",CurrentRmtmTitleQuery.SOURCE_SCHEMA).put("actor_id",actorId).put("full_title_id",fullTitleId);
        character(n,"holder",holder);character(n,"engine_current_heir",engineCurrentHeir);n.put("native_law_count",nativeLawCount);var rows=n.putArray("physical_own_laws");for(var law:physicalOwnLaws)rows.addObject().put("native_definition_id",law.nativeDefinitionId()).put("key",law.key());
        return n.put("engine_successor_count",engineSuccessorCount).put("sampled_twice",sampledTwice);}
}

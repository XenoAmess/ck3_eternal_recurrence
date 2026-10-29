package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Objects;

/** Original stable first-occurrence joins over the complete shared army and war models. No extra native read. */
public final class ArmyStateProjection {
    private ArmyStateProjection() { }
    public static List<NativeArmiesCodec.Army> playerArmiesFromState(List<NativeActiveWarsCodec.War> activeWars, JsonNode explicitPlayerArmies) {
        List<NativeArmiesCodec.Army> rows = new ArrayList<>();
        if (explicitPlayerArmies != null && !explicitPlayerArmies.isNull()) rows.addAll(NativeArmiesCodec.normalize(explicitPlayerArmies, "player_armies"));
        for (var war : List.copyOf(activeWars)) for (var army : war.alliedArmies()) if (army.controllable()) rows.add(army);
        return deduplicate(rows);
    }
    public static List<NativeArmiesCodec.Army> enemyArmiesFromWars(List<NativeActiveWarsCodec.War> activeWars) {
        List<NativeArmiesCodec.Army> rows = new ArrayList<>();
        for (var war : List.copyOf(activeWars)) rows.addAll(war.enemyArmies());
        return deduplicate(rows);
    }
    public static List<NativeArmiesCodec.Army> controllable(List<NativeArmiesCodec.Army> armies) {
        return List.copyOf(armies).stream().filter(NativeArmiesCodec.Army::controllable).toList();
    }
    public static List<NativeArmiesCodec.Army> deduplicate(List<NativeArmiesCodec.Army> armies) {
        var first = new LinkedHashMap<ArmyTypes.PublicUnitId,NativeArmiesCodec.Army>();
        for (var army : List.copyOf(armies)) first.putIfAbsent(Objects.requireNonNull(army).armyId(), army);
        return List.copyOf(first.values());
    }
}


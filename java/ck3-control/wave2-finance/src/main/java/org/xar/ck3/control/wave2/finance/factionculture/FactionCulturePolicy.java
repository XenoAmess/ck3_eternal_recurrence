package org.xar.ck3.control.wave2.finance.factionculture;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

import static org.xar.ck3.control.wave2.finance.factionculture.FactionCultureModel.*;

/** Preserves faction/county order and the original last observation for a repeated county. */
public final class FactionCulturePolicy {
    private FactionCulturePolicy() { }

    public static Context project(AlertProjection alert) {
        Objects.requireNonNull(alert, "alert");
        List<ContextRow> rows = new ArrayList<>();
        for (FactionProjection faction : alert.factions()) {
            Map<Integer, CountyMaterial> materialByCounty = new HashMap<>();
            for (CountyMaterial material : faction.materials()) materialByCounty.put(material.countyTitleId(), material);
            for (int countyId : faction.countyTitleIds()) {
                CountyMaterial material = materialByCounty.get(countyId);
                Optional<CultureRelation> relation = material == null ? Optional.empty() : material.relation();
                Optional<UnavailableReason> reason;
                if (relation.filter(AvailableCulture.class::isInstance).isPresent()) reason = Optional.empty();
                else if (relation.isPresent()) reason = Optional.of(UnavailableReason.CULTURE_RELATION_UNAVAILABLE);
                else reason = Optional.of(material == null ? UnavailableReason.COUNTY_MEMBER_OBSERVATION_NOT_PUBLISHED
                        : UnavailableReason.CULTURE_FIELDS_NOT_PUBLISHED);
                rows.add(new ContextRow(faction.factionId(), faction.factionTypeKey(), faction.targetCharacterId(),
                        countyId, relation, reason));
            }
        }
        return new Context(alert.frame(), alert.provenance(), rows);
    }
}

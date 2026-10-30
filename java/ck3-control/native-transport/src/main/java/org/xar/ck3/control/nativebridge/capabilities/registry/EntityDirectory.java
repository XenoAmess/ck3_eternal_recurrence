package org.xar.ck3.control.nativebridge.capabilities.registry;

import org.xar.ck3.control.contracts.NativeCharacterId;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import static org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;

/** Direct port of entity_directory_contract.build_entity_directory_v1; no native RPC or policy. */
public final class EntityDirectory {
    public static final String SCHEMA = "xar.ck3.entity-directory/v1";
    public record Request(Relation relationFilter, Integer afterCharacterId, int limit) {
        public Request { java.util.Objects.requireNonNull(relationFilter); if (afterCharacterId != null) NativeCharacterId.of(afterCharacterId); RegistryJson.require(limit >= 1 && limit <= 100, "directory limit 1..100 required"); }
    }
    public record Entity(String entityKind, int characterId, List<Relation> relationshipRoles,
            Component<Title> primaryTitle, Component<Integer> capitalProvinceId,
            Component<Integer> immediateLiegeCharacterId, Component<Integer> topLiegeCharacterId) {
        public Entity { relationshipRoles = List.copyOf(relationshipRoles); }
    }
    public record Readiness(boolean identityReady, boolean relationshipReady, boolean primaryTitleComponentsComplete,
            boolean realmIdentityComponentsComplete, boolean ready) { }
    public record Result(String schema, Status status, java.math.BigInteger snapshotRevision, int dateRaw,
            Relation relationFilter, Integer afterCharacterId, int limit, List<Entity> entities,
            Integer nextAfterCharacterId, int totalMatchingCount, Readiness readiness, String unavailableReason, Source source) {
        public Result { entities = List.copyOf(entities); }
    }
    private EntityDirectory() { }
    public static Result build(Root root, Request request) {
        java.util.Objects.requireNonNull(root); java.util.Objects.requireNonNull(request);
        if (root instanceof UnavailableRoot unavailable) return new Result(SCHEMA, Status.UNAVAILABLE,
                root.binding().nativeRevision(), root.binding().dateRaw(), request.relationFilter(), request.afterCharacterId(),
                request.limit(), List.of(), null, 0, new Readiness(false,false,false,false,false), unavailable.unavailableReason(), root.source());
        AvailableRoot value = (AvailableRoot) root; List<Entity> all = new ArrayList<>();
        all.add(entity(value.playerCharacterId(), Relation.SELF, value.primaryTitle(), value.capitalProvinceId(),
                value.immediateLiegeCharacterId(), value.topLiegeCharacterId()));
        for (Related related : value.relatedCharacterContexts()) all.add(entity(related.characterId(), related.relationshipRole(),
                related.primaryTitle(), related.capitalProvinceId(), related.immediateLiegeCharacterId(), related.topLiegeCharacterId()));
        all.sort(Comparator.comparingInt(Entity::characterId));
        RegistryJson.require(all.stream().map(Entity::characterId).distinct().count() == all.size(), "root relationship identities overlap");
        List<Entity> matching = all.stream().filter(row -> request.relationFilter() == Relation.ANY
                || row.relationshipRoles().contains(request.relationFilter())).toList();
        List<Entity> remaining = matching.stream().filter(row -> request.afterCharacterId() == null || row.characterId() > request.afterCharacterId()).toList();
        List<Entity> page = remaining.stream().limit(request.limit()).toList();
        Integer next = !page.isEmpty() && remaining.size() > page.size() ? page.getLast().characterId() : null;
        boolean titles = all.stream().allMatch(row -> row.primaryTitle().status() != Status.UNAVAILABLE);
        boolean realm = all.stream().allMatch(row -> row.topLiegeCharacterId().status() != Status.UNAVAILABLE);
        return new Result(SCHEMA, Status.AVAILABLE, root.binding().nativeRevision(), root.binding().dateRaw(),
                request.relationFilter(), request.afterCharacterId(), request.limit(), page, next, matching.size(),
                new Readiness(true,true,titles,realm,true), null, root.source());
    }
    private static Entity entity(int id, Relation relation, Title title, Integer capital, Integer immediate, int top) {
        return new Entity("character", id, List.of(relation),
                title == null ? Component.notApplicable("landless_or_no_primary_title") : Component.available(title),
                capital == null ? Component.notApplicable("no_current_capital") : Component.available(capital),
                immediate == null ? Component.notApplicable("independent") : Component.available(immediate), Component.available(top));
    }
}


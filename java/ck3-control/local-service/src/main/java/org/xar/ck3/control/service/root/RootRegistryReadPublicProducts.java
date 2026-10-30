package org.xar.ck3.control.service.root;

import org.xar.ck3.control.contracts.NativeCharacterId;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.CampaignProjection.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.RegistryCampaignProjection.PendingObject;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Context;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Contribution;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Two public read products. There is one installed ROOT native producer and no retained pre-Core service. */
public final class RootRegistryReadPublicProducts {
    static final Set<PublicMethod> METHODS = Set.of(PublicMethod.SEARCH_ENTITIES_V1, PublicMethod.QUERY_TURN_BUNDLE_V1);
    public record SearchRequest(BigInteger expectedRevision, EntityDirectory.Request directory) {
        public SearchRequest { revision(expectedRevision); Objects.requireNonNull(directory); }
    }
    public record BundleRequest(BigInteger expectedRevision) { public BundleRequest { revision(expectedRevision); } }
    public record DirectoryReply(EntityDirectory.Result directory) { public DirectoryReply { Objects.requireNonNull(directory); } }
    public record BundleReply(TurnBundle.Result<PendingObject,PendingObject> bundle) { public BundleReply { Objects.requireNonNull(bundle); } }
    /** Immutable data seam used by both registered handlers, never a Native permission or a constructed Root. */
    record Material(Root root, Obj snapshot) {
        Material {
            Objects.requireNonNull(root); Objects.requireNonNull(snapshot);
        }
    }
    @FunctionalInterface interface Current { Material read(BigInteger expectedRevision) throws InterruptedException; }
    private RootRegistryReadPublicProducts() { }

    public static Contribution install(Context context, PublicBindings registry) throws IOException {
        Objects.requireNonNull(context); Objects.requireNonNull(registry);
        ExactRef source;
        try {
            source = context.source(RootRegistryReadPublicProducts.class);
            context.source(RootTurnBundleReadSource.class);
            for (Class<?> producer : List.of(CampaignProjection.class, RegistryCampaignProjection.class,
                    EntityDirectory.class, TurnBundle.class, RegistryWire.class,RegistryPublicProfile.class)) context.source(Module.NATIVE_TRANSPORT, producer);
            context.source(Module.APPLICATION, FinanceReadContracts.class);
            context.source(Module.APPLICATION, CampaignRootContextJson.class);
        } catch (IOException missing) {
            var gaps = new ArrayList<RootRuntimePublicCatalog.DefinitionGap>();
            for (PublicMethod method : METHODS) gaps.add(new RootRuntimePublicCatalog.DefinitionGap(method.pythonName(),
                    "actual ROOT/registry typed producer source closure unavailable: " + missing.getMessage()));
            return new Contribution(List.of(), List.of(), gaps);
        }
        register(registry, source, new ActualCurrent(context));
        return new Contribution(List.of(), List.of(), List.of());
    }

    static void register(PublicBindings registry, ExactRef source, Current current) {
        Objects.requireNonNull(registry); Objects.requireNonNull(source); Objects.requireNonNull(current);
        StrictJson.require(registry.coverage().installed().stream().noneMatch(METHODS::contains),
                "registry reads already have another public producer");
        registry.register(PublicMethod.SEARCH_ENTITIES_V1, SearchRequest.class, DirectoryReply.class,
                input -> new DirectoryReply(EntityDirectory.build(current.read(input.expectedRevision()).root(), input.directory())),
                RootRegistryReadPublicProducts::decodeSearch, result -> RegistryWire.encodePublicDirectory(result.directory()),
                target(source, "search_entities_v1"), PublicRoutes.Status.IMPLEMENTED,
                "current physical Root; sole installed ROOT v2 public read, original archived native receipt, exact same public/native/date frame and typed keyset directory");
        registry.register(PublicMethod.QUERY_TURN_BUNDLE_V1, BundleRequest.class, BundleReply.class,
                input -> { Material actual = current.read(input.expectedRevision());
                    return new BundleReply(RootTurnBundleReadSource.aggregate(actual.root(), actual.snapshot())); },
                RootRegistryReadPublicProducts::decodeBundle, result -> RegistryWire.encodePublicBundle(result.bundle()),
                target(source, "query_turn_bundle_v1"), PublicRoutes.Status.IMPLEMENTED,
                "current physical Root; one held complete snapshot and sole installed ROOT v2 original; missing/null, partial council, territory and vitals remain explicit");
    }
    private static PublicRoutes.Target target(ExactRef source, String method) {
        return new PublicRoutes.Target(RootRegistryReadPublicProducts.class.getName(), method, source);
    }
    static SearchRequest decodeSearch(PublicBindings.Arguments arguments) {
        ObjectNode fields = arguments(arguments);
        names(fields, Set.of("expected_revision", "relation_filter", "after_character_id", "limit"));
        BigInteger expected = RegistryPublicProfile.revision(required(fields, "expected_revision"));
        Relation relation = Relation.ANY;
        if (fields.has("relation_filter")) {
            JsonNode raw = fields.get("relation_filter");
            StrictJson.require(raw.isTextual(), "relation_filter must be a finite relation string");
            relation = switch (raw.textValue()) {
                case "any" -> Relation.ANY; case "self" -> Relation.SELF;
                case "direct_landed_vassal" -> Relation.DIRECT_LANDED_VASSAL;
                case "adjacent_external_province_holder" -> Relation.ADJACENT_EXTERNAL_PROVINCE_HOLDER;
                default -> throw new IllegalArgumentException("unknown relation_filter");
            };
        }
        Integer after = !fields.has("after_character_id") || fields.get("after_character_id").isNull() ? null
                : NativeCharacterId.fromJson(fields.get("after_character_id")).value();
        int limit = fields.has("limit") ? number(fields.get("limit"), BigInteger.ONE, BigInteger.valueOf(100), "limit").intValueExact() : 50;
        return new SearchRequest(expected, new EntityDirectory.Request(relation, after, limit));
    }
    static BundleRequest decodeBundle(PublicBindings.Arguments arguments) {
        ObjectNode fields = arguments(arguments); names(fields, Set.of("expected_revision"));
        return new BundleRequest(RegistryPublicProfile.revision(required(fields, "expected_revision")));
    }
    private static ObjectNode arguments(PublicBindings.Arguments arguments) {
        if (!(arguments instanceof PublicBindings.Value actual))
            throw new IllegalArgumentException("registry public reads require named arguments; missing and null are distinct invalid inputs");
        JsonNode parsed = StrictJson.parse(actual.original().bytes(), 65_536);
        StrictJson.require(parsed instanceof ObjectNode, "named registry public arguments must be a JSON object");
        return (ObjectNode) parsed;
    }
    private static void names(ObjectNode fields, Set<String> allowed) {
        fields.fieldNames().forEachRemaining(name -> StrictJson.require(allowed.contains(name), "unknown registry public argument: " + name));
    }
    private static JsonNode required(ObjectNode fields, String key) {
        StrictJson.require(fields.has(key), "missing registry public argument: " + key); return fields.get(key);
    }
    private static BigInteger number(JsonNode raw, BigInteger low, BigInteger high, String name) {
        StrictJson.require(raw != null && raw.isIntegralNumber(), name + " must be an exact JSON integer");
        BigInteger result = raw.bigIntegerValue();
        StrictJson.require(result.compareTo(low) >= 0 && (high == null || result.compareTo(high) <= 0), name + " outside its exact range"); return result;
    }
    private static void revision(BigInteger value) {
        StrictJson.require(value != null && value.signum() >= 0, "nonnegative exact public revision required");
    }

    private static final class ActualCurrent implements Current {
        private final Context context;
        ActualCurrent(Context context) { this.context = Objects.requireNonNull(context); }
        @Override public Material read(BigInteger expectedRevision) throws InterruptedException {
            revision(expectedRevision); Instant deadline = context.clock().instant().plus(context.observationTimeout());
            try { return context.withCurrent(root -> root.withPublicObservation(deadline, (frame, driver, same) -> {
                var installed = context.installed(root); var runtime = installed.context(); runtime.writer().requireSession(same);
                StrictJson.require(frame.identity().frame().revision().equals(expectedRevision),
                        "registry public expected_revision differs from the actual current complete frame");
                var actual = installed.interactions().turnBundleSourceFor(runtime).readRoot(same, frame, deadline);
                return new Material(actual.root(), actual.frame().semantic());
            })); } catch (IOException missing) { throw new UncheckedIOException("actual current Root registry read unavailable", missing); }
        }
    }
}

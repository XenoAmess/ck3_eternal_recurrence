package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.EnumMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.RootReadContractCatalog;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;

/** Root-installed finite factories for actual guarded reads. This is not a general execute-step endpoint. */
public final class ArmyClosedReadContracts {
    public static final Set<PublicMethod> METHODS = Set.of(PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,
            PublicMethod.QUERY_PLAYER_TRUCE_EXPIRY_V1, PublicMethod.QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1);
    public record Selection(ArmyCalls.Call input, Context context) {
        public Selection {
            Objects.requireNonNull(input); Objects.requireNonNull(context);
            require(METHODS.contains(input.method()), "this Army producer is not migrated");
            input.revision().requireCurrent(context.before().frame().revision());
        }
    }
    private final EnumMap<PublicMethod,RootReadContractCatalog.Family<Selection,ArmyClosedReads.Observation>> families = new EnumMap<>(PublicMethod.class);
    public ArmyClosedReadContracts(ExactRef definitionSource, ExactRef decoderSource) {
        Objects.requireNonNull(definitionSource); Objects.requireNonNull(decoderSource);
        for (PublicMethod method : METHODS) {
            String capability = switch (method) {
                case QUERY_PLAYER_DEFAULT_RAISE_V1 -> "game.command.query-player-default-raise-v1";
                case QUERY_PLAYER_TRUCE_EXPIRY_V1 -> "game.command.query-raiktor-actual-truce-expiry-v1-N";
                case QUERY_ARMY_GATHERING_RESEARCH_SAMPLING_V1 -> "game.command.query-army-strengths-v1";
                default -> throw new IllegalArgumentException("unmigrated Army read");
            };
            families.put(method, new RootReadContractCatalog.Family<>("army-closed-read-" + method.pythonName(), Selection.class,
                    ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, Optional.of(capability), definitionSource, decoderSource,
                    ArmyClosedReadContracts::key, selection -> operation(selection, method), selection -> {
                        var primitive = primitive(selection, method);
                        return new ReadContract<>("army-closed-read-" + method.pythonName() + "-" + digest(key(selection).bytes()),
                                operation(selection, method), Optional.of(capability), primitive.permissionKey(), ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                                primitive.wire(), ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource, (request, requestId) -> {
                                    verify(request, selection); return primitive.request();
                                }, receipt -> decode(selection,receipt), receipt -> decode(selection,receipt),
                                (original,value,current,semantic) -> ArmyNativeReadEvidence.requireCanonicalEquivalent(original,current));
                    }));
        }
    }
    public List<RootReadContractCatalog.Family<?,?>> families() { return families.values().stream().<RootReadContractCatalog.Family<?,?>>map(family -> family).toList(); }
    public ReadContract<ArmyClosedReads.Observation> issue(RootReadContractCatalog installed, Selection selection) {
        Objects.requireNonNull(installed); Objects.requireNonNull(selection);
        return installed.issue(Objects.requireNonNull(families.get(selection.input().method())), selection);
    }
    public PlanningReadRequest request(Selection selection) {
        var context = selection.context(); var primitive = primitive(selection, selection.input().method());
        return new PlanningReadRequest(context.before(), context.source(), context.sessionId(), new OperationKey(primitive.request().step()),
                OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(selection.input()).bytes()), "Army public arguments"), context.deadline());
    }
    private static ArmyClosedReads.Observation decode(Selection selection, org.xar.ck3.control.application.action.PlanningReadReceipt receipt) {
        verify(receipt.request(),selection); return ArmyClosedReadCodec.decode(selection.input(),ArmyNativeReadEvidence.contextForRequest(selection.context(),receipt.request()),receipt);
    }
    private static ArmyNativeRecipes.Primitive primitive(Selection selection, PublicMethod method) {
        require(selection.input().method() == method, "Army dynamic family method mismatch");
        var recipe = ArmyNativeRecipes.prepare(selection.input(), selection.context(), new ArmyNativeRecipes.NoFacts(), false);
        require(recipe instanceof ArmyNativeRecipes.Primitive, "local/composite Army methods cannot become Native read steps");
        var primitive = (ArmyNativeRecipes.Primitive) recipe;
        require(primitive.effect() == ArmyNativeRecipes.Effect.READ_ONLY, "Army mutation and capture controls require the sole action authority");
        return primitive;
    }
    private static OperationKey operation(Selection selection, PublicMethod method) { return new OperationKey(primitive(selection, method).request().step()); }
    private static void verify(PlanningReadRequest request, Selection selection) {
        Context expected = selection.context();
        require(request.before().equals(expected.before()) && request.source().equals(expected.source())
                && request.sessionId().equals(expected.sessionId()), "Army read contract crossed its complete selected context");
        require(OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(selection.input()).bytes()), "Army arguments").equals(request.arguments()), "Army read arguments differ from their typed public request");
    }
    /** Include provenance, Game identity and episode; each invocation retains its separate actual deadline. */
    private static RawJson key(Selection selection) {
        Context c = selection.context(); var f = c.before().frame(); var source = c.source();
        var n = empty().put("method", selection.input().method().pythonName()).put("machine_id", c.before().machineId()).put("session_id", c.sessionId())
                .put("snapshot_id", f.snapshotId()).put("public_revision", f.revision().toString()).put("native_revision", c.nativeRevision().toString())
                .put("date_raw", c.dateRaw().toString()).put("player", c.playerId().toString())
                .put("episode", f.episodeRunId()).put("observation_version", c.before().observationVersion()).put("source_observed_at_utc", source.observedAtUtc()).put("source_exact_build", source.exactBuild());
        n.set("game", c.before().game().toJson()); n.set("source_ref", source.sourceRef().toJson()); n.set("public_arguments", parse(ArmyCallCodec.encode(selection.input()).bytes()));
        return new RawJson(bytes(n));
    }
    private static String digest(byte[] original) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException("SHA256 unavailable", impossible); }
    }
}

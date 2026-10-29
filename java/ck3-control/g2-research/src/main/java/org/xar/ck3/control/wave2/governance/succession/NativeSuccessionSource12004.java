package org.xar.ck3.control.wave2.governance.succession;

import static org.xar.ck3.control.wave2.governance.succession.NativeSuccessionObservation12004.*;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.check;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.RetainedArtifact;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.RootOwnedSources;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Reads only the exact retained originals selected by the existing Root owner. No native RPC. */
public final class NativeSuccessionSource12004 {
    private static final ObjectMapper EXTRACTION = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    public record Request(ExactRef rootResult, ExactRef turnBundle) {
        public Request { Objects.requireNonNull(rootResult); Objects.requireNonNull(turnBundle); }
    }
    public sealed interface Result permits Observed, Rejected { }
    public record Observed(Frame frame) implements Result { public Observed { Objects.requireNonNull(frame); } }
    public record Rejected(Reason reason, String detail) implements Result {
        public Rejected { Objects.requireNonNull(reason); StrictJson.text(detail); }
    }
    private NativeSuccessionSource12004() { }

    public static Result read(RootOwnedSources owner, G2RetainedNativeSourceProvider.Limits limits, Request request) {
        Objects.requireNonNull(owner); Objects.requireNonNull(limits); Objects.requireNonNull(request);
        ObjectNode token = StrictJson.object(); token.put("schema", "xar.java.native-succession-source-request12004/v1");
        token.set("root_result", request.rootResult().toJson()); token.set("turn_bundle", request.turnBundle().toJson());
        ProjectionJson payload = ProjectionJson.object(StrictJson.canonical(token), 16384);
        try {
            Optional<RetainedArtifact> selected = owner.selectedSource(Milestone.M3, payload);
            if (selected.isEmpty()) { return rejected(Reason.ROOT_SOURCE_UNAVAILABLE, "Root has no retained M3 native snapshot"); }
            RetainedArtifact artifact = selected.orElseThrow();
            G2RetainedNativeSourceProvider provider = new G2RetainedNativeSourceProvider(owner, limits);
            G2CallContextProducer.Result qualified = provider.context(Milestone.M3, payload);
            if (qualified instanceof G2CallContextProducer.Unavailable unavailable) {
                return rejected(Reason.ROOT_SOURCE_UNAVAILABLE, unavailable.reason() + ":" + unavailable.detail());
            }
            G2CallContextProducer.Context context = ((G2CallContextProducer.Available) qualified).context();
            check(context.source().sourceRef().equals(artifact.nativeObservation()), "selected native source changed");
            byte[] original = exact(owner, artifact.nativeObservation(), limits.nativeArtifactBytes());
            // These same immutable owner-row bytes already passed the shared strict UTF8/duplicate/token validator.
            JsonNode ownerRow = EXTRACTION.readTree(original);
            JsonNode snapshotWire = ownerRow.path("result").path("structured_content");
            check(snapshotWire.isObject(), "original semantic snapshot object required");
            byte[] rootBytes = exact(owner, request.rootResult(), SuccessionCodec.MAX_BYTES);
            byte[] bundleBytes = exact(owner, request.turnBundle(), SuccessionCodec.MAX_BYTES);
            JsonNode rootResult = SuccessionCodec.parse(rootBytes);
            JsonNode bundleWire = SuccessionCodec.parse(bundleBytes);
            Frame frame = frame(artifact, context, request, snapshotWire, rootResult, bundleWire);
            check(Arrays.equals(rootBytes, exact(owner, request.rootResult(), SuccessionCodec.MAX_BYTES))
                    && Arrays.equals(bundleBytes, exact(owner, request.turnBundle(), SuccessionCodec.MAX_BYTES))
                    && Arrays.equals(original, exact(owner, artifact.nativeObservation(), limits.nativeArtifactBytes())),
                    "original sources changed during reading");
            check(owner.currentSession().equals(Optional.of(artifact.retainedSession()))
                    && owner.selectedSource(Milestone.M3, payload).equals(selected), "Root session/selection changed");
            return new Observed(frame);
        } catch (IOException | IllegalArgumentException failure) {
            String detail = failure.getMessage() == null ? "native succession source rejected" : failure.getMessage();
            return rejected(Reason.SOURCE_REJECTED, detail);
        }
    }

    private static Frame frame(RetainedArtifact artifact, G2CallContextProducer.Context context, Request request,
                               JsonNode snapshotWire, JsonNode rootResult, JsonNode bundleWire) {
        SuccessionModel.Snapshot snapshot = SuccessionCodec.snapshot(snapshotWire);
        check(snapshot != null && snapshot.frame() != null && snapshot.actor() != null
                && snapshot.actor().alive() && Boolean.TRUE.equals(snapshot.paused())
                && Boolean.TRUE.equals(snapshot.mapReady()), "current paused living played actor required");
        SuccessionModel.TurnBundle bundle = SuccessionCodec.turnBundle(bundleWire, true);
        check(snapshot.frame().equals(bundle.frame()), "snapshot and original turn bundle crossed frames");
        JsonNode root = field(rootResult, "campaign_root_context");
        check("available".equals(text(rootResult, "status")) && "available".equals(text(root, "status")),
                "available completed native root required");
        check(SuccessionCodec.frame(field(rootResult, "binding"), false).equals(snapshot.frame()), "root public frame differs");
        check(StrictJson.integer(field(root, "snapshot_revision"), BigInteger.ONE, StrictJson.UINT64_MAX)
                .equals(snapshot.frame().nativeRevision())
                && StrictJson.integer(field(root, "date_raw"), Integer.MIN_VALUE, Integer.MAX_VALUE) == snapshot.frame().dateRaw(),
                "native root revision/date differs");
        check(NativeCharacterId.fromJson(field(root, "player_character_id")).value() == snapshot.actor().characterId()
                && field(root, "player_character_alive").isBoolean() && field(root, "player_character_alive").booleanValue(),
                "native root played actor differs");
        StrictJson.trueValue(field(field(root, "readiness"), "held_title_partition_ready"));
        JsonNode partition = field(field(field(field(bundleWire, "succession_state"), "value"), "partition"), "value");
        check(field(partition, "title_heirs").equals(field(root, "held_title_partition")), "full native partition differs from bundle");
        BigInteger query = StrictJson.integer(field(rootResult, "query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX);
        JsonNode source = field(bundleWire, "source");
        check("game.command.query-campaign-root-context-v1".equals(text(source, "capability"))
                && query.equals(StrictJson.integer(field(source, "query_sequence"), BigInteger.ONE, StrictJson.UINT64_MAX))
                && Objects.equals(field(source, "backend_id"), snapshotWire.get("backend_id")), "bundle/root source provenance differs");
        JsonNode heirs = field(root, "primary_title_succession_character_ids");
        check(heirs.isArray(), "ordered native heir vector required");
        Integer first = heirs.isEmpty() ? null : NativeCharacterId.fromJson(heirs.get(0)).value();
        check(Objects.equals(first, bundle.primaryHeirCharacterId()), "native primary heir differs from bundle");
        JsonNode government = field(root, "government");
        JsonNode governmentComponent = field(field(field(bundleWire, "ruler_state"), "value"), "government");
        if (government.isObject()) {
            check("available".equals(text(governmentComponent, "status"))
                    && government.equals(field(governmentComponent, "value")), "government root/bundle observation differs");
        } else {
            check(government.isNull() && field(governmentComponent, "value").isNull()
                    && !"available".equals(text(governmentComponent, "status")), "missing government cannot be promoted to observed");
        }
        ProjectionJson observedGovernment = government.isNull() ? null
                : ProjectionJson.object(SuccessionCodec.encode(government), SuccessionCodec.MAX_BYTES);
        return new Frame(new Proof(artifact.retainedSession(), context.source(), request.rootResult(), request.turnBundle()),
                snapshot, bundle, SuccessionLifecycleCodec.decode(SuccessionCodec.encode(field(snapshotWire, "succession_lifecycle"))),
                NativeSuccessionObservation12004.goal(snapshotWire.get("campaign_goal")), observedGovernment);
    }

    private static byte[] exact(RootOwnedSources owner, ExactRef reference, int maximum) throws IOException {
        check(reference.bytes() > 0 && reference.bytes() <= maximum, "retained source byte bound exceeded");
        byte[] bytes = owner.readExact(reference, maximum);
        check(bytes != null && bytes.length == reference.bytes()
                && G2RetainedNativeSourceProvider.sha256(bytes).equals(reference.sha256()), "exact original source bytes differ");
        return bytes;
    }
    private static JsonNode field(JsonNode value, String key) {
        check(value != null && value.isObject() && value.has(key), "missing native succession source field: " + key);
        return value.get(key);
    }
    private static String text(JsonNode value, String key) { return StrictJson.text(field(value, key)); }
    private static Rejected rejected(Reason reason, String detail) {
        return new Rejected(reason, detail.substring(0, Math.min(512, detail.length())));
    }
}

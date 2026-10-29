package org.xar.ck3.control.nativebridge.capabilities.publicmethods.gui;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.NullNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.driver.PublicSnapshotCodec;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.Context;
import org.xar.ck3.control.nativebridge.capabilities.gui.NativeUiParsedReturn;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.ExactRef;

/** Pure public DATA projection. Inputs never mint a read, writer, action or source permission. */
public final class GuiPublicMetadata {
    public static final String BEFORE_SCHEMA = "xar.gui-before-public-source/v1";
    private static final String PROJECTION_FIELD = "xar_java_snapshot_projection";
    private static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private record BeforeSource(ObjectNode snapshot, ObjectNode diagnostics) { }
    private GuiPublicMetadata() { }

    /** Preserve the actual before snapshot and actual before diagnostics as distinct sources. */
    public static RawJson beforeSource(RawJson actualSnapshot, RawJson actualDriverDiagnostics) {
        ObjectNode snapshot = object(actualSnapshot);
        ObjectNode diagnostics = object(actualDriverDiagnostics);
        ObjectNode bundle = StrictJson.object().put("schema", BEFORE_SCHEMA);
        bundle.set("snapshot", snapshot); bundle.set("driver_diagnostics", diagnostics);
        return RawJson.fullMaterial(StrictJson.canonical(bundle));
    }

    /** Validates the exact public artifact role without granting native/source or archive authority. */
    public static void requireParsedReturnReference(RawJson actualReference) {
        ObjectNode reference = StrictJson.object(StrictJson.parse(Objects.requireNonNull(actualReference).bytes()),
                Set.of("path", "bytes", "sha256", "validation_state"));
        require(reference.size() == 4 && "unvalidated".equals(StrictJson.text(reference.get("validation_state"))),
                "strict original parsed-return reference required");
        ObjectNode exact = reference.deepCopy(); exact.remove("validation_state");
        long bytes=ExactRef.fromJson(exact).bytes();
        require(bytes > 0 && bytes <= NativeUiParsedReturn.MAXIMUM_ARTIFACT_BYTES,
                "bounded nonempty actual parsed-return artifact required");
    }

    /** Original UI query metadata uses the retained Driver diagnostics, not the NativeHello generation. */
    public static ObjectNode queryFrame(ObjectNode original, Context before, RawJson actualBeforeSnapshot) {
        BeforeSource source = sourceBefore(before, actualBeforeSnapshot);
        ObjectNode snapshot = source.snapshot();
        ObjectNode diagnostics = source.diagnostics();
        String snapshotId = StrictJson.text(snapshot.get("snapshot_id"));
        BigInteger revision = unsigned(snapshot.get("revision"));
        BigInteger nativeRevision = snapshot.has("native_revision") ? unsigned(snapshot.get("native_revision")) : revision;
        // This default mirrors the original diagnostics.get(key, 0), only within an actual supplied diagnostics object.
        BigInteger driverGeneration = diagnostics.has("connection_generation")
                ? unsigned(diagnostics.get("connection_generation")) : BigInteger.ZERO;
        ObjectNode out = Objects.requireNonNull(original).deepCopy();
        out.put("queried_snapshot_id", snapshotId).put("queried_revision", revision)
                .put("queried_native_revision", nativeRevision)
                .put("queried_connection_generation", driverGeneration);
        out.set("episode_run_id", episodeRunId(before, snapshot));
        return out;
    }

    /** Original decision wrapper fields; its revision belongs to the original before frame. */
    public static ObjectNode decisionFrame(ObjectNode original, Context before, RawJson actualBeforeSnapshot) {
        ObjectNode out = Objects.requireNonNull(original).deepCopy();
        out.set("episode_run_id", episodeRunId(before, actualBeforeSnapshot));
        out.put("queried_revision", before.before().frame().revision());
        return noDesktopInputs(out);
    }

    /** Original White read wrappers retain source build and read-only semantics. */
    public static ObjectNode readFrame(ObjectNode original, Context before, RawJson actualBeforeSnapshot) {
        ObjectNode out = decisionFrame(original, before, actualBeforeSnapshot);
        return out.put("read_only", true).put("game_version", before.build().version())
                .put("executable_sha256", before.build().sha256());
    }

    /** Original wrapper get semantics: absent Native campaign episode becomes explicit null DATA. */
    public static JsonNode episodeRunId(Context before, RawJson actualBeforeSnapshot) {
        return episodeRunId(before, sourceBefore(before, actualBeforeSnapshot).snapshot());
    }

    private static JsonNode episodeRunId(Context before, ObjectNode snapshot) {
        if (before.before().observationVersion() == DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION) {
            JsonNode original = snapshot.get("episode_run_id");
            return original == null ? NullNode.instance : original.deepCopy();
        }
        return com.fasterxml.jackson.databind.node.TextNode.valueOf(before.before().frame().episodeRunId());
    }

    private static BeforeSource sourceBefore(Context before, RawJson actualBeforeSnapshot) {
        Objects.requireNonNull(before);
        ObjectNode source = StrictJson.object(PublicDataJson.object(Objects.requireNonNull(actualBeforeSnapshot)),
                Set.of("schema", "snapshot", "driver_diagnostics"));
        require(BEFORE_SCHEMA.equals(StrictJson.text(source.get("schema"))), "actual GUI before source schema required");
        ObjectNode snapshot = object(source.get("snapshot"));
        ObjectNode diagnostics = object(source.get("driver_diagnostics"));
        String snapshotId = StrictJson.text(snapshot.get("snapshot_id"));
        BigInteger revision = unsigned(snapshot.get("revision"));
        BigInteger nativeRevision = snapshot.has("native_revision") ? unsigned(snapshot.get("native_revision")) : revision;
        require(snapshotId.equals(before.before().frame().snapshotId()), "GUI public snapshot identity changed");
        require(revision.equals(before.before().frame().revision()), "GUI public revision changed");
        require(nativeRevision.equals(before.before().frame().identity().nativeRevision()), "GUI native revision changed");
        if (before.before().observationVersion() == DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION) {
            require(snapshot.has(PROJECTION_FIELD), "actual profile4 public snapshot representation required");
            // The sole public codec checks marker/profile and full DATA roles; this grants no observation authority.
            PublicSnapshotCodec.decode(PublicDataJson.encodeFullMaterial(snapshot));
        } else {
            require(!snapshot.has(PROJECTION_FIELD), "ordinary GUI context cannot consume profile4 representation");
        }
        return new BeforeSource(snapshot, diagnostics);
    }

    private static ObjectNode noDesktopInputs(ObjectNode original) {
        return original.put("uses_mouse", false).put("uses_keyboard", false).put("uses_ocr", false);
    }
    private static ObjectNode object(RawJson value) { return object(PublicDataJson.object(Objects.requireNonNull(value))); }
    private static ObjectNode object(JsonNode value) {
        require(value instanceof ObjectNode, "actual GUI source object required");
        return ((ObjectNode) value).deepCopy();
    }
    private static BigInteger unsigned(JsonNode value) {
        require(value != null && !value.isNull(), "original unsigned identity required");
        return value.isIntegralNumber() ? StrictJson.integer(value, BigInteger.ZERO, U64)
                : PublicUnsigned64.parse(value, PublicUnsigned64.Minimum.ZERO, PublicUnsigned64.NumericInput.DECIMAL_ONLY);
    }
    private static void require(boolean ok, String reason) { if (!ok) throw new IllegalArgumentException(reason); }
}

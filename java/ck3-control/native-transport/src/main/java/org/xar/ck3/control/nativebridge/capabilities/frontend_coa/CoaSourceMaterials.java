package org.xar.ck3.control.nativebridge.capabilities.frontend_coa;

import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.FrontendFrame;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Large source lives in the one durable original-material archive, never in the small intent argument domain. */
public final class CoaSourceMaterials implements ActionPorts.PreparationPort {
    private static final ObjectMapper JSON = new ObjectMapper();
    private final ActionPorts.OutcomeArchive archive;
    public CoaSourceMaterials(ActionPorts.OutcomeArchive archive) { this.archive = Objects.requireNonNull(archive); }
    public record Material(ExactRef reference, EncodedSource source, Binding binding, String sessionId, boolean large) {
        public Material { Objects.requireNonNull(reference); Objects.requireNonNull(source); Objects.requireNonNull(binding); text(sessionId, 4096); }
    }
    public Material preserve(EncodedSource source, Binding binding, CommandOrigin origin, String sessionId, boolean large) {
        requireOrigin(origin, binding); require(large || source.sourceBytes() <= V1_MAX_BYTES, "v1 source exceeds limit");
        ObjectNode row = JSON.createObjectNode(); row.put("schema", "xar.coa-source-material/v1"); row.put("source", source.source()); row.put("source_sha256", source.sourceSha256()); row.put("source_bytes", source.sourceBytes()); row.put("session_id", text(sessionId, 4096)); row.put("large", large); row.set("binding", bindingNode(binding));
        RawJson original = CoaCodec.raw(row); ExactRef reference = archive.preserveMaterial(original);
        require(reference.bytes() == original.bytes().length && reference.sha256().equals(sha256(original.bytes())), "archive material reference differs from exact original bytes");
        return new Material(reference, source, binding, sessionId, large);
    }
    public Material load(ExactRef reference, CommandOrigin origin, Binding expectedBinding, String sessionId) {
        RawJson original = archive.loadMaterial(reference); require(reference.bytes() == original.bytes().length && reference.sha256().equals(sha256(original.bytes())), "actual source material bytes or SHA256 changed");
        ObjectNode row = CoaCodec.object(CoaCodec.parse(original)); CoaCodec.exact(row, "schema", "source", "source_sha256", "source_bytes", "session_id", "large", "binding");
        require(CoaCodec.string(row, "schema").equals("xar.coa-source-material/v1") && CoaCodec.string(row, "session_id").equals(sessionId), "source material schema or session drift");
        boolean large = CoaCodec.bool(row, "large"); EncodedSource encoded = EncodedSource.encode(CoaCodec.string(row, "source"), large);
        require(encoded.source().equals(CoaCodec.string(row, "source")) && encoded.sourceSha256().equals(CoaCodec.string(row, "source_sha256")) && encoded.sourceBytes() == CoaCodec.intValue(row, "source_bytes", 1, V2_MAX_BYTES), "source material canonical bytes changed");
        Binding binding = CoaCodec.binding(CoaCodec.raw(row.get("binding"))); require(binding.equals(expectedBinding), "source material crossed original binding"); requireOrigin(origin, binding);
        return new Material(reference, encoded, binding, sessionId, large);
    }
    public static OpportunityJson.Obj arguments(Material material, boolean apply) {
        ObjectNode row = JSON.createObjectNode(); row.set("source_material", material.reference().toJson()); row.put("source_sha256", material.source().sourceSha256()); row.put("source_bytes", material.source().sourceBytes()); row.put("apply", apply); row.set("binding", bindingNode(material.binding()));
        return OpportunityJson.object(OpportunityJson.parse(CoaCodec.raw(row).bytes()), "CoA source arguments");
    }
    public Material material(ActionCommand command, Binding binding) {
        ObjectNode row = CoaCodec.object(OpportunityJson.toNode(command.arguments())); CoaCodec.exact(row, "source_material", "source_sha256", "source_bytes", "apply", "binding");
        require(CoaCodec.binding(CoaCodec.raw(row.get("binding"))).equals(binding), "intent source binding differs from caller");
        Material material = load(ExactRef.fromJson(row.get("source_material")), command.origin(), binding, command.sessionId());
        require(material.source().sourceSha256().equals(CoaCodec.string(row, "source_sha256")) && material.source().sourceBytes() == CoaCodec.intValue(row, "source_bytes", 1, V2_MAX_BYTES), "intent and durable source material identities differ"); CoaCodec.bool(row, "apply"); return material;
    }
    @Override public NativeRequest prepare(ActionCommand command) {
        String step = command.operation().value(); if (step.equals(PROBE_STEP)) {
            ObjectNode arguments = CoaCodec.object(OpportunityJson.toNode(command.arguments())); Binding binding = CoaCodec.binding(CoaCodec.raw(arguments.get("binding"))); Material material = material(command, binding);
            boolean apply = OpportunityJson.bool(command.arguments().get("apply"), "apply"); return CoaCodec.probeRequest(material.source(), apply);
        }
        require(command.arguments().members().isEmpty(), "CoA primitive accepts no additional arguments"); return CoaCodec.primitive(step);
    }
    public static Binding bindingOf(CommandOrigin origin, String sessionId) {
        if (origin instanceof CommandOrigin.Frontend frontend) {
            var identity = frontend.identity(); require(identity.frontendSessionId().equals(sessionId), "frontend source session drift");
            if (identity.frame() instanceof FrontendFrame.Menu) return new FrontendBinding(identity.connectionGeneration(), identity.bridgePid());
            FrontendFrame.Snapshot frame = (FrontendFrame.Snapshot)identity.frame();
            return new SnapshotBinding(SnapshotMode.FRONTEND_SNAPSHOT, frame.snapshotId(), frame.revision(), frame.nativeRevision(), frame.dateRaw(), java.util.Optional.empty(), identity.connectionGeneration(), identity.bridgePid());
        }
        throw new IllegalArgumentException("gameplay source needs the actual connection-generation binding; use requireOrigin with its original binding");
    }
    public static void requireOrigin(CommandOrigin origin, Binding binding) {
        Objects.requireNonNull(origin); Objects.requireNonNull(binding); require(origin.game().pid() == binding.bridgePid(), "CoA binding PID differs from actual Game generation");
        if (origin instanceof CommandOrigin.Frontend frontend) {
            var identity = frontend.identity(); require(identity.connectionGeneration().equals(binding.connectionGeneration()) && identity.bridgePid() == binding.bridgePid(), "CoA frontend connection identity drift");
            if (identity.frame() instanceof FrontendFrame.Menu) require(binding instanceof FrontendBinding, "frontend menu cannot forge a gameplay/snapshot binding");
            else { FrontendFrame.Snapshot frame = (FrontendFrame.Snapshot)identity.frame(); require(binding instanceof SnapshotBinding, "frontend snapshot requires its actual snapshot binding"); SnapshotBinding snapshot = (SnapshotBinding)binding;
                require(snapshot.mode() == SnapshotMode.FRONTEND_SNAPSHOT && snapshot.snapshotId().equals(frame.snapshotId()) && snapshot.revision().equals(frame.revision()) && snapshot.nativeRevision().equals(frame.nativeRevision()) && snapshot.dateRaw() == frame.dateRaw(), "frontend snapshot binding drift"); }
        } else {
            CommandOrigin.Gameplay gameplay = (CommandOrigin.Gameplay)origin; require(binding instanceof SnapshotBinding, "gameplay requires snapshot binding"); SnapshotBinding snapshot = (SnapshotBinding)binding; var frame = gameplay.before().frame();
            require(snapshot.mode() == SnapshotMode.GAMEPLAY && snapshot.snapshotId().equals(frame.snapshotId()) && snapshot.revision().equals(frame.revision()) && snapshot.nativeRevision().equals(frame.identity().nativeRevision()) && BigInteger.valueOf(snapshot.dateRaw()).equals(frame.identity().dateRaw()) && snapshot.episodeRunId().equals(java.util.Optional.of(frame.episodeRunId())), "actual gameplay source frame differs");
        }
    }
    public static ObjectNode bindingNode(Binding binding) {
        ObjectNode row = JSON.createObjectNode(); row.put("connection_generation", binding.connectionGeneration()); row.put("bridge_pid", binding.bridgePid()); row.put("revision", binding.revision());
        if (binding instanceof FrontendBinding) row.put("mode", "frontend");
        else { SnapshotBinding snapshot = (SnapshotBinding)binding; row.put("mode", snapshot.mode() == SnapshotMode.GAMEPLAY ? "gameplay" : "frontend_snapshot"); row.put("snapshot_id", snapshot.snapshotId()); row.put("native_revision", snapshot.nativeRevision()); row.put("date_raw", snapshot.dateRaw()); snapshot.episodeRunId().ifPresent(value -> row.put("episode_run_id", value)); }
        return row;
    }
}

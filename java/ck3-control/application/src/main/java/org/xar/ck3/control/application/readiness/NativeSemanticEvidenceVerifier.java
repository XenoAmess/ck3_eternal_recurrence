package org.xar.ck3.control.application.readiness;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.NativeCampaignProjection;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SemanticVerifier;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.VerifiedSemantic;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;

/** Independently reads all originals under the borrowed writer lock. Metadata never substitutes for bytes. */
public final class NativeSemanticEvidenceVerifier implements SemanticVerifier {
    @FunctionalInterface public interface ArtifactReader {
        byte[] read(ContinuityStorePort.Session borrowed, ExactRef ref, int maximumBytes) throws IOException;
    }
    private final ArtifactReader archive;
    public NativeSemanticEvidenceVerifier(ArtifactReader archive) { this.archive = Objects.requireNonNull(archive); }
    @Override public VerifiedSemantic verify(ContinuityStorePort.Session borrowed, SessionIdentity session,
            SemanticEvidence evidence) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(session); Objects.requireNonNull(evidence);
        String headBefore = borrowed.head().digest();
        try {
            var id = evidence.frame(); var frame = id.frame();
            require(session.machineId().equals(id.machineId()) && session.game().equals(id.game()), "semantic evidence crossed owned Game");
            byte[] semanticBytes = read(borrowed, evidence.semantic(), ReadinessArchive.Role.SEMANTIC.maximumBytes());
            byte[] nativeBytes = read(borrowed, evidence.originalNativePacket(), ReadinessArchive.Role.NATIVE_PACKET.maximumBytes());
            byte[] stampBytes = read(borrowed, evidence.driverStamp(), ReadinessArchive.Role.DRIVER_STAMP.maximumBytes());
            byte[] driverBytes = read(borrowed, evidence.originalDriver(), ReadinessArchive.Role.DRIVER.maximumBytes());
            Obj semantic = DriverJson.object(semanticBytes, ReadinessArchive.Role.SEMANTIC.maximumBytes());
            Obj stamp = DriverJson.object(stampBytes, ReadinessArchive.Role.DRIVER_STAMP.maximumBytes());
            Obj raw = framed(nativeBytes); DriverStateSnapshot.Complete driver = DriverStateSnapshot.decodeComplete(driverBytes);
            require(stamp.members().keySet().equals(Set.of("schema", "machine_id", "game_pid", "game_creation_filetime", "session_id",
                    "connection_generation", "driver_version", "episode_epoch", "observation_version", "full_binding_sha256",
                    "driver_sha256", "episode_run_id", "snapshot_id", "revision",
                    "native_revision", "date_raw", "actor_character_id", "observed_at")), "exact semantic stamp fields required");
            require(NativeDriverStamp.SCHEMA.equals(text(stamp.get("schema"), "schema")), "semantic stamp schema differs");
            require(session.machineId().equals(text(stamp.get("machine_id"), "machine_id"))
                    && session.sessionId().equals(text(stamp.get("session_id"), "session_id"))
                    && BigInteger.valueOf(session.game().pid()).equals(integer(stamp.get("game_pid"), "game_pid"))
                    && session.game().creationFiletime().value().toString().equals(text(stamp.get("game_creation_filetime"), "game_creation_filetime")),
                    "stamp crossed actual machine/Game/session identity");
            BigInteger generation = integer(stamp.get("connection_generation"), "connection_generation");
            require(generation.signum() > 0 && generation.bitLength() <= 64, "actual uint64 connection generation required");
            for (String field : List.of("driver_version", "episode_epoch")) {
                BigInteger version = integer(stamp.get(field), field);
                require(version.signum() >= 0 && version.compareTo(BigInteger.valueOf(org.xar.ck3.control.contracts.StrictJson.MAX_SAFE_INTEGER)) <= 0,
                        "nonnegative exact safe Driver version required: " + field);
            }
            require(BigInteger.valueOf(id.observationVersion()).equals(integer(stamp.get("observation_version"), "observation_version")),
                    "semantic contract observation version differs from archived stamp");
            require(DriverObservationAssembler.bindingSha256(semantic).equals(text(stamp.get("full_binding_sha256"), "full_binding_sha256")),
                    "semantic binding differs from archived complete-frame stamp");
            require(evidence.originalDriver().sha256().equals(text(stamp.get("driver_sha256"), "driver_sha256"))
                    && Arrays.equals(driver.encode(), driverBytes), "complete original Driver bytes/hash differ");
            require(evidence.observedAt().equals(Instant.parse(text(stamp.get("observed_at"), "observed_at"))), "semantic observed time differs from actual stamp");
            require("state_snapshot".equals(text(raw.get("type"), "type"))
                    && BigInteger.ONE.equals(integer(raw.get("protocol_version"), "protocol_version")), "original native state_snapshot required");
            require(frame.snapshotId().equals(text(raw.get("snapshot_id"), "snapshot_id"))
                    && frame.identity().nativeRevision().equals(integer(raw.get("revision"), "revision")), "native frame binding differs");
            Obj nativeState = object(raw.get("state"), "state");
            boolean nativeCampaign=id.observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION;
            boolean canonical=id.observationVersion()==DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION||nativeCampaign;
            if(canonical)requireCanonicalProjection(borrowed,evidence,semantic,nativeBytes,driverBytes);
            else requireNativeState(nativeState, semantic);
            for (Obj row : List.of(semantic, stamp)) {
                require(frame.snapshotId().equals(text(row.get("snapshot_id"), "snapshot_id"))
                        && frame.revision().equals(integer(row.get("revision"), "revision"))
                        && frame.identity().nativeRevision().equals(integer(row.get("native_revision"), "native_revision"))
                        && frame.identity().dateRaw().equals(integer(row.get("date_raw"), "date_raw"))
                        && (nativeCampaign&&row==semantic || frame.episodeRunId().equals(text(row.get("episode_run_id"), "episode_run_id"))), "archived semantic/stamp frame differs");
            }
            Obj diagnostics = object(semantic.get("diagnostics"), "diagnostics");
            require(BigInteger.valueOf(session.game().pid()).equals(integer(diagnostics.get("bridge_pid"), "bridge_pid"))
                    && integer(stamp.get("connection_generation"), "connection_generation").equals(integer(diagnostics.get("connection_generation"), "connection_generation")),
                    "semantic/stamp transport identity differs");
            Obj actor = object(semantic.get("played_character"), "played_character");
            require(frame.identity().player().equals(integer(actor.get("character_id"), "character_id"))
                    && frame.identity().player().equals(integer(stamp.get("actor_character_id"), "actor_character_id"))
                    && (nativeCampaign || frame.identity().player().equals(integer(semantic.get("episode_character_id"), "episode_character_id"))), "semantic actor/episode differs");
            bool(actor.get("alive"), "alive"); bool(semantic.get("paused"), "paused"); bool(semantic.get("map_ready"), "map_ready");
            require(driver.session().bridgePid() == session.game().pid()
                    && driver.session().episodeRunId().equals(frame.episodeRunId())
                    && driver.session().actorId().equals(frame.identity().player()), "full Driver session differs");
            List<Value> history = array(semantic.get("native_command_history"), "native_command_history");
            require(history.size() == driver.commandHistory().size(), "semantic history is incomplete");
            for (int index = 0; index < history.size(); index++)
                require(history.get(index).equals(DriverJson.object(driver.commandHistory().get(index).originalRow().json(), DriverJson.MAX_NATIVE_BYTES)), "semantic history differs from actual full Driver");
            requireSlot(semantic, "campaign_goal", driver.campaignGoal());
            if(!nativeCampaign)requireSlot(semantic, "succession_lifecycle", driver.successionLifecycle());
            requireSlot(semantic, "native_rollback_war_failure", driver.rollbackWarFailure());
            requireSlot(semantic, "native_rollback_war_failures", driver.rollbackWarFailures());
            for (String field : nativeCampaign?List.of("active_event","pending_character_interaction")
                    :List.of("active_event", "pending_character_interaction", "one_life_terminal_reason"))
                require(semantic.members().containsKey(field), "explicit semantic field absent: " + field);
            require(headBefore.equals(borrowed.head().digest()), "writer changed during same-lock semantic verification");
            Obj material = new Obj(Map.of("semantic", ref(evidence.semantic()), "native", ref(evidence.originalNativePacket()),
                    "stamp", ref(evidence.driverStamp()), "driver", ref(evidence.originalDriver())));
            String digest = DriverJson.sha256(DriverJson.encode(material));
            return new VerifiedSemantic(id, evidence.observedAt(), "semantic-" + digest, digest);
        } catch (IllegalArgumentException | ArithmeticException | java.time.DateTimeException failure) {
            throw new IOException("archived native semantic evidence failed: " + failure.getMessage(), failure);
        }
    }
    /** Current canonical profiles replay their sole original producer; raw fields may have legitimate normalized values. */
    private void requireCanonicalProjection(ContinuityStorePort.Session borrowed,SemanticEvidence evidence,Obj semantic,
            byte[] nativeBytes,byte[] driverBytes)throws IOException {
        ExactRef manifestRef=DriverObservationEvidenceReader.reference(semantic.get("java_driver_facts_evidence"));
        RawJson manifest=RawJson.fullMaterial(read(borrowed,manifestRef,DriverJson.MAX_NATIVE_BYTES));
        var actual=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,nativeBytes);
        ExactRef driverRef=DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest);
        byte[] manifestDriver;
        if (driverRef.equals(evidence.originalDriver())) {
            manifestDriver = driverBytes;
        } else {
            manifestDriver=read(borrowed,driverRef,ReadinessArchive.Role.DRIVER.maximumBytes());
        }
        require(Arrays.equals(manifestDriver,driverBytes),"canonical manifest and original Driver bytes differ");
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(manifestDriver),actual);
        require(facts.observationVersion()==evidence.frame().observationVersion(),
                "canonical SEM must retain its exact original facts observation version");
        var assembler=new DriverObservationAssembler();
        var rebuilt=assembler.assemble(actual,facts,evidence.originalNativePacket());
        require(rebuilt instanceof DriverObservationAssembler.Complete,"canonical original join has no actual living current actor");
        var complete=(DriverObservationAssembler.Complete)rebuilt;
        require(complete.identity().equals(evidence.frame())&&complete.observedAt().equals(evidence.observedAt())
                &&complete.semantic().equals(semantic),"canonical archived SEM crossed its actual actor/frame/public revision/Driver originals");
        if(facts.observationVersion()==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION)
            NativeCampaignProjection.requireJoinedSnapshot(complete.originalProjection().orElseThrow(),RawJson.fullMaterial(DriverJson.encode(semantic)));
    }
    private byte[] read(ContinuityStorePort.Session borrowed, ExactRef ref, int maximumBytes) throws IOException {
        require(ref.bytes() > 0 && ref.bytes() <= maximumBytes, "bounded nonempty semantic original required");
        byte[] bytes = archive.read(borrowed, ref, maximumBytes);
        require(bytes != null && bytes.length == ref.bytes() && ref.sha256().equals(DriverJson.sha256(bytes)), "actual original bytes differ from exact reference");
        return bytes;
    }
    private static Obj framed(byte[] bytes) {
        require(bytes.length >= 5 && ByteBuffer.wrap(bytes, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt() == bytes.length - 4,
                "exact original native LE uint32 length required");
        return DriverJson.object(Arrays.copyOfRange(bytes, 4, bytes.length), DriverJson.MAX_NATIVE_BYTES);
    }
    private static void requireNativeState(Obj nativeState, Obj semantic) {
        for (var entry : nativeState.members().entrySet()) {
            if (entry.getKey().equals("diagnostics") && entry.getValue() instanceof Obj original) {
                Obj joined = object(semantic.get("diagnostics"), "diagnostics");
                original.members().forEach((key, value) -> require(value.equals(joined.get(key)), "original native diagnostic was overwritten: " + key));
            } else require(entry.getValue().equals(semantic.get(entry.getKey())), "original native state field was overwritten: " + entry.getKey());
        }
    }
    /** The full Driver is the producer for these fields; preserve missing, null and the entire JSON value. */
    private static void requireSlot(Obj semantic, String field, DriverStateSnapshot.Slot slot) {
        switch (slot) {
            case DriverStateSnapshot.Missing ignored -> require(!semantic.members().containsKey(field), "absent Driver slot was invented: " + field);
            case DriverStateSnapshot.NullValue ignored -> require(semantic.members().containsKey(field) && semantic.get(field) == Nil.INSTANCE,
                    "explicit null Driver slot differs: " + field);
            case DriverStateSnapshot.Value value -> {
                byte[] prefix = "{\"value\":".getBytes(java.nio.charset.StandardCharsets.UTF_8);
                byte[] retained = value.json(); byte[] wrapped = new byte[prefix.length + retained.length + 1];
                System.arraycopy(prefix, 0, wrapped, 0, prefix.length);
                System.arraycopy(retained, 0, wrapped, prefix.length, retained.length); wrapped[wrapped.length - 1] = '}';
                require(semantic.members().containsKey(field) && DriverJson.object(wrapped, DriverJson.MAX_NATIVE_BYTES).get("value").equals(semantic.get(field)),
                        "full retained Driver slot differs: " + field);
            }
        }
    }
    private static Obj ref(ExactRef ref) {
        return new Obj(Map.of("path", new Text(ref.path()), "bytes", new IntegerValue(BigInteger.valueOf(ref.bytes())), "sha256", new Text(ref.sha256())));
    }
}

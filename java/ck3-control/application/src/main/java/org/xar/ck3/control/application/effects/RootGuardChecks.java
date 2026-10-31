package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Checks shared by the two real guards. A detached Head or a fabricated capability cannot open the held authority. */
final class RootGuardChecks {
    private RootGuardChecks() { }
    static ContinuityStorePort.Session session(Supplier<ContinuityStorePort.Session> borrowed, WriterContracts.Head proposed) throws IOException {
        ContinuityStorePort.Session session = Objects.requireNonNull(borrowed.get(), "actual borrowed writer Session required");
        WriterContracts.Head actual = session.head();
        StrictJson.require(actual.digest().equals(proposed.digest()) && actual.documents().equals(proposed.documents())
                && actual.absent().equals(proposed.absent()) && actual.indexRepairs().equals(proposed.indexRepairs())
                && actual.snapshotNeedsRecovery() == proposed.snapshotNeedsRecovery(), "guard did not receive the current same-lock writer Head");
        return session;
    }
    /** Provenance-only compatibility helper. Retains typed source metadata identity but removes runtime file existence, absolute path, byte count, and SHA/pin audits. */
    static void source(ContinuityStorePort.Session session, ExactRef actualDefinition) throws IOException {
        Objects.requireNonNull(actualDefinition);
        // Source metadata is retained for typed routing/identity checks by callers.
        // Runtime file/byte/SHA qualification is removed per explicit instruction.
    }
    static GuardEvidence binding(ReadinessAuthority.LeaseSnapshot lease, CommandOrigin origin, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, ActionPorts.OutcomeArchive archive, Clock clock,
            WriterContracts.Head head, String authorityId, ContinuityStorePort.Session session, OriginalEvidencePort originals) throws IOException {
        Objects.requireNonNull(lease);
        // Drop unused action inventory only after the actual ordinary authority supplied its original lease.
        // This is a DATA adapter; it never opens the held-only authority or manufactures ordinary Ready.
        return binding(new ReadinessAuthority.PhysicalReadLease(lease.frame(),lease.driver(),lease.capabilities(),lease.semantic(),
                lease.bridgeCapabilities(),lease.originalHello(),lease.originalHeartbeat(),lease.validUntil(),lease.originalSourceQualification()),
                origin,source,sessionId,operation,deadline,archive,clock,head,authorityId,session,originals);
    }
    static GuardEvidence binding(ReadinessAuthority.PhysicalReadLease lease, CommandOrigin origin, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, ActionPorts.OutcomeArchive archive, Clock clock,
            WriterContracts.Head head, String authorityId, ContinuityStorePort.Session session, OriginalEvidencePort originals) throws IOException {
        Objects.requireNonNull(lease);
        Instant bindingEnteredAt = clock.instant();
        RootGuardChecks.session(() -> session, head);
        var frame = lease.frame(); Instant now = clock.instant();
        StrictJson.require(origin instanceof CommandOrigin.Gameplay, "ordinary native guard requires a gameplay origin");
        var before = origin.requireGameplay(); var actual = frame.identity();
        StrictJson.require(before.machineId().equals(actual.machineId()) && before.game().equals(actual.game())
                && before.frame().episodeRunId().equals(actual.frame().episodeRunId())
                && before.frame().identity().player().equals(actual.frame().identity().player())
                && frame.source().equals(source) && frame.sessionId().equals(sessionId), "actual held Game/actor/episode/source/session changed");
        StrictJson.require(head.state().machineId().equals(origin.machineId()) && source.machineId().equals(origin.machineId()), "writer/source/observation machine changed");
        StrictJson.require(now.isBefore(deadline) && !now.isBefore(frame.observedAt()) && !now.isAfter(lease.validUntil()),
                "actual held readiness lease is stale: binding_entered_at=" + bindingEnteredAt + ", now=" + now
                        + ", deadline=" + deadline + ", observed_at=" + frame.observedAt() + ", valid_until=" + lease.validUntil()
                        + ", writer_sequence=" + head.state().sequence());
        var semantic = lease.semantic();
        StrictJson.require(semantic.frame().equals(frame.identity()) && semantic.originalNativePacket().equals(frame.originalEvidence())
                && semantic.observedAt().equals(frame.observedAt()), "readiness evidence differs from the actual held frame");
        byte[] packet = archive.loadNativeFrame(frame.originalEvidence()); exact(frame.originalEvidence(), packet);
        RawJson semanticBytes = archive.loadFullMaterial(semantic.semantic()); exact(semantic.semantic(), semanticBytes.bytes());
        requireSemanticOriginal(frame,semanticBytes);
        RawJson originalStamp=archive.loadMaterial(semantic.driverStamp()); exact(semantic.driverStamp(),originalStamp.bytes());
        RawJson originalDriver=archive.loadFullMaterial(semantic.originalDriver()); exact(semantic.originalDriver(),originalDriver.bytes());
        // These are actual received notices archived by the collector, not boolean permission flags supplied by a planner.
        for (ExactRef ref : java.util.List.of(lease.originalHello(), lease.originalHeartbeat())) {
            exact(ref, originals.read(session, ref, StrictJson.EXPLICIT_MAX_BYTES));
        }

        RawJson capabilities = new RawJson(OpportunityJson.encode(lease.capabilities()));
        ExactRef capability = archive.preserveMaterial(capabilities);
        StrictJson.require(capabilities.equals(archive.loadMaterial(capability)), "actual capability archive readback changed");
        Instant until = lease.validUntil().isBefore(deadline) ? lease.validUntil() : deadline;
        // Preserve a real revision drift for the coordinator's typed pre-dispatch mismatch branch.
        ExactRef basis = RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,
                lease.originalHello(),lease.originalHeartbeat(),lease.originalSourceQualification(),capability),
                operation,authorityId,archive,head);
        return new GuardEvidence(new CommandOrigin.Gameplay(actual), source, sessionId, frame.connectionGeneration(), operation, frame.originalEvidence(),
                lease.originalHello(), authorityId, frame.observedAt(), until, java.util.List.of(basis));
    }
    static GuardEvidence readBinding(ReadinessAuthority.LeaseSnapshot lease, CommandOrigin origin, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, ActionPorts.OutcomeArchive archive, Clock clock,
            WriterContracts.Head head, String authorityId, ContinuityStorePort.Session session, OriginalEvidencePort originals) throws IOException {
        Objects.requireNonNull(lease);
        // Drop unused action inventory only after the actual ordinary authority supplied its original lease.
        // This is a DATA adapter; it never opens the held-only authority or manufactures ordinary Ready.
        return readBinding(new ReadinessAuthority.PhysicalReadLease(lease.frame(),lease.driver(),lease.capabilities(),lease.semantic(),
                lease.bridgeCapabilities(),lease.originalHello(),lease.originalHeartbeat(),lease.validUntil(),lease.originalSourceQualification()),
                origin,source,sessionId,operation,deadline,archive,clock,head,authorityId,session,originals);
    }
    static GuardEvidence readBinding(ReadinessAuthority.PhysicalReadLease lease, CommandOrigin origin, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, ActionPorts.OutcomeArchive archive, Clock clock,
            WriterContracts.Head head, String authorityId, ContinuityStorePort.Session session, OriginalEvidencePort originals) throws IOException {
        Objects.requireNonNull(lease);
        Instant bindingEnteredAt = clock.instant();
        RootGuardChecks.session(() -> session, head);
        var frame = lease.frame(); Instant now = clock.instant();
        StrictJson.require(origin instanceof CommandOrigin.Gameplay, "ordinary native guard requires a gameplay origin");
        var before = origin.requireGameplay(); var actual = frame.identity();
        StrictJson.require(before.machineId().equals(actual.machineId()) && before.game().equals(actual.game())
                && before.frame().episodeRunId().equals(actual.frame().episodeRunId())
                && before.frame().identity().player().equals(actual.frame().identity().player())
                && frame.source().equals(source) && frame.sessionId().equals(sessionId), "actual held Game/actor/episode/source/session changed");
        StrictJson.require(head.state().machineId().equals(origin.machineId()) && source.machineId().equals(origin.machineId()), "writer/source/observation machine changed");
        StrictJson.require(now.isBefore(deadline) && !now.isBefore(frame.observedAt()) && !now.isAfter(lease.validUntil()),
                "actual held readiness lease is stale: binding_entered_at=" + bindingEnteredAt + ", now=" + now
                        + ", deadline=" + deadline + ", observed_at=" + frame.observedAt() + ", valid_until=" + lease.validUntil()
                        + ", writer_sequence=" + head.state().sequence());
        var semantic = lease.semantic();
        StrictJson.require(semantic.frame().equals(frame.identity()) && semantic.originalNativePacket().equals(frame.originalEvidence())
                && semantic.observedAt().equals(frame.observedAt()), "readiness evidence differs from the actual held frame");
        RawJson capabilities = new RawJson(OpportunityJson.encode(lease.capabilities()));
        ExactRef capability = archive.preserveMaterial(capabilities);
        StrictJson.require(capabilities.equals(archive.loadMaterial(capability)), "actual capability archive readback changed");
        Instant until = lease.validUntil().isBefore(deadline) ? lease.validUntil() : deadline;
        // Preserve a real revision drift for the coordinator's typed pre-dispatch mismatch branch.
        ExactRef basis = RootGuardEvidence.preservePhysicalRead(new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,
                lease.originalHello(),lease.originalHeartbeat(),lease.originalSourceQualification(),capability),
                operation,authorityId,archive,head);
        return new GuardEvidence(new CommandOrigin.Gameplay(actual), source, sessionId, frame.connectionGeneration(), operation, frame.originalEvidence(),
                lease.originalHello(), authorityId, frame.observedAt(), until, java.util.List.of(basis));
    }
    static void livingPaused(ReadinessAuthority.LeaseSnapshot lease) { livingPaused(Objects.requireNonNull(lease).frame()); }
    static void livingPaused(ReadinessAuthority.PhysicalReadLease lease) { livingPaused(Objects.requireNonNull(lease).frame()); }
    private static void livingPaused(Complete frame) {
        livingMap(frame);
        StrictJson.require(OpportunityJson.bool(frame.semantic().get("paused"),"paused"),"action/query requires an actual paused map");
    }
    static void livingMap(ReadinessAuthority.LeaseSnapshot lease) { livingMap(Objects.requireNonNull(lease).frame()); }
    static void livingMap(ReadinessAuthority.PhysicalReadLease lease) { livingMap(Objects.requireNonNull(lease).frame()); }
    private static void livingMap(Complete frame) {
        var snapshot = frame.semantic();
        StrictJson.require(OpportunityJson.bool(snapshot.get("map_ready"), "map_ready"), "action/query requires an actual ready map");
        var player = OpportunityJson.object(snapshot.get("played_character"), "played_character");
        StrictJson.require(OpportunityJson.bool(player.get("alive"), "alive")
                && OpportunityJson.integer(player.get("character_id"), "character_id").equals(frame.identity().frame().identity().player()), "actual played character is not the live bound actor");
        StrictJson.require(OpportunityJson.integer(snapshot.get("episode_character_id"), "episode_character_id").equals(frame.identity().frame().identity().player()), "actual episode actor is unreconciled");
        StrictJson.require(snapshot.members().containsKey("one_life_terminal_reason")
                && snapshot.get("one_life_terminal_reason") == OpportunityJson.Nil.INSTANCE, "terminal or unknown life state cannot grant an ordinary action/query");
    }
    /** Complete semantic DATA shares the existing full Driver lane; proposal/request limits remain unchanged. */
    static void requireSemanticOriginal(Complete frame,RawJson semantic) {
        Objects.requireNonNull(frame);Objects.requireNonNull(semantic);
        StrictJson.require(DriverJson.object(semantic.bytes(),DriverJson.MAX_NATIVE_BYTES).equals(frame.semantic()),
                "archived semantic body differs from the actual assembler result");
    }
    static void exact(ExactRef reference, byte[] bytes) {
        StrictJson.require(reference.bytes() == bytes.length && reference.sha256().equals(ActionCodec.sha256(bytes)), "archived original bytes/SHA changed");
    }
}

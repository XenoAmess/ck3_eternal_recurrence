package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Root-private first SAVE only. Real physical originals never grant ordinary gameplay/planning readiness. */
public final class RootFirstCheckpointGuard implements ActionPorts.GuardPort {
    @FunctionalInterface public interface FirstSaveAdmission {
        /** Root must replay its actual private Begun and exact retained Stage/request on this original writer. */
        void require(ContinuityStorePort.Session borrowed, WriterContracts.Head actualLockedHead,
                ActionCommand retainedFirstSave) throws IOException;
    }
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final RootLifecycleAuthority physical;
    private final RootExecutableBindings installed;
    private final SessionIdentity owner;
    private final G2Source source;
    private final CheckpointRequest.ObservationPort firstObservations;
    private final ActionCommand retained;
    private final byte[] retainedBody;
    private final FirstSaveAdmission admission;
    private final Clock clock;
    private final String authorityId;
    private final ThreadLocal<Boolean> checking = new ThreadLocal<>();

    /** Only the actual same-package Core constructs this guard inside its private first-SAVE route. */
    RootFirstCheckpointGuard(ContinuityWriter writer, NativeOutcomeArchive archive, RootLifecycleAuthority physical,
            RootExecutableBindings installed, SessionIdentity owner, G2Source source,
            CheckpointRequest.ObservationPort firstObservations, ActionCommand retainedFirstSave,
            FirstSaveAdmission actualBegun, Clock clock, String authorityId) {
        this.writer = Objects.requireNonNull(writer); this.archive = Objects.requireNonNull(archive);
        this.physical = Objects.requireNonNull(physical); this.installed = Objects.requireNonNull(installed);
        this.owner = Objects.requireNonNull(owner); this.source = Objects.requireNonNull(source);
        this.firstObservations = Objects.requireNonNull(firstObservations); retained = Objects.requireNonNull(retainedFirstSave);
        admission = Objects.requireNonNull(actualBegun); this.clock = Objects.requireNonNull(clock);
        this.authorityId = StrictJson.text(authorityId);
        require(archive.writer() == writer, "first SAVE must retain the actual sole writer/archive");
        require(retained.origin() instanceof CommandOrigin.Gameplay && retained.operation().equals(RootSaveRuntime.OPERATION)
                && retained.arguments().members().isEmpty()
                && retained.expected().observerSchema().equals(CheckpointRequestFactory.OBSERVER_SCHEMA),
                "first SAVE guard accepts only the actual shared SAVE request shape");
        require(retained.source().equals(source) && source.machineId().equals(owner.machineId())
                && retained.sessionId().equals(owner.sessionId()) && retained.before().machineId().equals(owner.machineId())
                && retained.before().game().equals(owner.game()), "first SAVE source/Game/session differs from its actual private owner");
        retainedBody = ActionCodec.encodeCommand(retained);
        definition();
    }

    @Override public GuardEvidence verify(WriterContracts.Head actualLockedHead, ActionCommand command) {
        Objects.requireNonNull(actualLockedHead); Objects.requireNonNull(command);
        require(checking.get() == null, "first SAVE guard cannot recursively collect another physical observation");
        require(Arrays.equals(retainedBody, ActionCodec.encodeCommand(command)), "first SAVE guard cannot authorize another command/body/deadline");
        checking.set(Boolean.TRUE);
        try {
            ContinuityStorePort.Session same = writer.borrowedSession();
            current(same, actualLockedHead); admission.require(same, actualLockedHead, retained);
            var definition = definition();
            var sourcePins = new ArrayList<>(List.of(pin(same, source.sourceRef()), pin(same, definition.implementationSource()), pin(same, definition.decoderSource())));
            // The same stable first-checkpoint producer must run outside the physical Driver facts freeze.
            CheckpointRequest.Readiness first;
            try { first = firstObservations.observe(command.deadline()); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); var failure = new InterruptedIOException("actual first SAVE readiness interrupted");
                failure.initCause(interrupted); throw failure;
            }
            require(first.mapReady() && first.paused() && first.saveEligible(), "actual first SAVE physical stability is unavailable: " + first.reason());
            require(first.observed().equals(retained.before()) && first.source().equals(source) && first.sessionId().equals(owner.sessionId()),
                    "first SAVE stable observation differs from the exact retained original command");
            var firstNativePin = same.capturePin(first.nativeEvidence(), WriterContracts.MAX_PIN_BYTES); same.verifyPin(firstNativePin); sourcePins.add(firstNativePin);
            byte[] firstPacket = archive.readArtifact(same, first.nativeEvidence(), WriterContracts.MAX_PIN_BYTES);
            require(firstPacket.length == first.nativeEvidence().bytes() && DriverJson.sha256(firstPacket).equals(first.nativeEvidence().sha256()),
                    "first SAVE stable original packet bytes changed");
            var decodedFirst = NativeWire.decode(firstPacket);
            require(decodedFirst instanceof NativeWire.Snapshot, "first SAVE stable original is not an actual native snapshot");
            var firstNative = (NativeWire.Snapshot) decodedFirst;
            require(firstNative.snapshotId().equals(first.observed().frame().snapshotId())
                    && firstNative.revision().equals(first.observed().frame().identity().nativeRevision()),
                    "first SAVE stable original packet differs from its actual frame identity");
            current(same, actualLockedHead); admission.require(same, actualLockedHead, retained);
            return physical.withSnapshot(same, command.deadline(), lease -> {
                current(same, actualLockedHead); admission.require(same, actualLockedHead, retained); lease.assertCurrent(same);
                Complete frame = lease.ordinary().orElseThrow(() -> new IOException("first SAVE lacks actual living complete native/Driver originals"));
                require(frame.identity().equals(retained.before()) && frame.identity().equals(first.observed())
                        && frame.source().equals(source) && frame.sessionId().equals(owner.sessionId())
                        && !frame.observedAt().isBefore(first.observedAt()),
                        "first SAVE physical capture changed the actual stable frame/source/session");
                // The two real captures may have different framed byte encodings. Verify each original separately,
                // then compare their actual native state in the checked JSON domain; never substitute one reference.
                var actualNative = lease.fullSnapshot().actual();
                var stableOriginal = new NativeObservationPort.ObservedFrame(actualNative.session(),
                        firstNative.snapshotId(), firstNative.revision(), new RawJson(firstNative.state().value()),
                        firstPacket, first.observedAt());
                require(DriverObservationAssembler.canonicalNativeState(stableOriginal).semantic().equals(
                        DriverObservationAssembler.canonicalNativeState(actualNative).semantic()),
                        "first SAVE physical native state changed after the real stable observation");
                require(lease.fullSnapshot().actual().session().machineId().equals(owner.machineId())
                        && lease.fullSnapshot().actual().session().game().equals(owner.game())
                        && lease.fullSnapshot().actual().session().sessionId().equals(owner.sessionId()), "first SAVE physical session differs from its private owner");
                require(NativeReadinessCollector.checkpointEligibility(frame.semantic())
                        == org.xar.ck3.control.application.session.SessionPorts.CheckpointEligibility.SAFE,
                        "foreground or terminal physical state cannot authorize first SAVE");
                require(OpportunityJson.bool(frame.semantic().get("paused"), "paused")
                        && OpportunityJson.bool(frame.semantic().get("map_ready"), "map_ready"), "first SAVE requires the actual paused map");
                require(lease.bridgeCapabilities().contains(definition.requiredCapability().orElseThrow()),
                        "actual physical HELLO does not advertise the installed SAVE capability");
                var semantic = physical.semantic(same, owner, lease);
                var sameArchive = archive.withSession(same);
                var values = lease.bridgeCapabilities().stream().sorted().<OpportunityJson.Value>map(OpportunityJson.Text::new).toList();
                var capabilityBytes = new RawJson(DriverJson.encode(new OpportunityJson.Obj(Map.of("bridge_capabilities", new OpportunityJson.Arr(values)))));
                ExactRef capability = sameArchive.preserveMaterial(capabilityBytes);
                require(capabilityBytes.equals(sameArchive.loadMaterial(capability)), "first SAVE received HELLO capability archive changed");
                var originals = new RootGuardEvidence.PhysicalReadOriginals(frame, semantic, lease.originalHello(), lease.originalHeartbeat(),
                        lease.sourceQualification().proof(), capability);
                ExactRef basis = RootGuardEvidence.preservePhysicalRead(originals, command.operation(), authorityId, sameArchive, actualLockedHead);
                Instant until = lease.validUntil().isBefore(command.deadline()) ? lease.validUntil() : command.deadline();
                GuardEvidence result = new GuardEvidence(new CommandOrigin.Gameplay(frame.identity()), source, frame.sessionId(),
                        frame.connectionGeneration(), command.operation(), frame.originalEvidence(), lease.originalHello(), authorityId,
                        frame.observedAt(), until, List.of(basis));
                RootGuardEvidence.requireHistory(result, sameArchive, same);
                lease.sourceQualification().assertCurrent(same); lease.assertCurrent(same);
                for (var pin : sourcePins) same.verifyPin(pin);
                require(definition.equals(definition()), "actual installed SAVE binding changed inside first-checkpoint guard");
                current(same, actualLockedHead); admission.require(same, actualLockedHead, retained);
                require(clock.instant().isBefore(until), "first SAVE physical guard expired before publication");
                return result;
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual private first SAVE guard unavailable", failure); }
        finally { checking.remove(); }
    }
    private ExecutableStepBindings.InstalledStep definition() {
        var definition = installed.resolve(RootSaveRuntime.OPERATION).orElseThrow(() -> new IllegalArgumentException("actual installed SAVE producer is missing"));
        require(definition.kind() == ExecutableStepBindings.Kind.ACTION && definition.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && definition.requiredCapability().equals(Optional.of("game.command.save-checkpoint")), "first SAVE cannot borrow another operation/mode/capability");
        return definition;
    }
    private WriterContracts.Pin pin(ContinuityStorePort.Session same, ExactRef source) throws IOException {
        require(source.bytes() > 0 && java.nio.file.Path.of(source.path()).isAbsolute(), "actual first SAVE installed source required");
        var pin = same.capturePin(source, WriterContracts.MAX_PIN_BYTES); same.verifyPin(pin); return pin;
    }
    private void current(ContinuityStorePort.Session same, WriterContracts.Head expected) throws IOException {
        writer.requireSession(same); var actual = same.head();
        require(actual.digest().equals(expected.digest()) && actual.documents().equals(expected.documents())
                && actual.absent().equals(expected.absent()) && actual.indexRepairs().equals(expected.indexRepairs())
                && actual.snapshotNeedsRecovery() == expected.snapshotNeedsRecovery(), "first SAVE did not receive the actual current same-lock writer Head");
        require(actual.state().machineId().equals(owner.machineId()) && clock.instant().isBefore(retained.deadline()),
                "first SAVE writer machine or original deadline changed");
    }
}

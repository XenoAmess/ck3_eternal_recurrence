package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Old episode subject and the actual native current-player token are distinct facts, never an ordinary gameplay identity. */
public record LifecycleIdentity(String machineId, GameGeneration game, String sessionId,
        BigInteger connectionGeneration, Subject subject, Frame frame, CurrentPlayer currentPlayer,
        TerminalReason terminalReason, Evidence evidence, Instant observedAt) {
    public record Subject(BigInteger characterId, String episodeRunId, long episodeEpoch, long driverVersion) {
        public Subject { NativeCharacterId.of(characterId); StrictJson.text(episodeRunId); StrictJson.safe(episodeEpoch, 0); StrictJson.safe(driverVersion, 0); }
    }
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw,
            boolean paused, boolean mapReady) {
        public Frame {
            StrictJson.text(snapshotId); FrontendFrame.positive(revision); FrontendFrame.positive(nativeRevision);
            Objects.requireNonNull(dateRaw); StrictJson.require(dateRaw.bitLength() <= 63, "exact signed i64 native lifecycle date required");
        }
    }
    public sealed interface CurrentPlayer permits Missing, Null, Character { }
    public record Missing() implements CurrentPlayer { }
    public record Null() implements CurrentPlayer { }
    public record Character(BigInteger characterId, boolean alive) implements CurrentPlayer {
        public Character { NativeCharacterId.of(characterId); }
    }
    public enum TerminalReason {
        MISSING("played_character_missing"), DEAD("played_character_dead"), CHANGED("played_character_changed");
        private final String wire;
        TerminalReason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
        public static TerminalReason fromWire(String value) {
            for (TerminalReason reason : values()) if (reason.wire.equals(value)) return reason;
            throw new IllegalArgumentException("actual native lifecycle reason is unknown");
        }
    }
    public record Evidence(ExactRef nativePacket, ExactRef helloPacket, ExactRef observationManifest,
            ExactRef originalDriver, java.util.Optional<ExactRef> completeSourceQualification) {
        public Evidence {
            Objects.requireNonNull(completeSourceQualification);
            var refs = java.util.stream.Stream.concat(List.of(nativePacket, helloPacket, observationManifest, originalDriver).stream(),completeSourceQualification.stream()).toList();
            StrictJson.require(new java.util.HashSet<>(refs).size() == refs.size(), "distinct lifecycle original evidence roles required");
            for (ExactRef ref : refs) StrictJson.require(ref.bytes() > 0, "actual lifecycle physical source required");
        }
        public Evidence(ExactRef nativePacket,ExactRef helloPacket,ExactRef observationManifest,
                ExactRef originalDriver,ExactRef completeSourceQualification) {
            this(nativePacket,helloPacket,observationManifest,originalDriver,java.util.Optional.of(completeSourceQualification));
        }
        public List<ExactRef> originals() {
            return java.util.stream.Stream.concat(List.of(nativePacket,helloPacket,observationManifest,originalDriver).stream(),completeSourceQualification.stream()).toList();
        }
    }
    public LifecycleIdentity {
        StrictJson.require(machineId != null && !machineId.equals("unknown") && machineId.matches("[a-z0-9][a-z0-9-]{0,63}"), "explicit lifecycle machine required");
        Objects.requireNonNull(game); StrictJson.text(sessionId); FrontendFrame.positive(connectionGeneration);
        Objects.requireNonNull(subject); Objects.requireNonNull(frame); Objects.requireNonNull(currentPlayer);
        Objects.requireNonNull(terminalReason); Objects.requireNonNull(evidence); Objects.requireNonNull(observedAt);
        boolean matches = switch (terminalReason) {
            case MISSING -> currentPlayer instanceof Missing || currentPlayer instanceof Null;
            case DEAD -> currentPlayer instanceof Character character && !character.alive() && character.characterId().equals(subject.characterId());
            case CHANGED -> currentPlayer instanceof Character character && !character.characterId().equals(subject.characterId());
        };
        StrictJson.require(matches, "actual current-player token does not support the source-bound lifecycle reason");
    }
    public ExactRef nativeEvidence() { return evidence.nativePacket(); }
    public ExactRef capabilityEvidence() { return evidence.helloPacket(); }
    public List<ExactRef> supportingEvidence() { return java.util.stream.Stream.concat(List.of(evidence.observationManifest(), evidence.originalDriver()).stream(), evidence.completeSourceQualification().stream()).toList(); }
    public boolean sameSession(LifecycleIdentity other) {
        return other != null && machineId.equals(other.machineId) && game.equals(other.game) && sessionId.equals(other.sessionId)
                && connectionGeneration.equals(other.connectionGeneration) && sameEpisode(other);
    }
    public boolean sameEpisode(LifecycleIdentity other) {
        return other != null && subject.characterId().equals(other.subject.characterId())
                && subject.episodeRunId().equals(other.subject.episodeRunId()) && subject.episodeEpoch() == other.subject.episodeEpoch();
    }
    public boolean sameGuardFrame(LifecycleIdentity other) {
        return sameSession(other) && other.subject.driverVersion() >= subject.driverVersion()
                && frame.equals(other.frame) && currentPlayer.equals(other.currentPlayer) && terminalReason == other.terminalReason
                && sameBytes(nativeEvidence(), other.nativeEvidence()) && sameBytes(capabilityEvidence(), other.capabilityEvidence());
    }
    public String bindingSha256() { return ActionCodec.sha256(StrictJson.canonical(LifecycleIdentityCodec.encode(this), 64 * 1024)); }
    private static boolean sameBytes(ExactRef first, ExactRef second) { return first.bytes() == second.bytes() && first.sha256().equals(second.sha256()); }
}

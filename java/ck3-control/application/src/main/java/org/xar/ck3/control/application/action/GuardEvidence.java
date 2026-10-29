package org.xar.ck3.control.application.action;

import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import java.util.List;
import java.util.HashSet;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Produced by the real guarded observer. A parsed or constructed record grants no authority. */
public record GuardEvidence(CommandOrigin origin, G2Source source, String sessionId,
        BigInteger connectionGeneration, OperationKey operation, ExactRef nativeEvidence,
        ExactRef capabilityEvidence, String authorityId, Instant observedAt, Instant validUntil,
        List<ExactRef> supportingEvidence) {
    public GuardEvidence {
        Objects.requireNonNull(origin); Objects.requireNonNull(source); StrictJson.text(sessionId);
        FrontendFrame.positive(connectionGeneration); Objects.requireNonNull(operation);
        Objects.requireNonNull(nativeEvidence); Objects.requireNonNull(capabilityEvidence); StrictJson.text(authorityId);
        StrictJson.require(nativeEvidence.bytes() > 0 && capabilityEvidence.bytes() > 0, "real native/capability references required");
        StrictJson.require(origin.machineId().equals(source.machineId()), "guard source machine drift");
        if (origin instanceof CommandOrigin.Frontend frontend) {
            var identity = frontend.identity();
            StrictJson.require(identity.frontendSessionId().equals(sessionId) && identity.connectionGeneration().equals(connectionGeneration)
                    && identity.nativeEvidence().equals(nativeEvidence) && identity.capabilityEvidence().equals(capabilityEvidence), "frontend guard proof/session/connection drift");
        }
        if (origin instanceof CommandOrigin.LifecycleTerminal lifecycle) {
            var identity = lifecycle.identity();
            StrictJson.require(identity.sessionId().equals(sessionId) && identity.connectionGeneration().equals(connectionGeneration)
                    && identity.nativeEvidence().equals(nativeEvidence) && identity.capabilityEvidence().equals(capabilityEvidence),
                    "lifecycle guard changed actual native snapshot, hello, session or connection");
        }
        if (origin instanceof CommandOrigin.Reconciliation reconciliation) {
            var identity = reconciliation.identity();
            StrictJson.require(identity.source().equals(source) && identity.sessionId().equals(sessionId)
                    && identity.connectionGeneration().equals(connectionGeneration) && identity.nativeEvidence().equals(nativeEvidence)
                    && identity.capabilityEvidence().equals(capabilityEvidence), "reconciliation guard changed its canonical pending/factual source or native session originals");
        }
        if (origin instanceof CommandOrigin.PhysicalStatusOnly physical) {
            var identity = physical.identity();
            StrictJson.require(identity.source().equals(source) && identity.sessionId().equals(sessionId)
                    && identity.connectionGeneration().equals(connectionGeneration) && identity.nativeEvidence().equals(nativeEvidence)
                    && identity.helloEvidence().equals(capabilityEvidence) && operation.value().equals(PhysicalStatusIdentity.OPERATION)
                    && identity.observedAt().equals(observedAt),
                    "physical status guard changed actual native/HELLO/source/session/original observation");
        }
        Objects.requireNonNull(observedAt); Objects.requireNonNull(validUntil);
        StrictJson.require(!validUntil.isBefore(observedAt), "guard validity interval regressed");
        supportingEvidence = List.copyOf(supportingEvidence);
        StrictJson.require(supportingEvidence.size() <= 128, "bounded guard supporting evidence closure required");
        var unique = new HashSet<ExactRef>();
        for (ExactRef ref : supportingEvidence) StrictJson.require(ref.bytes() > 0 && unique.add(ref), "nonempty unique guard supporting originals required");
        StrictJson.require(!(origin instanceof CommandOrigin.LifecycleTerminal || origin instanceof CommandOrigin.Reconciliation || origin instanceof CommandOrigin.PhysicalStatusOnly) || !supportingEvidence.isEmpty(),
                "terminal and reconciliation guards require a real source-bound physical evidence basis");
    }
    /** Historical guard bodies have no adopted supporting closure; this constructor grants no authority. */
    public GuardEvidence(CommandOrigin origin, G2Source source, String sessionId,
            BigInteger connectionGeneration, OperationKey operation, ExactRef nativeEvidence,
            ExactRef capabilityEvidence, String authorityId, Instant observedAt, Instant validUntil) {
        this(origin, source, sessionId, connectionGeneration, operation, nativeEvidence, capabilityEvidence,
                authorityId, observedAt, validUntil, List.of());
    }
    public GuardEvidence(ObservationIdentity observed, G2Source source, String sessionId,
            BigInteger connectionGeneration, OperationKey operation, ExactRef nativeEvidence,
            ExactRef capabilityEvidence, String authorityId, Instant observedAt, Instant validUntil) {
        this(new CommandOrigin.Gameplay(observed), source, sessionId, connectionGeneration, operation,
                nativeEvidence, capabilityEvidence, authorityId, observedAt, validUntil);
    }
    public GuardEvidence(ObservationIdentity observed, G2Source source, String sessionId,
            BigInteger connectionGeneration, OperationKey operation, ExactRef nativeEvidence,
            ExactRef capabilityEvidence, String authorityId, Instant observedAt, Instant validUntil,
            List<ExactRef> supportingEvidence) {
        this(new CommandOrigin.Gameplay(observed), source, sessionId, connectionGeneration, operation,
                nativeEvidence, capabilityEvidence, authorityId, observedAt, validUntil, supportingEvidence);
    }
    public ObservationIdentity observed() { return origin.requireGameplay(); }
}


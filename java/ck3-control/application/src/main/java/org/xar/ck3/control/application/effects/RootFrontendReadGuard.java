package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.List;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;

/** Frontend read branch never asks for map, player or episode readiness. */
public final class RootFrontendReadGuard implements PlanningReadCoordinator.ReadGuardPort {
    private final FrontendAuthority authority; private final Supplier<ContinuityStorePort.Session> borrowed;
    private final ActionPorts.OutcomeArchive archive; private final G2Source source; private final Clock clock;
    private final String authorityId; private final OriginalEvidencePort originals; private final RootReadContractCatalog catalog;
    public RootFrontendReadGuard(FrontendAuthority authority, Supplier<ContinuityStorePort.Session> borrowed,
            ActionPorts.OutcomeArchive archive, G2Source source, Clock clock, String authorityId, OriginalEvidencePort originals, RootReadContractCatalog catalog) {
        this.authority = Objects.requireNonNull(authority); this.borrowed = Objects.requireNonNull(borrowed); this.archive = Objects.requireNonNull(archive);
        this.source = Objects.requireNonNull(source); this.clock = Objects.requireNonNull(clock); this.authorityId = StrictJson.text(authorityId);
        this.originals = Objects.requireNonNull(originals); this.catalog = Objects.requireNonNull(catalog);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head, PlanningReadRequest request, ReadContract<?> contract) {
        StrictJson.require(catalog.containsIdentity(contract) && request.origin() instanceof CommandOrigin.Frontend
                && contract.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION && contract.operation().equals(request.operation()) && source.equals(request.source()), "exact registered frontend read origin/source/contract required");
        try {
            var session = RootGuardChecks.session(borrowed, head); RootGuardChecks.source(session, contract.sourceRef()); RootGuardChecks.source(session, source.sourceRef());
            var sameArchive = archive.withSession(session);
            return authority.current(session, request.origin().requireFrontend(), request.deadline(), actual -> {
                StrictJson.require(actual.executableOperations().contains(request.operation()), "actual frontend route does not admit this exact installed read");
                contract.requiredCapability().ifPresent(cap -> StrictJson.require(actual.bridgeCapabilities().contains(cap), "actual bridge did not advertise the frontend query capability"));
                var binding = RootFrontendGuardEvidence.binding(actual, request.origin().requireFrontend(), source, request.sessionId(), request.operation(), request.deadline(), head, authorityId, clock, session, sameArchive, originals);
                return new PlanningReadGuard(binding, FrontendGuardBinding.digest(binding.origin().requireFrontend()));
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual frontend read authority unavailable", failure); }
    }

    /** Equal query evidence is usable only inside its actual issuer's live whole-work read scope. */
    @Override public void verifyFrontendReadContinuation(WriterContracts.Head head, PlanningReadRequest request,
            ReadContract<?> contract, PlanningReadGuard before, PlanningReadGuard after) {
        StrictJson.require(catalog.containsIdentity(contract) && request.origin() instanceof CommandOrigin.Frontend
                && contract.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION && contract.operation().equals(request.operation())
                && source.equals(request.source()) && before.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION
                && after.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION,
                "frontend continuation needs the identical installed source/origin/read contract");
        try {
            var session = RootGuardChecks.session(borrowed, head);
            RootGuardChecks.source(session, contract.sourceRef()); RootGuardChecks.source(session, source.sourceRef());
            var sameArchive = archive.withSession(session);
            authority.currentSourceBoundRead(session, request.origin().requireFrontend(), request.deadline(), actual -> {
                StrictJson.require(actual.executableOperations().contains(request.operation()), "actual frontend scope does not admit this installed read");
                contract.requiredCapability().ifPresent(cap -> StrictJson.require(actual.bridgeCapabilities().contains(cap), "actual frontend scope lost its advertised read capability"));
                var binding = RootFrontendGuardEvidence.binding(actual, request.origin().requireFrontend(), source, request.sessionId(),
                        request.operation(), request.deadline(), head, authorityId, clock, session, sameArchive, originals);
                var expected = new PlanningReadGuard(binding, FrontendGuardBinding.digest(binding.origin().requireFrontend()));
                StrictJson.require(expected.equals(before) && expected.equals(after),
                        "both frontend read guards must exactly match the issuer's same active source-bound lease");
                return null;
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual source-bound frontend continuation unavailable", failure); }
    }
}

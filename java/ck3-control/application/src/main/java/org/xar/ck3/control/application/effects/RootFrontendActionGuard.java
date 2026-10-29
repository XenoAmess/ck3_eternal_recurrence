package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Map;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;

/** Frontend branch of the sole Root action guard, using the actual held frontend authority. */
public final class RootFrontendActionGuard implements ActionPorts.GuardPort {
    private final FrontendAuthority authority; private final Supplier<ContinuityStorePort.Session> borrowed;
    private final ActionPorts.OutcomeArchive archive; private final G2Source source; private final Clock clock;
    private final String authorityId; private final OriginalEvidencePort originals; private final RootExecutableBindings installed;
    public RootFrontendActionGuard(FrontendAuthority authority, Supplier<ContinuityStorePort.Session> borrowed,
            ActionPorts.OutcomeArchive archive, G2Source source, Clock clock, String authorityId, OriginalEvidencePort originals, RootExecutableBindings installed) {
        this.authority = Objects.requireNonNull(authority); this.borrowed = Objects.requireNonNull(borrowed); this.archive = Objects.requireNonNull(archive);
        this.source = Objects.requireNonNull(source); this.clock = Objects.requireNonNull(clock); this.authorityId = StrictJson.text(authorityId);
        this.originals = Objects.requireNonNull(originals); this.installed = Objects.requireNonNull(installed);
    }
    @Override public GuardEvidence verify(WriterContracts.Head head, ActionCommand command) {
        StrictJson.require(command.origin() instanceof CommandOrigin.Frontend && command.source().equals(source), "frontend origin/source required");
        var producer = installed.resolve(command.operation(), command.origin()).orElseThrow(() -> new IllegalArgumentException("frontend action has no installed exact native producer"));
        StrictJson.require((producer.kind() == ExecutableStepBindings.Kind.ACTION || producer.kind() == ExecutableStepBindings.Kind.COMPOSITE)
                && producer.guardMode() == ReadContract.GuardMode.FRONTEND_SESSION, "frontend guard cannot authorize an installed read/gameplay operation");
        try {
            var session = RootGuardChecks.session(borrowed, head); RootGuardChecks.source(session, producer.implementationSource());
            RootGuardChecks.source(session, producer.decoderSource()); RootGuardChecks.source(session, source.sourceRef());
            var sameArchive = archive.withSession(session);
            return authority.current(session, command.origin().requireFrontend(), command.deadline(), actual -> {
                StrictJson.require(actual.executableOperations().contains(command.operation()), "actual frontend route does not admit the exact action");
                producer.requiredCapability().ifPresent(cap -> StrictJson.require(actual.bridgeCapabilities().contains(cap), "actual bridge did not advertise the installed frontend action capability"));
                return RootFrontendGuardEvidence.binding(actual, command.origin().requireFrontend(), source, command.sessionId(), command.operation(), command.deadline(), head, authorityId, clock, session, sameArchive, originals);
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual frontend action authority unavailable", failure); }
    }
}

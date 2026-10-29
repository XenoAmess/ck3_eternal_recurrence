package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.ritecreation.RiteCreationContract;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;

/** Fresh Root uses its actual canonical episode. A constructor string or nearby state directory cannot issue a scope.
 * This authority borrows the caller's already-held collector/Driver frame; it performs no observation, write or submit. */
public final class RootRiteCreationScopeAuthority implements RootRiteCreationRuntimeFactory.ScopeProvider {
    private final RootCoreBoundPorts ports;private final Duration freshness;private final Clock clock;
    public RootRiteCreationScopeAuthority(RootCoreBoundPorts actualPorts,Duration actualFreshness,Clock actualClock){
        ports=Objects.requireNonNull(actualPorts);freshness=Objects.requireNonNull(actualFreshness);clock=Objects.requireNonNull(actualClock);
        if(freshness.isNegative()||freshness.isZero()||freshness.compareTo(Duration.ofMinutes(1))>0)throw new IllegalArgumentException("finite actual Root frame freshness required");
    }
    @Override public RiteCreationContract.Scope require(DriverObservationAssembler.Complete actual)throws IOException {
        Objects.requireNonNull(actual);var same=ports.borrowedSession();ports.requireSession(same);String head=same.head().digest();
        var context=ports.requireCurrent(same,new SessionIdentity(actual.identity().machineId(),actual.identity().game(),actual.sessionId()));
        var deadline=actual.observedAt().plus(freshness);context.requireCurrent(deadline);
        if(context.clock()!=clock||!actual.source().equals(context.source()))throw new IOException("Rite scope belongs to another actual Root source/clock");
        context.game().launchPlan().sources().requireLoadedClass(RootRiteCreationScopeAuthority.class);
        RiteCreationContract.Scope result=context.collector().borrowCurrent(same,actual.identity(),deadline,lease->{
            if(!lease.frame().equals(actual))throw new IOException("Rite scope lost the same actual held physical frame");
            return context.adopted().authority().withFrozenFacts(same,frozen->{
                if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw new IOException("actual canonical Driver is unavailable for the Rite scope");
                var driver=known.driver().session();String episode=driver.episodeRunId();
                if(episode.isEmpty()||!episode.equals(actual.identity().frame().episodeRunId())
                        ||!known.stamp().game().equals(context.game().generation())
                        ||driver.bridgePid()!=context.game().generation().pid()
                        ||!driver.actorId().equals(actual.identity().frame().identity().player()))
                    throw new IOException("fresh one-life Root Rite scope requires its exact actual canonical Game/episode/actor");
                return new RiteCreationContract.EpisodeScope(episode);
            });
        });
        ports.requireSession(same);if(!head.equals(same.head().digest()))throw new IOException("Rite scope capture changed its original writer head");
        return result;
    }
}

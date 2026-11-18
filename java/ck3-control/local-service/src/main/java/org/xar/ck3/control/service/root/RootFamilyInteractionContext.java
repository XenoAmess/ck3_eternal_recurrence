package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.FamilyPorts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPolicy;
import org.xar.ck3.control.nativebridge.capabilities.interactions.RootInteractionContextProjection;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One live Family context gate; historical ProjectedSource.decode remains on its original producer. */
public final class RootFamilyInteractionContext {
    @FunctionalInterface public interface Projected {
        FamilyPorts.ProjectedRead read(InteractionModels.Context actual) throws IOException;
    }
    @FunctionalInterface public interface Query<T> {
        PlanningReadResult<T> read(InteractionModels.Context actual) throws IOException;
    }
    private sealed interface Source permits Qualified,Unmigrated { }
    private record Qualified(RootInteractionContextProjection projection) implements Source { }
    private record Unmigrated(KnownInteractionsRuntimeInstaller.ConfiguredBuild build,
            KnownPendingInteractionPolicy.ContextReadPort reads) implements Source { }
    private final Source source;
    private RootFamilyInteractionContext(Source source) { this.source=source; }
    public static RootFamilyInteractionContext qualified(RootInteractionContextProjection actual) {
        return new RootFamilyInteractionContext(new Qualified(Objects.requireNonNull(actual)));
    }
    /** Explicit configured source DATA, never a fabricated projection or a Native qualification. */
    public static RootFamilyInteractionContext configuredUnavailable(KnownInteractionsRuntimeInstaller.ConfiguredBuild build) {
        Objects.requireNonNull(build);StrictJson.require(!build.qualified(),"qualified Family context must retain its real projection");
        return new RootFamilyInteractionContext(new Unmigrated(build,
                KnownPendingInteractionPolicy.typedUnavailable(build.version(),build.executableSha256())));
    }
    public static RootFamilyInteractionContext from(KnownInteractionsRuntimeInstaller sameKnown) {
        Objects.requireNonNull(sameKnown);var build=sameKnown.sources().configuredBuild();
        return build.qualified()?qualified(sameKnown.projection()):configuredUnavailable(build);
    }
    /** Original getter remains strict. Unmigrated callers must use the typed gate. */
    public RootInteractionContextProjection requireProjection() {
        if(source instanceof Qualified qualified)return qualified.projection();
        throw new IllegalStateException(KnownInteractionsRuntimeInstaller.ConfiguredBuild.UNMIGRATED_REASON);
    }
    public FamilyPorts.ProjectedRead projected(PlanningRequest request,Complete held,Obj flat,
            Projected actualKnown) throws IOException {
        Objects.requireNonNull(request);Objects.requireNonNull(flat);Objects.requireNonNull(actualKnown);
        requireFrame(held,request.deadline());
        StrictJson.require(held.identity().equals(request.before())&&held.source().equals(request.source())
                &&held.sessionId().equals(request.sessionId()),"Family context crossed the actual held planning frame/source/session");
        if(source instanceof Qualified qualified)
            return Objects.requireNonNull(actualKnown.read(qualified.projection().project(held,request.deadline())));
        var unavailable=(Unmigrated)source;requireSource(held,unavailable);
        var read=unavailable.reads().current(request);
        StrictJson.require(read instanceof KnownPendingInteractionPolicy.Unavailable,
                "unmigrated Family source cannot manufacture an available interaction context");
        var missing=((KnownPendingInteractionPolicy.Unavailable)read).result();
        return new FamilyPorts.ProjectedRead(flat,new PlanningReadResult.Unavailable<>(missing.reason(),missing.original(),
                missing.decodeFailure(),missing.observedFailure()));
    }
    /** Public held-frame reads have no PlanningRequest; do not invent one merely to publish Unavailable. */
    public <T> PlanningReadResult<T> query(Complete held,Instant deadline,
            Query<T> actualKnown) throws IOException {
        Objects.requireNonNull(actualKnown);requireFrame(held,deadline);
        if(source instanceof Qualified qualified)
            return Objects.requireNonNull(actualKnown.read(qualified.projection().project(held,deadline)));
        var unavailable=(Unmigrated)source;requireSource(held,unavailable);
        return new PlanningReadResult.Unavailable<>(KnownInteractionsRuntimeInstaller.ConfiguredBuild.UNMIGRATED_REASON,Optional.empty());
    }
    private static void requireFrame(Complete held,Instant deadline) {
        Objects.requireNonNull(held);Objects.requireNonNull(deadline);
        StrictJson.require(deadline.isAfter(held.observedAt()),"Family context deadline predates the held frame publication");
    }
    private static void requireSource(Complete held,Unmigrated actual) {
        String retained=held.source().exactBuild();
        StrictJson.require(retained.equalsIgnoreCase(actual.build().executableSha256())
                ||retained.equalsIgnoreCase(actual.build().version()+"@sha256:"+actual.build().executableSha256()),
                "Family unmigrated context crossed the configured exact build source");
    }
    /** Repeated Shared.from(sameKnown) keeps the original value identity, including the legacy projection hash. */
    @Override public boolean equals(Object other) {
        if(!(other instanceof RootFamilyInteractionContext value))return false;
        if(source instanceof Qualified a)return value.source instanceof Qualified b&&a.projection().equals(b.projection());
        return value.source instanceof Unmigrated b&&((Unmigrated)source).build().equals(b.build());
    }
    @Override public int hashCode() {
        return source instanceof Qualified value?value.projection().hashCode():((Unmigrated)source).build().hashCode();
    }
}

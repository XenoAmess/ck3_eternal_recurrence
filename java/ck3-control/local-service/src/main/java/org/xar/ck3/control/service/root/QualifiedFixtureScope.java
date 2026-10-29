package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Typed seam only. The actual RootAssembly issuer retains the original first Driver, same writer,
 * and AC's private upfront-parent/child continuation; data records or an implementation class alone grant nothing.
 * Every method must reject outside that issuer's active callback, after adoption/closure, or on changed source/owner.
 */
public sealed interface QualifiedFixtureScope permits RootFixtureQualifiedScope {
    void requireContext(RootRuntimeContext identical)throws IOException;
    void requireCurrent(Session identicalBorrowed)throws IOException;
    String parentActionId();
    ExactRef policySource();
    /** Actual canonical parent and settled-child history from the original reader under this same writer. */
    List<OpportunityJson.Obj> history(Session identicalBorrowed)throws IOException;
    @FunctionalInterface interface Work<T> {T apply(ReadinessAuthority.LeaseSnapshot actual)throws IOException;}
    <T>T withCurrent(Session identicalBorrowed,Instant originalDeadline,Work<T> work)throws IOException;
    /** Identical installed contract, original request/frame and same Core's guarded read coordinator. */
    <T>PlanningReadResult.Known<T> read(Session identicalBorrowed,ReadContract<T> identicalContract,
            PlanningReadRequest originalRequest)throws IOException;
    /** Independent actual native observation of this original child; no submitted action or replay. */
    Optional<Complete> after(Session identicalBorrowed,ActionCommand originalChild,Instant originalDeadline)throws IOException;
}

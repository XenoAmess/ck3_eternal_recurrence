package org.xar.ck3.control.service;

import jakarta.enterprise.context.ApplicationScoped;
import java.time.Instant;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2SoftwareFixtureSourceProvider;
import org.xar.ck3.control.g2.context.G2WindowsRootSources;
import org.xar.ck3.control.g2.context.RootG2HandoffWire;
import org.xar.ck3.control.g2.context.RootG2RequestHandoff;

/** Application-owned custody. There is deliberately no HTTP ticket-issuance endpoint. */
@ApplicationScoped
public class RootG2HandoffHost {
    private final RootG2RequestHandoff requests = new RootG2RequestHandoff(256);
    public RootG2RequestHandoff.Ticket issueSoftware(G2SoftwareFixtureSourceProvider source, long childPid,
            Milestone milestone, ProjectionJson payload, Instant deadline) {
        return requests.issueSoftware(source, childPid, milestone, payload, deadline);
    }
    public RootG2RequestHandoff.Ticket issueNative(G2WindowsRootSources source, G2WindowsRootSources.NativeArrival arrival,
            long childPid, Milestone milestone, ProjectionJson payload, Instant deadline) {
        return requests.issueNative(source, arrival, childPid, milestone, payload, deadline);
    }
    public G2CallContextProducer.Result redeem(RootG2HandoffWire.Input input) {
        return requests.redeem(input.ticketId(), input.childPid(), input.childCreationFiletimeDecimal(), input.milestone(), input.payload());
    }
}

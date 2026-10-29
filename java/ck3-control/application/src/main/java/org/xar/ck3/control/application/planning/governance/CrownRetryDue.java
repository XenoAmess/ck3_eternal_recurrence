package org.xar.ck3.control.application.planning.governance;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.NativeCalendarObservation;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec;
import org.xar.ck3.control.wave3.governance.crownretry.CrownRetryPolicy;

/** Actual same-writer publication + same-frame calendar input for the existing life-advance horizon. */
public final class CrownRetryDue {
    private final ContinuityStorePort writer;
    private final SessionAuthority writerAuthority;
    private final CrownRetryPublication publication;
    public CrownRetryDue(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority, CrownRetryPublication originalPublication) {
        writer = Objects.requireNonNull(soleWriter); writerAuthority = Objects.requireNonNull(actualWriterAuthority); publication = Objects.requireNonNull(originalPublication);
    }

    public VerifiedDue capture(ContinuityStorePort.Session borrowed, CrownRetryPublication.ImportProof proof,
            ObservationIdentity current, G2Source source, OpportunityJson.Obj originalSemantic, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(proof); Objects.requireNonNull(current);
        Objects.requireNonNull(source); Objects.requireNonNull(originalSemantic); Objects.requireNonNull(callerDeadline);
        writerAuthority.require(borrowed);
        var head = borrowed.head();
        NativeCalendarObservation.project(current, source, originalSemantic);
        CrownRetryPolicy.Frame verifiedFrame = publication.requireCurrentPublication(proof, borrowed, current, source, callerDeadline);
        DomainBodies.Read read = borrowed.readDomain(DomainBodies.Slot.CROWN);
        StrictJson.require(read instanceof DomainBodies.Available,
                "actual current CROWN body is unavailable for the due-date consumer");
        DomainBodies.Available actual = (DomainBodies.Available) read;
        StrictJson.require(actual.reference().equals(proof.body()),
                "CROWN due input changed after the same-writer publication guard");
        var input = StrictJson.object(); input.put("schema", CrownRetryCodec.MATCH_SCHEMA);
        input.put("bridge_pid", current.game().pid()); input.set("snapshot", OpportunityJson.toNode(originalSemantic));
        input.set("state", StrictJson.parse(actual.canonicalBody(), CrownRetryPublication.MAX_BODY_BYTES));
        input.putNull("law_key");
        CrownRetryCodec.MatchRequest parsed = CrownRetryCodec.decodeMatch(StrictJson.canonical(input, CrownRetryPublication.MAX_BODY_BYTES));
        StrictJson.require(verifiedFrame.equals(parsed.frame()),
                "CROWN due codec frame differs from the exact same-frame native calendar");
        writerAuthority.require(borrowed);
        StrictJson.require(head.digest().equals(borrowed.head().digest()),
                "writer changed while producing the actual CROWN due input");
        return new VerifiedDue(this, proof, current, source, verifiedFrame, parsed.state(), head.digest());
    }

    /** Revalidation before the actual readiness supplier publishes its RuntimeFacts. */
    public void requireCurrent(ContinuityStorePort.Session borrowed, VerifiedDue due, Instant callerDeadline) throws IOException {
        Objects.requireNonNull(due); Objects.requireNonNull(callerDeadline); writerAuthority.require(borrowed);
        StrictJson.require(due.issuer == this && due.headDigest.equals(borrowed.head().digest()),
                "CROWN due input crossed its actual source producer or writer head");
        StrictJson.require(due.frame.equals(publication.requireCurrentPublication(due.proof, borrowed, due.observed, due.source, callerDeadline)),
                "current CROWN publication no longer matches the captured due frame");
    }

    /**
     * Private typed data from actual publication/readback; a legacy Hint or JSON cannot construct it.
     * Its only operation clips a selected horizon. It never authorizes law submission or final terms.
     */
    public static final class VerifiedDue {
        private final CrownRetryDue issuer;
        private final CrownRetryPublication.ImportProof proof;
        private final ObservationIdentity observed;
        private final G2Source source;
        private final CrownRetryPolicy.Frame frame;
        private final CrownRetryPolicy.State state;
        private final String headDigest;
        private VerifiedDue(CrownRetryDue issuer, CrownRetryPublication.ImportProof proof,
                ObservationIdentity observed, G2Source source, CrownRetryPolicy.Frame frame,
                CrownRetryPolicy.State state, String headDigest) {
            this.issuer = issuer; this.proof = proof; this.observed = observed; this.source = source;
            this.frame = frame; this.state = state; this.headDigest = headDigest;
        }
        public BigInteger horizonDays(ObservationIdentity actualFrame, BigInteger requestedDays,
                boolean queryEnabled, boolean pausedQueryEnabled) {
            StrictJson.require(observed.equals(actualFrame),
                    "CROWN horizon consumer must use the exact captured Game birth, episode and complete native frame");
            return CrownRetryPolicy.horizonDays(frame, state, requestedDays, queryEnabled, pausedQueryEnabled);
        }
        /** A due query bypasses only optional review cadence; fresh native final terms still decide the law. */
        public boolean currentlyDue(ObservationIdentity actualFrame) {
            StrictJson.require(observed.equals(actualFrame), "Crown query due consumer crossed the exact captured native frame");
            return CrownRetryPolicy.matchingRetry(frame, state, null)
                    .filter(hint -> hint.retryDateRaw().compareTo(frame.dateRaw()) <= 0).isPresent();
        }
        public ObservationIdentity observed() { return observed; }
        public DomainBodies.BodyRef publicationBody() { return proof.body(); }
        public boolean authorizesAction() { return false; }
        public long savedDayCredit() { return 0; }
    }
}

package org.xar.ck3.control.g2.context;

import java.security.SecureRandom;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;

/** Root issues a narrow child/request ticket; the real NativeArrival stays only in this JVM. */
public final class RootG2RequestHandoff {
    public enum Scope { SOFTWARE_FIXTURE_ONLY, RETAINED_NATIVE_READ_ONLY }
    public record Ticket(String ticketId, long childPid, String childCreationFiletimeDecimal,
            Milestone milestone, String payloadSha256, String expiresAtUtc, Scope scope) {
        public Ticket {
            if (ticketId == null || !ticketId.matches("[0-9a-f]{64}") || childPid < 1 || childPid > 0xffff_ffffL
                    || childCreationFiletimeDecimal == null || !childCreationFiletimeDecimal.matches("[1-9][0-9]{0,19}")
                    || new java.math.BigInteger(childCreationFiletimeDecimal).bitLength() > 64
                    || payloadSha256 == null || !payloadSha256.matches("[0-9a-f]{64}")) { throw new IllegalArgumentException("exact Root child/request ticket required"); }
            Objects.requireNonNull(milestone); Objects.requireNonNull(scope); Instant.parse(expiresAtUtc);
        }
    }
    private record Pending(Ticket ticket, WindowsJobProcess.ProcessIdentity child,
            G2CallContextProducer.Provider source) { }
    private final int maximumPending;
    private final ConcurrentHashMap<String, Pending> pending = new ConcurrentHashMap<>();
    private final SecureRandom random = new SecureRandom();
    public RootG2RequestHandoff(int maximumPending) {
        if (maximumPending < 1 || maximumPending > 4096) { throw new IllegalArgumentException("finite Root ticket custody required"); }
        this.maximumPending = maximumPending;
    }
    /** Fixture mode is visibly separate and never calls the Native producer or grants Native scope. */
    public Ticket issueSoftware(G2SoftwareFixtureSourceProvider source, long childPid, Milestone milestone,
            ProjectionJson payload, Instant deadline) {
        Objects.requireNonNull(source);
        return issue(source, Scope.SOFTWARE_FIXTURE_ONLY, childPid, milestone, payload, deadline);
    }
    /** Actual retained opaque arrival is not serialized; every redemption revalidates it at source. */
    public Ticket issueNative(G2WindowsRootSources source, G2WindowsRootSources.NativeArrival arrival,
            long childPid, Milestone milestone, ProjectionJson payload, Instant deadline) {
        Objects.requireNonNull(source); Objects.requireNonNull(arrival);
        G2CallContextProducer.Provider retained = (actualMilestone, actualPayload) -> {
            try (G2WindowsRootSources.RequestScope scope = source.bindRequest(actualMilestone, actualPayload, arrival)) {
                Objects.requireNonNull(scope); return source.context(actualMilestone, actualPayload);
            }
        };
        return issue(retained, Scope.RETAINED_NATIVE_READ_ONLY, childPid, milestone, payload, deadline);
    }
    private synchronized Ticket issue(G2CallContextProducer.Provider source, Scope scope, long childPid,
            Milestone milestone, ProjectionJson payload, Instant deadline) {
        Objects.requireNonNull(milestone); G2CallContextProducer.requirePayloadToken(payload); Objects.requireNonNull(deadline);
        if (!deadline.isAfter(Instant.now())) { throw new IllegalArgumentException("fresh Root handoff deadline required"); }
        if (pending.size() >= maximumPending) { throw new IllegalStateException("Root pending request custody is full"); }
        WindowsJobProcess.ProcessIdentity child = WindowsJobProcess.observeLiveProcess(childPid).identity();
        G2CallContextProducer.Result qualified = source.context(milestone, payload);
        if (!(qualified instanceof G2CallContextProducer.Available)) { throw new IllegalStateException("Root source unavailable; no request ticket issued: " + qualified); }
        byte[] nonce = new byte[32]; random.nextBytes(nonce);
        Ticket ticket = new Ticket(HexFormat.of().formatHex(nonce), child.pid(), child.creationFiletimeDecimal(), milestone,
                G2RetainedNativeSourceProvider.sha256(payload.bytes()), deadline.toString(), scope);
        if (pending.putIfAbsent(ticket.ticketId(), new Pending(ticket, child, source)) != null) { throw new IllegalStateException("Root nonce collision; no ticket replaced"); }
        return ticket;
    }
    /** Consume before validation: unknown/wrong/expired attempts never replay the source request. */
    public G2CallContextProducer.Result redeem(String ticketId, long childPid, String childCreationFiletimeDecimal,
            Milestone milestone, ProjectionJson payload) {
        G2CallContextProducer.requirePayloadToken(payload);
        if (ticketId == null || !ticketId.matches("[0-9a-f]{64}")) { return unavailable("Root request ticket is malformed"); }
        Pending actual = pending.remove(ticketId);
        if (actual == null) { return unavailable("Root request ticket is missing or already consumed"); }
        Ticket ticket = actual.ticket();
        if (ticket.childPid() != childPid || !ticket.childCreationFiletimeDecimal().equals(childCreationFiletimeDecimal)
                || ticket.milestone() != milestone || !ticket.payloadSha256().equals(G2RetainedNativeSourceProvider.sha256(payload.bytes()))
                || !Instant.parse(ticket.expiresAtUtc()).isAfter(Instant.now())) { return unavailable("Root request ticket binding differs or expired"); }
        try {
            if (!actual.child().equals(WindowsJobProcess.observeLiveProcess(childPid).identity())) { return unavailable("actual child process identity changed"); }
            G2CallContextProducer.Result result = actual.source().context(milestone, payload);
            if (!actual.child().equals(WindowsJobProcess.observeLiveProcess(childPid).identity())) { return unavailable("actual child exited or changed during context read"); }
            return result;
        } catch (RuntimeException rejected) { return unavailable("actual Root source/child observation unavailable"); }
    }
    private static G2CallContextProducer.Unavailable unavailable(String detail) {
        return new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, detail);
    }
}

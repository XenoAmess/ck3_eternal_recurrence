package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Real frontend originals stay separate from Gameplay SEM/Driver facts. */
public final class RootFrontendGuardEvidence {
    public static final String SCHEMA = "xar.java.root-frontend-guard-original-basis/v2";
    private static final Set<String> FIELDS = Set.of("schema", "operation", "authority_id", "route_receipt", "native_packet", "hello", "heartbeat", "capabilities", "supporting_evidence");
    private RootFrontendGuardEvidence() { }
    /** Produce original guard DATA only from the concrete issuer's already active same-writer read scope.
     * The raw lease binder stays package-owned; this does not install an action, read or physical permit.
     */
    public static GuardEvidence sourceBound(FrontendAuthority authority, FrontendIdentity expected, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, WriterContracts.Head head, String authorityId,
            Clock clock, ContinuityStorePort.Session session, ActionPorts.OutcomeArchive archive, OriginalEvidencePort originals) throws IOException {
        java.util.Objects.requireNonNull(authority);
        return authority.currentSourceBoundRead(session, expected, deadline,
                actual -> binding(actual, expected, source, sessionId, operation, deadline, head, authorityId, clock, session, archive, originals));
    }
    static GuardEvidence binding(FrontendAuthority.LeaseSnapshot lease, FrontendIdentity expected, G2Source source,
            String sessionId, OperationKey operation, Instant deadline, WriterContracts.Head head, String authorityId,
            Clock clock, ContinuityStorePort.Session session, ActionPorts.OutcomeArchive archive, OriginalEvidencePort originals) throws IOException {
        var actual = lease.identity(); Instant now = clock.instant();
        StrictJson.require(expected.sameSession(actual) && actual.frontendSessionId().equals(sessionId) && lease.source().equals(source)
                && actual.machineId().equals(head.state().machineId()), "actual frontend Game/source/session/connection changed");
        StrictJson.require(now.isBefore(deadline) && !now.isBefore(lease.observedAt()) && !now.isAfter(lease.validUntil()), "actual frontend lease is stale");
        StrictJson.require(lease.originalRoute().nativeOk(), "actual independent frontend route query failed");
        byte[] route = originals.read(session, actual.nativeEvidence(), StrictJson.EXPLICIT_MAX_BYTES); RootGuardChecks.exact(actual.nativeEvidence(), route);
        StrictJson.require(java.util.Arrays.equals(route, lease.originalRoute().originalPacket()), "actual frontend frame differs from the original route packet");
        for (var ref : List.of(actual.capabilityEvidence(), lease.originalHeartbeat())) RootGuardChecks.exact(ref, originals.read(session, ref, StrictJson.EXPLICIT_MAX_BYTES));
        ExactRef receipt = archive.preserve(lease.originalRoute());
        StrictJson.require(lease.originalRoute().equals(archive.load(receipt)), "actual frontend route receipt archive changed");
        ObjectNode capabilities = StrictJson.object(); var steps = capabilities.putArray("executable_operations");
        lease.executableOperations().stream().map(OperationKey::value).sorted().forEach(steps::add);
        var bridge = capabilities.putArray("bridge_capabilities"); lease.bridgeCapabilities().stream().sorted().forEach(bridge::add);
        RawJson material = EffectJson.raw(capabilities); ExactRef materialRef = archive.preserveMaterial(material);
        StrictJson.require(material.equals(archive.loadMaterial(materialRef)), "actual frontend capabilities archive changed");
        var row = StrictJson.object(); row.put("schema", SCHEMA); row.put("operation", operation.value()); row.put("authority_id", authorityId);
        row.set("route_receipt", receipt.toJson()); row.set("native_packet", actual.nativeEvidence().toJson()); row.set("hello", actual.capabilityEvidence().toJson());
        row.set("heartbeat", lease.originalHeartbeat().toJson()); row.set("capabilities", materialRef.toJson());
        var supporting = row.putArray("supporting_evidence");
        for (ExactRef ref : lease.supportingEvidence()) {
            RootGuardChecks.exact(ref, originals.read(session, ref, org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES + 4)); supporting.add(ref.toJson());
        }
        RawJson basis = EffectJson.raw(row); ExactRef basisRef = archive.preserveMaterial(basis);
        StrictJson.require(basis.equals(archive.loadMaterial(basisRef)), "actual frontend guard basis archive changed");
        Instant until = lease.validUntil().isBefore(deadline) ? lease.validUntil() : deadline;
        return new GuardEvidence(new CommandOrigin.Frontend(actual), source, sessionId, actual.connectionGeneration(), operation,
                actual.nativeEvidence(), actual.capabilityEvidence(), authorityId, lease.observedAt(), until, List.of(basisRef));
    }
    public static void verify(GuardEvidence guard, ActionPorts.OutcomeArchive archive, ContinuityStorePort.Session session, OriginalEvidencePort originals) throws IOException {
        StrictJson.require(guard.origin() instanceof CommandOrigin.Frontend && guard.supportingEvidence().size() == 1, "actual frontend guard originals unavailable");
        var ref = guard.supportingEvidence().getFirst(); RawJson body = archive.loadMaterial(ref); RootGuardChecks.exact(ref, body.bytes());
        var row = StrictJson.object(EffectJson.parse(body), FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))) && guard.operation().value().equals(StrictJson.text(row.get("operation")))
                && guard.authorityId().equals(StrictJson.text(row.get("authority_id"))) && guard.nativeEvidence().equals(ExactRef.fromJson(row.get("native_packet")))
                && guard.capabilityEvidence().equals(ExactRef.fromJson(row.get("hello"))), "archived frontend guard basis binding changed");
        for (String field : List.of("native_packet", "hello", "heartbeat")) {
            ExactRef packet = ExactRef.fromJson(row.get(field)); RootGuardChecks.exact(packet, originals.read(session, packet, StrictJson.EXPLICIT_MAX_BYTES));
        }
        ExactRef cap = ExactRef.fromJson(row.get("capabilities")); RootGuardChecks.exact(cap, archive.loadMaterial(cap).bytes());
        var support = row.get("supporting_evidence");
        StrictJson.require(support != null && support.isArray() && support.size() <= 16
                && (guard.origin().requireFrontend().frame() instanceof FrontendFrame.Menu || !support.isEmpty()), "frontend snapshot original Driver closure unavailable");
        var unique = new java.util.HashSet<ExactRef>();
        for (var node : support) {
            ExactRef actual = ExactRef.fromJson(node); StrictJson.require(unique.add(actual), "duplicate frontend original evidence");
            RootGuardChecks.exact(actual, originals.read(session, actual, org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES + 4));
        }
        var outcome = archive.load(ExactRef.fromJson(row.get("route_receipt")));
        StrictJson.require(outcome instanceof NativeActionPort.AckReceived && ((NativeActionPort.AckReceived) outcome).nativeOk()
                && java.util.Arrays.equals(((NativeActionPort.AckReceived) outcome).originalPacket(), originals.read(session, guard.nativeEvidence(), StrictJson.EXPLICIT_MAX_BYTES)), "archived frontend route packet changed");
    }
}

package org.xar.ck3.control.application.planning.governance;

import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceFixtures.*;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Software producer/consumer role test; no actual worker128 receipt or Game transport. */
final class GovernanceCollectorReadReferenceTest {
    @Test void crownReturnsTheExistingV2ReadReferenceInsteadOfTheDispatchReference() {
        roundTrip(PlanningReadReceipt.ArchiveVersion.CURRENT_V2);
    }

    @Test void retainedV4ReadAndItsAttachmentAreReturnedWithoutRearchiving() {
        roundTrip(PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4);
    }

    @Test void unknownReadStaysUnavailableAndDoesNotArchiveOrBecomeCrownEvidence() {
        var fixture = new Fixture(PlanningReadReceipt.ArchiveVersion.CURRENT_V2);
        fixture.unavailable = true;
        var result = assertInstanceOf(Unavailable.class, fixture.collector().crown(fixture.request));
        assertEquals("original native read is UNKNOWN", result.reason());
        assertEquals(1, fixture.reads);
        assertEquals(0, fixture.preserveCalls);
        assertEquals(0, fixture.loadCalls);
    }

    @Test void wrongFrameIsStillRejectedBeforeAnOriginalReferenceIsPublished() {
        var fixture = new Fixture(PlanningReadReceipt.ArchiveVersion.CURRENT_V2);
        fixture.wrongFrame = true;
        assertThrows(IllegalArgumentException.class, () -> fixture.collector().crown(fixture.request));
        assertEquals(1, fixture.reads);
        assertEquals(0, fixture.preserveCalls);
        assertEquals(0, fixture.loadCalls);
    }

    private static void roundTrip(PlanningReadReceipt.ArchiveVersion version) {
        var fixture = new Fixture(version);
        var known = assertInstanceOf(Known.class, fixture.collector().crown(fixture.request));
        assertEquals(List.of(fixture.readRef), known.originals());
        // This is the same API used by RootCrownRetryRuntime.observe at its real failure point.
        PlanningReadReceipt loaded = fixture.archive.loadRead((ExactRef) known.originals().getFirst());
        assertSame(fixture.receipt, loaded);
        assertEquals(version, loaded.archiveVersion());
        assertEquals(version == PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4,
                loaded.retainedMaterial().isPresent());
        assertEquals(fixture.raw, fixture.contract.decode(loaded));
        assertEquals(1, fixture.reads);
        assertEquals(0, fixture.preserveCalls, "the already retained read must not be serialized again");
        assertEquals(1, fixture.loadCalls);
    }

    private static final class Fixture {
        final PlanningRequest request = request();
        final Obj raw = crown(request).originalReadback();
        final PlanningReadReceipt.ArchiveVersion version;
        final byte[] dispatchMetadata = StrictJson.canonical(StrictJson.object().put("schema", "xar.native-dispatch-archive/v1"));
        final ExactRef dispatchRef = new ExactRef("unit-dispatch.json", dispatchMetadata.length, ActionCodec.sha256(dispatchMetadata));
        final ExactRef readRef = new ExactRef("unit-planning-read.json", 17, "b".repeat(64));
        final ReadContract<Obj> contract;
        final ActionPorts.OutcomeArchive archive;
        PlanningReadReceipt receipt;
        int reads, preserveCalls, loadCalls;
        boolean unavailable, wrongFrame;

        Fixture(PlanningReadReceipt.ArchiveVersion actualVersion) {
            version = actualVersion;
            var operation = new OperationKey("unit-crown-query");
            contract = new ReadContract<>("unit-crown-definition", operation, Optional.empty(), "unit-crown-permission",
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, REF,
                    input -> new NativeRequest(operation.value(), Optional.empty(), new RawJson(encode(input.arguments()))),
                    original -> object(parse(original.original().originalResultToken().orElseThrow().bytes()), "Crown token"));
            archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        if (method.getName().equals("preserve")) { preserveCalls++; return dispatchRef; }
                        if (method.getName().equals("loadRead")) {
                            loadCalls++;
                            if (readRef.equals(args[0])) return receipt;
                            throw new IllegalArgumentException("dispatch reference is not a planning READ reference");
                        }
                        throw new AssertionError("unexpected archive operation: " + method.getName());
                    });
        }

        GovernanceCollector collector() {
            PlanningReadPort port = new PlanningReadPort() {
                @Override public <T> PlanningReadResult<T> read(ReadContract<T> actual, PlanningReadRequest input) {
                    reads++;
                    if (unavailable) return new PlanningReadResult.Unavailable<>("original native read is UNKNOWN",
                            Optional.of(new NativeActionPort.Unknown("unit-crown-read", "actual unknown", new byte[]{1}, Optional.empty())));
                    PlanningReadRequest captured = input;
                    if (wrongFrame) {
                        var other = request(10, false, List.of());
                        captured = new PlanningReadRequest(other.before(), other.source(), other.sessionId(), input.operation(), input.arguments(), input.deadline());
                    }
                    var binding = new GuardEvidence(captured.before(), captured.source(), captured.sessionId(), BigInteger.ONE,
                            captured.operation(), REF, REF, "unit-authority", NOW, NOW.plusSeconds(20));
                    var guard = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
                    var ack = new NativeActionPort.AckReceived("unit-crown-read", true, Optional.of(new RawJson(encode(raw))),
                            new RawJson(encode(new Obj(Map.of()))), new byte[]{1});
                    Optional<PlanningReadReceipt.RetainedMaterial> material = version == PlanningReadReceipt.ArchiveVersion.RETAINED_MATERIAL_V4
                            ? Optional.of(new PlanningReadReceipt.RetainedMaterial(PlanningReadReceipt.RetainedMaterial.Kind.FAMILY_RELATION_EXPORT,
                                    new ExactRef(java.nio.file.Path.of("unit-export.json").toAbsolutePath().normalize().toString(), 1, "c".repeat(64))))
                            : Optional.empty();
                    receipt = new PlanningReadReceipt(captured, actual.contractId(), "unit-crown-read", guard, guard, ack,
                            Optional.empty(), version, material);
                    return new PlanningReadResult.Known<>(actual.decode(receipt), receipt, readRef);
                }
            };
            var definitions = new GovernanceCollector.Reads(Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(),
                    Optional.of(contract), Optional.empty(), Optional.empty());
            return new GovernanceCollector(port, archive, current -> new Known<>(durable(current), List.of(REF)), definitions);
        }
    }
}

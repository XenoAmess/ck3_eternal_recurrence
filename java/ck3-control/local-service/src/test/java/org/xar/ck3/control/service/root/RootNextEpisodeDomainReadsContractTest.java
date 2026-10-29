package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.IntStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;

/** Contract metadata/refusals only: no Core, physical lease, native source or domain import authority is constructed. */
final class RootNextEpisodeDomainReadsContractTest {
    private static final ExactRef SOURCE = new ExactRef("domain-read-metadata-only", 1, "0".repeat(64));

    @Test void onlyTheIdenticalInstalledAndExplicitlyAllowedContractCanPassTheMetadataBoundary() {
        var actual = contract("collection", true, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        var sibling = contract("other-domain", true, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        var catalog = RootReadContractCatalog.staticOnly(List.of(actual, sibling));
        var allowed = RootNextEpisodeDomainReads.allowedContracts(catalog, List.of(actual));
        assertDoesNotThrow(() -> RootNextEpisodeDomainReads.requireAllowed(catalog, allowed, actual));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.requireAllowed(catalog, allowed, sibling));
        var copied = contract("collection", true, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        assertEquals(actual.contractId(), copied.contractId()); assertEquals(actual.sourceRef(), copied.sourceRef());
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.requireAllowed(catalog, allowed, copied));
        assertThrows(UnsupportedOperationException.class, () -> allowed.add(sibling));
    }

    @Test void AContractWithoutAnExplicitPureDecoderOrWithAnotherOriginCannotEnterTheDomainReadSet() {
        var liveOnly = contract("live-only", false, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        var frontend = contract("frontend", true, ReadContract.GuardMode.FRONTEND_SESSION);
        var catalog = RootReadContractCatalog.staticOnly(List.of(liveOnly, frontend));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.allowedContracts(catalog, List.of(liveOnly)));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.allowedContracts(catalog, List.of(frontend)));
    }

    @Test void EmptyDuplicateAndUnboundedDomainReadListsCannotCreateABroaderReadRegistration() {
        var contract = contract("one", true, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP);
        var catalog = RootReadContractCatalog.staticOnly(List.of(contract));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.allowedContracts(catalog, List.of()));
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.allowedContracts(catalog, List.of(contract, contract)));
        List<ReadContract<?>> tooMany = IntStream.range(0, 17)
                .<ReadContract<?>>mapToObj(index -> contract("read-" + index, true, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP)).toList();
        var full = RootReadContractCatalog.staticOnly(tooMany);
        assertThrows(IllegalArgumentException.class, () -> RootNextEpisodeDomainReads.allowedContracts(full, tooMany));
    }

    private static ReadContract<RawJson> contract(String id, boolean pure, ReadContract.GuardMode mode) {
        var operation = new OperationKey("domain-read-fixture-" + id);
        Function<PlanningReadReceipt, RawJson> decode = receipt -> receipt.original().originalResultToken().orElseThrow();
        java.util.function.BiFunction<PlanningReadRequest, String, NativeRequest> prepare = (request, requestId) ->
                new NativeRequest(operation.value(), Optional.of("game.query.fixture"), new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        if (pure) return new ReadContract<>("domain-read-fixture/" + id, operation, Optional.of("game.query.fixture"), "fixture-read-only",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, mode, SOURCE, prepare, decode, decode);
        return new ReadContract<>("domain-read-fixture/" + id, operation, Optional.of("game.query.fixture"), "fixture-read-only",
                ReadContract.PermissionMode.ADVERTISED_CAPABILITY, ReadContract.WireProfile.EXECUTE_STEP, mode, SOURCE, prepare, decode);
    }
}

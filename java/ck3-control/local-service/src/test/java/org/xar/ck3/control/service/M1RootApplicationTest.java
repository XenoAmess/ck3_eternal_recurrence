package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2CallContextProducer;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.m1.M1Operation;
import org.xar.ck3.control.g2.m1.M1Research;
import org.xar.ck3.control.g2.m1.M1ResultConsumers;

/** Exercises the actual application supplier branch without starting a second service. */
final class M1RootApplicationTest {
    @Test void missingTrueRootProviderReturnsUnavailableWithoutInvokingAnyDomain() {
        var calls = new AtomicInteger();
        var app = new M1RootApplication(new G2CallContextHost(), failIfCalled(calls));
        var missing = assertInstanceOf(M1RootApplication.Unavailable.class,
                app.evaluate(M1Operation.REALM_FEEDBACK, utf8("{}")));
        assertEquals(G2CallContextProducer.Reason.ROOT_PROVIDER_MISSING, missing.sourceFailure().reason());
        assertEquals(0, calls.get());
    }

    @Test void missingActualExeRemainsUnavailableThroughTheConsumedProductionBoundary() {
        var context = new G2CallContextHost(); var calls = new AtomicInteger();
        var sourceFailure = new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE,
                "synthetic missing EXE input");
        context.installRootProvider((milestone, payload) -> sourceFailure);
        var result = assertInstanceOf(M1RootApplication.Unavailable.class,
                new M1RootApplication(context, failIfCalled(calls)).evaluate(M1Operation.REALM_FEEDBACK, utf8("{}")));
        assertSame(sourceFailure, result.sourceFailure()); assertEquals(0, calls.get());
    }

    @Test void anAvailableSourceDoesNotPromoteUnknownRealmFactsAndKeepsProviderIdentity() {
        var context = new G2CallContextHost(); var calls = new AtomicInteger();
        var source = new G2Source("synthetic-m1-application", "2026-10-22T00:00:00Z", "synthetic-unit-only",
                new ExactRef("synthetic:/native-unit", 1, "a".repeat(64)));
        context.installRootProvider((milestone, payload) -> {
            calls.incrementAndGet(); assertEquals(Milestone.M1, milestone);
            return new G2CallContextProducer.Available(new G2CallContextProducer.Context(source, "synthetic-root-application",
                    G2RetainedNativeSourceProvider.sha256(payload.bytes())));
        });
        var host = new G2ResearchHost(new G2ResearchEngine(List.of(new M1Research())));
        var result = assertInstanceOf(M1RootApplication.Evaluated.class,
                new M1RootApplication(context, host).evaluate(M1Operation.REALM_FEEDBACK, utf8("{}")));
        assertEquals(source, result.response().source()); assertEquals("synthetic-root-application", result.response().requestId());
        assertInstanceOf(M1ResultConsumers.UnavailableFeedback.class,
                M1ResultConsumers.realmFeedback(result.response().result().bytes()));
        assertEquals(1, calls.get());
    }
    private static G2ResearchHost failIfCalled(AtomicInteger calls) {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M1; }
            @Override public G2Response evaluate(G2Request request) {
                calls.incrementAndGet(); throw new AssertionError("unavailable source must not evaluate a domain");
            }
        };
        return new G2ResearchHost(new G2ResearchEngine(List.of(domain)));
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

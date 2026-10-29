package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeFailure;
import org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;

/** Same two registered Root handlers and capture producer; these DATA callbacks never impersonate a live Root/lease. */
final class RootContactPublicFailureTest {
    @Test void twoActualRegisteredQueryPathsKeepOriginalFailureInsteadOfEncodingUnavailableSuccess() throws Exception {
        var registry = new PublicBindings(); var calls = new AtomicInteger();
        var original = new NativeActionPort.Unknown("q", "actual native request unresolved after write", new byte[]{1}, Optional.empty());
        var unavailable = new PlanningReadResult.Unavailable<ContactScopeObservation>("actual coordinator reason", Optional.of(original));
        RootContactPublicProducts.register(registry, new ExactRef("software-contact-registration-source", 1, "a".repeat(64)),
                request -> { calls.incrementAndGet(); return RootContactPublicProducts.capture(new ContactScopeObservation.Projected(request.query()), unavailable); },
                request -> { calls.incrementAndGet(); return RootContactPublicProducts.capture(new ContactScopeObservation.Actual(request.query()), unavailable); });
        registry.freeze(Set.of(PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1, PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE));
        for (PublicMethod method : List.of(PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1, PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE)) {
            String input = method == PublicMethod.QUERY_PROJECTED_CONTACT_SCOPE_V1
                    ? "{\"subject_army_id\":0,\"target_province_id\":31,\"incoming_entry_province_id\":30,\"expected_revision\":\"9\"}"
                    : "{\"subject_army_id\":0,\"target_province_id\":31}";
            ContactScopeFailure failure = assertThrows(ContactScopeFailure.class,
                    () -> registry.lookup(method).orElseThrow().invoke(PublicBindings.present(new RawJson(input.getBytes(StandardCharsets.UTF_8)))));
            assertSame(unavailable, failure.unavailable().orElseThrow()); assertSame(original, failure.original().orElseThrow());
            assertEquals(ContactScopeFailure.Kind.UNCLASSIFIED_NATIVE, failure.kind());
        }
        assertEquals(2, calls.get(), "one actual collector invocation for each method; no resubmission");
        assertThrows(IllegalArgumentException.class, () -> registry.lookup(PublicMethod.QUERY_ACTUAL_CONTACT_SCOPE).orElseThrow()
                .invoke(PublicBindings.present(new RawJson("{\"subject_army_id\":true,\"target_province_id\":31}".getBytes(StandardCharsets.UTF_8)))));
        assertEquals(2, calls.get(), "invalid input cannot dispatch");
    }
}

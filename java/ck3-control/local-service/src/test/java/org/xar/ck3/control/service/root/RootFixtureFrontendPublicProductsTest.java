package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.frontendfixture.FrontendFixturePolicy;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;

/** The original public submitters take no arguments; callers cannot replace the frozen policy/profile. */
class RootFixtureFrontendPublicProductsTest {
    private static PublicBindings.Value value(String json) {
        return new PublicBindings.Value(new RawJson(json.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void bothOriginalNoArgumentToolsAcceptMissingOrAnEmptyObject() {
        for(var kind:FrontendFixturePolicy.Kind.values()) {
            assertEquals(new RootFixtureFrontendPublicProducts.Request(kind),RootFixtureFrontendPublicProducts.decode(kind,new PublicBindings.Missing()));
            assertEquals(new RootFixtureFrontendPublicProducts.Request(kind),RootFixtureFrontendPublicProducts.decode(kind,value("{}")));
        }
    }
    @Test void nullScalarAndCallerInjectedPolicyOrProfileCannotSelectAnotherFixture() {
        for(var kind:FrontendFixturePolicy.Kind.values()) {
            assertThrows(IllegalArgumentException.class,()->RootFixtureFrontendPublicProducts.decode(kind,new PublicBindings.Null()));
            for(String input:java.util.List.of("true","null","[]","{\"fixture_policy\":null}","{\"profile_directory\":\"D:/other\"}"))
                assertThrows(IllegalArgumentException.class,()->RootFixtureFrontendPublicProducts.decode(kind,value(input)));
        }
    }
}

package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;

/** Domain discriminator DATA only; no environment, producer receipt, process or admission is manufactured. */
final class MappedSavedProfileKindTest {
    @Test void mappedVanillaRequiresTheSameExactTypedEnvironmentDomain() {
        InitialEpisodePolicy.requireMappedSavedProfileKind(ProfileKind.SAVED_VANILLA);
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.requireMappedSavedProfileKind(ProfileKind.SAVED_PRODUCT_ONLY));
    }
    @Test void otherTypedDomainsAndUnknownCannotBecomeMappedVanilla() {
        for(var kind:ProfileKind.values())if(kind!=ProfileKind.SAVED_VANILLA)
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.requireMappedSavedProfileKind(kind));
        assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.requireMappedSavedProfileKind(null));
    }
}

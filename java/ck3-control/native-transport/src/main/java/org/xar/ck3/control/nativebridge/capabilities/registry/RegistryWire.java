package org.xar.ck3.control.nativebridge.capabilities.registry;

import org.xar.ck3.control.application.action.RawJson;

/** Internal serializers preserve the original integer domain; public routes select their own profile. */
public final class RegistryWire {
    private RegistryWire() { }
    public static RawJson encodeDirectory(EntityDirectory.Result directory) { return RegistryJson.encode(directory); }
    public static <E,I> RawJson encodeBundle(TurnBundle.Result<E,I> bundle) { return RegistryJson.encode(bundle); }
    public static RawJson encodePublicDirectory(EntityDirectory.Result directory) {
        return RegistryPublicProfile.encode(RegistryPublicProfile.Profile.ENTITY_DIRECTORY, encodeDirectory(directory));
    }
    public static <E,I> RawJson encodePublicBundle(TurnBundle.Result<E,I> bundle) {
        return RegistryPublicProfile.encode(RegistryPublicProfile.Profile.TURN_BUNDLE, encodeBundle(bundle));
    }
}

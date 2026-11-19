package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import org.junit.jupiter.api.Test;

/** API-surface check only: it constructs no Core, RootContext, Game or installation authority. */
final class SavedTransportInstallationAccessTest {
    @Test void lexicalInstallationAccessCannotBecomeAPublicTransportOrCurrentEntry() throws Exception {
        Class<?> access=Class.forName("org.xar.ck3.control.service.root.RootApplicationSession$SavedTransportInstallation");
        if(Boolean.getBoolean("xar.saved.transport.genuine")) {
            var expected=java.nio.file.Path.of(System.getProperty("xar.saved.transport.genuineJar")).toAbsolutePath().normalize();
            for(Class<?> type:new Class<?>[]{RootApplicationAssembly.class,RootApplicationSession.class,RootLifecycleRuntimeFactory.class,RootPendingUiRuntime.class}) {
                var owner=java.nio.file.Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
                assertEquals(expected,owner);assertTrue(java.nio.file.Files.isRegularFile(owner));assertTrue(java.nio.file.Files.size(owner)>1_048_576);
            }
        }
        assertFalse(Modifier.isPublic(access.getModifiers()));assertTrue(Modifier.isFinal(access.getModifiers()));
        assertEquals(1,access.getDeclaredConstructors().length);
        assertTrue(Modifier.isPrivate(access.getDeclaredConstructors()[0].getModifiers()));
        assertTrue(AutoCloseable.class.isAssignableFrom(access));
        for(var field:access.getDeclaredFields())assertTrue(Modifier.isPrivate(field.getModifiers()));
        assertFalse(Modifier.isPublic(access.getDeclaredMethod("require",RootRuntimeContext.class,
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class).getModifiers()));
        for(Class<?> type:new Class<?>[]{RootLifecycleRuntimeFactory.Installed.class,RootPendingUiRuntime.class}) {
            var scoped=Arrays.stream(type.getDeclaredMethods()).filter(m->Arrays.asList(m.getParameterTypes()).contains(access)).toList();
            assertEquals(2,scoped.size());for(var method:scoped)assertFalse(Modifier.isPublic(method.getModifiers()));
        }
        assertFalse(Modifier.isPublic(RootApplicationAssembly.Core.class.getDeclaredMethod("requireSavedTransportInstallation",
                org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class,RootApplicationSession.class).getModifiers()));
        assertTrue(Modifier.isPrivate(RootApplicationSession.class.getDeclaredMethod("prepareInitialSavedTransportContinuity",java.time.Instant.class).getModifiers()));
        assertTrue(Modifier.isPublic(RootSessionAccess.class.getDeclaredMethod("current").getModifiers()));
    }
}

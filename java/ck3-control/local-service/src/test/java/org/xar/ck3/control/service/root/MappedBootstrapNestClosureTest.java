package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import org.xar.ck3.control.platform.NativeSavedGameClone;
import org.xar.ck3.control.platform.NativeSavedGamePreparation;
import org.xar.ck3.control.platform.QualifiedCloneCustody;

/** Classfile DATA only. No native API initialization, child process, Native call or completed runtime receipt is manufactured. */
final class MappedBootstrapNestClosureTest {
    @Test void mappedRequiredNamesIncludeAllActualDeclaredNativeNestsIncludingPrivatePhaseAndWin32ApiProviders() {
        var names=RootBootstrapRuntime.requiredClasses(RootBootstrapProtocol.Mode.INITIAL_SAVED_MATERIALIZED_POLICY);
        for(Class<?> root:List.of(NativeSavedGameClone.class,QualifiedCloneCustody.class,
                NativeSavedGamePreparation.class,IdentityBearingFileAttributes.class)) {
            for(Class<?> member:root.getNestMembers())assertTrue(names.contains(member.getName()),member.getName());
        }
        assertTrue(names.contains("org.xar.ck3.control.platform.QualifiedCloneCustody$Phase"));
        assertTrue(names.contains("org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes$Api"));
        assertTrue(names.contains("org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes$AttributeApi"));
        assertTrue(names.contains("org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes$Data"));
        assertTrue(names.contains("org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes$DataApi"));
    }
    @Test void exactMappedClassRosterIsStableDistinctAndImmutable() {
        var mode=RootBootstrapProtocol.Mode.INITIAL_SAVED_MATERIALIZED_POLICY;
        var first=RootBootstrapRuntime.requiredClasses(mode);var second=RootBootstrapRuntime.requiredClasses(mode);
        assertEquals(first,second);assertEquals(first.size(),new HashSet<>(first).size());
        assertThrows(UnsupportedOperationException.class,()->first.add("unqualified"));
    }
    @Test void legacyModesKeepTheirExistingTopLevelRosterAndDoNotImplicitlyEnterMappedNativeClosure() {
        for(var mode:List.of(RootBootstrapProtocol.Mode.PROFILE,RootBootstrapProtocol.Mode.NORMAL_EXIT,
                RootBootstrapProtocol.Mode.FORMAL_RELEASE,RootBootstrapProtocol.Mode.ORIGINAL_DRIVER_RUN_PROFILE)) {
            var names=RootBootstrapRuntime.requiredClasses(mode);
            assertFalse(names.contains("org.xar.ck3.control.platform.QualifiedCloneCustody$Phase"));
            assertTrue(names.contains("org.xar.ck3.control.service.root.RootBootstrapRuntime"));
        }
    }
}

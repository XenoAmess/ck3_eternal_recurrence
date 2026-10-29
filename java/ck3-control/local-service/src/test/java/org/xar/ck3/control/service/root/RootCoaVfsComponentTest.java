package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Duration;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.*;
import org.xar.ck3.control.service.mcp.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.*;

/** Real shared Prepared/SDK/codec consumers, without a fabricated Core or executable native component. */
final class RootCoaVfsComponentTest {
    @Test void oneComponentOccupiesOnlyVfsAndDuplicateActualOwnerIsRejectedBeforeCore() {
        var component=new RootCoaVfs.Prepared(new CoaVfs.Limits(1L<<30,1L<<28),Duration.ofSeconds(30));
        assertEquals(Set.of(Method.VFS),component.methods());assertTrue(component.domainRegistrations().isEmpty());assertTrue(component.privatePermissions().isEmpty());
        var parent=new RootFrontendCoaPublicProducts.Prepared(List.of(component));assertEquals(Set.of(Method.VFS),parent.componentMethods());
        assertThrows(IllegalArgumentException.class,()->new RootFrontendCoaPublicProducts.Prepared(List.of(component,component)));
        assertThrows(IllegalArgumentException.class,()->new RootCoaVfs.Prepared(new CoaVfs.Limits(1,1),Duration.ZERO));
    }
    @Test void originalActualSdkDescriptorFeedsTheUniqueVfsRequestCodecAndRejectsUnknownAuthorityFields()throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(Method.VFS.publicName())).findFirst().orElseThrow();
        var value=org.xar.ck3.control.contracts.StrictJson.object().put("game_directory","C:/controlled/actual-game").put("logical_path","gfx/coat_of_arms/patterns/name.dds");
        var original=new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(value));var arguments=new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,java.util.Optional.of(original));descriptor.validateArguments(arguments);
        var decoded=(Vfs)FrontendCoaCodec.decode(Method.VFS,original);assertEquals("gfx/coat_of_arms/patterns/name.dds",decoded.logicalPath());
        value.put("maximum_source_bytes",Long.MAX_VALUE);var forged=new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(value));assertThrows(Exception.class,()->descriptor.validateArguments(new PublicMcpDirectory.Arguments(PublicMcpDirectory.Presence.VALUE,java.util.Optional.of(forged))));assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.decode(Method.VFS,forged));
        value.remove("maximum_source_bytes");value.putNull("logical_path");var missing=new RawJson(org.xar.ck3.control.contracts.StrictJson.canonical(value));assertThrows(IllegalArgumentException.class,()->FrontendCoaCodec.decode(Method.VFS,missing));
    }
}

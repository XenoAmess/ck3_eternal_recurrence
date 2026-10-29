package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Whole-Root test continuation. The fixture must supply its actual private assembly; this helper mints none. */
public final class RootCoaVfsActualEntryChecks {
    private RootCoaVfsActualEntryChecks() { }
    public static CallResult exerciseActual(McpExecutableDirectory.Complete actual,RawJson originalArguments)throws ToolFailure,RpcFailure,IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(originalArguments);FrontendCoaCodec.decode(FrontendCoaContract.Method.VFS,originalArguments);
        String name=FrontendCoaContract.Method.VFS.publicName();if(actual.directory().tools().stream().noneMatch(tool->tool.name().equals(name)))throw new IOException("actual full Root lacks its VFS component route");
        var result=actual.directory().invoke(new ToolCall(name,new Arguments(Presence.VALUE,Optional.of(originalArguments)),Optional.empty(),new McpCancellation()));
        var wrapper=org.xar.ck3.control.contracts.FullJsonTree.parse(result.bytes(),RawJson.MAXIMUM_BYTES);if(!wrapper.path("isError").asBoolean(false)){
            var projection=wrapper.get("structuredContent");StrictJson.require(projection!=null&&projection.isObject(),"actual VFS public result lacks its source projection");
            StrictJson.require(!projection.get("provenance").get("engine_resolver_called").booleanValue()&&!projection.get("provenance").get("resource_registration_observed").booleanValue(),"static asset winner must not become an actual engine-load claim");
        }return result;
    }
}

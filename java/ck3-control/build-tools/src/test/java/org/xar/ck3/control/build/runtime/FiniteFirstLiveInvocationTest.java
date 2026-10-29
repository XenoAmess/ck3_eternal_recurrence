package org.xar.ck3.control.build.runtime;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Real invocation input custody and distinct wire routing; no package or Game qualification. */
public final class FiniteFirstLiveInvocationTest {
    @TempDir Path temporary;
    @Test public void actualFiniteRequestKeepsItsOwnSchemaAndExactThreeArguments()throws Exception {
        Path source=temporary.resolve("finite-request.json");Files.writeString(source,"{\"software_protocol_original\":true}");
        var original=SharedSourceFiles.observe(source).source();
        var invocation=new JavaRuntimeLaunch.FiniteFirstLiveInvocation(original);
        var decoded=JavaRuntimeLaunch.FiniteFirstLiveInvocation.decode(invocation.encode());
        assertEquals(original,decoded.finiteRequest());
        assertEquals(List.of(original.path(),Long.toString(original.bytes()),original.sha256()),decoded.arguments());
        assertThrows(IOException.class,()->RootStartupInvocation.decode(invocation.encode()));
        assertThrows(UnsupportedOperationException.class,()->decoded.arguments().add("saved-request"));
    }
    @Test public void finiteSchemaCannotCarryStartupOrCoercedReferenceBytes()throws Exception {
        var mapper=ControlBuild.strictMapper();var row=mapper.createObjectNode().put("schema",JavaRuntimeLaunch.FiniteFirstLiveInvocation.SCHEMA);
        var ref=row.putObject("finite_request");ref.put("path",temporary.resolve("finite.json").toString());
        ref.put("bytes",true);ref.put("sha256","a".repeat(64));
        assertThrows(IOException.class,()->JavaRuntimeLaunch.FiniteFirstLiveInvocation.decode(mapper.writeValueAsBytes(row)));
        row.remove("finite_request");row.putObject("startup").put("path",temporary.resolve("startup.json").toString());
        assertThrows(IOException.class,()->JavaRuntimeLaunch.FiniteFirstLiveInvocation.decode(mapper.writeValueAsBytes(row)));
    }
}

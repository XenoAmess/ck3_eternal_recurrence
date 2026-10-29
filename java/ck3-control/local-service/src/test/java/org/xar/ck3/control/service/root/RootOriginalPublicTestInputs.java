package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.ToolDescriptor;

/** Mandatory exact original SDK capture. Missing input fails; no reduced or synthetic descriptor fallback. */
public final class RootOriginalPublicTestInputs {
    private RootOriginalPublicTestInputs() { }
    public static List<ToolDescriptor> tools() throws IOException {
        String path=required("xar.public.mcp.tools.path");
        String count=required("xar.public.mcp.tools.bytes");
        String sha=required("xar.public.mcp.tools.sha256");
        StrictJson.require(count.matches("[1-9][0-9]*")&&sha.matches("[a-f0-9]{64}"),"canonical original tools byte count and SHA required");
        long bytes=Long.parseLong(count);Path actual=Path.of(path);
        StrictJson.require(actual.isAbsolute()&&actual.normalize().equals(actual)&&bytes<=RootRuntimeDefinitionModel.maximumDataBytes(RootRuntimeDefinitionModel.DataRole.MCP_TOOLS),"bounded absolute original tools capture required");
        var reference=new FileRef(path,bytes,sha);reference.verify();
        var witness=SharedSourceFiles.observe(actual);byte[] raw;
        try(var input=Files.newInputStream(actual)){raw=input.readNBytes(Math.toIntExact(bytes)+1);}
        StrictJson.require(raw.length==bytes,"original tools file changed while read");
        SharedSourceFiles.assertUnchanged(witness);reference.verify();
        return RootPublicCatalogCodec.decodeTools(new RawJson(raw));
    }
    private static String required(String name) {
        String value=System.getProperty(name);
        if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_MCP_TOOLS: missing -D"+name);
        return value;
    }
}

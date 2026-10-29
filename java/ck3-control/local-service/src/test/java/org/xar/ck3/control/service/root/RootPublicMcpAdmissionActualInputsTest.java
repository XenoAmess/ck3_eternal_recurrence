package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.service.mcp.McpCoverage;

/** Uses two genuine immutable definitions from the existing publication path. Missing inputs fail.
 * Both readExact calls construct the actual pre-Core factory without a supplied Core or Game.
 */
class RootPublicMcpAdmissionActualInputsTest {
    private static final String PROVISIONAL="xar.root.public.mcp.provisional.definitions";

    @Test void actualProvisionalFactoryRederivesTheFinalAdmissionWithoutChangingOtherOriginalInputs()throws Exception {
        var provisional=RootRuntimeDefinitions.readExact(requiredRef(PROVISIONAL),Clock.systemUTC());
        var definitions=RootDriverProductSourcesFactoryTest.actual().definitions();
        var bootstrap=provisional.inputs().data(RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION);
        var selected=definitions.inputs().data(RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION);
        assertNotEquals(provisional.inputs().originalRef(),definitions.inputs().originalRef(),"two actual immutable definitions required");
        assertNotEquals(bootstrap,selected,"final admission must have its own actual immutable original");
        assertEquals(provisional.inputs().sourceIndex(),definitions.inputs().sourceIndex(),"both phases must retain the same selected source graph");
        for(var role:RootRuntimeDefinitionModel.DataRole.values())if(role!=RootRuntimeDefinitionModel.DataRole.MCP_ADMISSION) {
            if(role==RootRuntimeDefinitionModel.DataRole.ROLLBACK_PROOF)
                assertEquals(provisional.inputs().optionalData(role),definitions.inputs().optionalData(role),"admission qualification changed optional rollback original");
            else assertEquals(provisional.inputs().data(role),definitions.inputs().data(role),"admission qualification changed another original DATA role: "+role);
        }

        bootstrap.verify();
        var initial=RootPublicCatalogCodec.decodeAdmission(new RawJson(Files.readAllBytes(Path.of(bootstrap.path()))));
        bootstrap.verify();
        assertTrue(initial.stream().anyMatch(row->row.admission()==McpCoverage.Admission.UNMIGRATED),"a final admitted document cannot stand in for provisional input");
        assertTrue(initial.stream().allMatch(row->row.admission()==McpCoverage.Admission.UNMIGRATED
                ||row.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION),"bootstrap must not grant a callable or retirement");
        assertEquals(2L,initial.stream().filter(row->row.admission()==McpCoverage.Admission.EXCLUDED_BY_CURRENT_CONFIGURATION).count(),
                "fresh all-ordinary bootstrap retains exactly the two actual absent fixture branches");

        selected.verify();
        var fromProvisional=provisional.quotePublicAdmission(Path.of(selected.path()));
        var fromFinal=definitions.quotePublicAdmission(Path.of(selected.path()));
        assertEquals(RootBootstrapOutputContract.Kind.MCP_ADMISSION,fromProvisional.kind());
        assertEquals(selected.bytes(),fromProvisional.bytes());assertEquals(selected.sha256(),fromProvisional.sha256());
        assertEquals(fromProvisional,fromFinal,"final input labels must not change actual typed-binding qualification");
        var original=provisional.inputs().originalRef();
        byte[] stdout=quoteStdout(new String[]{"quote-qualify",original.path(),Long.toString(original.bytes()),original.sha256(),selected.path()});
        var wire=assertInstanceOf(RootBootstrapProtocol.OrdinaryQuote.class,RootBootstrapProtocol.line(stdout,RootBootstrapProtocol.Quote.class));
        assertEquals("MCP_ADMISSION",wire.phase());assertEquals(definitions.inputs().configuration().machineId(),wire.machineId());
        assertEquals(provisional.inputs().configuration().reviewAtUtc(),wire.reviewAtUtc());
        assertEquals(Path.of(selected.path()).getParent().toString(),wire.assetRoot());
        assertEquals(java.util.List.of(fromProvisional),wire.outputs());
        assertTrue(wire.outputDirectories().isEmpty());assertTrue(wire.retainedInputs().isEmpty());
        assertEquals("AWAITING_REAL_INDEPENDENT_ISSUER_BINDING",wire.authority());
        // This is the unchanged prelaunch migration consumer, not physical Game or business acceptance.
        definitions.requireCompleteMigration();
    }

    /** Feed the original LF stdout bytes straight into the shared consumer; never re-encode a quote DTO. */
    private static byte[] quoteStdout(String[] arguments)throws Exception {
        synchronized(RootPublicMcpAdmission.class) {
            var bytes=new ByteArrayOutputStream();PrintStream previous=System.out;
            try(var captured=new PrintStream(bytes,true,StandardCharsets.UTF_8)) {
                System.setOut(captured);RootPublicMcpAdmission.main(arguments);
            }finally{System.setOut(previous);}
            return bytes.toByteArray();
        }
    }
    private static FileRef requiredRef(String prefix)throws IOException {
        String path=required(prefix+".path"),bytes=required(prefix+".bytes"),sha=required(prefix+".sha256");
        if(!Path.of(path).isAbsolute()||!bytes.matches("[1-9][0-9]{0,8}")||!sha.matches("[0-9a-f]{64}"))
            throw new IOException("actual provisional Root definitions exact ref required");
        long length=Long.parseLong(bytes);
        if(length>RootRuntimeDefinitions.MAXIMUM_BYTES)throw new IOException("provisional definitions exceed the real Root DATA bound");
        return new FileRef(path,length,sha);
    }
    private static String required(String property)throws IOException {
        String value=System.getProperty(property);
        if(value==null||value.isBlank())throw new IOException("required actual provisional definitions fixture property missing: "+property);
        return value;
    }
}

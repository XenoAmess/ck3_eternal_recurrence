package org.xar.ck3.control.service.events;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.evidence.PortableEvidence.*;
import org.xar.ck3.control.contracts.evidence.PortableEvidenceJson;
import org.xar.ck3.control.evidence.PortableEvidenceReader;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory.DirectBinding;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;

/** Concrete original offline evidence tools. Root composes these same typed methods into MCP. */
public final class PortableEvidenceMethods {
    private static final int RESULT_MAX_BYTES=2*1024*1024;
    private final PortableEvidenceReader reader;
    public PortableEvidenceMethods(PortableEvidenceReader reader){this.reader=Objects.requireNonNull(reader);reader.requireManifestSource();}
    public ListResult list(ListCall query){return reader.list(query);}
    public ReadResult read(ReadCall query){return reader.read(query);}
    public List<DirectBinding<?,?>> actualMethods(ExactRef implementationSource){
        Objects.requireNonNull(implementationSource);
        var list=new DirectBinding<ListCall,ListResult>("ck3_list_vanilla_event_evidence_v1",PublicMcpBindings.Kind.STATIC_KNOWLEDGE,ListCall.class,ListResult.class,this::list,
                call->PortableEvidenceJson.listCall(StrictJson.parse(call.arguments().objectOrEmpty().bytes())),
                result->result(PortableEvidenceJson.listResult(result)),
                new PublicRoutes.Target(getClass().getName(),"list",implementationSource));
        var read=new DirectBinding<ReadCall,ReadResult>("ck3_read_vanilla_event_evidence_v1",PublicMcpBindings.Kind.STATIC_KNOWLEDGE,ReadCall.class,ReadResult.class,this::read,
                call->PortableEvidenceJson.readCall(StrictJson.parse(call.arguments().objectOrEmpty().bytes())),
                result->result(PortableEvidenceJson.readResult(result)),
                new PublicRoutes.Target(getClass().getName(),"read",implementationSource));
        return List.of(list,read);
    }
    private static CallResult result(com.fasterxml.jackson.databind.node.ObjectNode value){
        RawJson encoded=PublicDataJson.encode(value);StrictJson.require(encoded.bytes().length<=RESULT_MAX_BYTES,"bounded complete portable evidence result required");
        return CallResult.fromBusinessJson(encoded);
    }
}

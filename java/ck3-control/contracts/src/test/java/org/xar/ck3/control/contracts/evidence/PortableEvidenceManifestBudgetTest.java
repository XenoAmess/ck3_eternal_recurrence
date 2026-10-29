package org.xar.ck3.control.contracts.evidence;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Regression for the actual role boundary: declaring a 2 MiB lease cannot use StrictJson's 1 MiB lane. */
final class PortableEvidenceManifestBudgetTest {
    private static final ObjectMapper FIXTURE=new ObjectMapper();
    private static ObjectNode manifest(int references){
        ObjectNode root=FIXTURE.createObjectNode().put("schema","xar.ck3.vanilla-event-portable-evidence-manifest").put("schema_version",1)
                .put("ck3_build",PortableEvidence.BUILD).put("ck3_exe_sha256",PortableEvidence.EXE_SHA256);
        root.putObject("compression").put("algorithm","gzip").put("filename","").put("mtime",0);
        var entry=root.putArray("evidence").addObject().put("evidence_id","0".repeat(64)).put("sha256","0".repeat(64)).put("kind","source_definition")
                .put("media_type","text/plain; charset=utf-8").put("bytes",0).put("blob_bytes",18).put("blob_sha256","1".repeat(64)).put("blob_path","blobs/"+"0".repeat(64)+".gz");
        var rows=entry.putArray("references");
        for(int index=0;index<references;index++)rows.addObject().put("event_definition_key",String.format(Locale.ROOT,"event.%05d",index))
                .put("logical_path","events/test.txt").put("origin","ck3_game").put("provenance","generated-definition-index").put("role","event_definition")
                .put("source_line",1).putNull("source_column").putNull("caller_candidate_resolution");
        root.putObject("statistics").put("evidence",1).put("generated_definition_references",references).put("lexical_caller_candidate_references",0)
                .put("manually_reviewed_analysis_source_references",0).put("observation_artifacts",0).put("observation_artifact_references",0).put("references",references).put("source_definitions",1);return root;
    }
    private static byte[] encoded(ObjectNode root) throws Exception{return FIXTURE.writeValueAsBytes(root);}
    @Test void smallRealShapeManifestWorksWhileGenericMapBudgetRemainsUnchanged() throws Exception {
        byte[] small=encoded(manifest(1));assertEquals(1,PortableEvidenceJson.manifest(small,"A".repeat(64)).statistics().references());
        assertEquals(1_048_576,StrictJson.EXPLICIT_MAX_BYTES);assertThrows(IllegalArgumentException.class,()->StrictJson.parse(small,PortableEvidenceJson.MANIFEST_LIMIT));
    }
    @Test void completeManifestAboveOneMiBUsesOnlyItsTwoMiBRoleAndRoundtripsAllReferences() throws Exception {
        ObjectNode original=manifest(5000);byte[] large=encoded(original);assertTrue(large.length>StrictJson.EXPLICIT_MAX_BYTES);assertTrue(large.length<PortableEvidenceJson.MANIFEST_LIMIT);
        var value=PortableEvidenceJson.manifest(large,"A".repeat(64));assertEquals(5000,value.evidence().getFirst().metadata().references().size());
        assertEquals("event.04999",value.evidence().getFirst().metadata().references().getLast().eventDefinitionKey());
        assertEquals(value,PortableEvidenceJson.manifest(encoded((ObjectNode)FIXTURE.readTree(large)),"A".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->StrictJson.parse(large,StrictJson.EXPLICIT_MAX_BYTES));
    }
    @Test void duplicateMissingWrongTypeTrailingAndMalformedUtf8StillRefuseInManifestLane() throws Exception {
        ObjectNode missing=manifest(1);missing.remove("statistics");assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(encoded(missing),"A".repeat(64)));
        ObjectNode wrong=manifest(1).put("schema_version",true);assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(encoded(wrong),"A".repeat(64)));
        ObjectNode floating=manifest(1).put("schema_version",1.0);assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(encoded(floating),"A".repeat(64)));
        ObjectNode string=manifest(1).put("schema_version","1");assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(encoded(string),"A".repeat(64)));
        String original=new String(encoded(manifest(1)),StandardCharsets.UTF_8);
        byte[] duplicate=original.replace("\"schema_version\":1","\"schema_version\":1,\"schema_version\":1").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(duplicate,"A".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest((original+" {}").getBytes(StandardCharsets.UTF_8),"A".repeat(64)));
        byte[] malformed=encoded(manifest(1));malformed[0]=(byte)0xff;assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(malformed,"A".repeat(64)));
        assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.manifest(new byte[PortableEvidenceJson.MANIFEST_LIMIT+1],"A".repeat(64)));
    }
}

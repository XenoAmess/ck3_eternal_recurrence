package org.xar.ck3.control.evidence;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.evidence.PortableEvidenceJson;
import static org.xar.ck3.control.contracts.evidence.PortableEvidence.*;

/** Required real checked-in producer and data fixtures. Missing configuration fails; it never skips. */
final class PortableEvidenceReaderTest {
    private static final int FIXTURE_LIMIT=2*1024*1024;
    private static final ObjectMapper FIXTURE_JSON=new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64).maxStringLength(FIXTURE_LIMIT).maxNumberLength(1000).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    @TempDir Path temporary;
    private static Path repository(){String value=System.getProperty("xar.repository.root");assertNotNull(value,"required persistent CI fixture xar.repository.root");return Path.of(value);}
    private static Path bundle(){return repository().resolve("ck3_autonomous_player/src/xar_autoplayer/vanilla_events/portable_evidence");}
    private static ObjectNode args(){return StrictJson.object();}
    private static JsonNode fixture(byte[] bytes) throws IOException {assertTrue(bytes.length>0&&bytes.length<=FIXTURE_LIMIT,"bounded actual fixture/oracle bytes required");return FIXTURE_JSON.readTree(bytes);}
    private static byte[] fixtureBytes(ObjectNode value) throws IOException {byte[] bytes=FIXTURE_JSON.writeValueAsBytes(value);assertTrue(bytes.length<=FIXTURE_LIMIT);return bytes;}
    private static JsonNode wire(ObjectNode value) throws IOException {return fixture(fixtureBytes(value));}
    private static String sha(byte[] bytes) throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static JsonNode python(String method,ObjectNode arguments) throws Exception {
        String code="import sys,json;sys.path.insert(0,sys.argv[1]);from xar_autoplayer.vanilla_events.portable_evidence import list_vanilla_event_evidence_v1,read_vanilla_event_evidence_v1;args=json.loads(sys.argv[4]);args['bundle_root']=sys.argv[2];fn=list_vanilla_event_evidence_v1 if sys.argv[3]=='list' else read_vanilla_event_evidence_v1;print(json.dumps(fn(**args),ensure_ascii=False,allow_nan=False))";
        String executable=System.getProperty("xar.python");assertNotNull(executable,"required persistent CI fixture xar.python");
        var builder=new ProcessBuilder(executable,"-c",code,repository().resolve("ck3_autonomous_player/src").toString(),bundle().toString(),method,new String(fixtureBytes(arguments),StandardCharsets.UTF_8));
        builder.environment().put("PYTHONDONTWRITEBYTECODE","1");builder.redirectErrorStream(true);Process process=builder.start();
        var output=CompletableFuture.supplyAsync(()->{try{return process.getInputStream().readNBytes(2*1024*1024+1);}catch(IOException failure){throw new UncheckedIOException(failure);}});
        if(!process.waitFor(60,TimeUnit.SECONDS)){process.destroyForcibly();assertTrue(process.waitFor(5,TimeUnit.SECONDS),"original timed-out producer did not exit after termination");fail("original producer exceeded bounded 60 second test deadline");}
        byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,process.exitValue(),new String(bytes,StandardCharsets.UTF_8));return fixture(bytes);
    }
    @Test void completeActualManifestAndContentHashCursorMatchOriginalPythonProducer() throws Exception {
        var reader=new PortableEvidenceReader(bundle());Manifest manifest=reader.manifest();assertEquals(299,manifest.evidence().size());
        assertEquals(sha(Files.readAllBytes(bundle().resolve("manifest_v1.json"))).toUpperCase(java.util.Locale.ROOT),manifest.datasetSha256());
        var queries=new ArrayList<ObjectNode>();queries.add(args());queries.add(args().put("limit",3));queries.add(args().put("event_definition_key","tgp_dynastic_cycle.0091"));
        queries.add(args().put("kind","observation_artifact").put("limit",100));queries.add(args().put("after_evidence_id",manifest.evidence().get(100).metadata().evidenceId().value()).put("limit",3));
        for(ObjectNode query:queries)assertEquals(python("list",query),wire(PortableEvidenceJson.listResult(reader.list(PortableEvidenceJson.listCall(query)))),query.toString());
        assertTrue(reader.portableEventKeys().contains("tgp_dynastic_cycle.0091"));
    }
    @Test void listFailurePrecedenceNormalizationAndUnindexedCursorMatchOriginalProducer() throws Exception {
        var reader=new PortableEvidenceReader(bundle());
        for(ObjectNode query:List.of(args().put("ck3_build","1.20.0.4").put("limit",0),args().put("event_definition_key",false),args().put("kind","wrong"),args().put("after_evidence_id","bad"),args().put("limit",true),args().put("limit",1.0),args().put("limit",0),args().put("event_definition_key","not_registered.1"),args().put("after_evidence_id","0".repeat(64))))
            assertEquals(python("list",query),wire(PortableEvidenceJson.listResult(reader.list(PortableEvidenceJson.listCall(query)))),query.toString());
    }
    @Test void boundedChunksEofHistoricalLocatorLabelAndFullPayloadVerificationMatchOriginalProducer() throws Exception {
        var reader=new PortableEvidenceReader(bundle());Manifest manifest=reader.manifest();
        Metadata source=manifest.evidence().stream().map(Blob::metadata).filter(value->value.kind()==Kind.SOURCE_DEFINITION).findFirst().orElseThrow();
        Metadata observation=manifest.evidence().stream().map(Blob::metadata).filter(value->value.kind()==Kind.OBSERVATION_ARTIFACT).findFirst().orElseThrow();
        Metadata largest=manifest.evidence().stream().map(Blob::metadata).max(java.util.Comparator.comparingLong(Metadata::bytes)).orElseThrow();
        for(ObjectNode query:List.of(args().put("evidence_id",source.evidenceId().value()).put("max_bytes",37),args().put("evidence_id",observation.evidenceId().value()),
                args().put("evidence_id",source.evidenceId().value()).put("offset",source.bytes()),args().put("evidence_id",source.evidenceId().value()).put("offset",source.bytes()+1),
                args().put("evidence_id",largest.evidenceId().value()).put("offset",largest.bytes()-17).put("max_bytes",17))){
            var actual=wire(PortableEvidenceJson.readResult(reader.read(PortableEvidenceJson.readCall(query))));assertEquals(python("read",query),actual,query.toString());
            if(actual.path("content_base64").isTextual())assertTrue(Base64.getDecoder().decode(actual.path("content_base64").textValue()).length<=65536);
        }
    }
    @Test void readInvalidTokensAndSafeIntegerBoundaryRefuseBeforeBundleAccess() throws Exception {
        var reader=new PortableEvidenceReader(temporary.resolve("absent"));
        assertEquals(Failure.INVALID_OFFSET,reader.read(PortableEvidenceJson.readCall(args().put("evidence_id","0".repeat(64)).put("offset",true))).failure().orElseThrow());
        assertEquals(Failure.INVALID_OFFSET,reader.read(PortableEvidenceJson.readCall(args().put("evidence_id","0".repeat(64)).put("offset",9007199254740992L))).failure().orElseThrow());
        assertEquals(Failure.INVALID_MAX,reader.read(PortableEvidenceJson.readCall(args().put("evidence_id","0".repeat(64)).put("max_bytes",65537))).failure().orElseThrow());
        for(ObjectNode query:List.of(args().put("evidence_id","bad"),args().put("evidence_id","0".repeat(64)).put("offset",false),args().put("evidence_id","0".repeat(64)).put("max_bytes",0),args().put("evidence_id","0".repeat(64)).put("ck3_build","bad")))
            assertEquals(python("read",query),wire(PortableEvidenceJson.readResult(reader.read(PortableEvidenceJson.readCall(query)))));
    }
    private Path oneBlobBundle() throws Exception {
        Path root=temporary.resolve("tiny");Files.createDirectory(root);Files.createDirectory(root.resolve("blobs"));
        ObjectNode manifest=(ObjectNode)fixture(Files.readAllBytes(bundle().resolve("manifest_v1.json")));ObjectNode entry=((ObjectNode)manifest.withArray("evidence").get(0)).deepCopy();
        manifest.putArray("evidence").add(entry);long definition=0,lexical=0,analysis=0,captured=0;
        for(JsonNode ref:entry.withArray("references"))switch(ref.path("provenance").textValue()){case "generated-definition-index"->definition++;case "lexical-caller-candidate-not-proven-runtime-caller"->lexical++;case "manually-reviewed-analysis-source"->analysis++;case "captured-observation-artifact"->captured++;default->throw new AssertionError();}
        boolean source=entry.path("kind").textValue().equals("source_definition");var stats=manifest.putObject("statistics");
        stats.put("evidence",1).put("generated_definition_references",definition).put("lexical_caller_candidate_references",lexical).put("manually_reviewed_analysis_source_references",analysis).put("observation_artifacts",source?0:1).put("observation_artifact_references",captured).put("references",entry.withArray("references").size()).put("source_definitions",source?1:0);
        Files.write(root.resolve("manifest_v1.json"),fixtureBytes(manifest));Files.copy(bundle().resolve(entry.path("blob_path").textValue()),root.resolve(entry.path("blob_path").textValue()));return root;
    }
    @Test void changedCompressedBytesOrTrailingGzipRefuseWithoutRepairWhileListDoesNotClaimPayloadVerification() throws Exception {
        Path root=oneBlobBundle();var reader=new PortableEvidenceReader(root);Blob blob=reader.manifest().evidence().getFirst();Path path=root.resolve(blob.blobPath());byte[] original=Files.readAllBytes(path);
        byte[] damaged=original.clone();damaged[damaged.length-1]^=1;Files.write(path,damaged);
        assertTrue(reader.list(PortableEvidenceJson.listCall(args())).failure().isEmpty(),"list validates metadata and blob set, not all payload hashes");
        assertEquals(Failure.INTEGRITY,reader.read(PortableEvidenceJson.readCall(args().put("evidence_id",blob.metadata().evidenceId().value()))).failure().orElseThrow());assertArrayEquals(damaged,Files.readAllBytes(path));
        byte[] trailing=Arrays.copyOf(original,original.length+1);Files.write(path,trailing);ObjectNode manifest=(ObjectNode)fixture(Files.readAllBytes(root.resolve("manifest_v1.json")));
        ((ObjectNode)manifest.withArray("evidence").get(0)).put("blob_bytes",trailing.length).put("blob_sha256",sha(trailing));Files.write(root.resolve("manifest_v1.json"),fixtureBytes(manifest));
        assertEquals(Failure.INTEGRITY,reader.read(PortableEvidenceJson.readCall(args().put("evidence_id",blob.metadata().evidenceId().value()))).failure().orElseThrow());assertArrayEquals(trailing,Files.readAllBytes(path));
    }
    @Test void missingExtraBlobAndWrongManifestTokenTypesFailBothReaderAndDiscoveryKeys() throws Exception {
        Path root=oneBlobBundle();var reader=new PortableEvidenceReader(root);reader.portableEventKeys();Files.write(root.resolve("blobs/extra.gz"),new byte[]{1});
        assertThrows(PortableEvidenceReader.BundleException.class,reader::portableEventKeys);assertEquals(Failure.INTEGRITY,reader.list(PortableEvidenceJson.listCall(args())).failure().orElseThrow());
        Files.delete(root.resolve("blobs/extra.gz"));ObjectNode manifest=(ObjectNode)fixture(Files.readAllBytes(root.resolve("manifest_v1.json")));manifest.put("schema_version",true);Files.write(root.resolve("manifest_v1.json"),fixtureBytes(manifest));
        assertThrows(PortableEvidenceReader.BundleException.class,reader::manifest);assertThrows(IllegalArgumentException.class,()->PortableEvidenceJson.listCall(args().put("unknown",1)));
    }
}

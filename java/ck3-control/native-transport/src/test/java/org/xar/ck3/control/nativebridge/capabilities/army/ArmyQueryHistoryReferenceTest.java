package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryReference.*;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore.*;

/** Real Store19 numeric producer/guarded files -> reader -> original numeric body/serde.
 * Files, faults and guards are finite synthetic test assets, never current Root/Game evidence.
 */
final class ArmyQueryHistoryReferenceTest {
    @TempDir Path temporary;
    private static final long MAXIMUM=8L*1024*1024;
    private static final String NAME="army-query-"+"1".repeat(32)+".json";
    private record Fixture(Path evidence,ArmyStrengthsDriverResult.NumericResult input,FullStored stored,RawJson summary) { }

    private static final class FiniteGuard implements StorageWriteGuard {
        private final Path root;
        private int writes;
        private boolean closed;
        FiniteGuard(Path root){this.root=root;}
        @Override public void close(){closed=true;}
        @Override public void requireInitialization(Path lock,List<Path> roots)throws IOException {throw new IOException("test grants no Root initialization authority");}
        @Override public <T>T write(WritePlan plan,PhysicalWrite<T> body)throws IOException {
            if(closed)throw new IOException("synthetic storage guard is closed");
            if(!plan.originalLock().startsWith(root))throw new IOException("foreign original lock");
            for(var mutation:plan.mutations()){
                if(!mutation.target().startsWith(root))throw new IOException("foreign sidecar target");
                if(mutation instanceof FileCreate create&&(create.maxLogicalBytes()<0||create.maxLogicalBytes()>MAXIMUM))
                    throw new IOException("finite synthetic physical file quote exhausted");
            }
            writes++;return body.run();
        }
    }
    private static ArmyStrengthsDriverResult.NumericResult input(long power)throws Exception {
        ObjectNode result=ArmyJson.empty().put("step",STEP).put("accepted",true).put("status","available")
                .put("backend_id","controlled").put("query_sequence",1).put("army_strengths_profile","ordinary_core_v1")
                .put("army_observed_phase_coverage","not_requested");
        ObjectNode row=result.putArray("army_strengths").addObject().put("status","available").put("army_id",0)
                .put("native_carmy_id",0).put("scope_role","player").put("regiment_count",0).put("current_soldiers",0)
                .put("maximum_soldiers",0).put("ai_base_power_raw",power).put("ai_base_power_scale",100000).putNull("unavailable_reason");
        row.putArray("war_ids");
        var seed=ArmyStrengthsSourceTest.input(result,ArmyStrengthsSourceTest.projectedHello());
        Row actual=ArmyStrengthsCodec.row(row,Mode.AUTO_CORE,new ArmyStrengthsFamilies.Registry());
        var old=seed.original();Read read=new Read(old.profile(),old.status(),old.sequence(),old.backendId(),
                List.of(actual),old.timing(),old.publishedScopeStatus(),old.original());
        Query query=new Query(Profile.ORDINARY_CORE_V1,Mode.AUTO_CORE,new Missing<>(),EntryMode.OBSERVED_PREPARED,EntryMode.OBSERVED_PREPARED);
        var selection=new ArmyStrengthsContracts.Selection(seed.snapshot(),query,seed.originalHello().orElseThrow(),new Missing<>());
        return ArmyStrengthsDriverResult.numeric(ArmyStrengthsDriverResult.project(selection,read,new ArmyStrengthsPipeline()));
    }
    private Fixture fixture()throws Exception {
        Path evidence=temporary.resolve("evidence");var numeric=input(Long.MAX_VALUE);
        try(var guard=new FiniteGuard(temporary)){
            var io=new GuardedFileIO(guard,temporary.resolve("original.lock"));
            var store=new ArmyQueryHistoryStore(new Settings(evidence,MAXIMUM),Optional.empty(),io);
            var stored=assertInstanceOf(FullStored.class,store.record(numeric));
            return new Fixture(evidence,numeric,stored,stored.summary());
        }
    }
    private static RawJson raw(ObjectNode object){return new RawJson(ArmyJson.bytes(object));}
    private static ObjectNode object(RawJson original){return ArmyJson.parse(original.bytes());}
    private static ObjectNode reference(ObjectNode summary){return (ObjectNode)summary.get("raw_result_reference");}
    private static String sha(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}

    @Test void realNumericProducerStore19AndHeldReaderKeepCompleteBodyIdentityAndSerde()throws Exception {
        var f=fixture();
        var read=ArmyQueryHistoryReference.read(f.summary(),f.evidence(),MAXIMUM);
        assertArrayEquals(f.input().original().bytes(),read.completeDriver().bytes());
        assertEquals(read.completeDriver().bytes().length+1,Files.size(f.stored().reference().path()));
        assertEquals(object(f.input().original()),object(read.completeDriver()));
        assertEquals(f.stored().reference(),read.reference());assertArrayEquals(f.summary().bytes(),read.originalSummary().bytes());
        assertEquals(read.reference().bytes(),read.observedIdentity().bytes());
        assertTrue(read.observedIdentity().device().matches("0|[1-9][0-9]*"));
        assertTrue(read.observedIdentity().inode().matches("0|[1-9][0-9]*"));
        assertEquals(new BigInteger("9223372036854775807"),object(read.completeDriver()).at("/army_strengths/0/ai_base_power_raw").bigIntegerValue());
        assertTrue(object(read.completeDriver()).at("/army_strengths/0/ai_base_power_raw").isIntegralNumber());
        assertEquals(object(read.completeDriver()),object(new RawJson(read.completeDriver().bytes())));
        ObjectNode upper=object(f.summary());reference(upper).put("sha256",f.stored().reference().sha256().toUpperCase(java.util.Locale.ROOT));
        assertEquals(read.reference(),ArmyQueryHistoryReference.read(raw(upper),f.evidence(),MAXIMUM).reference());
    }

    @Test void actualProducerMaximumPlusItsSingleLfIsAdmittedWithoutExpandingRawJson()throws Exception {
        long maximum=RawJson.MAXIMUM_BYTES,artifact=maximum+1;
        assertTrue(org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES>=artifact);
        assertEquals(maximum,ArmyQueryHistoryReference.jsonLength(artifact,10));
        assertEquals(maximum,ArmyQueryHistoryReference.jsonLength(maximum,125));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.jsonLength(artifact,32));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.jsonLength(artifact+1,10));
        assertEquals(3,ArmyQueryHistoryReference.jsonLength(4,10)); // exactly one LF, never trim the original JSON
        var f=fixture();ObjectNode summary=object(f.summary());reference(summary).put("bytes",artifact);
        IOException reached=new IOException("actual reader reached retained file admission");
        FileIO stopped=new FileIO(){
            @Override public Resolved resolve(Path file,Path evidence)throws IOException {throw reached;}
            @Override public ReadHandle open(Resolved resolved){throw new AssertionError("resolve intentionally stopped before allocation");}
            @Override public void verify(Resolved resolved,FileStamp stamp){throw new AssertionError("not reached");}
        };
        assertSame(reached,assertThrows(IOException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),artifact,stopped)));
        reference(summary).put("bytes",artifact+1);
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),artifact+1,stopped));
        // No64MiB fixture allocation or physical sidecar is needed to exercise the actual admission gate.
    }

    @Test void failedOrMalformedSummaryCannotPerformAnyFileIO()throws Exception {
        var f=fixture();var invalid=new ArrayList<ObjectNode>();
        for(Consumer<ObjectNode> mutation:List.<Consumer<ObjectNode>>of(
                s->s.put("full_result_preserved",false),s->s.put("full_result_preserved",1),
                s->s.put("history_summary_schema","other"),s->s.put("step","other"),s->s.remove("raw_result_reference"),
                s->reference(s).put("kind","original-pipe-bytes"),s->reference(s).put("wire_bytes_preserved",true),
                s->reference(s).put("wire_bytes_preserved",0),s->reference(s).put("bytes",true),
                s->reference(s).put("bytes",1.0),s->reference(s).put("bytes","1"),s->reference(s).putNull("bytes"),
                s->reference(s).remove("bytes"),s->reference(s).put("bytes",0),
                s->reference(s).put("sha256","x".repeat(64)),s->reference(s).put("path",NAME),
                s->reference(s).put("path",f.evidence().resolve("latest.json").toString()))) {
            ObjectNode value=object(f.summary());mutation.accept(value);invalid.add(value);
        }
        FileIO forbidden=new FileIO(){
            @Override public Resolved resolve(Path file,Path folder){throw new AssertionError("failed summary must not resolve or discover files");}
            @Override public ReadHandle open(Resolved target){throw new AssertionError("failed summary must not open");}
            @Override public void verify(Resolved target,FileStamp stamp){throw new AssertionError("failed summary must not verify");}
        };
        for(ObjectNode value:invalid)assertThrows(IllegalArgumentException.class,
                ()->ArmyQueryHistoryReference.read(raw(value),f.evidence(),MAXIMUM,forbidden));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(f.summary(),f.evidence(),0,forbidden));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(f.summary(),f.evidence(),f.stored().reference().bytes()-1,forbidden));
    }

    @Test void exactEvidenceLeafAndActualSizeOrHashAreRequired()throws Exception {
        var f=fixture();
        Path foreign=temporary.resolve("other");Files.createDirectory(foreign);
        assertThrows(IOException.class,()->ArmyQueryHistoryReference.read(f.summary(),foreign,MAXIMUM));
        ObjectNode size=object(f.summary());reference(size).put("bytes",f.stored().reference().bytes()+1);
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(size),f.evidence(),MAXIMUM));
        ObjectNode hash=object(f.summary());reference(hash).put("sha256","0".repeat(64));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(hash),f.evidence(),MAXIMUM));
        // Intentional corruption of this newly generated synthetic sidecar, never production evidence.
        byte[] changed=Files.readAllBytes(f.stored().reference().path());
        for(int i=0;i<changed.length;i++)if(changed[i]=='c'){changed[i]='C';break;}
        Files.write(f.stored().reference().path(),changed);
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(f.summary(),f.evidence(),MAXIMUM));
    }

    @Test void bodyCountersAndQueryIdentityMustMatchEvenWhenTheTamperedReferenceHashMatches()throws Exception {
        var f=fixture();ObjectNode original=object(f.input().original());
        for(String field:List.of("step","accepted","query_sequence","queried_snapshot_id","queried_revision","queried_native_revision",
                "status","backend_id","army_strengths_profile","army_observed_phase_coverage")){
            ObjectNode body=original.deepCopy();
            switch(field){
                case "accepted"->body.put(field,false);
                case "query_sequence","queried_revision","queried_native_revision"->body.put(field,999);
                default->body.put(field,"different-original-identity");
            }
            byte[] encoded=ArmyJson.bytes(body);Files.write(f.stored().reference().path(),encoded);
            ObjectNode summary=object(f.summary());reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
            assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM),field);
        }
        for(String field:List.of("step","accepted","query_sequence","queried_snapshot_id","queried_revision","queried_native_revision","army_strengths")){
            ObjectNode body=original.deepCopy();body.remove(field);byte[] encoded=ArmyJson.bytes(body);
            Files.write(f.stored().reference().path(),encoded);
            ObjectNode summary=object(f.summary());reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
            assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM),"missing "+field);
        }
        for(JsonNode invalid:List.of(ArmyJson.empty().nullNode(),ArmyJson.empty().objectNode(),ArmyJson.empty().booleanNode(false))){
            ObjectNode body=original.deepCopy();body.set("army_strengths",invalid);byte[] encoded=ArmyJson.bytes(body);
            Files.write(f.stored().reference().path(),encoded);
            ObjectNode summary=object(f.summary());reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
            assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM));
        }
        byte[] encoded=ArmyJson.bytes(original);Files.write(f.stored().reference().path(),encoded);
        for(Consumer<ObjectNode> mutation:List.<Consumer<ObjectNode>>of(s->s.put("army_count",true),
                s->s.put("army_count",1.0),s->s.put("army_count",2),s->s.remove("army_count"))){
            ObjectNode summary=object(f.summary());reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));mutation.accept(summary);
            assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM));
        }
    }

    @Test void aFailedNativeResultRemainsDataAndOptionalNullMatchesOriginalMissingGetSemantics()throws Exception {
        var f=fixture();ObjectNode body=object(f.input().original()).put("accepted",false);
        ObjectNode summary=object(f.summary()).put("accepted",false);
        // Controlled file mutation exercises the old reader's DATA semantics; it grants no native success.
        for(String key:List.of("status","backend_id","army_strengths_profile","army_observed_phase_coverage")){
            body.remove(key);summary.putNull(key);
        }
        byte[] encoded=ArmyJson.bytes(body);Files.write(f.stored().reference().path(),encoded);
        reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
        var observed=ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM);
        assertFalse(object(observed.completeDriver()).get("accepted").booleanValue());
        assertEquals(body,object(observed.completeDriver()));
        summary.put("status","available");
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM));
    }

    @Test void strictNumericAndBooleanTypesAndOriginalPositivePublicRevisionCannotBeWidened()throws Exception {
        var f=fixture();ObjectNode original=object(f.input().original());
        for(String field:List.of("query_sequence","queried_revision","queried_native_revision")){
            for(JsonNode bad:List.of(ArmyJson.empty().booleanNode(true),ArmyJson.empty().numberNode(1.0),
                    ArmyJson.empty().textNode("1"),ArmyJson.empty().numberNode(0),ArmyJson.empty().numberNode(-1))){
                ObjectNode body=original.deepCopy();body.set(field,bad);byte[] encoded=ArmyJson.bytes(body);Files.write(f.stored().reference().path(),encoded);
                ObjectNode summary=object(f.summary());summary.set(field,bad);reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
                assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM),field+" "+bad);
            }
        }
        ObjectNode body=original.deepCopy().put("accepted",1);byte[] encoded=ArmyJson.bytes(body);Files.write(f.stored().reference().path(),encoded);
        ObjectNode summary=object(f.summary());summary.put("accepted",1);reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM));
    }

    @Test void heldNativeIdentityModificationAndGrowthDuringReadingAreRejectedWithoutRetry()throws Exception {
        var f=fixture();var actual=new WindowsFileIO();AtomicInteger reads=new AtomicInteger();
        FileIO drift=new FileIO(){
            @Override public Resolved resolve(Path file,Path folder)throws IOException{return actual.resolve(file,folder);}
            @Override public void verify(Resolved resolved,FileStamp stamp)throws IOException{actual.verify(resolved,stamp);}
            @Override public ReadHandle open(Resolved resolved)throws IOException {
                ReadHandle held=actual.open(resolved);return new ReadHandle(){
                    private int observed;
                    @Override public FileStamp stamp()throws IOException {
                        FileStamp current=held.stamp();if(observed++==0)return current;
                        return new FileStamp(current.device(),current.inode(),current.creationFiletime(),
                                new BigInteger(current.modifiedFiletime()).add(BigInteger.ONE).toString(),current.bytes());
                    }
                    @Override public int read(byte[] bytes,int offset,int length)throws IOException {reads.incrementAndGet();return held.read(bytes,offset,length);}
                    @Override public void close()throws IOException{held.close();}
                };
            }
        };
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(f.summary(),f.evidence(),MAXIMUM,drift));
        assertTrue(reads.get()>0);AtomicInteger growCalls=new AtomicInteger();
        FileIO grow=new FileIO(){
            @Override public Resolved resolve(Path file,Path folder)throws IOException{return actual.resolve(file,folder);}
            @Override public void verify(Resolved resolved,FileStamp stamp)throws IOException{actual.verify(resolved,stamp);}
            @Override public ReadHandle open(Resolved resolved)throws IOException {
                ReadHandle held=actual.open(resolved);return new ReadHandle(){
                    @Override public FileStamp stamp()throws IOException{return held.stamp();}
                    @Override public int read(byte[] bytes,int offset,int length)throws IOException {
                        int count=held.read(bytes,offset,length);
                        if(growCalls.getAndIncrement()==0)Files.write(resolved.file(),new byte[]{32,32},java.nio.file.StandardOpenOption.APPEND);
                        return count;
                    }
                    @Override public void close()throws IOException{held.close();}
                };
            }
        };
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(f.summary(),f.evidence(),MAXIMUM,grow));
        assertEquals(2,growCalls.get(),"one initial chunk plus one bounded excess-byte read; no retry");
    }

    @Test void aLaterPartialNeverReplacesTheEarlierExactSuccessfulReference()throws Exception {
        var f=fixture();Path later=f.evidence().resolve("army-query-"+"f".repeat(32)+".json");
        Files.writeString(later,"partial");
        assertEquals(f.stored().reference(),ArmyQueryHistoryReference.read(f.summary(),f.evidence(),MAXIMUM).reference());
        ObjectNode partial=object(f.summary());reference(partial).put("path",later.toString());
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(partial),f.evidence(),MAXIMUM));
        ObjectNode failed=object(f.summary()).put("full_result_preserved",false).put("unavailable_reason","sidecar_budget_exhausted");
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryReference.read(raw(failed),f.evidence(),MAXIMUM));
    }

    @Test void strictUTF8RejectsEncodingSubstitutionEvenWithAMatchingFileHash()throws Exception {
        var f=fixture();byte[] original=f.input().original().bytes();
        List<byte[]> encodings=new ArrayList<>();
        byte[] bom=new byte[original.length+3];bom[0]=(byte)0xef;bom[1]=(byte)0xbb;bom[2]=(byte)0xbf;System.arraycopy(original,0,bom,3,original.length);
        encodings.add(bom);encodings.add(new String(original,StandardCharsets.UTF_8).getBytes(StandardCharsets.UTF_16LE));
        byte[] malformed=original.clone();malformed[0]=(byte)0xff;encodings.add(malformed);
        for(byte[] encoded:encodings){
            Files.write(f.stored().reference().path(),encoded);
            ObjectNode summary=object(f.summary());reference(summary).put("bytes",encoded.length).put("sha256",sha(encoded));
            assertThrows(IOException.class,()->ArmyQueryHistoryReference.read(raw(summary),f.evidence(),MAXIMUM));
        }
    }
}


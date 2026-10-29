package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.writer.StorageWriteGuard;

/** Actual numeric producer -> sidecar -> IO -> original summary/public serde.
 * All guards and packets here are explicitly software fixtures, never Root/Game qualification.
 */
final class ArmyQueryHistoryStoreTest {
    @TempDir Path temporary;
    private static final long MIB=1024*1024;
    private final List<MeteredGuard> scopes=new ArrayList<>();

    @AfterEach void closeOwnedScopes()throws IOException {
        IOException failure=null;
        for(var scope:scopes)try{scope.close();}catch(IOException close){if(failure==null)failure=close;else failure.addSuppressed(close);}
        if(failure!=null)throw failure;
    }

    private static ArmyStrengthsDriverResult.NumericResult input(long power,int payload,boolean wrongSequence)throws Exception {
        ObjectNode result=ArmyJson.empty().put("step",STEP).put("accepted",true).put("status","available")
                .put("backend_id","controlled").put("query_sequence",1).put("army_strengths_profile","ordinary_core_v1")
                .put("army_observed_phase_coverage","not_requested");
        ObjectNode row=result.putArray("army_strengths").addObject().put("status","available").put("army_id",0)
                .put("native_carmy_id",0).put("scope_role","player").put("regiment_count",0).put("current_soldiers",0)
                .put("maximum_soldiers",0).put("ai_base_power_raw",power).put("ai_base_power_scale",100000).putNull("unavailable_reason");
        row.putArray("war_ids");
        if(payload>0)result.put("software_synthetic_payload","x".repeat(payload));
        var seed=ArmyStrengthsSourceTest.input(result,ArmyStrengthsSourceTest.projectedHello());
        Row typed=ArmyStrengthsCodec.row(row,Mode.AUTO_CORE,new ArmyStrengthsFamilies.Registry());
        var old=seed.original();
        Read read=new Read(old.profile(),old.status(),wrongSequence?BigInteger.TWO:old.sequence(),old.backendId(),
                List.of(typed),old.timing(),old.publishedScopeStatus(),old.original());
        Query query=new Query(Profile.ORDINARY_CORE_V1,Mode.AUTO_CORE,new Missing<>(),
                EntryMode.OBSERVED_PREPARED,EntryMode.OBSERVED_PREPARED);
        var selection=new ArmyStrengthsContracts.Selection(seed.snapshot(),query,seed.originalHello().orElseThrow(),new Missing<>());
        var reply=ArmyStrengthsDriverResult.project(selection,read,new ArmyStrengthsPipeline());
        return ArmyStrengthsDriverResult.numeric(reply);
    }
    private final class MeteredGuard implements StorageWriteGuard {
        private final Path root; private final long maximum; private final boolean reject;
        private final SharedSourceFiles.DirectoryIdentity rootIdentity;
        private final Map<Path,SharedSourceFiles.NativeFile> files=new LinkedHashMap<>();
        private final Map<Path,SharedSourceFiles.DirectoryIdentity> directories=new LinkedHashMap<>();
        private boolean closed,active,unknown;
        private long logicalFileBytes,allocatedFileBytes;
        private int calls;
        MeteredGuard(Path root,long maximum,boolean reject)throws IOException {
            this.root=root;this.maximum=maximum;this.reject=reject;
            rootIdentity=SharedSourceFiles.nativeDirectory(root);scopes.add(this);
        }
        private void requireOpen()throws IOException {
            if(closed)throw new IOException("finite test scope is closed");
            if(unknown)throw new IOException("test allocation accounting remains UNKNOWN");
            if(!rootIdentity.equals(SharedSourceFiles.nativeDirectory(root)))throw new IOException("test root identity drift");
        }
        @Override public void requireInitialization(Path lock,List<Path> roots)throws IOException {
            requireOpen();throw new IOException("this test grants no initialization authority");
        }
        @Override public synchronized <T>T write(WritePlan plan,PhysicalWrite<T> body)throws IOException {
            requireOpen();if(active)throw new IOException("nested writes are not admitted by this finite test scope");
            calls++;if(reject)throw new IOException("actual finite test admission rejected");
            if(!plan.originalLock().startsWith(root))throw new IOException("foreign original lock");
            for(var mutation:plan.mutations()){
                if(!mutation.target().startsWith(root))throw new IOException("foreign physical target");
                if(!(mutation instanceof FileCreate)&&!(mutation instanceof DirectoryCreate))throw new IOException("unquoted test mutation kind");
                if(Files.exists(mutation.target(),LinkOption.NOFOLLOW_LINKS))throw new IOException("test create target already exists");
                if(mutation instanceof FileCreate file){
                    if(file.maxLogicalBytes()>maximum)throw new IOException("finite test quote exhausted");
                }
            }
            active=true;Throwable failure=null;
            try{return body.run();}
            catch(IOException|RuntimeException|Error original){failure=original;throw original;}
            finally {
                active=false;
                try{account(plan);}catch(IOException accounting){unknown=true;if(failure!=null)failure.addSuppressed(accounting);else throw accounting;}
            }
        }
        // This software fixture retains actual file allocations, including failed partial writes.
        // It does not issue a production Root card or claim complete directory-allocation accounting.
        private void account(WritePlan plan)throws IOException {
            for(var mutation:plan.mutations())if(Files.exists(mutation.target(),LinkOption.NOFOLLOW_LINKS)){
                if(mutation instanceof FileCreate file){
                    var actual=SharedSourceFiles.nativeFile(file.target());files.put(file.target(),actual);
                    if(actual.logicalBytes()>file.maxLogicalBytes())throw new IOException("actual file exceeded finite test quote");
                }else directories.put(mutation.target(),SharedSourceFiles.nativeDirectory(mutation.target()));
            }
            logicalFileBytes=0;allocatedFileBytes=0;
            for(var entry:files.values()){
                logicalFileBytes=Math.addExact(logicalFileBytes,entry.logicalBytes());
                allocatedFileBytes=Math.addExact(allocatedFileBytes,entry.allocatedBytes());
            }
        }
        @Override public synchronized void close()throws IOException {
            if(closed)return;
            if(active)throw new IOException("cannot close an active physical test write");
            try {
                requireOpen();
                for(var entry:files.entrySet()){
                    var actual=SharedSourceFiles.nativeFile(entry.getKey());var retained=entry.getValue();
                    if(!actual.identityKey().equals(retained.identityKey())||actual.logicalBytes()!=retained.logicalBytes()
                            ||actual.allocatedBytes()!=retained.allocatedBytes())throw new IOException("retained test allocation changed before close");
                }
                for(var entry:directories.entrySet())if(!entry.getValue().equals(SharedSourceFiles.nativeDirectory(entry.getKey())))
                    throw new IOException("created test directory identity changed before close");
            }finally{closed=true;}
        }
    }
    private ArmyQueryHistoryStore store(Path folder,long limit,MeteredGuard guard) {
        return new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(folder,limit),Optional.empty(),
                new ArmyQueryHistoryStore.GuardedFileIO(guard,temporary.resolve("original.lock")));
    }

    @Test void readonlySummaryReplayKeepsExactSettingsAndRejectsWrongJsonDomains() throws Exception {
        var admissions = new AtomicInteger();
        var forbidden = new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path path) { throw new AssertionError("zero must not scan"); }
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path path,long maximum,ArmyQueryHistoryStore.WriteBody body) {
                throw new AssertionError("zero must not write");
            }
        };
        Path leaf=temporary.resolve("readonly-replay-never-created");
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(leaf,0),admissions::incrementAndGet,forbidden);
        var settings=new org.xar.ck3.control.contracts.ExactRef(temporary.resolve("settings.json").toString(),10,"a".repeat(64));
        var plan=ArmyStrengthsDriverResult.historySummary(input(100,0,false).source(),store,settings,List.of(settings));
        var captured=plan.captureOriginal();plan.requireOriginal(captured);
        int checked=admissions.get();assertEquals(2,checked);
        RawJson raw=captured.storageOriginal();
        ObjectNode meta=ArmyJson.parse(raw.bytes());
        ObjectNode exact=assertInstanceOf(ObjectNode.class,meta.get("settings_original"));
        assertTrue(exact.get("bytes").isIntegralNumber());
        assertEquals(settings,org.xar.ck3.control.contracts.ExactRef.fromJson(exact));
        var replayed=plan.replayOriginal(new RawJson(raw.bytes()));
        assertArrayEquals(captured.summary().bytes(),replayed.summary().bytes());
        assertArrayEquals(raw.bytes(),replayed.storageOriginal().bytes());
        var wrongReferences=new ArrayList<ObjectNode>();
        for(com.fasterxml.jackson.databind.JsonNode value:List.<com.fasterxml.jackson.databind.JsonNode>of(
                com.fasterxml.jackson.databind.node.BooleanNode.TRUE,
                com.fasterxml.jackson.databind.node.DecimalNode.valueOf(new java.math.BigDecimal("10.0")),
                com.fasterxml.jackson.databind.node.TextNode.valueOf("10"),
                com.fasterxml.jackson.databind.node.NullNode.instance,
                com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(BigInteger.valueOf(-1)),
                com.fasterxml.jackson.databind.node.BigIntegerNode.valueOf(new BigInteger("9007199254740992")),
                com.fasterxml.jackson.databind.node.LongNode.valueOf(11))) {
            ObjectNode wrong=exact.deepCopy();wrong.set("bytes",value);wrongReferences.add(wrong);
        }
        wrongReferences.add(exact.deepCopy().put("path",temporary.resolve("other-settings.json").toString()));
        wrongReferences.add(exact.deepCopy().put("sha256","b".repeat(64)));
        wrongReferences.add(exact.deepCopy().put("extra",true));
        ObjectNode missing=exact.deepCopy();missing.remove("path");wrongReferences.add(missing);
        for(ObjectNode reference:wrongReferences) {
            ObjectNode wrong=meta.deepCopy();wrong.set("settings_original",reference);
            assertThrows(IllegalArgumentException.class,()->plan.replayOriginal(new RawJson(ArmyJson.bytes(wrong))));
        }
        ObjectNode wrongDirectory=meta.deepCopy().put("evidence_directory",temporary.resolve("other").toString());
        assertThrows(IllegalArgumentException.class,()->plan.replayOriginal(new RawJson(ArmyJson.bytes(wrongDirectory))));
        ObjectNode wrongLimit=meta.deepCopy().put("limit_bytes",1);
        assertThrows(IllegalArgumentException.class,()->plan.replayOriginal(new RawJson(ArmyJson.bytes(wrongLimit))));
        assertEquals(checked,admissions.get(),"readonly replay cannot admit or record again");
        assertFalse(Files.exists(leaf));
    }

    @Test void disabledAndAdmissionRejectedNeverTouchIOOrLazilyEncodeTheCompleteResult()throws Exception {
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path folder){throw new AssertionError("disabled must not scan evidence");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long max,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("disabled must not write");}
        };
        var lazy=input(Long.MAX_VALUE,0,true); // full encoder must reject this deliberately mismatched original sequence.
        assertThrows(IllegalArgumentException.class,lazy::original);
        var disabled=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("absent"),0),Optional.empty(),forbidden);
        var result=disabled.record(lazy);assertInstanceOf(ArmyQueryHistoryStore.Disabled.class,result);
        result.requireInput(lazy);assertTrue(result.issuedBy(disabled));assertFalse(Files.exists(temporary.resolve("absent")));
        ObjectNode body=ArmyJson.parse(result.summary().bytes());
        assertEquals("sidecar_disabled_by_session_budget",body.get("unavailable_reason").textValue());
        assertEquals(BigInteger.valueOf(Long.MAX_VALUE),body.at("/armies/0/ai_base_power_raw").bigIntegerValue());
        assertEquals("9223372036854775807",ArmyJson.parse(result.publicSummary().bytes()).at("/armies/0/ai_base_power_raw").textValue());
        AtomicInteger checked=new AtomicInteger();
        var denied=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("denied"),0),
                ()->{checked.incrementAndGet();throw new IOException("a".repeat(1100));},forbidden);
        var rejected=denied.record(lazy);assertInstanceOf(ArmyQueryHistoryStore.AdmissionRejected.class,rejected);assertEquals(1,checked.get());
        assertEquals(1000,ArmyJson.parse(rejected.summary().bytes()).at("/history_storage_diagnostic/reason").textValue().length());
    }

    @Test void actualNumericProducerStoredBytesAndReferenceMatchCompleteOriginalWithTrailingNewline()throws Exception {
        var numeric=input(Long.MIN_VALUE,0,false);var guard=new MeteredGuard(temporary,2*MIB,false);
        var store=store(temporary.resolve("actual-leaf"),2*MIB,guard);
        var result=assertInstanceOf(ArmyQueryHistoryStore.FullStored.class,store.record(numeric));
        byte[] original=numeric.original().bytes(),actual=Files.readAllBytes(result.reference().path());
        assertEquals(original.length+1,actual.length);assertEquals(10,actual[actual.length-1]);
        assertArrayEquals(original,java.util.Arrays.copyOf(actual,actual.length-1));
        assertEquals(ArmyQueryHistoryStore.GuardedFileIO.fileDigest(result.reference().path()),
                new ArmyQueryHistoryStore.Written(result.reference().bytes(),result.reference().sha256()));
        ObjectNode summary=ArmyJson.parse(result.summary().bytes());
        assertTrue(summary.get("full_result_preserved").booleanValue());
        assertFalse(summary.at("/raw_result_reference/wire_bytes_preserved").booleanValue());
        assertEquals(ArmyQueryHistoryStore.REFERENCE_KIND,summary.at("/raw_result_reference/kind").textValue());
        assertEquals(BigInteger.valueOf(Long.MIN_VALUE),summary.at("/armies/0/ai_base_power_raw").bigIntegerValue());
        assertEquals(summary,ArmyJson.parse(new RawJson(result.summary().bytes()).bytes()));
        ObjectNode publicSummary=ArmyJson.parse(result.publicSummary().bytes());
        assertEquals("-9223372036854775808",publicSummary.at("/armies/0/ai_base_power_raw").textValue());
        assertTrue(publicSummary.at("/armies/0/army_id").isIntegralNumber());
        assertEquals(publicSummary,ArmyJson.parse(new RawJson(result.publicSummary().bytes()).bytes()));
        assertEquals(1,guard.calls);assertTrue(result.issuedBy(store));result.requireInput(numeric);
        assertThrows(IllegalArgumentException.class,()->result.requireInput(input(0,0,false)));
        assertEquals(actual.length,guard.logicalFileBytes);
        assertEquals(SharedSourceFiles.nativeFile(result.reference().path()).allocatedBytes(),guard.allocatedFileBytes);
        guard.close();Path afterClose=temporary.resolve("after-close.json");AtomicInteger writes=new AtomicInteger();
        assertThrows(IOException.class,()->guard.write(new StorageWriteGuard.WritePlan(temporary.resolve("original.lock"),
                List.of(new StorageWriteGuard.FileCreate(afterClose,32))),()->{writes.incrementAndGet();Files.writeString(afterClose,"forbidden");return null;}));
        assertEquals(0,writes.get());assertFalse(Files.exists(afterClose));assertEquals(1,guard.calls);
    }

    @Test void realBudgetFailureRetainsTheOneMiBPartialAndRestartCountsIt()throws Exception {
        Path leaf=temporary.resolve("partials");var guard=new MeteredGuard(temporary,2*MIB,false);
        var store=store(leaf,2*MIB,guard);var full=assertInstanceOf(ArmyQueryHistoryStore.FullStored.class,store.record(input(2,0,false)));
        var failed=assertInstanceOf(ArmyQueryHistoryStore.BudgetExhausted.class,store.record(input(3,3*(int)MIB,false)));
        ObjectNode summary=ArmyJson.parse(failed.summary().bytes());assertFalse(summary.get("full_result_preserved").booleanValue());
        assertFalse(summary.has("raw_result_reference"));assertEquals("sidecar_budget_exhausted",summary.get("unavailable_reason").textValue());
        try(var entries=Files.list(leaf)){
            List<Path> partials=entries.filter(p->!p.equals(full.reference().path())).toList();
            assertEquals(1,partials.size());assertEquals(MIB,Files.size(partials.getFirst()));
        }
        long existing=new ArmyQueryHistoryStore.GuardedFileIO(guard,temporary.resolve("original.lock")).existingFlatBytes(leaf);
        assertEquals(full.reference().bytes()+MIB,existing);
        assertEquals(existing,summary.at("/history_storage_diagnostic/charged_bytes").longValue());
        assertEquals(existing,guard.logicalFileBytes,"failed physical partial remains in the guard's allocation ledger");
        var restarted=store(leaf,existing,guard);
        assertInstanceOf(ArmyQueryHistoryStore.BudgetExhausted.class,restarted.record(input(4,0,false)));
        try(var entries=Files.list(leaf)){assertEquals(2,entries.count());}
    }

    @Test void shortWriteAndPhysicalAdmissionFailureRetainHonestIODiagnostics()throws Exception {
        Path leaf=temporary.resolve("short");var guard=new MeteredGuard(temporary,2*MIB,false);
        var delegate=new ArmyQueryHistoryStore.GuardedFileIO(guard,temporary.resolve("original.lock"));
        var shortIO=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path folder)throws IOException{return delegate.existingFlatBytes(folder);}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long max,ArmyQueryHistoryStore.WriteBody body)throws IOException {
                return delegate.writeExclusive(target,max,out->body.write((bytes,offset,length)->out.write(bytes,offset,length-1)));
            }
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(leaf,2*MIB),Optional.empty(),shortIO);
        var failed=assertInstanceOf(ArmyQueryHistoryStore.IoError.class,store.record(input(0,0,false)));
        ObjectNode summary=ArmyJson.parse(failed.summary().bytes());
        assertEquals("sidecar_io_error",summary.get("unavailable_reason").textValue());
        assertTrue(summary.at("/history_storage_diagnostic/message").textValue().contains("short JSON sidecar write"));
        try(var files=Files.list(leaf)){Path partial=files.findFirst().orElseThrow();assertTrue(Files.size(partial)>0);}
        Path absent=temporary.resolve("guard-rejected");
        var denied=store(absent,2*MIB,new MeteredGuard(temporary,2*MIB,true));
        assertInstanceOf(ArmyQueryHistoryStore.IoError.class,denied.record(input(0,0,false)));
        assertFalse(Files.exists(absent));
    }

    @Test void compactInputIsCopiedOnlyAfterAdmissionAndSummaryPreservesNullMissingAndMalformedRows() {
        var full=ArmyJson.empty().put("step",STEP).put("accepted",true).put("query_sequence",1).put("queried_revision",2)
                .put("queried_native_revision",1);
        var rows=full.putArray("army_strengths");rows.addObject().put("army_id",0).putNull("ai_base_power_raw");
        rows.addObject().put("army_id",1).put("ai_base_power_raw",Long.MAX_VALUE);rows.add(9);
        RawJson summary=ArmyQueryHistoryStore.buildSummary(new RawJson(ArmyJson.bytes(full)),Optional.empty(),Optional.of("disabled"),Optional.empty());
        ObjectNode expected=ArmyJson.parse(summary.bytes());assertFalse(expected.at("/armies/0").has("owner_character_id"));
        assertTrue(expected.at("/armies/0/ai_base_power_raw").isNull());assertTrue(expected.at("/armies/2/malformed_row").booleanValue());
        AtomicInteger checked=new AtomicInteger();
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path p){throw new AssertionError("compact cannot inspect disk");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path p,long n,ArmyQueryHistoryStore.WriteBody b){throw new AssertionError("compact cannot write");}
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary,1),checked::incrementAndGet,forbidden);
        var result=assertInstanceOf(ArmyQueryHistoryStore.AlreadyCompact.class,store.record(new ArmyQueryHistoryStore.CompactInput(summary)));
        assertEquals(1,checked.get());assertArrayEquals(summary.bytes(),result.summary().bytes());
        full.put("query_sequence","1");
        assertThrows(IllegalArgumentException.class,()->ArmyQueryHistoryStore.buildSummary(new RawJson(ArmyJson.bytes(full)),Optional.empty(),Optional.empty(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->new ArmyQueryHistoryStore.Settings(temporary,-1));
    }

    @Test void aPortCannotFabricateAFullStoredReferenceWithoutTheActualWriteAndUnknownInventoryStaysUnknown()throws Exception {
        var forged=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path folder){return 0;}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){
                return new ArmyQueryHistoryStore.StoredFile(target,0,"0".repeat(64));
            }
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary,1024),Optional.empty(),forged);
        assertInstanceOf(ArmyQueryHistoryStore.IoError.class,store.record(input(0,0,false)));
        var failedScan=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path folder)throws IOException{throw new IOException("retained inventory unreadable");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("failed inventory cannot write");}
        };
        var unavailable=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary,1024),Optional.empty(),failedScan);
        var result=assertInstanceOf(ArmyQueryHistoryStore.IoError.class,unavailable.record(input(0,0,false)));
        assertTrue(ArmyJson.parse(result.summary().bytes()).at("/history_storage_diagnostic/charged_bytes").isNull());
    }

    @Test void flatInventoryCountsAllOrdinaryPartialsWithoutDescendingAndCreateNeverOverwrites()throws Exception {
        Path leaf=temporary.resolve("inventory");Files.createDirectory(leaf);Files.writeString(leaf.resolve("old.partial"),"123");
        Files.createDirectory(leaf.resolve("child"));Files.writeString(leaf.resolve("child/ignored"),"not a flat sidecar");
        var guard=new MeteredGuard(temporary,1024,false);var io=new ArmyQueryHistoryStore.GuardedFileIO(guard,temporary.resolve("original.lock"));
        assertEquals(3,io.existingFlatBytes(leaf));
        Path existing=leaf.resolve("old.partial");
        assertThrows(IOException.class,()->io.writeExclusive(existing,1024,out->new ArmyQueryHistoryStore.Written(0,"0".repeat(64))));
        assertEquals("123",Files.readString(existing));
    }
}


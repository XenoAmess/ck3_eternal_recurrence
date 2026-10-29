package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import java.nio.file.Files;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Pure archival contract interpretation; controlled packets grant no live query, writer or Game authority. */
final class ArmyStrengthsReplayTest {
    @TempDir Path temporary;
    @Test void exactInstalledFamilyReplaysOriginalPacketWithoutLivePrepareOrCache() throws Exception {
        Fixture fixture = fixture(result());
        assertTrue(fixture.contract().hasPureReplay());
        Read live = fixture.contract().decode(fixture.receipt());
        Read archived = fixture.contract().replay(fixture.receipt());
        assertEquals(live, archived);
        assertSame(fixture.receipt(), archived.original());
        var history = fixture.contract().projectOriginalHistory(fixture.receipt());
        assertEquals(org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.Kind.ARMY_STRENGTHS, history.kind());
        var full = ArmyJson.parse(history.fullResult().bytes());
        assertEquals(STEP, full.get("step").textValue());
        assertEquals(archived.sequence(), full.get("query_sequence").bigIntegerValue());
        assertEquals(archived.rows().size(), full.withArray("army_strengths").size());
        assertTrue(full.get("queried_revision").isIntegralNumber());
        assertEquals(fixture.selection().snapshot().binding().publicRevision(), full.get("queried_revision").bigIntegerValue());
        assertTrue(history.sourceClosure().contains(fixture.contract().sourceRef()));
        assertArrayEquals(history.fullResult().bytes(), fixture.contract().projectOriginalHistory(fixture.receipt()).fullResult().bytes());
        assertEquals(0, archived.rows().getFirst().core().army().value());
        assertArrayEquals(fixture.receipt().original().originalPacket(), archived.original().original().originalPacket());
        assertSame(fixture.contract(), fixture.contracts().issue(fixture.catalog(), fixture.selection()));
        assertTrue(fixture.catalog().containsIdentity(fixture.contract()));
        assertEquals("ordinary_core_v1", ArmyStrengthsCodec.parseValue(fixture.contract().prepare(fixture.receipt().request(), "unused-prepare-id").additionalFields()).get("army_strengths_profile").textValue());
        // A new catalog cannot issue a family installed in a different composition root.
        var foreign = new RootReadContractCatalog(List.of(), List.of());
        assertThrows(IllegalArgumentException.class, () -> fixture.contracts().issue(foreign, fixture.selection()));
    }

    @Test void replayKeepsStrictNativeTypesScopeAndSelectedOriginalContext() throws Exception {
        ObjectNode wrongType = result().put("query_sequence", true);
        Fixture malformed = fixture(wrongType);
        assertThrows(IllegalArgumentException.class, () -> malformed.contract().decode(malformed.receipt()));
        assertThrows(IllegalArgumentException.class, () -> malformed.contract().replay(malformed.receipt()));
        ObjectNode wrongScope = result();
        ArmyJson.object(wrongScope.withArray("army_strengths").get(0)).put("army_id", 1);
        Fixture crossedScope = fixture(wrongScope);
        assertThrows(IllegalArgumentException.class, () -> crossedScope.contract().replay(crossedScope.receipt()));
        Fixture exact = fixture(result());
        PlanningReadReceipt original = exact.receipt();
        var wrongId = new PlanningReadReceipt(original.request(), original.contractId() + "-foreign", original.requestId(), original.before(), original.after(), original.original());
        assertThrows(IllegalArgumentException.class, () -> exact.contract().replay(wrongId));
        assertThrows(IllegalArgumentException.class, () -> exact.contract().projectOriginalHistory(wrongId));
        var request = original.request();
        var changedDeadline = new PlanningReadRequest(request.before(), request.source(), request.sessionId(), request.operation(), request.arguments(), request.deadline().plusSeconds(1));
        var crossed = new PlanningReadReceipt(changedDeadline, original.contractId(), original.requestId(), original.before(), original.after(), original.original());
        assertThrows(IllegalArgumentException.class, () -> exact.contract().replay(crossed));
    }

    @Test void firstCompleteResultIsArchivedBeforeLookupAndCanonicalReplayOnlyReadsOriginals() throws Exception {
        ObjectNode raw = result(); ArmyJson.object(raw.withArray("army_strengths").get(0)).put("ai_base_power_raw", Long.MAX_VALUE);
        Fixture fixture = fixture(raw); PureArchive archive = new PureArchive();
        var receipt = fixture.receipt(); var reference = archive.preserveRead(receipt);
        var known = new PlanningReadResult.Known<>(fixture.contract().decode(receipt), receipt, reference);
        var projection = fixture.contract().projectOriginalHistory(receipt);
        assertThrows(IllegalArgumentException.class, () -> archive.materialReferenceOf(projection.fullResult()),
                "lookup must not manufacture an absent complete-result artifact");
        var candidate = DriverReadHistoryRowProducer.prepareRich(archive, fixture.catalog(), fixture.contract(), known, List.of(known), 1);
        assertEquals(2, archive.materialWrites, "retain the original full result before its canonical row");
        assertEquals(2, archive.materials.size()); assertTrue(candidate.fullResultReference().isPresent());
        var complete = archive.loadMaterial(candidate.fullResultReference().orElseThrow());
        assertEquals(DriverJson.object(projection.fullResult().bytes(), RawJson.MAXIMUM_BYTES),
                DriverJson.object(complete.bytes(), RawJson.MAXIMUM_BYTES));
        assertEquals(candidate.row(), DriverReadHistoryRowProducer.decode(candidate.row().encode()));
        var roles = candidate.provenance().publicNumbers().orElseThrow();
        var publicResult = roles.toPublic(candidate.row().result());
        assertEquals(candidate.row().result(), roles.fromPublic(publicResult));
        var rows = OpportunityJson.array(publicResult.get("army_strengths"), "original strengths");
        assertEquals(new OpportunityJson.Text(Long.toString(Long.MAX_VALUE)),
                OpportunityJson.object(rows.getFirst(), "original army").get("ai_base_power_raw"));
        byte[] originalPacket = receipt.original().originalPacket().clone();
        archive.readOnly = true; int writes = archive.materialWrites;
        var restored = DriverReadHistoryRowProducer.decode(archive.loadMaterial(candidate.rowReference()).bytes());
        assertEquals(known, DriverReadHistoryRowProducer.replayCanonical(archive, fixture.catalog(), fixture.contract(), restored));
        assertSame(candidate, DriverReadHistoryRowProducer.replay(archive, fixture.catalog(), fixture.contract(), known, candidate));
        assertEquals(writes, archive.materialWrites); assertArrayEquals(originalPacket, receipt.original().originalPacket());
        var emptyCatalog = new RootReadContractCatalog(List.of(), List.of());
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.replayCanonical(archive, emptyCatalog, fixture.contract(), restored));
        var savedFull = archive.materials.remove(candidate.fullResultReference().orElseThrow());
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.replayCanonical(archive, fixture.catalog(), fixture.contract(), restored),
                "cold replay must not recreate a lost original complete result");
        archive.materials.put(candidate.fullResultReference().orElseThrow(), savedFull);
        assertEquals(writes, archive.materialWrites);
    }

    @Test void missingForeignOrDuplicatedComponentsRejectBeforeAnyMaterialWrite() throws Exception {
        Fixture fixture = fixture(result()); PureArchive archive = new PureArchive();
        var reference = archive.preserveRead(fixture.receipt());
        var known = new PlanningReadResult.Known<>(fixture.contract().decode(fixture.receipt()), fixture.receipt(), reference);
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.prepareRich(archive, fixture.catalog(), fixture.contract(), known, List.of(), 1));
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.prepareRich(archive, fixture.catalog(), fixture.contract(), known, List.of(known, known), 1));
        Fixture other = fixture(result());
        var foreign = new PlanningReadResult.Known<>(other.contract().decode(other.receipt()), other.receipt(), archive.preserveRead(other.receipt()));
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.prepareRich(archive, fixture.catalog(), fixture.contract(), known, List.of(known, foreign), 1));
        var actual = fixture.receipt();
        var changed = new PlanningReadReceipt(actual.request(), actual.contractId()+"-wrong", actual.requestId(), actual.before(), actual.after(), actual.original());
        var wrong = new PlanningReadResult.Known<>(known.value(), changed, archive.preserveRead(changed));
        assertThrows(IllegalArgumentException.class, () -> DriverReadHistoryRowProducer.prepareRich(archive, fixture.catalog(), fixture.contract(), wrong, List.of(wrong), 1));
        assertEquals(0, archive.materialWrites); assertTrue(archive.materials.isEmpty());
    }


    @Test void actualInstalledDisabledPlanSkipsCompleteEncodingAndKeepsPrivateCaptureIdentity()throws Exception {
        AtomicInteger admission=new AtomicInteger();AtomicBoolean current=new AtomicBoolean(true);
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path leaf){throw new AssertionError("explicit0 must not scan");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("explicit0 must not write");}
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("not-created"),0),()->{
            admission.incrementAndGet();if(!current.get())throw new IOException("original DATA admission no longer current");
        },forbidden);
        ObjectNode original=result().put("unknown_future_wide_native_field",Long.MAX_VALUE);
        ArmyJson.object(original.withArray("army_strengths").get(0)).put("ai_base_power_raw",Long.MAX_VALUE);
        Fixture fixture=fixture(original,Optional.of(store));byte[] packet=fixture.receipt().original().originalPacket().clone();
        var plan=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
        assertSame(store,fixture.contracts().sidecarStore().orElseThrow());assertEquals(0,admission.get());
        assertThrows(IllegalStateException.class,()->fixture.contract().projectOriginalHistory(fixture.receipt()));
        assertEquals(0,admission.get(),"full-only API rejects Plan without storage or eager encoding");
        var captured=plan.captureOriginal();assertSame(captured,plan.captureOriginal());assertEquals(1,admission.get());
        plan.requireOriginal(captured);assertEquals(2,admission.get());
        var summary=DriverJson.object(captured.summary().bytes(),RawJson.MAXIMUM_BYTES);
        assertEquals(new OpportunityJson.Bool(false),summary.get("full_result_preserved"));
        assertFalse(summary.members().containsKey("unknown_future_wide_native_field"));assertFalse(Files.exists(temporary.resolve("not-created")));
        var publicRows=OpportunityJson.array(captured.publicNumbers().toPublic(summary).get("armies"),"summary armies");
        assertEquals(new OpportunityJson.Text(Long.toString(Long.MAX_VALUE)),OpportunityJson.object(publicRows.getFirst(),"summary row").get("ai_base_power_raw"));
        var cold=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
        assertThrows(IllegalArgumentException.class,()->cold.requireOriginal(captured));
        current.set(false);assertThrows(IOException.class,()->plan.requireOriginal(captured));int before=admission.get();
        var replayed=cold.replayOriginal(captured.storageOriginal());assertEquals(captured,replayed);assertEquals(before,admission.get(),"cold DATA replay must not run live admission/store");
        ObjectNode changed=ArmyJson.parse(captured.storageOriginal().bytes()).put("limit_bytes",1);
        assertThrows(IllegalArgumentException.class,()->cold.replayOriginal(new RawJson(ArmyJson.bytes(changed))));
        assertArrayEquals(packet,fixture.receipt().original().originalPacket());
    }

    @Test void disabledOriginalSummaryIsTheOnlyCanonicalRowAndColdReplayCreatesNoFullArtifact()throws Exception {
        AtomicInteger records=new AtomicInteger();
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path leaf){throw new AssertionError("no directory capture");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("no sidecar output");}
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("disabled"),0),records::incrementAndGet,forbidden);
        Fixture fixture=fixture(result(),Optional.of(store));PureArchive archive=new PureArchive();var receipt=fixture.receipt();
        var ref=archive.preserveRead(receipt);var known=new PlanningReadResult.Known<>(fixture.contract().decode(receipt),receipt,ref);
        var candidate=DriverArmySummaryHistoryRowProducer.prepare(archive,fixture.catalog(),fixture.contract(),known,List.of(known),1,List.of(fixture.contract().sourceRef()));
        assertEquals(2,archive.materialWrites,"only finite storage metadata and original small row");assertEquals(2,archive.materials.size());
        assertEquals(candidate.row(),DriverArmySummaryHistoryRowProducer.decode(candidate.row().encode()));
        assertTrue(candidate.row().result().get("armies") instanceof OpportunityJson.Arr);
        assertFalse(candidate.row().result().members().containsKey("army_strengths"));
        archive.readOnly=true;int writes=archive.materialWrites;int guards=records.get();
        var restored=DriverArmySummaryHistoryRowProducer.decode(archive.loadMaterial(candidate.rowReference()).bytes());
        assertEquals(known,DriverArmySummaryHistoryRowProducer.replayCanonical(archive,fixture.catalog(),fixture.contract(),restored));
        assertEquals(guards,records.get());assertEquals(writes,archive.materialWrites);
        assertSame(candidate,DriverArmySummaryHistoryRowProducer.replay(archive,fixture.catalog(),fixture.contract(),known,candidate));
        assertTrue(records.get()>guards,"live candidate revalidates the identical original admission");assertEquals(writes,archive.materialWrites);
        var badCatalog=new RootReadContractCatalog(List.of(),List.of());
        assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.replayCanonical(archive,badCatalog,fixture.contract(),restored));
    }


    @Test void positiveSourceOwnedPlanReplaysTheExactHeldSidecarAndRejectsReplacementWithoutRecordingAgain()throws Exception {
        // Actual temporary file DATA port. Family Store/Reference regressions separately own guarded Root I/O qualification.
        AtomicInteger writes=new AtomicInteger(),admission=new AtomicInteger();
        var io=new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path leaf)throws IOException {return 0;}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body)throws IOException {
                var buffer=new java.io.ByteArrayOutputStream();
                var actual=body.write((bytes,offset,length)->{if((long)buffer.size()+length>maximum)throw new IOException("finite DATA output quote exceeded");buffer.write(bytes,offset,length);return length;});
                byte[] retained=buffer.toByteArray();assertEquals(actual.bytes(),retained.length);assertEquals(actual.sha256(),ActionCodec.sha256(retained));
                Files.createDirectories(target.getParent());Files.write(target,retained,java.nio.file.StandardOpenOption.CREATE_NEW);writes.incrementAndGet();
                return new ArmyQueryHistoryStore.StoredFile(target,retained.length,ActionCodec.sha256(retained));
            }
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("actual-positive"),1<<20),admission::incrementAndGet,io);
        ObjectNode raw=result();ArmyJson.object(raw.withArray("army_strengths").get(0)).put("ai_base_power_raw",Long.MAX_VALUE);
        Fixture fixture=fixture(raw,Optional.of(store));
        var plan=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
        assertEquals(0,writes.get());var captured=plan.captureOriginal();plan.requireOriginal(captured);assertEquals(1,writes.get());
        var numeric=ArmyJson.parse(captured.summary().bytes());assertTrue(numeric.get("full_result_preserved").booleanValue());
        Path original=Path.of(numeric.get("raw_result_reference").get("path").textValue());
        var exact=ArmyQueryHistoryReference.read(captured.summary(),store.settings().evidenceDirectory(),1<<20);
        assertEquals(original,exact.reference().path());assertEquals(Long.MAX_VALUE,ArmyJson.parse(exact.completeDriver().bytes()).withArray("army_strengths").get(0).get("ai_base_power_raw").longValue());
        var cold=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
        int current=admission.get();assertEquals(captured,cold.replayOriginal(captured.storageOriginal()));assertEquals(current,admission.get());assertEquals(1,writes.get());
        ObjectNode crossed=ArmyJson.parse(captured.storageOriginal().bytes()).put("evidence_directory",temporary.resolve("foreign").toString());
        assertThrows(IllegalArgumentException.class,()->cold.replayOriginal(new RawJson(ArmyJson.bytes(crossed))));
        byte[] bytes=Files.readAllBytes(original);int position=new String(bytes,java.nio.charset.StandardCharsets.UTF_8).indexOf("9223372036854775807");assertTrue(position>=0);
        bytes[position]='8';Files.write(original,bytes,java.nio.file.StandardOpenOption.TRUNCATE_EXISTING);
        assertThrows(IllegalArgumentException.class,()->cold.replayOriginal(captured.storageOriginal()));assertEquals(1,writes.get());
    }

    @Test void summaryOriginalProducerRejectsInventedTypedKnownBeforeCapture()throws Exception {
        AtomicInteger admission=new AtomicInteger();
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path leaf){throw new AssertionError("no capture");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("no write");}
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("rejected"),0),admission::incrementAndGet,forbidden);
        Fixture fixture=fixture(result(),Optional.of(store));PureArchive archive=new PureArchive();var receipt=fixture.receipt();var ref=archive.preserveRead(receipt);
        var invented=new PlanningReadResult.Known<>(new Object(),receipt,ref);
        assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.prepare(archive,fixture.catalog(),fixture.contract(),invented,List.of(invented),1,List.of(fixture.contract().sourceRef())));
        assertEquals(0,admission.get());assertEquals(0,archive.materialWrites);
        var originalKnown=new PlanningReadResult.Known<>(fixture.contract().decode(receipt),receipt,ref);
        var secondQuery=new Query(Profile.ORDINARY_CORE_V1,Mode.AUTO_CORE,new Missing<>(),EntryMode.FIXED_CHUNK0_PREPARE,EntryMode.OBSERVED_PREPARED);
        var secondSelection=new ArmyStrengthsContracts.Selection(fixture.selection().snapshot(),secondQuery,fixture.selection().originalHello(),new Missing<>());
        var secondContract=fixture.contracts().issue(fixture.catalog(),secondSelection);
        var secondRaw=ArmyStrengthsSourceTest.input(result().put("query_sequence",2),ArmyStrengthsSourceTest.projectedHello()).original().original();
        var secondReceipt=new PlanningReadReceipt(fixture.contracts().request(secondSelection),secondContract.contractId(),secondRaw.requestId(),secondRaw.before(),secondRaw.after(),secondRaw.original());
        assertEquals(secondContract.decode(secondReceipt),secondContract.replay(secondReceipt));
        var forgedComponent=new PlanningReadResult.Known<>(new Object(),secondReceipt,archive.preserveRead(secondReceipt));
        assertThrows(IllegalArgumentException.class,()->DriverArmySummaryHistoryRowProducer.prepare(archive,fixture.catalog(),fixture.contract(),originalKnown,List.of(originalKnown,forgedComponent),1,List.of(fixture.contract().sourceRef())));
        assertEquals(0,admission.get());assertEquals(0,archive.materialWrites);
    }


    @Test void actualPrivateAdmissionRejectionStillRecordsTheOriginalSmallDiagnosticWithoutRequiringStorageSuccess()throws Exception {
        AtomicInteger checks=new AtomicInteger();
        var forbidden=new ArmyQueryHistoryStore.ArtifactIO() {
            @Override public long existingFlatBytes(Path leaf){throw new AssertionError("rejected storage must not scan");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("rejected storage must not write");}
        };
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve("admission-denied"),0),()->{
            checks.incrementAndGet();throw new IOException("original sidecar budget denied");
        },forbidden);
        Fixture fixture=fixture(result(),Optional.of(store));PureArchive archive=new PureArchive();var receipt=fixture.receipt();
        Read actual=fixture.contract().decode(receipt);var known=new PlanningReadResult.Known<>(actual,receipt,archive.preserveRead(receipt));
        var candidate=DriverArmySummaryHistoryRowProducer.prepare(archive,fixture.catalog(),fixture.contract(),known,List.of(known),1,List.of(fixture.contract().sourceRef()));
        assertEquals(1,checks.get(),"actual denied capture must not need its storage admission to become successful");
        assertEquals(new OpportunityJson.Text("sidecar_admission_rejected"),candidate.row().result().get("unavailable_reason"));
        assertEquals(new OpportunityJson.Bool(false),candidate.row().result().get("full_result_preserved"));assertEquals(2,archive.materialWrites);
        assertFalse(Files.exists(temporary.resolve("admission-denied")));archive.readOnly=true;
        assertSame(candidate,DriverArmySummaryHistoryRowProducer.replay(archive,fixture.catalog(),fixture.contract(),known,candidate));
        assertEquals(known,DriverArmySummaryHistoryRowProducer.replayCanonical(archive,fixture.catalog(),fixture.contract(),candidate.row()));
        assertEquals(1,checks.get());assertEquals(actual,fixture.contract().replay(receipt));
    }


    @Test void originalQuotaAndIoFailureOutcomesRebuildSmallSummariesWithoutRetryOrCompleteEncoding()throws Exception {
        for(boolean ioFailure:List.of(false,true)) {
            AtomicInteger scans=new AtomicInteger(),admission=new AtomicInteger();
            var denied=new ArmyQueryHistoryStore.ArtifactIO() {
                @Override public long existingFlatBytes(Path leaf)throws IOException {scans.incrementAndGet();if(ioFailure)throw new IOException("actual sidecar scan unavailable");return 1;}
                @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("no write after quota/scan failure");}
            };
            var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(temporary.resolve(ioFailure?"io-failure":"quota-full"),1),admission::incrementAndGet,denied);
            Fixture fixture=fixture(result().put("unknown_future_wide_native_field",Long.MAX_VALUE),Optional.of(store));
            var plan=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
            var captured=plan.captureOriginal();plan.requireOriginal(captured);assertEquals(1,scans.get());assertEquals(2,admission.get());
            var summary=ArmyJson.parse(captured.summary().bytes());assertEquals(ioFailure?"sidecar_io_error":"sidecar_budget_exhausted",summary.get("unavailable_reason").textValue());
            assertFalse(summary.get("full_result_preserved").booleanValue());
            var cold=assertInstanceOf(DriverReadHistoryRichMaterial.ArmySummaryPlan.class,fixture.contract().projectOriginalHistoryPayload(fixture.receipt()));
            assertEquals(captured,cold.replayOriginal(captured.storageOriginal()));assertEquals(1,scans.get());assertEquals(2,admission.get());
        }
    }

    /** Strict DATA custody only. This test supplies no writer/session/Root/Native or durable-store qualification. */
    private static final class PureArchive implements ActionPorts.OutcomeArchive {
        private final java.util.Map<ExactRef,PlanningReadReceipt> reads = new java.util.LinkedHashMap<>();
        private final java.util.Map<ExactRef,RawJson> materials = new java.util.LinkedHashMap<>();
        private int materialWrites; private boolean readOnly;
        private static ExactRef materialRef(RawJson raw) { return new ExactRef("controlled-material-"+ActionCodec.sha256(raw.bytes()), raw.bytes().length, ActionCodec.sha256(raw.bytes())); }
        private static void require(boolean condition) { if (!condition) throw new IllegalArgumentException("original pure archive input absent or changed"); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) {
            require(!readOnly);
            // Full typed receipt equality is retained; this test does not claim production receipt serialization.
            var body = new OpportunityJson.Obj(java.util.Map.of("contract",new OpportunityJson.Text(original.contractId()),
                    "request",new OpportunityJson.Text(original.requestId()),"session",new OpportunityJson.Text(original.request().sessionId()),
                    "source_time",new OpportunityJson.Text(original.request().source().observedAtUtc()),
                    "packet",new OpportunityJson.Text(java.util.Base64.getEncoder().encodeToString(original.original().originalPacket()))));
            RawJson raw = new RawJson(OpportunityJson.encode(body)); ExactRef ref = materialRef(raw);
            var prior = reads.putIfAbsent(ref, original); require(prior==null || prior.equals(original)); return ref;
        }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { var original=reads.get(ref);require(original!=null);return original; }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { return reads.entrySet().stream().filter(row->row.getValue().equals(original)).map(java.util.Map.Entry::getKey).findFirst().orElseThrow(()->new IllegalArgumentException("original typed receipt absent")); }
        @Override public ExactRef preserveMaterial(RawJson original) {
            require(!readOnly);ExactRef ref=materialRef(original);RawJson prior=materials.putIfAbsent(ref,new RawJson(original.bytes()));
            require(prior==null || java.util.Arrays.equals(prior.bytes(),original.bytes())); materialWrites++;return ref;
        }
        @Override public RawJson loadMaterial(ExactRef ref) { var original=materials.get(ref);require(original!=null && materialRef(original).equals(ref));return original; }
        @Override public ExactRef materialReferenceOf(RawJson original) {ExactRef ref=materialRef(original);require(materials.containsKey(ref));loadMaterial(ref);return ref;}
        private static UnsupportedOperationException unused() {return new UnsupportedOperationException("this pure DATA test has no action/native/writer authority");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unused();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw unused();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unused();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unused();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unused();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw unused();}
        @Override public byte[] loadNativeFrame(ExactRef ref){throw unused();}
    }

    private record Fixture(ArmyStrengthsContracts contracts, RootReadContractCatalog catalog,
            ArmyStrengthsContracts.Selection selection, ReadContract<Read> contract, PlanningReadReceipt receipt) { }

    private static Fixture fixture(ObjectNode result) throws Exception { return fixture(result,Optional.empty()); }
    private static Fixture fixture(ObjectNode result,Optional<ArmyQueryHistoryStore> sameStore) throws Exception {
        var seed = ArmyStrengthsSourceTest.input(result, ArmyStrengthsSourceTest.projectedHello());
        NativeWire.Hello seedHello = seed.originalHello().orElseThrow();
        byte[] oldPacket = seedHello.packet().value();
        ObjectNode helloBody = NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(oldPacket, 4, oldPacket.length)));
        helloBody.withArray("capabilities").add(CAPABILITY);
        NativeWire.Hello hello = (NativeWire.Hello) NativeWire.decode(NativeWire.packet(ArmyJson.bytes(helloBody)));
        var query = new Query(Profile.ORDINARY_CORE_V1, Mode.AUTO_CORE, new Missing<>(), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED);
        var selection = new ArmyStrengthsContracts.Selection(seed.snapshot(), query, hello, new Missing<>());
        var normalizers = new ArmyStrengthsFamilies.Registry(); normalizers.freeze();
        var source = new ExactRef("controlled-strengths-pure-replay-source", 1, "a".repeat(64));
        var contracts = new ArmyStrengthsContracts(source, source, normalizers, new ArmyStrengthsPipeline(), List.of(source,settingsDataRef()), sameStore,settingsDataRef());
        var catalog = new RootReadContractCatalog(List.of(), contracts.families());
        ReadContract<Read> contract = contracts.issue(catalog, selection);
        PlanningReadReceipt old = seed.original().original();
        var receipt = new PlanningReadReceipt(contracts.request(selection), contract.contractId(), old.requestId(), old.before(), old.after(), old.original());
        return new Fixture(contracts, catalog, selection, contract, receipt);
    }

    private static ObjectNode result() {
        ObjectNode result = ArmyJson.empty().put("step", STEP).put("accepted", true).put("status", "available")
                .put("query_sequence", 1).put("backend_id", "controlled-original-packet")
                .put("army_strengths_profile", "ordinary_core_v1").put("army_observed_phase_coverage", "not_requested");
        ObjectNode row = result.putArray("army_strengths").addObject().put("status", "available").put("army_id", 0)
                .put("native_carmy_id", 0).put("scope_role", "player").put("regiment_count", 0).put("current_soldiers", 0)
                .put("maximum_soldiers", 0).put("ai_base_power_raw", 0).put("ai_base_power_scale", 100000).putNull("unavailable_reason");
        row.putArray("war_ids");
        return result;
    }

    /** Actual typed settings encoder DATA for source-only contract tests; no Bound, Root or storage qualification. */
    private static ExactRef settingsDataRef() {
        byte[] raw=OriginalDriverQueryHistorySettings.encodeRequest(new OriginalDriverQueryHistorySettings.Request(
                "controlled-strengths-settings",java.time.Instant.EPOCH,java.time.Instant.EPOCH.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Disabled(),0,
                        OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE)));
        return new ExactRef("controlled-explicit-inline-strengths-settings",raw.length,ActionCodec.sha256(raw));
    }
}

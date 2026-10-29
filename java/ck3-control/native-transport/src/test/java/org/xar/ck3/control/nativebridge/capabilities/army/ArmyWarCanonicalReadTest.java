package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Real installed ArmyWarReads contract/decoder boundary. Synthetic packets do not qualify Root canonical history or Game. */
final class ArmyWarCanonicalReadTest {
    private static final Instant OBSERVED = Instant.parse("2026-10-24T00:00:00Z");
    private static final Instant DEADLINE = OBSERVED.plusSeconds(60);
    private static final ExactRef SOURCE = new ExactRef("synthetic-source-no-game", 1, "a".repeat(64));
    private static final PlanningReadPort NO_NATIVE = new PlanningReadPort() {
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            throw new AssertionError("canonical contract inspection must not submit Native I/O");
        }
    };
    @Test void installerSupplierIsDeferredUntilAQueryActuallyNeedsIndependentOwners() {
        var calls = new AtomicInteger();
        var reads = new ArmyWarReads(SOURCE, SOURCE, NO_NATIVE, () -> {
            calls.incrementAndGet(); throw new IllegalStateException("publisher not yet bound");
        });
        var frame = frame();
        assertTrue(reads.currentDeclarations(frame).isEmpty());
        var selection = selection(frame, PublicMethod.QUERY_DECLARABLE_WARS);
        var catalog = new RootReadContractCatalog(List.of(), reads.families());
        assertEquals("query-declarable-wars", reads.contract(catalog, selection).operation().value());
        assertEquals(0, calls.get(), "catalog installation must precede actual publisher binding");
    }
    @Test void actualOriginalDecoderAndExplicitSameFrameReuseAllowOnlyTransportDeadlineChange() throws Exception {
        var f = fixture(PublicMethod.QUERY_DECLARABLE_WARS); var original = receipt(f, packet());
        var value = f.contract().decode(original);
        assertEquals(value, f.contract().replay(original));
        assertEquals(BigInteger.TWO, original.request().before().frame().revision());
        assertEquals(BigInteger.valueOf(3), original.request().before().frame().identity().nativeRevision());
        var later = withDeadline(f.request(), DEADLINE.plusSeconds(30));
        f.contract().requireCanonicalReuse(original, value, later, f.frame().actual().semantic());
        assertEquals(DEADLINE, original.request().deadline(), "reuse never renews the original native invocation");
        assertEquals(value, f.contract().replay(original));
        var declarations = assertInstanceOf(ArmyWarReadCodec.Declarations.class, value);
        assertEquals("202-0--1", declarations.choices().getFirst().declarationId());
        assertEquals(BigInteger.valueOf(5), declarations.querySequence().value());
    }
    @Test void crossedContextOrArgumentsAndChangedTypedValueCannotReuseOriginal() throws Exception {
        var f = fixture(PublicMethod.QUERY_DECLARABLE_WARS); var original = receipt(f, packet()); var value = f.contract().replay(original);
        var old = f.request();
        var changedArgs = new PlanningReadRequest(old.before(), old.source(), old.sessionId(), old.operation(),
                old.arguments().with("unexpected", new OpportunityJson.Bool(true)), DEADLINE.plusSeconds(30));
        assertThrows(IllegalArgumentException.class, () -> f.contract().requireCanonicalReuse(original, value, changedArgs, f.frame().actual().semantic()));
        var changedSession = new PlanningReadRequest(old.before(), old.source(), "another-session", old.operation(), old.arguments(), DEADLINE.plusSeconds(30));
        assertThrows(IllegalArgumentException.class, () -> f.contract().requireCanonicalReuse(original, value, changedSession, f.frame().actual().semantic()));
        var changed = new ArmyWarReadCodec.Declarations(List.of(), UInt64.positive(BigInteger.valueOf(5)),
                ((ArmyWarReadCodec.Declarations)value).normalizedResult());
        assertThrows(IllegalArgumentException.class, () -> f.contract().requireCanonicalReuse(original, changed, withDeadline(old, DEADLINE.plusSeconds(30)), f.frame().actual().semantic()));
    }
    @Test void malformedWholePacketCannotAcquireAnOriginalDeclarationValue() throws Exception {
        var f = fixture(PublicMethod.QUERY_DECLARABLE_WARS);
        ObjectNode bad = packet(); ((ObjectNode) bad.path("result")).put("query_sequence", true);
        assertThrows(IllegalArgumentException.class, () -> f.contract().replay(receipt(f, bad)));
        ObjectNode wrongNative = packet(); ((ObjectNode) wrongNative.path("result")).put("snapshot_revision", 2);
        assertThrows(IllegalArgumentException.class, () -> f.contract().replay(receipt(f, wrongNative)));
        ObjectNode missing = packet(); ((ObjectNode) missing.path("result")).remove("declarable_wars");
        assertThrows(IllegalArgumentException.class, () -> f.contract().replay(receipt(f, missing)));
    }
    @Test void declarationOptInDoesNotAuthorizeOtherWarFamiliesToReuseAcrossDeadlines() throws Exception {
        var f = fixture(PublicMethod.QUERY_WAR_TERMINATION_OPTIONS); var original = receipt(f, packet());
        var value = new ArmyWarReadCodec.Declarations(List.of(), UInt64.positive(BigInteger.ONE), f.frame().actual().semantic());
        assertThrows(IllegalArgumentException.class, () -> f.contract().requireCanonicalReuse(original, value,
                withDeadline(f.request(), DEADLINE.plusSeconds(30)), f.frame().actual().semantic()));
    }
    @Test void producerRetainsUnknownAcrossDirectPlannerReadsAndOnlyExactOriginalCanPublish() throws Exception {
        var sends = new AtomicInteger(); var f = fixture(PublicMethod.QUERY_DECLARABLE_WARS, unknownBoundary(sends));
        assertInstanceOf(PlanningReadResult.Unavailable.class, f.reads().read(null, f.contract(), f.selection(), java.time.Duration.ofSeconds(60)));
        var pending = f.reads().pendingDeclaration().orElseThrow();
        assertEquals(f.request(), pending.request()); assertSame(f.contract(), pending.contract());
        assertEquals("original-fixture", pending.originalUnknown().requestId()); assertTrue(pending.originalUnknown().originalRequestPacket().length > 0);
        assertThrows(IllegalArgumentException.class, () -> f.reads().read(null, f.contract(), f.selection(), java.time.Duration.ofSeconds(60)));
        assertEquals(1, sends.get(), "a second planner/public caller cannot resubmit the unresolved original");
        ObjectNode other = packet().put("request_id", "different-request"); var otherReceipt = receipt(f, other);
        var unrelated = new PlanningReadResult.Known<>(f.contract().replay(otherReceipt), otherReceipt, SOURCE);
        assertThrows(IllegalArgumentException.class, () -> f.reads().publishOriginal(f.selection(), unrelated));
        assertEquals(pending, f.reads().pendingDeclaration().orElseThrow());
        var original = receipt(f, packet()); var known = new PlanningReadResult.Known<>(f.contract().replay(original), original, SOURCE);
        f.reads().publishOriginal(f.selection(), known);
        assertSame(known,f.reads().requireCurrentDeclarations(f.frame()).originalRead());
        assertTrue(f.reads().pendingDeclaration().isEmpty()); assertEquals(SOURCE, f.reads().requireCurrentDeclarations(f.frame()).evidence());
        assertEquals(1, sends.get(), "original late publication is not another Native write");
    }
    @Test void soleUnknownCustodyFormatsOriginalPendingAndNeverQueriesOrExportsAResultFrame() throws Exception {
        var sends=new AtomicInteger();var boundary=unknownBoundary(sends);var f=fixture(PublicMethod.QUERY_DECLARABLE_WARS,boundary);
        var before=ArmyDeclarationDiagnostics.capture(f.reads(),boundary);assertTrue(before.field().isEmpty());
        assertThrows(IllegalArgumentException.class,()->ArmyDeclarationDiagnostics.capture(f.reads(),NO_NATIVE));
        assertThrows(IllegalArgumentException.class,()->f.reads().read(null,f.contract(),f.selection()));
        assertThrows(IllegalArgumentException.class,()->f.reads().read(null,f.contract(),f.selection(),java.time.Duration.ZERO));assertEquals(0,sends.get());
        var requested=java.time.Duration.ofSeconds(120).plusMillis(125);
        assertInstanceOf(PlanningReadResult.Unavailable.class,f.reads().read(null,f.contract(),f.selection(),requested));
        var captured=ArmyDeclarationDiagnostics.capture(f.reads(),boundary);var pending=captured.pending().orElseThrow();
        assertEquals(requested,pending.originalTimeout());assertEquals("original-fixture",pending.requestId());
        var raw=ArmyJson.object(OpportunityJson.toNode(captured.field().orElseThrow()));
        assertEquals(java.util.Set.of("request_id","step","status","binding","timeout_seconds"),ArmyJson.names(raw));
        assertEquals(new java.math.BigDecimal("120.125"),raw.get("timeout_seconds").decimalValue());
        var binding=ArmyJson.object(raw.get("binding"));assertEquals(java.util.Set.of("snapshot_id","revision","native_revision","episode_run_id","date_raw","paused","map_ready","player_character_id","bridge_pid","connection_generation"),ArmyJson.names(binding));
        assertEquals(BigInteger.valueOf(3),binding.get("native_revision").bigIntegerValue());assertEquals(BigInteger.TWO,binding.get("revision").bigIntegerValue());
        assertFalse(raw.has("result_frame"));assertFalse(raw.has("rawReturn"));assertTrue(captured.originalCustody().orElseThrow().originalUnknown().rawReturn().isPresent());
        assertEquals(captured.field(),ArmyDeclarationDiagnostics.capture(f.reads(),boundary).field());captured.requireCurrent(f.reads(),boundary);
        assertThrows(IllegalArgumentException.class,()->before.requireCurrent(f.reads(),boundary));assertEquals(1,sends.get());
        byte[] originalPacket=f.reads().pendingDeclaration().orElseThrow().originalUnknown().originalRequestPacket();
        var original=receipt(f,packet());var known=new PlanningReadResult.Known<>(f.contract().replay(original),original,SOURCE);f.reads().publishOriginal(f.selection(),known);
        assertThrows(IllegalArgumentException.class,()->captured.requireCurrent(f.reads(),boundary));assertTrue(ArmyDeclarationDiagnostics.capture(f.reads(),boundary).field().isEmpty());
        assertEquals("original-fixture",NativeWire.decodeExecuteRequest(originalPacket).requestId());assertEquals(1,sends.get());
    }
    @Test void wrongOriginalSentPacketKeepsCustodyButCannotExportAnAssumedEmptyDiagnostic() throws Exception {
        var sends=new AtomicInteger();var boundary=unknownBoundary(sends,true);var f=fixture(PublicMethod.QUERY_DECLARABLE_WARS,boundary);
        f.reads().read(null,f.contract(),f.selection(),java.time.Duration.ofSeconds(60));
        assertThrows(IllegalArgumentException.class,()->ArmyDeclarationDiagnostics.capture(f.reads(),boundary));
        assertTrue(f.reads().pendingDeclaration().isPresent());assertEquals(1,sends.get());
    }
    @Test void actualPendingProjectionMatchesPinnedOriginalPythonTimeoutAndDiagnosticProducer(@org.junit.jupiter.api.io.TempDir java.nio.file.Path temporary) throws Exception {
        var sends=new AtomicInteger();var boundary=unknownBoundary(sends);var f=fixture(PublicMethod.QUERY_DECLARABLE_WARS,boundary);
        f.reads().read(null,f.contract(),f.selection(),java.time.Duration.ofSeconds(120).plusMillis(125));
        var actual=ArmyDeclarationDiagnostics.capture(f.reads(),boundary).field().orElseThrow();
        var input=ArmyJson.empty();input.set("snapshot",OpportunityJson.toNode(f.frame().actual().semantic()));input.put("timeout",new java.math.BigDecimal("120.125"));
        String python=requiredOriginal("xar.native.producer.python"),source=requiredOriginal("xar.native.producer.source");
        if(!java.nio.file.Path.of(python).isAbsolute()||!java.nio.file.Path.of(source).isAbsolute())throw new IllegalArgumentException("actual original fixture requires absolute Python/source paths");
        var output=temporary.resolve("original-pending.json");var error=temporary.resolve("original-pending.stderr");
        Process child=new ProcessBuilder(python,"-X","utf8","-c",ORIGINAL_PENDING,source,"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",java.util.Base64.getEncoder().encodeToString(ArmyJson.bytes(input)))
                .redirectOutput(output.toFile()).redirectError(error.toFile()).start();
        if(!child.waitFor(20,java.util.concurrent.TimeUnit.SECONDS)){child.destroyForcibly();throw new java.io.IOException("original pending diagnostics process timed out");}
        if(child.exitValue()!=0)throw new java.io.IOException("original pending diagnostics failed: "+java.nio.file.Files.readString(error));
        var original=DriverJson.object(java.nio.file.Files.readAllBytes(output),DriverJson.MAX_NATIVE_BYTES);
        assertEquals(actual,original.get("pending"));assertEquals(OpportunityJson.Nil.INSTANCE,original.get("closed"));assertEquals(1,sends.get());
    }
    private static String requiredOriginal(String key){String value=System.getProperty(key);if(value==null||value.isBlank())throw new IllegalStateException("NOT EXECUTED: required original pending fixture property missing: "+key);return value;}
    private static final String ORIGINAL_PENDING="""
        import ast,base64,copy,hashlib,json,sys,threading,types
        from pathlib import Path
        source=Path(sys.argv[1])
        if hashlib.sha256(source.read_bytes()).hexdigest()!=sys.argv[2]:raise RuntimeError('original Native Driver source drift')
        tree=ast.parse(source.read_text(encoding='utf-8-sig'))
        cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='NativeHeadlessGameplayDriver')
        class Timeout(Exception):
            request_id='original-fixture'
        scope={'copy':copy,'json':json,'QUERY_DECLARABLE_WARS_STEP':'query-declarable-wars','_NativeCommandResultTimeoutError':Timeout,'BridgeUnavailableError':RuntimeError}
        def method(name):
            node=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name==name)
            node.decorator_list=[]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),scope)
            return scope[name]
        row=json.loads(base64.b64decode(sys.argv[3]))
        owner=types.SimpleNamespace(_driver_state_lock=threading.RLock(),_pending_declaration_query=None,declarable_wars_timeout_seconds=row['timeout'])
        owner.take_snapshot_without_native_command_history=lambda:copy.deepcopy(row['snapshot'])
        owner._declaration_result_binding=method('_declaration_result_binding')
        def send(step,**kwargs):
            if step!='query-declarable-wars' or kwargs['timeout_seconds']!=row['timeout']:raise RuntimeError('wrong original request/timeout')
            raise Timeout('synthetic original low-level timeout')
        owner._execute_primitive_step=send
        try:method('_execute_declarable_war_step')(owner,'query-declarable-wars',expected_revision=row['snapshot']['revision'])
        except RuntimeError:pass
        if owner._pending_declaration_query is None:raise RuntimeError('original did not retain pending')
        owner._pending_declaration_query['result_frame']={'private':'retained-not-exported'}
        owner.state=types.SimpleNamespace(diagnostics=lambda:{})
        owner._transport_error=lambda:None
        owner.endpoint=types.SimpleNamespace(transport_diagnostic=lambda:None)
        diagnostic=method('diagnostics')
        pending=diagnostic(owner)['pending_declaration_query']
        if 'result_frame' in pending or owner._pending_declaration_query.get('result_frame') is None:raise RuntimeError('original custody/frame omission changed')
        owner._pending_declaration_query=None
        closed=diagnostic(owner)['pending_declaration_query']
        print(json.dumps({'pending':pending,'closed':closed},separators=(',',':')))
        """;
    private static PlanningReadPort unknownBoundary(AtomicInteger sends) { return unknownBoundary(sends,false); }
    private static PlanningReadPort unknownBoundary(AtomicInteger sends,boolean crossedPacket) {
        return new PlanningReadPort() {
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) { return unknown(contract, request); }
            @Override public <T> PlanningReadResult<T> read(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same, ReadContract<T> contract, PlanningReadRequest request) { return unknown(contract, request); }
            @Override public <T> PlanningReadAttempt<T> readOriginal(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,
                    ReadContract<T> contract, PlanningReadRequest request) {
                return new PlanningReadAttempt<>(unknown(contract,request),Optional.empty());
            }
            private <T> PlanningReadResult<T> unknown(ReadContract<T> contract, PlanningReadRequest request) {
                sends.incrementAndGet();
                try {
                    byte[] sent = NativeWire.execute("original-fixture", crossedPacket ? "query-war-termination-options-1" : request.operation().value(), request.before().frame().identity().nativeRevision(), ArmyJson.bytes(ArmyJson.empty()));
                    return new PlanningReadResult.Unavailable<>("synthetic Native I/O timeout", Optional.of(new NativeActionPort.Unknown("original-fixture", "timeout", sent, Optional.of(new RawJson(ArmyJson.bytes(ArmyJson.empty().put("result_frame","retained-not-exported")))))));
                } catch (java.io.IOException invalid) { throw new IllegalStateException(invalid); }
            }
        };
    }
    private record Fixture(ArmyWarReads reads, ArmyWarReads.Selection selection, ArmyRetreatFrames.Current frame, ReadContract<ArmyWarReadCodec.Observation> contract, PlanningReadRequest request) { }
    private static Fixture fixture(PublicMethod method) { return fixture(method, NO_NATIVE); }
    private static Fixture fixture(PublicMethod method, PlanningReadPort actualReadBoundary) {
        var reads = new ArmyWarReads(SOURCE, SOURCE, actualReadBoundary); var frame = frame();
        var selected = selection(frame, method); var catalog = new RootReadContractCatalog(List.of(), reads.families());
        var contract = reads.contract(catalog, selected); var c = frame.context();
        return new Fixture(reads, selected, frame, contract, new PlanningReadRequest(c.before(), c.source(), c.sessionId(), contract.operation(), ArmyWarReads.arguments(selected.input()), c.deadline()));
    }
    private static ArmyWarReads.Selection selection(ArmyRetreatFrames.Current frame, PublicMethod method) {
        var revision = new ArmyCalls.Revision(new Present<>(BigInteger.TWO));
        ArmyCalls.Call input = method == PublicMethod.QUERY_DECLARABLE_WARS ? new ArmyCalls.Frame(method, revision)
                : new ArmyCalls.War(method, revision, BigInteger.ONE);
        return new ArmyWarReads.Selection(input, frame, Optional.empty());
    }
    private static ArmyRetreatFrames.Current frame() {
        var source = new G2Source("synthetic-test-no-game", OBSERVED.toString(), "1.20.0.4", SOURCE);
        var key = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), BigInteger.valueOf(3), BigInteger.valueOf(77)), "native:3", BigInteger.TWO, "canonical-fixture");
        var identity = new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), key, 1);
        ObjectNode raw = ArmyJson.empty().put("paused", true).put("map_ready", true).put("snapshot_id", "native:3").put("revision", 2).put("native_revision", 3)
                .put("date_raw", 77).put("episode_run_id", "canonical-fixture");
        raw.putObject("played_character").put("character_id", 101).put("alive", true); raw.putObject("diagnostics").put("bridge_pid", 42).put("connection_generation", 1);
        var semantic = DriverJson.object(ArmyJson.bytes(raw), DriverJson.MAX_NATIVE_BYTES);
        return new ArmyRetreatFrames.Current(new Complete(identity, source, "fixture-session", BigInteger.ONE, semantic, SOURCE, OBSERVED, "b".repeat(64)), DEADLINE);
    }
    private static PlanningReadRequest withDeadline(PlanningReadRequest original, Instant deadline) {
        return new PlanningReadRequest(original.before(), original.source(), original.sessionId(), original.operation(), original.arguments(), deadline);
    }
    private static ObjectNode packet() {
        ObjectNode top = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", "original-fixture").put("ok", true);
        ObjectNode result = top.putObject("result").put("step", "query-declarable-wars").put("accepted", true).put("status", "available").put("query_sequence", 5).put("snapshot_revision", 3);
        ObjectNode choice = result.putArray("declarable_wars").addObject().put("declaration_id", "202-0--1").put("target_character_id", 202).put("casus_belli_index", 0)
                .put("casus_belli_key", "claim_cb").put("configuration_index", -1).put("claimant_character_id", -1);
        choice.putArray("target_title_ids").add(0).add(17); return top;
    }
    private static PlanningReadReceipt receipt(Fixture f, ObjectNode packet) throws Exception {
        var c = f.frame().context(); var operation = f.contract().operation();
        var guard = new PlanningReadGuard(new GuardEvidence(c.before(), c.source(), c.sessionId(), BigInteger.ONE, operation, SOURCE, SOURCE,
                "synthetic-canonical-source", OBSERVED, DEADLINE), true, true, true, "b".repeat(64));
        var full = new RawJson(ArmyJson.bytes(packet));
        String id = packet.path("request_id").textValue();
        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(ArmyJson.bytes(packet.path("result")))), full, NativeWire.packet(full.bytes()));
        return new PlanningReadReceipt(f.request(), f.contract().contractId(), id, guard, guard, ack);
    }
}

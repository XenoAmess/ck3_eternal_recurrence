package org.xar.ck3.control.wave2.events.nativepulse;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.nativepulse.NativeScriptMathProgram.*;

/** Real token producer, all new consumers, shared original Raw codec and archive recomputation. */
final class NativeScriptMathProgramTest {
    private static final NativePlayableAnnualGate.Executable EXE = NativePlayableAnnualGate.Executable.CURRENT_12004;
    private static final ExactRef REF = new ExactRef("fixture-only", 1, "0".repeat(64));
    private static final NativeRawScriptValue.Context CONTEXT = new NativeRawScriptValue.Context(
        new NativeRawScriptValue.Scope(BigInteger.valueOf(5), new BigInteger("18446744073709550001")), BigInteger.TEN, BigInteger.ZERO, BigInteger.ONE, 0);
    private static Root root() { return new Root(new BigInteger("18446744073709550002"), MATH_PRIMARY_VTABLE_RVA, MATH_BASE_VTABLE_RVA, Entry.NAMED_VALUE_70_375438F); }
    private static NativeRawScriptValue.Input operand(long raw, Optional<NativeRawScriptValue.Random> random) {
        return raw(new NativeRawScriptValue.Pdx(1, raw, 0, Optional.empty(), Optional.empty(), Optional.empty(), List.of()), random);
    }
    private static NativeRawScriptValue.Input raw(NativeRawScriptValue.Pdx value, Optional<NativeRawScriptValue.Random> random) {
        return new NativeRawScriptValue.Input(EXE, REF, REF, value, CONTEXT, random, List.of(), List.of());
    }
    private static SimpleField field(int token, long raw) { return new SimpleField(token, REF, operand(raw, Optional.empty())); }
    private static SimpleField unary(int token) { return new SimpleField(token,REF,raw(new NativeRawScriptValue.Pdx(0,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()),Optional.empty())); }
    private static Input input(List<Field> fields) { return new Input(EXE, REF, root(), CONTEXT, Optional.empty(), fields); }
    private static long known(List<Field> fields) { Result result = run(input(fields)); assertEquals(Status.RECONSTRUCTED, result.status()); return result.reconstructedPrefixRaw(); }

    @Test void actualParserTokensProduceExactNativeOpcodesAndPreserveOccurrences() {
        int[] tokens = {0x2d2,0x4f3,0x4f4,0x4f5,0x4f6,0x4f7,0x2a4,0x2a3,0x99b,0x548,0x56e,0x56f,0x74b,0x93d};
        for (int index = 0; index < tokens.length; index++) assertEquals(index, operatorForToken(tokens[index]).orElseThrow().nativeOpcode());
        assertTrue(operatorForToken(0x459).isEmpty()); assertThrows(IllegalArgumentException.class, () -> field(0x459, 7));
        SimpleField repeated = field(0x4f3, 7); Produced output = produce(input(List.of(repeated, repeated)));
        assertEquals(List.of(0,1), output.originalOrder().stream().map(Node::originalIndex).toList()); assertEquals(14, consume(output).reconstructedPrefixRaw());
        assertThrows(IllegalArgumentException.class, () -> consume(new Produced(output.original(), List.of(output.originalOrder().get(1), output.originalOrder().get(0)))));
    }
    @Test void zeroInitializedWrapperAndSequentialRealArithmeticUseOneAccumulator() {
        assertEquals(0, known(List.of()));
        assertEquals(150000, known(List.of(field(0x2d2,100000),field(0x4f3,25000),field(0x4f5,200000),field(0x4f4,100000))));
        assertEquals(Long.MIN_VALUE, known(List.of(field(0x2d2,Long.MAX_VALUE),field(0x4f3,1))));
        assertEquals(Long.MAX_VALUE, known(List.of(field(0x2d2,Long.MIN_VALUE),field(0x4f4,1))));
    }
    @Test void actualWideMultiplyAndDivisionBranchesPreserveRaw64() {
        assertEquals(Long.MAX_VALUE, known(List.of(field(0x2d2,Long.MAX_VALUE),field(0x4f5,100000))));
        assertEquals(Long.MIN_VALUE, known(List.of(field(0x2d2,Long.MIN_VALUE),field(0x4f6,100000))));
        assertEquals(4611686018427387903L, known(List.of(field(0x2d2,Long.MAX_VALUE),field(0x4f6,200000))));
        assertEquals(-4611686018427387904L, known(List.of(field(0x2d2,Long.MIN_VALUE),field(0x4f6,200000))));
        assertEquals(92233720368547L, known(List.of(field(0x2d2,Long.MAX_VALUE),field(0x4f6,10000000000L))));
        assertEquals(-100000, known(List.of(field(0x2d2,Long.MAX_VALUE),field(0x4f6,1))));
        assertEquals(0, known(List.of(field(0x2d2,Long.MIN_VALUE),field(0x4f6,Long.MIN_VALUE))));
    }
    @Test void divideAndModuloZeroDiagnoseNoWriteThenContinueOuterNodes() {
        Result result = run(input(List.of(field(0x2d2,123),field(0x4f6,0),field(0x4f7,0),field(0x4f3,7))));
        assertEquals(Status.RECONSTRUCTED,result.status()); assertEquals(130,result.reconstructedPrefixRaw());
        assertEquals(Optional.of(Diagnostic.DIVIDE_ZERO_NO_WRITE),result.applied().get(1).diagnostic());
        assertEquals(Optional.of(Diagnostic.MODULO_ZERO_NO_WRITE),result.applied().get(2).diagnostic());
        assertEquals(123,result.applied().get(1).afterRaw()); assertEquals(123,result.applied().get(2).afterRaw());
        Result opcode8zero=run(input(List.of(field(0x2d2,123),field(0x99b,0),field(0x4f3,7))));
        assertEquals(Status.RECONSTRUCTED,opcode8zero.status());assertEquals(130,opcode8zero.reconstructedPrefixRaw());
        assertEquals(Optional.of(Diagnostic.OPERATION_8_ZERO_NO_WRITE),opcode8zero.applied().get(1).diagnostic());
    }
    @Test void moduloNativeOverflowRetainsOperandRandomMutationAndExactPrefix() {
        var random = Optional.of(new NativeRawScriptValue.Random(0,0));
        var range = new NativeRawScriptValue.Pdx(2,-1,-1,Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        Input original = new Input(EXE,REF,root(),CONTEXT,random,List.of(new SimpleField(0x2d2,REF,operand(Long.MIN_VALUE,random)),new SimpleField(0x4f7,REF,raw(range,random))));
        Result result = run(original); assertEquals(Status.NATIVE_DIVIDE_OVERFLOW,result.status()); assertEquals(1,result.blockedOriginalIndex());
        assertEquals(Long.MIN_VALUE,result.reconstructedPrefixRaw()); assertEquals(Optional.of(new NativeRawScriptValue.Random(2,0)),result.afterRandom()); assertEquals(1,result.applied().size());
    }
    @Test void minMaxAbsAndRoundingIncludeNativeSigned32UnitNarrowing() {
        assertEquals(-7,known(List.of(field(0x2d2,7),field(0x2a4,-7)))); assertEquals(7,known(List.of(field(0x2d2,-7),field(0x2a3,7))));
        assertEquals(Long.MIN_VALUE,known(List.of(field(0x2d2,Long.MIN_VALUE),unary(0x74b))));
        assertEquals(-100000,known(List.of(field(0x2d2,-50000),unary(0x548))));
        assertEquals(-100000,known(List.of(field(0x2d2,-100001),unary(0x56e))));
        assertEquals(-200000,known(List.of(field(0x2d2,-100001),unary(0x56f))));
        assertEquals(0,known(List.of(field(0x2d2,429496729650001L),unary(0x56f))));
        assertEquals(100000,known(List.of(field(0x2d2,429496729650001L),unary(0x56e))));
        assertEquals(100000,known(List.of(field(0x2d2,429496729650001L),unary(0x548))));
    }
    @Test void unaryOperatorEvaluatesConstructorRawAndCannotParseOrConsumeRandomOrVirtualOperand() {
        var leaf = new NativeRawScriptValue.Leaf(BigInteger.TEN,BigInteger.valueOf(0xa07610));
        var unresolved = new NativeRawScriptValue.Pdx(1,9,0,Optional.empty(),Optional.empty(),Optional.of(leaf),List.of());
        assertThrows(IllegalArgumentException.class,()->new SimpleField(0x56f,REF,raw(unresolved,Optional.empty())));
        var random = Optional.of(new NativeRawScriptValue.Random(0,1)); var range = new NativeRawScriptValue.Pdx(2,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        assertThrows(IllegalArgumentException.class,()->new SimpleField(0x56f,REF,raw(range,random)));
        var initialized=new NativeRawScriptValue.Pdx(0,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        Input original = new Input(EXE,REF,root(),CONTEXT,random,List.of(new SimpleField(0x2d2,REF,operand(199999,random)),new SimpleField(0x56f,REF,raw(initialized,random))));
        Result result=run(original);assertEquals(100000,result.reconstructedPrefixRaw());assertEquals(random,result.afterRandom());
        var evaluated=result.applied().getLast().originalOperandResult();assertEquals(NativeRawScriptValue.Branch.INLINE_KIND_ZERO,evaluated.branch());assertTrue(evaluated.trace().isEmpty());
        assertEquals(0,evaluated.rawCallsConsumed());assertEquals(0,evaluated.scopeCallsConsumed());
        assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class,weightOperand(original));
    }
    @Test void retainedNativeLoadAndConstructorDriveBothEntriesEveryConsumerAndStrictColdReplay()throws Exception {
        String configured=System.getProperty("xar.g2.m2.native03.path");assertNotNull(configured,"mandatory retained complete native03 original; no skipped source regression");
        Path path=Path.of(configured);assertEquals(23289L,Files.size(path));byte[] original=Files.readAllBytes(path);
        assertEquals("922b45379a0e2b025e5e315d2ed04d4154b8b327bf595ac0058651a1880f05a4",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)));
        var evidence=StrictJson.parse(original,NativeScriptMathProgramJson.MAX_BYTES);
        assertEquals("448b81200100004183e809741e4183e80174184183e80174124183f801740c488b41304883c13048ff6018c3cccccccc",evidence.get("leafs").get(0).get("raw_hex").textValue());
        boolean constructor=false;for(var function:evidence.get("functions"))if(function.get("entry").longValue()==0xa13ae0L){constructor=true;assertEquals(171,function.get("total_bytes").intValue());}
        assertTrue(constructor,"complete actual initializer proof required");MemoryStore store=new MemoryStore();ExactRef source=store.preserve(original);
        for(Entry entry:Entry.values())for(int token:new int[]{0x548,0x56e,0x56f,0x74b}) {
            var random=Optional.of(new NativeRawScriptValue.Random(10,20));
            var initialized=new NativeRawScriptValue.Input(EXE,source,source,new NativeRawScriptValue.Pdx(0,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()),CONTEXT,random,List.of(),List.of());
            SimpleField unary=new SimpleField(token,source,initialized);assertEquals(OperandLoad.CONSTRUCTOR_FIELDS_RETAINED,operandLoad(operatorForToken(token).orElseThrow()));
            Root bound=new Root(root().originalObjectU64(),MATH_PRIMARY_VTABLE_RVA,MATH_BASE_VTABLE_RVA,entry);
            Input input=new Input(EXE,source,bound,CONTEXT,random,List.of(unary));Input decoded=NativeScriptMathProgramJson.decode(NativeScriptMathProgramJson.encode(input));
            Result result=consume(produce(decoded));assertEquals(Status.RECONSTRUCTED,result.status());assertEquals(random,result.afterRandom());assertEquals(0,result.reconstructedPrefixRaw());
            assertTrue(result.applied().getFirst().originalOperandResult().trace().isEmpty());assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class,weightOperand(decoded));
            var archived=NativeScriptMathProgramArchive.preserve(decoded,store);assertEquals(result,NativeScriptMathProgramArchive.replay(NativeScriptMathProgramArchive.decode(NativeScriptMathProgramArchive.encode(archived)),store).recomputed());
            if(entry==Entry.NAMED_VALUE_70_375438F) {
                var before=new NativeNamedScriptValueProgram.Before(BigInteger.valueOf(7),NativeNamedScriptValueProgram.PRIMARY_VTABLE,NativeNamedScriptValueProgram.SECONDARY_VTABLE,0,false,Optional.empty());
                var named=new NativeNamedScriptValueProgram.Input(source,3,before,decoded,Optional.empty());assertEquals(result,NativeNamedScriptValueProgram.run(named).math());
                var saved=NativeNamedScriptValueProgramArchive.preserve(named,store);assertEquals(NativeNamedScriptValueProgram.run(named),NativeNamedScriptValueProgramArchive.replay(NativeNamedScriptValueProgramArchive.decode(NativeNamedScriptValueProgramArchive.encode(saved)),store).recomputed());
                assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class,NativeNamedScriptValueProgram.weightOperand(named));
            }
            for(NativeRawScriptValue.Pdx ghost:List.of(new NativeRawScriptValue.Pdx(1,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()),new NativeRawScriptValue.Pdx(0,1,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()),new NativeRawScriptValue.Pdx(2,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()))) {
                var operand=new NativeRawScriptValue.Input(EXE,source,source,ghost,CONTEXT,random,List.of(),List.of());
                assertThrows(IllegalArgumentException.class,()->new SimpleField(token,source,operand));
                var validBinary=new Input(EXE,source,bound,CONTEXT,random,List.of(new SimpleField(0x2d2,source,operand)));
                var wire=(ObjectNode)StrictJson.parse(NativeScriptMathProgramJson.encode(validBinary));((ObjectNode)wire.withArray("original_fields").get(0)).put("native_token",token);
                byte[] legacyInvalid=StrictJson.canonical(wire);assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramJson.decode(legacyInvalid));
                var invalidRecord=new NativeScriptMathProgramArchive.Recorded(store.preserve(legacyInvalid),archived.derived());
                assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramArchive.replay(invalidRecord,store));
            }
        }
    }
    @Test void orderedRandomAndUnknownClassesOrCalleesCannotBeSkipped() {
        Result unknown = run(input(List.of(field(0x2d2,5),new UnreviewedField(0x459,REF,"native conditional node class unreviewed"),field(0x4f3,7))));
        assertEquals(Status.UNKNOWN_NODE_CLASS,unknown.status()); assertEquals(5,unknown.reconstructedPrefixRaw()); assertEquals(1,unknown.blockedOriginalIndex());
        assertEquals(Status.UNKNOWN_OPERATION,run(input(List.of(field(0x99b,2)))).status()); assertEquals(Status.UNKNOWN_OPERATION,run(input(List.of(field(0x93d,2)))).status());
        var random = Optional.of(new NativeRawScriptValue.Random(0,0));var range = new NativeRawScriptValue.Pdx(2,0,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of());
        Input stale = new Input(EXE,REF,root(),CONTEXT,random,List.of(new SimpleField(0x2d2,REF,raw(range,random)),new SimpleField(0x4f3,REF,operand(8,random))));
        Result mismatch = run(stale); assertEquals(Status.ORIGINAL_RANDOM_MISMATCH,mismatch.status()); assertEquals(Optional.of(new NativeRawScriptValue.Random(2,0)),mismatch.afterRandom());
    }
    @Test void sharedRawCodecOwnsContextRandomAndRejectsSourceDriftOrCoercions() {
        Input original = input(List.of(field(0x2d2,Long.MAX_VALUE),new UnreviewedField(9,REF,"unreviewed original")));
        byte[] bytes = NativeScriptMathProgramJson.encode(original);assertEquals(original,NativeScriptMathProgramJson.decode(bytes));
        assertArrayEquals(bytes,NativeScriptMathProgramJson.encode(NativeScriptMathProgramJson.decode(bytes)));
        List<Consumer<ObjectNode>> invalid = List.of(row->row.remove("original_random"),row->row.putNull("original_fields"),row->row.put("extra",1),
            row->row.withObject("root").put("object_u64",9007199254740993L),row->row.withObject("root").put("object_u64","018446744073709550002"),
            row->row.withObject("root").put("primary_vtable_rva",true),row->row.withObject("root").put("base_vtable_rva",MATH_BASE_VTABLE_RVA+16),
            row->((ObjectNode)row.withArray("original_fields").get(0)).put("native_token",0x459),row->((ObjectNode)row.withArray("original_fields").get(0)).put("native_token",123.0),
            row->row.withObject("original_context").put("word_08_u64","20"),row->row.withObject("original_context").put("mode_u8",false));
        for(Consumer<ObjectNode> mutate:invalid){ObjectNode row=(ObjectNode)StrictJson.parse(bytes,NativeScriptMathProgramJson.MAX_BYTES);mutate.accept(row);
            assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramJson.decode(row.toString().getBytes(StandardCharsets.UTF_8)));}
    }
    @Test void sameFactoryCodecOriginalWeightedConsumerAndNoLoadedWriterCredit() {
        Input original = input(List.of(field(0x2d2,150000),field(0x4f3,50000)));
        Input decoded = NativeScriptMathProgramJson.decode(NativeScriptMathProgramJson.encode(original));var factor = weightOperand(decoded);
        var modifier = new NativeOnActionWeightProgram.TriggerModifier(new NativeOnActionWeightProgram.Always(new NativeOnActionWeightProgram.InlineBool(true)),factor,new NativeOnActionWeightProgram.InlineRaw(0));
        var review = new NativeOnActionWeightProgram.Review(EXE,new NativeOnActionWeightProgram.Context(0,NativeOnActionWeightProgram.ScopeVerdict.VALIDATED),
            List.of(new NativeOnActionWeightProgram.RowSource(3,20,Optional.of(new NativeOnActionWeightProgram.Definition(Optional.empty(),Optional.of(new NativeOnActionWeightProgram.Program(100000,List.of(modifier))))))),0);
        var computed=assertInstanceOf(NativeOnActionWeightedIndex.Computed.class,NativeOnActionWeightProgram.analyze(NativeOnActionWeightProgram.decode(NativeOnActionWeightProgram.encode(review))).computation());
        assertEquals(40,computed.rows().getFirst().nativeWeight());Result result=run(decoded);assertFalse(result.originalNamed70WriterClosed());assertFalse(result.completeNativeAst());assertFalse(result.currentLoadedSourceQualified());assertFalse(result.nativeGameExecuted());
    }
    @Test void originalProducerToAllConsumersArchiveColdReplayAndNestedCustodyTamper() throws Exception {
        MemoryStore store=new MemoryStore();ExactRef observation=store.preserve("synthetic original observation fixture bytes".getBytes(StandardCharsets.UTF_8));
        ExactRef ast=store.preserve("synthetic original token and nested operand source fixture bytes".getBytes(StandardCharsets.UTF_8));
        var raw=new NativeRawScriptValue.Input(EXE,observation,ast,new NativeRawScriptValue.Pdx(1,200000,0,Optional.empty(),Optional.empty(),Optional.empty(),List.of()),CONTEXT,Optional.empty(),List.of(),List.of());
        Input original=new Input(EXE,observation,root(),CONTEXT,Optional.empty(),List.of(new SimpleField(0x2d2,ast,raw)));
        var recorded=NativeScriptMathProgramArchive.preserve(original,store);
        var replayed=NativeScriptMathProgramArchive.replay(NativeScriptMathProgramArchive.decode(NativeScriptMathProgramArchive.encode(recorded)),store);
        assertEquals(original,replayed.original());assertEquals(run(original),replayed.recomputed());
        assertInstanceOf(NativeOnActionWeightProgram.InlineRaw.class,weightOperand(replayed.original()));
        ExactRef wrong=store.preserve("{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramArchive.replay(new NativeScriptMathProgramArchive.Recorded(recorded.original(),wrong),store));
        byte[] saved=store.contents.get(ast.path());store.contents.put(ast.path(),"changed source".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramArchive.replay(recorded,store));store.contents.put(ast.path(),saved);
        store.contents.put(recorded.original().path(),"{}".getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->NativeScriptMathProgramArchive.replay(recorded,store));
    }
    private static final class MemoryStore implements NativeOnActionFieldArchive.Store {
        private final Map<String,byte[]> contents=new HashMap<>();private int sequence;
        @Override public ExactRef preserve(byte[] original){try{byte[] bytes=original.clone();String path="memory/"+sequence++;contents.put(path,bytes);
            return new ExactRef(path,bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}catch(java.security.NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
        @Override public byte[] load(ExactRef ref)throws IOException{byte[] bytes=contents.get(ref.path());if(bytes==null)throw new IOException("missing original");return bytes.clone();}
    }
}

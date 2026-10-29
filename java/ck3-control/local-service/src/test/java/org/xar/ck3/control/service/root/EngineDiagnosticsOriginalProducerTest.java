package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.EngineDiagnostics.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.catalog.VanillaEventCatalog;

/** Original byte payloads enter the production streaming accumulator, not an alternate test parser. */
class EngineDiagnosticsOriginalProducerTest {
    private static final Query ALL=new Query(100,100);
    private static PresentLog summarize(LogName name,byte[] original,Query query)throws Exception {
        return EngineDiagnosticsReader.summarize(name,original,query,VanillaEventCatalog.load().textRules());
    }
    private static byte[] utf8(String value){return value.getBytes(StandardCharsets.UTF_8);}

    @Test void actualAccumulatorNormalizesOriginalFingerprintsAndPreservesFirstSampleAndScalarOrder()throws Exception {
        String a="[time][E] alpha 12 at 0xAB 12345678-1234-1234-1234-123456789abc";
        String b="[next][W] alpha 99 at 0xCD abcdefab-1234-1234-1234-123456789abc";
        byte[] original=utf8(a+"\n"+b+"\n[time][F] \uE000\n[time][E] \uD800\uDC00\n[time][E] word2 ٣\n");
        var value=summarize(LogName.ERROR,original,ALL);var groups=value.fingerprints().orElseThrow();
        assertEquals(5,value.lineCount());assertEquals(5,value.nonemptyLineCount());
        assertEquals(new Severity(1,3,1),value.severity());assertEquals(4,groups.uniqueCount());
        assertEquals(List.of("alpha <n> at <hex> <uuid>","word2 <n>","\uE000","\uD800\uDC00"),
                groups.values().stream().map(Fingerprint::fingerprint).toList());
        assertEquals(2,groups.values().getFirst().occurrences());assertEquals(a,groups.values().getFirst().sample());
        assertFalse(groups.truncated());assertEquals(original.length,value.bytes());
        assertEquals(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original)),value.sha256());
        var limited=summarize(LogName.ERROR,original,new Query(1,2));
        assertEquals(4,limited.fingerprints().orElseThrow().uniqueCount());assertTrue(limited.fingerprints().orElseThrow().truncated());
        assertEquals(value.tail().subList(3,5),limited.tail());
        assertTrue(summarize(LogName.DEBUG,original,ALL).fingerprints().isEmpty());
        var wire=EngineDiagnostics.log(value);
        assertEquals(wire,StrictJson.parse(StrictJson.canonical(wire),65536));
        assertEquals("log records, not independent bugs",wire.path("severity_count_semantics").textValue());
        assertEquals("normalized message groups, not confirmed independent bugs",wire.path("fingerprint_count_semantics").textValue());
    }

    @Test void originalPythonStripCasefoldAndSplitlinesReachBothConsumers()throws Exception {
        String original="A\r\nB\rC\nD\u000bE\u000cF\u001cG\u001dH\u001eI\u0085J\u2028K\u2029";
        var actual=summarize(LogName.GAME,utf8(original),ALL);
        assertEquals(11,actual.lineCount());assertEquals(List.of("A","B","C","D","E","F","G","H","I","J","K"),actual.tail());
        var literals=EngineDiagnosticsReader.summarize(utf8(original),new LiteralQuery(LogName.GAME,List.of("A","K"),5));
        assertEquals(11,literals.scannedLineCount());assertEquals(List.of(new Sample(1,"A")),literals.matches().getFirst().samples());
        assertEquals(List.of(new Sample(11,"K")),literals.matches().get(1).samples());
        var noSamples=EngineDiagnosticsReader.summarize(utf8("A A\nA"),new LiteralQuery(LogName.GAME,List.of("A"),0));
        assertEquals(2,noSamples.matches().getFirst().lineCount());assertTrue(noSamples.matches().getFirst().samples().isEmpty());
        assertEquals(0,summarize(LogName.GAME,new byte[0],ALL).lineCount());
        assertEquals(2,summarize(LogName.GAME,utf8("\n\n"),ALL).lineCount());
        var folded=summarize(LogName.GAME,utf8("\u2003\u001f\n[time][E]\u2003ßTARTUP 7\n"),ALL);
        assertEquals(2,folded.lineCount());assertEquals(1,folded.nonemptyLineCount());
        assertEquals(List.of("[time][E]\u2003ßTARTUP 7"),folded.milestones());
        assertEquals("ßTARTUP <n>",folded.fingerprints().orElseThrow().values().getFirst().fingerprint());
        String many=java.util.stream.IntStream.range(0,45).mapToObj(i->"STARTUP "+i).collect(java.util.stream.Collectors.joining("\n"));
        var milestones=summarize(LogName.SYSTEM,utf8(many),ALL).milestones();
        assertEquals(40,milestones.size());assertEquals("STARTUP 5",milestones.getFirst());assertEquals("STARTUP 44",milestones.getLast());
    }

    @Test void twoThousandMeansUnicodeScalarsForTailFingerprintAndLiteralSample()throws Exception {
        String emoji="\uD83D\uDE00",longLine=emoji.repeat(2001),expected=emoji.repeat(2000)+"…";
        var actual=summarize(LogName.ERROR,utf8(longLine),ALL);
        assertEquals(List.of(expected),actual.tail());assertEquals(2001,expected.codePointCount(0,expected.length()));
        var literal=EngineDiagnosticsReader.summarize(utf8(longLine),new LiteralQuery(LogName.ERROR,List.of(emoji),1));
        assertEquals(List.of(new Sample(1,expected)),literal.matches().getFirst().samples());
        var fingerprint=summarize(LogName.ERROR,utf8("[x][E] "+longLine),ALL).fingerprints().orElseThrow().values().getFirst();
        assertEquals(expected,fingerprint.fingerprint());assertEquals(2001,fingerprint.sample().codePointCount(0,fingerprint.sample().length()));
        assertEquals(emoji.repeat(2000),EngineDiagnosticsReader.bounded(emoji.repeat(2000)));
    }

    @Test void malformedUtf8UsesCpythonReplacementConsumptionInBothOriginalConsumers()throws Exception {
        // CPython errors='replace': restricted second bytes are reprocessed, truncated valid prefixes are one replacement.
        byte[][] inputs={{(byte)0xed,(byte)0xa0,(byte)0x80},{(byte)0xe2,(byte)0x82},
                {(byte)0xf0,(byte)0x90,(byte)0x80,(byte)0x80},{(byte)0xf4,(byte)0x90,(byte)0x80,(byte)0x80},
                {(byte)0xc0,(byte)0xaf},{(byte)0xe2,0x28,(byte)0xa1}};
        List<String> expected=List.of("���","�","\uD800\uDC00","����","��","�(�");
        for(int i=0;i<inputs.length;i++) {
            var actual=summarize(LogName.ERROR,inputs[i],ALL);assertEquals(List.of(expected.get(i)),actual.tail());
            var literals=EngineDiagnosticsReader.summarize(inputs[i],new LiteralQuery(LogName.ERROR,List.of("�"),5));
            assertEquals(1,literals.scannedLineCount());assertEquals(i==2?0:1,literals.matches().getFirst().lineCount());
            assertEquals(i==2?List.of():List.of(new Sample(1,expected.get(i))),literals.matches().getFirst().samples());
        }
    }
}

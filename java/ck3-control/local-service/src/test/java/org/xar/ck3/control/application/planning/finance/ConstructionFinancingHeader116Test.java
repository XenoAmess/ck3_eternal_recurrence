package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.api.io.CleanupMode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.planning.warcashprovenance.EmergencyFinancingAssessmentCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Exact optional header DATA and real same-writer CAS regression; never Native or Root permission.
 * Only existing pure quote/command builders are reused, not their @Test or private fixture authority.
 */
final class ConstructionFinancingHeader116Test {
    @TempDir(cleanup=CleanupMode.NEVER) Path directory;

    @Test void exactCachedHeaderPreservesNumbersStringsOrderDepthAndOwnedIsolation()throws Exception {
        Obj full=quote(true);Value deep=new Text("depth forty");
        for(int i=0;i<40;i++)deep=obj("layer",deep);
        Obj opaque=DriverJson.object(Base64.getDecoder().decode("eyJ6IjoxLjAwLCJhIjotMC4wLCJlIjoxZSswLCJmcmFjdGlvbiI6MC4xMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OSwiZXNjYXBlZFx1MDAyMGtleSI6Ilx1NmM0OVx1NWI1N1x1ZDgzZFx1ZGU4MFxuXCJcXCIsInJvd3MiOltudWxsLGZhbHNlLHt9LFtdXX0="),4096).with("deep",deep);
        full=withOpaque(full,opaque);byte[] exact=DriverJson.encode(full),caller=exact.clone();
        var observed=ObservedRequest.fromFullMaterial(caller);byte[] header=observed.exactFinancingWrapper().orElseThrow();
        Value expected=DriverJson.object(exact,FullJsonTree.MAXIMUM_BYTES).get("financing_request");
        Value actual=DriverJson.object(header,OrdinaryWartimeConstructionCodec.MAX_BYTES).get("financing_request");
        assertArrayEquals(DriverJson.encode(expected),DriverJson.encode(actual));
        assertArrayEquals(PublicDataJson.encodeTyped(expected).bytes(),PublicDataJson.encodeTyped(actual).bytes());
        String encoded=new String(DriverJson.encode(actual),StandardCharsets.UTF_8);
        assertTrue(encoded.contains("1.00")&&encoded.contains("-0.0")&&encoded.contains("1e+0")&&encoded.contains("0.12345678901234567890123456789"));
        assertTrue(encoded.indexOf("\"z\"")<encoded.indexOf("\"a\""));
        var other=ObservedRequest.fromFullMaterial(exact);caller[0]='[';header[0]='!';byte[] raw=observed.original();raw[0]='!';
        assertArrayEquals(exact,observed.original());assertArrayEquals(other.exactFinancingWrapper().orElseThrow(),observed.exactFinancingWrapper().orElseThrow());
        Obj changed=withOpaque(full,opaque.with("z",new DecimalValue("2.00")));
        var distinct=ObservedRequest.fromFullMaterial(DriverJson.encode(changed));
        assertFalse(Arrays.equals(distinct.exactFinancingWrapper().orElseThrow(),observed.exactFinancingWrapper().orElseThrow()));
        try(var f=new Store(directory.resolve("exact"))) {
            f.writer.locked(same->{String before=same.head().digest();
                var source=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession);Obj manifest=source.preserve(observed);
                assertManifestOracle(manifest,expected);
                // Deep64 Source DATA is independent from the existing Native expected-action domain (depth32).
                // The separate shallow cases cover canonical commands; this deep input is never admitted as an action.
                var loaded=ConstructionOriginalSource.resolve(same,new NativeOutcomeArchive(f.store,f.writer),manifest);
                assertArrayEquals(exact,loaded.observed().original());
                assertArrayEquals(PublicDataJson.encodeTyped(expected).bytes(),PublicDataJson.encodeTyped(loaded.original().get("financing_request")).bytes());
                assertEquals(before,same.head().digest());return null;
            });
        }
    }
    @Test void oversizedExactHeaderRetainsOldAcceptedSetAndUsesOriginalFullParseFallback()throws Exception {
        Obj full=quote(false);String token="1e+"+"0".repeat(124);List<Value> values=new ArrayList<>();
        for(int i=0;i<3000;i++)values.add(new DecimalValue(token));
        full=withOpaque(full,new Arr(values));byte[] exact=DriverJson.encode(full);
        Value expected=full.get("financing_request");assertTrue(DriverJson.encode(expected).length>OrdinaryWartimeConstructionCodec.MAX_BYTES);
        byte[] normalized=SdkProjectionJson.encode(DriverJson.toNode(expected),65_536);
        assertTrue(normalized.length<65_536);EmergencyFinancingAssessmentCodec.decode(normalized);
        assertThrows(RuntimeException.class,()->new ObservedRequest(exact));
        var observed=ObservedRequest.fromFullMaterial(exact);assertTrue(observed.exactFinancingWrapper().isEmpty());
        assertArrayEquals(exact,observed.original());assertTrue(observed.input().financing().isPresent());
        try(var f=new Store(directory.resolve("oversized"))) {
            final Obj fixedFull=full;
            f.writer.locked(same->{String before=same.head().digest();
                Obj manifest=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed);assertManifestOracle(manifest,expected);
                assertTrue(DriverJson.encode(manifest).length<ActionCodec.MAX_COMMAND_BYTES);
                var command=command(f.source,fixedFull,manifest,"p116-oversized-lexical-header-software-data");
                var canonical=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
                var loaded=ConstructionOriginalSource.resolveCommand(same,new NativeOutcomeArchive(f.store,f.writer),canonical);
                assertArrayEquals(exact,loaded.observed().original());assertTrue(loaded.observed().exactFinancingWrapper().isEmpty());
                assertTrue(new String(DriverJson.encode(object(canonical.arguments().get("ordinary_cash_request"),"manifest").get("financing_request")),StandardCharsets.UTF_8).contains(token));
                assertEquals(before,same.head().digest());return null;
            });
        }
        System.out.println("P116 oversized exact header="+DriverJson.encode(expected).length+" normalized="+normalized.length+" full="+exact.length);
    }
    @Test void presentNullIsDistinctFromOldSmallNoCacheAndRemainsExact()throws Exception {
        byte[] nonNullSmall=DriverJson.encode(quote(false));
        assertTrue(new ObservedRequest(nonNullSmall).exactFinancingWrapper().isEmpty());
        assertTrue(ObservedRequest.fromFullMaterial(nonNullSmall).exactFinancingWrapper().isPresent());
        Obj small=quote(false).with("financing_request",Nil.INSTANCE);byte[] bytes=DriverJson.encode(small);
        var old=new ObservedRequest(bytes);assertTrue(old.exactFinancingWrapper().isEmpty());
        var full=ObservedRequest.fromFullMaterial(bytes);assertArrayEquals("{\"financing_request\":null}".getBytes(StandardCharsets.UTF_8),full.exactFinancingWrapper().orElseThrow());
        Obj large=quote(true).with("financing_request",Nil.INSTANCE);byte[] largeBytes=DriverJson.encode(large);
        var largeObserved=ObservedRequest.fromFullMaterial(largeBytes);
        try(var f=new Store(directory.resolve("null"))) {
            f.writer.locked(same->{
                var source=new ConstructionOriginalSource(f.archive,f.writer::borrowedSession);Obj inline=source.preserve(old);
                assertArrayEquals(bytes,DriverJson.encode(inline));assertFalse(inline.members().containsKey("input_ref"));
                Obj manifest=source.preserve(largeObserved);assertSame(Nil.INSTANCE,manifest.get("financing_request"));
                assertArrayEquals(largeBytes,ConstructionOriginalSource.resolve(same,new NativeOutcomeArchive(f.store,f.writer),manifest).observed().original());return null;
            });
        }
    }
    @Test void cachedHeaderNeverReplacesCurrentPhysicalCustodyOrHeaderBinding()throws Exception {
        Obj full=quote(true);byte[] exact=DriverJson.encode(full);var observed=ObservedRequest.fromFullMaterial(exact);
        assertTrue(observed.exactFinancingWrapper().isPresent());
        try(var f=new Store(directory.resolve("cold"))) {
            Obj manifest=f.writer.locked(same->new ConstructionOriginalSource(f.archive,f.writer::borrowedSession).preserve(observed));
            var command=command(f.source,full,manifest,"p116-cold-software-data");var decoded=ActionCodec.decodeCommand(ActionCodec.encodeCommand(command));
            var receipt=new ActionReceipt(1,1,decoded,ActionCodec.bodySha256(decoded),new ActionState.IntentDurable());
            var calls=new AtomicInteger();var binding=ConstructionOriginalSource.archivedBinding(new NativeRecordedEvidenceVerifier.Binding(command.operation(),f.source,
                    (head,actual,archive)->calls.incrementAndGet()),f.writer::borrowedSession);
            f.writer.locked(same->{var cold=new NativeOutcomeArchive(f.store,f.writer);String before=same.head().digest();
                binding.verifier().verify(same.head(),receipt,cold.withSession(same));assertEquals(1,calls.get());
                Obj changed=manifest.with("financing_request",object(manifest.get("financing_request"),"header").with("schema",new Text("p116-mismatch")));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,changed));
                Path payload=Path.of(reference(manifest).path()),held=payload.resolveSibling(payload.getFileName()+".held");
                Path foreign=directory.resolve("same-original-foreign-path.json");Files.write(foreign,exact);
                Obj alias=manifest.with("input_ref",DriverJson.object(StrictJson.canonical(exact(foreign).toJson(),4096),4096));
                assertThrows(RuntimeException.class,()->ConstructionOriginalSource.resolve(same,cold,alias));
                Files.move(payload,held);
                try {assertThrows(RuntimeException.class,()->binding.verifier().verify(same.head(),receipt,cold.withSession(same)));assertEquals(1,calls.get());}
                finally {Files.move(held,payload);}
                binding.verifier().verify(same.head(),receipt,cold.withSession(same));assertEquals(2,calls.get());
                assertArrayEquals(exact,observed.original());assertEquals(before,same.head().digest());return null;
            });
        }
    }

    @Test void nearFullRawLimitWithLiteralUtf8ExpansionRemainsAcceptedAndDiscardsHeader()throws Exception {
        Obj minimal=quote(false).with("stage",new Text("BEFORE_OPTIONAL_QUERY")).with("quoted_outlay",Nil.INSTANCE);
        minimal=withOpaque(minimal,obj("large",new Text("P116-LARGE-NUMBER"),"unicode",new Text("P116-LITERAL-EMOJI")));
        byte[] base=DriverJson.encode(minimal);assertTrue(base.length<48_000);
        byte[] numberMarker="\"P116-LARGE-NUMBER\"".getBytes(StandardCharsets.US_ASCII),unicodeMarker="\"P116-LITERAL-EMOJI\"".getBytes(StandardCharsets.US_ASCII);
        int n=indexOf(base,numberMarker),u=indexOf(base,unicodeMarker);assertTrue(n>=0&&u>n);
        String unicode="\""+new String(Character.toChars(0x1F600)).repeat(6000)+"\"";byte[] literal=unicode.getBytes(StandardCharsets.UTF_8);
        int target=FullJsonTree.MAXIMUM_BYTES-1,numberLength=target-(base.length-numberMarker.length-unicodeMarker.length+literal.length);
        assertTrue(numberLength>60_000_000);
        byte[] raw=new byte[target];int offset=0;
        System.arraycopy(base,0,raw,0,n);offset+=n;raw[offset++]='1';raw[offset++]='e';raw[offset++]='+';
        Arrays.fill(raw,offset,offset+numberLength-3,(byte)'0');offset+=numberLength-3;
        int middle=n+numberMarker.length;System.arraycopy(base,middle,raw,offset,u-middle);offset+=u-middle;
        System.arraycopy(literal,0,raw,offset,literal.length);offset+=literal.length;
        int tail=u+unicodeMarker.length;System.arraycopy(base,tail,raw,offset,base.length-tail);offset+=base.length-tail;
        assertEquals(raw.length,offset);assertTrue(raw.length<FullJsonTree.MAXIMUM_BYTES);
        Expansion stats=verifyDerivedExpansionAndExistingTypedFinancing(raw);
        assertTrue(stats.expandedBytes()>FullJsonTree.MAXIMUM_BYTES);assertTrue(stats.normalizedBytes()<65_536);
        var observed=ObservedRequest.fromFullMaterial(raw);assertTrue(observed.exactFinancingWrapper().isEmpty());
        assertTrue(observed.input().financing().isPresent());assertArrayEquals(raw,observed.original());
        System.out.println("P116 nearlimit raw="+raw.length+" wrapper="+stats.expandedBytes()+" sdk="+stats.normalizedBytes()+" cache=false input64M/retain262K unchanged");
    }
    private record Expansion(int expandedBytes,int normalizedBytes) { }
    private static Expansion verifyDerivedExpansionAndExistingTypedFinancing(byte[] raw) {
        var root=FullJsonTree.parse(raw,FullJsonTree.MAXIMUM_BYTES);var wrapper=StrictJson.object();wrapper.set("financing_request",root.get("financing_request"));
        byte[] normalized=SdkProjectionJson.encode(root.get("financing_request"),65_536);EmergencyFinancingAssessmentCodec.decode(normalized);
        return new Expansion(FullJsonTree.encode(wrapper,FullJsonTree.MAXIMUM_DRIVER_BYTES).length,normalized.length);
    }
    private static int indexOf(byte[] source,byte[] target) {
        outer:for(int start=0;start<=source.length-target.length;start++){for(int i=0;i<target.length;i++)if(source[start+i]!=target[i])continue outer;return start;}return -1;
    }
    private static Obj withOpaque(Obj full,Value opaque) {
        Obj finance=object(full.get("financing_request"),"finance"),gap=object(finance.get("gap_request"),"gap"),snapshot=object(gap.get("snapshot"),"snapshot");
        return full.with("financing_request",finance.with("gap_request",gap.with("snapshot",snapshot.with("opaque_header116",opaque))));
    }
    private static void assertManifestOracle(Obj manifest,Value expected) {
        assertArrayEquals(DriverJson.encode(manifest.with("financing_request",expected)),DriverJson.encode(manifest));
    }
    private static Obj quote(boolean large)throws Exception {
        var method=ConstructionFullCustody113Test.class.getDeclaredMethod("quote",boolean.class);method.setAccessible(true);return (Obj)method.invoke(null,large);
    }
    private static ActionCommand command(ExactRef source,Obj full,Obj supplied,String id) {
        try {
            var method=ConstructionFullCustody113Test.class.getDeclaredMethod("command",ExactRef.class,Obj.class,Obj.class,String.class);method.setAccessible(true);
            return (ActionCommand)method.invoke(null,source,full,supplied,id);
        }catch(ReflectiveOperationException failure){throw new IllegalStateException(failure instanceof java.lang.reflect.InvocationTargetException?failure.getCause():failure);}
    }
    private static ExactRef reference(Obj manifest){return ExactRef.fromJson(StrictJson.parse(DriverJson.encode(object(manifest.get("input_ref"),"reference"))));}
    private static ExactRef exact(Path path)throws IOException{byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().normalize().toString(),bytes.length,ActionCodec.sha256(bytes));}
    private static final class Store implements AutoCloseable {
        final StorageWriteGuardTestSupport guard;final ImmutableArtifactStore store;final ContinuityWriter writer;final NativeOutcomeArchive archive;final ExactRef source;
        Store(Path root)throws IOException {
            Files.createDirectories(root);var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1").put("machine_id","construction-full-original-software-machine")
                    .put("sequence",0).put("window_id",1).put("status","running").put("target_days",10958).put("target_years",30).put("calendar_year_days",365.25)
                    .put("start_date_raw",1000).put("target_date_raw",263992).put("last_settled_date_raw",1000).put("last_settled_cycles",1).put("manual_repair_count",1)
                    .put("automatic_recovery_count",0).put("binding_lineage_count",0).put("NEXT",2);
            state.putObject("game_binding").put("pid",123).put("creation_date","2026-10-23T01:00:00Z");state.putNull("latest_binding");state.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",1);
            Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,ContinuityJson.canonical(state));Files.write(anchor,ContinuityJson.canonical(state));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer=root.resolve("p116-software-source.txt");Files.writeString(producer,"P116 independent SOFTWARE source metadata, never Root authority",StandardCharsets.UTF_8);source=exact(producer);
            var layout=new Layout(snapshot,exact(anchor),"construction-full-original-software-machine");Path objects=root.resolve("objects");Files.createDirectory(objects);
            guard=StorageWriteGuardTestSupport.create(root,layout.lock(),32*1024*1024);store=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects,layout.lock(),32*1024*1024),guard);
            writer=new ContinuityWriter(layout,List.of(source),new TransitionAuthority(){
                public String revalidate(ContinuityState head,Request request){throw new AssertionError("no action/domain mutation in custody DATA");}
                public ContinuityState reduce(ContinuityState head,Request request){throw new AssertionError("no action/domain mutation in custody DATA");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),guard);archive=new NativeOutcomeArchive(store,writer);
        }
        public void close()throws IOException{guard.close();}
    }
}

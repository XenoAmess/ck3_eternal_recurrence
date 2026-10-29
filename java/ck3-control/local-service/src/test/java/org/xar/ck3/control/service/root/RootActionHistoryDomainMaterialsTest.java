package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverActionHistoryCodec.*;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial.PublicNumbers;
import org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence;
import org.xar.ck3.control.application.planning.finance.OrdinaryFinancePolicies;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;

/** Original recording policies and callbacks for the sole genuine installed Root fixture. No Root is fabricated here. */
public final class RootActionHistoryDomainMaterialsTest {
    @Test void originalGiftHasTwoReturnedRecordingsWhilePilgrimageAndCloseHaveNoOwnRecorder()throws Exception {
        String python=required("xar.python"),repository=required("xar.repository.root");
        Path bridge=Path.of(repository).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge");
        var driver=SharedSourceFiles.observe(bridge.resolve("native_driver.py"));
        assertEquals(1658471,driver.source().bytes());assertEquals("eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603",driver.source().sha256());
        var planner=SharedSourceFiles.observe(bridge.resolve("player_pilgrimage_planner_private_transport.py"));
        var close=SharedSourceFiles.observe(bridge.resolve("death_succession_modal_private_transport.py"));
        var gift=SharedSourceFiles.observe(bridge.resolve("faction_gift_formal_route_v1.py"));
        assertEquals(exact(planner.source()),RootActionHistoryMaterialSourceFactory.pilgrimageOriginal(exact(driver.source())));
        assertEquals(exact(close.source()),RootActionHistoryMaterialSourceFactory.closeOriginal(exact(driver.source())));
        assertEquals(exact(gift.source()),RootActionHistoryMaterialSourceFactory.giftOriginal(exact(driver.source())));
        String oracle="""
                import ast,json,pathlib,sys
                bridge=pathlib.Path(sys.argv[1])/'ck3_autonomous_player/src/xar_autoplayer/bridge'
                def module(name):return ast.parse((bridge/name).read_text(encoding='utf-8-sig'),filename=str(bridge/name))
                def function(tree,name):
                    matches=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
                    assert len(matches)==1,name
                    return matches[0]
                def calls(fn):return [n for n in ast.walk(fn) if isinstance(n,ast.Call)]
                direct=module('native_driver.py')
                entry=function(direct,'submit_player_pilgrimage_planner_private_v1')
                assert all(ast.unparse(n.func).split('.')[-1] not in ('execute_step','_record_command') for n in calls(entry))
                pilgrimage=module('player_pilgrimage_planner_private_transport.py')
                for name in ('submit_player_pilgrimage_planner_private_v1','_request'):
                    fn=function(pilgrimage,name);names=[ast.unparse(n.func) for n in calls(fn)]
                    assert not any(x.split('.')[-1] in ('execute_step','_record_command') for x in names),names
                assert 'driver.endpoint.send' in [ast.unparse(n.func) for n in calls(function(pilgrimage,'_request'))]
                modal=function(module('death_succession_modal_private_transport.py'),'continue_death_succession_modal_private_v1')
                assert all(ast.unparse(n.func).split('.')[-1]!='_record_command' for n in calls(modal))
                advances=[n for n in calls(modal) if ast.unparse(n.func)=='driver.execute_step']
                assert len(advances)==1 and ast.literal_eval(advances[0].args[0])=='life-advance'
                assert 'driver.endpoint.send' in [ast.unparse(n.func) for n in calls(modal)]
                formal=module('faction_gift_formal_route_v1.py');constants={}
                for item in formal.body:
                    if isinstance(item,ast.Assign) and isinstance(item.value,ast.Constant):
                        for key in item.targets:
                            if isinstance(key,ast.Name):constants[key.id]=item.value.value
                rows=[]
                for name,symbol in [('submit_faction_gift_private_v1','SUBMIT_STEP'),('query_faction_gift_receipt_private_v1','RECEIPT_STEP')]:
                    fn=function(formal,name);recorders=[n for n in calls(fn) if ast.unparse(n.func)=='driver._record_command']
                    assert len(recorders)==1
                    row=recorders[0];kw={k.arg:k.value for k in row.keywords}
                    assert ast.unparse(row.args[0])==symbol and ast.literal_eval(kw['ok']) is True
                    assert ast.unparse(kw['result'])=='projected'
                    rows.append(constants[symbol])
                assert rows==['private-submit-faction-gift-member-v1','private-query-faction-gift-receipt-v1']
                print(json.dumps({'gift_rows':rows,'pilgrimage_own_rows':0,'close_own_rows':0,'separate_life_step':'life-advance'}))
                """;
        Process child=new ProcessBuilder(python,"-c",oracle,repository).redirectErrorStream(true).start();
        try {
            if(!child.waitFor(30,TimeUnit.SECONDS)){child.destroyForcibly();fail("original recording policy oracle timed out");}
            byte[] output=child.getInputStream().readNBytes(8193);assertTrue(output.length<=8192);
            assertEquals(0,child.exitValue(),new String(output,StandardCharsets.UTF_8));
            var result=StrictJson.parse(output);assertEquals(2,result.get("gift_rows").size());
            assertEquals(0,result.get("pilgrimage_own_rows").intValue());assertEquals(0,result.get("close_own_rows").intValue());
            assertEquals("life-advance",result.get("separate_life_step").textValue());
        }finally{child.destroyForcibly();for(var source:List.of(driver,planner,close,gift))SharedSourceFiles.assertUnchanged(source);}
    }

    /** Mandatory callback after a real installed Root Gift action/publication; it never creates an action or a domain. */
    public static void assertActualGiftPublication(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootRuntimeContext context,RootInstalledCatalog catalog,Session same,ActionReceipt actual)throws Exception {
        context.writer().requireSession(same);assertSame(context,catalog.context());assertEquals(OrdinaryFinancePolicies.GIFT,actual.command().operation());
        var archive=context.archive().withSession(same);var materials=prepared.install(context,catalog).materials();
        var pair=assertInstanceOf(GiftLegacyPair.class,materials.capture(same,actual,archive));
        assertEquals(org.xar.ck3.control.application.effects.NativeEffectEvidence.archivedReads(actual,archive).stream().map(archive::readReferenceOf).toList(),
                pair.evidence().stream().filter(e->e.kind()==EvidenceKind.READ).map(Evidence::reference).toList());
        String head=same.head().digest();materials.requireOriginal(same,actual,pair,archive);assertEquals(head,same.head().digest());
        var owning=GiftActionHistoryEvidence.verify(same,actual,pair.originals(),archive,context.frameLoader(),context.finance().definitions());
        assertEquals(archive.materialReferenceOf(owning.submitResult()),pair.submitResult());assertEquals(archive.materialReferenceOf(owning.receiptResult()),pair.receiptResult());
        assertEquals(PublicNumbers.fromResults(owning.submitResult(),owning.submitPublic()),pair.submitNumbers());
        assertEquals(PublicNumbers.fromResults(owning.receiptResult(),owning.receiptPublic()),pair.receiptNumbers());
        var source=source(same,actual,archive,pair);var rows=DriverActionHistoryCodec.legacyRows(1,actual,source,archive);
        assertEquals(2,rows.size());assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(DriverActionHistoryCodec.GIFT_SUBMIT_OPERATION),rows.getFirst().get("command"));
        assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Text(DriverActionHistoryCodec.GIFT_RECEIPT_OPERATION),rows.get(1).get("command"));
        for(var row:rows){assertEquals(new org.xar.ck3.control.planning.opportunity.OpportunityJson.Bool(true),row.get("ok"));DriverActionHistoryCodec.verifyLegacy(same,actual,row,archive);}
        assertEquals(DriverJson.object(owning.submitResult().bytes(),RawJson.MAXIMUM_BYTES),rows.getFirst().get("result"));
        assertEquals(DriverJson.object(owning.receiptResult().bytes(),RawJson.MAXIMUM_BYTES),rows.get(1).get("result"));
        DriverActionHistoryCodec.requireCanonicalMembership(same,actual,source,archive);
        assertEquals(pair.submitNumbers(),DriverActionHistoryCodec.giftPublicNumbers(rows.getFirst()).orElseThrow());
        assertEquals(pair.receiptNumbers(),DriverActionHistoryCodec.giftPublicNumbers(rows.get(1)).orElseThrow());
    }

    /** Same actual R1 runtime, merged installation, action/replay and original independent read; no legacy row. */
    public static void assertActualPilgrimagePublication(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootRuntimeContext context,RootInstalledCatalog catalog,Session same,ActionReceipt actual)throws Exception {
        var runtime=catalog.additionalDomains().religion().service().component(RootReligionPilgrimage.Runtime.class).orElseThrow();
        runtime.requireContext(context);assertTrue(runtime.matchesControl(actual.command()));
        assertSame(runtime.actionBinding().effect(),catalog.bindings().actualActionBinding(actual.command().operation()).orElseThrow());
        assertSame(runtime.archivedBinding(),catalog.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow());
        assertCanonicalOnly(prepared,context,catalog,same,actual);
    }

    /** Same private Pending child and Timeline verifier; the separate actual Life action keeps its original recording. */
    public static void assertActualClosePublication(RootActionHistoryMaterialSourceFactory.Prepared prepared,
            RootRuntimeContext context,RootInstalledCatalog catalog,Session same,ActionReceipt actual)throws Exception {
        var lifecycle=catalog.remainingDomains().lifecycle();lifecycle.requireContext(context);var timeline=lifecycle.natural().timeline();
        assertEquals("continue-death-succession-modal-v1",actual.command().operation().value());
        assertSame(timeline.actionBinding().effect(),catalog.bindings().actualActionBinding(actual.command().operation()).orElseThrow());
        assertSame(timeline.replayBinding(),catalog.bindings().actualArchivedVerifier(actual.command().operation()).orElseThrow());
        assertInstanceOf(ActionState.ControlApplied.class,assertInstanceOf(ActionState.Settled.class,actual.state()).settlement());
        assertCanonicalOnly(prepared,context,catalog,same,actual);
    }
    private static void assertCanonicalOnly(RootActionHistoryMaterialSourceFactory.Prepared prepared,RootRuntimeContext context,
            RootInstalledCatalog catalog,Session same,ActionReceipt actual)throws Exception {
        context.writer().requireSession(same);assertSame(context,catalog.context());var archive=context.archive().withSession(same);
        var materials=prepared.install(context,catalog).materials();var only=assertInstanceOf(CanonicalOnly.class,materials.capture(same,actual,archive));
        assertEquals(CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,only.reason());
        assertTrue(only.evidence().stream().anyMatch(e->e.kind()==EvidenceKind.READ));materials.requireOriginal(same,actual,only,archive);
        var source=source(same,actual,archive,only);DriverActionHistoryCodec.requireCanonicalMembership(same,actual,source,archive);
        assertThrows(IllegalArgumentException.class,()->DriverActionHistoryCodec.legacyRows(1,actual,source,archive));
        assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());
    }
    private static Source source(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive archive,OriginalMaterial material)throws Exception {
        var record=ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
        var source=DriverActionHistoryCodec.source(actual,record,archive.receiptReferenceOf(actual),material);
        assertEquals(source,DriverActionHistoryCodec.decode(DriverActionHistoryCodec.encode(source)));
        DriverActionHistoryCodec.requireSource(actual,source,archive);return source;
    }
    private static ExactRef exact(FileRef source){return new ExactRef(source.path().replace((char)92,'/'),source.bytes(),source.sha256());}
    private static String required(String property){String value=System.getProperty(property);assertNotNull(value,"NOT_RUN_REQUIRED_ACTUAL_DOMAIN_HISTORY: "+property);assertFalse(value.isBlank());return value;}
}

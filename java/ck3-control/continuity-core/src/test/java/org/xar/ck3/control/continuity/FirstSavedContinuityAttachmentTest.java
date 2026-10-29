package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.continuity.SavedContinuityAttachment.FirstBasis;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Pure producer/codec/reducer checks. Synthetic metadata grants no first-SAVE, physical restore or Game authority. */
final class FirstSavedContinuityAttachmentTest {
    private static final String MACHINE="first-restore-software-fixture";
    private static final BigInteger ABOVE_SAFE=new BigInteger("9007199254740993"),U64_MAX=new BigInteger("18446744073709551615");
    private record Fixture(ContinuityState active,EpisodeWindow.CommittedBaseline baseline,FirstBasis basis,
                           SavedContinuityAttachment.Input input,GameGeneration replacement){ }
    private static ExactRef ref(String name,long bytes,char digest){return new ExactRef("/fixture-only/"+name,bytes,String.valueOf(digest).repeat(64));}
    private static GameGeneration game(long pid,String birth){ObjectNode value=StrictJson.object();value.put("pid",pid);value.put("creation_filetime",birth);return GameGeneration.fromJson(value);}
    private static Pin pin(ExactRef ref,String id){return new Pin(ref,new FileIdentity("1",id,"133000000000000001","2026-10-24T00:00:00Z",ref.bytes()));}
    private static EpisodeWindow.Identity identity(GameGeneration game,String session,String episode,long epoch,long actor,long date){return new EpisodeWindow.Identity(MACHINE,game,session,episode,epoch,actor,date);}
    private static ContinuityState commitProjection(ContinuityState reduced,long sequence,String identity){ObjectNode row=reduced.toJson();row.put("sequence",sequence);row.put("last_event_identity",identity);return ContinuityState.fromJson(row,MACHINE);}
    private static Fixture fixture(){
        ObjectNode seed=StrictJson.object();seed.put("schema","root.ck3.continuity-window/v1");seed.put("machine_id",MACHINE);seed.put("sequence",1);
        seed.put("window_id",1);seed.put("status","running");seed.put("target_days",10958);seed.put("start_date_raw",1000);seed.put("target_date_raw",1000+10958*24);
        seed.put("last_settled_cycles",4);seed.put("last_settled_date_raw",1000);seed.putObject("game_binding").put("pid",123).put("creation_date","2026-10-24T00:00:00Z");
        seed.putObject("pending_cycle").put("stage","auto_unsettled").put("sequence",5);seed.putNull("unknown_actions");seed.putObject("unknown_requests").put("request","UNKNOWN");seed.put("NEXT",6);
        ContinuityState old=ContinuityState.fromJson(seed,MACHINE);GameGeneration before=game(123,"133000000000000001"),opened=game(456,"133000000000000002"),restored=game(789,"133000000000000003");
        EpisodeWindow.Begin begin=new EpisodeWindow.Begin("fixture-BEGIN",identity(before,"old-session","old-episode",0,42,1000),identity(opened,"opened-session","opened-episode",1,43,500),
                1,2,"fixture-parent",1,"1".repeat(64),ref("lifecycle.json",1,'1'),ref("adopted-driver.json",1,'2'),List.of());
        ContinuityState waiting=commitProjection(EpisodeWindow.reduce(old,begin.request()),2,begin.request().identity());
        var committedBegin=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),ContinuityJson.digest(waiting.toJson()),pin(ref("begin-event.json",1,'3'),"9007199254740993"));
        EpisodeWindow.Baseline baseline=new EpisodeWindow.Baseline(committedBegin,"actual-first-save",ref("pair.json",1,'4'),"4".repeat(64),ref("first-save-receipt.json",1,'5'),"a".repeat(64),begin.after());
        ContinuityState active=commitProjection(EpisodeWindow.reduce(waiting,baseline.request()),3,baseline.request().identity());
        var committedBaseline=new EpisodeWindow.CommittedBaseline(baseline,3,baseline.request().identity(),ContinuityJson.digest(active.toJson()),pin(ref("baseline-event.json",1,'6'),"9007199254740994"));
        FirstBasis basis=new FirstBasis(MACHINE,active.origin(),new FirstBasis.Frame("first-saved-snapshot",ABOVE_SAFE,U64_MAX,500,43,"opened-episode"),committedBaseline,
                ref("driver.json",11,'7'),new FileStatIdentity(BigInteger.valueOf(11),"9007199254740995","1792800000000000001"),
                ref("save.ck3",13,'8'),new FileStatIdentity(BigInteger.valueOf(13),"9007199254740996","1792800000000000002"),
                baseline.canonicalSaveReceiptRef(),baseline.pairRef(),ref("baselined-first-material.json",1,'9'),baseline.proofDigest(),"campaign-fixture",2);
        ObjectNode details=StrictJson.object();details.put("evidence_id","actual-first-restore");details.put("source","explicit-first-material");
        details.put("new_ordinary_cycle_credit",0);details.put("game_day_credit",0);details.put("original_actions_replayed",false);details.put("window_origin_reset",false);
        ObjectNode opening=StrictJson.object();opening.put("machine_id",MACHINE);opening.set("game",restored.toJson());opening.put("session_id","restored-session");
        opening.put("episode_run_id","opened-episode");opening.put("actor_character_id",43);opening.put("date_raw",500);opening.put("snapshot_id","restored-raw-snapshot");opening.put("native_revision",U64_MAX.toString());
        ObjectNode progress=StrictJson.object();progress.put("ledger_cycles",0);progress.put("ledger_date_raw",500);
        var input=new SavedContinuityAttachment.Input(active,ContinuityJson.canonical(details),ContinuityJson.canonical(basis.toJson()),ContinuityJson.canonical(restored.toJson()),ContinuityJson.canonical(opening),ContinuityJson.canonical(progress));
        return new Fixture(active,committedBaseline,basis,input,restored);
    }
    private static SavedContinuityAttachment.Input with(Fixture f,ContinuityState before,ObjectNode details,ObjectNode basis,ObjectNode game,ObjectNode opening){
        ObjectNode progress=StrictJson.object();progress.put("ledger_cycles",before.settledCycles());progress.put("ledger_date_raw",before.settledDateRaw());
        return new SavedContinuityAttachment.Input(before,ContinuityJson.canonical(details),ContinuityJson.canonical(basis),ContinuityJson.canonical(game),ContinuityJson.canonical(opening),ContinuityJson.canonical(progress));
    }
    private static ObjectNode object(byte[] raw){return ContinuityJson.parseObject(raw,ContinuityJson.DOCUMENT_MAX_BYTES);}
    private static byte[] external(SavedContinuityAttachment.Input input,String schema){
        ObjectNode row=StrictJson.object();row.put("schema",schema);row.set("previous",input.predecessor().toJson());row.set("expected_predecessor",input.predecessor().toJson());
        row.set("details",object(input.details()));row.set("expected_details",object(input.details()));row.set("basis",object(input.basis()));row.set("game",object(input.game()));row.set("opening",object(input.opening()));row.set("progress",object(input.progress()));return ContinuityJson.canonical(row);
    }
    @Test void typedFirstProducerAndFullUInt64RevisionRoundTripExactly(){
        Fixture f=fixture();FirstBasis restored=FirstBasis.fromJson(f.basis().toJson());assertEquals(f.basis(),restored);
        assertEquals(ABOVE_SAFE,restored.frame().revision());assertEquals(U64_MAX,restored.frame().nativeRevision());
        assertEquals("18446744073709551615",restored.toJson().path("frame").path("native_revision").textValue());
        assertEquals("9007199254740996",restored.toJson().path("save_identity").path("file_id").textValue());
        assertFalse(restored.toJson().path("refs").has("settled_full_response"));
    }
    @Test void firstFrameRejectsNumbersBooleansFloatsOverflowLeadingZeroAndMissing(){
        Fixture f=fixture();for(String token:List.of("true","1.0","9007199254740993","null","\"01\"","\"18446744073709551616\"")){
            ObjectNode frame=f.basis().frame().toJson();frame.set("revision",StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class,()->FirstBasis.Frame.fromJson(frame));
        }
        ObjectNode missing=f.basis().frame().toJson();missing.remove("native_revision");assertThrows(ContractViolationException.class,()->FirstBasis.Frame.fromJson(missing));
        ObjectNode alias=f.basis().toJson();((ObjectNode)alias.get("refs")).set("settled_full_response",f.basis().firstSaveReceiptRef().toJson());
        assertThrows(ContractViolationException.class,()->FirstBasis.fromJson(alias));
    }
    @Test void firstRestorationPreservesActualOriginUnknownAndBaselineAndUsesTheCanonicalSaveSource(){
        Fixture f=fixture();ContinuityState after=SavedContinuityAttachment.reduce(f.input());assertEquals(f.active().origin(),after.origin());assertEquals(0,after.settledCycles());
        for(String field:List.of(EpisodeWindow.FIELD,"pending_cycle","unknown_actions","unknown_requests","NEXT"))assertEquals(f.active().toJson().get(field),after.toJson().get(field));
        assertEquals(f.replacement().toJson(),after.toJson().get("game_binding"));assertEquals(f.basis().firstSaveReceiptRef().toJson(),after.toJson().get("last_settled_source"));
        assertEquals(0,after.toJson().path("current_saved_reconciliation").path("game_day_credit").longValue());
        assertFalse(after.toJson().path("last_current_saved_cold").path("original_actions_replayed").booleanValue());
    }
    @Test void explicitWireVersionCannotBeAliasedToTheOldOrdinaryRequest(){
        Fixture f=fixture();assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.decode(external(f.input(),SavedContinuityAttachment.REQUEST_SCHEMA)));
        var decoded=SavedContinuityAttachment.decode(external(f.input(),SavedContinuityAttachment.FIRST_REQUEST_SCHEMA));
        assertEquals(SavedContinuityAttachment.reduce(f.input()).toJson(),SavedContinuityAttachment.reduce(decoded).toJson());
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.decode(external(f.input(),"xar.java-saved-continuity-reduce-request/v999")));
    }
    @Test void anOlderFirstFrontierCannotEraseProgressThroughTheOrdinaryRestoreReducer(){
        Fixture f=fixture();ObjectNode progressed=f.active().toJson();progressed.put("last_settled_cycles",1);progressed.put("last_settled_date_raw",524);
        ContinuityState before=ContinuityState.fromJson(progressed,MACHINE);
        var request=with(f,before,object(f.input().details()),f.basis().toJson(),object(f.input().game()),object(f.input().opening()));
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(request));
        assertEquals(1,before.settledCycles());assertEquals(f.active().toJson().get("pending_cycle"),before.toJson().get("pending_cycle"));
    }
    @Test void changedFirstPairReceiptCheckpointAndTypedOriginalWindowAreRejected(){
        Fixture f=fixture();ObjectNode wrong=f.basis().toJson();((ObjectNode)wrong.get("refs")).set("first_pair",ref("another-pair.json",1,'b').toJson());
        assertThrows(ContractViolationException.class,()->FirstBasis.fromJson(wrong));
        ObjectNode changed=f.basis().toJson();((ObjectNode)changed.get("checkpoint")).put("history_index",99);assertThrows(ContractViolationException.class,()->FirstBasis.fromJson(changed));
        ObjectNode origin=f.basis().toJson();((ObjectNode)origin.get("origin")).put("window_id",3);assertThrows(ContractViolationException.class,()->FirstBasis.fromJson(origin));
    }
    @Test void sameGameWrongEpisodeOrClaimedCreditCannotAcquireFirstRestoreState(){
        Fixture f=fixture();ObjectNode originalGame=f.baseline().baseline().savedIdentity().game().toJson();
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(with(f,f.active(),object(f.input().details()),f.basis().toJson(),originalGame,object(f.input().opening()))));
        ObjectNode wrongEpisode=object(f.input().opening());wrongEpisode.put("episode_run_id","other-episode");
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(with(f,f.active(),object(f.input().details()),f.basis().toJson(),object(f.input().game()),wrongEpisode)));
        ObjectNode credit=object(f.input().details());credit.put("new_ordinary_cycle_credit",1);
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(with(f,f.active(),credit,f.basis().toJson(),object(f.input().game()),object(f.input().opening()))));
        ObjectNode numeric=object(f.input().opening());numeric.put("native_revision",U64_MAX);
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(with(f,f.active(),object(f.input().details()),f.basis().toJson(),object(f.input().game()),numeric)));
        ObjectNode missing=object(f.input().opening());missing.remove("snapshot_id");
        assertThrows(ContractViolationException.class,()->SavedContinuityAttachment.reduce(with(f,f.active(),object(f.input().details()),f.basis().toJson(),object(f.input().game()),missing)));
    }
    @Test void nextBeginAfterFirstPhysicalAttachmentUsesCurrentGameWithoutRewritingItsOriginalOpening(){
        Fixture f=fixture();ContinuityState restored=commitProjection(SavedContinuityAttachment.reduce(f.input()),4,"c".repeat(64));
        EpisodeWindow.Identity before=identity(f.replacement(),"restored-session","opened-episode",2,43,500);
        EpisodeWindow.Identity next=identity(game(999,"133000000000000004"),"next-session","next-episode",3,44,300);
        EpisodeWindow.Begin begin=new EpisodeWindow.Begin("after-real-restoration",before,next,2,3,"next-parent",4,"d".repeat(64),ref("new-lifecycle.json",1,'d'),ref("new-adopted.json",1,'e'),List.of());
        ContinuityState waiting=EpisodeWindow.reduce(restored,begin.request());assertEquals(ContinuityState.Status.AWAITING_FIRST_SAVE,waiting.status());
        assertEquals(f.active().origin(),waiting.origin());assertEquals(f.baseline().baseline().begin().begin().after().game(),EpisodeWindow.requireActive(restored).begin().after().game());
        assertEquals(f.replacement(),begin.before().game());assertEquals(f.active().toJson().get("unknown_requests"),waiting.toJson().get("unknown_requests"));
    }
}

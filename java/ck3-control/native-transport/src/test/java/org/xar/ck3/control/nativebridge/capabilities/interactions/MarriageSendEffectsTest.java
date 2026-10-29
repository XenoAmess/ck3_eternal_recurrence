package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyOutgoingCodec.Roles;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyOutgoingCodec.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.FamilyMarriageSendReads.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Source-shaped software values exercise the sole wire codec and actual effect comparison; no runtime qualification. */
final class MarriageSendEffectsTest {
    private static final long HASH=0xF1234567L;
    private static final Roles ROLES=new Roles(7L,17L,8L,9L,null);
    private static final List<OptionRow> BANK=List.of(new OptionRow(0,0xF0000001L,1),new OptionRow(1,0xF0000001L,0),new OptionRow(2,0x80000000L,1));
    private static final Prepared PREPARED=new Prepared(HASH,ROLES,BANK,true,true,false,Optional.of(true));
    private static Frame frame(int revision,int sequence){return new Frame(BigInteger.valueOf(revision),BigInteger.valueOf(100),BigInteger.valueOf(7),Build.CROZIER4,BigInteger.valueOf(sequence));}
    private static Candidate candidate(long id,Roles roles,List<OptionRow> rows,int route){return new Candidate(id,HASH,roles,route,0,30,rows);}
    private static Snapshot snapshot(boolean before,List<Long> occupied,List<Candidate> candidates){
        return new Snapshot(frame(before?9:10,before?20:21),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(7),occupied,candidates,Optional.empty());
    }
    private static Snapshot wire(Snapshot actual){
        var encoded=FamilyOutgoingCodec.encodeGroup(actual);
        return FamilyOutgoingCodec.decodeGroup(StrictJson.parse(StrictJson.canonical(encoded)),actual.frame(),actual.profile());
    }
    @Test void completeSourceWireBeforeAbsenceAndLaterUniqueExactBankLinksOnlyOutgoingSend(){
        var before=wire(snapshot(true,List.of(),List.of()));var after=wire(snapshot(false,List.of(0L),List.of(candidate(0,ROLES,BANK,0))));
        assertEquals(OptionalLong.of(0),MarriageSendEffects.match(PREPARED,before,after));
        assertEquals(after,wire(after));assertEquals(BANK,after.candidates().getFirst().options());
        assertEquals(0xF0000001L,after.candidates().getFirst().options().getFirst().flag());
        assertEquals(0,after.candidates().getFirst().pendingFullId());
    }
    @Test void afterUniqueIsNotEnoughWhenBeforeIncompleteOrContainsSameMaterial(){
        var after=wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,BANK,2))));
        var unavailable=new Snapshot(frame(9,20),Profile.ARRANGE_MARRIAGE,false,OptionalLong.empty(),OptionalInt.empty(),OptionalLong.empty(),List.of(),List.of(),Optional.of("unknown occupied vtable"));
        assertTrue(MarriageSendEffects.match(PREPARED,wire(unavailable),after).isEmpty());
        assertTrue(MarriageSendEffects.match(PREPARED,wire(snapshot(true,List.of(1L),List.of(candidate(1,ROLES,BANK,0)))),after).isEmpty());
    }
    @Test void preexistingOccupiedIdCannotBecomeNewByChangingItsDefinitionOrInactiveState(){
        var before=wire(snapshot(true,List.of(1L),List.of()));
        var after=wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,BANK,0))));
        assertTrue(MarriageSendEffects.match(PREPARED,before,after).isEmpty());
        var existingInactive=wire(snapshot(true,List.of(1L),List.of(candidate(1,ROLES,BANK,99))));
        assertTrue(MarriageSendEffects.match(PREPARED,existingInactive,after).isEmpty());
    }
    @Test void allFiveRolesAndEveryRawAuthoredRowMustMatch(){
        var before=wire(snapshot(true,List.of(),List.of()));
        List<Roles> wrong=List.of(new Roles(7L,18L,8L,9L,null),new Roles(7L,17L,18L,9L,null),
                new Roles(7L,17L,8L,19L,null),new Roles(7L,17L,8L,9L,20L));
        for(var roles:wrong)assertTrue(MarriageSendEffects.match(PREPARED,before,wire(snapshot(false,List.of(1L),List.of(candidate(1,roles,BANK,0))))).isEmpty());
        var changed=List.of(new OptionRow(0,0xF0000001L,0),BANK.get(1),BANK.get(2));
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,changed,0))))).isEmpty());
        var collapsed=List.of(BANK.getFirst(),new OptionRow(1,0x80000000L,1));
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,collapsed,0))))).isEmpty());
    }
    @Test void ambiguityUnknownRouteRegressedFrameAndOtherDefinitionDoNotProveSend(){
        var before=wire(snapshot(true,List.of(),List.of()));
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(snapshot(false,List.of(1L,2L),List.of(candidate(1,ROLES,BANK,0),candidate(2,ROLES,BANK,2))))).isEmpty());
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,BANK,3))))).isEmpty());
        var sameFrame=new Snapshot(frame(9,21),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(7),List.of(1L),List.of(candidate(1,ROLES,BANK,0)),Optional.empty());
        assertEquals(OptionalLong.of(1),MarriageSendEffects.match(PREPARED,before,wire(sameFrame)),
                "same SEM may carry an independent later complete query; custody is required separately by the real typed observer");
        var regressed=new Snapshot(frame(8,21),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(7),List.of(1L),List.of(candidate(1,ROLES,BANK,0)),Optional.empty());
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(regressed)).isEmpty());
        var reusedQuery=new Snapshot(frame(9,20),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(7),List.of(1L),List.of(candidate(1,ROLES,BANK,0)),Optional.empty());
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(reusedQuery)).isEmpty());
        var otherDay=new Snapshot(new Frame(BigInteger.TEN,BigInteger.valueOf(101),BigInteger.valueOf(7),Build.CROZIER4,BigInteger.valueOf(21)),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(7),List.of(1L),List.of(candidate(1,ROLES,BANK,0)),Optional.empty());
        assertTrue(MarriageSendEffects.match(PREPARED,before,wire(otherDay)).isEmpty());
        var notSendable=new Prepared(HASH,ROLES,BANK,false,true,false,Optional.of(true));
        assertTrue(MarriageSendEffects.match(notSendable,before,wire(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,BANK,0))))).isEmpty());
    }
    @Test void actualRulerRedirectRetainsPlayedFrameAndIndependentMaterializedSender(){
        var roles=new Roles(31L,17L,18L,19L,20L);var prepared=new Prepared(HASH,roles,BANK,true,false,false,Optional.empty());
        var before=new Snapshot(frame(9,20),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(31),List.of(),List.of(),Optional.empty());
        var after=new Snapshot(frame(10,21),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(31),List.of(1L),List.of(candidate(1,roles,BANK,0)),Optional.empty());
        assertEquals(BigInteger.valueOf(7),wire(before).frame().actor());assertEquals(OptionalLong.of(31),wire(after).senderCharacterId());
        assertEquals(OptionalLong.of(1),MarriageSendEffects.match(prepared,wire(before),wire(after)));
        var nullableRoles=new Roles(31L,null,18L,null,null);
        var nullableAfter=new Snapshot(frame(10,21),Profile.ARRANGE_MARRIAGE,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(31),List.of(1L),List.of(candidate(1,nullableRoles,BANK,0)),Optional.empty());
        assertEquals(nullableRoles,wire(nullableAfter).candidates().getFirst().roles());
        assertEquals(OptionalLong.of(1),MarriageSendEffects.match(new Prepared(HASH,nullableRoles,BANK,true,false,false,Optional.empty()),wire(before),wire(nullableAfter)));
        assertThrows(IllegalArgumentException.class,()->new Snapshot(frame(9,20),Profile.EDUCATE_CHILD,true,OptionalLong.of(HASH),OptionalInt.of(4),OptionalLong.of(31),List.of(),List.of(),Optional.empty()));
        var forged=FamilyOutgoingCodec.encodeGroup(after).put("sender_character_id",7);
        assertThrows(IllegalArgumentException.class,()->decodeGroup(forged,frame(10,21),Profile.ARRANGE_MARRIAGE));
    }
    @Test void sharedCodecRejectsPartialArraysWrongTypesAliasesAndUnbackedCandidate(){
        var valid=FamilyOutgoingCodec.encodeGroup(snapshot(false,List.of(1L),List.of(candidate(1,ROLES,BANK,0))));
        var wrongType=valid.deepCopy().put("complete",1);assertThrows(IllegalArgumentException.class,()->decodeGroup(wrongType,frame(10,21),Profile.ARRANGE_MARRIAGE));
        var alias=valid.deepCopy().put("guardian_outgoing_requests",true);assertThrows(IllegalArgumentException.class,()->decodeGroup(alias,frame(10,21),Profile.ARRANGE_MARRIAGE));
        var missing=valid.deepCopy();missing.remove("occupied_pending_full_ids");assertThrows(IllegalArgumentException.class,()->decodeGroup(missing,frame(10,21),Profile.ARRANGE_MARRIAGE));
        var unbacked=valid.deepCopy();unbacked.putArray("occupied_pending_full_ids");assertThrows(IllegalArgumentException.class,()->decodeGroup(unbacked,frame(10,21),Profile.ARRANGE_MARRIAGE));
        var sixth=FamilyOutgoingCodec.encodeRoles(ROLES).put("sixth_role_id",0);assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.roles(sixth));
        var wrongBank=FamilyOutgoingCodec.encodeOptions(BANK);((com.fasterxml.jackson.databind.node.ObjectNode)wrongBank.get(0)).put("bank_value_u8",true);
        assertThrows(IllegalArgumentException.class,()->FamilyOutgoingCodec.options(wrongBank));
    }
    @Test void firstHeirSelectedOptionAndFulfillmentEffectiveLinealityAreIndependentNativeFields(){
        var selectedOnEffectiveOff=new Prepared(HASH,ROLES,BANK,true,true,false,Optional.of(false));
        var selectedOffEffectiveOn=new Prepared(HASH,ROLES,BANK,true,false,false,Optional.of(true));
        var heir=new Sender(Route.FIRST_HEIR,7,8,9,OptionalLong.of(17),false,false);
        assertTrue(MarriageSendEffects.matrilinealMatches(heir,true,selectedOnEffectiveOff));
        assertTrue(MarriageSendEffects.matrilinealMatches(heir,false,selectedOffEffectiveOn));
        assertFalse(MarriageSendEffects.matrilinealMatches(heir,true,selectedOffEffectiveOn));
        assertFalse(MarriageSendEffects.matrilinealMatches(heir,false,selectedOnEffectiveOff));
        var fulfill=new Sender(Route.FULFILL_BETROTHAL,7,8,9,OptionalLong.of(17),false,false);
        assertTrue(MarriageSendEffects.matrilinealMatches(fulfill,true,selectedOffEffectiveOn));
        assertTrue(MarriageSendEffects.matrilinealMatches(fulfill,false,selectedOnEffectiveOff));
        assertFalse(MarriageSendEffects.matrilinealMatches(fulfill,true,selectedOnEffectiveOff));
        assertFalse(MarriageSendEffects.matrilinealMatches(fulfill,false,selectedOffEffectiveOn));
        assertFalse(MarriageSendEffects.matrilinealMatches(fulfill,true,new Prepared(HASH,ROLES,BANK,true,true,false,Optional.empty())));
        var on=new Sender(Route.CHILD_MATRILINEAL,7,8,9,OptionalLong.of(17),true,false);
        var off=new Sender(Route.CHILD_DEFAULT,7,8,9,OptionalLong.of(17),false,true);
        var bothOff=new Prepared(HASH,ROLES,BANK,true,false,false,Optional.of(false));
        assertTrue(MarriageSendEffects.matrilinealMatches(on,true,PREPARED));
        assertFalse(MarriageSendEffects.matrilinealMatches(on,true,selectedOnEffectiveOff));
        assertFalse(MarriageSendEffects.matrilinealMatches(on,false,selectedOffEffectiveOn));
        assertTrue(MarriageSendEffects.matrilinealMatches(off,false,bothOff));
        assertFalse(MarriageSendEffects.matrilinealMatches(off,false,selectedOffEffectiveOn));
        assertFalse(MarriageSendEffects.matrilinealMatches(off,true,selectedOnEffectiveOff));
        var ruler=new Sender(Route.RULER,7,7,9,OptionalLong.empty(),false,false);
        assertTrue(MarriageSendEffects.matrilinealMatches(ruler,false,new Prepared(HASH,ROLES,BANK,true,true,false,Optional.empty())),"public ruler consumes actual native builder defaults without a private option setter");
    }
}


package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;

/** Regression for the real complete-scan matcher; no ACK fixture is promoted to an effect. */
final class GuardianOutgoingEffectsTest {
    private static Frame frame(int revision,int sequence) { return new Frame(BigInteger.valueOf(revision),BigInteger.valueOf(100),BigInteger.valueOf(19),Build.CROZIER4,BigInteger.valueOf(sequence)); }
    private static OrdinaryContext prepared(Long sixth) {
        var request=new OrdinaryRequest(new InteractionKey("educate_child_interaction"),new CharacterId(2),Optional.of(new EducationIntent(Optional.of(new CharacterId(2)),Optional.of(new CharacterId(3)),Optional.of(List.of(new InteractionKey("selected_option"))))));
        var roles=new Roles(19L,2L,3L,2L,null,sixth);
        var rows=new EducationOptions(new Availability(true,null),List.of(new EducationOption(0,7,"selected_option",true,1,true),new EducationOption(1,7,"selected_option",true,0,false)));
        var terms=new OrdinaryTerms(true,true,8,2,1,false,true,true,java.util.Collections.nCopies(10,BigInteger.ZERO),false,BigInteger.ZERO,BigInteger.ZERO,0);
        return new OrdinaryContext(frame(10,1),request,new Availability(true,null),new OrdinaryProofs(true,true,true,true,true,true,21,BigInteger.ONE),roles,terms,true,true,false,false,true,null,
                Optional.of(rows),Optional.of(new EducationMaterialization(new Availability(true,null),2L,3L,List.of("selected_option"),true,true)));
    }
    private static FamilyOutgoingCodec.Candidate candidate(long id,int route) {
        return new FamilyOutgoingCodec.Candidate(id,8,new FamilyOutgoingCodec.Roles(19L,2L,3L,2L,null),route,0,3,List.of(new FamilyOutgoingCodec.OptionRow(0,7,1),new FamilyOutgoingCodec.OptionRow(1,7,0)));
    }
    private static FamilyOutgoingCodec.Snapshot scan(int revision,int sequence,List<FamilyOutgoingCodec.Candidate> rows) {
        return new FamilyOutgoingCodec.Snapshot(frame(revision,sequence),FamilyOutgoingCodec.Profile.EDUCATE_CHILD,true,OptionalLong.of(8),OptionalInt.of(100),OptionalLong.of(19),rows.stream().map(FamilyOutgoingCodec.Candidate::pendingFullId).toList(),rows,Optional.empty());
    }
    @Test void exactNewNativeFullIdRequiresAllFiveRolesAndEveryRawAuthoredBankByte() {
        long full=0x81000001L;
        assertEquals(OptionalLong.of(full),GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(11,3,List.of(candidate(full,2)))));
        var wrongRoles=new FamilyOutgoingCodec.Candidate(full,8,new FamilyOutgoingCodec.Roles(19L,2L,4L,2L,null),2,0,3,candidate(full,2).options());
        assertTrue(GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(11,3,List.of(wrongRoles))).isEmpty());
        // Duplicate flags keep two independent raw bank bytes; matching only selected names would wrongly pass.
        var wrongBank=new FamilyOutgoingCodec.Candidate(full,8,candidate(full,2).roles(),2,0,3,List.of(new FamilyOutgoingCodec.OptionRow(0,7,1),new FamilyOutgoingCodec.OptionRow(1,7,1)));
        assertTrue(GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(11,3,List.of(wrongBank))).isEmpty());
    }
    @Test void absenceAutoAcceptanceAmbiguityAndUnknownRoutingStayUnresolved() {
        var before=scan(10,1,List.of());
        for(var after:List.of(scan(11,3,List.of()),scan(11,3,List.of(candidate(1,2),candidate(2,0))),scan(11,3,List.of(candidate(1,9)))))
            assertTrue(GuardianOutgoingEffects.match(prepared(null),before,after).isEmpty());
        var incomplete=new FamilyOutgoingCodec.Snapshot(frame(11,3),FamilyOutgoingCodec.Profile.EDUCATE_CHILD,false,OptionalLong.empty(),OptionalInt.empty(),OptionalLong.empty(),List.of(),List.of(),Optional.of("native_storage_changed_during_scan"));
        assertTrue(GuardianOutgoingEffects.match(prepared(null),before,incomplete).isEmpty());
        assertTrue(GuardianOutgoingEffects.match(prepared(9L),before,scan(11,3,List.of(candidate(1,2)))).isEmpty(),"pending storage has no qualified sixth-role read");
    }
    @Test void existingRequestReusedQueryOrRegressedNativeFrameCannotCreateSendData() {
        var row=candidate(1,2);
        assertTrue(GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of(row)),scan(11,3,List.of(row))).isEmpty());
        var other=new FamilyOutgoingCodec.Candidate(1,8,new FamilyOutgoingCodec.Roles(19L,9L,3L,9L,null),2,0,3,row.options());
        assertTrue(GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of(other)),scan(11,3,List.of(row))).isEmpty());
        assertEquals(OptionalLong.of(1),GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(10,3,List.of(row))),
                "same SEM is admissible as send DATA only; actual query custody and writer replay still must qualify it");
        assertThrows(IllegalArgumentException.class,()->GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(9,3,List.of(row))));
        assertThrows(IllegalArgumentException.class,()->GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(10,1,List.of(row))));
        assertThrows(IllegalArgumentException.class,()->GuardianOutgoingEffects.match(prepared(null),scan(10,2,List.of()),scan(11,3,List.of(row))));
    }
    @Test void completeStorageOccupancyRejectsAnIdPreviouslyOwnedByAnotherDefinition() {
        var occupied=new FamilyOutgoingCodec.Snapshot(frame(10,1),FamilyOutgoingCodec.Profile.EDUCATE_CHILD,true,
                OptionalLong.of(8),OptionalInt.of(100),OptionalLong.of(19),List.of(0L),List.of(),Optional.empty());
        assertTrue(GuardianOutgoingEffects.match(prepared(null),occupied,scan(11,3,List.of(candidate(0,2)))).isEmpty());
        assertEquals(OptionalLong.of(0),GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),scan(11,3,List.of(candidate(0,2)))));
        var wrongProfile=new FamilyOutgoingCodec.Snapshot(frame(11,3),FamilyOutgoingCodec.Profile.ARRANGE_MARRIAGE,true,
                OptionalLong.of(8),OptionalInt.of(100),OptionalLong.of(19),List.of(1L),List.of(candidate(1,2)),Optional.empty());
        assertTrue(GuardianOutgoingEffects.match(prepared(null),scan(10,1,List.of()),wrongProfile).isEmpty());
    }
}

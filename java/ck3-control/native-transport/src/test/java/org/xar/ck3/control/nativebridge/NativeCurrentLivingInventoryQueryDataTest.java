package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Draft typed DATA only: NOT_COMPILED/NOT_RUN, no Cpp frames/private Received or action authority. */
final class NativeCurrentLivingInventoryQueryDataTest {
    private static List<CurrentLivingInventoryQuerySource.Reference> references(){
        var refs=new ArrayList<CurrentLivingInventoryQuerySource.Reference>();
        for(var role:CurrentLivingInventoryQuerySource.ReferenceRole.values()){
            boolean material=role==CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_MATERIAL_COMMON;
            refs.add(new CurrentLivingInventoryQuerySource.Reference(role,material?CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT:CurrentLivingInventoryQuerySource.ReferenceState.ABSENT,
                    material?36:0,material?Optional.of(7L):Optional.empty()));
        }return refs;
    }
    private static CurrentLivingInventoryQuerySource.Numeric numeric(long raw){return new CurrentLivingInventoryQuerySource.Numeric(CurrentLivingInventoryQuerySource.NumericState.NUMERIC,1,Optional.of(raw));}
    private static List<CurrentLivingInventoryQuerySource.Numeric> values(){return List.of(numeric(Long.MIN_VALUE),numeric(-1),numeric(0),numeric(Long.MAX_VALUE));}
    private static CurrentLivingInventoryQuerySource source(long actor,List<CurrentLivingInventoryQuerySource.Artifact> artifacts,List<CurrentLivingInventoryQuerySource.Slot> slots,Optional<Integer> weapon){
        return new CurrentLivingInventoryQuerySource(actor,artifacts,slots,weapon,references(),true,true);
    }
    private static CurrentLivingInventoryQueryResult result(CurrentLivingInventoryQuerySource source,int signedActor){
        var core=new CoreFrame.Prefix(-24,3,true,0,true,true,signedActor,true);
        var owner=new CurrentLetterResult.OwnerWitness(BigInteger.ONE,BigInteger.TWO,BigInteger.TEN,7);
        return new CurrentLivingInventoryQueryResult(CurrentLivingInventoryQueryResult.Status.AVAILABLE,true,BigInteger.ONE,BigInteger.TWO,Optional.of(core),Optional.of(owner),Optional.of(source),Optional.empty());
    }
    @Test void consumedMaterialReferenceAndUnsignedActorRemainReadonlyData() throws IOException {
        for(int signed:List.of(0,-2)){
            var data=source(Integer.toUnsignedLong(signed),List.of(),List.of(),Optional.empty());
            assertEquals(Optional.of(7L),data.fixedReferences().get(1).artifactFullId());
            assertTrue(data.artifacts().isEmpty());
            var frame=result(data,signed);assertEquals(frame,CurrentLivingInventoryQueryResult.decode(frame.encode()));
            assertEquals(BigInteger.ZERO,frame.claimSequence());assertFalse(frame.effectAttempted());assertFalse(frame.nativeReturned());assertFalse(frame.nativeHandled());
        }
        assertThrows(IllegalArgumentException.class,()->result(source(0,List.of(),List.of(),Optional.empty()),-2));
    }
    @Test void fixedStatesAndSigned64TextStayDistinctAndCanonical() throws IOException {
        var artifact=new CurrentLivingInventoryQuerySource.Artifact(0,0,"",Integer.MIN_VALUE,false,values());
        var data=source(0,List.of(artifact),List.of(),Optional.empty());
        assertEquals(data,CurrentLivingInventoryQuerySource.decode(data.encode()));
        for(String bad:List.of("01","-0","+0","9223372036854775808","1.0")){
            var json=data.encode();((com.fasterxml.jackson.databind.node.ObjectNode)json.path("artifacts").get(0).path("numeric").get(0)).put("raw",bad);
            assertThrows(IOException.class,()->CurrentLivingInventoryQuerySource.decode(json));
        }
        var absent=new CurrentLivingInventoryQuerySource.Numeric(CurrentLivingInventoryQuerySource.NumericState.ABSENT,0,Optional.empty());
        var empty=new CurrentLivingInventoryQuerySource.Numeric(CurrentLivingInventoryQuerySource.NumericState.PRESENT_EMPTY,0,Optional.empty());
        assertNotEquals(absent,empty);
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingInventoryQuerySource.Reference(CurrentLivingInventoryQuerySource.ReferenceRole.FIXTURE_TARGET,
                CurrentLivingInventoryQuerySource.ReferenceState.ARTIFACT,36,Optional.of(0xffff_ffffL)));
    }
    @Test void actualReadTextAndPhysicalSlotsDoNotAcquireWriteRules() throws IOException {
        for(String text:List.of("","a\u0000b\n","\uD83D\uDE00".repeat(1024))){
            var artifact=new CurrentLivingInventoryQuerySource.Artifact(0,0,text,-2,true,values());
            var slots=List.of(new CurrentLivingInventoryQuerySource.Slot("weapon",Optional.of(0L)),new CurrentLivingInventoryQuerySource.Slot("secondary",Optional.of(0L)));
            var data=source(0,List.of(artifact),slots,Optional.of(0));
            assertEquals(data,CurrentLivingInventoryQuerySource.decode(data.encode()));
            assertThrows(IllegalArgumentException.class,()->source(0,List.of(artifact),slots,Optional.of(1)));
        }
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingInventoryQuerySource.Artifact(0,0,"x".repeat(4097),0,false,values()));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingInventoryQuerySource.Artifact(0,0,"\uD800",0,false,values()));
        assertThrows(IllegalArgumentException.class,()->source(0,List.of(),List.of(new CurrentLivingInventoryQuerySource.Slot("weapon",Optional.of(1L))),Optional.of(0)));
    }
    @Test void exactSchemasAndUnknownRemainSourceNullRatherThanEmptyInventory() throws IOException {
        var available=result(source(0,List.of(),List.of(),Optional.empty()),0);
        var json=NativeWire.object(NativeWire.parse(available.encode().bytes()));json.put("claim_sequence","1");
        assertThrows(IOException.class,()->CurrentLivingInventoryQueryResult.decode(new RawJson(StrictJson.canonical(json))));
        var source=available.source().orElseThrow().encode();source.put("raw_pointer",1);
        assertThrows(IOException.class,()->CurrentLivingInventoryQuerySource.decode(source));
        var unknown=new CurrentLivingInventoryQueryResult(CurrentLivingInventoryQueryResult.Status.INDETERMINATE,false,BigInteger.ZERO,BigInteger.ZERO,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("actual_source_unknown"));
        assertFalse(unknown.sourceAvailable());assertEquals(unknown,CurrentLivingInventoryQueryResult.decode(unknown.encode()));
        assertThrows(IllegalArgumentException.class,()->new CurrentLivingInventoryQueryResult(CurrentLivingInventoryQueryResult.Status.UNAVAILABLE,true,BigInteger.ZERO,BigInteger.ZERO,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.of("")));
    }
}

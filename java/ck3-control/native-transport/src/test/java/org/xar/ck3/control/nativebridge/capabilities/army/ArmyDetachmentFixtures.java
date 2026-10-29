package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.List;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentDataInputs.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyDetachmentInputsCodec.*;

/** Declared synthetic operands cover source branches; they do not represent a native observation. */
final class ArmyDetachmentFixtures {
    private ArmyDetachmentFixtures() { }
    static State state() { return new State(Status.AVAILABLE,true,null); }
    static Resolution resolution(long requested,String identity) { return new Resolution(state(),requested,true,16777216L,requested&0xFFFFFFL,identity,requested,Selection.REGISTRY_FULL_ID,false,identity,requested); }
    static MapperInputs mapper() {
        CountInput count=new CountInput(state(),0,"regi:51",Integer.MAX_VALUE,List.of(new CountChunk(0,7,10,null),new CountChunk(1,0,null,null),new CountChunk(2,0,null,null),new CountChunk(3,0,null,null),new CountChunk(4,0,null,null),new CountChunk(5,0,null,null),new CountChunk(6,0,null,null)));
        MapperInput first=new MapperInput(state(),0,"arrg:41",1,1,"DATA:41:0",51L,resolution(51,"regi:51"),0x52656769L,true,0,true,ObservedReturn.SELECTED_REGI,null,"regi:51",null,null,4);
        MapperInput fallback=new MapperInput(state(),1,"arrg:42",9,null,null,null,null,null,null,null,true,ObservedReturn.NATIVE_FALLBACK,"regi:fallback","regi:fallback",null,null,2);
        return new MapperInputs(state(),true,SeedSelection.FIRST_VALID_CURRENT_RECEIVER,1,2,2147483649L,2147483649L,"army:high",3,true,"Army:roster",true,
            List.of(new MapperOccurrence(state(),0,41L,resolution(41,"arrg:41"),0),new MapperOccurrence(state(),1,41L,resolution(41,"arrg:41"),0),new MapperOccurrence(state(),2,42L,resolution(42,"arrg:42"),1)),List.of(first,fallback),List.of(count));
    }
    static CallbackInputs callback() {
        KnownCallbacks known=new KnownCallbacks("native:200","native:201","native:202","native:300","native:203");
        CallbackIncoming absent=new CallbackIncoming(state(),List.of(0,2,5),"native:41",41L,"native:200","native:201",false,null,null,null,null,null,null,List.of());
        CallbackIncoming present=new CallbackIncoming(state(),List.of(1,3),"native:42",42L,"native:200","native:201",true,"native:400",2,4,"native:500","native:501","native:502",
            List.of(new CallbackRecord(state(),0,"native:600","native:601","native:300"),new CallbackRecord(state(),1,"native:608","native:601","native:300")));
        return new CallbackInputs(state(),true,true,Long.MIN_VALUE,0,known,List.of(absent,present));
    }
    static StoreInputs store() {
        List<SlotScan> scan=List.of(new SlotScan(state(),0,"native:1000",false,null));
        StoreRequest admitted=new StoreRequest(state(),List.of(0,2),"native:41",2147483649L,1L,"native:1010",true,"native:41",2147483649L,"native:200","native:201",scan);
        StoreRequest duplicate=new StoreRequest(state(),List.of(3),"native:41",2147483649L,1L,"native:1010",true,"native:41",2147483649L,"native:200","native:201",scan);
        StoreRequest absent=new StoreRequest(state(),List.of(1),"native:42",2L,2L,"native:1020",false,null,null,null,null,scan);
        StoreRequest mismatch=new StoreRequest(state(),List.of(4),"native:43",0L,0L,"native:1000",true,"native:43",3L,"native:200","native:201",scan);
        StoreRequest outside=new StoreRequest(state(),List.of(5),"native:44",5L,5L,null,null,null,null,null,null,List.of());
        return new StoreInputs(state(),true,true,Long.MAX_VALUE,"native:90",0,"native:91",0,3L,"native:1000",0L,null,3L,4294967295L,List.of(admitted,duplicate,absent,mismatch,outside));
    }
    static CharacterInputs character() {
        CharacterRequest invalid=new CharacterRequest(state(),0,"native:41",4294967295L,resolution(1,"native:71"),"native:800",null,null,null,null,false,false,resolution(41,"native:41"),51L,resolution(51,"native:51"),61L,resolution(61,"native:61"));
        CharacterRequest absent=new CharacterRequest(state(),1,"native:42",72L,resolution(72,"native:72"),"native:800",false,null,null,null,false,true,resolution(42,"native:42"),52L,resolution(52,"native:52"),62L,resolution(62,"native:62"));
        CharacterRequest reset=new CharacterRequest(state(),2,"native:43",73L,resolution(73,"native:73"),"native:801",true,"native:900",null,null,false,false,resolution(43,"native:43"),53L,resolution(53,"native:53"),63L,resolution(63,"native:63"));
        return new CharacterInputs(state(),true,true,Long.MIN_VALUE,"native:90",List.of(invalid,absent,reset));
    }
    static ArmyDetachmentDataInputs data() {
        Pending pending=new Pending(state(),"native:1000","native:1100",3,1,"native:1200",List.of(new PendingRecord(state(),0,"native:1100","native:1300","native:1400",51L,0)));
        DataOccurrence occurrence=new DataOccurrence(state(),0,"native:2000",51L,0,"native:50",resolution(51,"native:51"),0x52656769L,true,true,0);
        PhysicalChunk chunk=new PhysicalChunk(state(),0,"native:3000",3,2,51L,0,41L,0,Long.MIN_VALUE);
        Association association=new Association(state(),41L,resolution(41,"native:41"),61L,resolution(61,"native:61"),71L,resolution(71,"native:71"),81L,resolution(81,"native:81"),"native:4000",1L);
        Owner owner=new Owner(state(),51L,resolution(51,"native:51"),4,"native:5000",0x52656769L,"native:6000",0x50726F76L);
        DateInput date=new DateInput(state(),41L,51L,"native:71","native:6000",0x50726F76L,"native:6001",0x50726F76L,Long.MAX_VALUE,"observed_date_callee_output");
        Incoming incoming=new Incoming(state(),0,"native:41",41L,61L,71L,resolution(61,"native:61"),resolution(71,"native:71"),"native:800","native:2000",1,"native:2000","native:2016",true,81L,resolution(81,"native:81"),true,"native:900",List.of(occurrence),List.of(chunk),List.of(association),List.of(owner),List.of(date),pending);
        return new ArmyDetachmentDataInputs(state(),true,true,Long.MIN_VALUE,"native:40","native:1300","native:1400",List.of(new Candidate(state(),0,41L,resolution(41,"native:41"),0x41725267L,true,0)),List.of(incoming));
    }
    enum Family { MAPPER,CALLBACK,STORE,CHARACTER,DATA }
    static JsonNode json(Family family) { return switch(family) { case MAPPER->encodeMapper(mapper());case CALLBACK->encodeCallback(callback());case STORE->encodeStore(store());case CHARACTER->encodeCharacter(character());case DATA->encodeData(data()); }; }
}

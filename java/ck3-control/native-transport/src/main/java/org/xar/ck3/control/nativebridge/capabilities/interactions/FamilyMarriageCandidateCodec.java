package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Sole full native family enumeration row, shared by actual title-heir and specified-child reads. */
public final class FamilyMarriageCandidateCodec {
    private FamilyMarriageCandidateCodec() { }
    public static HeirMarriageCandidate decodeCompleteCandidate(JsonNode row,Context context,int actualSubject){
        need(actualSubject>0,"candidate row requires its actual selected subject");
        closed(row,"played_character_id","subject_character_id","candidate_character_id","recipient_matchmaker_character_id",
                "intermediary_character_id","native_rank","complete_can_send","recipient_ai_accept_raw",
                "recipient_answer_status_raw","recipient_answer_allows_send","heir_adult_measure_raw","candidate_adult_measure_raw",
                "played_dynasty_id","heir_dynasty_id","candidate_dynasty_id","realm_backed_actor_recipient");
        eq(row,"played_character_id",context.actor());eq(row,"subject_character_id",BigInteger.valueOf(actualSubject));nil(row,"native_rank");yes(row,"complete_can_send");
        CharacterId character=new CharacterId(integer(row,"candidate_character_id",1,Integer.MAX_VALUE));CharacterId recipient=new CharacterId(integer(row,"recipient_matchmaker_character_id",1,Integer.MAX_VALUE));
        int intermediary=integer(row,"intermediary_character_id",-1,Integer.MAX_VALUE),answer=integer(row,"recipient_answer_status_raw",0,2);boolean allowed=bool(row,"recipient_answer_allows_send");need(allowed==(answer!=2),"actual native answer0/1/2 admission differs");
        return new HeirMarriageCandidate(character,recipient,intermediary,allowed,number(row,"recipient_ai_accept_raw",I64_MIN,I64_MAX),answer,small(row,"heir_adult_measure_raw"),small(row,"candidate_adult_measure_raw"),dynasty(row,"played_dynasty_id"),dynasty(row,"heir_dynasty_id"),dynasty(row,"candidate_dynasty_id"),nullableBool(row,"realm_backed_actor_recipient"));
    }
    static Short small(JsonNode n,String name){return field(n,name).isNull()?null:(short)integer(n,name,Short.MIN_VALUE,Short.MAX_VALUE);}
    static BigInteger dynasty(JsonNode n,String name){return nullableNumber(n,name,BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MAX_VALUE));}
}

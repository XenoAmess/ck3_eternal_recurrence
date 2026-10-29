package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.Role.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentExtrasCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;

/** Existing original gateway callback boundaries only; not a currency/payment attribution. */
public final class WarPaymentResource4Codec {
    private WarPaymentResource4Codec() { }
    static final String KEY="resource4_wallet_context_v1";
    static final long ENTRY=0x28b9950;
    static void validate(Check c,JsonNode v,JsonNode record){
        c.fields(v,g(U32,"schema_version"),g(Role.U64,"source_entry_rva"),g(TEXT,"resource_name maintenance_attribution balance_boundary"),g(NEST,"before after"));
        need(is(v,"schema_version",1)&&is(v,"source_entry_rva",ENTRY)&&v.get("resource_name").textValue().equals("unknown")&&v.get("maintenance_attribution").textValue().equals("unclosed")&&v.get("balance_boundary").textValue().equals("whole_original_callback_entry_return"),"resource4 source/attribution");
        need(is(record,"kind",1)&&is(record,"resource_kind_raw",4),"resource4 different original callback");
        WarPaymentRaw4Codec.physicalFrame(c,v.get("before"));WarPaymentRaw4Codec.physicalFrame(c,v.get("after"));
    }
    static ArrayNode qualified(JsonNode j){
        ArrayNode out=array();JsonNode s=j.get("sampling"),current=j.get("current_session");
        if(!(yes(j,"installed")&&is(j,"install_failure_flags",0)&&yes(j,"read_complete")&&is(j,"overwritten",0)&&is(j,"publication_failures",0)&&yes(s,"available")&&yes(s,"capture_enabled")&&!yes(s,"busy")&&is(s,"active_captures",0)))return out;
        for(JsonNode r:j.get("records")){
            if(!r.has(KEY)||r.get(KEY).isNull())continue;
            JsonNode v=r.get(KEY);validate(new Check(Direction.NATIVE),v,r);JsonNode a=v.get("before"),b=v.get("after"),x=r.get("before"),y=r.get("after");
            if(!(yes(r,"original_called")&&yes(r,"original_returned")&&!yes(r,"tls_depth_exceeded")&&before(r.get("entry_event"),r.get("returned_event"))&&sameSession(r.get("session_entry"),r.get("session_return"))&&sameSession(r.get("session_entry"),current)
                &&nz(r.get("receiver"))&&eq(r,"receiver",x,"character")&&eq(r,"receiver",y,"character")&&is(a,"failed_reads",0)&&is(b,"failed_reads",0)
                &&present(a,"character_full_id")&&!is(a,"character_full_id",0xffffffffL)&&eq(a,"character_full_id",b,"character_full_id")&&eq(a,"character_full_id",x,"character_id")&&eq(a,"character_full_id",y,"character_id")&&eq(a,"character_full_id",current,"player_character_full_id")
                &&is(a,"character_magic",0x43686172)&&is(b,"character_magic",0x43686172)&&is(x,"character_magic",0x43686172)&&is(y,"character_magic",0x43686172)
                &&nz(a.get("extension"))&&eq(a,"extension",b,"extension")&&eq(a,"extension",x,"character_extension")&&eq(a,"extension",y,"character_extension")
                &&nz(a.get("context"))&&eq(a,"context",b,"context")&&n(a,"context").compareTo(WarPaymentNodes.U64.subtract(BigInteger.valueOf(0x4a0)))<=0&&present(a,"physical_4a0_bits")&&present(b,"physical_4a0_bits")))continue;
            ObjectNode q=empty();q.set("journal_sequence",r.get("journal_sequence"));q.put("source_entry_rva",ENTRY);q.set("caller_return_rva",r.get("caller_return_rva"));q.put("resource_kind_raw",4);q.set("component_raw",r.get("component_raw"));
            q.set("character",r.get("receiver"));q.set("character_full_id",a.get("character_full_id"));q.set("context",a.get("context"));q.put("slot_address",n(a,"context").add(BigInteger.valueOf(0x4a0)));
            q.set("before_balance_bits",a.get("physical_4a0_bits"));q.set("after_balance_bits",b.get("physical_4a0_bits"));q.set("requested_amount_raw",r.get("amount_raw"));
            q.put("boundary_matches_requested_sub_mod64",n(b,"physical_4a0_bits").equals(n(a,"physical_4a0_bits").subtract(n(r,"amount_raw")).and(WarPaymentNodes.U64)));
            for(String key:java.util.List.of("entry_event","returned_event","session_entry","session_return"))q.set(key,r.get(key).deepCopy());
            q.put("balance_boundary","whole_original_callback_entry_return").put("resource_name","unknown");for(String key:java.util.List.of("military_paid_raw","payer","cadence","settlement_token"))q.putNull(key);out.add(q);
        }
        return out;
    }
}

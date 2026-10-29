package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentNodes.Role.*;
import static org.xar.ck3.control.application.planning.finance.WarPaymentExtrasCodec.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;

/** Exact optional raw selector4 child; an empty derived vector never proves absence. */
public final class WarPaymentRaw4Codec {
    private WarPaymentRaw4Codec() { }
    static final String KEY="raw_resource4_getter_v1";
    static final long ENTRY=0x28b9490,TEXT_BEGIN=0x1000,TEXT_END=0x43d9848;
    static void physicalFrame(Check c,JsonNode f){
        c.fields(f,g(OU32,"character_full_id character_magic"),g(OU64,"extension context physical_4a0_bits"),g(U32,"failed_reads"));
        int failed=0;for(String key:List.of("character_full_id","character_magic","extension"))if(!present(f,key))failed++;
        if(nz(f.get("extension"))){if(!present(f,"context"))failed++;if(nz(f.get("context"))&&!present(f,"physical_4a0_bits"))failed++;}
        need(is(f,"failed_reads",failed),"raw4 frame failure count");
        need((nz(f.get("extension"))||!present(f,"context"))&&((nz(f.get("extension"))&&nz(f.get("context")))||!present(f,"physical_4a0_bits")),"raw4 skipped branch value invented");
    }
    static void validate(Check c,JsonNode v,JsonNode outer){
        c.fields(v,g(U32,"schema_version"),g(Role.U64,"source_entry_rva latest_sequence oldest_sequence overwritten publication_failures"),g(TEXT,"capture_origin resource_name payment_attribution"),g(BOOL,"read_complete"),g(NEST,"records"));
        need(is(v,"schema_version",1)&&is(v,"source_entry_rva",ENTRY)&&v.get("capture_origin").textValue().equals("native_entry_detour")&&v.get("resource_name").textValue().equals("unknown")&&v.get("payment_attribution").textValue().equals("unclosed"),"raw4 source/attribution");
        ArrayNode rows=list(v.get("records"),128);BigInteger latest=n(v,"latest_sequence"),oldest=latest.signum()==0?BigInteger.ZERO:latest.subtract(BigInteger.valueOf(127)).max(BigInteger.ONE);
        need(n(v,"oldest_sequence").equals(oldest)&&n(v,"overwritten").equals(latest.subtract(BigInteger.valueOf(128)).max(BigInteger.ZERO)),"raw4 ring bounds");
        BigInteger previous=BigInteger.ZERO;
        for(JsonNode r:rows){
            c.fields(r,g(Role.U64,"journal_sequence character out_pointer caller_return_absolute module_base raw_return_bits"),g(I32,"raw_selector"),g(OU64,"caller_return_rva out64_bits"),g(U32,"output_failed_reads"),g(BOOL,"original_called original_returned"),g(NEST,"entry_event returned_event session_entry session_return natural_parent_metadata natural_return_metadata before after"));
            need(is(r,"raw_selector",4),"raw4 different selector");
            for(String k:List.of("entry_event","returned_event"))event(c,r.get(k));
            for(String k:List.of("session_entry","session_return"))session(c,r.get(k));
            for(String k:List.of("natural_parent_metadata","natural_return_metadata"))natural(c,r.get(k));
            physicalFrame(c,r.get("before"));physicalFrame(c,r.get("after"));
            BigInteger pc=n(r,"caller_return_absolute"),base=n(r,"module_base"),relative=pc.subtract(base);
            boolean known=base.signum()!=0&&pc.compareTo(base)>=0&&relative.compareTo(BigInteger.valueOf(TEXT_BEGIN))>=0&&relative.compareTo(BigInteger.valueOf(TEXT_END))<0;
            need(known?present(r,"caller_return_rva")&&n(r,"caller_return_rva").equals(relative):!present(r,"caller_return_rva"),"raw4 image provenance");
            need(is(r,"output_failed_reads",present(r,"out64_bits")?0:1),"raw4 output failure");
            BigInteger seq=n(r,"journal_sequence");need(seq.compareTo(previous)>0,"raw4 ordinals");previous=seq;
        }
        if(!rows.isEmpty())need(n(rows.get(0),"journal_sequence").compareTo(oldest)>=0&&previous.compareTo(latest)<=0,"raw4 retained bounds");
        if(yes(v,"read_complete")){
            need(BigInteger.valueOf(rows.size()).equals(latest.min(BigInteger.valueOf(128))),"raw4 complete ring count");
            for(int i=0;i<rows.size();i++)need(n(rows.get(i),"journal_sequence").equals(oldest.add(BigInteger.valueOf(i))),"raw4 missing ordinal");
        }else need(rows.isEmpty(),"raw4 unreadable partial records");
        need(!yes(outer.get("sampling"),"clear_completed")||latest.signum()==0,"raw4 survived clear");
    }
    static ArrayNode qualified(JsonNode j){
        ArrayNode out=array();if(!j.has(KEY))return out;
        JsonNode v=j.get(KEY);validate(new Check(Direction.NATIVE),v,j);JsonNode s=j.get("sampling");
        if(!(yes(j,"installed")&&is(j,"install_failure_flags",0)&&yes(j,"read_complete")&&yes(s,"available")&&yes(s,"capture_enabled")&&!yes(s,"busy")&&is(s,"active_captures",0)&&yes(v,"read_complete")&&is(v,"overwritten",0)&&is(v,"publication_failures",0)))return out;
        for(JsonNode r:v.get("records")){
            JsonNode a=r.get("before"),b=r.get("after"),current=j.get("current_session");
            if(!(yes(r,"original_called")&&yes(r,"original_returned")&&nz(r.get("out_pointer"))&&eq(r,"raw_return_bits",r,"out_pointer")&&is(r,"output_failed_reads",0)&&present(r,"out64_bits")&&present(r,"caller_return_rva")
                &&before(r.get("entry_event"),r.get("returned_event"))&&sameSession(r.get("session_entry"),r.get("session_return"))&&sameSession(r.get("session_entry"),current)
                &&eq(a,b)&&is(a,"failed_reads",0)&&present(a,"character_full_id")&&!is(a,"character_full_id",0xffffffffL)&&eq(a,"character_full_id",current,"player_character_full_id")&&is(a,"character_magic",0x43686172)&&nz(r.get("character"))))continue;
            boolean physical=nz(a.get("extension"))&&nz(a.get("context"));BigInteger expected=physical?n(a,"physical_4a0_bits"):BigInteger.ZERO;
            if(!n(r,"out64_bits").equals(expected))continue;
            BigInteger bits=n(r,"out64_bits");ObjectNode q=empty();q.set("journal_sequence",r.get("journal_sequence"));q.set("caller_return_rva",r.get("caller_return_rva"));q.set("character_full_id",a.get("character_full_id"));q.set("context",a.get("context"));q.set("out64_bits",r.get("out64_bits"));
            q.put("out64_signed",bits.compareTo(TWO63)<0?bits:bits.subtract(TWO64));q.put("read_branch",physical?"physical_context_4a0":"default_zero_missing_extension_or_context");out.add(q);
        }
        return out;
    }
}

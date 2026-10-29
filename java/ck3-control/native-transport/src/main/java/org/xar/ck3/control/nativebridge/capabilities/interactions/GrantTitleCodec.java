package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.RawJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Full generation-bearing title picker sets and independent native holder postconditions. */
public final class GrantTitleCodec {
    private GrantTitleCodec() { }
    public static String step(GrantOperation operation) { return operation.wire()+"-grant-title-picker-v1"; }
    public static String capability(GrantOperation operation) { return "game.command."+step(operation); }
    public static RawJson request(Context c,GrantRequest r) {
        need(c.controls().paused() && c.controls().mapReady(),"grant requires current paused map");
        ObjectNode n=common(c).put("recipient_character_full_id",r.recipient().value()).put("requested_title_full_ids",csv(r.targets())).put("expected_selected_title_full_ids",csv(r.expectedSelected()));
        r.title().ifPresent(t->n.put("title_full_id",t.value())); r.desiredSelected().ifPresent(v->n.put("desired_selected",v)); return encode(n);
    }
    public static GrantResult decode(RawJson raw,Context c,GrantRequest r) {
        JsonNode n=parse(raw); eq(n,"schema","ck3_12003_grant_title_picker_v1"); eq(n,"operation",r.operation().wire());
        build(n,"exact_build","executable_sha256",c); eq(n,"recipient_character_full_id",BigInteger.valueOf(r.recipient().value()));
        boolean owner=bool(n,"owner_thread_verified"),frame=bool(n,"frame_verified"),source=bool(n,"source_abi_pins_verified"),dispatch=bool(n,"dispatch_invoked"),completed=bool(n,"native_call_completed"),selection=bool(n,"selection_verified"),transfer=bool(n,"transfer_verified"); no(n,"business_full_credit");
        if(frame) {
            eq(n,"native_revision",c.revision()); eq(n,"connection_generation",c.connectionGeneration()); eq(n,"game_pid",BigInteger.valueOf(c.before().game().pid())); eq(n,"played_character_id",c.actor()); eq(n,"date_raw",c.date()); need(owner && source,"grant lacks actual owner/method qualification");
        }
        GrantWindow before=window(field(n,"before"),r.targets()),after=window(field(n,"after"),r.targets());
        if(r.operation()==GrantOperation.QUERY) need(!dispatch && !completed && !selection && !transfer,"readonly grant query claimed mutation");
        if(transfer) {
            need(r.operation()==GrantOperation.SEND && !r.expectedSelected().isEmpty() && dispatch && completed && frame
                    && new HashSet<>(r.targets()).equals(new HashSet<>(r.expectedSelected())) && before.complete() && before.bound() && after.available()
                    && Boolean.TRUE.equals(before.canSend()) && Boolean.FALSE.equals(before.warning()) && new HashSet<>(before.selected()).equals(new HashSet<>(r.expectedSelected())),"transfer lacks complete actual native before state");
            need(before.holders().stream().allMatch(row->row.available() && Objects.equals(row.holder(),c.actor().longValueExact()))
                    && after.holders().stream().allMatch(row->row.available() && Objects.equals(row.holder(),r.recipient().value())),"transfer lacks complete native holder readback");
        }
        if(selection) {
            HashSet<FullId> desired=new HashSet<>(r.expectedSelected()); if(r.desiredSelected().orElse(false)) desired.add(r.title().orElseThrow()); else r.title().ifPresent(desired::remove);
            need(r.operation()==GrantOperation.SELECT && frame && before.complete() && after.complete()
                    && new HashSet<>(before.selected()).equals(new HashSet<>(r.expectedSelected())) && new HashSet<>(after.selected()).equals(desired),"selection proof differs from complete actual title sets");
        }
        GrantStatus status=enumeration(n,"status",GrantStatus.class); String reason=text(n,"unavailable_reason");
        need(status==GrantStatus.UNAVAILABLE || frame,"grant completion lacks current original frame");
        if(status==GrantStatus.PREPARED) need(r.operation()==GrantOperation.PREPARE && after.complete() && after.visible() && after.bound(),"prepared window not actually observed");
        if(status==GrantStatus.SELECTION_OBSERVED) need(selection,"selection status lacks exact native selection proof");
        need((status==GrantStatus.HOLDER_TRANSFER_OBSERVED)==transfer,"grant transfer status differs from actual readback");
        return new GrantResult(r.operation(),status,owner,frame,source,dispatch,completed,selection,transfer,before,after,reason);
    }
    private static GrantWindow window(JsonNode n,List<FullId> targets) {
        boolean available=bool(n,"available"),visible=bool(n,"window_visible"),bound=bool(n,"window_binding_verified"),complete=bool(n,"rows_complete");
        Boolean canSend=nullableBool(n,"native_can_send"),warning=nullableBool(n,"warning_confirmation_required");
        List<GrantRow> rows=list(n,"rows",2048,row->new GrantRow(new FullId(id(row,"title_full_id")),nullableId(row,"holder_character_full_id"),bool(row,"selected"),bool(row,"selectable")));
        unique(rows.stream().map(GrantRow::title).toList(),2048);
        List<FullId> selected=ids(n,"selected_title_full_ids",2048).stream().map(FullId::new).toList();
        need(selected.equals(rows.stream().filter(GrantRow::selected).map(GrantRow::title).toList()),"native selected set differs from complete row predicates");
        if(complete) need(available && visible && bound && canSend!=null && warning!=null,"complete rows lack actual window binding");
        List<GrantHolder> holders=list(n,"requested_title_holders",64,row->new GrantHolder(new FullId(id(row,"title_full_id")),bool(row,"available"),nullableId(row,"holder_character_full_id")));
        if(available) need(holders.stream().map(GrantHolder::title).toList().equals(targets),"native holder rows differ from ordered requested complete Title set");
        return new GrantWindow(available,visible,bound,complete,canSend,warning,rows,selected,holders);
    }
    /** A later query may inspect an UNKNOWN send; it never authorizes sending again. */
    public static boolean independentHolderTransfer(Context before,Context after,GrantRequest original,GrantResult observed) {
        if(original.operation()!=GrantOperation.SEND || observed.operation()!=GrantOperation.QUERY || !sameControl(before,after) || !observed.after().available()) return false;
        return observed.after().holders().stream().map(GrantHolder::title).toList().equals(original.targets())
            && observed.after().holders().stream().allMatch(row->row.available() && Objects.equals(row.holder(),original.recipient().value()));
    }
    public static boolean sameControl(Context before,Context after) {
        return before.before().machineId().equals(after.before().machineId()) && before.before().game().equals(after.before().game()) && before.sessionId().equals(after.sessionId())
            && before.connectionGeneration().equals(after.connectionGeneration()) && before.build()==after.build() && before.actor().equals(after.actor())
            && before.date().equals(after.date()) && before.controls().episodeRunId().equals(after.controls().episodeRunId()) && after.controls().paused() && after.controls().mapReady();
    }
}

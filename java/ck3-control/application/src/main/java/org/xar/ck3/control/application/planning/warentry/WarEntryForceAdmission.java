package org.xar.ck3.control.application.planning.warentry;

import static org.xar.ck3.control.application.planning.warentry.WarEntryJson.*;

import java.util.List;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.prewaradmission.OrdinaryPrewarAdmission;
import org.xar.ck3.control.wave2.military.prewaradmission.PrewarAdmissionCodec;

/** Explicit SDK-container projection into the existing complete force-risk production chain. */
public final class WarEntryForceAdmission {
    private static final String[] DECLARATION={"declaration_id","target_character_id","casus_belli_index","casus_belli_key","configuration_index","claimant_character_id","target_title_ids"};
    private WarEntryForceAdmission() { }
    public static Obj selectedDeclaration(Obj declaration) {return present(declaration,DECLARATION);}
    public static Obj assess(Obj snapshot,Obj declaration) {
        Obj projected=present(snapshot,"paused","map_ready","played_character","diagnostics","snapshot_id","revision","native_revision","date_raw","episode_run_id","capture_epoch","declarable_wars",PrewarAdmissionCodec.QUERY_KEY);
        Obj played=child(snapshot,"played_character");if(played!=null)projected=projected.with("played_character",present(played,"alive","character_id"));
        Obj diagnostics=child(snapshot,"diagnostics");if(diagnostics!=null) {
            Obj narrowed=present(diagnostics,"hello","connection_generation");Obj hello=child(diagnostics,"hello");
            if(hello!=null)narrowed=narrowed.with("hello",present(hello,"bridge_version","expected_ck3_version","expected_ck3_sha256"));
            projected=projected.with("diagnostics",narrowed);
        }
        if(snapshot.get("declarable_wars") instanceof Arr) {
            List<Value> declarations=array(snapshot.get("declarable_wars")).stream().map(value->value instanceof Obj row?(Value)selectedDeclaration(row):value).toList();
            projected=projected.with("declarable_wars",new Arr(declarations));
        }
        Obj query=child(snapshot,PrewarAdmissionCodec.QUERY_KEY);
        if(query!=null)projected=projected.with(PrewarAdmissionCodec.QUERY_KEY,present(query,"queried_snapshot_id","queried_revision","queried_native_revision","queried_date_raw","queried_actor_character_id","queried_connection_generation","queried_episode_run_id","accepted","status","execution_receipt","native_request_id",PrewarAdmissionCodec.DOMAIN_KEY));
        Obj envelope=obj().text("schema",PrewarAdmissionCodec.SCHEMA).value("snapshot",projected).value("declaration",selectedDeclaration(declaration)).build();
        var input=PrewarAdmissionCodec.decodeProjected(OpportunityJson.toNode(envelope));
        return parse(OrdinaryPrewarAdmission.encodeResult(OrdinaryPrewarAdmission.assess(input)));
    }
    private static Obj present(Obj source,String... fields) {Builder b=obj();if(source!=null)for(String field:fields)if(source.members().containsKey(field))b.value(field,source.get(field));return b.build();}
}

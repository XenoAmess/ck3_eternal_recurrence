package org.xar.ck3.control.wave2.events.registered;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.registered.RegistryJson.*;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

final class RegisteredGuiAvailabilityTest {
    private static final BigInteger PLAYER=BigInteger.valueOf(27181);
    private static ObjectValue option(boolean raw,boolean valid) {
        return b().set("rendered_index",0).set("native_option_index",0).set("shown",true).set("enabled",raw)
            .set("fallback",false).set("cancel",false).set("gui_availability",b().set("status","observed").set("is_valid",valid).build()).build();
    }
    private static ObjectValue context(ObjectValue row) {
        return b().set("schema","current-event-window-context-v2").set("schema_version",2).set("options",arr(row)).build();
    }
    @Test void registeredProjectionUsesGuiResultAndRetainsRawRow() {
        ObjectValue contract=b().set("option_count",1).set("native_option_indices",arr(v(0))).set("disabled_native_option_indices",arr())
            .set("snapshot_option_count",1).set("selected_native_option_index",0).set("selected_option_number",1).build();
        ObjectValue no=context(option(true,false));
        var blocked=RegisteredProjection.options(no,contract,BigInteger.ONE);
        assertFalse(blocked.checks().get("selected_native_option_enabled"));
        ObjectValue yes=context(option(false,true));
        var ready=RegisteredProjection.options(yes,contract,BigInteger.ONE);
        assertTrue(all(ready.checks()));assertEquals(v(false),ready.selected().get("enabled"));
    }
    @Test void fullRegisteredProducerBlocksFalseAndPersistsTrueObservation() throws Exception {
        var knowledge=RegisteredEventKnowledge.load();String build="1.19.0.6",key="tgp_travel_events.0030";
        ObjectValue contract=obj(materialize(knowledge.query(build,key).get("contract"),PLAYER));
        List<Value> rows=seq(contract.get("native_option_indices")).stream().map(index->(Value)b().set("rendered_index",integer(index)).set("native_option_index",index)
            .set("shown",true).set("enabled",true).set("fallback",false).set("cancel",false)
            .set("gui_availability",b().set("status","observed").set("is_valid",true).build()).build()).toList();
        List<Value> scopeNames=seq(seq(contract.get("saved_scope_name_sets")).getFirst());
        List<Value> scopes=scopeNames.stream().map(name->(Value)b().set("name",name).set("scope",b().set("status","available")
            .set("type_key",get(contract.get("scope_types"),str(name))).build()).build()).toList();
        ObjectValue base=b().set("schema","current-event-window-context-v2").set("schema_version",2).set("status","available").set("window_match_count",1)
            .set("event_definition_key",key).set("current_event_instance_id",9).set("snapshot_revision",19).set("date_raw",53284680)
            .set("root_scope",b().set("status","available").set("type_key","character").set("typed_identity",b().set("status","available").set("kind","character").set("character_id",PLAYER).build()).build())
            .set("saved_scopes",arr(scopes)).set("options",arr(rows)).build();
        var policy=new RegisteredVanillaEventPolicy(knowledge);
        var positive=policy.recommend(new RegisteredVanillaEventPolicy.Input(base,v(PLAYER),v(2),Optional.of(build),RetainedJson.NULL,RetainedJson.NULL,arr()));
        assertEquals(RegisteredVanillaEventPolicy.Status.RECOMMENDED,positive.status(),positive.wire().toString());
        assertEquals(b().set("status","observed").set("is_valid",true).build(),positive.wire().get("selected_gui_availability"));
        assertEquals(positive.wire(),RetainedJson.parse(RetainedJson.encode(positive.wire())));
        List<Value> negative=rows.stream().map(value->(Value)obj(value).with("gui_availability",b().set("status","observed").set("is_valid",false).build())).toList();
        var blocked=policy.recommend(new RegisteredVanillaEventPolicy.Input(base.with("options",arr(negative)),v(PLAYER),v(2),Optional.of(build),RetainedJson.NULL,RetainedJson.NULL,arr()));
        assertEquals(RegisteredVanillaEventPolicy.Status.BLOCKED,blocked.status());assertTrue(blocked.selection().isEmpty());
    }
}

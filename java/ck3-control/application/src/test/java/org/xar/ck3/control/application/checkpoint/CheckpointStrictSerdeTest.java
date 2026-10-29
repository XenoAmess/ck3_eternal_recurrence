package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

public class CheckpointStrictSerdeTest {
    private static final String DRIVER="{\"format_version\":2,\"pipe_name\":\"p\",\"bridge_pid\":1,\"episode_character_id\":29829,\"episode_run_id\":\"e\",\"last_checkpoint\":null,\"command_history\":[],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"campaign_goal\":null}";
    private static DriverStateSnapshot.Complete decode(String value){return DriverStateSnapshot.decodeComplete(value.getBytes(StandardCharsets.UTF_8));}
    @Test void booleanAndFloatingIntegerAliasesAreRejected(){
        assertThrows(Exception.class,()->decode(DRIVER.replace("\"format_version\":2","\"format_version\":true")));
        assertThrows(Exception.class,()->decode(DRIVER.replace("\"bridge_pid\":1","\"bridge_pid\":1.0")));
        assertThrows(Exception.class,()->decode(DRIVER.replace("\"episode_character_id\":29829","\"episode_character_id\":29829.0")));
    }
    @Test void missingNullAndEmptyCollectionRemainDistinct(){
        var missing=decode(DRIVER); assertInstanceOf(DriverStateSnapshot.Missing.class,missing.successionLifecycle());
        var nul=decode(DRIVER.replace("\"campaign_goal\":null","\"succession_lifecycle\":null,\"campaign_goal\":null"));
        assertInstanceOf(DriverStateSnapshot.NullValue.class,nul.successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.Missing.class,DriverStateSnapshot.decodeComplete(missing.encode()).successionLifecycle());
        assertInstanceOf(DriverStateSnapshot.NullValue.class,DriverStateSnapshot.decodeComplete(nul.encode()).successionLifecycle());
        assertThrows(Exception.class,()->decode(DRIVER.replace("\"campaign_goal\":null", "\"campaign_goal\":null,\"command_history\":null")));
    }
    @Test void unknownTopLevelFieldsRequireAnExplicitMigration(){assertThrows(Exception.class,()->decode(DRIVER.replace("\"format_version\":2","\"format_version\":2,\"future_field\":null")));}
    @Test void missingRequiredStateCannotBecomeACompleteSnapshot(){assertThrows(Exception.class,()->decode(DRIVER.replace("\"campaign_goal\":null", "\"rollback_war_failures\":[]")));}
    @Test void valueNullAndNonfiniteNumbersCannotSilentlyChangeBranches(){
        assertThrows(Exception.class,()->new DriverStateSnapshot.Value("null".getBytes(StandardCharsets.UTF_8)));
        assertThrows(Exception.class,()->new DriverStateSnapshot.Value(" ".getBytes(StandardCharsets.UTF_8)));
        assertThrows(Exception.class,()->decode(DRIVER.replace("\"campaign_goal\":null","\"campaign_goal\":{\"unknown_number\":1e400}")));
    }
}

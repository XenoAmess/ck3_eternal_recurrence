package org.xar.ck3.control.nativebridge.capabilities.interactions;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;

/** Exact old producer/consumer sources used by compatibility tests; no production Python dependency. */
final class FamilyRelationOriginalPins {
    private FamilyRelationOriginalPins() { }
    private record Pin(String relative,long bytes,String sha256) { }
    private static final List<Pin> SOURCES=List.of(
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_relationship_private_transport.py",29925L,"62695bddf2344cb824514c036306fa0ba2a0d07b7216b7a412ba322870cd338a"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_descendants_v1.py",29232L,"bfbfa8c6c1d6afbaa749d5852c2f0368ddced1f50ba8395052b6f2a2bfe4c410"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_first_heir_reproductive_inputs_v1.py",36187L,"aa183a475558d24f1e6b01981b6cae94bc87ae2778a04e617a74585f6184d36c"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/current_child_education_provider_inputs_v1.py",13616L,"7e0a3097918ccfdcf4ca661e1eba1839d96a0eda7cb68ca3e4ac4659df910c71"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/guardian_factory_create_inputs_contract_v1.py",37056L,"0d757dea4ca9091f3ef375bda120bdf9600f6bd385879d29152749b8a240ff10"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/family_generation_education_inputs_v1.py",7345L,"49472023f86b21385e1a256c9bedaa4ecba53c28557368bbb47d878fbe62aa58"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/family_generation_education_decision_v1.py",7000L,"6c9c49c593014dc3e2640dfdb792cd84adb0777257c9e93d24ebb56d9616994a"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/education_point_source_modifiers_12004.py",15185L,"b05409076308e306e8d95c5df4700b8ffc71e8b433008c26ba8cb2a9445c7eff"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/education_child_court_owner_readonly_12004.py",2249L,"df5520d233601f0302010c13a244467dc51ef2d202fabbae7ab735094bab68e7"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/conception_natural_observation_contract_12004.py",15900L,"289c093d162dff3b9ace58e2acbc896cbf22aeeae4846d4adf33b5e1c76e9e48"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/conception_natural_observation_12004.py",13439L,"7f475e5193004c456ec0853a0e5b4ef94d60dbc861d533626035f08b115bb1ad"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/conception_incoming_caller_sourcebinding_12004.py",17200L,"d87e11e86bbba475ffec0604692308d1b106962951cfa37cda012e30954f486f"),
        new Pin("ck3_autonomous_player/native_bridge/tests/fixtures/conception_pair_passive_12004_joined_journal.json",7150L,"69168452ff5a51706e1fb7b2a6156aaa43f77318bc57e3f5692f2c917836bf64"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py",2663L,"fe1a53ca0f01e60ae37231e3b1a566442454f3bb77afd33b616849b25f6d53e9"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py",2114L,"9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/marriage_matchmaking_private_transport.py",17426L,"08c4dff41aacfdd242d36db6c718c3db202da2b68145b5b3c002efdd9de4eee6"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/player_child_marriage_value_private_transport.py",9423L,"cc0e3b1c68ec71cbfa329543e927fe6337a008e3f4cf88f8a4f11a7f6e5ebfe8"));
    static String required(String property){String value=System.getProperty(property);assertNotNull(value,"required CI property: "+property);assertFalse(value.isBlank());return value;}
    static Path repository(){return Path.of(required("xar.repository.root"));}
    static void verify()throws Exception{for(Pin pin:SOURCES){byte[] bytes=Files.readAllBytes(repository().resolve(pin.relative()));assertEquals(pin.bytes(),bytes.length,pin.relative());assertEquals(pin.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)),pin.relative());}}
}


package org.xar.ck3.control.service.root;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.platform.NormalExitSourceInventory;
/** Actual temporary source files -> sole builder -> immutable input/consumer; no Managed proof is synthesized. */
final class NormalExitSourceInventoryTest{
    @TempDir Path temporary;
    record Fixture(Path user,Path game,Path mod,Path profile,Path inventory,Path snapshot){NormalExitSourceInventory.Input input()throws Exception{return new NormalExitSourceInventory.Input(ref(inventory),ref(profile),ref(snapshot));}}
    private static ExactRef ref(Path path)throws Exception{byte[] value=Files.readAllBytes(path);return new ExactRef(path.toRealPath().toString(),value.length,ActionCodec.sha256(value));}
    private Fixture fixture()throws Exception{
        Path user=Files.createDirectories(temporary.resolve("state/profile")),game=Files.createDirectories(temporary.resolve("install/game")),mod=Files.createDirectories(temporary.resolve("mod-root"));
        Path exe=Files.createDirectories(temporary.resolve("install/binaries")).resolve("ck3.exe");Files.writeString(exe,"controlled exact executable DATA");
        Files.writeString(user.resolve("pdx_settings.txt"),"original launch settings");Files.createDirectories(user.resolve("mod"));Files.writeString(user.resolve("mod/a.mod"),"path=\""+mod.toString().replace('\\','/')+"\"\n");Files.writeString(mod.resolve("descriptor.mod"),"name=\"source-only\"\n");Files.writeString(mod.resolve("content.txt"),"original mod bytes");
        var dlc=StrictJson.object();dlc.putArray("enabled_mods").add("mod/a.mod");Files.write(user.resolve("dlc_load.json"),StrictJson.canonical(dlc));
        for(String relative:List.of("gui/hud.gui","gui/frontend_ingame_menu.gui","gui/window_resign_confirmation.gui","gui/shared/buttons_icons.gui","gui/shared/buttons.gui","gui/shared/sounds.gui")){
            Path path=game.resolve(relative);Files.createDirectories(path.getParent());String root=relative.endsWith("hud.gui")?"timeline_widget":relative.endsWith("frontend_ingame_menu.gui")?"ingame_pausemenu":relative.endsWith("window_resign_confirmation.gui")?"ingame_resign_confirmation":null;
            Files.writeString(path,root==null?"# actual unrelated stock source DATA\n":"widget={name=\""+root+"\"}\n");}
        var guard=StrictJson.object().put("static_source_binding_only",true).put("launch_authority",false);guard.putObject("target").put("executable",exe.toString()).put("executable_sha256",ref(exe).sha256());
        Path guardPath=temporary.resolve("guard.json");Files.write(guardPath,StrictJson.canonical(guard));
        var profile=StrictJson.object().put("schema_version",1).put("guard_profile",guardPath.toString()).put("guard_profile_sha256",ref(guardPath).sha256()).put("userdir",user.toString())
                .put("evidence_directory",temporary.resolve("evidence").toString()).put("game_version","1.20.0.4").put("state_directory",temporary.resolve("state").toString());
        // All path roles are actual directories/files; static inspection does not grant their source/loaded ABI as a Game.
        Files.createDirectories(temporary.resolve("evidence"));
        for(String key:List.of("dll","injector")){Path file=temporary.resolve(key);Files.writeString(file,"controlled "+key);profile.set(key,StrictJson.object().put("path",file.toString()).put("sha256",ref(file).sha256()));}
        Path original=temporary.resolve("original-managed-profile.json");Files.write(original,StrictJson.canonical(profile));
        var built=NormalExitSourceInventory.build(new RawJson(Files.readAllBytes(original)),game);Path inventory=user.resolve(NormalExitSourceInventory.BASENAME);Files.write(inventory,built.inventory().bytes());
        Files.write(user.resolve(NormalExitSourceInventory.PROJECTION_BASENAME),built.profileProjection().bytes());
        Files.write(original,NormalExitSourceInventory.withInventory(new RawJson(Files.readAllBytes(original)),ref(inventory)).bytes());
        Path snapshot=temporary.resolve("original-settings-snapshot.txt");Files.write(snapshot,Files.readAllBytes(user.resolve("pdx_settings.txt")));return new Fixture(user,game,mod,original,inventory,snapshot);
    }
    @Test void actualBuilderToStrictConsumerRoundTripsAndSeparatesMutableOutputFromOriginal()throws Exception{
        var fixture=fixture();
        // Actual builder output must survive its consumer beyond the small receipt lane.
        for(int index=0;index<320;index++)Files.writeString(fixture.mod().resolve(String.format(java.util.Locale.ROOT,"%03d-",index)+"x".repeat(96)+".txt"),"bounded source DATA");
        var built=NormalExitSourceInventory.build(new RawJson(Files.readAllBytes(fixture.profile())),fixture.game());
        assertTrue(built.inventory().bytes().length>StrictJson.INPUT_MAX_BYTES);assertTrue(built.inventory().bytes().length<=4<<20);
        Files.write(fixture.inventory(),built.inventory().bytes());Files.write(fixture.user().resolve(NormalExitSourceInventory.PROJECTION_BASENAME),built.profileProjection().bytes());
        Files.write(fixture.profile(),NormalExitSourceInventory.withInventory(new RawJson(Files.readAllBytes(fixture.profile())),ref(fixture.inventory())).bytes());
        var input=fixture.input();assertFalse(StrictJson.parse(Files.readAllBytes(fixture.profile())).has("guard"));NormalExitSourceInventory.inspect(input);var original=Files.readAllBytes(fixture.snapshot());Files.writeString(fixture.user().resolve("pdx_settings.txt"),"actual changed game-owned output");
        NormalExitSourceInventory.inspect(input);assertArrayEquals(original,Files.readAllBytes(fixture.snapshot()));assertNotEquals(Files.readString(fixture.snapshot()),Files.readString(fixture.user().resolve("pdx_settings.txt")));
    }
    @Test void finalProfileReopensActualGuardAndRejectsForgedEmbeddedTarget()throws Exception{
        var fixture=fixture();var profile=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(Files.readAllBytes(fixture.profile()));profile.putObject("guard").putObject("target").put("executable","forged");
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.build(new RawJson(StrictJson.canonical(profile)),fixture.game()));
        Files.writeString(temporary.resolve("guard.json"),"{}");assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.inspect(fixture.input()));
    }
    @Test void nativeFixedProjectionIsRequiredAndCannotBeSubstitutedByEquivalentNoncanonicalJson()throws Exception{
        var fixture=fixture();var input=fixture.input();Path projection=fixture.user().resolve(NormalExitSourceInventory.PROJECTION_BASENAME);byte[] original=Files.readAllBytes(projection);
        Files.write(projection,(new String(original,java.nio.charset.StandardCharsets.UTF_8)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.inspect(input));
        Files.delete(projection);assertThrows(java.io.IOException.class,()->NormalExitSourceInventory.inspect(input));
    }
    @Test void versionedV2GuardCannotFallBackToTheUnversionedLegacyTarget()throws Exception{
            var fixture=fixture();var guard=StrictJson.object().put("schema","xar.java.normal-exit-static-target-binding/v2").put("static_source_binding_only",true).put("launch_authority",false);
            var profile=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(Files.readAllBytes(fixture.profile()));var existing=StrictJson.parse(Files.readAllBytes(temporary.resolve("guard.json")));guard.set("target",existing.get("target"));
            guard.set("original_native_plan",ref(fixture.profile()).toJson());guard.set("original_environment",ref(fixture.inventory()).toJson());guard.set("original_settings_snapshot",ref(fixture.snapshot()).toJson());
            Files.write(temporary.resolve("guard.json"),StrictJson.canonical(guard));profile.put("guard_profile_sha256",ref(temporary.resolve("guard.json")).sha256());
            assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.build(new RawJson(StrictJson.canonical(profile)),fixture.game()));
    }
    @Test void extraCompleteModFileAndChangedImmutableSnapshotRejectRatherThanRepin()throws Exception{
        var fixture=fixture();var input=fixture.input();Files.writeString(fixture.mod().resolve("new.txt"),"not inventoried");assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.inspect(input));Files.delete(fixture.mod().resolve("new.txt"));
        Files.writeString(fixture.snapshot(),"not the launch bytes");assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.inspect(input));
    }
    @Test void fixedRootAndStockDependencyGuiOverridesAreRejectedByActualBuilder()throws Exception{
        var fixture=fixture();Path gui=Files.createDirectories(fixture.mod().resolve("gui"));Files.writeString(gui.resolve("new.gui"),"widget={name=\"timeline_widget\"}");
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.build(new RawJson(Files.readAllBytes(fixture.profile())),fixture.game()));
        Files.writeString(gui.resolve("new.gui"),"type exit_button = widget {}");Files.writeString(fixture.game().resolve("gui/hud.gui"),"widget={name=\"timeline_widget\" exit_button={}}");Files.writeString(fixture.game().resolve("gui/shared/exit.gui"),"type exit_button = widget {}");
        assertThrows(IllegalArgumentException.class,()->NormalExitSourceInventory.build(new RawJson(Files.readAllBytes(fixture.profile())),fixture.game()));
    }
}

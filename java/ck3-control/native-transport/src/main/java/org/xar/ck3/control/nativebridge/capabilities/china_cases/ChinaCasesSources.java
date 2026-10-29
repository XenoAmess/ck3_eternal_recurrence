package org.xar.ck3.control.nativebridge.capabilities.china_cases;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact repository sources. A source witness is not deployment or exact-build live qualification. */
final class ChinaCasesSources {
    private ChinaCasesSources() { }
    static final String REPO="Z:/ck3_mod_rewrite/";
    record Pin(String relative,long bytes,String sha256) {
        ExactRef ref() { return new ExactRef(REPO+relative,bytes,sha256); }
        void verify() {
            try {
                byte[] current=Files.readAllBytes(Path.of(REPO+relative));
                StrictJson.require(current.length==bytes && HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(current)).equals(sha256),"original ZhongGuo source drift: "+relative);
            } catch(IOException|NoSuchAlgorithmException failure) { throw new IllegalStateException("original ZhongGuo source unavailable: "+relative,failure); }
        }
    }
    private static final List<Pin> PINS=List.of(
        new Pin("ck3_autonomous_player/native_bridge/src/bridge.cpp",1611813L,"41a3e271793e59cb87469324f0ef04611cc0277bedcc06d6fe1043c10fb83953"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",897392L,"a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",1658471L,"eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"),
        new Pin("tools/zhongguo_scoreboard_surface_checkpoint_provider.py",34028L,"18b23f6cf0b5c7c408e309ee90577b2e77fa4bc1258bd39b1407488021e329bb"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_b1_cycle_snapshot_contract.py",14610L,"247729b653d2ecca49a894024c9ab6e6450fb74fe17bd559174eca166291f06d"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_case_snapshot_contract.py",32905L,"ac2530429b0ed193382275eff57ea1b8fa3fb57dac3c9e3612fea21791953e50"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_ai_owned_case_snapshot_contract.py",32410L,"58eb3a6341d43c5b3932f786fa16c58e5d9b92227f846057070cdb69ff0efc75"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_result_case_snapshot_contract.py",23333L,"7eb341d0f4094536a92ce20762c6b939d5b68daff19f61da44c8ab636db42ac4"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_b2_pip_snapshot_contract.py",39892L,"e6ca1c8f711f24f25ac128d93e3336e92c945261443bbbd1b107247f8da19b77"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_promotion_compensation_postcondition_contract.py",10028L,"9a155b821ec4d9e7c27eca014d381dbd5ea48401de52db3112d045ad569b1f04"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_compensation_af5_snapshot_contract.py",8528L,"48cff74ba84a0a4f614c8071078c4066fe5af5fdf04f7ac7dda9121728e25744"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_projects_metrics_postcondition_contract.py",14013L,"b2dba9ee76457d0ec72bd87464eec145618e76482bb77d4b6687a03c88a60436"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_incident_snapshot_contract.py",26537L,"fb795fd95bcc927b6a4d50aa885c284b9e33d99a9d0896306b572843c06effcf"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_scoreboard_state_contract.py",18067L,"afe199408d36dfc28980e3588e1832aa27715a3a90572ae7200bbbd6a935d9bd"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_promotion_source_progress_contract.py",10516L,"9f8acf825ed2df8410484f48a5da979f0fb290056cf5080936e1c52409d21094"),
        new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/zhongguo_scoreboard_action_contract.py",34564L,"5859100b242207f358dddeb65a9a5feb517ea647d9704551688f3e5c080cf8ef"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_ai_owned_case_snapshot_v1.cpp",40875L,"9bd640de7784c5448d69a64c96150f9c497cfc963438f277ee0a931458a59306"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp",17327L,"84881b43d952bd1616af61f45f3442b843b0ee7dec213482e9392e07c7e33f5a"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp",16143L,"2ebeb40aff3c801787952b0341cfa5727679297e6ff1b7e7c5d1086dc5d510bd"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b1_cycle_snapshot_v1.cpp",13546L,"5b5857d5eac4c364bbd01d995b9a97ac098ed3f7762a253f95e0194d85a0356e"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b1_cycle_snapshot_v1_mailbox.cpp",11416L,"83c77c65169658c993f78bf60cb9badc2548ff64a1e022ba29d778255f71a2d1"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b1_cycle_snapshot_v1_serializer.cpp",9200L,"6a03c64b54e68e1e5e7543b03719b4cf1a2543b2611b2c30f51018537013b219"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b2_pip_snapshot_v1.cpp",44239L,"b5009b390353c7db835b2a602659e15d1f85f30507a5820002bb3237dea5e472"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b2_pip_snapshot_v1_mailbox.cpp",16137L,"20c4481554e4136f466eb644e521dc8d6acf5a735ff1c18a1f6edab9f2253273"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_b2_pip_snapshot_v1_serializer.cpp",19376L,"9b84f775bbf461547b6a75eef7e7106c4176b6f0946351e799d084690d452a1b"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_case_snapshot_v1.cpp",38106L,"c25970123844c3edac8d0668876fc68d1f9656a99437b6308bd0cba0a85e514e"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_case_snapshot_v1_mailbox.cpp",14802L,"7beb1235a892ecfa138c1e72d6182cd50cfb81441f2f93eb76064b872a60d317"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_case_snapshot_v1_serializer.cpp",15655L,"41bb321977d37e6bef2fbe34e2e0562300ad0721afaa36bc74e31ae161f131d1"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_compensation_af5_snapshot_v1.cpp",14686L,"4dd9d94280c3eedfc7710cb47dac16a70d46a6f3a0775063bca94f3785d4a340"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_compensation_af5_snapshot_v1_mailbox.cpp",16171L,"4703891f3c8eb3038d84c341e64e6eb6d9cd7196195545cb136e3746e1f7604b"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_incident_snapshot_v1.cpp",36304L,"8637ae0115fcf0c693a172ed78fac27ed4aa533bd207154d249841186d414247"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_incident_snapshot_v1_mailbox.cpp",18251L,"cf06621c2147fd90ecfebbbc5ee136607c720658cd85ba686485e2fca2f69f3d"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_incident_snapshot_v1_serializer.cpp",15515L,"f99d4dc768f2f8338424ceb0ea5d4c68d915bd7b0aeadc9372288c85d6b15b9e"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_projects_metrics_postcondition_v1.cpp",37404L,"dd431b33977fd65f32e07a4aca296d77cddd0dd1c71db0263c5c0fb627398d5b"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_projects_metrics_postcondition_v1_mailbox.cpp",16777L,"c442813d459d9c1b9e714c17a40e8b92bf858f1ec189c082e1ee58a9cee2076d"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_projects_metrics_postcondition_v1_serializer.cpp",10718L,"99cfb584ea562d7de30699e8840c96d559ec5415c2333f48effc349a8564d58d"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_promotion_compensation_postcondition_v1.cpp",37035L,"b44028dd9a76367281032b7e28510a65c2571e9430bfcbbcc4645cc0e5ab47fc"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_promotion_compensation_postcondition_v1_mailbox.cpp",16423L,"06d3334eb4674ceffe0931f11829a86e5d62f2cbb9e8e34440dd7b48bdd241f2"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_promotion_source_progress_v1_mailbox.cpp",24152L,"507baf071bc58016025d96207bad8b6a15673101bc5266cde50707f0b75c1f56"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_result_case_snapshot_v1.cpp",25147L,"cdf6bdb4c5451e9deb2ab258619eb07122ee795dd977b1885d40186d49ee8470"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_result_case_snapshot_v1_mailbox.cpp",17428L,"a27cac8c653b33ce25491fee9eaa66e671c2df31fc05253dc19d764f767bd576"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_result_case_snapshot_v1_serializer.cpp",10980L,"ab46c82c201f6eb00d6e42a8dd0528975e75991d9f0934e796bc7519645cad4b"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1.cpp",43015L,"73c6d3b603675a761053f3c337b552c382d3d7ba81e9dd4f5ffeda145304a885"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1_mailbox.cpp",24531L,"a78d4c0be90ed8af0c43e76b42cf4811223b8a20ef304c2096477f4cfca0ebd4"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_production_v1.cpp",10134L,"5e32554d409d21baa9ea8a1e289b840ea6d52e21ac77b761470429905693080b"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp",104731L,"8c21157bc4316fb1fdcfcc765a1f835689483df83d6797c8287d44a7e62e6dfe"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1_mailbox.cpp",16749L,"66a8ee78e8021b2fcdb73acd379ded4f9259efe20e36d070febd1ad78978a06a"),
        new Pin("ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1_serializer.cpp",16635L,"4c7e5f1e2010dd55fd67bbb08643134434975bb150a9501c4a6c0a927dc9c3a1")
    );
    static ExactRef contract(ChinaCasesCodec.Family family) {
        String filename=switch(family) {
            case B1 -> "zhongguo_b1_cycle_snapshot_contract.py";
            case CASE -> "zhongguo_case_snapshot_contract.py";
            case AIOWNED -> "zhongguo_ai_owned_case_snapshot_contract.py";
            case RESULT -> "zhongguo_result_case_snapshot_contract.py";
            case PIP -> "zhongguo_b2_pip_snapshot_contract.py";
            case PROMOTION -> "zhongguo_promotion_compensation_postcondition_contract.py";
            case AF5 -> "zhongguo_compensation_af5_snapshot_contract.py";
            case PROJECTS -> "zhongguo_projects_metrics_postcondition_contract.py";
            case INCIDENT -> "zhongguo_incident_snapshot_contract.py";
            case SCOREBOARD -> "zhongguo_scoreboard_state_contract.py";
            case PROGRESS -> "zhongguo_promotion_source_progress_contract.py";
        };
        return PINS.stream().filter(p->p.relative().endsWith("/"+filename)).findFirst().orElseThrow().ref();
    }
    static void verify(ChinaCasesCodec.Family family) {
        // Fixed source inventory, never permission by operation-name prefix.
        for(Pin pin:PINS) pin.verify();
        StrictJson.require(contract(family).bytes()>0,"registered contract source missing");
    }
}


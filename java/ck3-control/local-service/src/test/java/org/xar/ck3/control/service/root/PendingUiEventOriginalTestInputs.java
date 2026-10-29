package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.driver.DriverJson;
import static org.junit.jupiter.api.Assertions.*;

/** Original Python fixture/producers are mandatory compatibility inputs, never a new production implementation. */
final class PendingUiEventOriginalTestInputs {
    private PendingUiEventOriginalTestInputs(){ }
    static ObjectNode load()throws Exception{
        String python=System.getProperty("xar.python"),repository=System.getProperty("xar.repository.root");
        assertNotNull(python,"required xar.python missing; original producer differential cannot skip");assertFalse(python.isBlank());
        assertNotNull(repository,"required xar.repository.root missing; original producer differential cannot skip");assertFalse(repository.isBlank());
        Path root=Path.of(repository).toRealPath();
        String script="""
            import importlib.util,json,os
            from pathlib import Path
            root=Path(os.environ['XAR_SOURCE_REPOSITORY'])
            def module(name,relative):
                spec=importlib.util.spec_from_file_location(name,root/relative)
                value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
            event=module('actual_pending_event_fixture','ck3_autonomous_player/tests/unit/test_event_window_context_v1_bridge.py')
            pending=module('actual_pending_reply_fixture','ck3_autonomous_player/tests/unit/test_pending_character_interaction_context_v1_bridge.py')
            from xar_autoplayer.bridge.event_window_context_contract import normalize_current_event_window_context_v1
            from xar_autoplayer.bridge.native_driver import _semantic_snapshot_from_frame
            from xar_autoplayer.pending_interaction_fallback import plan_pending_interaction_left_reply_v1
            raw=event._frame('available')
            normalized=normalize_current_event_window_context_v1(raw,expected_event_instance_id=event.EVENT_ID,expected_date_raw=event.DATE_RAW,expected_snapshot_revision=event.NATIVE_REVISION)
            rows=[]
            for name in ('normal','notification','disabled','no_native'):
                packet=pending._semantic_snapshot();state=packet['state']
                state['local_player_id']=2001;state['one_life_terminal_reason']=None
                state['played_character'].update(spouse_ids=[],betrothed_id=None,primary_spouse_id=None)
                state['pending_character_interaction']['auto_accept_notification']=name=='notification'
                context=pending._frame(notification=name=='notification')
                if name=='disabled':context['legality']['reject'].update(allowed=False,reason='reject_not_legal')
                steps=['reject-pending-character-interaction','accept-pending-character-interaction','acknowledge-pending-character-interaction','block-pending-character-interaction']
                if name=='no_native':steps.remove('reject-pending-character-interaction')
                semantic=_semantic_snapshot_from_frame(packet)
                semantic.update(native_revision=pending.NATIVE_REVISION,revision=9007199254740993,episode_character_id=2001,episode_run_id='actual-new-episode')
                semantic['diagnostics']={'bridge_pid':4242,'connection_generation':3,'hello':{'expected_ck3_version':context['build']['version'],'expected_ck3_sha256':context['build']['exe_sha256']}}
                plan=plan_pending_interaction_left_reply_v1(snapshot=semantic,context=context,original_plan=None,action_steps=steps,registry_state_dir=None)
                rows.append(dict(name=name,packet=packet,context=context,query=pending._native_result(frame=context),steps=steps,plan=plan))
            print(json.dumps(dict(event=raw,event_normalized=normalized,event_snapshot=event._snapshot(),pending=rows),ensure_ascii=True,separators=(',',':')))
            """;
        var builder=new ProcessBuilder(python,"-c",script).directory(root.toFile()).redirectErrorStream(true);
        builder.environment().put("XAR_SOURCE_REPOSITORY",root.toString());builder.environment().put("PYTHONPATH",root.resolve("ck3_autonomous_player/src").toString());builder.environment().put("PYTHONDONTWRITEBYTECODE","1");
        var child=builder.start();var output=java.util.concurrent.CompletableFuture.supplyAsync(()->{try{return child.getInputStream().readAllBytes();}catch(IOException failure){throw new UncheckedIOException(failure);}});
        boolean ended=child.waitFor(45,TimeUnit.SECONDS);if(!ended)child.destroyForcibly();assertTrue(ended,"original pending UI producer timed out");
        byte[] bytes=output.get(5,TimeUnit.SECONDS);assertEquals(0,child.exitValue(),new String(bytes,StandardCharsets.UTF_8));
        return (ObjectNode)DriverJson.toNode(DriverJson.object(bytes,1<<20));
    }
}

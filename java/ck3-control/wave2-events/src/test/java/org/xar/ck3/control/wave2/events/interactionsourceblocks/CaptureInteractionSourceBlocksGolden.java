package org.xar.ck3.control.wave2.events.interactionsourceblocks;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Once-only original source helper oracle; never a default JUnit or production dependency. */
public final class CaptureInteractionSourceBlocksGolden {
    private CaptureInteractionSourceBlocksGolden() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) { throw new IllegalArgumentException("repo-root python-exe new-output required"); }
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(); Path python = Path.of(args[1]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!output.startsWith(temporary.getParent().resolve("logs")) || Files.exists(output)) { throw new IllegalArgumentException("fresh package output required"); }
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-c", SCRIPT, repo.toString(), output.toString()); builder.directory(repo.toFile()); builder.inheritIO();
        builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        if (!process.waitFor(90, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("original helper capture timeout"); }
        if (process.exitValue() != 0 || !Files.isRegularFile(output) || Files.size(output) > 65_536) { throw new IllegalStateException("original helper capture failed"); }
    }
    private static final String SCRIPT = """
            from pathlib import Path
            import sys,json,hashlib,datetime,re
            root,out=map(Path,sys.argv[1:]);sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'tools')]
            from xar_autoplayer import interaction_offline_analysis as original
            from ck3_live_run_id import current_machine_id
            q=chr(34);bs=chr(92)
            samples=[
             ('simple','x = { a = 1 }'),('nested','x = { nested = { value = { yes = yes } } }'),
             ('leading_blank','\\n \\n\\tx = {}'),('same_line_miss','prefix x = {}'),('empty',''),('whitespace',' \\t\\n'*32),
             ('quoted_braces','x = { log = '+q+'} { # still string'+q+' }'),
             ('escaped_quote','x = { log = '+q+'a'+bs+q+'}'+q+' a = { yes = yes } }'),
             ('escaped_backslash','x = { log = '+q+'a'+bs+bs+q+' a = { yes = yes } }'),
             ('comment_brace','x = { # } opening comment \\n a = { yes = yes } \\n}'),
             ('comment_cr','x = { # } ignored\\r a = {} }'),('comment_hides_close','x = { # }'),
             ('unclosed_brace','x = { nested = {}'),('unclosed_quote','x = { log = '+q+'still open }'),
             ('trailing_garbage','x = {} ignored } {'),('multiple','x = { first = yes }\\nx = { second = yes }'),
             ('key_prefix','xx = {}\\nx = { exact = yes }'),('cr_not_anchor','prefix\\rx = {}'),
             ('unicode_line_not_anchor','prefix'+chr(0x2028)+'x = {}'),
             ('python_whitespace',chr(28)+chr(29)+chr(30)+chr(31)+chr(0x85)+chr(0xa0)+chr(0x2003)+'x = {}'),
             ('whitespace_across_lines','\\n\\tx\\n =\\n {\\n a = 1\\n}'),
             ('unicode_body','x = { log = '+q+'漢字😀 }'+q+' }'),('bom_text',chr(0xfeff)+'x = {}'),
             ('effects','x = {\\n category = interaction_category_religion\\n on_accept = { scope:recipient = { add_stress = 10 } }\\n on_decline = { # ignored }\\n add_piety = -5 }\\n}'),
             ('absent_effects','x = { category = any }'),('same_line_effects','x = { on_accept = {} on_decline = {} }'),
             ('empty_effects','x = {\\n on_accept = {}\\n on_decline = {}\\n}'),
             ('nested_categories','x = {\\n category = first\\n child = {\\n category = nested\\n }\\n category = first\\n}'),
             ('category_prefix','x = {\\n category = abc-def\\n}'),
             ('prior_multiline_quote','log = '+q+'previous\\nx = { inside = yes }'+q),
             ('missing_key','y = { x = {} }'),('lf_after_cr','prefix\\r\\nx = {}')]
            cases=[]
            for name,source in samples:
                try:
                    value=original.block(source,'x')
                    effects=None if value is None else {'definition':value,'category':re.findall(r'(?m)^\\s*category\\s*=\\s*([A-Za-z0-9_]+)',value),'on_accept':original.block(value,'on_accept'),'on_decline':original.block(value,'on_decline')}
                    cases.append({'name':name,'text':source,'key':'x','expected_status':'absent' if value is None else 'found','expected_text':value,'expected_effects':effects})
                except ValueError as error:
                    cases.append({'name':name,'text':source,'key':'x','expected_status':'unterminated','expected_error':str(error)})
            producer=root/'ck3_autonomous_player/src/xar_autoplayer/interaction_offline_analysis.py'
            data={'schema':'xar.interaction-source-block-original-producer-golden/v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producer_path':producer.relative_to(root).as_posix(),'producer_sha256':hashlib.sha256(producer.read_bytes()).hexdigest(),'notice':'Actual unchanged block function called; category projection uses the exact current analyze_batch regex. Synthetic text only, zero Game/MCP/ledger or filesystem source-reader qualification.','cases':cases}
            raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8');assert len(raw)<=65536
            with out.open('xb') as stream:stream.write(raw)
            print(json.dumps({'machine_id':data['machine_id'],'output':str(out),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'legacy_cases':len(cases),'Game_MCP_ledger_calls':0}))
            """;
}

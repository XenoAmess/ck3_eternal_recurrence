package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.StrictJson;

/** Test-only exact original method/classes, stopped by the absent native-revision fixture after ingress validation. */
final class OriginalRootRevisionOracle {
    private OriginalRootRevisionOracle() { }
    record Failure(String kind,String message) { }
    private static final String CODE="""
        import ast,hashlib,json,pathlib,sys,types
        repo=pathlib.Path(sys.argv[1]).resolve(strict=True)
        base=repo/'ck3_autonomous_player/src/xar_autoplayer/bridge'
        def source(name,size,digest):
            path=base/name; raw=path.read_bytes()
            assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest,name
            return path,ast.parse(raw.decode('utf-8-sig'))
        driver,defs=source('driver.py',20803,'eed449063debf1a84216a350f0178d64a9a6602bbfcc266298a810a9bb736fb6')
        path,tree=source('service.py',897392,'a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e')
        env={}
        for name in ('BridgeUnavailableError','PreSubmissionRevisionMismatchError'):
            cls=next(n for n in defs.body if isinstance(n,ast.ClassDef) and n.name==name)
            exec(compile(ast.Module(body=[cls],type_ignores=[]),str(driver),'exec'),env)
        owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GameplayBridgeService')
        method=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='query_campaign_root_context_v1')
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),env)
        call=json.loads(sys.argv[2])
        # Actual source code reaches native_revision only after the original paused/current/expected/equality checks.
        snapshot={'paused':True,'revision':call['current']}
        software=types.SimpleNamespace(snapshot=lambda **kw:snapshot)
        try:
            env[method.name](software,expected_revision=call['expected'])
            raise AssertionError('native-free boundary fixture unexpectedly completed ROOT')
        except (env['BridgeUnavailableError'],ValueError) as failure:
            print(json.dumps({'kind':type(failure).__name__,'message':str(failure)},sort_keys=True,separators=(',',':')))
        """;
    static Failure failure(BigInteger current,BigInteger expected) throws IOException {
        Path repository=required("xar.repository.root"),python=required("xar.python");
        var args=StrictJson.object().put("current",current).put("expected",expected);
        ProcessBuilder builder=new ProcessBuilder(python.toString(),"-B","-X","utf8","-c",CODE,
                repository.toString(),new String(StrictJson.canonical(args),StandardCharsets.UTF_8));
        builder.directory(repository.toFile());builder.redirectErrorStream(true);
        Process child=builder.start();child.getOutputStream().close();
        try {
            if(!child.waitFor(45,TimeUnit.SECONDS))throw new IOException("NOT_RUN_ORIGINAL_ROOT_ORACLE_TIMEOUT");
            byte[] bytes=child.getInputStream().readNBytes(32769);
            if(bytes.length>32768 || child.exitValue()!=0)
                throw new IOException("NOT_RUN_REQUIRED_ORIGINAL_ROOT_SOURCE: "+new String(bytes,StandardCharsets.UTF_8));
            var row=StrictJson.object(StrictJson.parse(bytes),Set.of("kind","message"));
            return new Failure(StrictJson.text(row.get("kind")),StrictJson.text(row.get("message")));
        } catch(InterruptedException interrupted) {
            Thread.currentThread().interrupt();throw new IOException("original ROOT oracle interrupted",interrupted);
        } finally { if(child.isAlive())child.destroyForcibly(); }
    }
    private static Path required(String property) throws IOException {
        String value=System.getProperty(property);
        if(value==null || value.isBlank())throw new IOException("NOT_RUN_REQUIRED: "+property);
        Path path=Path.of(value);
        if(!path.isAbsolute() || !path.normalize().equals(path))throw new IOException("exact absolute original path required: "+property);
        return path.toRealPath();
    }
}

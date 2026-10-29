package org.xar.ck3.control.wave3.planning.military;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.contracts.StrictJson;

/** Explicit test-fixture capture only. Runs the unchanged real original Python producer, never a substitute/golden. */
public final class MilitaryGeometryOriginalCapture {
    private MilitaryGeometryOriginalCapture() { }
    private static final String CAPTURE = """
            import hashlib,inspect,json,pathlib,sys
            repo,inputs,source_sha=sys.argv[1:]
            source=pathlib.Path(repo)/'ck3_autonomous_player/src/xar_autoplayer/strategy.py'
            if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:
                raise RuntimeError('original producer source precheck differs')
            sys.path[:0]=[repo,str(pathlib.Path(repo)/'ck3_autonomous_player/src')]
            from xar_autoplayer import strategy
            if pathlib.Path(inspect.getsourcefile(strategy._audit_war_route)).resolve()!=source.resolve():
                raise RuntimeError('actual original producer module origin differs')
            vectors=json.loads(pathlib.Path(inputs).read_bytes())
            output=[]
            for row in vectors:
                args=dict(row['input'])
                route=args.pop('route_value')
                actual=strategy._audit_war_route(route,**args)
                output.append({'name':row['name'],'input':row['input'],'expected':actual})
            if hashlib.sha256(source.read_bytes()).hexdigest()!=source_sha:
                raise RuntimeError('original producer source postcheck differs')
            print(json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
            """;
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 5) throw new IllegalArgumentException("pinned Python,repo,authored inputs,original source SHA,output required");
        Path python = Path.of(args[0]).toAbsolutePath(); Path repo = Path.of(args[1]).toAbsolutePath();
        Path inputs = Path.of(args[2]).toAbsolutePath(); Path output = Path.of(args[4]).toAbsolutePath();
        if (!Files.isRegularFile(python) || !Files.isDirectory(repo) || !Files.isRegularFile(inputs) || Files.exists(output))
            throw new IOException("fresh actual fixture output and original existing inputs required");
        Files.createDirectories(output.getParent()); Path stderr = output.resolveSibling(output.getFileName() + ".stderr");
        Path stdout = output.resolveSibling(output.getFileName() + ".raw-stdout.json");
        if (Files.exists(stdout) || Files.exists(stderr)) throw new IOException("fresh original capture stream paths required");
        Path privatePycache = output.getParent().resolve("fresh-original-producer-pycache");
        if (Files.exists(privatePycache)) throw new IOException("original producer requires a fresh private bytecode lookup root");
        Process process = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-X", "pycache_prefix=" + privatePycache, "-c", CAPTURE,
                repo.toString(), inputs.toString(), args[3]).directory(repo.toFile()).redirectError(stderr.toFile()).redirectOutput(stdout.toFile()).start();
        if (!process.waitFor(Duration.ofSeconds(90).toMillis(), TimeUnit.MILLISECONDS)) {
            process.destroyForcibly(); process.waitFor(); throw new IOException("actual original producer capture timed out");
        }
        if (process.exitValue() != 0) throw new IOException("actual original producer exit=" + process.exitValue() + "; retained " + stderr);
        if (Files.size(stdout) <= 0 || Files.size(stdout) > 1_048_576) throw new IOException("bounded actual original producer stdout required");
        byte[] original = Files.readAllBytes(stdout);
        var rows = StrictJson.parse(original, 1_048_576);
        if (!rows.isArray() || rows.size() != 14) throw new IOException("all 14 actual original producer rows required");
        Files.write(output, original, StandardOpenOption.CREATE_NEW);
        System.out.println("ACTUAL_ORIGINAL_GEOMETRY_14_CAPTURED " + output);
    }
}

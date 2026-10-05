import hashlib
import json
from pathlib import Path

task_root = Path(__file__).resolve().parent
failed = task_root / 'review-package-001'
failure = {
    'status': 'REVIEW_ENVIRONMENT_FAILED_PRESERVED',
    'reason': 'Local inspect.py shadowed stdlib inspect when dataclasses imported the actual frozen parser. The failed mkdir reached only the already existing external source-slice-001. No candidate or main write.',
    'original_runner_sha256': hashlib.sha256((task_root / 'finish_review.py').read_bytes()).hexdigest(),
    'corrective_invocation': 'Python313 -I -B finish_review_002.py',
}
(failed / 'FAILURE.json').write_bytes((json.dumps(failure, indent=2) + '\n').encode())
source = (task_root / 'finish_review.py').read_text(encoding='utf-8')
source = source.replace("out=root/'review-package-001';out.mkdir(exist_ok=False)", "out=root/'review-package-002';out.mkdir(exist_ok=False)")
source = source.replace("title=one(one(b,'NOT'),'any_held_title') if False else next(", "title=next(")
source = source.replace("shutil.copyfile(root/'finish_review.py',out/'finish_review.py')", "shutil.copyfile(root/'finish_review_002.py',out/'finish_review_002.py'); (out/'executed-review-source.py').write_bytes(source.encode())")
exec(compile(source, str(task_root / 'executed-review-source.py'), 'exec'))

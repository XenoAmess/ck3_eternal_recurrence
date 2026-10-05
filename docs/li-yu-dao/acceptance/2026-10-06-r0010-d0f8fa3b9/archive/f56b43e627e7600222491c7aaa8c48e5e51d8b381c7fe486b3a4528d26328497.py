from pathlib import Path
# Keep first packaging attempt intact. Windows Path renders backslashes while
# ROOT ref3 stores forward slashes; compare resolved identity + bytes + SHA.
source=Path(__file__).with_name('seal_final_export_runtime_review.py').read_text(encoding='utf-8')
source=source.replace("P=O/'review-package-001'", "P=O/'review-package-002'")
source=source.replace("assert inventory_ref==export['source']['inventory']", "assert Path(inventory_ref['path']).resolve()==Path(export['source']['inventory']['path']).resolve() and inventory_ref['bytes']==export['source']['inventory']['bytes'] and inventory_ref['sha256']==export['source']['inventory']['sha256']")
source=source.replace("'reviewer_failure_preserved':", "'reviewer_final_packaging_failure_preserved':{'script':str(O/'seal_final_export_runtime_review.py'),'reason':'Raw ref3 dict path separator mismatch only; source bytes/SHA equal. Empty review-package-001 and original script retained.'},\n 'reviewer_failure_preserved':")
source=source.replace("'read_actual_export_metadata.py','seal_final_export_runtime_review.py']", "'read_actual_export_metadata.py','seal_final_export_runtime_review.py','seal_final_export_runtime_review_v2.py']")
exec(compile(source,str(Path(__file__).with_name('seal_final_export_runtime_review.py')),'exec'))

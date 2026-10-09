"""Locate pinned GUI pixels in an original PNG. This module never sends input.

Matching proves location only; desktop actions and lifecycle proof are separate.
"""
from pathlib import Path
import argparse
import hashlib
import json

def require(ok,message):
    if not ok:raise RuntimeError(message)
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def locate(image_path,template):
    import cv2,numpy as np
    from PIL import Image
    source=Path(template['source']['path'])
    require({k:v for k,v in pin(source).items() if k!='path'}=={k:template['source'][k] for k in ('bytes','sha256')},'Reviewed template source changed')
    require(template['scale']==1.0,'No inferred scaling is allowed')
    with Image.open(source) as img:
        require(list(img.size)==template['source']['size'],'Original template dimensions changed')
        patch=np.asarray(img.convert('RGB').crop(tuple(template['crop_ltrb'])))
    with Image.open(image_path) as img:actual_size=img.size;hay=np.asarray(img.convert('RGB'))
    patch=cv2.cvtColor(patch,cv2.COLOR_RGB2GRAY);hay=cv2.cvtColor(hay,cv2.COLOR_RGB2GRAY)
    height,width=patch.shape
    require(hay.shape[0]>=height and hay.shape[1]>=width and float(patch.std())>5,'Actual image/template geometry or contrast unavailable')
    scores=cv2.matchTemplate(hay,patch,cv2.TM_CCOEFF_NORMED)
    _,maximum,_,location=cv2.minMaxLoc(scores);left,top=location
    other=scores.copy()
    other[max(0,top-height):min(other.shape[0],top+height),max(0,left-width):min(other.shape[1],left+width)]=-1
    _,runner_up,_,_=cv2.minMaxLoc(other)
    result={'source':template['source'],'source_crop_ltrb':template['crop_ltrb'],'actual_image':pin(image_path),
        'actual_image_size':list(actual_size),'match_rectangle':[left,top,width,height],
        'correlation':float(maximum),'runner_up_correlation':float(runner_up),
        'point':[left+template['point_offset'][0],top+template['point_offset'][1]],'scale':1.0,
        'matched_uniquely':maximum>=template['minimum_correlation'] and maximum-runner_up>=template['minimum_runner_up_gap'],
        'business_result':'PENDING_ROOT_ACTUAL_VISUAL_AND_TYPED_REVIEW','uses_ocr':False}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--templates',type=Path,required=True)
    parser.add_argument('--name',required=True)
    parser.add_argument('--match-receipt',type=Path,required=True)
    args=parser.parse_args()
    template=json.loads(args.templates.read_bytes())['templates'][args.name]
    result=locate(args.image,template)
    args.match_receipt.parent.mkdir(parents=True,exist_ok=True)
    with args.match_receipt.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    return 0 if result['matched_uniquely'] else 2


if __name__=='__main__':
    raise SystemExit(main())

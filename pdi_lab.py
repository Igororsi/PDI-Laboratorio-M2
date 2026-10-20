from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import cv2
import numpy as np

def read_image(path):
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Falha ao ler imagem: {path}")
    if img.ndim not in (2, 3):
        raise ValueError("Imagem incompatível: dimensões inválidas.")
    return img

def to_gray(img):
    if img.ndim == 2:
        return img
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    if img.shape[2] == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    raise ValueError("Imagem incompatível: esperado 1, 3 ou 4 canais.")

def segment_image(img, method="fixed", threshold=120, block_size=11, constant=2,
                  hsv_low=(0,0,150), hsv_high=(179,255,255), invert=False):
    if not 0 <= threshold <= 255:
        raise ValueError("--threshold deve estar entre 0 e 255.")
    if block_size < 3 or block_size % 2 == 0:
        raise ValueError("--block-size deve ser ímpar e >= 3.")
    if method == "hsv":
        if img.ndim != 3 or img.shape[2] < 3:
            raise ValueError("O método hsv exige imagem colorida.")
        bgr = img[:,:,:3] if img.shape[2] == 3 else cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lo = np.array(hsv_low, dtype=np.uint8); hi = np.array(hsv_high, dtype=np.uint8)
        mask = cv2.inRange(hsv, lo, hi)
    else:
        gray = to_gray(img)
        if gray.dtype != np.uint8:
            if np.issubdtype(gray.dtype, np.integer):
                gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            else:
                raise ValueError("Tipo de imagem não suportado; use uint8 ou inteiro.")
        if method == "fixed":
            # Contrato do enunciado: f(x,y) >= T vira 255.
            mask = np.where(gray >= int(threshold), 255, 0).astype(np.uint8)
        elif method == "otsu":
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "adaptive":
            mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, int(block_size), float(constant))
        else:
            raise ValueError(f"Método desconhecido: {method}")
    if invert:
        mask = cv2.bitwise_not(mask)
    return mask

def validate_mask(mask, shape=None):
    if mask is None or mask.ndim != 2:
        raise ValueError("Máscara deve ter exatamente um canal.")
    if shape is not None and mask.shape != shape[:2]:
        raise ValueError("Dimensões da máscara diferem da entrada.")
    vals = set(np.unique(mask).tolist())
    if not vals.issubset({0,255}):
        raise ValueError(f"Máscara não binária: valores encontrados {sorted(vals)}")
    return True

def run_segment(args):
    img = read_image(args.input)
    mask = segment_image(img, args.method, args.threshold, args.block_size, args.constant,
                         tuple(args.hsv_low), tuple(args.hsv_high), args.invert)
    validate_mask(mask, img.shape)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out), mask):
        raise ValueError(f"Falha ao salvar: {out}")
    fg = int(np.count_nonzero(mask))
    total = int(mask.size)
    print(json.dumps({"operation":"segment","method":args.method,"width":int(mask.shape[1]),
                      "height":int(mask.shape[0]),"foreground_pixels":fg,
                      "foreground_ratio":fg/total,"unique_values":sorted(set(np.unique(mask).tolist()))},
                     ensure_ascii=False))
    return 0

def component_rows(mask, connectivity, min_area):
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=connectivity)
    rows=[]
    for label in range(1,n):
        x,y,w,h,area = [int(v) for v in stats[label]]
        cx,cy = [float(v) for v in centroids[label]]
        rows.append({"label":label,"area":area,"x":x,"y":y,"width":w,"height":h,
                     "cx":round(cx,4),"cy":round(cy,4),"kept":bool(area >= min_area)})
    return rows, labels

def write_csv(path, rows):
    with open(path,"w",newline="",encoding="utf-8") as f:
        fields=["label","area","x","y","width","height","cx","cy","kept"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def run_analyze(args):
    img = read_image(args.input)
    if img.ndim == 3:
        img = to_gray(img)
    if img.dtype != np.uint8:
        raise ValueError("A máscara de entrada deve ser uint8.")
    validate_mask(img)
    if args.connectivity not in (4,8):
        raise ValueError("--connectivity aceita somente 4 ou 8.")
    if args.min_area < 0:
        raise ValueError("--min-area deve ser inteiro não negativo.")
    prefix = Path(args.output); prefix.parent.mkdir(parents=True, exist_ok=True)
    stem = prefix.name
    outdir = prefix.parent
    # Count initial mask under both connectivities, and export the selected one.
    rows4,_ = component_rows(img,4,args.min_area)
    rows8,labels8 = component_rows(img,8,args.min_area)
    initial_rows = rows4 if args.connectivity == 4 else rows8
    _, labels_initial = cv2.connectedComponents(img, connectivity=args.connectivity)
    # Morphology: opening removes isolated specks; closing repairs tiny holes/gaps.
    shape = cv2.MORPH_ELLIPSE if args.kernel_shape == "ellipse" else cv2.MORPH_RECT
    kernel_open = cv2.getStructuringElement(shape,(args.open_kernel,args.open_kernel))
    kernel_close = cv2.getStructuringElement(shape,(args.close_kernel,args.close_kernel))
    opened = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel_open, iterations=args.iterations)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close, iterations=args.iterations)
    final_rows, final_labels = component_rows(closed,args.connectivity,args.min_area)
    # Initial CSV and final CSV
    write_csv(outdir/f"{stem}_initial.csv",initial_rows)
    write_csv(outdir/f"{stem}_final.csv",final_rows)
    cv2.imwrite(str(outdir/f"{stem}_stage_opening.png"),opened)
    cv2.imwrite(str(outdir/f"{stem}_stage_closing.png"),closed)
    cv2.imwrite(str(outdir/f"{stem}_labels.png"), colorize_labels(final_labels))
    # overlay with boxes
    overlay = cv2.cvtColor(closed,cv2.COLOR_GRAY2BGR)
    for row in final_rows:
        if row["kept"]:
            x,y,w,h = row["x"],row["y"],row["width"],row["height"]
            cv2.rectangle(overlay,(x,y),(x+w-1,y+h-1),(0,0,255),1)
            cv2.putText(overlay,str(row["label"]),(x,max(12,y-3)),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,0,0),1,cv2.LINE_AA)
    cv2.imwrite(str(outdir/f"{stem}_boxes.png"),overlay)
    area0=int(np.count_nonzero(img)); area1=int(np.count_nonzero(closed))
    summary={"input":str(args.input),"connectivity_selected":args.connectivity,
      "connectivity_4_initial_components":len(rows4),"connectivity_8_initial_components":len(rows8),
      "initial_components_selected":len(initial_rows),"final_components_raw":len(final_rows),
      "initial_components_kept":sum(r["kept"] for r in initial_rows),
      "final_components_kept":sum(r["kept"] for r in final_rows),
      "initial_foreground_pixels":area0,"final_foreground_pixels":area1,
      "initial_foreground_ratio":area0/img.size,"final_foreground_ratio":area1/closed.size,
      "min_area":args.min_area,"morphology":{"order":["opening","closing"],"shape":args.kernel_shape,
       "open_kernel":[args.open_kernel,args.open_kernel],"close_kernel":[args.close_kernel,args.close_kernel],
       "iterations":args.iterations}}
    with open(outdir/f"{stem}_summary.json","w",encoding="utf-8") as f: json.dump(summary,f,indent=2,ensure_ascii=False)
    print(json.dumps(summary,ensure_ascii=False))
    return 0

def colorize_labels(labels):
    h,w=labels.shape
    out=np.zeros((h,w,3),dtype=np.uint8)
    for lab in np.unique(labels):
        if lab == 0: continue
        # deterministic colors for repeatability
        color=((lab*67)%255,(lab*131)%255,(lab*197)%255)
        out[labels==lab]=color
    return out

def build_parser():
    p=argparse.ArgumentParser(prog="pdi_lab",description="Laboratórios PDI M2.1/M2.2")
    p.add_argument("--input",required=True,help="Imagem de entrada")
    p.add_argument("--output",required=True,help="Arquivo de saída (segment) ou prefixo (analyze)")
    p.add_argument("--operation",required=True,choices=["segment","analyze"])
    p.add_argument("--method",default="fixed",choices=["fixed","otsu","adaptive","hsv"])
    p.add_argument("--threshold",type=int,default=120)
    p.add_argument("--block-size",type=int,default=11)
    p.add_argument("--constant",type=float,default=2.0)
    p.add_argument("--hsv-low",type=int,nargs=3,default=[0,0,150],metavar=("HMIN","SMIN","VMIN"))
    p.add_argument("--hsv-high",type=int,nargs=3,default=[179,255,255],metavar=("HMAX","SMAX","VMAX"))
    p.add_argument("--invert",action="store_true",help="Inverte a máscara após limiarização")
    p.add_argument("--connectivity",type=int,default=8)
    p.add_argument("--min-area",type=int,default=20)
    p.add_argument("--kernel-shape",choices=["rect","ellipse"],default="ellipse")
    p.add_argument("--open-kernel",type=int,default=3)
    p.add_argument("--close-kernel",type=int,default=5)
    p.add_argument("--iterations",type=int,default=1)
    return p

def main(argv=None):
    parser=build_parser(); args=parser.parse_args(argv)
    try:
        if args.operation=="segment":
            if args.method not in ("fixed","otsu","adaptive","hsv"): raise ValueError("Método inválido.")
            return run_segment(args)
        if args.open_kernel < 1 or args.close_kernel < 1 or args.iterations < 1:
            raise ValueError("Parâmetros morfológicos devem ser positivos.")
        return run_analyze(args)
    except (ValueError, cv2.error, OSError) as exc:
        print(f"ERRO: {exc}",file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())

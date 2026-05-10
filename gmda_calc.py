"""
GMDA Metrics Runner
-------------------
Computes GMDA metrics (CanScore, CanOrg, CanAcc, ScaBias, DistAcc, RotBias, AngAcc)
for sketchmaps against a basemap, across multiple location folders.

Usage:
    python gmda_runner.py --root path/to/data --output results.xlsx

If --root is not provided, defaults to ./datasets/Data
"""

import os
import re
import json
import math
import argparse
import numpy as np
import pandas as pd
import geopandas as gpd

# ---------------------------------------------------------------------------
# Single source of truth for basemap filename detection.
# Matches: location1.png.geojson, _location2.jpg.geojson, basemap.png.geojson, ...
# ---------------------------------------------------------------------------
BASEMAP_PATTERN = re.compile(
    r'((_location|location)\d+|basemap)\.(png|jpg|jpeg)\.geojson$',
    re.IGNORECASE
)


def compute_mbr_points(geometry, otype, r_buffer=1):
    """Exact MBR logic from Script 1."""
    if geometry is None or geometry.is_empty:
        return None
    if otype == 'Polygon':
        x_min, y_min, x_max, y_max = map(float, geometry.bounds)
    elif otype == 'CircleMarker':
        coords = list(geometry.coords)[0]
        x, y = float(coords[0]), float(coords[1])
        x_min, x_max = x - r_buffer, x + r_buffer
        y_min, y_max = y - r_buffer, y + r_buffer
    else:
        return None

    return [
        [x_min, y_max], [(x_min + x_max) / 2, y_max], [x_max, y_max],
        [x_max, (y_min + y_max) / 2], [x_max, y_min],
        [(x_min + x_max) / 2, y_min], [x_min, y_min],
        [x_min, (y_min + y_max) / 2],
    ]


def landmark_pairs(dict_align, bsm_dict_mbr, skm_dict_mbr):
    keys = list(dict_align.keys())
    for i in range(len(keys) - 1):
        k1 = keys[i]
        if k1 not in bsm_dict_mbr or dict_align[k1] not in skm_dict_mbr:
            continue
        b1_pts, s1_pts = bsm_dict_mbr[k1], skm_dict_mbr[dict_align[k1]]

        for j in range(i + 1, len(keys)):
            k2 = keys[j]
            if k2 not in bsm_dict_mbr or dict_align[k2] not in skm_dict_mbr:
                continue
            b2_pts, s2_pts = bsm_dict_mbr[k2], skm_dict_mbr[dict_align[k2]]
            
            for p in range(8):
                b1_x, b1_y = b1_pts[p]
                s1_x, s1_y = s1_pts[p]
                for l in range(8):
                    b2_x, b2_y = b2_pts[l]
                    s2_x, s2_y = s2_pts[l]
                    yield b1_x, b1_y, b2_x, b2_y, s1_x, s1_y, s2_x, s2_y


def run_gmda_math(dict_align, bsm_dict_mbr, skm_dict_mbr):
    """Aggregated GMDA metrics following original logic."""
    nTL = len(bsm_dict_mbr)
    nDL = len(dict_align)
    n_nTL = math.comb(8 * nTL, 2) - nTL * math.comb(8, 2)
    n_nDL = math.comb(8 * nDL, 2) - nDL * math.comb(8, 2)

    sum_can_score, sum_sin, sum_cos, sum_diff_abs = 0, 0, 0, 0
    max_D_bsm, max_D_skm = 1e-9, 1e-9
    pairs_data = []

    for b1x, b1y, b2x, b2y, s1x, s1y, s2x, s2y in landmark_pairs(dict_align, bsm_dict_mbr, skm_dict_mbr):
        if (b1y < b2y and s1y < s2y) or (b1y > b2y and s1y > s2y): sum_can_score += 1
        if (b1x < b2x and s1x < s2x) or (b1x > b2x and s1x > s2x): sum_can_score += 1
        
        d_bsm = np.sqrt((b1x - b2x)**2 + (b1y - b2y)**2)
        d_skm = np.sqrt((s1x - s2x)**2 + (s1y - s2y)**2)
        max_D_bsm = max(max_D_bsm, d_bsm)
        max_D_skm = max(max_D_skm, d_skm)
        pairs_data.append((d_bsm, d_skm))

        ang_bsm = np.arctan2(b2x - b1x, b2y - b1y)
        ang_skm = np.arctan2(s2x - s1x, s2y - s1y)
        ang_diff = ang_skm - ang_bsm
        while ang_diff < -np.pi: ang_diff += (2 * np.pi)
        while ang_diff > np.pi: ang_diff -= (2 * np.pi)
        
        sum_sin += np.sin(ang_diff)
        sum_cos += np.cos(ang_diff)
        sum_diff_abs += np.abs(np.degrees(ang_diff))

    sum_dr_diff = sum([(ds/max_D_skm - db/max_D_bsm) for db, ds in pairs_data])
    sum_dr_diff_abs = sum([abs(ds/max_D_skm - db/max_D_bsm) for db, ds in pairs_data])

    return {
        'CanScore': sum_can_score,
        'CanOrg': np.round(sum_can_score / (2 * n_nTL), 2) if n_nTL > 0 else 0,
        'CanAcc': np.round(sum_can_score / (2 * n_nDL), 2) if n_nDL > 0 else 0,
        'ScaBias': np.round(sum_dr_diff / n_nDL, 2) if n_nDL > 0 else 0,
        'DistAcc': np.round(1 - (sum_dr_diff_abs / n_nDL), 2) if n_nDL > 0 else 0,
        'RotBias': np.round(np.degrees(np.arctan2(sum_sin/n_nDL, sum_cos/n_nDL)), 2) if n_nDL > 0 else 0,
        'AngAcc': np.round(1 - sum_diff_abs / (180 * n_nDL), 2) if n_nDL > 0 else 0
    }


def process_folder(folder_path):
    files = os.listdir(folder_path)
    
    # Generic basemap detection (uses shared BASEMAP_PATTERN)
    bsm_file = next((f for f in files if BASEMAP_PATTERN.match(f)), None)
    aln_file = next((f for f in files if f == 'alignment.json'), None)
    
    if not bsm_file or not aln_file:
        print(f"  [Skip] Missing basemap or alignment in {folder_path}")
        return pd.DataFrame()

    bsm_path = os.path.join(folder_path, bsm_file)
    aln_path = os.path.join(folder_path, aln_file)

    bsm_data = gpd.read_file(bsm_path)
    with open(aln_path, 'r') as f: full_align = json.load(f)

    # 1. Build Basemap Dict exactly as script 1
    bsm_dict_mbr = {}
    for i in range(len(bsm_data)):
        row = bsm_data.iloc[i]
        if row.get('aligned') == True and row['otype'] in ['Polygon', 'CircleMarker']:
            mbr = compute_mbr_points(row.geometry, row['otype'])
            if mbr: bsm_dict_mbr[row['id']] = mbr

    final_results = []
    for f_name in files:
        # Skip the basemap itself; only treat the rest as sketchmaps
        if f_name.endswith('.geojson') and f_name != bsm_file:
            target_key = f_name.replace('.geojson', '')
            if target_key not in full_align: continue
            
            skm_data = gpd.read_file(os.path.join(folder_path, f_name))
            
            # 2. Build Sketch Dict exactly as script 1 (matching row indices of Basemap)
            skm_dict_mbr = {}
            for i in range(min(len(skm_data), len(bsm_data))):
                sk_row = skm_data.iloc[i]
                # Script 1 uses bsm_data[i].aligned to filter skm_data[i]
                if bsm_data.iloc[i].get('aligned') == True and sk_row['otype'] in ['Polygon', 'CircleMarker']:
                    mbr = compute_mbr_points(sk_row.geometry, sk_row['otype'])
                    if mbr: skm_dict_mbr[sk_row['id']] = mbr

            # 3. Build Alignment Mapping using the specific [1:] slice
            dict_align = {}
            align_block = full_align[target_key]
            for al_id in align_block:
                if al_id == 'checkAlignnum': continue
                
                bsm_keys = align_block[al_id]['BaseAlign']['0']
                skm_val_list = align_block[al_id]['SketchAlign']['0']
                
                # REPLICATING: int(skm_value[0][1:])
                try:
                    raw_val = str(skm_val_list[0])
                    sk_id = int(raw_val[1:]) 
                except: continue
                
                for k in bsm_keys:
                    # Filter check like Script 1
                    if k in bsm_dict_mbr:
                        dict_align[k] = sk_id

            if len(dict_align) >= 2:
                stats = run_gmda_math(dict_align, bsm_dict_mbr, skm_dict_mbr)
                stats['ID'] = target_key
                final_results.append(stats)

    return pd.DataFrame(final_results)


def process_all_folders(root_path, output_xlsx='gmda_results.xlsx'):
    """Walk through root_path, process every subfolder, write each folder to its own Excel sheet."""
    folder_results = {}  # {folder_label: dataframe}
    
    # Walk through every subdirectory under the root
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Detect a valid folder: must have a basemap + alignment.json
        has_bsm = any(BASEMAP_PATTERN.match(f) for f in filenames)
        has_aln = 'alignment.json' in filenames
        
        if has_bsm and has_aln:
            # Use folder name relative to root as a label
            folder_label = os.path.relpath(dirpath, root_path)
            print(f"Processing: {folder_label}")
            
            df_folder = process_folder(dirpath)
            if not df_folder.empty:
                folder_results[folder_label] = df_folder
    
    if not folder_results:
        print("No valid folders found.")
        return {}
    
    # Write each folder's table to its own sheet in one Excel file
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        for folder_label, df_folder in folder_results.items():
            # Excel sheet names: max 31 chars, no special chars: \ / : * ? [ ]
            safe_name = re.sub(r'[\\/:*?\[\]]', '_', folder_label)[:31]
            df_folder.to_excel(writer, sheet_name=safe_name, index=False)
    
    print(f"\nResults written to: {output_xlsx}")
    print(f"Total folders processed: {len(folder_results)}")
    return folder_results


# ---------------------------------------------------------------------------
# Entry point — supports command-line arguments so the path isn't hardcoded
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run GMDA metrics across location folders.')
    parser.add_argument(
        '--root', '-r',
        default=os.path.join('datasets', 'Data'),
        help='Root folder containing the location subfolders (default: datasets/Data)'
    )
    parser.add_argument(
        '--output', '-o',
        default='gmda_results.csv',
        help='Output Excel filename (default: gmda_results.csv)'
    )
    args = parser.parse_args()
    
    if not os.path.isdir(args.root):
        print(f"ERROR: Root folder does not exist: {args.root}")
        print("Use --root to specify the correct path, e.g.:")
        print(r'  python gmda_runner.py --root C:\path\to\data')
        exit(1)
    
    process_all_folders(args.root, args.output)
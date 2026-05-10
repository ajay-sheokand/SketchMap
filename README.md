# GMDA Metrics Runner

This is a small Python tool that compares **sketchmaps** (hand-drawn maps) against a **basemap** (the real map) and computes a set of similarity scores called **GMDA metrics**.

It goes through all your location folders automatically and saves the results into one Excel file — with a separate sheet for each folder, so you can easily compare them.

---

## What you need before you start

1. **Python 3.10 or newer** installed on your computer.
   You can check by opening a terminal and typing:
   ```bash
   python --version
   ```
   If that doesn't work, try `py --version`.

2. **Your data folder**, organized like this:
   ```
   datasets/
     └── Data/
         ├── Loc0/
         │   ├── basemap.png.geojson      <-- the basemap
         │   ├── alignment.json           <-- alignment info
         │   ├── sketch_user1.geojson     <-- one or more sketchmaps
         │   └── sketch_user2.geojson
         ├── Loc1/
         │   ├── location1.png.geojson
         │   ├── alignment.json
         │   └── ...
         └── ...
   ```

   The basemap file in each folder can be named in any of these ways (case doesn't matter):
   - `location1.png.geojson`, `location2.jpg.geojson`, ...
   - `_location1.png.geojson`, `_location2.jpg.geojson`, ...
   - `basemap.png.geojson`, `basemap.jpg.geojson`

---

## Step 1 — Install the required packages

Open a terminal **inside the project folder** (the one containing `gmda_calc.py`) and run:

```bash
pip install -r requirements.txt
```

This installs everything the script needs: `numpy`, `pandas`, `geopandas`, `shapely`, and `openpyxl`.

> 💡 If you get an error about NumPy 2.x crashing `shapely`, the `requirements.txt` already pins `numpy<2` to avoid it.

---

## Step 2 — Run the script

### The basic way (uses default folder `datasets/Data`)

```bash
python gmda_calc.py
```

### Using your own data folder

```bash
python gmda_calc.py --root path/to/your/data
```

### Choosing a different output filename

```bash
python gmda_calc.py --root path/to/your/data --output my_results.xlsx
```

---

## Step 3 — Look at the results

After the script finishes, you'll see a new file called **`gmda_results.xlsx`** (or whatever you named it) in the project folder.

Open it in Excel (or LibreOffice / Google Sheets). At the bottom you'll see one tab per folder — `Loc0`, `Loc1`, `Loc2`, etc. Each tab contains a table where:

- Each **row** is one sketchmap.
- The **columns** are the GMDA metrics:

| Column     | Meaning (short version)                                |
|------------|--------------------------------------------------------|
| `ID`       | Name of the sketchmap                                  |
| `CanScore` | Raw count of correctly-oriented landmark pairs         |
| `CanOrg`   | Canonical organization score (how well things line up) |
| `CanAcc`   | Canonical accuracy                                     |
| `ScaBias`  | Scale bias (is the sketch larger or smaller?)          |
| `DistAcc`  | Distance accuracy                                      |
| `RotBias`  | Rotation bias in degrees                               |
| `AngAcc`   | Angular accuracy                                       |

---

## Common issues and how to fix them

### ❌ `Python was not found...` (Windows)
Windows is using a fake shortcut. Try:
```bash
py gmda_calc.py --root datasets/Data
```
or use the full path to your Python:
```bash
"C:\path\to\python.exe" gmda_calc.py --root datasets/Data
```

### ❌ `ModuleNotFoundError: No module named 'openpyxl'`
You forgot Step 1. Install it:
```bash
pip install openpyxl
```

### ❌ `PermissionError: ... gmda_results.xlsx`
The Excel file is open. **Close it** and run the script again.

### ❌ `ImportError: numpy.core.multiarray failed to import`
Your NumPy is too new for shapely. Fix:
```bash
pip install "numpy<2"
```
Then **restart your terminal / Jupyter kernel** and try again.

### ❌ `No valid folders found.`
The script couldn't find any folder with both a basemap file **and** an `alignment.json`. Check that:
- Your `--root` path is correct
- Each location folder really contains both files
- The basemap filename matches one of the supported patterns (see top of README)

---

## How to get help

If something isn't working, please share:
1. The exact command you ran.
2. The full error message (copy-paste, not screenshot if possible).
3. The result of `ls` (or `dir` on Windows) inside the folder that's giving trouble.

---

## File overview

| File                | What it does                                      |
|---------------------|---------------------------------------------------|
| `gmda_calc.py`      | The main script — does all the work               |
| `requirements.txt`  | List of Python packages you need                  |
| `README.md`         | This file                                         |
| `gmda_results.xlsx` | The output file (created after running the script)|
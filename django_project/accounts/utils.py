# accounts/utils.py
import pandas as pd


def read_excel_dynamic(file_path: str, min_non_empty: int = 3):
    """
    Excel sheet ko dynamically header detect karke read karta hai.
    Agar ek hi sheet ho -> DataFrame return karega
    Agar multiple sheets ho -> dict {sheet_name: DataFrame} return karega
    """

    xls = pd.ExcelFile(file_path)

    result = {}
    for sheet in xls.sheet_names:
        df_raw = pd.read_excel(file_path, sheet_name=sheet, header=None)

        # find header row dynamically
        header_row_index = None
        for idx, row in df_raw.iterrows():
            non_empty = row.dropna().shape[0]
            if non_empty >= min_non_empty:  # kam se kam 3 filled cells
                header_row_index = idx
                break

        if header_row_index is not None:
            df = pd.read_excel(file_path, sheet_name=sheet, header=header_row_index)
        else:
            df = df_raw

        # cleanup
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        df.columns = df.columns.astype(str)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df.columns = df.columns.str.strip()

        result[sheet] = df

    return result if len(result) > 1 else list(result.values())[0]


# utils.py
import olefile
import pandas as pd


def fix_embedded_excel(file_path):
    """
    Repair embedded Excel extracted from main workbook.
    Returns a valid Excel path with real data.
    """
    try:
        if olefile.isOleFile(file_path):
            ole = olefile.OleFileIO(file_path)
            if ole.exists("Package"):
                with ole.openstream("Package") as stream:
                    data = stream.read()
                    new_path = file_path.replace(".xlsx", "_fixed.xlsx")
                    with open(new_path, "wb") as f:
                        f.write(data)
                    return new_path
        return file_path
    except Exception as e:
        print(f"⚠️ OLE repair failed: {e}")
        return file_path


def read_excel_dynamic_fixed(file_path):
    """
    Reads an Excel file after repairing if needed.
    Returns dictionary of {sheet_name: dataframe}.
    """
    repaired_path = fix_embedded_excel(file_path)

    try:
        xls = pd.ExcelFile(repaired_path, engine="openpyxl")
        all_data = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, engine="openpyxl")
            df = df.dropna(how="all").dropna(axis=1, how="all")
            if not df.empty:
                all_data[sheet] = df
        return all_data
    except Exception as e:
        print(f"❌ Failed to read {repaired_path}: {e}")
        return {}




# accounts/utils.py
import os
import zipfile
from django.conf import settings

def extract_embedded_excels(file_path, base_file_name):
    embedded_links = []
    output_dir = os.path.join(settings.MEDIA_ROOT, "analysis_sheets")

    with zipfile.ZipFile(file_path, "r") as z:
        for name in z.namelist():
            if name.startswith("xl/embeddings/") and name.endswith(".xlsx"):
                out_name = f"{base_file_name}_{os.path.basename(name)}"
                out_path = os.path.join(output_dir, out_name)

                with z.open(name) as src, open(out_path, "wb") as dst:
                    dst.write(src.read())

                # Generate public URL
                file_url = f"{settings.MEDIA_URL}analysis_sheets/{out_name}"
                embedded_links.append(file_url)

    return embedded_links

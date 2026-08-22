import pandas as pd

def reconstruct_real_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye una fila por orden de compra real (ffill + dedup)."""
    df = df.copy()
    df["OC_FILL"] = df["ORDENCOMPRA"].ffill()
    return df.drop_duplicates(subset=["OC_FILL", "IMPORTE", "PROVEEDOR"]).copy()

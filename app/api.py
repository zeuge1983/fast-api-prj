import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_tickets():
    df = pd.read_csv(DATA_DIR / "support_tickets.csv")
    return df.to_dict(orient="records")

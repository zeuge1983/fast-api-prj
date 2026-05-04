import pandas as pd


def load_tickets():
    df = pd.read_csv("data/support_tickets.csv")
    return df.to_dict(orient="records")

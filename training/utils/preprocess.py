"""
Preprocessing utilities for URL data.
Generates processed_feature.csv from raw URL datasets.
"""

import pandas as pd
import numpy as np
import torch
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# Feature extraction (Decision Tree)  ✅ UNCHANGED
# ============================================================

def extract_features(url: str) -> dict:
    parsed = urlparse(url)
    hostname = parsed.netloc

    return {
        "length_url": len(url),
        "length_hostname": len(hostname),
        "nb_dots": url.count("."),
        "nb_hyphens": url.count("-"),
        "nb_at": url.count("@"),
        "nb_qm": url.count("?"),
        "nb_and": url.count("&"),
        "nb_or": url.lower().count("or"),
        "nb_eq": url.count("="),
        "nb_underscore": url.count("_"),
        "nb_tilde": url.count("~"),
        "nb_percent": url.count("%"),
        "nb_slash": url.count("/"),
        "nb_star": url.count("*"),
        "nb_colon": url.count(":"),
        "nb_comma": url.count(","),
        "nb_semicolumn": url.count(";"),
        "nb_dollar": url.count("$"),
        "nb_space": url.count(" "),
        "nb_www": url.lower().count("www"),
        "nb_com": url.lower().count(".com"),
        "nb_dslash": url.count("//"),
        "http_in_path": int("http" in parsed.path.lower()),
        "https_token": int("https" in url.lower()),
        "ratio_digits_url": sum(c.isdigit() for c in url) / max(len(url), 1),
        "ratio_digits_host": sum(c.isdigit() for c in hostname) / max(len(hostname), 1),
    }


def get_feature_columns():
    return list(extract_features("http://example.com").keys())


def prepare_decision_tree_features(df, feature_columns):
    """
    Backward-compatible wrapper.
    Prepares X, y for Decision Tree training.
    """
    X = df[feature_columns].values
    y = df["label"].values

    logger.info("Decision Tree features: shape=%s", X.shape)
    return X, y


# ============================================================
# Dataset preprocessing (CSV generation) ✅ UNCHANGED
# ============================================================

def preprocess_dataset(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Extracting features from URLs...")

    features = df["url"].apply(extract_features)
    features_df = pd.DataFrame(features.tolist())

    processed_df = pd.concat(
        [df[["url", "label"]].reset_index(drop=True), features_df],
        axis=1
    )

    logger.info("Feature extraction complete: %d records", len(processed_df))
    return processed_df


# ============================================================
# LSTM utilities ✅ FIXED & COMPLETED
# ============================================================

class URLTokenizer:
    """Character-level tokenizer for LSTM URLs."""

    def __init__(self, max_length=200):
        self.max_length = max_length
        self.char_to_idx = {}
        self.idx_to_char = {}
        self.vocab_size = 0

    def build_vocab(self, urls):
        logger.info("Building LSTM character vocabulary")

        chars = sorted(set("".join(urls)))
        self.char_to_idx = {c: i + 1 for i, c in enumerate(chars)}
        self.char_to_idx["<PAD>"] = 0

        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        self.vocab_size = len(self.char_to_idx)

        logger.info("LSTM vocab size: %d", self.vocab_size)

    def encode(self, url):
        encoded = [self.char_to_idx.get(c, 0) for c in url]
        return (encoded + [0] * self.max_length)[:self.max_length]

    def encode_batch(self, urls):
        return np.array([self.encode(u) for u in urls])

    # 🔥 THIS IS WHAT WAS MISSING AT RUNTIME
    def save_vocab(self, path):
        import json

        vocab_data = {
            "char_to_idx": self.char_to_idx,
            "max_length": self.max_length,
            "vocab_size": self.vocab_size,
        }

        with open(path, "w") as f:
            json.dump(vocab_data, f)

        logger.info("LSTM vocabulary saved to %s", path)

    def load_vocab(self, path):
        import json

        with open(path, "r") as f:
            vocab_data = json.load(f)

        self.char_to_idx = vocab_data["char_to_idx"]
        self.max_length = vocab_data["max_length"]
        self.vocab_size = vocab_data["vocab_size"]
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}

        logger.info("LSTM vocabulary loaded from %s", path)


def prepare_lstm_data(df, tokenizer: URLTokenizer):
    """
    Prepares X, y for LSTM training.

    Args:
        df: DataFrame with 'url' and 'label'
        tokenizer: fitted URLTokenizer

    Returns:
        X (np.ndarray), y (np.ndarray)
    """
    urls = df["url"].tolist()
    labels = df["label"].values

    X = tokenizer.encode_batch(urls)

    logger.info("LSTM data prepared: X=%s y=%s", X.shape, labels.shape)
    return X, labels


class URLDataset(torch.utils.data.Dataset):
    """PyTorch Dataset for LSTM."""

    def __init__(self, X, y):
        self.X = torch.LongTensor(X)
        self.y = torch.FloatTensor(y.copy())

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


# ============================================================
# CLI ENTRY POINT (preprocessing runner)
# ============================================================

if __name__ == "__main__":
    try:
        from .data_loader import load_and_sample_datasets
    except ImportError:
        from data_loader import load_and_sample_datasets

    PHISHING_PATH = "data/phishing_urls.csv"
    LEGIT_PATH = "data/legitimate_urls.csv"
    OUTPUT_PATH = "data/processed_feature.csv"

    logger.info("=" * 80)
    logger.info("URL PREPROCESSING PIPELINE")
    logger.info("=" * 80)

    df = load_and_sample_datasets(
        phishing_path=PHISHING_PATH,
        legitimate_path=LEGIT_PATH,
        num_phishing=50000,
        num_legitimate=50000,
    )

    processed_df = preprocess_dataset(df)
    processed_df.to_csv(OUTPUT_PATH, index=False)

    logger.info("Saved processed dataset to %s", OUTPUT_PATH)
    logger.info("Total rows saved: %d", len(processed_df))

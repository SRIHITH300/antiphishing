"""
Data loading utilities for phishing URL detection training pipeline.
"""
import pandas as pd
import numpy as np
from typing import Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_and_sample_datasets(
    phishing_path: str,
    legitimate_path: str,
    num_phishing: int,
    num_legitimate: int,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Load phishing and legitimate URL datasets, sample specified amounts,
    merge and shuffle them.
    
    Args:
        phishing_path: Path to phishing_urls.csv
        legitimate_path: Path to legitimate_urls.csv
        num_phishing: Number of phishing URLs to sample
        num_legitimate: Number of legitimate URLs to sample
        random_seed: Random seed for reproducibility
        
    Returns:
        Merged and shuffled DataFrame with 'url' and 'label' columns
        
    Raises:
        ValueError: If requested sample size exceeds dataset size
    """
    logger.info("Loading phishing URLs from %s", phishing_path)
    df_phishing = pd.read_csv(phishing_path)
    
    logger.info("Loading legitimate URLs from %s", legitimate_path)
    df_legitimate = pd.read_csv(legitimate_path)
    
    # Validate sample sizes
    if num_phishing > len(df_phishing):
        raise ValueError(
            f"Requested {num_phishing} phishing URLs but dataset only contains {len(df_phishing)}"
        )
    if num_legitimate > len(df_legitimate):
        raise ValueError(
            f"Requested {num_legitimate} legitimate URLs but dataset only contains {len(df_legitimate)}"
        )
    
    # Sample from each dataset
    np.random.seed(random_seed)
    logger.info("Sampling %d phishing URLs", num_phishing)
    sampled_phishing = df_phishing.sample(n=num_phishing, random_state=random_seed)
    
    logger.info("Sampling %d legitimate URLs", num_legitimate)
    sampled_legitimate = df_legitimate.sample(n=num_legitimate, random_state=random_seed)
    
    # Merge datasets
    logger.info("Merging and shuffling datasets")
    merged_df = pd.concat([sampled_phishing, sampled_legitimate], ignore_index=True)
    
    # Shuffle the merged dataset
    merged_df = merged_df.sample(frac=1, random_state=random_seed).reset_index(drop=True)
    
    logger.info(
        "Final dataset: %d total URLs (%d phishing, %d legitimate)",
        len(merged_df),
        num_phishing,
        num_legitimate
    )
    
    return merged_df


def load_processed_features(features_path: str) -> pd.DataFrame:
    """
    Load pre-processed feature dataset.
    
    Args:
        features_path: Path to processed_feature.csv
        
    Returns:
        DataFrame with URL features
    """
    logger.info("Loading processed features from %s", features_path)
    df_features = pd.read_csv(features_path)
    logger.info("Loaded %d feature records", len(df_features))
    return df_features


def align_features_with_urls(
    url_df: pd.DataFrame,
    features_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Align the sampled URLs with their corresponding features.
    
    Args:
        url_df: DataFrame with 'url' and 'label' columns
        features_df: DataFrame with features and 'url' column
        
    Returns:
        Merged DataFrame with URLs and their features
    """
    logger.info("Aligning URLs with features")
    
    # Merge on URL
    aligned_df = url_df.merge(features_df, on='url', how='inner', suffixes=('', '_feat'))
    
    # If there's a duplicate label column from features, use the one from url_df
    if 'label_feat' in aligned_df.columns:
        aligned_df = aligned_df.drop(columns=['label_feat'])
    
    logger.info("Aligned dataset contains %d records", len(aligned_df))
    
    if len(aligned_df) < len(url_df):
        logger.warning(
            "Lost %d URLs during alignment (features not found)",
            len(url_df) - len(aligned_df)
        )
    
    return aligned_df


def split_data(
    df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train, validation, and test sets.
    
    Args:
        df: Input DataFrame
        train_ratio: Proportion for training set
        val_ratio: Proportion for validation set
        test_ratio: Proportion for test set
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        "Ratios must sum to 1.0"
    
    # First split: train vs (val + test)
    train_df = df.sample(frac=train_ratio, random_state=random_seed)
    remaining_df = df.drop(train_df.index)
    
    # Second split: val vs test from remaining
    val_size = val_ratio / (val_ratio + test_ratio)
    val_df = remaining_df.sample(frac=val_size, random_state=random_seed)
    test_df = remaining_df.drop(val_df.index)
    
    logger.info(
        "Data split: train=%d, val=%d, test=%d",
        len(train_df),
        len(val_df),
        len(test_df)
    )
    
    return train_df, val_df, test_df

#added code block
"""
if __name__ == "__main__":
    print("=" * 80)
    print("DATA LOADER SANITY PIPELINE")
    print("=" * 80)

    try:
        df = load_and_sample_datasets(
            phishing_path="../data/phishing_urls.csv",
            legitimate_path="../data/legitimate_urls.csv",
            num_phishing=10,
            num_legitimate=10
        )

        print("\nSample loaded data:")
        print(df.head())
        print("\nShape:", df.shape)

    except Exception as e:
        print("ERROR:", e)
"""
from urllib.parse import urlparse


def extract_url_features(url: str) -> dict:
    """
    Extract numerical features from a URL.
    Matches feature columns used in preprocess.py
    """
    parsed = urlparse(url)
    hostname = parsed.netloc
    path = parsed.path

    return {
        "length_url": len(url),
        "length_hostname": len(hostname),

        "nb_dots": url.count("."),
        "nb_hyphens": url.count("-"),
        "nb_at": url.count("@"),
        "nb_qm": url.count("?"),
        "nb_and": url.count("&"),
        "nb_or": url.count("|"),
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

        "http_in_path": int("http" in path.lower()),
        "https_token": int("https" in url.lower()),

        "ratio_digits_url": sum(c.isdigit() for c in url) / max(len(url), 1),
        "ratio_digits_host": sum(c.isdigit() for c in hostname) / max(len(hostname), 1),
    }

if __name__ == "__main__":
    print("=" * 80)
    print("END-TO-END PREPROCESSING PIPELINE")
    print("=" * 80)

    PHISHING_PATH = "../data/phishing_urls.csv"
    LEGIT_PATH = "../data/legitimate_urls.csv"
    OUTPUT_PATH = "../data/processed_feature.csv"

    try:
        # 1️⃣ Load & sample datasets
        df = load_and_sample_datasets(
            phishing_path=PHISHING_PATH,
            legitimate_path=LEGIT_PATH,
            num_phishing=50000,
            num_legitimate=50000
        )

        print("Sampled URLs:", df.shape)

        # 2️⃣ Feature extraction
        feature_rows = []
        for _, row in df.iterrows():
            features = extract_url_features(row["url"])
            features["label"] = row["label"]
            features["url"] = row["url"]
            feature_rows.append(features)

        features_df = pd.DataFrame(feature_rows)

        # 3️⃣ Save processed dataset
        features_df.to_csv(OUTPUT_PATH, index=False)

        print("✅ processed_feature.csv GENERATED")
        print("Saved at:", OUTPUT_PATH)
        print("Shape:", features_df.shape)
        print("\nPreview:")
        print(features_df.head())

    except Exception as e:
        print("❌ PIPELINE FAILED")
        print("Error:", e)

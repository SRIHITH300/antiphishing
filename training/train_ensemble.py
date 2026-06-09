"""
Training script for Ensemble Meta-Model combining Decision Tree and LSTM.
"""
import os
import sys
import logging
import joblib
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from torch.utils.data import DataLoader

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import (
    load_and_sample_datasets,
    load_processed_features,
    align_features_with_urls,
    split_data
)
from utils.preprocess import (
    prepare_decision_tree_features,
    prepare_lstm_data,
    get_feature_columns,
    URLTokenizer,
    URLDataset
)
from utils.metrics import evaluate_and_save, print_metrics_comparison
from train_lstm import URLClassifierLSTM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================
NUM_PHISHING_URLS = 50000
NUM_LEGITIMATE_URLS = 50000
RANDOM_SEED = 42

DATA_DIR = 'data'
MODELS_DIR = 'models'
RESULTS_DIR = 'results'

PHISHING_PATH = os.path.join(DATA_DIR, 'phishing_urls.csv')
LEGITIMATE_PATH = os.path.join(DATA_DIR, 'legitimate_urls.csv')
FEATURES_PATH = os.path.join(DATA_DIR, 'processed_feature.csv')

DT_MODEL_PATH = os.path.join(MODELS_DIR, 'decision_tree_model.pkl')
LSTM_MODEL_PATH = os.path.join(MODELS_DIR, 'lstm_model.pt')
VOCAB_PATH = os.path.join(MODELS_DIR, 'url_vocab.json')
ENSEMBLE_MODEL_PATH = os.path.join(MODELS_DIR, 'ensemble_model.pkl')

# Ensemble meta-model choice: 'logistic' or 'xgboost'
META_MODEL_TYPE = 'xgboost'

# Device for LSTM
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BATCH_SIZE = 256

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_decision_tree_model(model_path: str):
    """Load trained Decision Tree model."""
    logger.info("Loading Decision Tree model from %s", model_path)
    model = joblib.load(model_path)
    return model


def load_lstm_model(model_path: str, vocab_size: int):
    """Load trained LSTM model."""
    logger.info("Loading LSTM model from %s", model_path)
    
    # Initialize model architecture
    model = URLClassifierLSTM(
        vocab_size=vocab_size,
        embedding_dim=128,
        hidden_dim=128,
        num_layers=2,
        dropout=0.3
    ).to(DEVICE)
    
    # Load weights
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    
    return model


def get_dt_predictions(model, X):
    """Get Decision Tree probability predictions."""
    probas = model.predict_proba(X)[:, 1]  # Probability of class 1 (phishing)
    return probas


def get_lstm_predictions(model, dataloader, device):
    """Get LSTM probability predictions."""
    model.eval()
    all_probs = []
    
    with torch.no_grad():
        for batch_X, _ in dataloader:
            batch_X = batch_X.to(device)
            outputs = model(batch_X)
            all_probs.extend(outputs.cpu().numpy())
    
    return np.array(all_probs)


# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def main():
    """Main training function for Ensemble Meta-Model."""
    logger.info("="*80)
    logger.info("ENSEMBLE META-MODEL TRAINING PIPELINE")
    logger.info("="*80)
    
    # Create directories
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Step 1: Load and sample datasets
    logger.info("\nStep 1: Loading and sampling datasets")
    logger.info("-" * 60)
    mixed_df = load_and_sample_datasets(
        PHISHING_PATH,
        LEGITIMATE_PATH,
        NUM_PHISHING_URLS,
        NUM_LEGITIMATE_URLS,
        RANDOM_SEED
    )
    
    # Step 2: Load processed features and align
    logger.info("\nStep 2: Loading and aligning features")
    logger.info("-" * 60)
    features_df = load_processed_features(FEATURES_PATH)
    aligned_df = align_features_with_urls(mixed_df, features_df)
    
    # Step 3: Split data
    logger.info("\nStep 3: Splitting data")
    logger.info("-" * 60)
    train_df, val_df, test_df = split_data(
        aligned_df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=RANDOM_SEED
    )
    
    # Step 4: Load pre-trained models
    logger.info("\nStep 4: Loading pre-trained models")
    logger.info("-" * 60)
    
    # Load Decision Tree
    dt_model = load_decision_tree_model(DT_MODEL_PATH)
    
    # Load LSTM
    tokenizer = URLTokenizer(max_length=200)
    tokenizer.load_vocab(VOCAB_PATH)
    lstm_model = load_lstm_model(LSTM_MODEL_PATH, tokenizer.vocab_size)
    
    # Step 5: Generate predictions from base models
    logger.info("\nStep 5: Generating predictions from base models")
    logger.info("-" * 60)
    
    feature_columns = get_feature_columns()
    
    # Validation set predictions
    logger.info("Generating validation predictions...")
    X_val_dt, y_val = prepare_decision_tree_features(val_df, feature_columns)
    X_val_lstm, _ = prepare_lstm_data(val_df, tokenizer)
    
    val_dataset = URLDataset(X_val_lstm, y_val)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    val_dt_probs = get_dt_predictions(dt_model, X_val_dt)
    val_lstm_probs = get_lstm_predictions(lstm_model, val_loader, DEVICE)
    
    # Stack predictions as meta-features
    X_val_meta = np.column_stack([val_dt_probs, val_lstm_probs])
    
    # Test set predictions
    logger.info("Generating test predictions...")
    X_test_dt, y_test = prepare_decision_tree_features(test_df, feature_columns)
    X_test_lstm, _ = prepare_lstm_data(test_df, tokenizer)
    
    test_dataset = URLDataset(X_test_lstm, y_test)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    test_dt_probs = get_dt_predictions(dt_model, X_test_dt)
    test_lstm_probs = get_lstm_predictions(lstm_model, test_loader, DEVICE)
    
    X_test_meta = np.column_stack([test_dt_probs, test_lstm_probs])
    
    logger.info("Meta-features shape - Val: %s, Test: %s", X_val_meta.shape, X_test_meta.shape)
    
    # Step 6: Train meta-model
    logger.info("\nStep 6: Training meta-model (%s)", META_MODEL_TYPE)
    logger.info("-" * 60)
    
    if META_MODEL_TYPE == 'logistic':
        meta_model = LogisticRegression(
            random_state=RANDOM_SEED,
            max_iter=1000
        )
    elif META_MODEL_TYPE == 'xgboost':
        meta_model = XGBClassifier(
            random_state=RANDOM_SEED,
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            eval_metric='logloss'
        )
    else:
        raise ValueError(f"Unknown meta-model type: {META_MODEL_TYPE}")
    
    meta_model.fit(X_val_meta, y_val)
    logger.info("Meta-model training completed")
    
    # Step 7: Evaluate ensemble on test set
    logger.info("\nStep 7: Evaluating ensemble on test set")
    logger.info("-" * 60)
    
    y_pred_ensemble = meta_model.predict(X_test_meta)
    y_pred_proba_ensemble = meta_model.predict_proba(X_test_meta)[:, 1]
    
    # Comprehensive evaluation
    ensemble_metrics = evaluate_and_save(
        y_test,
        y_pred_ensemble,
        y_pred_proba_ensemble,
        model_name='ensemble',
        results_dir=RESULTS_DIR
    )
    
    # Step 8: Save ensemble model
    logger.info("\nStep 8: Saving ensemble model")
    logger.info("-" * 60)
    joblib.dump(meta_model, ENSEMBLE_MODEL_PATH)
    logger.info("Ensemble model saved to %s", ENSEMBLE_MODEL_PATH)
    
    # Step 9: Compare all models
    logger.info("\nStep 9: Model comparison")
    logger.info("-" * 60)
    
    # Evaluate base models on test set for comparison
    y_pred_dt = (test_dt_probs > 0.5).astype(int)
    y_pred_lstm = (test_lstm_probs > 0.5).astype(int)
    
    # Load existing metrics if available, otherwise compute
    import json
    
    dt_metrics_path = os.path.join(RESULTS_DIR, 'metrics_decision_tree.json')
    lstm_metrics_path = os.path.join(RESULTS_DIR, 'metrics_lstm.json')
    
    try:
        with open(dt_metrics_path, 'r') as f:
            dt_metrics = json.load(f)
    except FileNotFoundError:
        logger.warning("Decision Tree metrics not found, computing...")
        from utils.metrics import compute_all_metrics
        dt_metrics = compute_all_metrics(y_test, y_pred_dt, test_dt_probs)
    
    try:
        with open(lstm_metrics_path, 'r') as f:
            lstm_metrics = json.load(f)
    except FileNotFoundError:
        logger.warning("LSTM metrics not found, computing...")
        from utils.metrics import compute_all_metrics
        lstm_metrics = compute_all_metrics(y_test, y_pred_lstm, test_lstm_probs)
    
    # Print comparison
    all_metrics = {
        'Decision_Tree': dt_metrics,
        'LSTM': lstm_metrics,
        'Ensemble': ensemble_metrics
    }
    
    print_metrics_comparison(all_metrics)
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("ENSEMBLE TRAINING COMPLETED")
    logger.info("="*80)
    logger.info("Ensemble Test Accuracy: %.4f", ensemble_metrics['accuracy'])
    logger.info("Ensemble Test F1-Macro: %.4f", ensemble_metrics['f1_macro'])
    logger.info("Ensemble Test ROC-AUC: %.4f", ensemble_metrics['roc_auc'])
    logger.info("Ensemble Test PR-AUC: %.4f", ensemble_metrics['pr_auc'])
    logger.info("="*80)
    
    # Show improvement
    logger.info("\nImprovement over base models:")
    logger.info("vs Decision Tree: +%.2f%% F1-Macro", 
                (ensemble_metrics['f1_macro'] - dt_metrics['f1_macro']) * 100)
    logger.info("vs LSTM: +%.2f%% F1-Macro", 
                (ensemble_metrics['f1_macro'] - lstm_metrics['f1_macro']) * 100)


if __name__ == '__main__':
    main()
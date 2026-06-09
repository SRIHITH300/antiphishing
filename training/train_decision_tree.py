"""
Training script for Decision Tree classifier on engineered URL features.
"""
import os
import sys
import logging
import joblib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import (
    load_and_sample_datasets,
    load_processed_features,
    align_features_with_urls,
    split_data
)
from utils.preprocess import prepare_decision_tree_features, get_feature_columns
from utils.metrics import evaluate_and_save

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

MODEL_PATH = os.path.join(MODELS_DIR, 'decision_tree_model.pkl')

# GridSearch parameters
GRID_PARAMS = {
    'max_depth': [10, 20, 30, None],
    'min_samples_split': [2, 5, 10],
    'criterion': ['gini', 'entropy']
}

# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def main():
    """Main training function for Decision Tree."""
    logger.info("="*80)
    logger.info("DECISION TREE TRAINING PIPELINE")
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
    
    # Step 2: Load processed features
    logger.info("\nStep 2: Loading processed features")
    logger.info("-" * 60)
    features_df = load_processed_features(FEATURES_PATH)
    
    # Step 3: Align URLs with features
    logger.info("\nStep 3: Aligning URLs with features")
    logger.info("-" * 60)
    aligned_df = align_features_with_urls(mixed_df, features_df)
    
    # Step 4: Split data
    logger.info("\nStep 4: Splitting data into train/val/test")
    logger.info("-" * 60)
    train_df, val_df, test_df = split_data(
        aligned_df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=RANDOM_SEED
    )
    
    # Step 5: Prepare features
    logger.info("\nStep 5: Preparing features")
    logger.info("-" * 60)
    feature_columns = get_feature_columns()
    
    X_train, y_train = prepare_decision_tree_features(train_df, feature_columns)
    X_val, y_val = prepare_decision_tree_features(val_df, feature_columns)
    X_test, y_test = prepare_decision_tree_features(test_df, feature_columns)
    
    logger.info("Training set: %d samples", len(X_train))
    logger.info("Validation set: %d samples", len(X_val))
    logger.info("Test set: %d samples", len(X_test))
    
    # Step 6: Train with GridSearchCV
    logger.info("\nStep 6: Training Decision Tree with GridSearchCV")
    logger.info("-" * 60)
    logger.info("Grid parameters: %s", GRID_PARAMS)
    
    base_model = DecisionTreeClassifier(random_state=RANDOM_SEED)
    
    grid_search = GridSearchCV(
        base_model,
        GRID_PARAMS,
        cv=5,
        scoring='f1_macro',
        n_jobs=-1,
        verbose=2
    )
    
    grid_search.fit(X_train, y_train)
    
    logger.info("Best parameters: %s", grid_search.best_params_)
    logger.info("Best CV F1-macro score: %.4f", grid_search.best_score_)
    
    # Get best model
    best_model = grid_search.best_estimator_
    
    # Step 7: Evaluate on test set
    logger.info("\nStep 7: Evaluating on test set")
    logger.info("-" * 60)
    
    # Predictions
    y_pred = best_model.predict(X_test)
    y_pred_proba = best_model.predict_proba(X_test)[:, 1]
    
    # Comprehensive evaluation
    metrics = evaluate_and_save(
        y_test,
        y_pred,
        y_pred_proba,
        model_name='decision_tree',
        results_dir=RESULTS_DIR
    )
    
    # Step 8: Save model
    logger.info("\nStep 8: Saving model")
    logger.info("-" * 60)
    joblib.dump(best_model, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("DECISION TREE TRAINING COMPLETED")
    logger.info("="*80)
    logger.info("Test Accuracy: %.4f", metrics['accuracy'])
    logger.info("Test F1-Macro: %.4f", metrics['f1_macro'])
    logger.info("Test ROC-AUC: %.4f", metrics['roc_auc'])
    logger.info("Test PR-AUC: %.4f", metrics['pr_auc'])
    logger.info("="*80)


if __name__ == '__main__':
    main()
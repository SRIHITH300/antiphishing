"""
Comprehensive evaluation metrics for model performance.
"""
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, roc_curve, precision_recall_curve
)
from typing import Dict, Tuple
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 8)


def compute_specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute specificity (True Negative Rate).
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        Specificity score
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return specificity


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: np.ndarray
) -> Dict:
    """
    Compute comprehensive evaluation metrics.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels (binary)
        y_pred_proba: Predicted probabilities for positive class
        
    Returns:
        Dictionary containing all metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # Per-class metrics
    precision_per_class = precision_score(y_true, y_pred, average=None)
    recall_per_class = recall_score(y_true, y_pred, average=None)
    f1_per_class = f1_score(y_true, y_pred, average=None)
    
    metrics['precision_class_0'] = float(precision_per_class[0])
    metrics['precision_class_1'] = float(precision_per_class[1])
    metrics['recall_class_0'] = float(recall_per_class[0])
    metrics['recall_class_1'] = float(recall_per_class[1])
    metrics['f1_class_0'] = float(f1_per_class[0])
    metrics['f1_class_1'] = float(f1_per_class[1])
    
    # Macro-averaged metrics
    metrics['precision_macro'] = float(precision_score(y_true, y_pred, average='macro'))
    metrics['recall_macro'] = float(recall_score(y_true, y_pred, average='macro'))
    metrics['f1_macro'] = float(f1_score(y_true, y_pred, average='macro'))
    
    # Weighted-averaged metrics
    metrics['precision_weighted'] = float(precision_score(y_true, y_pred, average='weighted'))
    metrics['recall_weighted'] = float(recall_score(y_true, y_pred, average='weighted'))
    metrics['f1_weighted'] = float(f1_score(y_true, y_pred, average='weighted'))
    
    # ROC-AUC and PR-AUC
    metrics['roc_auc'] = float(roc_auc_score(y_true, y_pred_proba))
    metrics['pr_auc'] = float(average_precision_score(y_true, y_pred_proba))
    
    # Specificity
    metrics['specificity'] = float(compute_specificity(y_true, y_pred))
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics['confusion_matrix'] = {
        'tn': int(cm[0, 0]),
        'fp': int(cm[0, 1]),
        'fn': int(cm[1, 0]),
        'tp': int(cm[1, 1])
    }
    
    return metrics


def save_metrics(metrics: Dict, output_path: str) -> None:
    """
    Save metrics to JSON file.
    
    Args:
        metrics: Dictionary of metrics
        output_path: Path to save JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics saved to %s", output_path)


def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: str,
    title: str = "Confusion Matrix"
) -> None:
    """
    Plot and save confusion matrix.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        output_path: Path to save plot
        title: Plot title
    """
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['Legitimate', 'Phishing'],
        yticklabels=['Legitimate', 'Phishing']
    )
    plt.title(title, fontsize=16, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Confusion matrix saved to %s", output_path)


def plot_roc_curve(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    output_path: str,
    title: str = "ROC Curve"
) -> None:
    """
    Plot and save ROC curve.
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities for positive class
        output_path: Path to save plot
        title: Plot title
    """
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    auc_score = roc_auc_score(y_true, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, linewidth=2, label=f'ROC curve (AUC = {auc_score:.4f})')
    plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("ROC curve saved to %s", output_path)


def plot_precision_recall_curve(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    output_path: str,
    title: str = "Precision-Recall Curve"
) -> None:
    """
    Plot and save Precision-Recall curve.
    
    Args:
        y_true: True labels
        y_pred_proba: Predicted probabilities for positive class
        output_path: Path to save plot
        title: Plot title
    """
    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    pr_auc = average_precision_score(y_true, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, linewidth=2, label=f'PR curve (AUC = {pr_auc:.4f})')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall', fontsize=12)
    plt.ylabel('Precision', fontsize=12)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.legend(loc='lower left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Precision-Recall curve saved to %s", output_path)


def evaluate_and_save(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_pred_proba: np.ndarray,
    model_name: str,
    results_dir: str = 'results'
) -> Dict:
    """
    Comprehensive evaluation: compute metrics and save all plots.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Predicted probabilities
        model_name: Name of the model (for file naming)
        results_dir: Directory to save results
        
    Returns:
        Dictionary of computed metrics
    """
    logger.info("Evaluating model: %s", model_name)
    
    # Compute all metrics
    metrics = compute_all_metrics(y_true, y_pred, y_pred_proba)
    
    # Save metrics JSON
    metrics_path = os.path.join(results_dir, f'metrics_{model_name}.json')
    save_metrics(metrics, metrics_path)
    
    # Plot and save confusion matrix
    cm_path = os.path.join(results_dir, f'confusion_matrix_{model_name}.png')
    plot_confusion_matrix(y_true, y_pred, cm_path, f'{model_name} - Confusion Matrix')
    
    # Plot and save ROC curve
    roc_path = os.path.join(results_dir, f'roc_curve_{model_name}.png')
    plot_roc_curve(y_true, y_pred_proba, roc_path, f'{model_name} - ROC Curve')
    
    # Plot and save Precision-Recall curve
    pr_path = os.path.join(results_dir, f'pr_curve_{model_name}.png')
    plot_precision_recall_curve(y_true, y_pred_proba, pr_path, f'{model_name} - PR Curve')
    
    # Print classification report
    logger.info("\n" + "="*60)
    logger.info("Classification Report for %s", model_name)
    logger.info("="*60)
    print(classification_report(
        y_true, y_pred,
        target_names=['Legitimate', 'Phishing'],
        digits=4
    ))
    
    return metrics


def print_metrics_comparison(metrics_dict: Dict[str, Dict]) -> None:
    """
    Print comparison table of metrics across models.
    
    Args:
        metrics_dict: Dictionary mapping model names to their metrics
    """
    logger.info("\n" + "="*80)
    logger.info("MODEL COMPARISON")
    logger.info("="*80)
    
    metric_names = [
        'accuracy', 'precision_macro', 'recall_macro', 'f1_macro',
        'roc_auc', 'pr_auc', 'specificity'
    ]
    
    # Print header
    header = f"{'Metric':<20}"
    for model_name in metrics_dict.keys():
        header += f"{model_name:>15}"
    print(header)
    print("-" * 80)
    
    # Print each metric
    for metric in metric_names:
        row = f"{metric:<20}"
        for model_name in metrics_dict.keys():
            value = metrics_dict[model_name].get(metric, 0.0)
            row += f"{value:>15.4f}"
        print(row)
    
    print("=" * 80)

#added code block

if __name__ == "__main__":
    print("=" * 80)
    print("METRICS SANITY PIPELINE")
    print("=" * 80)

    y_true = np.array([0, 0, 1, 1, 1])
    y_pred = np.array([0, 1, 1, 1, 0])
    y_pred_proba = np.array([0.1, 0.7, 0.9, 0.8, 0.3])

    metrics = compute_all_metrics(y_true, y_pred, y_pred_proba)

    print("\nComputed Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

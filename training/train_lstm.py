"""
Training script for LSTM classifier on raw URL sequences.
"""
import os
import sys
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm import tqdm

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import load_and_sample_datasets, split_data
from utils.preprocess import URLTokenizer, prepare_lstm_data, URLDataset
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

MODEL_PATH = os.path.join(MODELS_DIR, 'lstm_model.pt')
VOCAB_PATH = os.path.join(MODELS_DIR, 'url_vocab.json')

# LSTM hyperparameters
MAX_URL_LENGTH = 200
EMBEDDING_DIM = 128
HIDDEN_DIM = 128
NUM_LAYERS = 2
DROPOUT = 0.3

# Training hyperparameters
BATCH_SIZE = 256
NUM_EPOCHS = 10
LEARNING_RATE = 0.001
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ============================================================================
# LSTM MODEL DEFINITION
# ============================================================================

class URLClassifierLSTM(nn.Module):
    """LSTM-based URL classifier."""
    
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        """
        Initialize LSTM model.
        
        Args:
            vocab_size: Size of character vocabulary
            embedding_dim: Dimension of character embeddings
            hidden_dim: LSTM hidden dimension
            num_layers: Number of LSTM layers
            dropout: Dropout rate
        """
        super(URLClassifierLSTM, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=False
        )
        
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        """Forward pass."""
        # x: (batch_size, seq_len)
        embedded = self.embedding(x)  # (batch_size, seq_len, embedding_dim)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Use last hidden state
        last_hidden = hidden[-1]  # (batch_size, hidden_dim)
        
        # Dropout and classification
        dropped = self.dropout(last_hidden)
        logits = self.fc(dropped)  # (batch_size, 1)
        output = self.sigmoid(logits).squeeze()  # (batch_size,)
        
        return output


# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================

def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc='Training')
    for batch_X, batch_y in pbar:
        batch_X = batch_X.to(device)
        batch_y = batch_y.to(device)
        
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        predictions = (outputs > 0.5).float()
        correct += (predictions == batch_y).sum().item()
        total += batch_y.size(0)
        
        pbar.set_postfix({'loss': loss.item(), 'acc': correct/total})
    
    avg_loss = total_loss / len(dataloader)
    accuracy = correct / total
    return avg_loss, accuracy


def evaluate_epoch(model, dataloader, criterion, device):
    """Evaluate model."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for batch_X, batch_y in dataloader:
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)
            
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            total_loss += loss.item()
            predictions = (outputs > 0.5).float()
            correct += (predictions == batch_y).sum().item()
            total += batch_y.size(0)
            
            all_preds.extend(predictions.cpu().numpy())
            all_probs.extend(outputs.cpu().numpy())
            all_labels.extend(batch_y.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    accuracy = correct / total
    
    return avg_loss, accuracy, np.array(all_preds), np.array(all_probs), np.array(all_labels)


# ============================================================================
# MAIN TRAINING PIPELINE
# ============================================================================

def main():
    """Main training function for LSTM."""
    logger.info("="*80)
    logger.info("LSTM TRAINING PIPELINE")
    logger.info("="*80)
    logger.info("Device: %s", DEVICE)
    
    # Create directories
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Set random seeds
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(RANDOM_SEED)
    
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
    
    # Step 2: Split data
    logger.info("\nStep 2: Splitting data into train/val/test")
    logger.info("-" * 60)
    train_df, val_df, test_df = split_data(
        mixed_df,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        random_seed=RANDOM_SEED
    )
    
    # Step 3: Build vocabulary and tokenize
    logger.info("\nStep 3: Building vocabulary and tokenizing URLs")
    logger.info("-" * 60)
    tokenizer = URLTokenizer(max_length=MAX_URL_LENGTH)
    tokenizer.build_vocab(mixed_df['url'].tolist())
    tokenizer.save_vocab(VOCAB_PATH)
    
    # Prepare data
    X_train, y_train = prepare_lstm_data(train_df, tokenizer)
    X_val, y_val = prepare_lstm_data(val_df, tokenizer)
    X_test, y_test = prepare_lstm_data(test_df, tokenizer)
    
    # Create datasets and dataloaders
    train_dataset = URLDataset(X_train, y_train)
    val_dataset = URLDataset(X_val, y_val)
    test_dataset = URLDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    logger.info("Training batches: %d", len(train_loader))
    logger.info("Validation batches: %d", len(val_loader))
    logger.info("Test batches: %d", len(test_loader))
    
    # Step 4: Initialize model
    logger.info("\nStep 4: Initializing LSTM model")
    logger.info("-" * 60)
    model = URLClassifierLSTM(
        vocab_size=tokenizer.vocab_size,
        embedding_dim=EMBEDDING_DIM,
        hidden_dim=HIDDEN_DIM,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT
    ).to(DEVICE)
    
    total_params = sum(p.numel() for p in model.parameters())
    logger.info("Total parameters: %d", total_params)
    
    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Step 5: Training loop
    logger.info("\nStep 5: Training LSTM")
    logger.info("-" * 60)
    
    best_val_loss = float('inf')
    patience = 3
    patience_counter = 0
    
    for epoch in range(NUM_EPOCHS):
        logger.info(f"\nEpoch {epoch+1}/{NUM_EPOCHS}")
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
        
        # Validate
        val_loss, val_acc, _, _, _ = evaluate_epoch(model, val_loader, criterion, DEVICE)
        
        logger.info(
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
        )
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), MODEL_PATH)
            logger.info("Model saved (best validation loss)")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping triggered")
                break
    
    # Step 6: Load best model and evaluate on test set
    logger.info("\nStep 6: Evaluating on test set")
    logger.info("-" * 60)
    
    model.load_state_dict(torch.load(MODEL_PATH))
    test_loss, test_acc, y_pred, y_pred_proba, y_true = evaluate_epoch(
        model, test_loader, criterion, DEVICE
    )
    
    logger.info(f"Test Loss: {test_loss:.4f}, Test Acc: {test_acc:.4f}")
    
    # Comprehensive evaluation
    metrics = evaluate_and_save(
        y_true,
        y_pred,
        y_pred_proba,
        model_name='lstm',
        results_dir=RESULTS_DIR
    )
    
    # Final summary
    logger.info("\n" + "="*80)
    logger.info("LSTM TRAINING COMPLETED")
    logger.info("="*80)
    logger.info("Test Accuracy: %.4f", metrics['accuracy'])
    logger.info("Test F1-Macro: %.4f", metrics['f1_macro'])
    logger.info("Test ROC-AUC: %.4f", metrics['roc_auc'])
    logger.info("Test PR-AUC: %.4f", metrics['pr_auc'])
    logger.info("="*80)


if __name__ == '__main__':
    main()
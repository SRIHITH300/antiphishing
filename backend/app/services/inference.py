
import pickle
import json
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import Dict, List
import logging
import joblib  

from app.services.url_utils import extract_features, get_feature_columns
from app.core.config import settings

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    
    
    def __init__(self, vocab_size: int, embedding_dim: int = 128, hidden_dim: int = 128, num_layers: int = 2):
        super(LSTMModel, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.3 if num_layers > 1 else 0,
            bidirectional=False
        )
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, (hidden, cell) = self.lstm(embedded)
        last_hidden = hidden[-1]
        dropped = self.dropout(last_hidden)
        output = self.fc(dropped)
        return self.sigmoid(output)


class ModelInference:
    
    
    def __init__(self, dt_model_path: Path, lstm_model_path: Path, 
                 ensemble_model_path: Path, vocab_path: Path):

        self.device = torch.device('cuda' if torch.cuda.is_available() and settings.USE_GPU else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # ✅ FIXED: Load Decision Tree with joblib
        logger.info("Loading Decision Tree model...")
        self.dt_model = joblib.load(dt_model_path)
        logger.info("✓ Decision Tree loaded")
        
        # Load vocabulary
        logger.info("Loading vocabulary...")
        with open(vocab_path, 'r') as f:
            vocab_data = json.load(f)
        
        if isinstance(vocab_data, dict) and 'char_to_idx' in vocab_data:
            self.vocab = vocab_data['char_to_idx']
            self.max_length = vocab_data.get('max_length', 200)
        else:
            self.vocab = vocab_data
            self.max_length = 200
        
        self.vocab_size = len(self.vocab)
        logger.info(f"✓ Vocabulary loaded (size: {self.vocab_size})")
        
        # Load LSTM
        logger.info("Loading LSTM model...")
        self.lstm_model = LSTMModel(vocab_size=self.vocab_size)
        self.lstm_model.load_state_dict(torch.load(lstm_model_path, map_location=self.device))
        self.lstm_model.to(self.device)
        self.lstm_model.eval()
        logger.info("✓ LSTM loaded")
        
        # Load Ensemble (unchanged)
        logger.info("Loading Ensemble model...")
        with open(ensemble_model_path, 'rb') as f:
            self.ensemble_model = pickle.load(f)
        logger.info("✓ Ensemble model loaded")
        
        # Feature columns
        self.feature_columns = get_feature_columns()
        logger.info(f"✓ Feature columns loaded ({len(self.feature_columns)} features)")
    
    def predict(self, url: str) -> Dict:
        try:
            features = extract_features(url)
            feature_vector = self._features_to_vector(features)
            
            dt_prob = self.dt_model.predict_proba([feature_vector])[0][1]
            
            tokens = self._tokenize_url(url)
            
            with torch.no_grad():
                lstm_input = torch.tensor([tokens], dtype=torch.long).to(self.device)
                lstm_prob = self.lstm_model(lstm_input).cpu().item()
            
            ensemble_input = np.array([[dt_prob, lstm_prob]])
            final_prob = self.ensemble_model.predict_proba(ensemble_input)[0][1]
            is_phishing = final_prob >= settings.CONFIDENCE_THRESHOLD
            
            return {
                'is_phishing': bool(is_phishing),
                'confidence': float(final_prob),
                'details': {
                    'dt_score': float(dt_prob),
                    'lstm_score': float(lstm_prob),
                    'ensemble_score': float(final_prob)
                }
            }
            
        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            return {
                'is_phishing': False,
                'confidence': 0.5,
                'details': {'error': str(e)}
            }
    
    def _features_to_vector(self, features: Dict[str, float]) -> List[float]:
        return [features.get(col, 0.0) for col in self.feature_columns]
    
    def _tokenize_url(self, url: str) -> List[int]:
        tokens = []
        for char in url[:self.max_length]:
            token = self.vocab.get(char, self.vocab.get('<PAD>', 0))
            tokens.append(token)
        
        if len(tokens) < self.max_length:
            tokens.extend([0] * (self.max_length - len(tokens)))
        else:
            tokens = tokens[:self.max_length]
        
        return tokens

# Model Files Directory

This directory should contain your trained models:

## Required Files:

1. **decision_tree_model.pkl**
   - Scikit-learn Decision Tree classifier
   - Trained on engineered URL features
   - Should output probability for phishing class

2. **lstm_model.pt**
   - PyTorch LSTM model state dict
   - Character-level sequence model
   - Architecture: Embedding -> Bidirectional LSTM -> FC -> Sigmoid
   - Input: Tokenized URL sequences (max length 200)

3. **ensemble_model.pkl**
   - XGBoost or Logistic Regression meta-model
   - Takes [dt_prob, lstm_prob] as input
   - Outputs final phishing probability

4. **vocab.json**
   - Character to index mapping
   - Format: {"char": index, ...}
   - Must include '<PAD>' at index 0 and '<UNK>' at index 1
   - Example:
     {
       "<PAD>": 0,
       "<UNK>": 1,
       "a": 2,
       "b": 3,
       ...
     }

## Model Architecture Requirements:

### LSTM Model Structure:
- Input: Character indices (batch_size, seq_length)
- Embedding layer (vocab_size, 128)
- Bidirectional LSTM (2 layers, hidden_dim=256, dropout=0.3)
- Dropout (0.5)
- Fully connected (hidden_dim*2 -> 1)
- Sigmoid activation

### Feature Order (Decision Tree):
The feature extraction must produce features in this exact order:
1. url_length
2. hostname_length
3. path_length
4. num_dots
5. num_hyphens
6. num_underscores
7. num_slashes
8. num_question_marks
9. num_equal_signs
10. num_at_symbols
11. num_ampersands
12. num_exclamation_marks
13. num_hashtags
14. num_percent_signs
15. num_digits
16. digit_ratio
17. num_subdomains
18. is_https
19. has_ip_address
20. has_port
21. num_path_segments
22. has_query_params
23. entropy
24. num_suspicious_keywords
25. tld_length
26. special_char_ratio

## Important Notes:

- Models must be saved in inference mode (no training code)
- LSTM model should be saved using: `torch.save(model.state_dict(), 'lstm_model.pt')`
- Pickle files (DT and ensemble) should use protocol 4 or higher
- Vocabulary must be consistent with training
- All models must produce probability outputs (0.0 to 1.0)

## Testing Your Models:

Before deploying, verify:
1. All files are present and loadable
2. Feature extraction matches training
3. Vocabulary covers common URL characters
4. Inference runs without errors
5. Output format is consistent

Place your trained model files in this directory before running the application.

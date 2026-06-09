
import re
from urllib.parse import urlparse
from typing import Dict


def extract_features(url: str) -> Dict[str, float]:
 
    features = {}
    
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc
        path = parsed.path
        
        # EXACT MATCH TO TRAINING CODE (preprocess.py)
        # DO NOT MODIFY - these must match training exactly!
        
        features['length_url'] = len(url)
        features['length_hostname'] = len(hostname)
        features['nb_dots'] = url.count('.')
        features['nb_hyphens'] = url.count('-')
        features['nb_at'] = url.count('@')
        features['nb_qm'] = url.count('?')
        features['nb_and'] = url.count('&')
        features['nb_or'] = url.lower().count('or')  # ← CRITICAL FIX: substring, not "|"!
        features['nb_eq'] = url.count('=')
        features['nb_underscore'] = url.count('_')
        features['nb_tilde'] = url.count('~')
        features['nb_percent'] = url.count('%')
        features['nb_slash'] = url.count('/')
        features['nb_star'] = url.count('*')
        features['nb_colon'] = url.count(':')
        features['nb_comma'] = url.count(',')
        features['nb_semicolumn'] = url.count(';')
        features['nb_dollar'] = url.count('$')
        features['nb_space'] = url.count(' ')
        features['nb_www'] = url.lower().count('www')
        features['nb_com'] = url.lower().count('.com')
        features['nb_dslash'] = url.count('//')
        features['http_in_path'] = int('http' in path.lower())
        features['https_token'] = int('https' in url.lower())
        features['ratio_digits_url'] = sum(c.isdigit() for c in url) / max(len(url), 1)
        features['ratio_digits_host'] = sum(c.isdigit() for c in hostname) / max(len(hostname), 1)
        
    except Exception as e:
        # On error, return safe defaults
        features = _get_default_features()
    
    return features


def _get_default_features() -> Dict[str, float]:
    
    return {
        'length_url': 0.0,
        'length_hostname': 0.0,
        'nb_dots': 0.0,
        'nb_hyphens': 0.0,
        'nb_at': 0.0,
        'nb_qm': 0.0,
        'nb_and': 0.0,
        'nb_or': 0.0,
        'nb_eq': 0.0,
        'nb_underscore': 0.0,
        'nb_tilde': 0.0,
        'nb_percent': 0.0,
        'nb_slash': 0.0,
        'nb_star': 0.0,
        'nb_colon': 0.0,
        'nb_comma': 0.0,
        'nb_semicolumn': 0.0,
        'nb_dollar': 0.0,
        'nb_space': 0.0,
        'nb_www': 0.0,
        'nb_com': 0.0,
        'nb_dslash': 0.0,
        'http_in_path': 0.0,
        'https_token': 0.0,
        'ratio_digits_url': 0.0,
        'ratio_digits_host': 0.0
    }


def get_feature_columns():
    
    return [
        'length_url',
        'length_hostname',
        'nb_dots',
        'nb_hyphens',
        'nb_at',
        'nb_qm',
        'nb_and',
        'nb_or',
        'nb_eq',
        'nb_underscore',
        'nb_tilde',
        'nb_percent',
        'nb_slash',
        'nb_star',
        'nb_colon',
        'nb_comma',
        'nb_semicolumn',
        'nb_dollar',
        'nb_space',
        'nb_www',
        'nb_com',
        'nb_dslash',
        'http_in_path',
        'https_token',
        'ratio_digits_url',
        'ratio_digits_host'
    ]
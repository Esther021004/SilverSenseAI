# modules/module_b_sound.py
# B-Module — Sound Analyzer
# 독립 모듈: 다른 모듈과 import 금지

import os
import librosa
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional

# ==========================================
# 모델 정의 (SimpleCNN)
# ==========================================
class SimpleCNN(nn.Module):
    def __init__(self, n_classes=4):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(16)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(32)
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn3   = nn.BatchNorm2d(64)

        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.3)
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(64, n_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))
        x = self.pool(F.relu(self.bn2(self.conv2(x))))
        x = self.pool(F.relu(self.bn3(self.conv3(x))))
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.fc(x)
        return x


# ==========================================
# 전역 변수 (모델 로드)
# ==========================================
CLASS_TO_IDX = {
    "낙상": 0,
    "화재": 1,
    "갇힘": 2,
    "생활소음": 3,
}

idx_to_class = {v: k for k, v in CLASS_TO_IDX.items()}

# 모델 경로 (프로젝트 루트 기준)
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "aed_cnn_final_trainaug_fin.pth"
)

# 오디오 전처리 파라미터
SR = 16000
DURATION = 2.0
N_MELS = 64
N_FFT = 1024
HOP_LENGTH = 512

# 모델 로드 (한 번만 로드)
_model = None
_device = None


def _load_model():
    """모델을 한 번만 로드 (lazy loading)"""
    global _model, _device
    
    if _model is None:
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = SimpleCNN(n_classes=4).to(_device)
        
        if os.path.exists(MODEL_PATH):
            _model.load_state_dict(torch.load(MODEL_PATH, map_location=_device))
            _model.eval()
            print(f"✅ B 모듈: 모델 로드 완료 ({MODEL_PATH})")
        else:
            print(f"⚠️  B 모듈: 모델 파일을 찾을 수 없습니다 ({MODEL_PATH})")
            print("   더미 모드로 동작합니다.")
    
    return _model, _device


# ==========================================
# 오디오 전처리 함수
# ==========================================
def wav_to_logmel_infer(wav_path: str) -> np.ndarray:
    """
    WAV 파일을 log-mel spectrogram으로 변환 (추론용, augmentation 없음)
    """
    y, sr = librosa.load(wav_path, sr=SR, mono=True)

    # 길이 고정 (2초)
    target_len = int(SR * DURATION)
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)), mode="constant")
    else:
        y = y[:target_len]

    # mel-spectrogram
    mel = librosa.feature.melspectrogram(
        y=y, sr=SR, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS
    )

    # log scale (dB)
    log_mel = librosa.power_to_db(mel, ref=np.max)

    # 표준화
    log_mel = (log_mel - log_mel.mean()) / (log_mel.std() + 1e-6)

    return log_mel.astype(np.float32)


# ==========================================
# 모델 추론 함수
# ==========================================
def predict_audio_event(wav_path: str) -> Dict:
    """
    WAV 파일 경로를 받아서 모델로 추론 후 결과 반환
    
    Input: wav 파일 경로
    Output: {
        "event": str,        # "낙상", "화재", "갇힘", "생활소음"
        "confidence": float  # 0.0 ~ 1.0
    }
    """
    model, device = _load_model()
    
    # 모델 파일이 없으면 더미 반환
    if not os.path.exists(MODEL_PATH):
        return {
            "event": "생활소음",
            "confidence": 0.5
        }
    
    try:
        # 1) wav → logmel
        log_mel = wav_to_logmel_infer(wav_path)
        x = torch.tensor(log_mel, dtype=torch.float32).unsqueeze(0).unsqueeze(0)  # (1,1,64,T)
        x = x.to(device)

        # 2) forward
        with torch.no_grad():
            outputs = model(x)
            probs = torch.softmax(outputs, dim=1)[0].cpu().numpy()

        # 3) 결과 정리
        top_idx = int(np.argmax(probs))
        top_class = idx_to_class[top_idx]
        top_confidence = float(probs[top_idx])

        return {
            "event": top_class,
            "confidence": top_confidence
        }
    
    except Exception as e:
        print(f"❌ B 모듈 추론 에러: {e}")
        # 에러 발생 시 기본값 반환
        return {
            "event": "생활소음",
            "confidence": 0.5
        }


# ==========================================
# FastAPI에서 호출하는 메인 함수
# ==========================================
def analyze_sound(event: str, confidence: float) -> Dict:
    """
    B 모듈: 사운드/낙상 이벤트를 받아서
    표준화된 event label + confidence 를 돌려줌.
    
    Input: 이벤트 라벨 + confidence
    Output: 표준화된 사운드 분석 결과 dict
    
    {
        "event": str,        # "낙상", "생활소음" 등
        "confidence": float   # 0.0 ~ 1.0
    }
    
    Note: 현재는 입력값을 그대로 반환하지만,
          추후 오디오 파일을 받아서 모델로 분석하도록 확장 가능
    """
    # 기존 인터페이스 유지 (하위 호환)
    normalized_event = event
    final_confidence = confidence

    return {
        "event": normalized_event,
        "confidence": final_confidence,
    }


# ==========================================
# 오디오 파일을 직접 분석하는 함수 (선택적 사용)
# ==========================================
def analyze_sound_from_file(wav_path: str) -> Dict:
    """
    WAV 파일 경로를 받아서 모델로 분석
    
    Input: wav 파일 경로
    Output: {
        "event": str,
        "confidence": float
    }
    """
    return predict_audio_event(wav_path)

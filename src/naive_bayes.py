"""Naive Bayes de Bernoulli implementado de raiz (escola Bayesiana das aulas).

Reutiliza o Teorema de Bayes estudado nas aulas (ver `sumarios-de-aulas.txt`,
"procura do naufrago com Bayes" e "NLP/Estilometria"). Aplicado a features
binarias (presenca/ausencia de cada tag de ingrediente):

    P(classe | x) ∝ P(classe) * Π_j P(x_j | classe)

com a hipotese "naive" de independencia condicional entre features. Para
cada feature j e classe c usa-se a verosimilhanca de Bernoulli

    P(x_j=1 | c) = (N_{c,j} + alpha) / (N_c + 2*alpha)        (Laplace)

e a predicao e feita em espaco logaritmico para evitar underflow:

    score(c) = log P(c) + Σ_j [ x_j*log p_{c,j} + (1-x_j)*log(1-p_{c,j}) ]

A API (`fit`/`predict`) imita a do scikit-learn usada nas aulas, para poder
ser comparada lado a lado com a Arvore de Decisao e a Random Forest.
"""
from __future__ import annotations

import numpy as np


class BernoulliNaiveBayes:
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.classes_: np.ndarray | None = None
        self._log_prior: np.ndarray | None = None
        self._log_p: np.ndarray | None = None       # log P(x_j=1|c)
        self._log_not_p: np.ndarray | None = None    # log P(x_j=0|c)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BernoulliNaiveBayes":
        X = np.asarray(X)
        y = np.asarray(y)
        self.classes_ = np.array(sorted(set(y.tolist())))
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        self._log_prior = np.zeros(n_classes)
        prob = np.zeros((n_classes, n_features))

        for ci, c in enumerate(self.classes_):
            Xc = X[y == c]
            n_c = Xc.shape[0]
            # prior P(c)
            self._log_prior[ci] = np.log(n_c / X.shape[0])
            # verosimilhanca de Bernoulli com suavizacao de Laplace
            feature_counts = Xc.sum(axis=0)  # N_{c,j}
            prob[ci] = (feature_counts + self.alpha) / (n_c + 2 * self.alpha)

        self._log_p = np.log(prob)
        self._log_not_p = np.log(1.0 - prob)
        return self

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X)
        # score(c) = log P(c) + X·log p + (1-X)·log(1-p)
        # vetorizado: (n_amostras, n_classes)
        return (
            self._log_prior
            + X @ self._log_p.T
            + (1 - X) @ self._log_not_p.T
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.classes_ is None:
            raise RuntimeError("Modelo nao treinado: chamar fit() primeiro.")
        jll = self._joint_log_likelihood(X)
        return self.classes_[np.argmax(jll, axis=1)]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        jll = self._joint_log_likelihood(X)
        # normalizacao softmax estavel
        jll -= jll.max(axis=1, keepdims=True)
        probs = np.exp(jll)
        return probs / probs.sum(axis=1, keepdims=True)

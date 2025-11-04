"""
Accuracy validation system for FNA Platform.

Implements FR-011 compliance: 85% sentiment classification accuracy
vs human expert annotations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AccuracyMetrics:
    """Container for accuracy validation metrics."""
    total_samples: int
    correct_predictions: int
    accuracy_percentage: float
    optimism_accuracy: float
    risk_accuracy: float
    uncertainty_accuracy: float
    confidence_threshold: float
    validation_date: datetime


@dataclass
class ExpertAnnotation:
    """Human expert annotation for validation."""
    text_sample: str
    optimism_score: float
    risk_score: float
    uncertainty_score: float
    annotator_id: str
    annotation_date: datetime


class AccuracyValidator:
    """
    Validates sentiment analysis accuracy against human expert annotations.
    
    Implements FR-011 requirement: ≥85% sentiment classification accuracy.
    """
    
    def __init__(self, accuracy_threshold: float = 0.85):
        """
        Initialize accuracy validator.
        
        Args:
            accuracy_threshold: Minimum required accuracy (default: 0.85 = 85%)
        """
        self.accuracy_threshold = accuracy_threshold
        self.validation_history: List[AccuracyMetrics] = []
    
    def validate_analysis(
        self,
        predicted_scores: Dict[str, float],
        expert_annotations: List[ExpertAnnotation],
        tolerance: float = 0.10
    ) -> AccuracyMetrics:
        """
        Validate predicted scores against expert annotations.
        
        Args:
            predicted_scores: Predicted sentiment scores from model
            expert_annotations: List of expert annotations
            tolerance: Acceptable difference between predicted and expert scores (default: 0.10 = 10%)
            
        Returns:
            AccuracyMetrics: Validation results
        """
        if not expert_annotations:
            raise ValueError("At least one expert annotation required")
        
        # Calculate accuracy for each dimension
        optimism_correct = 0
        risk_correct = 0
        uncertainty_correct = 0
        total_samples = len(expert_annotations)
        
        for annotation in expert_annotations:
            # Check if predicted scores are within tolerance
            if abs(predicted_scores.get('optimism_score', 0) - annotation.optimism_score) <= tolerance:
                optimism_correct += 1
            
            if abs(predicted_scores.get('risk_score', 0) - annotation.risk_score) <= tolerance:
                risk_correct += 1
            
            if abs(predicted_scores.get('uncertainty_score', 0) - annotation.uncertainty_score) <= tolerance:
                uncertainty_correct += 1
        
        # Calculate accuracies
        optimism_accuracy = optimism_correct / total_samples if total_samples > 0 else 0.0
        risk_accuracy = risk_correct / total_samples if total_samples > 0 else 0.0
        uncertainty_accuracy = uncertainty_correct / total_samples if total_samples > 0 else 0.0
        
        # Overall accuracy (average of all dimensions)
        overall_accuracy = (optimism_accuracy + risk_accuracy + uncertainty_accuracy) / 3.0
        
        # Count correct predictions (all dimensions within tolerance)
        correct_predictions = sum(
            1 for ann in expert_annotations
            if (abs(predicted_scores.get('optimism_score', 0) - ann.optimism_score) <= tolerance and
                abs(predicted_scores.get('risk_score', 0) - ann.risk_score) <= tolerance and
                abs(predicted_scores.get('uncertainty_score', 0) - ann.uncertainty_score) <= tolerance)
        )
        
        metrics = AccuracyMetrics(
            total_samples=total_samples,
            correct_predictions=correct_predictions,
            accuracy_percentage=overall_accuracy * 100,
            optimism_accuracy=optimism_accuracy * 100,
            risk_accuracy=risk_accuracy * 100,
            uncertainty_accuracy=uncertainty_accuracy * 100,
            confidence_threshold=self.accuracy_threshold * 100,
            validation_date=datetime.utcnow()
        )
        
        # Check if accuracy meets threshold
        if overall_accuracy < self.accuracy_threshold:
            logger.warning(
                f"Accuracy validation failed: {overall_accuracy * 100:.2f}% < {self.accuracy_threshold * 100:.2f}%"
            )
        else:
            logger.info(
                f"Accuracy validation passed: {overall_accuracy * 100:.2f}% >= {self.accuracy_threshold * 100:.2f}%"
            )
        
        self.validation_history.append(metrics)
        return metrics
    
    def validate_batch(
        self,
        predictions: List[Dict[str, float]],
        annotations: List[List[ExpertAnnotation]]
    ) -> AccuracyMetrics:
        """
        Validate a batch of predictions against annotations.
        
        Args:
            predictions: List of predicted scores
            annotations: List of annotation lists (one per prediction)
            
        Returns:
            AccuracyMetrics: Combined validation results
        """
        if len(predictions) != len(annotations):
            raise ValueError("Number of predictions must match number of annotation sets")
        
        all_correct = 0
        total = 0
        optimism_correct = 0
        risk_correct = 0
        uncertainty_correct = 0
        
        for pred, ann_list in zip(predictions, annotations):
            for ann in ann_list:
                total += 1
                tolerance = 0.10
                
                if abs(pred.get('optimism_score', 0) - ann.optimism_score) <= tolerance:
                    optimism_correct += 1
                if abs(pred.get('risk_score', 0) - ann.risk_score) <= tolerance:
                    risk_correct += 1
                if abs(pred.get('uncertainty_score', 0) - ann.uncertainty_score) <= tolerance:
                    uncertainty_correct += 1
                
                if (abs(pred.get('optimism_score', 0) - ann.optimism_score) <= tolerance and
                    abs(pred.get('risk_score', 0) - ann.risk_score) <= tolerance and
                    abs(pred.get('uncertainty_score', 0) - ann.uncertainty_score) <= tolerance):
                    all_correct += 1
        
        overall_accuracy = all_correct / total if total > 0 else 0.0
        optimism_accuracy = optimism_correct / total if total > 0 else 0.0
        risk_accuracy = risk_correct / total if total > 0 else 0.0
        uncertainty_accuracy = uncertainty_correct / total if total > 0 else 0.0
        
        metrics = AccuracyMetrics(
            total_samples=total,
            correct_predictions=all_correct,
            accuracy_percentage=overall_accuracy * 100,
            optimism_accuracy=optimism_accuracy * 100,
            risk_accuracy=risk_accuracy * 100,
            uncertainty_accuracy=uncertainty_accuracy * 100,
            confidence_threshold=self.accuracy_threshold * 100,
            validation_date=datetime.utcnow()
        )
        
        self.validation_history.append(metrics)
        return metrics
    
    def get_validation_history(self) -> List[AccuracyMetrics]:
        """Get validation history."""
        return self.validation_history.copy()
    
    def get_latest_metrics(self) -> Optional[AccuracyMetrics]:
        """Get most recent validation metrics."""
        return self.validation_history[-1] if self.validation_history else None
    
    def meets_accuracy_requirement(self, metrics: AccuracyMetrics) -> bool:
        """Check if metrics meet accuracy requirement."""
        return metrics.accuracy_percentage >= self.accuracy_threshold * 100


# Global validator instance
_validator: Optional[AccuracyValidator] = None


def get_accuracy_validator() -> AccuracyValidator:
    """Get global accuracy validator instance."""
    global _validator
    if _validator is None:
        _validator = AccuracyValidator()
    return _validator


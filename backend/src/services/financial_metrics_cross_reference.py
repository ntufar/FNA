"""
Financial Metrics Cross-Reference Service for FNA Platform.

Implements FR-020: Cross-references narrative tone analysis with structured 
financial performance metrics extracted from iXBRL data to provide enhanced insights.
"""

import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal

from ..models import NarrativeAnalysis

logger = logging.getLogger(__name__)


class FinancialMetricsCrossReference:
    """
    Cross-references narrative sentiment with financial metrics to provide enhanced insights.
    
    Analyzes correlations, discrepancies, and patterns between narrative tone
    and actual financial performance data.
    """
    
    def __init__(self):
        """Initialize the cross-reference service."""
        logger.info("FinancialMetricsCrossReference service initialized")
    
    def analyze_cross_reference(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform cross-referenced analysis combining narrative sentiment with financial metrics.
        
        Args:
            narrative_analysis: NarrativeAnalysis model with sentiment scores
            financial_metrics: Optional financial metrics from iXBRL parsing
            
        Returns:
            dict: Enhanced insights combining narrative and financial data
        """
        insights = {
            'sentiment_summary': self._extract_sentiment_summary(narrative_analysis),
            'financial_summary': None,
            'correlations': [],
            'discrepancies': [],
            'enhanced_insights': [],
            'confidence_adjustment': None,
            'risk_alignment': None
        }
        
        # If financial metrics are available, perform cross-referencing
        if financial_metrics and financial_metrics.get('metadata', {}).get('parsing_success'):
            insights['financial_summary'] = self._extract_financial_summary(financial_metrics)
            insights['correlations'] = self._identify_correlations(
                narrative_analysis, financial_metrics
            )
            insights['discrepancies'] = self._identify_discrepancies(
                narrative_analysis, financial_metrics
            )
            insights['enhanced_insights'] = self._generate_enhanced_insights(
                narrative_analysis, financial_metrics, insights['correlations'], insights['discrepancies']
            )
            insights['confidence_adjustment'] = self._calculate_confidence_adjustment(
                narrative_analysis, financial_metrics, insights['correlations']
            )
            insights['risk_alignment'] = self._assess_risk_alignment(
                narrative_analysis, financial_metrics
            )
        else:
            insights['enhanced_insights'].append(
                "No financial metrics available for cross-referencing. "
                "Analysis based on narrative sentiment only."
            )
        
        return insights
    
    def _extract_sentiment_summary(self, analysis: NarrativeAnalysis) -> Dict[str, Any]:
        """Extract key sentiment metrics from narrative analysis."""
        return {
            'optimism_score': float(analysis.optimism_score),
            'optimism_confidence': float(analysis.optimism_confidence),
            'risk_score': float(analysis.risk_score),
            'risk_confidence': float(analysis.risk_confidence),
            'uncertainty_score': float(analysis.uncertainty_score),
            'uncertainty_confidence': float(analysis.uncertainty_confidence),
            'key_themes': analysis.key_themes or [],
            'overall_sentiment': self._classify_overall_sentiment(analysis)
        }
    
    def _extract_financial_summary(self, financial_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key financial metrics summary."""
        summary = {
            'revenue_trend': None,
            'income_trend': None,
            'profitability': None,
            'key_metrics': {},
            'period_comparison': {}
        }
        
        # Analyze revenue trends
        revenue = financial_metrics.get('revenue', {})
        if revenue:
            revenue_values = [v for v in revenue.values() if isinstance(v, (int, float, Decimal))]
            if revenue_values:
                summary['revenue_trend'] = self._calculate_trend(revenue_values)
                summary['key_metrics']['total_revenue'] = max(revenue_values) if revenue_values else None
        
        # Analyze income trends
        income = financial_metrics.get('income', {})
        if income:
            income_values = [v for v in income.values() if isinstance(v, (int, float, Decimal))]
            if income_values:
                summary['income_trend'] = self._calculate_trend(income_values)
                summary['key_metrics']['net_income'] = max(income_values) if income_values else None
        
        # Calculate profitability if both revenue and income available
        if summary['key_metrics'].get('total_revenue') and summary['key_metrics'].get('net_income'):
            try:
                revenue_val = float(summary['key_metrics']['total_revenue'])
                income_val = float(summary['key_metrics']['net_income'])
                if revenue_val > 0:
                    summary['profitability'] = income_val / revenue_val
            except (ValueError, TypeError):
                pass
        
        # Balance sheet metrics
        balance_sheet = financial_metrics.get('balance_sheet', {})
        if balance_sheet:
            # Extract common balance sheet metrics
            for key, value in balance_sheet.items():
                if isinstance(value, (int, float, Decimal)):
                    summary['key_metrics'][key] = float(value)
        
        return summary
    
    def _identify_correlations(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify correlations between narrative sentiment and financial performance."""
        correlations = []
        financial_summary = self._extract_financial_summary(financial_metrics)
        
        # Correlation 1: Optimism vs Revenue Growth
        if financial_summary.get('revenue_trend'):
            revenue_trend = financial_summary['revenue_trend']
            optimism = float(narrative_analysis.optimism_score)
            
            if revenue_trend == 'increasing' and optimism > 0.6:
                correlations.append({
                    'type': 'positive_alignment',
                    'metric': 'optimism_revenue',
                    'description': 'High optimism aligns with increasing revenue trend',
                    'strength': 'strong' if optimism > 0.7 else 'moderate'
                })
            elif revenue_trend == 'decreasing' and optimism < 0.4:
                correlations.append({
                    'type': 'negative_alignment',
                    'metric': 'optimism_revenue',
                    'description': 'Low optimism aligns with decreasing revenue trend',
                    'strength': 'strong' if optimism < 0.3 else 'moderate'
                })
        
        # Correlation 2: Risk Score vs Profitability
        if financial_summary.get('profitability') is not None:
            profitability = financial_summary['profitability']
            risk_score = float(narrative_analysis.risk_score)
            
            if profitability < 0.05 and risk_score > 0.6:
                correlations.append({
                    'type': 'risk_profitability',
                    'metric': 'risk_low_profitability',
                    'description': 'High risk perception aligns with low profitability margins',
                    'strength': 'strong'
                })
        
        # Correlation 3: Uncertainty vs Financial Volatility
        uncertainty = float(narrative_analysis.uncertainty_score)
        if uncertainty > 0.7:
            # Check for significant variations in financial metrics
            revenue = financial_metrics.get('revenue', {})
            if revenue:
                revenue_values = [v for v in revenue.values() if isinstance(v, (int, float, Decimal))]
                if len(revenue_values) > 1:
                    volatility = self._calculate_volatility(revenue_values)
                    if volatility > 0.15:  # 15% volatility threshold
                        correlations.append({
                            'type': 'uncertainty_volatility',
                            'metric': 'uncertainty_financial_volatility',
                            'description': 'High uncertainty aligns with significant financial volatility',
                            'strength': 'moderate'
                        })
        
        return correlations
    
    def _identify_discrepancies(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify discrepancies between narrative sentiment and financial performance."""
        discrepancies = []
        financial_summary = self._extract_financial_summary(financial_metrics)
        
        # Discrepancy 1: High Optimism but Declining Revenue
        if financial_summary.get('revenue_trend'):
            revenue_trend = financial_summary['revenue_trend']
            optimism = float(narrative_analysis.optimism_score)
            
            if revenue_trend == 'decreasing' and optimism > 0.65:
                discrepancies.append({
                    'type': 'optimism_revenue_mismatch',
                    'severity': 'high',
                    'description': f'High optimism ({optimism:.2f}) despite declining revenue trend',
                    'implication': 'Management may be overly optimistic or downplaying challenges'
                })
        
        # Discrepancy 2: Low Risk but Poor Profitability
        if financial_summary.get('profitability') is not None:
            profitability = financial_summary['profitability']
            risk_score = float(narrative_analysis.risk_score)
            
            if profitability < 0.02 and risk_score < 0.4:
                discrepancies.append({
                    'type': 'risk_profitability_mismatch',
                    'severity': 'moderate',
                    'description': f'Low risk perception ({risk_score:.2f}) despite low profitability ({profitability:.2%})',
                    'implication': 'Management may not be adequately acknowledging financial challenges'
                })
        
        # Discrepancy 3: High Uncertainty but Stable Financials
        uncertainty = float(narrative_analysis.uncertainty_score)
        if uncertainty > 0.7:
            revenue = financial_metrics.get('revenue', {})
            if revenue:
                revenue_values = [v for v in revenue.values() if isinstance(v, (int, float, Decimal))]
                if len(revenue_values) > 1:
                    volatility = self._calculate_volatility(revenue_values)
                    if volatility < 0.05:  # Low volatility
                        discrepancies.append({
                            'type': 'uncertainty_stability_mismatch',
                            'severity': 'low',
                            'description': f'High uncertainty ({uncertainty:.2f}) despite stable financial metrics',
                            'implication': 'Management may be expressing caution about future outlook despite current stability'
                        })
        
        return discrepancies
    
    def _generate_enhanced_insights(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Dict[str, Any],
        correlations: List[Dict[str, Any]],
        discrepancies: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate enhanced insights combining narrative and financial data."""
        insights = []
        financial_summary = self._extract_financial_summary(financial_metrics)
        
        # Insight 1: Overall alignment assessment
        if correlations:
            strong_correlations = [c for c in correlations if c.get('strength') == 'strong']
            if strong_correlations:
                insights.append(
                    f"Narrative sentiment shows strong alignment with financial performance "
                    f"({len(strong_correlations)} key correlations identified)."
                )
        
        # Insight 2: Discrepancy warnings
        if discrepancies:
            high_severity = [d for d in discrepancies if d.get('severity') == 'high']
            if high_severity:
                insights.append(
                    f"⚠️ {len(high_severity)} significant discrepancy(ies) detected between "
                    f"narrative tone and financial metrics. Review recommended."
                )
        
        # Insight 3: Profitability context
        if financial_summary.get('profitability') is not None:
            profitability = financial_summary['profitability']
            optimism = float(narrative_analysis.optimism_score)
            
            if profitability > 0.15 and optimism > 0.6:
                insights.append(
                    f"Strong profitability ({profitability:.1%}) aligns with optimistic narrative tone, "
                    f"suggesting management confidence is well-founded."
                )
            elif profitability < 0.05 and optimism < 0.4:
                insights.append(
                    f"Low profitability ({profitability:.1%}) aligns with cautious narrative tone, "
                    f"indicating management awareness of financial challenges."
                )
        
        # Insight 4: Revenue trend context
        if financial_summary.get('revenue_trend'):
            revenue_trend = financial_summary['revenue_trend']
            risk_score = float(narrative_analysis.risk_score)
            
            if revenue_trend == 'increasing' and risk_score < 0.4:
                insights.append(
                    "Increasing revenue trend with low risk perception suggests "
                    "sustainable growth trajectory."
                )
            elif revenue_trend == 'decreasing' and risk_score > 0.6:
                insights.append(
                    "Decreasing revenue trend with high risk perception indicates "
                    "management recognition of operational challenges."
                )
        
        return insights
    
    def _calculate_confidence_adjustment(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Dict[str, Any],
        correlations: List[Dict[str, Any]]
    ) -> Optional[Dict[str, float]]:
        """Calculate confidence adjustments based on financial metric alignment."""
        if not correlations:
            return None
        
        # Count strong correlations
        strong_correlations = len([c for c in correlations if c.get('strength') == 'strong'])
        moderate_correlations = len([c for c in correlations if c.get('strength') == 'moderate'])
        
        # Base adjustments
        base_adjustment = 0.0
        if strong_correlations >= 2:
            base_adjustment = 0.05  # Increase confidence
        elif strong_correlations >= 1:
            base_adjustment = 0.02
        elif moderate_correlations >= 2:
            base_adjustment = 0.01
        
        return {
            'optimism_confidence_adjustment': base_adjustment,
            'risk_confidence_adjustment': base_adjustment,
            'uncertainty_confidence_adjustment': base_adjustment,
            'reason': f'{strong_correlations} strong, {moderate_correlations} moderate correlations'
        }
    
    def _assess_risk_alignment(
        self,
        narrative_analysis: NarrativeAnalysis,
        financial_metrics: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Assess alignment between narrative risk perception and financial risk indicators."""
        financial_summary = self._extract_financial_summary(financial_metrics)
        risk_score = float(narrative_analysis.risk_score)
        
        # Assess financial risk indicators
        financial_risk_indicators = []
        
        # Low profitability as risk indicator
        if financial_summary.get('profitability') is not None:
            if financial_summary['profitability'] < 0.05:
                financial_risk_indicators.append('low_profitability')
        
        # Declining revenue as risk indicator
        if financial_summary.get('revenue_trend') == 'decreasing':
            financial_risk_indicators.append('declining_revenue')
        
        # Assess alignment
        narrative_risk_level = 'high' if risk_score > 0.6 else 'moderate' if risk_score > 0.4 else 'low'
        financial_risk_level = 'high' if len(financial_risk_indicators) >= 2 else 'moderate' if len(financial_risk_indicators) >= 1 else 'low'
        
        alignment = 'aligned' if narrative_risk_level == financial_risk_level else 'misaligned'
        
        return {
            'narrative_risk_level': narrative_risk_level,
            'financial_risk_level': financial_risk_level,
            'alignment': alignment,
            'financial_risk_indicators': financial_risk_indicators,
            'risk_score': risk_score
        }
    
    def _classify_overall_sentiment(self, analysis: NarrativeAnalysis) -> str:
        """Classify overall sentiment from analysis scores."""
        optimism = float(analysis.optimism_score)
        risk = float(analysis.risk_score)
        uncertainty = float(analysis.uncertainty_score)
        
        if optimism > 0.6 and risk < 0.4 and uncertainty < 0.4:
            return 'positive'
        elif optimism < 0.4 and risk > 0.6:
            return 'negative'
        elif uncertainty > 0.6:
            return 'uncertain'
        elif risk > 0.6:
            return 'cautious'
        else:
            return 'neutral'
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return 'stable'
        
        try:
            # Convert to floats
            float_values = [float(v) for v in values]
            
            # Simple trend calculation: compare first and last values
            if float_values[-1] > float_values[0] * 1.05:  # 5% increase
                return 'increasing'
            elif float_values[-1] < float_values[0] * 0.95:  # 5% decrease
                return 'decreasing'
            else:
                return 'stable'
        except (ValueError, TypeError):
            return 'stable'
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation (volatility) from a list of values."""
        if len(values) < 2:
            return 0.0
        
        try:
            float_values = [float(v) for v in values]
            mean_val = sum(float_values) / len(float_values)
            
            if mean_val == 0:
                return 0.0
            
            variance = sum((x - mean_val) ** 2 for x in float_values) / len(float_values)
            std_dev = variance ** 0.5
            
            # Coefficient of variation
            return std_dev / abs(mean_val) if mean_val != 0 else 0.0
        except (ValueError, TypeError):
            return 0.0


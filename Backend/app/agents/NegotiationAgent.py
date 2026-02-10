from typing import Dict, Any, Optional, List
import json
import re
import logging
from .base import BaseOmegaAgent
from app.schemas.negotiation import NegotiatedTerms
from app.schemas.negotiation_session import NegotiationSession

logger = logging.getLogger(__name__)


class NegotiationAgent(BaseOmegaAgent):
    """
    Strategic Negotiation Agent.
    
    This agent manages the multi-round negotiation process with the client.
    It uses a round-based strategy to make strategic concessions and reach
    a mutually beneficial deal.
    """
    def __init__(self):
        super().__init__(
            name="NegotiationAgent",
            instructions=[
                "You are an Elite Moroccan Car Negotiator and Marketing Expert at OMEGA.",
                "Your goal is to negotiate professionally with clients to reach a mutually beneficial deal.",
                "You engage in multi-turn conversations, making strategic concessions based on the round number.",
                "",
                "NEGOTIATION STRATEGY:",
                "- VÉRIFICATION STOCK : Avant de proposer quoi que ce soit, vérifie market_data['inventory']['stock_available'].",
                "- SI RUPTURE (Stock=0) : Ne propose AUCUNE offre, AUCUN prix. Réponds poliment que le modèle est actuellement indisponible et suggère des alternatives basées sur 'top_models' dans market_overview.",
                "- Round 1-2: Be firm, minimal concessions (1-3% max)",
                "- Round 3-4: Show flexibility, moderate concessions (3-7%)",
                "- Round 5: Final offer, maximum concessions (up to 10%)",
                "",
                "RULES for JSON:",
                "- Return ONLY a valid JSON object.",
                "- Do NOT use markdown bold (**) or bullet points inside JSON values.",
                "- Ensure all double quotes inside strings are escaped if necessary.",
                "- Use simple text for persuasion_points and marketing_message.",
                "- Language: Marketing message should depend on user language.",
            ]
        )

    async def start_negotiation(
        self, 
        user_data: Dict[str, Any], 
        valuation_data: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> NegotiatedTerms:
        """
        Generate initial offer to start negotiation.
        This is Round 1 - be professional but firm.
        """
        prompt = f"""
        INPUT DATA:
        USER: {json.dumps(user_data, default=str)}
        TRADE-IN: {json.dumps(valuation_data, default=str)}
        MARKET: {json.dumps(market_data, default=str)}
        
        TASK: Generate the INITIAL negotiation offer (Round 1/5).
        Be professional and confident. This is your opening offer.
        
        Required structure:
        {{
            "offer_price_mad": float,
            "discount_amount_mad": float,
            "trade_in_value_mad": float or null,
            "trade_in_year": int or null,
            "monthly_payment_mad": float or null,
            "payment_method": "Cash/Financing/Leasing/LLD",
            "persuasion_points": ["string", ...],
            "marketing_message": "string (warm, professional, in French)",
            "leverage_used": "string",
            "flexibility_level": "Low/Medium/High"
        }}
        """
        
        
        try:
            response = await self.arun(prompt)
            content = getattr(response, "content", None) or getattr(response, "output_text", str(response))
            
            # Check if the response is an error object (API might return error as content)
            if isinstance(content, dict) and content.get("object") == "error":
                error_msg = content.get("message", "Unknown error")
                error_type = content.get("type", "unknown")
                logger.error(f"❌ API returned error: {error_type} - {error_msg}")
                
                # Raise exception to trigger retry logic in base.py
                if "rate" in error_type.lower() or "rate limit" in error_msg.lower():
                    raise Exception(f"Rate limit exceeded: {error_msg}")
                else:
                    raise Exception(f"API error: {error_msg}")
            
            # If content is string, check if it contains error JSON
            if isinstance(content, str):
                content_lower = content.lower()
                if '"object":"error"' in content_lower or '"type":"rate_limited"' in content_lower or "rate limit exceeded" in content_lower:
                    # Try to extract JSON if it's embedded in text
                    try:
                        # First try direct load in case it is valid JSON
                        error_data = json.loads(content)
                    except json.JSONDecodeError:
                        # Try to find JSON block
                        import re
                        match = re.search(r"(\{.*\})", content, re.DOTALL)
                        if match:
                            try:
                                error_data = json.loads(match.group(1))
                            except:
                                error_data = {}
                        else:
                            error_data = {}
                    
                    # Check if extracted data is an error
                    if error_data.get("object") == "error" or "rate limit" in content_lower:
                        error_msg = error_data.get("message", "Rate limit error detected in content")
                        logger.error(f"❌ API error in response: {error_msg}")
                        raise Exception(f"Rate limit exceeded: {error_msg}")

            try:
                return self._parse_negotiation_response(content)
            except Exception as parse_error:
                # If parsing fails, check if it looked like an error response that we missed
                if "rate limit" in str(getattr(response, "content", "")).lower() or "429" in str(getattr(response, "content", "")).lower():
                     logger.warning("Parsing failed on what looks like a rate limit error. Treating as rate limit.")
                     raise Exception("Rate limit exceeded (detected during parsing)")
                raise parse_error
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            error_msg = str(e).lower()
            
            # If rate limit error persists after retries, provide a fallback offer
            if "rate limit" in error_msg or "429" in error_msg or "rate_limited" in error_msg:
                logger.error(f"❌ Rate limit persists after retries. Generating fallback offer.")
                return self._generate_fallback_offer(user_data, valuation_data, market_data)
            else:
                # For other errors, re-raise
                raise

    async def process_counter_offer(
        self,
        session: NegotiationSession,
        client_message: str,
        client_counter: Optional[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> NegotiatedTerms:
        """
        Process client's counter-offer and generate agent's response.
        Adjust strategy based on round number.
        """
        current_round = session.current_round
        max_rounds = session.max_rounds
        current_offer = session.current_offer_data
        initial_offer = session.initial_offer_data
        
        # Calculate how much we can concede based on round
        concession_factor = self._calculate_concession_factor(current_round, max_rounds)
        
        prompt = f"""
        NEGOTIATION CONTEXT:
        - Round: {current_round}/{max_rounds}
        - Initial Offer: {json.dumps(initial_offer, default=str)}
        - Current Offer: {json.dumps(current_offer, default=str)}
        - Concession Factor: {concession_factor} (0.0 = firm, 1.0 = maximum flexibility)
        
        CLIENT MESSAGE: "{client_message}"
        CLIENT COUNTER-OFFER: {json.dumps(client_counter, default=str) if client_counter else "None specified"}
        
        CONVERSATION HISTORY (last 3 messages):
        {json.dumps(conversation_history[-3:], indent=2, default=str)}
        
        TASK: Generate your counter-response for Round {current_round}.
        
        STRATEGY:
        - Analyze what the client is asking for
        - Determine if their request is reasonable given the concession factor
        - Make strategic concessions on price, monthly payment, or other terms
        - If Round {current_round} == {max_rounds}, this is your FINAL offer - be clear about it
        - Maintain professionalism and warmth
        
        Required JSON structure:
        {{
            "offer_price_mad": float,
            "discount_amount_mad": float,
            "trade_in_value_mad": float or null,
            "trade_in_year": int or null,
            "monthly_payment_mad": float or null,
            "payment_method": "Cash/Financing/Leasing/LLD",
            "persuasion_points": ["string", ...],
            "marketing_message": "string (acknowledge client's request, explain your position, present new offer)",
            "leverage_used": "string",
            "flexibility_level": "Low/Medium/High"
        }}
        """
        
        response = await self.arun(prompt)
        content = getattr(response, "content", None) or getattr(response, "output_text", str(response))
        
        return self._parse_negotiation_response(content)

    def _calculate_concession_factor(self, current_round: int, max_rounds: int) -> float:
        """
        Calculate how much flexibility to show based on round number.
        Returns 0.0 to 1.0 where 1.0 means maximum concessions allowed.
        """
        if current_round <= 2:
            return 0.2  # Very firm (1-3% concessions)
        elif current_round <= 4:
            return 0.5  # Moderate (3-7% concessions)
        else:
            return 0.8  # Final round (up to 10% concessions)

    def is_client_offer_acceptable(
        self,
        client_offer: Dict[str, Any],
        initial_offer: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> bool:
        """
        Determine if client's offer is within acceptable business range.
        Maximum discount allowed: 15% from initial offer.
        """
        if not client_offer or 'desired_price' not in client_offer:
            return False
        
        initial_price = initial_offer.get('offer_price_mad', 0)
        client_price = client_offer.get('desired_price', 0)
        
        if initial_price == 0:
            return False
        
        discount_percentage = ((initial_price - client_price) / initial_price) * 100
        
        # Maximum 15% discount allowed
        return discount_percentage <= 15.0

    def _parse_negotiation_response(self, content: str) -> NegotiatedTerms:
        """
        Parse LLM response into NegotiatedTerms object.
        """
        import re
        
        try:
            # Find JSON in response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                match = re.search(r"(\{.*\})", content, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                else:
                    json_str = content.strip()
            
            # Remove control characters
            json_str = re.sub(r'[\x00-\x1f]', '', json_str)
            
            data = json.loads(json_str, strict=False)
            
            # Check if the parsed data is actually an error object
            if isinstance(data, dict) and (data.get("object") == "error" or data.get("type") == "rate_limited"):
                error_msg = data.get("message", "Unknown API Error")
                raise Exception(f"API returned error object instead of terms: {error_msg}")
                
            return NegotiatedTerms(**data)
        except Exception as e:
            safe_content = content.encode('ascii', 'ignore').decode('ascii')
            print(f"Parsing failed: {e}. Raw content snippet: {safe_content[:200]}...")
            raise
    
    def _generate_fallback_offer(
        self,
        user_data: Dict[str, Any],
        valuation_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> NegotiatedTerms:
        """
        Generate a basic fallback offer when API is unavailable.
        Uses simple business logic instead of LLM.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("🔧 Generating fallback offer using business logic")
        
        # Extract data with safe defaults
        user_budget = user_data.get('max_budget_mad', 200000)
        preferences = user_data.get('preferences', {})
        brands = preferences.get('brands', [])
        
        # Get market price
        market_price = market_data.get('inventory', {}).get('avg_market_price', 180000)
        if market_price == 0:
            market_price = user_budget * 0.9  # Fallback to 90% of budget
        
        # Calculate offer with conservative discount (5%)
        discount_percentage = 0.05
        discount_amount = market_price * discount_percentage
        offer_price = market_price - discount_amount
        
        # Trade-in value
        trade_in_value = valuation_data.get('estimated_value', None)
        trade_in_year = valuation_data.get('year', None)
        
        # Monthly payment (assuming 60 months at 5% interest)
        if user_data.get('preferred_payment') == 'financing':
            principal = offer_price - (trade_in_value or 0)
            monthly_rate = 0.05 / 12  # 5% annual
            num_months = 60
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_months) / ((1 + monthly_rate)**num_months - 1)
        else:
            monthly_payment = None
        
        # Build fallback offer
        brand_str = brands[0] if brands else "ce véhicule"
        
        return NegotiatedTerms(
            offer_price_mad=round(offer_price, 2),
            discount_amount_mad=round(discount_amount, 2),
            trade_in_value_mad=round(trade_in_value, 2) if trade_in_value else None,
            trade_in_year=trade_in_year,
            monthly_payment_mad=round(monthly_payment, 2) if monthly_payment else None,
            payment_method=user_data.get('preferred_payment', 'Cash'),
            persuasion_points=[
                f"Prix compétitif pour {brand_str}",
                "Remise incluse dans cette offre",
                "Plusieurs options de financement disponibles" if monthly_payment else "Paiement comptant accepté",
                "Garantie constructeur incluse"
            ],
            marketing_message=(
                f"Nous sommes ravis de vous présenter notre offre pour {brand_str}. "
                f"Nous offrons une remise de {round(discount_amount)} MAD, "
                f"pour un prix final de {round(offer_price)} MAD. "
                + (f"Avec votre reprise estimée à {round(trade_in_value)} MAD, " if trade_in_value else "")
                + (f"vos mensualités seraient d'environ {round(monthly_payment)} MAD sur 60 mois. " if monthly_payment else "")
                + "N'hésitez pas à nous faire part de vos questions!"
            ),
            leverage_used="market_price_competitive",
            flexibility_level="Medium"
        )

    # Keep backward compatibility with old method
    async def negotiate(
        self, 
        user_data: Dict[str, Any], 
        valuation_data: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> NegotiatedTerms:
        """
        Legacy method for backward compatibility.
        Calls start_negotiation.
        """
        return await self.start_negotiation(user_data, valuation_data, market_data)

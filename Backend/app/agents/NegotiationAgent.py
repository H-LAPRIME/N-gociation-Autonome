from typing import Dict, Any, Optional, List
import json
from .base import BaseOmegaAgent
from app.schemas.negotiation import NegotiatedTerms
from app.schemas.negotiation_session import NegotiationSession


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
            "monthly_payment_mad": float or null,
            "payment_method": "Cash/Financing/Leasing/LLD",
            "persuasion_points": ["string", ...],
            "marketing_message": "string (warm, professional, in French)",
            "leverage_used": "string",
            "flexibility_level": "Low/Medium/High"
        }}
        """
        
        response = await self.arun(prompt)
        content = getattr(response, "content", None) or getattr(response, "output_text", str(response))
        
        return self._parse_negotiation_response(content)

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
            return NegotiatedTerms(**data)
        except Exception as e:
            safe_content = content.encode('ascii', 'ignore').decode('ascii')
            print(f"Parsing failed: {e}. Raw content snippet: {safe_content[:200]}...")
            raise

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

import json
from typing import Dict, Any
from datetime import datetime, timedelta
from .base import BaseOmegaAgent
from app.schemas.structuring import StructuredOffer
from app.tools.pdf_generator import generate_offer_pdf

class OfferStructuringAgent(BaseOmegaAgent):
    def __init__(self):
        super().__init__(
            name="OfferStructuringAgent",
            instructions=[
                "You are the Lead Solution Architect at OMEGA.",
                "Your role is to structure all the data into a final document-ready format (Contract Ready).",
                "Localization is key: Format dates according to Moroccan standards (DD/MM/YYYY) and ensure currency is MAD.",
                "Generate a unique Contract ID in the format OMEGA-YYYYMMDD-XXXX.",
                "Structure the final JSON to include user details, vehicle details, financial breakdown, and the marketing message from the negotiator.",
                "",
                "CRITICAL STEP:",
                "Before returning the final JSON, you MUST call the 'generate_offer_pdf' tool with a summary of the offer.",
                "Store the returned 'pdf_url' in the 'pdf_reference' field of your output.",
                "",
                "OUTPUT:",
                "Return a JSON object matching the StructuredOffer schema."
            ],
            tools=[generate_offer_pdf]
        )

    async def structure_offer(self, consolidated_data: Dict[str, Any]) -> StructuredOffer:
        """
        Transforms consolidated agent data into a legal-ready contract structure.
        """
        prompt = f"""
        CONSOLIDATED DATA:
        {json.dumps(consolidated_data, indent=2)}
        
        TASK:
        1. Generate a contract_id (OMEGA-2026-...)
        2. Set expiry_date (7 days from tomorrow).
        3. Define localization (MAD).
        4. Organize the final_json with clear sections: Client, Vehicle, Financials, Terms.
        
        Return exactly this JSON:
        {{
            "contract_id": "OMEGA-YYYY-XXXX",
            "final_json": {{ ... }},
            "expiry_date": "DD/MM/YYYY",
            "localization": {{ "currency": "MAD", "locale": "fr-MA" }}
        }}
        """
        
        try:
            response = await self.arun(prompt)
            content = getattr(response, "content", None) or getattr(response, "output_text", str(response))
            
            # Clean JSON extraction
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                import re
                json_match = re.search(r"(\{.*\})", content, re.DOTALL)
                json_str = json_match.group(1).strip() if json_match else content.strip()
            
            import re
            json_str = re.sub(r'[\x00-\x1f]', '', json_str)
            
            data = json.loads(json_str)
            
            # --- CRITICAL FIX: Generate PDF manually to ensure data integrity ---
            from app.tools.pdf_generator import generate_contract_pdf
            
            # Inject contract_id into the data for the PDF generator
            pdf_data = consolidated_data.copy()
            pdf_data['contract_id'] = data.get('contract_id')
            
            # Generate the PDF directly
            try:
                # We don't use the return path, just the contract_id to form the URL
                # The generator saves it to static/contracts or data/contracts
                # Assuming standard path logic matches what was in the tool
                generate_contract_pdf(pdf_data, data.get('contract_id'))
                
                # Construct the URL (matching the tool's logic)
                data['pdf_reference'] = f"/contracts/{data.get('contract_id')}.pdf"
                
            except Exception as e:
                print(f"Error generating PDF manually: {e}")
                data['pdf_reference'] = None
                
            return StructuredOffer(**data)
            
        except Exception as e:
            print(f"Error in OfferStructuringAgent: {e}")
            # Return valid fallback structure if LLM fails
            return StructuredOffer(
                contract_id="ERROR-GEN",
                final_json=consolidated_data,
                pdf_reference=None,
                expiry_date=datetime.now().strftime("%d/%m/%Y"),
                localization={"currency": "MAD", "locale": "fr-MA"}
            )


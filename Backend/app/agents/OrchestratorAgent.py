from typing import Dict, List, Any, Optional
import asyncio
import json
import time
import logging
from app.agents.UserProfileAgent import UserProfileAgent
from app.agents.MarketAnalysisAgent import MarketAnalysisAgent
from app.agents.ValuationAgent import ValuationAgent
from app.agents.NegotiationAgent import NegotiationAgent
from app.agents.BusinessConstraintAgent import BusinessConstraintAgent
from app.agents.OfferStructuringAgent import OfferStructuringAgent
from app.database.negotiation_db import negotiation_db
from app.database.chat_db import chat_db
from app.schemas.negotiation_session import NegotiationSessionCreate
from app.schemas.chat_session import ChatMessage
from app.services.auth_service import get_user_by_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    The Brain of OMEGA.
    
    The OrchestratorAgent is responsible for coordinating the interaction between
    specialized AI agents (User Profile, Market Analysis, Valuation, etc.) to
    provide a seamless car buying/selling experience.
    """
    def __init__(self):
        self.user_agent = UserProfileAgent()
        self.market_agent = MarketAnalysisAgent()
        self.valuation_agent = ValuationAgent()
        self.negotiation_agent = NegotiationAgent()
        self.business_agent = BusinessConstraintAgent()
        self.structuring_agent = OfferStructuringAgent()

    async def coordinate(self, user_id: int, user_query: str, history: List[Dict[str, str]] = None, user_profile_state: Dict = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Coordinates the workflow between all OMEGA agents with conversational profile building.
        """
        # Persist User Message if session exists
        if session_id:
            try:
                session = chat_db.get_session(session_id)
                if session:
                    user_msg = ChatMessage(role="user", content=user_query)
                    session.messages.append(user_msg)
                    chat_db.update_session(session)
            except Exception as e:
                logger.error(f"Failed to persist user message: {e}")

        start_time = time.time()
        logger.info(f"🚀 ORCHESTRATION START | Query: {user_query[:100]}")
        
        # Initialize profile state
        profile_state = user_profile_state or {}
        
        # Long-term Memory: Restore missing fields from historical sessions in data/negotiations
        profile_state = self._restore_profile_from_history(user_id, profile_state)
        
        # Identity Awareness: Fetch and merge data from the registered profile (users.json)
        profile_state = self._enrich_with_persisted_profile(user_id, profile_state)
        
        # Check if this is an auto-negotiation trigger
        if "[AUTO_NEGOTIATE]" in user_query:
            logger.info("⚡ AUTO-NEGOTIATION detected")
            return await self._handle_auto_negotiation(user_id, user_query, history, profile_state)
        
        logger.info(f"📊 Profile state: {profile_state}")
        
        # 2. Detect if user mentions trade-in OR if we are already in trade-in flow
        step_start = time.time()
        trade_in_explicit = await self._detect_trade_in_mention(user_query)
        
        # Check if we have partial trade-in data in the profile
        existing_trade_in = profile_state.get('profil_extraction', {}).get('trade_in_vehicle_details', {})
        trade_in_detected = trade_in_explicit or (bool(existing_trade_in) and any(existing_trade_in.values()))
        
        logger.info(f"🔍 Trade-in detection: Explicit={trade_in_explicit} | Context={bool(existing_trade_in)} => {trade_in_detected} ({time.time() - step_start:.2f}s)")
        
        # 3. Extract profile information FIRST (to be reactive in the same turn)
        step_start = time.time()
        # Find which field is CURRENTLY missing to help extraction
        _, current_missing, _ = self._check_profile_completion(profile_state, user_query)
        extracted_profile_data = await self._extract_profile_from_message(user_query, current_missing)
        logger.info(f"📝 Extracted data: {extracted_profile_data} ({time.time() - step_start:.2f}s)")
        
        # Merge extracted data into current profile_state for immediate use in completion check
        if extracted_profile_data.get('profil_extraction'):
            if 'profil_extraction' not in profile_state:
                profile_state['profil_extraction'] = {}
            # Deep merge simple fields
            for k, v in extracted_profile_data['profil_extraction'].items():
                if v: # Only update if we found something
                    profile_state['profil_extraction'][k] = v
        
        # 4. NOW check profile completion with the updated state
        step_start = time.time()
        profile_complete, missing_field, next_question = self._check_profile_completion(profile_state, user_query)
        logger.info(f"✅ Profile complete: {profile_complete} | Missing: {missing_field} ({time.time() - step_start:.2f}s)")
        
        # 5. Query Classification & Routing
        step_start = time.time()
        
        try:
            # Fast Path: Heuristic Classification
            intent = self._classify_intent_heuristic(user_query, history)
            
            if not intent:
                # Slow Path: LLM Fallback (only if ambiguous)
                classification_prompt = f"""
                Analyze current message and history to determine intent.
                History: {json.dumps(history[-3:] if history else [], default=str)}
                Current Query: "{user_query}"
                
                Is this a car transaction request (buy, sell, trade-in, estimate price)? 
                Return "TRANSACTION" or "GENERAL".
                """
                class_res = await self.user_agent.agent.arun(classification_prompt)
                intent = "GENERAL" if "GENERAL" in str(class_res.content).upper() else "TRANSACTION"
                
            logger.info(f"🎯 Intent classified: {intent} ({time.time() - step_start:.2f}s)")
        except Exception as e:
            logger.error(f"❌ Error during intent classification: {e}", exc_info=True)
            intent = "GENERAL"  # Default to general if classification fails
            logger.info(f"🎯 Intent defaulted to: {intent}")
        
        # 5. Handle different intents
        try:
            if trade_in_detected:
                logger.info("🔍 Entering trade-in handling block")
                # User mentioned trade-in, check if we have enough data
                extracted_data = extracted_profile_data.get('profil_extraction', {})
                trade_in_details = extracted_data.get('trade_in_vehicle_details', {})
                
                # Check completeness of trade-in data
                required_trade_in_fields = ['brand', 'model', 'year', 'mileage']
                missing_trade_in_fields = [field for field in required_trade_in_fields if not trade_in_details.get(field)]
                
                logger.info(f"🚗 Trade-in data: {trade_in_details}")
                logger.info(f"❓ Missing fields: {missing_trade_in_fields}")
                
                if not missing_trade_in_fields:
                    # All data present! Trigger auto-negotiation immediately
                    logger.info("✅ Complete trade-in data detected - Auto-negotiating")
                    
                    # Build enriched query for auto-negotiation
                    auto_neg_query = f"[AUTO_NEGOTIATE] Client veut acheter. Profil: {json.dumps(profile_state, default=str)} | Reprise: {json.dumps(trade_in_details, default=str)} | Préférences: {json.dumps(extracted_data.get('vehicle_preferences', {}), default=str)}"
                    
                    return await self._save_and_return(session_id, await self._handle_auto_negotiation(user_id, auto_neg_query, history, profile_state, session_id=session_id))
                
                elif len(missing_trade_in_fields) <= 2:
                    # Some data missing - Ask conversationally
                    field_questions = {
                        'brand': "Quelle est la marque de votre véhicule à reprendre ?",
                        'model': "Quel est le modèle exact ?",
                        'year': "De quelle année est-il ?",
                        'mileage': "Quel est son kilométrage actuel ?",
                        'condition': "Dans quel état général se trouve-t-il ? (Excellent, Bon, Moyen...)"
                    }
                    
                    # Build conversational response with context
                    current_info = ", ".join([f"{k}: {v}" for k, v in trade_in_details.items() if v])
                    next_question = field_questions.get(missing_trade_in_fields[0])
                    
                    chat_message = f"Parfait ! J'ai noté : {current_info}. {next_question}"
                    
                    return await self._save_and_return(session_id, {
                        "status": "success",
                        "chat_response": chat_message,
                        "ui_action": {
                            "type": "ASK_TRADE_IN_QUESTION",
                            "missing_fields": missing_trade_in_fields
                        },
                        "profile_data_extracted": extracted_profile_data,
                        "intent": "TRADE_IN_INQUIRY"
                    })
                
                else:
                    # Too much missing data - Show form
                    return await self._save_and_return(session_id, {
                        "status": "success",
                        "chat_response": "Parfait ! Pour évaluer votre reprise au meilleur prix, j'ai besoin de quelques détails sur votre véhicule. Veuillez remplir le formulaire ci-dessous 👇",
                        "ui_action": {
                            "type": "SHOW_TRADE_IN"
                        },
                        "profile_data_extracted": extracted_profile_data,
                        "intent": "TRADE_IN"
                    })
            
            # 5a. CASE: Intent is GENERAL
            # We prioritize a conversational response (handles greetings, off-topic, help)
            # Even if the profile is incomplete, we answer the question first.
            if intent == "GENERAL":
                # Check if it's a simple greeting to use the warm template
                greeting_keywords = ["hi", "hello", "bonjour", "salut", "hey", "bonsoir", "coucou"]
                is_simple_greeting = any(keyword in user_query.lower().strip() for keyword in greeting_keywords) and len(user_query.strip().split()) <= 3
                
                if is_simple_greeting and not profile_complete:
                    chat_prompt = f"""
                    Tu es OMEGA, l'assistant commercial privilégié d'un showroom automobile au Maroc.
                    Le client vient de te saluer : "{user_query}"
                    Réponds chaleureusement et présente-toi brièvement.
                    Mentionne que tu peux l'aider pour l'achat, la reprise ou le financement.
                    Sois accueillant et professionnel. PAS de JSON.
                    """
                else:
                    # Advanced conversational response (handles off-topic and identity)
                    # Fetch persisted info for identity awareness
                    persisted_user = get_user_by_id(user_id) or {}
                    
                    chat_prompt = f"""
                    Tu es OMEGA, l'assistant commercial privilégié d'un showroom automobile au Maroc.
                    
                    CONTEXTE IDENTITÉ (Données de ton interlocuteur) :
                    - Nom : {persisted_user.get('full_name', 'Client OMEGA')}
                    - Ville : {persisted_user.get('city', 'Inconnue')}
                    - Revenu : {persisted_user.get('income_mad', 'Inconnu')} MAD/mois
                    - Contrat : {persisted_user.get('financials', {}).get('contract_type', 'Inconnu')}
                    
                    Historique : {json.dumps(history[-5:] if history else [], default=str)}
                    Client : "{user_query}"
                    
                    Réponds de manière chaleureuse, professionnelle et intelligente SANS JSON.
                    
                    STRATÉGIE DE RÉPONSE :
                    1. **Identité** : Si le client demande qui il est, ou ce que tu sais de lui, utilise le CONTEXTE IDENTITÉ ci-dessus.
                    2. **Salutations** : Si c'est le début, souhaite la bienvenue en utilisant son nom si disponible.
                    3. **Questions automobiles** : Réponds avec expertise.
                    4. **Questions HORS-SUJET** : Réponds brièvement puis Trouve un LIEN CRÉATIF avec l'automobile puis redirige vers l'automobile.
                    5. **TON** : Conversationnel, créatif et engageant.
                    
                    IMPORTANT: Retourne UNIQUEMENT le texte, PAS de JSON.
                    """

                chat_res = await self.user_agent.agent.arun(chat_prompt)
                raw_content = getattr(chat_res, "content", "Bonjour ! Je suis OMEGA, votre assistant automobile.")
                chat_message = self._extract_clean_message(raw_content)

                # If profile is NOT complete, append a gentle reminder
                if not profile_complete:
                    nudge = f"\n\nAu fait, pour mieux vous accompagner dans votre projet, pourriez-vous me préciser votre **{missing_field}** ? 📍"
                    if "ville" in missing_field.lower():
                        nudge = f"\n\nJuste une petite chose : dans quelle **ville** êtes-vous situé ? Cela m'aidera à personnaliser mes offres pour vous. 📍"
                    elif "revenu" in missing_field.lower():
                        nudge = f"\n\nPour affiner nos solutions de financement, quel est votre **revenu mensuel** approximatif ? 💰"
                    
                    chat_message += nudge

                return await self._save_and_return(session_id, {
                    "status": "success",
                    "chat_response": chat_message,
                    "profile_data_extracted": extracted_profile_data,
                    "profile_completion": self._calculate_profile_completion(profile_state),
                    "intent": "GREETING" if is_simple_greeting else "GENERAL"
                })

            # 5b. CASE: Profile NOT complete (and intent is NOT GENERAL, likely TRANSACTION)
            elif not profile_complete:
                # Force profile question for transactional intents
                prefix = "C'est noté pour votre projet ! "
                car_details = extracted_profile_data.get('profil_extraction', {}).get('vehicle_preferences', {})
                if car_details.get('model'):
                    prefix = f"Excellente idée pour la {car_details.get('model')} ! "
                
                chat_message = f"{prefix}Avant d'entrer dans les détails de la négociation, j'ai besoin d'une petite précision : {next_question}"
                
                return await self._save_and_return(session_id, {
                    "status": "success",
                    "chat_response": chat_message,
                    "ui_action": {
                        "type": "ASK_PROFILE_QUESTION",
                        "field_to_collect": missing_field
                    },
                    "profile_data_extracted": extracted_profile_data,
                    "profile_completion": self._calculate_profile_completion(profile_state),
                    "intent": "PROFILE_BUILDING"
                })

            # 5c. CASE: Profile COMPLETE & TRANSACTION
            elif intent == "TRANSACTION":
                logger.info("🎯 Profile complete & TRANSACTION intent -> Triggering Auto-Negotiation")
                auto_neg_query = f"[AUTO_NEGOTIATE] Client prêt pour transaction. Profil complet: {json.dumps(profile_state, default=str)} | Query: {user_query}"
                return await self._save_and_return(session_id, await self._handle_auto_negotiation(user_id, auto_neg_query, history, profile_state, session_id=session_id))
        except Exception as e:
            logger.error(f"❌ Error in orchestration flow: {e}", exc_info=True)
            return await self._save_and_return(session_id, {
                "status": "error",
                "chat_response": "Une erreur est survenue. Veuillez réessayer.",
                "intent": "ERROR"
            })

        # --- TRANSACTIONAL FLOW (The existing pipeline) ---
        logger.info("💼 Starting TRANSACTION flow")
        
        # 1. Assess User Profile (with state)
        step_start = time.time()
        user_profile = await self.user_agent.assess_fiscal_health(user_id, user_query, current_profile_data=profile_state)
        logger.info(f"👤 User profile assessed ({time.time() - step_start:.2f}s)")
        
        # 2 & 3. Run Valuation and Market Analysis in PARALLEL for speed
        step_start = time.time()
        valuation_data = None
        market_data = None
        
        # Prepare parallel tasks
        tasks = []
        task_names = []
        
        # Add valuation task if trade-in present
        if user_profile.trade_in and user_profile.trade_in.model:
            tasks.append(self.valuation_agent.appraise_vehicle(user_profile.trade_in.model_dump()))
            task_names.append("valuation")
        
        # Add market analysis task if preferences exist
        brand = user_profile.preferences.brands[0] if user_profile.preferences.brands else None
        if brand or user_profile.preferences.category:
            tasks.append(self.market_agent.analyze_market(
                model=user_profile.preferences.category or "SUV",
                brand=brand,
                user_budget=user_profile.financials.max_budget_mad
            ))
            task_names.append("market")
        
        # Execute in parallel
        if tasks:
            results = await asyncio.gather(*tasks)
            
            # Assign results based on what was requested
            for i, task_name in enumerate(task_names):
                if task_name == "valuation":
                    valuation_data = results[i]
                elif task_name == "market":
                    market_data = results[i]
            
            logger.info(f"🚗📊 Valuation + Market analysis completed in parallel ({time.time() - step_start:.2f}s)")

        # 4. Negotiation Step
        negotiated_terms = None
        if market_data:
            step_start = time.time()
            negotiated_terms = await self.negotiation_agent.negotiate(
                user_data=user_profile.model_dump(),
                valuation_data=valuation_data,
                market_data=market_data
            )
            logger.info(f"🤝 Negotiation completed ({time.time() - step_start:.2f}s)")

        # 5. Business Validation
        validation_result = None
        if negotiated_terms:
            step_start = time.time()
            validation_result = await self.business_agent.validate_final_offer({
                "negotiated_terms": negotiated_terms.model_dump(),
                "user_profile": user_profile.model_dump(),
                "market_data": market_data
            })
            logger.info(f"✅ Business validation completed ({time.time() - step_start:.2f}s)")

        # 6. Offer Structuring
        structured_offer = None
        if validation_result and validation_result.is_approved:
            step_start = time.time()
            structured_offer = await self.structuring_agent.structure_offer({
                "user_profile": user_profile.model_dump(),
                "negotiated_terms": negotiated_terms.model_dump(),
                "valuation": valuation_data,
                "validation": validation_result.model_dump()
            })
            logger.info(f"📄 Offer structuring completed ({time.time() - step_start:.2f}s)")

        # 7. Generate Chat Response (Communication Step)
        chat_prompt = f"""
        Tu es OMEGA, l'assistant commercial privilégié d'un showroom automobile au Maroc.
        Données actuelles :
        - Profil : {user_profile.model_dump_json()}
        - Reprise : {json.dumps(valuation_data)}
        - Offre Finale : {structured_offer.model_dump_json() if structured_offer else "Aucune offre générée"}

        TACHE : Rédige une réponse DIRECTE et CHALEUREUSE pour le client.
        - Ne renvoie JAMAIS de JSON, de clés techniques ou de métadonnées.
        - Parle comme un humain expert et accueillant.
        - Si c'est une simple salutation, propose ton aide avec enthousiasme.
        - Si des infos manquent pour une offre, demande-les avec courtoisie.
        - Ta réponse sera affichée DIRECTEMENT au client dans le chatbot.
        """
        
        try:
            chat_res = await self.user_agent.agent.arun(chat_prompt)
            raw_content = getattr(chat_res, "content", str(chat_res))
            
            # Extract clean message using helper method
            chat_message = self._extract_clean_message(raw_content)
            
        except Exception as e:
            print(f"DEBUG: Error generating chat response: {e}")
            chat_message = "Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd'hui ?"

        print(f"DEBUG: Final Chat Message for User: {chat_message[:100]}...")

        # 8. Consolidate results
        total_time = time.time() - start_time
        logger.info(f"\u2705 ORCHESTRATION COMPLETE | Total time: {total_time:.2f}s")
        
        return await self._save_and_return(session_id, {
            "status": "success",
            "chat_response": chat_message,
            "user_profile": user_profile.model_dump(),
            "valuation": valuation_data,
            "market_analysis": market_data,
            "negotiated_offer": negotiated_terms.model_dump() if negotiated_terms else None,
            "business_validation": validation_result.model_dump() if validation_result else None,
            "final_structured_offer": structured_offer.model_dump() if structured_offer else None,
            "profile_completion": 100, # If we finished transaction, profile must be complete
            "orchestration_metadata": {
                "user_id": user_id,
                "timestamp": str(asyncio.get_event_loop().time())
            }
        })

    def _extract_clean_message(self, raw_content: str) -> str:
        """
        Extract clean conversational message from potentially JSON-formatted AI response.
        Handles nested JSON structures and extracts human-readable text.
        """
        import re
        
        try:
            chat_message = raw_content.strip()
            
            # If the agent returned JSON (even nested)
            if "{" in chat_message:
                try:
                    match = re.search(r"(\{.*\})", chat_message, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        
                        # Function to search for a key in nested dict
                        def find_key(d, key):
                            if key in d: return d[key]
                            for k, v in d.items():
                                if isinstance(v, dict):
                                    res = find_key(v, key)
                                    if res: return res
                            return None

                        # Search for human response in priority order
                        chat_message = (
                            find_key(data, "reply") or 
                            find_key(data, "content") or 
                            find_key(data, "message") or 
                            chat_message
                        )
                except:
                    pass

            # Clean markdown code blocks and whitespace
            chat_message = re.sub(r'```json|```', '', chat_message).strip()
            
            # If it's still raw JSON, use fallback
            if chat_message.startswith('{'):
                chat_message = "Bonjour ! Je suis OMEGA. Comment puis-je vous aider aujourd'hui ?"
            
            return chat_message
            
        except Exception as e:
            print(f"DEBUG: Error extracting clean message: {e}")
            return "Bonjour ! Je suis OMEGA. Comment puis-je vous aider dans votre projet automobile aujourd'hui ?"

    async def _detect_trade_in_mention(self, user_query: str) -> bool:
        """Detect if user mentions trade-in/reprise in their message."""
        keywords = ["reprise", "trade-in", "échanger", "échange", "vendre ma", "reprendre", "ancienne voiture"]
        query_lower = user_query.lower()
        return any(keyword in query_lower for keyword in keywords)
    
    def _check_profile_completion(self, profile_state: Dict, user_query: str) -> tuple[bool, str, str]:
        """
        Check profile completion and determine next question to ask.
        Returns: (is_complete, missing_field, next_question)
        """
        required_fields = {
            "city": "Pour mieux vous servir, dans quelle ville êtes-vous situé ? 📍",
            "monthly_income": "Quel est votre revenu mensuel approximatif ? (Cette information reste confidentielle) 💰",
            "contract_type": "Quel type de contrat avez-vous ? (CDI, CDD, Fonctionnaire, etc.)",
        }
        
        # Fix: Extract from nesting if exists
        data = profile_state.get('profil_extraction', {}) if 'profil_extraction' in profile_state else profile_state
        
        for field, question in required_fields.items():
            if not data.get(field):
                return False, field, question
        
        return True, None, None
    
    async def _extract_profile_from_message(self, user_query: str, expected_field: str = None) -> Dict:
        """Extract profile and trade-in information from user's message using LLM."""
        extraction_prompt = f"""
        Analyse le message de l'utilisateur et extrait toutes les informations pertinentes pour un showroom automobile.
        Message: "{user_query}"
        
        Retourne UNIQUEMENT un JSON structuré comme suit :
        {{
            "profil_extraction": {{
                "city": "nom de ville ou null",
                "monthly_income": "montant numérique ou null",
                "contract_type": "CDI/CDD/Fonctionnaire/etc ou null",
                "vehicle_preferences": {{
                    "brands": ["Peugeot", etc],
                    "model": "3008",
                    "category": "SUV/Berline/etc"
                }},
                "trade_in_vehicle_details": {{
                    "brand": "Marque du véhicule actuel",
                    "model": "Modèle du véhicule actuel",
                    "year": "Année (entier)",
                    "mileage": "Kilométrage (entier)",
                    "condition": "Excellent/Bon/Moyen"
                }}
            }}
        }}
        
        Sois précis et n'extrait que ce qui est explicitement mentionné ou fortement suggéré.
        """
        
        try:
            res = await self.user_agent.agent.arun(extraction_prompt)
            content = getattr(res, "content", "{}")
            
            # Parse JSON response
            import re
            if "{" in content:
                match = re.search(r"(\{.*\})", content, re.DOTALL)
                if match:
                    extracted = json.loads(match.group(1))
                    
                    # Recursive function to remove none/null values
                    def remove_none(obj):
                        if isinstance(obj, dict):
                            return {k: v for k, v in ((k, remove_none(v)) for k, v in obj.items()) if v is not None}
                        elif isinstance(obj, list):
                            return [v for v in (remove_none(v) for v in obj) if v is not None]
                        return obj

                    return remove_none(extracted)
        except:
            pass
        
        return {}
    
    def _calculate_profile_completion(self, profile_state: Dict) -> int:
        """Calculate profile completion percentage."""
        required_fields = ["city", "monthly_income", "contract_type"]
        data = profile_state.get('profil_extraction', {}) if 'profil_extraction' in profile_state else profile_state
        completed = sum(1 for field in required_fields if data.get(field))
        return int((completed / len(required_fields)) * 100)
    
    async def _handle_auto_negotiation(self, user_id: int, user_query: str, history: List[Dict[str, str]], profile_state: Dict = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle automatic negotiation trigger after trade-in form submission.
        Runs full pipeline and returns final offer.
        """
        logger.info(f"⚡ AUTO-NEGOTIATION: Starting full pipeline with profile_state: {bool(profile_state)}")
        
        try:
            # 1. Assess User Profile
            step_start = time.time()
            logger.info(f"🔍 Assessing user profile for user_id={user_id}")
            
            try:
                # Pass both query and current state to assessment agent
                user_profile = await self.user_agent.assess_fiscal_health(user_id, user_query, current_profile_data=profile_state)
                logger.info(f"👤 User profile assessed ({time.time() - step_start:.2f}s)")
            except Exception as e:
                logger.error(f"❌ Error assessing user profile: {e}", exc_info=True)
                return {
                    "status": "error",
                    "chat_response": "Désolé, une erreur est survenue lors de l'analyse de votre profil. Veuillez réessayer.",
                    "intent": "ERROR"
                }
            
            # 2 & 3. Run Valuation and Market Analysis
            step_start = time.time()
            valuation_data = None
            market_data = None
            
            tasks = []
            task_names = []
            
            logger.info(f"🔍 Preparing analysis tasks...")
            
            if user_profile.trade_in and user_profile.trade_in.model:
                logger.info(f"📊 Adding valuation task for: {user_profile.trade_in.model}")
                tasks.append(self.valuation_agent.appraise_vehicle(user_profile.trade_in.model_dump()))
                task_names.append("valuation")
            
            brand = user_profile.preferences.brands[0] if user_profile.preferences.brands else None
            if brand or user_profile.preferences.category:
                logger.info(f"📈 Adding market analysis task for: {brand or user_profile.preferences.category}")
                tasks.append(self.market_agent.analyze_market(
                    model=user_profile.preferences.category or "SUV",
                    brand=brand,
                    user_budget=user_profile.financials.max_budget_mad
                ))
                task_names.append("market")
            
            if tasks:
                try:
                    results = await asyncio.gather(*tasks)
                    for i, task_name in enumerate(task_names):
                        if task_name == "valuation":
                            valuation_data = results[i]
                            logger.info(f"✅ Valuation completed: {valuation_data}")
                        elif task_name == "market":
                            market_data = results[i]
                            logger.info(f"✅ Market analysis completed")
                    logger.info(f"🚗📊 Valuation + Market analysis completed ({time.time() - step_start:.2f}s)")
                except Exception as e:
                    logger.error(f"❌ Error during valuation/market analysis: {e}", exc_info=True)
                    return {
                        "status": "error",
                        "chat_response": "Une erreur est survenue lors de l'analyse du marché. Veuillez réessayer.",
                        "intent": "ERROR"
                    }

            # Create Negotiation Session
            logger.info("🏗️ Creating negotiation session...")
            
            # Structure the initial offer data
            initial_offer_data = {
                "user_profile": user_profile.model_dump(),
                "valuation": valuation_data,
                "market_data": market_data
            }
            
            # Create session in DB
            try:
                # Check for existing active session first
                existing_session = negotiation_db.get_active_session_by_user(user_id)
                if existing_session:
                    logger.info(f"⚠️ Found existing session {existing_session.session_id}, marking as expired")
                    existing_session.status = "expired"
                    negotiation_db.update_session(existing_session)
                
                session_create = NegotiationSessionCreate(
                    user_id=user_id,
                    initial_offer_data=initial_offer_data,
                    max_rounds=5
                )
                
                logger.info("💾 Saving session to database...")
                session = negotiation_db.create_session(session_create)
                logger.info(f"✅ Session created: {session.session_id}")
                
                # Generate initial offer using NegotiationAgent
                logger.info("🤖 Generating initial negotiation offer...")
                try:
                    initial_offer = await self.negotiation_agent.start_negotiation(
                        user_data=initial_offer_data.get('user_profile', {}),
                        valuation_data=initial_offer_data.get('valuation', {}),
                        market_data=initial_offer_data.get('market_data', {})
                    )
                    logger.info(f"✅ Initial offer generated: {initial_offer.offer_price_mad} MAD")
                except Exception as e:
                    logger.error(f"❌ Error generating initial offer: {e}", exc_info=True)
                    return {
                        "status": "error",
                        "chat_response": "Une erreur est survenue lors de la génération de l'offre. Veuillez réessayer.",
                        "intent": "ERROR"
                    }
                
                # Update session with initial offer
                logger.info("💾 Updating session with initial offer...")
                try:
                    session.current_offer_data = initial_offer.model_dump(mode='json')
                    negotiation_db.update_session(session)
                    logger.info("✅ Session updated with offer data")
                except Exception as e:
                    logger.error(f"❌ Error updating session with offer: {e}", exc_info=True)
                    # Continue anyway - we can still return the offer
                
                # Add to history
                logger.info("📝 Adding to negotiation history...")
                try:
                    from app.schemas.negotiation_session import NegotiationHistoryCreate
                    negotiation_db.add_history(NegotiationHistoryCreate(
                        session_id=session.session_id,
                        round_number=1,
                        speaker="agent",
                        message=initial_offer.marketing_message,
                        offer_data=initial_offer.model_dump(mode='json'),
                        action="propose"
                    ))
                    logger.info("✅ History entry added")
                except Exception as e:
                    logger.error(f"❌ Error adding history: {e}", exc_info=True)
                    # Continue anyway
                
                logger.info(f"🎉 Negotiation Session Created Successfully: {session.session_id}")
                
                # Prepare response
                try:
                    response_data = {
                        "status": "success",
                        "chat_response": initial_offer.marketing_message,
                        "user_profile": user_profile.model_dump(),
                        "valuation": valuation_data,
                        "market_analysis": market_data,
                        "ui_action": {
                            "type": "START_NEGOTIATION",
                            "session_id": session.session_id,
                            "initial_offer": initial_offer.model_dump(mode='json'),
                            "max_rounds": 5,
                            "current_round": 1
                        },
                        "intent": "AUTO_NEGOTIATE"
                    }
                    logger.info("✅ Response data prepared successfully")
                    return response_data
                except Exception as e:
                    logger.error(f"❌ Error preparing response data: {e}", exc_info=True)
                    return {
                        "status": "error",
                        "chat_response": "Une erreur est survenue lors de la préparation de la réponse. Veuillez réessayer.",
                        "intent": "ERROR"
                    }
                
            except Exception as e:
                logger.error(f"❌ Error creating negotiation session: {e}", exc_info=True)
                return {
                    "status": "error",
                    "chat_response": "Une erreur est survenue lors de la création de la session de négociation. Veuillez réessayer plus tard.",
                    "intent": "ERROR"
                }
        
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in auto-negotiation flow: {e}", exc_info=True)
            return {
                "status": "error",
                "chat_response": "Une erreur critique est survenue. Veuillez réessayer plus tard.",
                "intent": "ERROR"
            }

    def _classify_intent_heuristic(self, user_query: str, history: List[Dict]) -> str:
        """
        Fast heuristic intent classification to avoid LLM overhead.
        Returns 'TRANSACTION', 'GENERAL', or None (ambiguous, use LLM).
        """
        query_lower = user_query.lower()
        
        # 1. Explicit System Triggers
        if "[auto_negotiate]" in query_lower:
            return "TRANSACTION"
        
        # 2. Strong Transactional Keywords
        # Presence of ANY of these indicates a business intent
        transaction_keywords = [
            "buy", "sell", "price", "cost", "offer", "discount", 
            "deal", "budget", "financing", "loan", "credit",
            "acheter", "vendre", "prix", "coût", "offre", "remise",
            "budget", "financement", "crédit", "leasing", "lld", 
            "reprise", "exchange", "échange", "trade", "trade-in",
            "estimat", "quote", "devis", "facture", "contract", "contrat",
            "dacia", "peugeot", "renault", "citroen", "volkswagen",
            "audi", "bmw", "mercedes", "toyota", "hyundai", "kia",
            "sandero", "clio", "208", "3008", "duster", "stepway"
        ]
        
        if any(w in query_lower for w in transaction_keywords):
            return "TRANSACTION"
            
        # 3. Numeric Answers in Transactional Contexts
        import re
        if re.match(r'^\d+(\s*(dh|mad|km|ans))?$', query_lower.strip()):
             if history and history[-1].get("role") == "assistant":
                 return "TRANSACTION"

        # 4. Strong General/Chit-Chat Keywords (Short messages only)
        word_count = len(query_lower.split())
        greeting_keywords = ["bonjour", "salut", "hello", "hi", "coucou", "hey", "merci", "thanks", "ok", "d'accord", "bye", "au revoir"]
        
        if word_count <= 5 and any(w in query_lower for w in greeting_keywords):
            return "GENERAL"

        # 5. Ambiguous -> Return None to trigger LLM fallback
        return None

    def _restore_profile_from_history(self, user_id: int, current_state: Dict) -> Dict:
        """
        Look into historical sessions in data/negotiations to fill missing profile fields.
        """
        # Fields we want to restore
        required_fields = ["city", "monthly_income", "contract_type"]
        
        # Ensure 'profil_extraction' exists in state
        if 'profil_extraction' not in current_state:
            current_state['profil_extraction'] = {}
            
        extraction = current_state['profil_extraction']
        missing = [f for f in required_fields if not extraction.get(f)]
        
        if not missing:
            return current_state
            
        logger.info(f"🧠 Attempting to restore {missing} from history for user {user_id}")
        
        try:
             # Load all sessions
             sessions = negotiation_db._load_sessions()
             user_sessions = [s for s in sessions.values() if s.get('user_id') == user_id]
             
             # Sort by creation date (newest first)
             user_sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
             
             for session in user_sessions:
                 # 1. Look in initial_offer_data.user_profile (Preferred source)
                 offer_data = session.get('initial_offer_data', {})
                 profile = offer_data.get('user_profile', {})
                 
                 # 2. Look in financials if profile is sparse
                 financials = profile.get('financials', {})
                 
                 # Robust Mapping
                 mappings = {
                     'city': profile.get('city') or offer_data.get('city'),
                     'monthly_income': profile.get('income_mad') or financials.get('income_mad') or financials.get('monthly_income'),
                     'contract_type': financials.get('contract_type') or profile.get('contract_type')
                 }
                 
                 # Fill missing
                 for field in list(missing):
                     val = mappings.get(field)
                     if val is not None and val != "":
                         current_state['profil_extraction'][field] = val
                         missing.remove(field)
                         logger.info(f"✨ Restored {field}: {val} (from session {session.get('session_id')})")
                         
                 if not missing:
                     break
                     
        except Exception as e:
            logger.error(f"❌ Error restoring profile from history: {e}")
            
        return current_state

    def _enrich_with_persisted_profile(self, user_id: int, current_state: Dict) -> Dict:
        """
        Fetch the user's registered profile from users.json and fill missing fields in profile_state.
        This provides identity awareness from the moment the user registers.
        """
        try:
            user = get_user_by_id(user_id)
            if not user:
                return current_state
            
            # Ensure 'profil_extraction' exists in state
            if 'profil_extraction' not in current_state:
                current_state['profil_extraction'] = {}
                
            extraction = current_state['profil_extraction']
            
            # Map fields from the registered profile to the expected extraction keys
            # Only fill if the field is currently missing or null
            if not extraction.get('city') and user.get('city'):
                extraction['city'] = user.get('city')
                logger.info(f"📍 Profile Enrich: Restored city from registered profile: {user.get('city')}")
                
            if not extraction.get('monthly_income') and user.get('income_mad'):
                extraction['monthly_income'] = user.get('income_mad')
                logger.info(f"💰 Profile Enrich: Restored income from registered profile: {user.get('income_mad')}")
                
            financials = user.get('financials', {})
            if not extraction.get('contract_type') and financials.get('contract_type'):
                extraction['contract_type'] = financials.get('contract_type')
                logger.info(f"📄 Profile Enrich: Restored contract_type from registered profile: {financials.get('contract_type')}")
                
            # Preferences can also be merged
            prefs = user.get('preferences', {})
            if 'vehicle_preferences' not in extraction:
                extraction['vehicle_preferences'] = {}
            
            v_prefs = extraction['vehicle_preferences']
            if not v_prefs.get('brands') and prefs.get('brands'):
                v_prefs['brands'] = prefs.get('brands')
            if not v_prefs.get('usage') and prefs.get('usage'):
                v_prefs['usage'] = prefs.get('usage')

        except Exception as e:
            logger.error(f"❌ Error enriching profile from users.json: {e}")
            
        return current_state

    async def _save_and_return(self, session_id: Optional[str], result: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to persist bot response and return result."""
        if session_id and result.get("chat_response"):
            try:
                session = chat_db.get_session(session_id)
                if session:
                    bot_msg = ChatMessage(role="assistant", content=result["chat_response"])
                    session.messages.append(bot_msg)
                    chat_db.update_session(session)
            except Exception as e:
                logger.error(f"Failed to persist bot message: {e}")
        return result





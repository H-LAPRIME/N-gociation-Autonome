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
from app.db_config import get_async_db

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
        
        # 0. Early Intent Heuristic & Rapid Greeting Response
        # Detect if this is just a social interaction to bypass slow agent pipelines
        intent = self._classify_intent_heuristic(user_query, history)
        
        # Rapid handling for very simple greetings (Instant response)
        greeting_keywords = ["hi", "hello", "bonjour", "salut", "hey", "bonsoir", "coucou", "ca va", "ça va", "merci"]
        query_words = user_query.lower().strip().split()
        is_simple_greeting = any(keyword in user_query.lower() for keyword in greeting_keywords) and len(query_words) <= 4
        
        if is_simple_greeting:
            logger.info("⚡ Rapid Response: Simple greeting detected")
            username = (user_profile_state or {}).get('full_name') or "cher client"
            
            # Use templates for instant response
            if any(w in user_query.lower() for w in ["hi", "hello", "bonjour", "bonsoir"]):
                chat_message = f"Bonjour {username} ! Je suis OMEGA. Comment puis-je vous accompagner aujourd'hui ? 🚗"
            elif "salut" in user_query.lower() or "coucou" in user_query.lower():
                chat_message = f"Salut {username} ! Ravi de vous voir. En quoi puis-je vous être utile ? ✨"
            elif "va" in user_query.lower():
                chat_message = f"Je vais très bien, merci {username} ! Toujours prêt à vous aider à trouver votre prochaine voiture. Et vous ? 😊"
            else:
                chat_message = f"Je vous en prie {username} ! Je reste à votre disposition pour toute question. 👍"
            
            return await self._save_and_return(session_id, {
                "status": "success",
                "chat_response": chat_message,
                "intent": "GREETING",
                "profile_completion": self._calculate_profile_completion(user_profile_state or {})
            })

        # 1. Initialize/Merge profile state using Database-integrated UserProfileAgent
        # (This is only done if the intent is not an instant greeting)
        step_start = time.time()
        user_profile = None
        async for db in get_async_db():
            user_profile = await self.user_agent.assess_fiscal_health(
                user_id=user_id,
                user_input=user_query,
                db=db
            )
            break
            
        if not user_profile:
            logger.warning("⚠️ Database profile assessment failed, using provided state")
            profile_state = user_profile_state or {}
        else:
            profile_state = user_profile.model_dump()
            profile_state['profil_extraction'] = {
                "city": user_profile.city,
                "monthly_income": user_profile.income_mad,
                "contract_type": user_profile.financials.contract_type if user_profile.financials else None,
                "vehicle_preferences": user_profile.preferences.model_dump() if user_profile.preferences else {},
                "trade_in_vehicle_details": user_profile.trade_in.model_dump() if user_profile.trade_in else {}
            }
        
        logger.info(f"👤 User profile assessment & DB sync completed ({time.time() - step_start:.2f}s)")

        # Redo intent if it was None (ambiguous) but now we have more profile context
        if intent is None:
            intent = self._classify_intent_heuristic(user_query, history)
            if not intent:
                # Still ambiguous? Short LLM call
                try:
                    classification_prompt = f"Analyze intent: '{user_query}'. Return 'TRANSACTION' or 'GENERAL'."
                    class_res = await self.user_agent.arun(classification_prompt)
                    intent = "GENERAL" if "GENERAL" in str(class_res.content).upper() else "TRANSACTION"
                except Exception as e:
                    logger.warning(f"⚠️ Intent classification failed after retries: {e}")
                    intent = "GENERAL"  # Safe default
            logger.info(f"🎯 Final Intent: {intent}")

        # Check if this is an auto-negotiation trigger (e.g. from form submission)
        if "[AUTO_NEGOTIATE]" in user_query:
            logger.info("⚡ AUTO-NEGOTIATION detected")
            return await self._handle_auto_negotiation(user_id, user_query, history, profile_state)
        
        # 2. Detect if user mentions trade-in or if we already have it
        step_start = time.time()
        trade_in_explicit = await self._detect_trade_in_mention(user_query)
        existing_trade_in = profile_state.get('profil_extraction', {}).get('trade_in_vehicle_details', {})
        trade_in_detected = trade_in_explicit or (bool(existing_trade_in) and any(existing_trade_in.values()))
        
        # 3. Check profile completion with the updated state
        step_start = time.time()
        profile_complete, missing_field, next_question = self._check_profile_completion(profile_state, user_query)
        logger.info(f"✅ Profile complete: {profile_complete} | Missing: {missing_field} ({time.time() - step_start:.2f}s)")
        
        # 5. Handle different intents
        try:
            if trade_in_detected:
                logger.info("🔍 Entering trade-in handling block")
                # User mentioned trade-in, check if we have enough data
                extracted_data = profile_state.get('profil_extraction', {})
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
                    auto_neg_query = f"[AUTO_NEGOTIATE] Client veut acheter. Profil: {json.dumps(profile_state, default=str)} | Reprise: {json.dumps(trade_in_details, default=str)}"
                    
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
                        "profile_data_extracted": profile_state,
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
                        "profile_data_extracted": profile_state,
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
                    persisted_user = profile_state
                    
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

                try:
                    chat_res = await self.user_agent.arun(chat_prompt)
                    raw_content = getattr(chat_res, "content", "Bonjour ! Je suis OMEGA, votre assistant automobile.")
                    chat_message = self._extract_clean_message(raw_content)
                except Exception as e:
                    logger.error(f"❌ General chat response failed: {e}")
                    chat_message = "Bonjour ! Je suis OMEGA. Comment puis-je vous aider aujourd'hui ?"

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
                    "profile_data_extracted": profile_state,
                    "profile_completion": self._calculate_profile_completion(profile_state),
                    "intent": "GREETING" if is_simple_greeting else "GENERAL"
                })

            # 5b. CASE: Profile NOT complete (and intent is NOT GENERAL, likely TRANSACTION)
            elif not profile_complete:
                # Force profile question for transactional intents
                prefix = "C'est noté pour votre projet ! "
                car_details = profile_state.get('profil_extraction', {}).get('vehicle_preferences', {})
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
                    "profile_data_extracted": profile_state,
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
        if brand or user_profile.preferences.category or user_profile.preferences.model:
            logger.info(f"📈 Adding market analysis task for: {brand or user_profile.preferences.model or user_profile.preferences.category}")
            tasks.append(self.market_agent.analyze_market(
                model=user_profile.preferences.model or user_profile.preferences.category or "SUV",
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
            chat_res = await self.user_agent.arun(chat_prompt)
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
            
            user_profile = None
            async for db in get_async_db():
                user_profile = await self.user_agent.assess_fiscal_health(
                    user_id=user_id,
                    user_input=user_query,
                    db=db
                )
                break
            
            if not user_profile:
                raise Exception("Failed to retrieve or create user profile in DB")

            logger.info(f"👤 User profile assessed ({time.time() - step_start:.2f}s)")
            
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
            if brand or user_profile.preferences.category or user_profile.preferences.model:
                search_model = user_profile.preferences.model or user_profile.preferences.category or "Voiture"
                logger.info(f"📈 Adding market analysis task for: {brand or search_model}")
                tasks.append(self.market_agent.analyze_market(
                    model=search_model,
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

            # --- NEW: Out of Stock Check ---
            if market_data and market_data.get('inventory', {}).get('stock_available', 0) == 0:
                logger.info(f"🚫 Stock zero detected for {market_data.get('target_model')}. Aborting negotiation.")
                
                # Use NegotiationAgent to generate a polite out-of-stock message if possible, 
                # or just return a standard one.
                target_model = market_data.get('target_model', 'ce modèle')
                target_brand = market_data.get('target_brand')
                category_name = market_data.get('market_overview', {}).get('category', 'véhicules')
                
                # Check if it was a generic "SUV" query and we have nothing
                if target_model.lower() == "suv" or not target_brand:
                    chat_response = "Je suis sincèrement désolé, mais nous n'avons actuellement aucun véhicule correspondant à vos critères dans notre showroom. Nous recevons régulièrement de nouveaux arrivages. Souhaitez-vous voir nos modèles les plus populaires ?"
                else:
                    chat_response = f"Je suis sincèrement désolé, mais après vérification de notre inventaire en temps réel, nous n'avons pas la {target_brand} {target_model} disponible actuellement. Cependant, nous avons d'autres {category_name} qui pourraient vous intéresser. Souhaitez-vous explorer des alternatives ?"
                
                return {
                    "status": "success",
                    "chat_response": chat_response,
                    "market_analysis": market_data,
                    "intent": "OUT_OF_STOCK"
                }
            # -------------------------------

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





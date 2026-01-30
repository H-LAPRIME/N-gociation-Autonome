"""
Negotiation API Endpoints
--------------------------
Manages the multi-turn negotiation workflow, including starting sessions,
processing counter-offers, and generating final contracts.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from app.schemas.negotiation_session import (
    NegotiationSessionCreate,
    NegotiationSession,
    NegotiationMessageRequest,
    NegotiationMessageResponse,
    NegotiationHistory
)
from app.database.negotiation_db import negotiation_db
from app.agents.NegotiationAgent import NegotiationAgent
from app.agents.BusinessConstraintAgent import BusinessConstraintAgent
from app.agents.OfferStructuringAgent import OfferStructuringAgent
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/negotiation", tags=["negotiation"])
logger = logging.getLogger(__name__)

negotiation_agent = NegotiationAgent()
business_agent = BusinessConstraintAgent()
offer_agent = OfferStructuringAgent()


@router.post("/start", response_model=NegotiationMessageResponse)
async def start_negotiation(
    session_data: NegotiationSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new negotiation session with initial offer.
    """
    try:
        # Check if user already has an active session
        existing_session = negotiation_db.get_active_session_by_user(session_data.user_id)
        if existing_session:
            raise HTTPException(
                status_code=400,
                detail=f"User already has an active negotiation session: {existing_session.session_id}"
            )
        
        # Create new session
        session = negotiation_db.create_session(session_data)
        
        # Generate initial offer using NegotiationAgent
        initial_offer = await negotiation_agent.start_negotiation(
            user_data=session_data.initial_offer_data.get('user_profile', {}),
            valuation_data=session_data.initial_offer_data.get('valuation', {}),
            market_data=session_data.initial_offer_data.get('market_data', {})
        )
        
        # Update session with initial offer
        session.current_offer_data = initial_offer.model_dump(mode='json')
        negotiation_db.update_session(session)
        
        # Add to history
        from app.schemas.negotiation_session import NegotiationHistoryCreate
        negotiation_db.add_history(NegotiationHistoryCreate(
            session_id=session.session_id,
            round_number=1,
            speaker="agent",
            message=initial_offer.marketing_message,
            offer_data=initial_offer.model_dump(mode='json'),
            action="propose"
        ))
        
        logger.info(f"✅ Negotiation started: {session.session_id}")
        
        return NegotiationMessageResponse(
            agent_response=initial_offer.marketing_message,
            revised_offer=initial_offer.model_dump(mode='json'),
            round=session.current_round,
            remaining_rounds=session.max_rounds - session.current_round,
            status=session.status,
            session_id=session.session_id
        )
    
    except Exception as e:
        logger.error(f"Error starting negotiation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/message", response_model=NegotiationMessageResponse)
async def send_negotiation_message(
    session_id: str,
    message_data: NegotiationMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message in an active negotiation session.
    """
    try:
        # Get session
        session = negotiation_db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Negotiation session not found")
        
        if session.status != "active":
            raise HTTPException(status_code=400, detail=f"Session is {session.status}, not active")
        
        # Add client message to history
        from app.schemas.negotiation_session import NegotiationHistoryCreate
        negotiation_db.add_history(NegotiationHistoryCreate(
            session_id=session_id,
            round_number=session.current_round,
            speaker="client",
            message=message_data.message,
            offer_data=message_data.counter_offer,
            action=message_data.action
        ))
        
        # Handle different actions
        if message_data.action == "accept":
            return await _handle_accept(session, message_data)
        elif message_data.action == "reject":
            session.status = "rejected"
            negotiation_db.update_session(session)
            return NegotiationMessageResponse(
                agent_response="Nous comprenons votre décision. N'hésitez pas à revenir vers nous si vous changez d'avis.",
                revised_offer=None,
                round=session.current_round,
                remaining_rounds=0,
                status="rejected",
                session_id=session_id
            )
        else:  # counter
            return await _handle_counter_offer(session, message_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing negotiation message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_accept(session: NegotiationSession, message_data: NegotiationMessageRequest):
    """Handle client accepting the offer"""
    logger.info(f"🎉 Client accepted offer in session {session.session_id}")
    
    # Validate with BusinessConstraintAgent
    validation = await business_agent.validate_final_offer({
        "negotiated_terms": session.current_offer_data,
        "user_profile": session.initial_offer_data.get('user_profile', {}),
        "market_data": session.initial_offer_data.get('market_data', {})
    })
    
    if not validation.is_approved:
        # Business rejected - need to revise
        logger.warning(f"⚠️ Business validation failed: {validation.violations}")
        
        # Move to next round and ask agent to revise
        session.current_round += 1
        if session.current_round > session.max_rounds:
            session.status = "max_rounds_reached"
            negotiation_db.update_session(session)
            return NegotiationMessageResponse(
                agent_response="Désolé, nous ne pouvons pas approuver cette offre selon nos contraintes business. Le nombre maximum de rounds est atteint.",
                revised_offer=None,
                round=session.current_round,
                remaining_rounds=0,
                status="max_rounds_reached",
                session_id=session.session_id
            )
        
        # Get revised offer
        history = negotiation_db.get_history(session.session_id)
        revised_offer = await negotiation_agent.process_counter_offer(
            session=session,
            client_message=f"L'offre précédente a été rejetée par le système. Violations: {', '.join(validation.violations)}",
            client_counter=None,
            conversation_history=[h.model_dump() for h in history]
        )
        
        session.current_offer_data = revised_offer.model_dump(mode='json')
        negotiation_db.update_session(session)
        
        return NegotiationMessageResponse(
            agent_response=f"Nous devons ajuster l'offre pour respecter nos contraintes. {revised_offer.marketing_message}",
            revised_offer=revised_offer.model_dump(mode='json'),
            round=session.current_round,
            remaining_rounds=session.max_rounds - session.current_round,
            status="active",
            session_id=session.session_id
        )
    
    # Approved! Generate final contract
    session.status = "validating"
    negotiation_db.update_session(session)
    
    try:
        # Generate PDF contract
        structured_offer = await offer_agent.structure_offer({
            "user_profile": session.initial_offer_data.get('user_profile', {}),
            "negotiated_terms": session.current_offer_data,
            "valuation": session.initial_offer_data.get('valuation', {}),
            "validation": validation.model_dump()
        })
        
        session.status = "completed"
        session.current_offer_data['contract_id'] = structured_offer.contract_id
        session.current_offer_data['pdf_reference'] = structured_offer.pdf_reference
        negotiation_db.update_session(session)
        
        logger.info(f"✅ Contract generated: {structured_offer.contract_id}")
        
        return NegotiationMessageResponse(
            agent_response=f"Félicitations ! Votre contrat est prêt. Numéro: {structured_offer.contract_id}",
            revised_offer=session.current_offer_data,
            round=session.current_round,
            remaining_rounds=0,
            status="completed",
            session_id=session.session_id
        )
    
    except Exception as e:
        logger.error(f"Error generating contract: {e}")
        session.status = "error"
        negotiation_db.update_session(session)
        raise


async def _handle_counter_offer(session: NegotiationSession, message_data: NegotiationMessageRequest):
    """Handle client counter-offer"""
    try:
        # Increment round
        session.current_round += 1
        
        # Check max rounds
        if session.current_round > session.max_rounds:
            session.status = "max_rounds_reached"
            negotiation_db.update_session(session)
            
            return NegotiationMessageResponse(
                agent_response=f"Nous avons atteint le nombre maximum de rounds ({session.max_rounds}). Voici notre offre finale: {session.current_offer_data.get('offer_price_mad')} MAD. Souhaitez-vous l'accepter ?",
                revised_offer=session.current_offer_data,
                round=session.current_round,
                remaining_rounds=0,
                status="max_rounds_reached",
                session_id=session.session_id
            )
        
        # Get conversation history
        try:
            history = negotiation_db.get_history(session.session_id)
        except Exception as e:
            logger.error(f"DEBUG: Failed to get history: {e}")
            raise HTTPException(status_code=500, detail=f"DEBUG: Failed to get history: {e}")

        # Process counter-offer with agent
        try:
            revised_offer = await negotiation_agent.process_counter_offer(
                session=session,
                client_message=message_data.message,
                client_counter=message_data.counter_offer,
                conversation_history=[h.model_dump(mode='json') for h in history]
            )
        except Exception as e:
            logger.error(f"DEBUG: Failed in process_counter_offer: {e}")
            # Ensure we see the type of e
            import traceback
            tb = traceback.format_exc()
            raise HTTPException(status_code=500, detail=f"DEBUG: Failed in process_counter_offer: {e} | TB: {tb}")
        
        # Update session
        try:
            session.current_offer_data = revised_offer.model_dump(mode='json')
            negotiation_db.update_session(session)
        except Exception as e:
            logger.error(f"DEBUG: Failed to update session: {e}")
            raise HTTPException(status_code=500, detail=f"DEBUG: Failed to update session: {e}")
        
        # Add agent response to history
        try:
            from app.schemas.negotiation_session import NegotiationHistoryCreate
            negotiation_db.add_history(NegotiationHistoryCreate(
                session_id=session.session_id,
                round_number=session.current_round,
                speaker="agent",
                message=revised_offer.marketing_message,
                offer_data=revised_offer.model_dump(mode='json'),
                action="counter"
            ))
        except Exception as e:
            logger.error(f"DEBUG: Failed to add history: {e}")
            raise HTTPException(status_code=500, detail=f"DEBUG: Failed to add history: {e}")
        
        logger.info(f"🔄 Counter-offer processed: Round {session.current_round}/{session.max_rounds}")
        
        return NegotiationMessageResponse(
            agent_response=revised_offer.marketing_message,
            revised_offer=revised_offer.model_dump(mode='json'),
            round=session.current_round,
            remaining_rounds=session.max_rounds - session.current_round,
            status=session.status,
            session_id=session.session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DEBUG: Error in _handle_counter_offer wrapper: {e}")
        raise HTTPException(status_code=500, detail=f"DEBUG: Error in _handle_counter_offer wrapper: {e}")


@router.get("/{session_id}/history", response_model=List[NegotiationHistory])
async def get_negotiation_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history for a negotiation session"""
    session = negotiation_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = negotiation_db.get_history(session_id)
    return history


@router.get("/{session_id}", response_model=NegotiationSession)
async def get_negotiation_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get negotiation session details"""
    session = negotiation_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.delete("/{session_id}")
async def reset_negotiation_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Reset (delete) a negotiation session"""
    success = negotiation_db.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    logger.info(f"🗑️ Negotiation session reset: {session_id}")
    return {"success": True, "message": f"Session {session_id} reset successfully"}

import streamlit as st
import asyncio
import httpx
import os
import sys
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="OMEGA - Votre Conseiller Automobile",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- LUXURY STYLING ---
st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }
    
    /* Header Styling */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(to right, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subtitle {
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Chat Message Styling */
    .stChatMessage {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    /* Agent Badge Styling */
    .agent-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 5px;
        background-color: #3b82f6;
        color: white;
    }
    
    /* Expander Styling */
    .stExpander {
        background-color: rgba(15, 23, 42, 0.5);
        border: none;
    }
    
    /* Input Box Styling */
    .stChatInputContainer {
        border-top: 1px solid rgba(148, 163, 184, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<h1 class="main-title">OMEGA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Votre assistant intelligent pour la vente et l\'achat de véhicules au Maroc.</p>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Bonjour ! Je suis **OMEGA**, votre conseiller automobile personnel. Comment puis-je vous aider aujourd'hui ?\n\nVous cherchez un modèle précis ou vous souhaitez faire estimer votre véhicule ?"}
    ]

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "city": None,
        "monthly_income": None,
        "contract_type": None,
        "phone": None
    }

if "trade_in" not in st.session_state:
    st.session_state.trade_in = {
        "brand": None,
        "model": None,
        "year": None,
        "mileage": None,
        "condition": None
    }

if "profile_completion" not in st.session_state:
    st.session_state.profile_completion = 0

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Décrivez votre projet (ex: Je veux une 3008 et vendre ma Dacia...)"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # API Configuration
    BACKEND_URL = "http://localhost:8000/orchestrate"

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔄 *OMEGA est en train de consulter ses agents experts...*")
        
        try:
            # Call FastAPI Backend
            with st.status("⚙️ Intelligence Collective OMEGA active", expanded=True) as status:
                st.write("🕵️ Connexion au serveur backend...")
                
                # Format history for the backend
                chat_history = [
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages[-6:] # Send last 3 turns
                ]
                
                # Get current profile state from session
                profile_state = st.session_state.get("user_profile", {})
                
                payload = {
                    "user_id": 1, 
                    "query": prompt,
                    "history": chat_history,
                    "user_profile_state": profile_state
                }
                response_api = httpx.post(BACKEND_URL, json=payload, timeout=120.0)  # Increased to 120s
                
                if response_api.status_code == 200:
                    result = response_api.json()
                    status.update(label="✅ Analyse complète !", state="complete", expanded=False)
                else:
                    st.error(f"Erreur Backend ({response_api.status_code}): {response_api.text}")
                    result = {}
                    status.update(label="❌ Erreur de communication", state="error", expanded=True)

            # Extract results
            raw_chat_msg = result.get("chat_response")
            chat_msg = raw_chat_msg if raw_chat_msg else "Je n'ai pas pu générer de réponse précise, mais je suis là pour vous aider !"
            ui_action = result.get("ui_action", {})
            profile_data_extracted = result.get("profile_data_extracted", {})
            st.session_state.profile_completion = result.get("profile_completion", st.session_state.get("profile_completion", 0))
            
            # Update profile state with extracted data
            if profile_data_extracted:
                data = profile_data_extracted.get("profil_extraction", {})
                
                # Update user profile
                if "user_profile" not in st.session_state:
                    st.session_state.user_profile = {}
                
                for field in ["city", "monthly_income", "contract_type", "phone"]:
                    if data.get(field):
                        st.session_state.user_profile[field] = data[field]
                
                # Update trade-in
                if "trade_in" not in st.session_state:
                    st.session_state.trade_in = {}
                
                trade_data = data.get("trade_in_vehicle_details", {})
                for field in ["brand", "model", "year", "mileage", "condition"]:
                    if trade_data.get(field):
                        st.session_state.trade_in[field] = trade_data[field]
            
            # Display friendly response from Orchestrator
            message_placeholder.markdown(chat_msg)
            
            # Handle UI Actions - Store in session state to persist across reruns
            if ui_action.get("type") == "SHOW_TRADE_IN_FORM":
                st.session_state.show_trade_in_form = True
            
            # Display trade-in form if flagged (persists across reruns)
            if st.session_state.get("show_trade_in_form", False):
                with st.form(key=f"trade_in_form_{len(st.session_state.messages)}"):
                    st.markdown("### 🚗 Formulaire de Reprise")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        trade_brand = st.text_input("Marque *", placeholder="Ex: Dacia, Peugeot...")
                        trade_year = st.number_input("Année *", min_value=1990, max_value=2026, value=2020)
                        trade_condition = st.selectbox("État général *", ["Excellent", "Très bon", "Bon", "Moyen", "À rénover"])
                    
                    with col2:
                        trade_model = st.text_input("Modèle *", placeholder="Ex: Logan, 208...")
                        trade_mileage = st.number_input("Kilométrage (km) *", min_value=0, max_value=500000, step=1000)
                        trade_accidents = st.radio("Accidents ?", ["Non", "Oui - légers", "Oui - graves"])
                    
                    submit_trade_in = st.form_submit_button("💾 Soumettre la reprise", type="primary", use_container_width=True)
                    
                    if submit_trade_in:
                        if trade_brand and trade_model:
                            # Store trade-in data
                            st.session_state.trade_in = {
                                "brand": trade_brand,
                                "model": trade_model,
                                "year": trade_year,
                                "mileage": trade_mileage,
                                "condition": trade_condition,
                                "accidents": trade_accidents
                            }
                            
                            # Hide form
                            st.session_state.show_trade_in_form = False
                            
                            # Show loading message
                            with st.spinner("🔄 Lancement de la négociation..."):
                                # Trigger auto-negotiation
                                auto_neg_query = f"[AUTO_NEGOTIATE] Profil: {json.dumps(st.session_state.get('user_profile', {}))} | Reprise: {json.dumps(st.session_state.trade_in)}"
                                
                                auto_payload = {
                                    "user_id": 1,
                                    "query": auto_neg_query,
                                    "history": chat_history,
                                    "user_profile_state": profile_state
                                }
                                
                                try:
                                    auto_response = httpx.post(BACKEND_URL, json=auto_payload, timeout=120.0)
                                    if auto_response.status_code == 200:
                                        auto_result = auto_response.json()
                                        st.success("✅ Reprise enregistrée ! Négociation en cours...")
                                        
                                        # Add to chat history
                                        st.session_state.messages.append({
                                            "role": "user",
                                            "content": f"Reprise: {trade_brand} {trade_model} ({trade_year}), {trade_mileage} km"
                                        })
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": auto_result.get("chat_response", "Analyse en cours...")
                                        })
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur lors de la négociation: {auto_response.status_code}")
                                except Exception as e:
                                    st.error(f"Erreur: {e}")
                        else:
                            st.error("Veuillez remplir au minimum la marque et le modèle.")
            
            # Add assistant response to history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": chat_msg
            })

        except Exception as e:
            st.error(f"Une erreur système est survenue : {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Oups, j'ai rencontré un problème technique : {e}"})

# Sidebar options
with st.sidebar:
    st.title("⚙️ État du Dossier OMEGA")
    
    # --- PROFILE COMPLETION SECTION ---
    st.write("---")
    completion = st.session_state.get("profile_completion", 0)
    st.subheader(f"📊 Complétion du Profil : {completion}%")
    st.progress(completion / 100)
    
    if completion < 100:
        st.info("💡 Continuez à discuter avec OMEGA pour compléter votre dossier et obtenir une offre personnalisée !")
    else:
        st.success("✅ Votre profil est complet ! OMEGA peut maintenant finaliser votre offre.")

    # --- USER PROFILE DATA SUMMARY ---
    st.write("---")
    st.subheader("👤 Informations Profil")
    
    profile = st.session_state.get("user_profile", {})
    if any(profile.values()):
        for key, value in profile.items():
            if value:
                label = {
                    "city": "📍 Ville",
                    "monthly_income": "💰 Revenu",
                    "contract_type": "📄 Contrat",
                    "bank_seniority": "🏦 Ancienneté Bank",
                    "monthly_debts": "💳 Dettes",
                    "phone": "📱 Téléphone"
                }.get(key, key.capitalize())
                st.write(f"**{label}** : {value}")
    else:
        st.write("*Aucune information profil détectée pour le moment.*")

    # --- TRADE-IN SUMMARY ---
    st.write("---")
    st.subheader("🚗 Véhicule en Reprise")
    
    trade_in = st.session_state.get("trade_in", {})
    if trade_in.get("brand") or trade_in.get("model"):
        st.write(f"**Marque/Modèle** : {trade_in.get('brand')} {trade_in.get('model')}")
        if trade_in.get("year"): st.write(f"**Année** : {trade_in.get('year')}")
        if trade_in.get("mileage"): st.write(f"**Kilométrage** : {trade_in.get('mileage')} km")
        if trade_in.get("condition"): st.write(f"**État** : {trade_in.get('condition')}")
    else:
        st.write("*Aucun véhicule en reprise détecté.*")

    # --- APP SETTINGS ---
    st.write("---")
    if st.button("🗑️ Réinitialiser la conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_profile = {}
        st.session_state.trade_in = {}
        st.session_state.profile_completion = 0
        st.rerun()

    st.write("---")
    st.write("**Statut Serveur**")
    try:
        # Simple health check
        health_resp = httpx.get("http://localhost:8000/", timeout=1.0)
        if health_resp.status_code == 200:
            st.success("🟢 Backend Connecté")
        else:
            st.warning("🟠 Backend Inaccessible")
    except:
        st.error("🔴 Backend Déconnecté")

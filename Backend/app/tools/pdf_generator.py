"""
Enhanced PDF Contract Generator for OMEGA
Generates professional car sale contracts with signatures
"""
import os
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
import qrcode
from io import BytesIO


def generate_contract_pdf(offer_data: Dict[str, Any], contract_id: str) -> str:
    """
    Generate a professional PDF contract for car sale.
    
    Args:
        offer_data: Complete offer data including client, vehicle, financial details
        contract_id: Unique contract identifier
        
    Returns:
        str: Path to generated PDF file
    """
    # Create storage directory
    storage_path = "data/contracts"
    os.makedirs(storage_path, exist_ok=True)
    
    # Generate filename
    filename = f"{contract_id}.pdf"
    filepath = os.path.join(storage_path, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )
    
    # Title
    elements.append(Paragraph("CONTRAT DE VENTE AUTOMOBILE", title_style))
    elements.append(Paragraph(f"<b>N° {contract_id}</b>", ParagraphStyle('ContractID', parent=normal_style, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.5*cm))
    
    # Date
    date_str = datetime.now().strftime("%d/%m/%Y")
    elements.append(Paragraph(f"Date: {date_str}", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Client Information
    elements.append(Paragraph("INFORMATIONS CLIENT", heading_style))
    client_data = offer_data.get('user_profile', {})
    client_table_data = [
        ['Nom Complet:', client_data.get('full_name', 'N/A')],
        ['Email:', client_data.get('email', 'N/A')],
        ['Téléphone:', client_data.get('phone', 'N/A')],
        ['Ville:', client_data.get('city', 'N/A')],
        ['Type de Contrat:', client_data.get('contract_type', 'N/A')],
    ]
    client_table = Table(client_table_data, colWidths=[5*cm, 10*cm])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Vehicle Information
    elements.append(Paragraph("VÉHICULE ACHETÉ", heading_style))
    negotiated = offer_data.get('negotiated_terms', {})
    vehicle_table_data = [
        ['Marque:', client_data.get('vehicle_preferences', {}).get('brands', ['N/A'])[0] if client_data.get('vehicle_preferences', {}).get('brands') else 'N/A'],
        ['Modèle:', client_data.get('vehicle_preferences', {}).get('model', 'N/A')],
        ['Catégorie:', client_data.get('vehicle_preferences', {}).get('category', 'N/A')],
        ['Prix de Vente:', f"{negotiated.get('offer_price_mad', 0):,.2f} MAD"],
        ['Remise Accordée:', f"{negotiated.get('discount_amount_mad', 0):,.2f} MAD"],
    ]
    vehicle_table = Table(vehicle_table_data, colWidths=[5*cm, 10*cm])
    vehicle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
    ]))
    elements.append(vehicle_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Trade-in (if applicable)
    valuation = offer_data.get('valuation', {})
    if negotiated.get('trade_in_value_mad'):
        elements.append(Paragraph("VÉHICULE DE REPRISE", heading_style))
        tradein_table_data = [
            ['Marque:', valuation.get('brand', 'N/A')],
            ['Modèle:', valuation.get('model', 'N/A')],
            ['Année:', str(valuation.get('year', 'N/A'))],
            ['Kilométrage:', f"{valuation.get('mileage', 0):,} km"],
            ['État:', valuation.get('condition', 'N/A')],
            ['Valeur de Reprise:', f"{negotiated.get('trade_in_value_mad', 0):,.2f} MAD"],
        ]
        tradein_table = Table(tradein_table_data, colWidths=[5*cm, 10*cm])
        tradein_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
        ]))
        elements.append(tradein_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Financial Details
    elements.append(Paragraph("DÉTAILS FINANCIERS", heading_style))
    financial_table_data = [
        ['Mode de Paiement:', negotiated.get('payment_method', 'N/A')],
    ]
    
    if negotiated.get('monthly_payment_mad'):
        financial_table_data.extend([
            ['Mensualité:', f"{negotiated.get('monthly_payment_mad', 0):,.2f} MAD"],
            ['Durée:', '60 mois (estimation)'],
        ])
    
    # Calculate net amount
    net_amount = negotiated.get('offer_price_mad', 0) - negotiated.get('trade_in_value_mad', 0)
    financial_table_data.append(['Montant Net à Payer:', f"{net_amount:,.2f} MAD"])
    
    financial_table = Table(financial_table_data, colWidths=[5*cm, 10*cm])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.white),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(financial_table)
    elements.append(Spacer(1, 1*cm))
    
    # Terms and Conditions
    elements.append(Paragraph("CONDITIONS GÉNÉRALES", heading_style))
    terms = [
        "1. Le client s'engage à payer le montant convenu selon les modalités définies.",
        "2. Le véhicule est vendu dans l'état où il se trouve au moment de la signature.",
        "3. La garantie constructeur s'applique selon les termes du fabricant.",
        "4. Le transfert de propriété sera effectué après paiement complet.",
        "5. Ce contrat est soumis au droit marocain."
    ]
    for term in terms:
        elements.append(Paragraph(term, normal_style))
    elements.append(Spacer(1, 1*cm))
    
    # Signatures
    elements.append(Paragraph("SIGNATURES", heading_style))
    sig_table_data = [
        ['Le Client', 'OMEGA - Concessionnaire'],
        ['', ''],
        ['', ''],
        ['Signature: _______________', 'Signature: _______________'],
        [f'Date: {date_str}', f'Date: {date_str}']
    ]
    sig_table = Table(sig_table_data, colWidths=[8*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LINEABOVE', (0, 3), (-1, 3), 1, colors.black),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # QR Code for verification
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(f"OMEGA-CONTRACT-{contract_id}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to bytes
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Add QR code
    qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
    elements.append(Paragraph("Code de Vérification", ParagraphStyle('QRLabel', parent=normal_style, alignment=TA_CENTER, fontSize=8)))
    elements.append(qr_image)
    
    # Build PDF
    doc.build(elements)
    
    return filepath


# Tool function for agent
async def generate_offer_pdf(final_offer_data: str) -> Dict[str, Any]:
    """
    Tool function called by OfferStructuringAgent.
    
    Args:
        final_offer_data: JSON string with offer data
        
    Returns:
        Dict with pdf_url and status
    """
    import json
    
    try:
        # Parse offer data
        offer_data = json.loads(final_offer_data) if isinstance(final_offer_data, str) else final_offer_data
        
        # Generate contract ID if not present
        contract_id = offer_data.get('contract_id', f"OMEGA-{datetime.now().strftime('%Y%m%d')}-{os.urandom(3).hex().upper()}")
        
        # Generate PDF
        filepath = generate_contract_pdf(offer_data, contract_id)
        
        # Return web-accessible URL (relative path)
        pdf_url = f"/contracts/{contract_id}.pdf"
        
        return {
            "pdf_url": pdf_url,
            "contract_id": contract_id,
            "status": "success",
            "message": "PDF généré avec succès"
        }
    except Exception as e:
        return {
            "pdf_url": None,
            "status": "error",
            "message": f"Erreur lors de la génération du PDF: {str(e)}"
        }

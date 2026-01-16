import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, letter
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    Frame,
    PageTemplate,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import qrcode
from io import BytesIO
import requests


class PDFGenerator:
    def __init__(self, upload_dir: str = "uploads/prints"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Stili per il PDF
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura stili personalizzati per il PDF"""
        # Stile per il titolo principale
        self.styles.add(
            ParagraphStyle(
                name="AssetTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=8,
                alignment=TA_CENTER,
                textColor=colors.blue,
                fontName="Helvetica-Bold",
                borderWidth=1,
                borderColor=colors.blue,
                borderPadding=8,
                backColor=colors.blue,
            )
        )

        # Stile per i sottotitoli delle sezioni
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=11,
                spaceAfter=4,
                spaceBefore=8,
                textColor=colors.blue,
                fontName="Helvetica-Bold",
                leftIndent=0,
            )
        )

        # Stile per le informazioni
        self.styles.add(
            ParagraphStyle(
                name="InfoText",
                parent=self.styles["Normal"],
                fontSize=9,
                spaceAfter=2,
                fontName="Helvetica",
            )
        )

        # Stile per le etichette
        self.styles.add(
            ParagraphStyle(
                name="Label",
                parent=self.styles["Normal"],
                fontSize=8,
                spaceAfter=1,
                textColor=colors.darkgrey,
                fontName="Helvetica-Bold",
            )
        )

        # Stile per i valori
        self.styles.add(
            ParagraphStyle(
                name="Value",
                parent=self.styles["Normal"],
                fontSize=9,
                spaceAfter=2,
                fontName="Helvetica",
            )
        )

    def _get_page_size(self, paper_size: str):
        """Restituisce le dimensioni della pagina"""
        sizes = {"a4": A4, "a3": A3, "letter": letter}
        return sizes.get(paper_size.lower(), A4)

    def _generate_qr_code(self, text: str, size: int = 80) -> BytesIO:
        """Genera un QR code"""
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer

    def _format_value(self, value, translations=None):
        """Formatta il valore per la stampa: liste come stringhe, None come valore di default tradotto"""
        if translations is None:
            translations = self._get_translations("en")
        if (
            value is None
            or value == ""
            or value == translations.get("not_available", "N/A")
        ):
            return translations.get("not_available", "N/A")
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value if v)
        return str(value)

    def _create_compact_info_table(
        self,
        asset: Dict[str, Any],
        fields_config: list,
        translations: Optional[Dict[str, str]] = None,
    ) -> Optional[Table]:
        """Crea una tabella a due colonne (etichetta, valore) con le informazioni principali"""
        if translations is None:
            translations = self._get_translations("en")
        if not fields_config:
            fields_config = [
                {
                    "name": "asset_name",
                    "label": translations.get("asset_name", "Name"),
                    "visible": True,
                },
                {
                    "name": "asset_tag",
                    "label": translations.get("asset_tag", "Tag"),
                    "visible": True,
                },
                {
                    "name": "asset_ip",
                    "label": translations.get("asset_ip", "IP"),
                    "visible": True,
                },
                {
                    "name": "asset_serial",
                    "label": translations.get("asset_serial", "Serial"),
                    "visible": True,
                },
                {
                    "name": "asset_model",
                    "label": translations.get("asset_model", "Model"),
                    "visible": True,
                },
                {
                    "name": "asset_manufacturer",
                    "label": translations.get("asset_manufacturer", "Manufacturer"),
                    "visible": True,
                },
                {
                    "name": "asset_firmware",
                    "label": translations.get("asset_firmware", "Firmware"),
                    "visible": True,
                },
                {
                    "name": "asset_type",
                    "label": translations.get("asset_type", "Type"),
                    "visible": True,
                },
                {
                    "name": "asset_status",
                    "label": translations.get("asset_status", "Status"),
                    "visible": True,
                },
                {
                    "name": "asset_site",
                    "label": translations.get("asset_site", "Site"),
                    "visible": True,
                },
                {
                    "name": "asset_location",
                    "label": translations.get("asset_location", "Location"),
                    "visible": True,
                },
                {
                    "name": "asset_risk_score",
                    "label": translations.get("asset_risk_score", "Risk Score"),
                    "visible": True,
                },
            ]
        visible_fields = [
            field for field in fields_config if field.get("visible", True)
        ]
        data = []
        for field in visible_fields:
            field_name = field.get("name", "")
            field_label = field.get("label", "") or self._get_field_label(
                field_name, translations
            )
            field_value = self._get_field_value(asset, field_name, translations)
            field_value = self._format_value(field_value, translations)
            # Limita la lunghezza del valore per evitare overflow
            if len(field_value) > 60:
                field_value = field_value[:57] + "..."
            data.append([str(field_label), str(field_value)])
        if not data:
            return None
        col_widths = [60 * mm, 120 * mm]
        try:
            table = Table(data, colWidths=col_widths)
        except Exception as e:
            return None
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
                    ("BACKGROUND", (1, 0), (1, -1), colors.white),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return table

    def _create_risk_info_table(
        self, asset: Dict[str, Any], translations: Optional[Dict[str, str]] = None
    ) -> Table:
        """Crea una tabella compatta per le informazioni di rischio"""
        data = [
            ["Risk Score", f"{asset.get('risk_score', 0)}%"],
            ["Purdue Level", str(asset.get("purdue_level", "N/A"))],
            ["Business Criticality", str(asset.get("business_criticality", "N/A"))],
            ["Impact Value", str(asset.get("impact_value", "N/A"))],
            ["Physical Access", str(asset.get("physical_access_ease", "N/A"))],
            ["Exposure Level", str(asset.get("exposure_level", "N/A"))],
        ]

        table = Table(data, colWidths=[80 * mm, 100 * mm])
        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.lightblue,
                    ),  # Prima colonna con sfondo azzurro
                    (
                        "BACKGROUND",
                        (1, 0),
                        (-1, -1),
                        colors.white,
                    ),  # Altre colonne bianche
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (0, -1),
                        colors.darkblue,
                    ),  # Etichette in blu scuro
                    ("TEXTCOLOR", (1, 0), (-1, -1), colors.black),  # Valori in nero
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),  # Etichette in grassetto
                    ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),  # Valori normali
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        return table

    def _create_network_info_table(
        self, asset: Dict[str, Any], translations: Optional[Dict[str, str]] = None
    ) -> Table:
        """Crea una tabella per le informazioni di rete"""
        data = [
            ["VLAN", str(asset.get("vlan", "N/A"))],
            ["Logical Port", str(asset.get("logical_port", "N/A"))],
            ["Physical Plug", str(asset.get("physical_plug_label", "N/A"))],
            ["Remote Access", "Yes" if asset.get("remote_access") else "No"],
            ["Access Type", str(asset.get("remote_access_type", "N/A"))],
            ["Last Seen", str(asset.get("last_seen", "N/A"))],
        ]

        table = Table(data, colWidths=[80 * mm, 100 * mm])
        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.green,
                    ),  # Prima colonna con sfondo verde chiaro
                    (
                        "BACKGROUND",
                        (1, 0),
                        (-1, -1),
                        colors.white,
                    ),  # Altre colonne bianche
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (0, -1),
                        colors.darkgreen,
                    ),  # Etichette in verde scuro
                    ("TEXTCOLOR", (1, 0), (-1, -1), colors.black),  # Valori in nero
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),  # Etichette in grassetto
                    ("FONTNAME", (1, 0), (-1, -1), "Helvetica"),  # Valori normali
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        return table

    def _create_connections_table(
        self, asset: Dict[str, Any], translations: Optional[Dict[str, str]] = None
    ) -> Optional[Table]:
        """Crea una tabella per le connessioni remote"""
        connections = asset.get("connections", [])
        if not connections:
            return None
        if translations is None:
            translations = self._get_translations("en")

        # Intestazioni tradotte per connessioni remote
        headers = [
            translations.get("connected_asset", "Connected Asset"),
            translations.get("connection_type", "Type"),
            translations.get("local_interface", "Local Interface"),
            translations.get("remote_interface", "Remote Interface"),
            translations.get("port", "Port"),
            translations.get("protocol", "Protocol"),
        ]
        data = [headers]

        for conn in connections[:8]:  # Limita a 8 connessioni per spazio
            # Determina l'asset collegato
            target_asset = conn.get("target_asset", {})
            target_name = target_asset.get("name", "—") if target_asset else "—"
            if len(target_name) > 25:
                target_name = target_name[:22] + "..."

            # Interfacce (se disponibili)
            local_iface = (
                conn.get("local_interface", {}).get("name", "—")
                if conn.get("local_interface")
                else "—"
            )
            remote_iface = (
                conn.get("remote_interface", {}).get("name", "—")
                if conn.get("remote_interface")
                else "—"
            )

            # Limita lunghezza interfacce
            if len(local_iface) > 15:
                local_iface = local_iface[:12] + "..."
            if len(remote_iface) > 15:
                remote_iface = remote_iface[:12] + "..."

            data.append(
                [
                    self._format_value(target_name, translations),
                    self._format_value(conn.get("connection_type", "—"), translations),
                    self._format_value(local_iface, translations),
                    self._format_value(remote_iface, translations),
                    self._format_value(conn.get("port_parent", "—"), translations),
                    self._format_value(conn.get("protocol", "—"), translations),
                ]
            )

        # Larghezze colonne ottimizzate per le nuove informazioni
        table = Table(
            data, colWidths=[35 * mm, 25 * mm, 30 * mm, 30 * mm, 20 * mm, 20 * mm]
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f39c12")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),  # Smaller font for more information
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ]
            )
        )

        return table

    def _create_contacts_table(
        self, asset: Dict[str, Any], translations: Optional[Dict[str, str]] = None
    ) -> Optional[Table]:
        """Crea una tabella per i contatti"""
        contacts = asset.get("contacts", [])
        if not contacts:
            return None
        if translations is None:
            translations = self._get_translations("en")
        headers = [
            translations.get("contact_name", "Name"),
            translations.get("contact_email", "Email"),
            translations.get("contact_phone", "Phone"),
            translations.get("contact_type", "Type"),
        ]
        data = [headers]
        for contact in contacts[:3]:  # Limita a 3 contatti per spazio
            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            if len(name) > 20:
                name = name[:17] + "..."

            data.append(
                [
                    self._format_value(name, translations),
                    self._format_value(contact.get("email", "—"), translations),
                    self._format_value(contact.get("phone1", "—"), translations),
                    self._format_value(contact.get("type", "—"), translations),
                ]
            )

        table = Table(data, colWidths=[50 * mm, 60 * mm, 40 * mm, 30 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e74c3c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )

        return table

    def _get_field_value(
        self,
        asset: Dict[str, Any],
        field_name: str,
        translations: Optional[Dict[str, str]] = None,
    ) -> str:
        """Ottiene il valore di un campo specifico dall'asset"""
        if translations is None:
            translations = self._get_translations("en")
        if field_name == "asset_id":
            return str(asset.get("id", translations.get("not_available", "N/A")))
        elif field_name == "asset_name":
            return asset.get("name", translations.get("not_available", "N/A"))
        elif field_name == "asset_tag":
            return asset.get("tag", translations.get("not_available", "N/A"))
        elif field_name == "asset_type":
            return (asset.get("asset_type") or {}).get(
                "name", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_status":
            return (asset.get("status") or {}).get(
                "name", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_location":
            return (asset.get("location") or {}).get(
                "name", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_site":
            return (asset.get("site") or {}).get(
                "name", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_manufacturer":
            return (asset.get("manufacturer") or {}).get(
                "name", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_model":
            return asset.get("model", translations.get("not_available", "N/A"))
        elif field_name == "asset_serial":
            return asset.get("serial_number", translations.get("not_available", "N/A"))
        elif field_name == "asset_ip":
            return asset.get("ip_address", translations.get("not_available", "N/A"))
        elif field_name == "asset_firmware":
            return asset.get(
                "firmware_version", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_description":
            desc = asset.get("description", translations.get("not_available", "N/A"))
            if desc and len(desc) > 50:
                desc = desc[:47] + "..."
            return desc
        elif field_name == "asset_installation_date":
            install_date = asset.get("installation_date")
            if install_date:
                return (
                    install_date.strftime("%d/%m/%Y")
                    if hasattr(install_date, "strftime")
                    else str(install_date)
                )
            return translations.get("not_available", "N/A")
        elif field_name == "asset_business_criticality":
            return asset.get(
                "business_criticality", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_risk_score":
            risk_score = asset.get("risk_score")
            if risk_score is not None:
                return f"{risk_score}%"
            return translations.get("not_available", "N/A")
        elif field_name == "asset_vlan":
            return asset.get("vlan", translations.get("not_available", "N/A"))
        elif field_name == "asset_logical_port":
            return asset.get("logical_port", translations.get("not_available", "N/A"))
        elif field_name == "asset_physical_plug":
            return asset.get(
                "physical_plug_label", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_remote_access":
            return (
                translations.get("yes", "Yes")
                if asset.get("remote_access")
                else translations.get("no", "No")
            )
        elif field_name == "asset_remote_access_type":
            return asset.get(
                "remote_access_type", translations.get("not_available", "N/A")
            )
        elif field_name == "asset_last_seen":
            last_seen = asset.get("last_seen")
            if last_seen:
                return (
                    last_seen.strftime("%d/%m/%Y")
                    if hasattr(last_seen, "strftime")
                    else str(last_seen)
                )
            return translations.get("not_available", "N/A")
        else:
            return translations.get("not_available", "N/A")

    def _get_field_label(
        self, field_name: str, translations: Optional[Dict[str, str]] = None
    ) -> str:
        """Ottiene l'etichetta di un campo con supporto traduzioni"""
        # Etichette di fallback in inglese
        field_labels = {
            "asset_id": "ID",
            "asset_name": "Name",
            "asset_tag": "Tag",
            "asset_type": "Type",
            "asset_status": "Status",
            "asset_location": "Location",
            "asset_site": "Site",
            "asset_manufacturer": "Manufacturer",
            "asset_model": "Model",
            "asset_serial": "Serial",
            "asset_ip": "IP",
            "asset_firmware": "Firmware",
            "asset_description": "Description",
            "asset_installation_date": "Installation Date",
            "asset_business_criticality": "Business Criticality",
            "asset_risk_score": "Risk Score",
            "asset_vlan": "VLAN",
            "asset_logical_port": "Logical Port",
            "asset_physical_plug": "Physical Plug",
            "asset_remote_access": "Remote Access",
            "asset_remote_access_type": "Access Type",
            "asset_last_seen": "Last Seen",
        }

        # Se ci sono traduzioni, usa quelle, altrimenti fallback in inglese
        if translations and field_name in translations:
            return translations[field_name]

        return field_labels.get(field_name, field_name)

    def _get_translations(self, language: str) -> Dict[str, str]:
        """Ottiene le traduzioni per la lingua specificata"""
        translations = {
            "en": {
                "header_title": "Industrace - Asset Card",
                "generated_on": "Generated on",
                "at_time": "at",
                "risk_section": "Risk",
                "network_section": "Network",
                "connections_section": "Connections",
                "contacts_section": "Contacts",
                "qr_code_label": "QR Code for quick access",
                "yes": "Yes",
                "no": "No",
                "not_available": "N/A",
                "connection_type": "Type",
                "connected_asset": "Connected Asset",
                "local_interface": "Local Interface",
                "remote_interface": "Remote Interface",
                "port": "Port",
                "protocol": "Protocol",
                "contact_name": "Name",
                "contact_email": "Email",
                "contact_phone": "Phone",
                "contact_type": "Type",
                "custom_fields_section": "Custom Fields",
                "network_interfaces_section": "Network Interfaces",
                "asset_name": "Name",
                "asset_tag": "Tag",
                "asset_ip": "IP",
                "asset_serial": "Serial",
                "asset_model": "Model",
                "asset_manufacturer": "Manufacturer",
                "asset_firmware": "Firmware",
                "asset_type": "Type",
                "asset_status": "Status",
                "asset_site": "Site",
                "asset_location": "Location",
                "asset_risk_score": "Risk Score",
            },
            "it": {
                "header_title": "Industrace - Scheda Asset",
                "generated_on": "Generato il",
                "at_time": "alle ore",
                "risk_section": "Rischio",
                "network_section": "Rete",
                "connections_section": "Connessioni",
                "contacts_section": "Contatti",
                "qr_code_label": "QR Code per accesso rapido",
                "yes": "Sì",
                "no": "No",
                "not_available": "N/A",
                "connection_type": "Tipo",
                "connected_asset": "Asset collegato",
                "local_interface": "Interfaccia locale",
                "remote_interface": "Interfaccia remota",
                "port": "Porta",
                "protocol": "Protocollo",
                "contact_name": "Nome",
                "contact_email": "Email",
                "contact_phone": "Telefono",
                "contact_type": "Tipo",
                "custom_fields_section": "Campi personalizzati",
                "network_interfaces_section": "Interfacce di rete",
                "asset_name": "Nome",
                "asset_tag": "Tag",
                "asset_ip": "IP",
                "asset_serial": "Serial",
                "asset_model": "Modello",
                "asset_manufacturer": "Produttore",
                "asset_firmware": "Firmware",
                "asset_type": "Tipo",
                "asset_status": "Stato",
                "asset_site": "Sito",
                "asset_location": "Posizione",
                "asset_risk_score": "Risk Score",
            },
        }
        return translations.get(language, translations["en"])

    def generate_asset_pdf(
        self,
        asset: Dict[str, Any],
        template: Dict[str, Any],
        options: Dict[str, Any],
        language: str = "en",
    ) -> str:
        """Genera un PDF compatto e professionale per un asset su una pagina A4"""
        filename = f"asset_{asset.get('id', 'unknown')}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = self.upload_dir / filename
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )
        translations = self._get_translations(language)
        story = []
        # Header con logo e titolo
        # Cerca il logo in diversi percorsi
        logo_paths = [
            os.getenv("PDF_LOGO_PATH", "static/logo.png"),
            "backend/static/logo.png",
            "frontend/public/logo.png",
            "static/logo.png",
            "logo.png",
        ]
        logo_img = None
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    logo_img = Image(logo_path, width=25 * mm, height=25 * mm)
                    break
                except:
                    continue

        # Asset name in center (smaller than previous title)
        asset_name = self._format_value(asset.get("name", "Asset"), translations)
        # Creo uno stile specifico per centrare il nome dell'asset
        centered_style = ParagraphStyle(
            "CenteredAssetName",
            parent=self.styles["InfoText"],
            alignment=TA_CENTER,
            fontSize=14,
            fontName="Helvetica-Bold",
        )
        asset_name_para = Paragraph(asset_name, centered_style)

        # Data formattata con etichette su due righe
        current_date = datetime.now()
        date_str = current_date.strftime("%d/%m/%Y")
        time_str = current_date.strftime("%H:%M")
        generated_on = translations.get("generated_on", "Generato il")
        at_time = translations.get("at_time", "alle ore")
        date_para = Paragraph(
            f"<font size=8 color='#666'>{generated_on} {date_str}<br/>{at_time} {time_str}</font>",
            self.styles["InfoText"],
        )

        # Intestazione: logo | nome asset | data
        header_row = []
        if logo_img:
            header_row.append(logo_img)
        else:
            header_row.append("")
        header_row.append(asset_name_para)
        header_row.append(date_para)
        header_table = Table([header_row], colWidths=[30 * mm, 95 * mm, 50 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 8))

        # Riga asset info principale: nome asset, tipo, stato, produttore, modello, seriale
        asset_info_data = [
            [
                Paragraph(
                    f"<b>{translations.get('asset_name', 'Nome')}:</b> {self._format_value(asset.get('name'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_type', 'Tipo')}:</b> {self._format_value((asset.get('asset_type') or {}).get('name'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_status', 'Stato')}:</b> {self._format_value((asset.get('status') or {}).get('name'), translations)}",
                    self.styles["InfoText"],
                ),
            ],
            [
                Paragraph(
                    f"<b>{translations.get('asset_manufacturer', 'Produttore')}:</b> {self._format_value((asset.get('manufacturer') or {}).get('name'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_model', 'Modello')}:</b> {self._format_value(asset.get('model'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_serial', 'Serial')}:</b> {self._format_value(asset.get('serial_number'), translations)}",
                    self.styles["InfoText"],
                ),
            ],
            [
                Paragraph(
                    f"<b>{translations.get('asset_site', 'Sito')}:</b> {self._format_value((asset.get('site') or {}).get('name'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_location', 'Posizione')}:</b> {self._format_value((asset.get('location') or {}).get('name'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_firmware', 'Firmware')}:</b> {self._format_value(asset.get('firmware_version'), translations)}",
                    self.styles["InfoText"],
                ),
            ],
        ]
        
        # Aggiungi righe aggiuntive se i campi sono presenti
        additional_rows = []
        
        # Riga con installation_date, business_criticality, security_zone
        if asset.get('installation_date') or asset.get('business_criticality') or asset.get('security_zone'):
            additional_rows.append([
                Paragraph(
                    f"<b>{translations.get('asset_installation_date', 'Data Installazione')}:</b> {self._format_value(asset.get('installation_date'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_business_criticality', 'Criticità Business')}:</b> {self._format_value(asset.get('business_criticality'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_security_zone', 'Security Zone')}:</b> {self._format_value((asset.get('security_zone') or {}).get('name') if isinstance(asset.get('security_zone'), dict) else asset.get('security_zone'), translations)}",
                    self.styles["InfoText"],
                ),
            ])
        
        # Riga con area, remote_access, remote_access_type
        if asset.get('area') or asset.get('remote_access') is not None or asset.get('remote_access_type'):
            additional_rows.append([
                Paragraph(
                    f"<b>{translations.get('asset_area', 'Area')}:</b> {self._format_value((asset.get('area') or {}).get('name') if isinstance(asset.get('area'), dict) else asset.get('area'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_remote_access', 'Accesso Remoto')}:</b> {self._format_value('Yes' if asset.get('remote_access') else 'No', translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('asset_remote_access_type', 'Tipo Accesso Remoto')}:</b> {self._format_value(asset.get('remote_access_type'), translations)}",
                    self.styles["InfoText"],
                ),
            ])
        
        # Riga con protocols se presente
        if asset.get('protocols') and isinstance(asset.get('protocols'), list) and len(asset.get('protocols', [])) > 0:
            additional_rows.append([
                Paragraph(
                    f"<b>{translations.get('asset_protocols', 'Protocolli')}:</b> {self._format_value(', '.join(asset.get('protocols', [])), translations)}",
                    self.styles["InfoText"],
                ),
            ])
        
        asset_info_data.extend(additional_rows)
        
        asset_info_table = Table(asset_info_data, colWidths=[60 * mm, 60 * mm, 55 * mm])
        asset_info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(asset_info_table)
        story.append(Spacer(1, 8))
        # Linea di separazione
        story.append(
            Table(
                [[""]],
                colWidths=[180 * mm],
                rowHeights=[1],
                style=TableStyle(
                    [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#bfc9ca"))]
                ),
            )
        )
        story.append(Spacer(1, 4))

        # --- RISK AND CRITICALITY SECTION ---
        story.append(
            Paragraph(
                translations.get("risk_section", "Rischio e criticità"),
                self.styles["SectionTitle"],
            )
        )

        risk_info_data = [
            [
                Paragraph(
                    f"<b>{translations.get('risk_score', 'Rischio')}:</b> {self._format_value(asset.get('risk_score'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('business_criticality', 'Criticità')}:</b> {self._format_value(asset.get('business_criticality'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('impact_value', 'Impact')}:</b> {self._format_value(asset.get('impact_value'), translations)}",
                    self.styles["InfoText"],
                ),
            ],
            [
                Paragraph(
                    f"<b>{translations.get('purdue_level', 'Purdue')}:</b> {self._format_value(asset.get('purdue_level'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('physical_access', 'Accesso fisico')}:</b> {self._format_value(asset.get('physical_access_ease'), translations)}",
                    self.styles["InfoText"],
                ),
                Paragraph(
                    f"<b>{translations.get('exposure_level', 'Esposizione')}:</b> {self._format_value(asset.get('exposure_level'), translations)}",
                    self.styles["InfoText"],
                ),
            ],
        ]

        risk_table = Table(risk_info_data, colWidths=[60 * mm, 60 * mm, 55 * mm])
        risk_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(risk_table)
        story.append(Spacer(1, 4))

        # --- SEZIONE INTERFACCE DI RETE ---
        interfaces = asset.get("interfaces", [])
        if interfaces and isinstance(interfaces, list) and len(interfaces) > 0:
            story.append(
                Paragraph(
                    translations.get(
                        "network_interfaces_section", "Interfacce di rete"
                    ),
                    self.styles["SectionTitle"],
                )
            )
            # Intestazioni multilingua
            headers = [
                translations.get("iface_name", "Nome"),
                translations.get("iface_type", "Tipo"),
                translations.get("iface_ip", "IP"),
                translations.get("iface_mac", "MAC"),
                translations.get("iface_vlan", "VLAN"),
                translations.get("iface_gateway", "Gateway"),
                translations.get("iface_subnet", "Subnet"),
                translations.get("iface_logical_port", "Logical port"),
                translations.get("iface_plug_label", "Plug label"),
            ]
            data = [headers]
            for iface in interfaces:
                data.append(
                    [
                        self._format_value(iface.get("name"), translations),
                        self._format_value(iface.get("type"), translations),
                        self._format_value(iface.get("ip_address"), translations),
                        self._format_value(iface.get("mac_address"), translations),
                        self._format_value(iface.get("vlan"), translations),
                        self._format_value(iface.get("default_gateway"), translations),
                        self._format_value(iface.get("subnet_mask"), translations),
                        self._format_value(iface.get("logical_port"), translations),
                        self._format_value(
                            iface.get("physical_plug_label"), translations
                        ),
                    ]
                )
            iface_table = Table(
                data,
                colWidths=[
                    24 * mm,
                    16 * mm,
                    20 * mm,
                    24 * mm,
                    10 * mm,
                    20 * mm,
                    20 * mm,
                    22 * mm,
                    24 * mm,
                ],
            )
            iface_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#aed6f1")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#154360")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                        ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
                    ]
                )
            )
            story.append(iface_table)
            story.append(Spacer(1, 4))

        # Linea di separazione
        story.append(
            Table(
                [[""]],
                colWidths=[180 * mm],
                rowHeights=[1],
                style=TableStyle(
                    [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#bfc9ca"))]
                ),
            )
        )
        story.append(Spacer(1, 4))
        # Tabella connessioni principali (max 5)
        connections_table = self._create_connections_table(asset, translations)
        if connections_table:
            story.append(
                Paragraph(
                    translations.get("connections_section", "Connessioni principali"),
                    self.styles["SectionTitle"],
                )
            )
            story.append(connections_table)
        # Tabella contatti chiave (max 3)
        contacts_table = self._create_contacts_table(asset, translations)
        if contacts_table:
            story.append(
                Paragraph(
                    translations.get("contacts_section", "Contatti chiave"),
                    self.styles["SectionTitle"],
                )
            )
            story.append(contacts_table)
        # --- SEZIONE FORNITORI ---
        suppliers = asset.get("suppliers", [])
        if suppliers and isinstance(suppliers, list) and len(suppliers) > 0:
            story.append(Paragraph("Fornitori", self.styles["SectionTitle"]))
            supplier_data = [["Nome", "Email", "Telefono", "Sito", "Note"]]
            for s in suppliers:
                supplier_data.append(
                    [
                        self._format_value(s.get("name"), translations),
                        self._format_value(s.get("email"), translations),
                        self._format_value(s.get("phone"), translations),
                        self._format_value(s.get("website"), translations),
                        self._format_value(s.get("notes"), translations),
                    ]
                )
            supplier_table = Table(
                supplier_data, colWidths=[40 * mm, 40 * mm, 30 * mm, 35 * mm, 35 * mm]
            )
            supplier_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f7ca18")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6e2c00")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
                    ]
                )
            )
            story.append(supplier_table)
            story.append(Spacer(1, 4))

        # --- SEZIONE CAMPI CUSTOM ---
        custom_fields = asset.get("custom_fields", {})
        if custom_fields and isinstance(custom_fields, dict) and len(custom_fields) > 0:
            story.append(
                Paragraph(
                    translations.get("custom_fields_section", "Campi custom"),
                    self.styles["SectionTitle"],
                )
            )
            custom_data = [
                [str(k), self._format_value(v, translations)]
                for k, v in custom_fields.items()
            ]
            custom_table = Table(custom_data, colWidths=[60 * mm, 110 * mm])
            custom_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f9e79f")),
                        ("BACKGROUND", (1, 0), (1, -1), colors.white),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#7d6608")),
                        ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
                    ]
                )
            )
            story.append(custom_table)
        # QR code in basso a destra solo se richiesto
        if options.get("includeQR", True):
            base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            asset_url = f"{base_url}/assets/{asset.get('id')}"
            qr_buffer = self._generate_qr_code(asset_url, 60)
            qr_img = Image(qr_buffer, width=30 * mm, height=30 * mm)
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    translations.get("qr_code_label", "QR Code for quick access"),
                    self.styles["Label"],
                )
            )
            story.append(qr_img)
        doc.build(story)
        return str(filepath)

    def get_file_size(self, filepath: str) -> int:
        """Restituisce la dimensione del file in bytes"""
        try:
            return os.path.getsize(filepath)
        except OSError:
            return 0

    def generate_printed_kit(self, kit_data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Genera un printed kit completo per l'azienda"""
        try:
            import logging
            logging.info("Inizio generazione printed kit")
            
            # Determina la lingua (default: inglese)
            language = options.get("language", "en")
            
            # Dizionario traduzioni
            translations = {
                "en": {
                    "generated_on": "Generated on:",
                    "generated_by": "Generated by:",
                    "company_info": "1. COMPANY INFORMATION",
                    "company_name": "Company Name",
                    "slug": "Slug",
                    "created_on": "Created on",
                    "status": "Status",
                    "active": "Active",
                    "inactive": "Inactive",
                    "critical_assets": "2. CRITICAL ASSETS",
                    "name": "Name",
                    "type": "Type",
                    "site": "Site",
                    "risk_score": "Risk Score",
                    "no_critical_assets": "No critical assets identified",
                    "sites_areas": "3. SITES AND AREAS",
                    "code": "Code",
                    "address": "Address",
                    "description": "Description",
                    "complete_inventory": "4. COMPLETE ASSET INVENTORY",
                    "area": "Area",
                    "location": "Location",
                    "ip": "IP",
                    "manufacturer": "Manufacturer",
                    "serial_number": "Serial Number",
                    "notes": "Notes",
                    "critical_suppliers": "5. CRITICAL SUPPLIERS",
                    "email": "Email",
                    "phone": "Phone",
                    "footer": "Document automatically generated by Industrace on"
                },
                "it": {
                    "generated_on": "Generato il:",
                    "generated_by": "Generato da:",
                    "company_info": "1. INFORMAZIONI AZIENDA",
                    "company_name": "Nome Azienda",
                    "slug": "Slug",
                    "created_on": "Creato il",
                    "status": "Stato",
                    "active": "Attivo",
                    "inactive": "Inattivo",
                    "critical_assets": "2. ASSET CRITICI",
                    "name": "Nome",
                    "type": "Tipo",
                    "site": "Sito",
                    "risk_score": "Risk Score",
                    "no_critical_assets": "Nessun asset critico identificato",
                    "sites_areas": "3. STABILIMENTI E AREE",
                    "code": "Codice",
                    "address": "Indirizzo",
                    "description": "Descrizione",
                    "complete_inventory": "4. INVENTARIO COMPLETO ASSET",
                    "area": "Area",
                    "location": "Location",
                    "ip": "IP",
                    "manufacturer": "Produttore",
                    "serial_number": "Serial Number",
                    "notes": "Note",
                    "critical_suppliers": "5. FORNITORI CRITICI",
                    "email": "Email",
                    "phone": "Telefono",
                    "footer": "Documento generato automaticamente da Industrace il"
                }
            }
            
            t = translations.get(language, translations["en"])
            
            # Crea il nome del file
            tenant_name = kit_data["tenant"].name.replace(" ", "_").lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"printed-kit-{tenant_name}-{timestamp}.pdf"
            filepath = self.upload_dir / filename
            
            logging.info(f"File path: {filepath}")

            # Crea il documento PDF
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )

            # Lista degli elementi del PDF
            story = []
            
            logging.info("Creazione header documento")

            # Header del documento
            story.append(Paragraph(
                f"<b>PRINTED KIT - {kit_data['tenant'].name.upper()}</b>",
                self.styles["AssetTitle"]
            ))
            story.append(Spacer(1, 10))

            # Informazioni di generazione
            date_format = '%d/%m/%Y at %H:%M' if language == "en" else '%d/%m/%Y alle %H:%M'
            story.append(Paragraph(
                f"<b>{t['generated_on']}</b> {kit_data['generated_at'].strftime(date_format)}",
                self.styles["InfoText"]
            ))
            story.append(Paragraph(
                f"<b>{t['generated_by']}</b> {kit_data['generated_by']}",
                self.styles["InfoText"]
            ))
            story.append(Spacer(1, 15))
            
            logging.info("Creazione sezione tenant")

            # 1. INFORMAZIONI AZIENDA
            story.append(Paragraph(f"1. {t['company_info']}", self.styles["SectionTitle"]))
            created_date = kit_data["tenant"].created_at.strftime('%d/%m/%Y') if kit_data["tenant"].created_at else "N/A"
            tenant_info = [
                [t["company_name"], kit_data["tenant"].name],
                [t["slug"], kit_data["tenant"].slug],
                [t["created_on"], created_date],
                [t["status"], t["active"] if kit_data["tenant"].is_active else t["inactive"]]
            ]
            tenant_table = Table(tenant_info, colWidths=[80*mm, 100*mm])
            tenant_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(tenant_table)
            story.append(Spacer(1, 20))
            
            logging.info("Controllo sezioni opzionali")

            # 2. ASSET CRITICI
            if options.get("include_assets", True) and "assets" in kit_data:
                logging.info("Aggiunta sezione asset critici")
                story.append(Paragraph(f"2. {t['critical_assets']}", self.styles["SectionTitle"]))
                
                # Filtra asset critici (high risk o critical)
                critical_assets = []
                for asset in kit_data["assets"]:
                    # Considera critici asset con risk_score alto o status critico
                    if hasattr(asset, 'risk_score') and asset.risk_score and asset.risk_score > 7:
                        critical_assets.append(asset)
                    elif hasattr(asset, 'status') and asset.status and 'critic' in asset.status.name.lower():
                        critical_assets.append(asset)
                    elif hasattr(asset, 'criticality') and asset.criticality and asset.criticality == 'critical':
                        critical_assets.append(asset)
                
                if critical_assets:
                    critical_data = [[t["name"], t["type"], t["status"], t["site"], t["risk_score"]]]
                    for asset in critical_assets:
                        critical_data.append([
                            asset.name,
                            asset.asset_type.name if asset.asset_type else "N/A",
                            asset.status.name if asset.status else "N/A",
                            asset.site.name if asset.site else "N/A",
                            str(getattr(asset, 'risk_score', 'N/A'))
                        ])
                    
                    critical_table = Table(critical_data, colWidths=[50*mm, 35*mm, 35*mm, 40*mm, 30*mm])
                    critical_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 7),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.yellow])
                    ]))
                    story.append(critical_table)
                else:
                    story.append(Paragraph(t["no_critical_assets"], self.styles["InfoText"]))
                
                story.append(Spacer(1, 20))

            # 3. STABILIMENTI E AREE
            if options.get("include_sites", True) and "sites" in kit_data:
                logging.info("Aggiunta sezione sites")
                story.append(Paragraph(f"3. {t['sites_areas']}", self.styles["SectionTitle"]))
                
                sites_data = [[t["name"], t["code"], t["address"], t["description"]]]
                for site in kit_data["sites"]:
                    sites_data.append([
                        site.name,
                        site.code,
                        site.address or "N/A",
                        site.description or "N/A"
                    ])
                
                sites_table = Table(sites_data, colWidths=[50*mm, 30*mm, 60*mm, 40*mm])
                sites_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(sites_table)
                story.append(Spacer(1, 20))

            # 4. INVENTARIO COMPLETO ASSET
            if options.get("include_assets", True) and "assets" in kit_data:
                logging.info("Aggiunta sezione inventario completo")
                story.append(Paragraph(f"4. {t['complete_inventory']}", self.styles["SectionTitle"]))
                
                for i, asset in enumerate(kit_data["assets"], 1):
                    # Header dell'asset
                    story.append(Paragraph(f"<b>Asset {i}: {asset.name}</b>", self.styles["InfoText"]))
                    
                    # Dettagli dell'asset
                    asset_details = [
                        [t["name"], asset.name],
                        [t["type"], asset.asset_type.name if asset.asset_type else "N/A"],
                        [t["site"], asset.site.name if asset.site else "N/A"],
                        [t["area"], asset.location.area.name if asset.location and asset.location.area else "N/A"],
                        [t["location"], asset.location.name if asset.location else "N/A"],
                        [t["ip"], asset.interfaces[0].ip_address if asset.interfaces else "N/A"],
                        [t["manufacturer"], asset.manufacturer.name if asset.manufacturer else "N/A"],
                        [t["serial_number"], asset.serial_number or "N/A"],
                        [t["notes"], asset.description or "N/A"]
                    ]
                    
                    # Creo una tabella per ogni asset
                    asset_table = Table(asset_details, colWidths=[50*mm, 130*mm])
                    asset_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
                    ]))
                    story.append(asset_table)
                    story.append(Spacer(1, 10))
                
                story.append(Spacer(1, 20))

            # 5. FORNITORI CRITICI
            if options.get("include_suppliers", True) and "suppliers" in kit_data:
                logging.info("Aggiunta sezione fornitori critici")
                story.append(Paragraph(f"5. {t['critical_suppliers']}", self.styles["SectionTitle"]))
                
                suppliers_data = [[t["name"], t["email"], t["phone"], t["address"]]]
                for supplier in kit_data["suppliers"]:
                    suppliers_data.append([
                        supplier.name,
                        supplier.email or "N/A",
                        supplier.phone or "N/A",
                        f"{supplier.address or ''} {supplier.city or ''}".strip() or "N/A"
                    ])
                
                suppliers_table = Table(suppliers_data, colWidths=[50*mm, 50*mm, 35*mm, 55*mm])
                suppliers_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(suppliers_table)
                story.append(Spacer(1, 20))

            # Footer
            story.append(Spacer(1, 20))
            footer_date_format = '%d/%m/%Y at %H:%M' if language == "en" else '%d/%m/%Y alle %H:%M'
            story.append(Paragraph(
                f"<i>{t['footer']} {datetime.now().strftime(footer_date_format)}</i>",
                self.styles["InfoText"]
            ))

            logging.info("Generazione PDF finale")
            # Genera il PDF
            doc.build(story)
            
            logging.info(f"PDF generato con successo: {filepath}")
            return str(filepath)

        except Exception as e:
            import logging
            logging.error(f"Errore nella generazione del printed kit: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Errore nella generazione del printed kit: {str(e)}")

import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import qrcode

from app.schemas.print import normalize_print_language
from app.services.print_data import option_enabled

logger = logging.getLogger(__name__)

_ASSET_I18N = {
    "en": {
        "header_title": "Industrace - Asset Card",
        "generated_on": "Generated on",
        "at_time": "at",
        "risk_section": "Risk",
        "network_section": "Network",
        "connections_section": "Connections",
        "contacts_section": "Contacts",
        "suppliers_section": "Suppliers",
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
        "asset_installation_date": "Installation Date",
        "asset_business_criticality": "Business Criticality",
        "asset_security_zone": "Security Zone",
        "asset_area": "Area",
        "asset_remote_access": "Remote Access",
        "asset_remote_access_type": "Access Type",
        "asset_protocols": "Protocols",
        "risk_score": "Risk Score",
        "business_criticality": "Criticality",
        "impact_value": "Impact",
        "purdue_level": "Purdue",
        "physical_access": "Physical Access",
        "exposure_level": "Exposure",
        "iface_name": "Name",
        "iface_type": "Type",
        "iface_ip": "IP",
        "iface_mac": "MAC",
        "iface_vlan": "VLAN",
        "iface_gateway": "Gateway",
        "iface_subnet": "Subnet",
        "iface_logical_port": "Logical port",
        "iface_plug_label": "Plug label",
        "supplier_name": "Name",
        "supplier_email": "Email",
        "supplier_phone": "Phone",
        "supplier_website": "Website",
        "supplier_notes": "Notes",
    },
    "it": {
        "header_title": "Industrace - Scheda Asset",
        "generated_on": "Generato il",
        "at_time": "alle ore",
        "risk_section": "Rischio",
        "network_section": "Rete",
        "connections_section": "Connessioni",
        "contacts_section": "Contatti",
        "suppliers_section": "Fornitori",
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
        "asset_installation_date": "Data installazione",
        "asset_business_criticality": "Criticità business",
        "asset_security_zone": "Zona di sicurezza",
        "asset_area": "Area",
        "asset_remote_access": "Accesso remoto",
        "asset_remote_access_type": "Tipo accesso remoto",
        "asset_protocols": "Protocolli",
        "risk_score": "Risk Score",
        "business_criticality": "Criticità",
        "impact_value": "Impatto",
        "purdue_level": "Purdue",
        "physical_access": "Accesso fisico",
        "exposure_level": "Esposizione",
        "iface_name": "Nome",
        "iface_type": "Tipo",
        "iface_ip": "IP",
        "iface_mac": "MAC",
        "iface_vlan": "VLAN",
        "iface_gateway": "Gateway",
        "iface_subnet": "Subnet",
        "iface_logical_port": "Porta logica",
        "iface_plug_label": "Etichetta presa",
        "supplier_name": "Nome",
        "supplier_email": "Email",
        "supplier_phone": "Telefono",
        "supplier_website": "Sito",
        "supplier_notes": "Note",
    },
}

_KIT_I18N = {
    "en": {
        "generated_on": "Generated on:",
        "generated_by": "Generated by:",
        "company_info": "COMPANY INFORMATION",
        "company_name": "Company Name",
        "slug": "Slug",
        "created_on": "Created on",
        "status": "Status",
        "active": "Active",
        "inactive": "Inactive",
        "critical_assets": "CRITICAL ASSETS",
        "name": "Name",
        "type": "Type",
        "site": "Site",
        "risk_score": "Risk Score",
        "no_critical_assets": "No critical assets identified",
        "sites_areas": "SITES AND AREAS",
        "code": "Code",
        "address": "Address",
        "description": "Description",
        "complete_inventory": "COMPLETE ASSET INVENTORY",
        "area": "Area",
        "location": "Location",
        "ip": "IP",
        "manufacturer": "Manufacturer",
        "serial_number": "Serial Number",
        "notes": "Notes",
        "contacts": "CONTACTS",
        "no_contacts": "No contacts found",
        "critical_suppliers": "CRITICAL SUPPLIERS",
        "email": "Email",
        "phone": "Phone",
        "footer": "Document automatically generated by Industrace on",
    },
    "it": {
        "generated_on": "Generato il:",
        "generated_by": "Generato da:",
        "company_info": "INFORMAZIONI AZIENDA",
        "company_name": "Nome Azienda",
        "slug": "Slug",
        "created_on": "Creato il",
        "status": "Stato",
        "active": "Attivo",
        "inactive": "Inattivo",
        "critical_assets": "ASSET CRITICI",
        "name": "Nome",
        "type": "Tipo",
        "site": "Sito",
        "risk_score": "Risk Score",
        "no_critical_assets": "Nessun asset critico identificato",
        "sites_areas": "STABILIMENTI E AREE",
        "code": "Codice",
        "address": "Indirizzo",
        "description": "Descrizione",
        "complete_inventory": "INVENTARIO COMPLETO ASSET",
        "area": "Area",
        "location": "Location",
        "ip": "IP",
        "manufacturer": "Produttore",
        "serial_number": "Serial Number",
        "notes": "Note",
        "contacts": "CONTATTI",
        "no_contacts": "Nessun contatto trovato",
        "critical_suppliers": "FORNITORI CRITICI",
        "email": "Email",
        "phone": "Telefono",
        "footer": "Documento generato automaticamente da Industrace il",
    },
}


class PDFGenerator:
    def __init__(self, upload_dir: str = "uploads/prints"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
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
        self.styles.add(
            ParagraphStyle(
                name="InfoText",
                parent=self.styles["Normal"],
                fontSize=9,
                spaceAfter=2,
                fontName="Helvetica",
            )
        )
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

    @staticmethod
    def _xml(value) -> str:
        return xml_escape("" if value is None else str(value))

    def _para(self, text: str, style=None) -> Paragraph:
        return Paragraph(text, style or self.styles["InfoText"])

    def _labeled(self, label: str, value: str) -> Paragraph:
        return self._para(
            f"<b>{self._xml(label)}:</b> {self._xml(value)}", self.styles["InfoText"]
        )

    def _output_dir(self, tenant_id=None) -> Path:
        if tenant_id:
            out = self.upload_dir / str(tenant_id)
        else:
            out = self.upload_dir
        out.mkdir(parents=True, exist_ok=True)
        return out

    def generate_qr_code(self, text: str, size: int = 80) -> BytesIO:
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer

    def _format_value(self, value, translations=None):
        if translations is None:
            translations = self._get_translations("en")
        na = translations.get("not_available", "N/A")
        if value is None or value == "" or value == na:
            return na
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y %H:%M")
        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value if v) or na
        return str(value)

    def _format_risk_score(self, risk_score, translations=None):
        if risk_score is None:
            if translations is None:
                translations = self._get_translations("en")
            return translations.get("not_available", "N/A")
        return f"{float(risk_score):.2f} / 10"

    def _separator(self):
        return Table(
            [[""]],
            colWidths=[180 * mm],
            rowHeights=[1],
            style=TableStyle(
                [("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#bfc9ca"))]
            ),
        )

    def _create_connections_table(
        self, asset: Dict[str, Any], translations: Optional[Dict[str, str]] = None
    ) -> Optional[Table]:
        connections = asset.get("connections", [])
        if not connections:
            return None
        if translations is None:
            translations = self._get_translations("en")

        headers = [
            translations.get("connected_asset", "Connected Asset"),
            translations.get("connection_type", "Type"),
            translations.get("local_interface", "Local Interface"),
            translations.get("remote_interface", "Remote Interface"),
            translations.get("port", "Port"),
            translations.get("protocol", "Protocol"),
        ]
        data = [headers]

        for conn in connections[:8]:
            target_asset = conn.get("target_asset", {})
            target_name = target_asset.get("name", "—") if target_asset else "—"
            if len(target_name) > 25:
                target_name = target_name[:22] + "..."

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
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
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
        for contact in contacts[:3]:
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

    def _get_translations(self, language: str) -> Dict[str, str]:
        lang = normalize_print_language(language)
        return _ASSET_I18N.get(lang, _ASSET_I18N["en"])

    def _info_table_style(self) -> TableStyle:
        return TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )

    def generate_asset_pdf(
        self,
        asset: Dict[str, Any],
        template: Dict[str, Any],
        options: Dict[str, Any],
        language: str = "en",
    ) -> str:
        """Generate a compact A4 asset sheet with ReportLab."""
        options = options or {}
        template_options = (template or {}).get("options") or {}
        options = {**template_options, **options}
        language = normalize_print_language(
            language or options.get("language") or options.get("lang")
        )
        translations = self._get_translations(language)

        filename = f"asset_{asset.get('id', 'unknown')}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = self._output_dir(asset.get("tenant_id")) / filename
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )
        story = []

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
                except Exception:
                    continue

        asset_name = self._format_value(asset.get("name", "Asset"), translations)
        centered_style = ParagraphStyle(
            "CenteredAssetName",
            parent=self.styles["InfoText"],
            alignment=TA_CENTER,
            fontSize=14,
            fontName="Helvetica-Bold",
        )
        asset_name_para = Paragraph(self._xml(asset_name), centered_style)

        current_date = datetime.now(timezone.utc)
        date_str = current_date.strftime("%d/%m/%Y")
        time_str = current_date.strftime("%H:%M")
        generated_on = translations.get("generated_on", "Generated on")
        at_time = translations.get("at_time", "at")
        date_para = Paragraph(
            f"<font size=8 color='#666'>{self._xml(generated_on)} {self._xml(date_str)}"
            f"<br/>{self._xml(at_time)} {self._xml(time_str)}</font>",
            self.styles["InfoText"],
        )

        header_row = [logo_img if logo_img else "", asset_name_para, date_para]
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

        def cell(key, value):
            return self._labeled(
                translations.get(key, key),
                self._format_value(value, translations),
            )

        empty = self._para("")
        asset_info_data = [
            [
                cell("asset_name", asset.get("name")),
                cell("asset_type", (asset.get("asset_type") or {}).get("name")),
                cell("asset_status", (asset.get("status") or {}).get("name")),
            ],
            [
                cell("asset_manufacturer", (asset.get("manufacturer") or {}).get("name")),
                cell("asset_model", asset.get("model")),
                cell("asset_serial", asset.get("serial_number")),
            ],
            [
                cell("asset_site", (asset.get("site") or {}).get("name")),
                cell("asset_location", (asset.get("location") or {}).get("name")),
                cell("asset_firmware", asset.get("firmware_version")),
            ],
        ]

        if (
            asset.get("installation_date")
            or asset.get("business_criticality")
            or asset.get("security_zone")
        ):
            zone = asset.get("security_zone")
            zone_name = zone.get("name") if isinstance(zone, dict) else zone
            asset_info_data.append(
                [
                    cell("asset_installation_date", asset.get("installation_date")),
                    cell("asset_business_criticality", asset.get("business_criticality")),
                    cell("asset_security_zone", zone_name),
                ]
            )

        if (
            asset.get("area")
            or asset.get("remote_access") is not None
            or asset.get("remote_access_type")
        ):
            area = asset.get("area")
            area_name = area.get("name") if isinstance(area, dict) else area
            remote_label = (
                translations.get("yes", "Yes")
                if asset.get("remote_access")
                else translations.get("no", "No")
            )
            asset_info_data.append(
                [
                    cell("asset_area", area_name),
                    cell("asset_remote_access", remote_label),
                    cell("asset_remote_access_type", asset.get("remote_access_type")),
                ]
            )

        protocols = asset.get("protocols") or []
        if isinstance(protocols, list) and protocols:
            asset_info_data.append(
                [
                    cell("asset_protocols", ", ".join(str(p) for p in protocols)),
                    empty,
                    empty,
                ]
            )

        asset_info_table = Table(asset_info_data, colWidths=[60 * mm, 60 * mm, 55 * mm])
        asset_info_table.setStyle(self._info_table_style())
        story.append(asset_info_table)
        story.append(Spacer(1, 8))
        story.append(self._separator())
        story.append(Spacer(1, 4))

        if option_enabled(
            options, "includePhoto", "include_photo", default=False
        ):
            for photo in asset.get("photos") or []:
                path = photo.get("file_path") if isinstance(photo, dict) else None
                if path and os.path.exists(path):
                    try:
                        story.append(Image(path, width=40 * mm, height=40 * mm))
                        story.append(Spacer(1, 4))
                        break
                    except Exception:
                        continue

        if option_enabled(
            options, "includeRiskMatrix", "include_risk_matrix", default=True
        ):
            story.append(
                Paragraph(
                    self._xml(translations.get("risk_section", "Risk")),
                    self.styles["SectionTitle"],
                )
            )
            risk_table = Table(
                [
                    [
                        self._labeled(
                            translations.get("risk_score", "Risk Score"),
                            self._format_risk_score(
                                asset.get("risk_score"), translations
                            ),
                        ),
                        cell("business_criticality", asset.get("business_criticality")),
                        cell("impact_value", asset.get("impact_value")),
                    ],
                    [
                        cell("purdue_level", asset.get("purdue_level")),
                        cell("physical_access", asset.get("physical_access_ease")),
                        cell("exposure_level", asset.get("exposure_level")),
                    ],
                ],
                colWidths=[60 * mm, 60 * mm, 55 * mm],
            )
            risk_table.setStyle(self._info_table_style())
            story.append(risk_table)
            story.append(Spacer(1, 4))

        interfaces = asset.get("interfaces") or []
        if isinstance(interfaces, list) and interfaces:
            story.append(
                Paragraph(
                    self._xml(
                        translations.get(
                            "network_interfaces_section", "Network Interfaces"
                        )
                    ),
                    self.styles["SectionTitle"],
                )
            )
            headers = [
                translations.get("iface_name", "Name"),
                translations.get("iface_type", "Type"),
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

        story.append(self._separator())
        story.append(Spacer(1, 4))

        if option_enabled(
            options, "includeConnections", "include_connections", default=True
        ):
            connections_table = self._create_connections_table(asset, translations)
            if connections_table:
                story.append(
                    Paragraph(
                        self._xml(
                            translations.get("connections_section", "Connections")
                        ),
                        self.styles["SectionTitle"],
                    )
                )
                story.append(connections_table)

        contacts_table = self._create_contacts_table(asset, translations)
        if contacts_table:
            story.append(
                Paragraph(
                    self._xml(translations.get("contacts_section", "Contacts")),
                    self.styles["SectionTitle"],
                )
            )
            story.append(contacts_table)

        suppliers = asset.get("suppliers") or []
        if isinstance(suppliers, list) and suppliers:
            story.append(
                Paragraph(
                    self._xml(translations.get("suppliers_section", "Suppliers")),
                    self.styles["SectionTitle"],
                )
            )
            supplier_data = [
                [
                    translations.get("supplier_name", "Name"),
                    translations.get("supplier_email", "Email"),
                    translations.get("supplier_phone", "Phone"),
                    translations.get("supplier_website", "Website"),
                    translations.get("supplier_notes", "Notes"),
                ]
            ]
            for supplier in suppliers:
                supplier_data.append(
                    [
                        self._format_value(supplier.get("name"), translations),
                        self._format_value(supplier.get("email"), translations),
                        self._format_value(supplier.get("phone"), translations),
                        self._format_value(supplier.get("website"), translations),
                        self._format_value(supplier.get("notes"), translations),
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

        if option_enabled(
            options, "includeCustomFields", "include_custom_fields", default=True
        ):
            custom_fields = asset.get("custom_fields") or {}
            if isinstance(custom_fields, dict) and custom_fields:
                story.append(
                    Paragraph(
                        self._xml(
                            translations.get("custom_fields_section", "Custom Fields")
                        ),
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

        if option_enabled(options, "includeQR", "include_qr", default=True):
            base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            asset_url = f"{base_url}/assets/{asset.get('id')}"
            qr_buffer = self.generate_qr_code(asset_url, 60)
            qr_img = Image(qr_buffer, width=30 * mm, height=30 * mm)
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    self._xml(
                        translations.get("qr_code_label", "QR Code for quick access")
                    ),
                    self.styles["Label"],
                )
            )
            story.append(qr_img)

        doc.build(story)
        return str(filepath)

    def get_file_size(self, filepath: str) -> int:
        try:
            return os.path.getsize(filepath)
        except OSError:
            return 0

    @staticmethod
    def _is_critical_kit_asset(asset) -> bool:
        risk = getattr(asset, "risk_score", None)
        if risk is not None:
            try:
                if float(risk) >= 7:
                    return True
            except (TypeError, ValueError):
                pass
        criticality = (
            getattr(asset, "business_criticality", None) or ""
        ).strip().lower()
        return criticality in ("critical", "high")

    def generate_printed_kit(
        self, kit_data: Dict[str, Any], options: Dict[str, Any]
    ) -> str:
        """Generate a tenant printed kit PDF."""
        try:
            language = normalize_print_language(
                (options or {}).get("language") or (options or {}).get("lang")
            )
            t = _KIT_I18N.get(language, _KIT_I18N["en"])
            section_num = 0

            def next_section_title(label: str) -> str:
                nonlocal section_num
                section_num += 1
                return f"{section_num}. {label}"

            tenant = kit_data["tenant"]
            tenant_dir = self._output_dir(tenant.id)
            tenant_slug = (
                (tenant.slug or tenant.name or "tenant").replace(" ", "_").lower()
            )
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"printed-kit-{tenant_slug}-{timestamp}.pdf"
            filepath = tenant_dir / filename

            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=15 * mm,
                bottomMargin=15 * mm,
            )

            story = []
            story.append(
                Paragraph(
                    f"<b>PRINTED KIT - {self._xml((tenant.name or '').upper())}</b>",
                    self.styles["AssetTitle"],
                )
            )
            story.append(Spacer(1, 10))

            date_format = (
                "%d/%m/%Y at %H:%M" if language == "en" else "%d/%m/%Y alle %H:%M"
            )
            generated_at = kit_data["generated_at"]
            story.append(
                self._para(
                    f"<b>{self._xml(t['generated_on'])}</b> "
                    f"{self._xml(generated_at.strftime(date_format))}"
                )
            )
            story.append(
                self._para(
                    f"<b>{self._xml(t['generated_by'])}</b> "
                    f"{self._xml(kit_data['generated_by'])}"
                )
            )
            story.append(Spacer(1, 15))

            story.append(
                Paragraph(
                    self._xml(next_section_title(t["company_info"])),
                    self.styles["SectionTitle"],
                )
            )
            created_date = (
                tenant.created_at.strftime("%d/%m/%Y") if tenant.created_at else "N/A"
            )
            tenant_info = [
                [t["company_name"], tenant.name],
                [t["slug"], tenant.slug],
                [t["created_on"], created_date],
                [t["status"], t["active"] if tenant.is_active else t["inactive"]],
            ]
            tenant_table = Table(tenant_info, colWidths=[80 * mm, 100 * mm])
            tenant_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.blue),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (1, 0), (1, -1), colors.white),
                        ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(tenant_table)
            story.append(Spacer(1, 20))

            if option_enabled(
                options, "include_assets", "includeAssets", default=True
            ) and "assets" in kit_data:
                story.append(
                    Paragraph(
                        self._xml(next_section_title(t["critical_assets"])),
                        self.styles["SectionTitle"],
                    )
                )
                critical_assets = [
                    asset
                    for asset in kit_data["assets"]
                    if self._is_critical_kit_asset(asset)
                ]
                if critical_assets:
                    critical_data = [
                        [t["name"], t["type"], t["status"], t["site"], t["risk_score"]]
                    ]
                    for asset in critical_assets:
                        risk = getattr(asset, "risk_score", None)
                        critical_data.append(
                            [
                                asset.name,
                                asset.asset_type.name if asset.asset_type else "N/A",
                                asset.status.name if asset.status else "N/A",
                                asset.site.name if asset.site else "N/A",
                                f"{float(risk):.2f}" if risk is not None else "N/A",
                            ]
                        )
                    critical_table = Table(
                        critical_data,
                        colWidths=[50 * mm, 35 * mm, 35 * mm, 40 * mm, 30 * mm],
                    )
                    critical_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.red),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 7),
                                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                                (
                                    "ROWBACKGROUNDS",
                                    (0, 1),
                                    (-1, -1),
                                    [colors.white, colors.yellow],
                                ),
                            ]
                        )
                    )
                    story.append(critical_table)
                else:
                    story.append(
                        Paragraph(self._xml(t["no_critical_assets"]), self.styles["InfoText"])
                    )
                story.append(Spacer(1, 20))

            if option_enabled(
                options, "include_sites", "includeSites", default=True
            ) and "sites" in kit_data:
                story.append(
                    Paragraph(
                        self._xml(next_section_title(t["sites_areas"])),
                        self.styles["SectionTitle"],
                    )
                )
                sites_data = [[t["name"], t["code"], t["address"], t["description"]]]
                for site in kit_data["sites"]:
                    sites_data.append(
                        [
                            site.name,
                            site.code,
                            site.address or "N/A",
                            site.description or "N/A",
                        ]
                    )
                sites_table = Table(
                    sites_data, colWidths=[50 * mm, 30 * mm, 60 * mm, 40 * mm]
                )
                sites_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(sites_table)
                story.append(Spacer(1, 20))

            if option_enabled(
                options, "include_assets", "includeAssets", default=True
            ) and "assets" in kit_data:
                story.append(
                    Paragraph(
                        self._xml(next_section_title(t["complete_inventory"])),
                        self.styles["SectionTitle"],
                    )
                )
                for i, asset in enumerate(kit_data["assets"], 1):
                    story.append(
                        self._para(
                            f"<b>Asset {i}: {self._xml(asset.name)}</b>"
                        )
                    )
                    first_ip = "N/A"
                    if getattr(asset, "interfaces", None):
                        first_ip = asset.interfaces[0].ip_address or "N/A"
                    asset_details = [
                        [t["name"], asset.name],
                        [
                            t["type"],
                            asset.asset_type.name if asset.asset_type else "N/A",
                        ],
                        [t["site"], asset.site.name if asset.site else "N/A"],
                        [
                            t["area"],
                            asset.location.area.name
                            if asset.location and asset.location.area
                            else "N/A",
                        ],
                        [
                            t["location"],
                            asset.location.name if asset.location else "N/A",
                        ],
                        [t["ip"], first_ip],
                        [
                            t["manufacturer"],
                            asset.manufacturer.name if asset.manufacturer else "N/A",
                        ],
                        [t["serial_number"], asset.serial_number or "N/A"],
                        [t["notes"], asset.description or "N/A"],
                    ]
                    asset_table = Table(asset_details, colWidths=[50 * mm, 130 * mm])
                    asset_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (0, -1), colors.grey),
                                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )
                    story.append(asset_table)
                    story.append(Spacer(1, 10))
                story.append(Spacer(1, 20))

            if option_enabled(
                options, "include_contacts", "includeContacts", default=True
            ) and "contacts" in kit_data:
                story.append(
                    Paragraph(
                        self._xml(next_section_title(t["contacts"])),
                        self.styles["SectionTitle"],
                    )
                )
                contacts = kit_data["contacts"]
                if contacts:
                    contacts_data = [
                        [t["name"], t["type"], t["email"], t["phone"], t["notes"]]
                    ]
                    for contact in contacts:
                        full_name = (
                            f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                            or "N/A"
                        )
                        phone = contact.phone1 or contact.phone2 or "N/A"
                        contacts_data.append(
                            [
                                full_name,
                                contact.type or "N/A",
                                contact.email or "N/A",
                                phone,
                                (contact.notes or "N/A")[:80],
                            ]
                        )
                    contacts_table = Table(
                        contacts_data,
                        colWidths=[40 * mm, 25 * mm, 45 * mm, 30 * mm, 40 * mm],
                    )
                    contacts_table.setStyle(
                        TableStyle(
                            [
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (-1, 0),
                                    colors.Color(0.2, 0.4, 0.6),
                                ),
                                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 8),
                                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ]
                        )
                    )
                    story.append(contacts_table)
                else:
                    story.append(
                        Paragraph(self._xml(t["no_contacts"]), self.styles["InfoText"])
                    )
                story.append(Spacer(1, 20))

            if option_enabled(
                options, "include_suppliers", "includeSuppliers", default=True
            ) and "suppliers" in kit_data:
                story.append(
                    Paragraph(
                        self._xml(next_section_title(t["critical_suppliers"])),
                        self.styles["SectionTitle"],
                    )
                )
                suppliers_data = [[t["name"], t["email"], t["phone"], t["address"]]]
                for supplier in kit_data["suppliers"]:
                    suppliers_data.append(
                        [
                            supplier.name,
                            supplier.email or "N/A",
                            supplier.phone or "N/A",
                            f"{supplier.address or ''} {supplier.city or ''}".strip()
                            or "N/A",
                        ]
                    )
                suppliers_table = Table(
                    suppliers_data, colWidths=[50 * mm, 50 * mm, 35 * mm, 55 * mm]
                )
                suppliers_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.orange),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]
                    )
                )
                story.append(suppliers_table)
                story.append(Spacer(1, 20))

            story.append(Spacer(1, 20))
            footer_date_format = (
                "%d/%m/%Y at %H:%M" if language == "en" else "%d/%m/%Y alle %H:%M"
            )
            story.append(
                Paragraph(
                    f"<i>{self._xml(t['footer'])} "
                    f"{self._xml(datetime.now(timezone.utc).strftime(footer_date_format))}</i>",
                    self.styles["InfoText"],
                )
            )

            doc.build(story)
            return str(filepath)

        except Exception as e:
            logger.error("Printed kit generation failed: %s", e, exc_info=True)
            raise

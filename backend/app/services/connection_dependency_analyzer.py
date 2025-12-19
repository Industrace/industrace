# backend/app/services/connection_dependency_analyzer.py
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from app.models.asset_connection import AssetConnection
from app.models.asset_dependency import AssetDependency


class ConnectionDependencyAnalyzer:
    """
    Service per analizzare la relazione tra AssetConnection (connessioni fisiche)
    e AssetDependency (dipendenze logiche).
    
    Fornisce visibilità incrociata per identificare:
    - Connessioni con dipendenza corrispondente
    - Connessioni senza dipendenza (potenziale gap)
    - Dipendenze senza connessione (dipendenze logiche pure)
    - Connessioni critiche senza dipendenza (criticità)
    """
    
    CRITICAL_CONNECTION_TYPES = ['control', 'safety', 'operational', 'critical']
    
    @staticmethod
    def get_connection_dependency_status(
        db: Session,
        connection: AssetConnection
    ) -> Dict[str, Any]:
        """
        Analizza lo stato di relazione tra una connessione e le dipendenze.
        
        Args:
            connection: AssetConnection da analizzare
        
        Returns:
            Dict con:
            - 'has_dependency': bool
            - 'dependency_id': UUID (se esiste)
            - 'status': 'complete'|'missing'|'logical_only'|'connection_only'
            - 'severity': 'info'|'warning'|'critical'
            - 'suggested_action': str
        """
        if not connection.parent_asset_id or not connection.child_asset_id:
            return {
                'has_dependency': False,
                'dependency_id': None,
                'status': 'connection_only',
                'severity': 'info',
                'suggested_action': 'Connection incomplete (missing assets)'
            }
        
        # Cerca dipendenza corrispondente (bidirezionale)
        # Dipendenza A→B può matchare connessione A→B o B→A
        dependency = (
            db.query(AssetDependency)
            .filter(
                AssetDependency.tenant_id == connection.tenant_id,
                or_(
                    # Stessa direzione
                    and_(
                        AssetDependency.dependent_asset_id == connection.parent_asset_id,
                        AssetDependency.dependency_asset_id == connection.child_asset_id
                    ),
                    # Direzione inversa (se bidirezionale)
                    and_(
                        AssetDependency.dependent_asset_id == connection.child_asset_id,
                        AssetDependency.dependency_asset_id == connection.parent_asset_id
                    )
                )
            )
            .first()
        )
        
        has_dependency = dependency is not None
        
        # Determina severity basandosi su tipo di connessione
        is_critical = connection.connection_type in ConnectionDependencyAnalyzer.CRITICAL_CONNECTION_TYPES
        
        if has_dependency:
            status = 'complete'
            severity = 'info'
            suggested_action = None
        elif is_critical:
            status = 'missing'
            severity = 'critical'
            suggested_action = f'Critical connection ({connection.connection_type}) should have corresponding dependency'
        else:
            status = 'connection_only'
            severity = 'warning'
            suggested_action = 'Consider creating dependency for complete modeling'
        
        return {
            'has_dependency': has_dependency,
            'dependency_id': str(dependency.id) if dependency else None,
            'status': status,
            'severity': severity,
            'suggested_action': suggested_action,
            'connection_type': connection.connection_type,
            'is_critical': is_critical
        }
    
    @staticmethod
    def get_connections_with_dependency_status(
        db: Session,
        asset_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Ottiene tutte le connessioni di un asset con il loro stato di dipendenza.
        
        Args:
            asset_id: ID dell'asset
            tenant_id: ID del tenant
        
        Returns:
            Lista di dict con informazioni connessione + dependency_status
        """
        # Ottieni tutte le connessioni dell'asset (come parent o child)
        connections = (
            db.query(AssetConnection)
            .filter(
                AssetConnection.tenant_id == tenant_id,
                or_(
                    AssetConnection.parent_asset_id == asset_id,
                    AssetConnection.child_asset_id == asset_id
                )
            )
            .all()
        )
        
        result = []
        for conn in connections:
            status = ConnectionDependencyAnalyzer.get_connection_dependency_status(db, conn)
            
            # Determina asset collegato
            if conn.parent_asset_id == asset_id:
                connected_asset_id = conn.child_asset_id
                connected_asset = conn.child_asset
            else:
                connected_asset_id = conn.parent_asset_id
                connected_asset = conn.parent_asset
            
            result.append({
                'connection_id': str(conn.id),
                'connected_asset_id': str(connected_asset_id),
                'connected_asset_name': connected_asset.name if connected_asset else None,
                'connection_type': conn.connection_type,
                'protocol': conn.protocol,
                'port_parent': conn.port_parent,
                'port_child': conn.port_child,
                'description': conn.description,
                'dependency_status': status
            })
        
        return result
    
    @staticmethod
    def find_missing_dependencies(
        db: Session,
        tenant_id: uuid.UUID,
        critical_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Trova connessioni critiche senza dipendenza corrispondente.
        
        Args:
            tenant_id: ID del tenant
            critical_only: Se True, solo connessioni critiche
        
        Returns:
            Lista di connessioni con missing dependency
        """
        query = (
            db.query(AssetConnection)
            .filter(AssetConnection.tenant_id == tenant_id)
        )
        
        if critical_only:
            query = query.filter(
                AssetConnection.connection_type.in_(
                    ConnectionDependencyAnalyzer.CRITICAL_CONNECTION_TYPES
                )
            )
        
        connections = query.all()
        
        missing = []
        for conn in connections:
            if not conn.parent_asset_id or not conn.child_asset_id:
                continue
            
            status = ConnectionDependencyAnalyzer.get_connection_dependency_status(db, conn)
            
            if status['status'] == 'missing':
                missing.append({
                    'connection_id': str(conn.id),
                    'parent_asset_id': str(conn.parent_asset_id),
                    'parent_asset_name': conn.parent_asset.name if conn.parent_asset else None,
                    'child_asset_id': str(conn.child_asset_id),
                    'child_asset_name': conn.child_asset.name if conn.child_asset else None,
                    'connection_type': conn.connection_type,
                    'protocol': conn.protocol,
                    'severity': status['severity'],
                    'suggested_action': status['suggested_action']
                })
        
        return missing
    
    @staticmethod
    def suggest_dependency_from_connection(
        db: Session,
        connection: AssetConnection
    ) -> Dict[str, Any]:
        """
        Suggerisce tipo di dipendenza basandosi sul tipo di connessione.
        
        Args:
            connection: AssetConnection da cui suggerire dipendenza
        
        Returns:
            Dict con suggerimenti per creare AssetDependency
        """
        if not connection.parent_asset_id or not connection.child_asset_id:
            return {
                'error': 'Connection incomplete (missing assets)'
            }
        
        # Mapping connection_type -> dependency_type
        type_mapping = {
            'control': 'control_flow',
            'safety': 'control_flow',
            'operational': 'functional',
            'data': 'data_flow',
            'network': 'functional',
            'ethernet': 'functional',
            'serial': 'functional',
            'wireless': 'functional'
        }
        
        # Determina dependency_type
        dependency_type = type_mapping.get(
            connection.connection_type.lower(),
            'functional'  # Default
        )
        
        # Determina criticality basandosi su connection_type
        if connection.connection_type in ['control', 'safety', 'critical']:
            criticality = 'critical'
        elif connection.connection_type in ['operational']:
            criticality = 'high'
        else:
            criticality = 'medium'
        
        # Confidence: se connessione esiste, dipendenza è probabile (medium)
        confidence = 'medium'
        
        # Source: manual (utente deve crearla)
        source = 'manual'
        
        return {
            'dependent_asset_id': str(connection.parent_asset_id),
            'dependency_asset_id': str(connection.child_asset_id),
            'dependency_type': dependency_type,
            'criticality': criticality,
            'confidence': confidence,
            'source': source,
            'description': f'Dependency suggested from {connection.connection_type} connection',
            'suggested': True,
            'connection_id': str(connection.id)
        }
    
    @staticmethod
    def get_dependency_connection_status(
        db: Session,
        dependency: AssetDependency
    ) -> Dict[str, Any]:
        """
        Analizza se una dipendenza ha una connessione corrispondente.
        
        Args:
            dependency: AssetDependency da analizzare
        
        Returns:
            Dict con informazioni sulla connessione corrispondente
        """
        # Cerca connessione corrispondente (bidirezionale)
        connection = (
            db.query(AssetConnection)
            .filter(
                AssetConnection.tenant_id == dependency.tenant_id,
                or_(
                    # Stessa direzione
                    and_(
                        AssetConnection.parent_asset_id == dependency.dependent_asset_id,
                        AssetConnection.child_asset_id == dependency.dependency_asset_id
                    ),
                    # Direzione inversa
                    and_(
                        AssetConnection.parent_asset_id == dependency.dependency_asset_id,
                        AssetConnection.child_asset_id == dependency.dependent_asset_id
                    )
                )
            )
            .first()
        )
        
        has_connection = connection is not None
        
        return {
            'has_connection': has_connection,
            'connection_id': str(connection.id) if connection else None,
            'status': 'complete' if has_connection else 'logical_only',
            'connection_type': connection.connection_type if connection else None,
            'protocol': connection.protocol if connection else None
        }



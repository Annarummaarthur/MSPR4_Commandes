from fastapi import FastAPI, HTTPException, Depends, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import BaseModel, ConfigDict, validator, Field
from typing import List, Optional
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from db import SessionLocal, Base, engine

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration sécurité
security = HTTPBearer()
API_TOKEN = os.getenv("API_TOKEN", "default_token_mspr4_commandes")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_TOKEN:
        logger.warning(f"Tentative d'accès avec token invalide: {credentials.credentials[:10]}...")
        raise HTTPException(status_code=401, detail="Token invalide")
    return credentials

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="Microservice Commandes MSPR4",
    description="Microservice dédié uniquement à la gestion des commandes (Architecture Microservices Pure)",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS pour la communication inter-services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle SQLAlchemy - Commandes uniquement
class CommandeModel(Base):
    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=True, index=True)
    status = Column(String(50), default="pending", index=True)
    total_amount = Column(DECIMAL(10, 2), default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)

# Modèles Pydantic avec validation améliorée
class Commande(BaseModel):
    """Modèle complet d'une commande (microservice pur)"""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    order_id: str = Field(..., min_length=1, max_length=50, description="Identifiant unique de la commande")
    customer_id: str = Field(..., min_length=1, max_length=50, description="Identifiant du client")
    created_at: Optional[datetime] = None
    status: str = Field(default="pending", description="Statut de la commande")
    total_amount: Optional[float] = Field(default=0, ge=0, description="Montant total de la commande")
    updated_at: Optional[datetime] = None

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Le statut doit être un de: {", ".join(valid_statuses)}')
        return v

class CommandeCreate(BaseModel):
    """Modèle pour créer une commande"""
    order_id: str = Field(..., min_length=1, max_length=50)
    customer_id: str = Field(..., min_length=1, max_length=50)
    created_at: Optional[datetime] = None
    status: str = Field(default="pending")
    total_amount: Optional[float] = Field(default=0, ge=0)

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Le statut doit être un de: {", ".join(valid_statuses)}')
        return v

class CommandeUpdate(BaseModel):
    """Modèle pour modifier une commande"""
    customer_id: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None
    total_amount: Optional[float] = Field(None, ge=0)

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "processing", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f'Le statut doit être un de: {", ".join(valid_statuses)}')
        return v

class StatusUpdate(BaseModel):
    """Modèle pour mettre à jour le statut d'une commande"""
    status: str = Field(..., description="Nouveau statut de la commande")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Le statut doit être un de: {", ".join(valid_statuses)}')
        return v

# Gestionnaire d'erreurs global
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc):
    logger.error(f"Erreur base de données: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne de la base de données"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    logger.error(f"Erreur de validation: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

# Endpoints

@app.get("/")
def health_check():
    return {
        "status": "OK",
        "service": "Microservice Commandes",
        "version": "3.0.0",
        "architecture": "microservices_pure",
        "responsabilite": "Gestion UNIQUEMENT des commandes",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/stats")
def get_stats(db: Session = Depends(get_db), _: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        total_commandes = db.query(CommandeModel).count()
        total_amount = db.query(func.sum(CommandeModel.total_amount)).scalar() or 0
        
        # Statistiques par statut
        stats_status = {}
        statuts = ["pending", "processing", "completed", "cancelled"]
        for statut in statuts:
            count = db.query(CommandeModel).filter(CommandeModel.status == statut).count()
            stats_status[statut] = count
        
        # Statistiques avancées
        avg_amount = db.query(func.avg(CommandeModel.total_amount)).scalar() or 0
        max_amount = db.query(func.max(CommandeModel.total_amount)).scalar() or 0
        min_amount = db.query(func.min(CommandeModel.total_amount)).scalar() or 0
        
        return {
            "total_commandes": total_commandes,
            "montant_total": float(total_amount),
            "montant_moyen": float(avg_amount),
            "montant_max": float(max_amount),
            "montant_min": float(min_amount),
            "commandes_par_statut": stats_status,
            "microservice": "Commandes uniquement",
            "note": "Les produits et clients sont gérés par d'autres microservices"
        }
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors du calcul des statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du calcul des statistiques")

@app.get("/commandes", response_model=List[Commande])
def get_commandes(
    limit: int = Query(default=100, le=1000, ge=1, description="Nombre maximum de commandes à retourner"),
    offset: int = Query(default=0, ge=0, description="Nombre de commandes à ignorer"),
    status: Optional[str] = Query(default=None, description="Filtrer par statut"),
    customer_id: Optional[str] = Query(default=None, description="Filtrer par ID client"),
    order_by: Optional[str] = Query(default="id", description="Champ de tri (id, created_at, total_amount, status)"),
    order_direction: Optional[str] = Query(default="asc", description="Direction du tri (asc, desc)"),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        query = db.query(CommandeModel)
        
        # Filtres optionnels
        if status:
            valid_statuses = ["pending", "processing", "completed", "cancelled"]
            if status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs autorisées: {valid_statuses}")
            query = query.filter(CommandeModel.status == status)
        
        if customer_id:
            query = query.filter(CommandeModel.customer_id == customer_id)
        
        # Tri
        valid_order_fields = ["id", "created_at", "total_amount", "status", "order_id"]
        if order_by not in valid_order_fields:
            raise HTTPException(status_code=400, detail=f"Champ de tri invalide. Valeurs autorisées: {valid_order_fields}")
        
        if order_direction not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Direction de tri invalide. Valeurs autorisées: asc, desc")
        
        order_field = getattr(CommandeModel, order_by)
        if order_direction == "desc":
            order_field = order_field.desc()
        
        query = query.order_by(order_field)
        
        # Pagination
        return query.offset(offset).limit(limit).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des commandes: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des commandes")

# Endpoint de recherche avancée - DOIT être avant les routes avec paramètres
@app.get("/commandes/search", response_model=List[Commande])
def search_commandes(
    q: Optional[str] = Query(None, description="Recherche dans order_id ou customer_id"),
    min_amount: Optional[float] = Query(None, ge=0, description="Montant minimum"),
    max_amount: Optional[float] = Query(None, ge=0, description="Montant maximum"),
    date_from: Optional[str] = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    limit: int = Query(default=100, le=1000, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    """Recherche avancée dans les commandes"""
    try:
        query = db.query(CommandeModel)
        
        # Recherche textuelle
        if q:
            query = query.filter(
                (CommandeModel.order_id.ilike(f"%{q}%")) |
                (CommandeModel.customer_id.ilike(f"%{q}%"))
            )
        
        # Filtres par montant
        if min_amount is not None:
            query = query.filter(CommandeModel.total_amount >= min_amount)
        if max_amount is not None:
            query = query.filter(CommandeModel.total_amount <= max_amount)
        
        # Filtres par date
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(CommandeModel.created_at >= date_from_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date invalide pour date_from (YYYY-MM-DD)")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                query = query.filter(CommandeModel.created_at <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date invalide pour date_to (YYYY-MM-DD)")
        
        return query.order_by(CommandeModel.created_at.desc()).offset(offset).limit(limit).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")

@app.post("/commandes", response_model=Commande)
def create_commande(
    commande: CommandeCreate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        # Vérifier si l'order_id existe déjà
        existing_commande = db.query(CommandeModel).filter(CommandeModel.order_id == commande.order_id).first()
        if existing_commande:
            raise HTTPException(status_code=409, detail="Une commande avec cet order_id existe déjà")
        
        # Créer la commande
        commande_data = commande.model_dump()
        commande_data["updated_at"] = datetime.utcnow()
        
        # Si created_at n'est pas fourni, utiliser la date actuelle
        if not commande_data.get("created_at"):
            commande_data["created_at"] = datetime.utcnow()
        
        db_commande = CommandeModel(**commande_data)
        db.add(db_commande)
        db.commit()
        db.refresh(db_commande)
        
        logger.info(f"Commande créée: {db_commande.order_id} pour client {db_commande.customer_id}")
        return db_commande
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflit de données - ordre_id déjà existant")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur lors de la création de la commande: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la commande")

@app.get("/commandes/{id}", response_model=Commande)
def get_commande(id: int, db: Session = Depends(get_db), _: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        commande = db.query(CommandeModel).filter(CommandeModel.id == id).first()
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        return commande
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de la commande {id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de la commande")

@app.get("/commandes/order/{order_id}", response_model=Commande)
def get_commande_by_order_id(order_id: str, db: Session = Depends(get_db), _: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        commande = db.query(CommandeModel).filter(CommandeModel.order_id == order_id).first()
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        return commande
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération de la commande {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération de la commande")

@app.get("/commandes/customer/{customer_id}", response_model=List[Commande])
def get_commandes_by_customer(
    customer_id: str, 
    limit: int = Query(default=100, le=1000, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db), 
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        return db.query(CommandeModel).filter(CommandeModel.customer_id == customer_id).offset(offset).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des commandes pour le client {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des commandes")

@app.put("/commandes/{id}", response_model=Commande)
def update_commande(
    id: int,
    commande_update: CommandeUpdate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    try:
        commande = db.query(CommandeModel).filter(CommandeModel.id == id).first()
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        # Mettre à jour les champs fournis
        update_data = commande_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(commande, field, value)
        
        commande.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(commande)
        
        logger.info(f"Commande {id} mise à jour")
        return commande
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour de la commande {id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour de la commande")

@app.delete("/commandes/{id}")
def delete_commande(id: int, db: Session = Depends(get_db), _: HTTPAuthorizationCredentials = Security(verify_token)):
    try:
        commande = db.query(CommandeModel).filter(CommandeModel.id == id).first()
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        order_id = commande.order_id
        db.delete(commande)
        db.commit()
        
        logger.info(f"Commande {id} ({order_id}) supprimée")
        return {"message": "Commande supprimée avec succès", "order_id": order_id}
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur lors de la suppression de la commande {id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression de la commande")

# Endpoints pour la gestion des statuts (spécifique aux commandes)
@app.put("/commandes/{id}/status", response_model=Commande)
def update_commande_status(
    id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    """Mettre à jour uniquement le statut d'une commande"""
    try:
        commande = db.query(CommandeModel).filter(CommandeModel.id == id).first()
        if not commande:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        
        old_status = commande.status
        commande.status = status_update.status
        commande.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(commande)
        
        logger.info(f"Statut de la commande {id} changé de '{old_status}' à '{status_update.status}'")
        return commande
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour du statut de la commande {id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la mise à jour du statut")

@app.get("/commandes/status/{status}", response_model=List[Commande])
def get_commandes_by_status(
    status: str, 
    limit: int = Query(default=100, le=1000, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db), 
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    """Récupérer toutes les commandes avec un statut donné"""
    try:
        valid_statuses = ["pending", "processing", "completed", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs autorisées: {valid_statuses}")
        
        return db.query(CommandeModel).filter(CommandeModel.status == status).offset(offset).limit(limit).all()
        
    except SQLAlchemyError as e:
        logger.error(f"Erreur lors de la récupération des commandes avec statut {status}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des commandes")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) # Test CI/CD - Ven 18 jul 2025 23:33:24 CEST

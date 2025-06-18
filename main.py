from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Text
from db import SessionLocal, Base, engine
from dotenv import load_dotenv
from datetime import datetime
import os
import uvicorn

load_dotenv()

security = HTTPBearer()
API_TOKEN = os.getenv("API_TOKEN")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Accès interdit")


app = FastAPI(
    title="API Gestion des Commandes MSPR4",
    description="API pour la gestion des commandes et produits de commandes",
    version="1.0.0"
)


# Modèles SQLAlchemy (correspondant exactement à votre structure existante)
class CommandeModel(Base):
    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=True)
    total_amount = Column(DECIMAL(10, 2), default=0)
    
    # Relation avec les produits
    produits = relationship("ProduitCommandeModel", back_populates="commande", cascade="all, delete-orphan")


class ProduitCommandeModel(Base):
    __tablename__ = "produits_commandes"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("commandes.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(50), nullable=True)
    product_name = Column(String(255), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String(100), nullable=True)
    stock = Column(Integer, nullable=True)
    product_created_at = Column(DateTime, nullable=True)
    
    # Relation avec la commande
    commande = relationship("CommandeModel", back_populates="produits")


# Ne pas recréer les tables si elles existent déjà
# Base.metadata.create_all(bind=engine)


# Modèles Pydantic
class ProduitCommande(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None
    product_created_at: Optional[datetime] = None


class Commande(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    order_id: str
    customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    total_amount: Optional[float] = None
    produits: Optional[List[ProduitCommande]] = []


class CommandeCreate(BaseModel):
    order_id: str
    customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    total_amount: Optional[float] = None
    produits: Optional[List[ProduitCommande]] = []


class CommandeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    total_amount: Optional[float] = None


class ProduitCommandeCreate(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None
    product_created_at: Optional[datetime] = None


class ProduitCommandeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None
    product_created_at: Optional[datetime] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoints pour les commandes
@app.get("/", response_model=dict)
def health_check():
    return {
        "status": "API Commandes MSPR4 opérationnelle",
        "project": "MSPR4_Commandes",
        "database": "Supabase"
    }


@app.get("/stats", response_model=dict)
def get_stats(
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    nb_commandes = db.query(CommandeModel).count()
    nb_produits = db.query(ProduitCommandeModel).count()
    
    # Calcul du montant total
    from sqlalchemy import func
    total_amount = db.query(func.sum(CommandeModel.total_amount)).scalar()
    
    return {
        "nombre_commandes": nb_commandes,
        "nombre_produits": nb_produits,
        "montant_total": float(total_amount) if total_amount else 0
    }


@app.post("/commandes", response_model=Commande)
def create_commande(
    commande: CommandeCreate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    # Vérifier si l'order_id existe déjà
    existing_commande = db.query(CommandeModel).filter(CommandeModel.order_id == commande.order_id).first()
    if existing_commande:
        raise HTTPException(status_code=400, detail="Une commande avec cet order_id existe déjà")
    
    # Créer la commande
    commande_data = commande.model_dump(exclude={"produits"})
    db_commande = CommandeModel(**commande_data)
    db.add(db_commande)
    db.flush()  # Pour récupérer l'ID généré
    
    # Ajouter les produits si fournis
    if commande.produits:
        for produit_data in commande.produits:
            produit_dict = produit_data.model_dump()
            produit_dict["order_id"] = commande.order_id
            db_produit = ProduitCommandeModel(**produit_dict)
            db.add(db_produit)
    
    db.commit()
    db.refresh(db_commande)
    return db_commande


@app.get("/commandes", response_model=List[Commande])
def list_commandes(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    return db.query(CommandeModel).offset(offset).limit(limit).all()


@app.get("/commandes/{commande_id}", response_model=Commande)
def get_commande(
    commande_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    commande = db.query(CommandeModel).filter(CommandeModel.id == commande_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return commande


@app.get("/commandes/order/{order_id}", response_model=Commande)
def get_commande_by_order_id(
    order_id: str,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    commande = db.query(CommandeModel).filter(CommandeModel.order_id == order_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return commande


@app.get("/commandes/customer/{customer_id}", response_model=List[Commande])
def get_commandes_by_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    return db.query(CommandeModel).filter(CommandeModel.customer_id == customer_id).all()


@app.put("/commandes/{commande_id}", response_model=Commande)
def update_commande(
    commande_id: int,
    updated_commande: CommandeUpdate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    commande = db.query(CommandeModel).filter(CommandeModel.id == commande_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    for field, value in updated_commande.model_dump(exclude_unset=True).items():
        setattr(commande, field, value)
    
    db.commit()
    db.refresh(commande)
    return commande


@app.delete("/commandes/{commande_id}", response_model=dict)
def delete_commande(
    commande_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    commande = db.query(CommandeModel).filter(CommandeModel.id == commande_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    db.delete(commande)
    db.commit()
    return {"message": "Commande supprimée avec succès"}


# Endpoints pour les produits de commandes
@app.post("/commandes/{order_id}/produits", response_model=ProduitCommande)
def add_produit_to_commande(
    order_id: str,
    produit: ProduitCommandeCreate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    # Vérifier que la commande existe
    commande = db.query(CommandeModel).filter(CommandeModel.order_id == order_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    produit_data = produit.model_dump()
    produit_data["order_id"] = order_id
    db_produit = ProduitCommandeModel(**produit_data)
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit


@app.get("/commandes/{order_id}/produits", response_model=List[ProduitCommande])
def get_produits_commande(
    order_id: str,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    # Vérifier que la commande existe
    commande = db.query(CommandeModel).filter(CommandeModel.order_id == order_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    
    return db.query(ProduitCommandeModel).filter(ProduitCommandeModel.order_id == order_id).all()


@app.get("/produits-commandes", response_model=List[ProduitCommande])
def list_all_produits_commandes(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    return db.query(ProduitCommandeModel).offset(offset).limit(limit).all()


@app.get("/produits-commandes/{produit_id}", response_model=ProduitCommande)
def get_produit_commande(
    produit_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    produit = db.query(ProduitCommandeModel).filter(ProduitCommandeModel.id == produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit de commande non trouvé")
    return produit


@app.put("/produits-commandes/{produit_id}", response_model=ProduitCommande)
def update_produit_commande(
    produit_id: int,
    updated_produit: ProduitCommandeUpdate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    produit = db.query(ProduitCommandeModel).filter(ProduitCommandeModel.id == produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit de commande non trouvé")
    
    for field, value in updated_produit.model_dump(exclude_unset=True).items():
        setattr(produit, field, value)
    
    db.commit()
    db.refresh(produit)
    return produit


@app.delete("/produits-commandes/{produit_id}", response_model=dict)
def delete_produit_commande(
    produit_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    produit = db.query(ProduitCommandeModel).filter(ProduitCommandeModel.id == produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit de commande non trouvé")
    
    db.delete(produit)
    db.commit()
    return {"message": "Produit de commande supprimé avec succès"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True) 
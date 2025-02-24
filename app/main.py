import random
import uuid
import json
import asyncio
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID

# Configuration de la base de données PostgreSQL
DATABASE_URL = "sqlite:///./chatbot.db" # Changer pour PostgreSQL si nécessaire avec l'image Docker
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modèles SQLAlchemy avec support pour PostgreSQL UUID
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.now)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    sport = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    is_user = Column(String)  # "true" ou "false"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# Création des tables
Base.metadata.create_all(bind=engine)

# Modèles Pydantic
class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    user_id: uuid.UUID
    sport: str
    content: str
    conversation_id: Optional[uuid.UUID] = None

class MessageResponse(BaseModel):
    id: uuid.UUID
    content: str
    is_user: bool
    created_at: datetime

    class Config:
        orm_mode = True
        
class ConversationResponse(BaseModel):
    id: uuid.UUID
    sport: str
    messages: List[MessageResponse]
    created_at: datetime

    class Config:
        orm_mode = True

class ChatStreamRequest(BaseModel):
    user_id: uuid.UUID
    sport: str
    content: str
    conversation_id: Optional[uuid.UUID] = None

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration pour gérer les UUID
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # Si l'objet est un UUID, le convertir en string
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Route de vérification de santé
@app.get("/ping")
def pong():
    return {"ping": "pong!"}

# Réponses prédéfinies par sport
sport_responses = {
    "rugby": [
        "Le rugby est un sport de combat collectif qui se joue à 15 contre 15.",
        "Le XV de France a remporté le Tournoi des Six Nations en 2022.",
        "La Coupe du Monde de Rugby se déroule tous les quatre ans.",
        "L'essai vaut 5 points, la transformation 2 points et le drop ou la pénalité 3 points."
    ],
    "football": [
        "Le football se joue à 11 contre 11 avec un ballon rond.",
        "La Coupe du Monde de football a lieu tous les quatre ans.",
        "Le Real Madrid est le club le plus titré en Ligue des Champions.",
        "Un match de football dure 90 minutes, réparties en deux mi-temps de 45 minutes."
    ],
    "tennis": [
        "Le tennis se joue en simple (1 contre 1) ou en double (2 contre 2).",
        "Les quatre tournois du Grand Chelem sont l'Open d'Australie, Roland-Garros, Wimbledon et l'US Open.",
        "Le service alterne tous les deux points, et les joueurs changent de côté tous les jeux impairs.",
        "Le tie-break se joue à 6-6 dans la plupart des sets."
    ],
    "volley": [
        "Le volleyball se joue à 6 contre 6 sur un terrain séparé par un filet.",
        "Chaque équipe peut toucher le ballon trois fois avant de le renvoyer.",
        "Un match se joue en trois sets gagnants de 25 points (avec 2 points d'écart).",
        "La position des joueurs sur le terrain est réglementée et doit suivre un ordre précis."
    ],
    "cyclisme": [
        "Le Tour de France est la plus célèbre course cycliste au monde.",
        "Le cyclisme sur route comprend différents types d'épreuves : contre-la-montre, courses en ligne, etc.",
        "Le maillot jaune est porté par le leader du classement général du Tour de France.",
        "Un vélo de course pèse environ 7 kg et doit respecter des normes précises fixées par l'UCI."
    ]
}

# Routes pour les utilisateurs
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Routes pour les conversations
@app.post("/chat/", response_model=Dict)
def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    # Vérifier si l'utilisateur existe
    user = db.query(User).filter(User.id == message.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Vérifier si le sport est valide
    sport = message.sport.lower()
    if sport not in sport_responses:
        raise HTTPException(status_code=400, detail="Sport not supported")
    
    # Créer ou récupérer une conversation existante
    conversation = None
    if message.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == message.conversation_id,
            Conversation.user_id == message.user_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(user_id=message.user_id, sport=sport)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Enregistrer le message de l'utilisateur
    user_message = Message(
        conversation_id=conversation.id,
        is_user="true",
        content=message.content
    )
    db.add(user_message)
    
    # Générer et enregistrer la réponse du bot
    response_content = random.choice(sport_responses[sport])
    bot_message = Message(
        conversation_id=conversation.id,
        is_user="false",
        content=response_content
    )
    db.add(bot_message)
    
    db.commit()
    db.refresh(bot_message)
    
    # Créer la réponse avec l'ID de conversation
    response = MessageResponse(
        id=bot_message.id,
        content=bot_message.content,
        is_user=False,
        created_at=bot_message.created_at
    )
    
    # Ajouter l'ID de conversation à la réponse
    response_dict = json.loads(json.dumps(response.dict(), cls=UUIDEncoder))
    response_dict["conversation_id"] = str(conversation.id)
    
    return response_dict

@app.get("/history/{user_id}", response_model=List[ConversationResponse])
def get_history(user_id: uuid.UUID, db: Session = Depends(get_db)):
    # Vérifier si l'utilisateur existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Récupérer toutes les conversations de l'utilisateur
    conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
    
    result = []
    for conv in conversations:
        messages = db.query(Message).filter(Message.conversation_id == conv.id).all()
        message_responses = [
            MessageResponse(
                id=msg.id,
                content=msg.content,
                is_user=True if msg.is_user == "true" else False,
                created_at=msg.created_at
            ) for msg in messages
        ]
        
        result.append(
            ConversationResponse(
                id=conv.id,
                sport=conv.sport,
                messages=message_responses,
                created_at=conv.created_at
            )
        )
    
    return result

@app.get("/conversation/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère une conversation spécifique avec tous ses messages"""
    # Chercher la conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Récupérer tous les messages de la conversation
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).all()
    
    # Transformer les messages en format de réponse
    message_responses = [
        MessageResponse(
            id=msg.id,
            content=msg.content,
            is_user=True if msg.is_user == "true" else False,
            created_at=msg.created_at
        ) for msg in messages
    ]
    
    # Trier les messages par date de création
    message_responses.sort(key=lambda x: x.created_at)
    
    # Construire et retourner la réponse complète
    return ConversationResponse(
        id=conversation.id,
        sport=conversation.sport,
        messages=message_responses,
        created_at=conversation.created_at
    )

@app.get("/admin/stats")
def get_stats(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    conversation_count = db.query(Conversation).count()
    message_count = db.query(Message).count()
    
    # Stats par sport
    sport_stats = {}
    for sport in sport_responses.keys():
        sport_conversations = db.query(Conversation).filter(Conversation.sport == sport).count()
        sport_stats[sport] = sport_conversations
    
    return {
        "user_count": user_count,
        "conversation_count": conversation_count,
        "message_count": message_count,
        "sport_stats": sport_stats
    }

# Fonction simulant la génération de réponse progressive
async def generate_streaming_response(sport: str) -> AsyncGenerator[str, None]:
    # Réponses prédéfinies par sport (on utilise celles existantes)
    response = random.choice(sport_responses[sport])
    
    # Pour simuler un envoi mot par mot, on divise la réponse en mots
    words = response.split()
    for word in words:
        yield word + " "
        # Petit délai entre les mots pour simuler une réponse progressive
        await asyncio.sleep(0.1)

# Route pour le chat avec streaming
@app.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest, db: Session = Depends(get_db)):
    # Vérifier si l'utilisateur existe
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        return StreamingResponse(content=iter(["Utilisateur non trouvé"]), media_type="text/plain")
    
    # Vérifier si le sport est valide
    sport = request.sport.lower()
    if sport not in sport_responses:
        return StreamingResponse(content=iter(["Sport non pris en charge"]), media_type="text/plain")

    # Récupérer ou créer une conversation
    conversation = None
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == request.user_id
        ).first()
    
    if not conversation:
        conversation = Conversation(user_id=request.user_id, sport=sport)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Enregistrer le message de l'utilisateur
    user_message = Message(
        conversation_id=conversation.id,
        is_user="true",
        content=request.content
    )
    db.add(user_message)
    db.commit()
    
    # Créer un message vide pour la réponse du bot
    bot_message = Message(
        conversation_id=conversation.id,
        is_user="false",
        content=""  # Sera mis à jour après le streaming
    )
    db.add(bot_message)
    db.commit()
    db.refresh(bot_message)
    
    # Information à envoyer au frontend avant le streaming
    header_info = {
        "message_id": str(bot_message.id),
        "conversation_id": str(conversation.id)
    }
    
    # Yield l'information d'en-tête en premier, puis les mots
    async def generate_response():
        yield json.dumps(header_info) + "\n"
        
        full_response = ""
        async for word in generate_streaming_response(sport):
            full_response += word
            yield word
        
        # Mettre à jour le message dans la base de données avec la réponse complète
        db_message = db.query(Message).filter(Message.id == bot_message.id).first()
        if db_message:
            db_message.content = full_response.strip()
            db.commit()
    
    return StreamingResponse(
        content=generate_response(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
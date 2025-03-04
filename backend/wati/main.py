from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import database
from .routes import user, broadcast, contacts, auth, woocommerce, integration, wallet
from .services import dramatiq_router
from . import oauth2
from wati.models.ChatBox import Last_Conversation
from .models import ChatBox
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Models creation



async def create_db_and_tables():
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)



# database.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()

# Adding the routes
app.include_router(broadcast.router)
app.include_router(contacts.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(oauth2.router)
app.include_router(dramatiq_router.router)
app.include_router(woocommerce.router)
app.include_router(integration.router)

# Defining origins for CORS


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up the scheduler
# scheduler = BackgroundScheduler()

# def close_expired_chats():
#     db = next(database.get_db())  # Get the database session
#     now = datetime.now()
#     expired_conversations = db.query(ChatBox.Last_Conversation).filter(
#         ChatBox.Last_Conversation.active == True,
#         (now - ChatBox.Last_Conversation.last_chat_time) > timedelta(minutes=5)
#         # (now - ChatBox.Last_Conversation.first_chat_time) > timedelta(hours=24)
#     ).all()

#     for conversation in expired_conversations:
#         conversation.active = False
        
#     db.commit()

# # Schedule the job (do not start the scheduler here)
# scheduler.add_job(close_expired_chats, 'interval', minutes=1)

# @app.on_event("startup")
# async def startup_event():
#     # Start the scheduler here
#     scheduler.start()

# @app.on_event("shutdown")
# def shutdown_event():
#     # Shut down the scheduler
#     scheduler.shutdown()

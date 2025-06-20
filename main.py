from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, BigInteger, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from typing import Optional
import whisper
import os
import uuid

# ============================
# CONFIGURACIÓN GENERAL
# ============================

#DATABASE_URL = "postgresql://postgres:keni9614@localhost:5432/db_smartsecurity"
DATABASE_URL = "postgresql://postgres:onNAoMEopgjdtAWhnVrmCeLlMptjGCqC@shuttle.proxy.rlwy.net:43549/railway"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

db = SessionLocal()  # ✅ Se define para rutas externas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# MODELOS DE BASE DE DATOS
# ==========================

class Passenger(Base):
    __tablename__ = "passenger"
    passengerID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    passengerfirstName = Column(String(100))
    passengerlastname = Column(String(100))
    passengeremail = Column(String(150), unique=True)
    passengerdocumentID = Column(Integer)
    passengerdocumentType = Column(String(50))
    passengercellPhone = Column(Integer)
    passengercodecellPhone = Column(Integer)
    passengerpassword = Column(String(255))
    isActive = Column(Boolean, default=True)
    lastLogin = Column(TIMESTAMP, default=datetime.utcnow)
    drives = Column(Boolean, default=False)
    licenseCategory = Column(String(50), default='')
    licenseNumber = Column(String(50), default='')
    hasCar = Column(Boolean, default=False)
    licensePlate = Column(String(50), default='')

class Driver(Base):
    __tablename__ = "driver"
    passengerID = Column(Integer, ForeignKey("passenger.passengerID"), primary_key=True)
    drives = Column(Boolean, nullable=False)
    licenseCategory = Column(String(50))
    licenseNumber = Column(String(50))
    hasCar = Column(Boolean, nullable=False)
    licensePlate = Column(String(50))
    passenger = relationship("Passenger", backref="driver")

class Email(Base):
    __tablename__ = "email"
    emailID = Column(BigInteger, primary_key=True, autoincrement=True)
    subjectEmail = Column(String(150))
    descriptionEmail = Column(String)
    passengerID = Column(Integer, ForeignKey("passenger.passengerID"))
    isActive = Column(Boolean, default=True)
    lastLogin = Column(TIMESTAMP, default=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keyword"
    keywordID = Column(Integer, primary_key=True, autoincrement=True)
    keywordName = Column(String(100))

class Place(Base):
    __tablename__ = "place"
    placeID = Column(Integer, primary_key=True, autoincrement=True)
    placeName = Column(String(100))
    address = Column(String(200))

class TrustedContact(Base):
    __tablename__ = "trustedcontact"
    trustedContactID = Column(BigInteger, primary_key=True, autoincrement=True)
    trustedContactFullName = Column(String(100))
    trustedContactCodeCellPhone = Column(Integer)
    trustedContactCellPhone = Column(Integer)
    trustedContactEmail = Column(String(150))

class LocationTrack(Base):
    __tablename__ = 'location_track'
    passenger_id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ==========================
# MODELOS Pydantic (Frontend)
# ==========================

from typing import Optional

class PassengerBase(BaseModel):
    passengerID: Optional[int] = None
    passengerfirstName: str
    passengerlastname: str
    passengeremail: str
    passengerdocumentID: int
    passengerdocumentType: Optional[str] = ''
    passengercellPhone: int
    passengercodecellPhone: int
    passengerpassword: str
    isActive: Optional[bool] = True
    drives: Optional[bool] = False
    licenseCategory: Optional[str] = ''
    licenseNumber: Optional[str] = ''
    hasCar: Optional[bool] = False
    licensePlate: Optional[str] = ''

class DriverCreate(BaseModel):
    passenger: PassengerBase
    drives: bool
    licenseCategory: str
    licenseNumber: str
    hasCar: bool
    licensePlate: str

class EmailCreate(BaseModel):
    emailID: int
    subjectEmail: str
    descriptionEmail: str
    passengerID: int

class KeywordSchema(BaseModel):
    keywordID: Optional[int]=None
    keywordName: str

class PlaceSchema(BaseModel):
    placeID: Optional[int]=None 
    placeName: str
    address: str

class TrustedContactSchema(BaseModel):
    trustedContactID: Optional[int]=None
    trustedContactFullName: str
    trustedContactCodeCellPhone: int
    trustedContactCellPhone: int
    trustedContactEmail: str

class LoginInput(BaseModel):
    email: str
    password: str

class LocationUpdate(BaseModel):
    passenger_id: int
    latitude: float
    longitude: float

# ============================  
# RUTAS PASSENGER
# ============================

@app.post("/passenger/")
def crear_passenger(passenger: PassengerBase):
    db = SessionLocal()
    try:
        nuevo = Passenger(**passenger.dict())
        db.add(nuevo)
        db.commit()
        return {"message": "Passenger created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@app.put("/passenger/{passenger_id}")
def actualizar_passenger(passenger_id: int, data: PassengerBase):
    db = SessionLocal()
    try:
        pasajero = db.query(Passenger).filter(Passenger.passengerID == passenger_id).first()
        if not pasajero:
            raise HTTPException(status_code=404, detail="Passenger not found")

        for attr, value in data.dict().items():
            if attr != "passengerID":
                setattr(pasajero, attr, value)

        db.commit()
        return {"message": "Passenger updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@app.delete("/passenger/{passenger_id}")
def eliminar_passenger(passenger_id: int):
    db = SessionLocal()
    try:
        pasajero = db.query(Passenger).filter(Passenger.passengerID == passenger_id).first()
        if not pasajero:
            raise HTTPException(status_code=404, detail="Passenger not found")

        # 🧹 Borrar contactos de confianza por teléfono del pasajero
        db.query(TrustedContact).filter(
            TrustedContact.trustedContactCellPhone == pasajero.passengercellPhone
        ).delete()

        # 🧹 Borrar ubicaciones si tienen una relación (si Place tiene un passengerID, por ejemplo)
        db.query(Place).filter(Place.passengerID == passenger_id).delete()

        # 🗑️ Borrar pasajero
        db.delete(pasajero)
        db.commit()

        return {"message": "Passenger and related data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@app.get("/passenger/search")
def buscar_passenger_por_email_y_password(email: str, password: str):
    db = SessionLocal()
    try:
        pasajero = db.query(Passenger).filter(
            Passenger.passengeremail == email,
            Passenger.passengerpassword == password
        ).first()
        if pasajero:
            return pasajero.__dict__
        raise HTTPException(status_code=404, detail="Passenger not found")
    finally:
        db.close()

# ==========================
# RUTAS DE API DRIVER
# ==========================

@app.post("/driver/")
def crear_driver(driver_data: DriverCreate):
    db = SessionLocal()
    try:
        # Usar el passenger ya existente
        passenger = db.query(Passenger).filter(Passenger.passengerID == driver_data.passenger.passengerID).first()
        if not passenger:
            raise HTTPException(status_code=404, detail="Passenger not found")

        # Verificar si el driver ya existe
        existing_driver = db.query(Driver).filter(Driver.passengerID == driver_data.passenger.passengerID).first()
        if existing_driver:
            raise HTTPException(status_code=400, detail="Driver already exists")

        # Crear Driver únicamente
        driver = Driver(
            passengerID=passenger.passengerID,
            drives=driver_data.drives,
            licenseCategory=driver_data.licenseCategory,
            licenseNumber=driver_data.licenseNumber,
            hasCar=driver_data.hasCar,
            licensePlate=driver_data.licensePlate
        )
        db.add(driver)
        db.commit()
        return {"message": "Driver created successfully", "id": driver.passengerID}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@app.put("/driver/{driver_id}")
def actualizar_driver(driver_id: int, driver_data: DriverCreate):
    db = SessionLocal()
    try:
        passenger = db.query(Passenger).filter(Passenger.passengerID == driver_id).first()
        driver = db.query(Driver).filter(Driver.passengerID == driver_id).first()

        if not passenger or not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

        # Actualizar Passenger
        passenger.passengerFirstName = driver_data.passenger.passengerFirstName
        passenger.passengerLastName = driver_data.passenger.passengerLastName
        passenger.passengerEmail = driver_data.passenger.passengerEmail
        passenger.passengerDocumentID = driver_data.passenger.passengerDocumentID
        passenger.passengerDocumentType = driver_data.passenger.passengerDocumentType
        passenger.passengerCellPhone = driver_data.passenger.passengerCellPhone
        passenger.passengerCodeCellPhone = driver_data.passenger.passengerCodeCellPhone
        passenger.passengerPassword = driver_data.passenger.passengerPassword

        # Actualizar Driver
        driver.drives = driver_data.drives
        driver.licenseCategory = driver_data.licenseCategory
        driver.licenseNumber = driver_data.licenseNumber
        driver.hasCar = driver_data.hasCar
        driver.licensePlate = driver_data.licensePlate

        db.commit()
        return {"message": "Driver updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@app.delete("/driver/{driver_id}")
def eliminar_driver(driver_id: int):
    db = SessionLocal()
    try:
        # Verificar existencia
        driver = db.query(Driver).filter(Driver.passengerID == driver_id).first()
        passenger = db.query(Passenger).filter(Passenger.passengerID == driver_id).first()

        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        if not passenger:
            raise HTTPException(status_code=404, detail="Passenger not found")

        # Eliminar emails asociados al pasajero (si existen)
        db.query(Email).filter(Email.passengerID == passenger.passengerID).delete()

        # Eliminar contactos de confianza (si aplican)
        db.query(TrustedContact).filter(TrustedContact.trustedContactCellPhone == passenger.passengercellPhone).delete()

        # Eliminar driver y luego passenger
        db.delete(driver)
        db.delete(passenger)
        db.commit()

        return {"message": "Driver deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar driver: {str(e)}")
    finally:
        db.close()

@app.get("/driver/{driver_id}")
def obtener_driver(driver_id: int):
    db = SessionLocal()
    try:
        driver = db.query(Driver).filter(Driver.passengerID == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"message": "Driver exists"}
    finally:
        db.close()

# ============================
# RUTAS EMAIL
# ============================

@app.post("/email/")
def crear_email(email: EmailCreate):
    db = SessionLocal()
    try:
        nuevo_email = Email(**email.dict())
        db.add(nuevo_email)
        db.commit()
        return {"message": "Email added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ============================
# RUTAS KEYWORD
# ============================

@app.post("/keyword/")
def crear_keyword(keyword: KeywordSchema):
    db = SessionLocal()
    try:
        nueva = Keyword(**keyword.dict())
        db.add(nueva)
        db.commit()
        return {"message": "Keyword created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/keyword/")
def listar_keywords():
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).all()
        return keywords
    finally:
        db.close()

@app.delete("/keyword/{keyword_id}")
def eliminar_keyword(keyword_id: int):
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.keywordID == keyword_id).first()
        if not keyword:
            raise HTTPException(status_code=404, detail="Keyword not found")
        db.delete(keyword)
        db.commit()
        return {"message": "Keyword deleted"}
    finally:
        db.close()

@app.put("/keyword/{keyword_id}")
def actualizar_keyword(keyword_id: int, keyword: KeywordSchema):
    db = SessionLocal()
    try:
        existing = db.query(Keyword).filter(Keyword.keywordID == keyword_id).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Keyword not found")
        existing.keywordName = keyword.keywordName
        db.commit()
        return {"message": "Keyword updated"}
    finally:
        db.close()

# ============================
# RUTAS PLACE
# ============================

@app.post("/place/")
def crear_place(place: PlaceSchema):
    db = SessionLocal()
    try:
        nuevo = Place(
            placeName=place.placeName,
            address=place.address
        )
        db.add(nuevo)
        db.commit()
        return {"message": "Place created"}
    finally:
        db.close()

@app.get("/place/")
def listar_places():
    db = SessionLocal()
    try:
        return db.query(Place).all()
    finally:
        db.close()

@app.delete("/place/{place_id}")
def eliminar_place(place_id: int):
    db = SessionLocal()
    try:
        place = db.query(Place).filter(Place.placeID == place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        db.delete(place)
        db.commit()
        return {"message": "Place deleted"}
    finally:
        db.close()

@app.get("/place/search/")
def buscar_place(query: str):
    db = SessionLocal()
    try:
        results = db.query(Place).filter(
            (Place.placeName.ilike(f"%{query}%")) |
            (Place.address.ilike(f"%{query}%"))
        ).all()
        return results
    finally:
        db.close()

# ============================
# RUTAS TRUSTED CONTACT
# ============================

@app.post("/trustedcontact/")
def crear_trusted_contact(data: TrustedContactSchema):
    db = SessionLocal()
    try:
        nuevo = TrustedContact(**data.dict())
        db.add(nuevo)
        db.commit()
        return {"message": "Trusted contact created"}
    finally:
        db.close()

@app.get("/trustedcontact/")
def listar_trusted_contacts():
    db = SessionLocal()
    try:
        return db.query(TrustedContact).all()
    finally:
        db.close()

@app.delete("/trustedcontact/{contact_id}")
def eliminar_trusted_contact(contact_id: int):
    db = SessionLocal()
    try:
        contacto = db.query(TrustedContact).filter(TrustedContact.trustedContactID == contact_id).first()
        if not contacto:
            raise HTTPException(status_code=404, detail="Trusted contact not found")
        db.delete(contacto)
        db.commit()
        return {"message": "Trusted contact deleted"}
    finally:
        db.close()

@app.get("/trustedcontact/search/")
def buscar_contacto(query: str):
    db = SessionLocal()
    try:
        results = db.query(TrustedContact).filter(
            (TrustedContact.trustedContactFullName.ilike(f"%{query}%")) |
            (TrustedContact.trustedContactEmail.ilike(f"%{query}%"))
        ).all()
        return results
    finally:
        db.close()

# ============================  
# RUTAS LOGIN
# ============================

@app.post("/login/")
def login_passenger(data: LoginInput):
    db = SessionLocal()
    try:
        passenger = db.query(Passenger).filter(
            Passenger.passengeremail == data.email,
            Passenger.passengerpassword == data.password
        ).first()

        if not passenger:
            raise HTTPException(status_code=404, detail="Invalid email or password")

        return {
            "passengerID": passenger.passengerID,
            "passengerfirstName": passenger.passengerfirstName,  # minúscula f
            "passengerlastname": passenger.passengerlastname,
            "passengeremail": passenger.passengeremail,
            "passengerdocumentID": passenger.passengerdocumentID,
            "passengerdocumentType": passenger.passengerdocumentType,
            "passengercellPhone": passenger.passengercellPhone,
            "passengercodecellPhone": passenger.passengercodecellPhone,
            "passengerpassword": passenger.passengerpassword,
            "isActive": passenger.isActive,
            "lastLogin": passenger.lastLogin
        }
    finally:
        db.close()

# ============================
# TRANSCRIPCIÓN CON WHISPER
# ============================

model = whisper.load_model("base")  # Puedes cambiar a tiny, small, etc.

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.wav"
    with open(temp_filename, "wb") as buffer:
        buffer.write(await file.read())

    try:
        result = model.transcribe(
            temp_filename,
            language="es",
            verbose=False,
            temperature=0.0
        )
        print("🔊 TRANSCRIPCIÓN:", result["text"])  # ✅ AGREGA ESTO
        return {"text": result["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al transcribir: {str(e)}")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# ============================
# CAMINATA CON GPS
# ============================

@app.post("/location/update")
def update_location(data: LocationUpdate):
    try:
        location = db.query(LocationTrack).filter_by(passenger_id=data.passenger_id).first()
        if location:
            location.latitude = data.latitude
            location.longitude = data.longitude
        else:
            location = LocationTrack(**data.dict())
            db.add(location)
        db.commit()
        return {"status": "updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating location: {str(e)}")

@app.get("/location/{passenger_id}")
def get_location(passenger_id: int):
    location = db.query(LocationTrack).filter_by(passenger_id=passenger_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"lat": location.latitude, "lng": location.longitude, "updated": location.updated_at}

# ============================
# INICIO DEL SERVIDOR
# ============================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

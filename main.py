from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from sqlalchemy import BigInteger
from typing import Optional

# Configuración de la base de datos
#DATABASE_URL = "postgresql://postgres:keni9614@localhost:5432/db_smartsecurity"
DATABASE_URL = "postgresql://postgres:pApyzphFIKARRMuBVYsVqoorLspbgqRc@shortline.proxy.rlwy.net:55430/railway"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

app = FastAPI()

# 🔐 Habilitar CORS (antes de las rutas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia por ["http://localhost:3000"] si tu frontend está en otro puerto o dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# MODELOS DE BASE DE DATOS
# ==========================

class Passenger(Base):
    __tablename__ = "passenger"
    passengerID = Column("passengerID",Integer, primary_key=True, index=True, autoincrement=True)
    passengerFirstName = Column("passengerfirstName",String(100))
    passengerLastName = Column("passengerlastname",String(100))
    passengerEmail = Column("passengeremail",String(150))
    passengerDocumentID = Column("passengerdocumentID",Integer)
    passengerDocumentType = Column("passengerdocumentType",Integer)
    passengerCellPhone = Column("passengercellPhone",Integer)
    passengerCodeCellPhone = Column("passengercodecellPhone",Integer)
    passengerPassword = Column("passengerpassword",String(255))
    isActive = Column(Boolean, default=True)
    lastLogin = Column(TIMESTAMP, default=datetime.utcnow)

class Driver(Base):
    __tablename__ = "driver"
    passengerID = Column("passengerID",Integer, ForeignKey("passenger.passengerID"), primary_key=True)
    drives = Column("drives",Boolean, nullable=False)
    licenseCategory = Column("licenseCategory",String(50))
    licenseNumber = Column("licenseNumber",String(50))
    hasCar = Column("hasCar",Boolean, nullable=False)
    licensePlate = Column("licensePlate",String(50))
    passenger = relationship("Passenger", backref="driver")

class Email(Base):
    __tablename__ = "email"
    emailID = Column("emailID",BigInteger, primary_key=True, autoincrement=True)
    subjectEmail = Column("subjectEmail",String(150))
    descriptionEmail = Column("descriptionEmail",String)
    passengerID = Column("passengerID",Integer, ForeignKey("passenger.passengerID"))
    isActive = Column("isActive",Boolean, default=True)
    lastLogin = Column("lastLogin",TIMESTAMP, default=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keyword"
    keywordID = Column("keywordID",Integer, primary_key=True, autoincrement=True)
    keywordName = Column("keywordName",String(100))

class Place(Base):
    __tablename__ = "place"
    placeID = Column("placeID",Integer, primary_key=True, autoincrement=True)
    placeName = Column("placeName",String(100))
    address = Column("address",String(200))

class TrustedContact(Base):
    __tablename__ = "trustedcontact"
    trustedContactID = Column("trustedcontactid",BigInteger, primary_key=True, autoincrement=True)
    trustedContactFullName = Column("trustedcontactfullname",String(100))
    trustedContactCodeCellPhone = Column("trustedcontactcodecellphone",Integer)
    trustedContactCellPhone = Column("trustedcontactcellphone",Integer)
    trustedContactEmail = Column("trustedcontactemail",String(150))

Base.metadata.create_all(bind=engine)

# ==========================
# MODELOS Pydantic (Frontend)
# ==========================

class PassengerBase(BaseModel):
    passengerID: int
    passengerFirstName: str
    passengerLastName: str
    passengerEmail: str
    passengerDocumentID: int
    passengerDocumentType: int
    passengerCellPhone: int
    passengerCodeCellPhone: int
    passengerPassword: str

class DriverCreate(BaseModel):
    passenger: PassengerBase
    drives: bool
    licenseCategory: str
    licenseNumber: str
    hasCar: bool
    licensePlate: str

class EmailCreate(BaseModel):
    emailID: Optional[int]=None
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

# ============================  
# RUTAS PASSENGER
# ============================

@app.post("/passenger/")
def crear_passenger(passenger: PassengerBase):
    db = SessionLocal()
    try:
        existente = db.query(Passenger).filter(Passenger.passengerID == passenger.passengerID).first()
        if existente:
            raise HTTPException(status_code=400, detail="Passenger already exists")
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
        db.delete(pasajero)
        db.commit()
        return {"message": "Passenger deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ==========================
# RUTAS DE API DRIVER
# ==========================

@app.post("/driver/")
def crear_driver(driver_data: DriverCreate):
    db = SessionLocal()
    try:
        # Verifica si ya existe el passenger
        existing = db.query(Passenger).filter(Passenger.passengerID == driver_data.passenger.passengerID).first()
        if existing:
            raise HTTPException(status_code=400, detail="Passenger already exists")

        # Crear Passenger
        passenger = Passenger(
            passengerID=driver_data.passenger.passengerID,
            passengerFirstName=driver_data.passenger.passengerFirstName,
            passengerLastName=driver_data.passenger.passengerLastName,
            passengerEmail=driver_data.passenger.passengerEmail,
            passengerDocumentID=driver_data.passenger.passengerDocumentID,
            passengerDocumentType=driver_data.passenger.passengerDocumentType,
            passengerCellPhone=driver_data.passenger.passengerCellPhone,
            passengerCodeCellPhone=driver_data.passenger.passengerCodeCellPhone,
            passengerPassword=driver_data.passenger.passengerPassword
        )
        db.add(passenger)

        # Crear Driver
        driver = Driver(
            passengerID=driver_data.passenger.passengerID,
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
        driver = db.query(Driver).filter(Driver.passengerID == driver_id).first()
        passenger = db.query(Passenger).filter(Passenger.passengerID == driver_id).first()

        if not driver or not passenger:
            raise HTTPException(status_code=404, detail="Driver not found")

        db.delete(driver)
        db.delete(passenger)
        db.commit()
        return {"message": "Driver deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
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
        nuevo = Place(**place.dict())
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

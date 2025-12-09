from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    provinces = relationship("Province", back_populates="country")

class Province(Base):
    __tablename__ = "provinces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    country = relationship("Country", back_populates="provinces")
    cities = relationship("City", back_populates="province")

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    province_id = Column(Integer, ForeignKey("provinces.id"))
    province = relationship("Province", back_populates="cities")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

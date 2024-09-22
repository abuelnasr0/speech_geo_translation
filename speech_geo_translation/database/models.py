from sqlalchemy import ForeignKey
from sqlalchemy import String, Float, BigInteger, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

STRINGS_LINGTH = 70

class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(STRINGS_LINGTH), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(11), nullable=True, unique=True)


class Governorate(Base):
    __tablename__ = "governorate"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(STRINGS_LINGTH))


class Qism(Base):
    # section, (qism or markaz)
    __tablename__ = "qism"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    governorate_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("governorate.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(STRINGS_LINGTH))


class ServiceArea(Base):
    # Sub section, (Shayakha or village)
    __tablename__ = "service_area"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    governorate_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("governorate.id"), nullable=False
    )
    qism_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("qism.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(STRINGS_LINGTH))


class Complaint(Base):
    __tablename__ = "complaint"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    service_area_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("service_area.id"), nullable=False
    )
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)


    # Can be null
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customer.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(STRINGS_LINGTH), nullable=True)
    status: Mapped[str] = mapped_column(String(STRINGS_LINGTH), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=True)

from sqlalchemy import ForeignKey
from sqlalchemy import String, Float, BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(11), nullable=True, unique=True)


class Governorate(Base):
    __tablename__ = "governorate"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


class Qism(Base):
    # section, (qism or markaz)
    __tablename__ = "qism"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gov_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("governorate.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50))


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
    name: Mapped[str] = mapped_column(String(50))


class ComplaintLocation(Base):
    __tablename__ = "complaint_location"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    service_area_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("service_area.id"), nullable=False
    )


class Complaint(Base):
    __tablename__ = "complaint"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customer.id"), nullable=True
    )
    location_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("complaint_location.id"), nullable=False
    )
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    priority: Mapped[int] = mapped_column(int, nullable=True)

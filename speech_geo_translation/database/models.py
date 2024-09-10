from sqlalchemy import ForeignKey
from sqlalchemy import String, Float, BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Complaint(Base):
    __tablename__ = "complaint"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    complaint_type: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("complaint_type.id")
    )


class ComplaintType(Base):
    __tablename__ = "complaint_type"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20))

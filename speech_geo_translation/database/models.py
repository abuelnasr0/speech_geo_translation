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


class GovsQhrCounts(Base):
    __tablename__ = "govs_qhr_counts"

    gov_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("governorate.id"), primary_key=True, nullable=False
    )
    time: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    anamoly: Mapped[str] = mapped_column(
        String(10), default="PENDING"
    )  # or TRUE or FALSE


class QismsQhrCounts(Base):
    __tablename__ = "qisms_qhr_counts"

    qism_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("qism.id"), primary_key=True, nullable=False
    )
    time: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    anamoly: Mapped[str] = mapped_column(
        String(10), default="PENDING"
    )  # or TRUE or FALSE


class AreasQhrCounts(Base):
    __tablename__ = "areas_qhr_counts"

    area_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("service_area.id"), primary_key=True, nullable=False
    )
    time: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    anamoly: Mapped[str] = mapped_column(
        String(10), default="PENDING"
    )  # or TRUE or FALSE


"""
aggregation functions to count complaints regionly.
"""
COUNTING_GOVS_FUN_STRING = """
CREATE PROCEDURE IF NOT EXISTS count_govs_qhr()
BEGIN
    INSERT INTO govs_qhr_counts (gov_id, time, count, anamoly) 
    SELECT 
        S.governorate_id AS gov_id, 
        DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:00') AS time, 
        COUNT(*) AS count,
        'PENDING' AS anamoly
    FROM 
        service_area S 
    JOIN 
        complaint C ON C.service_area_id = S.id 
    WHERE 
        C.time <= NOW() 
        AND C.time >= NOW() - INTERVAL 15 MINUTE 
    GROUP BY 
        S.governorate_id;
END 
"""


COUNTING_QISMS_FUN_STRING = """
CREATE PROCEDURE IF NOT EXISTS count_qisms_qhr()
BEGIN
    INSERT INTO qisms_qhr_counts (qism_id, time, count, anamoly) 
    SELECT 
        S.qism_id AS qism_id, 
        DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:00') AS time, 
        COUNT(*) AS count,
        'PENDING' AS anamoly
    FROM 
        service_area S 
    JOIN 
        complaint C ON C.service_area_id = S.id 
    WHERE 
        C.time <= NOW() 
        AND C.time >= NOW() - INTERVAL 15 MINUTE 
    GROUP BY 
        S.qism_id;
END  
"""


COUNTING_AREAS_FUN_STRING = """
CREATE PROCEDURE IF NOT EXISTS count_areas_qhr()
BEGIN
    INSERT INTO areas_qhr_counts (area_id, time, count, anamoly) 
    SELECT 
        S.id AS area_id, 
        DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:00') AS time, 
        COUNT(*) AS count,
        'PENDING' AS anamoly
    FROM 
        service_area S 
    JOIN 
        complaint C ON C.service_area_id = S.id 
    WHERE 
        C.time <= NOW() 
        AND C.time >= NOW() - INTERVAL 15 MINUTE 
    GROUP BY 
        S.id;
END 
"""


"""
Event to call aggregation functions every 15 minute at (00, 15, 30, 45)
"""
EVENT_STRING = """CREATE EVENT IF NOT EXISTS count_complaints_regionly
ON SCHEDULE EVERY 1 MINUTE
DO
BEGIN
    IF MINUTE(NOW()) IN (0, 15, 30, 45) THEN
        CALL count_govs_qhr();
        CALL count_qisms_qhr();
        CALL count_areas_qhr();
    END IF;
END
"""

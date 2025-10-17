from datetime import datetime, date
from typing import Annotated

from sqlalchemy import BigInteger, Numeric, String, Boolean, TIMESTAMP, text, Text, ForeignKey, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

intpk = Annotated[int, mapped_column(primary_key=True)]


class User(BaseModel):
    __tablename__ = "users"
    
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False)
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False)


    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    support_requests: Mapped[list["SupportRequest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activities: Mapped[list["Activity"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Activity(BaseModel):
    __tablename__ = "activity"
    
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    first_seen: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), onupdate=text("NOW()"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"), nullable=False)
    actions: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    
    user: Mapped["User"] = relationship(back_populates="activities")


class MenuItem(BaseModel):
    __tablename__ = "menu_items"
    
    id: Mapped[intpk]
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    
    photo_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Добавляем недостающие отношения
    cart_entries: Mapped[list["CartItem"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="item", cascade="all, delete-orphan")


class CartItem(BaseModel):
    __tablename__ = "cart_items"
    
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    
    user: Mapped["User"] = relationship(back_populates="cart_items")
    item: Mapped["MenuItem"] = relationship(back_populates="cart_entries")


class Order(BaseModel):
    __tablename__ = "orders"

    id: Mapped[intpk]
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    total: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    
    
    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete")


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    id: Mapped[intpk]
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id", ondelete="SET NULL"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    
    
    order: Mapped["Order"] = relationship(back_populates="order_items")
    item: Mapped["MenuItem"] = relationship(back_populates="order_items")


class SupportRequest(BaseModel):
    __tablename__ = "support_requests"

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'open'"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    
    user: Mapped["User"] = relationship(back_populates="support_requests")

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), default='User')
    username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(24), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(24), nullable=True)
    calorie_target: Mapped[int] = mapped_column(Integer, default=0)
    protein_target: Mapped[int] = mapped_column(Integer, default=0)
    carb_target: Mapped[int] = mapped_column(Integer, default=0)
    fat_target: Mapped[int] = mapped_column(Integer, default=0)
    inviter_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    meals = relationship('Meal', back_populates='user', cascade='all,delete-orphan')


class Meal(Base):
    __tablename__ = 'meals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    food_description: Mapped[str] = mapped_column(String(255))
    calories: Mapped[float] = mapped_column(Float)
    protein: Mapped[float] = mapped_column(Float)
    carbs: Mapped[float] = mapped_column(Float)
    fats: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='meals')


class Friend(Base):
    __tablename__ = 'friends'
    __table_args__ = (UniqueConstraint('user_id', 'friend_id', name='uq_friends_pair'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Score(Base):
    __tablename__ = 'scores'
    __table_args__ = (UniqueConstraint('user_id', 'date', name='uq_scores_user_date'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    score: Mapped[float] = mapped_column(Float)
    calorie_progress: Mapped[float] = mapped_column(Float)
    protein_progress: Mapped[float] = mapped_column(Float)
    carb_progress: Mapped[float] = mapped_column(Float)
    fat_progress: Mapped[float] = mapped_column(Float)


class Invite(Base):
    __tablename__ = 'invites'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    new_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

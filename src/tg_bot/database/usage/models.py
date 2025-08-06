from sqlalchemy import Column, Integer, BigInteger, String, Date, Index # type: ignore
from sqlalchemy.orm import declarative_base # type: ignore
from database.base import Base 

class UserUsage(Base):
    __tablename__ = 'user_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False) 
    feature_type = Column(String, nullable=False) 
    usage_date = Column(Date, nullable=False)
    usage_count = Column(Integer, nullable=False, default=0) 

    __table_args__ = (Index('idx_user_feature_date', 'user_id', 'feature_type', 'usage_date'),)

    def __repr__(self):
        return f"<UserUsage(user_id={self.user_id}, feature_type='{self.feature_type}', usage_date={self.usage_date}, usage_count={self.usage_count})>"

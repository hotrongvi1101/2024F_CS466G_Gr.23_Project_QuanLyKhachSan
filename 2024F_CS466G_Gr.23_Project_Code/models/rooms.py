from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), default='Trống')

    @classmethod
    def get_all_rooms(cls):
        # Mô phỏng việc lấy tất cả các phòng
        return [
            {
                'code': '101', 
                'type': 'Phòng Đơn', 
                'price': 500000, 
                'status': 'Trống'
            },
            {
                'code': '201', 
                'type': 'Phòng Đôi', 
                'price': 800000, 
                'status': 'Đang Sử Dụng'
            }
        ]

    @classmethod
    def get_total_rooms(cls):
        return len(cls.get_all_rooms())

    @classmethod
    def get_occupied_rooms(cls):
        return len([room for room in cls.get_all_rooms() if room['status'] != 'Trống'])
class Booking:
    @classmethod
    def get_recent_bookings(cls, limit=5):
        # Mô phỏng các đặt phòng gần đây
        return [
            {
                'id': 1,
                'customer_name': 'Nguyễn Văn A',
                'room_number': '101',
                'check_in_date': '2024-02-15',
                'check_out_date': '2024-02-17',
                'total_price': 1000000
            },
            {
                'id': 2,
                'customer_name': 'Trần Thị B',                                                                                                      
                'room_number': '201',
                'check_in_date': '2024-02-16',
                'check_out_date': '2024-02-18',
                'total_price': 1600000
            }
        ][:limit]
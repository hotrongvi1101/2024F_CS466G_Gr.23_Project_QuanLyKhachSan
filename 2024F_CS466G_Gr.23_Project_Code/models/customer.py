class Customer:
    @classmethod
    def get_all_customers(cls):
        # Mô phỏng danh sách khách hàng
        return [
            {
                'id': 1,
                'name': 'Nguyễn Văn A',
                'phone': '0912345678',
                'email': 'nguyenvana@example.com',
                'total_stays': 3
            },
            {
                'id': 2,
                'name': 'Trần Thị B',
                'phone': '0987654321',
                'email': 'tranthib@example.com',
                'total_stays': 2
            }
        ]